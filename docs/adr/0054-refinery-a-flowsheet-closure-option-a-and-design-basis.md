---
status: Decided
date: 2026-11-26
amends: ADR-0040
authority: Owner-delegated stand-in (Claude Fable 2, claude-fable-5-2)
source_answers: docs/adr/answers/2026-11-26-claude-fable-2-owner-standin.md#gate-1--adr-0040-amendment-option-a
---

# ADR-0054: Refinery A v1 flowsheet closure (Option A) and nominal design basis

## Context

`ADR-0040` locked Refinery A v1's conservation-exact spine across CDU/VDU, FCC, hydrocracker, shared hydrogen/utilities, blending, tankage, and dispatch, while external review surfaced an open `WP-0` choice between Option A (adding SMR, Catalytic Reformer, FCC Selective HDS, and NHT as bounded interfaces plus terminal E10 ethanol) and Option B (external boundary imports). On 2026-11-26, the owner delegated stand-in review and gate closure to Claude Fable 2 (`claude-fable-5-2`).

## Decision

Claude Fable 2, acting as owner stand-in (`docs/adr/answers/2026-11-26-claude-fable-2-owner-standin.md`), ruled:

- **G1-1:** "I choose Option A. SMR, Catalytic Reformer, FCC Selective HDS and NHT are declared bounded mass, element and utility interfaces inside Refinery A v1. Terminal ethanol at 10 vol% is a terminal boundary import. Option B is rejected. Reasons: `SCN-A-H2CONT` is an SMR turndown, so the scenario already assumes an SMR. Option A also keeps the hydrogen and octane balances inside the plant, which is what 'first-principles physical coherence' requires."
- **G1-2:** "Crude charge is 180,000 bbl/day nominal (range 105,000–190,000). Design-blend cut yields in vol% are: LPG 2, LSR 6, heavy naphtha 12, kerosene 10, AGO 17, VGO 32, vacuum residue 21. VGO splits to HCU (36,000 planned, 40,000 maximum) and FCC (21,600 nominal, 30,000 maximum including UCO recycle)."
- **G1-3:** "'Net plant H2 supply' means SMR H2 plus reformer byproduct H2, minus the NHT draw and the FCC HDS draw. HCU, DHT and header loss draw from that net figure." Frozen fixture values: `SCN-A-T125` (`107.00` SMR + `73.00` reformer − `5.00` NHT − `5.00` FCC HDS = `170.00 t/day`; `5.00` loss, `40.00` DHT, `125.00` HCU headroom); `SCN-A-H2CONT` (`57.00` SMR + `73.00` reformer − `5.00` NHT − `5.00` FCC HDS = `120.00 t/day`; `5.00` loss, `40.00` DHT, `75.00` HCU headroom).
- **G1-4:** Bounded interface rules locked for SMR (120 t/day max, 45% min, 2%/min ramp, 3.50 kg gas/kg H2), NHT (36,000 bbl/day, 99.7 wt% liquid, `<= 0.5 ppmw` S, 0.135 wt% H2), Catalytic Reformer (30,000 bbl/day, 50% min, piecewise linear over RON 95–101 through `(95: 88.0% reformate, 2.0% H2)`, `(98: 86.0%, 2.2%)`, `(101: 83.0%, 2.6%)` with LPG and dry gas splitting the remainder in ratio `7.8 : 4.0` per Round 2 addendum `N3`), FCC Selective HDS (18,000 bbl/day, 99.5 wt% liquid, `<= 10 ppmw` S, 0.32 wt% H2, 1.0 AKI loss), DHT (60,000 bbl/day, LCO `<= 20 wt%`, `c_H2,SR` 0.45 wt%, `c_H2,LCO` 1.60 wt%, `<= 10 ppmw` S, cetane uplift +3 SR / +8 LCO), SRU (250 t/day S, 99.5% recovery), Steam and power (0.88 boiler efficiency, 2.5–4.5 GJ/t crude), and Terminal ethanol (10.0 vol% +/- 0.2, 113.0 AKI, +1.0 psi RVP bump, mass enters terminal control volume only).
- **G1-5:** "LSR naphtha goes through NHT before gasoline blending. Sweetening does not remove sulfur, so untreated LSR breaks the 10 ppmw pool limit. LSR also gets a second sink: a naphtha export boundary. Without it the regular pool sits at about 84.4 (R+M)/2 against the 84.2 gate, on my linear estimate."
- **G1-6:** "Jet, LPG, sulfur, vacuum residue, slurry and export naphtha are priced boundary sinks. They carry a market indicator and no customer contracts in v1."

## Considered options

- Option B (external boundary imports for pipeline H2, reformate/alkylate, and terminal ethanol plus heavy naphtha export) — rejected because `SCN-A-H2CONT` assumes an internal SMR and Option A keeps H2 and octane balances physically closed inside the plant.

## Consequences

- `ADR-0040` is amended to lock Option A, the 180,000 bbl/day design basis, the explicit H2 header identity, and the full bounded interface table.
- `PPC-REVIEW-002`, `PPC-ENG-001`, `PPC-WORLD-001`, `PPC-REVIEW-003`, `PPC-REVIEW-004`, and `PPC-PLAN-001` adopt Option A and remove all remaining "Option A vs Option B" wording.
