# PPC-VERIFY-001 — Verification and Release Qualification

Inspected PPC baseline: [`01027a84be5d453cbb4e2ea091e4884729918b15`](../registers/PPC-SOURCE-REGISTER.md). This commit is the original PPC source-inspection reference, not this draft's content revision or owner approval. Later linked specifications are read at the current branch revision.

| Control | Value |
|---|---|
| ID / status | PPC-VERIFY-001 / proposed draft, 0.1.0, 2026-11-25 |
| Authority | [PPC-005](../../PPC-005_Synthetic_Data_Generation_Strategy.md), [PPC-014](../../PPC-014_Implementation_Roadmap_and_Build_Runbook.md), [PPC-016](../../PPC-016_Evidence_Decision_Provenance_and_Evaluation_Architecture.md), [ARCH-000](../00-master-index/PPC-ARCH-000_Master_Architecture_Index_and_Authority_Baseline.md), [PPC-REG-001](../../PPC-REG-001_Architecture_Decision_Register.md) ADR-025, 031, 037 |
| Contract | Versioned requirement and independent oracle → observed result, deviation and qualification decision |

## 1. What counts as evidence

Architecture prose, a passing schema check and a self-authored unit test do not establish physical, semantic, temporal or security correctness. Each claim needs an independently specified expected result, exact input and release, observed result, tolerance and reviewer disposition. Verification stages are `SPECIFIED → FIXTURE_READY → RUN → POST_RUN_REVIEWED → QUALIFIED|FAILED`. A failed test stays visible after a fix. A qualification applies only to its stated version, environment, model envelope and role. This document defines obligations; it reports no executed suite.

`VerificationCase` includes stable case ID, stage, requirement ID, owner, actor role, channel, purpose, subject scope, method, independent oracle, fixture digest, branch, effective time, knowledge cutoff, input versions, expected output, units, tolerance, failure injection and required evidence. `RunEvidence` includes run ID, case ID, status, fixture digest, branch ID, upstream release pins, environment, code/config/model digests, command, UTC decision timestamp, actual output, logs, deviations, reviewer and decision. Use `OBSERVED` only for a real observation from a cited source; synthetic test inputs are `SYNTHETIC`, scenario interventions `SCENARIO_ASSUMPTION`, calculated expectations `DERIVED`.

## 2. Minimum independent challenges

| Family | Required positive and adverse proof |
|---|---|
| World and engineering | Mass/inventory balance, capacity bounds, zero and limit values, dimensional checks, independently calculated oracle, restart at event tie |
| Source integration | Duplicate/conflicting IDs, reordered corrections, crash before/after commit and ack, partial publication, reconciliation |
| Semantic and graph | Pinned IRI/SHACL/competency suite, false equivalence rejection, conversion loss, RDF/property-graph round trip, branch and time queries |
| Data and analytics | Grain uniqueness, KPI recomputation and threshold parity, incomplete release rejection, feasible/infeasible optimizer cases, holdout and uncertainty |
| Evidence and action | Decision-time and role cutoff, restricted-result side channel, hidden-truth isolation, approval exactness, idempotent replay |
| Platform | Backup/restore drill, corrupted object detection, secret scope, release compatibility and rollback |

For the T125 `SYNTHETIC` tank fixture, opening stock is 10,000 bbl, receipt is 500 bbl/h and dispatch is 700 bbl/h for two hours. On one liquid at constant density and a common reference-volume basis, the independent `DERIVED` close is 9,600 bbl against a 12,000 bbl limit. Apply the same source movement twice; expected close remains 9,600 bbl. Restart after the source commit but before acknowledgement; expected physical receipt count remains one. For the noon correction, test the publication, fallback and nondisclosure rules in [INFO-001 §3](../03-enterprise-information/PPC-INFO-001_Enterprise_Ontology_Identity_and_Time.md). These expectations can be checked without copying implementation logic. For separate `INT-RETRY-01`, [DATA-001 §3](../03-enterprise-information/PPC-DATA-001_Data_Products_KPIs_and_Analytical_Releases.md) supplies the 1,050 bbl and duplicate-delivery expectations. Verify them with an independent balance oracle and one applied source movement per key. For the noon correction, use [INFO-001 §3](../03-enterprise-information/PPC-INFO-001_Enterprise_Ontology_Identity_and_Time.md) as the fixture and selection authority. Include absent receipt, denied grant, grant that starts after the cutoff, late P1 after P2, a hidden intermediate revision and partial P2 redaction.

## 3. Release gate and open decisions

An integrated candidate pins each upstream contract and maturity state, world branch/checkpoint, source watermarks, product and graph snapshots, model versions, evidence release, policy and test-suite digest. Qualification fails if a required upstream release is pending, a material discrepancy is unresolved, a critical negative test fails, or a hidden/evidence leak occurs. `QUALIFIED` requires signed owner/reviewer disposition and a reproducible evidence package. A passed component test cannot stand in for an end-to-end scenario. No approvals or qualifications are asserted here.

Under [ADR-0050](../../adr/0050-formal-verification-and-benchmark-stack.md), PPC locks a minimal four-layer assurance stack: **Quint** (checked by Apalache/TLC) for discrete state machines, event ordering, idempotency, branch isolation, reader-as-of cutoffs, and approval lifecycles; **Python with `z3-solver` and Hypothesis** for exact conservation, intermediate-crossing, and utility-allocation invariants; **analytical oracles and time-step convergence checks** for numerical stability; and **independent published engineering benchmarks** (GPSA, Riazi, Gary–Handwerk, Maples, EIA) plus process/controls engineer sign-off for empirical credibility. Alloy 6, Dafny, Kani, and Bend 2 remain deferred unless a concrete obligation exceeds Quint or Z3 (or Rust enters ICE/EDI). The complete proof-obligation register (`PO-01`–`PO-12`), worked tank/derate counterexamples, and engineering sign-off boundaries live in [PPC-REVIEW-004](../independent-review/PPC-REVIEW-004_Proof_Obligation_and_Validation_Register.md). All unexecuted obligations are labeled **planned**, never passed. Note that `check_package.py` and `test_check_package.py` validate documentation routing, local links, and paper fixture tables only; they do not qualify physics or runtime behavior. T25–26, T54, T73–74, T113, T120–126 in the [discussion register](../registers/PPC-Discussion-Decision-Traceability.md) supply the discussion trail.

The [exchange register](../registers/PPC-Discussion-Decision-Traceability.md) routes T1, T25–26, T54, T58, T73–74, T113, T125–126 to this draft. `GAP-002` Markdown audit is closed in [PPC-REVIEW-001 §5](../independent-review/PPC-REVIEW-001_Document_Coverage_and_Transcript_Audit.md#5-audit-of-raw-chatgpt-transcript-t1t145-versus-ef4eb08-ppc-documents-closing-gap-002).

[INFO-001 §3](../03-enterprise-information/PPC-INFO-001_Enterprise_Ontology_Identity_and_Time.md) owns the complete P0/P1/P2 publication rows, source-record times, recipient availability and reader-as-of rule used by this draft.
