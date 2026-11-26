---
status: Decided
date: 2026-11-26
source_answers: docs/adr/answers/2026-11-26-first-principles-grill.md#round-3-2026-11-26
---

# ADR-0053: Legacy synthetic data quarantine and WorldExportBundle cross-repository contract

## Context

In T34 and T43–T44 the owner noted that earlier synthetic datasets stored in Cloudflare R2 and `Engineering_Drawing_to_Graph` were created before the canonical PPC world model existed and cannot reconcile logically across repositories. In Round 1 Q1 (`ADR-0041`) the owner confirmed that PPC creates the canonical world model consumed by the listed sister repositories.

## Decision

The owner accepted Round 3 Q18 via "Yes to all." (`docs/adr/answers/2026-11-26-first-principles-grill.md`):

- Accepted recommendation: "Yes. Lock both the legacy-data quarantine rule and the WorldExportBundle cross-repo publication contract."
- Quarantine before retirement: do not delete legacy R2 objects or sister-repo fixtures during the documents-only phase; label them `LEGACY_PRE_WORLD_MODEL` under isolated prefixes and schedule archival or deletion only after PPC's WP-1 canonical world passes independent verification.
- `WorldExportBundle` contract: PPC publishes one versioned export bundle (pinned world version, branch, seed, Delta tables, OT L0 tag schedule for ICE, structured equipment/topology manifest for EDI, KPI and process instance fixtures for EPM, and role-scoped evidence/dossier fixtures for ECE) so every sister repository consumes coherent data from Refinery A without reading hidden world truth as an integration shortcut.

## Consequences

- `PPC-WORLD-001`, `PPC-PLAN-001`, and `PPC-PLATFORM-001` define the `LEGACY_PRE_WORLD_MODEL` isolation rule and the versioned `WorldExportBundle` handoff schema.
