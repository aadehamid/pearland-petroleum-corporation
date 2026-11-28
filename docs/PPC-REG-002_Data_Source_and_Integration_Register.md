# PPC-REG-002 --- Data Source and Integration Register

**Purpose:** Living inventory of sources, ownership, integration
patterns and latency.

**Reconciliation note (2026-11-28, ADR-0045, ADR-0046, ADR-0055, ADR-0060 Q2):**
Retained and reconciled in place without superseding the baseline register
(`PPC-ARCH-000`). Slice 1 replaces Debezium/Kafka with transactional source
outboxes and NATS JetStream (`ADR-0046`; Kafka/Debezium deferred to an optional
later swap), replaces Cloudflare D1 with PostgreSQL workflow state (`ADR-0055`),
and replaces DuckLake with Delta Lake on Cloudflare R2 (`ADR-0045`, single-writer
`delta-rs` via Dagster and read-only DuckDB).

  ----------------------------------------------------------------------------------------------------------------------
  Source       Authority     Main objects                        Integration           Latency     Durable replay
  ------------ ------------- ----------------------------------- --------------------- ----------- ---------------------
  Twenty       CRM lifecycle accounts/contacts/opportunities     API                   C/B         R2 extracts

  ERPNext      finance/O2C   orders/invoices/AR/AP/payments      API                   C/B         R2 extracts

  PostgreSQL   commercial    contracts/trades/positions/hedges   Outbox→NATS           A           NATS + R2 raw

  MySQL        logistics     nominations/shipments/deliveries    Outbox→NATS           A           NATS + R2 raw

  SQLite       refinery edge unit status/production/events       micro-batch→R2        B           R2

  EIA          public        prices/stocks/runs/trade            Worker/API→R2         C           R2 raw
               petroleum                                                                           

  NOAA/NHC     weather       advisories/tracks                   Worker/API→R2/event   B           R2 raw

  EPA          regulatory    GHGRP Subpart Y; RFS/RIN context    API/file→R2           C           R2 raw

  PHMSA        pipeline      incident history                    file/API→R2           C           R2 raw

  PostgreSQL   workflow      alerts/recommendations/approvals    API/ACID txn          A           PG WAL + R2

  Delta Lake   analytical    Silver/Gold/KPI                     Dagster/delta-rs      B/C/D       R2 Delta snapshots
                                                                                                   (DuckDB read-only)
  ----------------------------------------------------------------------------------------------------------------------

Latency: A seconds, B minutes, C scheduled, D on-demand.

Every productionized interface must add schema/version, semantic
mapping, SLA, retry, failure behavior, DQ and owner.
