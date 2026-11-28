#!/usr/bin/env python3
"""WP-3A UC-3 Three-Way Fair Backcasting Attribution and Closed-Loop WP-1 Verification (EQ-09, PO-12b).

Decomposes total economic variance identically into:
  Delta_Pi_total = (Pi_recal_plan - Pi_orig_plan)        [LP calibration effect]
                 + (Pi_feasible_alt - Pi_recal_plan)     [decision-time opportunity]
                 + (Pi_actual - Pi_feasible_alt)         [execution and exogenous residual]
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
import math
from typing import Any

from generators import equations as eq
from intelligence.optimization.planning_lp import PlanningLPInputs, solve_planning_lp

_REQUIRED_SETPOINT_KEYS = (
    "hcu_feed_bpd",
    "cdu_total_bpd",
    "fcc_feed_bpd",
    "butane_vol_frac",
    "linear_bob_rvp_psi",
)


def _require_finite(name: str, value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"{name} must be a finite number, got {value!r}")
    return float(value)


def evaluate_lp_setpoints_in_wp1_physics(
    lp_result: Mapping[str, Any],
    inputs: PlanningLPInputs,
    compressor_circ_fraction: float,
    h2_allocable_t_per_day: float,
    rvp_cap_psi: float | None = None,
) -> dict[str, Any]:
    """Closed-loop check: bind LP setpoints to `inputs` and evaluate in mechanistic WP-1 EQ-05 & EQ-08 physics."""
    comp_frac = _require_finite("compressor_circ_fraction", compressor_circ_fraction)
    if not (0.0 <= comp_frac <= 1.0):
        raise ValueError(f"compressor_circ_fraction must be in [0, 1], got {comp_frac!r}")
    h2_alloc = _require_finite("h2_allocable_t_per_day", h2_allocable_t_per_day)
    if h2_alloc < 0.0:
        raise ValueError(f"h2_allocable_t_per_day must be non-negative, got {h2_alloc!r}")
    effective_rvp_cap = (
        inputs.bob_rvp_max_psi if rvp_cap_psi is None else _require_finite("rvp_cap_psi", rvp_cap_psi)
    )
    if effective_rvp_cap <= 0.0:
        raise ValueError(f"rvp_cap_psi must be positive, got {effective_rvp_cap!r}")

    if not isinstance(lp_result, Mapping):
        raise ValueError("lp_result must be a mapping")
    if lp_result.get("input_digest") != inputs.input_digest():
        raise ValueError(
            "lp_result input_digest does not match supplied PlanningLPInputs; cannot validate cross-scenario setpoints"
        )

    sp = lp_result.get("setpoints")
    if lp_result.get("feasibility_status") != "FEASIBLE" or sp is None:
        return {"closed_loop_feasible": False, "violations": ["LP_INFEASIBLE"]}
    if not isinstance(sp, Mapping):
        raise ValueError("lp_result['setpoints'] must be a mapping")
    missing = [k for k in _REQUIRED_SETPOINT_KEYS if k not in sp]
    if missing:
        raise ValueError(f"lp_result['setpoints'] missing required keys: {missing}")

    violations: list[str] = []
    hcu_feed = _require_finite("hcu_feed_bpd", sp["hcu_feed_bpd"])
    cdu_total = _require_finite("cdu_total_bpd", sp["cdu_total_bpd"])
    fcc_feed = _require_finite("fcc_feed_bpd", sp["fcc_feed_bpd"])
    linear_rvp = _require_finite("linear_bob_rvp_psi", sp["linear_bob_rvp_psi"])
    if cdu_total < inputs.cdu_min_bpd - 1e-6 or cdu_total > inputs.cdu_max_bpd + 1e-6:
        violations.append(
            f"CDU_BOUNDS_EXCEEDED ({cdu_total:.1f} outside [{inputs.cdu_min_bpd:.1f}, {inputs.cdu_max_bpd:.1f}])"
        )
    if fcc_feed > inputs.fcc_max_bpd + 1e-6:
        violations.append(f"FCC_CAP_EXCEEDED ({fcc_feed:.1f} > {inputs.fcc_max_bpd:.1f})")
    if hcu_feed < inputs.hcu_min_bpd - 1e-6 or hcu_feed > inputs.hcu_max_bpd + 1e-6:
        violations.append(
            f"HCU_SCENARIO_CAP_EXCEEDED ({hcu_feed:.1f} outside [{inputs.hcu_min_bpd:.1f}, {inputs.hcu_max_bpd:.1f}])"
        )
    if inputs.fixed_hcu_bpd is not None and abs(hcu_feed - inputs.fixed_hcu_bpd) > 1e-6:
        violations.append(f"HCU_FIXED_FEED_MISMATCH ({hcu_feed:.1f} != {inputs.fixed_hcu_bpd:.1f})")

    hcu_chk = eq.hcu_evaluate(
        requested_feed_bbl_per_day=hcu_feed,
        mech_cap_bbl_per_day=40000.0,
        compressor_circ_fraction=comp_frac,
        h2_allocable_t_per_day=h2_alloc,
        fixture_mode=True,
    )
    if not hcu_chk["feasible"]:
        violations.append(
            f"HCU_INFEASIBLE ({hcu_feed:.1f} > {hcu_chk['max_feed_bbl_per_day']:.1f} bbl/day)"
        )

    # Nonlinear Chevron RVP check on LP's butane blend fraction
    xb = _require_finite("butane_vol_frac", sp["butane_vol_frac"])
    if not (0.0 <= xb <= 1.0):
        raise ValueError(f"butane_vol_frac must be in [0, 1], got {xb!r}")
    nonlin_rvp = eq.chevron_rvp_psi([1.0 - xb, xb], [6.80, 52.0])
    rvp_exceeded = nonlin_rvp > effective_rvp_cap + 1e-9
    if rvp_exceeded:
        violations.append(
            f"NONLINEAR_CHEVRON_RVP_EXCEEDED (linear={linear_rvp:.3f}, chevron={nonlin_rvp:.3f} > {effective_rvp_cap:.2f})"
        )

    hcu_ulsd_bpd = float(hcu_chk["outputs"]["ulsd"]["volume_bbl_per_day"])
    return {
        "closed_loop_feasible": not violations,
        "violations": violations,
        "hcu_mechanistic_ulsd_bpd": hcu_ulsd_bpd,
        "hcu_mechanistic_ulsd_yield_vol": (hcu_ulsd_bpd / hcu_feed) if hcu_feed > 0.0 else 0.0,
        "hcu_mechanistic_max_feed_bpd": float(hcu_chk["max_feed_bbl_per_day"]),
        "chevron_rvp_psi": nonlin_rvp,
        "linear_rvp_psi": linear_rvp,
        "rvp_nonlinearity_gap_psi": nonlin_rvp - linear_rvp,
    }


def run_uc3_three_way_backcast(
    orig_inputs: PlanningLPInputs,
    recalibrated_hcu_ulsd_yield: float,
    recalibrated_butane_max_vol_frac: float,
    decision_alt_inputs: PlanningLPInputs,
    actual_realized_margin_usd_per_day: float,
    *,
    compressor_circ_fraction: float = 0.75,
    h2_allocable_t_per_day: float = 125.0,
    rvp_cap_psi: float | None = None,
) -> dict[str, Any]:
    """Execute EQ-09 three-way backcasting attribution and ground PO-12b calibration gap against WP-1 physics."""
    recal_ulsd = _require_finite("recalibrated_hcu_ulsd_yield", recalibrated_hcu_ulsd_yield)
    recal_butane = _require_finite("recalibrated_butane_max_vol_frac", recalibrated_butane_max_vol_frac)
    pi_actual = _require_finite("actual_realized_margin_usd_per_day", actual_realized_margin_usd_per_day)

    orig_lp = solve_planning_lp(orig_inputs)
    recal_inputs = replace(
        orig_inputs,
        case_id=f"{orig_inputs.case_id}-RECAL",
        delta_hcu_ulsd_yield_vol=recal_ulsd - orig_inputs.hcu_ulsd_yield_vol,
        butane_max_vol_frac=recal_butane,
    )
    recal_lp = solve_planning_lp(recal_inputs)
    alt_lp = solve_planning_lp(decision_alt_inputs)

    if any(r["feasibility_status"] != "FEASIBLE" for r in (orig_lp, recal_lp, alt_lp)):
        raise ValueError("All three backcasting cases must be feasible for EQ-09 attribution")

    orig_closed_loop = evaluate_lp_setpoints_in_wp1_physics(
        orig_lp,
        orig_inputs,
        compressor_circ_fraction=compressor_circ_fraction,
        h2_allocable_t_per_day=h2_allocable_t_per_day,
        rvp_cap_psi=rvp_cap_psi,
    )
    recal_closed_loop = evaluate_lp_setpoints_in_wp1_physics(
        recal_lp,
        recal_inputs,
        compressor_circ_fraction=compressor_circ_fraction,
        h2_allocable_t_per_day=h2_allocable_t_per_day,
        rvp_cap_psi=rvp_cap_psi,
    )

    pi_orig = float(orig_lp["margin_usd_per_day"])
    pi_recal = float(recal_lp["margin_usd_per_day"])
    pi_alt = float(alt_lp["margin_usd_per_day"])

    lp_calibration_effect = pi_recal - pi_orig
    decision_opportunity = pi_alt - pi_recal
    execution_residual = pi_actual - pi_alt
    total_delta = pi_actual - pi_orig
    identity_residual = (lp_calibration_effect + decision_opportunity + execution_residual) - total_delta

    # Ground PO-12b in actual WP-1 mechanistic discrepancy + closed-loop restoration (not an arbitrary scalar nudge):
    # original LP must show a genuine WP-1 physics gap (violation or mechanistic ULSD yield gap),
    # recalibrated LP must close WP-1 physics cleanly, and the EQ-09 calibration attribution must be non-zero.
    wp1_ulsd_yield = orig_closed_loop["hcu_mechanistic_ulsd_yield_vol"]
    orig_eff_ulsd = orig_inputs.hcu_ulsd_yield_vol + orig_inputs.delta_hcu_ulsd_yield_vol
    orig_has_wp1_gap = (not orig_closed_loop["closed_loop_feasible"]) or (abs(orig_eff_ulsd - wp1_ulsd_yield) > 1e-4)
    recal_matches_wp1_yield = abs(recal_ulsd - wp1_ulsd_yield) < abs(orig_eff_ulsd - wp1_ulsd_yield)
    po12b_world_truth_proven = (
        orig_has_wp1_gap
        and recal_closed_loop["closed_loop_feasible"]
        and recal_matches_wp1_yield
        and abs(lp_calibration_effect) > 1e-6
    )

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
        "wp1_hcu_ulsd_yield_vol": wp1_ulsd_yield,
        "orig_closed_loop": orig_closed_loop,
        "recal_closed_loop": recal_closed_loop,
        "po12b_nonzero_calibration_proven": po12b_world_truth_proven,
        "cases": {
            "orig_plan": orig_lp,
            "recal_plan": recal_lp,
            "feasible_alt": alt_lp,
        },
    }
