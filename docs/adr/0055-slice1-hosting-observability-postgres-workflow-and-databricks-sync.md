---
status: Decided
date: 2026-11-26
amends: ADR-0045, ADR-0048, ADR-0051
authority: Owner-delegated stand-in (Claude Fable 2, claude-fable-5-2)
source_answers: docs/adr/answers/2026-11-26-claude-fable-2-owner-standin.md#gate-2--adr-0045-and-adr-0051-operations
---

# ADR-0055: Slice 1 exe.dev 12 GB lightweight OTel topology, PostgreSQL workflow state, and Databricks Free Edition synced copy

## Context

External review of `ADR-0045`, `ADR-0048`, and `ADR-0051` surfaced three `WP-0` operational choices: (a) Databricks Free Edition ingest without custom R2 external locations (`T86`), (b) `exe.dev` Slice 1 RAM sizing with or without ClickHouse-backed Langfuse v3, and (c) consolidating workflow/approval state into PostgreSQL versus retaining Cloudflare D1 (cited in baseline `PPC-002`, `PPC-012`, `PPC-014`). On 2026-11-26, the owner delegated stand-in gate closure to Claude Fable 2 (`claude-fable-5-2`).

## Decision

Claude Fable 2, acting as owner stand-in (`docs/adr/answers/2026-11-26-claude-fable-2-owner-standin.md`), ruled:

- **G2-a (Databricks synced copy):** "WP-8 [split into `WP-8A` for Databricks parity and `WP-8B` for `WorldExportBundle` certification in `PPC-PLAN-001`] copies pinned Delta tables into Databricks Free Edition workspace-managed tables. A Dagster job on `exe.dev` runs the copy, never a laptop. No paid Databricks tier is used in v1. The paid external-location path is documented only. The WP-0 probe picks the copy mechanism. If no mechanism works, stop and raise an ADR."
- **G2-b (12 GB Slice 1 topology and lightweight OTel collector):** "Slice 1 runs one 12 GB `exe.dev` VM with an OpenTelemetry Collector that writes OTLP JSON files, shipped hourly to R2 under `telemetry/otel/`. DuckDB queries them for the trace-leak tests. Langfuse v3 with ClickHouse moves to WP-7. If `exe.dev` cannot give 12 GB on one VM, use two VMs (8 GB stores, 4 GB apps) with the same Compose files. No local Ollama runs on these VMs. This stages ADR-0048 and does not reverse it."
- **G2-c (PostgreSQL workflow state; D1 retired for v1):** "All workflow, approval and LangGraph checkpoint state lives in PostgreSQL on `exe.dev`. Cloudflare D1 is not used in v1. Reason: proposal, authorization and receipt must commit in one ACID transaction with the idempotency key, and the WAL backup already covers it."

## Considered options

- Running ClickHouse-backed Langfuse v3 in Slice 1 on 16 GB across two VMs (deferred to `WP-7` to keep Slice 1 lean).
- Retaining Cloudflare D1 with R2 SQL-dump backups alongside PostgreSQL (rejected because workflow authorization and receipts need one ACID transaction with idempotency keys and WAL recovery).
- Paid Databricks tier in v1 (rejected under the no-paid-commercial-license rule).

## Consequences

- `ADR-0045` is clarified to lock Dagster-driven synced copies into Databricks Free Edition workspace-managed tables in `WP-8A`, gated by the `WP-0` ingest probe.
- `ADR-0048` is staged so Slice 1 ships OTLP JSON traces to R2 `telemetry/otel/` (queried by DuckDB for leak tests) while ClickHouse-backed Langfuse v3 enters in `WP-7`. The `WP-3B` LLM endpoint choice remains explicitly reserved for Hamid Adesokan (with recorded responses for golden tests).
- `ADR-0051` is amended to lock the 12 GB single VM (or 8 GB + 4 GB two-VM fallback) topology and consolidate all workflow, approval, and LangGraph checkpoint state into PostgreSQL on `exe.dev`, removing Cloudflare D1 from v1.
