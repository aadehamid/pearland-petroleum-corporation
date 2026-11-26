---
status: Decided
date: 2026-11-26
amends: ADR-003, ADR-004, ADR-010, ADR-018
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

- `PPC-PLATFORM-001` and `PPC-PLAN-001` (WP-4) adopt this deployment topology and require a verified restore drill meeting the RPO/RTO targets before Slice 1 qualification.

## Post-review clarification notes (2026-11-26)

This note records operational sizing and storage dispositions surfaced by the independent external-model review for owner confirmation in `WP-0`. It does not alter the owner decision recorded above.

- **`exe.dev` memory sizing and Langfuse v3 footprint:** Self-hosted Langfuse v3 requires ClickHouse and Redis alongside PostgreSQL, MySQL, Neo4j Community, Dagster daemon/webserver, FastAPI, Dash, NATS, and Mosquitto. Combined steady-state memory requires `12–16 GB RAM` across two `exe.dev` VMs (or an `8 GB` single VM if Slice 1 defers Langfuse v3 in favor of a lightweight OpenTelemetry collector). See the per-service sizing and backup/RPO/RTO table in `docs/enterprise-architecture/independent-review/PPC-REVIEW-003_System_and_Decision_Register.md` Section 1.
- **Cloudflare D1 disposition:** `ADR-005` named Cloudflare D1 for lightweight workflow state, while `ADR-0051` hosts operational stores on `exe.dev` PostgreSQL. `WP-0` tracks the owner choice between consolidating lightweight workflow state into `exe.dev` PostgreSQL or retaining D1 with automated R2 SQL-dump backups.
- **Databricks Free Edition ingest:** Consistent with `ADR-0045` (`T86`, lines 19603–19607), paid Databricks tiers read R2 Delta prefixes directly while Databricks Free Edition verification (`WP-8`) syncs pinned Delta copies into workspace-managed storage.
