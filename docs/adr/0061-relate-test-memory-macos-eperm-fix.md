---
status: Decided
date: 2026-11-28
amends: ADR-0058
authority: Owner-delegated stand-in (Claude Fable 5.2, under ADR-0059)
source_answers: docs/adr/answers/2026-11-28-claude-fable-5-2-test-memory-eperm-ruling.md
---

# ADR-0061: Upstream fix and installer update for macOS `test_memory.py` `PermissionError`

## Context

Under [ADR-0058](0058-shared-relate-project-memory-for-all-agents.md), `scripts/test_memory.py` is installed and updated by the `relate-project-memory` skill (`install.py --update`) rather than hand-edited in PPC. During the 2026-11-28 overnight run, `WithRelate._group_alive` intermittently raised macOS `PermissionError` (`EPERM`) on `os.killpg(pgid, 0)` immediately after `SIGKILL` while PID 1 reaped zombie processes. Under [ADR-0059](0059-overnight-night-run-delegation-and-standin-authority.md), the options were submitted to Claude Fable 5.2 as owner-delegated stand-in.

## Decision

Claude Fable 5.2 ruled Option 1 (saved verbatim in [docs/adr/answers/2026-11-28-claude-fable-5-2-test-memory-eperm-ruling.md](answers/2026-11-28-claude-fable-5-2-test-memory-eperm-ruling.md)):

1. Fix `WithRelate._group_alive` upstream in `personal-agent-skills` (`relate-project-memory`) so transient `PermissionError` retries for up to 1 second before returning `False`, while every other exception continues to raise.
2. Do not bypass hooks (`--no-verify`), skip the test, or hand-edit PPC's copy of `scripts/test_memory.py`.
3. Pull the fix into PPC via a dedicated chore PR containing only the `install.py --update --tests-dir scripts` output (merged as PR #25, `fe3f327`).
4. Preserve all five core choices of [ADR-0058](0058-shared-relate-project-memory-for-all-agents.md) unchanged and record this amendment referencing [ADR-0059](0059-overnight-night-run-delegation-and-standin-authority.md).

## Considered options

- Hand-editing PPC's copy of `scripts/test_memory.py` or skipping the test (rejected because it breaks `ADR-0058`'s installer-owned provenance).
- Stopping the overnight run immediately without attempting the upstream fix (rejected because the upstream fix is isolated to `_group_alive` and verifiable through the full check and review loop).

## Consequences

- `scripts/test_memory.py` in PPC remains cleanly installer-managed and passes `scripts/check.sh` on macOS without intermittent `EPERM` failures.
- `scripts/adr_graph.py changed ADR-0058` traces `ADR-0061` with explicit stand-in authority and archived verbatim answer provenance per `ADR-0059`.
