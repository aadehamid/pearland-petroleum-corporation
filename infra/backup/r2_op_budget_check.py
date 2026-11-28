#!/usr/bin/env python3
"""WP-4A Cloudflare R2 free-tier Class A write-operation budget check (C9, ADR-0055).

Verifies that the 60-second SQLite Litestream / Postgres WAL / MySQL binlog /
hourly OTel Collector + daily Neo4j dump sync cadences (governed by PPC-REVIEW-003 §2
and ADR-0055) stay comfortably inside the Cloudflare R2 free-tier monthly Class A
operation allowance (1,000,000/month, per Cloudflare R2 pricing docs).

Provenance note: sync cadences are governed by PPC-REVIEW-003 §2, while per-sync
Class A op counts are conservative operational estimates, so the resulting monthly
total is classified as ESTIMATED rather than DERIVED.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence


R2_FREE_TIER_CLASS_A_OPS_PER_MONTH = 1_000_000
DAYS_PER_MONTH = 31  # conservative upper bound


@dataclass(frozen=True)
class SyncStreamSpec:
    name: str
    interval_seconds: int
    class_a_ops_per_sync: int
    description: str


DEFAULT_SLICE1_SYNC_STREAMS: tuple[SyncStreamSpec, ...] = (
    SyncStreamSpec("sqlite_litestream_refinery", 60, 2, "SQLite Litestream 60s WAL segment + manifest PUT"),
    SyncStreamSpec("postgres_wal_archive", 60, 2, "PostgreSQL 60s WAL archive + checksum PUT"),
    SyncStreamSpec("mysql_binlog_sync", 60, 2, "MySQL 60s binlog segment + index PUT"),
    SyncStreamSpec("otel_collector_hourly", 3600, 2, "Lightweight OTel Collector hourly OTLP JSON PUT to telemetry/otel/"),
    SyncStreamSpec("neo4j_offline_dump_daily", 86400, 3, "Neo4j Community daily offline neo4j-admin dump + manifest PUT"),
    SyncStreamSpec("delta_gold_kpi_publish", 900, 4, "delta-rs 15-min Silver/Gold/KPI commit + parquet + manifest PUT"),
)


def evaluate_r2_op_budget(
    streams: Sequence[SyncStreamSpec] = DEFAULT_SLICE1_SYNC_STREAMS,
    monthly_limit: int = R2_FREE_TIER_CLASS_A_OPS_PER_MONTH,
    safety_margin_ratio: float = 0.50,
) -> dict[str, Any]:
    """Compute conservative 31-day Class A write ops and verify compliance with R2 free tier."""
    seconds_per_month = DAYS_PER_MONTH * 86400
    breakdown: list[dict[str, Any]] = []
    total_ops = 0
    for s in streams:
        if s.interval_seconds <= 0 or s.class_a_ops_per_sync < 0:
            raise ValueError(f"Invalid sync spec: {s}")
        syncs = seconds_per_month // s.interval_seconds
        ops = syncs * s.class_a_ops_per_sync
        total_ops += ops
        breakdown.append(
            {
                "stream": s.name,
                "interval_seconds": s.interval_seconds,
                "class_a_ops_per_sync": s.class_a_ops_per_sync,
                "monthly_class_a_ops": ops,
                "description": s.description,
            }
        )
    utilization_pct = 100.0 * total_ops / monthly_limit
    within_free_tier = total_ops <= monthly_limit
    within_safety_margin = total_ops <= int(monthly_limit * safety_margin_ratio)
    if not within_free_tier:
        status = "FREE_TIER_EXCEEDED"
    elif not within_safety_margin:
        status = "SAFETY_MARGIN_EXCEEDED"
    else:
        status = "PASSED"
    return {
        "provenance_class": "ESTIMATED",
        "input_basis": "ESTIMATED_OP_COUNTS_ON_GOVERNED_CADENCES",
        "monthly_free_tier_limit": monthly_limit,
        "conservative_days": DAYS_PER_MONTH,
        "total_monthly_class_a_ops": total_ops,
        "utilization_pct": round(utilization_pct, 2),
        "within_free_tier": within_free_tier,
        "within_safety_margin": within_safety_margin,
        "status": status,
        "breakdown": breakdown,
    }
