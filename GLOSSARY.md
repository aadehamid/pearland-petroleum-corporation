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
A versioned export package published by PPC from one verified Refinery A world containing pinned Delta tables, OT tag schedules, engineering topology manifests, KPI fixtures, and role-scoped evidence fixtures for sister repositories.
_Avoid_: Shared database, canonical shortcut

**Legacy Pre-World-Model Data**:
Older synthetic datasets created in Cloudflare R2 or sister repositories before the canonical PPC world model existed, isolated under a quarantine label until replaced by verified world outputs.
_Avoid_: Current baseline, production fixture

**Interactive Enterprise Context Explorer**:
The browser-based graph and scenario impact investigation interface that lets business users explore authorized relationship projections, compare branches, and trace KPI constituents while keeping calculations in authoritative models.
_Avoid_: Teaching demo, calculation graph


