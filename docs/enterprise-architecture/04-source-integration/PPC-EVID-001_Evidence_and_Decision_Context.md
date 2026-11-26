# PPC-EVID-001 — Evidence and Decision Context

Inspected PPC baseline: [`01027a84be5d453cbb4e2ea091e4884729918b15`](../registers/PPC-SOURCE-REGISTER.md). This commit is an inspection reference, not owner approval.

| Control | Value |
|---|---|
| ID / status | PPC-EVID-001 / proposed draft for owner review |
| Version / date | 0.1.0-draft / 2026-11-25 |
| Authority | [PPC-016](../../PPC-016_Evidence_Decision_Provenance_and_Evaluation_Architecture.md), [PPC-018](../../PPC-018_Enterprise_Evidence_Corpus_and_Unstructured_Data_Generation_Strategy.md), ECE when released; ADR-026–032 |
| Inputs / output | Source assertions and restricted corpus → time- and role-scoped evidence set and decision dossier |

## 1. Evidence boundary

ECE owns reusable evidence and decision-context patterns. PPC owns fictional artifacts, claims, roles and decisions. A corpus generator may see canonical truth to create records; an ordinary retrieval or evaluation agent cannot. A document's existence, statement and accessibility are separate facts. A later correction may alter current interpretation but cannot become evidence that a planner had earlier. Vector similarity ranks candidates; it cannot authorize a document or establish its truth.

## 2. Typed assertions and decision state

`Artifact`: immutable ID/revision, source system, author role, content digest, document locator, valid-from/to and authored times, source-record time, publication time, recipient-specific `available_at` or `delivered_at`, `ingested_at`, recipient or route, access label, branch and provenance class. `SourceAssertion`: artifact ID, exact field/page/span locator, quoted or structured proposition, valid-from/to, source-record and publication times, recipient-specific `available_at`, `ingested_at`, access label, status and supersession. `EvidenceItem` binds an eligible assertion, artifact revision, role, branch, release and knowledge cutoff. `Claim`: proposition, `EVIDENCE|INFERENCE|CONTRADICTION|UNKNOWN`, evidence-item and source-assertion IDs, model result if inferred, and explicit unknown reason. `DecisionDossier`: decision ID, branch, actor, cutoff, policy version, options and constraints, evidence release, selected/deferred option, approval and execution events, expected and later observed outcome. A dossier's later outcome is sealed from its earlier decision view.

An assertion flows `DRAFT → PUBLISHED → DELIVERED → SUPERSEDED` with recipient-specific access. `PUBLISHED` does not mean every recipient has it. Decision transitions are `OPEN → RECOMMENDED|ESCALATED|EXPIRED`, `RECOMMENDED → APPROVED|REJECTED|ESCALATED|EXPIRED`, and `APPROVED → EXECUTED|EXPIRED`. An explicitly preapproved bounded action may follow `RECOMMENDED → AUTO_EXECUTED` after its policy check. `REJECTED`, `EXPIRED`, `ESCALATED`, `AUTO_EXECUTED` and `EXECUTED` are terminal for that decision; renewed work creates a new decision ID. A historical query selects the pinned release, branch, effective interval, publication/receipt and role availability at cutoff. It filters access before retrieval and explanation. Unknown historical access returns `UNKNOWN`, not presumed permission.

## 3. Synthetic noon correction fixture

All times are UTC on 2026-11-01 and all records are `SYNTHETIC`. Publication P1 says slot S contains pump A and becomes available to the planner at 12:30. A correction P2 says pump B was installed at 10:00. Its source records P2 at 12:00 but releases P2 to the planner at 13:00. At a 12:45 decision cutoff, P2 is ineligible. The planner uses authorized P1 as the last publication, with its age and uncertainty, or returns `UNRESOLVED` if no eligible publication exists. At 13:00, P2 may be used if the planner is authorized and receipt is confirmed. Replaying the 12:45 dossier at 15:00 still excludes P2. If P2 is restricted, the answer must reveal neither B nor the correction's existence. `recorded_at=12:00` alone never proves availability.

A conflicting accessible maintenance note does not silently override P1. The answer labels `CONTRADICTION`, cites both assertions and escalates the identity question. A missing note yields `UNKNOWN` where the decision requires its content. A duplicate indexed artifact keeps one assertion identity and one evidence count.

## 4. Qualification and decisions

Test exact locator resolution, citation support, contradictory and missing evidence, publication delay, later corrections, current versus historical permission, restricted-result side channels, branch leakage and hidden-truth isolation. Record expected/observed claim sets, cutoff, actor, manifest, authorization policy and evaluation scorer version. PPC-016's target percentages remain goals, not measured outcomes here. ECE package maturity and access-history representation remain open. T3–5, T31–33, T72, T84, T106–109 and T116–118 in the [discussion register](../registers/PPC-Discussion-Decision-Traceability.md) motivate the design; external screenshots and market attachments remain unqualified source material.

The [exchange register](../registers/PPC-Discussion-Decision-Traceability.md) routes T3–5, T26–27, T31–33, T72, T84, T106–109 and T116–118 to this draft. This is topic-level routing; GAP-002 item and original-asset checks remain open.

[INFO-001 §3](../03-enterprise-information/PPC-INFO-001_Enterprise_Ontology_Identity_and_Time.md) owns the complete P0/P1/P2 publication rows, source-record times, recipient availability and reader-as-of rule used by this draft.
