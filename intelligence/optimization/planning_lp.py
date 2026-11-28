#!/usr/bin/env python3
"""Deliberately reduced Pyomo + HiGHS Planning LP for Refinery A v1 (WP-3A, EQ-09, ADR-0048).

Intentionally kept structurally reduced compared to the mechanistic World Kernel
(EQ-01..EQ-08):
- Linear base-plus-delta unit yield vectors (no 4-lump ODE integration)
- Linear volume-weighted blend indices for RVP and octane (no Chevron RVP^1.25
  or Ethyl RT-70 nonlinear interactions)
- Vintage-pinned lagged crude assays

This deliberate structural gap guarantees that UC-3 three-way backcasting isolates
a genuine, measurable LP calibration effect (`PO-12b`, `ENG-V08a`).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

import pyomo.environ as pyo


@dataclass(frozen=True)
class PlanningLPInputs:
    case_id: str
    branch_id: str
    provenance_class: str = "SCENARIO_ASSUMPTION"
    # Crude prices ($/bbl)
    price_crude_light: float = 74.0
    price_crude_med: float = 70.5
    price_crude_heavy: float = 65.0
    # Product prices ($/bbl)
    price_bob: float = 96.0
    price_ulsd: float = 104.0
    price_jet: float = 94.0
    price_resid: float = 61.0
    price_butane: float = 42.0
    # Operating / utility costs ($/bbl feed or $/t H2)
    cost_h2_per_t: float = 1650.0
    cost_var_cdu_per_bbl: float = 1.25
    cost_var_hcu_per_bbl: float = 3.40
    cost_var_fcc_per_bbl: float = 2.80
    # Active unit & utility bounds
    cdu_min_bpd: float = 105000.0
    cdu_max_bpd: float = 190000.0
    hcu_max_bpd: float = 40000.0
    hcu_min_bpd: float = 0.0
    fcc_max_bpd: float = 30000.0
    h2_hcu_headroom_t_per_day: float = 125.0
    hcu_h2_intensity_t_per_kbbl: float = 2.8907  # linear planning factor (t H2 per 1000 bbl VGO)
    # Linearized planning yield factors (deliberately lagged/reduced vs nonlinear kernel)
    hcu_ulsd_yield_vol: float = 0.430   # lagged planning estimate (mechanistic slate ~0.442)
    hcu_jet_yield_vol: float = 0.225
    hcu_naphtha_yield_vol: float = 0.310
    fcc_naphtha_yield_vol: float = 0.510
    fcc_lco_yield_vol: float = 0.175
    fcc_slurry_yield_vol: float = 0.075
    # Linearized gasoline blend constraints (deliberately linear RVP & AKI!)
    bob_rvp_max_psi: float = 9.00
    bob_aki_min: float = 84.2
    butane_max_vol_frac: float = 0.06
    # Forced HCU feed (for feasibility rejection tests like 30,001 bbl/day)
    fixed_hcu_bpd: float | None = None
    # Demand caps (bbl/day)
    demand_ulsd_max_bpd: float = 85000.0
    demand_bob_max_bpd: float = 95000.0

    def input_digest(self) -> str:
        return hashlib.sha256(
            json.dumps(self.__dict__, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()


def solve_planning_lp(inputs: PlanningLPInputs) -> dict[str, Any]:
    """Solve the reduced Refinery A Planning LP with Pyomo + HiGHS (feasibility tol 1e-7)."""
    m = pyo.ConcreteModel(name=f"ppc_planning_lp_{inputs.case_id}")

    # Decision variables (bbl/day)
    m.crude_light = pyo.Var(domain=pyo.NonNegativeReals, bounds=(0, 80000))
    m.crude_med = pyo.Var(domain=pyo.NonNegativeReals, bounds=(0, 120000))
    m.crude_heavy = pyo.Var(domain=pyo.NonNegativeReals, bounds=(0, 60000))

    m.vgo_to_hcu = pyo.Var(domain=pyo.NonNegativeReals, bounds=(inputs.hcu_min_bpd, inputs.hcu_max_bpd))
    m.vgo_to_fcc = pyo.Var(domain=pyo.NonNegativeReals, bounds=(0, inputs.fcc_max_bpd))

    m.butane_to_bob = pyo.Var(domain=pyo.NonNegativeReals, bounds=(0, 10000))
    m.bob_prod = pyo.Var(domain=pyo.NonNegativeReals, bounds=(0, inputs.demand_bob_max_bpd))
    m.ulsd_prod = pyo.Var(domain=pyo.NonNegativeReals, bounds=(0, inputs.demand_ulsd_max_bpd))
    m.jet_prod = pyo.Var(domain=pyo.NonNegativeReals)
    m.resid_prod = pyo.Var(domain=pyo.NonNegativeReals)

    # Total crude charge bounds
    cdu_total = m.crude_light + m.crude_med + m.crude_heavy
    m.c_cdu_min = pyo.Constraint(expr=cdu_total >= inputs.cdu_min_bpd)
    m.c_cdu_max = pyo.Constraint(expr=cdu_total <= inputs.cdu_max_bpd)

    # Crude slate VGO availability (linearized 27% / 33.5% / 35.75% VGO vol yields)
    vgo_avail = 0.270 * m.crude_light + 0.335 * m.crude_med + 0.3575 * m.crude_heavy
    m.c_vgo_bal = pyo.Constraint(expr=m.vgo_to_hcu + m.vgo_to_fcc <= vgo_avail)

    # Optional fixed HCU feed constraint (for infeasibility testing)
    if inputs.fixed_hcu_bpd is not None:
        m.c_hcu_fixed = pyo.Constraint(expr=m.vgo_to_hcu == inputs.fixed_hcu_bpd)

    # Shared H2 headroom constraint (EQ-07 linear approximation)
    h2_used_hcu = (m.vgo_to_hcu / 1000.0) * inputs.hcu_h2_intensity_t_per_kbbl
    m.c_h2_headroom = pyo.Constraint(expr=h2_used_hcu <= inputs.h2_hcu_headroom_t_per_day)

    # Straight-run naphtha, distillate, jet, resid balances
    sr_naphtha = 0.260 * m.crude_light + 0.170 * m.crude_med + 0.085 * m.crude_heavy
    sr_kero = 0.130 * m.crude_light + 0.100 * m.crude_med + 0.055 * m.crude_heavy
    sr_ago = 0.210 * m.crude_light + 0.170 * m.crude_med + 0.110 * m.crude_heavy
    sr_resid = 0.100 * m.crude_light + 0.205 * m.crude_med + 0.3875 * m.crude_heavy

    bob_base = sr_naphtha + inputs.hcu_naphtha_yield_vol * m.vgo_to_hcu + inputs.fcc_naphtha_yield_vol * m.vgo_to_fcc
    m.c_bob_bal = pyo.Constraint(expr=m.bob_prod == bob_base + m.butane_to_bob)
    m.c_butane_cap = pyo.Constraint(expr=m.butane_to_bob <= inputs.butane_max_vol_frac * m.bob_prod)

    # Deliberately LINEAR RVP blending (6.80 psi base, 52.0 psi n-butane) -> structurally diverges from Chevron RVP^1.25!
    m.c_rvp_linear = pyo.Constraint(
        expr=6.80 * bob_base + 52.0 * m.butane_to_bob <= inputs.bob_rvp_max_psi * m.bob_prod
    )
    # Deliberately LINEAR AKI blending (85.45 base, 92.0 butane)
    m.c_aki_linear = pyo.Constraint(
        expr=85.45 * bob_base + 92.0 * m.butane_to_bob >= inputs.bob_aki_min * m.bob_prod
    )

    m.c_ulsd_bal = pyo.Constraint(
        expr=m.ulsd_prod <= sr_ago + inputs.hcu_ulsd_yield_vol * m.vgo_to_hcu + inputs.fcc_lco_yield_vol * m.vgo_to_fcc
    )
    m.c_jet_bal = pyo.Constraint(expr=m.jet_prod == sr_kero + inputs.hcu_jet_yield_vol * m.vgo_to_hcu)
    m.c_resid_bal = pyo.Constraint(expr=m.resid_prod == sr_resid + inputs.fcc_slurry_yield_vol * m.vgo_to_fcc)

    # EQ-09 Daily gross margin objective ($/day)
    revenue = (
        inputs.price_bob * m.bob_prod
        + inputs.price_ulsd * m.ulsd_prod
        + inputs.price_jet * m.jet_prod
        + inputs.price_resid * m.resid_prod
    )
    feed_cost = (
        inputs.price_crude_light * m.crude_light
        + inputs.price_crude_med * m.crude_med
        + inputs.price_crude_heavy * m.crude_heavy
        + inputs.price_butane * m.butane_to_bob
    )
    var_cost = (
        inputs.cost_var_cdu_per_bbl * cdu_total
        + inputs.cost_var_hcu_per_bbl * m.vgo_to_hcu
        + inputs.cost_var_fcc_per_bbl * m.vgo_to_fcc
        + inputs.cost_h2_per_t * h2_used_hcu
    )
    m.obj = pyo.Objective(expr=revenue - feed_cost - var_cost, sense=pyo.maximize)

    solver = pyo.SolverFactory("appsi_highs")
    solver.highs_options["primal_feasibility_tolerance"] = 1e-7
    solver.highs_options["dual_feasibility_tolerance"] = 1e-7
    res = solver.solve(m, load_solutions=False)

    term = str(res.solver.termination_condition)
    if res.solver.termination_condition != pyo.TerminationCondition.optimal:
        return {
            "case_id": inputs.case_id,
            "branch_id": inputs.branch_id,
            "method_class": "PLANNING_LP",
            "output_provenance_class": "ESTIMATED",
            "feasibility_status": "INFEASIBLE",
            "termination_condition": term,
            "margin_usd_per_day": None,
            "setpoints": None,
            "input_digest": inputs.input_digest(),
        }

    m.solutions.load_from(res)
    bob_v = float(pyo.value(m.bob_prod))
    but_v = float(pyo.value(m.butane_to_bob))
    but_frac = (but_v / bob_v) if bob_v > 0.0 else 0.0
    linear_rvp = 6.80 * (1.0 - but_frac) + 52.0 * but_frac

    setpoints = {
        "crude_light_bpd": float(pyo.value(m.crude_light)),
        "crude_med_bpd": float(pyo.value(m.crude_med)),
        "crude_heavy_bpd": float(pyo.value(m.crude_heavy)),
        "cdu_total_bpd": float(pyo.value(cdu_total)),
        "hcu_feed_bpd": float(pyo.value(m.vgo_to_hcu)),
        "fcc_feed_bpd": float(pyo.value(m.vgo_to_fcc)),
        "bob_bpd": bob_v,
        "butane_to_bob_bpd": but_v,
        "butane_vol_frac": but_frac,
        "linear_bob_rvp_psi": linear_rvp,
        "ulsd_bpd": float(pyo.value(m.ulsd_prod)),
        "jet_bpd": float(pyo.value(m.jet_prod)),
        "resid_bpd": float(pyo.value(m.resid_prod)),
        "h2_used_hcu_t_per_day": float(pyo.value(h2_used_hcu)),
    }
    return {
        "case_id": inputs.case_id,
        "branch_id": inputs.branch_id,
        "method_class": "PLANNING_LP",
        "output_provenance_class": "ESTIMATED",
        "feasibility_status": "FEASIBLE",
        "termination_condition": term,
        "margin_usd_per_day": float(pyo.value(m.obj)),
        "setpoints": setpoints,
        "input_digest": inputs.input_digest(),
    }
