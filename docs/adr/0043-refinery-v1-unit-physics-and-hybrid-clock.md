---
status: Decided
date: 2026-11-26
source_answers: docs/adr/answers/2026-11-26-first-principles-grill.md#round-2-2026-11-26
---

# ADR-0043: Refinery A v1 unit physics split and hybrid multi-rate simulation clock

## Context

`ADR-0040` established a staged mechanistic refinery model on a conservation-exact plant spine for Refinery A v1. `PPC-ENG-001` and `PPC-WORLD-002` still left open which units require mechanistic equations in v1 versus bounded conservation interfaces, and which execution clock synchronizes sub-minute OT observations, intra-step tank crossings, hourly scheduling, and daily accounting.

## Decision

The owner decided Round 2 Q7 and Q8 (`docs/adr/answers/2026-11-26-first-principles-grill.md`):

- **Unit physics split (Q7):** Owner verbatim: "Q7: yes . As long as the outcome help us determine all of the business use cases that we want to enable". Accepted recommendation: "Yes. Adopt this six-part unit split as the governing v1 physics scope for Refinery A."
  1. Tankage and transfer headers — transient mass and component-property conservation with exact intra-step bound-crossing detection (no end-of-step clipping), plus hydraulic pump and line capacity limits where routing constrains movement.
  2. CDU and VDU — crude-assay TBP/D86 cut-point separation model (cut-point shift and overlap, temperature-compensated density and Watson K, sulfur distribution by cut) rather than tray-by-tray flash.
  3. Hydrocracker (HCU) and recycle-gas compressor — polytropic compressor head and capacity curve coupled to hydrogen circulation and H2-to-oil ratio, driving a lumped-conversion and hydrogen-consumption closure (replacing the ungrounded linear 0.75 availability cap).
  4. FCC — lumped severity yield plus coke-and-heat-balance closure (feed Watson K and carbon residue plus riser severity producing gas, LPG, gasoline, LCO, slurry, and coke, bounded by regenerator air-blower coke burn).
  5. Product blending and quality release — mass-basis mixing for sulfur and density plus nonlinear blending indices for RON/MON octane, RVP, flash point, and ULSD cetane/cloud point, keeping quality hold and lot release separate.
  6. Shared hydrogen and utilities — plant-wide header balances (producers minus committed consumers), with hydrotreating, sulfur recovery, and steam/power generation represented as declared bounded mass-and-utility interface units in v1.
- **Simulation clock (Q8, Option 1):** Owner accepted via "Yes to the rest." Accepted option: "Hybrid event-and-step clock — a deterministic 1-minute canonical process balance step with exact analytical or root-finding splits at intra-step tank or constraint crossings, an optional 1-second synthetic equipment-telemetry projection layer for fast ICE machine tags (vibration, compressor speed), and explicit UTC-to-site-business-day calendars for shifts and accounting (handling 23-hour and 25-hour DST days)."

## Consequences

- `PPC-ENG-001` must specify primary engineering equations, units, reference conditions, and valid envelopes for all six unit groups and verify that they support every target business use case.
- `PPC-WORLD-002` must specify the 1-minute canonical step, exact intra-step bound-crossing splits, optional 1-second OT telemetry projection, and UTC-to-local business-day calendar mapping.

## Post-review amendment note (2026-11-26)

- **Extended by [ADR-0056](0056-identity-steward-action-thresholds-and-refinery-a-parameters.md) (owner-delegated stand-in Claude Fable 2):** Locks exact Refinery A v1 synthetic parameter ranges, FCC lump-to-stream/sulfur splits, HCU selectivity/UCO scaling, corrected Maples/Fahim RT-70 octane constants, and numerical tolerances without altering the owner decision above.
