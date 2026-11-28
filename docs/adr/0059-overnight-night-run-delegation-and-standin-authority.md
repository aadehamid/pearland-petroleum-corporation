---
status: Decided
date: 2026-11-27
amends: none
authority: Owner (Hamid Adesokan)
source_answers: docs/adr/answers/2026-11-27-night-run-delegation.md
---

# ADR-0059: Overnight night-run execution and owner stand-in delegation (Claude Fable 5.2 / Codex GPT 6.2 Astra)

## Context

On 2026-11-27, the PPC owner authorized an unsupervised overnight run (`night-run` + `/goal`) to execute `PPC-PLAN-001` work packages in sequence through the repository's normal pull-request, check, and independent-review loop. Under `way-of-working` and `night-run`, any delegation of owner decision authority must be recorded as an ADR quoting the owner's words before the first delegated decision relies on it. The verbatim 23:36 CST question, the full 23:39 CST draft brief, and all owner replies in chronological order are saved in [docs/adr/answers/2026-11-27-night-run-delegation.md](answers/2026-11-27-night-run-delegation.md).

## Decision

The owner (Hamid Adesokan) recorded the following instructions verbatim in [docs/adr/answers/2026-11-27-night-run-delegation.md](answers/2026-11-27-night-run-delegation.md):

1. At 23:36 CST:

   > once you complete this please continue working on the plan until complete.

2. At 23:37 CST:

   > /deep-research use for all your deep reserach. you will have to do some to gather information that will make the simluationa and synthetic data generation robuts. 
   > all api keys ypu need can be found in /Users/hamidadesokan/.config
   >
   > Yes to all by the way

3. At 23:44 CST (following the draft `night-run` brief presented at 23:39 CST):

   > /goal execute the approved PPC night-run brief.  please once you complete this continue to work the plan until done. Validation is important so make sure you validate everyhting that you did . Use the consistentcy skill to check things yourself before you send them for reviews . this will help you catch things before you set it out. 
   >
   > If you want anything you want me to decide on let Claude Fable 5.2 do it on my behalf. if for any reasons Claud Fable is not available. Use Codex GPT 6.2 Astra

## Considered options

- Pausing the overnight run whenever a decision arises during execution (not chosen; the owner named Claude Fable 5.2 to decide on his behalf, with Codex GPT 6.2 Astra if Claude Fable is not available, while the 23:39 CST brief keeps `PO-12a` owner sign-off and live LLM endpoint selection with the owner).
- Allowing the coding agent itself to decide open owner questions without an independent stand-in (not chosen; questions requiring an owner decision go to Claude Fable 5.2, or Codex GPT 6.2 Astra if unavailable).

## Consequences

- During this overnight run, questions that the coding agent needs decided on the owner's behalf (other than the two owner steps explicitly kept in the 23:39 CST brief) go to Claude Fable 5.2 (`claude -p --model fable --permission-mode plan`) as owner stand-in, falling back to Codex GPT 6.2 Astra (`codex`) only if Claude Fable 5.2 is unavailable.
- Each stand-in ruling is saved verbatim under `docs/adr/answers/` and recorded in an ADR marked `authority: Owner-delegated stand-in (...)` so the owner can review or reverse any delegated decision afterward.
- The two owner steps kept in the 23:39 CST brief remain with Hamid Adesokan: `PO-12a` owner sign-off at `WP-1` exit (log the independent benchmark report and continue unblocked work) and live LLM endpoint selection before `WP-3B` live-model wiring (do not start live LLM calls; offline recorded fixtures only).
- Every stop condition from the approved 23:39 CST brief remains in force verbatim: a question evidence cannot settle (escalated only to Claude Fable 5.2 or Codex GPT 6.2 Astra when an owner decision is needed, stopping if it remains unsettled), spending money or paid tiers, deleting remote data, rewriting `main`, any `after-merge.sh` refusal, `PO-12a` owner sign-off (log report and continue unblocked work), and live LLM endpoint choice before `WP-3B` live-model wiring (do not start live LLM calls; offline recorded fixtures only), plus the brief's instruction to never commit or print secrets from `/Users/hamidadesokan/.config`.
