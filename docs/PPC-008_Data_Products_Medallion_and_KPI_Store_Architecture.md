# PPC-008 --- Data Products, Medallion, and KPI Store Architecture

**Purpose:** Define reusable data products, medallion layers,
measurement governance and KPI persistence.

PPC uses an **ASD-STE100-inspired** technical writing style and
consistent defined terminology.

## Medallion

**Raw:** preserved source evidence/replay.\
**Silver:** cleaned, standardized, conformed facts/dimensions.\
**Gold:** reusable integrated business logic and data products.\
**Consumption:** approved SQL/views/APIs consumed by users and
applications.

Foundational/derived data-product categories describe business purpose;
medallion describes processing maturity. They are related but not
identical.

## Foundational products

Trusted representations of core entities/events: Customer, Contract,
Trade, Position, Product Movement, Inventory, Market Price,
Product/Location masters.

## Derived products

Decision-ready products: Market & Pricing, Physical Movement &
Logistics, Asset & Reliability, Commercial Margin, Commercial Risk,
Forecast Performance.

## Event product

Event
ID/type/time/geography/severity/source/provenance/status/confidence,
affected entities and lifecycle.

## KPI Store

Stores official simulated KPI results and evaluation metadata, not every
operational metric or report calculation. Logical fields include KPI
ID/version, period/grain, dimensions, value/unit/currency, target,
thresholds, status, calculation version, source run, scenario,
provenance and quality status.

## Initial KPIs

Commercial: Gasoline Netback CPG, ULSD Netback CPG, Margin Capture %.\
Trading: Trading P&L, Optionality Capture.\
Logistics: OTIF, Logistics Cost/Gallon, Demurrage Cost.\
Refining: Refinery Utilization, Unplanned Capacity Loss, Yield Capture.\
Planning: Forecast Accuracy, Inventory Days of Cover.\
Risk: Margin-at-Risk, Position Exposure.

## Margin hierarchy

Market Opportunity → Theoretical Margin → Realized Margin → Margin
Capture % → Margin Leakage. Leakage decomposes into downtime, yield,
crude/product selection, freight, demurrage, inventory placement,
pricing, compliance, hedge performance and missed optionality.

## Consumption rule

Superset, Dash, APIs and agents consume approved semantic/consumption
interfaces. They do not redefine enterprise KPI logic.

## EPM-governed promotion and product mapping
PPC follows EPM measurement/KPI promotion rules and maps Gold/data products to authoritative EPM portfolio entries where they exist. KPI Store implements EPM-governed identity/lifecycle; semantic identity points to the KPI and compute occurs against governed metric/data-product views.
