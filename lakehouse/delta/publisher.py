#!/usr/bin/env python3
"""WP-3 Delta Lake (delta-rs) + DuckDB Read-Only Publisher, Tall KPI Store, and ReleaseManifest (ADR-0045, DATA-001).

Implements:
- Serialized single-writer idempotent delta-rs appends guarded by `_delta_log` `(txnAppId, txnVersion)` scan
  and Delta `CommitProperties` + `Transaction` metadata (intended for single-writer Dagster concurrency pool = 1
  per table per PPC-PLAN-001 WP-3)
- Read-only DuckDB views over Delta tables (never writes Delta, ADR-0045)
- EPM-aligned tall KPI facts with KPI / OPERATIONAL_METRIC / MARKET_INDICATOR measure classes and T100 decomposition links
- Deterministic SHA-256 digest-verified ReleaseManifest construction and RETRACTED (L1/X1) metadata
- NEVER reads hidden canonical world truth (enforced by physical_graph.py C5)
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import duckdb
import pyarrow as pa
from deltalake import CommitProperties, DeltaTable, Transaction, write_deltalake


LEGAL_MEASURE_CLASSES = ("KPI", "OPERATIONAL_METRIC", "MARKET_INDICATOR")
LEGAL_RELEASE_STATUSES = ("PUBLISHED", "SUPERSEDED", "RETRACTED")


def canonical_digest(obj: Any) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def write_delta_table_idempotent(
    table_path: str | Path,
    rows: Sequence[Mapping[str, Any]],
    *,
    txn_app_id: str,
    txn_version: int,
    mode: str = "append",
) -> dict[str, Any]:
    """Write rows to a Delta Lake table idempotently using delta-rs (txnAppId, txnVersion)."""
    path = Path(table_path)
    path.mkdir(parents=True, exist_ok=True)
    if (path / "_delta_log").exists():
        dt = DeltaTable(str(path))
        # Scan committed _delta_log JSON entries for (appId, version) idempotency under single-writer serialization
        for log_file in sorted((path / "_delta_log").glob("*.json")):
            for line in log_file.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                rec = json.loads(line)
                txn = rec.get("txn")
                if txn and txn.get("appId") == txn_app_id and int(txn.get("version", -1)) >= txn_version:
                    return {
                        "status": "IDEMPOTENT_SKIPPED",
                        "table_path": str(path),
                        "txn_app_id": txn_app_id,
                        "txn_version": txn_version,
                        "delta_version": dt.version(),
                    }

    if not rows:
        raise ValueError("Cannot write an empty batch to Delta table")

    pa_table = pa.Table.from_pylist([dict(r) for r in rows])
    props = CommitProperties(app_transactions=[Transaction(app_id=txn_app_id, version=txn_version)])
    write_deltalake(str(path), pa_table, mode=mode, commit_properties=props)
    dt_after = DeltaTable(str(path))
    return {
        "status": "COMMITTED",
        "table_path": str(path),
        "txn_app_id": txn_app_id,
        "txn_version": txn_version,
        "delta_version": dt_after.version(),
        "row_count": len(rows),
    }


def query_delta_readonly_duckdb(table_path: str | Path, sql_where: str = "1=1") -> list[dict[str, Any]]:
    """Query a Delta table strictly read-only through DuckDB over delta-rs Arrow dataset (ADR-0045)."""
    dt = DeltaTable(str(table_path))
    arrow_tbl = dt.to_pyarrow_table(engine="datafusion")
    con = duckdb.connect(database=":memory:", read_only=False)
    try:
        con.register("delta_view", arrow_tbl)
        cur = con.execute(f"SELECT * FROM delta_view WHERE {sql_where}")
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        con.close()


@dataclass(frozen=True)
class KPIFactRow:
    release_id: str
    branch_id: str
    kpi_name: str
    measure_class: str  # KPI | OPERATIONAL_METRIC | MARKET_INDICATOR
    epm_artifact: str
    value: float
    unit: str
    parent_kpi: str | None
    effective_at_utc: str
    published_at_utc: str
    provenance_class: str = "DERIVED"
    access_label: str = "INTERNAL"

    def to_dict(self) -> dict[str, Any]:
        if self.measure_class not in LEGAL_MEASURE_CLASSES:
            raise ValueError(f"Illegal measure_class {self.measure_class!r}")
        return {
            "release_id": self.release_id,
            "branch_id": self.branch_id,
            "kpi_name": self.kpi_name,
            "measure_class": self.measure_class,
            "epm_artifact": self.epm_artifact,
            "value": float(self.value),
            "unit": self.unit,
            "parent_kpi": self.parent_kpi or "",
            "effective_at_utc": self.effective_at_utc,
            "published_at_utc": self.published_at_utc,
            "provenance_class": self.provenance_class,
            "access_label": self.access_label,
        }


def build_release_manifest(
    *,
    release_id: str,
    branch_id: str,
    status: str,
    published_at_utc: str,
    cutoff_utc: str,
    delta_tables: Mapping[str, int],
    kpi_rows: Sequence[Mapping[str, Any]],
    supersedes_release_id: str | None = None,
    retraction_reason: str | None = None,
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    """Construct a deterministic SHA-256 digest-verified ReleaseManifest for PUBLISHED / SUPERSEDED / RETRACTED."""
    if status not in LEGAL_RELEASE_STATUSES:
        raise ValueError(f"Invalid release status: {status!r}")
    if status == "RETRACTED" and not retraction_reason:
        raise ValueError("RETRACTED release requires explicit retraction_reason (DATA-001 §2 L1/X1)")

    body = {
        "schema_version": "1.0.0",
        "release_id": release_id,
        "branch_id": branch_id,
        "status": status,
        "published_at_utc": published_at_utc,
        "cutoff_utc": cutoff_utc,
        "supersedes_release_id": supersedes_release_id,
        "retraction_reason": retraction_reason,
        "delta_table_versions": dict(sorted(delta_tables.items())),
        "kpi_row_count": len(kpi_rows),
        "kpi_rows_digest": canonical_digest(list(kpi_rows)),
        "provenance_class": "DERIVED",
        "created_at_utc": created_at_utc if created_at_utc is not None else published_at_utc,
    }
    body["manifest_sha256"] = canonical_digest(body)
    return body
