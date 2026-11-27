# Owner-Delegated Stand-In Decisions — Claude Fable 2 (`claude-fable-5-2`)

- **Date:** 2026-11-26
- **Repository baseline reviewed:** `main` @ `a192662` (after PR #10 merge)
- **Delegation authority (verbatim owner instruction, 2026-11-26 21:56 CST):**
  > `/goal can you ask Claude Fable 2 to stand in for me and review all the documents until they the plan is clear for implementation. Stop at the implementation plan commited . Do not start yet. Go through the PR process as before mereg all PR and delete unused branches`
- **Stand-in model:** `claude-fable-5-2` (Claude Fable 2, invoked read-only via `claude -p --model fable --permission-mode plan`)
- **Boundary retained by Hamid Adesokan:** Phase 0 implementation authorization and the `WP-3B` hosted/local LLM endpoint choice remain explicitly with Hamid.

---

## Verbatim Section 1 Rulings (Claude Fable 2, 2026-11-26)

Every number in Section 1 is `SYNTHETIC` unless marked otherwise. I ruled as the owner's stand-in on the three gates only. Phase 0 authorization stays with Hamid.

### Gate 1 — ADR-0040 amendment: Option A

**G1-1. I choose Option A.** SMR, Catalytic Reformer, FCC Selective HDS and NHT are declared bounded mass, element and utility interfaces inside Refinery A v1. Terminal ethanol at 10 vol% is a terminal boundary import. Option B is rejected. Reasons: `SCN-A-H2CONT` is an SMR turndown, so the scenario already assumes an SMR. Option A also keeps the hydrogen and octane balances inside the plant, which is what "first-principles physical coherence" requires.

**G1-2. Design basis.** Crude charge is 180,000 bbl/day nominal (range 105,000–190,000). Design-blend cut yields in vol% are: LPG 2, LSR 6, heavy naphtha 12, kerosene 10, AGO 17, VGO 32, vacuum residue 21. VGO splits to HCU (36,000 planned, 40,000 maximum) and FCC (21,600 nominal, 30,000 maximum including UCO recycle).

**G1-3. Hydrogen header identity.** "Net plant H2 supply" means SMR H2 plus reformer byproduct H2, minus the NHT draw and the FCC HDS draw. HCU, DHT and header loss draw from that net figure. The frozen fixtures stay exact:

| Term (t/day) | `SCN-A-T125` | `SCN-A-H2CONT` |
|---|---:|---:|
| SMR H2 | 107.00 | 57.00 |
| Reformer byproduct H2 | 73.00 | 73.00 |
| NHT draw | −5.00 | −5.00 |
| FCC HDS draw | −5.00 | −5.00 |
| **Net plant H2 supply** | **170.00** | **120.00** |
| Header loss / DHT / HCU headroom | 5.00 / 40.00 / 125.00 | 5.00 / 40.00 / 75.00 |

In fixture mode, hold all interface terms at these constants. The reformer runs from its feed tank, so a short HCU derate does not change reformer H2 inside the fixture window. In runtime mode, each term follows its interface rule below.

**G1-4. Interface boundaries.**

| Interface | Inputs | Outputs and rule | Limits |
|---|---|---|---|
| SMR | Purchased natural gas (CH4-equivalent), steam | H2 at 99.9 mol%. 3.50 kg gas per kg H2 (2.60 feed, 0.90 fuel; range 3.1–4.1). CO2 = 44/16 × gas mass, vented at the boundary. Water and combustion air are declared boundary terms. | Capacity 120.00 t/day H2. Minimum 45% (54.00). Ramp 2% of capacity per minute. |
| NHT | LSR and straight-run heavy naphtha (all of it) | Liquid 99.7 wt%, sulfur ≤ 0.5 ppmw. H2 0.135 wt% of feed (0.05–0.30). H2S to SRU by sulfur balance. | 36,000 bbl/day |
| Catalytic Reformer | Hydrotreated heavy naphtha plus HCU heavy naphtha | At RON 98, wt% of feed: reformate 86.0, H2 2.2, LPG 7.8, dry gas 4.0. Linear in severity over RON 95–101: reformate 88→83, H2 2.0→2.6. | 30,000 bbl/day, minimum 50% |
| FCC Selective HDS | All FCC naphtha | Liquid 99.5 wt%, sulfur ≤ 10 ppmw (target 8). H2 0.32 wt% (0.20–0.50). Octane loss 1.0 (R+M)/2 (0.5–2.0). | 18,000 bbl/day |
| DHT | Kerosene, AGO, FCC LCO | `c_H2,SR` 0.45 wt% (0.30–0.60). `c_H2,LCO` 1.60 wt% (1.20–2.20). Product sulfur ≤ 10 ppmw. Cetane uplift +3 on straight-run, +8 on LCO. | 60,000 bbl/day. LCO ≤ 20 wt% of feed. |
| SRU | All H2S and NH3 streams | 99.5% of sulfur (99.0–99.9) to elemental sulfur export. The rest leaves as SO2 at the boundary. NH3 leaves as N2. | 250 t/day sulfur |
| Steam and power | Fuel gas, purchased gas, purchased power | Linear specific use per tonne of unit feed. Boiler efficiency 0.88. Purchased power closes the power header. | Site energy 2.5–4.5 GJ per tonne crude |
| Terminal ethanol | Purchased denatured ethanol at each terminal | 10.0 vol% ± 0.2. Blending octane 113.0 (R+M)/2. RVP rise +1.0 psi. Mass enters the terminal control volume, never the refinery. | Per terminal |

**G1-5. Two corrections to the stream table.** LSR naphtha goes through NHT before gasoline blending. Sweetening does not remove sulfur, so untreated LSR breaks the 10 ppmw pool limit. LSR also gets a second sink: a naphtha export boundary. Without it the regular pool sits at about 84.4 (R+M)/2 against the 84.2 gate, on my linear estimate.

**G1-6. Sinks without customers.** Jet, LPG, sulfur, vacuum residue, slurry and export naphtha are priced boundary sinks. They carry a market indicator and no customer contracts in v1.

### Gate 2 — ADR-0045 and ADR-0051 operations

**G2-a. Databricks: synced copy.** WP-8 copies pinned Delta tables into Databricks Free Edition workspace-managed tables. A Dagster job on `exe.dev` runs the copy, never a laptop. No paid Databricks tier is used in v1. The paid external-location path is documented only. The WP-0 probe picks the copy mechanism. If no mechanism works, stop and raise an ADR.

**G2-b. Topology: 12 GB, lightweight collector.** Slice 1 runs one 12 GB `exe.dev` VM with an OpenTelemetry Collector that writes OTLP JSON files, shipped hourly to R2 under `telemetry/otel/`. DuckDB queries them for the trace-leak tests. Langfuse v3 with ClickHouse moves to WP-7. If `exe.dev` cannot give 12 GB on one VM, use two VMs (8 GB stores, 4 GB apps) with the same Compose files. No local Ollama runs on these VMs. This stages ADR-0048 and does not reverse it.

**G2-c. Workflow state: PostgreSQL.** All workflow, approval and LangGraph checkpoint state lives in PostgreSQL on `exe.dev`. Cloudflare D1 is not used in v1. Reason: proposal, authorization and receipt must commit in one ACID transaction with the idempotency key, and the WAL backup already covers it.

### Gate 3 — Governance, thresholds and parameters

**G3-a. Steward.** The role is `IDENTITY_STEWARD`. The PPC owner holds it until he delegates it in writing. Only this role accepts, rejects or supersedes a mapping assertion. Agents may propose candidates and never accept them. An open conflict returns `UNRESOLVED` and holds publication for that scope. No confidence score resolves a conflict automatically.

**G3-b. Action thresholds.** Volumes are barrels at 60 °F. Dollars are the absolute margin effect from a `RELEASED` `ModelRun`, or volume times pinned price for notional. If any one limit is exceeded, the next tier applies. A missing estimate counts as exceeded. The proposer never approves. An agent never approves.

| Class | Allowed actions | Limits and approver |
|---|---|---|
| `AUTO_EXECUTE` | Raise an alert. Open a draft maintenance notification. Request a LIMS retest that leaves hold status unchanged. Re-run a failed quality or reconciliation job. | 0 bbl, $0, no physical, commercial, quality or financial effect. 20 per agent per logical hour. Grant `PG-A0-v1`. |
| `REQUIRE_APPROVAL` tier 1 | Feed-rate or mode change inside the envelope. Cut-point shift. In-refinery tank transfer. | Rate change ≤ 10% and ≤ 4,000 bbl/day. Shift ≤ 5 °C. Transfer ≤ 25,000 bbl. Effect ≤ $250,000. Shift Supervisor. Expires in 30 logical minutes. |
| `REQUIRE_APPROVAL` tier 2 | Larger rate change. Max-distillate or max-gasoline swing. Inter-terminal transfer. Spot purchase or sale. Delivery reschedule ≤ 72 h. Rerouting a held lot to another hold. | Shift ≤ 15 °C. ≤ 50,000 bbl. ≤ $5,000,000 notional. Effect ≤ $1,000,000. Refinery Operations Manager for physical actions, Commercial Manager for commercial ones. Expires in 4 logical hours. |
| `ESCALATE` | Anything above tier 2. Contract allocation or force majeure. An uncertainty band that crosses a limit. No feasible option. Approver unavailable. | VP Supply and Operations (held by the owner), under a new decision ID. |
| `PROHIBITED` | Releasing a lot from `QUALITY_HOLD` or overriding an assay. Overriding a physical bound or envelope. Writing an OT setpoint, interlock or alarm limit. Changing mappings, grants, policy or thresholds. Reading or writing `evaluation/hidden/`. Retracting a release or deleting raw data. Hedges and financial postings. Using an approval on another branch. Touching any real system. | No agent path. Policy returns `DENIED`. |

Simulating inside a scenario branch is a read-class tool call and needs no approval. The AGENT-001 fixture (5,000 bbl terminal transfer) lands in tier 2 with the Commercial Manager, as that document expects.

**G3-c. Parameter ranges and tolerances.**

| Unit | Nominal and allowed range |
|---|---|
| Crude slate | Three assays: light sweet (API 39.0, S 0.35 wt%), medium sour (31.0, 1.60), heavy sour (24.0, 2.60). Design blend 30/50/20 vol%. Each assay has at least 12 TBP points and must give the G1-2 yields within ±2 vol% absolute. |
| CDU/VDU | TBP cut points in °C: 30, 85, 175, 240, 360, 565. Shift ±15. Overlap ≤ 2 wt% of crude per adjacent pair. Loss 0.2 wt% (0–0.5). |
| HCU | `R_min,vol` 4,000 SCF/bbl (3,000–6,000). Conversion 0.90 (0.40–0.95). Chemical H2 = 2.0 wt% × (ξ / 0.90). Purge plus dissolved loss 0.10 wt% (0–0.20) in runtime mode and 0 in fixture mode. Recycle H2 purity 0.85 mole fraction (0.75–0.95), held fixed in fixture mode. Heat release 30 MJ per kg H2 consumed (25–40). Compressor polytropic efficiency 0.76 (0.70–0.82). Converted products scale with ξ at the fixed selectivity of the REVIEW-002 slate. UCO = (1 − ξ) × feed. Quench must not bind at or below 1.05 × 4,336.08 t/day at 75% circulation. |
| FCC | Targets in wt% of feed: conversion 70–78, naphtha 44–52, dry gas plus LPG 16–22, coke 4.5–6.5, LCO 14–20, slurry 5–9. Unconverted lump splits 70/30 to LCO and slurry (60–80% LCO). Gas lump splits 20/80 to dry gas and LPG. Feed sulfur goes 45% H2S, 6% naphtha, 22% LCO, 17% slurry, 10% coke. Coke ceiling 7.0 wt% of 30,000 bbl/day feed. The REVIEW-002 test constants prove closure only. They give 9.0 wt% coke and are not the calibrated set. |
| Blending | RT-70 constants: `a1` 0.03324, `a2` 0.00085, `b1` 0.04285, `b2` 0.00066, `b3` −0.00632. Error bands: RVP ±0.3 psi, octane ±0.5, flash ±2 °C, cloud ±2 °C. Sulfur and density exact. Premium is at most 10% of the gasoline pool. |
| Numerics | Mass and element residual ≤ 1e-9 relative. Frozen fixtures reproduce to every printed digit. Step refinement: ≤ 1e-9 relative on tank integrals, ≤ 1e-4 on nonlinear unit outputs, zero flipped discrete outcomes. ODE `rtol` 1e-10. HiGHS feasibility 1e-7. IPOPT 1e-8. |

**G3-d. Sign-off at WP-1 exit.** Hamid Adesokan signs as PPC owner. The evidence is the PO-12 benchmark report, prepared by a process-engineering reviewer who did not write the kernel. This stand-in ruling approves the ranges above and cannot pre-sign results that do not exist yet. If WP-1 cannot close a balance inside a range, it returns to the owner and does not tune silently.

### Explicitly reserved for Hamid Adesokan

- **LLM endpoint for WP-3B:** A hosted API is paid usage, and the 12 GB VM cannot run a local model. Stand-in recommends a configured endpoint with recorded responses for golden tests; Hamid decides the live provider before `WP-3B` starts.
- **Phase 0 authorization:** Remains explicitly with Hamid Adesokan.

---

## Verbatim Stand-In Addendum (Claude Fable 2, Round 2, 2026-11-26 at commit `34f7790`)

- **N1 (HCU UCO and product scaling clarification, clarifying `G3-c`):** "Stand-in clarification: define UCO = (1 − ξ) × (feed + chemical H2) and products = `s_p` × ξ × (feed + chemical H2). This reproduces every printed number. Record it as a dated addendum under Section 1."
- **N3 (Catalytic Reformer severity curve clarification, clarifying `G1-4`):** "Stand-in clarification: piecewise linear through (95: 88.0, 2.0), (98: 86.0, 2.2), (101: 83.0, 2.6). LPG and dry gas take the remainder at 7.8 to 4.0. Same addendum."
