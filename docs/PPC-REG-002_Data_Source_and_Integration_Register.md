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

  EPA          regulatory    GHGRP facility registry; RFS/RIN    API/file→R2           C           R2 raw

  PHMSA        pipeline      incident history                    file/API→R2           C           R2 raw

  PostgreSQL   workflow      alerts/recommendations/approvals    API/ACID txn          A           PG WAL + R2

  Delta Lake   analytical    Silver/Gold/KPI                     Dagster/delta-rs      B/C/D       R2 Delta snapshots
                                                                                                   (DuckDB read-only)
  ----------------------------------------------------------------------------------------------------------------------

Latency: A seconds, B minutes, C scheduled, D on-demand.

Every productionized interface must add schema/version, semantic
mapping, SLA, retry, failure behavior, DQ and owner.

### WP-1 Public Raw External Interfaces (`generators/public_ingest.py`)

- **Schema/version:** `PPC-WP1-PUBLIC-DATA-VINTAGE` v`1.0.0` (`fixtures/golden/public_data_vintage_manifest.json`), `provenance_class: OBSERVED`.
- **Semantic mapping:** Raw `OBSERVED` external context landed under `raw/external/{eia,noaa,epa,phmsa}/vintage=<date>/` per `PPC-013` and `ADR-0057` (never written to the hidden-truth bucket); conditions fictional distributions without redefining EPM KPIs (`PPC-WORLD-001 §4`).
- **SLA:** On-demand vintage pin per release window (daily/weekly historical series pinned by explicit date range).
- **Retry:** Single 2-second backoff retry on HTTP 429; 60-second request timeout.
- **Failure behavior:** Fail-closed on HTTP 4xx/5xx (with `api_key` redacted), missing/zero/truncated EIA `total`, duplicate EIA periods, filter mismatches (EIA series ID, EPA NAICS `324110`/state), malformed HURDAT2 rows, missing PHMSA `REPORT_NUMBER` data, or R2 ETag-vs-MD5 mismatch.
- **DQ:** Recomputable SHA-256 and MD5/ETag per object and manifest, non-empty rows, unique EIA periods ordered for summary stats, per-record filter/ID conformance (note: EPA Envirofacts `PUB_DIM_FACILITY` returns no server-side total count, so pagination runs to exhaustion with per-record validation), and secret-free manifest verification (`tests/test_public_ingest.py`).
- **Owner:** Refinery Process Modeling & Simulation Engineer (`WP-1` accountable role in `PPC-PLAN-001`).
