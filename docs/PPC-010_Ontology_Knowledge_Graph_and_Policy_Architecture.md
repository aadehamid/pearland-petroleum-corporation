# PPC-010 --- Ontology, Knowledge Graph, and Policy Architecture

**Purpose:** Separate formal enterprise meaning from operational
relationship efficiency.

PPC uses an **ASD-STE100-inspired** technical writing style and
consistent defined terminology.

## Two graph roles

**Meaning matters:** Apache Jena/Fuseki with RDF, RDFS, OWL, SHACL,
SKOS, PROV-O and SPARQL.\
**Operational efficiency matters:** Neo4j Community labelled property
graph for current instances, state, exposure traversal and GraphRAG
context.

Do not force one graph technology to solve both problems.

## Jena example

`EnterpriseKPI rdfs:subClassOf Metric`. `evaluatesObjective` has
governed domain/range. SHACL can require each Enterprise KPI to have
owner, formula, unit, time grain, objective and supplying data product.

## Neo4j example

Hurricane → THREATENS → Refinery → CONTAINS → Hydrocracker → PRODUCES →
ULSD → STORED_AT → Terminal → FULFILLS → Contract → FOR → Customer.

Neo4j answers which current customers/KPIs are exposed through a path.
Jena answers what those entity/relationship types mean and what semantic
constraints apply.

## Mapping

Operational nodes carry stable semantic type URIs that map to ontology
classes. AML defines structural representation. RDF/OWL defines formal
meaning. Neo4j holds operational instances. OpenMetadata catalogs
physical assets and lineage.

## Policy

Policy is conceptually separate from meaning and state. Initial
policy-as-code defines allowed actions, preconditions, approval
thresholds, prohibited conditions and escalation rules.

Example: an inventory transfer above a governed volume requires
Commercial Manager approval. The optimizer may recommend the transfer;
the agent cannot bypass the approval policy.

## Agent context

Jena = meaning. Neo4j = relationships/current context. DuckLake =
analytical facts. Policy = permitted actions. This four-part context
feeds Intelligent Automation.

## Evidence and decision graph
PPC extends the graph with ECE-derived concepts: Decision, DecisionOption, EvidenceItem, SourceAssertion, Claim, Artifact, Constraint, Approval and Outcome. Jena formalizes selected semantics; Neo4j traverses operational evidence and decision relationships.

Do not confuse provenance with epistemic status. Provenance explains origin. Epistemic status explains whether a claim is evidence, inference, contradiction or unknown.

## EPM ontology source-of-truth boundary
PPC consumes versioned EPM Turtle as downstream machine semantic authority and does not fork the enterprise ontology. Jena validates/queries it; Neo4j exposes PPC instances typed by EPM IDs. PPC-specific classes remain in a PPC namespace until promoted upstream.
