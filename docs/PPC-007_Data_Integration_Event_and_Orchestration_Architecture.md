# PPC-007 --- Data Integration, Event, and Orchestration Architecture

**Purpose:** Define how PPC systems exchange data and events.

PPC uses an **ASD-STE100-inspired** technical writing style. PPC does
not claim formal ASD-STE100 compliance. Terms keep one defined meaning
across the documentation.

## Pattern choices

Dagster orchestrates. Debezium captures Postgres/MySQL changes. Kafka
transports/replays events. Workers integrate public APIs and expose
operational APIs. R2 is durable landing/replay. DuckDB
federates/transforms. OpenLineage publishes run lineage.

## Integration patterns

-   **CDC:** Postgres/MySQL → Debezium → Kafka.
-   **Application API:** Twenty and ERPNext APIs.
-   **Public API:** Workers → raw R2 → processing/event classification.
-   **Micro-batch:** SQLite periodic extract → R2 → DuckDB/DuckLake.
-   **Analytical federation:** DuckDB across source/extract/lakehouse.
-   **Event-driven:** Kafka → Neo4j/Performance Intelligence/automation.

## Latency classes

A: seconds, event/CDC.\
B: minutes, near-real-time extracts/advisories.\
C: scheduled hourly/daily/weekly.\
D: on-demand analysis/backfill/scenario.

## Event topics

Examples: `ppc.commercial.trade.changed`,
`ppc.logistics.shipment.changed`, `ppc.refinery.unit.event`,
`ppc.weather.event`, `ppc.data.quality.event`,
`ppc.performance.kpi.changed`, `ppc.automation.recommendation.created`.

## Integration contract

Every interface records source, target, pattern, owner, schema, semantic
mapping, latency class/SLA, retry, replay, DQ, lineage, security and
failure behavior.

## Example

MySQL shipment becomes DELAYED → Debezium → Kafka → Neo4j state update →
exposure traversal → margin/OTIF risk model → policy → D1 recommendation
→ Dash approval UX.

## Recovery

Raw snapshots and durable extracts live in R2. Failed downstream
transformations can replay from R2. CDC event archives can also be
persisted to R2 beyond Kafka retention.
