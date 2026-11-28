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
from lakehouse.delta.reader_as_of import (
    AccessGrant,
    DeliveryReceipt,
    PublicationRecord,
    ReleaseEvent,
    select_reader_as_of,
)

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
                    published_at_utc="2026-06-15T08:15:00Z",
                ).to_dict(),
                KPIFactRow(
                    release_id="REL-20260615-01",
                    branch_id="baseline",
                    kpi_name="Hydrocracker Throughput",
                    measure_class="OPERATIONAL_METRIC",
                    epm_artifact="ontology/kpi_ontology_class_hierarchy.md",
                    value=30000.0,
                    unit="bbl/day",
                    parent_kpi="ULSD Netback CPG",
                    effective_at_utc="2026-06-15T08:00:00Z",
                    published_at_utc="2026-06-15T08:15:00Z",
                ).to_dict(),
            ]
            r1 = write_delta_table_idempotent(tbl, rows, txn_app_id="ppc_kpi_pub", txn_version=1)
            self.assertEqual(r1["status"], "COMMITTED")
            self.assertEqual(r1["row_count"], 2)

            # Re-running the identical (txnAppId, txnVersion) MUST skip cleanly without duplicating rows
            r2 = write_delta_table_idempotent(tbl, rows, txn_app_id="ppc_kpi_pub", txn_version=1)
            self.assertEqual(r2["status"], "IDEMPOTENT_SKIPPED")

            # Read-only DuckDB query over Delta table returns exact 2 rows (zero duplication)
            queried = query_delta_readonly_duckdb(tbl, "branch_id = 'baseline'")
            self.assertEqual(len(queried), 2)
            by_name = {q["kpi_name"]: q for q in queried}
            self.assertEqual(by_name["Hydrocracker Throughput"]["parent_kpi"], "ULSD Netback CPG")

            # Deterministic SHA-256 digest-verified ReleaseManifest + RETRACTED validation
            man = build_release_manifest(
                release_id="REL-20260615-01",
                branch_id="baseline",
                status="PUBLISHED",
                published_at_utc="2026-06-15T08:15:00Z",
                cutoff_utc="2026-06-15T08:15:00Z",
                delta_tables={"kpi_store_facts": r1["delta_version"]},
                kpi_rows=rows,
            )
            self.assertEqual(man["kpi_row_count"], 2)
            self.assertEqual(len(man["manifest_sha256"]), 64)
            with self.assertRaises(ValueError):
                build_release_manifest(
                    release_id="REL-20260615-01",
                    branch_id="baseline",
                    status="RETRACTED",
                    published_at_utc="2026-06-15T11:00:00Z",
                    cutoff_utc="2026-06-15T11:00:00Z",
                    delta_tables={"kpi_store_facts": r1["delta_version"]},
                    kpi_rows=rows,
                    retraction_reason=None,
                )

    def test_info001_reader_as_of_receipts_grants_ordinals_offsets_and_l1_x1_retraction_cutoff(self):
        pubs = [
            PublicationRecord(
                publication_id="S2-P1",
                subject_key="LOT:CRUDE-2026-009",
                branch_id="baseline",
                release_id="S2-L1",
                supersession_ordinal=1,
                effective_at_utc="2026-06-15T08:00:00Z",
                recorded_at_utc="2026-06-15T09:00:00Z",
                published_at_utc="2026-06-15T09:30:00Z",
                allowed_roles=("PLANNER", "OPERATOR"),
                supersedes_publication_id=None,
                payload={"sulfur_wt_pct": 1.60},
            ),
            PublicationRecord(
                publication_id="S2-P2",
                subject_key="LOT:CRUDE-2026-009",
                branch_id="baseline",
                release_id="S2-L2",
                supersession_ordinal=2,
                effective_at_utc="2026-06-15T08:00:00Z",
                recorded_at_utc="2026-06-15T11:20:00Z",
                published_at_utc="2026-06-15T11:30:00Z",
                allowed_roles=("PLANNER",),
                supersedes_publication_id="S2-P1",
                payload={"sulfur_wt_pct": 2.45},
            ),
            # Backdated publication (recorded 15:00 > published 09:30): MUST be ineligible at 10:00
            PublicationRecord(
                publication_id="BACKDATED-1",
                subject_key="LOT:BACKDATED",
                branch_id="baseline",
                release_id="S2-L1",
                supersession_ordinal=1,
                effective_at_utc="2026-06-15T08:00:00Z",
                recorded_at_utc="2026-06-15T15:00:00Z",
                published_at_utc="2026-06-15T09:30:00Z",
                allowed_roles=("PLANNER",),
                supersedes_publication_id=None,
                payload={"sulfur_wt_pct": 9.99},
            ),
        ]
        release_events = [
            ReleaseEvent(
                release_id="S2-L1",
                status="PUBLISHED",
                published_at_utc="2026-06-15T09:30:00Z",
                delivered_at_utc="2026-06-15T09:30:00Z",
                authorized_at_utc="2026-06-15T09:30:00Z",
            ),
            # Retraction X1 effective only once published (11:00), authorized (11:05), AND delivered (11:15)
            ReleaseEvent(
                release_id="S2-L1",
                status="RETRACTED",
                published_at_utc="2026-06-15T11:00:00Z",
                authorized_at_utc="2026-06-15T11:05:00Z",
                delivered_at_utc="2026-06-15T11:15:00Z",
            ),
            ReleaseEvent(
                release_id="S2-L2",
                status="PUBLISHED",
                published_at_utc="2026-06-15T11:30:00Z",
                delivered_at_utc="2026-06-15T11:30:00Z",
                authorized_at_utc="2026-06-15T11:30:00Z",
            ),
        ]
        receipts = [
            DeliveryReceipt("S2-P1", "PLANNER", "portal", "2026-06-15T09:31:00Z"),
            DeliveryReceipt("S2-P1", "OPERATOR", "portal", "2026-06-15T09:31:00Z"),
            DeliveryReceipt("S2-P2", "PLANNER", "portal", "2026-06-15T11:31:00Z"),
            DeliveryReceipt("BACKDATED-1", "PLANNER", "portal", "2026-06-15T09:31:00Z"),
        ]
        grants = [
            AccessGrant("PLANNER", "portal", "operations", "2026-06-15T00:00:00Z", None, "ALLOW"),
            AccessGrant("OPERATOR", "portal", "operations", "2026-06-15T00:00:00Z", None, "ALLOW"),
        ]

        # 1. Unknown subject -> UNKNOWN (true epistemic gap, P2)
        unk = select_reader_as_of(
            subject_key="LOT:NONEXISTENT",
            branch_id="baseline",
            reader_role="PLANNER",
            reader_cutoff_utc="2026-06-15T10:00:00Z",
            publications=pubs,
            release_events=release_events,
            receipts=receipts,
            grants=grants,
        )
        self.assertEqual(unk["status"], "UNKNOWN")

        # 2. DATA-001 §2 L1/X1 cutoff-scoped retraction:
        # At 10:00 AND at 11:14 (before retraction delivery at 11:15), replay RETAINS S2-P1!
        for cutoff in ("2026-06-15T10:00:00Z", "2026-06-15T11:14:00Z"):
            retained = select_reader_as_of(
                subject_key="LOT:CRUDE-2026-009",
                branch_id="baseline",
                reader_role="PLANNER",
                reader_cutoff_utc=cutoff,
                publications=pubs,
                release_events=release_events,
                receipts=receipts,
                grants=grants,
            )
            self.assertEqual(retained["status"], "RESOLVED")
            self.assertEqual(retained["publication_id"], "S2-P1")

        # At 11:15 (retraction published, authorized, AND delivered; S2-P2 not yet published), returns UNRESOLVED
        retracted = select_reader_as_of(
            subject_key="LOT:CRUDE-2026-009",
            branch_id="baseline",
            reader_role="PLANNER",
            reader_cutoff_utc="2026-06-15T11:15:00Z",
            publications=pubs,
            release_events=release_events,
            receipts=receipts,
            grants=grants,
        )
        self.assertEqual(retracted["status"], "UNRESOLVED")
        self.assertIsNone(retracted["payload"])

        # At 12:00 (and using timezone-offset ISO string 07:00-05:00 == 12:00Z), PLANNER sees S2-P2
        restated = select_reader_as_of(
            subject_key="LOT:CRUDE-2026-009",
            branch_id="baseline",
            reader_role="PLANNER",
            reader_cutoff_utc="2026-06-15T07:00:00-05:00",
            publications=pubs,
            release_events=release_events,
            receipts=receipts,
            grants=grants,
        )
        self.assertEqual(restated["status"], "RESOLVED")
        self.assertEqual(restated["publication_id"], "S2-P2")
        self.assertEqual(restated["payload"]["sulfur_wt_pct"], 2.45)

        # 3. Backdated publication (recorded_at 15:00 > cutoff 10:00) MUST return UNRESOLVED
        backdated = select_reader_as_of(
            subject_key="LOT:BACKDATED",
            branch_id="baseline",
            reader_role="PLANNER",
            reader_cutoff_utc="2026-06-15T10:00:00Z",
            publications=pubs,
            release_events=release_events,
            receipts=receipts,
            grants=grants,
        )
        self.assertEqual(backdated["status"], "UNRESOLVED")

        # 4. Missing receipt OR DENY grant OR wrong purpose OR unmapped release MUST fail closed (UNRESOLVED)
        no_rcpt = select_reader_as_of(
            subject_key="LOT:CRUDE-2026-009",
            branch_id="baseline",
            reader_role="PLANNER",
            reader_cutoff_utc="2026-06-15T10:00:00Z",
            publications=pubs,
            release_events=release_events,
            receipts=[],
            grants=grants,
        )
        self.assertEqual(no_rcpt["status"], "UNRESOLVED")

        denied = select_reader_as_of(
            subject_key="LOT:CRUDE-2026-009",
            branch_id="baseline",
            reader_role="PLANNER",
            reader_cutoff_utc="2026-06-15T10:00:00Z",
            publications=pubs,
            release_events=release_events,
            receipts=receipts,
            grants=grants + [AccessGrant("PLANNER", "portal", "operations", "2026-06-15T00:00:00Z", None, "DENY")],
        )
        self.assertEqual(denied["status"], "UNRESOLVED")

        unmapped_rel = select_reader_as_of(
            subject_key="LOT:CRUDE-2026-009",
            branch_id="baseline",
            reader_role="PLANNER",
            reader_cutoff_utc="2026-06-15T10:00:00Z",
            publications=pubs,
            release_events=[],
            receipts=receipts,
            grants=grants,
        )
        self.assertEqual(unmapped_rel["status"], "UNRESOLVED")

        # 5. Forked successor (two publications superseding S2-P1) MUST be rejected rather than guessed
        forked_pubs = [
            pubs[0],
            pubs[1],
            PublicationRecord(
                publication_id="S2-P2-FORK",
                subject_key="LOT:CRUDE-2026-009",
                branch_id="baseline",
                release_id="S2-L2",
                supersession_ordinal=2,
                effective_at_utc="2026-06-15T08:00:00Z",
                recorded_at_utc="2026-06-15T11:25:00Z",
                published_at_utc="2026-06-15T11:35:00Z",
                allowed_roles=("PLANNER",),
                supersedes_publication_id="S2-P1",
                payload={"sulfur_wt_pct": 2.99},
            ),
        ]
        forked = select_reader_as_of(
            subject_key="LOT:CRUDE-2026-009",
            branch_id="baseline",
            reader_role="PLANNER",
            reader_cutoff_utc="2026-06-15T12:00:00Z",
            publications=forked_pubs,
            release_events=release_events,
            receipts=receipts,
            grants=grants,
        )
        self.assertEqual(forked["status"], "REJECTED_CHAIN")
        self.assertEqual(forked["reason"], "FORKED_SUCCESSOR")

    def test_rdf_pyshacl_to_neo4j_cypher_projection_and_loss_report(self):
        ttl = REPO_ROOT / "semantic" / "ontology" / "ppc_core.ttl"
        shacl = REPO_ROOT / "semantic" / "shapes" / "ppc_core.shacl.ttl"
        self.assertTrue(ttl.is_file(), f"Missing ontology {ttl}")
        self.assertTrue(shacl.is_file(), f"Missing SHACL shapes {shacl}")

        res1 = validate_and_project_rdf_to_cypher(
            ttl,
            branch_id="baseline",
            snapshot_id="SNAP-20260615-01",
            shacl_path=shacl,
        )
        res2 = validate_and_project_rdf_to_cypher(
            ttl,
            branch_id="baseline",
            snapshot_id="SNAP-20260615-01",
            shacl_path=shacl,
        )
        self.assertTrue(res1["conforms"])
        self.assertGreater(res1["rdf_triple_count"], 20)
        self.assertGreater(res1["lpg_node_count"], 5)
        self.assertEqual(res1["cypher_sha256"], res2["cypher_sha256"])
        self.assertIn("MERGE (snap:GraphSnapshot", res1["cypher_statements"][0])

        # Missing shacl_path MUST raise FileNotFoundError (never silently skip validation)
        with self.assertRaises(FileNotFoundError):
            validate_and_project_rdf_to_cypher(
                ttl,
                branch_id="baseline",
                snapshot_id="SNAP-BAD",
                shacl_path=REPO_ROOT / "semantic" / "shapes" / "does_not_exist.ttl",
            )

        # Non-conforming Turtle ontology MUST fail SHACL validation loudly
        with tempfile.TemporaryDirectory(prefix="ppc-wp3-shacl-") as tmp:
            bad_ttl = Path(tmp) / "bad.ttl"
            bad_ttl.write_text(
                "@prefix ppc: <https://ppc.local/ontology/core#> .\n"
                "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n"
                "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n"
                "ppc:BadSite a ppc:Site ;\n"
                "    ppc:siteId \"SITE-BAD\"^^xsd:string ;\n"
                "    rdfs:label \"Bad Site\" ;\n"
                "    ppc:provenanceClass \"NOT_A_VALID_CLASS\"^^xsd:string .\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                validate_and_project_rdf_to_cypher(
                    bad_ttl,
                    branch_id="baseline",
                    snapshot_id="SNAP-BAD",
                    shacl_path=shacl,
                )


if __name__ == "__main__":
    unittest.main()
