# PPC-KNOWLEDGE-001 — Architecture Learning and Design Rationale

Inspected PPC baseline: [`01027a84be5d453cbb4e2ea091e4884729918b15`](../registers/PPC-SOURCE-REGISTER.md). This commit is the original PPC source-inspection reference, not this draft's content revision or owner approval. Later linked specifications are read at the current branch revision.

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

**Historical knowledge is recipient-specific.** [INFO-001 §3](../03-enterprise-information/PPC-INFO-001_Enterprise_Ontology_Identity_and_Time.md) owns the reader-as-of query rule; a current database row cannot reconstruct that view without publication and access history.

**A branch preserves a decision comparison.** A counterfactual branch copies a declared checkpoint and changes one assumption. It must not overwrite the actual path, borrow sibling evidence or execute a real-world action. A difference between branch outputs is model evidence under its envelope, not automatically a causal claim about a real plant.

**A release is a consistent cut.** Independent latest tables can represent different source watermarks. A publication manifest must pin the set and disclose incomplete components. A broker's delivery guarantee cannot alone establish one business effect. INT-001 and DATA-001 give those claims separate tests.

## 3. Alternatives and reconciled decision ledger

The full system-and-decision register, trade-offs, consequences, and cross-boundary walkthroughs live in [PPC-REVIEW-003](../independent-review/PPC-REVIEW-003_System_and_Decision_Register.md). Decisions from the 2026-11-26 architecture reconciliation are recorded in [ADR-0040](../../adr/0040-staged-mechanistic-refinery-model-and-closed-flowsheet.md) through [ADR-0056](../../adr/0056-identity-steward-action-thresholds-and-refinery-a-parameters.md):

| Question | Recorded baseline | Reconciled disposition (`ADR-0040`–`0056`) |
|---|---|---|
| Catalog | OpenMetadata, ADR-007 | Staged to WP-7; lightweight GX/OpenLineage manifests in Slice 1 (`ADR-0047`) |
| Formal and applied graph | Jena/Fuseki and Neo4j Community, ADR-009/010 | Git Turtle + `pyshacl` → Neo4j Community on `exe.dev`; Fuseki optional offline (`ADR-0044`, `0051`) |
| Source capture & IT transport | Debezium CDC + Kafka + Dagster, ADR-015/016 | Transactional outbox + NATS JetStream + Dagster on IT; OPC UA + Sparkplug B on OT; Kafka/Debezium deferred (`ADR-0046`) |
| Analytical storage & Databricks | DuckLake + Databricks Free, ADR-017/018 | Delta Lake on Cloudflare R2 + DuckDB read-only; Dagster on `exe.dev` syncs pinned Delta copies to Databricks Free Edition in `WP-8A` (`ADR-0045`, `0051`, `0055`, T86) |
| Workspace & Relate WASM | Dash, ADR-014 | FastAPI + Dash in Slice 1; Relate WASM business Context Explorer in Slice 1.5 (`ADR-0047`, `0052`, T111) |
| Optimization, agents & workflow state | OR-Tools; LangGraph/Langfuse/D1 in PPC-011/012 | Pyomo + HiGHS/IPOPT; LangGraph + Pydantic-typed tools + PostgreSQL workflow state (no D1 in v1) + lightweight OTel Collector to R2 `telemetry/otel/` in Slice 1, staging ClickHouse-backed Langfuse v3 to `WP-7` (`ADR-0048`, `0055`, `0056`) |
| Formal verification | Open in T26/T74 | Quint + Python/Z3/Hypothesis + independent engineering benchmarks (`ADR-0050`, `0056`, `PPC-REVIEW-004`) |
| Process authority | EPM dependency in ADR-033/035/038/039 | Generalized `DS_Business_Process` derived from `kpi-store/1.2` in separate upstream track; commit-pinned provisional adapters (`ADR-0042`, `0044`) |
| Legacy data & sister repos | Unowned in `ef4eb08` | Non-destructive manifest quarantine as `LEGACY_PRE_WORLD_MODEL`; certified `WorldExportBundle` v1 in `WP-8B` for ICE/EDI/EPM/ECE (`ADR-0053`) |

## 4. Worked check and unresolved coverage

For separate `SYNTHETIC` integration retry fixture `INT-RETRY-01` on one liquid at constant density and a common reference-volume basis, 1,000 + 200 − 150 = 1,050 bbl (`DERIVED`). If a duplicate 200 bbl receipt produces 1,250 bbl, the defect is duplicate business effect even if each message was delivered according to broker policy. For future-evidence checks, use [INFO-001 §3](../03-enterprise-information/PPC-INFO-001_Enterprise_Ontology_Identity_and_Time.md). These examples illustrate two distinct failure modes. [DATA-001 §3](../03-enterprise-information/PPC-DATA-001_Data_Products_KPIs_and_Analytical_Releases.md) defines the `INT-RETRY-01` arithmetic and expected duplicate result. [VERIFY-001 §2](../07-scenarios-verification/PPC-VERIFY-001_Verification_and_Release_Qualification.md) requires independent execution evidence; its T125 tank fixture is separate.

`GAP-002` Markdown transcript reconciliation is complete in [PPC-REVIEW-001 §5](../independent-review/PPC-REVIEW-001_Document_Coverage_and_Transcript_Audit.md#5-audit-of-raw-chatgpt-transcript-t1t145-versus-ef4eb08-ppc-documents-closing-gap-002) and [ADR-0040](../../adr/0040-staged-mechanistic-refinery-model-and-closed-flowsheet.md)–[ADR-0056](../../adr/0056-identity-steward-action-thresholds-and-refinery-a-parameters.md). Five unexported external attachments and screenshots remain unavailable and excluded from normative claims. T22, T25, T63–65, T74–77, T123–126 and T136–142 support this companion.

The [exchange register](../registers/PPC-Discussion-Decision-Traceability.md) routes T22, T25, T28–30, T46–47, T63–65, T74, T76–77, T123–124, T126, T136–142 to this draft. `GAP-002` Markdown audit is closed in [PPC-REVIEW-001 §5](../independent-review/PPC-REVIEW-001_Document_Coverage_and_Transcript_Audit.md#5-audit-of-raw-chatgpt-transcript-t1t145-versus-ef4eb08-ppc-documents-closing-gap-002).

[INFO-001 §3](../03-enterprise-information/PPC-INFO-001_Enterprise_Ontology_Identity_and_Time.md) owns the complete P0/P1/P2 publication rows, source-record times, recipient availability and reader-as-of rule used by this draft.
