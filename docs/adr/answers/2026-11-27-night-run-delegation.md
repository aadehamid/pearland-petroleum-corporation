# Owner Answers — Overnight Night-Run Execution and Stand-In Delegation (2026-11-27)

This file records, in chronological order, the owner's instructions and the exact draft `night-run` brief presented to the owner on 2026-11-27 before launching the overnight run of `PPC-PLAN-001`.

## 1. Owner prompt at 23:36 CST (plan continuation)

> once you complete this please continue working on the plan until complete.

## 2. Owner prompt at 23:37 CST (deep research, API keys, and confirmation of ADR Q1–Q4 plus plan sequence)

In reply to the agent's 23:36 CST question asking whether the owner accepted ADR consistency questions 1–4 and the proposed sequence (rebase and ship WP-0, propose the physical-model consistency graph before WP-1, and continue through the plan while stopping at owner gates):

> /deep-research use for all your deep reserach. you will have to do some to gather information that will make the simluationa and synthetic data generation robuts. 
> all api keys ypu need can be found in /Users/hamidadesokan/.config
>
> Yes to all by the way

## 3. Draft `night-run` brief presented at 23:39 CST

In reply to the owner asking `"How can you work the plan autonomously. I am about to head to bed. can we set the plan as the goal?"`, the agent presented this exact draft brief for approval:

```markdown
# Night run brief, pearland-petroleum-corporation, 2026-11-27

Permission (owner's words): "<to be filled from your approval reply>"
Goal (owner's words): "once you complete this please continue working on the plan until complete." + "/deep-research use for all your deep reserach. you will have to do some to gather information that will make the simluationa and synthetic data generation robuts. all api keys ypu need can be found in /Users/hamidadesokan/.config"

Done means:
1. `python3 scripts/adr_graph.py check` exits 0 on `main` and runs as a required gate in `scripts/check.sh`.
2. An ADR recording this overnight delegation is merged on `main` before any delegated decision is made.
3. WP-0 (`feat/wp0-schemas-pins-probes`) is rebased onto `main`, passes `scripts/check.sh`, independent review, and PR review, and merges into `main`.
4. A primary-sourced `deep-research` report supporting Refinery A v1 physics, crude assays, public feeds (EIA, NOAA, EPA, PHMSA), and synthetic data calibration is saved in the session artifacts directory and cited in WP-1.
5. A PPC physical-model consistency graph built with `consistency-graph` (checking facilities, equipment, streams, EPM KPI provenance, classification tags, and hidden-truth isolation) is merged on `main`, exits 0, and runs in `scripts/check.sh`.
6. WP-1 (public data ingest, `refinery_a_design_basis.yaml`, `CFG-0` + DEXPI source, `refinery_a_ot_tags.yaml`, commercial world, deterministic `EQ-01`–`EQ-08` kernel, Quint/Z3/Hypothesis suites, and an independent `PO-12a` benchmark report) is merged on `main` with all automated suites passing, ready for your `PO-12a` sign-off.
7. Every subsequent unblocked work package (`WP-4A` local/Docker parity and backup drills, `WP-2`, `WP-3A`, `WP-3`) is shipped in order through the PR loop until complete or blocked by a stop condition, with all decisions, merged PRs, and remaining owner gates logged in the morning summary.

Owner's steps after the run:
1. Review and sign off the independent `PO-12a` benchmark report at WP-1 exit (`ADR-0056` `G3-d`).
2. Choose the live LLM endpoint before `WP-3B` live-model wiring (`PPC-PLAN-001` §2).
3. Review any decisions marked as made under the delegation (all reversible).

Target: `pearland-petroleum-corporation` (`origin/main`) on this macOS arm64 machine, Cloudflare R2 (`pearland-petroleum-corp` and `pearland-petroleum-hidden` using `/Users/hamidadesokan/.config/ppc/`), Databricks Free Edition, and local 12 GB Docker Compose parity (`ADR-0055`).

Order:
1. Merge ADR cleanup PR (`docs/settle-adr-inconsistencies`, currently in check + Pi review)
2. Merge overnight delegation ADR PR
3. Merge `adr_graph.py check` gate PR in `scripts/check.sh`
4. Rebase, review, and merge WP-0 (`feat/wp0-schemas-pins-probes`)
5. Run `deep-research` for WP-1 physics, assays, and public feeds
6. Build and merge PPC physical-model consistency graph and wire into `scripts/check.sh`
7. Build, verify, and merge WP-1 (including independent `PO-12a` benchmark report)
8. Continue through `WP-4A`, `WP-2`, `WP-3A`, and `WP-3` in PR-sized steps until complete or blocked

Decisions (delegation):
  Decide implementation details and approve the physical-model consistency graph design from evidence in this order:
  1. Recorded, approved ADRs (`PPC-REG-001` and `docs/adr/`).
  2. PPC architecture documents ranked by `README.md`.
  3. Primary sources verified via `deep-research`.
  4. Verified external primary sources.
  Every delegated decision is recorded in its ADR/record and logged so you can reverse it.

Reviewers: default `way-of-working` table (`changing.md`) — Cursor bot as PR reviewer (20-minute wait, Pi stand-in if unavailable), Pi (`pi-review.sh --role independent`) as independent reviewer because I am Gemini/Antigravity.
Merge rule: default — check green, CI green, every independent-review finding resolved, MERGE verdict on latest push from a different tool.
Check command: `./scripts/check.sh`
Remote and default branch: `origin` and `main`
Brief: `/Users/hamidadesokan/.gemini/antigravity-cli/brain/9eb5f098-f332-4b5f-8ff6-f7b300a26530/scratch/night-run-brief.md`
Log: `/Users/hamidadesokan/.gemini/antigravity-cli/brain/9eb5f098-f332-4b5f-8ff6-f7b300a26530/scratch/night-run-log.md`
Stop conditions: a question evidence cannot settle; spending money or paid tiers; deleting remote data; rewriting `main`; any `after-merge.sh` refusal; `PO-12a` owner sign-off (log report and continue unblocked work); live LLM endpoint choice before `WP-3B` live-model wiring (do not start live LLM calls; offline recorded fixtures only).
Owner's other instructions: "use /deep-research for all deep research; API keys are in /Users/hamidadesokan/.config; never commit or print secrets; save decisions and findings to PPC shared memory."
```

## 4. Owner approval and stand-in delegation at 23:44 CST

> /goal execute the approved PPC night-run brief.  please once you complete this continue to work the plan until done. Validation is important so make sure you validate everyhting that you did . Use the consistentcy skill to check things yourself before you send them for reviews . this will help you catch things before you set it out. 
>
> If you want anything you want me to decide on let Claude Fable 5.2 do it on my behalf. if for any reasons Claud Fable is not available. Use Codex GPT 6.2 Astra
