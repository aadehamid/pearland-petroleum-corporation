#!/usr/bin/env python3
"""Post-restore outbox-sequence vs InboxReceipt RECOVERY_GAP checker (WP-4A/WP-4B, PO-03).

Compares committed source outbox sequences and delivery keys against applied
InboxReceipt records (and optional R2 raw-event high-water marks) scoped strictly
per `(source_system, branch_id, partition_key)` in accordance with PPC-INT-001 §2
("Source sequence is ordered only within its declared partition"; "Same key with
different digest is a conflict").

Exposes:
- Unapplied outbox rows (`RECOVERY_GAP_UNAPPLIED_OUTBOX`)
- Missing outbox rows proven committed by InboxReceipt or R2 raw log (`RECOVERY_GAP_MISSING_OUTBOX_TAIL`, `RECOVERY_GAP_MISSING_OUTBOX_VS_R2`)
- Interior per-partition sequence holes (`RECOVERY_GAP_SEQUENCE_HOLE`)
- Duplicate per-partition sequence rows (`duplicate_outbox`, `duplicate_inbox`)
- Cross-sequence delivery-key reuse or digest conflicts (`DELIVERY_KEY_REUSED_ACROSS_SEQUENCES`, `PAYLOAD_DIGEST_CONFLICT`, `DELIVERY_KEY_MISMATCH`)
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence


def _stream_key(row: Mapping[str, Any]) -> tuple[str, str, str]:
    return (
        str(row["source_system"]),
        str(row["branch_id"]),
        str(row.get("partition_key", "default")),
    )


def _normalize_r2_hw(
    r2_raw_high_water: Mapping[tuple[str, str, str], int],
) -> dict[tuple[str, str, str], int]:
    out: dict[tuple[str, str, str], int] = {}
    for k, v in r2_raw_high_water.items():
        if len(k) != 3:
            raise ValueError(
                f"r2_raw_high_water keys must be 3-tuples (source_system, branch_id, partition_key), got {k!r}"
            )
        out[(str(k[0]), str(k[1]), str(k[2]))] = int(v)
    return out


def check_recovery_gaps(
    outbox_rows: Sequence[Mapping[str, Any]],
    inbox_rows: Sequence[Mapping[str, Any]],
    r2_raw_high_water: Mapping[tuple[str, str, str], int],
) -> dict[str, Any]:
    """Compare source outbox entries against InboxReceipts and mandatory R2 raw-log high-water marks."""
    inbox_by_key: dict[tuple[str, str, str, int], dict[str, Any]] = {}
    duplicate_inbox: list[dict[str, Any]] = []
    inbox_seqs_by_stream: dict[tuple[str, str, str], list[int]] = {}
    conflicts: list[dict[str, Any]] = []

    # Track delivery_key -> (digest, first_seq_key) across ALL rows to catch cross-sequence key reuse/conflicts
    delivery_key_seen_outbox: dict[str, tuple[str, tuple[str, str, str, int]]] = {}
    delivery_key_seen_inbox: dict[str, tuple[str, tuple[str, str, str, int]]] = {}

    for row in inbox_rows:
        src, branch, part = _stream_key(row)
        seq = int(row["source_sequence"])
        inbox_seqs_by_stream.setdefault((src, branch, part), []).append(seq)
        key = (src, branch, part, seq)
        if key in inbox_by_key:
            duplicate_inbox.append({"key": key, "delivery_key": row.get("delivery_key")})
        else:
            inbox_by_key[key] = dict(row)

        dkey = str(row.get("delivery_key") or "")
        dig = str(row.get("payload_digest") or "")
        if dkey:
            if dkey in delivery_key_seen_inbox:
                prev_dig, prev_key = delivery_key_seen_inbox[dkey]
                conflicts.append(
                    {
                        "kind": "PAYLOAD_DIGEST_CONFLICT" if prev_dig != dig else "DELIVERY_KEY_REUSED_ACROSS_SEQUENCES",
                        "side": "inbox",
                        "delivery_key": dkey,
                        "first_key": prev_key,
                        "second_key": key,
                        "first_digest": prev_dig,
                        "second_digest": dig,
                    }
                )
            else:
                delivery_key_seen_inbox[dkey] = (dig, key)

    gaps: list[dict[str, Any]] = []
    duplicate_outbox: list[dict[str, Any]] = []
    outbox_by_key: dict[tuple[str, str, str, int], dict[str, Any]] = {}
    outbox_seqs_by_stream: dict[tuple[str, str, str], list[int]] = {}

    for row in outbox_rows:
        src, branch, part = _stream_key(row)
        seq = int(row["source_sequence"])
        outbox_seqs_by_stream.setdefault((src, branch, part), []).append(seq)
        key = (src, branch, part, seq)
        if key in outbox_by_key:
            duplicate_outbox.append({"key": key, "delivery_key": row.get("delivery_key")})
        else:
            outbox_by_key[key] = dict(row)

        dkey = str(row.get("delivery_key") or "")
        dig = str(row.get("payload_digest") or "")
        if dkey:
            if dkey in delivery_key_seen_outbox:
                prev_dig, prev_key = delivery_key_seen_outbox[dkey]
                conflicts.append(
                    {
                        "kind": "PAYLOAD_DIGEST_CONFLICT" if prev_dig != dig else "DELIVERY_KEY_REUSED_ACROSS_SEQUENCES",
                        "side": "outbox",
                        "delivery_key": dkey,
                        "first_key": prev_key,
                        "second_key": key,
                        "first_digest": prev_dig,
                        "second_digest": dig,
                    }
                )
            else:
                delivery_key_seen_outbox[dkey] = (dig, key)

        receipt = inbox_by_key.get(key)
        if receipt is None:
            gaps.append(
                {
                    "kind": "RECOVERY_GAP_UNAPPLIED_OUTBOX",
                    "source_system": src,
                    "branch_id": branch,
                    "partition_key": part,
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
                    "partition_key": part,
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
                    "partition_key": part,
                    "source_sequence": seq,
                    "outbox_digest": row.get("payload_digest"),
                    "inbox_digest": receipt.get("payload_digest"),
                }
            )

    r2_hw = _normalize_r2_hw(r2_raw_high_water)
    all_streams = set(outbox_seqs_by_stream) | set(inbox_seqs_by_stream) | set(r2_hw)
    for stream in sorted(all_streams):
        src, branch, part = stream
        out_seqs = sorted(set(outbox_seqs_by_stream.get(stream, [])))
        in_seqs = sorted(set(inbox_seqs_by_stream.get(stream, [])))
        max_out = out_seqs[-1] if out_seqs else 0
        max_in = in_seqs[-1] if in_seqs else 0
        max_r2 = r2_hw.get(stream, 0)

        for prev, curr in zip(out_seqs, out_seqs[1:]):
            if curr != prev + 1:
                gaps.append(
                    {
                        "kind": "RECOVERY_GAP_SEQUENCE_HOLE",
                        "source_system": src,
                        "branch_id": branch,
                        "partition_key": part,
                        "missing_range": [prev + 1, curr - 1],
                    }
                )

        missing_in_outbox = [s for s in in_seqs if (src, branch, part, s) not in outbox_by_key]
        if missing_in_outbox:
            gaps.append(
                {
                    "kind": "RECOVERY_GAP_MISSING_OUTBOX_TAIL",
                    "source_system": src,
                    "branch_id": branch,
                    "partition_key": part,
                    "outbox_high_water": max_out,
                    "inbox_high_water": max_in,
                    "missing_sequences": missing_in_outbox,
                }
            )
        if stream not in r2_hw:
            gaps.append(
                {
                    "kind": "RECOVERY_GAP_MISSING_R2_EVIDENCE",
                    "source_system": src,
                    "branch_id": branch,
                    "partition_key": part,
                    "outbox_high_water": max_out,
                }
            )
        elif r2_hw[stream] > max_out:
            gaps.append(
                {
                    "kind": "RECOVERY_GAP_MISSING_OUTBOX_VS_R2",
                    "source_system": src,
                    "branch_id": branch,
                    "partition_key": part,
                    "outbox_high_water": max_out,
                    "r2_raw_high_water": r2_hw[stream],
                }
            )

    clean = not gaps and not conflicts and not duplicate_inbox and not duplicate_outbox
    return {
        "status": "CLEAN" if clean else "RECOVERY_GAP",
        "outbox_count": len(outbox_rows),
        "inbox_count": len(inbox_rows),
        "r2_evidence_consulted_streams": sorted(f"{s}:{b}:{p}" for s, b, p in r2_hw),
        "gaps": gaps,
        "conflicts": conflicts,
        "duplicate_inbox": duplicate_inbox,
        "duplicate_outbox": duplicate_outbox,
    }
