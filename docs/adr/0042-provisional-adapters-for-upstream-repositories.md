---
status: Decided
date: 2026-11-26
source_answers: docs/adr/answers/2026-11-26-first-principles-grill.md#round-1-2026-11-26
---

# ADR-0042: Provisional adapters for upstream repositories and exclusion of people graph from v1

## Context

Four upstream dependencies in `PPC-DEPENDENCY-AND-COMPATIBILITY.md` do not yet have released reusable packages (`DS_Business_Process`, ICE mapping YAML, full EDI drawing extraction, and ECE reusable schemas). Meanwhile, `enterprise-people-graph` exists in the local workspace under `personal-agent-skills/AGENTS.md` but is not part of PPC.

## Decision

The owner decided Round 1 Q5 (`docs/adr/answers/2026-11-26-first-principles-grill.md`):

- Owner verbatim: "Q5: We will keep people graph out for now. Also the genralized ontology will be a sperate step."
- Combined with "yes to all other", PPC adopts versioned provisional adapters pinned to the current commits of EPM, ICE, EDI, and ECE while explicitly marking pending upstream dependencies as unapproved, keeps `enterprise-people-graph` out of PPC v1, and treats the generalized downstream business-process ontology (`DS_Business_Process`) as a separate upstream step.

## Considered options

- Hard-gating PPC architecture reconciliation and Slice 1 planning on completed upstream releases (rejected because it stalls PPC indefinitely).
- Including `enterprise-people-graph` in PPC v1 for role and authorization graphs (rejected for v1; PPC uses its own role and grant contracts).

## Consequences

- PPC specifications must pin exact upstream commits in provisional adapters, never mark pending upstream drafts as approved releases, and leave generalized business-process bindings explicitly pending until the separate upstream ontology step lands.
