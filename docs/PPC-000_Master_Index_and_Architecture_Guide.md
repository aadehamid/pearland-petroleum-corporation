# PPC-000 --- Master Index and Architecture Guide

**Baseline:** PPC Architecture Baseline v1.0\
**Company:** Pearland Petroleum Corporation (PPC), fictional\
**Purpose:** Front door to the architecture and document pack.

## Documentation standard

PPC uses an **ASD-STE100-inspired** technical writing style. PPC does
not claim formal ASD-STE100 compliance. Use consistent terms, direct
verbs, short sections, explicit relationships, and established technical
vocabulary when it improves precision.

## Governing principles

-   Business meaning is independent of software products.
-   Public observations and synthetic PPC facts are always
    distinguishable.
-   Each operational object has an authoritative source for its
    lifecycle stage.
-   The canonical synthetic PPC world exists before heterogeneous
    source-system materialization.
-   Data products expose reusable governed information. BI tools do not
    own KPI logic.
-   Formal semantics and operational graph traversal are separate
    responsibilities.
-   Specialized models calculate forecasts, causal effects, uncertainty,
    and optimized actions. LLMs orchestrate and explain.
-   Material actions remain subject to explicit policy and human
    approval.

## What PPC is

PPC is an executable reference implementation of the Enterprise
Performance Model (EPM). It combines public observations with a
synthetic downstream enterprise to answer: **An event occurred. What
changed, what performance is at risk, why, what should PPC do, and what
can PPC learn?**

## Architecture

``` text
PUBLIC WORLD                     PPC OPERATIONAL WORLD
EIA/NOAA/EPA/PHMSA               Twenty/ERPNext/Postgres/MySQL/SQLite
          \                         /
           +------ INTEGRATION -----+
           Workers/Debezium/Kafka/Dagster/R2/DuckDB
                         |
                  DATA PLATFORM
               DuckLake/Databricks
                         |
             MEANING/GOVERNANCE/TRUST
 AML/Azimutt/OpenMetadata/GX/OpenLineage/Jena/Neo4j
                         |
                   INTELLIGENCE
 Forecasting/Causal/PyMC/OR-Tools/MLflow/LangGraph
                         |
                    EXPERIENCE
              Superset/Dash/Grafana
```

## Reading map

  Question                        Document
  ------------------------------- -------------
  Why PPC?                        PPC-001
  Overall stack?                  PPC-002
  Business meaning?               PPC-003
  Modeling standard?              PPC-004
  Synthetic generation?           PPC-005
  Where data lives?               PPC-006
  Integration/events?             PPC-007
  Data products/KPIs?             PPC-008
  Governance/quality?             PPC-009
  Ontology/graph/policy?          PPC-010
  Performance Intelligence?       PPC-011
  Automation/agents/UX?           PPC-012
  R2 standard?                    PPC-013
  How to build?                   PPC-014
  Why decisions were made?        PPC-REG-001
  Source/integration inventory?   PPC-REG-002
  KPI/data-product inventory?     PPC-REG-003
  What every tool does?           PPC-REF-001
  Unstructured evidence corpus?   PPC-018

## EPM chain

Strategy/Objectives → Domains → Value Streams/Stages ↔ Capabilities →
Processes/Activities → Decisions → Outcomes → Measurements → Metrics →
governed KPIs → Data Products → KPI Store/Consumption →
Analytics/Automation/AI/Learning.

## Provenance

`OBSERVED`, `DERIVED`, `ESTIMATED`, `SYNTHETIC`, `SCENARIO_ASSUMPTION`.

## Deferred infrastructure

No dedicated feature store, vector database, or policy server in v1.
DuckLake Gold, PostgreSQL/pgvector, and policy-as-code are sufficient
until a demonstrated requirement appears.

## Evidence and decision-provenance extension
PPC depends on Enterprise Context Engineering for evidence, decision provenance, temporal context, retrieval grounding and evaluation. Read `PPC-016_Evidence_Decision_Provenance_and_Evaluation_Architecture.md`.

PPC uses two independent axes: **data provenance** (`OBSERVED`, `DERIVED`, `ESTIMATED`, `SYNTHETIC`, `SCENARIO_ASSUMPTION`) and **epistemic status** (`EVIDENCE`, `INFERENCE`, `CONTRADICTION`, `UNKNOWN`). Canonical PPC truth is complete simulation truth. Agent-visible evidence is intentionally partial, and hidden truth is excluded from blind evaluation.

## EPM execution dependency
PPC consumes versioned EPM architectural principles, business/process authority, semantic model, ontology/SHACL, measurement/KPI rules, data-product portfolio, KPI Store contract and competency questions. Read `PPC-017_EPM_Dependency_Semantic_Authority_and_Process_Conformance_Contract.md`.

PPC adopts **Meaning does not compute** and compares executed synthetic processes with EPM's designed process authority.

## Enterprise evidence corpus
PPC generates documents, messages, reports, approvals, policies, operational notes and learning artifacts from the canonical world. Each artifact reflects only what its author role knew at that time. Read `PPC-018_Enterprise_Evidence_Corpus_and_Unstructured_Data_Generation_Strategy.md`.
