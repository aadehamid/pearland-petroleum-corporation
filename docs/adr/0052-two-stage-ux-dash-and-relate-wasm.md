---
status: Decided
date: 2026-11-26
amends: ADR-014
source_answers: docs/adr/answers/2026-11-26-first-principles-grill.md#round-3-2026-11-26
---

# ADR-0052: Two-stage UX contract with FastAPI/Dash in Slice 1 and Relate WASM in Slice 1.5

## Context

In T111 (`EA09D-D09`, user-directed) the owner designated browser-based Relate WASM as a business-facing Interactive Enterprise Context Explorer for relationship, impact, and scenario exploration rather than a teaching toy. In Round 2 Q12 (`ADR-0047`) the owner kept FastAPI plus Plotly Dash as the Slice 1 workspace so browser WASM qualification does not block Slice 1 delivery.

## Decision

The owner accepted Round 3 Q17 via "Yes to all." (`docs/adr/answers/2026-11-26-first-principles-grill.md`):

- Accepted recommendation: "Yes. Lock that two-stage UX contract so Slice 1 ships cleanly on FastAPI/Dash and Relate WASM enters immediately after as a first-class business explorer once its security and compatibility gate passes."
- Slice 1 ships the bounded FastAPI plus Plotly Dash workspace to prove the end-to-end decision loop.
- Slice 1.5 promotes Relate WASM as the business-facing Interactive Enterprise Context Explorer, gated on server-side permission filtering before browser graph packaging, strict `POTENTIAL_EXPOSURE` versus model-quantified labeling, and Cypher query parity on Slice 1 snapshots.

## Consequences

- `PPC-UX-001`, `PPC-GRAPH-001`, and `PPC-PLAN-001` reflect this two-stage progression and reconcile `ADR-014`, `ADR-0047`, and T111 without contradiction.
