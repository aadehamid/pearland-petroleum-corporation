#!/usr/bin/env python3
"""Tests for WP-8A DuckDB-vs-Databricks KPI parity and WP-8B Certified WorldExportBundle v1."""
from __future__ import annotations

import base64
import gzip
import hashlib
import unittest
import zlib
from pathlib import Path

from evaluations.world_export_bundle_v1 import (
    assemble_world_export_bundle_v1,
    audit_observable_for_hidden_leaks,
)
from lakehouse.delta.databricks_parity import diff_duckdb_vs_databricks_kpis

REPO_ROOT = Path(__file__).resolve().parents[1]
BUNDLE_SCHEMA = REPO_ROOT / "schemas" / "world_export_bundle.schema.json"


def _ref(name: str, path: str, payload: bytes) -> dict:
    return {
        "name": name,
        "path": path,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "size_bytes": len(payload),
    }


class TestWP8ParityAndWorldBundle(unittest.TestCase):
    def test_wp8a_duckdb_vs_databricks_kpi_parity_and_drift_detection(self):
        duck = [
            {"release_id": "REL-1", "branch_id": "baseline", "kpi_name": "ULSD Netback CPG", "measure_class": "KPI", "value": 214.50, "threshold_status": "GREEN"},
            {"release_id": "REL-1", "branch_id": "baseline", "kpi_name": "Margin Capture %", "measure_class": "KPI", "value": None, "threshold_status": "UNRESOLVED"},
        ]
        dbx_ok = [
            {"release_id": "REL-1", "branch_id": "baseline", "kpi_name": "ULSD Netback CPG", "measure_class": "KPI", "value": 214.50001, "threshold_status": "GREEN"},
            {"release_id": "REL-1", "branch_id": "baseline", "kpi_name": "Margin Capture %", "measure_class": "KPI", "value": None, "threshold_status": "UNRESOLVED"},
        ]
        ok = diff_duckdb_vs_databricks_kpis(duck, dbx_ok)
        self.assertEqual(ok["status"], "PARITY_PASSED")
        self.assertEqual(ok["drift_count"], 0)

        dbx_drift = [
            {"release_id": "REL-1", "branch_id": "baseline", "kpi_name": "ULSD Netback CPG", "measure_class": "KPI", "value": 220.0, "threshold_status": "GREEN"},
            {"release_id": "REL-1", "branch_id": "baseline", "kpi_name": "Margin Capture %", "measure_class": "KPI", "value": 0.0, "threshold_status": "UNRESOLVED"},
        ]
        bad = diff_duckdb_vs_databricks_kpis(duck, dbx_drift)
        self.assertEqual(bad["status"], "PARITY_FAILED")
        self.assertEqual(bad["drift_count"], 2)

        # NaN/Inf values and duplicate keys MUST fail parity rather than silently passing
        nan_row = [{"release_id": "REL-1", "branch_id": "baseline", "kpi_name": "K1", "measure_class": "KPI", "value": float("nan"), "threshold_status": "GREEN"}]
        nan_res = diff_duckdb_vs_databricks_kpis(nan_row, nan_row)
        self.assertEqual(nan_res["status"], "PARITY_FAILED")
        self.assertEqual(nan_res["drifts"][0]["kind"], "NON_FINITE_VALUE")

        dup_res = diff_duckdb_vs_databricks_kpis([duck[0], duck[0]], [duck[0]])
        self.assertEqual(dup_res["status"], "PARITY_FAILED")
        self.assertEqual(dup_res["drifts"][0]["kind"], "DUPLICATE_KEY_IN_DUCKDB")

        # Absent `value` field MUST fail parity rather than counting as matching SQL NULL
        no_val_row = [{"release_id": "REL-1", "branch_id": "baseline", "kpi_name": "K1", "measure_class": "KPI", "threshold_status": "GREEN"}]
        no_val_res = diff_duckdb_vs_databricks_kpis(no_val_row, no_val_row)
        self.assertEqual(no_val_res["status"], "PARITY_FAILED")
        self.assertEqual(no_val_res["drift_count"], 2)

    def test_wp8b_certified_world_export_bundle_schema_and_leak_audit(self):
        pins = [
            {"upstream_repo": "aadehamid/enterprise-performance-model", "pinned_commit": "511a9e8", "adapter_version": "0.1.0", "maturity_status": "PROVISIONAL_COMMIT_PIN"},
            {"upstream_repo": "aadehamid/industrial-context-engineering", "pinned_commit": "1467e92", "adapter_version": "0.1.0", "maturity_status": "PROVISIONAL_COMMIT_PIN"},
            {"upstream_repo": "aadehamid/engineering-drawing-intelligence", "pinned_commit": "12a4a6a", "adapter_version": "0.1.0", "maturity_status": "PROVISIONAL_COMMIT_PIN"},
            {"upstream_repo": "aadehamid/enterprise-context-engine", "pinned_commit": "750b398", "adapter_version": "0.1.0", "maturity_status": "PROVISIONAL_COMMIT_PIN"},
        ]
        clean_bytes = b'{"provenance_class":"SYNTHETIC","status":"OK"}'
        obs_artifacts = {
            "delta_tables": [_ref("kpi_store", "exports/world_bundle/observable/B1/kpi.parquet", clean_bytes)],
            "ice_ot_l0": [_ref("ot_tags", "exports/world_bundle/observable/B1/ot_tags.yaml", clean_bytes)],
            "edi_topology": [_ref("cfg0", "exports/world_bundle/observable/B1/cfg0.json", clean_bytes)],
            "epm_kpi_fixtures": [_ref("epm_kpis", "exports/world_bundle/observable/B1/kpis.json", clean_bytes)],
            "ece_evidence_dossiers": [_ref("dossiers", "exports/world_bundle/observable/B1/dossiers.json", clean_bytes)],
        }
        hid_artifacts = {
            "canonical_world_snapshots": [_ref("world_snap", "evaluation/hidden/world_bundle/B1/snap.json", clean_bytes)],
            "evaluation_scoring_keys": [_ref("score_key", "evaluation/hidden/world_bundle/B1/keys.json", clean_bytes)],
        }

        bundle = assemble_world_export_bundle_v1(
            bundle_id="PPC-BUNDLE-V1-20261128",
            world_version="world-v1.0.0",
            branch_id="baseline",
            root_seed=42,
            adapter_pins=pins,
            observable_artifacts=obs_artifacts,
            hidden_artifacts=hid_artifacts,
            observable_payloads_for_audit={"dossiers.json": clean_bytes},
            schema_path=BUNDLE_SCHEMA,
        )
        self.assertEqual(bundle["qualification_verdict"], "QUALIFIED_PROVISIONAL")
        self.assertEqual(bundle["leak_audit"]["status"], "PASSED")
        self.assertEqual(bundle["leak_audit"]["hidden_fields_found_in_observable"], 0)

        # Leaking hidden truth marker into observable/ MUST fail audit and drop verdict to DRAFT
        leaked = assemble_world_export_bundle_v1(
            bundle_id="PPC-BUNDLE-V1-LEAK",
            world_version="world-v1.0.0",
            branch_id="baseline",
            root_seed=42,
            adapter_pins=pins,
            observable_artifacts=obs_artifacts,
            hidden_artifacts=hid_artifacts,
            observable_payloads_for_audit={"dossiers.json": b'{"ref":"evaluation/hidden/scoring_keys"}'},
            schema_path=BUNDLE_SCHEMA,
        )
        self.assertEqual(leaked["leak_audit"]["status"], "FAILED")
        self.assertEqual(leaked["leak_audit"]["hidden_fields_found_in_observable"], 1)
        self.assertEqual(leaked["qualification_verdict"], "DRAFT")

        # Leaked hidden path inside observable manifest metadata itself MUST ALSO fail audit,
        # even if caller tries to shadow `__observable_manifest__`!
        bad_obs = {
            **obs_artifacts,
            "delta_tables": [_ref("bad_ref", "evaluation/hidden/leak.parquet", clean_bytes)],
        }
        leaked_meta = assemble_world_export_bundle_v1(
            bundle_id="PPC-BUNDLE-V1-META-LEAK",
            world_version="world-v1.0.0",
            branch_id="baseline",
            root_seed=42,
            adapter_pins=pins,
            observable_artifacts=bad_obs,
            hidden_artifacts=hid_artifacts,
            observable_payloads_for_audit={"__observable_manifest__": b"clean", "dossiers.json": clean_bytes},
            schema_path=BUNDLE_SCHEMA,
        )
        self.assertEqual(leaked_meta["leak_audit"]["status"], "FAILED")
        self.assertEqual(leaked_meta["qualification_verdict"], "DRAFT")

        # Real schema hidden-truth field names, UTF-16/UTF-32 (incl. odd-offset), gzip, base64, hex,
        # and invalid-byte-split markers MUST ALL fail audit!
        for case_name, bad_payload in (
            ("schema_field", b'{"canonical_world_snapshots":[{"name":"s0"}],"evaluation_scoring_keys":[]}'),
            ("utf16_leak", "evaluation/hidden/keys.json".encode("utf-16-le")),
            ("utf16_odd_offset", b"\x9c" + "evaluation/hidden/keys.json".encode("utf-16-le")),
            ("utf32_leak", "evaluation/hidden/keys.json".encode("utf-32-le")),
            ("gzip_leak", gzip.compress(b"ref: evaluation/hidden/scoring_keys.json")),
            ("gzip_trailing_pad", gzip.compress(b"evaluation/hidden/keys.json") + b"\x00pad"),
            ("gzip_multimember_pad", gzip.compress(b"no marker here") + gzip.compress(b"evaluation/hidden/keys.json") + b"\x00pad"),
            (
                "gzip_17_members_pad",
                b"".join(gzip.compress(f"pad{i}".encode()) for i in range(16))
                + gzip.compress(b"evaluation/hidden/keys.json")
                + b"\x00pad",
            ),
            (
                "leak_behind_40_sha256_hashes",
                (
                    '{"records":['
                    + ",".join(
                        f'{{"record_sha256":"{hashlib.sha256(str(i).encode()).hexdigest()}"}}'
                        for i in range(40)
                    )
                    + '],"ref":"'
                    + base64.b64encode(base64.b64encode(gzip.compress(b"evaluation/hidden/keys.json"))).decode("ascii")
                    + '"}'
                ).encode("utf-8"),
            ),
            (
                "zlib_corrupt_gap_then_hidden_member",
                zlib.compress(b"clean") + b"GARBAGEHDR" + zlib.compress(b"evaluation/hidden/keys.json"),
            ),
            (
                "gzip_corrupt_crc_trailer",
                gzip.compress(b"evaluation/hidden/keys.json")[:-1]
                + bytes([gzip.compress(b"evaluation/hidden/keys.json")[-1] ^ 0xFF]),
            ),
            (
                "zlib_corrupt_adler_trailer",
                zlib.compress(b"evaluation/hidden/keys.json")[:-1]
                + bytes([zlib.compress(b"evaluation/hidden/keys.json")[-1] ^ 0xFF]),
            ),
            (
                "zlib_corrupt_flg_header",
                b"\x78\x9d" + zlib.compress(b"evaluation/hidden/keys.json")[2:],
            ),
            (
                "zlib_corrupt_cmf_header",
                b"\x79\x9d" + zlib.compress(b"evaluation/hidden/keys.json")[2:],
            ),
            (
                "gzip_truncated_then_garbage_then_clean",
                gzip.compress(b"evaluation/hidden/keys.json" + b"A" * 100)[:40]
                + b"MIDGARBAGE"
                + gzip.compress(b"all clean here"),
            ),
            (
                "gzip_truncated_then_bogus_gzip_header",
                gzip.compress(b"evaluation/hidden/keys.json" + b"A" * 100)[:40]
                + b"\x1f\x8b\x08\x00"
                + b"\x00" * 5
                + b"junknotstream",
            ),
            (
                "zlib_bomb_exceeding_budget_fails_closed",
                zlib.compress(b"\x00" * (65 * 1024 * 1024)) + zlib.compress(b"evaluation/hidden/keys.json") + b"\x00pad",
            ),
            ("base64_leak", base64.b64encode(b"evaluation/hidden/score.key")),
            ("base64_urlsafe", base64.urlsafe_b64encode(b"\x01\x9c" + b"hidden_truth" + b"\xff")),
            ("base64_unpadded", base64.b64encode(b"hidden_truth!").rstrip(b"=")),
            ("base64_offset1", b"x" + base64.b64encode(b"evaluation/hidden/keys.json")),
            ("layered_b64_gzip", base64.b64encode(gzip.compress(b"evaluation/hidden/keys.json"))),
            ("layered_hex_gzip", gzip.compress(b"evaluation/hidden/keys.json").hex().encode("ascii")),
            ("layered_gzip_b64", gzip.compress(base64.b64encode(b"evaluation/hidden/keys.json"))),
            ("hex_leak", b"evaluation/hidden/score.key".hex().encode("ascii")),
            ("hex_odd_nibble", b"A" + b"evaluation/hidden/score.key".hex().encode("ascii")),
            ("split_invalid_byte", b"evaluation/\x94hidden/keys.json"),
        ):
            evasion = assemble_world_export_bundle_v1(
                bundle_id=f"PPC-BUNDLE-{case_name}",
                world_version="world-v1.0.0",
                branch_id="baseline",
                root_seed=42,
                adapter_pins=pins,
                observable_artifacts=obs_artifacts,
                hidden_artifacts=hid_artifacts,
                observable_payloads_for_audit={case_name: bad_payload},
                schema_path=BUNDLE_SCHEMA,
            )
            self.assertEqual(evasion["leak_audit"]["status"], "FAILED", case_name)
            self.assertEqual(evasion["qualification_verdict"], "DRAFT", case_name)

        # Finding provenance distinguishes manifest findings from caller payload keys named `__observable_manifest__`
        attr = audit_observable_for_hidden_leaks(
            {"__observable_manifest__": b"evaluation/hidden/x"},
            manifest_json='{"r2_bucket":"pearland-petroleum-corp"}',
        )
        self.assertEqual(attr["findings"][0]["artifact"], "payload:__observable_manifest__")

        # Explicitly pin DECOMPRESSION_BUDGET_EXCEEDED_UNSCANNED marker on budget-exceeding bomb
        bomb_audit = audit_observable_for_hidden_leaks(
            {"bomb.zlib": zlib.compress(b"\x00" * (65 * 1024 * 1024)) + b"\x00pad"}
        )
        self.assertEqual(bomb_audit["leak_audit"]["status"], "FAILED")
        self.assertTrue(
            any(f["marker"] == "DECOMPRESSION_BUDGET_EXCEEDED_UNSCANNED" for f in bomb_audit["findings"])
        )

        # Explicitly pin DECOMPRESSION_ERROR_UNSCANNED as the sole failure signal on a corrupt clean stream
        clean_gz = gzip.compress(b"all clean here")
        corrupt_clean_gz = clean_gz[:-1] + bytes([clean_gz[-1] ^ 0xFF])
        corrupt_clean_audit = audit_observable_for_hidden_leaks({"corrupt_clean.gz": corrupt_clean_gz})
        self.assertEqual(corrupt_clean_audit["leak_audit"]["status"], "FAILED")
        self.assertEqual(
            [f["marker"] for f in corrupt_clean_audit["findings"]],
            ["DECOMPRESSION_ERROR_UNSCANNED"],
        )

        # Verify corrupt zlib CMF/FLG headers both recover the hidden marker and emit DECOMPRESSION_ERROR_UNSCANNED
        for hdr_name, bad_hdr in (
            ("flg", b"\x78\x9d" + zlib.compress(b"evaluation/hidden/keys.json")[2:]),
            ("cmf", b"\x79\x9d" + zlib.compress(b"evaluation/hidden/keys.json")[2:]),
        ):
            corrupt_hdr_audit = audit_observable_for_hidden_leaks({f"bad_{hdr_name}.zlib": bad_hdr})
            self.assertEqual(corrupt_hdr_audit["leak_audit"]["status"], "FAILED", hdr_name)
            hdr_markers = {f["marker"] for f in corrupt_hdr_audit["findings"]}
            self.assertIn("DECOMPRESSION_ERROR_UNSCANNED", hdr_markers, hdr_name)
            self.assertIn("evaluation/hidden", hdr_markers, hdr_name)

        # Corrupt zlib header PLUS corrupted body byte MUST fail closed both unwrapped AND base64/hex-wrapped
        double_corrupt = bytearray(zlib.compress(b"evaluation/hidden/keys.json"))
        double_corrupt[0] = 0x79
        double_corrupt[2] ^= 0xFF
        double_bytes = bytes(double_corrupt)
        for wrap_name, wrapped in (
            ("unwrapped", double_bytes),
            ("b64_wrapped", base64.b64encode(double_bytes)),
            ("hex_wrapped", double_bytes.hex().encode("ascii")),
        ):
            double_audit = audit_observable_for_hidden_leaks({f"double_{wrap_name}.zlib": wrapped})
            self.assertEqual(double_audit["leak_audit"]["status"], "FAILED", wrap_name)
            self.assertTrue(
                any(f["marker"] == "DECOMPRESSION_ERROR_UNSCANNED" for f in double_audit["findings"]),
                (wrap_name, double_audit["findings"]),
            )

        # Clean base64-wrapped zlib/gzip, small-window RFC 1950 zlib, raw-deflate, UTF-16/32, and ASCII MUST pass
        cobj = zlib.compressobj(9, zlib.DEFLATED, 8)
        small_win_zlib = cobj.compress(b"clean refinery operational summary") + cobj.flush()
        raw_deflate_clean = zlib.compress(b"small text")[2:-4]
        for clean_name, clean_payload in (
            ("b64_zlib_clean", base64.b64encode(zlib.compress(b"small text"))),
            ("b64_gzip_clean", base64.b64encode(gzip.compress(b"small text"))),
            ("small_win_zlib_clean", small_win_zlib),
            ("raw_deflate_clean", raw_deflate_clean),
            ("utf16le_clean", "clean refinery operational summary".encode("utf-16-le")),
            ("utf16be_clean", "clean refinery operational summary".encode("utf-16-be")),
            ("utf32le_clean", "clean refinery operational summary".encode("utf-32-le")),
            ("alnum_word_clean", b"operationalreport12345678"),
            ("alnum_24_clean", b"operationalreport1234567"),
        ):
            clean_res = audit_observable_for_hidden_leaks({clean_name: clean_payload})
            self.assertEqual(clean_res["leak_audit"]["status"], "PASSED", (clean_name, clean_res["findings"]))

        # Empty adapter_pins MUST be rejected
        with self.assertRaises(ValueError):
            assemble_world_export_bundle_v1(
                bundle_id="PPC-BUNDLE-EMPTY-PINS",
                world_version="world-v1.0.0",
                branch_id="baseline",
                root_seed=42,
                adapter_pins=[],
                observable_artifacts=obs_artifacts,
                hidden_artifacts=hid_artifacts,
                observable_payloads_for_audit={"dossiers.json": clean_bytes},
                schema_path=BUNDLE_SCHEMA,
            )


if __name__ == "__main__":
    unittest.main()
