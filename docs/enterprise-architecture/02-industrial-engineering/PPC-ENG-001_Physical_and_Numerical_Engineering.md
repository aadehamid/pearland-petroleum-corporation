# PPC-ENG-001 — Physical and Numerical Engineering

**Draft 0.1 for owner and independent review.** Baseline: [PPC main at 6559459](https://github.com/aadehamid/pearland-petroleum-corporation/tree/655945926b7546f8dcf0c3cb0008e676b5131d76). This contract defines how a proposed change in refinery feed becomes a feasible trajectory, with a quantity, basis, uncertainty and independently checkable result. Its fictional fixture inputs are `SYNTHETIC`, hypothetical operating changes are `SCENARIO_ASSUMPTION`, and hand-calculated outputs are `DERIVED`. Runtime, plant calibration and engineering qualification remain open.

## 1. Decision and scope

The owner adopted a hybrid engineering and business simulation (T20). T73 proposes physical and engineering validation (Pillar 1, line 15572). In T74 (line 16033), the owner asks for agent-neutral specifications and established equations with a rationale wherever applicable. PPC-005 governs coherent synthetic generation. ADR-019 and ADR-034 assign numerical calculations to specialized models. PPC-011 governs analytical uses, and PPC-019 separates semantic relationships from executable calculations. The proposed calculations below support one fictional refinery. An LP case proposes feasible production under its assumptions. The world engine checks the time-dependent trajectory, inventory, utilities, quality and approved actions. Release a customer shortfall or a margin impact only after downstream logistics and commercial calculations use those results.

Stage the fidelity: first balance quantities at declared boundaries; then add assay- and mode-dependent yields and shared limits; introduce equipment dynamics only where they change a decision and have independent validation. The chartered CDU, FCC and HCU may be represented by reduced-order units. VDU, treating, utilities and blending can enter as explicit bounded interfaces until qualified as models. Document every excluded stream as an assumption or boundary term.

## 2. Interface, ownership and units

| Contract object | Required fields and rules |
|---|---|
| Model release | Stable model ID and version, engine and parameter digests, asset/configuration revision, equations, input/output units, time resolution, valid envelope, calibration and holdout references, numerical method, absolute/relative tolerances, owner and maturity. |
| Stream or lot | Stable material and movement IDs, direction, sending and receiving boundary, interval, quantity kind (mass, reference volume, rate, energy or concentration), units, reference conditions, assay revision, provenance and uncertainty. Rates require elapsed-time units. |
| Evaluation request | World release, branch, checkpoint, asset, interval, operating mode, authorized intervention where applicable, source cutoffs, balances at interval start, active constraints and supported inputs. |
| Result | Run and causal IDs, interval and basis, accepted quantities, end state, binding limits, residuals, evidence links and status. Distinguish feasible, infeasible, insufficient input and outside the qualified envelope. |
| State commitment | WORLD-001 owns physical state and authority; WORLD-002 orders, commits and replays transitions. An engineering calculation proposes a transition and evidence. A failed calculation commits no partial state. |

Choose a consistent mass basis for conversion accounting. For a liquid lot with qualified density, mass = reference volume × density at compatible reference conditions, after unit conversion. Distinguish standard from observed volume and absolute from gauge pressure. Preserve the source measurement and conversion provenance. Missing density blocks a mass conversion. Regional volume series and benchmark aggregates provide plausibility checks only. EIA explains why less-dense refined products can yield more barrels than the crude input; a volume difference alone cannot diagnose a mass-balance error. [EIA refinery inputs and outputs](https://www.eia.gov/energyexplained/oil-and-petroleum-products/refining-crude-oil-inputs-and-outputs.php)

## 3. Engineering equations and operating envelopes

| Boundary | Proposed model | Failure or qualification criterion |
|---|---|---|
| Tank or movement | Closing mass = opening mass + integrated inbound mass rate − integrated outbound mass rate − declared losses. Track stock in transit explicitly. At plant consolidation, internal transfers cancel. | Check working minimum and maximum at each crossing. A valid closing stock can conceal an infeasible intermediate stock. A transfer requires its matching leg or an identified transit balance. |
| CDU/VDU separation | For crude lot c and cut j, cut mass = sum over c of feed mass × assay cut fraction. Use nonnegative fractions and include residue and explicit losses. Fractions close to one per assay on its declared basis, within a justified tolerance. | Reject missing fractions and incompatible cut definitions. Record the unrounded residual. A cut is an intermediate stream; finished product requires downstream processing or release. |
| FCC and hydrocracker | Use mode-specific calibrated mass yields, feed envelope and explicit coproducts. Across the chosen control volume: total input mass − total output mass − change in holdup = residual. Include hydrogen addition for the HCU, and products such as gas and coke where they cross the boundary. | Document yield denominator (hydrocarbon feed or total charge). With hydrogen addition, output fractions on hydrocarbon feed alone need not sum to one. Verify element balances when making sulfur or hydrogen claims. |
| Shared utilities | Convert each binding resource into a compatible limit. Example: net allocable hydrogen kg/h divided by kg hydrogen consumed per tonne of feed bounds feed in t/h. Subtract other committed users before allocating. Sum allocations against a single network balance. | Require positive, validated intensity at the selected mode and a common interval. Distinguish gross circulation from net consumption. Shared recycle cancels within its accounting boundary. |
| Capacity and operating mode | Feasible feed is bounded by mechanical restriction, utilities, available feed, routing and receiving capacity after all limits have the same units and interval. Zero availability permits zero feed. A cap is a maximum; executed feed may be lower. | A feasible steady-state point can be unreachable within a ramp or startup interval. Dynamic claims require qualified transition limits and initial conditions. |
| Blend quality | For a conservative component on a mass basis, concentration = sum(component mass × component concentration) / total mass. Preserve quality hold and release as separate dispositions. | Empty blend has undefined concentration. Unknown or ambiguous assay remains pending. Octane and vapor pressure need validated property models. A sulfur-only calculation cannot release an entire fuel grade. |
| Energy/steam/power | When energy is binding, define a control volume, energy entering/leaving with streams, heat/work signs and transient accumulation. A reduced-order utility intensity (e.g. kWh/t) times feed t/h yields kW. | A consumption coefficient alone cannot establish thermal feasibility. Report enthalpy, heat-loss or efficiency assumptions before claiming energy closure. |

## 4. Hand-checkable fixtures

**Tank.** T125 starts with 10,000 reference bbl, a 12,000 bbl working limit, 500 bbl/h in and 700 bbl/h out for two hours. Constant density, no losses. The change is −400 bbl and the expected closing stock is **9,600 bbl**. As a new boundary case, start at 11,900 bbl with net inflow of 200 bbl/h. The tank reaches capacity at **0.5 h**. The proposed unmodified one-hour trajectory is infeasible. Restrict or reschedule the remainder only under an explicit operating rule.

**Derate.** T125 specifies 40,000 bbl/day nominal and an illustrative 0.75 availability factor. That gives a **30,000 bbl/day upper bound**. In WORLD-002 §6 the plan remains 36,000 bbl/day. At 08:10 the restriction binds executed feed at 30,000 bbl/day. At the 08:40 fork the baseline continues at that rate, while an authorized child action reduces executed feed to 24,000 bbl/day for the final 30 minutes. The baseline processes **1,500 bbl**, the child **1,375 bbl**. The **125 bbl** difference concerns HCU feed. This fixture assumes no additional binding constraint. A hydrogen-supported maximum of 28,000 bbl/day, if supplied for a different scenario, would take precedence over the mechanical maximum. No diesel yield or margin follows from either cap alone.

**Assay and hydrogen.** New synthetic unit-test values: 60 t of crude A with a 0.30 light-cut mass fraction and 40 t of crude B with a 0.20 fraction produce **26 t light cut and 74 t remainder** in a two-cut, lossless illustration. This is separation. For a separate conversion illustration, 100 t hydrocarbon plus 2 t net hydrogen entering a boundary with unchanged holdup requires 102 t of total outputs. If the output ledger totals 100 t with no declared loss, the residual is **+2 t** and the ledger fails exact closure. An engineer investigates missing streams, accumulation, units and measurements before estimating losses.

**Blending and rejection.** T24 starts with 100 t at 10 ppm sulfur by mass and a second component at 100 ppm. For a synthetic 15 ppm upper bound, the exact maximum added mass solves (1000 + 100x)/(100 + x) ≤ 15, giving **x ≤ 100/17 t**, approximately 5.88235 t. At 5 t the result is **100/7 ppm** (about 14.286); at 6 t it is **800/53 ppm** (about 15.094). Compare unrounded values on compatible bases. This is an idealized component constraint. In a crude-rejection case a delayed or disputed assay keeps stock on hold. Retain custody quantity, test revision, specification and authorized disposition separately.

## 5. Calibration, LP and fair backcasting

1. Pin the original plan and LP case, assay, forecast, prices, model parameters, physical configuration, evidence cutoff and time basis. Maintain a separate link to the observed and subsequently reconciled actual series.
2. Identify parameters with documented units and physical bounds. Fit on a declared calibration period. Record objective, constraints, solver status, parameter uncertainty and identifiable range. Flag non-identifiable coefficients; multiple fits with similar residuals can imply different interventions.
3. Evaluate on a separate holdout containing relevant loads and disturbances. Compare against a simple balance or qualified independent model; inspect bias by mode as well as aggregate error. Verify physical feasibility throughout the trajectory.
4. Freeze calibration before comparing actions. Hold initial state, disturbance policy and decision-time information constant across branches. Run changes to calibration or hindsight inputs as separate cases. Report case order, interaction and unexplained residual when attributing opportunity.
5. For each claim record the binding constraint, quantity, time period, model uncertainty and available alternative. Link product effects to qualified yields and quality, then link delivery and margin to business data products. A solver optimum outside the envelope is an unqualified result.

## 6. Numerical verification and release evidence

| Check | Independent reference and expected behavior |
|---|---|
| ENG-V01 — dimensions | Express the same flow in bbl/day and bbl/h. Integrated reference volumes agree. Reject mixed mass and volume without a supported conversion. |
| ENG-V02 — conservation and limits | Recompute the tank, assay and conversion fixtures independently. Check intermediate crossings and residual sign. Flag double-counted recycle, missing loss or unmatched transfer. |
| ENG-V03 — shared constraints | Tighten a binding utility bound with all else fixed. Maximum feasible feed cannot increase. Increasing nominal capacity while another bound binds cannot increase the feasible maximum. |
| ENG-V04 — quality | Run the two blend quantities, exact equality, zero total mass, missing assay and mismatched basis. Compare threshold before display rounding. Preserve hold when other specification fields remain unknown. |
| ENG-V05 — numerical convergence | Compare analytic balances and multiple decreasing time steps on the same pinned input. Report per-variable errors, event times and any changed discrete decision. Fail if feasibility changes unexpectedly even within an aggregate numeric tolerance. |
| ENG-V06 — recovery and isolation | Restart at a checkpoint using saved integrator history and a model/parameter digest. Match discrete outcomes and qualified numerical tolerance. A child scenario cannot mutate parent case evidence. |
| ENG-V07 — calibration and uncertainty | Publish training/holdout separation, residuals by operating mode, uncertainty and sensitivity. Report out-of-range inputs explicitly and distinguish parameter uncertainty from measurement uncertainty. |
| ENG-V08 — LP and evidence | Replay baseline, recalibrated baseline and decision alternative with separate case IDs. Resolve each conclusion to its input vintage, constraint set and feasible trajectory. An unauthorized future lab result must be absent from the decision-time case. |

For output q set absolute tolerance in q's units and dimensionless relative tolerance before testing. Compare against an independent reference using an agreed criterion such as absolute error ≤ absolute tolerance + relative tolerance × absolute reference value. Record unrounded results, mass and component residuals, solver and time-step settings, and any step or event at a bound. Failed convergence, missing inputs, and physically infeasible outcomes require distinct statuses. The exact simplified arithmetic in §4 can be checked today. Actual engine outputs, fitted yields, real operating envelopes, independent benchmarks and approved tolerances are **pending qualification**. Formal methods can test transition logic; empirical evidence is needed for claims that the physical response is realistic.

## 7. Authority, traceability and review questions

| Source | Receiving sections | Disposition |
|---|---|---|
| T20–24, especially T24 lines 3574–3914 | §§1–4 | Owner adopted hybrid simulation. Assays, modes, utilities and blending are design proposals requiring qualification. |
| T2–3, T23–27, T35 | §§2, 5–6 | Preserve case lineage, historical knowledge and execution constraints for fair attribution. |
| T37–38, T45 | §§1, 3–4 | Use licensed, revision-scoped engineering evidence and public observation vintages. Aggregate observations do not become PPC measurements. |
| T51–52 | §§1, 6 | Assess physical-simulation libraries and operating limits with independent evidence. |
| T114–115 | §6 | Version model inputs and holdouts; qualify optimization, causal assumptions, uncertainty and feasibility. |
| T73, lines 15572–15625 | §§1, 6 | Pillar 1 proposes physical checks at component, process-system and enterprise-network levels. |
| T74, lines 16030–16601 | §§1, 6 | The owner requests agent-neutral specifications, established equations with explanations, and assessment of formal verification where applicable. Tool selection remains open. |
| T122, T125 lines 36752–36916; WORLD-001 §5 and WORLD-002 §6 | §§3–6 | Preserve original tank and derate inputs. Assay fractions, 5/6 t blend trial quantities and the overfill case are new synthetic exercises. |
| PPC-005, PPC-011, PPC-019, ADR-001/019/034 | §§1–6 | Governed models calculate; semantic relationships and graph exposure aid interpretation. Existing ADRs retain their recorded scope. |

Before declaring any model qualified, reviewers should identify who owns the parameter data and tolerances, which independent benchmark covers the envelope, which omitted streams affect closure and which commercial decision changes if a simplification fails. Defer verified operational signal semantics to OT-001, engineering revision and topology to EDI-001, and executable qualification evidence to VERIFY-001. The separate upstream business-process ontology release remains a dependency for semantic mappings.

[Master index](../00-master-index/PPC-ARCH-000_Master_Architecture_Index_and_Authority_Baseline.md) · [Discussion register](../registers/PPC-Discussion-Decision-Traceability.md) · [Canonical world](../01-enterprise-world/PPC-WORLD-001_Canonical_Enterprise_World.md) · [Time and replay](../01-enterprise-world/PPC-WORLD-002_Simulation_Time_Replay_and_Branches.md) · [Synthetic generation](../../PPC-005_Synthetic_Data_Generation_Strategy.md) · [Performance intelligence](../../PPC-011_Performance_Intelligence_ML_and_Causal_Analytics.md) · [Ontology reuse](../../PPC-019_Public_Ontology_Reuse_and_Implementation_Guide.md).

The [exchange register](../registers/PPC-Discussion-Decision-Traceability.md) routes T20–21, T23–24, T35, T37–38, T45, T51–52, T73–74, T114–115, T125 to this draft.
