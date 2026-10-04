# PPC-019 — Public Ontology Reuse and Implementation Guide

| Document control | Value |
| --- | --- |
| Version | 0.1 |
| Date | 2026-10-03 |
| Status | Proposed recommendations for review; no new ontology adoption is asserted |
| Company | Pearland Petroleum Corporation (PPC), fictional |
| Proposed repository path | `docs/PPC-019_Public_Ontology_Reuse_and_Implementation_Guide.md` |
| Purpose | List public ontologies PPC can leverage, explain their intended use, and define a practical route from reference selection to validated implementation |
| Authority | EPM governs downstream meaning; ECE governs generic evidence/context patterns; PPC consumes and instantiates their versioned contracts |

## 1. Recommendation and documentation gap

Create this guide as a separate document. Keep PPC-010 as the ontology, graph and policy architecture. Keep PPC-017 as the EPM dependency and semantic authority contract.

The repository inspection found architecture guidance but no dedicated public-ontology inventory with domain fit, reuse scope, selection status, mapping guidance and acceptance records. PPC-003 lists core concepts. PPC-010 separates formal meaning from operational graph traversal. PPC-016 defines evidence and decision provenance. PPC-017 governs upstream dependencies. These documents establish the boundaries for this guide; they do not replace its detailed inventory.

**Recommended direction:** evaluate Industrial Ontologies Foundry (IOF) Core as a common industrial foundation. Use small, selected domain modules and supporting vocabularies. Preserve EPM identifiers and definitions. Do not import every candidate into one ontology.

No single verified public ontology covers PPC's complete downstream enterprise, business architecture, commercial operations, KPIs, evidence and decisions. This guide recommends a modular baseline.

Public availability does not establish reuse permission for an exact artifact. Source pages were inspected during research, but immutable release pins, dependency closure, license compatibility and term-by-term mapping remain implementation tasks. All proposed PPC uses below are project recommendations, not claims that the source ontologies already implement PPC behavior.

## 2. Existing architecture and reuse boundaries

| Authority or component | Responsibility |
| --- | --- |
| Public ontology publishers | Define external reference concepts and their published semantics |
| Enterprise Performance Model (EPM) | Select or map downstream references; own enterprise business, process, metric/KPI and data-product meaning |
| Enterprise Context Engineering (ECE) | Define reusable evidence, provenance, temporal context, uncertainty and decision-context patterns |
| PPC | Create fictional instances, source mappings, scenarios, calculations and explicitly scoped extensions |
| Apache Jena/Fuseki | Store/query formal semantics and approved RDF instances; support the selected validation workflow |
| Neo4j | Project operational relationships and evidence available to the consuming application or agent |
| Analytical models and governed compute | Calculate production, forecasts, exposure, optimization results and KPI values |
| Policy implementation | Enforce permissions, approval thresholds and allowed actions |

EPM adoption of IOF/BFO is a proposed architectural choice. Assess its compatibility with the current EPM model before changing subclass relationships. A candidate foundation must not silently recast approved enterprise concepts.

PPC retains the rule **Meaning does not compute**. An ontology can describe a forecast, input, unit or KPI. It does not supply the validated forecasting algorithm or governed netback formula.

PPC also retains two independent axes:

- Data provenance: `OBSERVED`, `DERIVED`, `ESTIMATED`, `SYNTHETIC`, `SCENARIO_ASSUMPTION`.
- Epistemic status: `EVIDENCE`, `INFERENCE`, `CONTRADICTION`, `UNKNOWN`.

Neither an ontology type nor a provenance chain establishes that a claim is true or available at decision time.

## 3. Public ontology shortlist

“Priority” means recommended assessment order. It does not mean approval to import.

| ID | Ontology or vocabulary | What it provides | Proposed PPC use | Priority and limit |
| --- | --- | --- | --- | --- |
| ONT-001 | [IOF Core](https://spec.industrialontologies.org/portal/) | Common industrial concepts built on Basic Formal Ontology (BFO) | Shared meaning for industrial assets, materials, activities and related operational information | First: candidate industrial foundation; not a complete downstream model |
| ONT-002 | [IOF Maintenance](https://spec.industrialontologies.org/portal/release/202603/) | Failure events, operating/failed states, maintenance activities and work-order records | Asset & Reliability, unit outages, repair activities and recovery evidence | First: selected module, conditional on foundation compatibility |
| ONT-003 | [IOF Supply Chain](https://spec.industrialontologies.org/portal/release/202603/supplychain/SupplyChainOntology.html) | Generic supply-chain structure, inventory and related concepts | Terminal inventory, supply-network nodes, and logistics relationships | First: extend for petroleum nominations, custody and movements |
| ONT-004 | [Industrial Data Ontology (IDO) and POSC Caesar Reference Data Library](https://rds.posccaesar.org/) | Industrial asset/process semantics and OWL 2 reference data, including equipment and units | Refinery equipment classification, engineering properties and equipment functions | Specialist: select terms or map references; evaluate separately from IOF |
| ONT-005 | [OntoCAPE](https://publications.rwth-aachen.de/record/153233) | Chemical process engineering concepts, including materials, reactions and unit operations | Feedstocks, process streams, refinery processing and intermediate products | Specialist: obtain and validate artifacts; current download and license remain open |
| ONT-006 | [QUDT](https://www.qudt.org/) | Quantities, units, dimensions and quantity values | Volume, mass, flow, pressure and dimensional checks on measurements | First: small unit/quantity subset; petroleum measurement basis still needs explicit modeling |
| ONT-007 | [SOSA/SSN](https://www.w3.org/TR/vocab-ssn/) | Observations, sensors, observable properties, samples and actuators | Tank readings, process measurements and public weather observations | First: observation subset; observations do not automatically imply causal impacts |
| ONT-008 | [GeoSPARQL](https://www.ogc.org/standards/geosparql/) | Geographic features, geometry and spatial queries | Asset locations, pipeline routes and hurricane-footprint intersections | First: scenario geography; exposure/damage estimation remains analytical work |
| ONT-009 | [PROV-O](https://www.w3.org/TR/prov-o/) | Entities, activities, agents and provenance relationships | Source capture, generator runs, transformations, model runs and derived outputs | First: already named in PPC; align through ECE |
| ONT-010 | [OWL-Time](https://www.w3.org/TR/owl-time/) | Instants, intervals, durations and ordering relationships | Outage windows, delivery windows, policy validity and decision-time context | First: minimal subset through ECE; pin a specific published version |
| ONT-011 | [SKOS](https://www.w3.org/TR/skos-reference/) | Concept schemes, controlled labels, hierarchical relations and vocabulary mappings | Product grades, modes, status codes and reviewed vocabulary crosswalks | First: already named in PPC; distinguish vocabulary mapping from logical equivalence |
| ONT-012 | [W3C Organization Ontology (ORG)](https://www.w3.org/TR/vocab-org/) | Organizations, units, posts, roles, memberships and sites | PPC departments, operational roles, ownership and approval-role context | Supporting: membership/role facts do not themselves grant authority |
| ONT-013 | [Financial Industry Business Ontology (FIBO)](https://spec.edmcouncil.org/fibo/) | Financial business concepts covering entities, obligations, instruments and market information | Counterparties, selected contractual obligations, hedge instruments and financial market data | Later: select relevant modules; not a complete physical petroleum trading model |
| ONT-014 | [Web Annotation Data Model](https://www.w3.org/TR/annotation-model/) | Annotation bodies and targets, including selectors for parts of resources | Link a claim or reviewer comment to a precise passage in an immutable evidence artifact | Supporting: use with ECE evidence locators; does not assess truth |
| ONT-015 | [Performance Summary Display Ontology (PSDO)](https://www.ebi.ac.uk/ols4/ontologies/psdo) | Performance-summary and feedback-display concepts, as assessed in the People Graph reference register | Optional evaluation of scorecard explanations and feedback displays | Later: supporting display semantics only; release/license questions remain open |

IOF's public portal identifies an MIT license and publishes release browsers. This is useful initial license evidence, not a substitute for checking the selected files and imported dependencies. POSC Caesar provides public OWL reference data; do not equate access to that data with unrestricted access to ISO publications. The IDO naming and standards lineage has evolved, so record the exact selected ontology IRI and version rather than referring only to “ISO 15926.”

The RWTH publication establishes OntoCAPE's research provenance. Its historical homepage was not accessible through the research tool. Treat artifact acquisition, maintenance assessment and licensing as unresolved.

### Additional candidates outside the initial shortlist

- [O3PO](https://github.com/BDI-UFRGS/O3POntology) describes offshore petroleum production plants and is BFO-aligned. It can inform equipment modeling, but its upstream/offshore scope is a weaker fit than the candidates above for PPC's downstream baseline.
- SEPIO can be evaluated through ECE for a bounded claim/evidence pilot. The People Graph register retains its cross-domain suitability as open. Do not adopt it as PPC's complete decision-dossier ontology.
- ODRL can describe policy expressions in a later assessment. Runtime access control and approval enforcement remain application responsibilities.

## 4. Detailed reuse guidance

### 4.1 Common industrial structure — IOF Core

Start with a small EPM concept set: Asset, Refinery Unit, Material/Product, Production Activity and relevant specifications or records. Read candidate definitions and axioms. Decide whether each EPM concept is a specialization, a related reference or an incompatible concept.

Keep distinct:

- A hydrocracker unit as a physical asset.
- Hydrocracking as an executed process.
- A design or operating specification as information.
- A refinery unit's current operating state.

Do not map all four to a generic “Process” node. They participate in different relationships and have different identity and time requirements.

### 4.2 Reliability — IOF Maintenance

Model failure events, failed/degraded states, maintenance work-order records and executed maintenance activities as separate objects. Connect them to affected equipment and dated evidence.

For the hurricane scenario, represent a synthetic outage event and its operating-state interval. Connect a repair work order and subsequent maintenance activity. Compute capacity loss from governed capacity, duration and operating data. The failure event alone does not quantify lost production.

### 4.3 Inventory and logistics — IOF Supply Chain

Use selected supply-chain concepts to structure inventory and network relationships. Extend EPM for nomination, shipment, delivery, custody transfer and transport mode where the reference does not meet the approved definition.

Distinguish physical stock from an inventory-position record and from a commercial position. Model quantity at a product/location/time grain. A terminal is not its inventory, and a shipment is not the delivery commitment it may fulfill.

### 4.4 Engineering classification — IDO/POSC Caesar

Assess equipment and process reference terms for pumps, valves, columns, heat exchangers and related refinery objects. Preserve external reference identifiers in reviewed mappings. Use reference classifications to enrich asset master records without replacing EPM or source-system identity.

IDO and IOF are alternative or complementary modeling approaches only after compatibility review. An overlapping label does not establish equivalent identity criteria, temporal treatment or property semantics. Prefer reference alignment where a formal import is unnecessary.

### 4.5 Refinery process structure — OntoCAPE

Evaluate selected modules for material streams, unit operations, chemical components and processing relationships. Keep product grade specifications separate from chemical substances and mixtures.

The initial CDU, FCC and hydrocracker can use simplified process structures. Mass balance, yields and operating constraints belong in governed simulation or optimization code. A “produces ULSD” relationship expresses context; it does not establish a yield or guarantee that an intermediate stream meets finished-product specifications.

### 4.6 Quantities — QUDT

Use explicit quantity values and governed unit identifiers. Preserve the original value/unit before conversion. Capture measurement basis, currency where relevant, and any required temperature, pressure or standard-condition basis.

Examples include terminal stock volume, unit throughput and pressure. CPG netback also needs currency, price basis, product, market and period. A physical unit vocabulary does not supply those business qualifiers.

Validate compatible dimensions. Use deterministic governed conversions. Standard volume and observed volume require a measurement basis; matching “gallon” labels alone is insufficient. Do not treat volume-to-mass conversion as a fixed unit conversion without the required density and conditions.

### 4.7 Observations — SOSA/SSN

For each selected observation, identify the feature of interest, observed property, result, phenomenon time, result time and procedure/source as appropriate. Associate quantity results with QUDT where the chosen profile permits it.

Use this for a synthetic terminal tank reading or an observed weather measurement. A NOAA forecast is a forecast artifact; do not label it as a direct observation of a future physical event. Link estimated results to the model/procedure and epistemic classification.

### 4.8 Geography — GeoSPARQL

Represent facilities and routes as geographic features with geometry, a declared coordinate reference system and a geometry version. Preserve the footprint's source and valid time.

Spatial intersection can identify assets within a selected hazard footprint. Record that as a spatial result. Wind vulnerability, inundation, outage probability and supply impact require additional data and models. Do not infer a plant shutdown from intersection alone.

### 4.9 Evidence and time — PROV-O, OWL-Time and Web Annotation

Use PROV-O to trace source artifacts, transformation activities, responsible agents and generated outputs. Use ECE patterns to specify availability, validity, uncertainty and decision context. Use OWL-Time where interval relationships add value; ordinary typed timestamps remain appropriate for simple fields.

A claim should resolve to an assertion or passage in a fixed artifact version. Web Annotation selectors can identify that passage. Preserve the artifact digest and locator so a later edit does not silently change the supporting evidence.

Store effective/phenomenon time separately from publication, ingestion and decision time. An 08:20 artifact cannot support an 08:15 decision unless independently available evidence supports the claim. PROV-O does not enforce this rule by itself.

### 4.10 Organization and terminology — ORG and SKOS

Use ORG for organizational units, posts and membership. Link approvals to the applicable role assignment and policy version. A Commercial Manager title does not itself establish authority for a specific action or date.

Use SKOS for product-grade schemes, mode codes and reference mappings. Keep concept schemes versioned. The same preferred label in two schemes does not establish identity.

### 4.11 Commercial and financial semantics — FIBO

Assess a bounded use case such as a hedge instrument, counterparty or contractual obligation. Use only modules required by that case, with their transitive dependencies.

Keep physical commitments, commercial positions and derivative instruments separate. Petroleum pricing formulas, volume tolerances, nomination deadlines, quality obligations, demurrage and physical settlement need EPM-specific definitions where public modules do not fit.

### 4.12 Performance displays — PSDO

Evaluate PSDO only when a concrete display or feedback requirement exists. It can provide supporting vocabulary for communicating performance. EPM retains objective, measurement, metric, KPI, target and threshold definitions. Governed compute retains formulas.

This mirrors the actual People Graph approach: its reference register describes PSDO as selective supporting reuse and retains release/license closure as open. It does not approve PSDO as the foundation of the entire graph.

## 5. Mapping and import rules

Choose the weakest mapping that accurately expresses the relationship.

| Reuse method | Use when | Required evidence |
| --- | --- | --- |
| Direct term reuse | The published definition fits the required concept | Exact term/version and import-dependency review |
| EPM specialization | An EPM class is a narrower kind of the external class | Definition review and justified subclass axiom |
| Vocabulary crosswalk | Two controlled-vocabulary concepts need a reviewed correspondence | Mapping type, scope, version and reviewer |
| Reference alignment | A source is useful but its axioms should not enter EPM | Non-logical mapping record and rationale |
| Local extension | No suitable public or upstream term exists | Definition, owner, competency questions and promotion route |

Use `owl:equivalentClass` only after showing that both class definitions and their logical consequences agree. Use `owl:sameAs` only for the same individual. Never use it to connect a CRM record, customer organization and database identifier indiscriminately.

Use SKOS mapping properties for SKOS concepts. Do not substitute `skos:exactMatch` for OWL class equivalence. Explicitly distinguish a class URI, vocabulary concept URI, instance URI and source-record identifier.

Retain EPM semantic IDs. Local PPC extensions remain in a PPC namespace until accepted upstream. Bind generic evidence patterns through ECE. Document any approved exceptions under PPC-017.

## 6. Worked reference scenario

All enterprise names and operational conditions in this example are fictional. This is a proposed modeling pattern, not an implemented ontology or calculated scenario.

| Step | Representation | Candidate references | Execution requirement |
| --- | --- | --- | --- |
| Capture public storm information | Immutable source artifact with source, version, publication and valid times | PROV-O, OWL-Time; SOSA only for appropriate observations | Preserve observed/forecast distinction |
| Locate exposed assets | PPC refinery and terminal features; selected storm geometry | GeoSPARQL, EPM asset types | Spatial query with coordinate-system handling |
| Represent unit outage | Synthetic outage event, affected hydrocracker and state interval | IOF Core/Maintenance | State transition and source-event reconciliation |
| Estimate production loss | Model output linked to inputs and run | EPM, QUDT, PROV-O | Validated production/uncertainty model |
| Project inventory | Product/location/time stock trajectory | IOF Supply Chain, QUDT, OWL-Time | Inventory balance and forecast computation |
| Identify commitment risk | Contract obligations connected to customer, shipment and delivery window | EPM; selected FIBO concepts if suitable | Fulfillment and risk calculations |
| Explain performance impact | KPI result and supporting evidence | EPM, ECE, PROV-O; optional PSDO display | Governed KPI formula and claim-level grounding |
| Recommend and approve action | Alternatives, constraints, selected option, authority and outcome | EPM/ECE, ORG | Optimization plus enforced approval policy |

Keep source evidence, inferred exposure, predicted outage and synthetic scenario assumptions separate. A graph path supplies context; it does not establish a causal effect or numerical financial loss.

## 7. Semantic implementation profile

### 7.1 Formal graph

Load the pinned EPM bundle and selected ECE contracts. Resolve approved external dependencies to immutable local artifacts. Do not fetch mutable upstream imports silently during a production release.

Keep schema, PPC instances, reference vocabularies and evidence graphs distinguishable. Named graphs can support this separation, but named graphs alone do not enforce access control. Exclude hidden evaluation truth from agent-visible datasets and credentials.

### 7.2 Source and analytical mappings

Map Twenty, ERPNext, PostgreSQL, MySQL and SQLite representations to governed entity IDs. Record source system, object type, source key, EPM type, transformation and mapping version. Preserve authoritative lifecycle ownership.

Keep structural AML mappings and semantic RDF mappings aligned. Do not use canonical synthetic truth as an integration shortcut.

### 7.3 Neo4j projection

Project the operational subset required by the use case. Record the EPM semantic type URI, stable instance ID, effective interval, source references and mapping version. Define how reified events, quantities and temporal relationships become nodes or properties.

Do not flatten away the distinction between asset, process, observation, forecast and assertion. Test that source-to-RDF-to-LPG projection preserves the semantics required by each competency question. Neo4j does not inherit OWL reasoning or SHACL enforcement merely because nodes carry URIs.

### 7.4 Proposed artifact locations

These are proposed additions within existing repository folders, not files claimed to exist.

| Location | Intended content |
| --- | --- |
| `semantic/ontology/` | PPC extension definitions and the resolved EPM release reference |
| `semantic/mappings/` | Reviewed external-reference and source-system mappings |
| `semantic/shapes/` | PPC-specific validation shapes consistent with upstream contracts |
| `graph/rdf/` | Dataset/loading and named-graph configuration |
| `graph/neo4j/` | Projection specifications and loading logic |
| `tests/` | Competency, identity, temporal and projection checks |
| PPC project R2 bucket | Selected immutable source packages, license evidence, release manifests and generated data |

Store lightweight reviewed specifications in Git. Store generated datasets and large release artifacts in R2 under PPC-013. An external ontology package belongs in the release manifest even when the package itself is retained in R2.

## 8. Validation and competency questions

Implement these checks after module selection. They are acceptance criteria for future implementation, not tests completed by this document.

1. Can every operational entity resolve to its EPM type and source identity?
2. Can the model distinguish a refinery unit from its operating process and outage event?
3. Which units and measurement bases apply to each quantity?
4. Which source/version/time supports a reported tank level or weather value?
5. Which assets intersect the selected storm footprint, and which impacts are only estimates?
6. Which outage interval overlaps a delivery commitment window?
7. Which customers and obligations depend on the affected inventory and shipments?
8. Which governed data product and formula produced each KPI result?
9. Which evidence was available when a recommendation was made?
10. Which policy and valid role assignment authorized the selected action?
11. Can the Neo4j projection answer the required questions without losing source/time semantics?
12. Can an evaluated agent retrieve any hidden canonical truth or scoring key? Expected result: no.

Run syntax and import resolution checks, OWL consistency checks appropriate to the selected profile, SHACL validation, mapping coverage checks and competency queries. Reasoner consistency is not data completeness. SHACL completeness is not proof of business truth.

Use a small golden fixture for the hurricane scenario. Include negative cases: incompatible units, a forecast mistaken for an observation, duplicate source identities, future evidence, expired approval authority and hidden-truth leakage.

## 9. Adoption sequence

| Stage | Work | Completion evidence |
| --- | --- | --- |
| 1 — Fit assessment | Review IOF/BFO compatibility with EPM and select one bounded scenario | Definitions, alternatives, owners and mapping decisions recorded |
| 2 — Minimal profile | Assess Core, Maintenance, Supply Chain, QUDT, SOSA, GeoSPARQL and existing PROV-O/SKOS; add a small time profile | Exact terms/modules, pins, dependency closure and license evidence |
| 3 — Executable pilot | Load a small RDF fixture and project the required Neo4j subset | Validation and competency-query results |
| 4 — Engineering enrichment | Evaluate IDO/POSC Caesar and OntoCAPE for concrete gaps | Reviewed reference mappings and artifact/license closure |
| 5 — Commercial/evidence enrichment | Evaluate FIBO, ORG and Web Annotation where required | Bounded use-case acceptance and temporal/projection tests |
| 6 — Optional communication modules | Assess PSDO and any later evidence/policy candidates | Demonstrated requirement and approved scope |

If IOF compatibility is not established, keep its terms as reviewed references while retaining the current EPM foundation. Do not block the executable PPC pilot on importing a large ontology suite.

## 10. Artifact acceptance record

Complete one record per selected package. A discovery URL alone is insufficient.

```yaml
ontology_id: ONT-001
status: candidate
publisher: Industrial Ontologies Foundry
discovery_url: https://spec.industrialontologies.org/portal/
selected_ontology_iri: null
selected_version_iri: null
release_or_commit: null
retrieved_at: null
sha256: null
r2_locator: null
license_artifact: null
attribution: null
imported_dependencies: []
selected_terms: []
reuse_method: null
epm_mapping_version: null
ece_contract_version: null
owner: null
definition_review: pending
license_review: pending
owl_validation: pending
shacl_validation: pending
competency_results: pending
projection_validation: pending
decision_record: null
```

Record ontology and documentation licenses separately when they differ. Retain source attribution and redistribution conditions. Check any extracted subset's maintenance and licensing implications. Document versions of mapping and validation tools used to build the release.

## 11. Repository integration instructions

Add this file under `docs/`. The following are proposed companion edits; this deliverable does not modify the repository.

| Existing document | Suggested addition |
| --- | --- |
| PPC-000 | Add a reading-map entry: “Which public ontologies can we reuse? — PPC-019” |
| PPC-003 | Link to PPC-019 for reference reuse; retain EPM as business semantic authority |
| PPC-010 | Link to PPC-019 for the shortlist, mapping rules and graph implementation profile |
| PPC-016 | Link to the provenance/time/annotation guidance; keep ECE authority and evidence-isolation rules |
| PPC-017 | Link to the external dependency acceptance record; retain upstream artifact maturity and version checks |
| PPC-014 | Add module assessment and scenario-pilot tasks when implementation is scheduled |
| PPC-REG-001 | Record any adopted foundation/module decisions after review; allocate the next available ADR ID at that time |
| README | Add PPC-019 to the documentation entry points if desired |

Do not change the architecture baseline version or mark candidates as adopted merely because this guide has been added.

## 12. Source register and inspection basis

### PPC documents inspected

The review used the repository tree, README, AGENTS, PPC-000, PPC-003, PPC-010, PPC-016, PPC-017 and PPC-REG-001. It focused on ontology scope, ownership and document placement rather than a full review of all implementation areas.

| Document | Link |
| --- | --- |
| PPC overview | [README](https://github.com/aadehamid/pearland-petroleum-corporation/blob/main/README.md) |
| Agent guidance | [AGENTS](https://github.com/aadehamid/pearland-petroleum-corporation/blob/main/AGENTS.md) |
| Master index | [PPC-000](https://github.com/aadehamid/pearland-petroleum-corporation/blob/main/docs/PPC-000_Master_Index_and_Architecture_Guide.md) |
| Business semantic model | [PPC-003](https://github.com/aadehamid/pearland-petroleum-corporation/blob/main/docs/PPC-003_Business_Semantic_and_Domain_Model.md) |
| Ontology and graph architecture | [PPC-010](https://github.com/aadehamid/pearland-petroleum-corporation/blob/main/docs/PPC-010_Ontology_Knowledge_Graph_and_Policy_Architecture.md) |
| Evidence architecture | [PPC-016](https://github.com/aadehamid/pearland-petroleum-corporation/blob/main/docs/PPC-016_Evidence_Decision_Provenance_and_Evaluation_Architecture.md) |
| EPM dependency contract | [PPC-017](https://github.com/aadehamid/pearland-petroleum-corporation/blob/main/docs/PPC-017_EPM_Dependency_Semantic_Authority_and_Process_Conformance_Contract.md) |
| Decision register | [PPC-REG-001](https://github.com/aadehamid/pearland-petroleum-corporation/blob/main/docs/PPC-REG-001_Architecture_Decision_Register.md) |
| People Graph reuse precedent | [LIONG reference register](https://github.com/aadehamid/enterprise-people-graph/blob/main/LIONG-REF-001_Consolidated_Reference_Register.md) |

### Additional primary references

- [IOF public source repository](https://github.com/iofoundry/ontology).
- [IOF maintenance research paper](https://arxiv.org/abs/2404.05224).
- [POSC Caesar reference-data architecture](https://rds.posccaesar.org/doc/presentations/presentation_intro_plmrdl/).
- [ISO IDO standards scope](https://www.iso.org/standard/87560.html). A scope page is not the reusable ontology package.
- [OntoCAPE process-engineering paper](https://www.sciencedirect.com/science/article/pii/S0098135409000362). Verify the selected artifact independently before implementation.
- [QUDT schema documentation](https://qudt.org/doc/2025/04/DOC_SCHEMA-QUDT.html).
- [GeoSPARQL 1.1 specification](https://docs.ogc.org/is/22-047r1/22-047r1.html).
- [FIBO public source repository](https://github.com/edmcouncil/fibo).
- [OWL-Time 2017 Recommendation](https://www.w3.org/TR/2017/REC-owl-time-20171019/). Select a specific version; the unversioned URL may point to later work.
- [SEPIO discovery page](https://www.ebi.ac.uk/ols4/ontologies/sepio).
- [ODRL Information Model](https://www.w3.org/TR/odrl-model/).

All source links are discovery or documentation references unless an acceptance record explicitly identifies a selected artifact. This guide does not claim legal clearance, full compatibility, completed imports or implemented mappings.
