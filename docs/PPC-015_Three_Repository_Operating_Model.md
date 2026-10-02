# PPC-015 --- Three-Repository Operating Model

**Baseline:** PPC Architecture Baseline v1.0\
**Purpose:** Define how `enterprise-performance-model`,
`enterprise-context-engineering`, and `pearland-petroleum-corporation`
work together without duplicating ownership or allowing semantic drift.

## Documentation standard

PPC uses an **ASD-STE100-inspired** technical writing style. PPC does
not claim formal ASD-STE100 compliance. Use consistent terms, direct
verbs, short sections, explicit relationships, and established technical
vocabulary when it improves precision.

------------------------------------------------------------------------

# 1. Executive Summary

The three repositories have different responsibilities.

-   **Enterprise Performance Model (EPM)** defines and validates the
    downstream enterprise model.
-   **Enterprise Context Engineering (ECE)** defines and validates the
    context, evidence, provenance, retrieval, and reasoning framework.
-   **Pearland Petroleum Corporation (PPC)** integrates both into a
    realistic fictional downstream enterprise and proves that the two
    architectures work together.

PPC is therefore not the source of truth for EPM meaning and is not the
source of truth for generic context-engineering patterns.

PPC is the **integrated enterprise implementation and proving ground**.

``` text
ENTERPRISE PERFORMANCE MODEL
Business/performance semantics
Ontology
KPI architecture
Data-product architecture
        |
        | publishes governed releases
        v

                PEARLAND PETROLEUM CORPORATION
                Integrated executable enterprise
                Synthetic downstream company
                Data + graph + KPIs + AI + automation
        ^
        | publishes reusable framework releases
        |
ENTERPRISE CONTEXT ENGINEERING
Evidence/provenance
Temporal context
Decision provenance
Retrieval/reasoning
Evaluation
```

------------------------------------------------------------------------

# 2. Repository Responsibilities

## 2.1 Enterprise Performance Model

Repository:

``` text
enterprise-performance-model
```

Primary question:

> **What does the downstream enterprise mean, and how should performance
> be represented?**

EPM owns the canonical downstream business and performance model.

Its scope includes:

-   business domains;
-   value streams;
-   value-stream stages;
-   capabilities;
-   sub-capabilities;
-   processes;
-   activities;
-   decisions;
-   business entities;
-   measurements;
-   metrics;
-   KPIs;
-   objectives;
-   targets and thresholds;
-   data-product semantics;
-   KPI Store architecture;
-   semantic definitions;
-   enterprise ontology;
-   SHACL constraints;
-   competency questions;
-   semantic validation;
-   ontology releases.

EPM remains executable.

It should contain code and tests that validate the model itself.

Examples:

``` text
validate_ontology.py
run_shacl.py
test_competency_questions.py
validate_kpi_metadata.py
build_epm_ontology_release.py
```

These functions make sense even if PPC does not exist.

------------------------------------------------------------------------

## 2.2 Enterprise Context Engineering

Repository:

``` text
enterprise-context-engineering
```

Primary question:

> **How can people and AI agents assemble trustworthy enterprise context
> from distributed evidence?**

ECE owns reusable context-engineering patterns.

Its scope includes:

-   evidence models;
-   claim-level provenance;
-   temporal validity;
-   evidence versus inference;
-   uncertainty and unknowns;
-   decision provenance;
-   source-to-answer traceability;
-   synthetic evidence generation;
-   hidden canonical truth;
-   visible evidence generation;
-   retrieval patterns;
-   grounding;
-   context graphs;
-   agent evaluation;
-   evidence evaluation;
-   context-release manifests;
-   reusable R2 workflow patterns.

ECE also remains executable.

Examples:

``` text
generate_canonical_truth.py
generate_evidence_artifacts.py
build_context_graph.py
evaluate_grounding.py
validate_provenance.py
publish_context_release.py
```

These functions must still make sense without PPC.

------------------------------------------------------------------------

## 2.3 Pearland Petroleum Corporation

Repository:

``` text
pearland-petroleum-corporation
```

Primary question:

> **Can EPM and Enterprise Context Engineering operate together in a
> realistic downstream enterprise?**

PPC owns the fictional enterprise implementation.

Its scope includes:

-   PPC source systems;
-   PPC synthetic master and transactional data;
-   CRM and ERP instances;
-   commercial/trading data;
-   logistics data;
-   refinery/edge data;
-   public-source conditioning;
-   integration pipelines;
-   CDC and event streaming;
-   DuckLake/Databricks analytical implementations;
-   PPC-specific data products;
-   KPI Store implementation;
-   PPC graph instances;
-   event-to-performance propagation;
-   Performance Intelligence;
-   causal models;
-   forecasting;
-   uncertainty;
-   optimization;
-   Intelligent Automation;
-   decision workflows;
-   agent workflows;
-   Superset/Dash/Grafana applications;
-   scenario simulations;
-   learning cases.

PPC is the **integration and execution environment**.

------------------------------------------------------------------------

# 3. The Dependency Direction

The dependency model is intentionally asymmetric.

``` text
enterprise-performance-model
            |
            | dependency
            v
pearland-petroleum-corporation


enterprise-context-engineering
            |
            | dependency
            v
pearland-petroleum-corporation
```

EPM does not require PPC to build or validate the EPM ontology.

ECE does not require PPC to build or validate provenance, retrieval, or
grounding patterns.

PPC requires both.

This prevents circular ownership.

------------------------------------------------------------------------

# 4. EPM as a Versioned Semantic Dependency

The EPM ontology is a first-class PPC dependency.

PPC should not copy the ontology and allow an independent version to
evolve.

EPM publishes versioned releases.

Example:

``` text
epm-ontology-v0.6.ttl
epm-shapes-v0.6.ttl
epm-semantic-model-v1.2
epm-kpi-architecture-v1.0
```

A PPC release records the versions it uses.

Example:

``` yaml
ppc_release: 0.1.0

dependencies:
  epm:
    ontology: 0.6
    shapes: 0.6
    semantic_model: 1.2
    kpi_architecture: 1.0
```

This makes the semantic dependency explicit and reproducible.

------------------------------------------------------------------------

# 5. Class Versus Instance

One of the most important repository boundaries is the distinction
between **enterprise meaning** and **enterprise instance data**.

EPM defines classes and semantic relationships.

Example:

``` text
epm:Refinery
epm:RefineryUnit
epm:Customer
epm:Shipment
epm:EnterpriseKPI
```

PPC creates instances of those concepts.

Example:

``` turtle
ppc:PearlandGulfCoastRefinery
    rdf:type epm:Refinery .

ppc:Hydrocracker01
    rdf:type epm:RefineryUnit .

ppc:CustomerABC
    rdf:type epm:Customer .
```

EPM answers:

> What is a refinery?

PPC answers:

> Which refinery does PPC operate in this scenario?

------------------------------------------------------------------------

# 6. PPC Extensions to EPM

PPC may discover concepts that do not yet exist in EPM.

Do not immediately modify EPM.

PPC can define a local extension first.

Example:

``` text
ppc:EmergencyInventoryTransfer
```

The project then asks:

> Is this concept specific to PPC, or is it a reusable downstream
> concept?

If PPC-specific, it remains a PPC extension.

If reusable:

``` text
PPC extension
    ↓
EPM change proposal
    ↓
EPM review
    ↓
approved EPM concept
    ↓
future EPM release
    ↓
PPC adopts new release
```

This creates a governed feedback loop without weakening semantic
ownership.

------------------------------------------------------------------------

# 7. Context Engineering as a Versioned Framework Dependency

ECE should also publish reusable contracts and patterns.

Examples:

``` text
context-provenance-model-v0.4
decision-dossier-schema-v0.3
evidence-item-schema-v0.5
context-evaluation-rubric-v0.2
r2-workflow-standard-v1.0
```

PPC records which versions it uses.

Example:

``` yaml
dependencies:
  context_engineering:
    provenance_model: 0.4
    decision_dossier: 0.3
    evidence_schema: 0.5
    evaluation_rubric: 0.2
```

PPC can then implement those contracts for downstream scenarios.

------------------------------------------------------------------------

# 8. Example: One PPC Decision Across All Three Repositories

Scenario:

A hurricane threatens PPC's Gulf Coast refinery. ULSD inventory cover
falls. PPC considers reducing exports.

## EPM contributes meaning

EPM defines:

``` text
Refinery
Refinery Unit
Product
Inventory
Customer
Contract
Shipment
Business Decision
Enterprise KPI
Commercial Margin
Data Product
```

It also defines relationships such as:

``` text
BusinessProcess realizes Capability
DataProduct supplies Metric
KPI evaluates Objective
Decision influences Outcome
```

## Context Engineering contributes decision context

ECE defines:

``` text
Decision
Alternative
Constraint
Evidence
Actor / Role
Approval
Rationale
Outcome
Confidence
Temporal validity
```

ECE also defines how evidence and inference are distinguished.

## PPC supplies the executable scenario

PPC creates:

``` text
Hurricane AL09
PPC Gulf Coast Refinery
Hydrocracker 01
Houston Terminal
ULSD
Customer ABC
Contract C8291
Decision D8271
```

The decision may be:

> Reduce ULSD export allocation by 40,000 barrels.

PPC calculates operational and commercial effects.

ECE structures the decision evidence and provenance.

EPM supplies the enterprise meaning.

------------------------------------------------------------------------

# 9. Three Types of Execution

Execution exists in all three repositories.

They execute different things.

## 9.1 EPM --- Specification Execution

Question:

> **Is the enterprise model valid?**

Examples:

-   ontology build;
-   RDF validation;
-   SHACL validation;
-   semantic consistency;
-   competency questions;
-   KPI metadata validation;
-   release packaging.

## 9.2 Context Engineering --- Framework Execution

Question:

> **Does the context architecture work?**

Examples:

-   canonical truth generation;
-   evidence generation;
-   provenance validation;
-   context graph construction;
-   retrieval;
-   grounding;
-   decision-rationale recovery;
-   evaluation.

## 9.3 PPC --- Enterprise Simulation Execution

Question:

> **Can the two architectures operate together in a realistic
> enterprise?**

Examples:

-   generate PPC world;
-   populate CRM/ERP/source databases;
-   integrate data;
-   calculate KPIs;
-   detect events;
-   analyze drivers;
-   estimate causal effects;
-   forecast;
-   optimize actions;
-   enforce policy;
-   capture decision provenance;
-   execute agent workflows;
-   evaluate outcomes.

------------------------------------------------------------------------

# 10. Where New Code Should Go

Use this rule:

> **If the code still makes sense without Pearland Petroleum
> Corporation, it probably belongs upstream.**

## EPM examples

``` text
validate_ontology.py
run_shacl.py
validate_kpi_semantics.py
build_epm_release.py
```

## Context Engineering examples

``` text
evidence_manifest.py
decision_dossier.py
claim_provenance.py
evaluate_grounding.py
```

## PPC examples

``` text
generate_ppc_world.py
materialize_ppc_postgres.py
materialize_ppc_mysql.py
simulate_ppc_hurricane.py
calculate_ppc_margin.py
optimize_ppc_inventory.py
```

If a reusable PPC utility becomes generic, promote it upstream through
an explicit change proposal.

------------------------------------------------------------------------

# 11. What Stays in the EPM Homelab

Do not move every experiment into PPC.

The EPM Homelab remains useful for isolated learning and semantic
experimentation.

Examples:

-   learning RDF;
-   testing Fuseki;
-   experimenting with ontology queries;
-   validating a small KPI model;
-   teaching Meaning versus Compute.

PPC is for **integrated enterprise execution**.

The Homelab is for **focused learning and experimentation**.

The same rule applies to small EPM O2C demos. A compact teaching/demo
implementation can remain in EPM even if PPC contains a larger O2C
implementation.

------------------------------------------------------------------------

# 12. What Stays in Context Engineering

Context Engineering should retain generic scenarios and evaluation
fixtures that do not require the PPC domain.

Examples:

-   provenance tests;
-   evidence-versus-inference tests;
-   temporal contradiction scenarios;
-   missing-evidence scenarios;
-   decision-rationale reconstruction;
-   generic hidden-truth evaluation.

PPC can also contribute downstream-specific test cases, but those remain
PPC artifacts unless generalized.

------------------------------------------------------------------------

# 13. Source Precedence in PPC

When PPC sources conflict, use explicit precedence.

Recommended order:

1.  approved EPM canonical semantic artifact;
2.  approved EPM decision / specification;
3.  approved ECE framework contract;
4.  approved PPC architecture decision;
5.  current validated PPC implementation;
6.  candidate PPC artifact;
7.  working PPC conversation;
8.  prior/outside conversation;
9.  unvalidated extracted source logic;
10. general industry assumption.

Public observed data has factual authority for the external observations
it reports, but it does not override governed EPM semantic definitions.

------------------------------------------------------------------------

# 14. Release Manifest

Every PPC release should record upstream dependencies.

Example:

``` yaml
project: pearland-petroleum-corporation
release: 0.1.0

epm:
  ontology: 0.6
  shapes: 0.6
  business_architecture: 1.1
  kpi_architecture: 1.0

context_engineering:
  provenance_model: 0.4
  decision_model: 0.3
  evidence_schema: 0.5
  evaluation_rubric: 0.2

ppc:
  world_version: 0.1
  generator_version: 0.1.0
  architecture_baseline: 1.0
```

This creates repeatability across repository evolution.

------------------------------------------------------------------------

# 15. Upstream Change Process

PPC is a proving ground, so it will find gaps.

When PPC finds an EPM semantic gap:

``` text
PPC issue/proposal
→ EPM review
→ EPM ADR/change
→ EPM release
→ PPC dependency update
```

When PPC finds a context-engineering framework gap:

``` text
PPC issue/proposal
→ ECE review
→ reusable pattern/schema/evaluation change
→ ECE release
→ PPC dependency update
```

Do not silently patch upstream concepts only inside PPC.

------------------------------------------------------------------------

# 16. Recommended Repository Relationship

``` text
enterprise-performance-model/
    publishes/
      ontology/
      semantic contracts/
      KPI architecture/
      data-product architecture/

enterprise-context-engineering/
    publishes/
      evidence contracts/
      provenance contracts/
      context/retrieval patterns/
      evaluation contracts/

pearland-petroleum-corporation/
    depends-on/
      EPM releases
      ECE releases

    implements/
      source systems
      integrations
      analytical platform
      knowledge graphs
      Performance Intelligence
      Intelligent Automation
      agents
      user experiences
```

------------------------------------------------------------------------

# 17. Final Operating Principle

The relationship among the repositories can be summarized in three
sentences.

> **EPM defines what the downstream enterprise means.**

> **Enterprise Context Engineering defines how trustworthy enterprise
> context is assembled, grounded, and evaluated.**

> **PPC proves that both can operate together in a realistic,
> heterogeneous downstream enterprise.**

That is the architectural boundary to preserve as all three repositories
evolve.

## 18. Evidence and evaluation dependency from ECE
PPC treats ECE evidence/provenance/evaluation contracts as versioned upstream dependencies, just as EPM ontology/performance semantics are upstream dependencies.

Record versions for evidence-item schema, source-assertion/claim model, decision-dossier schema, provenance model, temporal-context model, evaluation rubric and hidden-truth isolation rules. PPC specializes these contracts but does not fork their generic meaning. Reusable improvements discovered in PPC should be proposed upstream to ECE, released there, then adopted by PPC.

## 19. EPM release dependency is broader than ontology
PPC's EPM dependency includes principles, business/process authority, semantic model, ontology/SHACL, measurement/KPI model, data-product portfolio, KPI Store contract and competency questions. PPC records upstream authority/maturity and does not silently promote drafts. EPM defines designed processes; PPC executes instances and measures conformance.
