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
| WP-0 authority and platform | Disposition independent review findings, the seven Reassess and six Extend ADRs in [ARCH-000 §7](../00-master-index/PPC-ARCH-000_Master_Architecture_Index_and_Authority_Baseline.md), GAP-002 and 13 CAN-* candidates. Pin EPM/ICE/EDI/ECE and process maturity. Complete PPC-014 Phase 0 authority, then Phase 1 R2 prefixes, PostgreSQL, MySQL, SQLite and DuckDB/DuckLake before any dependent work. | Owner dispositions, compatibility matrix, storage and service readiness, no invented approval |
| WP-1 coherent world | PPC-014 Phase 2 public EIA, NOAA/NHC, PHMSA and EPA ingestion with vintage pins; WORLD-001/002 and ENG-001 contracts; one connected refinery and deterministic checkpoints | Independent balance/boundary oracles, replay and branch isolation |
| WP-2 source lifecycles | OT/EDI adoption, source apps, outbox/inbox and reconciliation | Duplicate, stale, crash and quantity cases |
| WP-3 governed information | INFO/GRAPH/DATA/EVID contracts and release manifests using the pinned public vintages from WP-1 | Semantic mapping, grain, cutoff, access, external observation vintage and graph-versus-model checks |
| WP-3A numerical gate | ANALYTICS-001 Phase 9 models and independent engineering/optimization benchmarks. Pass R3 before integrating effects into a business UI. | Independent model math and envelope checks with reviewed results |
| WP-3B workspace and policy | Phase 10 UX-001 bounded Dash workspace, LangGraph workflow, D1 state, Langfuse tracing and AGENT-001 policy checks, authorization basis and action receipts. Start only after WP-3A passes R3. | API authorization, policy denial, approval replay and golden agent cases; Relate WASM negative tests if selected |
| WP-4 platform qualification | PLATFORM-001 deployment, secrets, backup/restore and isolation before the first integrated slice | Restore drill, scope denial, integrity and recovery evidence |
| WP-5 derate slice | Scenario A across source, engineering, model, graph, data and workspace after WP-3B and WP-4; exercise Phase 10 authority | End-to-end positive/adverse/replay evidence, policy denial and reviewer verdict |
| WP-6 quality slice | Scenario B across logistics, LIMS, CTRM, planning and finance after WP-3B and WP-4; exercise Phase 10 authority | Lifecycle/reconciliation, late evidence and action authorization evidence |
| WP-7 observability and regression | Phase 11 Grafana and OpenMetadata observability, then Phase 12 hurricane chain and AGENT-001 bounded-tool regression | Platform/lineage/incident signals, cross-domain KPI, recovery and historical decision evidence |

The [ARCH-000 §10 readiness gates](../00-master-index/PPC-ARCH-000_Master_Architecture_Index_and_Authority_Baseline.md) apply across these packages. WP-0 supplies R0, R1 pins and PPC-014 Phases 0–1 before WP-1 starts Phase 2. WP-1/2/3 follow Phases 2–8 in order and establish R2. WP-3A covers Phase 9 and must pass R3 before WP-3B integrates effects into UX. WP-4 qualifies recovery and isolation for R4 before integrated slices. WP-3B supplies Phase 10 policy authority before WP-5/6 exercise R5. WP-7 supplies Phase 11 observability before Phase 12 demonstration and R6. This is a proposed dependency crosswalk; [PPC-014](../../PPC-014_Implementation_Roadmap_and_Build_Runbook.md) owns phase order. Every package contract names owner, scope, inputs, output schema, dependencies, test oracle, failure cases, exact acceptance result and handoff artifact. A package is `READY` only when its required upstream releases and fixtures exist. `IN_PROGRESS` and `DONE` require recorded work; no package here is claimed started.

## 3. Readiness examples and open decisions

The T125 `SYNTHETIC` derate fixture has a 40,000 bbl/day nominal bound and a `SCENARIO_ASSUMPTION` 0.75 restriction at 08:10. Its `DERIVED` cap is 30,000 bbl/day. Reviewing its units and independent oracle contributes to WP-1 readiness; it does not authorize implementation. If the EDI adoption is missing, WP-5 remains blocked even when a graph diagram exists. A duplicate 500 bbl receipt test must show one physical effect before WP-6 can pass. Reader-as-of acceptance follows [INFO-001 §3](../03-enterprise-information/PPC-INFO-001_Enterprise_Ontology_Identity_and_Time.md), including delayed delivery and restricted publications. A failed test returns the package to review with the deviation, not a green summary.

The owner must decide first-slice order, revised ADRs, service choices and acceptable model envelope. Keep pending dependencies explicit. T21, T34, T63–65, T93, T122–126 and T136–142 in the [discussion register](../registers/PPC-Discussion-Decision-Traceability.md) motivate the sequence. T127–130 and T143–145 concern documentation publication, not implementation approval. WP-0 must close the independent review disposition gate before Phase 0 authorization; WP-4 must qualify infrastructure before WP-5 or WP-6 integration.

The [exchange register](../registers/PPC-Discussion-Decision-Traceability.md) routes T21, T34, T46–47, T63–65, T76–77, T93, T122–124, T126–130, T136–145 to this draft. This is topic-level routing; GAP-002 item and original-asset checks remain open.

[INFO-001 §3](../03-enterprise-information/PPC-INFO-001_Enterprise_Ontology_Identity_and_Time.md) owns the complete P0/P1/P2 publication rows, source-record times, recipient availability and reader-as-of rule used by this draft.
