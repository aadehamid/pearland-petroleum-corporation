---
status: Decided
date: 2026-11-26
amends: none
source_answers: docs/adr/answers/2026-11-26-first-principles-grill.md#round-3-2026-11-26
---

# ADR-0051: exe.dev, Cloudflare R2, and staged Databricks hosting topology with RPO/RTO targets

## Context

In T52 and T79–T81 the owner prohibited paid commercial licenses, allowed Cloudflare R2 as an explicit free-tier exception, confirmed no Neo4j Enterprise entitlement, and identified an existing `exe.dev` subscription to host Neo4j Community (avoiding AuraDB Free inactivity wipes) and PostgreSQL. `PPC-PLATFORM-001` and `PPC-RISKS-AND-OPEN-QUESTIONS.md` left deployment placement and RPO/RTO objectives open.

## Decision

The owner accepted Round 3 Q16 via "Yes to all." (`docs/adr/answers/2026-11-26-first-principles-grill.md`):

- Accepted recommendation: "Yes. Lock this exe.dev plus Cloudflare R2 plus staged Databricks topology and the RPO/RTO contract."
- Durable source-of-truth tier (Cloudflare R2): raw public and source evidence, canonical world checkpoints, Delta Lake analytical tables, and immutable `ReleaseManifest` files.
- Operational runtime tier (`exe.dev` persistent VMs with local Docker Compose parity for dev/CI): PostgreSQL (CTRM, TimescaleDB historian, pgvector evidence, Dagster metadata), MySQL (Logistics), SQLite (Refinery/LIMS edge), NATS JetStream, Mosquitto (OT Sparkplug B), Neo4j Community (persistent `/data` volume, treated strictly as a rebuildable projection with offline `neo4j-admin dump` backups to R2), FastAPI backend, and Dash workspace.
- Enterprise portability tier (Databricks Free Edition to paid Databricks): reads the same Delta Lake tables on R2, staged off the Slice 1 critical path.
- Recovery objectives: zero silent data loss across committed world checkpoints and source outboxes (RPO = last committed manifest and WAL backup on R2); full deterministic rebuild within 1 hour (RTO <= 1 hour), proven by a restore drill before Slice 1 release.

## Consequences

- `PPC-PLATFORM-001` and `PPC-PLAN-001` adopt this deployment topology: `WP-4A` provisions the platform and runs a synthetic stub-writer baseline drill in parallel with `WP-1`–`WP-3`, and `WP-4B` (`R4` gate, after `WP-3` delivers live outbox and Delta writers) executes the live restore drill proving the `RPO` and `RTO <= 1 hour` targets before `WP-5` Slice 1 qualification.

## Post-review clarification notes (2026-11-26)

This note records subsequent amendments without altering the owner decision recorded above.

- **Amended by [ADR-0055](0055-slice1-hosting-observability-postgres-workflow-and-databricks-sync.md) (`exe.dev` 12 GB Slice 1 topology and OTel collector):** Slice 1 runs on one `12 GB` `exe.dev` VM (or an `8 GB` stores plus `4 GB` apps two-VM fallback if `exe.dev` cannot provision 12 GB on one VM) with a lightweight OpenTelemetry Collector shipping OTLP JSON hourly to R2 `telemetry/otel/` (queried by DuckDB for trace-leak tests). ClickHouse-backed Langfuse v3 moves to `WP-7`, and no local Ollama runs on these VMs.
- **Amended by [ADR-0055](0055-slice1-hosting-observability-postgres-workflow-and-databricks-sync.md) (Cloudflare D1 retired for v1):** Baseline docs (`PPC-002` §5, `PPC-012`, `PPC-014`) mentioned Cloudflare D1 for lightweight workflow state. Under `ADR-0055` (`G2-c`), all workflow, approval, and LangGraph checkpoint state lives in PostgreSQL on `exe.dev` so proposals, authorizations, and receipts commit in one ACID transaction covered by WAL backups; Cloudflare D1 is not used in v1.
- **Databricks Free Edition ingest (`ADR-0055` `G2-a`):** `WP-8A` uses a Dagster job on `exe.dev` to copy pinned Delta tables into Databricks Free Edition workspace-managed tables (never a laptop), selected by the `WP-0` ingest probe.
