# PPC-017 — EPM Dependency, Semantic Authority, and Process Conformance Contract

**Baseline:** PPC Architecture Baseline v1.2  
**Purpose:** Define how PPC consumes EPM releases, respects semantic authority, applies Meaning-vs-Compute, and validates synthetic enterprise behavior against EPM process authority.

## 1. Dependency bundle
Each PPC release records immutable versions/commits/checksums where possible for:

```yaml
epm:
  architectural_principles: <version>
  business_architecture: <version>
  process_authority: <version>
  semantic_model: <version>
  ontology: <version>
  shacl_shapes: <version>
  measurement_kpi_model: <version>
  data_product_portfolio: <version>
  kpi_store_contract: <version>
  competency_questions: <version>
```

## 2. Artifact authority
PPC distinguishes canonical foundation artifacts, process authority, machine ontology source of truth, approved decisions/specifications, drafts/candidates, existing-unlinked material, and superseded/retired material.

PPC must not silently promote a draft or existing-unlinked EPM artifact into an approved dependency. Exceptions are recorded in the PPC Architecture Decision Register.

## 3. Meaning versus Compute
PPC adopts the EPM rule:

> **Meaning does not compute.**

```text
EPM semantic identity
      ↓
PPC KPI metadata identity
      ↓
governed formula pointer
      ↓
governed metric/data-product view
      ↓
compute
      ↓
KPI value
```

Jena, Neo4j, Superset and LLMs do not become authoritative KPI calculators.

## 4. Business process authority
PPC consumes EPM machine-readable process-authority artifacts where available, including downstream process maps, O2C/Commercial value streams, data-product portfolio and schemas.

EPM defines the designed process. PPC generates executed process instances.

```text
EPM process authority
       ↓
expected stages/activities/relationships
       ↓
PPC synthetic transactions/events
       ↓
process-conformance evaluation
```

PPC can generate deliberate delay, rework, skipped activity, exception handling or control failure. Such deviations are labeled; they do not silently redefine EPM.

## 5. Process Performance Intelligence
PPC can compare designed and executed process paths, identify bottlenecks/rework/cycle-time/handoff delay, and relate them to OTIF, DSO, demurrage, margin and other outcomes. Process conformance is diagnostic evidence; causal claims still require causal analysis.

## 6. Competency questions
PPC inherits relevant EPM competency questions and adds instance-level tests such as:
- Which PPC capability supports this process?
- Which process instance produced this measurement?
- Which data product supplies this KPI?
- Which KPI evaluates the affected objective?
- Which source object maps to this enterprise concept?
- Which event changed process state?
- Which customer/contract is affected by the deviation?

## 7. Data products and KPI promotion
PPC maps implementations to authoritative EPM data-product definitions where they exist. PPC-only products are extensions until accepted upstream.

PPC follows EPM promotion logic: measurement → standardized metric/indicator → governed KPI. A report calculation or synthetic field is not automatically a KPI.

## 8. Semantic release tests
Before PPC release:
1. Dependency manifest resolves.
2. Required ontology classes/properties exist.
3. SHACL validation passes where applicable.
4. Required competency questions pass.
5. PPC extensions are separated from EPM concepts.
6. KPI metadata conforms to EPM contract.
7. Data-product mappings resolve.
8. Process instances map to EPM process authority.
9. Non-approved upstream dependencies have explicit exceptions.

## 9. Change handling
When EPM changes, PPC compares semantic IDs/definitions, runs ontology/SHACL/competency tests, process-conformance regression, KPI/data-product contract tests, records migration decisions, then updates the dependency manifest.

## Governing principle
> **EPM defines downstream design and meaning. PPC instantiates, executes, measures, and tests that design without becoming a competing semantic authority.**
