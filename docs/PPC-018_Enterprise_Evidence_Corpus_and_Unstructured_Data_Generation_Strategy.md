# PPC-018 — Enterprise Evidence Corpus and Unstructured Data Generation Strategy

**Baseline:** PPC Architecture Baseline v1.3  
**Purpose:** Define how PPC generates a realistic enterprise information environment of documents, messages, reports, approvals, policies, operational notes, and learning artifacts from the canonical synthetic world.  
**Upstream dependency:** Enterprise Context Engineering (ECE) provides reusable evidence, provenance, temporal-context, and evaluation patterns.  
**Related PPC artifacts:** PPC-005, PPC-006, PPC-010, PPC-012, PPC-013, PPC-014, PPC-016, PPC-017.

## Documentation standard

PPC uses an **ASD-STE100-inspired** technical writing style. PPC does not claim formal ASD-STE100 compliance.

# 1. Purpose

A realistic enterprise does not communicate only through database rows. People make decisions using operational applications, reports, emails, chat messages, meeting notes, planning decks, policies, procedures, approvals, spreadsheets, incident reports, shift handovers, model outputs, assumptions, and retrospectives.

PPC therefore generates an **Enterprise Evidence Corpus** in addition to structured source-system data.

The corpus is consistent with the canonical PPC world, but it does not expose complete canonical truth.

> Different people know different things at different times, through different sources, with different levels of confidence.

# 2. Relationship to the canonical PPC world

```text
                    CANONICAL PPC WORLD
                  Complete simulation truth
                           |
          +----------------+----------------+
          |                                 |
          v                                 v
 STRUCTURED REPRESENTATIONS          UNSTRUCTURED EVIDENCE
 Twenty / ERPNext                    Emails / chat
 PostgreSQL / MySQL                  Meeting notes
 SQLite / APIs                       Planning decks
 DuckLake / KPI Store                Policies / approvals
          |                          Incident / learning
          +---------------+-----------------+
                          |
                          v
                 AGENT-VISIBLE WORLD
```

Canonical truth determines what actually happened. The evidence corpus determines what an actor or evaluated agent could reasonably know.

# 3. Three layers

**Canonical simulation truth:** complete state for generation, reconciliation, validation, scoring and counterfactuals.  
**Enterprise evidence world:** realistic records and communications, including estimates, stale information, partial information, disagreement and superseded information.  
**Agent-visible world:** the subset available under role, time, security, publication and evaluation rules.

# 4. Artifact families

| Family | Examples | Typical roles |
|---|---|---|
| Operational | shift handover, outage notice, terminal status | operators, supervisors |
| Maintenance/Reliability | work summary, repair estimate | maintenance, reliability |
| Commercial/Trading | trader email, position/pricing note | traders, commercial |
| Logistics | nomination, scheduler note, delay notice | schedulers, logistics |
| Planning | demand forecast, supply plan, inventory outlook, scenario deck | planners |
| Risk | exposure report, limit alert, Margin-at-Risk analysis | risk |
| Finance/O2C | credit review, invoice/collection/dispute note | finance, credit |
| Management | daily review, KPI scorecard, executive deck | management |
| Decision | recommendation, alternatives analysis, approval | decision owner/approver |
| Governance | policy, procedure, authority matrix | governance |
| Data/Technology | DQ incident, pipeline notice, product-health report | data/technology |
| Outcome | execution confirmation, result/variance report | operations/commercial |
| Learning | retrospective, RCA, lessons learned, training case | cross-functional/L&D |

# 5. Role and persona model

Initial personas include refinery operator, operations supervisor, maintenance engineer, reliability engineer, supply planner, product/pipeline scheduler, logistics coordinator, physical trader, pricing analyst, commercial manager, market analyst, risk analyst/manager, customer-service analyst, credit analyst, finance/AR analyst, data-product owner, data steward, data engineer, and executive leader.

A role controls vocabulary, business concerns, system visibility, detail level, artifact types, decision authority, and knowledge at a point in time.

# 6. Knowledge-state model

```text
KnowledgeState(actor, t)
=
Available evidence
+ Role access
+ Prior communications
+ Current assumptions
+ Model outputs available at t
- Information not yet published
```

Document generation receives the actor's knowledge state, not unrestricted canonical truth.

# 7. Artifact metadata

Each governed artifact records, where applicable:

```yaml
artifact_id:
artifact_family:
artifact_type:
title:
author_role:
author_actor_id:
business_domain:
created_at:
effective_at:
available_at:
ingested_at:
valid_from:
valid_to:
superseded_by:
confidentiality:
scenario_id:
decision_ids:
event_ids:
entity_links:
  customer_ids:
  contract_ids:
  shipment_ids:
  asset_ids:
  product_ids:
  location_ids:
  kpi_ids:
provenance:
  generation_method:
  generator_version:
  world_version:
  source_inputs:
  seed:
knowledge_state:
  known_facts:
  assumptions:
  estimates:
  unknowns:
```

# 8. Source assertions

Artifacts contain material **SourceAssertions** with precise locators where practical.

Examples:

- email E-1004, paragraph 2: repair estimate 24–48 hours;
- planning deck P-209, slide 6/table row Houston: inventory cover 1.9 days;
- policy POL-INV-007, section 4.2: transfer approval threshold.

Claims should resolve to the smallest practical source assertion.

# 9. Structured-to-unstructured generation

Generated documents originate from the same world as structured systems.

```text
SQLite: Hydrocracker availability = 65%
        ↓
Operations update: "approximately 65% of normal rate"
        ↓
Maintenance note: "24–48 hour repair window"
        ↓
Planning deck: "base case assumes 70% through tomorrow"
```

Representations differ because roles, timing, assumptions and purpose differ.

# 10. Controlled imperfection

The canonical world remains coherent. The evidence world intentionally includes:

- partial evidence;
- stale evidence;
- legitimate disagreement;
- uncertainty/ranges;
- superseded information;
- controlled manual or interpretation errors.

Controlled errors are recorded in hidden truth.

# 11. Progressive knowledge

```text
08:00  Possible hydrocracker problem
08:20  Rate reduced
08:45  Repair estimate 24–48 hours
10:15  Replacement part required
14:30  Minimum 48-hour outage
D+1    Restart revised
D+3    Unit restored
D+7    Root-cause review
```

An answer about 09:00 cannot use D+1 information.

# 12. Contradiction model

Classify contradictions as temporal, model, role/perspective, data, policy, or human disagreement. Hidden truth records whether disagreement is intentional and whether a correct resolution exists.

# 13. Hurricane evidence timeline

A rich scenario can generate:

```text
07:45 NOAA advisory
07:52 Operations control-room update
08:01 Refinery availability snapshot
08:05 Trader email
08:09 Scheduler chat
08:12 Inventory report
08:15 Supply optimization meeting
08:18 Meeting notes
08:22 Commercial exposure analysis
08:25 Planning deck
08:31 Margin-at-Risk model output
08:37 Recommendation memo
08:42 Commercial Manager approval
09:03 Execution confirmation
11:00 Updated inventory forecast
16:00 Daily commercial review
D+1   Outcome report
D+7   Performance retrospective
D+30  Learning case
```

# 14. Perspective differences

Trader communications emphasize market structure, basis, replacement barrels and optionality. Maintenance emphasizes diagnosis, parts and repair uncertainty. Schedulers emphasize nominations, inventory and movement timing. Risk emphasizes scenarios, limits and uncertainty. Executives emphasize material KPI impact, decisions, ownership and action.

# 15. Templates and language generation

Use templates for stable structures such as policies, approvals, shift handovers, KPI reviews, incidents, decision memos and model summaries.

Use controlled language generation for emails, chat, meeting notes, commentary and retrospectives.

The language generator receives only actor-visible knowledge.

# 16. Artifact formats

PPC can generate Markdown, TXT, JSON, CSV, HTML, PDF, DOCX, PPTX, XLSX, email-like EML/normalized message JSON, and chat/event JSON. Native formats are useful when parsing/layout is part of the test. Keep normalized text for validation.

# 17. Entity linking

Artifacts link to known enterprise identifiers such as customer, contract, trade, shipment, invoice, asset, refinery unit, terminal, product, decision, event, KPI and data-product IDs. Do not rely only on names in text.

# 18. Evidence graph integration

```text
Artifact -MENTIONS-> Entity
Artifact -ABOUT_EVENT-> Event
SourceAssertion -LOCATED_IN-> Artifact
Claim -SUPPORTED_BY-> SourceAssertion
Decision -SUPPORTED_BY-> EvidenceItem
Decision -CONSIDERED-> DecisionOption
Decision -APPROVED_BY-> Role
Decision -RESULTED_IN-> Outcome
```

Neo4j stores operational relationships/locators. R2 stores durable native artifacts. Jena formalizes selected semantics.

# 19. R2 storage model

Recommended prefixes:

```text
raw/documents/
raw/messages/
cache/documents/normalized/
cache/evidence/
cache/source-assertions/
cache/decision-dossiers/
cache/graph/
evaluation/development/
evaluation/hidden/
manifests/corpus/
manifests/scenarios/
```

ECE and PPC use separate project buckets.

# 20. Corpus manifest

Each corpus release records corpus/world/generator versions, scenario set, EPM dependency, ECE contract version, seed, artifact counts by family, source-assertion count, decision count, contradiction/unknown counts, time range, checksums and hidden-evaluation version.

# 21. Retrieval architecture

Do not flatten all evidence into one vector index.

```text
Question
  +--> structured facts --> DuckLake / KPI Store
  +--> relationships -----> Neo4j
  +--> formal meaning ----> Jena
  +--> documents ---------> pgvector/document retrieval
  +--> catalog/lineage ---> OpenMetadata
```

Vector similarity does not establish evidence authority.

# 22. Hidden evaluation truth

Hidden evaluation can include canonical rationale, expected artifacts/assertions, known contradictions/unknowns, correct temporal cutoff, expected alternatives/policy outcome and simulated actual outcome.

Evaluated agents must not access hidden prefixes or hidden tables.

# 23. Corpus quality rules

Validate structural quality, temporal ordering, semantic/entity links, provenance, hidden-truth isolation, persona plausibility, role-appropriate knowledge, controlled uncertainty and non-duplicative narrative.

Hard temporal rule: evidence cannot support a decision before `available_at`.

# 24. Evaluation cases

Examples:

- Which evidence supported the 08:42 transfer approval?
- What did the Commercial Manager know at 08:35?
- Operations and Planning disagree about availability. What are both values and which is newer?
- What was the exact mechanical root cause at 08:15? Expected: `UNKNOWN` if not yet diagnosed.
- Why reduce export allocation rather than buy all replacement supply in the spot market?

# 25. Learning artifacts

```text
Decision
  ↓
Action
  ↓
Outcome
  ↓
Variance from expectation
  ↓
Retrospective
  ↓
Root-cause analysis
  ↓
Learning case
  ↓
Policy/model/process update candidate
```

A retrospective distinguishes what was known at decision time from later knowledge.

# 26. Relationship to EPM process conformance

EPM defines designed processes. PPC structured events and unstructured evidence document actual execution and human response. This lets PPC explain both the process deviation and how people understood/responded to it.

# 27. Relationship to ECE

ECE owns reusable Artifact, EvidenceItem, SourceAssertion, Claim, DecisionDossier, temporal-context, epistemic-status and hidden-evaluation patterns. PPC specializes them with downstream personas, systems, processes, KPIs, events and scenarios.

Reusable improvements flow upstream to ECE rather than creating incompatible PPC definitions.

# 28. Implementation sequence

1. Freeze ECE evidence contract version.
2. Define PPC artifact taxonomy and personas.
3. Define artifact metadata/source-assertion schemas.
4. Add knowledge-state calculation.
5. Build structured-to-unstructured generators.
6. Add controlled staleness/contradiction/unknown generation.
7. Add native-format renderers.
8. Persist artifacts/manifests in R2.
9. Build entity/source-assertion graph.
10. Build development retrieval corpus.
11. Create access-isolated hidden evaluation corpus.
12. Add temporal/provenance/narrative quality gates.
13. Add decision-rationale and contradiction evaluations.
14. Generate retrospective and learning artifacts after scenario completion.

# Governing principle

> **PPC does not generate documents to decorate the simulation. It generates an evidence environment that reproduces how enterprise knowledge is created, delayed, interpreted, contradicted, superseded, and used in decisions.**
