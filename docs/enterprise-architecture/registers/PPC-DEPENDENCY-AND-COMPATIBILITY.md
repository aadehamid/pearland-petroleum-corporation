# PPC dependency and compatibility register

Reconciled gate list, 2026-11-26. [ARCH-000 §8](../00-master-index/PPC-ARCH-000_Master_Architecture_Index_and_Authority_Baseline.md#8-versioned-dependency-and-scenario-manifest-policy) defines the top-level release manifest. Under [ADR-0042](../../adr/0042-provisional-adapters-for-upstream-repositories.md), PPC decouples its schedule from pending upstream releases using versioned provisional adapters pinned to verified commits (never labeling pending drafts as approved). Under [ADR-0053](../../adr/0053-legacy-data-quarantine-and-world-export-bundle.md), PPC publishes `WorldExportBundle` so sister repositories consume one coherent Refinery A world.

| Dependency | Verified local commit (2026-11-26) | Maturity & PPC adapter rule | Compatibility proof still needed (`WP-0`–`WP-8B`) |
|---|---|---|---|
| `enterprise-performance-model` (EPM) | `main` @ `511a9e8d` | Git Turtle + `pyshacl` + Neo4j runtime; DuckDB & Databricks demos exist; provisional adapter pinned | IRI, SHACL, tall KPI formula, and DuckDB/Databricks parity (`WP-3`, `WP-8A`, `WP-8B`) |
| `DS_Business_Process` (`downstream_oil_and_gas_ontology_release`) | Local `share/epm-1.0` @ `2b3f02e`; `ds-business-process/1.0` separate upstream track | **Pending upstream release** (derived from `kpi-store/1.2`, `ADR-0044`); bindings stay explicitly pending | Released digest, migration, and conformance tests (`WP-7`) |
| `scada_harmonization` (ICE) | `main` @ `30c20c3` (PR #68); `cursor/handoff-close-68` @ `65ffe10` | Phase 1 L0 Parquet + 1 s stream + Plane 3 split merged; mapping YAML unwritten; provisional adapter pinned | Tag, unit, quality, Sparkplug B, and identity fixture (`WP-2`, `WP-8B`) |
| `Engineering_Drawing_to_Graph` (EDI) | `main` @ `12a4a6a` (PR #56) | Bounded structured DEXPI slice documented; flat extraction pending; provisional adapter pinned | Revision, directed topology, and recovery fixture (`WP-2`, `WP-8B`) |
| `enterprise-context-engineering` (ECE) | `main` @ `750b398` (PR #12) | Architecture docs present; reusable schema package pending; provisional adapter pinned | Reader-as-of `INFO-001 §3` and claim-provenance contract parity (`WP-3`, `WP-8B`) |
| `enterprise-people-graph` | `teaching/ontology-101` @ `eb2fdb7` | **Excluded from PPC v1** ([ADR-0042](../../adr/0042-provisional-adapters-for-upstream-repositories.md)) | None for v1 |
| Public ontologies (`PPC-019`) | Discovery links only | Candidate references; no unapproved imports | License, release, dependency closure, and mapping review |
| EIA / NOAA / EPA / PHMSA feeds | External APIs | Public observations with source and vintage | Vintage pinning, quality, license, and fictional exposure separation (`WP-1`) |
| PPC world / source / Delta / Neo4j | Reconciled (`ADR-0040`–`0056`) | Implementation-ready specs; runtime **planned** | Quint/Z3/analytical oracles, restore drill, and golden slices (`WP-1`–`WP-8B`) |

Fail a qualified release if a required package has no pinned identity or the tested combination differs from the activation manifest.
