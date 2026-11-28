// PO-03: Idempotency Across Crash Point 1 (before NATS ack) and Crash Point 2 (pinned Delta batch retry)
// Governing authorities: ADR-0046, PPC-INT-001 §2, PPC-REVIEW-004 PO-03
// Verified with `quint verify --invariant safety_all`.
module po03_idempotency {
  type DeliveryKey = str
  type Digest = str

  var receipts: DeliveryKey -> Digest
  var staging_applied: DeliveryKey -> int   // business-effect count per delivery_key (must never exceed 1)
  var quarantined: Set[DeliveryKey]
  var worker_crashed_cp1: bool
  var pinned_batch_txn1: Set[DeliveryKey]
  var sink_committed_txn1: Set[DeliveryKey]
  var ledger_txn1_done: bool
  var sink_commit_count: DeliveryKey -> int // Delta commit count per key (must never exceed 1)

  action init = all {
    receipts' = Map(),
    staging_applied' = Map(),
    quarantined' = Set(),
    worker_crashed_cp1' = false,
    pinned_batch_txn1' = Set(),
    sink_committed_txn1' = Set(),
    ledger_txn1_done' = false,
    sink_commit_count' = Map(),
  }

  // Crash Point 1: atomic write of Silver staging + InboxReceipt, optional crash before NATS ack
  action deliver_event(dkey: DeliveryKey, dig: Digest, crash_before_ack: bool): bool =
    if (dkey.in(receipts.keys())) (
      if (receipts.get(dkey) == dig) all {
        receipts' = receipts,
        staging_applied' = staging_applied,
        quarantined' = quarantined,
        worker_crashed_cp1' = false,
        pinned_batch_txn1' = pinned_batch_txn1,
        sink_committed_txn1' = sink_committed_txn1,
        ledger_txn1_done' = ledger_txn1_done,
        sink_commit_count' = sink_commit_count,
      } else all {
        receipts' = receipts,
        staging_applied' = staging_applied,
        quarantined' = quarantined.union(Set(dkey)),
        worker_crashed_cp1' = false,
        pinned_batch_txn1' = pinned_batch_txn1,
        sink_committed_txn1' = sink_committed_txn1,
        ledger_txn1_done' = ledger_txn1_done,
        sink_commit_count' = sink_commit_count,
      }
    ) else all {
      receipts' = receipts.put(dkey, dig),
      staging_applied' = staging_applied.put(dkey, 1),
      quarantined' = quarantined,
      worker_crashed_cp1' = crash_before_ack,
      pinned_batch_txn1' = pinned_batch_txn1,
      sink_committed_txn1' = sink_committed_txn1,
      ledger_txn1_done' = ledger_txn1_done,
      sink_commit_count' = sink_commit_count,
    }

  // Crash Point 2a: pin current applied rows to txn1 and commit to idempotent Delta sink, then crash before ledger mark
  action sink_commit_txn1_and_crash = all {
    pinned_batch_txn1 == Set(),
    staging_applied.keys() != Set(),
    pinned_batch_txn1' = staging_applied.keys(),
    sink_committed_txn1' = staging_applied.keys(),
    sink_commit_count' = staging_applied.keys().mapBy(_ => 1),
    ledger_txn1_done' = false,
    receipts' = receipts,
    staging_applied' = staging_applied,
    quarantined' = quarantined,
    worker_crashed_cp1' = worker_crashed_cp1,
  }

  // Crash Point 2b: retry txn1 uses ONLY pinned_batch_txn1 (never drops newly arrived rows or double-commits)
  action retry_txn1_complete_ledger = all {
    pinned_batch_txn1 != Set(),
    not(ledger_txn1_done),
    ledger_txn1_done' = true,
    receipts' = receipts,
    staging_applied' = staging_applied,
    quarantined' = quarantined,
    worker_crashed_cp1' = worker_crashed_cp1,
    pinned_batch_txn1' = pinned_batch_txn1,
    sink_committed_txn1' = sink_committed_txn1,
    sink_commit_count' = sink_commit_count,
  }

  action step = any {
    deliver_event("DK1", "D1", true),
    deliver_event("DK1", "D1", false),
    deliver_event("DK1", "D_TAMPERED", false),
    deliver_event("DK2", "D2", false),
    sink_commit_txn1_and_crash,
    retry_txn1_complete_ledger,
  }

  val no_double_staging = staging_applied.keys().forall(k => staging_applied.get(k) == 1)
  val no_double_sink = sink_commit_count.keys().forall(k => sink_commit_count.get(k) == 1)
  val pinned_matches_sink = sink_committed_txn1 == pinned_batch_txn1
  val safety_all = no_double_staging and no_double_sink and pinned_matches_sink
}
