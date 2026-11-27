---
status: Decided
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

The agent proposed the following under that request, and the owner approved it:

- Owner verbatim (2026-11-27): `"I approve the ADR-0058 choices. But since I use Dropbox all my agents will have access to the memmory. Also will this work for all agents working in this rpo?"`

Testing that question showed that Codex's workspace sandbox can read a store inside `.git` but cannot write to it. The owner then chose two options in a decision round on 2026-11-27. Each option is quoted as the owner selected it:

- Store location: `"Move to .relate-memory/ (Recommended)"`, which amends item 2.
- Dropbox: `"Sync it; one machine at a time (Recommended)"`, which adds item 5.

1. **One command for every agent.** `scripts/memory.sh` is the only way to write memory, and the usual way to read it. Any agent that can run a shell command can use it. The script checks each episode before it writes, writes it in one transaction, and retries when another agent holds the store's write lock. An agent that prefers MCP tools can also read the store through `relate serve --mcp stdio --read-only=live`.
2. **One store per clone, outside Git.** The store is a Relate directory store in the git-ignored `.relate-memory/` folder at the root of the main checkout. All worktrees of a clone share it, and Git never tracks it. A sandboxed agent that cannot write inside `.git` can still save there when the main checkout is in its workspace. An agent in a linked worktree outside the main checkout needs that folder added as a writable root. `PPC_MEMORY_DB` overrides the path. (Amended 2026-11-27: the store was first at `.git/relate-memory`.)
3. **The `relate-agent-memory` model, without embeddings.** The graph holds `Entity`, `Episode` and `Fact` nodes. Each fact has a slot, two time ranges and a link to its evidence. The latest fact written to a slot is its current fact. A full-text index over current facts serves recall. No embedding model is shared by all agents, so the store has no vector index.
4. **One skill, reached from every agent.** The skill lives at `.agents/skills/project-memory/SKILL.md`. `.claude/skills/project-memory/SKILL.md` is a symbolic link to that file. The link is to the file, because `scripts/tree-state.py` rejects directory links. `AGENTS.md` points to it, and `.gemini/settings.json` makes Gemini CLI read `AGENTS.md`. A Claude Code `SessionStart` hook prints the most recent facts when a session starts.
5. **Dropbox sync, one machine at a time.** Dropbox syncs the store to every machine, so agents on all of them read the same memory. Relate's writer lock holds only on one machine, so agents save from one machine at a time. `scripts/memory.sh` refuses to save, and `check` fails, when Dropbox has left conflicted copies in the store.

## Considered options

- **The blog's single `memory.rl` file in `~/.claude/memory/` with `Person`, `Object`, `Location` and `Event` labels.** Rejected. A single-file store lets only one process open it at a time. The location belongs to Claude Code, and the model keeps no evidence or corrections.
- **A store inside `.git`.** First chosen, then replaced. Codex's workspace sandbox blocks every write inside `.git`.
- **One store per machine, ignored by Dropbox.** Rejected by the owner. It removes the conflict risk, but machines no longer share memory.
- **A store committed to Git.** Rejected. Binary store files do not merge, and memory changes every session.
- **Vector recall.** Deferred until all agents share one embedding model.

## Consequences

- A memory supplements the record and never replaces it. Decisions stay on the record only in `docs/adr/` with the owner's words.
- Memory holds only what any agent may see. Secrets and anything from `evaluation/hidden/` stay out of it.
- Every machine that syncs this Dropbox folder shares the memory. When saves from two machines collide, Dropbox writes conflicted copies. Saves then stop until a person chooses which copy wins.
- `scripts/check.sh` runs `scripts/test_memory.py`. The tests skip where `relate` is not installed, which includes CI.
