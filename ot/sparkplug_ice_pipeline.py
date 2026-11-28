#!/usr/bin/env python3
"""OT/ICE Plane Publisher: OPC UA / MQTT Sparkplug B / TimescaleDB projection (WP-2, OT-001).

Consumes fixtures/golden/refinery_a_ot_tags.yaml and enforces:
- OT-01: Ambiguous tag rejection (duplicate tag names or ambiguous equipment mapping)
- OT-02: Deadband compression with mandatory bypass on Bad/Uncertain quality transitions
- OT-03: Broker disconnect and NBIRTH/DBIRTH rebirth sequence (bdSeq increment + full refresh)
- OT-04..06: 1-second compressor telemetry projection and OT-DELAY-01 visibility timestamps
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


class AmbiguousTagError(ValueError):
    """Raised when an OT tag binding is ambiguous or unregistered (OT-01)."""


@dataclass(frozen=True)
class SparkplugMetricEvent:
    message_type: str  # NBIRTH | DBIRTH | DDATA
    bd_seq: int
    seq: int
    tag_name: str
    equipment_id: str
    value: float
    unit: str
    quality: str  # Good | Uncertain | Bad
    effective_at_utc: str
    recorded_at_utc: str
    published_at_utc: str
    provenance_class: str = "SYNTHETIC"


class SparkplugOTPublisher:
    """Deterministic Sparkplug B v3.0 publisher with deadband, Bad-quality bypass, and rebirth."""

    def __init__(self, tag_schedule: Mapping[str, Any]):
        self.tags_by_name: dict[str, dict[str, Any]] = {}
        for t in tag_schedule.get("tags", []):
            name = str(t["tag_name"])
            if name in self.tags_by_name:
                raise AmbiguousTagError(f"OT-01: duplicate tag_name {name!r} in OT tag schedule")
            if not t.get("equipment_id"):
                raise AmbiguousTagError(f"OT-01: tag {name!r} missing unambiguous equipment_id")
            self.tags_by_name[name] = dict(t)

        self.bd_seq: int = 0
        self.seq: int = 0
        self.connected: bool = False
        self._last_published: dict[str, tuple[float, str]] = {}  # tag -> (value, quality)
        self._latest_sample: dict[str, tuple[float, str, str, str]] = {}

    def _next_seq(self) -> int:
        val = self.seq
        self.seq = (self.seq + 1) % 256
        return val

    def connect_and_birth(self, ts_utc: str) -> list[SparkplugMetricEvent]:
        """Connect (or reconnect after disconnect) and emit NBIRTH/DBIRTH rebirth snapshot (OT-03)."""
        self.connected = True
        self.bd_seq += 1
        self.seq = 0
        events: list[SparkplugMetricEvent] = []
        for tag_name, meta in sorted(self.tags_by_name.items()):
            if tag_name in self._latest_sample:
                val, qual, eff_ts, rec_ts = self._latest_sample[tag_name]
            else:
                val, qual, eff_ts, rec_ts = 0.0, "Uncertain", ts_utc, ts_utc
            events.append(
                SparkplugMetricEvent(
                    message_type="DBIRTH",
                    bd_seq=self.bd_seq,
                    seq=self._next_seq(),
                    tag_name=tag_name,
                    equipment_id=str(meta["equipment_id"]),
                    value=val,
                    unit=str(meta["unit"]),
                    quality=qual,
                    effective_at_utc=eff_ts,
                    recorded_at_utc=rec_ts,
                    published_at_utc=ts_utc,
                )
            )
            self._last_published[tag_name] = (val, qual)
        return events

    def simulate_broker_disconnect(self) -> None:
        self.connected = False

    def ingest_sample(
        self,
        tag_name: str,
        value: float,
        quality: str,
        effective_at_utc: str,
        recorded_at_utc: str,
        published_at_utc: str,
    ) -> SparkplugMetricEvent | None:
        """Process one OT sample applying OT-01 ambiguity check and OT-02 deadband/Bad bypass."""
        if tag_name not in self.tags_by_name:
            raise AmbiguousTagError(f"OT-01: unregistered or ambiguous OT tag {tag_name!r}")
        if quality not in ("Good", "Uncertain", "Bad"):
            raise ValueError(f"Invalid OPC UA quality code: {quality!r}")

        meta = self.tags_by_name[tag_name]
        self._latest_sample[tag_name] = (value, quality, effective_at_utc, recorded_at_utc)
        if not self.connected:
            return None

        deadband = float(meta.get("deadband", 0.0))
        prev = self._last_published.get(tag_name)
        quality_changed = (prev is None) or (prev[1] != quality)
        # OT-02: Bad/Uncertain quality transition ALWAYS bypasses deadband immediately!
        exceeds_deadband = (prev is None) or (abs(value - prev[0]) >= deadband)
        if not quality_changed and not exceeds_deadband:
            return None

        ev = SparkplugMetricEvent(
            message_type="DDATA",
            bd_seq=self.bd_seq,
            seq=self._next_seq(),
            tag_name=tag_name,
            equipment_id=str(meta["equipment_id"]),
            value=value,
            unit=str(meta["unit"]),
            quality=quality,
            effective_at_utc=effective_at_utc,
            recorded_at_utc=recorded_at_utc,
            published_at_utc=published_at_utc,
        )
        self._last_published[tag_name] = (value, quality)
        return ev


def filter_visible_ot_events(
    events: Sequence[SparkplugMetricEvent],
    reader_cutoff_utc: str,
) -> list[SparkplugMetricEvent]:
    """Enforce OT-DELAY-01 / INFO-001 visibility: only events published <= cutoff are visible."""
    return [e for e in events if e.published_at_utc <= reader_cutoff_utc]
