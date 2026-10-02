# Pearland Petroleum Corporation

> **An executable synthetic downstream oil and gas enterprise for proving Enterprise Performance Modeling and Enterprise Context Engineering end to end.**

Pearland Petroleum Corporation (PPC) is a fictional North American downstream oil and gas company.

This repository builds PPC as a realistic, heterogeneous enterprise environment using public market and industry data, synthetic internal business data, operational source systems, data integration, semantic models, knowledge graphs, performance intelligence, and intelligent automation.

The central question is:

> **An event occurred. What changed, what performance is at risk, why, what should PPC do, and what can PPC learn from the outcome?**

PPC is not only a synthetic dataset.

It is an **executable enterprise laboratory**.

---

## Documentation style

PPC documentation uses an **ASD-STE100-inspired** technical writing style.

The project does not claim formal ASD-STE100 compliance.

The writing follows these principles:

- Use one term consistently for one concept.
- Prefer direct verbs.
- Keep sentences and sections reasonably short.
- Define technical terms before relying on them.
- Make relationships explicit.
- Avoid unnecessary synonyms for governed concepts.
- Use established downstream, data, architecture, and AI terminology when it improves precision.
- Separate facts, assumptions, estimates, synthetic values, and scenarios.

---

# Why this repository exists

Enterprise performance does not exist inside one report, database, application, or KPI.

A downstream event can propagate across many parts of the enterprise.

For example:

```text
Hurricane
    ↓
Refinery availability
    ↓
ULSD production
    ↓
Terminal inventory
    ↓
Customer commitments
    ↓
Spot replacement supply
    ↓
Logistics cost
    ↓
Commercial margin
    ↓
Enterprise KPI
    ↓
Business decision
```

A realistic enterprise must connect these relationships across different systems, data models, business processes, and decision contexts.

PPC provides a controlled environment for building and testing that architecture without using confidential enterprise data.

---

# PPC and the other repositories

PPC is the integration and execution environment for two upstream architecture repositories.

```text
                 ENTERPRISE PERFORMANCE MODEL
                  Business and performance meaning
                             │
                             │
                             ▼
              ┌──────────────────────────────┐
              │                              │
              │  PEARLAND PETROLEUM          │
              │  CORPORATION                 │
              │                              │
              │  Executable synthetic        │
              │  downstream enterprise       │
              │                              │
              └──────────────────────────────┘
                             ▲
                             │
                             │
                ENTERPRISE CONTEXT ENGINEERING
             Evidence, provenance, context and reasoning
```

## Enterprise Performance Model

The `enterprise-performance-model` repository defines:

- downstream business domains;
- value streams and stages;
- capabilities and sub-capabilities;
- business processes and activities;
- business decisions;
- measurements, metrics and KPIs;
- data products;
- KPI Store architecture;
- enterprise semantic definitions;
- downstream ontology;
- semantic constraints and competency questions.

It answers:

> **What does the downstream enterprise mean, and how should its performance be represented?**

PPC consumes versioned EPM artifacts rather than redefining them.

For example:

```text
EPM defines:
    epm:Refinery
    epm:Customer
    epm:Shipment
    epm:EnterpriseKPI

PPC instantiates:
    ppc:PearlandGulfCoastRefinery
    ppc:CustomerABC
    ppc:Shipment8821
    ppc:ULSDNetback
```

---

## Enterprise Context Engineering

The `enterprise-context-engineering` repository defines reusable patterns for:

- evidence;
- provenance;
- temporal context;
- decision provenance;
- evidence versus inference;
- uncertainty and unknowns;
- source-to-answer traceability;
- synthetic evidence generation;
- retrieval and grounding;
- context graphs;
- agent evaluation.

It answers:

> **How can people and AI agents assemble trustworthy enterprise context from distributed evidence?**

PPC applies these patterns to downstream operations and performance.

---

## PPC

PPC answers:

> **Can the Enterprise Performance Model and Enterprise Context Engineering operate together in a realistic enterprise?**

PPC therefore owns the fictional enterprise implementation:

- source applications;
- synthetic operations;
- public-data integration;
- event processing;
- data pipelines;
- analytical products;
- KPI Store implementation;
- knowledge graphs;
- Performance Intelligence;
- Intelligent Automation;
- AI agents;
- user applications;
- scenarios and evaluations.

For the complete repository relationship, see:

`docs/PPC-015_Three_Repository_Operating_Model.md`

---

# What is real and what is synthetic?

PPC deliberately combines real public observations with fictional enterprise data.

Every material value must be classified as one of:

| Provenance | Meaning |
|---|---|
| `OBSERVED` | Direct public observation |
| `DERIVED` | Deterministic calculation from governed inputs |
| `ESTIMATED` | Statistical or analytical model estimate |
| `SYNTHETIC` | Fictional PPC enterprise fact |
| `SCENARIO_ASSUMPTION` | Explicit scenario or stress-test input |

Examples:

```text
EIA PADD 3 distillate inventory
→ OBSERVED

Five-year inventory deviation
→ DERIVED

Next-week inventory forecast
→ ESTIMATED

PPC Houston Terminal inventory
→ SYNTHETIC

Assume hydrocracker unavailable for 72 hours
→ SCENARIO_ASSUMPTION
```

Synthetic PPC information must never be represented as factual information about a real company.

---

# Initial business scope

The first PPC world focuses on:

## Geography

U.S. Gulf Coast / PADD 3

## Products

- ULSD
- regular gasoline
- premium gasoline

## Initial synthetic enterprise

- one Gulf Coast refinery;
- simplified CDU, FCC and hydrocracker;
- three terminals;
- pipeline, truck and marine logistics;
- twelve representative customers;
- customer contracts;
- physical trades and positions;
- inventory;
- shipments and deliveries;
- commercial commitments;
- hedges;
- financial transactions.

The architecture is designed to expand later.

---

# Source systems

PPC intentionally distributes information across heterogeneous systems.

```text
Twenty
CRM
Accounts / Contacts / Opportunities

ERPNext
ERP
Orders / Invoices / AR / AP / Payments

PostgreSQL
Commercial / Trading
Contracts / Trades / Positions / Hedges

MySQL
Logistics
Nominations / Shipments / Deliveries

SQLite
Refinery / Edge
Unit Status / Production / Operator Events

External APIs
Observed World
EIA / NOAA / EPA / PHMSA
```

Identifiers, schemas, grains, time zones, and update patterns intentionally differ between systems.

The integration architecture must reconcile them.

---

# Architecture

```text
                     PUBLIC / EXTERNAL WORLD

                  EIA   NOAA   EPA   PHMSA
                         │
                         ▼
                 Cloudflare Workers
                         │
                         ▼
                    Cloudflare R2
                  Raw / Durable Evidence


                  PPC SOURCE SYSTEMS

        Twenty        ERPNext       PostgreSQL
          CRM           ERP          Commercial
           │             │               │
           └─────────────┼───────────────┤
                         │               │
                       MySQL           SQLite
                     Logistics        Refinery
                         │               │
                         └───────┬───────┘
                                 ▼

                         INTEGRATION

                   Debezium / Kafka
                         Dagster
                          DuckDB
                            │
                            ▼

                       DATA PLATFORM

                   DuckLake / Databricks
                            │
                ┌───────────┼────────────┐
                ▼           ▼            ▼
              Silver       Gold      KPI Store
                            │
                            ▼

                  GOVERNANCE & MEANING

             AML / Azimutt / OpenMetadata
             Great Expectations / OpenLineage
                 Jena / Fuseki / Neo4j
                            │
                            ▼

                      INTELLIGENCE

                 Forecasting / ML
                  Causal Inference
                     PyMC
                    OR-Tools
                     MLflow
                            │
                            ▼

                 INTELLIGENT AUTOMATION

                    LangGraph
                  Policy-as-Code
                 Cloudflare D1
                            │
                            ▼

                       EXPERIENCE

                Superset / Dash / Grafana
```

---

# The canonical PPC world

Synthetic data is not generated independently inside each source system.

PPC first generates one internally coherent **canonical synthetic world**.

```text
Public observations
        ↓
Canonical PPC World
        ↓
 ┌──────┼────────┬────────┬─────────┐
 ▼      ▼        ▼        ▼         ▼
CRM    ERP    PostgreSQL  MySQL    SQLite
```

Each system receives a different representation of the same fictional enterprise.

Those representations intentionally contain realistic integration differences.

The integration platform must reconstruct the governed enterprise model.

The canonical world is used to validate the simulation. It must not be used as a hidden shortcut by integration pipelines.

---

# Data architecture

PPC follows:

```text
RAW
 ↓
SILVER
 ↓
GOLD
 ↓
SEMANTIC / CONSUMPTION
```

## Raw

Preserved source evidence and replay data.

## Silver

Cleaned and conformed enterprise facts and dimensions.

## Gold

Reusable business data products and derived analytical products.

## Semantic / Consumption

Approved interfaces for:

- BI;
- APIs;
- agents;
- applications;
- analytics.

Consumers should not depend directly on internal transformation structures.

---

# Data products

Initial PPC products include:

```text
Event

Market & Pricing

Asset & Reliability

Physical Movement & Logistics

Commercial Margin

Commercial Risk

Forecast Performance
```

Data products supply governed information to metrics, KPIs, analytical models and decisions.

---

# KPI Store

The KPI Store is PPC's authoritative store for governed performance results.

Initial KPI candidates include:

## Commercial

- Gasoline Netback CPG
- ULSD Netback CPG
- Margin Capture %

## Trading

- Trading P&L
- Optionality Capture

## Logistics

- OTIF
- Logistics Cost/Gallon
- Demurrage Cost

## Refining

- Refinery Utilization
- Unplanned Capacity Loss
- Yield Capture

## Planning

- Forecast Accuracy
- Inventory Days of Cover

## Risk

- Margin-at-Risk
- Position Exposure

A calculation does not become a KPI merely because it appears in a report.

---

# Meaning and operational context

PPC deliberately uses two graph models.

## Formal meaning

Apache Jena/Fuseki:

```text
RDF
RDFS
OWL
SHACL
SKOS
PROV-O
SPARQL
```

This layer answers:

> **What does this concept mean?**

## Operational knowledge graph

Neo4j Community:

```text
Event
  ↓
Asset
  ↓
Product
  ↓
Inventory
  ↓
Contract
  ↓
Customer
  ↓
KPI
```

This layer answers:

> **What is connected to this event right now?**

The two graphs have different responsibilities.

---

# Performance Intelligence

Performance Intelligence answers:

> **What happened, why did it happen, what may happen next, and which levers matter?**

PPC uses specialized analytical methods:

```text
Forecasting
→ StatsForecast / MLForecast

Predictive ML
→ scikit-learn / XGBoost / LightGBM

Causal inference
→ DoWhy / EconML

Uncertainty
→ PyMC

Optimization
→ OR-Tools

Model lifecycle
→ MLflow
```

LLMs do not replace these methods.

---

# Intelligent Automation

Intelligent Automation asks:

> **Given what happened and what is at risk, what approved action should occur?**

A typical workflow is:

```text
Event
 ↓
Exposure
 ↓
Performance impact
 ↓
Alternatives
 ↓
Optimization
 ↓
Policy check
 ↓
Recommend / Approve / Execute / Escalate
 ↓
Outcome
 ↓
Learning
```

Material actions remain subject to policy and human approval.

---

# AI and agents

PPC agents use governed tools.

```text
                    PPC AGENT
                        │
       ┌────────────────┼────────────────┐
       ▼                ▼                ▼
     Jena             Neo4j           DuckLake
    Meaning        Relationships        Facts
       │                │                │
       └────────────────┼────────────────┘
                        │
              Analytical Models
                        │
                    OR-Tools
                        │
                     Policy
                        │
                     Action
```

LangGraph manages stateful agent workflows.

Langfuse records agent traces and evaluations.

PostgreSQL/pgvector provides initial document and learning-case retrieval.

The LLM interprets and explains. It does not invent authoritative calculations.

---


# EPM dependency and process conformance

PPC consumes a versioned EPM dependency bundle: principles, business/process authority, semantic model, ontology/SHACL, measurement/KPI rules, data-product portfolio, KPI Store contract and competency questions.

PPC adopts:

> **Meaning does not compute.**

EPM defines designed business/process/performance meaning. PPC creates synthetic instances, executes governed calculations, and measures process conformance.

See `docs/PPC-017_EPM_Dependency_Semantic_Authority_and_Process_Conformance_Contract.md`.

# Evidence, decision provenance, and evaluation

PPC also implements the evidence and decision-provenance patterns defined by Enterprise Context Engineering.

The project separates:

- **data provenance** — where a value came from; and
- **epistemic status** — whether a claim is evidence, inference, contradiction, or unknown.

PPC keeps complete canonical simulation truth separate from the **agent-visible evidence world**. Blind evaluations must not expose hidden decision rationale, expected evidence sets, or scoring keys to the evaluated agent.

Material decisions use a decision dossier that records drivers, constraints, alternatives, selected/rejected options, authority, approval, expected outcome, actual outcome and known uncertainty.

See `docs/PPC-016_Evidence_Decision_Provenance_and_Evaluation_Architecture.md`.

# Enterprise evidence corpus

PPC generates an **Enterprise Evidence Corpus** of documents, messages, reports, approvals, policies, operational notes and learning artifacts, in addition to structured source-system data.

The corpus comes from the canonical PPC world, but each artifact shows only what its author role could know at that time. It includes controlled staleness, disagreement and uncertainty. Hidden truth stays isolated from evaluated agents.

See `docs/PPC-018_Enterprise_Evidence_Corpus_and_Unstructured_Data_Generation_Strategy.md`.

# User experiences

PPC deliberately separates three interfaces.

## Apache Superset

Enterprise BI, scorecards, KPI trends and governed analytical consumption.

## Plotly Dash

Operational Performance Intelligence, events, exposure graphs, scenarios, recommendations and approvals.

## Grafana OSS

Technical health, pipeline monitoring, latency, freshness and infrastructure alerts.

---

# First end-to-end scenario

The initial reference scenario is:

> **A Gulf Coast hurricane threatens PPC's refinery and logistics network while PADD 3 distillate inventory is seasonally tight.**

The system must demonstrate:

```text
Observed NOAA event
        ↓
PPC asset exposure
        ↓
Probabilistic capacity loss
        ↓
ULSD production impact
        ↓
Terminal inventory trajectory
        ↓
Customer commitment risk
        ↓
KPI / Margin-at-Risk
        ↓
Performance explanation
        ↓
Alternative actions
        ↓
Optimization
        ↓
Policy / Approval
        ↓
Action
        ↓
Outcome
        ↓
Learning
```

---

# Repository structure

The target repository structure is:

```text
pearland-petroleum-corporation/
├── README.md
├── AGENTS.md
├── docs/
├── architecture/
├── semantic/
│   ├── aml/
│   ├── ontology/
│   ├── shapes/
│   └── mappings/
├── schemas/
├── generators/
├── source-systems/
│   ├── crm/
│   ├── erp/
│   ├── commercial/
│   ├── logistics/
│   └── refinery/
├── integration/
│   ├── dagster/
│   ├── debezium/
│   ├── kafka/
│   └── workers/
├── lakehouse/
│   ├── ducklake/
│   └── databricks/
├── data-products/
├── kpi-store/
├── graph/
│   ├── rdf/
│   └── neo4j/
├── intelligence/
│   ├── forecasting/
│   ├── causal/
│   ├── probabilistic/
│   └── optimization/
├── automation/
├── apps/
│   ├── superset/
│   ├── dash/
│   └── grafana/
├── evaluations/
├── fixtures/
├── tests/
└── infra/
```

Large generated datasets, model artifacts and synthetic releases do not belong in Git.

They belong in the PPC Cloudflare R2 project bucket.

---

# Start here

If you are new to PPC:

1. Read `docs/PPC-000_Master_Index_and_Architecture_Guide.md`.
2. Read `docs/PPC-001_Problem_Statement_and_Simulation_Charter.md`.
3. Read `docs/PPC-015_Three_Repository_Operating_Model.md`.
4. Read `docs/PPC-REF-001_Technology_Roles_Interactions_and_Data_Flows.md`.
5. Review the EPM ontology release used by the current PPC release.
6. Review the Context Engineering contracts used by the current PPC release.
7. Read `docs/PPC-014_Implementation_Roadmap_and_Build_Runbook.md` before changing implementation code.

---

# Documentation

The PPC Architecture Baseline contains:

```text
PPC-000  Master Index and Architecture Guide
PPC-001  Problem Statement and Simulation Charter
PPC-002  Enterprise Architecture and Technology Stack
PPC-003  Business, Semantic and Domain Model
PPC-004  Data Modeling and Model-as-Code Standard
PPC-005  Synthetic Data Generation Strategy
PPC-006  Distributed Source Systems and Data Architecture
PPC-007  Data Integration, Event and Orchestration Architecture
PPC-008  Data Products, Medallion and KPI Store Architecture
PPC-009  Metadata, Governance, Quality and Observability
PPC-010  Ontology, Knowledge Graph and Policy Architecture
PPC-011  Performance Intelligence, ML and Causal Analytics
PPC-012  Intelligent Automation, Agent and User Experience
PPC-013  Cloudflare R2 Durability and Project Storage Standard
PPC-014  Implementation Roadmap and Build Runbook
PPC-015  Three-Repository Operating Model
PPC-016  Evidence, Decision Provenance and Evaluation Architecture
PPC-017  EPM Dependency, Semantic Authority and Process Conformance Contract
PPC-018  Enterprise Evidence Corpus and Unstructured Data Generation Strategy

PPC-REG-001  Architecture Decision Register
PPC-REG-002  Data Source and Integration Register
PPC-REG-003  KPI, Metric and Data Product Register

PPC-REF-001  Technology Roles, Interactions and Data Flows
```

---

# Source precedence

When sources conflict, use this order:

1. approved canonical EPM semantic artifact;
2. approved EPM decision or specification;
3. approved Enterprise Context Engineering contract;
4. approved PPC architecture decision;
5. current validated PPC implementation;
6. candidate PPC artifact;
7. current PPC working conversation;
8. prior or outside-project conversation;
9. unvalidated extracted source logic;
10. general industry assumption.

Public observations retain factual authority for the external observations they report.

They do not redefine governed EPM business semantics.

---

# Current status

PPC is currently in **architecture baseline / implementation preparation**.

The technology architecture and initial documentation baseline are defined.

The next major stage is implementation of **PPC World v0.1**.

---

# Governing principle

> **EPM defines what the downstream enterprise means.**

> **Enterprise Context Engineering defines how trustworthy enterprise context is assembled, grounded, and evaluated.**

> **PPC proves that both can operate together in a realistic, heterogeneous downstream enterprise.**
