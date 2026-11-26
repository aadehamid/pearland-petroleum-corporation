# PPC discussion and decision traceability register

Draft for owner review · 25 November 2026 · Companion to [PPC-ARCH-000](../00-master-index/PPC-ARCH-000_Master_Architecture_Index_and_Authority_Baseline.md) and [PPC-WORLD-001](../01-enterprise-world/PPC-WORLD-001_Canonical_Enterprise_World.md).

## Evidence and coverage

The source is **ChatGPT-Downstream Backcasting Research-20261125-2232.md**, exported 25 November at 22:32:53. Line numbers refer to the 40,519-line Markdown export, including its header. T1–T145 identify consecutive user prompts and their responses. The table below accounts for every exchange; grouped rows identify a related sequence, and their standing describes the sequence. The [source locator CSV](PPC-Discussion-Source-Locators.csv) provides finer addresses inside those ranges. For example, filter the CSV on exchange `27` and source ID `WORLD-07` to find the original decision-quality question at line 4591, or `EA-DBX-002` for the Delta *recommendation* at line 19736. Use `(exchange, source_id)` plus the unique source line when an ID recurs. T27 lines 4585–4586 are competency questions WORLD-01/02. T122 lines 35138–35139 reuse those labels for work packages. In T71 line 14934 the exported heading is literally `,000 bbl/day`; it follows an interactive control whose selected value is unavailable. It supplies no numerical fixture.

**Scope of the check.** This is a complete exchange inventory for this export, with 1955 discussion headings and 1281 individually addressed table rows containing source identifiers. The CSV has 3236 fine locators across 135 exchanges; T10, T12, T16–18, T28, T30, T77, T131 and T137 have no fine CSV row and remain reachable through the exchange ranges below. The CSV retains original subjects and recorded standing where available. Its categories aid navigation; the surrounding exchange determines meaning. The ADR and destination columns on CSV rows are exchange-level routing, not proof that an ADR approves each detail. Unnumbered rationale, equations, code, diagrams and examples remain anchored by the surrounding line range. Interactive output sometimes exports as an empty widget or SVG. Where fidelity affects a design decision, verify the original artifact. No access to the private transcript is required to read the architecture specification.

**Authority.** An explicit user requirement or correction establishes direction. An existing ADR governs its recorded scope until formally changed. An assistant recommendation, a table cell labeled “Required,” or a request to continue does not by itself approve a replacement. For conflicting sources, preserve the incumbent and the proposed change and identify the owner decision. The repository baseline for this check is [PPC at 08e7b33](https://github.com/aadehamid/pearland-petroleum-corporation/tree/08e7b3356f9b3ad18ce6a632d82615ad5a4e3847). Document identifiers below use the short forms in ARCH-000.

## Decisions that change how the documents must be written

| Question and evidence | Reconciled standing | Destination and close-out |
|---|---|---|
| Who owns the world? T11–20, T43–44; ADR-001/024/028 | Owner adopted a hybrid engineering and business simulation. One canonical history produces imperfect source views. Earlier independently generated data can be a reusable fixture only with explicit provenance. | WORLD-001 §§1–4; INT-001 source generation. Test two heterogeneous source views against one hidden reference. |
| How many refineries? T21, T23, T122; PPC-001/005 | Public anchoring is required. Multiple refineries and the expanded engineering blueprint are staged proposals. Current v0.1 charter is one Gulf Coast refinery and three terminals. | WORLD-001 §§1–2; PLAN-001. A charter or roadmap change must identify the added scope. |
| Is an LP run evidence of a missed opportunity? T2–3, T23–27, T115 | Preserve case lineage, the information cutoff, constraint set and execution evidence. Calibration, decision and execution effects have separate explanations. | WORLD-001 §§4–7; ANALYTICS-001 and EVID-001. Repeat case with a changed model but identical history. |
| Can users introduce new information? T36, T71–72, T111 | Owner requested dynamic scenario recomputation, explanations of infeasibility and a business-facing impact explorer. Connectivity supports investigation; a numerical claim needs a qualified calculation. | WORLD-001 §§3–7, WORLD-002, UX-001. Test infeasible input, late evidence and baseline preservation. |
| Which scenario leads? T58, T97, T122, T125–126; PPC-001/014 | Compressor derate and crude rejection are proposed first and second engineering slices. The charter retains its hurricane demonstration. | WORLD-001 §§1,5–7 and SCENARIO-001. Reconcile implementation order in PLAN-001. |
| What happens to the ontology? T6–9, T89–92, T131–135; ADR-033/035/038/039 | Upstream owns the generalized process release. PPC binds an approved version when available. EPM retains performance meaning; local instances and qualified calculations belong to PPC. | WORLD-001 §§2,8; INFO-001 and DATA-001. Record release, maturity, mappings and compatibility results. |
| Which storage format? T50, T79–87; ADR-003/004/017/018 | **Decided** ([ADR-0045](../../adr/0045-delta-lake-on-r2-and-databricks-portability.md), T86): Delta Lake on Cloudflare R2 replaces DuckLake (`delta-rs` sole writer with `aws_conditional_put="etag"`, DuckDB read-only); Databricks Free Edition ingests synced copies into workspace-managed Delta (`WP-8`), paid tiers use UC external locations or managed migration. | `DATA-001`/`PLATFORM-001`/`PLAN-001`; run dual-writer conflict and Free Edition ingest probes in WP-0. |
| Which technology choices are still open? T46–61, T75, T95, T110–121; ARCH-000 ADR reconciliation | **Decided** (`ADR-0044`–`0052`): Python/FastAPI preferred; open-source/free-tier only with R2 exception; Git Turtle/`pyshacl`→Neo4j; outbox+NATS on IT and Sparkplug B on OT; Pyomo/HiGHS/IPOPT; LangGraph+Pydantic tools+OTel; Dash Slice 1 + Relate WASM Slice 1.5; `exe.dev` + R2 + RPO/RTO. | `PLATFORM-001`, `INT-001`, `UX-001`, `AGENT-001`, `PPC-REVIEW-003`; close WP-0 flowsheet/sizing/steward gates before Phase 0. |
| What must the review package preserve? T22, T25, T70, T74–77, T123–127, T136–145 | Retain diagrams, definitions, calculations, alternatives, competence questions, validation evidence and historical rationale. Markdown is the repository draft format; the requested HTML presentation belongs to later package assembly. | KNOWLEDGE-001, VERIFY-001 and PLAN-001. Independent architecture review follows document publication and owner review. |

## Exchange register

Read the ADR column as related baseline context. Where an exchange spans several decisions, consult the CSV and the original line range. The registered destinations are draft documents in the master index. A topic destination does not establish item-level or attachment coverage.


### Backcasting and the enterprise world

| Exchange · source lines | Standing | Discussion and disposition | Destination | Related ADRs |
|---|---|---|---|---|
| T1 · 9–76 | Request | Reconstruct a past operating period and compare feasible alternatives using synthetic data and open tools. | ANALYTICS-001, VERIFY-001, SCENARIO-001 | 019 |
| T2 · 77–161 | Direction | Call it a simulation experience. Show LP case order, tuning effects, fair attribution and investigation dashboards. | ANALYTICS-001, UX-001 | 019, 031 |
| T3 · 162–275 | Direction | Preserve historical and current decisions for comparison. Score model calibration, decision quality and execution separately. | EVID-001, ANALYTICS-001 | 028, 029, 031 |
| T4–T5 · 276–721 | Analysis | PPC hosts the simulation, ECE supplies evidence contracts and EPM supplies performance meaning. See T133–135 for the process authority refinement. | ARCH-000, EVID-001, DATA-001 | 026, 033, 034 |
| T6–T8 · 722–1558 | Mixed | Generalize the company-independent downstream map. Keep industry meaning distinct from the PPC specialization and industrial information mappings. | INFO-001, OT-001, ARCH-000 | 008, 033, 035 |
| T9–T10 · 1559–1710 | Direction | Industrial harmonization is reusable across companies. ICE is the proposed name and role. Repository renaming is a separate action. | OT-001, ARCH-000 | 024 |
| T11–T12 · 1711–1884 | Endorsed direction | One fictional company generates the physical, commercial and temporal world consumed by reusable frameworks. | WORLD-001, ARCH-000 | 001, 026, 033 |
| T13–T18 · 1885–2348 | Exploration and preference | Keep the PPC model authoritative. Genie or another immersive interface can be evaluated later. Build the backcasting investigation and decision experience first. | WORLD-001, UX-001 | 001, 019 |
| T19 · 2349–2520 | Proposal | Start from business footprint, participants and capabilities, then design the world and its generated records. | WORLD-001, SCENARIO-001 | 001, 002 |
| T20 · 2521–2893 | Explicit adoption | Adopt the hybrid engineering and business simulation. Link physical objects, streams, utilities and feasible operating limits to commercial consequences. | WORLD-001, ENG-001 | 001, 019 |
| T21 · 2894–3223 | Mixed | Use public data to test realism. The two-refinery design is a growth path. Stage one coherent refinery first. Compare T122 and PPC-005. | WORLD-001, ENG-001, PLAN-001 | 001, 002 |
| T22 · 3224–3318 | Direction | Preserve the architecture and repository relationships in well-structured HTML design material when the design is consolidated. | KNOWLEDGE-001, ARCH-000 | 025 |
| T23 · 3319–3573 | Proposal | Refinery A blueprint includes unit, stream, equipment and quality identities. Keep approved plan, observations, reconciled actuals and feasible counterfactuals distinct. | WORLD-001, ENG-001 | 001, 024 |
| T24 · 3574–3914 | Proposal | Use assays, cut yields, unit operating envelopes, balances, blending and LP calibration. Preserve model versions and test limits before opportunity valuation. | ENG-001, ANALYTICS-001, WORLD-001 | 019 |
| T25 · 3915–4034 | Direction | Include diagrams and validated questions in the eventual HTML. Record proposed tests separately from successful results. | KNOWLEDGE-001, VERIFY-001, WORLD-001 | 025, 037 |
| T26 · 4035–4340 | Mixed | Capture historical decisions and rationale. Formal verification and Bend are candidates for selected invariants. | EVID-001, ANALYTICS-001, VERIFY-001 | 029, 031 |
| T27 · 4341–4647 | Proposal | Separate lifecycle, condition and operating state. Change state through effective events and executed actions. Preserve checkpoints and the eight WORLD questions. | WORLD-001, WORLD-002, EVID-001 | 001, 028, 029, 031 |
| T28–T30 · 4648–4789 | Navigation | Program naming and a reusable ecosystem diagram. Preserve repository relationships in the architecture overview. | ARCH-000, KNOWLEDGE-001 | 025 |
| T31 · 4790–4878 | Proposal | Add roles, incentives, information limits, authority and coordination to the decision model. | WORLD-001, EVID-001 | 029 |
| T32 · 4879–5208 | Direction | Historical evidence spans documents, messages and structured records. Consume generalized process meaning. See T131 and T135. | EVID-001, INFO-001 | 026, 029, 030, 035 |
| T33 · 5209–5521 | Proposal | Generate heterogeneous source documents and transactions from business events with role-specific observations and timing. | INT-001, EVID-001 | 024, 030 |
| T34 · 5522–5856 | Mixed | Define canonical contracts first, then reassess repository tools and existing generated data. Prior cleanup discussions provide no execution or deletion evidence. | WORLD-001, INT-001, PLAN-001 | 001, 003, 024 |
| T35 · 5857–6186 | Proposal | Separate domain engines, event scheduling and numerical calculations. Pin run context and compare decision alternatives on a common basis. | WORLD-002, ENG-001, ANALYTICS-001 | 001, 019 |
| T36 · 6187–6503 | Direction | Support new evidence and user interventions. Validate constraints, explain infeasibility and recompute accepted scenarios in isolated branches. | WORLD-001, WORLD-002, UX-001 | 019, 020 |

### Engineering information and industrial architecture

| Exchange · source lines | Standing | Discussion and disposition | Destination | Related ADRs |
|---|---|---|---|---|
| T37–T38 · 6504–6917 | Exploration | Use P&ID topology and public example data for engineering context. Check source licenses, revisions and mappings before operational use. | EDI-001, OT-001, ENG-001 | 008, 024 |
| T39–T42 · 6918–7265 | Mixed | Reuse the engineering-drawing repository for engineering contracts. EDI naming, access and repository reorganization have separate dispositions. | EDI-001, ARCH-000 | 008 |
| T43–T44 · 7266–7476 | Clarification | Distinguish reusable extraction fixtures from company operational data. Only coherent world-generated records can represent PPC operational history. | WORLD-001, EDI-001 | 001, 024 |
| T45 · 7477–7797 | Proposal | Condition synthetic cases on licensed public observations with time, scale, geography and uncertainty. Avoid treating an aggregate as a PPC measurement. | WORLD-001, ENG-001, SCENARIO-001 | 002, 031 |
| T46–T47 · 7798–8432 | Direction | Inventory technology across all repositories, including open-source libraries and Databricks roles. Evaluate overlaps before selecting replacements. | PLATFORM-001, KNOWLEDGE-001, PLAN-001 | 018, 021 |
| T48–T49 · 8433–8880 | Mixed | Prefer open tools and suitable free editions. Evaluate Coreflux as an operational-data publisher or generator driven by the same world state. | OT-001, PLATFORM-001 | 001, 024 |
| T50 · 8881–9093 | Proposal | Compare analytical formats and durable storage. Reconcile using T86 and existing ADRs before changing the stack. | PLATFORM-001, DATA-001 | 003, 017, 018 |
| T51–T52 · 9094–9489 | Direction and proposals | Complete the OT stack review. Exclude paid commercial licenses in this evaluation. Review physical-simulation libraries with evidence. | OT-001, ENG-001, PLATFORM-001 | 019 |
| T53 · 9490–9738 | Proposal | Compare SCADA/HMI choices and operator displays. An HMI publishes commands or displays observations within its authority. | OT-001, UX-001 | 024 |
| T54 · 9739–10125 | Direction and proposals | Validate events and physics. Specify transport, OPC UA and MQTT/Sparkplug roles and qualify the chosen stack. | OT-001, VERIFY-001 | 024 |
| T55 · 10126–10541 | Proposal | Define historian quality, sampling, storage, time and replay independently of the world state. | OT-001, INT-001 | 024, 031 |
| T56–T57 · 10542–11279 | Mixed | Simulate inconsistent identifiers, units and quality. Keep site mappings, enterprise harmonization and semantic context traceable to original signals. | OT-001, INFO-001 | 008, 024 |
| T58 · 11280–11554 | Proposal | Use the compressor derate to verify OT-to-enterprise behavior before qualifying advanced diagnostics. | OT-001, SCENARIO-001, VERIFY-001 | 024, 037 |
| T59–T61 · 11555–12282 | Exploration | Evaluate model deployment, portable runtimes and durable agent state at the edge. Keep core simulation independent of model availability. | OT-001, ANALYTICS-001, PLATFORM-001 | 019, 020 |
| T62 · 12283–12635 | Exploration | Assess semantic translation, ontology-to-graph mappings and embedded graph tooling. Qualify independently. | INFO-001, GRAPH-001 | 008, 009, 010 |
| T63–T65 · 12636–12857 | Mixed | Complete outstanding OT discussions before enterprise design and preserve first-principles explanations and implementation-ready deliverables. | KNOWLEDGE-001, PLAN-001, OT-001 | 025 |
| T66–T67 · 12858–13601 | Proposal | Separate edge execution planes and specify versioned observation, event and command contracts including recovery. | OT-001, INT-001, PLATFORM-001 | 020, 024 |
| T68 · 13602–13949 | Mixed | Consider small edge models; also begins OT-09 on semantic identity. Both topics are part of this exchange. | OT-001, INFO-001 | 008, 019 |
| T69–T70 · 13950–14743 | Direction and proposal | Give information and semantic modeling dedicated coverage. Preserve canonical measurement, asset identity and mapping rationale. | INFO-001, OT-001 | 005, 008, 033 |
| T71 · 14744–15104 | Proposal | Separate physical, observational, informational and decision events. Validate and isolate interventions and preserve event history. | WORLD-001, WORLD-002, UX-001 | 001, 020, 031 |
| T72 · 15105–15465 | Mixed | Turn market observations into sourced scenario hypotheses. Preserve decisions, alternatives, evidence cutoffs, approvals and execution. | WORLD-001, EVID-001, SCENARIO-001 | 002, 029, 031 |
| T73 · 15466–16029 | Proposal | Verify physical behavior, timing, evidence and business consequences with independent references and adversarial cases. | VERIFY-001, ENG-001 | 011, 019, 037 |
| T74 · 16030–16601 | Direction and exploration | Make specifications usable by different implementation agents. Document mathematics, units and complementary formal, numerical and empirical checks. | ENG-001, VERIFY-001, KNOWLEDGE-001 | 019, 025 |
| T75 · 16602–17194 | Direction and proposals | Prefer Python and FastAPI for backends. Evaluate lower-level languages on a demonstrated need. Preserve the industrial-stack and implementation rationale. | PLATFORM-001, OT-001 | 020 |
| T76–T77 · 17195–17275 | Direction | Retain detailed reasoning and decisions across the series. Control when enterprise design begins. | KNOWLEDGE-001, ARCH-000, PLAN-001 | 025 |

### Enterprise platform and upstream ontology

| Exchange · source lines | Standing | Discussion and disposition | Destination | Related ADRs |
|---|---|---|---|---|
| T78 · 17276–17502 | Proposal | Set responsibilities across local/cloud runtime, transactional stores, analytical compute and durable data. | PLATFORM-001, ARCH-000 | 003, 004, 018 |
| T79 · 17503–17786 | Direction | R2 is an explicit exception to the open-source preference. No Neo4j Enterprise entitlement for PPC. Consider free hosting and T80–81. | PLATFORM-001, GRAPH-001 | 003, 010 |
| T80–T82 · 17787–18511 | Exploration | Evaluate exe.dev for Neo4j/Postgres, managed services, S3-compatible alternatives, DuckDB and Databricks roles, and ParadeDB. Availability is not a deployment record. | PLATFORM-001, DATA-001 | 003, 004, 010, 017, 018 |
| T83 · 18512–18839 | Case input | Use market-brief observations to motivate scenario variants. Qualify the source, timing and PPC exposure separately. | SCENARIO-001, WORLD-001 | 002, 031 |
| T84 · 18840–19093 | Exploration | Evaluate OCR and document indexing for evidence extraction. Retain source-page provenance and assess accuracy. | EVID-001, EDI-001 | 026, 030, 032 |
| T85–T87 · 19094–20233 | Mixed | Databricks compatibility is required at T86. Delta is a preferred candidate. Preserve incumbent ADRs and distinguish data ownership, storage format and execution engine. | DATA-001, PLATFORM-001 | 003, 004, 017, 018 |
| T88 · 20234–20377 | Reference | Discussion interprets supplied diagrams as design examples. Original image details remain a separate source check. | ARCH-000, UX-001 | 025 |
| T89–T92 · 20378–21238 | Direction | Use KPI Store 1.2 as the starting point for the company-agnostic process ontology. Keep PPC-specific language out of the upstream agent instructions. | INFO-001, ARCH-000 | 033, 035, 038 |
| T93 · 21239–21308 | Checkpoint | Resume enterprise design with process ontology handled on its own track. | PLAN-001, ARCH-000 | 033, 038 |

### Integration, data products, intelligence and verification

| Exchange · source lines | Standing | Discussion and disposition | Destination | Related ADRs |
|---|---|---|---|---|
| T94 · 21309–21820 | Proposal | Model transaction lifecycles and systems of record, including operational, logistics, commercial and financial events. | INT-001, WORLD-001 | 001, 023, 024 |
| T95–T96 · 21821–22670 | Proposal | Compare Kafka and NATS, CDC and batch. Preserve source records, integrated facts and governed releases with reconciliation. | INT-001, DATA-001 | 015, 016, 017 |
| T97 · 22671–23139 | Proposal | Use crude-quality failure to trace custody, quality, holds, planning and commercial effects. Capture replays, corrections and timing. | SCENARIO-001, INT-001, WORLD-001 | 001, 024 |
| T98–T99 · 23140–24080 | Proposal | Define domain products, grain, dimensions and ownership before storage schemas. | DATA-001, INFO-001 | 013, 033, 039 |
| T100 · 24081–24496 | Direction | Separate measure classes and expose KPI constituent metrics, formula, grain and lineage. | DATA-001, ANALYTICS-001 | 013, 034, 039 |
| T101–T102 · 24497–25135 | Mixed | Govern KPI definitions, calculations and consumption. Assess Ossie as a semantic tool against the governing contracts. | DATA-001, INFO-001 | 013, 034, 039 |
| T103–T105 · 25136–26620 | Proposal | Separate concepts, source records and instances, govern identity resolution and translate meanings across representations with explicit mapping strength. | INFO-001, GRAPH-001 | 005, 008, 009, 010, 033 |
| T106 · 26621–27130 | Proposal | Separate technical metadata, lineage, evidence, provenance and governance. Qualify each claim against cited evidence. | EVID-001, PLATFORM-001 | 007, 012, 026, 027, 032 |
| T107–T109 · 27131–28168 | Mixed | Specify business workflows and governed natural-language analytics. Trading/risk and integration diagrams are use-case references, not PPC deployments. | UX-001, DATA-001, EVID-001 | 013, 023, 034 |
| T110–T112 · 28169–29059 | Mixed | Use browser graph exploration for business investigation and scenario impact. Distinguish connectivity, modeled sensitivity and measured change. Relate requires qualification. | UX-001, GRAPH-001, ANALYTICS-001 | 010, 014, 019 |
| T113 · 29060–29652 | Proposal | Compare cross-platform results, business relevance, semantic correctness and analytical trust. | VERIFY-001, ANALYTICS-001 | 019, 032, 037 |
| T114–T115 · 29653–30906 | Proposal | Version training/evaluation data, independently qualify numerical models and optimization, record causal assumptions, uncertainty and feasibility. | ANALYTICS-001, ENG-001 | 019, 034 |
| T116–T118 · 30907–32583 | Mixed | Use bounded analytical tools and consequential-action policy. Evaluate agent frameworks and observability candidates without overriding PPC-011/012. | AGENT-001, EVID-001, PLATFORM-001 | 019, 020, 026, 029 |
| T119 · 32584–33077 | Proposal | Define deployment and recovery responsibilities for exe.dev, R2 and Databricks. Verify entitlements and capacity before implementation. | PLATFORM-001 | 003, 004, 010, 018 |
| T120–T121 · 33078–34583 | Proposal | Pin multi-repository releases, inputs and watermarks. Use explicit outbox, inbox, reconciliation and recovery contracts. | PLATFORM-001, INT-001, DATA-001 | 012, 015, 016, 038 |
| T122 · 34584–35266 | Proposal | Minimum viable enterprise and two golden slices. Start with one connected refinery, then derate and quality rejection. Preserve the charter hurricane case. | SCENARIO-001, WORLD-001, PLAN-001 | 001, 019, 037 |
| T123–T124 · 35267–36608 | Proposal | Inventory capability maturity and preserve normative rules, design rationale, implementation packages and verification as distinct views. | ARCH-000, KNOWLEDGE-001, PLAN-001 | 025, 038 |
| T125 · 36609–37482 | Proposal | Define engineering contracts with units, independent oracles and envelopes. Preserve tank-balance and reduced-order derate examples. | ENG-001, WORLD-001, VERIFY-001 | 001, 019 |
| T126 · 37483–37881 | Proposal | Sequence readiness gates and agent-neutral work packages before implementation. Independent numerical checks and evidence required. | PLAN-001, VERIFY-001, KNOWLEDGE-001 | 019, 025, 037 |

### Reconciliation, documentation and handoff

| Exchange · source lines | Standing | Discussion and disposition | Destination | Related ADRs |
|---|---|---|---|---|
| T127–T130 · 37882–38393 | Mixed | Place comprehensive docs in a dedicated PPC folder. Reconcile actual repository content and KPI 1.2. Independent review follows publication. | ARCH-000, PLAN-001 | 025, 038 |
| T131–T135 · 38394–39144 | Owner clarification | The generalized branch is a placeholder in the inspected baseline. A separate effort owns the release. PPC consumes an approved version; keep its local binding pending. | INFO-001, ARCH-000 | 033, 035, 038 |
| T136–T139 · 39145–39646 | Direction and analysis | Complete documentation and publish before handoff. Preserve existing baseline, record decisions and identify gaps. | ARCH-000, PLAN-001, KNOWLEDGE-001 | 025, 038 |
| T140–T142 · 39647–40358 | Proposal | Reconcile all 39 ADRs, pin repository authorities, register 19 documents and sequence authoring and verification. | ARCH-000, KNOWLEDGE-001, PLAN-001 | 025, 038 |
| T143–T145 · 40359–40519 | Publication | Author the draft master index, publish in PPC and move to WORLD-001. PR 3 was subsequently corrected and merged; the document remains draft. | ARCH-000, WORLD-001, PLAN-001 | 025 |

## Physical and numerical engineering coverage

[ENG-001](../02-industrial-engineering/PPC-ENG-001_Physical_and_Numerical_Engineering.md) §7 records its routed exchanges, including T37–38, T45, T51–52 and T114–115. Its worked arithmetic is a specification check; calibration, holdout accuracy, production tolerances and runtime behavior remain open.

## Items still open

- **`GAP-002` reconciled for Markdown transcript text (2026-11-26).** All 145 owner prompts and decision tables in `ChatGPT-Downstream Backcasting Research-20261125-2232.md` were audited directly in [PPC-REVIEW-001 §5](../independent-review/PPC-REVIEW-001_Document_Coverage_and_Transcript_Audit.md#5-audit-of-raw-chatgpt-transcript-t1t145-versus-ef4eb08-ppc-documents-closing-gap-002), and all 12 previously downgraded owner decisions are now recorded in [ADR-0040](../../adr/0040-staged-mechanistic-refinery-model-and-closed-flowsheet.md)–[ADR-0053](../../adr/0053-legacy-data-quarantine-and-world-export-bundle.md) and propagated across all 19 specifications. See the WORLD-001 decision crosswalk above and the [WORLD-002 section crosswalk](../01-enterprise-world/PPC-WORLD-002_Simulation_Time_Replay_and_Branches.md#9-source-crosswalk-and-handoff).
- **Original attachments.** T72 and T83 refer to market material. T88, T90 and T108 refer to screenshots. The export records the discussion, but a screenshot interpretation or a market excerpt is insufficient to qualify a numerical assumption. Recheck the original asset before using it as engineering or market evidence.
- **Approval and validation.** An exchange locator is evidence that a subject was discussed. A passed test needs a fixture, its expected and observed results, and a qualified version. The independent architecture review and Phase 0 authorization remain later steps.

## Industrial information coverage

[OT-001](../02-industrial-engineering/PPC-OT-001_Industrial_Information_Architecture.md) §6 maps T53–58 and edge-model exploration to specific sections. The T54 validation direction and T55 license constraint retain their source standing. §4 distinguishes the merged derate ledger from new observation fixtures. The pinned ICE L0 record supports replay (`scada_harmonization` `main` @ `30c20c3`), while mapping YAML and Sparkplug publication remain upstream gaps (`GAP-004`). OT-01 through OT-06 name the runtime evidence required in WP-2/WP-4; `GAP-002` Markdown transcript audit is reconciled in [PPC-REVIEW-001 §5](../independent-review/PPC-REVIEW-001_Document_Coverage_and_Transcript_Audit.md#5-audit-of-raw-chatgpt-transcript-t1t145-versus-ef4eb08-ppc-documents-closing-gap-002).

## Engineering information integration coverage

[EDI-001](../02-industrial-engineering/PPC-EDI-001_Engineering_Information_Integration.md) §§1–2 and §5 cover T37–38 (lines 6504–6917), which explored P&ID topology and the evidence and licensing needed to reuse public drawings. For T39–42 (lines 6918–7265), §§1–3 describe how the engineering specialist reviews and publishes a revision and how PPC adopts it. T43–44 maps to §§1 and 4 on coherent company history and reusable test fixtures. T84 maps to §§2 and 5 on extraction evidence and accuracy. §4 reconciles the pinned upstream structured results with the new PPC adoption example. GAP-005 and PPC runtime qualification remain open.

## Enterprise ontology, identity and time coverage

[INFO-001](../03-enterprise-information/PPC-INFO-001_Enterprise_Ontology_Identity_and_Time.md) §1 records the separate upstream process release and EPM authority (T6–8, T32, T89–92 and T131–135). §2 covers the source, tag and enterprise identity questions in T56–57 and T68–70. §§2–4 connect T62, T98–99 and T101–105 to mapping strength, decision-time reconstruction and semantic compatibility. T93 routes to PLAN-001 and ARCH-000. §4 records the SEM and EA05C verification targets and outstanding runtime evidence.

## Remaining draft destination crosswalk

This table reproduces the destinations recorded in the Exchange Register above. It is generated from those rows by `check_package.py`; editorial coverage in each draft can cite additional exchanges, but those citations do not change recorded routing. It does not establish exhaustive OT/EA disposition or approval. The CSV supplies finer line locators. Original images, market attachments and interactive output still need source checks under GAP-002.

| Draft | Source exchanges and destination sections | Standing and limit |
|---|---|---|
| [GRAPH-001](../03-enterprise-information/PPC-GRAPH-001_Enterprise_Instance_Graph.md) | T62, T79, T103–105, T110–112 → §§1–4 | Reconciled (`ADR-0044`, `0051`, `0052`); runtime planned |
| [DATA-001](../03-enterprise-information/PPC-DATA-001_Data_Products_KPIs_and_Analytical_Releases.md) | T4–5, T50, T80–82, T85–87, T95–96, T98–102, T107–109, T120–121 → §§1–4 | Delta Lake on R2 + T100 measure classes locked (`ADR-0045`); runtime planned |
| [INT-001](../04-source-integration/PPC-INT-001_Source_Lifecycles_and_Integration.md) | T33–34, T55, T66–67, T94–97, T120–121 → §§1–4 | Outbox + NATS JetStream + Dagster locked for Slice 1 (`ADR-0046`); runtime planned |
| [EVID-001](../04-source-integration/PPC-EVID-001_Evidence_and_Decision_Context.md) | T3–5, T26–27, T31–33, T72, T84, T106–109, T116–118 → §§1–4 | Provisional ECE adapter locked (`ADR-0042`, `0053`); 5 external attachments unavailable |
| [ANALYTICS-001](../05-intelligence-experience/PPC-ANALYTICS-001_Performance_Intelligence_and_Optimization.md) | T1–3, T24, T26, T35, T59–61, T100, T110–115 → §§1–3 | Pyomo + HiGHS/IPOPT locked (`ADR-0048`); Scenario A reconciled; runtime planned |
| [UX-001](../05-intelligence-experience/PPC-UX-001_Enterprise_Intelligence_Workspace.md) | T2, T13–18, T36, T53, T71, T88, T107–112 → §§1–3 | Two-stage UX locked: Dash Slice 1, Relate WASM Slice 1.5 (`ADR-0047`, `0052`) |
| [AGENT-001](../05-intelligence-experience/PPC-AGENT-001_Agent_Tools_and_Consequential_Actions.md) | T116–118 → §§1–3 | LangGraph + Pydantic tools + OTel/self-hosted Langfuse locked (`ADR-0048`); runtime planned |
| [PLATFORM-001](../06-platform-operations/PPC-PLATFORM-001_Infrastructure_Security_and_Operations.md) | T46–52, T59–61, T66–67, T75, T78–82, T85–87, T106, T116–121 → §§1–3 | `exe.dev` + R2 + Databricks + RPO/RTO locked (`ADR-0051`); restore drill planned |
| [VERIFY-001](../07-scenarios-verification/PPC-VERIFY-001_Verification_and_Release_Qualification.md) | T1, T25–26, T54, T58, T73–74, T113, T125–126 → §§1–3 | Quint + Z3/Hypothesis + benchmarks locked (`ADR-0050`, `PPC-REVIEW-004`); planned |
| [SCENARIO-001](../07-scenarios-verification/PPC-SCENARIO-001_Golden_Enterprise_Scenarios.md) | T1, T19, T45, T58, T72, T83, T97, T122 → §§1–4 | Unified `UC-1`–`UC-6` (`ADR-0049`) + mechanistic `EQ-05`/`EQ-07` derate; planned |
| [PLAN-001](../08-implementation/PPC-PLAN-001_Implementation_Work_Packages_and_Readiness.md) | T21, T34, T46–47, T63–65, T76–77, T93, T122–124, T126–130, T136–145 → §§1–5 | Detailed work packages `WP-0`–`WP-8` ready; awaiting Phase 0 authorization |
| [KNOWLEDGE-001](../09-architecture-knowledge/PPC-KNOWLEDGE-001_Architecture_Learning_and_Design_Rationale.md) | T22, T25, T28–30, T46–47, T63–65, T74, T76–77, T123–124, T126, T136–142 → §§1–4 | Reconciled rationale ledger (`ADR-0040`–`0053`, `PPC-REVIEW-001`–`004`) |
