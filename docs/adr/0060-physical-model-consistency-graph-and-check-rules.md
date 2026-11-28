---
status: Decided
date: 2026-11-28
amends: none
authority: Owner-delegated stand-in (Claude Fable 5.2, under ADR-0059)
source_answers: docs/adr/answers/2026-11-28-claude-fable-5-2-physical-graph-ruling.md
---

# ADR-0060: Physical-model consistency graph design, EPM KPI provenance, and check gating

## Context

PPC describes facilities, process units, storage tanks, hydraulic transfer lines, pumps, process streams, KPIs, data products, and integration pipelines across architecture documents, EPM adapter artifacts (`PPC-017`), schemas, infrastructure configs, and upcoming WP-1 generator configurations and generated datasets. Before writing WP-1 physical simulation code, the owner required a consistency graph built with `consistency-graph` (`scripts/physical_graph.py`) and proposed for approval before implementation. Under [ADR-0059](0059-overnight-night-run-delegation-and-standin-authority.md), the design proposal and three first-pass rulings (`Q1`–`Q3`) were submitted to Claude Fable 5.2 as owner-delegated stand-in.

## Decision

Claude Fable 5.2 approved building `scripts/physical_graph.py` with conditions `C1`–`C7` and rulings `Q1`–`Q3` (saved verbatim in [docs/adr/answers/2026-11-28-claude-fable-5-2-physical-graph-ruling.md](answers/2026-11-28-claude-fable-5-2-physical-graph-ruling.md)):

1. **Overall design (`C1`–`C7`):** Approved to build from `start.py` on current `main` (`C1`). Take node IDs directly from sources rather than inventing codes (`C2`). Check `7 + 1` interfaces in `PPC-REVIEW-002` (7 internal bounded interfaces linked to `SITE-REF-A`, plus Terminal Ethanol in terminals and not linked to `SITE-REF-A`, `C3`). Check only counts that a source promises (including word-counts in `PPC-WORLD-001`), reporting unpromised totals as derived (`C4`). Allow the WP-0 isolation probe in Check 5 strictly via the declared probe prefix in `infra/r2/r2_prefix_map.yaml` and read permitted hidden-truth writers from repository sources (`C5`). Report missing future directories (`ot/`, `api/`, `verification/`) as `pending` rather than silently passing (`C6`). Scope Check 4 (provenance classification) to machine-readable records and document table classification statements (`C7`).
2. **EPM KPI provenance (`Q1`, amended):** Treat `PPC-REG-003`'s 15 KPI candidates and 7 data products as pending EPM bindings in `planned` mode; code defining a KPI without an EPM binding fails from the first run. Reject `PPC_EXTENSION` because PPC must never redefine KPI meaning (`PPC-017`); allowed states are `CONSUMED_PROVISIONAL`, `PENDING_UPSTREAM_RELEASE`, or `pending`. Any future PR adding `semantic/mappings/epm_kpi_bindings.yaml` must also add it to `PPC-PLAN-001`.
3. **`PPC-REG-002` and obsolete scaffold folders (`Q2`, amended):** Retain `PPC-REG-002` without marking it superseded (`PPC-ARCH-000`), parse it as a source, and let `physical_graph.py check` report its stale `Debezium→Kafka`, `D1`, and `DuckLake` rows alongside the empty `integration/debezium/`, `integration/kafka/`, and `lakehouse/ducklake/` scaffold folders as findings to be settled in a dedicated reconciliation PR.
4. **Gate order (`Q3`):** Report mode (`planned` vs `built`) per section based solely on which files exist. In the initial PR, `scripts/check.sh` runs `scripts/test_physical_graph.py` as a failing step and runs `physical_graph.py check` and `summary` as a non-failing report. Once the `Q2` findings are reconciled and `check` reports zero findings, promote `physical_graph.py check` to a failing gate in `scripts/check.sh`. Pending items never fail the gate. Add one pointer line in `AGENTS.md`.

## Considered options

- Excluding `PPC-REG-002` from the graph and marking it superseded (rejected under `Q2` because `PPC-ARCH-000` retains it and reconciles without superseding it).
- Introducing a `PPC_EXTENSION` KPI disposition (rejected under `Q1` because no PPC document defines it and it would risk letting PPC redefine EPM KPI meaning).
- Making `physical_graph.py check` a failing gate immediately on first merge before reconciling `Q2` findings (rejected under `Q3`; follow the `consistency-graph` skill's two-step gate order).

## Consequences

- `scripts/physical_graph.py`, `scripts/test_physical_graph.py`, the `AGENTS.md` pointer line, and the initial `scripts/check.sh` wiring ship first, surfacing `Q2` findings (`PPC-REG-002` legacy rows and obsolete scaffold folders) and any source spelling findings cleanly.
- A follow-up reconciliation PR settles those findings and promotes `physical_graph.py check` to a failing gate in `scripts/check.sh` before WP-1 code merges.
- As WP-1+ fixtures (`fixtures/golden/refinery_a_design_basis.yaml`, `fixtures/golden/refinery_a_ot_tags.yaml`, `generators/`, and generated manifests) arrive, they are added as sources to the same graph.
