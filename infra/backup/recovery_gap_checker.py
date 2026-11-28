#!/usr/bin/env python3
"""Post-restore outbox-sequence vs InboxReceipt RECOVERY_GAP checker (WP-4A/WP-4B, PO-03).

Compares committed source outbox sequences and delivery keys against applied
InboxReceipt records (and optional R2 raw-event high-water marks) after a store
restore to expose:
- Unapplied outbox rows (`RECOVERY_GAP_UNAPPLIED_OUTBOX`)
- Missing outbox tail where InboxReceipt or R2 raw log proves higher committed sequence (`RECOVERY_GAP_MISSING_OUTBOX_TAIL`)
- Interior sequence holes (`RECOVERY_GAP_SEQUENCE_HOLE`)
- Duplicate outbox or inbox entries (`duplicate_outbox`, `duplicate_inbox`)
- Payload digest or delivery-key conflicts (`PAYLOAD_DIGEST_CONFLICT`, `DELIVERY_KEY_MISMATCH`)
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence


def check_recovery_gaps(
    outbox_rows: Sequence[Mapping[str, Any]],
    inbox_rows: Sequence[Mapping[str, Any]],
    r2_raw_high_water: Mapping[tuple[str, str], int] | None = None,
) -> dict[str, Any]:
    """Compare source outbox entries against applied InboxReceipts per (source_system, branch_id)."""
    inbox_by_key: dict[tuple[str, str, int], dict[str, Any]] = {}
    duplicate_inbox: list[dict[str, Any]] = []
    inbox_seqs_by_stream: dict[tuple[str, str], list[int]] = {}
    for row in inbox_rows:
        src = str(row["source_system"])
        branch = str(row["branch_id"])
        seq = int(row["source_sequence"])
        inbox_seqs_by_stream.setdefault((src, branch), []).append(seq)
        key = (src, branch, seq)
        if key in inbox_by_key:
            duplicate_inbox.append({"key": key, "delivery_key": row.get("delivery_key")})
        else:
            inbox_by_key[key] = dict(row)

    gaps: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    duplicate_outbox: list[dict[str, Any]] = []
    outbox_by_key: dict[tuple[str, str, int], dict[str, Any]] = {}
    outbox_seqs_by_stream: dict[tuple[str, str], list[int]] = {}

    for row in outbox_rows:
        src = str(row["source_system"])
        branch = str(row["branch_id"])
        seq = int(row["source_sequence"])
        outbox_seqs_by_stream.setdefault((src, branch), []).append(seq)
        key = (src, branch, seq)
        if key in outbox_by_key:
            duplicate_outbox.append({"key": key, "delivery_key": row.get("delivery_key")})
            continue
        outbox_by_key[key] = dict(row)

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
            continue

        if str(receipt.get("delivery_key")) != str(row.get("delivery_key")):
            conflicts.append(
                {
                    "kind": "DELIVERY_KEY_MISMATCH",
                    "source_system": src,
                    "branch_id": branch,
                    "source_sequence": seq,
                    "outbox_delivery_key": row.get("delivery_key"),
                    "inbox_delivery_key": receipt.get("delivery_key"),
                }
            )
        if str(receipt.get("payload_digest")) != str(row.get("payload_digest")):
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

    # Detect lost outbox tail (InboxReceipt or R2 raw event log has sequences absent from restored outbox)
    all_streams = set(outbox_seqs_by_stream) | set(inbox_seqs_by_stream) | set(r2_raw_high_water or {})
    for stream in sorted(all_streams):
        src, branch = stream
        out_seqs = sorted(set(outbox_seqs_by_stream.get(stream, [])))
        in_seqs = sorted(set(inbox_seqs_by_stream.get(stream, [])))
        max_out = out_seqs[-1] if out_seqs else 0
        max_in = in_seqs[-1] if in_seqs else 0
        max_r2 = int((r2_raw_high_water or {}).get(stream, 0))

        # Interior holes in outbox sequences
        for prev, curr in zip(out_seqs, out_seqs[1:]):
            if curr != prev + 1:
                gaps.append(
                    {
                        "kind": "RECOVERY_GAP_SEQUENCE_HOLE",
                        "source_system": src,
                        "branch_id": branch,
                        "missing_range": [prev + 1, curr - 1],
                    }
                )

        # Inbox receipts present that are missing from restored outbox (tail truncation or partial snapshot)
        missing_in_outbox = [s for s in in_seqs if (src, branch, s) not in outbox_by_key]
        if missing_in_outbox:
            gaps.append(
                {
                    "kind": "RECOVERY_GAP_MISSING_OUTBOX_TAIL",
                    "source_system": src,
                    "branch_id": branch,
                    "outbox_high_water": max_out,
                    "inbox_high_water": max_in,
                    "missing_sequences": missing_in_outbox,
                }
            )
        if max_r2 > max_out:
            gaps.append(
                {
                    "kind": "RECOVERY_GAP_MISSING_OUTBOX_VS_R2",
                    "source_system": src,
                    "branch_id": branch,
                    "outbox_high_water": max_out,
                    "r2_raw_high_water": max_r2,
                }
            )

    clean = not gaps and not conflicts and not duplicate_inbox and not duplicate_outbox
    return {
        "status": "CLEAN" if clean else "RECOVERY_GAP",
        "outbox_count": len(outbox_rows),
        "inbox_count": len(inbox_rows),
        "gaps": gaps,
        "conflicts": conflicts,
        "duplicate_inbox": duplicate_inbox,
        "duplicate_outbox": duplicate_outbox,
    }
