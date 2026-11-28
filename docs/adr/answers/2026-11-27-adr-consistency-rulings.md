# Owner Answers — ADR Consistency Rulings (2026-11-27)

This file records the exact questions, recommendations, and verbatim owner answer from the 2026-11-27 ADR consistency decision round on branch `docs/settle-adr-inconsistencies`. File-scheme links from the chat message are rendered as repository paths or short ADR numbers; all question, recommendation, and owner answer wording is preserved verbatim.

## Round 1 (2026-11-27)

### Q1 — Frontmatter `amends:` versus index `clarifies` and `stages` (`ADR-0044`, `ADR-0045`, `ADR-0047`, `ADR-0051`)

**Question and recommendation:**
Keep the index and body verbs (`clarifies` and `stages`) for `ADR-0044`, `ADR-0045`, `ADR-0047`, and `ADR-0051`, and trim frontmatter `amends:` to true amendments only (10 findings). Recommended: yes. In all four files, the frontmatter placed clarified or staged targets under `amends:`, while both `docs/adr/README.md` and each ADR's own body state they are clarified or staged (`ADR-035` in `0044`, `ADR-018` in `0045`, `ADR-007`, `ADR-014`, `ADR-022`, and `ADR-023` in `0047`, and `ADR-003`, `ADR-004`, `ADR-010`, and `ADR-018` in `0051`). Trimming frontmatter `amends:` matches how `ADR-0040`–`0043`, `0049`, `0050`, `0052`, `0053`, and `0058` already work (`ADR-009` on `0044`, `ADR-017` on `0045`, and `none` on `0047` and `0051`).

### Q2 — `ADR-0055` relation to `ADR-0045` and `ADR-0048`

**Question and recommendation:**
Update `ADR-0055` so it amends `ADR-0051`, clarifies `ADR-0045`, and stages `ADR-0048` (2 findings). Recommended: yes. Right now `0055` lists `amends: ADR-0045, ADR-0048, ADR-0051` in its frontmatter and index row. Its own Consequences section and the target ADRs' status notes say it clarifies `ADR-0045` and stages `ADR-0048`, and the verbatim stand-in ruling in `2026-11-26-claude-fable-2-owner-standin.md` (`G2-b`) states "This stages ADR-0048 and does not reverse it." All sources already agree `ADR-0055` amends `ADR-0051`.

### Q3 — `ADR-0056` relation to `ADR-0043`, `ADR-0048`, and `ADR-0050`

**Question and recommendation:**
Update `ADR-0056` so it extends `ADR-0043`, `ADR-0048`, and `ADR-0050`, and fix `ADR-0048`'s index status to `Decided (staged by ADR-0055; extended by ADR-0056)` (3 findings). Recommended: yes. Right now `0056` lists `amends: ADR-0043, ADR-0048, ADR-0050` in its frontmatter and index row, while the post-review notes inside `0043`, `0048`, and `0050` all say `Extended by ADR-0056` because `ADR-0056` locks parameter ranges, thresholds, and tolerances without altering those decisions. For `ADR-0048`, the index status currently says `staged by ADR-0055, ADR-0056`, which disagrees with both `0048`'s body note (`Extended`) and `0056` (`Amends`), since `ADR-0056` does not stage any part of `ADR-0048`.

### Q4 — Add `adr_graph.py check` as a required gate in `scripts/check.sh`

**Question and recommendation:**
Add `python3 scripts/adr_graph.py check` as a required gate in `scripts/check.sh` once all 18 findings are resolved. Recommended: yes, in a separate follow-up PR right after the ADR cleanup PR merges (one concern per PR), or in the same PR if you prefer one PR.

### Owner verbatim response (2026-11-27 23:37 CST)

> Yes to all by the way
