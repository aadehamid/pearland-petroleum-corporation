# PPC-004 --- Data Modeling and Model-as-Code Standard

**Purpose:** Define conceptual, logical and physical modeling and the
AML/Azimutt approach.

PPC uses an **ASD-STE100-inspired** technical writing style. PPC does
not claim formal ASD-STE100 compliance. Terms keep one defined meaning
across the documentation.

## Modeling levels

-   **Semantic model:** what the business means.
-   **Conceptual model:** major concepts and relationships, independent
    of technology.
-   **Logical model:** information needed to represent those concepts.
-   **Physical model:** how a specific technology stores them.

## Choice

AML is the authoritative data-model-as-code language for data-relevant
conceptual/logical structures. Azimutt is the primary visual
modeler/explorer. Native DDL and migrations implement physical schemas.
pgModeler is optional for PostgreSQL-specific physical engineering.

## Why AML

AML uses entity/attribute/relation concepts, supports namespaces,
documentation and custom properties, and can carry PPC metadata such as
`concept_id`, `domain`, `owner`, `classification`, `data_product`, and
glossary mappings.

## Example

``` text
customer {
  concept_id: CUSTOMER,
  domain: commercial,
  classification: business_entity
}
  customer_id uuid pk
  name varchar
```

## Source representations

The enterprise Customer can map to `crm.twenty.account`,
`erp.erpnext.customer`, `commercial.postgres.counterparty`,
`logistics.mysql.ship_to`, and `analytics.ducklake.silver_customer`.

## Repository

``` text
architecture/semantic/
architecture/models/*.aml
physical/postgres/
physical/mysql/
physical/sqlite/
physical/ducklake/
physical/databricks/
ontology/
metadata/openmetadata/
```

## Generation goal

AML should increasingly drive DDL templates, documentation, basic DQ
rules, catalog registration, ontology mappings and synthetic-generator
contracts. Do not force non-data business architecture such as Value
Stream or Objective into AML when a broader semantic representation is
clearer.

## Relationship between AML and EPM semantics
AML defines PPC data-relevant structure; it does not replace EPM semantic authority. AML entities should carry stable EPM semantic IDs where available. Generated schemas, DQ rules, catalog and ontology mappings preserve those IDs.
