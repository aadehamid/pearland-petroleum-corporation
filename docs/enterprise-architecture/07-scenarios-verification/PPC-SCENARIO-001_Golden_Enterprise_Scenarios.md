# PPC-SCENARIO-001 — Golden Enterprise Scenarios

Inspected PPC baseline: [`01027a84be5d453cbb4e2ea091e4884729918b15`](../registers/PPC-SOURCE-REGISTER.md). This commit is the original PPC source-inspection reference, not this draft's content revision or owner approval. Later linked specifications are read at the current branch revision.

| Control | Value |
|---|---|
| ID / status | PPC-SCENARIO-001 / proposed draft, 0.1.0, 2026-11-25 |
| Authority | [PPC-001](../../PPC-001_Problem_Statement_and_Simulation_Charter.md), [PPC-005](../../PPC-005_Synthetic_Data_Generation_Strategy.md), [PPC-014](../../PPC-014_Implementation_Roadmap_and_Build_Runbook.md), [ARCH-000](../00-master-index/PPC-ARCH-000_Master_Architecture_Index_and_Authority_Baseline.md), [PPC-REG-001](../../PPC-REG-001_Architecture_Decision_Register.md) ADR-025, 031, 037 |
| Contract | Pinned world and intervention → source-visible history, alternative branch and independently checked outcome |

## 1. Scenario portfolio

The existing hurricane chain remains part of PPC's charter. Compressor derate and crude-quality rejection are proposed earlier verification slices, not an approved change to the charter or roadmap. Every golden case identifies world version, branch/fork, logical clock, public source vintage, model and EPM dependency, evidence cutoff, allowed roles, expected source records, calculation oracle and failure injections. A `ScenarioCase` has case ID, version, lifecycle status, world version, branch ID, parent checkpoint, logical clock, public source vintage, model, EPM, ICE, EDI and ECE contract pins, evidence cutoff, query channel and purpose, allowed roles, expected source records, failure injections, intervention list, expected release IDs, oracle version and access policy. The scenario artifact moves `DRAFT → REVIEWED → FROZEN`. A replay uses the frozen manifest. [VERIFY-001 §1](PPC-VERIFY-001_Verification_and_Release_Qualification.md) owns run, post-run review, failure and signed qualification states; scenario qualification records the linked verification case and run IDs. Fixture facts below are `SYNTHETIC`; interventions are `SCENARIO_ASSUMPTION`. Numerical outputs are `DERIVED` or `ESTIMATED` as stated.

## 2. Derate slice

In fixture `SCN-A-T125`, the T125 Scenario A case, a `SCENARIO_ASSUMPTION` derate at 08:10 UTC applies a 0.75 availability fraction to the `SYNTHETIC` nominal 40,000 bbl/day bound. The `DERIVED` cap is 30,000 bbl/day. The `SYNTHETIC` plan of 36,000 bbl/day exceeds the cap by a `DERIVED` 6,000 bbl/day. A `SCENARIO_ASSUMPTION` request of 30,001 bbl/day must fail. Over a `SCENARIO_ASSUMPTION` six-hour interval wholly after the restriction, the requested 9,000 bbl and capped 7,500 bbl differ by a `DERIVED` 1,500 bbl of feed capacity; this is not a product or margin loss. OT publishes a source measurement with tag, unit, quality and time; ICE mapping and an EDI-adopted topology identify the affected unit. The graph can trace potentially exposed contracts. A separately qualified model calculates product and economic differences. The planner may compare a baseline and derate branch but cannot execute a change without policy approval. [WORLD-002 §6](../01-enterprise-world/PPC-WORLD-002_Simulation_Time_Replay_and_Branches.md) fixes planner availability of the 08:12 observation at 08:12 for this fixture. [OT-001 §4](../02-industrial-engineering/PPC-OT-001_Industrial_Information_Architecture.md) uses independent fixture `OT-DELAY-01`, with planner availability at 08:16.

Adverse and replay checks: ambiguous tag, missing engineering adoption, delayed measurement, duplicate derate message, same-time command, restart at the event frontier, sibling-branch contamination and restricted correction. Expected responses are unresolved/quarantined, one physical transition and a reproducible old decision view. A linear feed bound is an illustrative model assumption; compressor thermodynamics and commercial loss require independent qualification.

## 3. Crude-quality rejection slice

A `SYNTHETIC` 500 bbl receipt at 08:00 UTC produces one logistics ticket at 08:05. A failed LIMS assay is recorded at 09:00, published at 09:20 and available to a planner at 09:30. CTRM actualization waits for a disposition. Planning considers feasible rerouting or hold; finance posts later. A duplicate ticket cannot add another 500 bbl. A source outage leaves a visible incomplete reconciliation. A correction published after a decision can create a restated analysis but cannot enter that decision's evidence. Source-record and physical truth remain distinct.

The first acceptance path checks one receipt, inventory balance, source lifecycle transitions, approved quality disposition, analytical watermark, KPI grain and action authority. Inject out-of-order assay revisions, conflicting IDs, unavailable finance, restricted evidence, crash after commit and a sibling branch. Keep old release and dossier IDs for replay.

## 4. Hurricane regression and qualification

The existing hurricane sequence covers availability, ULSD output, terminal inventory, customer commitments, replacement supply, logistics cost and margin. Its public weather observation is `OBSERVED` only with a source and vintage; fictional PPC impacts are `SYNTHETIC` or model `ESTIMATED`. It is a later broad regression, not an already implemented scenario. Check cross-domain timing, scenario isolation, graph exposure versus model magnitude, decision evidence and KPI recomputation.

Acceptance requires exact fixture manifests, independent physical and commercial expected values, source/evidence timelines, branch diff, negative cases and [VERIFY-001](PPC-VERIFY-001_Verification_and_Release_Qualification.md) evidence. No case is claimed run or qualified. Open decisions: first-slice approval, plant model envelope, product/contract sample and hurricane event vintage. T45, T58, T72–74, T83, T97, T122 and T125 in the [discussion register](../registers/PPC-Discussion-Decision-Traceability.md) support the portfolio; cited market attachments need separate source review.

The [exchange register](../registers/PPC-Discussion-Decision-Traceability.md) routes T1, T19, T45, T58, T72, T83, T97, T122 to this draft. This is topic-level routing; GAP-002 item and original-asset checks remain open.
