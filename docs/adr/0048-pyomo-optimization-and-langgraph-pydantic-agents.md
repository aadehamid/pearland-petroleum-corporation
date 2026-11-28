---
status: Decided
date: 2026-11-26
amends: PPC-011, PPC-012
source_answers: docs/adr/answers/2026-11-26-first-principles-grill.md#round-2-2026-11-26
---

# ADR-0048: Pyomo with HiGHS/IPOPT for optimization and LangGraph with Pydantic tools and OpenTelemetry/Langfuse for agents

## Context

`PPC-011` recorded OR-Tools for optimization and `PPC-012` recorded LangGraph and Langfuse for agent workflows and tracing, while later drafts raised Pyomo/HiGHS, Pydantic AI, and OpenTelemetry/Logfire as alternatives. PPC requires open-source/no-paid-runtime tooling, Python/FastAPI backends, and transparent algebraic refinery formulations that extend from LP to nonlinear blending and conversion.

## Decision

The owner accepted Round 2 Q13 via "Yes to the rest." (`docs/adr/answers/2026-11-26-first-principles-grill.md`):

- Accepted recommendation: "Yes. Adopt Pyomo plus HiGHS/IPOPT for refinery optimization, and use LangGraph with Pydantic-typed tool contracts and OpenTelemetry to self-hosted Langfuse."
- Optimization (item 1): "Adopt Pyomo with HiGHS (extending to IPOPT when nonlinear blending or kinetics enter) as the canonical optimization modeling stack instead of OR-Tools, because algebraic refinery formulations are easier to audit, verify against conservation equations, and extend from LP to NLP."
- Agents and telemetry (item 2): "Keep LangGraph for stateful human-approval and escalation workflows, use Pydantic AI (or Pydantic-typed tool contracts) inside nodes for strict schema-validated tool calls, and use OpenTelemetry exporting to self-hosted Langfuse (instead of paid Logfire cloud) with PostgreSQL/pgvector for evidence retrieval and Ollama/local-or-configured LLM endpoints."

## Consequences

- `PPC-011`, `PPC-ANALYTICS-001`, `PPC-012`, and `PPC-AGENT-001` must be updated to record Pyomo + HiGHS/IPOPT as the optimization stack and LangGraph + Pydantic-typed tool contracts + OpenTelemetry to self-hosted Langfuse as the agent stack.

## Post-review amendment notes (2026-11-26)

- **Staged by [ADR-0055](0055-slice1-hosting-observability-postgres-workflow-and-databricks-sync.md) (owner-delegated stand-in Claude Fable 2):** Slice 1 ships OTLP JSON traces hourly from a lightweight OpenTelemetry Collector to R2 `telemetry/otel/` (queried by DuckDB for leak tests), staging ClickHouse-backed self-hosted Langfuse v3 to `WP-7`; no local Ollama runs on the 12 GB `exe.dev` VM; live `WP-3B` LLM endpoint selection remains explicitly with Hamid Adesokan (with recorded responses for golden tests).
- **Extended by [ADR-0056](0056-identity-steward-action-thresholds-and-refinery-a-parameters.md):** Locks numeric `AUTO_EXECUTE` / `REQUIRE_APPROVAL` Tier 1 & Tier 2 / `ESCALATE` / `PROHIBITED` (`DENIED`) thresholds and HiGHS (`1e-7`) / IPOPT (`1e-8`) solver tolerances.
