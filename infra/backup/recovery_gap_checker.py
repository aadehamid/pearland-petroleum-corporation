#!/usr/bin/env python3
"""Post-restore outbox-sequence vs InboxReceipt RECOVERY_GAP checker (WP-4A/WP-4B, PO-03).

Compares committed source outbox sequences against applied InboxReceipt records
after a store restore to expose any missing sequence numbers (`RECOVERY_GAP`),
digest conflicts (`PAYLOAD_CONFLICT`), or duplicate deliveries cleanly.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence


def check_recovery_gaps(
    outbox_rows: Sequence[Mapping[str, Any]],
    inbox_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Compare source outbox entries against applied InboxReceipts per (source_system, branch_id)."""
    inbox_by_key: dict[tuple[str, str, int], dict[str, Any]] = {}
    duplicate_inbox: list[dict[str, Any]] = []
    for row in inbox_rows:
        key = (str(row["source_system"]), str(row["branch_id"]), int(row["source_sequence"]))
        if key in inbox_by_key:
            duplicate_inbox.append({"key": key, "delivery_key": row.get("delivery_key")})
        else:
            inbox_by_key[key] = dict(row)

    gaps: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    outbox_seqs_by_stream: dict[tuple[str, str], list[int]] = {}

    for row in outbox_rows:
        src = str(row["source_system"])
        branch = str(row["branch_id"])
        seq = int(row["source_sequence"])
        outbox_seqs_by_stream.setdefault((src, branch), []).append(seq)

        key = (src, branch, seq)
        receipt = inbox_by_key.get(key)
        if receipt is None:
            gaps.append(
                {
                    "kind": "RECOVERY_GAP_UNAPPLIED_OUTBOX",
                    "source_system": src,
                    "branch_id": branch,
                    "source_sequence": seq,
                    "delivery_key": row.get("delivery_key"),
                }
            )
        elif str(receipt.get("payload_digest")) != str(row.get("payload_digest")):
            conflicts.append(
                {
                    "kind": "PAYLOAD_DIGEST_CONFLICT",
                    "source_system": src,
                    "branch_id": branch,
                    "source_sequence": seq,
                    "outbox_digest": row.get("payload_digest"),
                    "inbox_digest": receipt.get("payload_digest"),
                }
            )

    # Check sequence contiguity inside each (source_system, branch_id) stream
    for (src, branch), seqs in sorted(outbox_seqs_by_stream.items()):
        ordered = sorted(set(seqs))
        for prev, curr in zip(ordered, ordered[1:]):
            if curr != prev + 1:
                gaps.append(
                    {
                        "kind": "RECOVERY_GAP_SEQUENCE_HOLE",
                        "source_system": src,
                        "branch_id": branch,
                        "missing_range": [prev + 1, curr - 1],
                    }
                )

    clean = not gaps and not conflicts and not duplicate_inbox
    return {
        "status": "CLEAN" if clean else "RECOVERY_GAP",
        "outbox_count": len(outbox_rows),
        "inbox_count": len(inbox_rows),
        "gaps": gaps,
        "conflicts": conflicts,
        "duplicate_inbox": duplicate_inbox,
    }
