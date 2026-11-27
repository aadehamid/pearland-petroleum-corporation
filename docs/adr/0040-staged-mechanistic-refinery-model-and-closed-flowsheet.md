---
status: Decided
date: 2026-11-26
source_answers: docs/adr/answers/2026-11-26-first-principles-grill.md#round-1-2026-11-26
---

# ADR-0040: Staged mechanistic refinery physics on a closed Refinery A v1 flowsheet

## Context

`PPC-001` scopes three simplified units (CDU, FCC, hydrocracker) and states that PPC is not a production refinery simulator. `PPC-ENG-001` currently relies on reduced-order rules such as a linear 0.75 availability cap on hydrocracker feed, while `PPC-WORLD-001` and the architecture review handoff require tracing a shift from crude receipt through tankage, distillation, conversion, shared hydrogen and utilities, blending, quality release, and dispatch. Without vacuum separation (or an explicit heavy-cut interface), a shared hydrogen balance, and a blending and tankage boundary, FCC and hydrocracker flows cannot close mass or propagate a compressor derate coherently.

## Decision

The owner accepted the recommendations for Round 1 Q2 and Q3 ("yes to all other" in `docs/adr/answers/2026-11-26-first-principles-grill.md`):

- **Physics ceiling (Q2, Option 2):** "Staged mechanistic core on a conservation-exact plant spine — strict transient mass, sulfur/hydrogen element, and energy conservation across the full refinery from day one, adding mechanistic unit equations (shortcut or stage vapor-liquid equilibrium, lumped reaction kinetics, polytropic compressor curves, nonlinear octane and RVP blending) only where thermodynamics or dynamics change an operational or commercial decision." Recommendation accepted: "Yes. Adopt option 2 so every plant balance is physically closed from day one, while deeper mechanistic equations enter wherever they materially change an operating or commercial decision."
- **Flowsheet boundary (Q3):** "Lock Refinery A v1 as the minimum physically closed flowsheet — crude receipt and tankage, CDU plus VDU (or an explicit atmospheric/vacuum cut boundary), FCC, hydrocracker, shared hydrogen and utility header, product blending, finished tankage, quality release, and dispatch — while treating hydrotreating, sulfur recovery, and steam/power as explicit bounded mass-and-utility interfaces until a scenario needs internal unit equations." Recommendation accepted: "Yes. Lock that minimum physically closed flowsheet as Refinery A v1, with declared mass, element, and utility boundary terms for units outside the v1 core."

## Considered options

- Conservation-exact reduced order only (rejected because thermodynamic and kinetic coupling cannot be represented where it changes operating or commercial choices).
- Full dynamic DAE process simulator from day one across every unit (rejected as disproportionate to PPC's charter).
- Keeping the three-unit charter boundary without vacuum cuts, shared hydrogen, or blending (rejected because mass and utility closure fail across conversion units).

## Consequences

- `PPC-ENG-001`, `PPC-WORLD-001`, `PPC-WORLD-002`, and `PPC-VERIFY-001` must specify conservation-exact control volumes across the full Refinery A v1 flowsheet and declare explicit boundary terms for hydrotreating, sulfur recovery, and steam/power.
- Unit-level mechanistic equations will be selected per unit in subsequent review rounds based on whether they change operational or commercial decisions.

## Post-review clarification notes (2026-11-26)

This note records subsequent amendments without altering the owner decision recorded above.

- **Amended by [ADR-0054](0054-refinery-a-flowsheet-closure-option-a-and-design-basis.md) (2026-11-26, owner-delegated stand-in Claude Fable 2):** Option A is locked. SMR, Catalytic Reformer, FCC Selective HDS, and NHT are declared bounded mass, element, and utility interfaces inside Refinery A v1, and terminal 10 vol% ethanol is a terminal boundary import. Option B is rejected. See `ADR-0054` for the 180,000 bbl/day nominal design basis, H2 header identity (`170.00` / `120.00 t/day`), and interface limits.
