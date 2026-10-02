# PPC-002 --- Enterprise Architecture and Technology Stack

**Purpose:** Define the complete stack, responsibilities, ownership
boundaries, and major interactions.

## Documentation standard

PPC uses an **ASD-STE100-inspired** technical writing style. PPC does
not claim formal ASD-STE100 compliance. Use consistent terms, direct
verbs, short sections, explicit relationships, and established technical
vocabulary when it improves precision.

## Governing principles

-   Business meaning is independent of software products.
-   Public observations and synthetic PPC facts are always
    distinguishable.
-   Each operational object has an authoritative source for its
    lifecycle stage.
-   The canonical synthetic PPC world exists before heterogeneous
    source-system materialization.
-   Data products expose reusable governed information. BI tools do not
    own KPI logic.
-   Formal semantics and operational graph traversal are separate
    responsibilities.
-   Specialized models calculate forecasts, causal effects, uncertainty,
    and optimized actions. LLMs orchestrate and explain.
-   Material actions remain subject to explicit policy and human
    approval.

## Technology map

  ----------------------------------------------------------------------------------
  Area                    Choice                     Primary role
  ----------------------- -------------------------- -------------------------------
  CRM                     Twenty open-source         accounts, contacts,
                          components                 opportunities

  ERP                     ERPNext                    O2C, invoices, AR/AP,
                                                     procurement, finance

  Commercial              PostgreSQL                 contracts, trades, positions,
                                                     hedges

  Logistics               MySQL                      nominations, shipments,
                                                     deliveries

  Refinery edge           SQLite                     unit state, production,
                                                     operator events

  External                EIA/NOAA/EPA/PHMSA         observed external world

  Object store            Cloudflare R2              raw evidence, extracts,
                                                     canonical world,
                                                     artifacts/replay

  Workflow                Cloudflare D1              alerts, recommendations,
                                                     approvals

  API/edge                Workers                    ingestion and operational APIs

  Modeling                AML + Azimutt              model-as-code and visual
                                                     modeling

  Orchestration           Dagster                    assets, schedules, sensors,
                                                     backfills

  CDC                     Debezium                   Postgres/MySQL changes

  Events                  Apache Kafka               event transport/replay

  Compute                 DuckDB                     federation, profiling,
                                                     transforms, simulation

  Lakehouse               DuckLake                   Silver/Gold/data products/KPI
                                                     Store

  Enterprise lab          Databricks Free            enterprise-style lakehouse/ML
                                                     comparison

  Catalog                 OpenMetadata               discovery, ownership, glossary,
                                                     lineage, products

  DQ                      Great Expectations         explicit quality rules

  Run lineage             OpenLineage                job/run/dataset events

  Formal semantics        Jena/Fuseki                RDF/RDFS/OWL/SHACL/SPARQL

  Operational graph       Neo4j Community            current context and traversal

  BI                      Superset                   governed analytical consumption

  Decision UX             Plotly Dash                events, scenarios,
                                                     recommendations, approvals

  Monitoring              Grafana OSS                technical health

  ML lifecycle            MLflow                     experiments/models/evaluation

  Forecasting             StatsForecast/MLForecast   forecasts

  Causal                  DoWhy/EconML               causal estimation

  Probabilistic           PyMC                       uncertainty

  Optimization            OR-Tools                   constrained actions

  Vector                  PostgreSQL + pgvector      documents/cases

  Local LLM               Ollama                     local inference

  Agent                   LangGraph                  controlled stateful workflow

  Agent telemetry         Langfuse                   traces/evaluation
  ----------------------------------------------------------------------------------

## Boundary examples

Superset consumes official KPI logic; it does not define it. Jena
defines formal meaning; Neo4j holds operational instances/state.
OpenMetadata catalogs and governs implementations; it does not
independently redefine business semantics. Dagster orchestrates; Kafka
transports events. R2 is durable object storage; it is not the universal
transactional system of record.

## Cross-system O2C example

Twenty Account → PostgreSQL commercial contract → ERPNext sales order →
MySQL shipment/delivery → ERPNext invoice/payment → DuckLake conformed
O2C history → KPI Store OTIF/DSO/margin.

## Dual analytical implementation

DuckDB/DuckLake is the open reference implementation. Databricks Free is
the enterprise-like comparison. The same semantic and data-product
contracts should map to both.
