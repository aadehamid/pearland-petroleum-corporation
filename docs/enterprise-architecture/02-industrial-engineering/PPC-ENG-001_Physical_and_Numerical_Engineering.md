# PPC-ENG-001 — Physical and Numerical Engineering

**Reconciled specification (v0.3, 2026-11-26) for owner review.** Baseline inspected: `ef4eb08`; revised after independent Codex and Claude reviews. Governing decisions: [ADR-0040](../../adr/0040-staged-mechanistic-refinery-model-and-closed-flowsheet.md), [ADR-0043](../../adr/0043-refinery-v1-unit-physics-and-hybrid-clock.md), [ADR-0048](../../adr/0048-pyomo-optimization-and-langgraph-pydantic-agents.md), [ADR-0049](../../adr/0049-v1-business-use-cases.md), [ADR-0050](../../adr/0050-formal-verification-and-benchmark-stack.md). Full derivations, primary citations, units, and shift trace live in [PPC-REVIEW-002](../independent-review/PPC-REVIEW-002_Governing_Refinery_Equations_and_Balances.md). Proof obligations live in [PPC-REVIEW-004](../independent-review/PPC-REVIEW-004_Proof_Obligation_and_Validation_Register.md). Fictional inputs are `SYNTHETIC`, hypothetical operating changes are `SCENARIO_ASSUMPTION`, and verified arithmetic outputs are `DERIVED`. Runtime execution, calibration, and qualification remain **planned**, not passed.

## 1. Decision and scope

Under [ADR-0040](../../adr/0040-staged-mechanistic-refinery-model-and-closed-flowsheet.md), PPC builds a **First-Principles Refinery Model** ([GLOSSARY.md](../../../GLOSSARY.md)): a conservation-exact transient mass, sulfur/hydrogen element, and energy spine across **Refinery A v1**, adding mechanistic thermodynamic, kinetic, or hydraulic equations wherever they change an operational or commercial decision across `UC-1` through `UC-6` ([ADR-0049](../../adr/0049-v1-business-use-cases.md)).

Refinery A v1 locks crude receipt and segregated hold tankage (`TK-101H`), CDU plus VDU cut-point separation, FCC, hydrocracker with recycle-gas compressor, shared hydrogen and utility headers, feed-dependent DHT routing (carrying LCO, kerosene, and AGO before ULSD blending), product blending, finished tankage, quality release, and dispatch. External refining review identified two physical-closure items requiring WP-0 owner disposition on `ADR-0040` ([PPC-REVIEW-002 §1](../independent-review/PPC-REVIEW-002_Governing_Refinery_Equations_and_Balances.md#critical-flowsheet-closure-finding-requiring-wp-0-owner-disposition-proposed-amendment-to-adr-0040)): selecting **Option A** (add SMR, Catalytic Reformer, and FCC Selective HDS as declared bounded interfaces plus terminal 10 vol% ethanol) or **Option B** (purchased pipeline $\text{H}_2$, purchased reformate/alkylate, and terminal ethanol at the boundary, exporting heavy naphtha).

Python with SciPy/NumPy evaluates the canonical world kernel. Pyomo with HiGHS (extending to IPOPT for NLP checks) executes a **deliberately reduced Planning LP** (delta-base vectors, linear blend indices, lagged assays) kept distinct from the mechanistic world kernel so `UC-3` backcasting isolates genuine LP calibration error ([ADR-0048](../../adr/0048-pyomo-optimization-and-langgraph-pydantic-agents.md)).

## 2. Interface, ownership and units

| Contract object | Required fields and rules |
|---|---|
| Model release | Stable model ID and version, engine and parameter digests, asset/configuration revision, equation IDs (`EQ-01`–`EQ-09`), units, time resolution (1-minute canonical step + exact intra-step crossing splits per [ADR-0043](../../adr/0043-refinery-v1-unit-physics-and-hybrid-clock.md)), valid envelope, calibration/holdout refs, numerical tolerances, owner, and maturity. |
| Stream or lot | Stable material/movement IDs, direction, sending/receiving control volume, half-open interval `[start, end)`, quantity kind (SI mass `kg`/`t`, standard volume `bbl` at 60 °F / 14.696 psia, rate, energy, concentration), units, reference conditions, assay revision, provenance class, and uncertainty. |
| Evaluation request | World release, branch, checkpoint, control volume, interval, operating mode, authorized intervention, source cutoffs, opening balances, active constraints, and supported inputs. |
| Result | Run and causal IDs, interval and basis, accepted quantities, closing state, binding limits, mass/element/energy residuals, evidence links, and status (`FEASIBLE`, `INFEASIBLE`, `INSUFFICIENT_INPUT`, `OUT_OF_ENVELOPE`). |
| State commitment | [WORLD-001](../01-enterprise-world/PPC-WORLD-001_Canonical_Enterprise_World.md) owns physical state; [WORLD-002](../01-enterprise-world/PPC-WORLD-002_Simulation_Time_Replay_and_Branches.md) orders, commits, and replays transitions. Failed calculations commit no partial state. |

SI mass (`kg` or `t`) is the sole conservation basis (`EQ-01`). Convert standard liquid volumes (`bbl` at `60 °F / 14.696 psia`, API MPMS Ch. 11.1) using exact rational densities $\rho_{\text{ref}} = \text{SG}_{60/60}\cdot 999.016\text{ kg/m}^3$ and $c_{\text{bbl}} = 0.158987294928\text{ m}^3/\text{bbl}$. Never sum barrels of different densities as mass. Missing density returns `INSUFFICIENT_INPUT`.

## 3. Governing engineering equations and operating envelopes

Full equations, constants, valid ranges, and primary citations live in [PPC-REVIEW-002](../independent-review/PPC-REVIEW-002_Governing_Refinery_Equations_and_Balances.md).

| Control volume | Governing equation ID and model (`ADR-0043`) | Failure or qualification criterion |
|---|---|---|
| Density & reference basis | `EQ-01` (API MPMS Ch. 11.1; Riazi Ch. 2): $\text{SG}_{60/60} = 141.5/(\text{API}+131.5)$; $m = V_{\text{std}}\cdot c_{\text{bbl}}\cdot\rho_{\text{ref}}$. | Missing density or uncompensated temperature fails conversion. |
| Tankage & transfer headers | `EQ-02` (Perry's §4) & `EQ-03` (Perry's §6 Darcy–Weisbach, Colebrook–White, Churchill 1977 transition band `2100 < Re < 4000`, ANSI/HI 9.6.7 viscous pump correction): transient mass balance with exact intra-step bound crossing $t^*$; explicit transit stock $M_{\text{transit}} \ge 0$. | Check $M_{\min} \le M_k(t) \le M_{\max}$ at every crossing (`PO-01`). End-of-step clipping is forbidden. Every transfer requires its matching leg or transit balance (`PO-02`). |
| CDU + VDU separation | `EQ-04` (Riazi Ch. 2–3; Gary–Handwerk Ch. 3–4): TBP cut-point split with zero-sum overlap ($\sum_j \delta_{\text{overlap},j} = 0$), Watson $K_w$, and cut sulfur conservation. | Cut shifts bounded within $\pm 15^\circ\text{C}$. Reject missing fractions or nonzero overlap sum. |
| HCU & recycle compressor | `EQ-05` (GPSA §13 polytropic head $H_p$; Gary–Handwerk Ch. 8; Maples Ch. 11): mass-basis `min(...)` over mechanical cap, mass-converted recycle $\text{H}_2$-to-oil bound $(w_{\text{H2,rec}}\dot{m}_{\text{rec,max}})/R_{\min,\text{mass}}$, inter-bed quench duty bound, and shared-$\text{H}_2$ allocation $\dot{m}_{\text{H2,alloc}}/c_{\text{H2,net}}(\xi)$; explicit $P_{\text{H2}}$ purity closure; exact mass closure separating gas/acid-gas from liquid barrels. | All candidate bounds share exact SI mass-rate units (`PO-05`). Tightening compressor speed, quench, or shared $\text{H}_2$ cannot increase feasible feed. |
| FCC reactor–regenerator | `EQ-06` (Lee, Chen, Huang, & Chen 1989 4-lump model extending Weekman–Nace 1970; Gary–Handwerk Ch. 6): inlet CCR split $y_D(0) = f_{\text{add}} w_{\text{CCR}}$, $y_A(0) = 1 - y_D(0)$ guaranteeing $d(\sum y)/d\tau = 0$ identically; coupled reactor–regenerator coke/heat balance bounded by air-blower coke burn and $T_{\text{regen,max}}$. | Mass residual $\le 10^{-9}$ for any positive CCR; energy residual $\le 10^{-4}$ relative (`PO-06`). Route LCO through DHT before ULSD blending. |
| Shared H2, DHT & utilities | `EQ-07` (Perry's §4; Gary–Handwerk Ch. 16): single header balance subtracting header losses $\dot{m}_{\text{H2,loss}}$ and committed priority users before allocating headroom; DHT $\text{H}_2$ demand and cetane/sulfur scale with feed LCO fraction. | No double allocation of shared $\text{H}_2$ (`PO-04`). Producer control volume locked in WP-0 (`ADR-0040` Option A or B). |
| Blending & quality release | `EQ-08` (exact mass sulfur/density; Chevron $\text{RVP}^{1.25}$; Ethyl RT-70 RON/MON; Wickey–Chittenden flash; Hu–Burns/Riazi cloud $T^{20}$; ASTM D975 cetane). Refinery BOB gate (`84/88 (R+M)/2`) + terminal `E10` ethanol (`87/91`); ULSD `<= 15 ppmw` S, flash `>= 52 °C`, D613 CN `>= 40` (or D4737 CI `>= 40` with aromatics `<= 35 vol%`). | Unrounded threshold check (`PO-07`). Empty blend, missing assay, or unhydrotreated LCO stays `QUALITY_HOLD`. |
| Economic objective & backcasting | `EQ-09` (Maples; Pyomo + HiGHS/IPOPT): Planning LP structurally reduced vs mechanistic World Kernel so $\Delta\Pi$ decomposes cleanly into LP calibration error, decision opportunity, and execution residual. | Pin case order, evidence cutoff, model vintage, and price vintage. |

## 4. Python-verified hand fixtures

**Tank conservation and intermediate overfill (`PO-01`).** At pinned $\text{SG}_{60/60} = 0.840$ ($\rho_{\text{ref}} = 839.173440\text{ kg/m}^3$, `133.417915 kg/bbl`), `T125` starts at `10,000 bbl` (`1,334,179.15 kg`), working cap `12,000 bbl`, `500 bbl/h` in (`66,708.96 kg/h`) and `700 bbl/h` out (`93,392.54 kg/h`) for `2 h`, closing at **9,600 bbl** (`1,280,811.99 kg`, residual `0.00 kg`). Boundary test: start at `11,800 bbl` (`1,574,331.40 kg`), hour 1 net `+400 bbl/h`, hour 2 net `-500 bbl/h`. Closing stock at `2 h` is `11,700 bbl` (`1,560,989.61 kg`), yet the tank crosses `12,000 bbl` at **0.5 h** and overflows to `12,200 bbl` (`1,627,698.57 kg`) at `1 h` unless split at $t^* = 0.5\text{ h}$.

**Mechanistic compressor derate (`EQ-05`, `EQ-07`, `PO-04`, `PO-05`).** Nominal VGO charge is `40,000 bbl/day` ($\text{SG} = 0.910 \Rightarrow 5,781.44\text{ t/day}$). At `08:10 UTC`, a `SCENARIO_ASSUMPTION` compressor speed/driver restriction lowers recycle $\text{H}_2$ flow to 75% (`289.17 t/day` pure $\text{H}_2$ at $R_{\min,\text{mass}} = 0.06669\text{ kg/kg}$), yielding a `SCENARIO_ASSUMPTION` **30,000 bbl/day** (`4,336.08 t/day`) feed cap (assuming the unit runs at $R_{\min}$ at `40,000 bbl/day` with quench and shared $\text{H}_2$ non-binding). Across the 70-minute window `08:00–09:10 UTC` (`WORLD-002 §6`), baseline processes **1,500 bbl** and the `08:40 UTC` child branch (`24,000 bbl/day` for the final 30 minutes) processes **1,375 bbl** (`125 bbl` difference). With `2.0 wt%` synthetic chemical $\text{H}_2$ uptake (`86.72 t/day`, `1,199.7 SCF/bbl`), total mass output is **4,422.80 t/day** (`0.00 t/day` residual) across acid gas (`66.34 t/day`), dry gas (`44.23 t/day`), LPG (`154.80 t/day`), and $\text{C}_5+$ liquids (`32,643.6 bbl/day`, `+8.81%` liquid volumetric gain; complete slate in `PPC-REVIEW-002 §3`). Under a constant-uptake, zero-purge-loss shared-$\text{H}_2$ boundary test (`75.00 t/day` headroom after `40.00 t/day` DHT), shared $\text{H}_2$ overrides the compressor cap at `3,750.00 t/day` (`25,945 bbl/day`).

**FCC positive-CCR closure (`EQ-06`, `PO-06`).** With $w_{\text{CCR}} = 0.04$, $f_{\text{add}} = 0.75$ ($y_D(0) = 0.030$, $y_A(0) = 0.970$), integrating Lee et al. (1989) to $\tau = 1$ yields $y_A + y_B + y_C + y_D = 1.000000000000$.

**Realistic summer gasoline RVP and mass sulfur blending (`EQ-08`, `PO-07`).** `95 vol%` summer RBOB base (`7.00 psi`, $BI = 11.3860$) plus `5 vol%` $n$-butane (`52.00 psi`, $BI = 139.6382$) gives $BI_{\text{blend}} = 17.7986$ and **$\text{RVP}_{\text{blend}} = 10.01\text{ psi}$** (`+0.76 psi` above linear average `9.25 psi`, pushing a `9.50 psi` summer spec off-grade). Sulfur (`T24`): `100 t` at `10 ppmw` plus $x$ tonnes at `100 ppmw` $\le 15\text{ ppmw}$ requires $x \le \mathbf{100/17\text{ t}}$ (`5.88235 t`): `5 t` gives `100/7 ppmw` (`14.286`, PASS); `6 t` gives `800/53 ppmw` (`15.094`, HOLD).

## 5. Calibration, LP and fair backcasting

1. Pin the original plan, deliberately reduced Planning LP case, assay revision, forecast, price vintage, model parameters, configuration, evidence cutoff, and time basis separately from observed and reconciled actuals.
2. Assign parameter ranges and owners in `WP-0`; validate numeric calibration against holdout disturbances and published benchmarks at the `WP-1` exit gate (`PO-12`). Never claim real plant calibration for synthetic parameters.
3. Freeze calibration before comparing operating alternatives. Hold initial state, paired exogenous RNG streams, and decision-time evidence constant across branches (`WORLD-002 §5`). Report case order and interaction residuals (`EQ-09`).
4. Record binding constraints, units, uncertainty, and feasible alternatives for every economic claim. A solver optimum outside the valid envelope returns `OUT_OF_ENVELOPE`.

## 6. Numerical verification and release evidence

Checks `ENG-V01`–`ENG-V08` map directly to proof obligations `PO-01`–`PO-12` in [PPC-REVIEW-004](../independent-review/PPC-REVIEW-004_Proof_Obligation_and_Validation_Register.md) under the [ADR-0050](../../adr/0050-formal-verification-and-benchmark-stack.md) assurance stack (Quint + Python/Z3/Hypothesis + analytical/engineering benchmarks).

| Check | Mapped proof obligations & independent expected behavior |
|---|---|
| ENG-V01 — dimensions | `PO-02`, `PO-05`: Verify exact mass-basis unit cancellation in `EQ-01` and `EQ-05`; reject mixed mass/volume bounds without density conversion. |
| ENG-V02 — conservation and limits | `PO-01`, `PO-02`, `PO-06`: Recompute tank, intermediate-overfill, FCC positive-CCR, and HCU gas/liquid slates independently; reject overfill, negative inventory, and unmatched transfer. |
| ENG-V03 — shared constraints | `PO-04`, `PO-05`: Tighten compressor speed, quench, or shared $\text{H}_2$ headroom; maximum feasible feed cannot increase; double allocation of shared $\text{H}_2$ rejected. |
| ENG-V04 — quality | `PO-07`: Verify Chevron RVP, RT-70 octane, Wickey–Chittenden flash, Hu–Burns cloud, ASTM D975 cetane, and BOB `84/88` + E10 rules on unrounded thresholds; preserve `QUALITY_HOLD` on missing assay or unhydrotreated LCO. |
| ENG-V05 — numerical convergence | `PO-11`: Compare `60 s`, `10 s`, and `1 s` steps plus analytical crossings and 23/25-hour DST days; fail if any discrete bound or decision flips. |
| ENG-V06 — recovery and isolation | `PO-03`, `PO-09`: Restart from checkpoint with saved state and parameter digest; match discrete outcomes and tolerances; child branch never mutates parent. |
| ENG-V07 — calibration and uncertainty | `PO-06`, `PO-12`: Publish training/holdout separation, mode residuals, EIA/textbook plausibility checks, and process-engineer sign-off at WP-1 exit. |
| ENG-V08 — LP and evidence | `PO-08`, `PO-10`, `PO-12`: Replay Planning LP vs recalibrated LP vs decision-time alternative under separate case IDs (`UC-3`); future lab results stay absent at cutoff. |

All runtime checks above are **planned**. Only the Python-checked paper fixtures in §4 and `PPC-REVIEW-002 §3` have been verified today.

## 7. Authority, traceability and review questions

| Source | Receiving sections | Disposition |
|---|---|---|
| T20–24, T73–74, T114–115, T125 | §§1–6 | Reconciled through [ADR-0040](../../adr/0040-staged-mechanistic-refinery-model-and-closed-flowsheet.md), [ADR-0043](../../adr/0043-refinery-v1-unit-physics-and-hybrid-clock.md), [ADR-0048](../../adr/0048-pyomo-optimization-and-langgraph-pydantic-agents.md), [ADR-0050](../../adr/0050-formal-verification-and-benchmark-stack.md), and [PPC-REVIEW-002](../independent-review/PPC-REVIEW-002_Governing_Refinery_Equations_and_Balances.md). |
| T2–3, T23–27, T35 | §§2, 5–6 | Preserves case lineage, Planning LP separation, and fair attribution (`EQ-09`, `UC-3`). |
| T37–38, T45, T51–52 | §§1, 3–4, 6 | No-paid-commercial-license constraint enforced; public EIA/NOAA observations condition scenarios without becoming PPC plant measurements. |
| PPC-005, PPC-011, PPC-019, ADR-001/019/034 | §§1–6 | Governed engineering and Pyomo models compute; semantics and graph projections never compute. |

Process and controls engineer sign-off boundaries are tracked in [PPC-REVIEW-004 §4](../independent-review/PPC-REVIEW-004_Proof_Obligation_and_Validation_Register.md#4-engineering-judgment-boundaries-process--controls-engineer-sign-off).

[Master index](../00-master-index/PPC-ARCH-000_Master_Architecture_Index_and_Authority_Baseline.md) · [Governing equations](../independent-review/PPC-REVIEW-002_Governing_Refinery_Equations_and_Balances.md) · [Proof obligations](../independent-review/PPC-REVIEW-004_Proof_Obligation_and_Validation_Register.md) · [Canonical world](../01-enterprise-world/PPC-WORLD-001_Canonical_Enterprise_World.md) · [Time and replay](../01-enterprise-world/PPC-WORLD-002_Simulation_Time_Replay_and_Branches.md).

The [exchange register](../registers/PPC-Discussion-Decision-Traceability.md) routes T20–21, T23–24, T35, T37–38, T45, T51–52, T73–74, T114–115, T125 to this draft.
