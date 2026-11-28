---
status: Decided
date: 2026-11-27
amends: none
authority: Owner (Hamid Adesokan)
source_answers: docs/adr/answers/2026-11-27-night-run-delegation.md
---

# ADR-0059: Overnight night-run execution and owner stand-in delegation (Claude Fable 5.2 / Codex GPT 6.2 Astra)

## Context

On 2026-11-27, the PPC owner authorized an unsupervised overnight run (`night-run` + `/goal`) to execute `PPC-PLAN-001` work packages in sequence through the repository's normal pull-request, check, and independent-review loop. Under `way-of-working` and `night-run`, any delegation of owner decision authority must be recorded as an ADR quoting the owner's words before the first delegated decision relies on it.

## Decision

The owner (Hamid Adesokan) recorded the following instructions verbatim in [docs/adr/answers/2026-11-27-night-run-delegation.md](answers/2026-11-27-night-run-delegation.md):

- Execution and validation: `"/goal execute the approved PPC night-run brief.  please once you complete this continue to work the plan until done. Validation is important so make sure you validate everyhting that you did . Use the consistentcy skill to check things yourself before you send them for reviews . this will help you catch things before you set it out."`
- Deep research and credentials location: `"/deep-research use for all your deep reserach. you will have to do some to gather information that will make the simluationa and synthetic data generation robuts. all api keys ypu need can be found in /Users/hamidadesokan/.config"`
- Stand-in decision authority: `"If you want anything you want me to decide on let Claude Fable 5.2 do it on my behalf. if for any reasons Claud Fable is not available. Use Codex GPT 6.2 Astra"`

## Considered options

- Pausing the overnight run whenever an owner-level ruling or design approval arises (rejected by the owner in favor of delegating decisions to Claude Fable 5.2, with Codex GPT 6.2 Astra as fallback).
- Allowing the coding agent itself to decide open owner questions without an independent stand-in (rejected to preserve separation between the implementer and the owner's stand-in decision maker).

## Consequences

- Every owner-level decision or sign-off required during this run is presented to Claude Fable 5.2 (`claude -p --model fable --permission-mode plan`) as owner stand-in, falling back to Codex GPT 6.2 Astra (`codex`) only if Claude Fable 5.2 is unavailable.
- Each stand-in ruling is saved verbatim under `docs/adr/answers/` and recorded in an ADR marked `authority: Owner-delegated stand-in (...)` so the owner can review or reverse any delegated decision afterward.
- Hard stop conditions remain in force regardless of delegation: no paid commercial tiers or spending money without authorization, no deletion of remote data or buckets, no history rewrites on `main`, and no committing or printing of secrets from `/Users/hamidadesokan/.config`.
