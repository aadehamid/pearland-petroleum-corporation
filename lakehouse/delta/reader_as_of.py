#!/usr/bin/env python3
"""INFO-001 §3 Reader-as-of Selection Engine & DATA-001 §2 L1/X1 Release Resolver (WP-3, PO-08).

Enforces strict temporal and authorization non-interference matching `check_package.py` fixtures:
- Parses all ISO-8601 timestamps as timezone-aware UTC datetimes (never lexicographic string compare).
- Eligibility requires ALL of:
  1. Active ALLOW grant (with no matching DENY) for `(reader_role, channel, purpose)` at `cutoff`.
  2. `recorded_at_utc <= cutoff` AND `published_at_utc <= cutoff`.
  3. A `DeliveryReceipt` for `(publication_id, reader_role, channel)` with `published_at <= delivered_at <= cutoff`.
  4. An explicit published `ReleaseEvent` (`PUBLISHED`/`SUPERSEDED`) that has NOT been effectively retracted
     by an authorized, delivered retraction event at or before `cutoff` (`DATA-001 §2` L1/X1; earlier
     cutoffs retain the published release; unmapped releases fail closed).
- Selects by immutable `supersession_ordinal` within `(subject_key, branch_id)` — rejecting cycles,
  forked successors, or ordinal ties (`NON_UNIQUE`) rather than guessing by delivery time.
- Returns `UNKNOWN` only when no publication exists at all for `(subject_key, branch_id)`, and opaque
  `UNRESOLVED` with zero payload disclosure when records exist but none are eligible at `cutoff`.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence


def parse_utc_timestamp(ts: str) -> datetime:
    """Parse an ISO-8601 timestamp string into a timezone-aware UTC datetime."""
    if not isinstance(ts, str) or not ts.strip():
        raise ValueError(f"Expected non-empty ISO-8601 timestamp string, got {ts!r}")
    dt = datetime.fromisoformat(ts.strip().replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError(f"Timestamp must include timezone offset or Z suffix: {ts!r}")
    return dt.astimezone(timezone.utc)


@dataclass(frozen=True)
class AccessGrant:
    role: str
    channel: str
    purpose: str
    valid_from_utc: str
    valid_until_utc: str | None = None
    effect: str = "ALLOW"  # ALLOW | DENY
    recorded_at_utc: str | None = None

    def __post_init__(self) -> None:
        if self.effect not in ("ALLOW", "DENY"):
            raise ValueError(f"AccessGrant.effect must be 'ALLOW' or 'DENY', got {self.effect!r}")


@dataclass(frozen=True)
class DeliveryReceipt:
    publication_id: str
    recipient_role: str
    channel: str
    delivered_at_utc: str


@dataclass(frozen=True)
class ReleaseEvent:
    release_id: str
    status: str  # PUBLISHED | SUPERSEDED | RETRACTED
    published_at_utc: str
    delivered_at_utc: str
    authorized_at_utc: str


@dataclass(frozen=True)
class PublicationRecord:
    publication_id: str
    subject_key: str
    branch_id: str
    release_id: str
    supersession_ordinal: int
    effective_at_utc: str
    recorded_at_utc: str
    published_at_utc: str
    allowed_roles: tuple[str, ...]
    supersedes_publication_id: str | None
    payload: Mapping[str, Any]
    provenance_class: str = "SYNTHETIC"
    effective_end_utc: str | None = None


def _validate_supersession_chain(pubs: Sequence[PublicationRecord]) -> str | None:
    """Return an error tag if the scope's supersession chain has a cycle, fork, or invalid ordinal."""
    by_id: dict[str, PublicationRecord] = {}
    children_of: dict[str, list[str]] = {}
    for p in pubs:
        if p.supersession_ordinal < 0:
            return "INVALID_ORDINAL"
        if p.publication_id in by_id:
            return "NON_UNIQUE"
        by_id[p.publication_id] = p
        if p.supersedes_publication_id is not None:
            children_of.setdefault(p.supersedes_publication_id, []).append(p.publication_id)
            if len(children_of[p.supersedes_publication_id]) > 1:
                return "FORKED_SUCCESSOR"

    # Detect cycles via walk
    for pid in by_id:
        seen: set[str] = set()
        cur: str | None = pid
        while cur is not None:
            if cur in seen:
                return "SUPERSESSION_CYCLE"
            seen.add(cur)
            node = by_id.get(cur)
            if node is None:
                break
            cur = node.supersedes_publication_id
    return None


def _grant_allows(
    grants: Sequence[AccessGrant],
    role: str,
    channel: str,
    purpose: str,
    cutoff: datetime,
) -> bool:
    applicable: list[AccessGrant] = []
    for g in grants:
        if g.effect not in ("ALLOW", "DENY"):
            raise ValueError(f"AccessGrant.effect must be 'ALLOW' or 'DENY', got {g.effect!r}")
        if g.role != role or g.channel != channel or g.purpose != purpose:
            continue
        rec_at = parse_utc_timestamp(g.recorded_at_utc or g.valid_from_utc)
        if rec_at > cutoff:
            continue
        start = parse_utc_timestamp(g.valid_from_utc)
        end = parse_utc_timestamp(g.valid_until_utc) if g.valid_until_utc is not None else None
        if start <= cutoff and (end is None or cutoff < end):
            applicable.append(g)
    if not applicable:
        return False
    if any(g.effect == "DENY" for g in applicable):
        return False
    return any(g.effect == "ALLOW" for g in applicable)


def _release_is_active_at_cutoff(
    release_id: str,
    release_events: Sequence[ReleaseEvent],
    cutoff: datetime,
) -> bool:
    """Return True iff release_id was published/delivered/authorized by cutoff and NOT retracted by cutoff.

    Fail-closed: an unmapped release (no matching PUBLISHED/SUPERSEDED event by cutoff) returns False.
    Per DATA-001 §2 L1/X1, a retraction takes effect ONLY if the retraction event was published,
    delivered, and authorized at or before cutoff; earlier cutoffs retain the published release.
    """
    matching = [e for e in release_events if e.release_id == release_id]
    if not matching:
        return False

    published_ok = any(
        e.status in ("PUBLISHED", "SUPERSEDED")
        and parse_utc_timestamp(e.published_at_utc) <= cutoff
        and parse_utc_timestamp(e.delivered_at_utc) <= cutoff
        and parse_utc_timestamp(e.authorized_at_utc) <= cutoff
        for e in matching
    )
    if not published_ok:
        return False

    retracted_by_cutoff = any(
        e.status == "RETRACTED"
        and parse_utc_timestamp(e.published_at_utc) <= cutoff
        and parse_utc_timestamp(e.delivered_at_utc) <= cutoff
        and parse_utc_timestamp(e.authorized_at_utc) <= cutoff
        for e in matching
    )
    return not retracted_by_cutoff


def select_reader_as_of(
    *,
    subject_key: str,
    branch_id: str,
    reader_role: str,
    reader_cutoff_utc: str,
    publications: Sequence[PublicationRecord],
    release_events: Sequence[ReleaseEvent],
    receipts: Sequence[DeliveryReceipt],
    grants: Sequence[AccessGrant],
    channel: str = "portal",
    purpose: str = "operations",
    event_time_utc: str | None = None,
) -> dict[str, Any]:
    """Select the single authoritative publication visible to (reader_role, channel, purpose, cutoff)."""
    cutoff = parse_utc_timestamp(reader_cutoff_utc)
    event_dt = parse_utc_timestamp(event_time_utc) if event_time_utc is not None else None
    branch_pubs = [p for p in publications if p.subject_key == subject_key and p.branch_id == branch_id]
    if not branch_pubs:
        return {
            "status": "UNKNOWN",
            "subject_key": subject_key,
            "branch_id": branch_id,
            "reader_cutoff_utc": reader_cutoff_utc,
            "publication_id": None,
            "payload": None,
        }

    # Check scope-level supersession chain integrity (reject cycles/forks rather than guessing)
    chain_err = _validate_supersession_chain(branch_pubs)
    if chain_err is not None:
        return {
            "status": "NON_UNIQUE" if chain_err == "NON_UNIQUE" else "REJECTED_CHAIN",
            "reason": chain_err,
            "subject_key": subject_key,
            "branch_id": branch_id,
            "reader_cutoff_utc": reader_cutoff_utc,
            "publication_id": None,
            "payload": None,
        }

    # Check grant eligibility at cutoff (INFO-001 §3)
    if not _grant_allows(grants, reader_role, channel, purpose, cutoff):
        return {
            "status": "UNRESOLVED",
            "subject_key": subject_key,
            "branch_id": branch_id,
            "reader_cutoff_utc": reader_cutoff_utc,
            "publication_id": None,
            "payload": None,
        }

    eligible: list[PublicationRecord] = []
    for p in branch_pubs:
        if reader_role not in p.allowed_roles:
            continue
        rec_dt = parse_utc_timestamp(p.recorded_at_utc)
        pub_dt = parse_utc_timestamp(p.published_at_utc)
        if rec_dt > cutoff or pub_dt > cutoff:
            continue
        has_receipt = any(
            r.publication_id == p.publication_id
            and r.recipient_role == reader_role
            and r.channel == channel
            and pub_dt <= parse_utc_timestamp(r.delivered_at_utc) <= cutoff
            for r in receipts
        )
        if not has_receipt:
            continue
        if not _release_is_active_at_cutoff(p.release_id, release_events, cutoff):
            continue
        if event_dt is not None:
            eff_start = parse_utc_timestamp(p.effective_at_utc)
            eff_end = parse_utc_timestamp(p.effective_end_utc) if p.effective_end_utc is not None else None
            if not (eff_start <= event_dt and (eff_end is None or event_dt < eff_end)):
                continue
        eligible.append(p)

    if not eligible:
        return {
            "status": "UNRESOLVED",
            "subject_key": subject_key,
            "branch_id": branch_id,
            "reader_cutoff_utc": reader_cutoff_utc,
            "publication_id": None,
            "payload": None,
        }

    highest_ordinal = max(p.supersession_ordinal for p in eligible)
    top = [p for p in eligible if p.supersession_ordinal == highest_ordinal]
    if len(top) != 1:
        return {
            "status": "NON_UNIQUE",
            "subject_key": subject_key,
            "branch_id": branch_id,
            "reader_cutoff_utc": reader_cutoff_utc,
            "publication_id": None,
            "payload": None,
        }

    chosen = top[0]
    return {
        "status": "RESOLVED",
        "subject_key": subject_key,
        "branch_id": branch_id,
        "reader_cutoff_utc": reader_cutoff_utc,
        "publication_id": chosen.publication_id,
        "supersession_ordinal": chosen.supersession_ordinal,
        "release_id": chosen.release_id,
        "effective_at_utc": chosen.effective_at_utc,
        "published_at_utc": chosen.published_at_utc,
        "provenance_class": chosen.provenance_class,
        "payload": dict(chosen.payload),
    }
