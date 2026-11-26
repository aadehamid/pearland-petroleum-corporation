# PPC-UX-001 — Enterprise Intelligence Workspace

| Control | Value |
|---|---|
| ID / status | PPC-UX-001 / proposed draft, 0.1.0, 2026-11-25 |
| Authority | [PPC-012](../../PPC-012_Intelligent_Automation_Agent_and_User_Experience.md), [PPC-010](../../PPC-010_Ontology_Knowledge_Graph_and_Policy_Architecture.md); ADR-013, 014, 020 |
| Contract | Authorized question and pinned release → evidence-linked investigation, scenario or approval request |

## 1. Workflow boundary

The baseline uses Superset for scorecards, Dash for decisions and Grafana for operations. A browser graph based on Relate WASM is a proposal for investigation; it does not replace ADR-014. A workspace presents a selected world branch, release and historical cutoff. It separates source observations, graph connectivity, model results, approved KPI values and agent narratives. Every material number links to a product/model release and provenance class. A relationship path is labeled `POTENTIAL_EXPOSURE` until a qualified model quantifies it.

`WorkspaceRequest` includes actor/role, purpose, branch, graph snapshot, product/evidence release, effective time, knowledge cutoff and query. `InvestigationResult` includes typed cards: assertion with locator; relationship path with edge IDs; quantified result with model and unit; uncertainty; contradiction; unknown; and action proposal with policy outcome. An absent or unauthorized result has the same nondisclosing presentation. A saved investigation pins its releases. Its lifecycle is `OPEN → SAVED → SUBMITTED_FOR_REVIEW → CLOSED`; a scenario comparison is a new branch view, not a mutation of baseline.

## 2. Worked interaction

At 10:30 UTC in a `SYNTHETIC` derate fixture, a planner opens the affected hydrocracker and sees a graph path to contract K. The interface says K is potentially exposed. It displays a separately computed `ESTIMATED` 8,000 bbl/day ULSD difference only when a qualified run and its assumptions are present. The planner compares baseline and derate branches with their model versions. A rejected 90,000 bbl/day feed proposal shows the 80,000 bbl/day bound, not a fabricated feasible schedule.

At 12:45, a pump correction recorded at noon but not released to the planner until 13:00 cannot appear in the investigation. The view uses the last authorized 12:30 publication or displays unresolved. A restricted correction cannot be hinted by a blank graph node or a changed count. Refreshing the screen after 13:00 does not rewrite the saved 12:45 investigation. Duplicate events do not create duplicate alert cards; a failed API call leaves the saved view intact and identifies the unavailable component without leaking protected data.

## 3. Qualification and alternatives

Exercise role-specific views, as-of replay, branch comparison, provenance links, stale/incomplete release banners, duplicate alerts, browser restart, keyboard access and a screen recording of graph-versus-model labels. Verify authorization at the API, not only in the browser. Record exact screenshot/workflow version and expected/observed behavior. No UI deployment is claimed. ADR-014 Dash remains the selection; Relate WASM, alternative frontends and graph visualization boundaries need a workflow prototype and owner decision. T13–18, T36, T107–112 in the [discussion register](../registers/PPC-Discussion-Decision-Traceability.md) motivate the proposed experience; supplied images are reference material pending source review.
