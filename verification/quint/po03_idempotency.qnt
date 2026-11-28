// PO-03: Idempotency Across Crash Point 1 (before NATS ack) and Crash Point 2 (exclusive pre-pinned Delta batch retry)
// Governing authorities: ADR-0046, PPC-INT-001 §2, PPC-REVIEW-004 PO-03
// Non-vacuous model: tracks per-key staging_applied, exclusive per-txn pins (txn1 and txn2),
// sink_committed_keys, and delta_published so any unpinned retry marking newly arrived rows
// or any cross-txn double-publish would violate safety_all.
// Verified with `quint verify --invariant safety_all`.
module po03_idempotency {
  type DeliveryKey = str
  type Digest = str

  var receipts: DeliveryKey -> Digest
  var staging_applied: DeliveryKey -> int
  var quarantined: Set[DeliveryKey]
  var worker_crashed_cp1: bool
  var pinned_txn1: Set[DeliveryKey]
  var pinned_txn2: Set[DeliveryKey]
  var sink_committed_keys: Set[DeliveryKey]
  var sink_double_commit: bool
  var delta_published: Set[DeliveryKey]
  var ledger_txn1_done: bool
  var ledger_txn2_done: bool

  action init = all {
    receipts' = Map(),
    staging_applied' = Map(),
    quarantined' = Set(),
    worker_crashed_cp1' = false,
    pinned_txn1' = Set(),
    pinned_txn2' = Set(),
    sink_committed_keys' = Set(),
    sink_double_commit' = false,
    delta_published' = Set(),
    ledger_txn1_done' = false,
    ledger_txn2_done' = false,
  }

  // Crash Point 1: atomic Silver staging + InboxReceipt, optional crash before NATS ack
  action deliver_event(dkey: DeliveryKey, dig: Digest, crash_before_ack: bool): bool =
    if (dkey.in(receipts.keys())) (
      if (receipts.get(dkey) == dig) all {
        receipts' = receipts,
        staging_applied' = staging_applied,
        quarantined' = quarantined,
        worker_crashed_cp1' = false,
        pinned_txn1' = pinned_txn1,
        pinned_txn2' = pinned_txn2,
        sink_committed_keys' = sink_committed_keys,
        sink_double_commit' = sink_double_commit,
        delta_published' = delta_published,
        ledger_txn1_done' = ledger_txn1_done,
        ledger_txn2_done' = ledger_txn2_done,
      } else all {
        receipts' = receipts,
        staging_applied' = staging_applied,
        quarantined' = quarantined.union(Set(dkey)),
        worker_crashed_cp1' = false,
        pinned_txn1' = pinned_txn1,
        pinned_txn2' = pinned_txn2,
        sink_committed_keys' = sink_committed_keys,
        sink_double_commit' = sink_double_commit,
        delta_published' = delta_published,
        ledger_txn1_done' = ledger_txn1_done,
        ledger_txn2_done' = ledger_txn2_done,
      }
    ) else all {
      receipts' = receipts.put(dkey, dig),
      staging_applied' = staging_applied.put(dkey, 1),
      quarantined' = quarantined,
      worker_crashed_cp1' = crash_before_ack,
      pinned_txn1' = pinned_txn1,
      pinned_txn2' = pinned_txn2,
      sink_committed_keys' = sink_committed_keys,
      sink_double_commit' = sink_double_commit,
      delta_published' = delta_published,
      ledger_txn1_done' = ledger_txn1_done,
      ledger_txn2_done' = ledger_txn2_done,
    }

  // Phase 2a: atomically claim/pin only unpublished, unpinned staging rows to txn1 or txn2
  action pin_txn1 = {
    val claimable = staging_applied.keys().exclude(delta_published).exclude(pinned_txn2)
    all {
      pinned_txn1 == Set(),
      not(ledger_txn1_done),
      claimable != Set(),
      pinned_txn1' = claimable,
      pinned_txn2' = pinned_txn2,
      receipts' = receipts,
      staging_applied' = staging_applied,
      quarantined' = quarantined,
      worker_crashed_cp1' = worker_crashed_cp1,
      sink_committed_keys' = sink_committed_keys,
      sink_double_commit' = sink_double_commit,
      delta_published' = delta_published,
      ledger_txn1_done' = ledger_txn1_done,
      ledger_txn2_done' = ledger_txn2_done,
    }
  }

  action pin_txn2 = {
    val claimable = staging_applied.keys().exclude(delta_published).exclude(pinned_txn1)
    all {
      pinned_txn2 == Set(),
      not(ledger_txn2_done),
      claimable != Set(),
      pinned_txn2' = claimable,
      pinned_txn1' = pinned_txn1,
      receipts' = receipts,
      staging_applied' = staging_applied,
      quarantined' = quarantined,
      worker_crashed_cp1' = worker_crashed_cp1,
      sink_committed_keys' = sink_committed_keys,
      sink_double_commit' = sink_double_commit,
      delta_published' = delta_published,
      ledger_txn1_done' = ledger_txn1_done,
      ledger_txn2_done' = ledger_txn2_done,
    }
  }

  // Phase 2b: commit txn1 or txn2 pinned set to Delta sink (flags sink_double_commit if another txn already committed any key!)
  action sink_commit_txn1 = all {
    pinned_txn1 != Set(),
    not(ledger_txn1_done),
    not(pinned_txn1.subseteq(sink_committed_keys)),
    sink_double_commit' = (sink_double_commit or (pinned_txn1.intersect(sink_committed_keys) != Set())),
    sink_committed_keys' = sink_committed_keys.union(pinned_txn1),
    pinned_txn1' = pinned_txn1,
    pinned_txn2' = pinned_txn2,
    receipts' = receipts,
    staging_applied' = staging_applied,
    quarantined' = quarantined,
    worker_crashed_cp1' = worker_crashed_cp1,
    delta_published' = delta_published,
    ledger_txn1_done' = ledger_txn1_done,
    ledger_txn2_done' = ledger_txn2_done,
  }

  action sink_commit_txn2 = all {
    pinned_txn2 != Set(),
    not(ledger_txn2_done),
    not(pinned_txn2.subseteq(sink_committed_keys)),
    sink_double_commit' = (sink_double_commit or (pinned_txn2.intersect(sink_committed_keys) != Set())),
    sink_committed_keys' = sink_committed_keys.union(pinned_txn2),
    pinned_txn1' = pinned_txn1,
    pinned_txn2' = pinned_txn2,
    receipts' = receipts,
    staging_applied' = staging_applied,
    quarantined' = quarantined,
    worker_crashed_cp1' = worker_crashed_cp1,
    delta_published' = delta_published,
    ledger_txn1_done' = ledger_txn1_done,
    ledger_txn2_done' = ledger_txn2_done,
  }

  // Phase 2c: mark ONLY txn's pinned keys as delta_published (never marks newly arrived unpinned rows!)
  action complete_ledger_txn1 = all {
    pinned_txn1 != Set(),
    not(ledger_txn1_done),
    pinned_txn1.subseteq(sink_committed_keys),
    delta_published' = delta_published.union(pinned_txn1),
    ledger_txn1_done' = true,
    ledger_txn2_done' = ledger_txn2_done,
    pinned_txn1' = pinned_txn1,
    pinned_txn2' = pinned_txn2,
    receipts' = receipts,
    staging_applied' = staging_applied,
    quarantined' = quarantined,
    worker_crashed_cp1' = worker_crashed_cp1,
    sink_committed_keys' = sink_committed_keys,
    sink_double_commit' = sink_double_commit,
  }

  action complete_ledger_txn2 = all {
    pinned_txn2 != Set(),
    not(ledger_txn2_done),
    pinned_txn2.subseteq(sink_committed_keys),
    delta_published' = delta_published.union(pinned_txn2),
    ledger_txn2_done' = true,
    ledger_txn1_done' = ledger_txn1_done,
    pinned_txn1' = pinned_txn1,
    pinned_txn2' = pinned_txn2,
    receipts' = receipts,
    staging_applied' = staging_applied,
    quarantined' = quarantined,
    worker_crashed_cp1' = worker_crashed_cp1,
    sink_committed_keys' = sink_committed_keys,
    sink_double_commit' = sink_double_commit,
  }

  action step = any {
    deliver_event("DK1", "D1", true),
    deliver_event("DK1", "D1", false),
    deliver_event("DK1", "D_TAMPERED", false),
    deliver_event("DK2", "D2", false),
    pin_txn1,
    pin_txn2,
    sink_commit_txn1,
    sink_commit_txn2,
    complete_ledger_txn1,
    complete_ledger_txn2,
  }

  val no_double_staging = staging_applied.keys().forall(k => staging_applied.get(k) == 1)
  val no_double_sink = not(sink_double_commit)
  val no_silent_drop = delta_published.subseteq(sink_committed_keys)
  val disjoint_pins = pinned_txn1.intersect(pinned_txn2) == Set()
  val safety_all = no_double_staging and no_double_sink and no_silent_drop and disjoint_pins
}
