#!/usr/bin/env python3
"""EDI Provisional Adapter CFG-0 Adoption Handler (WP-2, EDI-001 §2–§4, B7).

Validates WP-1's structured DEXPI CFG-0 engineering topology (`fixtures/golden/cfg0_dexpi_topology.json`),
enforces directed graph integrity (every piping connection endpoint and pump resolves to declared
equipment), compares the adopted canonical digest against an independently pinned upstream CFG-0
digest (B7), enforces per-branch `expected_prior_configuration` optimistic concurrency (EDI-001 §3),
and persists idempotent EDI-001 §2/§4 adoption receipts in SQLite across process restarts.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


EDI_PROVISIONAL_COMMIT = "12a4a6a"


def canonical_cfg0_digest(topology: Mapping[str, Any]) -> str:
    """Compute canonical SHA-256 digest over CFG-0 configuration_id, site_id, equipment, and piping_connections."""
    equipment = topology.get("equipment", [])
    connections = topology.get("piping_connections", [])
    core = {
        "configuration_id": str(topology["configuration_id"]),
        "site_id": str(topology["site_id"]),
        "equipment": sorted(equipment, key=lambda x: str(x["tag"])),
        "piping_connections": sorted(connections, key=lambda x: str(x["id"])),
    }
    return hashlib.sha256(
        json.dumps(core, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


class EDIAdoptionRegistry:
    """SQLite-backed idempotent EDI-001 §2–§4 adoption registry keyed by request_id with branch state tracking."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        if db_path is None:
            self.db_path: Path | None = None
            self.conn = sqlite3.connect(":memory:", isolation_level=None)
        else:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.conn = sqlite3.connect(str(self.db_path), isolation_level=None)
            self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS edi_adoption_receipts (
                request_id TEXT PRIMARY KEY,
                world_id TEXT NOT NULL,
                branch_id TEXT NOT NULL,
                adopted_digest TEXT NOT NULL,
                receipt_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS edi_branch_configurations (
                world_id TEXT NOT NULL,
                branch_id TEXT NOT NULL,
                active_configuration_id TEXT NOT NULL,
                adopted_digest TEXT NOT NULL,
                updated_at_utc TEXT NOT NULL,
                PRIMARY KEY (world_id, branch_id)
            );
            """
        )

    def active_configuration(self, world_id: str, branch_id: str) -> str | None:
        row = self.conn.execute(
            "SELECT active_configuration_id FROM edi_branch_configurations WHERE world_id = ? AND branch_id = ?",
            (world_id, branch_id),
        ).fetchone()
        return str(row["active_configuration_id"]) if row is not None else None

    def adopt_cfg0_topology(
        self,
        cfg0_path: str | Path,
        *,
        request_id: str,
        world_id: str,
        branch_id: str,
        authorized_actor: str,
        expected_cfg0_digest: str,
        expected_prior_configuration: str | None = None,
        edi_publication_id: str = "EDI-PUB-CFG0-V1",
        source_approval_evidence: str = "ADR-0054",
        effective_at_utc: str = "2026-06-15T00:00:00Z",
        recorded_at_utc: str | None = None,
    ) -> dict[str, Any]:
        """Validate WP-1 CFG-0 through EDI provisional adapter and persist an idempotent EDI-001 §2–§4 receipt."""
        raw = json.loads(Path(cfg0_path).read_text(encoding="utf-8"))
        equipment = raw.get("equipment", [])
        connections = raw.get("piping_connections", [])
        if not equipment or not connections:
            raise ValueError("EDI-001: CFG-0 topology must declare non-empty equipment and piping_connections")

        node_ids = {str(e["tag"]) for e in equipment}
        dangling: list[str] = []
        for conn in connections:
            src = str(conn["from"])
            dst = str(conn["to"])
            if src not in node_ids or dst not in node_ids:
                dangling.append(f"{conn['id']}: {src} -> {dst}")
            for pid in conn.get("pumps", []):
                if str(pid) not in node_ids:
                    dangling.append(f"{conn['id']}: pump {pid}")
        if dangling:
            raise ValueError(f"EDI-001: dangling directed edges or pumps in CFG-0 topology: {dangling}")

        adopted_digest = canonical_cfg0_digest(raw)
        config_id = str(raw["configuration_id"])

        cur = self.conn.cursor()
        cur.execute("BEGIN IMMEDIATE")
        try:
            # 1. Durable idempotent request_id replay vs conflict (EDI-001 §4)
            prior = cur.execute(
                "SELECT world_id, branch_id, adopted_digest, receipt_json FROM edi_adoption_receipts WHERE request_id = ?",
                (request_id,),
            ).fetchone()
            if prior is not None:
                cur.execute("ROLLBACK")
                if (
                    prior["adopted_digest"] == adopted_digest
                    and prior["branch_id"] == branch_id
                    and prior["world_id"] == world_id
                ):
                    return json.loads(prior["receipt_json"])
                reason = (
                    "DIFFERENT_SCOPE_FOR_EXISTING_REQUEST_ID"
                    if prior["adopted_digest"] == adopted_digest
                    else "DIFFERENT_PAYLOAD_FOR_EXISTING_REQUEST_ID"
                )
                return {
                    "request_id": request_id,
                    "outcome": "CONFLICT",
                    "reason": reason,
                    "prior_digest": prior["adopted_digest"],
                    "incoming_digest": adopted_digest,
                    "prior_world_id": prior["world_id"],
                    "prior_branch_id": prior["branch_id"],
                    "b7_digest_parity": False,
                }

            # 2. Non-vacuous B7 check against independently pinned expected upstream CFG-0 digest
            if adopted_digest != expected_cfg0_digest:
                cur.execute("ROLLBACK")
                raise ValueError(
                    f"B7 digest parity violation: adopted digest {adopted_digest} != expected upstream CFG-0 digest {expected_cfg0_digest}"
                )

            # 3. EDI-001 §3 prior-configuration base check before advancing branch configuration
            branch_row = cur.execute(
                "SELECT active_configuration_id FROM edi_branch_configurations WHERE world_id = ? AND branch_id = ?",
                (world_id, branch_id),
            ).fetchone()
            current_prior = str(branch_row["active_configuration_id"]) if branch_row is not None else None
            if expected_prior_configuration != current_prior:
                cur.execute("ROLLBACK")
                raise ValueError(
                    f"EDI-001 §3 prior configuration mismatch on {world_id}/{branch_id}: "
                    f"expected {expected_prior_configuration!r}, active is {current_prior!r}"
                )

            rec_ts = recorded_at_utc or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            receipt = {
                "adapter_id": "edi-provisional",
                "upstream_commit": EDI_PROVISIONAL_COMMIT,
                "request_id": request_id,
                "world_id": world_id,
                "branch_id": branch_id,
                "expected_prior_configuration": expected_prior_configuration,
                "edi_publication_id": edi_publication_id,
                "source_approval_evidence": source_approval_evidence,
                "authorized_actor": authorized_actor,
                "effective_at_utc": effective_at_utc,
                "recorded_at_utc": rec_ts,
                "outcome": "ADOPTED",
                "configuration_id": config_id,
                "site_id": str(raw["site_id"]),
                "equipment_count": len(equipment),
                "connection_count": len(connections),
                "expected_cfg0_digest": expected_cfg0_digest,
                "adopted_digest": adopted_digest,
                "b7_digest_parity": True,
                "provenance_class": "SYNTHETIC",
            }
            cur.execute(
                """
                INSERT INTO edi_adoption_receipts (request_id, world_id, branch_id, adopted_digest, receipt_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (request_id, world_id, branch_id, adopted_digest, json.dumps(receipt, sort_keys=True)),
            )
            cur.execute(
                """
                INSERT INTO edi_branch_configurations (world_id, branch_id, active_configuration_id, adopted_digest, updated_at_utc)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(world_id, branch_id) DO UPDATE SET
                    active_configuration_id = excluded.active_configuration_id,
                    adopted_digest = excluded.adopted_digest,
                    updated_at_utc = excluded.updated_at_utc
                """,
                (world_id, branch_id, config_id, adopted_digest, rec_ts),
            )
            cur.execute("COMMIT")
            return receipt
        except Exception:
            if self.conn.in_transaction:
                cur.execute("ROLLBACK")
            raise

    def close(self) -> None:
        self.conn.close()


def adopt_cfg0_topology(
    cfg0_path: str | Path,
    *,
    request_id: str,
    world_id: str,
    branch_id: str,
    authorized_actor: str,
    expected_cfg0_digest: str,
    db_path: str | Path | None = None,
    expected_prior_configuration: str | None = None,
    edi_publication_id: str = "EDI-PUB-CFG0-V1",
    source_approval_evidence: str = "ADR-0054",
    effective_at_utc: str = "2026-06-15T00:00:00Z",
    recorded_at_utc: str | None = None,
) -> dict[str, Any]:
    """Convenience wrapper around SQLite-backed EDIAdoptionRegistry (pass db_path for durable cross-restart idempotency)."""
    reg = EDIAdoptionRegistry(db_path=db_path)
    try:
        return reg.adopt_cfg0_topology(
            cfg0_path,
            request_id=request_id,
            world_id=world_id,
            branch_id=branch_id,
            authorized_actor=authorized_actor,
            expected_cfg0_digest=expected_cfg0_digest,
            expected_prior_configuration=expected_prior_configuration,
            edi_publication_id=edi_publication_id,
            source_approval_evidence=source_approval_evidence,
            effective_at_utc=effective_at_utc,
            recorded_at_utc=recorded_at_utc,
        )
    finally:
        reg.close()
