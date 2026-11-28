# Stand-in ruling: macOS `test_memory.py` `PermissionError` (`ADR-0059` / `ADR-0058`)

- **Date:** 2026-11-28
- **Authority:** Owner-delegated stand-in (Claude Fable 5.2 via `claude -p --model fable --permission-mode plan`, per `ADR-0059`)
- **Context:** During the overnight run, `scripts/test_memory.py` intermittently failed in `WithRelate._group_alive` on macOS XNU when `os.killpg(pgid, 0)` returned transient `EPERM` (`PermissionError`) while a `SIGKILL`ed process group's zombie members were being reaped by PID 1. `scripts/test_memory.py` is owned by the `relate-project-memory` skill in `personal-agent-skills` (`ADR-0058`).

## Verbatim ruling

> **Ruling: Option 1.** Fix it upstream in personal-agent-skills, then pull it into PPC with `install.py --update`.
> I checked the template: `_group_alive` catches only `ProcessLookupError`, so the report matches the code.
> Constraints:
> 1. Change `_group_alive` only. On `PermissionError`, retry for up to 1 second, then return `False`. Let every other error raise.
> 2. Do not use `--no-verify`, skip the test, or hand-edit PPC's copy of `test_memory.py`.
> 3. The personal-agent-skills PR goes through the full review loop and `scripts/check.sh`. Before merging, guard against the merge commit exposing Hamid's personal email.
> 4. In PPC, open a dedicated chore PR that contains only the `install.py --update` output.
> 5. Record the ruling as a short amendment note to ADR-0058, citing ADR-0059, and list it in the morning log. I could not find ADR-0059 in this repository, so cite PPC's copy.
> 6. If the fix fails review or the race persists, stop the run (Option 3).

## Execution receipt

- Upstream fix merged in `personal-agent-skills` PR #124 (`d7e7b78`).
- PPC update merged in `pearland-petroleum-corporation` PR #25 (`fe3f327`), containing only the `install.py --update --tests-dir scripts` output for `scripts/test_memory.py`.
