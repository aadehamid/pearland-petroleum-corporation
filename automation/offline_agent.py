#!/usr/bin/env python3
"""Offline Recorded-Response Agent Adapter & Redacted OTel Trace Exporter (WP-3B, N10, ADR-0059).

Runs golden agent evaluations strictly against deterministic recorded fixtures under
fixtures/golden/agent_recorded_responses/. Live LLM endpoint wiring is intentionally
deferred pending Hamid Adesokan's endpoint selection per ADR-0059.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


SENSITIVE_SUBSTRINGS = (
    "secret",
    "token",
    "password",
    "authorization",
    "api_key",
    "apikey",
    "bearer",
    "credential",
    "restricted",
    "private_key",
)


def _is_sensitive_key(key: str) -> bool:
    lk = key.lower()
    return any(tok in lk for tok in SENSITIVE_SUBSTRINGS)


def _redact_value(val: Any) -> Any:
    if isinstance(val, Mapping):
        return redact_otel_attributes(val)
    if isinstance(val, list):
        return [_redact_value(item) for item in val]
    if isinstance(val, tuple):
        return [_redact_value(item) for item in val]
    if isinstance(val, str):
        low = val.lower()
        if any(
            pat in low
            for pat in ("bearer ", "token=", "secret=", "password=", "api_key=", "apikey=", "authorization:")
        ):
            return "[REDACTED]"
    return val


def redact_otel_attributes(attrs: Mapping[str, Any]) -> dict[str, Any]:
    """Recursively strip restricted or secret attributes (including inside lists) before OTLP export."""
    cleaned: dict[str, Any] = {}
    for k, v in attrs.items():
        if _is_sensitive_key(str(k)):
            cleaned[k] = "[REDACTED]"
        else:
            cleaned[k] = _redact_value(v)
    return cleaned


class RecordedResponseAgentAdapter:
    """Deterministic offline agent runner backed by committed JSON response fixtures (no live LLM calls)."""

    mode = "OFFLINE_RECORDED_FIXTURE_ONLY"
    live_llm_status = "DEFERRED_PENDING_OWNER_CHOICE_ADR_0059"

    def __init__(self, fixture_path: str | Path):
        self.fixture = json.loads(Path(fixture_path).read_text(encoding="utf-8"))

    def run_investigation(self, scenario_id: str, cutoff_utc: str, reader_role: str) -> dict[str, Any]:
        cases = self.fixture.get("cases", {})
        if scenario_id not in cases:
            raise KeyError(f"No recorded response fixture for scenario {scenario_id!r}")
        case = cases[scenario_id]
        trace = redact_otel_attributes(
            {
                "scenario_id": scenario_id,
                "cutoff_utc": cutoff_utc,
                "reader_role": reader_role,
                "adapter_mode": self.mode,
                "restricted_payload": "SHOULD_NEVER_APPEAR_IN_TRACE",
            }
        )
        return {
            "scenario_id": scenario_id,
            "cutoff_utc": cutoff_utc,
            "potential_exposure_paths": list(case["potential_exposure_paths"]),
            "model_quantified_cards": list(case["model_quantified_cards"]),
            "recommended_action": dict(case["recommended_action"]),
            "otel_span": trace,
            "provenance_class": "SYNTHETIC",
        }
