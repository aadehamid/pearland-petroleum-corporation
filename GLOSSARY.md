# Pearland Petroleum Corporation

Pearland Petroleum Corporation (PPC) is a fictional Gulf Coast downstream oil and gas enterprise laboratory that connects a coherent physical refinery world to independent operational, semantic, analytical, and decision systems. Upstream released ontology terms retain upstream authority; this glossary defines PPC domain language.

## Language

### World and physics

**Canonical World**:
The single fictional physical and commercial state of PPC used for simulation generation and blind evaluation.
_Avoid_: Ground truth, live plant, source database

**First-Principles Refinery Model**:
A refinery model that enforces exact transient mass, element, and energy conservation across the plant spine, adding mechanistic thermodynamic, kinetic, or hydraulic equations wherever they change an operating or commercial decision.
_Avoid_: Production refinery simulator, linear shortcut

**Refinery A**:
PPC's primary fictional Gulf Coast refinery, whose minimum physically closed flowsheet spans crude receipt and tankage, crude and vacuum distillation, fluid catalytic cracking, hydrocracking, shared hydrogen and utility headers, product blending, finished tankage, quality release, and dispatch.
_Avoid_: Three-unit plant, demo refinery

**Control Volume**:
A declared physical boundary around a tank, process unit, header, or site across which all entering, leaving, accumulated, and lost quantities are accounted on a compatible basis.
_Avoid_: Box, scope, node

**Branch**:
An isolated scenario history forked from a committed checkpoint to evaluate an alternative assumption or intervention without altering the parent history.
_Avoid_: Forked database, scenario copy

### Records, time, and authority

**Source Record**:
An assertion recorded by an independent operational or business system at its own lifecycle stage, which may lag, omit, or disagree with the canonical world.
_Avoid_: Canonical fact, plant truth

**Effective Time**:
The instant or half-open interval when a physical condition, installation, or commercial obligation applies in the modeled world.
_Avoid_: Recorded time, ingestion time

**Recorded Time**:
The instant a source application stores an assertion; it does not establish when a recipient could read that assertion.
_Avoid_: Effective time, availability time

**Availability Time**:
The instant a specific recipient or role can access a published revision through a named channel under historical authorization grants.
_Avoid_: Published time, current permission

**UNRESOLVED**:
The nondisclosing access-check result returned when no publication satisfies reader authorization, channel, delivery receipt, and cutoff rules, or when a required identity mapping resolves to zero or multiple unresolved targets.
_Avoid_: Unknown, access denied error

**UNKNOWN**:
An epistemic claim status stating that the accessible, authorized evidence cannot responsibly answer a question.
_Avoid_: Unresolved, missing permission

**Hidden Truth**:
The restricted canonical simulation ledger, evaluation decision rationales, and scoring keys stored under separate credentials under `evaluation/hidden/` and excluded from integration pipelines and blind agent retrieval.
_Avoid_: Visible corpus, agent context, ground truth

**Identity Steward (`IDENTITY_STEWARD`)**:
The single governance role (held by the PPC owner until delegated in writing, `ADR-0056`) authorized to accept, reject, or supersede conflicting identity mapping assertions; agents may propose candidates but never accept them.
_Avoid_: Auto-resolver, confidence merge

**POTENTIAL_EXPOSURE**:
The graph-connectivity label assigned when a topology path links a disrupted unit or stream to a downstream asset or commercial contract without a qualified model calculation establishing numeric impact.
_Avoid_: Quantified impact, confirmed loss

**QUALITY_HOLD**:
The inventory disposition state preventing a crude or product lot from entering blending, commercial availability, or dispatch until an authorized passing LIMS assay and release gate clear it.
_Avoid_: Soft warning, pending sale

**RECOVERY_GAP**:
The explicit halt condition raised on store restore when comparing a source outbox's highest committed sequence number against PostgreSQL `InboxReceipt` high-water marks and R2 raw logs reveals a missing tail inside the RPO window.
_Avoid_: Silent drop, best-effort catchup

### Process interface units and blending terms

**Steam Methane Reformer (SMR)**:
A hydrogen production interface unit that converts natural gas and steam into plant makeup hydrogen, fuel offgas, and carbon dioxide (`ADR-0054`).
_Avoid_: Unmodeled H2 source

**Naphtha Hydrotreater (NHT)**:
A hydrotreating interface unit that removes sulfur from light straight-run (LSR) and heavy straight-run naphtha (`<= 0.5 ppmw` sulfur) before gasoline blending or catalytic reforming (`ADR-0054`).
_Avoid_: Sweetening-only unit

**Diesel Hydrotreater (DHT)**:
A hydrotreating interface unit that removes sulfur and saturates aromatics in straight-run distillates and FCC light cycle oil (LCO) using plant hydrogen before ULSD blending (`ADR-0054`).
_Avoid_: Direct LCO blending

**Catalytic Reformer**:
A naphtha-upgrading interface unit that converts hydrotreated heavy naphtha and HCU heavy naphtha into high-octane reformate and byproduct hydrogen (`ADR-0054`).
_Avoid_: Straight-run gasoline blendstock

**FCC Selective HDS**:
A selective hydrodesulfurization interface unit that lowers FCC naphtha sulfur (`<= 10 ppmw` target `8 ppmw`) while minimizing olefin saturation and octane loss before gasoline blending (`ADR-0054`).
_Avoid_: Untreated FCC gasoline

**Sulfur Recovery Unit (SRU)**:
The Claus sulfur recovery and sour-water stripper interface unit converting `H2S` and `NH3` acid-gas streams into elemental sulfur export (`99.5%` recovery), boundary `SO2`, and `N2` (`ADR-0054`).
_Avoid_: Unaccounted sour gas

**Blendstock for Oxygenate Blending (BOB)**:
Sub-octane refinery-gate gasoline (`RBOB` or `CBOB`, `>= 84.2` regular / `>= 88.6` premium `(R+M)/2`) blended to meet retail octane (`87.0` / `91.0`) and RVP limits after terminal splash-blending with `10 vol%` denatured ethanol (`E10`).
_Avoid_: Finished retail gasoline at refinery gate

**Planning LP**:
The deliberately reduced linear optimization model (Pyomo + HiGHS, delta-base yield vectors, linear blend indices, lagged assays) kept structurally distinct from the nonlinear mechanistic Canonical World Kernel so `UC-3` LP calibration error is real and measurable (`ADR-0048`).
_Avoid_: Identical world clone, simulator optimizer

### Ecosystem boundaries

**Enabling System**:
An operational, industrial, commercial, analytical, or governance system that records, transports, stores, interprets, or acts on information around the physical refinery.
_Avoid_: Tech stack, tool list

**Provisional Adapter**:
A versioned boundary contract in PPC pinned to a specific upstream repository commit when that upstream repository has not yet published an approved release.
_Avoid_: Approved dependency, forked ontology

### Performance and backcasting

**Operational Backcasting**:
Reconstructing a completed operating period from actual prices, operating conditions, and historical records to compare a planning model's prediction against what physically occurred.
_Avoid_: Strategic backcasting, variance report

**Opportunity-Based Backcasting**:
Evaluating what the refinery or integrated value chain could feasibly have achieved during a completed operating period under the actual constraints and decision-time evidence to isolate recoverable value leakage.
_Avoid_: Hindsight blame, unconstrained optimum

**Measure Class**:
The governance category of a quantitative series, distinguishing governed KPIs, constituent operational metrics, and external market indicators.
_Avoid_: Metric bucket, report number

**Release Manifest**:
An immutable record pinning the exact world version, branch, source watermarks, analytical table snapshots, semantic digests, and model versions that form one business-consistent cut.
_Avoid_: Latest table, ad-hoc snapshot

### Verification and cross-repository exchange

**Proof Obligation**:
A formally stated invariant or quantitative property paired with its governing equation or predicate, domain, verification method, independent expected result, acceptance criterion, and evidence status.
_Avoid_: Unit test, sanity check

**WorldExportBundle**:
A versioned export package published by PPC after observable source, graph, KPI, and evidence generation, strictly split into an `observable/` layer for sister repositories and a separately credentialed `hidden_truth/` evaluation layer under `evaluation/hidden/`.
_Avoid_: Shared database, canonical shortcut

**Legacy Pre-World-Model Data**:
Older synthetic datasets created in Cloudflare R2 or sister repositories before the canonical PPC world model existed, isolated under a quarantine label until replaced by verified world outputs.
_Avoid_: Current baseline, production fixture

**Interactive Enterprise Context Explorer**:
The browser-based graph and scenario impact investigation interface that lets business users explore authorized relationship projections, compare branches, and trace KPI constituents while keeping calculations in authoritative models.
_Avoid_: Teaching demo, calculation graph


