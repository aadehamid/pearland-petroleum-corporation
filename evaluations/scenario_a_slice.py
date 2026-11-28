#!/usr/bin/env python3
"""WP-5 Scenario A Vertical Slice: Hydrocracker Recycle Compressor Derate (`SCN-A-T125` & `SCN-A-H2CONT`).

Exercises all six implemented PPC layers end-to-end against the external golden oracle
`fixtures/golden/scn_a_t125_oracle.json` (`UC-1`, `UC-3`, `SCENARIO-001 §2`, `WORLD-002 §6`, `OT-DELAY-01`):
1. WP-1c (`generators/world_kernel.py`, `generators/equations.py`):
   - `SCN-A-T125` 70-minute baseline + 08:40 checkpoint + isolated child-24k fork (1500 / 1375 / 125 bbl, PO-09).
   - `EQ-05`/`EQ-07` exact checks for `SCN-A-T125` (30,000 bbl/day, 4,336.08 t/day, 30,001 rejected)
     and `SCN-A-H2CONT` (57 t/day SMR -> 75 t/day HCU headroom -> shared_h2_cap, 3,750 t/day ~ 25,945.1 bbl/day).
2. WP-2 (`ot/sparkplug_ice_pipeline.py`, `source-systems/refinery/outbox_store.py`, `integration/outbox_inbox_service.py`):
   - Sparkplug B NBIRTH/DBIRTH + `REFA.HCU.K201.SI_4110.PV` DDATA with `OT-DELAY-01` cutoff (08:15:00 invisible, 08:16:00 visible).
   - Atomic outbox + Silver staging inbox + idempotent duplicate handling + Delta publication.
3. WP-3 (`lakehouse/delta/publisher.py`, `lakehouse/delta/reader_as_of.py`):
   - Idempotent Delta KPI store carrying registered EPM KPI `Unplanned Capacity Loss`
     (`ontology/kpi_ontology_class_hierarchy.md`), read-only DuckDB query, SHA-256 `ReleaseManifest`,
     and `select_reader_as_of` cutoff & RBAC enforcement.
4. WP-3A (`intelligence/optimization/planning_lp.py`, `intelligence/optimization/backcasting.py`):
   - Pyomo + HiGHS reduced Planning LP (`SCN-A-T125` feasible, `30,001` infeasible, `SCN-A-H2CONT` 75 t/day H2 binding)
     and `EQ-09` three-way UC-3 backcasting proving `PO-12b` against WP-1 physics.
5. WP-3B (`api/auth_and_context.py`, `policy/engine.py`, `automation/offline_agent.py`):
   - Offline `RecordedResponseAgentAdapter` (zero live LLM calls; redacted OTel trace).
   - `AuthRBACStore` + `PolicyGateService` (`PO-10`): agent forged `X-Role` denied, Shift Supervisor approval,
     fresh-revision execution, and single-use replay rejection (`PROPOSAL_ALREADY_EXECUTED`).
6. WP-5B (`apps/relate-wasm/graph_package.py`):
   - Server-side permission-filtered Relate WASM package preserving `POTENTIAL_EXPOSURE` (graph) vs
     `MODEL_QUANTIFIED` (LP/KPI card) badge separation (`UX-001`, `ADR-0052`).
"""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

from api.auth_and_context import AuthRBACStore
from automation.offline_agent import RecordedResponseAgentAdapter
from generators import equations as eq
from generators.world_kernel import RefineryWorldKernel, WorldEvent, WorldState
from integration.outbox_inbox_service import AtomicStagingInboxService
from intelligence.optimization.backcasting import run_uc3_three_way_backcast
from intelligence.optimization.planning_lp import PlanningLPInputs, solve_planning_lp
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
from ot.sparkplug_ice_pipeline import SparkplugOTPublisher, filter_visible_ot_events
from policy.engine import PolicyGateService

REPO_ROOT = Path(__file__).resolve().parents[1]
ORACLE_PATH = REPO_ROOT / "fixtures" / "golden" / "scn_a_t125_oracle.json"
OT_TAGS_PATH = REPO_ROOT / "fixtures" / "golden" / "refinery_a_ot_tags.yaml"
THRESHOLDS_PATH = REPO_ROOT / "schemas" / "policy_thresholds.yaml"
AGENT_FIXTURE_PATH = REPO_ROOT / "fixtures" / "golden" / "agent_recorded_responses" / "scn_a_t125_recorded.json"


def _load_module(mod_name: str, rel_path: str) -> Any:
    if mod_name in sys.modules:
        return sys.modules[mod_name]
    path = REPO_ROOT / rel_path
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module {mod_name} from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


def run_scenario_a_walkthrough(work_dir: str | Path | None = None) -> dict[str, Any]:
    """Execute deterministic Scenario A (SCN-A-T125 & SCN-A-H2CONT) in-process vertical slice and return evidence summary."""
    oracle_bytes = ORACLE_PATH.read_bytes()
    oracle_sha256 = hashlib.sha256(oracle_bytes).hexdigest()
    oracle = json.loads(oracle_bytes.decode("utf-8"))
    t125_oracle = oracle["scenarios"]["SCN-A-T125"]
    h2cont_oracle = oracle["scenarios"]["SCN-A-H2CONT"]
    ot_schedule = yaml.safe_load(OT_TAGS_PATH.read_text(encoding="utf-8"))

    outbox_mod = _load_module("ppc_wp5_outbox_store", "source-systems/refinery/outbox_store.py")
    wasm_mod = _load_module("ppc_wp5_relate_wasm_pkg", "apps/relate-wasm/graph_package.py")

    # 1. WP-1c: Canonical World Kernel 70-min shift + 08:40 checkpoint + isolated child-24k fork + replay
    t0 = datetime(2026, 6, 15, 8, 0, tzinfo=timezone.utc)
    t_derate = datetime(2026, 6, 15, 8, 10, tzinfo=timezone.utc)
    t_fork = datetime(2026, 6, 15, 8, 40, tzinfo=timezone.utc)
    t_end = datetime(2026, 6, 15, 9, 10, tzinfo=timezone.utc)

    base = RefineryWorldKernel(WorldState("world-v1.0.0", "scn-a-baseline", 42, t0), step_seconds=60, fixture_mode=True)
    base.schedule_event(
        WorldEvent(
            "EVT-DERATE-K201",
            t_derate,
            "HCU_COMPRESSOR_DERATE",
            {"compressor_circ_fraction": float(t125_oracle["compressor_circ_fraction"])},
        )
    )
    base.advance_to(t_fork)
    ckpt = base.checkpoint()
    ckpt_digest_before = ckpt["state_digest"]

    child = RefineryWorldKernel.from_checkpoint(ckpt, branch_id="scn-a-child-24k")
    child.schedule_event(WorldEvent("EVT-SET-24K", t_fork, "HCU_FEED_SETPOINT", {"requested_feed_bbl_per_day": 24000.0}))
    base.advance_to(t_end)
    child.advance_to(t_end)
    replay = RefineryWorldKernel.from_checkpoint(ckpt)
    replay.advance_to(t_end)

    # Exact EQ-05 / EQ-07 checks for SCN-A-T125 and SCN-A-H2CONT
    h2_norm = eq.h2_header_balance(107.0, 73.0, 5.0, 5.0, 5.0, 40.0)
    hcu_t125 = eq.hcu_evaluate(
        requested_feed_bbl_per_day=float(t125_oracle["expected_max_hcu_feed_bbl_per_day"]),
        compressor_circ_fraction=float(t125_oracle["compressor_circ_fraction"]),
        h2_allocable_t_per_day=float(h2_norm["hcu_headroom_t_per_day"]),
        fixture_mode=True,
    )
    hcu_infeas = eq.hcu_evaluate(
        requested_feed_bbl_per_day=float(t125_oracle["infeasible_probe_bbl_per_day"]),
        compressor_circ_fraction=float(t125_oracle["compressor_circ_fraction"]),
        h2_allocable_t_per_day=float(h2_norm["hcu_headroom_t_per_day"]),
        fixture_mode=True,
    )
    h2_cont = eq.h2_header_balance(float(h2cont_oracle["smr_h2_t_per_day"]), 73.0, 5.0, 5.0, 5.0, 40.0)
    hcu_h2cont = eq.hcu_evaluate(
        requested_feed_bbl_per_day=30000.0,
        compressor_circ_fraction=float(t125_oracle["compressor_circ_fraction"]),
        h2_allocable_t_per_day=float(h2_cont["hcu_headroom_t_per_day"]),
        fixture_mode=True,
    )

    tmp_ctx = tempfile.TemporaryDirectory(prefix="ppc-wp5-") if work_dir is None else None
    base_dir = Path(tmp_ctx.name) if tmp_ctx is not None else Path(work_dir)
    base_dir.mkdir(parents=True, exist_ok=True)
    try:
        # 2. WP-2: Sparkplug OT publisher (OT-DELAY-01) + atomic source outbox -> Silver inbox -> Delta
        ot_pub = SparkplugOTPublisher(ot_schedule, buffer_path=base_dir / "ot_buffer.json")
        birth_events = ot_pub.connect_and_birth("2026-06-15T08:00:00Z")
        derate_ot_ev = ot_pub.ingest_sample(
            tag_name="REFA.HCU.K201.SI_4110.PV",
            value=75.0,
            quality="Good",
            effective_at_utc="2026-06-15T08:10:00Z",
            recorded_at_utc="2026-06-15T08:10:05Z",
            published_at_utc=str(t125_oracle["ot_delay_event_published_utc"]),
        )
        if derate_ot_ev is None:
            raise RuntimeError("Expected K-201 speed derate sample to publish DDATA")
        ot_visible_0815 = filter_visible_ot_events([derate_ot_ev], str(t125_oracle["ot_delay_invisible_cutoff_utc"]))
        ot_visible_0816 = filter_visible_ot_events([derate_ot_ev], str(t125_oracle["ot_delay_visible_cutoff_utc"]))

        src_store = outbox_mod.TransactionalOutboxSourceStore(base_dir / "refinery_src.db", "refinery_sqlite")
        inbox = AtomicStagingInboxService(base_dir / "silver_inbox.db")
        auth = AuthRBACStore(base_dir / "auth.db", signing_secret="wp5-scenario-a-fixture-signing-secret")
        gate = PolicyGateService(THRESHOLDS_PATH, base_dir / "policy.db")
        delta_events_dir = base_dir / "delta" / "hcu_events"
        delta_kpi_dir = base_dir / "delta" / "kpi_facts"
        try:
            src_store.commit_with_outbox(
                branch_id="scn-a-baseline",
                partition_key="unit:4B",
                source_tx_id="TX-SCN-A-DERATE-1",
                event_id="EVT-DERATE-K201",
                delivery_key="refinery_sqlite:scn-a-baseline:unit:4B:rev1",
                native_entity_key="4B",
                source_revision=1,
                event_type="HCU_COMPRESSOR_DERATE",
                effective_at_utc="2026-06-15T08:10:00Z",
                recorded_at_utc="2026-06-15T08:10:05Z",
                payload={"unit": "4B", "compressor": "K-201", "compressor_circ_fraction": 0.75},
            )
            ev_dict = asdict(src_store.fetch_pending_outbox()[0])
            ev_dict["published_at_utc"] = str(t125_oracle["ot_delay_event_published_utc"])
            out_first = inbox.consume_event(ev_dict)
            out_dup = inbox.consume_event(ev_dict)

            def _commit_events(*, table_name: str, rows: list[dict[str, Any]], txn_app_id: str, txn_version: int) -> None:
                drows = [
                    {
                        "delivery_key": str(r["delivery_key"]),
                        "event_id": str(r["event_id"]),
                        "branch_id": str(r["branch_id"]),
                        "event_type": str(r["event_type"]),
                        "effective_at_utc": str(r["effective_at_utc"]),
                        "published_at_utc": str(r["published_at_utc"]),
                    }
                    for r in rows
                ]
                write_delta_table_idempotent(delta_events_dir, drows, txn_app_id=txn_app_id, txn_version=txn_version)

            pub_events = inbox.publish_staging_to_delta_idempotent(
                txn_app_id="wp5_scenario_a_events",
                txn_version=1,
                table_name="hcu_events",
                source_system="refinery_sqlite",
                branch_id="scn-a-baseline",
                sink_commit_fn=_commit_events,
            )

            # 3. WP-3: Registered EPM KPI store (`Unplanned Capacity Loss`) + ReleaseManifest + reader-as-of
            capacity_loss_bpd = 36000.0 - float(hcu_t125["max_feed_bbl_per_day"])
            kpi_rows = [
                KPIFactRow(
                    release_id="SCN-A-REL-1",
                    branch_id="scn-a-baseline",
                    kpi_name="Unplanned Capacity Loss",
                    measure_class="KPI",
                    epm_artifact="ontology/kpi_ontology_class_hierarchy.md",
                    value=capacity_loss_bpd,
                    unit="bbl/day",
                    parent_kpi=None,
                    effective_at_utc="2026-06-15T08:10:00Z",
                    published_at_utc=str(t125_oracle["ot_delay_event_published_utc"]),
                    access_label="OPERATIONS",
                ).to_dict()
            ]
            kpi_write = write_delta_table_idempotent(
                delta_kpi_dir, kpi_rows, txn_app_id="wp5_scenario_a_kpis", txn_version=1
            )
            kpi_readback = sorted(
                query_delta_readonly_duckdb(delta_kpi_dir),
                key=lambda r: (str(r["release_id"]), str(r["kpi_name"])),
            )
            manifest = build_release_manifest(
                release_id="SCN-A-REL-1",
                branch_id="scn-a-baseline",
                status="PUBLISHED",
                published_at_utc=str(t125_oracle["ot_delay_event_published_utc"]),
                cutoff_utc="2026-06-15T08:15:00Z",
                delta_tables={"hcu_events": 0, "kpi_facts": int(kpi_write["delta_version"])},
                kpi_rows=kpi_rows,
            )

            grants = [
                AccessGrant(
                    role="Planner",
                    channel="workspace",
                    purpose="operations",
                    valid_from_utc="2026-06-15T08:00:00Z",
                    recorded_at_utc="2026-06-15T08:00:00Z",
                    effect="ALLOW",
                )
            ]
            pub_derate = PublicationRecord(
                publication_id="SCN-A-P1",
                subject_key="unit:4B:derate",
                branch_id="scn-a-baseline",
                release_id="SCN-A-REL-1",
                supersession_ordinal=1,
                effective_at_utc="2026-06-15T08:10:00Z",
                recorded_at_utc="2026-06-15T08:10:05Z",
                published_at_utc=str(t125_oracle["ot_delay_event_published_utc"]),
                allowed_roles=("Planner",),
                supersedes_publication_id=None,
                payload={"unit": "4B", "max_feed_bbl_per_day": 30000.0, "binding_constraint": "compressor_circulation_cap"},
            )
            receipt_derate = DeliveryReceipt(
                publication_id="SCN-A-P1",
                recipient_role="Planner",
                channel="workspace",
                delivered_at_utc=str(t125_oracle["ot_delay_event_published_utc"]),
            )
            rel_event = ReleaseEvent(
                release_id="SCN-A-REL-1",
                status="PUBLISHED",
                published_at_utc=str(t125_oracle["ot_delay_event_published_utc"]),
                delivered_at_utc=str(t125_oracle["ot_delay_event_published_utc"]),
                authorized_at_utc=str(t125_oracle["ot_delay_event_published_utc"]),
            )
            reader_0815 = select_reader_as_of(
                subject_key="unit:4B:derate",
                branch_id="scn-a-baseline",
                reader_role="Planner",
                reader_cutoff_utc=str(t125_oracle["ot_delay_invisible_cutoff_utc"]),
                publications=[pub_derate],
                release_events=[rel_event],
                receipts=[receipt_derate],
                grants=grants,
                channel="workspace",
                purpose="operations",
            )
            reader_0816 = select_reader_as_of(
                subject_key="unit:4B:derate",
                branch_id="scn-a-baseline",
                reader_role="Planner",
                reader_cutoff_utc=str(t125_oracle["ot_delay_visible_cutoff_utc"]),
                publications=[pub_derate],
                release_events=[rel_event],
                receipts=[receipt_derate],
                grants=grants,
                channel="workspace",
                purpose="operations",
            )

            # 4. WP-3A: Pyomo+HiGHS Planning LP (SCN-A-T125, 30,001 infeasible, SCN-A-H2CONT) + UC-3 backcasting
            lp_t125_in = PlanningLPInputs(case_id="SCN-A-T125", branch_id="scn-a-baseline", hcu_max_bpd=30000.0)
            lp_t125 = solve_planning_lp(lp_t125_in)
            lp_30001 = solve_planning_lp(
                PlanningLPInputs(
                    case_id="SCN-A-30001",
                    branch_id="scn-a-baseline",
                    hcu_max_bpd=30000.0,
                    fixed_hcu_bpd=float(t125_oracle["infeasible_probe_bbl_per_day"]),
                )
            )
            lp_h2cont = solve_planning_lp(
                PlanningLPInputs(
                    case_id="SCN-A-H2CONT",
                    branch_id="scn-a-h2cont",
                    hcu_max_bpd=30000.0,
                    h2_hcu_headroom_t_per_day=float(h2cont_oracle["expected_hcu_headroom_t_per_day"]),
                )
            )
            alt_in = PlanningLPInputs(
                case_id="SCN-A-UC3-ALT",
                branch_id="scn-a-alt",
                hcu_max_bpd=30000.0,
                hcu_ulsd_yield_vol=0.430,
                delta_hcu_ulsd_yield_vol=0.012,
                butane_max_vol_frac=0.034,
                price_ulsd=106.0,
            )
            backcast = run_uc3_three_way_backcast(
                orig_inputs=lp_t125_in,
                recalibrated_hcu_ulsd_yield=0.442,
                recalibrated_butane_max_vol_frac=0.034,
                decision_alt_inputs=alt_in,
                actual_realized_margin_usd_per_day=float(lp_t125["margin_usd_per_day"]) - 125000.0,
                compressor_circ_fraction=float(t125_oracle["compressor_circ_fraction"]),
                rvp_cap_psi=9.00,
            )

            # 5. WP-3B: Offline recorded agent + signed RBAC + ACID PolicyGateService (PO-10)
            agent = RecordedResponseAgentAdapter(AGENT_FIXTURE_PATH)
            agent_out = agent.run_investigation(
                "SCN-A-T125", str(t125_oracle["ot_delay_visible_cutoff_utc"]), "Planner"
            )
            rec_act = agent_out["recommended_action"]

            auth.seed_fixture_accounts("wp5-fixture-pass")
            agent_tok = auth.issue_token("ppc_agent_1", "wp5-fixture-pass")
            sup_tok = auth.issue_token("shift_supervisor", "wp5-fixture-pass")
            assert agent_tok is not None and sup_tok is not None

            action_payload = {
                "unit": rec_act["target_unit"],
                "baseline_feed_bbl_per_day": 30000.0,
                "feed_bbl_per_day": float(rec_act["requested_feed_bbl_per_day"]),
                "rate_change_bbl_per_day": float(rec_act["rate_change_bbl_per_day"]),
                "rate_change_pct": float(rec_act["rate_change_pct"]),
            }
            proposal = gate.submit_proposal(
                proposal_id="PROP-SCN-A-01",
                branch_id="scn-a-baseline",
                action_type=str(rec_act["action_type"]),
                proposer_id="usr-agent-1",
                proposer_is_agent=True,
                payload=action_payload,
                metrics={
                    "margin_effect_usd": float(rec_act["margin_effect_usd"]),
                    "rate_change_bbl_per_day": float(rec_act["rate_change_bbl_per_day"]),
                    "rate_change_pct": float(rec_act["rate_change_pct"]),
                },
                now_utc=t_fork,
                expected_source_revision="rev-1",
            )
            agent_forged_auth = gate.authorize_proposal_with_session(
                auth_store=auth,
                token=agent_tok,
                headers={"X-Role": "Shift Supervisor"},
                auth_id="AUTH-FORGED-01",
                proposal_id="PROP-SCN-A-01",
                branch_id="scn-a-baseline",
                payload_digest=proposal["payload_digest"],
                now_utc=t_fork,
            )
            sup_auth = gate.authorize_proposal_with_session(
                auth_store=auth,
                token=sup_tok,
                auth_id="AUTH-SUP-01",
                proposal_id="PROP-SCN-A-01",
                branch_id="scn-a-baseline",
                payload_digest=proposal["payload_digest"],
                now_utc=t_fork,
            )
            exec_res = gate.execute_authorized_action(
                idempotency_key="EXEC-SCN-A-01",
                proposal_id="PROP-SCN-A-01",
                auth_id="AUTH-SUP-01",
                branch_id="scn-a-baseline",
                payload=action_payload,
                now_utc=t_fork,
                current_source_revision="rev-1",
            )
            exec_replay_denied = gate.execute_authorized_action(
                idempotency_key="EXEC-SCN-A-02-REPLAY",
                proposal_id="PROP-SCN-A-01",
                auth_id="AUTH-SUP-01",
                branch_id="scn-a-baseline",
                payload=action_payload,
                now_utc=t_fork,
                current_source_revision="rev-1",
            )

            # 6. WP-5B: Server-filtered Relate WASM graph package (POTENTIAL_EXPOSURE vs MODEL_QUANTIFIED)
            pub_ts = str(t125_oracle["ot_delay_event_published_utc"])
            wasm_nodes = [
                {
                    "id": "4B",
                    "label": "ProcessUnit",
                    "name": "Hydrocracker",
                    "branch_id": "scn-a-baseline",
                    "published_at_utc": pub_ts,
                    "allowed_roles": ["Planner", "Shift Supervisor"],
                    "properties": {"compressor": "K-201", "derate_pct": 75.0},
                },
                {
                    "id": "TK-301",
                    "label": "Tank",
                    "name": "ULSD Product Tank",
                    "branch_id": "scn-a-baseline",
                    "published_at_utc": pub_ts,
                    "allowed_roles": ["Planner", "Shift Supervisor"],
                    "properties": {"product": "ULSD"},
                },
                {
                    "id": "TERM-01",
                    "label": "Terminal",
                    "name": "Houston Rack Terminal",
                    "branch_id": "scn-a-baseline",
                    "published_at_utc": pub_ts,
                    "allowed_roles": ["Planner", "Shift Supervisor"],
                    "properties": {"region": "PADD 3"},
                },
            ]
            wasm_edges = [
                {
                    "id": "E-4B-TK301",
                    "source": "4B",
                    "target": "TK-301",
                    "type": "FEEDS",
                    "branch_id": "scn-a-baseline",
                    "published_at_utc": pub_ts,
                    "allowed_roles": ["Planner", "Shift Supervisor"],
                },
                {
                    "id": "E-TK301-TERM01",
                    "source": "TK-301",
                    "target": "TERM-01",
                    "type": "SUPPLIES",
                    "branch_id": "scn-a-baseline",
                    "published_at_utc": pub_ts,
                    "allowed_roles": ["Planner", "Shift Supervisor"],
                },
            ]
            wasm_cards = [
                {
                    "card_id": "CARD-SCN-A-CAP-LOSS",
                    "model_run_id": f"LP-{lp_t125['input_digest'][:12]}",
                    "kpi_name": "Unplanned Capacity Loss",
                    "value": round(capacity_loss_bpd, 4),
                    "unit": "bbl/day",
                    "badge": "MODEL_QUANTIFIED",
                    "branch_id": "scn-a-baseline",
                    "published_at_utc": pub_ts,
                    "allowed_roles": ["Planner", "Shift Supervisor"],
                }
            ]
            wasm_planner = wasm_mod.build_filtered_graph_package(
                branch_id="scn-a-baseline",
                reader_role="Planner",
                reader_cutoff_utc=str(t125_oracle["ot_delay_visible_cutoff_utc"]),
                nodes=wasm_nodes,
                edges=wasm_edges,
                kpi_cards=wasm_cards,
            )
            wasm_guest = wasm_mod.build_filtered_graph_package(
                branch_id="scn-a-baseline",
                reader_role="ExternalGuest",
                reader_cutoff_utc=str(t125_oracle["ot_delay_visible_cutoff_utc"]),
                nodes=wasm_nodes,
                edges=wasm_edges,
                kpi_cards=wasm_cards,
            )

            evidence = {
                "case_id": "SCN-A-T125",
                "branch_id": "scn-a-baseline",
                "scenario_id": "SCN-A-T125",
                "oracle_id": oracle["oracle_id"],
                "oracle_sha256": oracle_sha256,
                "execution_mode": "IN_PROCESS_VERTICAL_SLICE",
                "qualification_verdict": "DRAFT",
                "qualification_note": (
                    "In-process vertical slice verification summary; promotion to QUALIFIED_PROVISIONAL "
                    "requires live exe.dev + R2 run, upstream adapter pins, and owner-approved PR per VERIFY-001."
                ),
                "world_kernel": {
                    "provenance_class": "SYNTHETIC",
                    "baseline_processed_bbl": base.state.hcu_cumulative_processed_bbl,
                    "child_24k_processed_bbl": child.state.hcu_cumulative_processed_bbl,
                    "branch_delta_bbl": base.state.hcu_cumulative_processed_bbl - child.state.hcu_cumulative_processed_bbl,
                    "checkpoint_immutable": ckpt["state"].digest() == ckpt_digest_before,
                    "replay_bit_identical": replay.state.digest() == base.state.digest(),
                    "t125_binding_constraint": hcu_t125["binding_constraint"],
                    "t125_max_feed_bbl_per_day": hcu_t125["max_feed_bbl_per_day"],
                    "t125_max_feed_t_per_day": hcu_t125["max_feed_t_per_day"],
                    "t125_30001_feasible": hcu_infeas["feasible"],
                    "h2cont_headroom_t_per_day": h2_cont["hcu_headroom_t_per_day"],
                    "h2cont_binding_constraint": hcu_h2cont["binding_constraint"],
                    "h2cont_max_feed_t_per_day": hcu_h2cont["max_feed_t_per_day"],
                    "h2cont_max_feed_bbl_per_day": hcu_h2cont["max_feed_bbl_per_day"],
                },
                "ot_and_integration": {
                    "provenance_class": "SYNTHETIC",
                    "birth_event_count": len(birth_events),
                    "ot_tag_id": derate_ot_ev.tag_name,
                    "ot_visible_at_0815_count": len(ot_visible_0815),
                    "ot_visible_at_0816_count": len(ot_visible_0816),
                    "inbox_first": out_first.status,
                    "inbox_duplicate": out_dup.status,
                    "delta_publish": pub_events["status"],
                },
                "lakehouse_and_reader": {
                    "provenance_class": "DERIVED",
                    "kpi_rows": kpi_readback,
                    "release_manifest_sha256": manifest["manifest_sha256"],
                    "reader_0815_status": reader_0815["status"],
                    "reader_0816_status": reader_0816["status"],
                    "reader_0816_publication_id": reader_0816["publication_id"],
                },
                "planning_lp_and_backcast": {
                    "provenance_class": "ESTIMATED",
                    "t125_status": lp_t125["feasibility_status"],
                    "t125_hcu_feed_bpd": lp_t125["setpoints"]["hcu_feed_bpd"],
                    "t125_margin_usd_per_day": lp_t125["margin_usd_per_day"],
                    "probe_30001_status": lp_30001["feasibility_status"],
                    "h2cont_status": lp_h2cont["feasibility_status"],
                    "h2cont_hcu_feed_bpd": lp_h2cont["setpoints"]["hcu_feed_bpd"],
                    "h2cont_h2_used_t_per_day": lp_h2cont["setpoints"]["h2_used_hcu_t_per_day"],
                    "po12b_proven": backcast["po12b_nonzero_calibration_proven"],
                    "backcast_identity_residual": backcast["identity_residual_usd_per_day"],
                },
                "agent_and_policy": {
                    "provenance_class": "SYNTHETIC",
                    "agent_adapter_mode": agent.mode,
                    "otel_restricted_redacted": agent_out["otel_span"]["restricted_payload"] == "[REDACTED]",
                    "proposal_authority_class": proposal["authority_class"],
                    "proposal_tier": proposal["tier"],
                    "proposal_required_role": proposal["required_approver_role"],
                    "agent_forged_auth_status": agent_forged_auth["status"],
                    "supervisor_auth_status": sup_auth["status"],
                    "execution_status": exec_res["status"],
                    "replay_denied_reason": exec_replay_denied.get("reason"),
                },
                "relate_wasm_explorer": {
                    "provenance_class": "DERIVED",
                    "planner_node_badges": [n["badge"] for n in wasm_planner["nodes"]],
                    "planner_edge_badges": [e["badge"] for e in wasm_planner["edges"]],
                    "planner_card_badges": [c["badge"] for c in wasm_planner["model_quantified_cards"]],
                    "planner_reachable_from_4b": wasm_mod.reachable_exposure_ids(wasm_planner, "4B"),
                    "guest_node_count": len(wasm_guest["nodes"]),
                    "guest_card_count": len(wasm_guest["model_quantified_cards"]),
                    "planner_package_sha256": wasm_planner["package_sha256"],
                },
            }
            evidence["evidence_sha256"] = hashlib.sha256(
                json.dumps(evidence, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            return evidence
        finally:
            gate.close()
            auth.close()
            inbox.close()
            src_store.close()
    finally:
        if tmp_ctx is not None:
            tmp_ctx.cleanup()
