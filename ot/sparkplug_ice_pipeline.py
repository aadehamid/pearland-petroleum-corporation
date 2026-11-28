#!/usr/bin/env python3
"""OT/ICE Plane Publisher: Sparkplug B v3.0 Deadband, Rebirth, Persistence, and Delay Visibility (WP-2, OT-001).

Consumes `fixtures/golden/refinery_a_ot_tags.yaml` and enforces:
- OT-01: Ambiguous/duplicate/unregistered tag rejection
- OT-02: Inclusive deadband compression with mandatory bypass on Bad/Uncertain quality transitions
- OT-03: Broker disconnect, NBIRTH (seq=0) + DBIRTH (seq=1..255) rebirth sequence with bdSeq increment,
  persistent restart buffer (no invented observations for tags without samples)
- OT-DELAY-01: Visibility cutoff filter (`published_at_utc <= reader_cutoff_utc`)
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
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
    value: float | None
    unit: str
    quality: str  # Good | Uncertain | Bad
    effective_at_utc: str
    recorded_at_utc: str
    published_at_utc: str
    provenance_class: str = "SYNTHETIC"


class SparkplugOTPublisher:
    """Deterministic Sparkplug B v3.0 publisher with deadband, Bad-quality bypass, NBIRTH/DBIRTH, and buffer persistence."""

    def __init__(self, tag_schedule: Mapping[str, Any], buffer_path: str | Path | None = None):
        self.tags_by_name: dict[str, dict[str, Any]] = {}
        self.site_id = str(tag_schedule.get("site_id", "SITE-REF-A"))
        for t in tag_schedule.get("tags", []):
            name = str(t.get("tag_id") or t.get("tag_name") or "").strip()
            if not name:
                raise AmbiguousTagError("OT-01: tag entry missing tag_id / tag_name")
            if name in self.tags_by_name:
                raise AmbiguousTagError(f"OT-01: duplicate tag_name {name!r} in OT tag schedule")
            if not t.get("equipment_id"):
                raise AmbiguousTagError(f"OT-01: tag {name!r} missing unambiguous equipment_id")
            unit = str(t.get("native_unit") or t.get("unit") or "")
            if "deadband" in t and t["deadband"] is not None:
                deadband = float(t["deadband"])
            elif "eu_range" in t and "deadband_pct" in t:
                lo, hi = float(t["eu_range"][0]), float(t["eu_range"][1])
                deadband = (hi - lo) * float(t["deadband_pct"]) / 100.0
            else:
                deadband = 0.0
            self.tags_by_name[name] = {
                **dict(t),
                "tag_name": name,
                "unit": unit,
                "deadband": deadband,
            }

        self.buffer_path = Path(buffer_path) if buffer_path is not None else None
        self.bd_seq: int = 0
        self.seq: int = 0
        self.connected: bool = False
        self._last_published: dict[str, tuple[float, str]] = {}
        self._latest_sample: dict[str, tuple[float, str, str, str]] = {}
        self._load_persisted_buffer()

    def _load_persisted_buffer(self) -> None:
        if self.buffer_path is not None and self.buffer_path.is_file():
            data = json.loads(self.buffer_path.read_text(encoding="utf-8"))
            self.bd_seq = int(data.get("bd_seq", 0))
            for k, v in data.get("latest_sample", {}).items():
                self._latest_sample[k] = (float(v[0]), str(v[1]), str(v[2]), str(v[3]))

    def _save_persisted_buffer(self) -> None:
        if self.buffer_path is not None:
            self.buffer_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "bd_seq": self.bd_seq,
                "latest_sample": {k: list(v) for k, v in sorted(self._latest_sample.items())},
            }
            self.buffer_path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")

    def _next_data_seq(self) -> int:
        # Sparkplug B v3.0: NBIRTH uses seq=0; subsequent DBIRTH/DDATA use 1..255 wrapping back to 1
        self.seq = 1 if self.seq >= 255 or self.seq <= 0 else self.seq + 1
        return self.seq

    def connect_and_birth(self, ts_utc: str) -> list[SparkplugMetricEvent]:
        """Connect/reconnect and emit NBIRTH (seq=0) followed by DBIRTH ONLY for tags with real observed samples."""
        self.connected = True
        self.bd_seq += 1
        self.seq = 0
        self._save_persisted_buffer()

        events: list[SparkplugMetricEvent] = [
            SparkplugMetricEvent(
                message_type="NBIRTH",
                bd_seq=self.bd_seq,
                seq=0,
                tag_name=f"{self.site_id}.NODE.BIRTH",
                equipment_id=self.site_id,
                value=float(self.bd_seq),
                unit="bdSeq",
                quality="Good",
                effective_at_utc=ts_utc,
                recorded_at_utc=ts_utc,
                published_at_utc=ts_utc,
            )
        ]
        # OT-001: missing sample stays missing — never invent 0.0 / Uncertain for tags with no observation
        for tag_name, meta in sorted(self.tags_by_name.items()):
            if tag_name not in self._latest_sample:
                continue
            val, qual, eff_ts, rec_ts = self._latest_sample[tag_name]
            events.append(
                SparkplugMetricEvent(
                    message_type="DBIRTH",
                    bd_seq=self.bd_seq,
                    seq=self._next_data_seq(),
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
        """Process one OT sample applying OT-01 ambiguity check, OT-02 deadband/Bad bypass, and OT-03 buffer persistence."""
        if tag_name not in self.tags_by_name:
            raise AmbiguousTagError(f"OT-01: unregistered or ambiguous OT tag {tag_name!r}")
        if quality not in ("Good", "Uncertain", "Bad"):
            raise ValueError(f"Invalid OPC UA quality code: {quality!r}")

        meta = self.tags_by_name[tag_name]
        self._latest_sample[tag_name] = (value, quality, effective_at_utc, recorded_at_utc)
        self._save_persisted_buffer()
        if not self.connected:
            return None

        deadband = float(meta["deadband"])
        prev = self._last_published.get(tag_name)
        quality_changed = (prev is None) or (prev[1] != quality)
        exceeds_deadband = (prev is None) or (abs(value - prev[0]) >= deadband)
        if not quality_changed and not exceeds_deadband:
            return None

        ev = SparkplugMetricEvent(
            message_type="DDATA",
            bd_seq=self.bd_seq,
            seq=self._next_data_seq(),
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
