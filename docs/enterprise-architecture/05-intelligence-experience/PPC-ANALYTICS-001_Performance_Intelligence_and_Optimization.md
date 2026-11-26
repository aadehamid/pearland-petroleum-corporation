# PPC-ANALYTICS-001 — Performance Intelligence and Optimization

Inspected PPC baseline: [`01027a84be5d453cbb4e2ea091e4884729918b15`](../registers/PPC-SOURCE-REGISTER.md). This commit is an inspection reference, not owner approval.

| Control | Value |
|---|---|
| ID / status | PPC-ANALYTICS-001 / proposed draft, 0.1.0, 2026-11-25 |
| Authority | [PPC-011](../../PPC-011_Performance_Intelligence_ML_and_Causal_Analytics.md), [ENG-001](../02-industrial-engineering/PPC-ENG-001_Physical_and_Numerical_Engineering.md), [PPC-017](../../PPC-017_EPM_Dependency_Semantic_Authority_and_Process_Conformance_Contract.md); ADR-019, 034 |
| Contract | Pinned product/model/branch inputs → quantified result with limits and lineage |

## 1. Authority and methods

EPM defines KPI meaning. PPC's qualified computation calculates values and effects. Physical engineering constrains feasible outcomes. A graph path identifies candidates for analysis, not a numerical effect. Forecasting, counterfactual simulation, process diagnosis, optimization and causal estimation are different methods and require different evidence. The baseline names OR-Tools, MLflow, StatsForecast/MLForecast, DoWhy/EconML and PyMC. Pyomo/HiGHS is a candidate, not a recorded replacement. The system has no authority over a real facility.

`ModelRun` requires run ID, method class, model/formula/parameter digests, branch, actor/role and access scope, knowledge cutoff, world and product release IDs, horizon, grain, units, input provenance, seed, solver configuration, feasibility status, uncertainty representation and output digest. A result is `DRAFT → VALIDATED → RELEASED → SUPERSEDED`. Invalid inputs, out-of-envelope parameters or an infeasible solver return an explicit status and diagnostics, never a persuasive point estimate. A scenario input is `SCENARIO_ASSUMPTION`; a forecast is `ESTIMATED`; a deterministic calculation over a synthetic world is `DERIVED` with synthetic lineage.

## 2. Worked alternatives

For separate `SYNTHETIC` capacity illustration `CAP-ILLUS-01`, 100,000 bbl/day is the baseline hydrocracker feed limit and 80,000 bbl/day is the derated limit. A `SCENARIO_ASSUMPTION` proposal to feed 90,000 bbl/day is infeasible by a `DERIVED` 10,000 bbl/day. The maximum permitted daily feed under a constant 80,000 bbl/day bound is 80,000 bbl (`DERIVED`) for 24 elapsed hours. This is a reduced-order capacity example, not compressor thermodynamics. If a qualified model estimates 0.4 bbl ULSD per bbl feed (`ESTIMATED`), the `DERIVED` 20,000 bbl/day feed reduction implies an `ESTIMATED` 8,000 bbl/day ULSD difference. Inventory, blending and contract constraints can reduce or change the commercial impact; they must be modeled before margin is stated.

An optimizer can compare no action with a 5,000 bbl spot purchase. The purchase is feasible only if location, timing, quality, credit and approvals pass. A duplicate model run with identical input digest, actor/role, access scope, branch, knowledge cutoff and pinned releases returns the same result ID or an explicitly equivalent reproducible result. A late input creates a new run; an old decision keeps its original model result. A restricted contract cannot enter a planner's optimization or leak through an option list. A sibling branch's capacity cannot enter baseline.

## 3. Qualification and decisions

Check dimensions, independent conservation oracle, envelope crossings, objective sign, known feasible/infeasible LP cases, solver tolerance, seed replay, backtest against held-out synthetic history, temporal leakage, branch isolation and permission filtering. For a causal claim, record intervention definition, assumptions, confounders, identification strategy and sensitivity analysis; a simulated difference alone is a model counterfactual. Store exact inputs, expected/observed outputs, versions and reviewer disposition. None is reported as executed. Open decisions: acceptable calibration envelope, economic objective, uncertainty intervals and OR-Tools versus Pyomo/HiGHS. T23–26, T35 and T113–115 in the [discussion register](../registers/PPC-Discussion-Decision-Traceability.md) are proposal provenance for this separate illustration. T125 governs the 40,000 to 30,000 bbl/day Scenario A fixture in WORLD-001 and SCENARIO-001.

The [exchange register](../registers/PPC-Discussion-Decision-Traceability.md) routes T1–3, T23–26, T35, T59–61, T100, T110–115 and T125 to this draft. This is topic-level routing; GAP-002 item and original-asset checks remain open.
