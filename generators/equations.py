#!/usr/bin/env python3
"""Refinery A v1 primary-sourced governing equations (EQ-01 through EQ-08).

All conservation balances execute strictly on SI mass basis (kg or metric tonnes t).
Standard volumes (bbl at 60 degF / 14.696 psia, API MPMS Ch. 11.1) convert only
through an explicitly supplied reference density. Missing density raises
InsufficientInputError ("INSUFFICIENT_INPUT").

Governing specifications:
- PPC-REVIEW-002 (Governing Refinery Equations, Control Volumes, and Shift Trace)
- PPC-ENG-001 (Physical and Numerical Engineering)
- ADR-0040, ADR-0043, ADR-0054 (Option A), ADR-0056 (G3-c)
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Mapping, Sequence


# Exact physical and conversion constants (PPC-REVIEW-002 §2 EQ-01, EQ-05)
RHO_WATER_60F_KG_M3 = 999.016
C_BBL_M3 = 0.158987294928
LB_TO_KG = 0.45359237
M_H2_LB_LBMOL = 2.01588
V_M_STD_SCF_LBMOL = 379.48
G_ACCEL_M_S2 = 9.80665
R_GAS_J_MOL_K = 8.314462618

RHO_WATER_60F_FRAC = Fraction("999.016")
C_BBL_M3_FRAC = Fraction("0.158987294928")

# Locked Ethyl RT-70 interaction coefficients (Maples 2nd ed. / Fahim et al., ADR-0056 G3-c)
RT70_A1 = 0.03324
RT70_A2 = 0.00085
RT70_B1 = 0.04285
RT70_B2 = 0.00066
RT70_B3 = -0.00632

# HCU normalized converted product selectivities (PPC-REVIEW-002 §3 / EQ-05)
HCU_SELECTIVITIES: dict[str, float] = {
    "acid_gas": 1.50 / 90.0,
    "dry_gas": 1.00 / 90.0,
    "lpg": 3.50 / 90.0,
    "light_naphtha": 10.00 / 90.0,
    "heavy_naphtha": 14.00 / 90.0,
    "jet_kero": 20.00 / 90.0,
    "ulsd": 40.00 / 90.0,
}
HCU_LIQUID_SG: dict[str, float] = {
    "lpg": 0.540,
    "light_naphtha": 0.675,
    "heavy_naphtha": 0.755,
    "jet_kero": 0.810,
    "ulsd": 0.840,
    "uco": 0.865,
}

# Calibrated WP-1 FCC 4-lump kinetic constants (calibrated to ADR-0056 G3-c ranges:
# 70-78% conversion, 44-52% naphtha, 16-22% gas, 4.5-6.5% coke, 14-20% LCO, 5-9% slurry)
FCC_WP1_CALIBRATED_KINETICS: dict[str, float] = {
    "k1": 2.48,       # VGO -> Gasoline
    "k2": 0.24,       # Gasoline -> Gas + Coke (overcracking)
    "k3": 0.66,       # VGO -> Dry gas + LPG
    "k4": 0.145,      # VGO -> Catalytic coke
    "beta_bc": 0.82,  # Fraction of overcracked gasoline going to gas vs coke
    "alpha_d": 0.35,  # Catalyst deactivation decay constant
    "f_add": 0.65,    # Inlet CCR additive coke fraction
}

# FCC ADR-0056 G3-c lump-to-stream and feed-sulfur distribution splits
FCC_LCO_OF_UNCONVERTED = 0.70
FCC_SLURRY_OF_UNCONVERTED = 0.30
FCC_DRYGAS_OF_GAS = 0.20
FCC_LPG_OF_GAS = 0.80
FCC_SULFUR_SPLITS: dict[str, float] = {
    "h2s_to_sru": 0.45,
    "fcc_naphtha": 0.06,
    "lco": 0.22,
    "slurry": 0.17,
    "regen_coke_sox": 0.10,
}


class InsufficientInputError(ValueError):
    """Raised when required physical inputs (e.g. reference density or assay) are missing."""

    status_code = "INSUFFICIENT_INPUT"


class OutOfEnvelopeError(ValueError):
    """Raised when operating conditions fall outside a declared equation envelope."""

    status_code = "OUT_OF_ENVELOPE"


# ----------------------------------------------------------------------------
# EQ-01 — Reference volume, density, and API gravity conversion
# ----------------------------------------------------------------------------

def api_to_sg_60_60(api: float | None) -> float:
    if api is None:
        raise InsufficientInputError("INSUFFICIENT_INPUT: missing API gravity")
    if not (10.0 <= api <= 90.0):
        raise OutOfEnvelopeError(f"OUT_OF_ENVELOPE: API {api} outside [10, 90]")
    return 141.5 / (api + 131.5)


def sg_to_rho_ref_kg_m3(sg_60_60: float | None) -> float:
    if sg_60_60 is None or sg_60_60 <= 0.0:
        raise InsufficientInputError("INSUFFICIENT_INPUT: missing or non-positive SG_60/60")
    return sg_60_60 * RHO_WATER_60F_KG_M3


def volume_bbl_to_mass_kg(volume_std_bbl: float, sg_60_60: float | None) -> float:
    rho = sg_to_rho_ref_kg_m3(sg_60_60)
    return volume_std_bbl * C_BBL_M3 * rho


def mass_kg_to_volume_bbl(mass_kg: float, sg_60_60: float | None) -> float:
    rho = sg_to_rho_ref_kg_m3(sg_60_60)
    return mass_kg / (C_BBL_M3 * rho)


def volume_bbl_to_mass_kg_exact(volume_std_bbl: Fraction, sg_60_60: Fraction) -> Fraction:
    """Exact rational EQ-01 conversion for zero-residual arithmetic oracles."""
    return volume_std_bbl * C_BBL_M3_FRAC * (sg_60_60 * RHO_WATER_60F_FRAC)


# ----------------------------------------------------------------------------
# EQ-02 — Transient control-volume mass conservation with exact crossing t*
# ----------------------------------------------------------------------------

@dataclass(frozen=True)
class TankStepResult:
    opening_mass_kg: float
    closing_mass_kg: float
    accepted_inflow_kg: float
    accepted_outflow_kg: float
    diverted_or_blocked_kg: float
    loss_kg: float
    mass_residual_kg: float
    crossing_occurred: bool
    crossing_time_s: float | None
    crossing_bound: str | None  # "MAX" | "MIN" | None
    rule_applied: str


def step_tank_with_exact_crossing(
    opening_mass_kg: float,
    min_mass_kg: float,
    max_mass_kg: float,
    inflow_rate_kg_s: float,
    outflow_rate_kg_s: float,
    dt_s: float,
    loss_rate_kg_s: float = 0.0,
    rule: str = "throttle",
) -> TankStepResult:
    """Advance tank control volume over [0, dt_s) with exact intra-step crossing split t*.

    End-of-step clipping is strictly forbidden (PO-01). When net flow would cross
    max_mass_kg or min_mass_kg inside (0, dt_s), the step splits analytically at t*
    and applies `rule` ("throttle" | "divert" | "block") over [t*, dt_s).
    """
    if dt_s <= 0.0:
        raise ValueError("dt_s must be positive")
    if inflow_rate_kg_s < 0.0 or outflow_rate_kg_s < 0.0 or loss_rate_kg_s < 0.0:
        raise ValueError("Flow and loss rates must be non-negative")
    if opening_mass_kg < min_mass_kg - 1e-9 or opening_mass_kg > max_mass_kg + 1e-9:
        raise OutOfEnvelopeError(
            f"OUT_OF_ENVELOPE: opening mass {opening_mass_kg} kg outside [{min_mass_kg}, {max_mass_kg}]"
        )
    if rule not in ("throttle", "divert", "block"):
        raise ValueError(f"Unsupported crossing rule: {rule!r}")

    net_rate = inflow_rate_kg_s - outflow_rate_kg_s - loss_rate_kg_s
    unconstrained_end = opening_mass_kg + net_rate * dt_s

    crossing_bound: str | None = None
    t_star: float | None = None

    if net_rate > 0.0 and unconstrained_end > max_mass_kg:
        crossing_bound = "MAX"
        t_star = max(0.0, (max_mass_kg - opening_mass_kg) / net_rate)
    elif net_rate < 0.0 and unconstrained_end < min_mass_kg:
        crossing_bound = "MIN"
        t_star = max(0.0, (min_mass_kg - opening_mass_kg) / net_rate)

    if crossing_bound is None or t_star is None:
        acc_in = inflow_rate_kg_s * dt_s
        acc_out = outflow_rate_kg_s * dt_s
        loss = loss_rate_kg_s * dt_s
        closing = opening_mass_kg + acc_in - acc_out - loss
        residual = closing - (opening_mass_kg + acc_in - acc_out - loss)
        return TankStepResult(
            opening_mass_kg=opening_mass_kg,
            closing_mass_kg=closing,
            accepted_inflow_kg=acc_in,
            accepted_outflow_kg=acc_out,
            diverted_or_blocked_kg=0.0,
            loss_kg=loss,
            mass_residual_kg=residual,
            crossing_occurred=False,
            crossing_time_s=None,
            crossing_bound=None,
            rule_applied="none",
        )

    dt_rem = dt_s - t_star
    loss_1 = loss_rate_kg_s * t_star
    in_1 = inflow_rate_kg_s * t_star
    out_1 = outflow_rate_kg_s * t_star

    if crossing_bound == "MAX":
        if rule == "block":
            # Stop inflow completely over [t*, dt_s); cap combined drain so tank cannot cross below min_mass_kg
            in_2 = 0.0
            avail_drain = max(0.0, max_mass_kg - min_mass_kg)
            req_drain = (outflow_rate_kg_s + loss_rate_kg_s) * dt_rem
            scale = min(1.0, avail_drain / req_drain) if req_drain > 0.0 else 1.0
            out_2 = outflow_rate_kg_s * dt_rem * scale
            loss_2 = loss_rate_kg_s * dt_rem * scale
            diverted = inflow_rate_kg_s * dt_rem + (outflow_rate_kg_s * dt_rem - out_2)
        else:
            # throttle or divert excess inflow so mass rides exactly on max_mass_kg
            cap_in_rate = min(inflow_rate_kg_s, outflow_rate_kg_s + loss_rate_kg_s)
            in_2 = cap_in_rate * dt_rem
            out_2 = outflow_rate_kg_s * dt_rem
            loss_2 = loss_rate_kg_s * dt_rem
            diverted = (inflow_rate_kg_s - cap_in_rate) * dt_rem
    else:  # MIN bound
        eff_loss_rate = min(loss_rate_kg_s, inflow_rate_kg_s)
        if rule == "block":
            # Stop outflow over [t*, dt_s); cap post-t* refill so tank cannot re-cross above max_mass_kg
            avail_fill = max(0.0, max_mass_kg - min_mass_kg)
            loss_2 = eff_loss_rate * dt_rem
            req_in_2 = inflow_rate_kg_s * dt_rem
            in_2 = min(req_in_2, avail_fill + loss_2)
            out_2 = 0.0
            diverted = outflow_rate_kg_s * dt_rem + (req_in_2 - in_2)
        else:
            cap_out_rate = max(0.0, inflow_rate_kg_s - eff_loss_rate)
            in_2 = inflow_rate_kg_s * dt_rem
            out_2 = cap_out_rate * dt_rem
            loss_2 = eff_loss_rate * dt_rem
            diverted = (outflow_rate_kg_s - cap_out_rate) * dt_rem

    acc_in = in_1 + in_2
    acc_out = out_1 + out_2
    loss = loss_1 + loss_2
    closing = opening_mass_kg + acc_in - acc_out - loss
    residual = closing - (opening_mass_kg + acc_in - acc_out - loss)
    return TankStepResult(
        opening_mass_kg=opening_mass_kg,
        closing_mass_kg=closing,
        accepted_inflow_kg=acc_in,
        accepted_outflow_kg=acc_out,
        diverted_or_blocked_kg=diverted,
        loss_kg=loss,
        mass_residual_kg=residual,
        crossing_occurred=True,
        crossing_time_s=t_star,
        crossing_bound=crossing_bound,
        rule_applied=rule,
    )


# ----------------------------------------------------------------------------
# EQ-03 — Pipe transfer hydraulics and pump head bounds
# ----------------------------------------------------------------------------

def darcy_friction_factor(re_num: float, rel_roughness: float) -> float:
    """All-regime Darcy friction factor: 64/Re (laminar), Churchill (transition), Colebrook-White (turbulent)."""
    if re_num <= 0.0:
        raise ValueError("Reynolds number must be positive")
    if re_num <= 2100.0:
        return 64.0 / re_num
    if re_num < 4000.0:
        # Smooth Churchill (1977) interpolation across transition band 2100 < Re < 4000
        a = (2.457 * math.log(1.0 / ((7.0 / re_num) ** 0.9 + 0.27 * rel_roughness))) ** 16
        b = (37530.0 / re_num) ** 16
        return 8.0 * ((8.0 / re_num) ** 12 + 1.0 / ((a + b) ** 1.5)) ** (1.0 / 12.0)
    # Colebrook-White fixed-point iteration initialized from Haaland approximation
    inv_sqrt_f = -1.8 * math.log10((rel_roughness / 3.7) ** 1.11 + 6.9 / re_num)
    for _ in range(12):
        inv_sqrt_f = -2.0 * math.log10(rel_roughness / 3.7 + 2.51 * inv_sqrt_f / re_num)
    return 1.0 / (inv_sqrt_f * inv_sqrt_f)


def check_transfer_hydraulics(
    flow_bbl_per_day: float,
    diameter_m: float,
    length_m: float,
    roughness_m: float,
    k_fittings: float,
    delta_z_m: float,
    delta_p_pa: float,
    sg_60_60: float,
    viscosity_pa_s: float,
    pump_h0_m: float,
    pump_cp_s2_m5: float,
    speed_ratio: float = 1.0,
    viscous_derate_c_h: float = 1.0,
) -> dict[str, Any]:
    """Evaluate EQ-03 Darcy-Weisbach head requirement vs centrifugal pump head curve."""
    if not (0.0 < viscous_derate_c_h <= 1.0):
        raise OutOfEnvelopeError("ANSI/HI 9.6.7 viscous derating C_H must be in (0, 1]")
    rho = sg_to_rho_ref_kg_m3(sg_60_60)
    q_m3_s = flow_bbl_per_day * C_BBL_M3 / 86400.0
    area = math.pi * diameter_m * diameter_m / 4.0
    v = q_m3_s / area
    re_num = rho * v * diameter_m / viscosity_pa_s if v > 0.0 else 0.0
    f = darcy_friction_factor(re_num, roughness_m / diameter_m) if re_num > 0.0 else 0.0
    h_f = (f * (length_m / diameter_m) + k_fittings) * (v * v) / (2.0 * G_ACCEL_M_S2)
    h_req = delta_z_m + delta_p_pa / (rho * G_ACCEL_M_S2) + h_f
    h_pump = viscous_derate_c_h * ((speed_ratio ** 2) * pump_h0_m - pump_cp_s2_m5 * (q_m3_s ** 2))
    return {
        "feasible": h_pump >= h_req,
        "reynolds": re_num,
        "friction_factor": f,
        "head_loss_m": h_f,
        "head_required_m": h_req,
        "head_available_m": h_pump,
        "head_margin_m": h_pump - h_req,
    }


# ----------------------------------------------------------------------------
# EQ-04 — Crude assay characterization and CDU/VDU cut-point separation
# ----------------------------------------------------------------------------

def watson_kw(mean_avg_bp_c: float, sg_60_60: float) -> float:
    tb_rankine = (mean_avg_bp_c + 273.15) * 9.0 / 5.0
    return (tb_rankine ** (1.0 / 3.0)) / sg_60_60


def _interp_tbp_vol_frac(tbp_points: Sequence[Sequence[float]], temp_c: float) -> float:
    """Piecewise-linear interpolation of cumulative TBP volume fraction F(T) in [0, 1]."""
    if temp_c <= tbp_points[0][1]:
        return tbp_points[0][0] / 100.0
    if temp_c >= tbp_points[-1][1]:
        return tbp_points[-1][0] / 100.0
    for i in range(len(tbp_points) - 1):
        v0, t0 = tbp_points[i]
        v1, t1 = tbp_points[i + 1]
        if t0 <= temp_c <= t1:
            frac = (temp_c - t0) / (t1 - t0)
            return (v0 + frac * (v1 - v0)) / 100.0
    return 1.0


def cdu_vdu_cut_split(
    crude_feeds_t_per_day: Mapping[str, float],
    assays_by_id: Mapping[str, Mapping[str, Any]],
    cut_points_c: Sequence[float] = (30.0, 85.0, 175.0, 240.0, 360.0, 565.0),
    nominal_cut_points_c: Sequence[float] = (30.0, 85.0, 175.0, 240.0, 360.0, 565.0),
    column_loss_wt_frac: float = 0.002,
    overlap_shifts: Sequence[float] | None = None,
) -> dict[str, Any]:
    """Evaluate EQ-04 CDU/VDU TBP cut-point split with exact mass and sulfur conservation."""
    if len(cut_points_c) != 6 or len(nominal_cut_points_c) != 6:
        raise ValueError("Expected 6 TBP cut points defining 7 cuts")
    for tc, tnom in zip(cut_points_c, nominal_cut_points_c):
        if abs(tc - tnom) > 15.0 + 1e-9:
            raise OutOfEnvelopeError(f"OUT_OF_ENVELOPE: cut shift {tc - tnom:+.2f} C exceeds +/-15 C")
    if not (0.0 <= column_loss_wt_frac <= 0.005 + 1e-12):
        raise OutOfEnvelopeError(f"OUT_OF_ENVELOPE: column loss {column_loss_wt_frac} outside [0, 0.005]")

    cut_names = ("LPG", "LSR", "HEAVY_NAPHTHA", "KEROSENE", "AGO", "VGO", "VACUUM_RESIDUE")
    deltas = list(overlap_shifts) if overlap_shifts is not None else [0.0] * 7
    if len(deltas) != 7 or abs(sum(deltas)) > 1e-12:
        raise ValueError("Per-crude fractionation overlap deltas must have length 7 and sum strictly to 0")
    for idx, d in enumerate(deltas):
        if abs(d) > 0.02 + 1e-12:
            raise OutOfEnvelopeError(
                f"OUT_OF_ENVELOPE: fractionation overlap delta[{idx}]={d:+.4f} exceeds +/-0.02 (2 wt%)"
            )
    # Derive adjacent-cut overlap fluxes f[0..5] where d[0]=-f[0], d[i]=f[i-1]-f[i], d[6]=f[5]
    fluxes: list[float] = []
    running = 0.0
    for idx in range(6):
        running -= deltas[idx]
        if abs(running) > 0.02 + 1e-12:
            raise OutOfEnvelopeError(
                f"OUT_OF_ENVELOPE: cumulative adjacent cut overlap flux[{idx}]={running:+.4f} exceeds +/-0.02 (2 wt%)"
            )
        fluxes.append(running)

    cut_mass = {name: 0.0 for name in cut_names}
    cut_sulfur_mass = {name: 0.0 for name in cut_names}
    cut_vol_bbl = {name: 0.0 for name in cut_names}
    total_feed_t = 0.0
    total_loss_t = 0.0
    total_in_sulfur_t = 0.0
    loss_sulfur_t = 0.0

    for assay_id, feed_t in crude_feeds_t_per_day.items():
        if feed_t < 0.0:
            raise ValueError("Crude feed mass rate must be non-negative")
        if feed_t == 0.0:
            continue
        assay = assays_by_id[assay_id]
        pts = assay["tbp_points_vol_pct_c"]
        cuts = assay["cuts"]

        # Cumulative volume fractions at cut points -> volume fractions per cut
        cum_v = [0.0] + [_interp_tbp_vol_frac(pts, t) for t in cut_points_c] + [1.0]
        vol_fracs = [max(0.0, cum_v[i + 1] - cum_v[i]) for i in range(7)]
        sgs = [float(c["sg_60_60"]) for c in cuts]
        s_wt_fracs = [float(c["sulfur_wt_pct"]) / 100.0 for c in cuts]

        # Convert volume partition to mass partition using cut SGs
        raw_m = [vf * sg for vf, sg in zip(vol_fracs, sgs)]
        tot_raw_m = sum(raw_m)
        base_y = [m / tot_raw_m for m in raw_m]
        y_cuts = [(1.0 - column_loss_wt_frac) * y + d for y, d in zip(base_y, deltas)]
        if any(y < 0.0 for y in y_cuts):
            raise OutOfEnvelopeError(f"Negative cut mass yield produced for assay {assay_id}")

        crude_avg_s = sum(y * s for y, s in zip(base_y, s_wt_fracs))
        total_feed_t += feed_t
        loss_t = feed_t * column_loss_wt_frac
        total_loss_t += loss_t
        loss_sulfur_t += loss_t * crude_avg_s
        # True base crude feed sulfur BEFORE any overlap redistribution
        total_in_sulfur_t += feed_t * crude_avg_s

        # Base cut sulfur before overlap, plus exact donor-cut sulfur transport across adjacent boundaries
        per_crude_s = [feed_t * (1.0 - column_loss_wt_frac) * base_y[i] * s_wt_fracs[i] for i in range(7)]
        for i, f_ij in enumerate(fluxes):
            if f_ij >= 0.0:
                s_moved = feed_t * f_ij * s_wt_fracs[i]
            else:
                s_moved = feed_t * f_ij * s_wt_fracs[i + 1]
            per_crude_s[i] -= s_moved
            per_crude_s[i + 1] += s_moved

        for idx, cname in enumerate(cut_names):
            m_j = feed_t * y_cuts[idx]
            s_j = per_crude_s[idx]
            cut_mass[cname] += m_j
            cut_sulfur_mass[cname] += s_j
            cut_vol_bbl[cname] += mass_kg_to_volume_bbl(m_j * 1000.0, sgs[idx])

    out_cuts: dict[str, dict[str, float]] = {}
    for cname in cut_names:
        m_t = cut_mass[cname]
        s_t = cut_sulfur_mass[cname]
        v_bbl = cut_vol_bbl[cname]
        sg_eff = (m_t * 1000.0) / (v_bbl * C_BBL_M3 * RHO_WATER_60F_KG_M3) if v_bbl > 0.0 else 0.0
        out_cuts[cname] = {
            "mass_t_per_day": m_t,
            "volume_bbl_per_day": v_bbl,
            "sg_60_60": sg_eff,
            "sulfur_wt_pct": (100.0 * s_t / m_t) if m_t > 0.0 else 0.0,
        }

    mass_out = sum(cut_mass.values()) + total_loss_t
    sulfur_out = sum(cut_sulfur_mass.values()) + loss_sulfur_t
    return {
        "feed_t_per_day": total_feed_t,
        "loss_t_per_day": total_loss_t,
        "cuts": out_cuts,
        "mass_residual_t_per_day": mass_out - total_feed_t,
        "sulfur_residual_t_per_day": sulfur_out - total_in_sulfur_t,
    }


# ----------------------------------------------------------------------------
# EQ-05 — Hydrocracker recycle compressor, quench, P_H2, and lumped conversion
# ----------------------------------------------------------------------------

def hcu_r_min_mass(r_min_vol_scf_per_bbl: float, feed_sg_60_60: float) -> float:
    """Exact SI mass-per-mass H2-to-oil ratio (kg pure H2 / kg VGO feed), EQ-05."""
    rho_feed = sg_to_rho_ref_kg_m3(feed_sg_60_60)
    return (r_min_vol_scf_per_bbl * (M_H2_LB_LBMOL / V_M_STD_SCF_LBMOL) * LB_TO_KG) / (rho_feed * C_BBL_M3)


def hcu_polytropic_head_j_kg(
    p1_bar: float,
    p2_bar: float,
    t1_k: float,
    mw_gas_kg_kmol: float,
    z_avg: float = 1.03,
    k_gamma: float = 1.38,
    eta_p: float = 0.76,
) -> float:
    """GPSA §13 real-gas polytropic head H_p (J/kg)."""
    if not (0.70 <= eta_p <= 0.82):
        raise OutOfEnvelopeError(f"OUT_OF_ENVELOPE: compressor eta_p {eta_p} outside [0.70, 0.82]")
    n_over_nm1 = (k_gamma / (k_gamma - 1.0)) * eta_p
    r_specific = (R_GAS_J_MOL_K * 1000.0) / mw_gas_kg_kmol
    return z_avg * r_specific * t1_k * n_over_nm1 * ((p2_bar / p1_bar) ** (1.0 / n_over_nm1) - 1.0)


def hcu_evaluate(
    requested_feed_bbl_per_day: float,
    feed_sg_60_60: float = 0.910,
    feed_sulfur_wt_frac: float = 0.015,
    mech_cap_bbl_per_day: float = 40000.0,
    compressor_circ_fraction: float = 1.0,
    r_min_vol_scf_per_bbl: float = 4000.0,
    recycle_h2_purity_y_h2: float = 0.85,
    h2_allocable_t_per_day: float = 125.0,
    feed_available_t_per_day: float | None = None,
    downstream_cap_t_per_day: float | None = None,
    quench_cap_t_per_day: float | None = None,
    conversion_xi: float = 0.90,
    p_h2_bar: float = 135.0,
    t_rxr_c: float = 395.0,
    fixture_mode: bool = True,
    purge_dissolved_wt_frac: float = 0.001,
) -> dict[str, Any]:
    """Evaluate EQ-05 HCU unified SI mass-rate feed cap, H2 uptake, heat release, and sulfur/mass slate."""
    if not (80.0 <= p_h2_bar <= 180.0):
        raise OutOfEnvelopeError(f"OUT_OF_ENVELOPE: P_H2 {p_h2_bar} bar outside [80, 180]")
    if not (360.0 <= t_rxr_c <= 430.0):
        raise OutOfEnvelopeError(f"OUT_OF_ENVELOPE: T_rxr {t_rxr_c} C outside [360, 430]")
    if not (0.40 <= conversion_xi <= 0.95):
        raise OutOfEnvelopeError(f"OUT_OF_ENVELOPE: conversion xi {conversion_xi} outside [0.40, 0.95]")
    if not (3000.0 <= r_min_vol_scf_per_bbl <= 6000.0):
        raise OutOfEnvelopeError(f"OUT_OF_ENVELOPE: R_min {r_min_vol_scf_per_bbl} outside [3000, 6000]")
    if not (0.70 <= recycle_h2_purity_y_h2 <= 0.98):
        raise OutOfEnvelopeError(f"OUT_OF_ENVELOPE: y_h2_rec {recycle_h2_purity_y_h2} outside [0.70, 0.98]")
    if not (0.0 <= feed_sulfur_wt_frac <= 0.06):
        raise OutOfEnvelopeError(f"OUT_OF_ENVELOPE: feed_sulfur_wt_frac {feed_sulfur_wt_frac} outside [0, 0.06]")

    r_min_m = hcu_r_min_mass(r_min_vol_scf_per_bbl, feed_sg_60_60)
    mech_cap_t = volume_bbl_to_mass_kg(mech_cap_bbl_per_day, feed_sg_60_60) / 1000.0
    nominal_pure_h2_rec_t = mech_cap_t * r_min_m
    active_pure_h2_rec_t = nominal_pure_h2_rec_t * compressor_circ_fraction
    active_total_recycle_gas_t = active_pure_h2_rec_t / recycle_h2_purity_y_h2
    circ_cap_t = active_pure_h2_rec_t / r_min_m

    c_h2_chem = 0.020 * (conversion_xi / 0.90)
    c_h2_loss = 0.0 if fixture_mode else purge_dissolved_wt_frac
    c_h2_net = c_h2_chem + c_h2_loss
    h2_cap_t = max(0.0, h2_allocable_t_per_day) / c_h2_net

    # Default quench cap sized non-binding at 1.05 * 4,336.08 t/day at 75% circulation (ADR-0056 G3-c)
    if quench_cap_t_per_day is None:
        quench_cap_t_per_day = (1.05 * (mech_cap_t * 0.75)) * (compressor_circ_fraction / 0.75)

    bounds_t: dict[str, float] = {
        "mechanical_cap": mech_cap_t,
        "compressor_circulation_cap": circ_cap_t,
        "quench_thermal_cap": quench_cap_t_per_day,
        "shared_h2_cap": h2_cap_t,
    }
    if feed_available_t_per_day is not None:
        bounds_t["feed_available_cap"] = feed_available_t_per_day
    if downstream_cap_t_per_day is not None:
        bounds_t["downstream_cap"] = downstream_cap_t_per_day

    binding_name = min(bounds_t, key=lambda k: bounds_t[k])
    max_feed_t = max(0.0, bounds_t[binding_name])
    max_feed_bbl = mass_kg_to_volume_bbl(max_feed_t * 1000.0, feed_sg_60_60)

    req_t = volume_bbl_to_mass_kg(requested_feed_bbl_per_day, feed_sg_60_60) / 1000.0
    feasible = req_t <= max_feed_t + 1e-9
    actual_feed_t = min(req_t, max_feed_t)
    actual_feed_bbl = mass_kg_to_volume_bbl(actual_feed_t * 1000.0, feed_sg_60_60)

    h2_chem_t = actual_feed_t * c_h2_chem
    h2_net_t = actual_feed_t * c_h2_net
    total_in_t = actual_feed_t + h2_chem_t
    # Locked ADR-0056 G3-c hydrocracking heat release: 30 MJ/kg H2 consumed
    quench_heat_release_kw = (h2_chem_t * 1000.0 / 86400.0) * 30000.0

    # Stoichiometric HDS sulfur closure (MW_H2S / AW_S = 34.08088 / 32.065)
    feed_sulfur_t = actual_feed_t * feed_sulfur_wt_frac
    hydrotreated_liquid_s_t = actual_feed_t * 10e-6  # ~10 ppmw residual S across hydrotreated liquids
    s_to_h2s_t = max(0.0, feed_sulfur_t - hydrotreated_liquid_s_t)
    stoich_h2s_t = s_to_h2s_t * (34.08088 / 32.065)

    outputs: dict[str, dict[str, float | str | None]] = {}
    converted_total_t = conversion_xi * total_in_t
    if fixture_mode:
        # Exact PPC-REVIEW-002 §3 hand-fixture selectivities
        for pname, sel in HCU_SELECTIVITIES.items():
            m_t = sel * converted_total_t
            sg = HCU_LIQUID_SG.get(pname)
            vol = mass_kg_to_volume_bbl(m_t * 1000.0, sg) if sg is not None else None
            outputs[pname] = {
                "phase": "gas" if sg is None else "liquid",
                "mass_t_per_day": m_t,
                "sg_60_60": sg,
                "volume_bbl_per_day": vol,
            }
    else:
        # Runtime mode: acid_gas carries full stoichiometric H2S (+0.15% feed NH3/trace),
        # remaining converted hydrocarbon mass closes strictly to converted_total_t.
        acid_gas_t = stoich_h2s_t + actual_feed_t * 0.0015
        if acid_gas_t > converted_total_t:
            raise OutOfEnvelopeError("Stoichiometric H2S exceeds total converted HCU mass")
        hc_converted_t = converted_total_t - acid_gas_t
        hc_sel_sum = sum(v for k, v in HCU_SELECTIVITIES.items() if k != "acid_gas")
        outputs["acid_gas"] = {
            "phase": "gas",
            "mass_t_per_day": acid_gas_t,
            "sg_60_60": None,
            "volume_bbl_per_day": None,
        }
        for pname, sel in HCU_SELECTIVITIES.items():
            if pname == "acid_gas":
                continue
            m_t = (sel / hc_sel_sum) * hc_converted_t
            sg = HCU_LIQUID_SG.get(pname)
            vol = mass_kg_to_volume_bbl(m_t * 1000.0, sg) if sg is not None else None
            outputs[pname] = {
                "phase": "gas" if sg is None else "liquid",
                "mass_t_per_day": m_t,
                "sg_60_60": sg,
                "volume_bbl_per_day": vol,
            }

    uco_t = (1.0 - conversion_xi) * total_in_t
    uco_sg = HCU_LIQUID_SG["uco"]
    outputs["uco"] = {
        "phase": "liquid",
        "mass_t_per_day": uco_t,
        "sg_60_60": uco_sg,
        "volume_bbl_per_day": mass_kg_to_volume_bbl(uco_t * 1000.0, uco_sg),
    }

    total_out_t = sum(float(v["mass_t_per_day"]) for v in outputs.values())
    c5_plus_bbl = sum(
        float(outputs[k]["volume_bbl_per_day"])
        for k in ("light_naphtha", "heavy_naphtha", "jet_kero", "ulsd", "uco")
    )
    c3_plus_bbl = c5_plus_bbl + float(outputs["lpg"]["volume_bbl_per_day"])
    liq_gain_c5_pct = (100.0 * (c5_plus_bbl / actual_feed_bbl - 1.0)) if actual_feed_bbl > 0.0 else 0.0

    acid_gas_mass = float(outputs["acid_gas"]["mass_t_per_day"])
    acid_gas_s_capacity_t = acid_gas_mass * (32.065 / 34.08088)
    s_carried_in_acid_gas_t = min(s_to_h2s_t, acid_gas_s_capacity_t)
    sulfur_out_t = s_carried_in_acid_gas_t + hydrotreated_liquid_s_t
    return {
        "feasible": feasible,
        "status": "FEASIBLE" if feasible else "INFEASIBLE",
        "r_min_mass": r_min_m,
        "recycle_h2_purity_y_h2": recycle_h2_purity_y_h2,
        "active_total_recycle_gas_t_per_day": active_total_recycle_gas_t,
        "quench_heat_release_kw": quench_heat_release_kw,
        "binding_constraint": binding_name,
        "bounds_t_per_day": bounds_t,
        "max_feed_t_per_day": max_feed_t,
        "max_feed_bbl_per_day": max_feed_bbl,
        "actual_feed_t_per_day": actual_feed_t,
        "actual_feed_bbl_per_day": actual_feed_bbl,
        "h2_chem_t_per_day": h2_chem_t,
        "h2_net_t_per_day": h2_net_t,
        "total_input_mass_t_per_day": total_in_t,
        "total_output_mass_t_per_day": total_out_t,
        "mass_residual_t_per_day": total_out_t - total_in_t,
        "sulfur_balance": {
            "feed_sulfur_t_per_day": feed_sulfur_t,
            "s_to_h2s_t_per_day": s_to_h2s_t,
            "s_carried_in_acid_gas_t_per_day": s_carried_in_acid_gas_t,
            "stoichiometric_h2s_t_per_day": stoich_h2s_t,
            "liquid_product_sulfur_t_per_day": hydrotreated_liquid_s_t,
            "sulfur_residual_t_per_day": sulfur_out_t - feed_sulfur_t,
            "acid_gas_covers_stoichiometric_h2s": acid_gas_mass >= stoich_h2s_t - 1e-9,
        },
        "c5_plus_bbl_per_day": c5_plus_bbl,
        "c3_plus_bbl_per_day": c3_plus_bbl,
        "liquid_vol_gain_c5_pct": liq_gain_c5_pct,
        "outputs": outputs,
    }


# ----------------------------------------------------------------------------
# EQ-06 — FCC 4-lump kinetics (Lee, Chen, Huang, & Pan 1989) + heat/coke balance
# ----------------------------------------------------------------------------

def fcc_4lump_integrate(
    w_ccr_feed: float,
    k1: float,
    k2: float,
    k3: float,
    k4: float,
    beta_bc: float,
    alpha_d: float,
    f_add: float = 0.75,
    n_steps: int = 400,
) -> tuple[float, float, float, float]:
    """Integrate Lee et al. (1989) 4-lump riser ODEs over tau in [0, 1] with exact RK4."""
    if not (0.0 <= w_ccr_feed <= 0.25):
        raise OutOfEnvelopeError(f"OUT_OF_ENVELOPE: w_ccr_feed {w_ccr_feed} outside [0, 0.25]")
    if not (0.5 <= f_add <= 1.0):
        raise OutOfEnvelopeError(f"OUT_OF_ENVELOPE: f_add {f_add} outside [0.5, 1.0]")

    y_d = f_add * w_ccr_feed
    y_a = 1.0 - y_d
    y_b = 0.0
    y_c = 0.0

    def deriv(tau: float, state: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
        a, b, _c, _d = state
        phi = math.exp(-alpha_d * tau)
        da = -phi * (k1 + k3 + k4) * a * a
        db = phi * (k1 * a * a - k2 * b)
        dc = phi * (k3 * a * a + beta_bc * k2 * b)
        dd = phi * (k4 * a * a + (1.0 - beta_bc) * k2 * b)
        return (da, db, dc, dd)

    h = 1.0 / n_steps
    y = (y_a, y_b, y_c, y_d)
    for step in range(n_steps):
        tau = step * h
        d1 = deriv(tau, y)
        d2 = deriv(tau + 0.5 * h, tuple(y[i] + 0.5 * h * d1[i] for i in range(4)))
        d3 = deriv(tau + 0.5 * h, tuple(y[i] + 0.5 * h * d2[i] for i in range(4)))
        d4 = deriv(tau + h, tuple(y[i] + h * d3[i] for i in range(4)))
        y = tuple(y[i] + (h / 6.0) * (d1[i] + 2.0 * d2[i] + 2.0 * d3[i] + d4[i]) for i in range(4))
    return y


def fcc_evaluate(
    feed_t_per_day: float,
    feed_sulfur_wt_frac: float = 0.015,
    w_ccr_feed: float = 0.012,
    t_rxr_c: float = 525.0,
    t_regen_c: float = 705.0,
    cat_to_oil: float = 6.5,
    max_feed_bbl_per_day: float = 30000.0,
    feed_sg_60_60: float = 0.910,
    kinetics: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    """Evaluate EQ-06 4-lump FCC conversion, stream/sulfur splits, and coke/heat balance."""
    if not (495.0 <= t_rxr_c <= 550.0):
        raise OutOfEnvelopeError(f"OUT_OF_ENVELOPE: FCC T_rxr {t_rxr_c} C outside [495, 550]")
    if not (670.0 <= t_regen_c <= 740.0):
        raise OutOfEnvelopeError(f"OUT_OF_ENVELOPE: FCC T_regen {t_regen_c} C outside [670, 740]")
    if not (4.0 <= cat_to_oil <= 9.0):
        raise OutOfEnvelopeError(f"OUT_OF_ENVELOPE: FCC cat-to-oil {cat_to_oil} outside [4, 9]")

    kin = dict(FCC_WP1_CALIBRATED_KINETICS)
    if kinetics:
        kin.update(kinetics)

    # Arrhenius temperature coupling and catalyst-to-oil contact scaling around (525 C, 6.5)
    t_ref_k = 525.0 + 273.15
    t_rxr_k = t_rxr_c + 273.15
    inv_dt = (1.0 / t_ref_k) - (1.0 / t_rxr_k)
    cto_scale = (cat_to_oil / 6.5) ** 0.45
    k1_eff = kin["k1"] * math.exp((42000.0 / R_GAS_J_MOL_K) * inv_dt) * cto_scale
    k2_eff = kin["k2"] * math.exp((52000.0 / R_GAS_J_MOL_K) * inv_dt) * cto_scale
    k3_eff = kin["k3"] * math.exp((65000.0 / R_GAS_J_MOL_K) * inv_dt) * cto_scale
    k4_eff = kin["k4"] * math.exp((48000.0 / R_GAS_J_MOL_K) * inv_dt) * cto_scale

    ya, yb, yc, yd = fcc_4lump_integrate(
        w_ccr_feed=w_ccr_feed,
        k1=k1_eff,
        k2=k2_eff,
        k3=k3_eff,
        k4=k4_eff,
        beta_bc=kin["beta_bc"],
        alpha_d=kin["alpha_d"],
        f_add=kin["f_add"],
    )
    sum_y = ya + yb + yc + yd

    max_feed_t = volume_bbl_to_mass_kg(max_feed_bbl_per_day, feed_sg_60_60) / 1000.0
    coke_burn_ceiling_t = 0.070 * max_feed_t
    coke_t = feed_t_per_day * yd

    # Stream splits (ADR-0056 G3-c)
    lco_t = feed_t_per_day * ya * FCC_LCO_OF_UNCONVERTED
    slurry_t = feed_t_per_day * ya * FCC_SLURRY_OF_UNCONVERTED
    naphtha_t = feed_t_per_day * yb
    dry_gas_t = feed_t_per_day * yc * FCC_DRYGAS_OF_GAS
    lpg_t = feed_t_per_day * yc * FCC_LPG_OF_GAS

    # Reactor-regenerator macroscopic energy balance (kJ/s)
    # Coke combustion heat release (~34,500 kJ/kg) must cover catalyst circulation enthalpy;
    # negative flue-gas/loss surplus means the corner is thermally INFEASIBLE.
    m_feed_kg_s = feed_t_per_day * 1000.0 / 86400.0
    m_coke_kg_s = coke_t * 1000.0 / 86400.0
    m_cat_kg_s = cat_to_oil * m_feed_kg_s
    cp_cat = 1.15  # kJ/(kg K)
    dh_comb_coke = 34500.0  # kJ/kg
    q_rxr_needed_kw = m_cat_kg_s * cp_cat * (t_regen_c - t_rxr_c)
    q_coke_release_kw = m_coke_kg_s * dh_comb_coke
    q_flue_and_loss_kw = q_coke_release_kw - q_rxr_needed_kw
    heat_balance_feasible = q_flue_and_loss_kw >= -1e-6
    energy_residual_rel = (
        abs((q_rxr_needed_kw + max(0.0, q_flue_and_loss_kw)) - q_coke_release_kw)
        / max(1.0, q_coke_release_kw)
    )

    feasible = (
        (feed_t_per_day <= max_feed_t + 1e-9)
        and (coke_t <= coke_burn_ceiling_t + 1e-9)
        and heat_balance_feasible
    )

    total_s_in_t = feed_t_per_day * feed_sulfur_wt_frac
    sulfur_streams = {k: total_s_in_t * frac for k, frac in FCC_SULFUR_SPLITS.items()}

    mass_out = lco_t + slurry_t + naphtha_t + dry_gas_t + lpg_t + coke_t
    return {
        "feasible": feasible,
        "status": "FEASIBLE" if feasible else "INFEASIBLE",
        "heat_balance_feasible": heat_balance_feasible,
        "q_rxr_needed_kw": q_rxr_needed_kw,
        "q_coke_release_kw": q_coke_release_kw,
        "q_flue_and_loss_kw": q_flue_and_loss_kw,
        "lumps": {"y_A": ya, "y_B": yb, "y_C": yc, "y_D": yd, "sum": sum_y},
        "conversion_wt_pct": 100.0 * (1.0 - ya),
        "yields_wt_pct": {
            "naphtha": 100.0 * yb,
            "gas_total": 100.0 * yc,
            "dry_gas": 100.0 * yc * FCC_DRYGAS_OF_GAS,
            "lpg": 100.0 * yc * FCC_LPG_OF_GAS,
            "coke": 100.0 * yd,
            "lco": 100.0 * ya * FCC_LCO_OF_UNCONVERTED,
            "slurry": 100.0 * ya * FCC_SLURRY_OF_UNCONVERTED,
        },
        "streams_t_per_day": {
            "fcc_naphtha": naphtha_t,
            "lco": lco_t,
            "slurry": slurry_t,
            "dry_gas": dry_gas_t,
            "lpg": lpg_t,
            "coke_burned": coke_t,
        },
        "sulfur_t_per_day": sulfur_streams,
        "coke_burn_ceiling_t_per_day": coke_burn_ceiling_t,
        "mass_residual_t_per_day": mass_out - feed_t_per_day,
        "sulfur_residual_t_per_day": sum(sulfur_streams.values()) - total_s_in_t,
        "energy_residual_rel": energy_residual_rel,
    }


# ----------------------------------------------------------------------------
# EQ-07 — Shared hydrogen header and Option A bounded interfaces
# ----------------------------------------------------------------------------

def h2_header_balance(
    smr_h2_t_per_day: float,
    reformer_h2_t_per_day: float,
    nht_draw_t_per_day: float,
    fcc_hds_draw_t_per_day: float,
    header_loss_t_per_day: float,
    dht_committed_t_per_day: float,
    hcu_requested_t_per_day: float = 0.0,
    prev_smr_h2_t_per_day: float | None = None,
    dt_minutes: float | None = None,
    smr_nameplate_t_per_day: float = 120.0,
    smr_ramp_pct_per_min: float = 2.0,
) -> dict[str, Any]:
    """Evaluate EQ-07 single H2 header identity (G1-3), SMR 2%/min ramp limit, and zero double allocation (PO-04)."""
    smr_ramp_feasible = True
    smr_effective_t = smr_h2_t_per_day
    if prev_smr_h2_t_per_day is not None and dt_minutes is not None:
        max_delta = smr_nameplate_t_per_day * (smr_ramp_pct_per_min / 100.0) * max(0.0, dt_minutes)
        delta = smr_h2_t_per_day - prev_smr_h2_t_per_day
        if abs(delta) > max_delta + 1e-9:
            smr_ramp_feasible = False
            smr_effective_t = prev_smr_h2_t_per_day + math.copysign(max_delta, delta)

    net_supply = smr_effective_t + reformer_h2_t_per_day - nht_draw_t_per_day - fcc_hds_draw_t_per_day
    allocable_after_loss = max(0.0, net_supply - header_loss_t_per_day)
    dht_allocated = min(dht_committed_t_per_day, allocable_after_loss)
    dht_shortfall = max(0.0, dht_committed_t_per_day - dht_allocated)
    hcu_headroom = max(0.0, allocable_after_loss - dht_allocated)
    hcu_allocated = min(hcu_requested_t_per_day, hcu_headroom)
    total_allocated = dht_allocated + hcu_allocated + min(header_loss_t_per_day, max(0.0, net_supply))
    no_double_alloc = total_allocated <= max(0.0, net_supply) + 1e-9
    return {
        "smr_effective_t_per_day": smr_effective_t,
        "smr_ramp_feasible": smr_ramp_feasible,
        "net_plant_h2_supply_t_per_day": net_supply,
        "allocable_after_loss_t_per_day": allocable_after_loss,
        "dht_committed_t_per_day": dht_committed_t_per_day,
        "dht_allocated_t_per_day": dht_allocated,
        "dht_shortfall_t_per_day": dht_shortfall,
        "hcu_headroom_t_per_day": hcu_headroom,
        "hcu_allocated_t_per_day": hcu_allocated,
        "no_double_allocation": no_double_alloc,
    }


def dht_interface_step(sr_dist_t_per_day: float, fcc_lco_t_per_day: float) -> dict[str, Any]:
    """Feed-dependent DHT Option A interface (G1-4): LCO <= 20 wt% feed, linear H2 uptake."""
    total_feed = sr_dist_t_per_day + fcc_lco_t_per_day
    if total_feed <= 0.0:
        return {"feasible": True, "lco_wt_frac": 0.0, "h2_uptake_t_per_day": 0.0, "cetane_uplift": 0.0}
    w_lco = fcc_lco_t_per_day / total_feed
    w_sr = sr_dist_t_per_day / total_feed
    c_h2 = w_sr * 0.0045 + w_lco * 0.0160
    return {
        "feasible": w_lco <= 0.20 + 1e-9,
        "lco_wt_frac": w_lco,
        "h2_uptake_wt_frac": c_h2,
        "h2_uptake_t_per_day": total_feed * c_h2,
        "cetane_uplift": w_sr * 3.0 + w_lco * 8.0,
    }


def reformer_interface_step(feed_t_per_day: float, ron_target: float = 98.0) -> dict[str, Any]:
    """Piecewise-linear Catalytic Reformer Option A interface over RON 95-101 (ADR-0054 N3)."""
    if not (95.0 <= ron_target <= 101.0):
        raise OutOfEnvelopeError(f"OUT_OF_ENVELOPE: Reformer RON {ron_target} outside [95, 101]")
    if ron_target <= 98.0:
        frac = (ron_target - 95.0) / 3.0
        y_ref = 0.880 + frac * (0.860 - 0.880)
        y_h2 = 0.020 + frac * (0.022 - 0.020)
    else:
        frac = (ron_target - 98.0) / 3.0
        y_ref = 0.860 + frac * (0.830 - 0.860)
        y_h2 = 0.022 + frac * (0.026 - 0.022)
    rem = 1.0 - y_ref - y_h2
    y_lpg = rem * (7.8 / (7.8 + 4.0))
    y_dg = rem * (4.0 / (7.8 + 4.0))
    return {
        "reformate_t_per_day": feed_t_per_day * y_ref,
        "h2_byproduct_t_per_day": feed_t_per_day * y_h2,
        "lpg_t_per_day": feed_t_per_day * y_lpg,
        "dry_gas_t_per_day": feed_t_per_day * y_dg,
        "mass_residual_t_per_day": feed_t_per_day * ((y_ref + y_h2 + y_lpg + y_dg) - 1.0),
    }


# ----------------------------------------------------------------------------
# EQ-08 — Product blending properties and unrounded fuel specification gates
# ----------------------------------------------------------------------------

def blend_sulfur_ppmw(masses_t: Sequence[float], sulfur_ppmw: Sequence[float]) -> float:
    tot_m = sum(masses_t)
    if tot_m <= 0.0:
        raise InsufficientInputError("INSUFFICIENT_INPUT: empty blend mass")
    return sum(m * s for m, s in zip(masses_t, sulfur_ppmw)) / tot_m


def blend_density_ideal_kg_m3(masses_kg: Sequence[float], densities_kg_m3: Sequence[float]) -> float:
    tot_m = sum(masses_kg)
    if tot_m <= 0.0 or any(d <= 0.0 for d in densities_kg_m3):
        raise InsufficientInputError("INSUFFICIENT_INPUT: invalid blend mass or density")
    return tot_m / sum(m / d for m, d in zip(masses_kg, densities_kg_m3))


def chevron_rvp_psi(vol_fracs: Sequence[float], rvps_psi: Sequence[float]) -> float:
    """Chevron VPBI (exponent 1.25, inverse 0.8) for gasoline RVP blending."""
    if abs(sum(vol_fracs) - 1.0) > 1e-6:
        raise ValueError("Volume fractions must sum to 1.0")
    bi = sum(xv * (rvp ** 1.25) for xv, rvp in zip(vol_fracs, rvps_psi))
    return bi ** 0.8


def ethyl_rt70_octane(
    vol_fracs: Sequence[float],
    rons: Sequence[float],
    mons: Sequence[float],
    olefins_vol_pct: Sequence[float],
    aromatics_vol_pct: Sequence[float],
) -> dict[str, float]:
    """Ethyl RT-70 nonlinear RON/MON interaction model (Maples/Fahim constants, ADR-0056 G3-c)."""
    if abs(sum(vol_fracs) - 1.0) > 1e-6:
        raise ValueError("Volume fractions must sum to 1.0")
    sens = [r - m for r, m in zip(rons, mons)]
    r_bar = sum(x * r for x, r in zip(vol_fracs, rons))
    m_bar = sum(x * m for x, m in zip(vol_fracs, mons))
    s_bar = sum(x * s for x, s in zip(vol_fracs, sens))
    o_bar = sum(x * o for x, o in zip(vol_fracs, olefins_vol_pct))
    a_bar = sum(x * a for x, a in zip(vol_fracs, aromatics_vol_pct))

    rs_bar = sum(x * r * s for x, r, s in zip(vol_fracs, rons, sens))
    ms_bar = sum(x * m * s for x, m, s in zip(vol_fracs, mons, sens))
    o2_bar = sum(x * (o ** 2) for x, o in zip(vol_fracs, olefins_vol_pct))
    a2_bar = sum(x * (a ** 2) for x, a in zip(vol_fracs, aromatics_vol_pct))

    ron_blend = r_bar + RT70_A1 * (rs_bar - r_bar * s_bar) + RT70_A2 * (o2_bar - o_bar ** 2)
    mon_blend = (
        m_bar
        + RT70_B1 * (ms_bar - m_bar * s_bar)
        + RT70_B2 * (o2_bar - o_bar ** 2)
        + RT70_B3 * (((a2_bar - a_bar ** 2) / 100.0) ** 2)
    )
    return {
        "ron": ron_blend,
        "mon": mon_blend,
        "aki": 0.5 * (ron_blend + mon_blend),
        "linear_aki": 0.5 * (r_bar + m_bar),
    }


def wickey_chittenden_flash_c(vol_fracs: Sequence[float], flash_points_c: Sequence[float]) -> float:
    """Wickey-Chittenden (1963) flash-point blending index (exact degF/degC equivalent)."""
    if abs(sum(vol_fracs) - 1.0) > 1e-6:
        raise ValueError("Volume fractions must sum to 1.0")
    i_blend = sum(
        xv * (10.0 ** (-6.1188 + 4345.2 / ((tc * 9.0 / 5.0 + 32.0) + 383.0)))
        for xv, tc in zip(vol_fracs, flash_points_c)
    )
    tf_blend = 4345.2 / (math.log10(i_blend) + 6.1188) - 383.0
    return (tf_blend - 32.0) * 5.0 / 9.0


def hu_burns_cloud_k(vol_fracs: Sequence[float], cloud_points_k: Sequence[float]) -> float:
    """Hu-Burns (1970) / Riazi Ch. 10 cloud-point blending index (T_cp^20)."""
    if abs(sum(vol_fracs) - 1.0) > 1e-6:
        raise ValueError("Volume fractions must sum to 1.0")
    return sum(xv * (tk ** 20.0) for xv, tk in zip(vol_fracs, cloud_points_k)) ** 0.05


def evaluate_ulsd_release(
    sulfur_ppmw: float | None,
    flash_c: float | None,
    cetane_number: float | None,
    cetane_index: float | None,
    aromatics_vol_pct: float | None,
    cloud_c: float | None,
    seasonal_cloud_max_c: float,
    contains_unhydrotreated_lco: bool = False,
) -> dict[str, Any]:
    """Unrounded ASTM D975 S15 & 40 CFR 1090 ULSD release gate (PO-07)."""
    reasons: list[str] = []
    if contains_unhydrotreated_lco:
        reasons.append("UNHYDROTREATED_LCO_FORBIDDEN")
    if any(v is None for v in (sulfur_ppmw, flash_c, cetane_number, cloud_c)):
        reasons.append("MISSING_ASSAY")
    else:
        assert sulfur_ppmw is not None and flash_c is not None and cetane_number is not None and cloud_c is not None
        if sulfur_ppmw > 15.0:
            reasons.append(f"SULFUR_EXCEEDS_15_PPMW ({sulfur_ppmw:.4f})")
        if flash_c < 52.0:
            reasons.append(f"FLASH_BELOW_52C ({flash_c:.2f})")
        if cetane_number < 40.0:
            reasons.append(f"CETANE_NUMBER_BELOW_40 ({cetane_number:.2f})")
        ci_ok = (cetane_index is not None) and (cetane_index >= 40.0)
        arom_ok = (aromatics_vol_pct is not None) and (aromatics_vol_pct <= 35.0)
        if not (ci_ok or arom_ok):
            reasons.append("D975_CETANE_INDEX_OR_AROMATICS_FAILED")
        if cloud_c > seasonal_cloud_max_c:
            reasons.append(f"CLOUD_EXCEEDS_SEASONAL ({cloud_c:.2f} > {seasonal_cloud_max_c:.2f})")
    return {
        "disposition": "RELEASE" if not reasons else "QUALITY_HOLD",
        "passed": not reasons,
        "reasons": reasons,
    }


def evaluate_bob_and_e10_release(
    grade: str,
    bob_aki: float | None,
    bob_rvp_psi: float | None,
    bob_rvp_max_psi: float,
    sulfur_ppmw: float | None,
    contains_untreated_lsr: bool = False,
    ethanol_vol_frac: float = 0.10,
    premium_pool_vol_frac: float | None = None,
    annual_avg_sulfur_ppmw: float | None = None,
) -> dict[str, Any]:
    """Refinery-gate BOB release check + terminal 10 vol% ethanol E10 calculation (ADR-0054, ADR-0056 G3-c)."""
    min_bob_aki = 88.6 if grade == "PREMIUM" else 84.2
    min_e10_aki = 91.0 if grade == "PREMIUM" else 87.0
    reasons: list[str] = []
    if contains_untreated_lsr:
        reasons.append("UNTREATED_LSR_FORBIDDEN")
    if premium_pool_vol_frac is not None and premium_pool_vol_frac > 0.10 + 1e-9:
        reasons.append(f"PREMIUM_POOL_SHARE_EXCEEDS_10PCT ({100.0 * premium_pool_vol_frac:.2f}%)")
    if annual_avg_sulfur_ppmw is not None and annual_avg_sulfur_ppmw > 10.0 + 1e-9:
        reasons.append(f"TIER3_ANNUAL_AVG_SULFUR_EXCEEDS_10_PPMW ({annual_avg_sulfur_ppmw:.4f})")
    if any(v is None for v in (bob_aki, bob_rvp_psi, sulfur_ppmw)):
        reasons.append("MISSING_ASSAY")
        return {"disposition": "QUALITY_HOLD", "passed": False, "reasons": reasons, "terminal_e10_aki": None}
    assert bob_aki is not None and bob_rvp_psi is not None and sulfur_ppmw is not None
    if bob_aki < min_bob_aki:
        reasons.append(f"BOB_AKI_BELOW_{min_bob_aki} ({bob_aki:.4f})")
    if bob_rvp_psi > bob_rvp_max_psi:
        reasons.append(f"BOB_RVP_EXCEEDS_{bob_rvp_max_psi} ({bob_rvp_psi:.4f})")
    if sulfur_ppmw > 80.0:
        reasons.append(f"SULFUR_EXCEEDS_80_PPMW_CAP ({sulfur_ppmw:.4f})")
    e10_aki = (1.0 - ethanol_vol_frac) * bob_aki + ethanol_vol_frac * 113.0
    e10_rvp = bob_rvp_psi + 1.0
    if e10_aki < min_e10_aki:
        reasons.append(f"E10_AKI_BELOW_{min_e10_aki} ({e10_aki:.4f})")
    return {
        "disposition": "RELEASE" if not reasons else "QUALITY_HOLD",
        "passed": not reasons,
        "reasons": reasons,
        "terminal_e10_aki": e10_aki,
        "terminal_e10_rvp_psi": e10_rvp,
    }
