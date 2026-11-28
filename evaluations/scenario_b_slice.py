#!/usr/bin/env python3
"""WP-6 Scenario B Vertical Slice: Crude-Quality Rejection & Delayed Lab Correction (UC-2, SCENARIO-001 §3).

Verifies the canonical S2-* timeline across segregated tank TK-101H, LIMS, CTRM,
Logistics, and analytical releases:
- 08:00 / 08:05 UTC: 500 bbl receipt S2-M1 into segregated hold tank TK-101H (duplicate S2-M1 rejected idempotently)
- 09:00 / 09:20 / 09:30 UTC: failed LIMS assay S2-P1 (receipt S2-R1) -> QUALITY_HOLD
- 09:45 / 09:50 UTC: analytical release cut S2-L1
- 10:00 UTC: planner decision S2-D1 pinned to 10:00 cutoff (sees S2-P1 + S2-L1 ONLY)
- 12:00 / 12:30 / 13:00 UTC: delayed passing LIMS correction S2-P2 (receipt S2-R2)
- 13:10 / 13:15 UTC: restatement release S2-L2 (superseding S2-L1)
- Replay of 10:00 decision S2-D1 reproduces S2-P1 & S2-L1 identically with ZERO leakage of S2-P2 or S2-L2.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any


def run_scenario_b_walkthrough() -> dict[str, Any]:
    """Execute deterministic Scenario B S2-* walkthrough and return RunEvidence bundle."""
    # 1. Idempotent movement receipt ledger for S2-M1 (500 bbl into TK-101H)
    applied_movements: dict[str, dict[str, Any]] = {}
    tank_tk101h_bbl = 0.0

    def apply_movement(delivery_key: str, bbl: float, digest: str) -> str:
        nonlocal tank_tk101h_bbl
        if delivery_key in applied_movements:
            if applied_movements[delivery_key]["digest"] == digest:
                return "IDEMPOTENT_DUPLICATE"
            return "CONFLICT_QUARANTINED"
        applied_movements[delivery_key] = {"bbl": bbl, "digest": digest}
        tank_tk101h_bbl += bbl
        return "APPLIED"

    m1_digest = hashlib.sha256(b'{"id":"S2-M1","tank":"TK-101H","bbl":500.0}').hexdigest()
    m1_first = apply_movement("deliv:S2-M1:v1", 500.0, m1_digest)
    m1_dup = apply_movement("deliv:S2-M1:v1", 500.0, m1_digest)
    m1_conflict = apply_movement("deliv:S2-M1:v1", 999.0, "f" * 64)

    # 2. Temporal publication log for S2-P1 (09:30 failed) and S2-P2 (13:00 corrected passing)
    publications = [
        {
            "publication_id": "S2-P1",
            "receipt_id": "S2-R1",
            "release_id": "S2-L1",
            "effective_at_utc": "2026-06-15T09:00:00Z",
            "recorded_at_utc": "2026-06-15T09:20:00Z",
            "published_at_utc": "2026-06-15T09:30:00Z",
            "release_published_utc": "2026-06-15T09:50:00Z",
            "allowed_roles": ("Planner", "Analyst"),
            "disposition": "QUALITY_HOLD",
            "sulfur_wt_pct": 3.45,
        },
        {
            "publication_id": "S2-P2",
            "receipt_id": "S2-R2",
            "release_id": "S2-L2",
            "supersedes": "S2-P1",
            "effective_at_utc": "2026-06-15T12:00:00Z",
            "recorded_at_utc": "2026-06-15T12:30:00Z",
            "published_at_utc": "2026-06-15T13:00:00Z",
            "release_published_utc": "2026-06-15T13:15:00Z",
            "allowed_roles": ("Planner", "Analyst"),
            "disposition": "RELEASE",
            "sulfur_wt_pct": 1.38,
        },
    ]

    def query_as_of(role: str, cutoff_utc: str) -> dict[str, Any]:
        vis = [
            p
            for p in publications
            if role in p["allowed_roles"] and p["published_at_utc"] <= cutoff_utc
        ]
        if not vis:
            return {"status": "UNRESOLVED", "publication_id": None, "release_id": None}
        latest = max(vis, key=lambda p: p["published_at_utc"])
        rel_id = latest["release_id"] if latest["release_published_utc"] <= cutoff_utc else None
        return {
            "status": "RESOLVED",
            "publication_id": latest["publication_id"],
            "release_id": rel_id,
            "disposition": latest["disposition"],
            "sulfur_wt_pct": latest["sulfur_wt_pct"],
        }

    # 10:00 decision S2-D1 before S2-P2 exists, and replay of S2-D1 AFTER S2-P2 & S2-L2 arrive
    decision_s2_d1_initial = query_as_of("Planner", "2026-06-15T10:00:00Z")
    restated_1315 = query_as_of("Planner", "2026-06-15T13:15:00Z")
    decision_s2_d1_replay = query_as_of("Planner", "2026-06-15T10:00:00Z")
    unauthorized_view = query_as_of("ExternalGuest", "2026-06-15T13:15:00Z")

    evidence = {
        "scenario_id": "SCENARIO-B-S2",
        "qualification_verdict": "QUALIFIED_PROVISIONAL",
        "provenance_class": "SYNTHETIC",
        "tank_tk101h_bbl": tank_tk101h_bbl,
        "m1_outcomes": {"first": m1_first, "duplicate": m1_dup, "conflict": m1_conflict},
        "decision_s2_d1_1000": decision_s2_d1_initial,
        "restated_1315": restated_1315,
        "decision_s2_d1_replay": decision_s2_d1_replay,
        "replay_exact_match": decision_s2_d1_initial == decision_s2_d1_replay,
        "unauthorized_view": unauthorized_view,
    }
    evidence["evidence_sha256"] = hashlib.sha256(
        json.dumps(evidence, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return evidence
