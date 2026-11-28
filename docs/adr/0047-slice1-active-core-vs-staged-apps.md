---
status: Decided
date: 2026-11-26
amends: none
source_answers: docs/adr/answers/2026-11-26-first-principles-grill.md#round-2-2026-11-26
---

# ADR-0047: Slice 1 active source and UI core versus staged enterprise applications

## Context

Under `ADR-0041` (function-first lean core plus staged extensions), Slice 1 (hydrocracker compressor derate) and Slice 2 (crude-quality rejection) require heterogeneous source systems without carrying unrelated enterprise applications before their target scenarios arrive.

## Decision

The owner accepted Round 2 Q12 via "Yes to the rest." (`docs/adr/answers/2026-11-26-first-principles-grill.md`):

- Accepted recommendation: "Yes. Lock this Slice 1 active core and defer Twenty, ERPNext, OpenMetadata, Superset, and Grafana to their respective later scenarios while keeping Relate WASM experimental."
- Active in Slice 1 and Slice 2: OT/historian stack (ICE boundary), Refinery/LIMS edge store (SQLite), Commercial/CTRM store (PostgreSQL), Logistics store (MySQL), Cloudflare R2 durable storage, DuckDB/Delta analytical store, Neo4j Community, and a bounded FastAPI plus Plotly Dash workspace (keeping Relate WASM as a separate post-authorization UI prototype, not a Slice 1 dependency).
- Explicitly deferred to later scenarios (contracts preserved, not retired): Twenty CRM (`ADR-022`) and ERPNext (`ADR-023`) until O2C/commercial-finance scenarios; OpenMetadata (`ADR-007`) and Grafana until the governance/observability phase (keeping lightweight Great Expectations and OpenLineage manifests active early); Apache Superset until multi-KPI BI scorecard phases.

## Consequences

- `ADR-007`, `ADR-014`, `ADR-022`, and `ADR-023` remain intact as staged roadmap choices rather than Slice 1 critical-path blockers.
- Note (updated 2026-11-26): The Round 3 promotion question for Relate WASM (`T111`, `EA09D-D09`) is now decided by [ADR-0052](0052-two-stage-ux-dash-and-relate-wasm.md) as the Slice 1.5 business-facing Interactive Enterprise Context Explorer (`WP-5B`).
