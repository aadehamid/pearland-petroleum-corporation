# PPC-016 — Evidence, Decision Provenance, and Evaluation Architecture

**Baseline:** PPC Architecture Baseline v1.1  
**Purpose:** Define how PPC represents evidence, claims, decision-time context, hidden truth, uncertainty, contradiction, and agent evaluation.  
**Upstream dependency:** Enterprise Context Engineering (ECE) provides reusable evidence/provenance/evaluation contracts. PPC specializes those contracts for downstream performance and decision workflows.

## Documentation standard
PPC uses an **ASD-STE100-inspired** technical writing style. PPC does not claim formal ASD-STE100 compliance.

## 1. Why PPC needs this architecture
PPC must answer not only what happened and what action is best, but also what information was available at decision time, which source supports each claim, what is inferred, what sources disagree, what remains unknown, which alternatives existed, which authority allowed the decision, and whether later evidence validated the rationale.

## 2. Two independent classification axes

### Data provenance
| Provenance | Meaning |
|---|---|
| `OBSERVED` | Direct public or source-system observation |
| `DERIVED` | Deterministic calculation from governed inputs |
| `ESTIMATED` | Statistical, causal, probabilistic, or analytical estimate |
| `SYNTHETIC` | Fictional PPC enterprise fact |
| `SCENARIO_ASSUMPTION` | Explicit scenario/stress-test assumption |

### Epistemic status
| Status | Meaning |
|---|---|
| `EVIDENCE` | Directly supported by accessible source assertions |
| `INFERENCE` | Reasoned conclusion from evidence/models/relationships |
| `CONTRADICTION` | Relevant sources conflict |
| `UNKNOWN` | Available evidence does not support a responsible conclusion |

A synthetic source-system fact can be `SYNTHETIC` and `EVIDENCE` inside the simulation. A forecast is normally `ESTIMATED` and supports an `INFERENCE`.

## 3. Canonical truth versus agent-visible evidence
```text
CANONICAL PPC WORLD
complete simulation truth
       |
       +---------------------+
       |                     |
       v                     v
SOURCE-SYSTEM WORLD     HIDDEN EVALUATION TRUTH
CRM/ERP/DBs/docs        rationale/gold evidence/labels
       |
       v
AGENT-VISIBLE WORLD
       |
       v
RETRIEVAL / GRAPH / AGENT
```
Canonical truth is used for generation, reconciliation and scoring. It is not a normal retrieval source during blind evaluation.

## 4. Core evidence entities
**Artifact:** inspectable source object: record, API response, email, meeting note, deck, memo, policy, model run, optimizer result or approval.  
**EvidenceItem:** governed unit of evidence.  
**SourceAssertion:** specific statement/field within an artifact with a precise locator where practical.  
**Claim:** material statement in an answer, report, recommendation or retrospective.

Trace:
`Claim -> SourceAssertion -> Artifact -> Source/System -> Scenario/Release -> Provenance`.

## 5. Decision dossier
Every material PPC decision has a hidden canonical dossier with: decision ID/time/domain/statement, owner role, authority basis, affected entities, drivers, constraints, options, selected/rejected/deferred options, approval status, expected outcome, actual outcome, ground-truth rationale, uncertainties, related KPIs/data products/events.

## 6. Decision-time evidence
Store authored time, effective time, publication/availability time, ingestion time, decision time, validity interval and superseded/current state.

Example: an 08:20 forecast cannot explain an 08:15 decision.

Temporal leakage is a hard evaluation failure.

## 7. Controlled imperfection
The canonical world remains coherent. The evidence world can contain stale assumptions, delayed updates, partial context, disagreement, superseded policy and controlled contradictions. Agents must reason about source, time, authority and uncertainty.

## 8. Claim-level provenance example
A recommendation to transfer inventory may contain:
- hydrocracker availability: source-system assertion, `SYNTHETIC` + `EVIDENCE`;
- terminal cover forecast: model run, `ESTIMATED` + `INFERENCE`;
- avoided margin loss: optimization/scenario outputs, `ESTIMATED` + `INFERENCE`;
- approval requirement: policy assertion, `EVIDENCE`.

## 9. Evidence artifacts
PPC should generate trader emails, supply-review notes, operations updates, planning decks, commercial reviews, policies, approval messages, outcome reports and retrospective learning notes. No single artifact should reveal complete hidden truth by default.

## 10. Evidence and decision graph
```text
Decision -SUPPORTED_BY-> EvidenceItem
Decision -CONSIDERED-> DecisionOption
Decision -CONSTRAINED_BY-> Constraint
Decision -AUTHORIZED_BY-> Policy
Decision -APPROVED_BY-> Role
Decision -RESULTED_IN-> Outcome
Claim -SUPPORTED_BY-> SourceAssertion
SourceAssertion -LOCATED_IN-> Artifact
```
Jena formalizes selected meaning. Neo4j supports operational traversal.

## 11. Evaluation
PPC evaluates data/system correctness and agent/context correctness.

Agent/context measures include claim-level provenance coverage, unsupported-claim rate, epistemic labeling, temporal correctness, source selection, hidden-truth isolation, uncertainty handling, policy correctness and decision-rationale recovery.

Initial goals: >=95% material claims with resolvable evidence on golden cases; zero hidden-truth leakage; zero temporal leakage on golden temporal cases; <2% unsupported material claims with every miss root-caused; 100% required epistemic labeling on designated cases.

## 12. Development and hidden evaluation
Development may contain visible questions, sample evidence and controlled contradiction examples. Hidden evaluation contains canonical rationale, held-out decisions, expected evidence sets, hidden outcomes, contradiction/unknown labels and scoring keys. Retrieval agents must not have access to hidden evaluation storage.

## 13. R2 additions
Recommended logical prefixes:
```text
cache/documents/
cache/evidence/
cache/decision-dossiers/
cache/graph/
evaluation/development/
evaluation/hidden/
```
Hidden prefixes require separate access control.

## 14. Relationship to EPM and ECE
EPM defines downstream concepts such as Customer, Shipment, KPI, Decision and Data Product. ECE defines generic Evidence, SourceAssertion, Claim, DecisionOption, provenance, temporal and evaluation patterns. PPC instantiates and specializes both.

## 15. Release requirements
Each PPC release records EPM semantic/ontology versions, ECE evidence/provenance/evaluation contract versions, PPC world/generator versions, artifact manifests/checksums, visible/hidden evaluation-set versions and validation results.

## Governing principle
> **The canonical world tells PPC what happened. The evidence world determines what an agent is allowed to know. Claim-level provenance shows why an answer is justified.**
