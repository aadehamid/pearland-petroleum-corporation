# PPC-009 --- Metadata, Governance, Quality, and Observability

**Purpose:** Define trust, ownership, lineage, quality and incident
context.

PPC uses an **ASD-STE100-inspired** technical writing style and
consistent defined terminology.

## OpenMetadata

Acts as catalog/governance control plane: glossary, domains,
ownership/stewardship, classifications, data products/contracts,
technical assets, lineage, quality results, certification and discovery.

## Great Expectations

Executes explicit quality rules. Rules include schema/null/uniqueness
plus PPC semantic rules: inventory conservation, capacity, accounting
reconciliation, valid provenance and cross-system referential
resolution.

## OpenLineage

Publishes job/run/dataset events such as START/COMPLETE/FAIL. Dagster
and other processing jobs emit lineage that OpenMetadata can
contextualize.

## Three anomaly classes

**Technical:** pipeline/job failed.\
**Data:** null/distribution/freshness rule failed.\
**Business:** data is technically valid but business behavior is
abnormal, such as shipments dropping while orders remain normal.
Performance Intelligence detects business anomalies.

## Data-product health

Combine freshness, quality, completeness, pipeline health, lineage
health and contract compliance. A degraded product can propagate a
`quality_status` to KPI outputs.

## Impact example

Commercial Margin product becomes stale → OpenMetadata lineage
identifies dependent KPI assets → Neo4j maps business/decision
dependencies → automation marks KPI stale, blocks high-risk automated
pricing, opens incident and notifies owner.

## Governance

Every concept/product/KPI has owner, steward, lifecycle state, effective
dates and change process. Historical definitions and KPI values are
retained when restated.
