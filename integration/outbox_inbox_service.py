#!/usr/bin/env python3
"""Atomic Silver Staging + InboxReceipt Consumer and Idempotent Delta Publisher (WP-2, PO-03).

Implements INT-001 §2 and ADR-0046:
- Commits Silver staging row + InboxReceipt in ONE ACID transaction (Crash Point 1 safe).
- Identical duplicate delivery_key + payload_digest returns prior InboxReceipt (zero double effect).
- Same delivery_key + DIFFERENT payload_digest routes to conflict_quarantine (IDENTITY_STEWARD).
- Out-of-order source_revision enters revision_quarantine without inventing missing events.
- Separate captured / durable / applied / published watermarks per (source_system, branch_id).
- Crash Point 2 safe idempotent publish ledger keyed by (txn_app_id, txn_version).
- NEVER imports or queries hidden canonical world truth.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class ConsumeOutcome:
    status: str  # APPLIED | IDEMPOTENT_DUPLICATE | CONFLICT_QUARANTINED | REVISION_QUARANTINED
    delivery_key: str
    event_id: str
    payload_digest: str
    reason: str | None = None


class AtomicStagingInboxService:
    """PostgreSQL-compatible ACID staging + InboxReceipt + conflict quarantine consumer."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS inbox_receipts (
                delivery_key TEXT PRIMARY KEY,
                event_id TEXT NOT NULL,
                source_system TEXT NOT NULL,
                branch_id TEXT NOT NULL,
                partition_key TEXT NOT NULL,
                source_sequence INTEGER NOT NULL,
                source_revision INTEGER NOT NULL,
                payload_digest TEXT NOT NULL,
                applied_result TEXT NOT NULL,
                acknowledged_at_utc TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS silver_staging (
                staging_id INTEGER PRIMARY KEY AUTOINCREMENT,
                delivery_key TEXT NOT NULL UNIQUE,
                event_id TEXT NOT NULL,
                source_system TEXT NOT NULL,
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
                delta_published INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS conflict_quarantine (
                quarantine_id INTEGER PRIMARY KEY AUTOINCREMENT,
                delivery_key TEXT NOT NULL,
                event_id TEXT NOT NULL,
                branch_id TEXT NOT NULL,
                reason TEXT NOT NULL,
                existing_digest TEXT,
                incoming_digest TEXT NOT NULL,
                incoming_payload_json TEXT NOT NULL,
                resolution_status TEXT NOT NULL DEFAULT 'PENDING_IDENTITY_STEWARD',
                quarantined_at_utc TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS source_watermarks (
                source_system TEXT NOT NULL,
                branch_id TEXT NOT NULL,
                captured_seq INTEGER NOT NULL DEFAULT 0,
                durable_seq INTEGER NOT NULL DEFAULT 0,
                applied_seq INTEGER NOT NULL DEFAULT 0,
                published_seq INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (source_system, branch_id)
            );
            CREATE TABLE IF NOT EXISTS delta_publish_ledger (
                txn_app_id TEXT NOT NULL,
                txn_version INTEGER NOT NULL,
                table_name TEXT NOT NULL,
                row_count INTEGER NOT NULL,
                committed_at_utc TEXT NOT NULL,
                PRIMARY KEY (txn_app_id, txn_version)
            );
            """
        )
        self.conn.commit()

    def _upsert_watermark(
        self, cur: sqlite3.Cursor, source_system: str, branch_id: str, column: str, seq: int
    ) -> None:
        if column not in ("captured_seq", "durable_seq", "applied_seq", "published_seq"):
            raise ValueError(f"Invalid watermark column: {column}")
        cur.execute(
            "INSERT OR IGNORE INTO source_watermarks (source_system, branch_id) VALUES (?, ?)",
            (source_system, branch_id),
        )
        cur.execute(
            f"UPDATE source_watermarks SET {column} = MAX({column}, ?) WHERE source_system = ? AND branch_id = ?",
            (seq, source_system, branch_id),
        )

    def consume_event(
        self,
        event: Mapping[str, Any],
        *,
        inject_crash_after_staging_before_ack: bool = False,
        expected_prev_revision: int | None = None,
    ) -> ConsumeOutcome:
        """Apply one event atomically to Silver staging + InboxReceipt (PO-03 Crash Point 1 safe)."""
        dkey = str(event["delivery_key"])
        eid = str(event["event_id"])
        src = str(event["source_system"])
        branch = str(event["branch_id"])
        part = str(event["partition_key"])
        seq = int(event["source_sequence"])
        rev = int(event["source_revision"])
        digest = str(event["payload_digest"])
        payload_json = str(event["payload_json"])
        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        cur = self.conn.cursor()
        try:
            cur.execute("BEGIN IMMEDIATE")
            self._upsert_watermark(cur, src, branch, "captured_seq", seq)
            self._upsert_watermark(cur, src, branch, "durable_seq", seq)

            existing = cur.execute(
                "SELECT payload_digest, event_id FROM inbox_receipts WHERE delivery_key = ?",
                (dkey,),
            ).fetchone()
            if existing is not None:
                if existing["payload_digest"] == digest:
                    self.conn.commit()
                    return ConsumeOutcome(
                        status="IDEMPOTENT_DUPLICATE",
                        delivery_key=dkey,
                        event_id=eid,
                        payload_digest=digest,
                    )
                cur.execute(
                    """
                    INSERT INTO conflict_quarantine (
                        delivery_key, event_id, branch_id, reason,
                        existing_digest, incoming_digest, incoming_payload_json, quarantined_at_utc
                    ) VALUES (?, ?, ?, 'CONFLICTING_PAYLOAD_DIGEST', ?, ?, ?, ?)
                    """,
                    (dkey, eid, branch, existing["payload_digest"], digest, payload_json, now_utc),
                )
                self.conn.commit()
                return ConsumeOutcome(
                    status="CONFLICT_QUARANTINED",
                    delivery_key=dkey,
                    event_id=eid,
                    payload_digest=digest,
                    reason="CONFLICTING_PAYLOAD_DIGEST",
                )

            # Out-of-order revision check (must not invent missing predecessor revisions)
            if expected_prev_revision is not None and rev > expected_prev_revision + 1:
                cur.execute(
                    """
                    INSERT INTO conflict_quarantine (
                        delivery_key, event_id, branch_id, reason,
                        existing_digest, incoming_digest, incoming_payload_json, quarantined_at_utc
                    ) VALUES (?, ?, ?, 'OUT_OF_ORDER_REVISION', NULL, ?, ?, ?)
                    """,
                    (dkey, eid, branch, digest, payload_json, now_utc),
                )
                self.conn.commit()
                return ConsumeOutcome(
                    status="REVISION_QUARANTINED",
                    delivery_key=dkey,
                    event_id=eid,
                    payload_digest=digest,
                    reason="OUT_OF_ORDER_REVISION",
                )

            cur.execute(
                """
                INSERT INTO silver_staging (
                    delivery_key, event_id, source_system, branch_id, partition_key,
                    source_sequence, source_revision, event_type,
                    effective_at_utc, recorded_at_utc, published_at_utc,
                    provenance_class, access_label, payload_digest, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    dkey,
                    eid,
                    src,
                    branch,
                    part,
                    seq,
                    rev,
                    str(event["event_type"]),
                    str(event["effective_at_utc"]),
                    str(event["recorded_at_utc"]),
                    event.get("published_at_utc"),
                    str(event.get("provenance_class", "SYNTHETIC")),
                    str(event.get("access_label", "INTERNAL")),
                    digest,
                    payload_json,
                ),
            )
            cur.execute(
                """
                INSERT INTO inbox_receipts (
                    delivery_key, event_id, source_system, branch_id, partition_key,
                    source_sequence, source_revision, payload_digest, applied_result, acknowledged_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'APPLIED', ?)
                """,
                (dkey, eid, src, branch, part, seq, rev, digest, now_utc),
            )
            self._upsert_watermark(cur, src, branch, "applied_seq", seq)
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

        if inject_crash_after_staging_before_ack:
            # Crash Point 1: DB commit succeeded, NATS ack lost -> redelivery MUST hit IDEMPOTENT_DUPLICATE
            raise RuntimeError("INJECTED_CRASH_POINT_1_BEFORE_NATS_ACK")

        return ConsumeOutcome(
            status="APPLIED",
            delivery_key=dkey,
            event_id=eid,
            payload_digest=digest,
        )

    def publish_staging_to_delta_idempotent(
        self,
        *,
        txn_app_id: str,
        txn_version: int,
        table_name: str,
        source_system: str,
        branch_id: str,
        sink_commit_fn: Any,
        inject_crash_after_sink_before_mark: bool = False,
    ) -> dict[str, Any]:
        """PO-03 Crash Point 2 safe idempotent publisher using (txnAppId, txnVersion)."""
        prior = self.conn.execute(
            "SELECT row_count FROM delta_publish_ledger WHERE txn_app_id = ? AND txn_version = ?",
            (txn_app_id, txn_version),
        ).fetchone()
        if prior is not None:
            return {"status": "IDEMPOTENT_ALREADY_PUBLISHED", "row_count": int(prior["row_count"])}

        rows = [
            dict(r)
            for r in self.conn.execute(
                """
                SELECT * FROM silver_staging
                WHERE source_system = ? AND branch_id = ? AND delta_published = 0
                ORDER BY staging_id ASC
                """,
                (source_system, branch_id),
            ).fetchall()
        ]
        if not rows:
            return {"status": "NO_PENDING_ROWS", "row_count": 0}

        # Sink itself must enforce idempotency on (txn_app_id, txn_version) just like delta-rs
        sink_commit_fn(table_name=table_name, rows=rows, txn_app_id=txn_app_id, txn_version=txn_version)

        if inject_crash_after_sink_before_mark:
            # Crash Point 2: Delta committed on R2, worker died before updating staging published watermark
            raise RuntimeError("INJECTED_CRASH_POINT_2_BEFORE_STAGING_MARK")

        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        max_seq = max(int(r["source_sequence"]) for r in rows)
        ids = [int(r["staging_id"]) for r in rows]
        cur = self.conn.cursor()
        try:
            cur.execute("BEGIN IMMEDIATE")
            cur.executemany("UPDATE silver_staging SET delta_published = 1 WHERE staging_id = ?", [(i,) for i in ids])
            cur.execute(
                """
                INSERT INTO delta_publish_ledger (txn_app_id, txn_version, table_name, row_count, committed_at_utc)
                VALUES (?, ?, ?, ?, ?)
                """,
                (txn_app_id, txn_version, table_name, len(rows), now_utc),
            )
            self._upsert_watermark(cur, source_system, branch_id, "published_seq", max_seq)
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
        return {"status": "PUBLISHED", "row_count": len(rows), "published_seq": max_seq}

    def watermarks(self, source_system: str, branch_id: str) -> dict[str, int]:
        row = self.conn.execute(
            "SELECT captured_seq, durable_seq, applied_seq, published_seq FROM source_watermarks WHERE source_system = ? AND branch_id = ?",
            (source_system, branch_id),
        ).fetchone()
        if row is None:
            return {"captured_seq": 0, "durable_seq": 0, "applied_seq": 0, "published_seq": 0}
        return dict(row)

    def staging_count(self) -> int:
        return int(self.conn.execute("SELECT COUNT(*) FROM silver_staging").fetchone()[0])

    def quarantine_count(self) -> int:
        return int(self.conn.execute("SELECT COUNT(*) FROM conflict_quarantine").fetchone()[0])

    def close(self) -> None:
        self.conn.close()
