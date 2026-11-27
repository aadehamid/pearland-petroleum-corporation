# PPC-013 --- Cloudflare R2 Durability and Project Storage Standard

> **Reconciliation notice (2026-11-26):** Preserved historical Baseline v1.0 R2 standard. Amended by [ADR-0045](adr/0045-delta-lake-on-r2-and-databricks-portability.md) (Delta Lake via `delta-rs` replaces DuckLake), [ADR-0051](adr/0051-exe-dev-r2-databricks-hosting-and-recovery.md), and [ADR-0053](adr/0053-legacy-data-quarantine-and-world-export-bundle.md) (adds `delta/`, `exports/world_bundle/observable/`, and `legacy_quarantine/` prefixes). See [PPC-PLATFORM-001](enterprise-architecture/06-platform-operations/PPC-PLATFORM-001_Infrastructure_Security_and_Operations.md).

**Purpose:** Apply the user's generic R2 agent standard to PPC.

## Core rule

R2 is durable object storage. Local disk is scratch. Git holds code,
docs and small fixtures. Operational databases remain authoritative for
their transactional domains. DuckLake remains authoritative for
integrated analytical history.

## Connection

Use the fixed Cloudflare account/endpoint supplied by the project owner,
`region=auto`, S3 v4 signing and boto3. Credentials must come from a
secret store and must never appear in chat, logs or committed
configuration.

## One bucket

Use one PPC project bucket. Recommended logical prefixes:

``` text
raw/external/{eia,noaa,epa,phmsa}/
raw/source_extracts/{postgres,mysql,sqlite,d1}/
raw/cdc/{postgres,mysql}/
cache/{normalized,conformed,features,simulation,scenarios,quality}/
models/{forecasting,causal,anomaly,optimization}/
exports/{powerbi,api,training,demo}/
fixtures/{golden,test}/
manifests/{ingestion,generation,scenarios,releases}/
notes/
_probe/
```

## Canonical world

Persist certified canonical synthetic-world snapshots under
`evaluation/hidden/world_version=.../` with generation manifests (superseding the earlier `cache/simulation/` path so all hidden canonical state sits under one restricted credential boundary; see `ADR-0051`, `ADR-0053`, and `PPC-PLAN-001`). This
canonical world state is for simulator validation and blind evaluation. Integration code must not use
hidden canonical IDs to bypass source-system reconciliation.

## Raw

Preserve API responses and source extracts with
retrieval/publication/effective metadata, checksums and source
parameters. Raw is append-oriented.

## Replay

R2 is the durable recovery boundary. Rebuild Silver/Gold/KPI Store from
raw/extract snapshots after failures. Archive CDC batches when long-term
replay beyond Kafka retention is required.

## Manifests

Record world version, seed, code/model/schema versions, public-data
snapshot, record counts, checksums and scenario configuration.

## Models and fixtures

R2 stores large model artifacts and large golden fixtures. Git stores
code, schemas, docs and small fixtures.

## Agent behavior

Pull only required objects. Prefer remote/streaming reads when
supported. Process locally only as scratch. Upload durable outputs.
Delete temporary leftovers. Connectivity probes use `_probe/` or
`notes/`, never live raw/cache prefixes.

## Evidence and hidden-evaluation storage
PPC adds `cache/documents/`, `cache/evidence/`, `cache/decision-dossiers/`, `cache/graph/`, `evaluation/development/` and `evaluation/hidden/` logical prefixes. Hidden evaluation truth and canonical decision rationale require restricted credentials and must never be available to ordinary retrieval agents or prompt/model tuning workflows.
