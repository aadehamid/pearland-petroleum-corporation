# PPC-INT-001 — Source Lifecycles and Integration

Inspected PPC baseline: [`01027a84be5d453cbb4e2ea091e4884729918b15`](../registers/PPC-SOURCE-REGISTER.md). This commit is the original PPC source-inspection reference, not this draft's content revision or owner approval. Later linked specifications are read at the current branch revision.

| Control | Value |
|---|---|
| ID / status | PPC-INT-001 / proposed draft for owner review |
| Version / date | 0.1.0-draft / 2026-11-25 |
| Authority | [PPC-006](../../PPC-006_Distributed_Source_Systems_and_Data_Architecture.md), [PPC-007](../../PPC-007_Data_Integration_Event_and_Orchestration_Architecture.md), [PPC-REG-002](../../PPC-REG-002_Data_Source_and_Integration_Register.md); ADR-015, 016, 024 |
| Inputs / output | Independent source transactions → durable messages, reconciled extracts and explicit failures |

## 1. Ownership and flow

The canonical world generates coherent fictional causes. Each simulated application owns its recorded lifecycle, native ID and corrections. Integration reads these source records; it cannot query hidden world truth to repair gaps. A physical receipt, LIMS result, CTRM actualization, ERP posting and planning decision are different events with different authorities. Operational reactions and analytical releases have separate completion boundaries. Under [ADR-0046](../../adr/0046-ot-it-integration-split-sparkplug-nats-outbox.md) (amending ADR-015 and ADR-016 for Slice 1), Dagster orchestrates pipelines, transactional outbox tables in IT source databases capture changes, and **NATS JetStream** transports IT events while OPC UA and MQTT/Sparkplug B govern the OT/ICE plane; Apache Kafka and Debezium CDC are deferred to an optional enterprise-scale swap phase. See [PPC-REVIEW-003 §3](../independent-review/PPC-REVIEW-003_System_and_Decision_Register.md#3-paper-end-to-end-boundary-walkthrough-tests) for the full paper boundary walkthroughs of delayed LIMS correction and duplicated crude movement.

```text
source commit + outbox intent → transport → inbox receipt → source response
                         ↘ durable raw → reconcile → release manifest
```

## 2. Message and recovery contract

`SourceEvent` has `publication_id`, subject scope, scoped ordinal, supersedes-publication ID, `event_id`, `source_system`, `source_incarnation`, `native_entity_key`, `source_revision`, `event_type`, `schema_version`, `effective_at`, `recorded_at`, `published_at`, `branch_id`, `partition_key`, `source_sequence`, `provenance_class`, `access_label`, recipient/role-and-channel availability relation from [INFO-001 §3](../03-enterprise-information/PPC-INFO-001_Enterprise_Ontology_Identity_and_Time.md), immutable `payload_ref` and payload digest, `producer_identity`, `delivery_key`, predecessor and correlation IDs. Source sequence is ordered only within its declared partition. The outbox entry and source transaction commit together. Delivery attempts carry a stable key; a consumer inbox records applied revision and result before acknowledgement. `OutboxEntry` binds source transaction ID, event ID, delivery key, payload digest and publish status. `InboxReceipt` binds delivery key, source revision, payload digest, applied result, branch and acknowledged time. An identical duplicate returns its prior receipt. Same key with different digest is a conflict. Out-of-order revision waits for a predecessor or enters quarantine with a reason; timeout must not invent a missing business event.

For each source keep captured, durable, applied and published watermarks separately. A crash after source commit but before publish resumes the outbox. A crash after consumer apply but before ack reuses the inbox receipt. A partial downstream batch cannot advance the published watermark. Processing transitions are `RECEIVED → VALIDATED|QUARANTINED|REJECTED`, `VALIDATED → APPLIED|QUARANTINED|REJECTED`, `QUARANTINED → RETRYING|REJECTED`, `RETRYING → VALIDATED|QUARANTINED|REJECTED`, and `APPLIED → PUBLISHED`. `PUBLISHED` and `REJECTED` are terminal for that delivery key. An applied effect cannot be rejected or reapplied; a correction needs a new source revision and delivery key. Reconciliation compares source counts, IDs, quantities and revision cutoffs; a mismatch is evidence, not an automatic correction. Authenticated source identity, least-privilege route and branch scope are preconditions.

## 3. Synthetic quality-rejection trace

At 08:00 UTC, one `SYNTHETIC` crude movement of 500 bbl is received physically. At 08:05 a logistics source commits ticket `M1`. LIMS records a `SYNTHETIC` failed assay at 09:00, publishes it at 09:20, and a planner may first read it at 09:30. CTRM holds actualization until it receives the quality disposition. A duplicate delivery of `M1` cannot create another 500 bbl. An ERP invoice that arrives at 11:00 cannot be included in a 10:00 financial release. A corrected LIMS revision published at 12:00 can change a later decision or restatement, but the 10:00 planner replay retains the earlier eligible result. If the assay is restricted to another role, the planner receives no result or disclosure of its contents.

If transport fails after ticket commit, the world retains one physical receipt and the outbox remains pending. Once transport recovers, the same ticket reaches the inbox exactly once in business effect. Analytical rebuilding from raw cannot replay physical receipt. A sibling branch uses its own outbox, inbox and release identifiers. A publisher without authorization for the logistics source or branch is rejected before inbox application; its message is retained as a security event without a business effect.

## 4. Qualification and choices

Acceptance must inject crashes at source commit, outbox publish, inbox apply, acknowledgement and release publication. Check duplicate/conflicting IDs, reordered revisions, stale policy, poison payload, backlog recovery, branch separation, role filtering and quantity reconciliation. Retain source logs, inbox/outbox state, watermarks, expected/observed effects and replay hashes. No runtime result is claimed.

[ADR-0046](../../adr/0046-ot-it-integration-split-sparkplug-nats-outbox.md) amends ADR-015 and ADR-016 for Slice 1 to lock Dagster orchestration, transactional source outboxes, and NATS JetStream on IT (deferring Kafka and Debezium to an optional later swap) alongside Sparkplug B on OT. Ordering partition keys, JetStream retention limits, and backpressure thresholds require WP-2/WP-4 benchmark evidence before runtime qualification. T94–97 and T120–121 in the [discussion register](../registers/PPC-Discussion-Decision-Traceability.md) are the discussion sources.

The [exchange register](../registers/PPC-Discussion-Decision-Traceability.md) routes T33–34, T55, T66–67, T94–97, T120–121 to this draft. `GAP-002` Markdown audit is closed in [PPC-REVIEW-001 §5](../independent-review/PPC-REVIEW-001_Document_Coverage_and_Transcript_Audit.md#5-audit-of-raw-chatgpt-transcript-t1t145-versus-ef4eb08-ppc-documents-closing-gap-002).
