#!/usr/bin/env python3
"""WP-3A UC-3 Three-Way Fair Backcasting Attribution and Closed-Loop WP-1 Verification (EQ-09, PO-12b).

Decomposes total economic variance identically into:
  Delta_Pi_total = (Pi_recal_plan - Pi_orig_plan)        [LP calibration effect]
                 + (Pi_feasible_alt - Pi_recal_plan)     [decision-time opportunity]
                 + (Pi_actual - Pi_feasible_alt)         [execution and exogenous residual]
"""
from __future__ import annotations

from dataclasses import replace
from typing import Any

from generators import equations as eq
from intelligence.optimization.planning_lp import PlanningLPInputs, solve_planning_lp


def evaluate_lp_setpoints_in_wp1_physics(
    lp_result: dict[str, Any],
    inputs: PlanningLPInputs,
    compressor_circ_fraction: float,
    h2_allocable_t_per_day: float,
    rvp_cap_psi: float = 9.00,
) -> dict[str, Any]:
    """Closed-loop check: feed LP setpoints into mechanistic WP-1 EQ-05 & EQ-08 physics."""
    sp = lp_result["setpoints"]
    if sp is None:
        return {"closed_loop_feasible": False, "violations": ["LP_INFEASIBLE"]}

    violations: list[str] = []
    hcu_chk = eq.hcu_evaluate(
        requested_feed_bbl_per_day=sp["hcu_feed_bpd"],
        mech_cap_bbl_per_day=40000.0,
        compressor_circ_fraction=compressor_circ_fraction,
        h2_allocable_t_per_day=h2_allocable_t_per_day,
        fixture_mode=True,
    )
    if not hcu_chk["feasible"]:
        violations.append(
            f"HCU_INFEASIBLE ({sp['hcu_feed_bpd']:.1f} > {hcu_chk['max_feed_bbl_per_day']:.1f} bbl/day)"
        )

    # Nonlinear Chevron RVP check on LP's butane blend fraction
    xb = sp["butane_vol_frac"]
    nonlin_rvp = eq.chevron_rvp_psi([1.0 - xb, xb], [6.80, 52.0])
    rvp_exceeded = nonlin_rvp > rvp_cap_psi + 1e-9
    if rvp_exceeded:
        violations.append(
            f"NONLINEAR_CHEVRON_RVP_EXCEEDED (linear={sp['linear_bob_rvp_psi']:.3f}, chevron={nonlin_rvp:.3f} > {rvp_cap_psi:.2f})"
        )

    return {
        "closed_loop_feasible": not violations,
        "violations": violations,
        "hcu_mechanistic_ulsd_bpd": float(hcu_chk["outputs"]["ulsd"]["volume_bbl_per_day"]),
        "hcu_mechanistic_max_feed_bpd": float(hcu_chk["max_feed_bbl_per_day"]),
        "chevron_rvp_psi": nonlin_rvp,
        "linear_rvp_psi": sp["linear_bob_rvp_psi"],
        "rvp_nonlinearity_gap_psi": nonlin_rvp - sp["linear_bob_rvp_psi"],
    }


def run_uc3_three_way_backcast(
    orig_inputs: PlanningLPInputs,
    recalibrated_hcu_ulsd_yield: float,
    recalibrated_butane_max_vol_frac: float,
    decision_alt_inputs: PlanningLPInputs,
    actual_realized_margin_usd_per_day: float,
) -> dict[str, Any]:
    """Execute EQ-09 three-way backcasting attribution proving measurable LP calibration error (PO-12b)."""
    orig_lp = solve_planning_lp(orig_inputs)
    recal_inputs = replace(
        orig_inputs,
        case_id=f"{orig_inputs.case_id}-RECAL",
        hcu_ulsd_yield_vol=recalibrated_hcu_ulsd_yield,
        butane_max_vol_frac=recalibrated_butane_max_vol_frac,
    )
    recal_lp = solve_planning_lp(recal_inputs)
    alt_lp = solve_planning_lp(decision_alt_inputs)

    if any(r["feasibility_status"] != "FEASIBLE" for r in (orig_lp, recal_lp, alt_lp)):
        raise ValueError("All three backcasting cases must be feasible for EQ-09 attribution")

    pi_orig = float(orig_lp["margin_usd_per_day"])
    pi_recal = float(recal_lp["margin_usd_per_day"])
    pi_alt = float(alt_lp["margin_usd_per_day"])
    pi_actual = float(actual_realized_margin_usd_per_day)

    lp_calibration_effect = pi_recal - pi_orig
    decision_opportunity = pi_alt - pi_recal
    execution_residual = pi_actual - pi_alt
    total_delta = pi_actual - pi_orig
    identity_residual = (lp_calibration_effect + decision_opportunity + execution_residual) - total_delta

    return {
        "provenance_class": "DERIVED",
        "case_order": ["orig_plan", "recal_plan", "feasible_alt", "actual"],
        "pi_orig_plan_usd_per_day": pi_orig,
        "pi_recal_plan_usd_per_day": pi_recal,
        "pi_feasible_alt_usd_per_day": pi_alt,
        "pi_actual_usd_per_day": pi_actual,
        "lp_calibration_effect_usd_per_day": lp_calibration_effect,
        "decision_time_opportunity_usd_per_day": decision_opportunity,
        "execution_and_exogenous_residual_usd_per_day": execution_residual,
        "total_delta_usd_per_day": total_delta,
        "identity_residual_usd_per_day": identity_residual,
        "po12b_nonzero_calibration_proven": abs(lp_calibration_effect) > 1.0,
        "cases": {
            "orig_plan": orig_lp,
            "recal_plan": recal_lp,
            "feasible_alt": alt_lp,
        },
    }
