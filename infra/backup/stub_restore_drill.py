#!/usr/bin/env python3
"""WP-4A baseline SQLite-only stub-writer backup and restore drill (ADR-0051, ADR-0055).

Creates a deterministic SQLite operational store with transactional outbox rows,
snapshots it to a backup artifact, records pre-restore canonical SHA-256 state hash,
corrupts the live DB file, restores from the backup artifact, times restore plus
RECOVERY_GAP verification, and verifies exact pre/post state-hash parity. Full
multi-store live RTO <= 1 hour qualification at Slice 1 data volume runs in WP-4B.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import tempfile
import time
from pathlib import Path
from typing import Any

from infra.backup.recovery_gap_checker import check_recovery_gaps


def _canonical_db_digest(db_path: Path) -> tuple[str, list[dict[str, Any]]]:
    con = sqlite3.connect(str(db_path))
    try:
        rows = con.execute(
            "SELECT source_system, branch_id, source_sequence, delivery_key, payload_digest "
            "FROM outbox_entries ORDER BY source_sequence"
        ).fetchall()
    finally:
        con.close()
    records = [
        {
            "source_system": r[0],
            "branch_id": r[1],
            "source_sequence": int(r[2]),
            "delivery_key": r[3],
            "payload_digest": r[4],
        }
        for r in rows
    ]
    digest = hashlib.sha256(json.dumps(records, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return digest, records


def run_sqlite_stub_restore_drill(row_count: int = 25) -> dict[str, Any]:
    """Execute a complete timed corruption-and-restore drill in an isolated temp workspace."""
    with tempfile.TemporaryDirectory(prefix="ppc-wp4a-drill-") as tmp:
        root = Path(tmp)
        live_db = root / "refinery_live.sqlite3"
        backup_db = root / "backup_snapshot.sqlite3"

        # 1. Seed synthetic stub outbox transactions in WAL mode
        con = sqlite3.connect(str(live_db))
        con.execute("PRAGMA journal_mode=WAL;")
        con.execute(
            """
            CREATE TABLE outbox_entries (
                source_system TEXT NOT NULL,
                branch_id TEXT NOT NULL,
                source_sequence INTEGER NOT NULL PRIMARY KEY,
                delivery_key TEXT NOT NULL,
                payload_digest TEXT NOT NULL
            )
            """
        )
        inbox_rows: list[dict[str, Any]] = []
        for seq in range(1, row_count + 1):
            pdig = hashlib.sha256(f"stub-payload-{seq}".encode("utf-8")).hexdigest()
            dkey = f"refinery_lims:stub:{seq}"
            con.execute(
                "INSERT INTO outbox_entries VALUES (?, ?, ?, ?, ?)",
                ("refinery_lims", "baseline", seq, dkey, pdig),
            )
            inbox_rows.append(
                {
                    "source_system": "refinery_lims",
                    "branch_id": "baseline",
                    "source_sequence": seq,
                    "delivery_key": dkey,
                    "payload_digest": pdig,
                }
            )
        con.commit()

        # 2. Consistent online SQLite backup API snapshot (matches Litestream / WAL snapshot semantics)
        bcon = sqlite3.connect(str(backup_db))
        con.backup(bcon)
        bcon.close()
        con.close()

        pre_digest, _ = _canonical_db_digest(live_db)

        # 3. Inject catastrophic local corruption (overwrite live DB bytes with garbage)
        live_db.write_bytes(b"CORRUPTED_STORAGE_SECTORS_" * 64)
        for wal_ext in ("-wal", "-shm"):
            wal_file = Path(f"{live_db}{wal_ext}")
            if wal_file.exists():
                wal_file.unlink()

        # 4. Timed restore from backup snapshot including mandatory RECOVERY_GAP verification
        t0 = time.monotonic()
        shutil.copy2(backup_db, live_db)
        post_digest, restored_outbox = _canonical_db_digest(live_db)
        gap_report = check_recovery_gaps(restored_outbox, inbox_rows)
        rto_seconds = time.monotonic() - t0
        passed = (pre_digest == post_digest) and (gap_report["status"] == "CLEAN") and (rto_seconds <= 3600.0)
        return {
            "provenance_class": "SYNTHETIC",
            "store": "sqlite_refinery_stub",
            "row_count": row_count,
            "pre_restore_sha256": pre_digest,
            "post_restore_sha256": post_digest,
            "hash_equal": pre_digest == post_digest,
            "stub_drill_elapsed_seconds": round(rto_seconds, 6),
            "stub_drill_scope": "sqlite_only_baseline_not_wp4b_live_rto_proof",
            "recovery_gap_status": gap_report["status"],
            "status": "PASSED" if passed else "FAILED",
        }
