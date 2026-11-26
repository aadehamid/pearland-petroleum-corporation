# PPC-GRAPH-001 — Enterprise Instance Graph

Inspected PPC baseline: [`01027a84be5d453cbb4e2ea091e4884729918b15`](../registers/PPC-SOURCE-REGISTER.md). This commit is the original PPC source-inspection reference, not this draft's content revision or owner approval. Later linked specifications are read at the current branch revision.

| Control | Value |
|---|---|
| ID / status | PPC-GRAPH-001 / proposed draft for owner review |
| Version / date | 0.1.0-draft / 2026-11-25 |
| Authority | [PPC-010](../../PPC-010_Ontology_Knowledge_Graph_and_Policy_Architecture.md), [PPC-016](../../PPC-016_Evidence_Decision_Provenance_and_Evaluation_Architecture.md), [INFO-001](PPC-INFO-001_Enterprise_Ontology_Identity_and_Time.md); ADR-008–010 in [PPC-REG-001](../../PPC-REG-001_Architecture_Decision_Register.md) |
| Inputs / output | Pinned semantic, identity, source, evidence and analytical releases → immutable, branch-scoped graph publication |

## 1. Boundary and authority

The enterprise instance graph is a derived projection for relationship queries. EPM Turtle and shapes own formal meaning. Source applications own recorded transactions; the PPC world owns simulated physical state; governed models own quantities. Neo4j Community is the baseline operational graph under ADR-010; T79 states that PPC has no Neo4j Enterprise entitlement. A graph edge can show possible exposure, but cannot calculate volume, margin or causation. A proposed Relate browser and translation tools need separate qualification. No real plant is represented.

```text
Released source + identity + evidence + semantic inputs
                 ↓ validate, project, reconcile
           branch-scoped graph snapshot
                 ↓ authorized traversal
        exposure path + source lineage
                 ↓ qualified model, if needed
              quantified result
```

## 2. Projection contract

`GraphNode` has `node_id: opaque string`, `kind: governed IRI and version`, `branch_id`, `valid_from/to: UTC instant`, `publication_id`, `source_recorded_at: UTC instant`, `supersedes_publication_id` and scoped ordinal, `source_refs: nonempty list`, `mapping_assertion_id` where mapped, and `provenance_class`, `authorization_label`, `published_at` and the recipient/role-and-channel availability relation from [INFO-001 §3](PPC-INFO-001_Enterprise_Ontology_Identity_and_Time.md). `GraphEdge` has its own `edge_id`, versioned `relation_iri`, typed `from_id/to_id`, `branch_id`, half-open valid interval, publication ID, published-at time, source-record time, supersedes-publication ID, scoped supersession ordinal, source refs, provenance class, assertion status, confidence basis and authorization label. It uses the same recipient/role-and-channel availability relation as `GraphNode`. Intervals are half-open. A source reference includes immutable revision and locator. `GraphSnapshot` has snapshot ID, parent, branch, subject scope, scoped ordinal, supersedes-publication ID, source-recorded time, lifecycle status, semantic and mapping digests, per-source watermarks, input release IDs, projection version, creation time, publication time, recipient/role-and-channel availability relation, authorization scope and integrity digest. Both the snapshot and returned assertions must pass the reader cutoff. Apply [INFO-001 §3](PPC-INFO-001_Enterprise_Ontology_Identity_and_Time.md) to each complete subject-scoped graph publication and its assertions. If any assertion in that subject scope is denied, use an older eligible publication for that scope or return `UNRESOLVED`; traversal cannot mix old and new edges within a scope. Optional unknown endpoints remain unresolved assertions, not invented nodes.

Graph publication transitions `CANDIDATE → VALIDATED|REJECTED|QUARANTINED`, `QUARANTINED → CANDIDATE|REJECTED`, `VALIDATED → PUBLISHED|REJECTED`, and `PUBLISHED → SUPERSEDED` when a successor is published for that scope. The supersession link is global; [INFO-001 §3](PPC-INFO-001_Enterprise_Ontology_Identity_and_Time.md) decides which publication each reader may use. `REJECTED` is terminal for that candidate ID; a corrected candidate gets a new ID. Publication needs a consistent input cut. A correction creates a new snapshot and retains the prior one for replay. A source deletion becomes a scoped tombstone; it does not silently erase historical evidence. One projection rule has one owner and version. The conversion report lists every source assertion, projected target, loss or rejection. Required meaning lost in RDF-to-property-graph conversion blocks publication.

Queries require pinned release, branch, snapshot, subject scope, effective time, knowledge cutoff, actor/recipient, role, channel and purpose. Inherited branch data is frozen at the fork and may change only through explicit adoption. Filter authorization before traversal, ranking, aggregation and response formatting. A restricted edge must not leak through path counts, node names, error wording or a guessed correction. Return `UNRESOLVED` if a required identity maps to zero or several eligible targets.

## 3. Worked synthetic fixture

All entities, times and values here are `SYNTHETIC`. At 10:00 UTC, a reviewed engineering publication links compressor C to hydrocracker H. A source observation at 10:05 records a derate. The 10:30 snapshot can show `C → FEEDS → H → PRODUCES → ULSD → FULFILLS → contract K`. It labels K as *potentially exposed*. Only the pinned engineering model and commercial calculation can state a numerical effect. A duplicate delivery of the same observation revision creates no second edge. A corrected engineering link recorded at 12:00 produces a new snapshot; the 11:00 decision replay still uses the old graph. A sibling scenario link cannot appear in baseline.

If K is restricted to another role, an unauthorized planner sees no K, path count, or clue that K exists. If the correction itself is inaccessible, the planner uses the last authorized publication for that question or receives `UNRESOLVED`. A graph rebuild must not execute another physical derate or operational transaction.

## 4. Qualification and open decisions

Acceptance evidence must include a projection manifest, round-trip assertion comparison, negative false-equivalence fixture, shape and competency results, as-of replay, branch isolation, restricted-path side-channel test, duplicate delivery test, corruption/rebuild test and measured query results on the chosen workload. Expected and observed results, exact digests and reviewer disposition are required. None is reported as run here.

Under [ADR-0044](../../adr/0044-turtle-pyshacl-neo4j-serving-path.md), [ADR-0051](../../adr/0051-exe-dev-r2-databricks-hosting-and-recovery.md), and [ADR-0052](../../adr/0052-two-stage-ux-dash-and-relate-wasm.md), Git Turtle validated with `rdflib`/`pyshacl` feeds Neo4j Community hosted on `exe.dev` (persistent `/data`, offline `neo4j-admin dump` to R2, strictly treated as a rebuildable projection), with standing Jena/Fuseki demoted to an optional offline SPARQL tool and Relate WASM committed as the Slice 1.5 business-facing Interactive Enterprise Context Explorer gated on API permission filtering and Cypher parity. Open runtime checks: graph retention/query bounds and supported RDF-to-LPG construct loss report. Source discussion: T62, T103–106 and T110–112 in the [exchange register](../registers/PPC-Discussion-Decision-Traceability.md), with line locators in its CSV. Those exchanges propose projection and browser exploration; they do not prove deployment.

The [exchange register](../registers/PPC-Discussion-Decision-Traceability.md) routes T62, T79, T103–105, T110–112 to this draft. `GAP-002` Markdown audit is closed in [PPC-REVIEW-001 §5](../independent-review/PPC-REVIEW-001_Document_Coverage_and_Transcript_Audit.md#5-audit-of-raw-chatgpt-transcript-t1t145-versus-ef4eb08-ppc-documents-closing-gap-002).
