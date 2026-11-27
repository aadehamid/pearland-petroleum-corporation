---
status: Decided
date: 2026-11-26
amends: ADR-009, ADR-035
source_answers: docs/adr/answers/2026-11-26-first-principles-grill.md#round-2-2026-11-26
---

# ADR-0044: Git Turtle and pyshacl to Neo4j runtime serving path with generalized DS_Business_Process lineage

## Context

`ADR-009` in `PPC-REG-001` selected a standing Apache Jena/Fuseki server for formal semantics. Both `enterprise-performance-model` and `industrial-context-engineering` (formerly `scada_harmonization`, PR #57) now standardize on Git Turtle validated with `pyshacl` projected directly into Neo4j Community, without a standing runtime triple store. Meanwhile, the generalized downstream business-process ontology is being derived separately from `kpi-store/1.2` on the `ds-business-process/1.0` branch of `downstream_oil_and_gas_ontology_release`.

## Decision

The owner decided Round 2 Q9 (`docs/adr/answers/2026-11-26-first-principles-grill.md`):

- Owner verbatim: "Q9: Yes. remeber the ontology that will be specialized for PPC will be generalize from KPI 1.2 in downstreal oil and gas ontology release. The generalized version will be in the ds business process branch in the downstreal oil and gas release repo"
- Accepted recommendation: "Yes. Make Git Turtle plus pyshacl validation feeding Neo4j Community the canonical serving path, and demote Jena/Fuseki to an optional offline verification tool."

## Considered options

- Retaining a standing Apache Jena/Fuseki server in PPC runtime (rejected because it diverges from both EPM and ICE serving architectures).

## Consequences

- `ADR-009` is amended: Git Turtle plus `rdflib`/`pyshacl` validation at release time feeding Neo4j Community (`ADR-010`) is PPC's canonical runtime path; Apache Jena/Fuseki stays optional for offline SPARQL verification and homelab learning only.
- `ADR-035` is clarified: PPC specializes and consumes the approved generalized ontology from branch `ds-business-process/1.0` (derived from `kpi-store/1.2`) in `downstream_oil_and_gas_ontology_release` once released.
