# PPC-UX-001 — Enterprise Intelligence Workspace

Inspected PPC baseline: [`01027a84be5d453cbb4e2ea091e4884729918b15`](../registers/PPC-SOURCE-REGISTER.md). This commit is the original PPC source-inspection reference, not this draft's content revision or owner approval. Later linked specifications are read at the current branch revision.

| Control | Value |
|---|---|
| ID / status | PPC-UX-001 / proposed draft, 0.1.0, 2026-11-25 |
| Authority | [PPC-012](../../PPC-012_Intelligent_Automation_Agent_and_User_Experience.md), [PPC-010](../../PPC-010_Ontology_Knowledge_Graph_and_Policy_Architecture.md); ADR-013, 014, 020 |
| Contract | Authorized question and pinned release → evidence-linked investigation, scenario or approval request |

## 1. Workflow boundary

The baseline uses Superset for scorecards, Dash for decisions and Grafana for operations. A browser graph based on Relate WASM is a proposal for investigation; it does not replace ADR-014. A workspace presents a selected world branch, release and historical cutoff. It separates source observations, graph connectivity, model results, approved KPI values and agent narratives. Every material number links to a product/model release and provenance class. A relationship path is labeled `POTENTIAL_EXPOSURE` until a qualified model quantifies it.

`WorkspaceRequest` includes request ID, model and analytical release IDs, actor/role, channel, purpose, subject scope, branch, graph snapshot, product/evidence release, effective time, knowledge cutoff and query. `InvestigationResult` includes investigation ID, request ID, lifecycle status, branch ID, effective time, knowledge cutoff, pinned release IDs, actor/role, channel, purpose, subject scope and typed cards. Each card carries its own provenance class, epistemic status, recipient availability and access label: assertion with locator; relationship path with edge IDs; quantified result with model and unit; uncertainty; contradiction; unknown; and action proposal with policy outcome. An absent or unauthorized result has the same nondisclosing presentation. A saved investigation pins its releases. Its lifecycle is `OPEN → SAVED|DISCARDED`, `SAVED → SUBMITTED_FOR_REVIEW|CLOSED|DISCARDED`, `SUBMITTED_FOR_REVIEW → CLOSED`; `CLOSED` and `DISCARDED` are terminal; a scenario comparison is a new branch view, not a mutation of baseline.

## 2. Worked interaction

At 10:30 UTC in separate `SYNTHETIC` capacity illustration `CAP-ILLUS-01`, a planner opens the affected hydrocracker and sees a graph path to contract K. The interface says K is potentially exposed. It displays a separately computed `ESTIMATED` 8,000 bbl/day ULSD difference only when a qualified run and its assumptions are present. The planner compares baseline and derate branches with their model versions. A rejected 90,000 bbl/day feed proposal shows the 80,000 bbl/day bound, not a fabricated feasible schedule.

The saved noon-correction investigation uses [INFO-001 §3](../03-enterprise-information/PPC-INFO-001_Enterprise_Ontology_Identity_and_Time.md). It pins the reader, channel, purpose and cutoff with its releases. Restricted corrections cannot change counts or placeholder cards. A later screen refresh cannot change the saved result. Duplicate events do not create duplicate alert cards; a failed API call leaves the saved view intact and identifies the unavailable component without leaking protected data.

## 3. Qualification and alternatives

Exercise role-specific views, as-of replay, branch comparison, provenance links, stale/incomplete release banners, duplicate alerts, browser restart, keyboard access and a screen recording of graph-versus-model labels. Verify authorization at the API, not only in the browser. Record exact screenshot/workflow version and expected/observed behavior. No UI deployment is claimed. ADR-014 Dash remains the selection; Relate WASM, alternative frontends and graph visualization boundaries need a workflow prototype and owner decision. T13–18, T36, T107–112 in the [discussion register](../registers/PPC-Discussion-Decision-Traceability.md) motivate the proposed experience; supplied images are reference material pending source review.

The [exchange register](../registers/PPC-Discussion-Decision-Traceability.md) routes T2, T13–18, T36, T53, T71, T88, T107–112 to this draft. This is topic-level routing; GAP-002 item and original-asset checks remain open.

[INFO-001 §3](../03-enterprise-information/PPC-INFO-001_Enterprise_Ontology_Identity_and_Time.md) owns the complete P0/P1/P2 publication rows, source-record times, recipient availability and reader-as-of rule used by this draft.
