#!/usr/bin/env python3
"""Offline contract and parser tests for WP-1a public data ingestion."""
from __future__ import annotations

import hashlib
import io
import json
import unittest
import zipfile
from pathlib import Path

from generators import public_ingest

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "fixtures" / "golden" / "public_data_vintage_manifest.json"

SAMPLE_HURDAT2 = """AL092017, HARVEY, 3,
20170825, 1800, , HU, 27.3N, 96.6W, 110, 943, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
20170826, 0300, L, HU, 28.0N, 97.0W, 115, 937, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
20170826, 1200, , TS, 28.7N, 97.3W, 60, 978, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
AL011999, ARLENE, 1,
19990611, 1800, , TD, 28.0N, 62.0W, 30, 1009, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
"""


def _make_phmsa_zip(include_readme: bool = True, empty_rows: bool = False) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        if include_readme:
            zf.writestr("00_readme_definitions.txt", "PHMSA field definitions\nNot a data table\n")
        body = "REPORT_NUMBER,I_YEAR,ACCIDENT_STATE_ABBREVIATION,COMMODITY_RELEASED_TYPE,CAUSE\n"
        if not empty_rows:
            body += (
                "20240001,2024,TX,CRUDE OIL,CORROSION FAILURE\n"
                "20240002,2024,LA,REFINED PETROLEUM PRODUCT,EQUIPMENT FAILURE\n"
            )
        zf.writestr("accident_hazardous_liquid_2010_present.csv", body)
    return buf.getvalue()


class TestPublicIngest(unittest.TestCase):
    def test_eia_url_builder_enforces_length_bounds(self):
        url = public_ingest.build_eia_query_url(
            "petroleum/pri/spt/data/", "RWTC", "daily", "2024-01-01", "2025-12-31", "DUMMY_KEY"
        )
        self.assertIn("facets%5Bseries%5D%5B%5D=RWTC", url)
        self.assertIn("length=5000", url)
        with self.assertRaises(ValueError):
            public_ingest.build_eia_query_url(
                "petroleum/pri/spt/data/", "RWTC", "daily", "2024-01-01", "2025-12-31", "DUMMY_KEY", length=5001
            )

    def test_eia_empty_series_raises_instead_of_emitting_observed(self):
        entry = public_ingest.EIA_SERIES_CATALOG[0]
        empty_resp = json.dumps({"response": {"total": "0", "data": []}}).encode("utf-8")
        with self.assertRaises(ValueError):
            public_ingest.fetch_eia_series(entry, "KEY", "2025-01-01", "2025-12-31", http_get=lambda _u: empty_resp)

    def test_epa_pagination_collects_multiple_pages_without_truncation(self):
        calls: list[str] = []

        def fake_get(url: str) -> bytes:
            calls.append(url)
            if "ROWS/0:1/" in url:
                return json.dumps([{"FACILITY_ID": 1001}, {"FACILITY_ID": 1002}]).encode("utf-8")
            if "ROWS/2:3/" in url:
                return json.dumps([{"facility_id": 1003}]).encode("utf-8")
            raise AssertionError(f"Unexpected EPA URL: {url}")

        rows = public_ingest.fetch_epa_ghgrp_state("TX", http_get=fake_get, page_size=2)
        self.assertEqual(len(rows), 3)
        self.assertEqual(len(calls), 2)

    def test_hurdat2_and_phmsa_parsers(self):
        all_storms = public_ingest.parse_hurdat2_storms(SAMPLE_HURDAT2, min_year=0)
        self.assertEqual(len(all_storms), 2)
        storms_2010 = public_ingest.parse_hurdat2_storms(SAMPLE_HURDAT2, min_year=2010)
        self.assertEqual(len(storms_2010), 1)
        self.assertEqual(storms_2010[0]["storm_id"], "AL092017")
        self.assertEqual(storms_2010[0]["max_wind_kt"], 115)
        self.assertEqual(storms_2010[0]["min_pressure_mb"], 937)
        self.assertTrue(storms_2010[0]["reached_hurricane"])

        # Multi-member archive: skips 00_readme_definitions.txt and finds REPORT_NUMBER CSV
        phmsa_rows = public_ingest.parse_phmsa_liquid_zip(_make_phmsa_zip(include_readme=True))
        self.assertEqual(len(phmsa_rows), 2)
        self.assertEqual(phmsa_rows[0]["provenance_class"], "OBSERVED")

        # Zero data rows must fail rather than report INGESTED
        with self.assertRaises(ValueError):
            public_ingest.parse_phmsa_liquid_zip(_make_phmsa_zip(include_readme=True, empty_rows=True))

    def test_run_public_ingest_offline_upload_and_dry_run_modes(self):
        uploaded: dict[str, bytes] = {}

        def fake_get(url: str) -> bytes:
            if "api.eia.gov" in url:
                return json.dumps(
                    {"response": {"total": "2", "data": [{"period": "2025-01-02", "value": "73.12"}, {"period": "2025-01-03", "value": "74.05"}]}}
                ).encode("utf-8")
            if "nhc.noaa.gov" in url:
                return SAMPLE_HURDAT2.encode("utf-8")
            if "data.epa.gov" in url:
                # Mix uppercase and lowercase facility_id keys as returned by Envirofacts
                if "/STATE/TX/" in url:
                    return json.dumps([{"FACILITY_ID": 1000025, "STATE": "TX", "NAICS_CODE": "324110"}]).encode("utf-8")
                return json.dumps([{"facility_id": 1000099, "state": "LA", "naics_code": "324110"}]).encode("utf-8")
            raise AssertionError(f"Unexpected URL: {url}")

        def fake_upload(key: str, data: bytes, _ctype: str) -> None:
            uploaded[key] = data

        manifest = public_ingest.run_public_ingest(
            vintage="2026-11-28",
            start_date="2025-01-01",
            end_date="2025-12-31",
            eia_api_key="TEST_SECRET_NEVER_STORED",
            http_get=fake_get,
            upload_fn=fake_upload,
            phmsa_zip_bytes=_make_phmsa_zip(),
        )
        self.assertEqual(manifest["provenance_class"], "OBSERVED")
        self.assertEqual(manifest["upload_status"], "UPLOADED_TO_R2")
        self.assertEqual(manifest["r2_bucket"], "pearland-petroleum-corp")
        self.assertTrue(all(o["uploaded"] for o in manifest["objects"]))
        self.assertEqual(manifest["sources"]["eia"]["series_count"], 14)
        self.assertEqual(manifest["sources"]["epa"]["unique_facilities"], 2)
        self.assertEqual(manifest["sources"]["phmsa"]["status"], "INGESTED")
        # NOAA object describes full archive (2 storms, 1999..2017) while summary tracks since-2010
        noaa_obj = next(o for o in manifest["objects"] if o["source"] == "noaa")
        self.assertEqual(noaa_obj["row_count"], 2)
        self.assertEqual(noaa_obj["date_min"], "1999")
        self.assertEqual(noaa_obj["date_max"], "2017")
        self.assertEqual(manifest["sources"]["noaa"]["storms_since_2010"], 1)
        self.assertIn("manifests/ingestion/public_vintage_2026-11-28.json", uploaded)
        self.assertNotIn("TEST_SECRET_NEVER_STORED", json.dumps(manifest))

        # Dry-run (--no-upload) must NOT claim R2 upload occurred
        dry = public_ingest.run_public_ingest(
            vintage="2026-11-28",
            start_date="2025-01-01",
            end_date="2025-12-31",
            eia_api_key="TEST_SECRET_NEVER_STORED",
            http_get=fake_get,
            upload_fn=None,
        )
        self.assertEqual(dry["upload_status"], "LOCAL_DRY_RUN_NOT_UPLOADED")
        self.assertIsNone(dry["r2_bucket"])
        self.assertTrue(all(not o["uploaded"] for o in dry["objects"]))

    def test_committed_vintage_manifest_integrity_and_no_secrets(self):
        if not MANIFEST_PATH.exists():
            self.skipTest("Committed vintage manifest not yet generated")
        raw = MANIFEST_PATH.read_text(encoding="utf-8")
        self.assertNotIn("EIA_API_KEY", raw)
        self.assertNotIn("SECRET_ACCESS_KEY", raw)
        data = json.loads(raw)
        self.assertEqual(data["provenance_class"], "OBSERVED")
        self.assertEqual(data["upload_status"], "UPLOADED_TO_R2")
        self.assertTrue(all(o["uploaded"] for o in data["objects"]))
        recorded = data.pop("manifest_sha256")
        computed = hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        self.assertEqual(recorded, computed)
        self.assertEqual(data["sources"]["eia"]["series_count"], 14)
        for sid, info in data["sources"]["eia"]["series"].items():
            self.assertGreater(info["row_count"], 0, f"EIA series {sid} returned zero rows")
        noaa_obj = next(o for o in data["objects"] if o["source"] == "noaa")
        self.assertEqual(noaa_obj["row_count"], data["sources"]["noaa"]["total_storms_in_archive"])
        self.assertGreater(data["sources"]["noaa"]["storms_since_2010"], 100)
        self.assertGreater(data["sources"]["epa"]["unique_facilities"], 10)


if __name__ == "__main__":
    unittest.main()
