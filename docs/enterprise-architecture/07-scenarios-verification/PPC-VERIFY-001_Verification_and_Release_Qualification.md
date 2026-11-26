# PPC-VERIFY-001 — Verification and Release Qualification

| Control | Value |
|---|---|
| ID / status | PPC-VERIFY-001 / proposed draft, 0.1.0, 2026-11-25 |
| Authority | [PPC-005](../../PPC-005_Synthetic_Data_Generation_Strategy.md), [PPC-014](../../PPC-014_Implementation_Roadmap_and_Build_Runbook.md), [PPC-016](../../PPC-016_Evidence_Decision_Provenance_and_Evaluation_Architecture.md), [ARCH-000](../00-master-index/PPC-ARCH-000_Master_Architecture_Index_and_Authority_Baseline.md) |
| Contract | Versioned requirement and independent oracle → observed result, deviation and qualification decision |

## 1. What counts as evidence

Architecture prose, a passing schema check and a self-authored unit test do not establish physical, semantic, temporal or security correctness. Each claim needs an independently specified expected result, exact input and release, observed result, tolerance and reviewer disposition. Verification stages are `SPECIFIED → FIXTURE_READY → RUN → REVIEWED → QUALIFIED|FAILED`. A failed test stays visible after a fix. A qualification applies only to its stated version, environment, model envelope and role. This document defines obligations; it reports no executed suite.

`VerificationCase` includes stable case ID, requirement ID, owner, method, independent oracle, fixture digest, branch, input versions, expected output, units, tolerance, failure injection and required evidence. `RunEvidence` includes environment, code/config/model digests, command, UTC time, actual output, logs, deviations, reviewer and decision. Use `OBSERVED` only for a real observation from a cited source; synthetic test inputs are `SYNTHETIC`, scenario interventions `SCENARIO_ASSUMPTION`, calculated expectations `DERIVED`.

## 2. Minimum independent challenges

| Family | Required positive and adverse proof |
|---|---|
| World and engineering | Mass/inventory balance, capacity bounds, zero and limit values, dimensional checks, independently calculated oracle, restart at event tie |
| Source integration | Duplicate/conflicting IDs, reordered corrections, crash before/after commit and ack, partial publication, reconciliation |
| Semantic and graph | Pinned IRI/SHACL/competency suite, false equivalence rejection, conversion loss, RDF/property-graph round trip, branch and time queries |
| Data and analytics | Grain uniqueness, KPI recomputation and threshold parity, incomplete release rejection, feasible/infeasible optimizer cases, holdout and uncertainty |
| Evidence and action | Decision-time and role cutoff, restricted-result side channel, hidden-truth isolation, approval exactness, idempotent replay |
| Platform | Backup/restore drill, corrupted object detection, secret scope, release compatibility and rollback |

For the `SYNTHETIC` tank fixture, 1,000 + 200 − 150 = 1,050 bbl is the independent `DERIVED` expected close. Apply the 200 bbl receipt twice with one source ID; expected close remains 1,050 bbl. Restart after the source commit but before acknowledgement; expected physical receipt count remains one. A 12:45 planner query cannot use a noon-recorded correction released at 13:00. It must use the last authorized 12:30 publication or return unresolved. Restricted corrections must not leak. These expectations can be checked without copying implementation logic.

## 3. Release gate and open decisions

An integrated candidate pins each upstream contract and maturity state, world branch/checkpoint, source watermarks, product and graph snapshots, model versions, evidence release, policy and test-suite digest. Qualification fails if a required upstream release is pending, a material discrepancy is unresolved, a critical negative test fails, or a hidden/evidence leak occurs. `QUALIFIED` requires signed owner/reviewer disposition and a reproducible evidence package. A passed component test cannot stand in for an end-to-end scenario. No approvals or qualifications are asserted here.

Alternative verification methods include a hand-calculated reference for balances, model checking for state transitions, fault injection for recovery and held-out empirical cases for physical fidelity. Choose methods by the claim; one cannot substitute for another. Open decisions: quantified tolerances, independent benchmark owners, acceptable recovery point/time, and which optional services can be absent from the first slice. T25–26, T54, T73–74, T113, T120–126 in the [discussion register](../registers/PPC-Discussion-Decision-Traceability.md) supply the discussion trail. The original numerical examples require their own fixture review before qualification.
