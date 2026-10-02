# PPC-003 --- Business, Semantic, and Domain Model

**Purpose:** Define authoritative human-readable business meaning.

## Documentation standard

PPC uses an **ASD-STE100-inspired** technical writing style. PPC does
not claim formal ASD-STE100 compliance. Use consistent terms, direct
verbs, short sections, explicit relationships, and established technical
vocabulary when it improves precision.

## Governing principles

-   Business meaning is independent of software products.
-   Public observations and synthetic PPC facts are always
    distinguishable.
-   Each operational object has an authoritative source for its
    lifecycle stage.
-   The canonical synthetic PPC world exists before heterogeneous
    source-system materialization.
-   Data products expose reusable governed information. BI tools do not
    own KPI logic.
-   Formal semantics and operational graph traversal are separate
    responsibilities.
-   Specialized models calculate forecasts, causal effects, uncertainty,
    and optimized actions. LLMs orchestrate and explain.
-   Material actions remain subject to explicit policy and human
    approval.

## Business hierarchy and relationships

Enterprise → Business Domain → Value Stream → Value-Stream Stage. Stages
**use** capabilities. Capabilities decompose into sub-capabilities and
are realized through processes. Processes contain activities. Events
trigger/change work. Activities support decisions. Decisions influence
outcomes.

A value stream is not a list of capabilities. One capability can support
several stages and value streams.

## Performance vocabulary

**Measurement:** observed or calculated value with context.\
**Metric:** standardized repeatable measure used to monitor, compare, or
diagnose.\
**KPI:** governed metric used to evaluate an important objective/outcome
and trigger accountability/action.

## PPC value streams

Source and Optimize Supply; Convert Feedstock to Products; Position and
Move Product; Price and Sell Product; Fulfill Customer Commitment;
Invoice and Settle; Manage Commercial Risk; Evaluate and Optimize
Performance.

## Initial capabilities

Market Intelligence, Physical Trading, Refinery Planning, Inventory
Management, Product Scheduling, Transportation Management, Pricing
Management, Customer Fulfillment, Billing/Receivables, Commercial Risk
Management, Performance Management.

## Core concepts

Party, Customer, Counterparty, Product, Commodity, Location, Asset,
Refinery, Refinery Unit, Terminal, Pipeline, Route, Contract, Trade,
Position, Hedge, Order, Nomination, Shipment, Delivery, Invoice,
Payment, Inventory Position, Price Observation, Event, Measurement,
Metric, KPI, Target, Threshold, Data Product, Recommendation, Action,
Scenario, Learning Case.

## Customer example

`Customer` is the enterprise concept. Twenty `Account`, ERPNext
`Customer`, PostgreSQL `Counterparty`, MySQL `Ship-To`, and DuckLake
`Conformed Customer` are system representations. A governed identity
crosswalk connects them.

## Semantic implementation rule

The written semantic model defines agreed meaning. AML defines
data-relevant structure. RDF/OWL formalizes selected meaning.
OpenMetadata catalogs implementations. Neo4j represents operational
instances and current relationships.

## Authority boundary with EPM
This document is a PPC implementation guide, not independent downstream semantic authority. PPC concepts conform to the referenced EPM release. EPM process-authority artifacts govern designed processes where available. PPC creates instances, mappings and explicitly labeled extensions.
