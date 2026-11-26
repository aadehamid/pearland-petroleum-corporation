# PPC-INT-001 — Source Lifecycles and Integration

Inspected PPC baseline: [`01027a84be5d453cbb4e2ea091e4884729918b15`](../registers/PPC-SOURCE-REGISTER.md). This commit is an inspection reference, not owner approval.

| Control | Value |
|---|---|
| ID / status | PPC-INT-001 / proposed draft for owner review |
| Version / date | 0.1.0-draft / 2026-11-25 |
| Authority | [PPC-006](../../PPC-006_Distributed_Source_Systems_and_Data_Architecture.md), [PPC-007](../../PPC-007_Data_Integration_Event_and_Orchestration_Architecture.md), [PPC-REG-002](../../PPC-REG-002_Data_Source_and_Integration_Register.md); ADR-015, 016, 024 |
| Inputs / output | Independent source transactions → durable messages, reconciled extracts and explicit failures |

## 1. Ownership and flow

The canonical world generates coherent fictional causes. Each simulated application owns its recorded lifecycle, native ID and corrections. Integration reads these source records; it cannot query hidden world truth to repair gaps. A physical receipt, LIMS result, CTRM actualization, ERP posting and planning decision are different events with different authorities. Operational reactions and analytical releases have separate completion boundaries. Kafka transport, Debezium CDC and Dagster orchestration are the recorded baseline. NATS JetStream and Python-native capture are proposed alternatives, not adopted replacements.

```text
source commit + outbox intent → transport → inbox receipt → source response
                         ↘ durable raw → reconcile → release manifest
```

## 2. Message and recovery contract

`SourceEvent` has `event_id`, `source_system`, `source_incarnation`, `native_entity_key`, `source_revision`, `event_type`, `schema_version`, `effective_at`, `recorded_at`, `published_at`, `branch_id`, `partition_key`, `source_sequence`, `provenance_class`, `access_label`, recipient `available_at`, immutable payload digest, predecessor and correlation IDs. Source sequence is ordered only within its declared partition. The outbox entry and source transaction commit together. Delivery attempts carry a stable key; a consumer inbox records applied revision and result before acknowledgement. An identical duplicate returns its prior receipt. Same key with different digest is a conflict. Out-of-order revision waits for a predecessor or enters quarantine with a reason; timeout must not invent a missing business event.

For each source keep captured, durable, applied and published watermarks separately. A crash after source commit but before publish resumes the outbox. A crash after consumer apply but before ack reuses the inbox receipt. A partial downstream batch cannot advance the published watermark. `RECEIVED → VALIDATED → APPLIED → PUBLISHED` is a processing lifecycle; `QUARANTINED`, `RETRYING` and `REJECTED` are explicit states. Reconciliation compares source counts, IDs, quantities and revision cutoffs; a mismatch is evidence, not an automatic correction. Authenticated source identity, least-privilege route and branch scope are preconditions.

## 3. Synthetic quality-rejection trace

At 08:00 UTC, one `SYNTHETIC` crude movement of 500 bbl is received physically. At 08:05 a logistics source commits ticket `M1`. LIMS records a `SYNTHETIC` failed assay at 09:00, publishes it at 09:20, and a planner may first read it at 09:30. CTRM holds actualization until it receives the quality disposition. A duplicate delivery of `M1` cannot create another 500 bbl. An ERP invoice that arrives at 11:00 cannot be included in a 10:00 financial release. A corrected LIMS revision published at 12:00 can change a later decision or restatement, but the 10:00 planner replay retains the earlier eligible result. If the assay is restricted to another role, the planner receives no result or disclosure of its contents.

If transport fails after ticket commit, the world retains one physical receipt and the outbox remains pending. Once transport recovers, the same ticket reaches the inbox exactly once in business effect. Analytical rebuilding from raw cannot replay physical receipt. A sibling branch uses its own outbox, inbox and release identifiers. A publisher without authorization for the logistics source or branch is rejected before inbox application; its message is retained as a security event without a business effect.

## 4. Qualification and choices

Acceptance must inject crashes at source commit, outbox publish, inbox apply, acknowledgement and release publication. Check duplicate/conflicting IDs, reordered revisions, stale policy, poison payload, backlog recovery, branch separation, role filtering and quantity reconciliation. Retain source logs, inbox/outbox state, watermarks, expected/observed effects and replay hashes. No runtime result is claimed.

ADR-015 and ADR-016 remain in force. NATS versus Kafka, CDC versus source-native capture, ordering partition, retention and backpressure thresholds require measured comparison and owner disposition. T94–97 and T120–121 in the [discussion register](../registers/PPC-Discussion-Decision-Traceability.md) are the discussion sources; T95–96 were proposals, not deployment evidence.

The [exchange register](../registers/PPC-Discussion-Decision-Traceability.md) routes T33–34, T55, T66–67, T94–97 and T120–121 to this draft. This is topic-level routing; GAP-002 item and original-asset checks remain open.
