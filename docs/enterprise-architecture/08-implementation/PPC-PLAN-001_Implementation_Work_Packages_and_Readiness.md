# PPC-PLAN-001 — Implementation Work Packages and Readiness

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
| WP-0 authority | Resolve ADR-007/009/014/015/017/018; pin EPM/ICE/EDI/ECE and process maturity | Owner dispositions, compatibility matrix, no invented approval |
| WP-1 coherent world | WORLD-001/002 and ENG-001 contracts; one connected refinery and deterministic checkpoints | Independent balance/boundary oracles, replay and branch isolation |
| WP-2 source lifecycles | OT/EDI adoption, source apps, outbox/inbox and reconciliation | Duplicate, stale, crash and quantity cases |
| WP-3 governed information | INFO/GRAPH/DATA/EVID contracts and release manifests | Semantic mapping, grain, cutoff, access and graph-versus-model checks |
| WP-4 derate slice | Scenario A across source, engineering, model, graph, data and workspace | End-to-end positive/adverse/replay evidence and reviewer verdict |
| WP-5 quality slice | Scenario B across logistics, LIMS, CTRM, planning and finance | Lifecycle/reconciliation, late evidence and authorization evidence |
| WP-6 broad regression | Hurricane chain and platform restore | Cross-domain KPI, recovery and historical decision evidence |

Every package contract names owner, scope, inputs, output schema, dependencies, test oracle, failure cases, exact acceptance result and handoff artifact. A package is `READY` only when its required upstream releases and fixtures exist. `IN_PROGRESS` and `DONE` require recorded work; no package here is claimed started. The small first slice still lives within the full charter.

## 3. Readiness examples and open decisions

A `SYNTHETIC` derate fixture with 100,000 and 80,000 bbl/day bounds can make WP-1 ready for a bounded build after the equation, units and independent oracle are reviewed. If the EDI adoption is missing, WP-4 remains blocked even when a graph diagram exists. A duplicate 500 bbl receipt test must show one physical effect before WP-5 can pass. Replaying a 12:45 planner decision must exclude a noon-recorded correction released at 13:00; a restricted correction stays invisible. A failed test returns the package to review with the deviation, not a green summary.

The owner must decide first-slice order, revised ADRs, service choices and acceptable model envelope. Keep pending dependencies explicit. T21, T34, T63–65, T93, T122–126 and T136–142 in the [discussion register](../registers/PPC-Discussion-Decision-Traceability.md) motivate the sequence. T127–130 and T143–145 concern documentation publication, not implementation approval.
