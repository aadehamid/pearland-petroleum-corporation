# Owner Answers — ADR Consistency Rulings (2026-11-27)

This file records the exact reconciliation round presented to the owner and the owner's verbatim answer on branch `docs/settle-adr-inconsistencies`. File-scheme links from the chat message are rendered as repository paths or short ADR numbers; all question, recommendation, and owner answer wording is preserved verbatim.

## Evidence-settled omissions presented before Q1–Q4 (3 findings, no conflicting sources)

The following paragraph was presented to the owner in the same message, ahead of Q1–Q4:

> Three of the 18 findings are simple omissions where no two sources disagree, so I will fix them in the PR once your rulings below are in. First, `ADR-0047`'s status in `docs/adr/README.md` omits `(extended by ADR-0052)` even though `ADR-0052`'s index row and the note inside `docs/adr/0047-slice1-active-core-vs-staged-apps.md` already agree. Second, `docs/adr/0048-pyomo-optimization-and-langgraph-pydantic-agents.md` has no `amends:` line in its frontmatter even though its body, Round 2 Q13, and the index all agree it amends `PPC-011` and `PPC-012` (2 findings).

Supporting repository evidence already on `main`:
- `ADR-0047`: `docs/adr/README.md` row `ADR-0052` states `Amends ADR-014; extends ADR-0047`, and `docs/adr/0047-slice1-active-core-vs-staged-apps.md` line 25 records that `ADR-0052` decided the Relate WASM Slice 1.5 promotion.
- `ADR-0048`: `docs/adr/README.md` row `ADR-0048` states `Amends PPC-011, PPC-012`, `docs/adr/0048-pyomo-optimization-and-langgraph-pydantic-agents.md` Context/Decision/Consequences specify replacing OR-Tools (`PPC-011`) and updating LangGraph/Pydantic/OTel/Langfuse (`PPC-012`), and `docs/adr/answers/2026-11-26-first-principles-grill.md` Round 2 Q13 records the owner's acceptance.

## Round 1 (2026-11-27)

### Q1 — Frontmatter `amends:` versus index `clarifies` and `stages` (`ADR-0044`, `ADR-0045`, `ADR-0047`, `ADR-0051`)

**Question and recommendation (verbatim):**
Keep the index and body verbs (`clarifies` and `stages`) for `ADR-0044`, `ADR-0045`, `ADR-0047`, and `ADR-0051`, and trim frontmatter `amends:` to true amendments only (10 findings). Recommended: yes. In all four files, the frontmatter placed clarified or staged targets under `amends:`, while both `docs/adr/README.md` and each ADR's own body state they are clarified or staged (`ADR-035` in `0044`, `ADR-018` in `0045`, `ADR-007`, `ADR-014`, `ADR-022`, and `ADR-023` in `0047`, and `ADR-003`, `ADR-004`, `ADR-010`, and `ADR-018` in `0051`). Trimming frontmatter `amends:` matches how `ADR-0040`–`0043`, `0049`, `0050`, `0052`, `0053`, and `0058` already work (`ADR-009` on `0044`, `ADR-017` on `0045`, and `none` on `0047` and `0051`).

**Agent correction note (2026-11-27, agent's own note, not the owner's words):**
Independent review caught an inaccuracy in the parenthetical above for `ADR-0051`. `docs/adr/0051-exe-dev-r2-databricks-hosting-and-recovery.md` discusses Cloudflare R2, Neo4j Community, and Databricks consistently with `ADR-003`, `ADR-004`, `ADR-010`, and `ADR-018`, but its body does not cite those four ADR IDs by name; `docs/adr/README.md` (`Clarifies ADR-003, ADR-004, ADR-010, ADR-018`) is the record that states the clarification links. The approved outcome (`amends: none` in `0051` frontmatter) is unchanged.

### Q2 — `ADR-0055` relation to `ADR-0045` and `ADR-0048`

**Question and recommendation (verbatim):**
Update `ADR-0055` so it amends `ADR-0051`, clarifies `ADR-0045`, and stages `ADR-0048` (2 findings). Recommended: yes. Right now `0055` lists `amends: ADR-0045, ADR-0048, ADR-0051` in its frontmatter and index row. Its own Consequences section and the target ADRs' status notes say it clarifies `ADR-0045` and stages `ADR-0048`, and the verbatim stand-in ruling in `2026-11-26-claude-fable-2-owner-standin.md` (`G2-b`) states "This stages ADR-0048 and does not reverse it." All sources already agree `ADR-0055` amends `ADR-0051`.

### Q3 — `ADR-0056` relation to `ADR-0043`, `ADR-0048`, and `ADR-0050`

**Question and recommendation (verbatim):**
Update `ADR-0056` so it extends `ADR-0043`, `ADR-0048`, and `ADR-0050`, and fix `ADR-0048`'s index status to `Decided (staged by ADR-0055; extended by ADR-0056)` (3 findings). Recommended: yes. Right now `0056` lists `amends: ADR-0043, ADR-0048, ADR-0050` in its frontmatter and index row, while the post-review notes inside `0043`, `0048`, and `0050` all say `Extended by ADR-0056` because `ADR-0056` locks parameter ranges, thresholds, and tolerances without altering those decisions. For `ADR-0048`, the index status currently says `staged by ADR-0055, ADR-0056`, which disagrees with both `0048`'s body note (`Extended`) and `0056` (`Amends`), since `ADR-0056` does not stage any part of `ADR-0048`.

### Q4 — Add `adr_graph.py check` as a required gate in `scripts/check.sh`

**Question and recommendation (verbatim):**
Add `python3 scripts/adr_graph.py check` as a required gate in `scripts/check.sh` once all 18 findings are resolved. Recommended: yes, in a separate follow-up PR right after the ADR cleanup PR merges (one concern per PR), or in the same PR if you prefer one PR.

### Owner verbatim response (2026-11-27 23:37 CST)

> Yes to all by the way
