# PPC-PLAN-001 — Implementation Work Packages and Readiness

Inspected PPC baseline: [`01027a84be5d453cbb4e2ea091e4884729918b15`](../registers/PPC-SOURCE-REGISTER.md). This commit is the original PPC source-inspection reference, not this draft's content revision or owner approval. Later linked specifications are read at the current branch revision.

| Control | Value |
|---|---|
| ID / status | PPC-PLAN-001 / proposed draft, 0.1.0, 2026-11-25 |
| Authority | [PPC-014](../../PPC-014_Implementation_Roadmap_and_Build_Runbook.md), [ARCH-000](../00-master-index/PPC-ARCH-000_Master_Architecture_Index_and_Authority_Baseline.md); ADR-025, 037, 038 |
| Contract | Reviewed architecture and gates → bounded, agent-neutral implementation packages |

## 1. Readiness boundary

PPC-014 remains the recorded roadmap. This plan proposes a dependency order for review; it authorizes no code, deployment, upstream release or ADR change. An architecture draft is `PROPOSED`. A selected design needs owner decision. Implemented behavior needs code evidence. A passed test needs run evidence. Qualification needs a reviewed envelope and release. Git commits alone satisfy none of the latter states. The generalized process release remains pending separate upstream work.

## 2. Work packages and exit evidence

| Package | Inputs and deliverable | Required exit evidence |
|---|---|---|
| WP-0 authority | Disposition independent architecture review findings; resolve the seven Reassess ADRs and disposition all six Extend ADRs in [ARCH-000 §7](../00-master-index/PPC-ARCH-000_Master_Architecture_Index_and_Authority_Baseline.md), including ADR-035; disposition GAP-002 item-level OT/EA and original-asset checks; assess all 13 CAN-* candidates and PPC-011/012 OR-Tools, LangGraph and Langfuse choices; pin EPM/ICE/EDI/ECE and process maturity | Owner dispositions, compatibility matrix, no invented approval |
| WP-1 coherent world | PPC-014 Phase 2 public EIA, NOAA/NHC, PHMSA and EPA ingestion with vintage pins; WORLD-001/002 and ENG-001 contracts; one connected refinery and deterministic checkpoints | Independent balance/boundary oracles, replay and branch isolation |
| WP-2 source lifecycles | OT/EDI adoption, source apps, outbox/inbox and reconciliation | Duplicate, stale, crash and quantity cases |
| WP-3 governed information | INFO/GRAPH/DATA/EVID contracts and release manifests using the pinned public vintages from WP-1 | Semantic mapping, grain, cutoff, access, external observation vintage and graph-versus-model checks |
| WP-3A model and workspace | ANALYTICS-001 and UX-001 calculation, optimization and bounded workspace prototype before WP-5 | Independent model math and envelope checks; API authorization and Relate WASM negative tests if selected |
| WP-4 platform qualification | PLATFORM-001 deployment, secrets, backup/restore and isolation before the first integrated slice | Restore drill, scope denial, integrity and recovery evidence |
| WP-5 derate slice | Scenario A across source, engineering, model, graph, data and workspace after WP-3A and WP-4 | End-to-end positive/adverse/replay evidence and reviewer verdict |
| WP-6 quality slice | Scenario B across logistics, LIMS, CTRM, planning and finance | Lifecycle/reconciliation, late evidence and authorization evidence |
| WP-7 broad regression | Hurricane chain and AGENT-001 bounded tools, policy and action authorization | Cross-domain KPI, recovery and historical decision evidence |

The [ARCH-000 §10 readiness gates](../00-master-index/PPC-ARCH-000_Master_Architecture_Index_and_Authority_Baseline.md) apply across these packages. WP-0 supplies R0 and Phase 0 authority. WP-0 and WP-1 establish R1 dependency pins. WP-1 supplies the Phase 2 public foundation before Phase 3 generation. WP-1/2/3 establish R2 core contracts and PPC-014 Phases 3–8. WP-3A establishes R3 independent numerical benchmarks and covers Phase 9 models before the workspace. WP-4 establishes R4 infrastructure qualification and Phase 1 recovery prerequisites. WP-5/6 exercise R5 and Phases 10–11. WP-7 supports R6 and Phase 12. This is a proposed dependency crosswalk, not a change to PPC-014 phase order. Every package contract names owner, scope, inputs, output schema, dependencies, test oracle, failure cases, exact acceptance result and handoff artifact. A package is `READY` only when its required upstream releases and fixtures exist. `IN_PROGRESS` and `DONE` require recorded work; no package here is claimed started. The small first slice still lives within the full charter.

## 3. Readiness examples and open decisions

The T125 `SYNTHETIC` derate fixture has a 40,000 bbl/day nominal bound and a `SCENARIO_ASSUMPTION` 0.75 restriction at 08:10. Its `DERIVED` cap is 30,000 bbl/day. Reviewing its units and independent oracle contributes to WP-1 readiness; it does not authorize implementation. If the EDI adoption is missing, WP-5 remains blocked even when a graph diagram exists. A duplicate 500 bbl receipt test must show one physical effect before WP-6 can pass. Reader-as-of acceptance follows [INFO-001 §3](../03-enterprise-information/PPC-INFO-001_Enterprise_Ontology_Identity_and_Time.md), including delayed delivery and restricted publications. A failed test returns the package to review with the deviation, not a green summary.

The owner must decide first-slice order, revised ADRs, service choices and acceptable model envelope. Keep pending dependencies explicit. T21, T34, T63–65, T93, T122–126 and T136–142 in the [discussion register](../registers/PPC-Discussion-Decision-Traceability.md) motivate the sequence. T127–130 and T143–145 concern documentation publication, not implementation approval. WP-0 must close the independent review disposition gate before Phase 0 authorization; WP-4 must qualify infrastructure before WP-5 or WP-6 integration.

The [exchange register](../registers/PPC-Discussion-Decision-Traceability.md) routes T21, T34, T46–47, T63–65, T76–77, T93, T122–124, T126–130, T136–145 to this draft. This is topic-level routing; GAP-002 item and original-asset checks remain open.

[INFO-001 §3](../03-enterprise-information/PPC-INFO-001_Enterprise_Ontology_Identity_and_Time.md) owns the complete P0/P1/P2 publication rows, source-record times, recipient availability and reader-as-of rule used by this draft.
