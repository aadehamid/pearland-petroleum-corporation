# PPC-REG-001 --- Architecture Decision Register

**Purpose:** Preserve why PPC architecture choices were made.

  --------------------------------------------------------------------------
  ADR                     Decision                Rationale / consequence
  ----------------------- ----------------------- --------------------------
  001                     Canonical synthetic     One coherent world; source
                          world precedes source   fragmentation is simulated
                          materialization         deliberately

  002                     Public and synthetic    Prevent synthetic facts
                          provenance is explicit  from masquerading as
                                                  public evidence

  003                     One R2 bucket per       Durable, simple project
                          project                 boundary

  004                     R2 is object store, not Preserve
                          universal system of     transactional/analytical
                          record                  ownership

  005                     AML is authoritative    Extensible,
                          data-model-as-code      machine-readable,
                                                  visualizable structure

  006                     Azimutt is visual       Human exploration without
                          modeler                 owning model meaning

  007                     OpenMetadata is         Central context for
                          catalog/governance      assets, owners, lineage,
                          plane                   quality

  008                     RDF and LPG are         Meaning and operational
                          separate roles          traversal optimize
                                                  different problems

  009                     Jena/Fuseki for formal  Open RDF/OWL/SHACL/SPARQL
                          semantics               stack

  010                     Neo4j Community for     Mature property-graph
                          applied graph           traversal and ecosystem

  011                     GX executes DQ;         Avoid quality metadata
                          OpenMetadata            silo
                          contextualizes          

  012                     OpenLineage             Portable job/run/dataset
                          standardizes run        events
                          lineage                 

  013                     Superset does not own   Avoid recreating
                          KPI logic               report-specific metric
                                                  divergence

  014                     Dash is decision        Events/scenarios/actions
                          application             require application UX,
                                                  not only BI

  015                     Dagster orchestrates;   Clear separation of
                          Kafka transports        workflow and event bus

  016                     Debezium handles        Realistic change capture
                          Postgres/MySQL CDC      

  017                     DuckDB                  Separate compute from
                          computes/federates;     durable analytical model
                          DuckLake stores history 

  018                     Databricks is           Demonstrate architecture
                          enterprise-like         portability
                          parallel implementation 

  019                     Specialized models, not Reliability, testability
                          LLMs, calculate         and explainability
                          analytics               

  020                     Agents cannot bypass    Human agency and
                          policy/approval         operational safety

  021                     Defer                   Add only when requirements
                          feature/vector/policy   justify complexity
                          infrastructure          

  022                     Twenty components used  User requirement for CRM
                          must be open-source     

  023                     ERPNext selected for    Open-source ERP with
                          ERP                     useful O2C/finance
                                                  coverage

  024                     Controlled source       Make integration/semantic
                          imperfections are       reconciliation realistic
                          intentional             

  025                     STE-inspired writing,   Clarity without forcing
                          not claimed compliance  aerospace-style
                                                  constraints
  --------------------------------------------------------------------------

## Additional decisions from the ECE dependency review
| ADR | Decision | Rationale / consequence |
|---|---|---|
| ADR-026 | Adopt ECE evidence and decision-provenance contracts | Avoid duplicate provenance semantics |
| ADR-027 | Separate data provenance from epistemic status | Origin is different from claim support |
| ADR-028 | Isolate canonical truth from agent-visible evidence | Prevent evaluation leakage |
| ADR-029 | Use canonical decision dossiers for material decisions | Preserve alternatives, authority, rationale, outcome and uncertainty |
| ADR-030 | Generate structured and unstructured evidence | Enterprise context is distributed |
| ADR-031 | Make temporal correctness a hard evaluation requirement | Future/superseded information cannot explain earlier decisions |
| ADR-032 | Evaluate claim-level provenance and unsupported claims | Correct calculations alone do not prove trustworthy reasoning |

## Additional decisions from the EPM dependency review
| ADR | Decision | Rationale / consequence |
|---|---|---|
| ADR-033 | Consume a versioned EPM dependency bundle, not only ontology | Keep process/KPI/data-product authority aligned |
| ADR-034 | Adopt `Meaning does not compute` | Prevent semantic stores, BI and LLMs from becoming calculation authority |
| ADR-035 | EPM process authority constrains PPC baseline generation | Designed and executed processes become comparable |
| ADR-036 | Add process-conformance intelligence | Connect process execution to performance |
| ADR-037 | Inherit EPM competency questions and add instance tests | Make semantic integration executable |
| ADR-038 | Record upstream EPM artifact maturity/authority | Prevent silent promotion of drafts |
| ADR-039 | Map PPC data products/KPIs to EPM definitions where available | Avoid parallel performance architecture |
