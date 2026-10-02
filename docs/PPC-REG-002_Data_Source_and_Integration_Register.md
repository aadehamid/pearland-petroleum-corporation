# PPC-REG-002 --- Data Source and Integration Register

**Purpose:** Living inventory of sources, ownership, integration
patterns and latency.

  ----------------------------------------------------------------------------------------------------------------------
  Source       Authority     Main objects                        Integration           Latency     Durable replay
  ------------ ------------- ----------------------------------- --------------------- ----------- ---------------------
  Twenty       CRM lifecycle accounts/contacts/opportunities     API                   C/B         R2 extracts

  ERPNext      finance/O2C   orders/invoices/AR/AP/payments      API                   C/B         R2 extracts

  PostgreSQL   commercial    contracts/trades/positions/hedges   Debezium→Kafka        A           Kafka + R2 CDC

  MySQL        logistics     nominations/shipments/deliveries    Debezium→Kafka        A           Kafka + R2 CDC

  SQLite       refinery edge unit status/production/events       micro-batch→R2        B           R2

  EIA          public        prices/stocks/runs/trade            Worker/API→R2         C           R2 raw
               petroleum                                                                           

  NOAA/NHC     weather       advisories/tracks                   Worker/API→R2/event   B           R2 raw

  EPA          regulatory    RFS/RIN context                     API/file→R2           C           R2 raw

  PHMSA        pipeline      incident history                    file/API→R2           C           R2 raw

  D1           workflow      alerts/recommendations/approvals    API/event             A           extracts as needed

  DuckLake     analytical    Silver/Gold/KPI                     Dagster/DuckDB        B/C/D       R2-backed
                                                                                                   artifacts/snapshots
  ----------------------------------------------------------------------------------------------------------------------

Latency: A seconds, B minutes, C scheduled, D on-demand.

Every productionized interface must add schema/version, semantic
mapping, SLA, retry, failure behavior, DQ and owner.
