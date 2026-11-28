// Abstract Quint model of PO-08 temporal, receipt, grant, and cutoff-scoped retraction non-interference.
// Companion specification to lakehouse/delta/reader_as_of.py (PPC-REVIEW-004 PO-08 stays planned until
// model-to-implementation conformance runs in CI).
module po08_noninterference {
  type Pub = {
    id: str,
    ordinal: int,
    recorded_at: int,
    published_at: int,
    receipt_at: int,
    retracted_at: int, // -1 means not retracted
    restricted: bool,
    payload: int
  }

  var world_a: Set[Pub]
  var world_b: Set[Pub]
  var reader_cutoff: int
  var reader_has_grant: bool

  // Record-level visibility independent of dynamic grant toggles
  pure def record_eligible_at_cutoff(p: Pub, cutoff: int): bool =
    (not(p.restricted))
      and (p.recorded_at <= cutoff)
      and (p.published_at <= cutoff)
      and (p.receipt_at >= p.published_at)
      and (p.receipt_at <= cutoff)
      and (p.retracted_at == -1 or p.retracted_at > cutoff)

  pure def is_visible(p: Pub, cutoff: int, has_grant: bool): bool =
    has_grant and record_eligible_at_cutoff(p, cutoff)

  pure def visible_projection(w: Set[Pub], cutoff: int, has_grant: bool): Set[Pub] =
    w.filter(p => is_visible(p, cutoff, has_grant))

  action init = all {
    reader_cutoff' = 100,
    reader_has_grant' = true,
    world_a' = Set(
      { id: "P1", ordinal: 0, recorded_at: 80, published_at: 85, receipt_at: 90, retracted_at: 115, restricted: false, payload: 10 },
      { id: "P_FUTURE", ordinal: 1, recorded_at: 80, published_at: 120, receipt_at: 125, retracted_at: -1, restricted: false, payload: 111 },
      { id: "P_RETRACTED", ordinal: 2, recorded_at: 70, published_at: 75, receipt_at: 80, retracted_at: 95, restricted: false, payload: 333 },
      { id: "P_SECRET", ordinal: 3, recorded_at: 80, published_at: 85, receipt_at: 90, retracted_at: -1, restricted: true, payload: 999 }
    ),
    world_b' = Set(
      { id: "P1", ordinal: 0, recorded_at: 80, published_at: 85, receipt_at: 90, retracted_at: 115, restricted: false, payload: 10 },
      { id: "P_FUTURE", ordinal: 1, recorded_at: 80, published_at: 120, receipt_at: 125, retracted_at: -1, restricted: false, payload: 222 },
      { id: "P_RETRACTED", ordinal: 2, recorded_at: 70, published_at: 75, receipt_at: 80, retracted_at: 95, restricted: false, payload: 444 },
      { id: "P_SECRET", ordinal: 3, recorded_at: 80, published_at: 85, receipt_at: 90, retracted_at: -1, restricted: true, payload: 888 }
    )
  }

  // Mutate only records permanently ineligible at reader_cutoff (future, unreceipted, retracted, or restricted)
  action mutate_ineligible_in_b = all {
    reader_cutoff' = reader_cutoff,
    reader_has_grant' = reader_has_grant,
    world_a' = world_a,
    world_b' = world_b.map(p =>
      if (not(record_eligible_at_cutoff(p, reader_cutoff))) { ...p, payload: p.payload + 1 } else p
    )
  }

  action toggle_grant = all {
    reader_cutoff' = reader_cutoff,
    reader_has_grant' = not(reader_has_grant),
    world_a' = world_a,
    world_b' = world_b
  }

  action step = any {
    mutate_ineligible_in_b,
    toggle_grant
  }

  // PO-08 invariant: ineligible (future, restricted, unreceipted, or cutoff-retracted) mutations never alter reader view
  val non_interference =
    visible_projection(world_a, reader_cutoff, reader_has_grant)
      == visible_projection(world_b, reader_cutoff, reader_has_grant)
}
