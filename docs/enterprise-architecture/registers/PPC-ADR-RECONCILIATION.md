# PPC ADR reconciliation

Reconciled disposition record, 2026-11-26. [PPC-REG-001](../../PPC-REG-001_Architecture_Decision_Register.md) (`ADR-001`–`039`) is preserved verbatim. New and amending owner decisions live in [docs/adr/README.md](../../adr/README.md) (`ADR-0040`–`0053`), citing saved owner answers in [2026-11-26-first-principles-grill.md](../../adr/answers/2026-11-26-first-principles-grill.md). See [PPC-REVIEW-003](../independent-review/PPC-REVIEW-003_System_and_Decision_Register.md) for full trade-offs and consequences.

| ADR | Baseline | Reconciled decision | Decision status |
|---|---|---|---|
| 007 | OpenMetadata catalog | Deferred to WP-7; lightweight GX + OpenLineage manifests run in Slice 1 ([ADR-0047](../../adr/0047-slice1-active-core-vs-staged-apps.md)) | **Decided** |
| 009 | Standing Jena/Fuseki | Amended: Git Turtle + `rdflib`/`pyshacl` → Neo4j Community runtime path; Fuseki optional offline ([ADR-0044](../../adr/0044-turtle-pyshacl-neo4j-serving-path.md)) | **Decided** |
| 014 | Plotly Dash decision app | Amended to two-stage UX: FastAPI + Dash in Slice 1; Relate WASM business explorer in Slice 1.5 ([ADR-0047](../../adr/0047-slice1-active-core-vs-staged-apps.md), [ADR-0052](../../adr/0052-two-stage-ux-dash-and-relate-wasm.md)) | **Decided** |
| 015 | Dagster and Kafka | Amended for Slice 1: Dagster + NATS JetStream on IT, Sparkplug B on OT; Kafka deferred ([ADR-0046](../../adr/0046-ot-it-integration-split-sparkplug-nats-outbox.md)) | **Decided** |
| 016 | Debezium CDC | Amended for Slice 1: transactional source outboxes on IT; Debezium deferred ([ADR-0046](../../adr/0046-ot-it-integration-split-sparkplug-nats-outbox.md)) | **Decided** |
| 017 | DuckDB/DuckLake | Amended: Delta Lake on Cloudflare R2 replaces DuckLake; DuckDB queries locally ([ADR-0045](../../adr/0045-delta-lake-on-r2-and-databricks-portability.md), T86) | **Decided** |
| 018 | Databricks parallel lab | Clarified: eventual target enterprise platform reading the same R2 Delta tables, staged post-Slice-1 ([ADR-0045](../../adr/0045-delta-lake-on-r2-and-databricks-portability.md), [ADR-0051](../../adr/0051-exe-dev-r2-databricks-hosting-and-recovery.md)) | **Decided** |
| 022, 023 | Twenty CRM, ERPNext | Preserved as staged O2C/Hurricane extensions; deferred from Slice 1/2 ([ADR-0047](../../adr/0047-slice1-active-core-vs-staged-apps.md)) | **Decided** |
| 035 | EPM process authority | Clarified: generalized `DS_Business_Process` derives from `kpi-store/1.2` in separate upstream step ([ADR-0042](../../adr/0042-provisional-adapters-for-upstream-repositories.md), [ADR-0044](../../adr/0044-turtle-pyshacl-neo4j-serving-path.md)) | **Decided** |
| PPC-011/012 | OR-Tools; LangGraph/Langfuse | Pyomo + HiGHS/IPOPT replaces OR-Tools; LangGraph + Pydantic tools + OTel/self-hosted Langfuse ([ADR-0048](../../adr/0048-pyomo-optimization-and-langgraph-pydantic-agents.md)) | **Decided** |

Of the 13 `CAN-*` topics in `ARCH-000 §7.2`, nine are fully closed by `ADR-0040`–`0053`, and four (`CAN-SCENARIO-ISOLATION`, `CAN-TEMPORAL-IDENTITY`, `CAN-QUANTIFIED-IMPACT`, `CAN-AGENT-AUTHORITY`) have reconciled normative contracts awaiting only WP-0 operational sign-off on identity-conflict steward assignment and numeric action-approval thresholds.
