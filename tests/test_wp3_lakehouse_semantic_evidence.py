#!/usr/bin/env python3
"""Independent verification tests for WP-3 Delta Lake, Tall KPI Store, Neo4j RDF Projection, and INFO-001 Reader-as-of."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from graph.neo4j.projection_loader import validate_and_project_rdf_to_cypher
from lakehouse.delta.publisher import (
    KPIFactRow,
    build_release_manifest,
    query_delta_readonly_duckdb,
    write_delta_table_idempotent,
)
from lakehouse.delta.reader_as_of import PublicationRecord, select_reader_as_of

REPO_ROOT = Path(__file__).resolve().parents[1]


class TestWP3LakehouseSemanticEvidence(unittest.TestCase):
    def test_delta_rs_idempotent_write_duckdb_readonly_and_t100_release_manifest(self):
        with tempfile.TemporaryDirectory(prefix="ppc-wp3-delta-") as tmp:
            tbl = Path(tmp) / "kpi_store_facts"
            rows = [
                KPIFactRow(
                    release_id="REL-20260615-01",
                    branch_id="baseline",
                    kpi_name="ULSD Netback CPG",
                    measure_class="KPI",
                    epm_artifact="ontology/kpi_ontology_class_hierarchy.md",
                    value=214.5,
                    unit="cents/gal",
                    parent_kpi=None,
                    effective_at_utc="2026-06-15T08:00:00Z",
                    published_at_utc="2026-06-15T09:50:00Z",
                ).to_dict(),
                KPIFactRow(
                    release_id="REL-20260615-01",
                    branch_id="baseline",
                    kpi_name="HCU Feed Rate",
                    measure_class="OPERATIONAL_METRIC",
                    epm_artifact="ontology/kpi_ontology_class_hierarchy.md",
                    value=30000.0,
                    unit="bbl/day",
                    parent_kpi="ULSD Netback CPG",
                    effective_at_utc="2026-06-15T08:00:00Z",
                    published_at_utc="2026-06-15T09:50:00Z",
                ).to_dict(),
                KPIFactRow(
                    release_id="REL-20260615-01",
                    branch_id="baseline",
                    kpi_name="USGC ULSD Spot",
                    measure_class="MARKET_INDICATOR",
                    epm_artifact="ontology/kpi_ontology_class_hierarchy.md",
                    value=1.999,
                    unit="USD/gal",
                    parent_kpi="ULSD Netback CPG",
                    effective_at_utc="2026-06-15T08:00:00Z",
                    published_at_utc="2026-06-15T09:50:00Z",
                    provenance_class="OBSERVED",
                ).to_dict(),
            ]

            r1 = write_delta_table_idempotent(tbl, rows, txn_app_id="ppc-kpi-baseline", txn_version=1)
            self.assertEqual(r1["status"], "COMMITTED")
            self.assertEqual(r1["row_count"], 3)

            # Re-running exact same (txnAppId, txnVersion) skips idempotently (PO-03)
            r2 = write_delta_table_idempotent(tbl, rows, txn_app_id="ppc-kpi-baseline", txn_version=1)
            self.assertEqual(r2["status"], "IDEMPOTENT_SKIPPED")

            # DuckDB read-only query sees exactly 3 rows and preserves measure_class decomposition
            queried = query_delta_readonly_duckdb(tbl, "branch_id = 'baseline'")
            self.assertEqual(len(queried), 3)
            self.assertEqual({r["measure_class"] for r in queried}, {"KPI", "OPERATIONAL_METRIC", "MARKET_INDICATOR"})

            # Signed ReleaseManifest and RETRACTED (L1/X1) validation
            man = build_release_manifest(
                release_id="REL-20260615-01",
                branch_id="baseline",
                status="PUBLISHED",
                published_at_utc="2026-06-15T09:50:00Z",
                cutoff_utc="2026-06-15T09:45:00Z",
                delta_tables={"kpi_store_facts": r1["delta_version"]},
                kpi_rows=rows,
            )
            self.assertEqual(len(man["manifest_sha256"]), 64)
            with self.assertRaises(ValueError):
                build_release_manifest(
                    release_id="REL-BAD",
                    branch_id="baseline",
                    status="RETRACTED",
                    published_at_utc="2026-06-15T10:00:00Z",
                    cutoff_utc="2026-06-15T09:45:00Z",
                    delta_tables={"kpi_store_facts": 0},
                    kpi_rows=rows,
                    retraction_reason=None,
                )

    def test_info001_reader_as_of_p0_p1_p2_and_data001_l1_x1_retraction(self):
        pubs = [
            PublicationRecord(
                publication_id="S2-P1",
                subject_key="ASSAY:S2-M1",
                branch_id="baseline",
                release_id="S2-L1",
                effective_at_utc="2026-06-15T09:00:00Z",
                recorded_at_utc="2026-06-15T09:20:00Z",
                published_at_utc="2026-06-15T09:30:00Z",
                allowed_roles=("planner", "analyst"),
                supersedes_publication_id=None,
                payload={"disposition": "QUALITY_HOLD", "sulfur_ppmw": 18.2},
            ),
            PublicationRecord(
                publication_id="S2-P2",
                subject_key="ASSAY:S2-M1",
                branch_id="baseline",
                release_id="S2-L2",
                effective_at_utc="2026-06-15T12:00:00Z",
                recorded_at_utc="2026-06-15T12:30:00Z",
                published_at_utc="2026-06-15T13:00:00Z",
                allowed_roles=("planner", "analyst"),
                supersedes_publication_id="S2-P1",
                payload={"disposition": "RELEASE", "sulfur_ppmw": 11.4},
            ),
            PublicationRecord(
                publication_id="SECRET-P1",
                subject_key="CONTRACT:CONFIDENTIAL",
                branch_id="baseline",
                release_id="S2-L1",
                effective_at_utc="2026-06-15T08:00:00Z",
                recorded_at_utc="2026-06-15T08:05:00Z",
                published_at_utc="2026-06-15T08:10:00Z",
                allowed_roles=("executive",),
                supersedes_publication_id=None,
                payload={"margin_secret": 999999},
            ),
        ]
        rel_status = {"S2-L1": "PUBLISHED", "S2-L2": "PUBLISHED"}

        # P0: 10:00 replay sees S2-P1 and NEVER leaks 13:00 S2-P2
        at_1000 = select_reader_as_of(
            subject_key="ASSAY:S2-M1",
            branch_id="baseline",
            reader_role="planner",
            reader_cutoff_utc="2026-06-15T10:00:00Z",
            publications=pubs,
            release_statuses=rel_status,
        )
        self.assertEqual(at_1000["status"], "RESOLVED")
        self.assertEqual(at_1000["publication_id"], "S2-P1")
        self.assertEqual(at_1000["payload"]["disposition"], "QUALITY_HOLD")

        # 13:15 sees corrected S2-P2
        at_1315 = select_reader_as_of(
            subject_key="ASSAY:S2-M1",
            branch_id="baseline",
            reader_role="planner",
            reader_cutoff_utc="2026-06-15T13:15:00Z",
            publications=pubs,
            release_statuses=rel_status,
        )
        self.assertEqual(at_1315["publication_id"], "S2-P2")

        # P1: Unauthorized role gets opaque UNRESOLVED with zero payload disclosure
        restricted = select_reader_as_of(
            subject_key="CONTRACT:CONFIDENTIAL",
            branch_id="baseline",
            reader_role="planner",
            reader_cutoff_utc="2026-06-15T10:00:00Z",
            publications=pubs,
            release_statuses=rel_status,
        )
        self.assertEqual(restricted["status"], "UNRESOLVED")
        self.assertIsNone(restricted["payload"])

        # P2: True epistemic gap (never published on branch) returns UNKNOWN
        epistemic_gap = select_reader_as_of(
            subject_key="ASSAY:NONEXISTENT",
            branch_id="baseline",
            reader_role="planner",
            reader_cutoff_utc="2026-06-15T10:00:00Z",
            publications=pubs,
            release_statuses=rel_status,
        )
        self.assertEqual(epistemic_gap["status"], "UNKNOWN")

        # L1/X1: If S2-L1 is RETRACTED, 10:00 query returns UNRESOLVED (cannot fabricate or peek at 13:00 S2-L2)
        retracted = select_reader_as_of(
            subject_key="ASSAY:S2-M1",
            branch_id="baseline",
            reader_role="planner",
            reader_cutoff_utc="2026-06-15T10:00:00Z",
            publications=pubs,
            release_statuses={"S2-L1": "RETRACTED", "S2-L2": "PUBLISHED"},
        )
        self.assertEqual(retracted["status"], "UNRESOLVED")

    def test_rdf_pyshacl_to_neo4j_cypher_projection_and_loss_report(self):
        ttl = REPO_ROOT / "semantic" / "ontology" / "ppc_core.ttl"
        shacl = REPO_ROOT / "semantic" / "shapes" / "ppc_core_shapes.ttl"
        res = validate_and_project_rdf_to_cypher(
            ttl,
            branch_id="baseline",
            snapshot_id="SNAP-001",
            shacl_path=shacl if shacl.exists() else None,
        )
        self.assertTrue(res["conforms"])
        self.assertGreater(res["rdf_triple_count"], 0)
        self.assertGreater(res["lpg_node_count"], 0)
        self.assertTrue(any("GraphSnapshot" in stmt for stmt in res["cypher_statements"]))
        # Deterministic replay produces identical Cypher SHA-256
        res2 = validate_and_project_rdf_to_cypher(
            ttl,
            branch_id="baseline",
            snapshot_id="SNAP-001",
            shacl_path=shacl if shacl.exists() else None,
        )
        self.assertEqual(res["cypher_sha256"], res2["cypher_sha256"])


if __name__ == "__main__":
    unittest.main()
