# PPC ADR reconciliation

Draft disposition record, 2026-11-25. [PPC-REG-001](../../PPC-REG-001_Architecture_Decision_Register.md) remains the decision authority. [ARCH-000 §7](../00-master-index/PPC-ARCH-000_Master_Architecture_Index_and_Authority_Baseline.md#7-existing-adr-baseline-and-proposed-reconciliation) lists all 39 IDs once: 26 retain, 6 extend, 7 reassess. Those are proposed review dispositions, not amendments.

| ADR | Baseline | Proposed question | Decision status |
|---|---|---|---|
| 007 | OpenMetadata catalog | First-slice scope | Open |
| 009 | Jena/Fuseki | Standing server need | Open |
| 014 | Dash decision app | Relate/browser integration | Open |
| 015 | Dagster and Kafka | NATS versus Kafka | Open |
| 016 | Debezium CDC | Compare Python-native and source-native capture before any replacement | Open |
| 017 | DuckDB/DuckLake | Delta on R2 or coexistence | Open |
| 018 | Databricks parallel implementation | Role, entitlement and timing | Open |
| 035 | EPM process authority | Clarify generalized process release boundary without changing the recorded decision | Open |

The Extend dispositions are ADR-005, 006, 011, 026, 033 and 035. ARCH-000 §7.2 lists all 13 unapproved CAN-* candidates; each needs an owner disposition before any approval claim. PPC-011 names OR-Tools; PPC-012 names LangGraph/Langfuse. Pyomo/HiGHS, Pydantic AI and OpenTelemetry/Logfire are later candidates. The separate generalized process release may require clarification of ADR-035; no new ADR number or approval is assigned here. Owner wording and decision time must be recorded before changing the baseline.
