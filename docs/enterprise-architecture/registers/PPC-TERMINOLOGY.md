# PPC architecture terminology

Draft local reading aid, 2026-11-25. Upstream released terms retain upstream authority; this file does not redefine them. See [INFO-001](../03-enterprise-information/PPC-INFO-001_Enterprise_Ontology_Identity_and_Time.md) and [PPC-017](../../PPC-017_EPM_Dependency_Semantic_Authority_and_Process_Conformance_Contract.md).

| Term | Use in this package |
|---|---|
| World truth | PPC's hidden fictional physical/business state for generation and evaluation |
| Source record | What an independent simulated application recorded at its lifecycle stage |
| Recorded time | When a source stored an assertion; it does not prove reader availability |
| Publication / availability | When a revision was released and when a specific role could access it |
| Effective time | When the asserted condition applies in the modeled world |
| Branch | Isolated scenario history descended from a pinned checkpoint |
| Graph snapshot | Derived, immutable projection of declared inputs for traversal |
| Analytical release | Business-consistent manifest of product snapshots and watermarks |
| KPI definition / value | Approved EPM meaning versus a separate PPC computed result |
| Qualified | Exact version and envelope passed independent review with retained evidence |
| `SYNTHETIC` | Fictional PPC enterprise fact; never a fact about a real company |
| `SCENARIO_ASSUMPTION` | Explicit hypothetical intervention or stress input |

`OBSERVED`, `DERIVED` and `ESTIMATED` retain the meanings in [README](../../../README.md#what-is-real-and-what-is-synthetic). An epistemic `EVIDENCE`, `INFERENCE`, `CONTRADICTION` or `UNKNOWN` label is a separate axis under PPC-016.
