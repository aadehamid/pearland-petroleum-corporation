# PPC-009 --- Metadata, Governance, Quality, and Observability

> **Reconciliation Notice (2026-11-26):** This baseline document is preserved for historical continuity. Owner decisions `ADR-0047` (staging OpenMetadata and Grafana to `WP-7` after Slice 1 while retaining Great Expectations, OpenLineage manifests, and OTel tracing in Slice 1) and `ADR-0051` (`exe.dev` sizing and per-store backups) supersede immediate Slice 1 deployment of OpenMetadata and Grafana here. See `docs/enterprise-architecture/06-platform-operations/PPC-PLATFORM-001_Infrastructure_Security_and_Operations.md` and `docs/enterprise-architecture/independent-review/PPC-REVIEW-003_System_and_Decision_Register.md` for current authority.

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
