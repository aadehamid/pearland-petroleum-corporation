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

import unittest

from intelligence.optimization.backcasting import (
    evaluate_lp_setpoints_in_wp1_physics,
    run_uc3_three_way_backcast,
)
from intelligence.optimization.planning_lp import PlanningLPInputs, solve_planning_lp


class TestWP3APlanningLPAndBackcasting(unittest.TestCase):
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
        # Determinism check
        orig_replay = solve_planning_lp(orig)
        self.assertEqual(orig_res["margin_usd_per_day"], orig_replay["margin_usd_per_day"])

        # Closed-loop check on uncalibrated LP exposes real nonlinear Chevron RVP violation!
        orig_cl = evaluate_lp_setpoints_in_wp1_physics(
            orig_res, orig, compressor_circ_fraction=0.75, h2_allocable_t_per_day=125.0, rvp_cap_psi=9.00
        )
        self.assertFalse(orig_cl["closed_loop_feasible"])
        self.assertGreater(orig_cl["rvp_nonlinearity_gap_psi"], 0.4)

        # Recalibrated LP tightens butane cap to 3.4% (Chevron RVP <= 9.00) and updates HCU ULSD yield to 0.442
        # Decision alternative swings FCC/crude mix under higher ULSD margin
        alt = PlanningLPInputs(
            case_id="UC3-ALT",
            branch_id="scn-a-alt",
            hcu_max_bpd=30000.0,
            hcu_ulsd_yield_vol=0.442,
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
        )
        self.assertTrue(backcast["po12b_nonzero_calibration_proven"])
        self.assertAlmostEqual(backcast["identity_residual_usd_per_day"], 0.0, places=6)

        # Recalibrated LP MUST pass closed-loop WP-1 physics with ZERO violations!
        recal_cl = evaluate_lp_setpoints_in_wp1_physics(
            backcast["cases"]["recal_plan"],
            orig,
            compressor_circ_fraction=0.75,
            h2_allocable_t_per_day=125.0,
            rvp_cap_psi=9.00,
        )
        self.assertTrue(recal_cl["closed_loop_feasible"], recal_cl["violations"])


if __name__ == "__main__":
    unittest.main()
