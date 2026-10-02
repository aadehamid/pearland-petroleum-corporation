# PPC-005 --- Synthetic Data Generation Strategy

**Supersedes:** PPC-SIM-002\
**Purpose:** Generate a realistic fictional PPC enterprise that remains
logically connected to public observations.

PPC uses an **ASD-STE100-inspired** technical writing style. PPC does
not claim formal ASD-STE100 compliance. Terms keep one defined meaning
across the documentation.

## Core rule

Do not generate independent plausible tables. Generate **one coherent
canonical PPC world**, then materialize different slices into source
systems.

``` text
Observed external state
→ Canonical PPC world
→ heterogeneous source-system materialization
→ enterprise integration
→ DuckLake/Databricks
→ data products/KPIs
```

## Provenance

Every material value is `OBSERVED`, `DERIVED`, `ESTIMATED`, `SYNTHETIC`,
or `SCENARIO_ASSUMPTION`. Store source, effective/publication time,
generation method, run ID, seed, model version, scenario and confidence.

## Generation layers

1.  Public environment.
2.  Stable PPC master data.
3.  Operational state.
4.  Commercial state.
5.  Derived metrics/KPIs.
6.  Events/scenario branches.
7.  Recommendations/actions/outcomes.

## Public anchoring

PPC is a plausible subset of PADD 3, not an unrelated universe. PPC
throughput/inventory/demand are conditioned on regional observations
within governed bounds. PPC-specific events can create deviations.

## Physical rules

Inventory: ending = beginning + receipts + production + transfers in -
shipments - transfers out - losses.\
Refinery: product output + losses approximately equals feed input.\
Capacity: throughput/movement/inventory cannot exceed available
capacity.\
Movement: destination inventory cannot appear without a valid source and
transit.

## Commercial rules

Customer demand combines baseline profile, seasonality, regional demand
factor, price response, contract effect, event effect and correlated
noise. Transaction price = observed benchmark + regional basis + PPC
differential + logistics/customer adjustment. Positions derive from
trades, inventory, commitments and hedges.

## Margin accounting

Realized Margin = Revenue - product/feedstock cost - freight - variable
operating cost - compliance cost - other governed variable costs. Margin
Leakage = Theoretical Margin - Realized Margin. Margin Capture % =
Realized/Theoretical.

## Correlated randomness

Use global + PADD + product + asset + customer/lane residual shocks.
Avoid independent noise on every field.

## Deliberate integration realism

Materialized systems intentionally differ in identifiers, schemas, time
zones, grains, update methods and terminology. Example: Customer may be
`ACC-481`, `100392`, `CP-8892`, and ship-to `78422`. Product may be
ULSD, DSL2, DIESEL, or a broader public distillate category. Integration
must resolve these differences.

## Time discipline

Store `effective_time` and `publication_time`. Never let a decision use
a public observation before publication unless a scenario explicitly
grants foresight.

## Event propagation

Event → exposed entity → state change → operational effect →
data-product effect → metric/KPI effect → candidate action. Store lag,
duration, recovery curve, confidence and affected products.

## Counterfactuals

Retain baseline and scenario branches. Do not overwrite history.
Counterfactuals quantify event impact, action benefit and loss avoided.

## Generation order

Calendar/dimensions → public observations → master data →
capacities/contracts → forecasts → availability → throughput →
yields/production → logistics capacity → movements → actual demand →
inventory → pricing/trades → costs → deliveries → positions/hedges →
margin → metrics → KPIs → scenarios → recommendations/actions →
outcomes/learning.

## Quality gates

Referential integrity, conservation, capacity, accounting, temporal
leakage, statistical plausibility, event connectivity, provenance and
reproducibility are hard gates.

## PPC World v0.1

One Gulf Coast refinery; simplified CDU/FCC/hydrocracker; three
terminals; primary product pipeline plus truck/marine; ULSD/gasoline;
twelve customers; twelve months daily history; public data aligned to
the same period; hurricane, unit outage, logistics and RIN/regulatory
scenarios.

## Source-system materialization

Canonical world is durably snapshotted in R2. Commercial slices go to
PostgreSQL, logistics to MySQL, refinery/edge to SQLite, workflow state
to D1, CRM/ERP objects through Twenty/ERPNext. Integration must
reconstruct the conformed enterprise model without using hidden
canonical IDs as shortcuts.

## Evidence-world generation
The generator produces a complete **canonical PPC world** and a partial **agent-visible evidence world**. The evidence world can include stale assumptions, delayed updates, incomplete documents and controlled contradictions while canonical truth remains coherent.

For material decisions, generate a hidden canonical decision dossier first, then role-specific records/documents from controlled slices. Store authoring, effective, publication/availability, ingestion and decision time separately. Canonical truth and hidden dossiers are not normal retrieval sources during blind evaluation.

## EPM-driven process generation
Where EPM publishes machine-readable process authority, PPC uses it as a generator input contract. Generate valid baseline paths plus explicitly configured deviations such as delay, rework, skipped activity, exception handling or control failure. Record whether each path is expected, valid alternate or intentional deviation.
