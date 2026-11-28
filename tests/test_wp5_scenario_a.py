#!/usr/bin/env python3
"""Tests for WP-5 Scenario A vertical slice (SCN-A-T125 & SCN-A-H2CONT) against external golden oracle."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

import yaml

from evaluations.scenario_a_slice import ORACLE_PATH, run_scenario_a_walkthrough

REPO_ROOT = Path(__file__).resolve().parents[1]
EPM_BINDINGS_PATH = REPO_ROOT / "semantic" / "mappings" / "epm_kpi_bindings.yaml"


class TestWP5ScenarioA(unittest.TestCase):
    def test_scenario_a_t125_and_h2cont_end_to_end_against_external_oracle(self):
        oracle = json.loads(ORACLE_PATH.read_text(encoding="utf-8"))
        t125 = oracle["scenarios"]["SCN-A-T125"]
        h2cont = oracle["scenarios"]["SCN-A-H2CONT"]

        ev = run_scenario_a_walkthrough()
        self.assertEqual(ev["scenario_id"], "SCN-A-T125")
        self.assertEqual(ev["qualification_verdict"], "QUALIFIED_PROVISIONAL")
        self.assertEqual(ev["provenance_class"], "SYNTHETIC")

        # 1. WP-1c canonical world kernel matches frozen external oracle
        wk = ev["world_kernel"]
        self.assertAlmostEqual(wk["baseline_processed_bbl"], t125["shift_70min_baseline_processed_bbl"], places=9)
        self.assertAlmostEqual(wk["child_24k_processed_bbl"], t125["shift_70min_child_24k_processed_bbl"], places=9)
        self.assertAlmostEqual(wk["branch_delta_bbl"], t125["shift_70min_branch_delta_bbl"], places=9)
        self.assertTrue(wk["checkpoint_immutable"])
        self.assertTrue(wk["replay_bit_identical"])
        self.assertEqual(wk["t125_binding_constraint"], t125["expected_binding_constraint"])
        self.assertAlmostEqual(wk["t125_max_feed_bbl_per_day"], t125["expected_max_hcu_feed_bbl_per_day"], places=6)
        self.assertAlmostEqual(wk["t125_max_feed_t_per_day"], t125["expected_max_hcu_feed_t_per_day"], places=2)
        self.assertFalse(wk["t125_30001_feasible"])

        self.assertAlmostEqual(wk["h2cont_headroom_t_per_day"], h2cont["expected_hcu_headroom_t_per_day"], places=6)
        self.assertEqual(wk["h2cont_binding_constraint"], h2cont["expected_binding_constraint"])
        self.assertAlmostEqual(wk["h2cont_max_feed_t_per_day"], h2cont["expected_max_hcu_feed_t_per_day"], places=2)
        self.assertAlmostEqual(
            wk["h2cont_max_feed_bbl_per_day"], h2cont["expected_max_hcu_feed_bbl_per_day_approx"], places=1
        )

        # 2. WP-2 OT-DELAY-01 + atomic inbox idempotency (initial birth emits NBIRTH only; no invented DBIRTH)
        ot_int = ev["ot_and_integration"]
        self.assertEqual(ot_int["birth_event_count"], 1)
        self.assertEqual(ot_int["ot_tag_id"], "REFA.HCU.K201.SI_4110.PV")
        self.assertEqual(ot_int["ot_visible_at_0815_count"], 0)
        self.assertEqual(ot_int["ot_visible_at_0816_count"], 1)
        self.assertEqual(ot_int["inbox_first"], "APPLIED")
        self.assertEqual(ot_int["inbox_duplicate"], "IDEMPOTENT_DUPLICATE")
        self.assertEqual(ot_int["delta_publish"], "PUBLISHED")

        # 3. WP-3 Delta KPI store (registered EPM binding) + reader-as-of temporal cutoff
        lr = ev["lakehouse_and_reader"]
        epm_doc = yaml.safe_load(EPM_BINDINGS_PATH.read_text(encoding="utf-8"))
        registered_kpis = {
            (b["kpi"], b["measure_class"], b["epm_artifact"]) for b in epm_doc["bindings"] if "kpi" in b
        }
        self.assertEqual(len(lr["kpi_rows"]), 1)
        row = lr["kpi_rows"][0]
        self.assertIn((row["kpi_name"], row["measure_class"], row["epm_artifact"]), registered_kpis)
        self.assertAlmostEqual(row["value"], 6000.0, places=6)
        self.assertEqual(lr["reader_0815_status"], "UNRESOLVED")
        self.assertEqual(lr["reader_0816_status"], "RESOLVED")
        self.assertEqual(lr["reader_0816_publication_id"], "SCN-A-P1")

        # 4. WP-3A Planning LP + UC-3 PO-12b backcasting
        lp = ev["planning_lp_and_backcast"]
        self.assertEqual(lp["t125_status"], "FEASIBLE")
        self.assertLessEqual(lp["t125_hcu_feed_bpd"], 30000.0 + 1e-6)
        self.assertEqual(lp["probe_30001_status"], "INFEASIBLE")
        self.assertEqual(lp["h2cont_status"], "FEASIBLE")
        self.assertLessEqual(lp["h2cont_hcu_feed_bpd"], 25950.0)
        self.assertTrue(lp["po12b_proven"])
        self.assertAlmostEqual(lp["backcast_identity_residual"], 0.0, places=6)

        # 5. WP-3B offline agent + signed RBAC + PO-10 ACID policy gate
        ap = ev["agent_and_policy"]
        self.assertEqual(ap["agent_adapter_mode"], "OFFLINE_RECORDED_FIXTURE_ONLY")
        self.assertTrue(ap["otel_restricted_redacted"])
        self.assertEqual(ap["proposal_authority_class"], "REQUIRE_APPROVAL")
        self.assertEqual(ap["proposal_tier"], 1)
        self.assertEqual(ap["proposal_required_role"], "Shift Supervisor")
        self.assertEqual(ap["agent_forged_auth_status"], "DENIED")
        self.assertEqual(ap["supervisor_auth_status"], "AUTHORIZED")
        self.assertEqual(ap["execution_status"], "EXECUTED")
        self.assertEqual(ap["replay_denied_reason"], "PROPOSAL_ALREADY_EXECUTED")

        # 6. WP-5B Relate WASM server-filtered graph package
        rw = ev["relate_wasm_explorer"]
        self.assertEqual(rw["planner_node_badges"], ["POTENTIAL_EXPOSURE", "POTENTIAL_EXPOSURE", "POTENTIAL_EXPOSURE"])
        self.assertEqual(rw["planner_edge_badges"], ["POTENTIAL_EXPOSURE", "POTENTIAL_EXPOSURE"])
        self.assertEqual(rw["planner_card_badges"], ["MODEL_QUANTIFIED"])
        self.assertEqual(rw["planner_reachable_from_4b"], ["TERM-01", "TK-301"])
        self.assertEqual(rw["guest_node_count"], 0)
        self.assertEqual(rw["guest_card_count"], 0)

        # Determinism check: second independent run produces identical SHA-256 evidence
        ev2 = run_scenario_a_walkthrough()
        self.assertEqual(ev["evidence_sha256"], ev2["evidence_sha256"])


if __name__ == "__main__":
    unittest.main()
