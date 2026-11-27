---
name: project-memory
description: Shared PPC project memory in a Relate graph, used by every agent through scripts/memory.sh. Use to recall what earlier sessions learned before starting work, and to save a decision, owner preference, correction or hard-won finding before a session ends.
---

# Project memory

Every agent on this repository (Claude Code, Codex, Cursor, Gemini, Kimi, Pi and the rest) shares one memory: a Relate graph that `scripts/memory.sh` reads and writes. Run `scripts/memory.sh` with no arguments for its commands. The store lives in the repository's common git directory, so every worktree sees the same memory and Git never tracks it.

Memory supplements the record. Decisions are on the record only in `docs/adr/` with the owner's words; a memory points at that record and never replaces it.

## Recall first

At session start, and before work on a topic earlier sessions may have touched:

```bash
scripts/memory.sh brief                 # most recent current facts
scripts/memory.sh recall r2 bucket      # full-text search over current facts
scripts/memory.sh about wp-0            # current facts about one entity
scripts/memory.sh history storage/table-format     # every value a slot has held
```

Results are JSON lines. Each names the agent and episode the fact came from; quote that evidence when you rely on a memory. When a memory conflicts with the repository, the repository wins: save a correction.

## Save before you finish

Save when the session produced something a later session needs and cannot find by reading the repo: an owner preference or ruling, a correction to an earlier memory, a gotcha that cost time, where some work stopped. Code structure, git history and anything already in a document stay out; the repo already holds them.

1. Run `scripts/memory.sh slots` and reuse an existing slot when the new fact answers the same question. A slot is `<entity>/<aspect>`, such as `storage/table-format` or `wp-0/status`. A slot holds one current fact; writing a new fact into it closes the old one and links the two, so a correction is just a new fact in the old slot.
2. Write one episode as JSON and pipe it in:

```bash
scripts/memory.sh remember - <<'JSON'
{
  "episode": {"id": "2026-11-27-codex-table-format", "session": "<session id or branch>",
              "agent": "codex", "kind": "finding", "at": "2026-11-27T10:00:00Z",
              "text": "Read ADR-0045 while planning the WP-0 storage probes."},
  "mentions": [{"key": "r2", "name": "Cloudflare R2"}, {"key": "adr-0045", "name": "ADR-0045"}],
  "facts": [
    {"id": "2026-11-27-codex-table-format-1", "slot": "storage/table-format",
     "text": "PPC tables are Delta Lake on Cloudflare R2, computed locally with DuckDB (ADR-0045).",
     "about": ["r2", "adr-0045"], "validFrom": "2026-11-27T00:00:00Z"}
  ]
}
JSON
```

- `agent` names the tool that wrote it (`claude-code`, `codex`, `cursor`, `gemini`, `kimi`, `pi`).
- `kind` is `decision`, `preference`, `correction`, `finding`, `handoff` or `tool_call`.
- `at` is the UTC time you learned it; `validFrom` (optional, defaults to `at`) is when it became true.
- Ids are stable and unique: date, agent and a short slug. Re-running the same episode changes nothing.
- Entity keys are lowercase and stable: `adr-0045`, `wp-0`, `r2`, `refinery-a`, `owner`, `file:scripts/check.sh`.
- Each fact is one self-contained sentence that names its source document when one exists.

The command validates the JSON before writing and prints `memory: saved episode …`. Run `scripts/memory.sh check` afterwards; it fails if a slot holds two current facts.

## What memory must hold

Memory is read by every agent, so it holds only what any agent may see. Secrets, tokens, credentials and anything from `evaluation/hidden/` stay out, as do values from the hidden canonical world; `AGENTS.md` keeps pipelines and agents away from them. PPC is fictional: a fact about PPC data says so.

## Serving memory over MCP

An agent that prefers tools to shell commands can read the store over MCP, read-only, beside the writers:

```bash
relate serve --mcp stdio --database "$(scripts/memory.sh path)" --read-only=live
```

Writes still go through `scripts/memory.sh remember`, so validation and supersession always run.
