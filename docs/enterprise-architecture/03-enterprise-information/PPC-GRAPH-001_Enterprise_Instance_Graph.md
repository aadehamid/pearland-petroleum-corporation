# PPC-GRAPH-001 — Enterprise Instance Graph

| Control | Value |
|---|---|
| ID / status | PPC-GRAPH-001 / proposed draft for owner review |
| Version / date | 0.1.0-draft / 2026-11-25 |
| Authority | [PPC-010](../../PPC-010_Ontology_Knowledge_Graph_and_Policy_Architecture.md), [PPC-016](../../PPC-016_Evidence_Decision_Provenance_and_Evaluation_Architecture.md), [INFO-001](PPC-INFO-001_Enterprise_Ontology_Identity_and_Time.md); ADR-008–010 in [PPC-REG-001](../../PPC-REG-001_Architecture_Decision_Register.md) |
| Inputs / output | Pinned semantic, identity, source, evidence and analytical releases → immutable, branch-scoped graph publication |

## 1. Boundary and authority

The enterprise instance graph is a derived projection for relationship queries. EPM Turtle and shapes own formal meaning. Source applications own recorded transactions; the PPC world owns simulated physical state; governed models own quantities. Neo4j Community is the baseline operational graph under ADR-010. A graph edge can show possible exposure, but cannot calculate volume, margin or causation. A proposed Relate browser and translation tools need separate qualification. No real plant is represented.

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

`GraphNode` has `node_id: opaque string`, `kind: governed IRI and version`, `branch_id`, `valid_from/to: UTC instant`, `recorded_from/to: UTC instant`, `source_refs: nonempty list`, `mapping_assertion_id` where mapped, and `classification`. `GraphEdge` adds `edge_id`, `relation_iri`, typed `from_id/to_id`, `assertion_status`, `confidence_basis`, and authorization label. Intervals are half-open. A source reference includes immutable revision and locator. `GraphSnapshot` has snapshot ID, parent, branch, semantic and mapping digests, per-source watermarks, input release IDs, projection version, creation time and integrity digest. Optional unknown endpoints remain unresolved assertions, not invented nodes.

Allowed lifecycle: `CANDIDATE → VALIDATED → PUBLISHED → SUPERSEDED`; rejection or quarantine branches from candidate/validation. Publication needs a consistent input cut. A correction creates a new snapshot and retains the prior one for replay. A source deletion becomes a scoped tombstone; it does not silently erase historical evidence. One projection rule has one owner and version. The conversion report lists every source assertion, projected target, loss or rejection. Required meaning lost in RDF-to-property-graph conversion blocks publication.

Queries require branch, snapshot, effective time, knowledge cutoff, role and purpose. Inherited branch data is frozen at the fork and may change only through explicit adoption. Filter authorization before traversal, ranking, aggregation and response formatting. A restricted edge must not leak through path counts, node names, error wording or a guessed correction. Return `UNRESOLVED` if a required identity maps to zero or several eligible targets.

## 3. Worked synthetic fixture

All entities, times and values here are `SYNTHETIC`. At 10:00 UTC, a reviewed engineering publication links compressor C to hydrocracker H. A source observation at 10:05 records a derate. The 10:30 snapshot can show `C → FEEDS → H → PRODUCES → ULSD → FULFILLS → contract K`. It labels K as *potentially exposed*. Only the pinned engineering model and commercial calculation can state a numerical effect. A duplicate delivery of the same observation revision creates no second edge. A corrected engineering link recorded at 12:00 produces a new snapshot; the 11:00 decision replay still uses the old graph. A sibling scenario link cannot appear in baseline.

If K is restricted to another role, an unauthorized planner sees no K, path count, or clue that K exists. If the correction itself is inaccessible, the planner uses the last authorized publication for that question or receives `UNRESOLVED`. A graph rebuild must not execute another physical derate or operational transaction.

## 4. Qualification and open decisions

Acceptance evidence must include a projection manifest, round-trip assertion comparison, negative false-equivalence fixture, shape and competency results, as-of replay, branch isolation, restricted-path side-channel test, duplicate delivery test, corruption/rebuild test and measured query results on the chosen workload. Expected and observed results, exact digests and reviewer disposition are required. None is reported as run here.

ADR-009 and ADR-010 remain baseline. Open choices: standing Jena service versus validation at release; Relate WASM permissions and deployment; graph retention and query bounds; supported RDF construct subset. Compare each against access, conversion loss and operating evidence before an ADR change. Source discussion: T62, T103–106 and T110–112 in the [exchange register](../registers/PPC-Discussion-Decision-Traceability.md), with line locators in its CSV. Those exchanges propose projection and browser exploration; they do not prove deployment.
