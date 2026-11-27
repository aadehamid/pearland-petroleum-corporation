---
status: Decided
date: 2026-11-26
source_answers: docs/adr/answers/2026-11-26-first-principles-grill.md#round-1-2026-11-26
---

# ADR-0041: Function-first lean core enabling stack aligned with sister repositories

## Context

`PPC-REG-001` (ADR-001 through ADR-039) commits PPC to more than twenty products, and `PPC-ARCH-000` §7 flags seven existing ADRs (007, 009, 014, 015, 016, 017, 018) for reassessment alongside new OT and agent candidates. At the same time, PPC serves as the shared executable world model consumed by the listed sister repositories (`enterprise-performance-model`, `scada_harmonization`, `Engineering_Drawing_to_Graph`, and `enterprise-context-engineering`), whose goals and contracts must remain coherent with PPC's technology choices.

## Decision

The owner decided Round 1 Q1 and Q4 (`docs/adr/answers/2026-11-26-first-principles-grill.md`):

- **Mission boundary and cross-repo alignment (Q1):** Owner verbatim: "Q1. Yes. Everything we created from first principle in PPC is meant to be used by the other repos listed in PPC docs. The world model is created in PPC. and the technological choices made must align with PPC and other repos golas . You will see sections on repo responsibility innthe doc." Recommendation accepted: "Yes. Keep PPC as the single target, stay strictly documents-only through architecture reconciliation and the implementation plan, and wait for separate authorization before any Phase 0 code or prototypes."
- **Enabling-systems posture (Q4, Option 1):** Owner accepted via "yes to all other". Option 1: "Function-first lean core plus staged extensions — define the refinery's operational and business functions first, commit the smallest coherent runnable stack that proves the full physical-to-decision loop in Slice 1, and explicitly defer or retire heavy products via ADR until a scenario demands them." Recommendation accepted: "Yes. Adopt option 1 so we prove physical, temporal, semantic, and decision coherence on a lean runnable core first without discarding the broader enterprise roadmap."

## Considered options

- Standing up the full twenty-plus product baseline stack from Slice 1 (rejected due to integration and operational drag before proving core physical-to-decision coherence).
- Permanently stripping PPC down to a Python-only lab and discarding enterprise platforms (rejected so the staged enterprise roadmap and sister-repo alignment remain intact).

## Consequences

- Every technology reassessment (ADR-007, 009, 014, 015, 016, 017, 018, plus OT, optimization, and agent choices) must be evaluated against both Slice 1 lean-core coherence and the shared goals of EPM, ICE, EDI, and ECE.
- No implementation code or prototypes are authorized until the architecture reconciliation and implementation plan are delivered and Phase 0 is separately approved.
