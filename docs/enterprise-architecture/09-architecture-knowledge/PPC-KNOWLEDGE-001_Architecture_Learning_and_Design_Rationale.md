# PPC-KNOWLEDGE-001 — Architecture Learning and Design Rationale

| Control | Value |
|---|---|
| ID / status | PPC-KNOWLEDGE-001 / explanatory draft, 0.1.0, 2026-11-25 |
| Authority | [ARCH-000](../00-master-index/PPC-ARCH-000_Master_Architecture_Index_and_Authority_Baseline.md) for package scope; [PPC-REG-001](../../PPC-REG-001_Architecture_Decision_Register.md) for existing decisions |
| Contract | Source discussion and approved records → traceable rationale, alternatives and unresolved questions |

## 1. What this companion records

This file explains why the proposed contracts separate authorities. It is not an ADR, an implementation report or proof of qualification. The [discussion register](../registers/PPC-Discussion-Decision-Traceability.md) and [source locators](../registers/PPC-Discussion-Source-Locators.csv) identify the original exchanges; a topic locator does not prove that every mathematical example or attachment has been transferred. Preserve the original PPC-000–019 and ADR-001–039 baseline. Owner words, approval and dates belong in an ADR when a candidate becomes a decision. A `RationaleRecord` has source exchange and line, topic, affected spec section, alternative, standing (`PROPOSAL|OWNER_DIRECTION|RECORDED_ADR`), evidence locator, open question and disposition. Its lifecycle is `LOCATED → INTERPRETED → REVIEWED → DISPOSITIONED`; an unreviewed record cannot be described as decided. Replay of the record uses the original line and the document revision that interpreted it. Access to a restricted original asset never follows from a public locator.

## 2. First-principles rationale

**One world, many records.** One physical receipt can produce a logistics ticket, assay, trade update and invoice on different clocks. Source applications must retain independent, imperfect records, or PPC cannot test reconciliation and decision-time knowledge. The world is generation and evaluation truth, not an integration shortcut. WORLD-001/002 and INT-001 own the executable contracts.

**Meaning, projection and calculation.** EPM and future approved process packages define meaning. A graph projects typed relationships for traversal. Engineering and governed analytical tools compute quantities. If a graph path is described as a margin loss, the user cannot inspect the equation or assumptions. INFO-001, GRAPH-001, DATA-001 and ANALYTICS-001 keep those roles visible.

**Historical knowledge is recipient-specific.** A source may record a correction at noon and release it to the planner at 13:00. At 12:45, the planner uses the last authorized 12:30 publication or returns unresolved. An inaccessible correction stays undisclosed. EVID-001 owns the query rule; a current database row cannot reconstruct that view without publication and access history.

**A branch preserves a decision comparison.** A counterfactual branch copies a declared checkpoint and changes one assumption. It must not overwrite the actual path, borrow sibling evidence or execute a real-world action. A difference between branch outputs is model evidence under its envelope, not automatically a causal claim about a real plant.

**A release is a consistent cut.** Independent latest tables can represent different source watermarks. A publication manifest must pin the set and disclose incomplete components. A broker's delivery guarantee cannot alone establish one business effect. INT-001 and DATA-001 give those claims separate tests.

## 3. Alternatives and evidence ledger

| Question | Recorded baseline | Proposal and missing evidence |
|---|---|---|
| Formal and applied graph | Jena/Fuseki and Neo4j Community, ADR-009/010 | Standing semantic server scope and Relate browser require measured needs and access tests |
| Event transport | Kafka with Dagster orchestration, ADR-015 | NATS JetStream comparison requires retry/replay and operations evidence |
| Analytical history | DuckLake, ADR-017 | Delta on R2 or coexistence requires writer, recovery and Databricks parity tests |
| Workspace | Dash, ADR-014 | Relate WASM or another frontend needs workflow and permission prototype |
| Optimization and agents | OR-Tools; LangGraph/Langfuse in PPC-011/012 | Pyomo/HiGHS, Pydantic AI and OpenTelemetry/Logfire need comparative evidence |
| Process authority | EPM dependency in ADR-033/035/038/039 | Generalized upstream process release is pending; owner must reconcile ADR-035 |

## 4. Worked check and unresolved coverage

For a `SYNTHETIC` tank, 1,000 + 200 − 150 = 1,050 bbl (`DERIVED`). If an integration retry produces 1,250 bbl, the defect is duplicate business effect even if each message was delivered according to broker policy. If a decision at 12:45 cites a correction released at 13:00, the defect is future evidence even if its record time was noon. These examples illustrate two distinct failure modes; [VERIFY-001](../07-scenarios-verification/PPC-VERIFY-001_Verification_and_Release_Qualification.md) owns their executable oracles.

GAP-002 remains open: T1–T145 have topic locators, but OT-01–12 and EA-01–09D have not received an item-by-item, attachment-checked disposition. Numerical source examples and supplied diagrams still need source checks. T22, T25, T63–65, T74–77, T123–126 and T136–142 support this companion. Do not mark the discussion exhaustive or a choice approved from this explanatory file.
