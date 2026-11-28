#!/usr/bin/env python3
"""WP-6 Scenario B Vertical Slice: Crude-Quality Rejection & Delayed Lab Correction (UC-2, SCENARIO-001 §3).

Exercises the real merged WP-1b, WP-1c, WP-2, and WP-3 components end-to-end across the
canonical S2-* timeline for segregated hold tank TK-101H:
- WP-1b (`fixtures/golden/refinery_a_design_basis.yaml`): authoritative TK-101H bounds & SG (0..150,000 bbl, SG 0.871).
- WP-1c (`generators/equations.py`): EQ-02 exact tank mass balance for the 500 bbl receipt S2-M1.
- WP-2 (`source-systems/refinery/outbox_store.py`, `integration/outbox_inbox_service.py`):
  - Atomic source DB + outbox commit of S2-M1 (08:00 effective / 08:05 recorded).
  - Crash Point 1 (`INT-RETRY-01`) duplicate redelivery -> IDEMPOTENT_DUPLICATE (500 bbl, never 1000 bbl).
  - Tampered-digest redelivery -> CONFLICT_QUARANTINED (PENDING_IDENTITY_STEWARD).
  - Idempotent Delta publication from Silver staging via `publish_staging_to_delta_idempotent`.
- WP-3 (`lakehouse/delta/publisher.py`, `lakehouse/delta/reader_as_of.py`):
  - Delta Lake idempotent writes + read-only DuckDB verification of S2-M1 movement row.
  - Analytical release manifests S2-L1 (recorded 09:40, published 09:45, delivered 09:50) and
    S2-L2 (recorded 13:05, published 13:10, delivered 13:15) carrying registered EPM KPI rows
    (`Inventory Days of Cover`, `ontology/kpi_ontology_class_hierarchy.md`).
  - INFO-001 §3 `select_reader_as_of` with AccessGrant (`08:00`, `workspace`, `crude-disposition`),
    DeliveryReceipt, ReleaseEvent, and PublicationRecord matching `SCENARIO-001 §3` exactly:
    - `S2-P1` / `S2-R1`: effective 08:00, recorded 09:00, published 09:20, delivered 09:30 (`QUALITY_HOLD`).
    - `S2-L1`: recorded 09:40, published 09:45, delivered 09:50.
    - `S2-D1`: 10:00 UTC planner decision cutoff (sees `S2-P1` + `S2-L1` ONLY).
    - `S2-P2` / `S2-R2`: effective 08:00, recorded 12:00, published 12:30, delivered 13:00 (`RELEASE`).
    - `S2-L2`: recorded 13:05, published 13:10, delivered 13:15.
    - Boundary checks at 09:25 (pre-receipt `UNRESOLVED`), 09:47 (assay `S2-P1`/`QUALITY_HOLD` eligible at 09:30,
      analytical release `S2-L1` still `UNRESOLVED` until 09:50), 13:12 (assay `S2-P2`/`RELEASE` eligible at 13:00,
      analytical release still `S2-L1` until `S2-L2` delivery at 13:15), 10:00 replay (zero leakage of `S2-P2`/`S2-L2`),
      and unauthorized `ExternalGuest` (opaque `UNRESOLVED`, `payload: None`).
"""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

from generators import equations as eq
from integration.outbox_inbox_service import AtomicStagingInboxService
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
DESIGN_BASIS_PATH = REPO_ROOT / "fixtures" / "golden" / "refinery_a_design_basis.yaml"


def _load_outbox_store_module() -> Any:
    mod_name = "ppc_wp6_outbox_store"
    if mod_name in sys.modules:
        return sys.modules[mod_name]
    path = REPO_ROOT / "source-systems" / "refinery" / "outbox_store.py"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load outbox_store module from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_tk101h_spec() -> dict[str, Any]:
    basis = yaml.safe_load(DESIGN_BASIS_PATH.read_text(encoding="utf-8"))
    for tank in basis["tanks"]:
        if tank["id"] == "TK-101H":
            return dict(tank)
    raise KeyError("TK-101H not found in fixtures/golden/refinery_a_design_basis.yaml")


def run_scenario_b_walkthrough(work_dir: str | Path | None = None) -> dict[str, Any]:
    """Execute deterministic Scenario B S2-* vertical slice across WP-1b/1c/2/3 and return RunEvidence."""
    outbox_mod = _load_outbox_store_module()
    tk_spec = _load_tk101h_spec()
    sg = float(tk_spec["ref_sg_60_60"])
    min_mass_kg = eq.volume_bbl_to_mass_kg(float(tk_spec["working_min_bbl"]), sg)
    max_mass_kg = eq.volume_bbl_to_mass_kg(float(tk_spec["working_max_bbl"]), sg)
    open_mass_kg = eq.volume_bbl_to_mass_kg(float(tk_spec["initial_bbl"]), sg)

    tmp_ctx = tempfile.TemporaryDirectory(prefix="ppc-wp6-") if work_dir is None else None
    base_dir = Path(tmp_ctx.name) if tmp_ctx is not None else Path(work_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    try:
        src_store = outbox_mod.TransactionalOutboxSourceStore(base_dir / "logistics_source.db", "logistics_sqlite")
        inbox = AtomicStagingInboxService(base_dir / "silver_inbox.db")
        delta_movements_dir = base_dir / "delta" / "tank_movements"
        delta_kpi_dir = base_dir / "delta" / "kpi_facts"
        try:
            # 1. Atomic source DB + outbox commit for S2-M1 (500 bbl receipt into TK-101H)
            src_store.commit_with_outbox(
                branch_id="scn-b-s2",
                partition_key="tank:TK-101H",
                source_tx_id="TX-S2-M1",
                event_id="S2-M1",
                delivery_key="logistics_sqlite:scn-b-s2:tank:TK-101H:S2-M1:v1",
                native_entity_key="TK-101H",
                source_revision=1,
                event_type="CRUDE_RECEIPT_HOLD",
                effective_at_utc="2026-06-15T08:00:00Z",
                recorded_at_utc="2026-06-15T08:05:00Z",
                payload={"movement_id": "S2-M1", "tank_id": "TK-101H", "receipt_bbl": 500.0},
            )
            pending_outbox = src_store.fetch_pending_outbox()
            if len(pending_outbox) != 1:
                raise RuntimeError(f"Expected 1 pending outbox event, got {len(pending_outbox)}")
            m1_event = asdict(pending_outbox[0])
            m1_event["published_at_utc"] = "2026-06-15T08:05:00Z"

            # First delivery simulates Crash Point 1 (committed atomically before ack), then redelivery (INT-RETRY-01)
            crash_point_1_caught = False
            try:
                inbox.consume_event(m1_event, inject_crash_after_staging_before_ack=True)
            except RuntimeError as exc:
                if "INJECTED_CRASH_POINT_1" not in str(exc):
                    raise
                crash_point_1_caught = True
            m1_first_status = "APPLIED" if crash_point_1_caught and inbox.staging_count() == 1 else "UNEXPECTED"

            m1_dup_outcome = inbox.consume_event(m1_event)

            tampered_payload = json.dumps(
                {"movement_id": "S2-M1", "tank_id": "TK-101H", "receipt_bbl": 999.0},
                sort_keys=True,
                separators=(",", ":"),
            )
            tampered_event = {
                **m1_event,
                "payload_json": tampered_payload,
                "payload_digest": hashlib.sha256(tampered_payload.encode("utf-8")).hexdigest(),
            }
            m1_conflict_outcome = inbox.consume_event(tampered_event)

            # Publish Silver staging to Delta Lake idempotently and verify via read-only DuckDB
            def _commit_to_delta(*, table_name: str, rows: list[dict[str, Any]], txn_app_id: str, txn_version: int) -> None:
                delta_rows = [
                    {
                        "delivery_key": str(r["delivery_key"]),
                        "event_id": str(r["event_id"]),
                        "branch_id": str(r["branch_id"]),
                        "tank_id": str(json.loads(r["payload_json"])["tank_id"]),
                        "receipt_bbl": float(json.loads(r["payload_json"])["receipt_bbl"]),
                        "effective_at_utc": str(r["effective_at_utc"]),
                        "recorded_at_utc": str(r["recorded_at_utc"]),
                        "provenance_class": str(r["provenance_class"]),
                    }
                    for r in rows
                ]
                write_delta_table_idempotent(
                    delta_movements_dir,
                    delta_rows,
                    txn_app_id=txn_app_id,
                    txn_version=txn_version,
                )

            pub_res = inbox.publish_staging_to_delta_idempotent(
                txn_app_id="wp6_scenario_b_movements",
                txn_version=1,
                table_name="tank_movements",
                source_system="logistics_sqlite",
                branch_id="scn-b-s2",
                sink_commit_fn=_commit_to_delta,
            )
            pub_retry = inbox.publish_staging_to_delta_idempotent(
                txn_app_id="wp6_scenario_b_movements",
                txn_version=1,
                table_name="tank_movements",
                source_system="logistics_sqlite",
                branch_id="scn-b-s2",
                sink_commit_fn=_commit_to_delta,
            )
            delta_movement_rows = query_delta_readonly_duckdb(delta_movements_dir)
            credited_bbl = sum(float(r["receipt_bbl"]) for r in delta_movement_rows)

            # 2. WP-1c EQ-02 physical tank step for the committed 500 bbl receipt into TK-101H over 300s (08:00..08:05)
            receipt_mass_kg = eq.volume_bbl_to_mass_kg(credited_bbl, sg)
            tk_step = eq.step_tank_with_exact_crossing(
                opening_mass_kg=open_mass_kg,
                min_mass_kg=min_mass_kg,
                max_mass_kg=max_mass_kg,
                inflow_rate_kg_s=receipt_mass_kg / 300.0,
                outflow_rate_kg_s=0.0,
                dt_s=300.0,
                loss_rate_kg_s=0.0,
                rule="block",
            )
            tank_tk101h_bbl = eq.mass_kg_to_volume_bbl(tk_step.closing_mass_kg, sg)

            # 3. WP-3 Analytical Release Manifests (S2-L1 & S2-L2) + Delta KPI store using EPM-bound KPI
            # `Inventory Days of Cover` (semantic/mappings/epm_kpi_bindings.yaml, ADR-0060 Q1).
            # At 180,000 bbl/day nominal refinery crude charge, 500 bbl released into available stock adds 500/180000 days.
            nominal_crude_bpd = 180000.0
            kpi_l1 = [
                KPIFactRow(
                    release_id="S2-L1",
                    branch_id="scn-b-s2",
                    kpi_name="Inventory Days of Cover",
                    measure_class="KPI",
                    epm_artifact="ontology/kpi_ontology_class_hierarchy.md",
                    value=0.0,  # LOT-44 held in TK-101H is excluded from available crude cover until quality release
                    unit="days",
                    parent_kpi=None,
                    effective_at_utc="2026-06-15T09:40:00Z",
                    published_at_utc="2026-06-15T09:45:00Z",
                    access_label="OPERATIONS",
                ).to_dict()
            ]
            kpi_l2 = [
                KPIFactRow(
                    release_id="S2-L2",
                    branch_id="scn-b-s2",
                    kpi_name="Inventory Days of Cover",
                    measure_class="KPI",
                    epm_artifact="ontology/kpi_ontology_class_hierarchy.md",
                    value=tank_tk101h_bbl / nominal_crude_bpd,
                    unit="days",
                    parent_kpi=None,
                    effective_at_utc="2026-06-15T13:05:00Z",
                    published_at_utc="2026-06-15T13:10:00Z",
                    access_label="OPERATIONS",
                ).to_dict()
            ]
            kpi_w1 = write_delta_table_idempotent(
                delta_kpi_dir, kpi_l1, txn_app_id="wp6_scenario_b_kpis", txn_version=1
            )
            manifest_l1 = build_release_manifest(
                release_id="S2-L1",
                branch_id="scn-b-s2",
                status="PUBLISHED",
                published_at_utc="2026-06-15T09:45:00Z",
                cutoff_utc="2026-06-15T09:40:00Z",
                delta_tables={"tank_movements": 0, "kpi_facts": int(kpi_w1["delta_version"])},
                kpi_rows=kpi_l1,
            )

            # 4. WP-3 INFO-001 §3 reader-as-of selection across the exact SCENARIO-001 §3 S2-* timeline
            grants = [
                AccessGrant(
                    role="Planner",
                    channel="workspace",
                    purpose="crude-disposition",
                    valid_from_utc="2026-06-15T08:00:00Z",
                    recorded_at_utc="2026-06-15T08:00:00Z",
                    effect="ALLOW",
                ),
                AccessGrant(
                    role="Analyst",
                    channel="workspace",
                    purpose="crude-disposition",
                    valid_from_utc="2026-06-15T08:00:00Z",
                    recorded_at_utc="2026-06-15T08:00:00Z",
                    effect="ALLOW",
                ),
            ]
            pub_p1 = PublicationRecord(
                publication_id="S2-P1",
                subject_key="assay:TK-101H:LOT-44",
                branch_id="scn-b-s2",
                release_id="REL-S2-P1",
                supersession_ordinal=1,
                effective_at_utc="2026-06-15T08:00:00Z",
                recorded_at_utc="2026-06-15T09:00:00Z",
                published_at_utc="2026-06-15T09:20:00Z",
                allowed_roles=("Planner", "Analyst"),
                supersedes_publication_id=None,
                payload={"lot_id": "LOT-44", "tank_id": "TK-101H", "disposition": "QUALITY_HOLD", "sulfur_wt_pct": 3.45},
            )
            receipt_r1 = DeliveryReceipt(
                publication_id="S2-P1",
                recipient_role="Planner",
                channel="workspace",
                delivered_at_utc="2026-06-15T09:30:00Z",
            )
            rel_p1 = ReleaseEvent(
                release_id="REL-S2-P1",
                status="PUBLISHED",
                published_at_utc="2026-06-15T09:20:00Z",
                delivered_at_utc="2026-06-15T09:30:00Z",
                authorized_at_utc="2026-06-15T09:20:00Z",
            )

            pub_l1 = PublicationRecord(
                publication_id="S2-L1",
                subject_key="release:TK-101H:LOT-44",
                branch_id="scn-b-s2",
                release_id="S2-L1",
                supersession_ordinal=1,
                effective_at_utc="2026-06-15T09:40:00Z",
                recorded_at_utc="2026-06-15T09:40:00Z",
                published_at_utc="2026-06-15T09:45:00Z",
                allowed_roles=("Planner", "Analyst"),
                supersedes_publication_id=None,
                payload={"release_id": "S2-L1", "manifest_sha256": manifest_l1["manifest_sha256"], "lot_disposition": "QUALITY_HOLD"},
            )
            receipt_l1 = DeliveryReceipt(
                publication_id="S2-L1",
                recipient_role="Planner",
                channel="workspace",
                delivered_at_utc="2026-06-15T09:50:00Z",
            )
            rel_l1 = ReleaseEvent(
                release_id="S2-L1",
                status="PUBLISHED",
                published_at_utc="2026-06-15T09:45:00Z",
                delivered_at_utc="2026-06-15T09:50:00Z",
                authorized_at_utc="2026-06-15T09:45:00Z",
            )

            def _query_view(
                role: str,
                cutoff_utc: str,
                pubs: list[PublicationRecord],
                rels: list[ReleaseEvent],
                rcpts: list[DeliveryReceipt],
            ) -> dict[str, Any]:
                assay = select_reader_as_of(
                    subject_key="assay:TK-101H:LOT-44",
                    branch_id="scn-b-s2",
                    reader_role=role,
                    reader_cutoff_utc=cutoff_utc,
                    publications=pubs,
                    release_events=rels,
                    receipts=rcpts,
                    grants=grants,
                    channel="workspace",
                    purpose="crude-disposition",
                )
                release = select_reader_as_of(
                    subject_key="release:TK-101H:LOT-44",
                    branch_id="scn-b-s2",
                    reader_role=role,
                    reader_cutoff_utc=cutoff_utc,
                    publications=pubs,
                    release_events=rels,
                    receipts=rcpts,
                    grants=grants,
                    channel="workspace",
                    purpose="crude-disposition",
                )
                return {
                    "status": assay["status"],
                    "publication_id": assay["publication_id"],
                    "effective_at_utc": assay.get("effective_at_utc"),
                    "published_at_utc": assay.get("published_at_utc"),
                    "payload": assay["payload"],
                    "release_status": release["status"],
                    "release_id": release["publication_id"],
                    "release_payload": release["payload"],
                }

            initial_pubs = [pub_p1, pub_l1]
            initial_rels = [rel_p1, rel_l1]
            initial_receipts = [receipt_r1, receipt_l1]

            # Sharp SCENARIO-001 §3 boundary probes with independent assay vs analytical-release clocks:
            # 09:25 -> assay UNRESOLVED (S2-R1 at 09:30), release UNRESOLVED (S2-L1 at 09:50)
            pre_receipt_0925 = _query_view("Planner", "2026-06-15T09:25:00Z", initial_pubs, initial_rels, initial_receipts)
            # 09:47 -> assay RESOLVED as S2-P1/QUALITY_HOLD (09:30 <= 09:47), release STILL UNRESOLVED (09:50 > 09:47)
            pre_release_delivery_0947 = _query_view(
                "Planner", "2026-06-15T09:47:00Z", initial_pubs, initial_rels, initial_receipts
            )

            # 10:00 UTC planner decision S2-D1 BEFORE S2-P2/S2-L2 exist -> S2-P1 + S2-L1
            decision_s2_d1_initial = _query_view(
                "Planner", "2026-06-15T10:00:00Z", initial_pubs, initial_rels, initial_receipts
            )

            # 12:00..13:15 delayed passing lab correction S2-P2 (receipt S2-R2 at 13:00) + restatement S2-L2 (13:15)
            kpi_w2 = write_delta_table_idempotent(
                delta_kpi_dir, kpi_l2, txn_app_id="wp6_scenario_b_kpis", txn_version=2
            )
            manifest_l2 = build_release_manifest(
                release_id="S2-L2",
                branch_id="scn-b-s2",
                status="PUBLISHED",
                published_at_utc="2026-06-15T13:10:00Z",
                cutoff_utc="2026-06-15T13:05:00Z",
                delta_tables={"tank_movements": 0, "kpi_facts": int(kpi_w2["delta_version"])},
                kpi_rows=kpi_l2,
                supersedes_release_id="S2-L1",
            )
            pub_p2 = PublicationRecord(
                publication_id="S2-P2",
                subject_key="assay:TK-101H:LOT-44",
                branch_id="scn-b-s2",
                release_id="REL-S2-P2",
                supersession_ordinal=2,
                effective_at_utc="2026-06-15T08:00:00Z",
                recorded_at_utc="2026-06-15T12:00:00Z",
                published_at_utc="2026-06-15T12:30:00Z",
                allowed_roles=("Planner", "Analyst"),
                supersedes_publication_id="S2-P1",
                payload={"lot_id": "LOT-44", "tank_id": "TK-101H", "disposition": "RELEASE", "sulfur_wt_pct": 1.38},
            )
            receipt_r2 = DeliveryReceipt(
                publication_id="S2-P2",
                recipient_role="Planner",
                channel="workspace",
                delivered_at_utc="2026-06-15T13:00:00Z",
            )
            rel_p2 = ReleaseEvent(
                release_id="REL-S2-P2",
                status="PUBLISHED",
                published_at_utc="2026-06-15T12:30:00Z",
                delivered_at_utc="2026-06-15T13:00:00Z",
                authorized_at_utc="2026-06-15T12:30:00Z",
            )

            pub_l2 = PublicationRecord(
                publication_id="S2-L2",
                subject_key="release:TK-101H:LOT-44",
                branch_id="scn-b-s2",
                release_id="S2-L2",
                supersession_ordinal=2,
                effective_at_utc="2026-06-15T13:05:00Z",
                recorded_at_utc="2026-06-15T13:05:00Z",
                published_at_utc="2026-06-15T13:10:00Z",
                allowed_roles=("Planner", "Analyst"),
                supersedes_publication_id="S2-L1",
                payload={"release_id": "S2-L2", "manifest_sha256": manifest_l2["manifest_sha256"], "lot_disposition": "RELEASE"},
            )
            receipt_l2 = DeliveryReceipt(
                publication_id="S2-L2",
                recipient_role="Planner",
                channel="workspace",
                delivered_at_utc="2026-06-15T13:15:00Z",
            )
            rel_l2 = ReleaseEvent(
                release_id="S2-L2",
                status="PUBLISHED",
                published_at_utc="2026-06-15T13:10:00Z",
                delivered_at_utc="2026-06-15T13:15:00Z",
                authorized_at_utc="2026-06-15T13:10:00Z",
            )

            all_pubs = [pub_p1, pub_l1, pub_p2, pub_l2]
            all_rels = [rel_p1, rel_l1, rel_p2, rel_l2]
            all_receipts = [receipt_r1, receipt_l1, receipt_r2, receipt_l2]

            # 13:12 UTC: S2-P2 delivered at 13:00 -> assay resolves S2-P2/RELEASE; S2-L2 delivered at 13:15 -> release stays S2-L1
            pre_release_1312 = _query_view("Planner", "2026-06-15T13:12:00Z", all_pubs, all_rels, all_receipts)
            # 13:15 UTC: both S2-P2/RELEASE and S2-L2 are eligible
            restated_1315 = _query_view("Planner", "2026-06-15T13:15:00Z", all_pubs, all_rels, all_receipts)
            # Replay 10:00 decision S2-D1 AFTER S2-P2 & S2-L2 exist -> exact match to S2-P1 + S2-L1, zero leakage!
            decision_s2_d1_replay = _query_view("Planner", "2026-06-15T10:00:00Z", all_pubs, all_rels, all_receipts)
            unauthorized_view = _query_view("ExternalGuest", "2026-06-15T13:15:00Z", all_pubs, all_rels, all_receipts)

            kpi_delta_rows = sorted(
                query_delta_readonly_duckdb(delta_kpi_dir),
                key=lambda r: (str(r["release_id"]), str(r["kpi_name"])),
            )
            evidence = {
                "scenario_id": "SCENARIO-B-S2",
                "qualification_verdict": "QUALIFIED_PROVISIONAL",
                "provenance_class": "SYNTHETIC",
                "tank_tk101h_bbl": tank_tk101h_bbl,
                "tank_mass_residual_kg": tk_step.mass_residual_kg,
                "delta_movement_row_count": len(delta_movement_rows),
                "kpi_rows": kpi_delta_rows,
                "quarantine_count": inbox.quarantine_count(),
                "watermarks": inbox.watermarks("logistics_sqlite", "scn-b-s2"),
                "m1_outcomes": {
                    "first": m1_first_status,
                    "duplicate": m1_dup_outcome.status,
                    "conflict": m1_conflict_outcome.status,
                    "delta_publish": pub_res["status"],
                    "delta_publish_retry": pub_retry["status"],
                },
                "release_manifests": {
                    "S2-L1_sha256": manifest_l1["manifest_sha256"],
                    "S2-L2_sha256": manifest_l2["manifest_sha256"],
                },
                "pre_receipt_0925": pre_receipt_0925,
                "pre_release_delivery_0947": pre_release_delivery_0947,
                "decision_s2_d1_1000": decision_s2_d1_initial,
                "pre_release_1312": pre_release_1312,
                "restated_1315": restated_1315,
                "decision_s2_d1_replay": decision_s2_d1_replay,
                "replay_exact_match": decision_s2_d1_initial == decision_s2_d1_replay,
                "unauthorized_view": unauthorized_view,
            }
            evidence["evidence_sha256"] = hashlib.sha256(
                json.dumps(evidence, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            return evidence
        finally:
            inbox.close()
            src_store.close()
    finally:
        if tmp_ctx is not None:
            tmp_ctx.cleanup()
