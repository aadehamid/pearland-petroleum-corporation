---
status: Proposed
date: 2026-11-27
amends: none
authority: Owner (Hamid Adesokan)
---

# ADR-0058: Shared Relate project memory for all coding agents

## Context

Coding agents lose what they learn when a session ends. Several agents work on this repository: Claude Code, Codex, Cursor, Gemini, Kimi and Pi. A note one agent keeps in its own memory folder is invisible to the others.

Relate is an embedded Cypher graph database with a single-binary command line. The Neo4j GraphAcademy post "Give Claude Code a memory with Relate" (Adam Cowley, 2026-11-12) shows how to use it as agent memory. Relate also publishes the `relate-agent-memory` model. In that model, facts link to the episode they came from, and a correction closes the old fact instead of deleting it.

## Decision

The owner asked for this on 2026-11-27:

- Owner verbatim (2026-11-27): `"Can you set up Relate for this project? https://graphacademy.neo4j.com/blog/give-claude-code-a-memory-with-relate Even though this is for Claude code. All agents must be able to use the relate that you set up"`

The agent proposes the following under that request. This record stays Proposed until the owner approves these choices in the pull request that adds it.

1. **One command for every agent.** `scripts/memory.sh` is the only way to write memory, and the usual way to read it. Any agent that can run a shell command can use it. The script checks each episode before it writes, writes it in one transaction, and retries when another agent holds the store's write lock. An agent that prefers MCP tools can also read the store through `relate serve --mcp stdio --read-only=live`.
2. **One store per clone, outside Git.** The store is a Relate directory store at `<git common dir>/relate-memory`. All worktrees of a clone share it, and Git never tracks it. `PPC_MEMORY_DB` overrides the path.
3. **The `relate-agent-memory` model, without embeddings.** The graph holds `Entity`, `Episode` and `Fact` nodes. Each fact has a slot, two time ranges and a link to its evidence. The latest fact written to a slot is its current fact. A full-text index over current facts serves recall. No embedding model is shared by all agents, so the store has no vector index.
4. **One skill, reached from every agent.** The skill lives at `.agents/skills/project-memory/SKILL.md`. `.claude/skills/project-memory/SKILL.md` is a symbolic link to that file. The link is to the file, because `scripts/tree-state.py` rejects directory links. `AGENTS.md` points to it, and `.gemini/settings.json` makes Gemini CLI read `AGENTS.md`. A Claude Code `SessionStart` hook prints the most recent facts when a session starts.

## Considered options

- **The blog's single `memory.rl` file in `~/.claude/memory/` with `Person`, `Object`, `Location` and `Event` labels.** Rejected. A single-file store lets only one process open it at a time. The location belongs to Claude Code, and the model keeps no evidence or corrections.
- **A store committed to Git.** Rejected. Binary store files do not merge, and memory changes every session.
- **Vector recall.** Deferred until all agents share one embedding model.

## Consequences

- A memory supplements the record and never replaces it. Decisions stay on the record only in `docs/adr/` with the owner's words.
- Memory holds only what any agent may see. Secrets and anything from `evaluation/hidden/` stay out of it.
- Each clone has its own memory. A second machine starts with an empty store.
- `scripts/check.sh` runs `scripts/test_memory.py`. The tests skip where `relate` is not installed, which includes CI.
