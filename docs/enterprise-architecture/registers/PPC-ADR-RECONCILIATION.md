# PPC ADR reconciliation

Draft disposition record, 2026-11-25. [PPC-REG-001](../../PPC-REG-001_Architecture_Decision_Register.md) remains the decision authority. [ARCH-000 §7](../00-master-index/PPC-ARCH-000_Master_Architecture_Index_and_Authority_Baseline.md#7-existing-adr-baseline-and-proposed-reconciliation) lists all 39 IDs once: 26 retain, 7 extend, 6 reassess. Those are proposed review dispositions, not amendments.

| ADR | Baseline | Proposed question | Decision status |
|---|---|---|---|
| 007 | OpenMetadata catalog | First-slice scope | Open |
| 009 | Jena/Fuseki | Standing server need | Open |
| 014 | Dash decision app | Relate/browser integration | Open |
| 015 | Dagster and Kafka | NATS versus Kafka | Open |
| 017 | DuckDB/DuckLake | Delta on R2 or coexistence | Open |
| 018 | Databricks parallel lab | Role, entitlement and timing | Open |

PPC-011 names OR-Tools; PPC-012 names LangGraph/Langfuse. Pyomo/HiGHS, Pydantic AI and OpenTelemetry/Logfire are later candidates. The separate generalized process release may require clarification of ADR-035; no new ADR number or approval is assigned here. Owner wording and decision time must be recorded before changing the baseline.
