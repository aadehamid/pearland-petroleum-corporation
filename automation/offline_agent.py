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


REDACT_KEYS = frozenset({"password", "password_hash", "token", "secret", "restricted_payload", "api_key"})


def redact_otel_attributes(attrs: Mapping[str, Any]) -> dict[str, Any]:
    """Strip restricted or secret attributes before writing OTLP JSON telemetry to R2."""
    cleaned: dict[str, Any] = {}
    for k, v in attrs.items():
        if k.lower() in REDACT_KEYS or "secret" in k.lower() or "restricted" in k.lower():
            cleaned[k] = "[REDACTED]"
        elif isinstance(v, Mapping):
            cleaned[k] = redact_otel_attributes(v)
        else:
            cleaned[k] = v
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
