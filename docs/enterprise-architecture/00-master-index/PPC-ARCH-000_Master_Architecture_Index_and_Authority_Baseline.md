# PPC-ARCH-000 — Master Architecture Index and Authority Baseline

| Document control | Value |
|---|---|
| Artifact ID | `PPC-ARCH-000` (registered in §5; draft for review) |
| Version | `0.1.0-draft` |
| Status | **Draft for owner review and independent challenge**; not an approved architecture baseline |
| Prepared | 2026-11-25 |
| Target repository | `aadehamid/pearland-petroleum-corporation` |
| Proposed target path | `docs/enterprise-architecture/00-master-index/PPC-ARCH-000_Master_Architecture_Index_and_Authority_Baseline.md` |
| Source PPC revision | `01027a84be5d453cbb4e2ea091e4884729918b15` (`main`, inspected) |
| Primary purpose | Preserve the existing PPC architecture and establish a controlled, traceable index for a proposed, more detailed enterprise-world architecture before implementation |
| Change authority | PPC project owner; approval required before treating candidate choices as binding |
| Scope exclusion | Does not implement systems, approve external ontologies, alter upstream repositories, resolve contested architecture choices, or certify runtime behavior |

> **Reading rule:** This document is an integration and navigation artifact, not a replacement for the existing `docs/PPC-000`–`PPC-019` documents or `PPC-REG-001`. Existing approved decisions remain authoritative until changed through controlled ADRs. Proposed additions below are *candidates* unless specifically identified otherwise.

## 1. Executive intent and project boundary

Pearland Petroleum Corporation (PPC) is a **fictional** downstream oil-and-gas enterprise laboratory designed to connect real public observations with explicitly synthetic operational, commercial, engineering, analytical, and decision records. Its central question, established in the PPC README, is: *An event occurred. What changed, what performance is at risk, why, what should PPC do, and what can PPC learn from the outcome?*

The architecture must support a reproducible chain from **world event → source observations and transactions → integration and reconciliation → governed enterprise information → performance calculations → evidence-backed investigation → bounded proposed or approved actions → observed simulated outcome**. Neither the graph nor an LLM independently determines physical consequences or authoritative KPI values.

The currently documented PPC World v0.1 charter encompasses one fictional Gulf Coast refinery (with simplified CDU, FCC, and hydrocracker), three terminals, logistics, customers, trading, inventory, commercial commitments, and financial records. A smaller first vertical slice is an **implementation increment within that charter**, not an unapproved scope reduction. The existing hurricane demonstration remains in the portfolio; the compressor-derate and crude-quality-rejection scenarios described in the current architecture discussions are **proposed first implementation and verification slices**, subject to roadmap reconciliation.

### 1.1 Objectives

1. Preserve the pre-existing PPC design intent, decisions, and architectural rationale, including superseded alternatives and their history.
2. Make authority explicit: distinguish simulated physical truth, original source records, evidence, semantics, governed calculations, and operational decisions.
3. Avoid creating competing ontologies, KPI definitions, or reusable engineering/context frameworks in PPC.
4. Produce complete, versioned interface and equation specifications that can be independently tested and reused by an implementation agent.
5. Make hypothetical scenario impacts distinguishable from actual graph connectivity, measured effects, and real-world causal claims.
6. Publish a **review baseline first**, then receive independent architecture challenge and resolve findings **before** Phase 0 implementation authorization.

### 1.2 Non-goals

- Connecting to, controlling, or asserting authority over any real production OT equipment.
- Claiming engineering feasibility or regulatory suitability for real facilities from a synthetic reduced-order model.
- Treating KPI Store 1.2's environment-specific installations as automatically compatible with PPC's runtime.
- Declaring `ds-business-process/1.0` generalized or released before its separate owner approves and verifies it.
- Replacing the existing PPC ADR register without owner approval.
- Making a graph traversal, generated narrative, or ontology class into an authoritative quantitative calculation.

## 2. Source baseline and reproducibility

The following source revisions were inspected through the connected GitHub repository interface. These are **Git commit identities**, not claims that a release is business-approved. Use immutable commit-qualified file links to repeat a particular review. Recheck revisions before publishing this document if branches have advanced.

| Source | Branch and inspected commit | Source role | Review constraint |
|---|---|---|---|
| [PPC](https://github.com/aadehamid/pearland-petroleum-corporation) | `main` @ [`01027a84`](https://github.com/aadehamid/pearland-petroleum-corporation/commit/01027a84be5d453cbb4e2ea091e4884729918b15) | Existing charter, architecture documents, decisions; fictional-world implementation owner | No code/runtime qualification established by the file inspection |
| [EPM](https://github.com/aadehamid/enterprise-performance-model) | `main` @ [`511a9e8d`](https://github.com/aadehamid/enterprise-performance-model/commit/511a9e8db4008ef43a0dda0f92cef17664e4c995) | Performance meaning, module architecture, competency questions, KPI/data-product semantics, examples | Check per-module approval/release, not just `main` |
| [Downstream ontology release](https://github.com/aadehamid/downstream_oil_and_gas_ontology_release) | `kpi-store/1.2` @ [`ddf6b68b`](https://github.com/aadehamid/downstream_oil_and_gas_ontology_release/commit/ddf6b68b614c8ae5cdaeb935fe435562bf2678d0) | Current specific ontology and implementation/release baseline | Distinguish tested rehearsal behavior from unqualified target deployment |
| Same downstream ontology repository | `ds-business-process/1.0` @ `ddf6b68b` at inspection | **Placeholder branch for future generalization** | At inspection, the two branches point to **the same commit**; this does **not** establish a completed generalized release |
| [SCADA Harmonization / proposed ICE role](https://github.com/aadehamid/scada_harmonization) | `main` @ [`1467e927`](https://github.com/aadehamid/scada_harmonization/commit/1467e9278a9fa50d80618a296297eb40cd4416c2) | L0 data contracts and evolving OT harmonization | Do not assume mapping layer or Sparkplug publication is complete |
| [Engineering Drawing to Graph / EDI](https://github.com/aadehamid/Engineering_Drawing_to_Graph) | `main` @ [`12a4a6a6`](https://github.com/aadehamid/Engineering_Drawing_to_Graph/commit/12a4a6a6f715c7db76a26d763cb1938d6cf0cc05) | Engineering object/revision contracts and bounded structured graph pipeline | Distinguish implemented structured slice from planned drawing-extraction/recovery qualification |
| [Enterprise Context Engineering / ECE](https://github.com/aadehamid/enterprise-context-engineering) | `main` @ [`750b398b`](https://github.com/aadehamid/enterprise-context-engineering/commit/750b398b6a50aedd552a72056d09cf1ccf6a296a) | Evidence, provenance, temporal decision context and evaluation patterns | Reusable schema package has not been established as published |

**Evidence classes:** `SOURCE_OBSERVED` = a repository artifact or explicit status statement was inspected; `DESIGN_PROPOSED` = described in our architecture discussions or this blueprint; `TEST_REPORTED` = project documentation states a test ran, but it was not independently rerun here; `QUALIFIED` = requires separately recorded environment, test, and approval evidence. These are architecture-evidence classes, separate from the value classes `OBSERVED`, `DERIVED`, `ESTIMATED`, `SYNTHETIC` and `SCENARIO_ASSUMPTION` in the PPC README. The illustrative manifest's seed and scenario fields describe proposed synthetic fixtures, not observed operating values. No software tests or operational acceptance suites were executed while preparing this draft.

### 2.1 Source precedence and conflict handling

The [README source-precedence order](../../../README.md#source-precedence) is controlling when sources conflict. The domain notes below identify the subject of a claim; they do not reorder the ten levels. ICE, EDI and `DS_Business_Process` enter that order by their actual approval and artifact status, not by repository name. Pending specialist releases cannot displace approved EPM semantics or PPC ADRs.

1. **Source authority is domain-specific.** The PPC charter governs the fictional project; `PPC-REG-001` governs existing PPC ADR history; EPM release/decision artifacts govern performance semantics; the eventual approved `DS_Business_Process` release will govern generic downstream business-process concepts; ECE/ICE/EDI govern their reusable specialist contracts within their documented scope.
2. For a claim about a repository's **current progress**, prefer its designated current status/handoff and the code/test evidence over a stale high-level README. Example: Engineering Drawing to Graph's README describes documentation-first status while its later runbook reports completed bounded structured pipelines; reconcile rather than erase the discrepancy.
3. A newer architecture **proposal** never automatically supersedes an existing PPC ADR. Record conflict, alternatives, decision owner, evidence, and resolution first.
4. A branch, file path, draft or README description is not sufficient proof of approval, successful execution, or production qualification.
5. When sources disagree, retain both original claims and open a traceable discrepancy. Do not silently prefer recency or merge incompatible terminology.
6. Source changes after the pinned review baseline require a delta review before merging a revised document package.

## 3. Authority and responsibility model

| Domain | Normative authority (current or intended) | PPC responsibility | Must not be conflated with |
|---|---|---|---|
| General downstream business-process definitions | **Future approved** `DS_Business_Process` release; `kpi-store/1.2` is its current starting reference | Use pinned approved generalized concepts; map PPC process instances and preserve provisional mapping status | A completed generalized ontology today |
| Enterprise performance semantics | Approved EPM modules/decisions and KPI-store contract | Governed calculations and PPC instances; conform to EPM KPI/data-product definitions | EPM as the store of PPC's operational values |
| Formal semantic source | Released Turtle, shapes, manifests and approved module authority | Verify IRIs and mappings; create approved PPC-specific extensions | Neo4j property-graph projection as original semantic SoT |
| Physical world truth | PPC canonical simulator and physical-model configuration | Stable world state, deterministic transitions, scenario branches, conservation/constraints | What individual applications recorded or knew |
| Operational source records | Each simulated source application for its recorded lifecycle | Generate/reconcile source-consistent transactions and histories | Hidden simulator truth substituted for source evidence |
| Industrial observations | ICE reusable Level-0 and future normalization contracts; actual PPC source measurements | Bind instrument/tag/observable quantity to PPC assets, preserving source time and quality | A historian reading as proof of equipment's complete physical state |
| Engineering topology | EDI reusable extraction, revision and publication contracts; PPC-approved engineering configuration | Adopt engineering snapshot explicitly into a world version | Extracted drawing assertion as automatic authorization to change the world |
| Evidence and historical decision context | ECE reusable provenance/temporal/evaluation contracts when published | PPC-specific claims, documents, decisions and access restrictions | A later outcome used as evidence available at an earlier decision |
| Enterprise instance graph | PPC's governed source-informed projection | Stable IDs, temporal associations, scenario-qualified graph snapshots | Source of physical calculations or an unrestricted graph of all truth |
| Analytics and optimization | Qualified PPC numerical/optimization models; EPM defines meaning | Compute forecasts, opportunity, constraints, KPIs and quantified impact | Cypher traversal, ontology semantics or LLM prose as computation |
| Consequential actions | PPC application policy + authorized human/role | Check exact action, preconditions, approval, idempotency and audit | Model recommendation as authorization |
| Storage/catalog | Operational source systems, PPC data products, EPM contracts; R2 durable objects | Define which data is authoritative by lifecycle and release | R2 as universal transactional database |

**Architecture direction:** `DS_Business_Process → EPM process/performance alignment → PPC instance application` is a **semantic dependency**, not a mandated synchronous runtime hop. ICE, EDI, and ECE remain independent specialist contract owners and may be mapped into PPC without calling EPM for every observation or engineering revision.

### 3.1 Shared contract owners

The linked section owns each proposed PPC rule. A consumer uses that rule at its own boundary and records its release and version. These drafts do not replace an approved upstream contract.

| Shared rule | Proposed PPC owner | Consumers |
|---|---|---|
| Publication identity, source-record and recipient availability times, historical grants, supersession order and reader-as-of cutoff | [INFO-001 §3](../03-enterprise-information/PPC-INFO-001_Enterprise_Ontology_Identity_and_Time.md) | Identity, source events, evidence, graph, data products, workspace, tools and verification |
| Evidence IDs, revision locators, claims and dossier fields | [EVID-001 §2](../04-source-integration/PPC-EVID-001_Evidence_and_Decision_Context.md), under PPC-016 and future ECE release | Retrieval, agents, workspace and historical evaluation |
| Proposal, authorization, decision and execution states | [AGENT-001 §1](../05-intelligence-experience/PPC-AGENT-001_Agent_Tools_and_Consequential_Actions.md), under PPC-012 | Decision dossier, consequential tools and verification |
| Product values, KPI bindings and release manifest | [DATA-001 §2](../03-enterprise-information/PPC-DATA-001_Data_Products_KPIs_and_Analytical_Releases.md), using approved EPM definitions | Graph, analytics, workspace and agents |
| Verification stages and signed qualification | [VERIFY-001 §1](../07-scenarios-verification/PPC-VERIFY-001_Verification_and_Release_Qualification.md) | Golden scenarios, model runs and release gates |
| Scenario A observation schedule and the separate delayed OT observation | [WORLD-002 §6](../01-enterprise-world/PPC-WORLD-002_Simulation_Time_Replay_and_Branches.md) and [OT-001 §4](../02-industrial-engineering/PPC-OT-001_Industrial_Information_Architecture.md), respectively | SCENARIO-001, WORLD-001 and OT-04 |

### 3.2 Distinct identity domains

Do not collapse these identities: physical asset; functional position; installed equipment; engineering object; drawing symbol/appearance; tag assignment; observation/measurement; source-system record; business entity; KPI definition; KPI value; scenario branch; decision dossier; evidence artifact; ontology class IRI. Define mapping authority, validity interval, recorded/knowledge time, source lineage, and permissible cardinality at each boundary.

## 4. Existing PPC baseline: preservation and navigation

`PPC-000` through `PPC-019`, `PPC-REG-001` through `PPC-REG-003`, and `PPC-REF-001` are the existing foundational documents and registers/reference materials. **None is declared superseded by this draft.** Proposed disposition here means a future review or supplemental specification, not an instruction to overwrite a source document.

| Existing ID | Current primary subject | Draft disposition / linkage |
|---|---|---|
| PPC-000 | Architecture master index | Retain; add navigation to new supplemental package after approval |
| PPC-001 | Problem statement, simulation charter, scope | Retain; document proposed first-slice order without changing charter |
| PPC-002 | Enterprise stack, responsibilities, boundaries | Reassess technology-dependent selections through ADRs; no automatic change |
| PPC-003 | Business, semantic and domain model | Retain; align future DS_Business_Process precedence explicitly |
| PPC-004 | Conceptual/logical/physical modeling, AML/Azimutt | Retain; specify ontology, engineering and API-schema boundaries |
| PPC-005 | Synthetic world generation and high-level constraints | Extend through WORLD-001, WORLD-002 and ENG-001 |
| PPC-006 | Source systems, ownership, identity and medallion | Extend through INT-001 and INFO-001 |
| PPC-007 | Integration patterns and event transport | Reassess Kafka/NATS; define reliability contracts in INT-001 |
| PPC-008 | Data products, KPI Store, medallion | Extend through DATA-001 with EPM lineage and release semantics |
| PPC-009 | Metadata, DQ, lineage, observability | Extend through PLATFORM-001 and VERIFY-001 |
| PPC-010 | Ontology, operational graph, policy | Extend through INFO-001 and GRAPH-001 |
| PPC-011 | Performance intelligence, causal/ML/optimization | Extend through ENG-001 and ANALYTICS-001 |
| PPC-012 | Agents, automation and UX | Reassess tool options; extend through AGENT-001 and UX-001 |
| PPC-013 | R2 durability, raw/replay/manifests | Retain; specify consistency, isolation, recovery and selected table format |
| PPC-014 | Original phased roadmap/runbook | Retain as existing roadmap; reconcile proposed vertical-slice implementation order in PLAN-001 |
| PPC-015 | EPM–ECE–PPC operating model | Retain; extend specialist ownership of ICE/EDI and proposed DS_Business_Process |
| PPC-016 | Evidence, claim provenance, hidden truth | Retain; add versioned executable contract tests in EVID-001 |
| PPC-017 | EPM semantic dependency and conformance | Retain; add future independent DS_Business_Process dependency and compatibility policy |
| PPC-018 | Enterprise evidence corpus | Retain; extend golden scenario templates and time-cutoff fixtures |
| PPC-019 | Public ontology reuse candidates and mapping rules | Retain as **proposed ontology candidates**, not automatic adopted dependencies; note generalized process priority |
| PPC-REG-001 | ADR-001 to ADR-039 | Preserve verbatim until approved amendments/decisions are made |
| PPC-REG-002 | Source and integration inventory | Retain as the existing source/integration register; reconcile future INT-001 specifications without superseding it |
| PPC-REG-003 | KPI and data-product inventory | Retain as the existing KPI/data-product register; align future DATA-001 and EPM mappings without superseding it |
| PPC-REF-001 | Reference explaining what each tool does | Retain as the existing tool reference; distinguish documented tools from proposed technology alternatives |

Original documentation URLs follow `https://github.com/aadehamid/pearland-petroleum-corporation/blob/01027a84be5d453cbb4e2ea091e4884729918b15/docs/<exact-filename>`. Exact file names are in the original `docs/` directory and the existing master index. This index's new links should be generated/validated at publication rather than guessing paths.

## 5. Proposed comprehensive documentation registry

The file status below describes this repository revision. A draft is available to read; a planned entry awaits authoring. Architecture approval is tracked separately. The ID prefix `PPC-` is required in published names; the short ID is used for readability. The final location is under `docs/enterprise-architecture/` in PPC. Each spec must cross-link to preserved PPC docs, source evidence and ADRs.

| Short ID | Proposed title | Proposed area | Core normative question | Existing references | File status |
|---|---|---|---|---|---|
| ARCH-000 | Master Architecture Index and Authority Baseline | `00-master-index/` | What is authoritative, proposed, required and traceable? | PPC-000, 015, 017, REG-001 | Draft (this index) |
| WORLD-001 | Canonical Enterprise World | `01-enterprise-world/` | Which physical/business world state exists, and who can change it? | PPC-001, 005, 013 | [Draft](../01-enterprise-world/PPC-WORLD-001_Canonical_Enterprise_World.md) |
| WORLD-002 | Simulation, Time, Replay and Branches | `01-enterprise-world/` | How are time, deterministic transitions and scenarios isolated? | PPC-005, 013, 016 | [Draft](../01-enterprise-world/PPC-WORLD-002_Simulation_Time_Replay_and_Branches.md) |
| ENG-001 | Physical and Numerical Engineering | `02-industrial-engineering/` | Which reduced-order equations, units and bounds are qualified? | PPC-005, 011, 019 | [Draft](../02-industrial-engineering/PPC-ENG-001_Physical_and_Numerical_Engineering.md) |
| OT-001 | Industrial Information Architecture | `02-industrial-engineering/` | How do source measurements, tags, historian and ICE mapping work? | PPC-006, 010; ICE | [Draft](../02-industrial-engineering/PPC-OT-001_Industrial_Information_Architecture.md) |
| EDI-001 | Engineering Information Integration | `02-industrial-engineering/` | How do approved engineering revisions/configurations enter PPC? | PPC-010, 019; EDI | [Draft](../02-industrial-engineering/PPC-EDI-001_Engineering_Information_Integration.md) |
| INFO-001 | Enterprise Ontology, Identity and Time | `03-enterprise-information/` | How do approved process/semantic concepts map to PPC identities? | PPC-003, 004, 017, 019 | [Draft](../03-enterprise-information/PPC-INFO-001_Enterprise_Ontology_Identity_and_Time.md) |
| GRAPH-001 | Enterprise Instance Graph | `03-enterprise-information/` | How are instances projected, versioned, secured and queried? | PPC-010, 016 | [Draft](../03-enterprise-information/PPC-GRAPH-001_Enterprise_Instance_Graph.md) |
| DATA-001 | Data Products, KPIs and Analytical Releases | `03-enterprise-information/` | How are facts, metrics, status, restatement and releases governed? | PPC-008, 013, 017 | [Draft](../03-enterprise-information/PPC-DATA-001_Data_Products_KPIs_and_Analytical_Releases.md) |
| INT-001 | Source Lifecycles and Integration | `04-source-integration/` | What do source events, outbox/inbox, recovery and reconciliation mean? | PPC-006, 007 | [Draft](../04-source-integration/PPC-INT-001_Source_Lifecycles_and_Integration.md) |
| EVID-001 | Evidence and Decision Context | `04-source-integration/` | What evidence could an agent know, when, from which source? | PPC-016, 018; ECE | [Draft](../04-source-integration/PPC-EVID-001_Evidence_and_Decision_Context.md) |
| ANALYTICS-001 | Performance Intelligence and Optimization | `05-intelligence-experience/` | Which validated numerical, causal, forecasting and optimization tools calculate impact? | PPC-011 | [Draft](../05-intelligence-experience/PPC-ANALYTICS-001_Performance_Intelligence_and_Optimization.md) |
| UX-001 | Enterprise Intelligence Workspace | `05-intelligence-experience/` | What business workflows use graph and scenario tools, with what authorization? | PPC-012 | [Draft](../05-intelligence-experience/PPC-UX-001_Enterprise_Intelligence_Workspace.md) |
| AGENT-001 | Agent Tools and Consequential Actions | `05-intelligence-experience/` | What may an agent read, simulate, recommend or execute? | PPC-012, 016 | [Draft](../05-intelligence-experience/PPC-AGENT-001_Agent_Tools_and_Consequential_Actions.md) |
| PLATFORM-001 | Infrastructure, Security and Operations | `06-platform-operations/` | How are services deployed, recovered, monitored and secured? | PPC-002, 009, 013, 014 | [Draft](../06-platform-operations/PPC-PLATFORM-001_Infrastructure_Security_and_Operations.md) |
| VERIFY-001 | Verification and Release Qualification | `07-scenarios-verification/` | What independently proves each behavioral and security contract? | PPC-005, 014, 016 | [Draft](../07-scenarios-verification/PPC-VERIFY-001_Verification_and_Release_Qualification.md) |
| SCENARIO-001 | Golden Enterprise Scenarios | `07-scenarios-verification/` | Which end-to-end fixtures demonstrate the enterprise? | PPC-001, 005, 014 | [Draft](../07-scenarios-verification/PPC-SCENARIO-001_Golden_Enterprise_Scenarios.md) |
| PLAN-001 | Implementation Work Packages and Readiness | `08-implementation/` | What is the smallest safe, testable dependency order? | PPC-014 | [Draft](../08-implementation/PPC-PLAN-001_Implementation_Work_Packages_and_Readiness.md) |
| KNOWLEDGE-001 | Architecture Learning and Design Rationale | `09-architecture-knowledge/` | Why was each engineering choice made; what first-principles reasoning must be preserved? | OT/EA discussion series | [Draft](../09-architecture-knowledge/PPC-KNOWLEDGE-001_Architecture_Learning_and_Design_Rationale.md) |

Supplementary draft registers now include [SOURCE-REGISTER](../registers/PPC-SOURCE-REGISTER.md), [REQUIREMENTS-COVERAGE](../registers/PPC-REQUIREMENTS-COVERAGE.md), [ADR-RECONCILIATION](../registers/PPC-ADR-RECONCILIATION.md), [DEPENDENCY-AND-COMPATIBILITY](../registers/PPC-DEPENDENCY-AND-COMPATIBILITY.md), [RISKS-AND-OPEN-QUESTIONS](../registers/PPC-RISKS-AND-OPEN-QUESTIONS.md), and [TERMINOLOGY](../registers/PPC-TERMINOLOGY.md). These route evidence and open questions; they do not grant approval. `independent-review/` remains a later evidence location. Do not duplicate upstream normative artifacts within PPC; reference pinned sources.

### 5.1 Authoring order and dependency rationale

1. **ARCH-000**, then **WORLD-001** and **WORLD-002** to establish authorities, world state, time and reproducibility.
2. **ENG-001**, **OT-001**, **EDI-001** to specify world constraints and industrial/engineering observation/configuration boundaries.
3. **INFO-001**, **GRAPH-001**, **INT-001** for stable identity, semantics, source lifecycles and graph projections. Cross-check identity and event assumptions bidirectionally.
4. **DATA-001**, **EVID-001** for governed analytical and decision evidence.
5. **ANALYTICS-001**, **UX-001**, **AGENT-001** for quantified decisions, the browser graph experience and authorization.
6. **PLATFORM-001**, **VERIFY-001**, **SCENARIO-001** for deployment and acceptance; **write local verification obligations alongside each earlier spec**, not only at the end.
7. **PLAN-001**, **KNOWLEDGE-001** to operationalize the implementation and preserve detailed learning/explanatory context.

### 5.2 Required structure for each normative specification

- Document control; exact authority and status; versioned inputs and affected artifacts.
- Scope, assumptions, definitions and explicit non-goals.
- System/context boundary, source-of-truth table, lifecycle/state machine and dependencies.
- Typed interface contracts with IDs, timestamps, units, cardinality, allowed/unknown states and source references.
- Engineering/commercial math where applicable, plus dimensional checks and independent fixtures.
- Typical and adverse worked examples; duplicates, stale events, contradictions and recovery.
- Security/access, time-cutoff and scenario-isolation conditions.
- Testable acceptance criteria (positive, negative, boundary, replay, failure injection) and evidence needed for qualification.
- Alternatives, unresolved decisions and traceability to prior PPC documents and upstream sources.
- Explicit separation of *proposed*, *approved*, *implemented*, *tested* and *qualified* statements.

## 6. OT/EA discussion-to-document coverage

The labels `OT-01…OT-12` and `EA-01…EA-09D` reference architectural **conversation work**, not independently existing repository files. The detailed passages, mathematical examples, diagrams, alternatives and decisions must be recovered and preserved before this matrix can be marked exhaustive. Below is a **topic-level coverage map**, not a claim that each session has been completely transcribed.

| Architecture discussion theme | Principal specification(s) | Key acceptance trace |
|---|---|---|
| Industrial control, ISA-95, sensor/tag/historian, edge and enterprise normalization (OT) | OT-001, EDI-001, INFO-001 | Exact tag/identity/time/quality mapping; negative ambiguous mappings |
| Canonical physical world, simulation, state, clocks and branches (OT/EA) | WORLD-001, WORLD-002, ENG-001 | Replay, invariant, boundary and cross-scenario isolation tests |
| Process ontology, performance meaning and EPM boundaries (EA) | INFO-001, DATA-001 | Pinned generalized process release; SHACL/competency/measure tests |
| Source systems, integration, CDC, lifecycle and physical vs commercial truth (EA) | INT-001, WORLD-002 | Duplicate, stale, out-of-order, partial-commit and reconciliation cases |
| Equipment topology, DEXPI, revision, source assertions (OT/EA) | EDI-001, GRAPH-001 | Accepted engineering snapshot with source evidence and graph round trip |
| Bitemporal identity, graph, scenario isolation, provenance (EA) | INFO-001, GRAPH-001, EVID-001 | As-of and known-at queries; permission filtering; no future evidence |
| Data products, Delta/R2, KPI Store, semantic views and consistency (EA) | DATA-001, PLATFORM-001 | Product release manifest and exact KPI recomputation/round trip |
| Physics, optimization, causality, uncertainty and model lifecycle (EA) | ENG-001, ANALYTICS-001, VERIFY-001 | Independent engineering benchmark, feasible LP, model evaluation |
| Relate WASM, business-facing change investigation (EA) | UX-001, GRAPH-001, ANALYTICS-001 | Relationship exposure distinguished from quantified model impact |
| Agent tools, memory, workflow and authorization (EA) | AGENT-001, EVID-001, PLATFORM-001 | Tool scopes, action approval, replay/idempotency, decision-time evidence |
| Infrastructure, backups, security, qualification and work packages (EA) | PLATFORM-001, VERIFY-001, PLAN-001 | Restore drill, version compatibility, readiness gates |
| Detailed first-principles rationale and historical options (OT/EA) | KNOWLEDGE-001 and ADR register | No unexplained loss of equations, worked examples or rejected alternatives |

**GAP-002 remains open.** The exchange inventory covers T1–T145. The new drafts have topic and section crosswalks in the [discussion register](../registers/PPC-Discussion-Decision-Traceability.md), but full OT-01–12 and EA-01–09D item-level and original-asset checks remain. Section 12 tracks this same gap.

## 7. Existing ADR baseline and proposed reconciliation

Source: [PPC-REG-001 at inspected revision](https://github.com/aadehamid/pearland-petroleum-corporation/blob/01027a84be5d453cbb4e2ea091e4884729918b15/docs/PPC-REG-001_Architecture_Decision_Register.md). This is **not** the source of an authorization to replace any ADR. It records ADR-001 to ADR-039.

| Proposed disposition | Count | ADR IDs | Treatment |
|---|---:|---|---|
| **Retain** | 26 | 001, 002, 003, 004, 008, 010, 012, 013, 019, 020, 021, 022, 023, 024, 025, 027, 028, 029, 030, 031, 032, 034, 036, 037, 038, 039 | Keep existing rationale and authority; add acceptance criteria where needed |
| **Extend** | 6 | 005, 006, 011, 026, 033, 035 | Preserve existing choice; clarify modeling roles, validation and versioned dependencies |
| **Reassess** | 7 | 007, 009, 014, 015, 016, 017, 018 | Compare approved original with proposed alternative, with evidence and user decision |
| **Total** | **39** | Each ADR appears exactly once | No ADR marked superseded by this document |

### 7.1 Seven changes that require explicit architecture decisions

| Existing ADR | Earlier selection | Candidate/current question | Evidence needed |
|---|---|---|---|
| ADR-007 | OpenMetadata catalog/governance plane | Required from first slice or later? | Minimum metadata needs, operability, and real users |
| ADR-009 | Jena/Fuseki for formal semantics | Which semantic consumers require a standing RDF server? | Upstream release flows, SPARQL needs, community deployment compatibility |
| ADR-014 | Dash decision application | Is a different frontend necessary for Relate WASM and integrated scenario UX? | User workflow prototypes, data/API permissions, deployment footprint |
| ADR-015 | Dagster orchestrates; Kafka transports | NATS JetStream initially versus Kafka while keeping orchestration separate | Delivery semantics, replay, CDC, operations, failure tests |
| ADR-016 | Debezium CDC | Python-native or source-native capture versus the incumbent | Capture completeness, recovery, ordering and measured operations |
| ADR-017 | DuckDB/DuckLake analytical history | Delta on R2 versus DuckLake (or scoped coexistence) | Concurrent-write qualification, Databricks interoperability, restore and migration |
| ADR-018 | Databricks as parallel enterprise-like implementation | Exact role, tiers, scope and timing | Actual entitlement/feature qualification, cost and portability |

PPC-011 documents **OR-Tools** as an existing optimization choice, while PPC-012 documents **LangGraph** and **Langfuse** as existing agent/observability choices. **Pyomo/HiGHS**, **Pydantic AI**, and **OpenTelemetry/Logfire** are candidate alternatives raised for future assessment; they are **not recorded choices or alternatives in PPC-011/012**. Any proposed replacement should receive **new or amended ADRs** before it changes the existing baseline; these alternatives are not independently numbered choices in `PPC-REG-001`.

### 7.2 New ADR candidate topics (not assigned/approved)

`CAN-WORLD-AUTHORITY`, `CAN-SCENARIO-ISOLATION`, `CAN-ENGINEERING-QUALIFICATION`, `CAN-ICE-EDI-REUSE`, `CAN-DS-BUSINESS-PROCESS`, `CAN-TEMPORAL-IDENTITY`, `CAN-EVENT-RECOVERY`, `CAN-RELEASE-CONSISTENCY`, `CAN-RELATE-UX`, `CAN-QUANTIFIED-IMPACT`, `CAN-AGENT-AUTHORITY`, `CAN-GOLDEN-SCENARIOS`, `CAN-VERIFICATION-GATES`.

Each candidate needs owner, problem, alternatives, rationale, affected original ADRs, impacts on upstream authorities, tests, disposition and decision timestamp. Do not assign approved ADR numbers or imply consensus from sequence-advancing conversation phrases.

## 8. Versioned dependency and scenario manifest policy

The existing PPC-017 requires EPM manifests and semantic tests. A complete PPC release should also identify exact versions of ICE, EDI and ECE contracts, data products, graph snapshots, models, and source observations. Propose a **single top-level release manifest with separately governed component identities**. Different version layers must not be conflated:

- Git commit identifies source tree, not business approval.
- Ontology module version identifies released semantic content, not PPC data values.
- Engineering source revision identifies a source configuration; EDI publication identifies an accepted engineering projection; PPC adoption is a separate event.
- World state version and scenario branch identify simulated physical reality and scenario-specific changes.
- Transaction/event IDs identify source records and message delivery, not the underlying physical event by default.
- Delta/DuckLake table snapshot identifies a technical read state; a business-consistent data-product release pins aligned inputs and declared watermarks.
- Graph snapshot identifies one derived instance projection and its source/effective/recorded-time boundaries.
- Model version identifies numerical/ML formulation and parameters; a result also requires seed/input snapshot/solver profile.
- Evidence/decision release identifies eligibility, visibility and a historical knowledge cutoff.

### 8.1 Proposed manifest shape (illustrative, not implemented)

```yaml
schema_version: "proposal-0.1"
ppc_release_id: "<release-id>"
status: "DRAFT"
source_commit: "<ppc-commit>"
world:
  world_version: "<immutable-world-version>"
  scenario_id: "<scenario-branch>"
  effective_clock_origin: "<ISO-8601 timestamp>"
  input_snapshot_sha256: "<hash>"
  generator_seed: 42
semantic:
  ds_business_process:
    status: "PENDING_UPSTREAM_RELEASE"
    approved_release: null
  epm_modules: []  # add approved versions with digest, owner and compatibility status
engineering:
  edi_contract: "<approved-contract-version-or-PENDING>"
  engineering_publication: "<accepted-publication-id>"
  ppc_configuration_adoption: "<world-configuration-event-id>"
industrial:
  ice_mapping: "<approved-mapping-version-or-PENDING>"
evidence:
  ece_contract: "<approved-version-or-PENDING>"
  historical_knowledge_cutoff: "<ISO-8601 timestamp>"
compute:
  analytical_release_id: "<release-id>"
  model_versions: {}
  solver_profile: "<verified-profile>"
  graph_snapshot_id: "<graph-snapshot-id>"
verification:
  suite_digest: "<hash>"
  status: "NOT_RUN"
  evidence_refs: []
```

This is a **shape illustration only**. It is not a schema file, executable contract or license to use placeholder dependencies in a qualified release. A later specification must identify required versus optional dependencies and fail closed when an essential source is unavailable/unapproved.

### 8.2 Compatibility gates

Before an integrated PPC scenario or release is approved:

1. Every required upstream reference resolves to an immutable digest and approved authority status.
2. Concept IRIs/definitions and mappings pass the required semantic, shape and competency checks.
3. PPC identity crosswalks and time validity match the selected engineering, OT and source revisions.
4. Business values and KPI results are recomputable from pinned inputs and definitions; thresholds/status and data-quality flags remain distinct.
5. Scenario branches are isolated and results cannot be mistaken for baseline facts.
6. Source-visible evidence obeys access scope and the decision-time cutoff; hidden truth remains unreachable to ordinary agent tools.
7. Graph snapshots reflect declared inputs, permissions, and timeline; graph connectivity is never presented as a numerical effect.
8. Integration replay/idempotency and storage/restore controls have scenario-relevant test evidence.
9. Version, test and approval evidence identifies the exact released code/configuration and environment.

## 9. Golden scenarios and verification scope

### Scenario A — Hydrocracker compressor derate (proposed first slice)

An authorized scenario changes a compressor condition represented in PPC's qualified, simplified physical model. The world model calculates whether and how capacity/throughput/production change. Synthetic OT observations and source records are emitted without access to hidden truth outside authorized generation. ICE mappings identify measurements and assets. EDI supplies source-backed topology. Planning/optimization evaluates feasible alternatives; EPM-governed measures/KPI values quantify effects. Neo4j/Relate exposes connectivity and potential exposure, while model outputs establish what actually changes in the scenario.

Acceptance MUST include independent mass/inventory/capacity checks, reproducible replay, state/version pinning, ambiguous tag rejection, source-time fidelity, graph-versus-physics separation, numeric baseline/scenario differences and permission isolation. A linear availability approximation is only an illustrative modeling assumption, not actual compressor thermodynamics.

### Scenario B — Crude-quality rejection (proposed second slice)

Represent contract, nomination, custody/receipt, sampling, LIMS results, disposition, CTRM actualization, tank inventory, planning alternatives, financial effects and approved EPM KPIs as separate lifecycle authorities. Test duplicate deliveries, unknown product mappings, delayed finance, contradictory evidence, out-of-order messages and replay without repeating a physical receipt. A source application may lag the fictional physical event; do not silently fix it with omniscient canonical world data.

### Scenario C — Hurricane disruption (preserved existing charter scenario)

Retain the existing hurricane/event-to-margin chain as a later broad regression/integrated demonstration. Do not erase the original roadmap merely because the narrower engineering and commercial slices are proposed earlier.

### Verification layers (non-substitutable)

| Layer | Example evidence | What it does **not** establish |
|---|---|---|
| Schema and semantic | JSON/Pydantic tests, SHACL, competency queries | Physical correctness |
| Formal state/identity | Temporal and transition invariants, model checking | Numerical realism |
| Physical/numerical | Independent conservation benchmarks, unit tests, solver sanity | Full refinery engineering fidelity |
| Integration | Duplicate/out-of-order/restart/reconciliation tests | Quantified business value |
| Graph | Instance/type/lineage round trip, as-of/permission checks | Causal or physical propagation from path alone |
| KPI/data product | Formula and threshold recomputation, backfill/restatement tests | Approval of undefined business populations |
| Agent/evidence | Claim-level citations, temporal leakage, policy-authorized actions | Permission to execute consequential operations without a service-side gate |
| End-to-end scenario | Expected world/source/graph/economic states and recovery | Real-world plant qualification |

## 10. Implementation sequencing and readiness gates

The proposed vertical-slice order is not yet an approved replacement for PPC-014:

- **R0 — Architecture baseline:** Reconcile authority, existing docs, ADR candidates and source coverage.
- **R1 — Repository/contract inventory:** Record exact repo revisions and qualified upstream dependencies.
- **R2 — Core contracts:** World identity, timestamps, scenario isolation, source lifecycles, first physical model and evidence cutoffs.
- **R3 — Independent numerical benchmarks:** Validate engineering and optimization math before integrating effects into business UI.
- **R4 — Infrastructure qualification:** Benchmark compact deployment; test secrets, backup/restore and isolation.
- **R5 — First integrated golden slice:** Compressor derate with scoped source records, graph, governed KPI and scenario impact.
- **R6 — Reviewable release:** Traceability, negative tests, performance/recovery and sign-off evidence.

**Authorization boundary:** An independent architecture review follows initial comprehensive document creation and publication; its findings must be dispositioned before Phase 0 implementation is authorized. A preliminary document review pass is not a production-readiness declaration.

## 11. Publication and independent-review requirements

### 11.1 Before publishing the architecture review baseline

- [ ] Confirm source refs and refresh any advanced branches; record exact hashes.
- [ ] Assign and register finalized document IDs and filenames; verify unique authority.
- [ ] Map each preserved PPC-000–019 section and all 39 ADRs to retain/extend/reassess dispositions.
- [ ] Capture and map the **complete** OT/EA conversation-derived technical content; do not claim completeness from summaries alone.
- [ ] Ensure each normative clause has an owner, testable meaning, source or clearly marked proposal status.
- [ ] Complete equations, worked examples, edge cases and independent verification for all physics/optimization claims.
- [ ] Review EPM / `kpi-store/1.2` source and future DS_Business_Process boundary; leave pending release unapproved.
- [ ] Distinguish current ICE Level-0 and EDI structured pipelines from future capabilities; do not overstate ECE implementation.
- [ ] Resolve or explicitly expose conflicting technology decisions; do not silently supersede existing ADRs.
- [ ] Validate file paths, links, identifiers, terminology, tables and internal references.
- [ ] Conduct owner review and record approval for publication to a controlled PPC PR.

### 11.2 Independent reviewer mandate (after publication)

The independent agent must read pinned source files and the complete normative/reasoning package. It should challenge authority boundaries, source and temporal correctness, physical dimensionality and fidelity, causal claims, KPI governance, overengineering, deployment compatibility, access isolation, failure recovery, browser graph user value, release consistency and end-to-end acceptance. Findings must be classified by severity with evidence, reproducibility, recommendation, proposed ADR disposition and owner response. The reviewer cannot approve itself or retroactively assert missing runtime evidence.

### 11.3 Controlled publication workflow

1. Draft and peer-check the package away from existing `docs/PPC-*` paths.
2. Owner reviews the content and authorizes a dedicated PPC branch/PR.
3. Publish the first architecture-review baseline; never label it implemented or qualified.
4. Request an independent agent review of the published revision.
5. Resolve/reject findings with recorded rationale and approved ADR amendments.
6. Only then plan and authorize Phase 0 implementation.

## 12. Open issues and evidence gaps (must not silently close)

| ID | Gap / issue | Why it matters | Disposition needed |
|---|---|---|---|
| GAP-001 | `DS_Business_Process` generalized release pending | Process IDs/semantics may change | Await other agent's approved release; compatibility plan |
| GAP-002 | Open. Exchange inventory complete; substantive item-to-section coverage and source-asset checks remain open (§6). | Risk of lost detailed reasoning, math and examples | Verify destination sections or record explicit dispositions in the [discussion register](../registers/PPC-Discussion-Decision-Traceability.md) before a completeness claim. |
| GAP-003 | Existing PPC technology choices differ from later proposals | Conflicting ADR authority | Decision-by-decision review before changing stack |
| GAP-004 | ICE identity/mapping YAML not yet written as of inspected handoff | No qualified enterprise OT normalization | Provisional boundary and upstream qualification |
| GAP-005 | EDI complete drawing/extraction/recovery lifecycle not qualified | Only bounded structured engineering slice established | Scope reuse and test exact DEXPI profiles |
| GAP-006 | ECE versioned reusable contracts not yet published in inspected tree | Downstream cannot bind final schema versions | Provisional adapters, upstream release gate |
| GAP-007 | KPI Store 1.2 client installation and certain cross-store cases not qualified | Cannot assume PPC compatibility | Environment-specific qualification, Community/Enterprise assessment |
| GAP-008 | PPC physical equations and world event kernel have draft contracts, not implementation or independent qualification | No authoritative quantified scenario impact | Independent benchmarks and runtime evidence |
| GAP-009 | Multi-store business-consistent release has a draft contract, not an implementation | Inconsistent KPI/graph/model views | Build and test manifest and watermarks |
| GAP-010 | Frontend Relate WASM compatibility/performance/authorization unproven | Graph exploration may leak or overpromise | Bounded prototype and negative tests |
| GAP-011 | Current PPC integrated source-system deployment not established | Architecture diagrams not operational proof | Infra and end-to-end evidence before claims |
| GAP-012 | Formal approval of new ADR candidates outstanding | Proposals risk being misrepresented as requirements | User-approved decision register entries |

## 13. Verification of this draft

This document was prepared from read-only inspection of the pinned GitHub source baseline and architecture discussion. At initial drafting, the six source repository commits were retrieved; the ontology `ds-business-process/1.0` and `kpi-store/1.2` branch pointers both resolved to `ddf6b68b...`. PPC's existing 20 numbered architecture documents and 39-ADR register had been inspected in that review sequence. The new specifications in this branch are draft documentation, not a refreshed upstream status audit.

For the 2026-11-26 documentation pass, all 19 registered spec IDs had unique, existing files and matching headings. A prior structural inventory counted 19 registered documents; it did not establish semantic completeness. The seven classes in the independent review are the subject of this revision, and runtime qualification remains open. The earlier pass checked links and tables on its then-current draft; its exact counts are not claimed for this revision. Arithmetic checks covered the stated tank, derate, replay, assay, blend and unit-conversion examples. The earlier noon/13:00 temporal fixture failed review; INFO-001 §3 now specifies complete chained publications. An in-memory SQL query over its documented rows returned A for (09:59, 13:00) and (10:30, 12:45), and B for (10:00, 13:00) and (10:30, 13:00). With P2 hidden it returned A; a second P2 occupant triggered the uniqueness check. These are specification-fixture checks, not application tests. No runtime implementation is qualified by this documentation pass. The exchange register covered T1–T145; the finer CSV had 3236 locators across 135 exchanges. These checks do not close GAP-002 or substitute for source-asset review, owner approval or independent architecture review.

No application tests, formal proofs, physical simulations or deployment checks are claimed. This pass changed documentation only on the existing branch; it did not push, merge or change branches.

## 14. Source reading list (pinned)

### PPC

- [PPC README](https://github.com/aadehamid/pearland-petroleum-corporation/blob/01027a84be5d453cbb4e2ea091e4884729918b15/README.md) — charter orientation and project scope.
- [PPC-000](https://github.com/aadehamid/pearland-petroleum-corporation/blob/01027a84be5d453cbb4e2ea091e4884729918b15/docs/PPC-000_Master_Index_and_Architecture_Guide.md) — existing architecture index.
- [PPC-005](https://github.com/aadehamid/pearland-petroleum-corporation/blob/01027a84be5d453cbb4e2ea091e4884729918b15/docs/PPC-005_Synthetic_Data_Generation_Strategy.md) — world and source-generation principles.
- [PPC-007](https://github.com/aadehamid/pearland-petroleum-corporation/blob/01027a84be5d453cbb4e2ea091e4884729918b15/docs/PPC-007_Data_Integration_Event_and_Orchestration_Architecture.md) — existing event integration choices.
- [PPC-014](https://github.com/aadehamid/pearland-petroleum-corporation/blob/01027a84be5d453cbb4e2ea091e4884729918b15/docs/PPC-014_Implementation_Roadmap_and_Build_Runbook.md) — original roadmap.
- [PPC-015](https://github.com/aadehamid/pearland-petroleum-corporation/blob/01027a84be5d453cbb4e2ea091e4884729918b15/docs/PPC-015_Three_Repository_Operating_Model.md) — existing EPM/ECE/PPC authority.
- [PPC-016](https://github.com/aadehamid/pearland-petroleum-corporation/blob/01027a84be5d453cbb4e2ea091e4884729918b15/docs/PPC-016_Evidence_Decision_Provenance_and_Evaluation_Architecture.md) — provenance/evidence.
- [PPC-017](https://github.com/aadehamid/pearland-petroleum-corporation/blob/01027a84be5d453cbb4e2ea091e4884729918b15/docs/PPC-017_EPM_Dependency_Semantic_Authority_and_Process_Conformance_Contract.md) — semantic authority.
- [PPC-019](https://github.com/aadehamid/pearland-petroleum-corporation/blob/01027a84be5d453cbb4e2ea091e4884729918b15/docs/PPC-019_Public_Ontology_Reuse_and_Implementation_Guide.md) — proposed public ontology assessment.
- [PPC-REG-001](https://github.com/aadehamid/pearland-petroleum-corporation/blob/01027a84be5d453cbb4e2ea091e4884729918b15/docs/PPC-REG-001_Architecture_Decision_Register.md) — 39 original decisions.

### Other repositories

- [EPM README](https://github.com/aadehamid/enterprise-performance-model/blob/511a9e8db4008ef43a0dda0f92cef17664e4c995/README.md), [module guide](https://github.com/aadehamid/enterprise-performance-model/blob/511a9e8db4008ef43a0dda0f92cef17664e4c995/business_architecture/ontology/MODULES.md), [projection guide](https://github.com/aadehamid/enterprise-performance-model/blob/511a9e8db4008ef43a0dda0f92cef17664e4c995/business_architecture/ontology/projection/README.md).
- [KPI Store 1.2 README](https://github.com/aadehamid/downstream_oil_and_gas_ontology_release/blob/ddf6b68b614c8ae5cdaeb935fe435562bf2678d0/README.md), [release manifest](https://github.com/aadehamid/downstream_oil_and_gas_ontology_release/blob/ddf6b68b614c8ae5cdaeb935fe435562bf2678d0/release.json), [known issues](https://github.com/aadehamid/downstream_oil_and_gas_ontology_release/blob/ddf6b68b614c8ae5cdaeb935fe435562bf2678d0/KNOWN-OPEN-ITEMS.md).
- [ICE L0 contract](https://github.com/aadehamid/scada_harmonization/blob/1467e9278a9fa50d80618a296297eb40cd4416c2/docs/LSC-004_Level_0_Contract.md), [current handoff](https://github.com/aadehamid/scada_harmonization/blob/1467e9278a9fa50d80618a296297eb40cd4416c2/HANDOFF.md).
- [EDI logical contracts](https://github.com/aadehamid/Engineering_Drawing_to_Graph/blob/12a4a6a6f715c7db76a26d763cb1938d6cf0cc05/docs/LIONG-005-data-contracts.md), [evaluation](https://github.com/aadehamid/Engineering_Drawing_to_Graph/blob/12a4a6a6f715c7db76a26d763cb1938d6cf0cc05/docs/LIONG-010-evaluation.md), [implementation runbook](https://github.com/aadehamid/Engineering_Drawing_to_Graph/blob/12a4a6a6f715c7db76a26d763cb1938d6cf0cc05/docs/LIONG-011-build-runbook.md).
- [ECE operating model](https://github.com/aadehamid/enterprise-context-engineering/blob/750b398b6a50aedd552a72056d09cf1ccf6a296a/docs/architecture/epm-ece-ppc-operating-model.md), [evidence strategy](https://github.com/aadehamid/enterprise-context-engineering/blob/750b398b6a50aedd552a72056d09cf1ccf6a296a/docs/strategy/synthetic-data-generation-strategy.md).

---

**Document status reminder:** This is a **reviewable draft**. Its principal contribution is source/decision/document authority, transparency about gaps and a concrete architecture-writing plan. It does not by itself close any readiness gate or establish the validity of the full future architecture.
