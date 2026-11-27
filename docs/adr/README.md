# PPC Architecture Decision Records (ADR-0040 onward)

Baseline decisions `ADR-001` through `ADR-039` are preserved verbatim in [PPC-REG-001](../PPC-REG-001_Architecture_Decision_Register.md). Decisions recorded from the 2026-11-26 architecture reconciliation live here in sequential order, citing saved owner answers in [answers/2026-11-26-first-principles-grill.md](answers/2026-11-26-first-principles-grill.md) and owner-delegated stand-in rulings in [answers/2026-11-26-claude-fable-2-owner-standin.md](answers/2026-11-26-claude-fable-2-owner-standin.md).

| ADR | Title | Status | Date | Amends / clarifies |
|---|---|---|---|---|
| [ADR-0040](0040-staged-mechanistic-refinery-model-and-closed-flowsheet.md) | Staged mechanistic refinery physics on a closed Refinery A v1 flowsheet | Decided (amended by ADR-0054) | 2026-11-26 | Extends PPC-001, PPC-005 |
| [ADR-0041](0041-function-first-lean-core-enabling-stack.md) | Function-first lean core enabling stack aligned with sister repositories | Decided | 2026-11-26 | Extends PPC-002, PPC-015 |
| [ADR-0042](0042-provisional-adapters-for-upstream-repositories.md) | Provisional adapters for upstream repositories and exclusion of people graph from v1 | Decided | 2026-11-26 | Clarifies ADR-033, ADR-038 |
| [ADR-0043](0043-refinery-v1-unit-physics-and-hybrid-clock.md) | Refinery A v1 unit physics split and hybrid multi-rate simulation clock | Decided (extended by ADR-0056) | 2026-11-26 | Extends ADR-001, ADR-019 |
| [ADR-0044](0044-turtle-pyshacl-neo4j-serving-path.md) | Git Turtle and pyshacl to Neo4j runtime serving path with generalized DS_Business_Process lineage | Decided | 2026-11-26 | Amends ADR-009; clarifies ADR-035 |
| [ADR-0045](0045-delta-lake-on-r2-and-databricks-portability.md) | Delta Lake on Cloudflare R2 with DuckDB local compute and Databricks target portability | Decided (clarified by ADR-0055) | 2026-11-26 | Amends ADR-017; clarifies ADR-018 |
| [ADR-0046](0046-ot-it-integration-split-sparkplug-nats-outbox.md) | OT/IT integration split with Sparkplug B on OT and outbox plus NATS JetStream on IT | Decided | 2026-11-26 | Amends ADR-015, ADR-016 |
| [ADR-0047](0047-slice1-active-core-vs-staged-apps.md) | Slice 1 active source and UI core versus staged enterprise applications | Decided | 2026-11-26 | Stages ADR-007, ADR-014, ADR-022, ADR-023 |
| [ADR-0048](0048-pyomo-optimization-and-langgraph-pydantic-agents.md) | Pyomo with HiGHS/IPOPT for optimization and LangGraph with Pydantic tools and OpenTelemetry/Langfuse for agents | Decided (staged by ADR-0055, ADR-0056) | 2026-11-26 | Amends PPC-011, PPC-012 |
| [ADR-0049](0049-v1-business-use-cases.md) | Complete v1 business use-case catalog (UC-1 through UC-6) | Decided | 2026-11-26 | Extends PPC-001, SCENARIO-001 |
| [ADR-0050](0050-formal-verification-and-benchmark-stack.md) | Formal verification and empirical validation stack | Decided (extended by ADR-0056) | 2026-11-26 | Extends VERIFY-001, ENG-001 |
| [ADR-0051](0051-exe-dev-r2-databricks-hosting-and-recovery.md) | exe.dev, Cloudflare R2, and staged Databricks hosting topology with RPO/RTO targets | Decided (amended by ADR-0055) | 2026-11-26 | Clarifies ADR-003, ADR-004, ADR-010, ADR-018 |
| [ADR-0052](0052-two-stage-ux-dash-and-relate-wasm.md) | Two-stage UX contract with FastAPI/Dash in Slice 1 and Relate WASM in Slice 1.5 | Decided | 2026-11-26 | Amends ADR-014; extends ADR-0047 |
| [ADR-0053](0053-legacy-data-quarantine-and-world-export-bundle.md) | Legacy synthetic data quarantine and WorldExportBundle cross-repository contract | Decided | 2026-11-26 | Extends ADR-001, ADR-028, PPC-015 |
| [ADR-0054](0054-refinery-a-flowsheet-closure-option-a-and-design-basis.md) | Refinery A v1 flowsheet closure (Option A) and 180,000 bbl/day nominal design basis | Decided (owner stand-in) | 2026-11-26 | Amends ADR-0040 |
| [ADR-0055](0055-slice1-hosting-observability-postgres-workflow-and-databricks-sync.md) | Slice 1 12 GB lightweight OTel topology, PostgreSQL workflow state (no D1), and Databricks Free Edition synced copy | Decided (owner stand-in) | 2026-11-26 | Amends ADR-0045, ADR-0048, ADR-0051 |
| [ADR-0056](0056-identity-steward-action-thresholds-and-refinery-a-parameters.md) | `IDENTITY_STEWARD` role, numeric action-authority thresholds (`PROHIBITED`), and Refinery A v1 parameter ranges | Decided (owner stand-in) | 2026-11-26 | Amends ADR-0043, ADR-0048, ADR-0050 |
| [ADR-0058](0058-shared-relate-project-memory-for-all-agents.md) | Shared Relate project memory for all coding agents | Decided | 2026-11-27 | None |
