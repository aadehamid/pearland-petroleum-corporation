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

    @property
    def min_mass_kg(self) -> float:
        return eq.volume_bbl_to_mass_kg(self.min_bbl, self.sg_60_60)

    @property
    def max_mass_kg(self) -> float:
        return eq.volume_bbl_to_mass_kg(self.max_bbl, self.sg_60_60)

    @property
    def volume_bbl(self) -> float:
        return eq.mass_kg_to_volume_bbl(self.mass_kg, self.sg_60_60)


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
    reformer_h2_t_per_day: float = 73.0
    nht_h2_draw_t_per_day: float = 5.0
    fcc_hds_h2_draw_t_per_day: float = 5.0
    h2_header_loss_t_per_day: float = 5.0
    dht_committed_h2_t_per_day: float = 40.0
    hcu_cumulative_processed_bbl: float = 0.0
    hcu_cumulative_processed_t: float = 0.0
    tanks: dict[str, TankState] = field(default_factory=dict)
    applied_events: dict[str, str] = field(default_factory=dict)  # event_id -> payload_digest
    history: list[dict[str, Any]] = field(default_factory=list)

    def digest(self) -> str:
        """Deterministic SHA-256 state digest excluding branch_id metadata for cross-branch comparison."""
        canonical = {
            "world_version": self.world_version,
            "current_time_utc": self.current_time_utc.isoformat(),
            "state_revision": self.state_revision,
            "hcu_planned_feed_bbl_per_day": round(self.hcu_planned_feed_bbl_per_day, 9),
            "hcu_compressor_circ_fraction": round(self.hcu_compressor_circ_fraction, 9),
            "hcu_condition": self.hcu_condition,
            "hcu_running": self.hcu_running,
            "smr_h2_t_per_day": round(self.smr_h2_t_per_day, 9),
            "hcu_cumulative_processed_bbl": round(self.hcu_cumulative_processed_bbl, 9),
            "hcu_cumulative_processed_t": round(self.hcu_cumulative_processed_t, 9),
            "tanks": {
                tid: round(t.mass_kg, 6) for tid, t in sorted(self.tanks.items())
            },
            "applied_events": dict(sorted(self.applied_events.items())),
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
        self._scheduled.sort(key=lambda e: (e.effective_at_utc, e.event_id))

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
        """Restore a kernel from checkpoint, optionally forking an isolated child branch (PO-09)."""
        restored_state: WorldState = copy.deepcopy(ckpt["state"])
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
                return {
                    "status": "INFEASIBLE",
                    "event_id": ev.event_id,
                    "requested_bbl_per_day": req_bbl,
                    "max_permitted_bbl_per_day": chk["max_feed_bbl_per_day"],
                    "binding_constraint": chk["binding_constraint"],
                }
            self.state.hcu_planned_feed_bbl_per_day = req_bbl
        elif ev.event_type == "SMR_TURNDOWN":
            smr_h2 = float(ev.payload["smr_h2_t_per_day"])
            if not (54.0 <= smr_h2 <= 120.0):
                raise eq.OutOfEnvelopeError(f"SMR H2 {smr_h2} outside [54.0, 120.0] t/day")
            self.state.smr_h2_t_per_day = smr_h2
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
        h2 = eq.h2_header_balance(
            self.state.smr_h2_t_per_day,
            self.state.reformer_h2_t_per_day,
            self.state.nht_h2_draw_t_per_day,
            self.state.fcc_hds_h2_draw_t_per_day,
            self.state.h2_header_loss_t_per_day,
            self.state.dht_committed_h2_t_per_day,
        )
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
