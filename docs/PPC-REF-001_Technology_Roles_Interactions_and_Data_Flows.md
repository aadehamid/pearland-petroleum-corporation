# PPC-REF-001 --- Technology Roles, Interactions, and Data Flows

**Purpose:** Practical guide to what each technology does, why PPC uses
it, what informs it, and what it informs.

## How to read this guide

For each component, ask four questions: **What does it own/do? What does
it receive? What does it produce? What must it not become?**

## Twenty

**Role:** CRM. Owns account/contact/opportunity relationship lifecycle.\
**Receives:** synthetic PPC customer/opportunity materialization.\
**Informs:** commercial relationship context, ERP/commercial identity
matching, customer analytics.\
**Does not own:** shipment, invoice, trade or enterprise Customer
meaning.\
**Example:** Account `ACC-481` maps to enterprise Customer
`PPC-CUST-001`.

## ERPNext

**Role:** ERP/O2C/finance.\
**Owns:** sales orders, invoices, receivables/payments, AP/procurement
and accounting representation.\
**Informs:** DSO, invoice accuracy, cash realization, customer
profitability.\
**Example:** MySQL delivery completion can support ERPNext invoice
lifecycle; DuckLake combines both for O2C KPIs.

## PostgreSQL

**Role:** simulated commercial/ETRM source.\
**Owns:** contracts, trades, positions, hedges and commercial
commitments.\
**Informs:** risk, margin, customer commitments and trading decisions.\
**Example:** contract commitment joins to MySQL shipment to calculate
fulfillment.

## MySQL

**Role:** logistics execution.\
**Owns:** nominations, shipments, delivery/movement status.\
**Informs:** OTIF, inventory trajectory, logistics cost and customer
service risk.\
**Example:** shipment changes flow through Debezium/Kafka to Neo4j and
analytical products.

## SQLite

**Role:** local refinery/edge application.\
**Owns:** unit status, local production snapshots, operator/maintenance
events.\
**Informs:** availability, production, yield and outage impact.\
**Example:** hydrocracker trip reduces available ULSD production in
simulation.

## Public APIs

**Role:** observed external world. EIA supplies petroleum context;
NOAA/NHC weather; EPA regulatory/RFS context; PHMSA pipeline incident
history.\
**Informs:** simulation conditioning, event detection and model
calibration.\
**Rule:** public observations remain physically and semantically
distinct from synthetic PPC facts.

## Cloudflare Workers

**Role:** API/edge integration.\
**Receives:** external API requests or operational API calls.\
**Produces:** raw R2 objects and/or normalized event calls.\
**Example:** NOAA advisory is preserved in R2 and can emit a weather
event.

## Cloudflare R2

**Role:** durable object store and replay boundary.\
**Stores:** raw API payloads, source extracts/CDC archives,
canonical-world snapshots, manifests, model artifacts, large fixtures
and exports.\
**Does not own:** live transactional lifecycle or integrated analytical
semantics.

## Cloudflare D1

**Role:** lightweight operational workflow state.\
**Stores:** alerts, recommendation status, approvals and workflow
state.\
**Example:** OR-Tools recommendation becomes a D1 approval request
surfaced in Dash.

## AML + Azimutt

**Role:** authoritative data-model-as-code plus visual modeling.\
**Informs:** DDL, catalog mappings, DQ generation, ontology mappings and
synthetic schema contracts.\
**Does not define:** all business architecture or ontology meaning.

## Dagster

**Role:** orchestration.\
**Knows:** assets, dependencies, schedules, sensors, partitions and
backfills.\
**Informs:** OpenLineage run events and materialization flow.\
**Does not transport:** business events.

## Debezium

**Role:** CDC from PostgreSQL/MySQL.\
**Produces:** row-change events for Kafka.\
**Example:** shipment `IN_TRANSIT→DELAYED` becomes a change event.

## Apache Kafka

**Role:** event backbone.\
**Receives:** CDC and meaningful domain/data events.\
**Informs:** Neo4j state, event processors, automation and downstream
consumers.\
**Does not orchestrate:** multi-step data pipelines.

## DuckDB

**Role:** analytical compute/federation.\
**Reads:** Postgres/MySQL/SQLite extracts/R2/DuckLake where
appropriate.\
**Performs:** profiling, joins, transformations, simulation and
investigations.\
**Does not own:** durable enterprise analytical history.

## DuckLake

**Role:** integrated analytical system.\
**Owns:** Silver conformed history, Gold data products, KPI Store and
feature tables.\
**Informs:** Superset, Dash, ML models, optimization and agents.

## Databricks Free Edition

**Role:** enterprise-like parallel lakehouse/ML implementation.\
**Purpose:** demonstrate that EPM architecture is portable beyond
DuckLake.\
**Does not replace:** the open reference implementation.

## OpenMetadata

**Role:** catalog/governance control plane.\
**Knows:** assets, owners/stewards, glossary, domains,
products/contracts, lineage, certification and quality results.\
**Receives:** metadata from systems, GX results and OpenLineage.\
**Does not independently redefine:** enterprise business meaning.

## Great Expectations

**Role:** DQ execution.\
**Tests:** schema, null/uniqueness, inventory conservation, capacity,
accounting, provenance and cross-system rules.\
**Publishes/contextualizes through:** OpenMetadata.

## OpenLineage

**Role:** standard run/job/dataset lineage events.\
**Connects:** processing execution to catalog lineage.

## Apache Jena/Fuseki

**Role:** formal semantic layer.\
**Stores:** RDF/RDFS/OWL, SHACL, SKOS/PROV-O as appropriate.\
**Answers:** What does this concept mean? What constraints apply?\
**Example:** EnterpriseKPI is a Metric and must satisfy KPI SHACL
requirements.

## Neo4j Community

**Role:** operational labelled-property graph.\
**Stores:** current instances and relationships.\
**Answers:** What is connected to this event now? Which customers/KPIs
are exposed?\
**Example:**
Hurricane→Refinery→Hydrocracker→ULSD→Terminal→Contract→Customer.

## Policy-as-Code

**Role:** action constraints.\
**Receives:** proposed action plus context.\
**Produces:** allowed/recommend/approval/escalation outcome.\
**Example:** transfer above threshold requires Commercial Manager
approval.

## MLflow

**Role:** model experiment/registry lifecycle.\
**Tracks:** parameters, metrics, artifacts, versions and evaluation.\
**Artifacts:** durable copies can live in R2.

## Forecasting / ML

StatsForecast/MLForecast predict time-series outcomes.
scikit-learn/XGBoost/LightGBM handle general predictive models. Outputs
are `ESTIMATED`, not observed facts.

## DoWhy + EconML

**Role:** causal estimation.\
**Uses:** explicit causal assumptions plus observed/synthetic history.\
**Produces:** evidence about estimated causal effects and
counterfactuals.

## PyMC

**Role:** probabilistic uncertainty.\
**Example:** probability distribution of hurricane-induced capacity loss
and resulting margin-at-risk.

## OR-Tools

**Role:** constrained optimization.\
**Receives:** feasible alternatives, costs, capacities, priorities and
policies.\
**Produces:** mathematically optimized candidate action.\
**Does not approve:** the action.

## Ollama

**Role:** local LLM/embedding runtime for development. Model licenses
are tracked separately from runtime license.

## LangGraph

**Role:** stateful agent orchestration.\
**Coordinates:** Jena meaning, Neo4j context, DuckLake facts, models,
optimizer and policy.\
**Rule:** it cannot bypass governed tools or approval.

## PostgreSQL + pgvector

**Role:** initial vector/document retrieval.\
**Stores:** embeddings for playbooks, cases, definitions and documents.\
**Avoids:** premature dedicated vector infrastructure.

## Langfuse

**Role:** LLM/agent tracing and evaluation.\
**Different from MLflow:** Langfuse observes agent/tool behavior; MLflow
observes analytical model lifecycle.

## Apache Superset

**Role:** enterprise BI.\
**Consumes:** governed consumption views/KPI Store.\
**Does not own:** official KPI definitions.

## Plotly Dash

**Role:** operational decision application.\
**Combines:** events, Neo4j exposure, DuckLake economics, scenarios,
recommendations and D1 approvals.

## Grafana OSS

**Role:** technical observability.\
**Shows:** ingestion/pipeline health, lag, freshness, failures and
platform metrics.

## End-to-end example

``` text
NOAA advisory
→ Worker → R2 raw + weather event
→ Neo4j exposure graph
→ PyMC capacity scenarios
→ DuckLake inventory/margin calculations
→ DoWhy/driver analysis as applicable
→ OR-Tools alternatives
→ Policy check
→ D1 approval state
→ Dash recommendation
→ action/outcome
→ KPI Store + learning case
```

## Data-quality failure example

``` text
GX test fails on Commercial Margin
→ OpenMetadata marks product degraded
→ Neo4j finds dependent KPIs/decisions
→ automation marks KPI stale and blocks high-risk automated action
→ D1 incident/approval workflow
→ Grafana technical signal + Dash business impact
```

## Enterprise Context Engineering reuse
PPC reuses ECE contracts for Artifact, EvidenceItem, SourceAssertion, Claim, DecisionOption, DecisionDossier, temporal context and hidden-truth evaluation. R2 stores evidence bundles; DuckDB/DuckLake process structured corpus/evaluation data; Jena formalizes evidence semantics; Neo4j connects claims/decisions/evidence; OpenMetadata catalogs artifacts; Dagster orchestrates generation; Langfuse records agent retrieval/tool traces.

## EPM-driven execution flow
EPM provides principles, process authority, ontology/SHACL, KPI rules and data-product contracts. PPC maps structures to those IDs, generates process instances, computes governed values and tests conformance.

`EPM O2C process → PPC ERP/Commercial/Logistics transactions → event log → process conformance → KPI impact → evidence/decision context`.
