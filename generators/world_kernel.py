#!/usr/bin/env python3
"""Deterministic Refinery A v1 Canonical World Kernel (WORLD-001, WORLD-002, ADR-0043).

Implements:
- Hybrid 1-minute canonical process clock with exact intra-step bound crossings (EQ-02)
- Semantic-keyed PCG64 paired RNG streams (identical exogenous shocks across sibling branches)
- Deterministic event ordering, idempotent delivery keys, and conflict rejection
- Atomic immutable checkpoints with SHA-256 state digest
- Isolated child branch fork and replay (zero parent mutation, PO-09)
- America/Chicago 23-hour / 25-hour DST business-day parity (PO-11)
"""
from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping
from zoneinfo import ZoneInfo

import numpy as np

from generators import equations as eq

CHICAGO_TZ = ZoneInfo("America/Chicago")


def paired_rng(root_seed: int, stream_key: str) -> np.random.Generator:
    """Semantic-keyed PCG64 RNG stream independent of branch_id (paired exogenous shocks, WORLD-002 §5)."""
    h = hashlib.sha256(f"{root_seed}:{stream_key}".encode("utf-8")).digest()
    seed_int = int.from_bytes(h[:16], "big")
    return np.random.Generator(np.random.PCG64(seed_int))


def local_business_day_elapsed_hours(date_iso: str, start_hour_local: int = 6) -> float:
    """Return exact elapsed UTC hours in an America/Chicago business day (23h spring / 25h fall DST)."""
    year, month, day = (int(x) for x in date_iso.split("-"))
    start_local = datetime(year, month, day, start_hour_local, 0, 0, tzinfo=CHICAGO_TZ)
    next_day = datetime(year, month, day, tzinfo=CHICAGO_TZ) + timedelta(days=1)
    end_local = datetime(next_day.year, next_day.month, next_day.day, start_hour_local, 0, 0, tzinfo=CHICAGO_TZ)
    return (end_local.astimezone(timezone.utc) - start_local.astimezone(timezone.utc)).total_seconds() / 3600.0


@dataclass
class TankState:
    tank_id: str
    min_bbl: float
    max_bbl: float
    sg_60_60: float
    mass_kg: float
    inflow_kg_s: float = 0.0
    outflow_kg_s: float = 0.0
    loss_kg_s: float = 0.0

    @property
    def min_mass_kg(self) -> float:
        return eq.volume_bbl_to_mass_kg(self.min_bbl, self.sg_60_60)

    @property
    def max_mass_kg(self) -> float:
        return eq.volume_bbl_to_mass_kg(self.max_bbl, self.sg_60_60)

    @property
    def volume_bbl(self) -> float:
        return eq.mass_kg_to_volume_bbl(self.mass_kg, self.sg_60_60)


# W2-02 (WORLD-002 §3.2): physical restrictions always execute before discretionary requests at the same instant
EVENT_ORDER_PRIORITY: dict[str, int] = {
    "HCU_COMPRESSOR_DERATE": 0,
    "SMR_TURNDOWN": 0,
    "TANK_FLOW_SCHEDULE": 0,
    "HCU_FEED_SETPOINT": 1,
}


@dataclass
class WorldEvent:
    event_id: str
    effective_at_utc: datetime
    event_type: str
    payload: dict[str, Any]
    provenance_class: str = "SCENARIO_ASSUMPTION"

    def payload_digest(self) -> str:
        return hashlib.sha256(json.dumps(self.payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


@dataclass
class WorldState:
    world_version: str
    branch_id: str
    root_seed: int
    current_time_utc: datetime
    state_revision: int = 0
    hcu_planned_feed_bbl_per_day: float = 36000.0
    hcu_mech_cap_bbl_per_day: float = 40000.0
    hcu_compressor_circ_fraction: float = 1.0
    hcu_condition: str = "NORMAL"
    hcu_running: bool = True
    smr_h2_t_per_day: float = 107.0
    smr_target_h2_t_per_day: float | None = None
    reformer_h2_t_per_day: float = 73.0
    nht_h2_draw_t_per_day: float = 5.0
    fcc_hds_h2_draw_t_per_day: float = 5.0
    h2_header_loss_t_per_day: float = 5.0
    dht_committed_h2_t_per_day: float = 40.0
    hcu_cumulative_processed_bbl: float = 0.0
    hcu_cumulative_processed_t: float = 0.0
    tanks: dict[str, TankState] = field(default_factory=dict)
    applied_events: dict[str, str] = field(default_factory=dict)  # event_id -> payload_digest
    rejected_events: dict[str, dict[str, Any]] = field(default_factory=dict)  # event_id -> rejection detail
    history: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.smr_target_h2_t_per_day is None:
            self.smr_target_h2_t_per_day = self.smr_h2_t_per_day

    def digest(self) -> str:
        """Deterministic SHA-256 state digest covering ALL mutable physics fields (excluding branch_id)."""
        canonical = {
            "world_version": self.world_version,
            "current_time_utc": self.current_time_utc.isoformat(),
            "state_revision": self.state_revision,
            "hcu_planned_feed_bbl_per_day": round(self.hcu_planned_feed_bbl_per_day, 9),
            "hcu_mech_cap_bbl_per_day": round(self.hcu_mech_cap_bbl_per_day, 9),
            "hcu_compressor_circ_fraction": round(self.hcu_compressor_circ_fraction, 9),
            "hcu_condition": self.hcu_condition,
            "hcu_running": self.hcu_running,
            "smr_h2_t_per_day": round(self.smr_h2_t_per_day, 9),
            "smr_target_h2_t_per_day": round(float(self.smr_target_h2_t_per_day), 9),
            "reformer_h2_t_per_day": round(self.reformer_h2_t_per_day, 9),
            "nht_h2_draw_t_per_day": round(self.nht_h2_draw_t_per_day, 9),
            "fcc_hds_h2_draw_t_per_day": round(self.fcc_hds_h2_draw_t_per_day, 9),
            "h2_header_loss_t_per_day": round(self.h2_header_loss_t_per_day, 9),
            "dht_committed_h2_t_per_day": round(self.dht_committed_h2_t_per_day, 9),
            "hcu_cumulative_processed_bbl": round(self.hcu_cumulative_processed_bbl, 9),
            "hcu_cumulative_processed_t": round(self.hcu_cumulative_processed_t, 9),
            "tanks": {
                tid: {
                    "mass_kg": round(t.mass_kg, 6),
                    "inflow_kg_s": round(t.inflow_kg_s, 9),
                    "outflow_kg_s": round(t.outflow_kg_s, 9),
                }
                for tid, t in sorted(self.tanks.items())
            },
            "applied_events": dict(sorted(self.applied_events.items())),
            "rejected_events": dict(sorted(self.rejected_events.items())),
        }
        return hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


class RefineryWorldKernel:
    """Deterministic Refinery A v1 canonical world simulator (1-minute canonical steps + exact splits)."""

    def __init__(self, state: WorldState, step_seconds: int = 60, fixture_mode: bool = True):
        if step_seconds <= 0:
            raise ValueError("step_seconds must be positive")
        self.state = state
        self.step_seconds = step_seconds
        self.fixture_mode = fixture_mode
        self._scheduled: list[WorldEvent] = []

    def schedule_event(self, event: WorldEvent) -> None:
        self._scheduled.append(event)
        self._scheduled.sort(
            key=lambda e: (e.effective_at_utc, EVENT_ORDER_PRIORITY.get(e.event_type, 1), e.event_id)
        )

    def checkpoint(self) -> dict[str, Any]:
        """Return an immutable deep-copied checkpoint with SHA-256 digest."""
        snap = copy.deepcopy(self.state)
        return {
            "state": snap,
            "scheduled": copy.deepcopy(self._scheduled),
            "state_digest": snap.digest(),
            "step_seconds": self.step_seconds,
            "fixture_mode": self.fixture_mode,
            "provenance_class": "SYNTHETIC",
        }

    @classmethod
    def from_checkpoint(cls, ckpt: Mapping[str, Any], branch_id: str | None = None) -> "RefineryWorldKernel":
        """Restore a kernel from checkpoint after verifying SHA-256 integrity (WORLD-002 §4 / W2-07)."""
        restored_state: WorldState = copy.deepcopy(ckpt["state"])
        actual_digest = restored_state.digest()
        if str(ckpt.get("state_digest", "")) != actual_digest:
            raise ValueError(
                f"Checkpoint integrity violation (W2-07): recorded digest {ckpt.get('state_digest')!r} != actual {actual_digest!r}"
            )
        if branch_id is not None:
            restored_state.branch_id = branch_id
        kernel = cls(
            restored_state,
            step_seconds=int(ckpt["step_seconds"]),
            fixture_mode=bool(ckpt["fixture_mode"]),
        )
        kernel._scheduled = copy.deepcopy(ckpt["scheduled"])
        return kernel

    def _apply_event(self, ev: WorldEvent) -> dict[str, Any]:
        pdig = ev.payload_digest()
        if ev.event_id in self.state.applied_events:
            if self.state.applied_events[ev.event_id] == pdig:
                return {"status": "IDEMPOTENT_DUPLICATE", "event_id": ev.event_id}
            raise ValueError(f"CONFLICT: event_id {ev.event_id!r} reused with different payload")

        if ev.event_type == "HCU_COMPRESSOR_DERATE":
            circ = float(ev.payload["compressor_circ_fraction"])
            if not (0.0 < circ <= 1.0):
                raise eq.OutOfEnvelopeError("compressor_circ_fraction must be in (0, 1]")
            self.state.hcu_compressor_circ_fraction = circ
            self.state.hcu_condition = "DERATED" if circ < 1.0 else "NORMAL"
            self.state.hcu_running = True
        elif ev.event_type == "HCU_FEED_SETPOINT":
            req_bbl = float(ev.payload["requested_feed_bbl_per_day"])
            h2 = eq.h2_header_balance(
                self.state.smr_h2_t_per_day,
                self.state.reformer_h2_t_per_day,
                self.state.nht_h2_draw_t_per_day,
                self.state.fcc_hds_h2_draw_t_per_day,
                self.state.h2_header_loss_t_per_day,
                self.state.dht_committed_h2_t_per_day,
            )
            chk = eq.hcu_evaluate(
                requested_feed_bbl_per_day=req_bbl,
                mech_cap_bbl_per_day=self.state.hcu_mech_cap_bbl_per_day,
                compressor_circ_fraction=self.state.hcu_compressor_circ_fraction,
                h2_allocable_t_per_day=h2["hcu_headroom_t_per_day"],
                fixture_mode=self.fixture_mode,
            )
            if not chk["feasible"]:
                rej = {
                    "status": "INFEASIBLE",
                    "event_id": ev.event_id,
                    "event_type": ev.event_type,
                    "effective_at_utc": ev.effective_at_utc.isoformat(),
                    "requested_bbl_per_day": req_bbl,
                    "max_permitted_bbl_per_day": chk["max_feed_bbl_per_day"],
                    "binding_constraint": chk["binding_constraint"],
                }
                self.state.rejected_events[ev.event_id] = rej
                self.state.history.append(rej)
                return rej
            self.state.hcu_planned_feed_bbl_per_day = req_bbl
        elif ev.event_type == "SMR_TURNDOWN":
            smr_h2 = float(ev.payload["smr_h2_t_per_day"])
            if not (54.0 <= smr_h2 <= 120.0):
                raise eq.OutOfEnvelopeError(f"SMR H2 {smr_h2} outside [54.0, 120.0] t/day")
            self.state.smr_target_h2_t_per_day = smr_h2
            # Respect 2%/min SMR ramp during stepping unless explicit steady-state boundary fixture requests instant jump
            if bool(ev.payload.get("instant_boundary_fixture", False)):
                self.state.smr_h2_t_per_day = smr_h2
        elif ev.event_type == "TANK_FLOW_SCHEDULE":
            tid = str(ev.payload["tank_id"])
            if tid not in self.state.tanks:
                raise ValueError(f"Unknown tank_id in TANK_FLOW_SCHEDULE: {tid!r}")
            tk = self.state.tanks[tid]
            tk.inflow_kg_s = float(ev.payload.get("inflow_kg_s", tk.inflow_kg_s))
            tk.outflow_kg_s = float(ev.payload.get("outflow_kg_s", tk.outflow_kg_s))
            tk.loss_kg_s = float(ev.payload.get("loss_kg_s", tk.loss_kg_s))
        else:
            raise ValueError(f"Unknown event_type: {ev.event_type!r}")

        self.state.applied_events[ev.event_id] = pdig
        self.state.state_revision += 1
        rec = {
            "status": "APPLIED",
            "event_id": ev.event_id,
            "event_type": ev.event_type,
            "effective_at_utc": ev.effective_at_utc.isoformat(),
            "state_revision": self.state.state_revision,
        }
        self.state.history.append(rec)
        return rec

    def _step_interval(self, dt_s: float) -> dict[str, Any]:
        # Enforce SMR 2%/min ramp toward smr_target_h2_t_per_day inside every step (EQ-07)
        target_smr = (
            float(self.state.smr_target_h2_t_per_day)
            if self.state.smr_target_h2_t_per_day is not None
            else self.state.smr_h2_t_per_day
        )
        h2 = eq.h2_header_balance(
            target_smr,
            self.state.reformer_h2_t_per_day,
            self.state.nht_h2_draw_t_per_day,
            self.state.fcc_hds_h2_draw_t_per_day,
            self.state.h2_header_loss_t_per_day,
            self.state.dht_committed_h2_t_per_day,
            prev_smr_h2_t_per_day=self.state.smr_h2_t_per_day,
            dt_minutes=dt_s / 60.0,
        )
        self.state.smr_h2_t_per_day = float(h2["smr_effective_t_per_day"])
        hcu_res = eq.hcu_evaluate(
            requested_feed_bbl_per_day=self.state.hcu_planned_feed_bbl_per_day,
            mech_cap_bbl_per_day=self.state.hcu_mech_cap_bbl_per_day,
            compressor_circ_fraction=self.state.hcu_compressor_circ_fraction,
            h2_allocable_t_per_day=h2["hcu_headroom_t_per_day"],
            fixture_mode=self.fixture_mode,
        )
        day_frac = dt_s / 86400.0
        self.state.hcu_cumulative_processed_bbl += hcu_res["actual_feed_bbl_per_day"] * day_frac
        self.state.hcu_cumulative_processed_t += hcu_res["actual_feed_t_per_day"] * day_frac

        # Step every active tank in WorldState via EQ-02 exact intra-step t* bound crossing split
        for tid in sorted(self.state.tanks):
            tk = self.state.tanks[tid]
            if tk.inflow_kg_s != 0.0 or tk.outflow_kg_s != 0.0 or tk.loss_kg_s != 0.0:
                tres = eq.step_tank_with_exact_crossing(
                    opening_mass_kg=tk.mass_kg,
                    min_mass_kg=tk.min_mass_kg,
                    max_mass_kg=tk.max_mass_kg,
                    inflow_rate_kg_s=tk.inflow_kg_s,
                    outflow_rate_kg_s=tk.outflow_kg_s,
                    dt_s=dt_s,
                    loss_rate_kg_s=tk.loss_kg_s,
                )
                tk.mass_kg = float(tres.closing_mass_kg)
        return hcu_res

    def advance_to(self, target_time_utc: datetime) -> list[dict[str, Any]]:
        """Advance simulation deterministically to target_time_utc, splitting exactly at event times."""
        if target_time_utc < self.state.current_time_utc:
            raise ValueError("Cannot advance backwards in simulation time")
        event_outcomes: list[dict[str, Any]] = []
        while self.state.current_time_utc < target_time_utc:
            # Apply any events due at exact current_time_utc
            while self._scheduled and self._scheduled[0].effective_at_utc <= self.state.current_time_utc:
                ev = self._scheduled.pop(0)
                event_outcomes.append(self._apply_event(ev))

            next_step = min(
                target_time_utc,
                self.state.current_time_utc + timedelta(seconds=self.step_seconds),
            )
            if self._scheduled and self._scheduled[0].effective_at_utc < next_step:
                next_step = self._scheduled[0].effective_at_utc

            dt_s = (next_step - self.state.current_time_utc).total_seconds()
            if dt_s > 0.0:
                self._step_interval(dt_s)
                self.state.current_time_utc = next_step

        # Apply events due exactly at target_time_utc
        while self._scheduled and self._scheduled[0].effective_at_utc <= self.state.current_time_utc:
            ev = self._scheduled.pop(0)
            event_outcomes.append(self._apply_event(ev))
        return event_outcomes


def evaluate_refinery_plant_snapshot(
    design_basis: Mapping[str, Any],
    crude_feeds_bbl_per_day: Mapping[str, float] | None = None,
    hcu_compressor_circ_fraction: float = 1.0,
    smr_h2_t_per_day: float = 107.0,
    fcc_t_rxr_c: float = 525.0,
    fcc_cat_to_oil: float = 6.5,
    hcu_fixture_mode: bool = False,
) -> dict[str, Any]:
    """Evaluate a full coupled Refinery A v1 plant snapshot across EQ-01 through EQ-08.

    Steps CDU/VDU (EQ-04), Reformer (EQ-07), DHT (EQ-07), FCC (EQ-06), shared H2 header
    (EQ-07), HCU (EQ-05), hydraulic transfer checks (EQ-03), and ULSD/BOB blending (EQ-08).
    Reports BOTH HCU C5+ liquid gain and refinery-wide C5+/C3+ liquid volume balances so
    PO-12a reviewers have transparent unit-vs-plant evidence.
    """
    assays_by_id = {a["id"]: a for a in design_basis["crude_assays"]}
    if crude_feeds_bbl_per_day is None:
        # Nominal 180,000 bbl/day design blend (30% Light Sweet / 50% Medium Sour / 20% Heavy Sour)
        crude_feeds_bbl_per_day = {
            "ASSAY-LIGHT-SWEET": 54000.0,
            "ASSAY-MEDIUM-SOUR": 90000.0,
            "ASSAY-HEAVY-SOUR": 36000.0,
        }

    crude_feeds_t: dict[str, float] = {}
    total_crude_bbl = 0.0
    for aid, bbl in crude_feeds_bbl_per_day.items():
        sg = eq.api_to_sg_60_60(float(assays_by_id[aid]["target_api_gravity"]))
        crude_feeds_t[aid] = eq.volume_bbl_to_mass_kg(bbl, sg) / 1000.0
        total_crude_bbl += bbl

    cdu = eq.cdu_vdu_cut_split(crude_feeds_t, assays_by_id)
    cuts = cdu["cuts"]

    # Bounded interfaces (EQ-07): NHT, Reformer (RON 98), DHT (SR AGO + <=20% FCC LCO), FCC HDS
    heavy_naphtha_t = cuts["HEAVY_NAPHTHA"]["mass_t_per_day"]
    nht_h2_t = heavy_naphtha_t * 0.0015  # ~5.0 t/day
    reformer = eq.reformer_interface_step(heavy_naphtha_t, ron_target=98.0)

    # Split VGO between FCC (30 kbbl/d cap) and HCU (40 kbbl/d cap)
    vgo_bbl = cuts["VGO"]["volume_bbl_per_day"]
    vgo_sg = cuts["VGO"]["sg_60_60"]
    vgo_s_frac = cuts["VGO"]["sulfur_wt_pct"] / 100.0
    fcc_feed_bbl = min(23000.0, vgo_bbl * 0.40)
    fcc_feed_t = eq.volume_bbl_to_mass_kg(fcc_feed_bbl, vgo_sg) / 1000.0
    fcc = eq.fcc_evaluate(
        feed_t_per_day=fcc_feed_t,
        feed_sulfur_wt_frac=vgo_s_frac,
        w_ccr_feed=0.012,
        t_rxr_c=fcc_t_rxr_c,
        cat_to_oil=fcc_cat_to_oil,
        feed_sg_60_60=vgo_sg,
    )
    fcc_hds_h2_t = fcc["streams_t_per_day"]["fcc_naphtha"] * 0.0038

    # DHT processes SR AGO + <= 20 wt% FCC LCO
    ago_t = cuts["AGO"]["mass_t_per_day"]
    lco_to_dht_t = min(fcc["streams_t_per_day"]["lco"], 0.20 * ago_t / 0.80)
    dht = eq.dht_interface_step(ago_t, lco_to_dht_t)

    # Shared H2 header (EQ-07)
    h2 = eq.h2_header_balance(
        smr_h2_t_per_day=smr_h2_t_per_day,
        reformer_h2_t_per_day=reformer["h2_byproduct_t_per_day"],
        nht_draw_t_per_day=nht_h2_t,
        fcc_hds_draw_t_per_day=fcc_hds_h2_t,
        header_loss_t_per_day=5.0,
        dht_committed_t_per_day=dht["h2_uptake_t_per_day"],
    )

    hcu_req_bbl = max(0.0, vgo_bbl - fcc_feed_bbl)
    hcu = eq.hcu_evaluate(
        requested_feed_bbl_per_day=hcu_req_bbl,
        feed_sg_60_60=vgo_sg,
        feed_sulfur_wt_frac=vgo_s_frac,
        compressor_circ_fraction=hcu_compressor_circ_fraction,
        h2_allocable_t_per_day=h2["hcu_headroom_t_per_day"],
        fixture_mode=hcu_fixture_mode,
    )

    # Hydraulic checks on every EQ-03 transfer line in design basis (applying ANSI/HI 9.6.7 viscous derate C_H)
    primary_pumps = {
        p["line_id"]: p for p in design_basis.get("pumps", []) if p.get("role") == "primary"
    }
    hydraulics_ok = True
    for line in design_basis.get("transfer_lines", []):
        pump = primary_pumps[line["id"]]
        c_h = 0.88 if pump.get("viscous_service") else 1.0
        hres = eq.check_transfer_hydraulics(
            flow_bbl_per_day=float(line["nominal_flow_bbl_per_day"]),
            diameter_m=float(line["diameter_m"]),
            length_m=float(line["length_m"]),
            roughness_m=float(line["roughness_m"]),
            k_fittings=float(line["k_fittings"]),
            delta_z_m=float(line["delta_z_m"]),
            delta_p_pa=float(line["delta_p_pa"]),
            sg_60_60=float(line["fluid_sg"]),
            viscosity_pa_s=float(line["fluid_viscosity_pa_s"]),
            pump_h0_m=float(pump["h0_m"]),
            pump_cp_s2_m5=float(pump["cp_s2_per_m5"]),
            viscous_derate_c_h=c_h,
        )
        hydraulics_ok = hydraulics_ok and bool(hres["feasible"])

    # Representative ULSD and Regular BOB release gates (EQ-08)
    ulsd_gate = eq.evaluate_ulsd_release(
        sulfur_ppmw=10.0,
        flash_c=60.0,
        cetane_number=46.0,
        cetane_index=46.0,
        aromatics_vol_pct=26.0,
        cloud_c=-10.0,
        seasonal_cloud_max_c=-5.0,
    )
    rt70 = eq.ethyl_rt70_octane(
        vol_fracs=[0.40, 0.40, 0.15, 0.05],
        rons=[98.0, 90.0, 68.0, 94.0],
        mons=[87.0, 79.0, 66.0, 90.0],
        olefins_vol_pct=[1.0, 28.0, 1.0, 0.0],
        aromatics_vol_pct=[62.0, 25.0, 3.0, 0.0],
    )
    # Summer RFG Regular BOB trim (1% n-butane @ 52 psi in 5.6 psi base -> ~6.25 psi <= 6.4 psi max)
    bob_rvp = eq.chevron_rvp_psi([0.99, 0.01], [5.6, 52.0])
    bob_gate = eq.evaluate_bob_and_e10_release(
        grade="REGULAR",
        bob_aki=rt70["aki"],
        bob_rvp_psi=bob_rvp,
        bob_rvp_max_psi=6.4,
        sulfur_ppmw=8.5,
        premium_pool_vol_frac=0.096,
        annual_avg_sulfur_ppmw=8.5,
    )

    # Plant-wide liquid volume accounting (includes any unprocessed VGO routed to TK-201 during HCU derate)
    unprocessed_vgo_to_tk201_bbl = max(0.0, hcu_req_bbl - float(hcu["actual_feed_bbl_per_day"]))
    ref_bbl = eq.mass_kg_to_volume_bbl(reformer["reformate_t_per_day"] * 1000.0, 0.785)
    fcc_naph_bbl = eq.mass_kg_to_volume_bbl(fcc["streams_t_per_day"]["fcc_naphtha"] * 1000.0, 0.745)
    fcc_slurry_bbl = eq.mass_kg_to_volume_bbl(fcc["streams_t_per_day"]["slurry"] * 1000.0, 1.020)
    fcc_lco_rem_bbl = eq.mass_kg_to_volume_bbl(
        max(0.0, fcc["streams_t_per_day"]["lco"] - lco_to_dht_t) * 1000.0, 0.925
    )
    dht_ulsd_bbl = eq.mass_kg_to_volume_bbl((ago_t + lco_to_dht_t) * 1000.0, 0.840)
    plant_c5_plus_bbl = (
        cuts["LSR"]["volume_bbl_per_day"]
        + ref_bbl
        + cuts["KEROSENE"]["volume_bbl_per_day"]
        + dht_ulsd_bbl
        + fcc_naph_bbl
        + fcc_lco_rem_bbl
        + fcc_slurry_bbl
        + hcu["c5_plus_bbl_per_day"]
        + unprocessed_vgo_to_tk201_bbl
        + cuts["VACUUM_RESIDUE"]["volume_bbl_per_day"]
    )
    plant_lpg_bbl = (
        cuts["LPG"]["volume_bbl_per_day"]
        + eq.mass_kg_to_volume_bbl((reformer["lpg_t_per_day"] + fcc["streams_t_per_day"]["lpg"]) * 1000.0, 0.540)
        + float(hcu["outputs"]["lpg"]["volume_bbl_per_day"])
    )
    plant_c5_gain_pct = 100.0 * (plant_c5_plus_bbl / total_crude_bbl - 1.0)
    plant_c3_gain_pct = 100.0 * ((plant_c5_plus_bbl + plant_lpg_bbl) / total_crude_bbl - 1.0)
    hcu_h2_scf_per_bbl = (
        (float(hcu["h2_net_t_per_day"]) * 1000.0 * 423.6) / float(hcu["actual_feed_bbl_per_day"])
        if float(hcu["actual_feed_bbl_per_day"]) > 0.0
        else 0.0
    )

    return {
        "provenance_class": "SYNTHETIC",
        "total_crude_bbl_per_day": total_crude_bbl,
        "cdu": cdu,
        "reformer": reformer,
        "dht": dht,
        "fcc": fcc,
        "h2_header": h2,
        "hcu": hcu,
        "unprocessed_vgo_to_tk201_bbl_per_day": unprocessed_vgo_to_tk201_bbl,
        "hydraulics_all_feasible": hydraulics_ok,
        "ulsd_gate": ulsd_gate,
        "bob_gate": bob_gate,
        "volume_gain_summary": {
            "hcu_c5_plus_gain_pct": hcu["liquid_vol_gain_c5_pct"],
            "hcu_h2_uptake_scf_per_bbl": hcu_h2_scf_per_bbl,
            "plant_c5_plus_gain_pct": plant_c5_gain_pct,
            "plant_c3_plus_gain_pct": plant_c3_gain_pct,
        },
    }


def run_eng_v07_mode_benchmark(design_basis: Mapping[str, Any]) -> dict[str, Any]:
    """Run ENG-V07 training-vs-holdout operating-mode benchmark with transparent unit AND plant plausibility gates."""
    training_modes = {
        "train_nominal_design_blend": evaluate_refinery_plant_snapshot(
            design_basis,
            crude_feeds_bbl_per_day={"ASSAY-LIGHT-SWEET": 54000.0, "ASSAY-MEDIUM-SOUR": 90000.0, "ASSAY-HEAVY-SOUR": 36000.0},
            hcu_compressor_circ_fraction=1.0,
            smr_h2_t_per_day=107.0,
        ),
        "train_uc1_compressor_derate_75pct": evaluate_refinery_plant_snapshot(
            design_basis,
            crude_feeds_bbl_per_day={"ASSAY-LIGHT-SWEET": 54000.0, "ASSAY-MEDIUM-SOUR": 90000.0, "ASSAY-HEAVY-SOUR": 36000.0},
            hcu_compressor_circ_fraction=0.75,
            smr_h2_t_per_day=107.0,
        ),
    }
    holdout_modes = {
        "holdout_uc4_heavy_sour_swing": evaluate_refinery_plant_snapshot(
            design_basis,
            crude_feeds_bbl_per_day={"ASSAY-LIGHT-SWEET": 36000.0, "ASSAY-MEDIUM-SOUR": 72000.0, "ASSAY-HEAVY-SOUR": 72000.0},
            hcu_compressor_circ_fraction=1.0,
            smr_h2_t_per_day=115.0,
        ),
        "holdout_light_sweet_high_severity_fcc": evaluate_refinery_plant_snapshot(
            design_basis,
            crude_feeds_bbl_per_day={"ASSAY-LIGHT-SWEET": 90000.0, "ASSAY-MEDIUM-SOUR": 72000.0, "ASSAY-HEAVY-SOUR": 18000.0},
            hcu_compressor_circ_fraction=1.0,
            smr_h2_t_per_day=107.0,
            fcc_t_rxr_c=532.0,
            fcc_cat_to_oil=7.0,
        ),
        "holdout_uc2_smr_h2_constrained": evaluate_refinery_plant_snapshot(
            design_basis,
            crude_feeds_bbl_per_day={"ASSAY-LIGHT-SWEET": 54000.0, "ASSAY-MEDIUM-SOUR": 90000.0, "ASSAY-HEAVY-SOUR": 36000.0},
            hcu_compressor_circ_fraction=0.75,
            smr_h2_t_per_day=60.0,
        ),
    }

    def _summarize(mode_dict: Mapping[str, Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
        out: dict[str, dict[str, Any]] = {}
        for name, snap in mode_dict.items():
            vg = snap["volume_gain_summary"]
            out[name] = {
                "cdu_mass_residual_t": abs(snap["cdu"]["mass_residual_t_per_day"]),
                "cdu_sulfur_residual_t": abs(snap["cdu"]["sulfur_residual_t_per_day"]),
                "fcc_mass_residual_t": abs(snap["fcc"]["mass_residual_t_per_day"]),
                "fcc_sulfur_residual_t": abs(snap["fcc"]["sulfur_residual_t_per_day"]),
                "fcc_heat_feasible": snap["fcc"]["heat_balance_feasible"],
                "hcu_mass_residual_t": abs(snap["hcu"]["mass_residual_t_per_day"]),
                "hcu_sulfur_residual_t": abs(snap["hcu"]["sulfur_balance"]["sulfur_residual_t_per_day"]),
                "hcu_acid_gas_covers_h2s": snap["hcu"]["sulfur_balance"]["acid_gas_covers_stoichiometric_h2s"],
                "h2_no_double_alloc": snap["h2_header"]["no_double_allocation"],
                "hydraulics_all_feasible": snap["hydraulics_all_feasible"],
                "hcu_binding_constraint": snap["hcu"]["binding_constraint"],
                "hcu_c5_plus_gain_pct": vg["hcu_c5_plus_gain_pct"],
                "hcu_h2_uptake_scf_per_bbl": vg["hcu_h2_uptake_scf_per_bbl"],
                "plant_c5_plus_gain_pct": vg["plant_c5_plus_gain_pct"],
                "plant_c3_plus_gain_pct": vg["plant_c3_plus_gain_pct"],
                "po12a_hcu_gain_in_4_to_10": 4.0 <= vg["hcu_c5_plus_gain_pct"] <= 10.0,
                "po12a_hcu_h2_in_1000_to_2500": 1000.0 <= vg["hcu_h2_uptake_scf_per_bbl"] <= 2500.0,
                "po12a_plant_c5_gain_in_4_to_10": 4.0 <= vg["plant_c5_plus_gain_pct"] <= 10.0,
            }
        return out

    train_res = _summarize(training_modes)
    holdout_res = _summarize(holdout_modes)
    max_rel_residual = max(
        max(v["cdu_mass_residual_t"], v["cdu_sulfur_residual_t"], v["fcc_mass_residual_t"],
            v["fcc_sulfur_residual_t"], v["hcu_mass_residual_t"], v["hcu_sulfur_residual_t"])
        for v in (*train_res.values(), *holdout_res.values())
    )
    unit_and_conservation_pass = all(
        v["fcc_heat_feasible"]
        and v["hcu_acid_gas_covers_h2s"]
        and v["h2_no_double_alloc"]
        and v["hydraulics_all_feasible"]
        and v["po12a_hcu_gain_in_4_to_10"]
        and v["po12a_hcu_h2_in_1000_to_2500"]
        for v in holdout_res.values()
    )
    po12a_plant_c5_band_pass = all(v["po12a_plant_c5_gain_in_4_to_10"] for v in holdout_res.values())
    return {
        "provenance_class": "SYNTHETIC",
        "training_modes": train_res,
        "holdout_modes": holdout_res,
        "max_absolute_residual_t_per_day": max_rel_residual,
        "unit_and_conservation_gates_pass": unit_and_conservation_pass,
        "po12a_plant_c5_gain_band_pass": po12a_plant_c5_band_pass,
        # Strict overall holdout gate does NOT pass while plant C5+ gain sits outside PO-12a +4..+10% band;
        # requires independent PO-12a engineering review & Hamid Adesokan's owner sign-off (ADR-0059 / G3-d).
        "all_holdout_gates_pass": unit_and_conservation_pass and po12a_plant_c5_band_pass,
    }
