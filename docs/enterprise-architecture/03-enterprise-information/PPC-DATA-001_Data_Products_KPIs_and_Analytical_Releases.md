# PPC-DATA-001 — Data Products, KPIs and Analytical Releases

Inspected PPC baseline: [`01027a84be5d453cbb4e2ea091e4884729918b15`](../registers/PPC-SOURCE-REGISTER.md). This commit is the original PPC source-inspection reference, not this draft's content revision or owner approval. Later linked specifications are read at the current branch revision.

| Control | Value |
|---|---|
| ID / status | PPC-DATA-001 / proposed draft for owner review |
| Version / date | 0.1.0-draft / 2026-11-25 |
| Authority | [PPC-008](../../PPC-008_Data_Products_Medallion_and_KPI_Store_Architecture.md), [PPC-017](../../PPC-017_EPM_Dependency_Semantic_Authority_and_Process_Conformance_Contract.md), [PPC-REG-003](../../PPC-REG-003_KPI_Metric_and_Data_Product_Register.md); ADR-013, 017, 018, 033, 034, 039 |
| Inputs / output | Pinned source extracts, identity and EPM releases → governed product and KPI release |

## 1. Product and calculation boundary

Domain owners publish products at a stated business grain. Raw preserves source bytes and native keys. Silver reconciles identity, units and time without hiding disagreement. Gold contains reusable domain facts. A KPI value uses an approved EPM definition and governed computation. A semantic URI supplies meaning, not arithmetic. Superset, graph, agents and user interfaces read approved consumption views. [PPC-013](../../PPC-013_Cloudflare_R2_Durability_and_Project_Storage_Standard.md) governs durable objects. DuckDB/DuckLake and a parallel Databricks implementation remain recorded baselines under ADR-017/018. Delta on R2 and Databricks's exact role, tier, entitlement and timing require owner reconciliation.

## 2. Typed contracts and lifecycle

`ProductContract`: `product_id`, owner, version, row grain, primary dimensions, branch policy, event and source times, provenance class, schema digest, source dependencies, access label, freshness bound, null policy and quality tests. `MeasureContract`: quantity ID, approved meaning/version, unit and basis, formula pointer, aggregation rule, missing-value policy and tolerance. `KPIContract`: approved EPM ID/version, owner, supplying product ID, objective, measure IDs, approved formula pointer, unit and basis, period/grain, target and threshold version. Formula authority remains the released EPM contract. `ValueRecord`: immutable value ID, `measure_id` and `kpi_id` where applicable, definition and threshold versions, branch, period, dimensions, numeric value or explicit unknown with `unknown_reason`, unit and unit basis or currency, calculation digest, input release, `provenance_class`, separate `threshold_status` and `quality_status`, and restatement-of ID, publication ID, published-at time and recipient/role-and-channel availability relation from [INFO-001 §3](PPC-INFO-001_Enterprise_Ontology_Identity_and_Time.md). Every material input and output value carries `OBSERVED`, `DERIVED`, `ESTIMATED`, `SYNTHETIC` or `SCENARIO_ASSUMPTION`.

`ReleaseManifest`: release ID, `PREPARING|VALIDATED|PUBLISHED|RETRACTED|REJECTED`, published-at time, recipient/role-and-channel availability relation, EPM release ID, world version, table snapshot IDs, per-source captured/durable/applied/published watermarks, `branch_id`, semantic and mapping digests, model version, reconciliation report, access scope and approval evidence. `PUBLISHED` is atomic at the manifest boundary.The release transitions `PREPARING → VALIDATED|REJECTED`, `VALIDATED → PUBLISHED|REJECTED`, and `PUBLISHED → RETRACTED`. `REJECTED` and `RETRACTED` are terminal; a corrected release gets a new ID. An incomplete watermark blocks validation and records the reason in the rejected candidate. Publication is recipient-specific for reads under [INFO-001 §3](PPC-INFO-001_Enterprise_Ontology_Identity_and_Time.md).  A table snapshot alone is not a business-consistent release. Late source data creates a later release and, when needed, a restated value. Historical values remain addressable.

## 3. Worked quantity and adverse cases

The following is separate `SYNTHETIC` integration retry fixture `INT-RETRY-01`, not the T125 tank oracle or a certified KPI. All volumes use one liquid at constant density on a common reference-volume basis. A tank starts at 1,000 bbl. A received 200 bbl and dispatched 150 bbl give a `DERIVED` closing balance of 1,050 bbl (`1,000 + 200 − 150`). A product cannot publish if dispatch is still captured but not applied: its release must report an incomplete watermark, not 1,200 bbl as final. A repeated 200 bbl receipt with the same source movement ID contributes zero additional barrels. A corrected dispatch of 160 bbl gives a new `DERIVED` balance of 1,040 bbl in a restatement; the earlier release stays reproducible.

For separate `SYNTHETIC` utilization illustration `UTIL-ILLUS-01` only, 80,000 bbl/day divided by 100,000 bbl/day is 0.8, or 80% (`DERIVED`). Both values must share unit basis, day length and branch. This number is not an official KPI until a released EPM definition, scope, numerator/denominator policy, threshold and approved product are pinned. A 23-hour local day cannot silently be treated as 24 elapsed hours. A model forecast is `ESTIMATED`; a hypothetical outage is `SCENARIO_ASSUMPTION`, even when both are displayed beside source facts.

## 4. Qualification and unresolved choices

Qualify grain uniqueness, units, null behavior, source-to-Gold reconciliation, formula parity with an independent reference, threshold status, role filtering, incomplete-release rejection, replay, restatement and cross-engine equivalence. Record row-level expected and observed values, manifests, code and EPM digests, tolerances and approval. No such execution is claimed here.

ADR-017 retains DuckLake until the owner decides whether Delta replaces or coexists with it. ADR-018 retains Databricks as a parallel lab; entitlement and feature compatibility remain unverified. Open choices include concurrent-writer protocol, business release frequency and threshold ownership. T94–102 and T120–121 in the [discussion register](../registers/PPC-Discussion-Decision-Traceability.md) motivate these contracts; the source locators preserve their proposed standing.

The [exchange register](../registers/PPC-Discussion-Decision-Traceability.md) routes T4–5, T50, T80–82, T85–87, T95–96, T98–102, T107–109, T120–121 to this draft. This is topic-level routing; GAP-002 item and original-asset checks remain open.
