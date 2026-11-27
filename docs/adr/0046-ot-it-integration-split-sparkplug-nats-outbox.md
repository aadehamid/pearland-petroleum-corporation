---
status: Decided
date: 2026-11-26
amends: ADR-015, ADR-016
source_answers: docs/adr/answers/2026-11-26-first-principles-grill.md#round-2-2026-11-26
---

# ADR-0046: OT/IT integration split with Sparkplug B on OT and outbox plus NATS JetStream on IT

## Context

`ADR-015` and `ADR-016` in `PPC-REG-001` selected Dagster, Apache Kafka, and Debezium CDC for IT integration. `scada_harmonization` standardizes the OT plane on OPC UA (`asyncua`), MQTT with Sparkplug B (`Mosquitto`), and PostgreSQL/TimescaleDB or Parquet L0. Running Kafka and Debezium in Slice 1 adds substantial operational overhead before proving core physical-to-decision coherence.

## Decision

The owner accepted Round 2 Q11 Option 1 via "Yes to the rest." (`docs/adr/answers/2026-11-26-first-principles-grill.md`):

- Accepted option: "Clean OT/IT split with lean IT core — keep OPC UA plus MQTT/Sparkplug B and PostgreSQL/TimescaleDB on the OT plane (aligned with ICE), keep Dagster for orchestration, and use transactional outbox tables in IT source databases plus NATS JetStream for IT event transport in Slice 1; defer Kafka and Debezium to an optional enterprise-scale swap phase."
- Accepted recommendation: "Yes. Adopt option 1 so OT matches scada_harmonization, IT tests real pub/sub replay and outbox/inbox crash recovery with a minimal footprint, and Kafka/Debezium stay cleanly deferred."

## Consequences

- `ADR-015` and `ADR-016` are amended for Slice 1: Dagster orchestrates pipelines, transactional outbox tables capture IT source changes, and NATS JetStream transports IT events; Apache Kafka and Debezium CDC are deferred to an optional enterprise-scale swap phase.
- The OT plane aligns with `scada_harmonization` using OPC UA, MQTT/Sparkplug B, and PostgreSQL/TimescaleDB.
