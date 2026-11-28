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


def _make_phmsa_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(
            "accident_hazardous_liquid_2010_present.csv",
            "REPORT_NUMBER,I_YEAR,ACCIDENT_STATE_ABBREVIATION,COMMODITY_RELEASED_TYPE,CAUSE\n"
            "20240001,2024,TX,CRUDE OIL,CORROSION FAILURE\n"
            "20240002,2024,LA,REFINED PETROLEUM PRODUCT,EQUIPMENT FAILURE\n",
        )
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

    def test_hurdat2_and_phmsa_parsers(self):
        storms = public_ingest.parse_hurdat2_storms(SAMPLE_HURDAT2, min_year=2010)
        self.assertEqual(len(storms), 1)
        self.assertEqual(storms[0]["storm_id"], "AL092017")
        self.assertEqual(storms[0]["max_wind_kt"], 115)
        self.assertEqual(storms[0]["min_pressure_mb"], 937)
        self.assertTrue(storms[0]["reached_hurricane"])

        phmsa_rows = public_ingest.parse_phmsa_liquid_zip(_make_phmsa_zip())
        self.assertEqual(len(phmsa_rows), 2)
        self.assertEqual(phmsa_rows[0]["provenance_class"], "OBSERVED")

    def test_run_public_ingest_offline_with_mocks(self):
        uploaded: dict[str, bytes] = {}

        def fake_get(url: str) -> bytes:
            if "api.eia.gov" in url:
                return json.dumps(
                    {"response": {"total": "2", "data": [{"period": "2025-01-02", "value": "73.12"}, {"period": "2025-01-03", "value": "74.05"}]}}
                ).encode("utf-8")
            if "nhc.noaa.gov" in url:
                return SAMPLE_HURDAT2.encode("utf-8")
            if "data.epa.gov" in url:
                return json.dumps([{"facility_id": 1000025, "state": "LA", "naics_code": "324110"}]).encode("utf-8")
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
        self.assertEqual(manifest["sources"]["eia"]["series_count"], 14)
        self.assertEqual(manifest["sources"]["phmsa"]["status"], "INGESTED")
        self.assertIn("manifests/ingestion/public_vintage_2026-11-28.json", uploaded)
        blob = json.dumps(manifest)
        self.assertNotIn("TEST_SECRET_NEVER_STORED", blob)

    def test_committed_vintage_manifest_integrity_and_no_secrets(self):
        if not MANIFEST_PATH.exists():
            self.skipTest("Committed vintage manifest not yet generated")
        raw = MANIFEST_PATH.read_text(encoding="utf-8")
        self.assertNotIn("EIA_API_KEY", raw)
        self.assertNotIn("SECRET_ACCESS_KEY", raw)
        data = json.loads(raw)
        self.assertEqual(data["provenance_class"], "OBSERVED")
        recorded = data.pop("manifest_sha256")
        computed = hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        self.assertEqual(recorded, computed)
        self.assertEqual(data["sources"]["eia"]["series_count"], 14)
        for sid, info in data["sources"]["eia"]["series"].items():
            self.assertGreater(info["row_count"], 0, f"EIA series {sid} returned zero rows")
        self.assertGreater(data["sources"]["noaa"]["storms_since_2010"], 100)
        self.assertGreater(data["sources"]["epa"]["unique_facilities"], 10)


if __name__ == "__main__":
    unittest.main()
