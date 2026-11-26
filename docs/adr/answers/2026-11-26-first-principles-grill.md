# Owner Answers — First-Principles Refinery Grill Session (2026-11-26)

This file records the exact questions, recommendations, and verbatim owner answers from the `/grill-with-docs` session on branch `docs/first-principles-refinery-grill` (baseline `ef4eb08`). Markdown formatting in quoted questions and recommendations is preserved as asked.

## Round 1 (2026-11-26)

### Q1 — Mission boundary and deliverable

**Question:**
Your prompt describes an ambitious plan to build a refinery from first principles with coherent enabling systems, while the attached handoff brief sets a strict documents-only boundary that reconciles the `ef4eb08` PPC architecture package and stops after delivering an implementation plan. Should we treat PPC as the single target enterprise laboratory, use this interview to lock your owner decisions, glossary terms, and ADRs, and stay strictly documents-only through architecture reconciliation and the implementation plan (holding all code and prototypes until separate Phase 0 authorization)?

**Recommendation:**
Yes. Keep PPC as the single target, stay strictly documents-only through architecture reconciliation and the implementation plan, and wait for separate authorization before any Phase 0 code or prototypes.

### Q2 — What "first principles" means for refinery physics

**Question:**
Right now, PPC-ENG-001 relies on reduced-order rules (such as a linear 0.75 availability cap on hydrocracker feed), while PPC-001 states that PPC is not a production refinery simulator. Which physical ceiling do you mean by building the refinery from first principles?

1. Conservation-exact reduced order only — transient mass, element, and energy balances, assay splits, mode yield tables, linear or empirical blend rules, and utility caps.
2. Staged mechanistic core on a conservation-exact plant spine — strict transient mass, sulfur/hydrogen element, and energy conservation across the full refinery from day one, adding mechanistic unit equations (shortcut or stage vapor-liquid equilibrium, lumped reaction kinetics, polytropic compressor curves, nonlinear octane and RVP blending) only where thermodynamics or dynamics change an operational or commercial decision.
3. Full dynamic process simulator from day one — rigorous DAE tray-by-tray thermodynamics, detailed reaction kinetics, regulatory control loops, and pipe-network hydraulics across every unit.

Should we adopt option 2 and define `First-principles refinery model` in the glossary with that exact boundary?

**Recommendation:**
Yes. Adopt option 2 so every plant balance is physically closed from day one, while deeper mechanistic equations enter wherever they materially change an operating or commercial decision.

### Q3 — Canonical refinery flowsheet boundary (Refinery A v1)

**Question:**
PPC-001 scopes three process units (CDU, FCC, hydrocracker), whereas PPC-WORLD-001 and the handoff require crude receipt, tankage, routing, shared hydrogen and utilities, blending, quality release, and dispatch. Without a vacuum separation step (or explicit heavy-cut boundary), a shared hydrogen balance, and a tank-and-blending layer, the FCC and hydrocracker cannot close mass or propagate a compressor derate coherently.

Should we lock Refinery A v1 as the minimum physically closed flowsheet — crude receipt and tankage, CDU plus VDU (or an explicit atmospheric/vacuum cut boundary), FCC, hydrocracker, shared hydrogen and utility header, product blending, finished tankage, quality release, and dispatch — while treating hydrotreating, sulfur recovery, and steam/power as explicit bounded mass-and-utility interfaces until a scenario needs internal unit equations?

**Recommendation:**
Yes. Lock that minimum physically closed flowsheet as Refinery A v1, with declared mass, element, and utility boundary terms for units outside the v1 core.

### Q4 — Posture toward the enabling-systems stack

**Question:**
PPC-REG-001 commits to over twenty products (Twenty CRM, ERPNext, Postgres, MySQL, SQLite, Debezium, Kafka, Dagster, DuckLake, Databricks, OpenMetadata, GX, OpenLineage, Jena/Fuseki, Neo4j, Dash, Superset, Grafana, LangGraph, Langfuse, OR-Tools, Cloudflare R2/D1), and PPC-ARCH-000 flags seven of those ADRs for reassessment plus new OT and agent candidates. Before we evaluate individual tools in Round 2, which overall posture should govern the enabling systems?

1. Function-first lean core plus staged extensions — define the refinery's operational and business functions first, commit the smallest coherent runnable stack that proves the full physical-to-decision loop in Slice 1, and explicitly defer or retire heavy products via ADR until a scenario demands them.
2. Full baseline stack from Slice 1 — stand up all baseline products early to test full enterprise heterogeneity immediately.
3. Permanent hard prune — strip PPC down permanently to a lightweight Python-first lab and retire heavy enterprise tools such as ERPNext, Twenty, Databricks, Kafka, and OpenMetadata.

Should we adopt option 1?

**Recommendation:**
Yes. Adopt option 1 so we prove physical, temporal, semantic, and decision coherence on a lean runnable core first without discarding the broader enterprise roadmap.

### Q5 — Sister-repository coupling and `enterprise-people-graph` scope

**Question:**
Four upstream dependencies in PPC-DEPENDENCY-AND-COMPATIBILITY.md do not yet have released reusable packages (`DS_Business_Process`, ICE mapping YAML, full EDI drawing extraction, and ECE reusable schemas). Meanwhile, `enterprise-people-graph` sits in your local workspace but is absent from PPC.

Should PPC decouple its schedule from upstream release calendars by using versioned provisional adapters pinned to the current commits of EPM, ICE, EDI, and ECE (while explicitly marking pending upstream dependencies as unapproved), and keep `enterprise-people-graph` out of PPC v1?

**Recommendation:**
Yes. Use versioned provisional adapters pinned to current upstream commits for EPM, ICE, EDI, and ECE, and keep `enterprise-people-graph` out of PPC v1.

### Q6 — Where to record glossary terms and ADRs as we grill

**Question:**
PPC already has PPC-TERMINOLOGY.md, PPC-REG-001 (ADR-001 through ADR-039), and PPC-ADR-RECONCILIATION.md. To avoid two competing glossaries or silently overwriting baseline ADRs, should we work on a dedicated docs branch (once Round 1 settles), write the canonical domain glossary to a root `GLOSSARY.md` (with `PPC-TERMINOLOGY.md` pointing to it), and record new hard-to-reverse decisions in `docs/adr/` starting at `0040-` while keeping `PPC-REG-001` intact?

**Recommendation:**
Yes. Use a dedicated docs branch with root `GLOSSARY.md` as the single domain glossary and `docs/adr/0040-...` for new decisions, preserving `PPC-REG-001` as the baseline record.

### Owner verbatim response (Round 1)

> Q1. Yes. Everything we created from first principle in PPC is meant to be used by the other repos listed in PPC docs. The world model is created in PPC. and the technological choices made must align with PPC and other repos golas . You will see sections on repo responsibility innthe doc.
>
> Q5: We will keep people graph out for now. Also the genralized ontology will be a sperate step.
>
> yes to all other

## Round 2 (2026-11-26)

### Q7 — Unit-by-unit mechanistic scope in Refinery A v1

**Question:**
Round 1 locked a conservation-exact transient mass, sulfur/hydrogen element, and energy spine across Refinery A v1, with mechanistic equations added where thermodynamics or dynamics change an operating or commercial decision. Should we lock the following v1 physics split for PPC-ENG-001?

1. Tankage and transfer headers — transient mass and component-property conservation with exact intra-step bound-crossing detection (no end-of-step clipping), plus hydraulic pump and line capacity limits where routing constrains movement.
2. CDU and VDU — crude-assay TBP/D86 cut-point separation model (cut-point shift and overlap, temperature-compensated density and Watson K, sulfur distribution by cut) rather than tray-by-tray flash.
3. Hydrocracker (HCU) and recycle-gas compressor — polytropic compressor head and capacity curve coupled to hydrogen circulation and H2-to-oil ratio, driving a lumped-conversion and hydrogen-consumption closure (replacing the ungrounded linear 0.75 availability cap).
4. FCC — lumped severity yield plus coke-and-heat-balance closure (feed Watson K and carbon residue plus riser severity producing gas, LPG, gasoline, LCO, slurry, and coke, bounded by regenerator air-blower coke burn).
5. Product blending and quality release — mass-basis mixing for sulfur and density plus nonlinear blending indices for RON/MON octane, RVP, flash point, and ULSD cetane/cloud point, keeping quality hold and lot release separate.
6. Shared hydrogen and utilities — plant-wide header balances (producers minus committed consumers), with hydrotreating, sulfur recovery, and steam/power generation represented as declared bounded mass-and-utility interface units in v1.

**Recommendation:**
Yes. Adopt this six-part unit split as the governing v1 physics scope for Refinery A.

### Q8 — Canonical simulation clock and multi-rate synchronization

**Question:**
Refinery physics, ICE telemetry (1 s machine streams and 180 s process streams), hourly scheduling, and daily production accounting run on different clocks. Which execution clock should govern PPC-WORLD-002?

1. Hybrid event-and-step clock — a deterministic 1-minute canonical process balance step with exact analytical or root-finding splits at intra-step tank or constraint crossings, an optional 1-second synthetic equipment-telemetry projection layer for fast ICE machine tags (vibration, compressor speed), and explicit UTC-to-site-business-day calendars for shifts and accounting (handling 23-hour and 25-hour DST days).
2. Pure hourly discrete-time step — matches LP planning directly, but cannot drive realistic sub-hour OT observations or tank crossings without artificial interpolation.
3. Full continuous variable-step DAE solver across all units — high implementation complexity and harder deterministic checkpointing across coupled engines.

Should we adopt option 1?

**Recommendation:**
Yes. Adopt option 1 so the canonical world stays deterministic and checkpointable while supporting exact constraint crossings, ICE fast-class telemetry, and site accounting calendars.

### Q9 — Formal semantics and graph serving path (ADR-009 and ADR-010)

**Question:**
enterprise-performance-model and scada_harmonization both use Git Turtle validated by pyshacl as the formal semantic source of truth and project directly into Neo4j Community for runtime queries, with no standing triple store in production. PPC's baseline ADR-009 still requires a standing Apache Jena/Fuseki server.

Should we amend ADR-009 so Git Turtle plus rdflib/pyshacl validation at release time feeding Neo4j Community (ADR-010) is PPC's canonical runtime path — aligning directly with EPM and ICE — while keeping Apache Jena/Fuseki optional for offline SPARQL testing and homelab learning only?

**Recommendation:**
Yes. Make Git Turtle plus pyshacl validation feeding Neo4j Community the canonical serving path, and demote Jena/Fuseki to an optional offline verification tool.

### Q10 — Analytical table format and Databricks role (ADR-017 and ADR-018)

**Question:**
ADR-017 selects DuckDB and DuckLake, while ADR-018 keeps Databricks Free Edition as a parallel enterprise lab. Meanwhile, PPC-DATA-001 requires atomic business-consistent release manifests on Cloudflare R2, and EPM's demos already exercise both DuckDB and Databricks Free Edition. Which analytical storage contract should govern PPC?

1. Delta Lake on Cloudflare R2 (single-writer controlled through Dagster and pinned by immutable ReleaseManifest records), queried locally by DuckDB and directly portable to Databricks Free Edition in a later verification phase — replacing DuckLake so one open table format serves both local compute and Databricks without a translation bridge.
2. Keep DuckLake on R2 as the primary analytical format in Slice 1, and maintain a separate export step whenever Databricks Free Edition is tested.
3. Versioned Parquet plus immutable JSON ReleaseManifest files on R2 for Slice 1 (matching scada_harmonization L0), deferring the Delta-versus-DuckLake table-format choice until concurrent multi-writer needs arise.

Should we adopt option 1 (Delta Lake on R2 with single-writer ReleaseManifest discipline, DuckDB for local compute, and Databricks Free Edition staged as a post-Slice-1 portability phase)?

**Recommendation:**
Yes. Adopt option 1 so DuckDB and Databricks Free Edition share one open table format on R2 while keeping Databricks off the Slice 1 critical path.

### Q11 — OT and IT event transport and change capture (ADR-015, ADR-016, and OT-001)

**Question:**
On the OT side, scada_harmonization uses OPC UA (asyncua), MQTT with Sparkplug B (Mosquitto), and TimescaleDB/PostgreSQL or Parquet L0. On the IT side, PPC's baseline ADR-015 and ADR-016 select Dagster, Apache Kafka, and Debezium CDC, while PPC-INT-001 proposes a transactional outbox and NATS JetStream as lighter alternatives. Which integration topology should govern Slice 1 and later stages?

1. Clean OT/IT split with lean IT core — keep OPC UA plus MQTT/Sparkplug B and PostgreSQL/TimescaleDB on the OT plane (aligned with ICE), keep Dagster for orchestration, and use transactional outbox tables in IT source databases plus NATS JetStream for IT event transport in Slice 1; defer Kafka and Debezium to an optional enterprise-scale swap phase.
2. Full baseline IT stack from Slice 1 — run OPC UA/MQTT on OT alongside Kafka, Debezium, and Dagster on IT immediately.
3. Brokerless IT batch for Slice 1 — keep MQTT/Sparkplug B on OT, and let Dagster pull IT outbox tables straight to R2 without Kafka or NATS until streaming latency requires an IT broker.

Should we adopt option 1?

**Recommendation:**
Yes. Adopt option 1 so OT matches scada_harmonization, IT tests real pub/sub replay and outbox/inbox crash recovery with a minimal footprint, and Kafka/Debezium stay cleanly deferred.

### Q12 — Slice 1 versus staged scope for source systems, catalog, and UI (ADR-007, ADR-014, ADR-022, ADR-023)

**Question:**
Under our function-first lean core posture (ADR-0041), Slice 1 (hydrocracker compressor derate) and Slice 2 (crude-quality rejection) need genuine cross-system heterogeneity without carrying unrelated enterprise apps before their scenarios arrive. Should we lock the following staged rollout?

- Active in Slice 1 and Slice 2: OT/historian stack (ICE boundary), Refinery/LIMS edge store (SQLite), Commercial/CTRM store (PostgreSQL), Logistics store (MySQL), Cloudflare R2 durable storage, DuckDB/Delta analytical store, Neo4j Community, and a bounded FastAPI plus Plotly Dash workspace (keeping Relate WASM as a separate post-authorization UI prototype, not a Slice 1 dependency).
- Explicitly deferred to later scenarios (contracts preserved, not retired): Twenty CRM (ADR-022) and ERPNext (ADR-023) until O2C/commercial-finance scenarios; OpenMetadata (ADR-007) and Grafana until the governance/observability phase (keeping lightweight Great Expectations and OpenLineage manifests active early); Apache Superset until multi-KPI BI scorecard phases.

**Recommendation:**
Yes. Lock this Slice 1 active core and defer Twenty, ERPNext, OpenMetadata, Superset, and Grafana to their respective later scenarios while keeping Relate WASM experimental.

### Q13 — Optimization, analytics, and agent framework choices (PPC-011 and PPC-012)

**Question:**
PPC-011 records OR-Tools for optimization and PPC-012 records LangGraph and Langfuse for agent workflows and tracing. Later drafts raised Pyomo/HiGHS, Pydantic AI, and OpenTelemetry/Logfire as candidates. Keeping your Python/FastAPI preference and no-paid-runtime constraint in mind, should we:

1. Adopt Pyomo with HiGHS (extending to IPOPT when nonlinear blending or kinetics enter) as the canonical optimization modeling stack instead of OR-Tools, because algebraic refinery formulations are easier to audit, verify against conservation equations, and extend from LP to NLP.
2. Keep LangGraph for stateful human-approval and escalation workflows, use Pydantic AI (or Pydantic-typed tool contracts) inside nodes for strict schema-validated tool calls, and use OpenTelemetry exporting to self-hosted Langfuse (instead of paid Logfire cloud) with PostgreSQL/pgvector for evidence retrieval and Ollama/local-or-configured LLM endpoints.

**Recommendation:**
Yes. Adopt Pyomo plus HiGHS/IPOPT for refinery optimization, and use LangGraph with Pydantic-typed tool contracts and OpenTelemetry to self-hosted Langfuse.

### Owner verbatim response (Round 2)

> Q7: yes . As long as the outcome help us determine all of the business use cases that we want to enable
>
> Q9: Yes. remeber the ontology that will be specialized for PPC will be generalize from KPI 1.2 in downstreal oil and gas ontology release. The generalized version will be in the ds business process branch in the downstreal oil and gas release repo
>
> Q10: this decision was already made to use Delta Table since the eventual target platform will be Databricks. didnt you see it in the chat conversations@[/Users/hamidadesokan/Downloads/ChatGPT-Downstream Backcasting Research-20261125-2232.md] i have attached the raw converations from all the documents was created form here for additional context.
>
> Yes to the rest. from some of the questions you are asking it looks like the decisiosn we made outside of here did not make it to the documents created in PPC repo

## Round 3 (2026-11-26)

### Q14 — Complete v1 business use-case catalog (Q7 condition)

**Question:**
In Q7 you made the v1 physics split conditional on enabling all target business use cases. Combining PPC-001, SCENARIO-001, and your ChatGPT transcript (T1–T3, T36, T72, T83, T100, T111, T122), six core business use cases emerge:

1. UC-1 — Hydrocracker compressor derate and response (physical derate → H2 circulation and severity limit → ULSD yield and tank trajectory → exposed contracts → feasible optimization, policy-gated action, and backcast attribution).
2. UC-2 — Crude-quality rejection and delayed lab correction (custody receipt → late or disputed LIMS assay → physical presence versus commercial quality hold → CTRM and planning rerouting → late restatement without altering earlier decision-time knowledge).
3. UC-3 — Operational and opportunity-based backcasting (reconstructing a completed shift or month from actual prices, assays, and constraints to separate LP model calibration error, decision quality, and execution deviation).
4. UC-4 — Interactive scenario exploration, economic mode swing, and KPI decomposition (user introduces a constraint, market-brief crack-spread shift, or operating intervention such as max-distillate versus max-gasoline swing → isolated branch recomputation → decomposing KPIs into operational metrics and market indicators).
5. UC-5 — Gulf Coast hurricane disruption and supply-chain response (preserved PPC-001 charter scenario linking observed NOAA advisories and EIA PADD 3 stocks to refinery/terminal exposure, customer OTIF, spot replacement, margin-at-risk, approval, and learning).
6. UC-6 — Cross-repository coherent world benchmark (generating realistic OT, ET, IT, and unstructured evidence from one canonical Refinery A world so ICE, EDI, EPM, and ECE all run against the same coherent enterprise).

Should we lock UC-1 through UC-6 as the complete v1 business use-case catalog that every physical equation and enabling system must trace to?

**Recommendation:**
Yes. Lock UC-1 through UC-6 as the governing v1 use-case catalog, with max-distillate versus max-gasoline mode swing explicitly covered by the CDU/VDU, FCC, HCU, and blending equations.

### Q15 — Formal verification stack and proof-obligation scope (T26 and T74)

**Question:**
In T74 you shared 17 formal-methods tools and the discussion proposed Quint, Alloy 6, and Dafny/Z3 (with Kani and Bend 2 as experiments), while PPC-ENG-001 and PPC-VERIFY-001 left the selection open. Maintaining four or five proof languages creates high specification drift, whereas a tight two-tool core plus engineering benchmarks covers every proof obligation in the handoff:

1. Quint (checked by Apalache/TLC) for discrete state machines, event ordering, idempotent retry, branch isolation, reader-as-of cutoffs, and approval lifecycles.
2. Python with z3-solver and Hypothesis property-based tests for exact conservation and feasibility invariants (detecting intermediate tank overflow despite legal closing stock, preventing double allocation of shared hydrogen, and rejecting duplicate physical effects on retry).
3. Independent published engineering benchmarks and analytical oracles (primary process-engineering equations, textbook balances, and EIA/public plausibility checks) for continuous numerical convergence and empirical refinery credibility.
4. Defer Alloy 6, Dafny, Kani, and Bend 2 to targeted later investigations only when a concrete proof obligation exceeds Quint or Z3 (or when a Rust component enters ICE/EDI).

Should we adopt this minimal verification stack as PPC's formal and empirical assurance baseline?

**Recommendation:**
Yes. Lock Quint, Python/Z3 with Hypothesis, and independent engineering benchmarks as the primary verification stack, keeping Alloy, Dafny, Kani, and Bend 2 deferred until a concrete obligation requires them.

### Q16 — Hosting topology (exe.dev, Cloudflare R2, Databricks) and recovery targets (T79–T81)

**Question:**
Your ChatGPT transcript established no paid commercial licenses, Cloudflare R2 as an explicit free-tier exception, no Neo4j Enterprise entitlement, and your exe.dev subscription to host Neo4j Community (avoiding AuraDB Free inactivity wipes) and PostgreSQL. However, PPC-PLATFORM-001 and PPC-RISKS-AND-OPEN-QUESTIONS.md still list hosting placement and recovery objectives as open. Should we lock the following topology and RPO/RTO contract?

- Durable source-of-truth tier (Cloudflare R2): raw public and source evidence, canonical world checkpoints, Delta Lake analytical tables, and immutable ReleaseManifest files.
- Operational runtime tier (exe.dev persistent VMs with local Docker Compose parity for dev/CI): PostgreSQL (CTRM, TimescaleDB historian, pgvector evidence, Dagster metadata), MySQL (Logistics), SQLite (Refinery/LIMS edge), NATS JetStream, Mosquitto (OT Sparkplug B), Neo4j Community (persistent /data volume, treated strictly as a rebuildable projection with offline neo4j-admin dump backups to R2), FastAPI backend, and Dash workspace.
- Enterprise portability tier (Databricks Free Edition → paid Databricks): reads the same Delta Lake tables on R2, staged off the Slice 1 critical path.
- Recovery objectives: zero silent data loss across committed world checkpoints and source outboxes (RPO = last committed manifest and WAL backup on R2), with full deterministic rebuild from R2 manifests and backups within 1 hour (RTO ≤ 1 hour), proven by a restore drill before Slice 1 release.

**Recommendation:**
Yes. Lock this exe.dev plus Cloudflare R2 plus staged Databricks topology and the RPO/RTO contract.

### Q17 — Reconciling Relate WASM's standing in the UX roadmap (T111 versus Q12)

**Question:**
In T111 (EA09D-D09, user-directed) you specified that Relate WASM in the browser is a business-facing Interactive Enterprise Context Explorer for investigating relationships, change impact, and scenario differences — not a teaching tool. In Round 2 Q12 you agreed not to make Relate WASM a Slice 1 critical-path blocker ahead of FastAPI and Dash.

Should we reconcile both positions into one two-stage UX contract: ship the bounded FastAPI plus Plotly Dash workspace in Slice 1 to prove the end-to-end decision loop, and formally commit Relate WASM as the immediate Slice 1.5 business-facing Interactive Enterprise Context Explorer gated on one bounded security and compatibility check (server-side permission filtering before browser graph packaging, strict POTENTIAL_EXPOSURE versus model-quantified labeling, and Cypher query parity on Slice 1 snapshots)?

**Recommendation:**
Yes. Lock that two-stage UX contract so Slice 1 ships cleanly on FastAPI/Dash and Relate WASM enters immediately after as a first-class business explorer once its security and compatibility gate passes.

### Q18 — Quarantine of pre-world-model synthetic data and the cross-repo export contract (T34, T43–T44, Q1)

**Question:**
In T34 and T43–T44 you noted that older synthetic datasets in Cloudflare R2 and Engineering_Drawing_to_Graph were created before this canonical world existed and cannot connect coherently across repositories. In Q1 you confirmed that PPC creates the canonical world model consumed by the listed sister repositories. Should we lock two boundary rules?

1. Quarantine before retirement: Do not delete legacy R2 objects or sister-repo fixtures during this documents-only phase; label them LEGACY_PRE_WORLD_MODEL under isolated prefixes and schedule archival or deletion only after PPC's WP-1 canonical world passes independent verification.
2. WorldExportBundle contract: Define one versioned export bundle owned by PPC (pinned world version, branch, seed, Delta tables, OT L0 tag schedule for ICE, structured equipment/topology manifest for EDI, KPI and process instance fixtures for EPM, and role-scoped evidence/dossier fixtures for ECE) so every sister repository consumes coherent data from Refinery A without reading hidden world truth as an integration shortcut.

**Recommendation:**
Yes. Lock both the legacy-data quarantine rule and the WorldExportBundle cross-repo publication contract.

### Q19 — Execution step once the design tree is settled

**Question:**
After Round 3 answers land, every branch of the design tree will be resolved. Which next step do you want me to run on this branch (docs/first-principles-refinery-grill)?

1. Execute the full documents-only handoff reconciliation now — close GAP-002 against the ChatGPT transcript, build the full document coverage matrix, research and embed primary-sourced governing refinery equations into PPC-ENG-001 and linked specs, produce the complete system-and-decision register and proof-obligation register (including the worked tank and derate counterexamples), reconcile PPC-PLAN-001 and PPC-014 into a full work-package implementation plan, run check_package.py and an independent review, and stop for your Phase 0 authorization.
2. Stop after closing the grill session — finalize only GLOSSARY.md, docs/adr/0040–0053, and updated decision registers on this branch, leaving the full equation research, spec edits, and implementation plan for a separate agent run.

Should we proceed with option 1 once you confirm our shared understanding after Round 3?

**Recommendation:**
Yes. Once you confirm Round 3, execute the full documents-only reconciliation and implementation plan on this branch and stop before any Phase 0 code or prototypes.

### Owner verbatim response (Round 3)

> Yes to all. Also do we need to take another look at the documents created in the PPC repo from the conversations. We went through each of the choices in that conversation.
