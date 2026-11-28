// PO-03: Idempotency across Crash Point 1 (before NATS ack) and Crash Point 2 (before staging watermark mark)
// Governing authorities: ADR-0046, PPC-INT-001 §2, PPC-REVIEW-004 PO-03
module po03_idempotency {
  type EventId = str
  type Digest = str

  var outbox: Set[(EventId, Digest)]
  var inbox_receipts: EventId -> Digest
  var silver_staging: Set[EventId]
  var conflict_quarantine: Set[EventId]
  var delta_published: Set[EventId]
  var delta_txn_versions: Set[int]
  var business_effect_count: EventId -> int

  action init = all {
    outbox' = Set(("M1", "D1")),
    inbox_receipts' = Map(),
    silver_staging' = Set(),
    conflict_quarantine' = Set(),
    delta_published' = Set(),
    delta_txn_versions' = Set(),
    business_effect_count' = Map("M1" -> 0),
  }

  // Atomic commit of Silver staging + InboxReceipt; even if worker crashes before NATS ack,
  // redelivery sees existing receipt with same digest and performs zero duplicate business effect.
  action deliver_event(ev: EventId, dig: Digest) = {
    if (ev.in(inbox_receipts.keys())) {
      if (inbox_receipts.get(ev) == dig) {
        all {
          outbox' = outbox,
          inbox_receipts' = inbox_receipts,
          silver_staging' = silver_staging,
          conflict_quarantine' = conflict_quarantine,
          delta_published' = delta_published,
          delta_txn_versions' = delta_txn_versions,
          business_effect_count' = business_effect_count,
        }
      } else {
        all {
          outbox' = outbox,
          inbox_receipts' = inbox_receipts,
          silver_staging' = silver_staging,
          conflict_quarantine' = conflict_quarantine.union(Set(ev)),
          delta_published' = delta_published,
          delta_txn_versions' = delta_txn_versions,
          business_effect_count' = business_effect_count,
        }
      }
    } else {
      all {
        outbox' = outbox,
        inbox_receipts' = inbox_receipts.put(ev, dig),
        silver_staging' = silver_staging.union(Set(ev)),
        conflict_quarantine' = conflict_quarantine,
        delta_published' = delta_published,
        delta_txn_versions' = delta_txn_versions,
        business_effect_count' = business_effect_count.put(ev, business_effect_count.get(ev) + 1),
      }
    }
  }

  // Crash Point 2: delta-rs txnAppId/txnVersion guarantees idempotent Delta publish
  action publish_to_delta(txn_ver: int, ev: EventId) = all {
    ev.in(silver_staging),
    if (txn_ver.in(delta_txn_versions)) {
      all {
        delta_published' = delta_published,
        delta_txn_versions' = delta_txn_versions,
      }
    } else {
      all {
        delta_published' = delta_published.union(Set(ev)),
        delta_txn_versions' = delta_txn_versions.union(Set(txn_ver)),
      }
    },
    outbox' = outbox,
    inbox_receipts' = inbox_receipts,
    silver_staging' = silver_staging,
    conflict_quarantine' = conflict_quarantine,
    business_effect_count' = business_effect_count,
  }

  action step = any {
    deliver_event("M1", "D1"),
    deliver_event("M1", "D_CONFLICT"),
    publish_to_delta(1, "M1"),
  }

  // Invariant: No delivery key ever produces more than one business effect across retries/crashes
  val no_duplicate_business_effect = business_effect_count.get("M1") <= 1
  val delta_subset_of_staging = delta_published.subseteq(silver_staging)
}
