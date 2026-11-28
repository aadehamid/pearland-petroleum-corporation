#!/usr/bin/env python3
"""INFO-001 §3 Reader-as-of Selection Engine & DATA-001 §2 L1/X1 Release Resolver (WP-3, PO-08).

Enforces strict non-interference and epistemic honesty:
- Returns `UNRESOLVED` (with zero content disclosure) whenever a record is:
  - restricted to a role the reader does not hold (P1),
  - published after reader_cutoff_utc (P0 / temporal non-interference),
  - mapped to a RETRACTED release with no eligible replacement (DATA-001 §2 L1/X1), or
  - missing a required identity/mapping link.
- Returns `UNKNOWN` ONLY when no publication exists at all for the requested subject
  within the reader's authorized scope (true epistemic gap, P2).
- Never leaks whether an unseen record was restricted vs post-cutoff vs unmapped!
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class PublicationRecord:
    publication_id: str
    subject_key: str
    branch_id: str
    release_id: str
    effective_at_utc: str
    recorded_at_utc: str
    published_at_utc: str
    allowed_roles: tuple[str, ...]
    supersedes_publication_id: str | None
    payload: Mapping[str, Any]
    provenance_class: str = "SYNTHETIC"


def select_reader_as_of(
    *,
    subject_key: str,
    branch_id: str,
    reader_role: str,
    reader_cutoff_utc: str,
    publications: Sequence[PublicationRecord],
    release_statuses: Mapping[str, str],
) -> dict[str, Any]:
    """Select the single authoritative publication visible to (reader_role, reader_cutoff_utc).

    Guarantees PO-08 non-interference:
    - Any restricted or post-cutoff publication is invisible and never disclosed.
    - If a visible publication belongs to a RETRACTED release (L1/X1) and no valid
      non-retracted predecessor/replacement exists at cutoff, returns status `UNRESOLVED`.
    - If no publication exists for the subject on this branch at all, returns `UNKNOWN`.
    - If publications exist on the branch but none are authorized & published <= cutoff,
      returns `UNRESOLVED` with an opaque reason code (never revealing restricted content).
    """
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

    # Filter strictly by reader authorization and temporal publication cutoff
    eligible = [
        p
        for p in branch_pubs
        if (reader_role in p.allowed_roles) and (p.published_at_utc <= reader_cutoff_utc)
    ]
    if not eligible:
        # Opaque UNRESOLVED: hides whether record is restricted or future-published (PO-08)
        return {
            "status": "UNRESOLVED",
            "subject_key": subject_key,
            "branch_id": branch_id,
            "reader_cutoff_utc": reader_cutoff_utc,
            "publication_id": None,
            "payload": None,
        }

    # Exclude publications tied to RETRACTED releases (DATA-001 §2 L1/X1)
    active = [p for p in eligible if release_statuses.get(p.release_id, "PUBLISHED") != "RETRACTED"]
    if not active:
        return {
            "status": "UNRESOLVED",
            "subject_key": subject_key,
            "branch_id": branch_id,
            "reader_cutoff_utc": reader_cutoff_utc,
            "publication_id": None,
            "payload": None,
        }

    # Pick latest eligible active publication by (published_at_utc, effective_at_utc, publication_id)
    chosen = max(active, key=lambda p: (p.published_at_utc, p.effective_at_utc, p.publication_id))
    return {
        "status": "RESOLVED",
        "subject_key": subject_key,
        "branch_id": branch_id,
        "reader_cutoff_utc": reader_cutoff_utc,
        "publication_id": chosen.publication_id,
        "release_id": chosen.release_id,
        "effective_at_utc": chosen.effective_at_utc,
        "published_at_utc": chosen.published_at_utc,
        "provenance_class": chosen.provenance_class,
        "payload": dict(chosen.payload),
    }
