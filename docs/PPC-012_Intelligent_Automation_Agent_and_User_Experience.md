# PPC-012 --- Intelligent Automation, Agent, and User Experience Architecture

> **Reconciliation notice (2026-11-26):** Preserved historical Baseline v1.0 automation/UX guide. Amended by [ADR-0044](adr/0044-turtle-pyshacl-neo4j-serving-path.md), [ADR-0047](adr/0047-slice1-active-core-vs-staged-apps.md), [ADR-0048](adr/0048-pyomo-optimization-and-langgraph-pydantic-agents.md), and [ADR-0052](adr/0052-two-stage-ux-dash-and-relate-wasm.md) (Pyomo/HiGHS, Pydantic-typed tools, OTel/Langfuse, FastAPI/Dash Slice 1 + Relate WASM Slice 1.5). See [PPC-UX-001](enterprise-architecture/05-intelligence-experience/PPC-UX-001_Enterprise_Intelligence_Workspace.md) and [PPC-AGENT-001](enterprise-architecture/05-intelligence-experience/PPC-AGENT-001_Agent_Tools_and_Consequential_Actions.md).

**Purpose:** Define controlled decision workflows, agents, GraphRAG and
human experiences.

PPC uses an **ASD-STE100-inspired** technical writing style and
consistent defined terminology.

## Automation principle

LLMs do not calculate authoritative KPIs, forecasts, causal effects or
optimized actions. They interpret requests, select governed tools,
synthesize evidence and explain results.

## LangGraph workflow

Event received → classify → query Neo4j exposure → query DuckLake
economics → query Jena meaning → run analytical model → generate
feasible alternatives → OR-Tools optimization → policy check →
recommend/approve/escalate → D1 workflow state.

## Authority classes

`AUTO_EXECUTE`: low-risk/reversible/pre-approved.\
`RECOMMEND`: propose only.\
`REQUIRE_APPROVAL`: human authorization.\
`ESCALATE`: outside policy/risk tolerance or no feasible action.

## Explainable recommendation

Must show event, affected entities, evidence, KPI impact,
margin-at-risk, assumptions, uncertainty, alternatives, recommended
action, expected benefit, constraints, authority class and approver.

## GraphRAG

Neo4j retrieves relevant subgraphs; DuckLake retrieves numerical facts;
Jena supplies semantic definitions; pgvector retrieves
documents/cases/policies. The LLM synthesizes but cites/links the
governed evidence.

## User experiences

**Superset:** executive KPI scorecards, trends and governed analysis.\
**Dash:** event center, exposure graph, driver analysis, scenario
workbench, recommendation/approval UX.\
**Grafana:** technical pipelines, latency, failures, freshness and
platform health.\
**Streamlit:** optional data-science prototypes.

## Agent observability

Langfuse records prompts/tool calls/traces/evaluations. MLflow records
predictive/causal model experiments. These are different concerns.

## Golden tests

Store scenarios with expected exposed customers, expected drivers and
expected policy outcomes. Large fixtures go to R2; small fixtures may
live in Git.

## Evidence-grounded agent behavior
Every material recommendation/explanation should expose supporting evidence, source locator, provenance, epistemic status, decision-time availability, assumptions/uncertainty, contradictions/unknowns, alternatives/constraints and policy/authority basis.

Evaluated agents must not access hidden canonical decision truth. Langfuse traces should record evidence and tools used. Dash should provide an evidence panel for material recommendation claims.
