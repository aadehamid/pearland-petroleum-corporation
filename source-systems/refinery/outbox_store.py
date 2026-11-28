#!/usr/bin/env python3
"""Transactional source-system stores with atomic OutboxEntry capture (WP-2, INT-001, ADR-0046).

Provides SQLite-backed Refinery/LIMS, PostgreSQL-compatible Commercial/CTRM, and
MySQL-compatible Logistics/Movement stores. Every business mutation commits its
native record and an OutboxEntry in ONE ACID transaction. No module in this package
ever reads canonical hidden world truth.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


def canonical_payload_digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class OutboxRecord:
    outbox_id: int
    source_system: str
    source_tx_id: str
    event_id: str
    delivery_key: str
    branch_id: str
    partition_key: str
    source_sequence: int
    source_revision: int
    event_type: str
    effective_at_utc: str
    recorded_at_utc: str
    published_at_utc: str | None
    provenance_class: str
    access_label: str
    payload_digest: str
    payload_json: str
    publish_status: str


class TransactionalOutboxSourceStore:
    """Base ACID store combining native business tables and transactional outbox_entries."""

    def __init__(self, db_path: str | Path, source_system: str):
        self.db_path = Path(db_path)
        self.source_system = source_system
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS native_records (
                native_entity_key TEXT NOT NULL,
                source_revision INTEGER NOT NULL,
                branch_id TEXT NOT NULL,
                record_type TEXT NOT NULL,
                effective_at_utc TEXT NOT NULL,
                recorded_at_utc TEXT NOT NULL,
                provenance_class TEXT NOT NULL,
                access_label TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                PRIMARY KEY (native_entity_key, source_revision, branch_id)
            );
            CREATE TABLE IF NOT EXISTS outbox_entries (
                outbox_id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_system TEXT NOT NULL,
                source_tx_id TEXT NOT NULL,
                event_id TEXT NOT NULL UNIQUE,
                delivery_key TEXT NOT NULL UNIQUE,
                branch_id TEXT NOT NULL,
                partition_key TEXT NOT NULL,
                source_sequence INTEGER NOT NULL,
                source_revision INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                effective_at_utc TEXT NOT NULL,
                recorded_at_utc TEXT NOT NULL,
                published_at_utc TEXT,
                provenance_class TEXT NOT NULL,
                access_label TEXT NOT NULL,
                payload_digest TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                publish_status TEXT NOT NULL DEFAULT 'PENDING'
            );
            """
        )
        self.conn.commit()

    def commit_with_outbox(
        self,
        *,
        source_tx_id: str,
        event_id: str,
        delivery_key: str,
        branch_id: str,
        partition_key: str,
        native_entity_key: str,
        source_revision: int,
        event_type: str,
        effective_at_utc: str,
        recorded_at_utc: str,
        payload: Mapping[str, Any],
        provenance_class: str = "SYNTHETIC",
        access_label: str = "INTERNAL",
        inject_crash_before_commit: bool = False,
    ) -> OutboxRecord:
        """Atomically persist native business record + OutboxEntry in one ACID transaction."""
        payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        digest = canonical_payload_digest(payload)
        cur = self.conn.cursor()
        try:
            cur.execute("BEGIN IMMEDIATE")
            row = cur.execute(
                "SELECT COALESCE(MAX(source_sequence), 0) FROM outbox_entries WHERE partition_key = ? AND branch_id = ?",
                (partition_key, branch_id),
            ).fetchone()
            next_seq = int(row[0]) + 1
            cur.execute(
                """
                INSERT INTO native_records (
                    native_entity_key, source_revision, branch_id, record_type,
                    effective_at_utc, recorded_at_utc, provenance_class, access_label, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    native_entity_key,
                    source_revision,
                    branch_id,
                    event_type,
                    effective_at_utc,
                    recorded_at_utc,
                    provenance_class,
                    access_label,
                    payload_json,
                ),
            )
            cur.execute(
                """
                INSERT INTO outbox_entries (
                    source_system, source_tx_id, event_id, delivery_key, branch_id,
                    partition_key, source_sequence, source_revision, event_type,
                    effective_at_utc, recorded_at_utc, provenance_class, access_label,
                    payload_digest, payload_json, publish_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING')
                """,
                (
                    self.source_system,
                    source_tx_id,
                    event_id,
                    delivery_key,
                    branch_id,
                    partition_key,
                    next_seq,
                    source_revision,
                    event_type,
                    effective_at_utc,
                    recorded_at_utc,
                    provenance_class,
                    access_label,
                    digest,
                    payload_json,
                ),
            )
            if inject_crash_before_commit:
                raise RuntimeError("INJECTED_CRASH_BEFORE_SOURCE_COMMIT")
            outbox_id = int(cur.lastrowid)
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
        return OutboxRecord(
            outbox_id=outbox_id,
            source_system=self.source_system,
            source_tx_id=source_tx_id,
            event_id=event_id,
            delivery_key=delivery_key,
            branch_id=branch_id,
            partition_key=partition_key,
            source_sequence=next_seq,
            source_revision=source_revision,
            event_type=event_type,
            effective_at_utc=effective_at_utc,
            recorded_at_utc=recorded_at_utc,
            published_at_utc=None,
            provenance_class=provenance_class,
            access_label=access_label,
            payload_digest=digest,
            payload_json=payload_json,
            publish_status="PENDING",
        )

    def fetch_pending_outbox(self, branch_id: str | None = None) -> list[OutboxRecord]:
        sql = "SELECT * FROM outbox_entries WHERE publish_status = 'PENDING'"
        params: list[Any] = []
        if branch_id is not None:
            sql += " AND branch_id = ?"
            params.append(branch_id)
        sql += " ORDER BY outbox_id ASC"
        rows = self.conn.execute(sql, params).fetchall()
        return [OutboxRecord(**dict(r)) for r in rows]

    def mark_published(self, delivery_key: str, published_at_utc: str | None = None) -> None:
        ts = published_at_utc or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.conn.execute(
            "UPDATE outbox_entries SET publish_status = 'PUBLISHED', published_at_utc = ? WHERE delivery_key = ?",
            (ts, delivery_key),
        )
        self.conn.commit()

    def count_native_records(self) -> int:
        return int(self.conn.execute("SELECT COUNT(*) FROM native_records").fetchone()[0])

    def close(self) -> None:
        self.conn.close()
