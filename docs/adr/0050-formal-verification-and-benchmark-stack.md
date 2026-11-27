---
status: Decided
date: 2026-11-26
source_answers: docs/adr/answers/2026-11-26-first-principles-grill.md#round-3-2026-11-26
---

# ADR-0050: Formal verification and empirical validation stack

## Context

In T26 and T74 the owner asked where formal verification and battle-tested engineering equations apply across PPC. Seventeen formal-methods tools were reviewed, and `PPC-ENG-001` and `PPC-VERIFY-001` left tool selection open. Adopting four or five separate proof languages introduces specification drift, whereas a tight two-tool formal core paired with independent engineering benchmarks covers every discrete, algebraic, and continuous obligation.

## Decision

The owner accepted Round 3 Q15 via "Yes to all." (`docs/adr/answers/2026-11-26-first-principles-grill.md`):

- Accepted recommendation: "Yes. Lock Quint, Python/Z3 with Hypothesis, and independent engineering benchmarks as the primary verification stack, keeping Alloy, Dafny, Kani, and Bend 2 deferred until a concrete obligation requires them."
- Primary assurance stack:
  1. Quint (checked by Apalache/TLC) for discrete state machines, event ordering, idempotent retry, branch isolation, reader-as-of cutoffs, and approval lifecycles.
  2. Python with `z3-solver` and Hypothesis property-based tests for exact conservation and feasibility invariants.
  3. Independent published engineering benchmarks and analytical oracles for continuous numerical convergence and empirical refinery credibility.
  4. Alloy 6, Dafny, Kani, and Bend 2 deferred until a concrete obligation exceeds Quint or Z3 (or a Rust component enters ICE/EDI).

## Consequences

- `PPC-VERIFY-001` and the proof-obligation register assign each material property to Quint, Z3/Hypothesis, analytical oracle, or empirical engineering benchmark, and label every unexecuted check `planned`.
