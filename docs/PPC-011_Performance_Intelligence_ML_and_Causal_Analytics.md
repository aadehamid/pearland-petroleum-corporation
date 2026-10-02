# PPC-011 --- Performance Intelligence, ML, and Causal Analytics

**Purpose:** Define how PPC explains performance, forecasts outcomes,
quantifies uncertainty and optimizes alternatives.

PPC uses an **ASD-STE100-inspired** technical writing style and
consistent defined terminology.

## Performance Intelligence

Answers: What happened? Why? What may happen next? Which levers matter?

## Methods

MLflow tracks experiments/models. scikit-learn/XGBoost/LightGBM handle
predictive models. StatsForecast/MLForecast provide forecasting.
DoWhy/EconML estimate causal effects. PyMC models uncertainty. OR-Tools
optimizes constrained decisions.

## KPI explanation

Example ULSD margin variance can be decomposed into market crack,
pricing execution, outage, freight, feedstock differential, lost
optionality and residual. KPI Store records the official outcome;
diagnostic products supply drivers.

## Causal discipline

Distinguish `CORRELATED_WITH`, `INFLUENCES`, `CAUSES`, `CONSTRAINS`, and
`EXPLAINS_VARIANCE_IN`. Domain knowledge proposes causal graphs;
statistical methods estimate/refute effects. Do not infer causality from
correlation alone.

## Counterfactual

For an outage, retain the simulated actual path and a no-outage
counterfactual. The difference estimates event impact. A second
counterfactual can estimate benefit from a chosen action.

## Uncertainty

Propagate event uncertainty through capacity, production, inventory and
margin. Report distributions/intervals where useful rather than false
point certainty.

## Optimization

OR-Tools evaluates feasible transfers, spot purchases, export
reductions, yield changes or routing subject to inventory minimums,
capacities, contract/customer priorities, penalties and costs. Objective
is enterprise value/risk, not a single local metric.

## Feature strategy

Use governed DuckLake Gold feature tables initially. Add a feature-store
product only if online/offline consistency becomes a demonstrated
problem.

## Process Performance Intelligence
EPM supplies designed processes; PPC supplies event logs from executed synthetic instances. PPC can analyze conformance, rework, bottlenecks, cycle time and handoff delay and relate them to KPIs. Process-mining findings are diagnostic evidence; causal claims require causal estimation/refutation.
