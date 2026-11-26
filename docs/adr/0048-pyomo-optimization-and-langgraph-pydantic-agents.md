---
status: Decided
date: 2026-11-26
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
