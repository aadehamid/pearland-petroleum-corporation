---
status: Decided
date: 2026-11-26
amends: ADR-017
source_answers: docs/adr/answers/2026-11-26-first-principles-grill.md#round-2-2026-11-26
---

# ADR-0045: Delta Lake on Cloudflare R2 with DuckDB local compute and Databricks target portability

## Context

`ADR-017` in `PPC-REG-001` recorded DuckDB/DuckLake for analytical history and `ADR-018` positioned Databricks Free Edition as a parallel lab. In the upstream architecture discussion (T86, 2026-11-25), the owner required Databricks compatibility and selected Delta Lake as the long-term table format, which the draft `ef4eb08` package had left open for ADR reconciliation.

## Decision

The owner confirmed Round 2 Q10 (`docs/adr/answers/2026-11-26-first-principles-grill.md`):

- Owner verbatim: "Q10: this decision was already made to use Delta Table since the eventual target platform will be Databricks. didnt you see it in the chat conversations@[/Users/hamidadesokan/Downloads/ChatGPT-Downstream Backcasting Research-20261125-2232.md] i have attached the raw converations from all the documents was created form here for additional context."
- Accepted option (Option 1): "Delta Lake on Cloudflare R2 (single-writer controlled through Dagster and pinned by immutable ReleaseManifest records), queried locally by DuckDB and directly portable to Databricks Free Edition in a later verification phase — replacing DuckLake so one open table format serves both local compute and Databricks without a translation bridge."

## Considered options

- Retaining DuckLake on R2 with a separate export bridge to Databricks (rejected in favor of native Delta Lake portability).
- Plain versioned Parquet without Delta Lake transaction logs (rejected because Databricks is the eventual target platform).

## Consequences

- `ADR-017` is amended: Delta Lake on Cloudflare R2 replaces DuckLake as PPC's analytical table format, with single-writer Dagster control and immutable `ReleaseManifest` cuts.
- `ADR-018` is clarified: Databricks is the eventual target enterprise platform (developed against Databricks Free Edition and portable to higher tiers), staged off the Slice 1 critical path while DuckDB queries the same Delta tables locally.

## Post-review clarification notes (2026-11-26)

This note records implementation details surfaced by the independent external-model review against the upstream transcript (`T86`, lines 19603–19607). It does not alter the owner decision recorded above.

- **Single-writer lock on Cloudflare R2:** Because `delta-rs` requires either an external lock provider or conditional-PUT support on S3-compatible object stores and Cloudflare R2 supports ETag-based conditional PUT, `delta-rs` writes on R2 must run with `aws_conditional_put="etag"` behind a Dagster concurrency pool of `1` per Delta table, while DuckDB reads those tables read-only.
- **Databricks Free Edition ingest path (`T86`, confirmed by [ADR-0055](0055-slice1-hosting-observability-postgres-workflow-and-databricks-sync.md)):** Databricks Free Edition cannot mount custom Cloudflare R2 external locations directly (`T86`, lines 19603–19607). Under `ADR-0055` (`G2-a`), `WP-8A` copies pinned Delta tables into Databricks Free Edition workspace-managed Delta tables via a Dagster job on `exe.dev` (never a laptop), using the copy mechanism verified in the `WP-0` ingest probe; paid Databricks tiers remain documented only for future expansion.
