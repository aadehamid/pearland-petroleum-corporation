---
status: Decided
date: 2026-11-26
source_answers: docs/adr/answers/2026-11-26-first-principles-grill.md#round-3-2026-11-26
---

# ADR-0049: Complete v1 business use-case catalog (UC-1 through UC-6)

## Context

In Round 2 Q7 the owner approved the Refinery A v1 unit physics split on the condition that it supports all target business use cases. `PPC-001`, `PPC-SCENARIO-001`, and the upstream architecture transcript (T1–T3, T36, T72, T83, T100, T111, T122) define six distinct downstream operational, commercial, analytical, and cross-repository use cases that must trace back to the physical model and enabling systems.

## Decision

The owner accepted Round 3 Q14 via "Yes to all." (`docs/adr/answers/2026-11-26-first-principles-grill.md`):

- Accepted recommendation: "Yes. Lock UC-1 through UC-6 as the governing v1 use-case catalog, with max-distillate versus max-gasoline mode swing explicitly covered by the CDU/VDU, FCC, HCU, and blending equations."
- Governing v1 catalog:
  - `UC-1`: Hydrocracker compressor derate and response.
  - `UC-2`: Crude-quality rejection and delayed lab correction.
  - `UC-3`: Operational and opportunity-based backcasting.
  - `UC-4`: Interactive scenario exploration, economic mode swing (including max-distillate versus max-gasoline), and KPI decomposition into operational metrics and market indicators.
  - `UC-5`: Gulf Coast hurricane disruption and supply-chain response (preserved `PPC-001` charter scenario).
  - `UC-6`: Cross-repository coherent world benchmark feeding ICE, EDI, EPM, and ECE from one Refinery A world.

## Consequences

- Every governing equation in `PPC-ENG-001` and every enabling-system contract in `docs/enterprise-architecture/` must trace to at least one use case in `UC-1`–`UC-6`.
