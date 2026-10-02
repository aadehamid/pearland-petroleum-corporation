# PPC-014 --- Implementation Roadmap and Build Runbook

**Purpose:** Define the build sequence from empty environment to PPC
World v0.1.

## Phase 0 --- Repository and contracts

Create repo structure, ADR register, semantic vocabulary, AML models,
provenance enum, IDs, quality rules and environment/secrets pattern.

## Phase 1 --- Durable storage and local platform

Create PPC R2 bucket/prefixes. Stand up PostgreSQL, MySQL, SQLite
source, DuckDB/DuckLake and basic development environment.

## Phase 2 --- Public-data foundation

Ingest EIA first. Add NOAA/NHC, PHMSA and EPA. Preserve raw responses in
R2. Normalize publication/effective time.

## Phase 3 --- Canonical world generator

Generate master data and twelve-month baseline. Enforce conservation,
capacity, accounting, correlation, provenance and reproducibility.
Snapshot world/manifests to R2.

## Phase 4 --- Source-system materialization

Load commercial slices to Postgres, logistics to MySQL, refinery to
SQLite, CRM/ERP records to Twenty/ERPNext, workflow seed data to D1.
Introduce controlled identifier/schema/time-zone differences.

## Phase 5 --- Integration

Deploy Dagster. Configure Debezium/Kafka for Postgres/MySQL. Add API
integrations and SQLite micro-batch. Land/replay through R2. Emit
OpenLineage.

## Phase 6 --- Silver/Gold

Build identity crosswalks and conformed dimensions/facts. Create
foundational and derived data products. Register/catalog in
OpenMetadata. Add GX rules.

## Phase 7 --- KPI Store and consumption

Implement KPI metadata/values/thresholds/status and semantic consumption
views. Connect Superset.

## Phase 8 --- Knowledge

Create Jena ontology/SHACL shapes. Populate Neo4j operational graph and
semantic mappings.

## Phase 9 --- Performance Intelligence

Create forecasts, anomaly models, variance decomposition, causal
experiments, probabilistic scenarios and OR-Tools optimization. Track
with MLflow.

## Phase 10 --- Automation

Implement LangGraph workflow, policy checks, D1 state and Dash decision
UX. Add golden agent tests and Langfuse tracing.

## Phase 11 --- Observability

Grafana platform dashboards; OpenMetadata quality/lineage/incident
context; event-to-business impact propagation.

## Phase 12 --- Demonstration

Run hurricane scenario end-to-end: public event → exposure → impact →
KPI → explanation → alternatives → optimized recommendation →
policy/approval → action → outcome → learning case.

## Release gates

No phase promotes uncertified data if hard DQ/conservation/provenance
tests fail. Every architecture change requires ADR update. Every demo
must identify observed, synthetic, estimated and assumed values.

## Evidence and evaluation implementation work
Before blind agent evaluation:
1. Implement Artifact, EvidenceItem, SourceAssertion, Claim, DecisionOption and DecisionDossier schemas.
2. Add authoring/effective/publication/ingestion/decision-time fields.
3. Generate role-specific documents/messages from hidden dossiers.
4. Add `evaluation/development/` and access-controlled `evaluation/hidden/`.
5. Build claim-to-source graph relationships.
6. Create temporal-leakage, contradiction, unknown and missing-evidence golden cases.
7. Verify evaluated agents cannot retrieve hidden truth.
8. Score claim-level provenance, unsupported claims, epistemic labeling and temporal correctness.

The hurricane demo is incomplete until it can explain the decision using only evidence available at decision time.

## EPM dependency and conformance work
Before treating source-system generation as EPM-conformant: create/pin the EPM dependency manifest; map PPC AML/source concepts to EPM IDs; load/validate ontology; run competency questions; constrain baseline process generation with EPM process authority; generate event logs/conformance tests; record intentional deviations; validate KPI/data-product contracts; block silent use of non-approved upstream authority.
