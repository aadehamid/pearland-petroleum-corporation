---
status: Decided
date: 2026-11-26
amends: none
authority: Owner-delegated stand-in (Claude Fable 2, claude-fable-5-2)
source_answers: docs/adr/answers/2026-11-26-claude-fable-2-owner-standin.md#gate-3--governance-thresholds-and-parameters
---

# ADR-0056: Identity steward role, numeric action-authority thresholds, and Refinery A v1 parameter ranges

## Context

`PPC-ARCH-000`, `PPC-AGENT-001`, `PPC-ENG-001`, `PPC-REVIEW-003`, and `PPC-PLAN-001` left three governance parameters open in `WP-0`: the identity-conflict steward role, concrete numeric thresholds separating agent authority classes, and initial synthetic parameter ranges and numerical tolerances for Refinery A v1. On 2026-11-26, the owner delegated stand-in gate closure to Claude Fable 2 (`claude-fable-5-2`).

## Decision

Claude Fable 2, acting as owner stand-in (`docs/adr/answers/2026-11-26-claude-fable-2-owner-standin.md`), ruled:

- **G3-a (Identity steward):** "The role is `IDENTITY_STEWARD`. The PPC owner holds it until he delegates it in writing. Only this role accepts, rejects or supersedes a mapping assertion. Agents may propose candidates and never accept them. An open conflict returns `UNRESOLVED` and holds publication for that scope. No confidence score resolves a conflict automatically."
- **G3-b (Numeric action thresholds and `PROHIBITED` class):** Volumes are barrels at 60 °F; dollars are absolute margin effect from a `RELEASED` `ModelRun` or volume times pinned price for notional. Exceeding any limit or missing an estimate escalates to the next tier; proposers and agents never approve.
  - `AUTO_EXECUTE`: alert, draft maintenance notification, LIMS retest request leaving hold unchanged, re-run failed DQ/reconciliation job (`0 bbl`, `$0`, no physical/commercial/quality/financial effect, max 20 per agent per logical hour, grant `PG-A0-v1`).
  - `REQUIRE_APPROVAL` Tier 1: feed/mode change inside envelope (`<= 10%` and `<= 4,000 bbl/day`), cut-point shift (`<= 5 °C`), in-refinery tank transfer (`<= 25,000 bbl`), margin effect `<= $250,000`; approver `Shift Supervisor`; expires in `30` logical minutes.
  - `REQUIRE_APPROVAL` Tier 2: larger rate change, mode swing, inter-terminal transfer, spot purchase/sale, delivery reschedule `<= 72 h`, rerouting a held lot to another hold (`<= 15 °C`, `<= 50,000 bbl`, `<= $5,000,000` notional, `<= $1,000,000` effect); approver `Refinery Operations Manager` (physical) or `Commercial Manager` (commercial); expires in `4` logical hours.
  - `ESCALATE`: anything above Tier 2, contract allocation/force majeure, uncertainty band crossing a limit, no feasible option, or unavailable approver; approver `VP Supply and Operations` (held by the owner) under a new decision ID.
  - `PROHIBITED` (maps to `DENIED`, no agent path): releasing `QUALITY_HOLD` or overriding an assay, overriding physical bounds/envelopes, writing OT setpoints/interlocks/alarms, changing mappings/grants/policy/thresholds, reading or writing `evaluation/hidden/`, retracting releases or deleting raw data, hedges/financial postings, cross-branch approval reuse, or touching any real system.
- **G3-c (Synthetic parameter ranges and numerical tolerances):** Locks three crude assays (light sweet 39.0 API / 0.35 wt% S, medium sour 31.0 / 1.60, heavy sour 24.0 / 2.60; 30/50/20 vol% design blend; >= 12 TBP points matching G1-2 yields within +/-2 vol%), CDU/VDU TBP cuts (`30, 85, 175, 240, 360, 565 °C`, +/-15 °C shift, overlap `<= 2 wt%`, loss `0.2 wt%`), HCU parameters (`R_min,vol` 4,000 SCF/bbl, `ξ` 0.90 nominal / 0.40–0.95, `c_H2,chem = 2.0 wt% * (ξ / 0.90)`, purge+dissolved 0.10 wt% runtime / 0 fixture, recycle H2 purity 0.85 fixed in fixture mode, 30 MJ/kg H2 heat release, `η_p` 0.76, `UCO = (1-ξ)*(feed + chemical H2)` and `products = s_p * ξ * (feed + chemical H2)` per Round 2 addendum `N1`, quench non-binding at `<= 1.05 * 4,336.08 t/day` at 75% circulation), FCC yield/split/sulfur targets (conversion 70–78%, naphtha 44–52%, gas 16–22% split 20/80 dry gas/LPG, coke 4.5–6.5% with 7.0 wt% cap at 30k bbl/day, unconverted lump split 70/30 LCO/slurry, sulfur 45% H2S / 6% naphtha / 22% LCO / 17% slurry / 10% coke), corrected Ethyl RT-70 constants (`a1=0.03324, a2=0.00085, b1=0.04285, b2=0.00066, b3=-0.00632`, premium `<= 10%` of gasoline pool), and numerical tolerances (`<= 1e-9` mass/element residual, ODE `rtol` `1e-10`, HiGHS `1e-7`, IPOPT `1e-8`).
- **G3-d (WP-1 exit sign-off):** "Hamid Adesokan signs as PPC owner. The evidence is the PO-12 [split into `PO-12a` plausibility at `WP-1` exit and `PO-12b` LP calibration at `WP-3A` exit] benchmark report, prepared by a process-engineering reviewer who did not write the kernel. This stand-in ruling approves the ranges above and cannot pre-sign results that do not exist yet. If WP-1 cannot close a balance inside a range, it returns to the owner and does not tune silently."

## Considered options

- Leaving governance thresholds and unit parameter ranges deferred to WP-0 execution (rejected because WP-1 and WP-3B implementers need exact bounded contracts upfront).
- Allowing confidence-score auto-resolution of identity conflicts (rejected to preserve deterministic `UNRESOLVED` handling).

## Consequences

- `PPC-AGENT-001`, `PPC-ENG-001`, `PPC-REVIEW-002`, `PPC-REVIEW-003`, `PPC-REVIEW-004`, and `PPC-PLAN-001` adopt `IDENTITY_STEWARD`, the `PROHIBITED` class (`DENIED`), the numeric Tier 1/Tier 2/`ESCALATE` limits, and the locked parameter/numerical tolerances.
- `PO-12` splits cleanly into `PO-12a` (Refinery A plausibility signed by Hamid at `WP-1` exit) and `PO-12b` (measurable Planning LP calibration error at `WP-3A` exit).

## Relation-verb reconciliation note (2026-11-27)

- Owner confirmed in [2026-11-27-adr-consistency-rulings.md](answers/2026-11-27-adr-consistency-rulings.md) (`"Yes to all by the way"`): frontmatter and `docs/adr/README.md` align with target ADR notes (`amends: none`; extends `ADR-0043`, `ADR-0048`, and `ADR-0050`).
