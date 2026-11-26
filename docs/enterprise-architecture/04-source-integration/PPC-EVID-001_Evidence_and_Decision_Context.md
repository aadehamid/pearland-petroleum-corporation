# PPC-EVID-001 — Evidence and Decision Context

Inspected PPC baseline: [`01027a84be5d453cbb4e2ea091e4884729918b15`](../registers/PPC-SOURCE-REGISTER.md). This commit is the original PPC source-inspection reference, not this draft's content revision or owner approval. Later linked specifications are read at the current branch revision.

| Control | Value |
|---|---|
| ID / status | PPC-EVID-001 / proposed draft for owner review |
| Version / date | 0.1.0-draft / 2026-11-25 |
| Authority | [PPC-016](../../PPC-016_Evidence_Decision_Provenance_and_Evaluation_Architecture.md), [PPC-018](../../PPC-018_Enterprise_Evidence_Corpus_and_Unstructured_Data_Generation_Strategy.md), ECE when released; ADR-026–032 |
| Inputs / output | Source assertions and restricted corpus → time- and role-scoped evidence set and decision dossier |

## 1. Evidence boundary

ECE owns reusable evidence and decision-context patterns. PPC owns fictional artifacts, claims, roles and decisions. A corpus generator may see canonical truth to create records; an ordinary retrieval or evaluation agent cannot. A document's existence, statement and accessibility are separate facts. A later correction may alter current interpretation but cannot become evidence that a planner had earlier. Vector similarity ranks candidates; it cannot authorize a document or establish its truth.

## 2. Typed assertions and decision state

`Artifact`: immutable ID/revision and publication ID, source system, author role, content digest, document locator, subject scope, scoped ordinal, supersedes-publication ID, valid-from/to and authored times, source-record time, publication time, recipient/role-and-channel availability relation, `ingested_at`, recipient or route, access label, branch and provenance class. `SourceAssertion`: immutable assertion ID, publication ID, artifact ID and revision, branch ID, provenance class, exact field/page/span locator, quoted or structured proposition, valid-from/to, source-record and publication times, recipient/role-and-channel availability relation, `ingested_at`, access label, status, supersedes-publication ID and supersession scope and ordinal as defined by [INFO-001 §3](../03-enterprise-information/PPC-INFO-001_Enterprise_Ontology_Identity_and_Time.md). `EvidenceItem` has immutable evidence-item ID and binds an eligible assertion, artifact revision, actor/recipient and role, channel, purpose, branch, release, knowledge cutoff, delivery receipt ID and historical grant ID. `Claim`: immutable claim ID, branch ID, knowledge cutoff, provenance class, proposition, `EVIDENCE|INFERENCE|CONTRADICTION|UNKNOWN`, evidence-item and source-assertion IDs, model result if inferred, and explicit unknown reason. `DecisionDossier`: decision ID, linked proposal, authorization basis and receipt IDs when applicable, branch, actor, channel, purpose, cutoff, policy version, authority basis, decision status, options and constraints, selected, rejected and deferred options, rationale, uncertainties, evidence release, visibility scope for hidden truth, approval and execution events, expected and later observed outcome. A dossier's later outcome is sealed from its earlier decision view.

Assertion publication follows `DRAFT → PUBLISHED → SUPERSEDED`; `PUBLISHED → SUPERSEDED` is allowed without any recipient delivery. Delivery is a separate receipt for each recipient/role and channel, so publication never implies access. Decision and action transitions are governed by [AGENT-001 §1](../05-intelligence-experience/PPC-AGENT-001_Agent_Tools_and_Consequential_Actions.md). The dossier records the linked transition event from AGENT-001. Its `REJECTED`, `DEFERRED` and `RECOMMENDED_ONLY` outcomes have no business effect.

Historical queries use [INFO-001 §3](../03-enterprise-information/PPC-INFO-001_Enterprise_Ontology_Identity_and_Time.md). If no publication qualifies for the reader at the cutoff, return only `UNRESOLVED`. Do not identify an excluded publication or explain why it was excluded. `UNKNOWN` describes a claim that the accessible evidence cannot answer; it is not an access result.

## 3. Synthetic noon correction fixture

Use the `SYNTHETIC` P0/P1/P2 slot fixture and exact cutoffs in [INFO-001 §3](../03-enterprise-information/PPC-INFO-001_Enterprise_Ontology_Identity_and_Time.md). The evidence release must retain each artifact revision, assertion locator, delivery receipt and historical grant used by that reader. Replay pins the dossier cutoff. A hidden or partially denied publication contributes no citation or observable change.

A conflicting accessible maintenance note does not silently override P1. The answer labels `CONTRADICTION`, cites both assertions and escalates the identity question. A missing note yields `UNKNOWN` where the decision requires its content. A duplicate indexed artifact keeps one assertion identity and one evidence count.

## 4. Qualification and decisions

Test exact locator resolution, citation support, contradictory and missing evidence, publication delay, later corrections, current versus historical permission, restricted-result side channels, branch leakage and hidden-truth isolation. Record expected/observed claim sets, cutoff, actor, manifest, authorization policy and evaluation scorer version. PPC-016's target percentages remain goals, not measured outcomes here. ECE package maturity and access-history representation remain open. T3–5, T31–33, T72, T84, T106–109 and T116–118 in the [discussion register](../registers/PPC-Discussion-Decision-Traceability.md) motivate the design; external screenshots and market attachments remain unqualified source material.

The [exchange register](../registers/PPC-Discussion-Decision-Traceability.md) routes T3–5, T26–27, T31–33, T72, T84, T106–109, T116–118 to this draft. This is topic-level routing; GAP-002 item and original-asset checks remain open.

[INFO-001 §3](../03-enterprise-information/PPC-INFO-001_Enterprise_Ontology_Identity_and_Time.md) owns the complete P0/P1/P2 publication rows, source-record times, recipient availability and reader-as-of rule used by this draft.
