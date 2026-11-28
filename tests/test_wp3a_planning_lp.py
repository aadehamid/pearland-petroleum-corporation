#!/usr/bin/env python3
"""WP-3A verification suite (ENG-V08a, PO-12b, R3 Numerical Gate).

Verifies:
1. Known feasible/infeasible fixtures (30,001 bbl/day rejected under 75% derate; 75 t/day H2 cap binds SCN-A-H2CONT).
2. Deterministic solver replay (identical inputs -> bit-identical optimal margin & setpoints).
3. Deliberate Planning LP vs mechanistic WP-1 World Kernel structural separation:
   - Uncalibrated linear-RVP Planning LP over-blends butane to 4.86% (appearing legal at 9.00 psi linear
     while violating nonlinear Chevron RVP at > 9.5 psi!), proving real LP calibration error (PO-12b).
   - Recalibrated LP with conservative butane cap produces closed-loop feasible WP-1 setpoints with zero violations.
4. Exact EQ-09 three-way UC-3 backcasting attribution identity with non-zero LP calibration attribution.
"""
from __future__ import annotations

import json
from pathlib import Path
import unittest

import yaml

from intelligence.optimization.backcasting import (
    evaluate_lp_setpoints_in_wp1_physics,
    run_uc3_three_way_backcast,
)
from intelligence.optimization.planning_lp import PlanningLPInputs, solve_planning_lp

REPO_ROOT = Path(__file__).resolve().parents[1]


class TestWP3APlanningLPAndBackcasting(unittest.TestCase):
    def test_manifest_and_design_basis_alignment(self):
        manifest = json.loads((REPO_ROOT / "fixtures/golden/wp3a_release_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["provenance_class"], "SYNTHETIC")
        self.assertEqual(manifest["solver_profile"]["lp_solver"], "appsi_highs")
        self.assertAlmostEqual(manifest["solver_profile"]["lp_feasibility_tolerance"], 1e-7, places=12)
        design_basis_path = REPO_ROOT / manifest["design_basis_ref"]
        vintage_path = REPO_ROOT / manifest["public_vintage_ref"]
        self.assertTrue(design_basis_path.exists())
        self.assertTrue(vintage_path.exists())

        basis = yaml.safe_load(design_basis_path.read_text(encoding="utf-8"))
        defaults = PlanningLPInputs(case_id="SCN-A-T125", branch_id="baseline")
        units_by_id = {u["id"]: u for u in basis["units"]}
        self.assertAlmostEqual(defaults.cdu_min_bpd, float(basis["crude_slate"]["min_charge_bbl_per_day"]), places=6)
        self.assertAlmostEqual(defaults.cdu_max_bpd, float(basis["crude_slate"]["max_charge_bbl_per_day"]), places=6)
        self.assertAlmostEqual(defaults.hcu_max_bpd, float(units_by_id["4B"]["capacity_bbl_per_day"]), places=6)
        self.assertAlmostEqual(defaults.fcc_max_bpd, float(units_by_id["4A"]["capacity_bbl_per_day"]), places=6)

        # Explicitly run SCN-A-T125 pinned scenario under 75% compressor derate
        t125 = solve_planning_lp(PlanningLPInputs(case_id="SCN-A-T125", branch_id="scn-a-derate", hcu_max_bpd=30000.0))
        self.assertEqual(t125["feasibility_status"], "FEASIBLE")
        self.assertLessEqual(t125["setpoints"]["hcu_feed_bpd"], 30000.0 + 1e-6)

    def test_infeasible_30001_rejected_and_h2cont_75t_binds(self):
        # 30,001 bbl/day fixed HCU feed against 30,000 bbl/day derated cap MUST be INFEASIBLE
        infeas = solve_planning_lp(
            PlanningLPInputs(
                case_id="SCN-A-30001",
                branch_id="scn-a-derate",
                hcu_max_bpd=30000.0,
                fixed_hcu_bpd=30001.0,
            )
        )
        self.assertEqual(infeas["feasibility_status"], "INFEASIBLE")

        # SCN-A-H2CONT: 75 t/day shared H2 headroom must bind HCU below 30,000 bbl/day (~25,945 bbl/day)
        h2cont = solve_planning_lp(
            PlanningLPInputs(
                case_id="SCN-A-H2CONT",
                branch_id="scn-a-h2cont",
                hcu_max_bpd=30000.0,
                h2_hcu_headroom_t_per_day=75.0,
            )
        )
        self.assertEqual(h2cont["feasibility_status"], "FEASIBLE")
        self.assertLessEqual(h2cont["setpoints"]["hcu_feed_bpd"], 25950.0)
        self.assertAlmostEqual(h2cont["setpoints"]["h2_used_hcu_t_per_day"], 75.0, places=4)

    def test_po12b_uc3_backcast_proves_nonzero_lp_calibration_and_closed_loop_feasibility(self):
        # Uncalibrated LP uses lagged linear RVP (allows up to 4.86% butane -> violates nonlinear Chevron RVP > 9.00)
        orig = PlanningLPInputs(
            case_id="UC3-ORIG",
            branch_id="scn-a-derate",
            hcu_max_bpd=30000.0,
            hcu_ulsd_yield_vol=0.430,
            butane_max_vol_frac=0.06,
        )
        orig_res = solve_planning_lp(orig)
        self.assertEqual(orig_res["feasibility_status"], "FEASIBLE")
        # Determinism check covers BOTH optimal margin and every setpoint value
        orig_replay = solve_planning_lp(orig)
        self.assertEqual(orig_res["margin_usd_per_day"], orig_replay["margin_usd_per_day"])
        self.assertEqual(orig_res["setpoints"], orig_replay["setpoints"])

        # Closed-loop check on uncalibrated LP exposes real nonlinear Chevron RVP violation!
        orig_cl = evaluate_lp_setpoints_in_wp1_physics(
            orig_res, orig, compressor_circ_fraction=0.75, h2_allocable_t_per_day=125.0, rvp_cap_psi=9.00
        )
        self.assertFalse(orig_cl["closed_loop_feasible"])
        self.assertGreater(orig_cl["rvp_nonlinearity_gap_psi"], 0.4)

        # Recalibrated LP tightens butane cap to 3.4% (Chevron RVP <= 9.00) and applies base+delta HCU ULSD yield to 0.442
        # Decision alternative swings FCC/crude mix under higher ULSD margin
        alt = PlanningLPInputs(
            case_id="UC3-ALT",
            branch_id="scn-a-alt",
            hcu_max_bpd=30000.0,
            hcu_ulsd_yield_vol=0.430,
            delta_hcu_ulsd_yield_vol=0.012,
            butane_max_vol_frac=0.034,
            fcc_max_bpd=30000.0,
            price_ulsd=106.0,
        )
        backcast = run_uc3_three_way_backcast(
            orig_inputs=orig,
            recalibrated_hcu_ulsd_yield=0.442,
            recalibrated_butane_max_vol_frac=0.034,
            decision_alt_inputs=alt,
            actual_realized_margin_usd_per_day=orig_res["margin_usd_per_day"] - 125000.0,
            compressor_circ_fraction=0.75,
            h2_allocable_t_per_day=125.0,
            rvp_cap_psi=9.00,
        )
        self.assertTrue(backcast["po12b_nonzero_calibration_proven"])
        self.assertAlmostEqual(backcast["identity_residual_usd_per_day"], 0.0, places=6)
        self.assertFalse(backcast["orig_closed_loop"]["closed_loop_feasible"])
        self.assertTrue(backcast["recal_closed_loop"]["closed_loop_feasible"], backcast["recal_closed_loop"]["violations"])

        # Arbitrary nudge that does NOT close WP-1 Chevron-RVP physics MUST NOT claim PO-12b proven
        nudge_only = run_uc3_three_way_backcast(
            orig_inputs=orig,
            recalibrated_hcu_ulsd_yield=0.4301,
            recalibrated_butane_max_vol_frac=0.06,
            decision_alt_inputs=alt,
            actual_realized_margin_usd_per_day=orig_res["margin_usd_per_day"] - 125000.0,
            compressor_circ_fraction=0.75,
            h2_allocable_t_per_day=125.0,
            rvp_cap_psi=9.00,
        )
        self.assertFalse(nudge_only["po12b_nonzero_calibration_proven"])

    def test_input_validation_and_scenario_bound_binding(self):
        with self.assertRaises(ValueError):
            PlanningLPInputs(case_id="BAD-NAN", branch_id="b1", price_ulsd=float("nan"))
        with self.assertRaises(ValueError):
            PlanningLPInputs(case_id="BAD-BOOL", branch_id="b1", hcu_max_bpd=True)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            PlanningLPInputs(case_id="BAD-BOUNDS", branch_id="b1", hcu_min_bpd=50000.0, hcu_max_bpd=30000.0)
        with self.assertRaises(ValueError):
            PlanningLPInputs(case_id="BAD-RVP", branch_id="b1", bob_rvp_max_psi=0.0)
        with self.assertRaises(ValueError):
            PlanningLPInputs(case_id="BAD-PROV", branch_id="b1", provenance_class="UNKNOWN")

        scen_20k = PlanningLPInputs(case_id="MAINT-20K", branch_id="b1", hcu_max_bpd=20000.0)
        scen_30k = PlanningLPInputs(case_id="DERATE-30K", branch_id="b1", hcu_max_bpd=30000.0)
        res_30k = solve_planning_lp(scen_30k)
        # Cross-scenario setpoints MUST fail closed via input_digest mismatch
        with self.assertRaises(ValueError):
            evaluate_lp_setpoints_in_wp1_physics(
                res_30k, scen_20k, compressor_circ_fraction=1.0, h2_allocable_t_per_day=125.0
            )
        # Missing setpoint keys with matching digest MUST raise ValueError (not KeyError)
        with self.assertRaises(ValueError):
            evaluate_lp_setpoints_in_wp1_physics(
                {"feasibility_status": "FEASIBLE", "input_digest": scen_20k.input_digest(), "setpoints": {}},
                scen_20k,
                compressor_circ_fraction=1.0,
                h2_allocable_t_per_day=125.0,
            )
        # Hand-built setpoint exceeding scenario's 20,000 bbl/day cap MUST fail closed even when physics allows 40,000
        forged_25k = {
            "feasibility_status": "FEASIBLE",
            "input_digest": scen_20k.input_digest(),
            "setpoints": {
                "hcu_feed_bpd": 25000.0,
                "cdu_total_bpd": 150000.0,
                "fcc_feed_bpd": 20000.0,
                "butane_vol_frac": 0.0,
                "linear_bob_rvp_psi": 6.8,
            },
        }
        chk = evaluate_lp_setpoints_in_wp1_physics(
            forged_25k, scen_20k, compressor_circ_fraction=1.0, h2_allocable_t_per_day=125.0
        )
        self.assertFalse(chk["closed_loop_feasible"])
        self.assertTrue(any("HCU_SCENARIO_CAP_EXCEEDED" in v for v in chk["violations"]))


if __name__ == "__main__":
    unittest.main()
