#!/usr/bin/env python3
"""WP-8A DuckDB vs Databricks Free Edition Synced-Copy KPI Parity Diff (UC-6, ADR-0045, ADR-0055).

Compares row-level KPI and constituent operational-metric outputs computed by
DuckDB (read-only over R2 Delta Gold/KPI tables) against Databricks Free Edition
workspace-managed Delta copies (EA03C-11, SEM-10), verifying key uniqueness,
numeric tolerance (with explicit NaN/Inf rejection), null parity, and
threshold-status equivalence.
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Mapping, Sequence


def diff_duckdb_vs_databricks_kpis(
    duckdb_rows: Sequence[Mapping[str, Any]],
    databricks_rows: Sequence[Mapping[str, Any]],
    *,
    rel_tol: float = 1e-6,
    abs_tol: float = 1e-9,
) -> dict[str, Any]:
    """Perform strict row-level cross-engine KPI parity diff (SEM-10, EA03C-11)."""
    def _key(r: Mapping[str, Any]) -> tuple[str, str, str, str]:
        return (
            str(r["release_id"]),
            str(r["branch_id"]),
            str(r["kpi_name"]),
            str(r["measure_class"]),
        )

    drifts: list[dict[str, Any]] = []
    duck_map: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for r in duckdb_rows:
        k = _key(r)
        if k in duck_map:
            drifts.append({"key": list(k), "kind": "DUPLICATE_KEY_IN_DUCKDB"})
        duck_map[k] = dict(r)

    dbx_map: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for r in databricks_rows:
        k = _key(r)
        if k in dbx_map:
            drifts.append({"key": list(k), "kind": "DUPLICATE_KEY_IN_DATABRICKS"})
        dbx_map[k] = dict(r)

    for k in sorted(set(duck_map) | set(dbx_map)):
        if k not in dbx_map:
            drifts.append({"key": list(k), "kind": "MISSING_IN_DATABRICKS"})
            continue
        if k not in duck_map:
            drifts.append({"key": list(k), "kind": "MISSING_IN_DUCKDB"})
            continue
        d_row = duck_map[k]
        b_row = dbx_map[k]
        if d_row.get("threshold_status") != b_row.get("threshold_status"):
            drifts.append(
                {
                    "key": list(k),
                    "kind": "THRESHOLD_STATUS_MISMATCH",
                    "duckdb": d_row.get("threshold_status"),
                    "databricks": b_row.get("threshold_status"),
                }
            )
        dv = d_row.get("value")
        bv = b_row.get("value")
        if (dv is None) != (bv is None):
            drifts.append({"key": list(k), "kind": "NULL_HANDLING_MISMATCH", "duckdb": dv, "databricks": bv})
            continue
        if dv is not None and bv is not None:
            df = float(dv)
            bf = float(bv)
            if not math.isfinite(df) or not math.isfinite(bf):
                drifts.append(
                    {
                        "key": list(k),
                        "kind": "NON_FINITE_VALUE",
                        "duckdb": str(df),
                        "databricks": str(bf),
                    }
                )
                continue
            diff = abs(df - bf)
            limit = max(abs_tol, rel_tol * max(abs(df), abs(bf)))
            if diff > limit:
                drifts.append(
                    {
                        "key": list(k),
                        "kind": "NUMERIC_DRIFT",
                        "duckdb": df,
                        "databricks": bf,
                        "abs_diff": diff,
                    }
                )

    report = {
        "provenance_class": "DERIVED",
        "duckdb_row_count": len(duckdb_rows),
        "databricks_row_count": len(databricks_rows),
        "drift_count": len(drifts),
        "drifts": drifts,
        "status": "PARITY_PASSED" if not drifts else "PARITY_FAILED",
    }
    report["report_sha256"] = hashlib.sha256(
        json.dumps(report, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return report
