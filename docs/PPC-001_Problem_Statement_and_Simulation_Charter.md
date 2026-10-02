# PPC-001 --- Problem Statement and Simulation Charter

**Supersedes:** PPC-SIM-001\
**Purpose:** Define the problem, simulation scope, objectives, and
acceptance criteria.

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

## Problem

Downstream events cross functional boundaries. A refinery outage can
change throughput, yield, inventory, basis, customer availability,
logistics cost, export optionality, margin, hedge exposure, and service
performance. Traditional reporting fragments this chain.

PPC must answer: 1. What event occurred? 2. What assets, products,
routes, customers, contracts, and positions are exposed? 3. What changed
operationally and commercially? 4. Which KPI moved or is at risk? 5.
Why? 6. What margin/service impact is expected? 7. What feasible actions
exist? 8. Which action is preferred? 9. What can auto-execute, what
requires approval, and what must escalate? 10. What should PPC learn?

## Executable loop

Observed external world → Event → PPC exposure → Operational/commercial
impact → Measurements/metrics/KPIs → Performance Intelligence →
Alternatives → Optimization/policy → Recommendation/action → Outcome →
Learning.

## Initial scope

PADD 3 Gulf Coast. ULSD and gasoline. One fictional refinery with
simplified CDU/FCC/hydrocracker, three terminals, pipeline/truck/marine
logistics, twelve customers, contracts, trades, positions, inventory and
commitments.

## Public/synthetic boundary

Public data describes external conditions. PPC internal operations are
fictional. Public observations condition the simulation; they do not
reveal a real company's proprietary operations.

## Primary scenario

A Gulf Coast hurricane occurs while observed PADD 3 distillate inventory
is tight. PPC identifies exposed assets, estimates probabilistic
capacity loss, forecasts inventory, identifies customer risk, quantifies
margin-at-risk, generates and optimizes alternatives, applies policy,
requests approval where required, records outcomes, and creates a
learning case.

## Non-goals

PPC is not a live trading system, physical-control system, production
refinery simulator, real VaR engine, or representation of a named real
company.

## Acceptance

A user can trace a KPI from objective to formula, data product, source
representation, event drivers, causal evidence, recommendation, policy
decision, action and outcome. Every material value has provenance.

## Context and evidence success criteria
PPC must demonstrate why a decision was justified from evidence available at the time. Material claims resolve to source assertions/artifacts; evidence, inference, contradiction and unknown are distinguished; temporal leakage is prohibited; hidden canonical truth is isolated; alternatives, constraints, authority, approval, expected outcome and actual outcome are retained; later evidence can be compared with the original rationale to create a learning case.

## EPM conformance success criteria
A PPC release identifies EPM dependency versions, passes required semantic competency questions, preserves Meaning-vs-Compute, maps PPC process instances to EPM process authority, and identifies intentional deviations rather than silently redefining the designed process.
