#!/usr/bin/env python3
"""Tests for WP-8A DuckDB-vs-Databricks KPI parity and WP-8B Certified WorldExportBundle v1."""
from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

from evaluations.world_export_bundle_v1 import assemble_world_export_bundle_v1
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


if __name__ == "__main__":
    unittest.main()
