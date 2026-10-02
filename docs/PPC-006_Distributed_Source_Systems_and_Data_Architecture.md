# PPC-006 --- Distributed Source Systems and Data Architecture

**Purpose:** Define where PPC data lives, why, and which system is
authoritative.

PPC uses an **ASD-STE100-inspired** technical writing style. PPC does
not claim formal ASD-STE100 compliance. Terms keep one defined meaning
across the documentation.

## Systems

**Twenty:** CRM account/contact/opportunity/relationship activity.\
**ERPNext:** finance, procurement, sales order, invoice, receivable,
payment.\
**PostgreSQL:** commercial contracts, trades, positions, hedges,
commitments.\
**MySQL:** nominations, shipments, loads, deliveries, movement
execution.\
**SQLite:** local refinery unit status, production snapshots, operator
and maintenance events.\
**APIs:** external observed world.\
**D1:** event/alert/recommendation/approval workflow state.\
**R2:** durable objects and replay.\
**DuckLake:** conformed analytical history and governed products.\
**Databricks:** enterprise-like parallel implementation.

## System-of-record examples

Customer relationship lifecycle → Twenty. Invoice/payment → ERPNext.
Trade → PostgreSQL. Shipment execution → MySQL. Refinery unit status →
SQLite. PADD inventory → EIA. Conformed Customer → DuckLake Silver.
Commercial Margin product → DuckLake Gold. Official KPI value → KPI
Store. Approval state → D1.

## Intentional differences

Postgres uses UTC; MySQL can use America/Chicago; SQLite uses local
refinery time. EIA may be weekly PADD grain; SQLite hourly unit grain;
MySQL shipment grain; Postgres trade grain; Gold daily product/location
grain. Update patterns include CDC, API, polling, micro-batch and object
arrival.

## Enterprise identity

Never assume source keys align. Build crosswalks for Party/Customer,
Product, Location, Contract and Asset. Preserve source identifiers and
enterprise identifiers.

## Medallion

R2 Raw preserves source evidence. Silver conforms identities, types,
time and business keys. Gold implements reusable derived products/KPI
inputs. Consumption exposes approved interfaces only.
