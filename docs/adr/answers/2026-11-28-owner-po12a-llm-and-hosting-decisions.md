# Owner Answers — PO-12a Sign-Off, Live LLM Endpoint, and Local Hosting (2026-11-28)

This file records, in chronological order, the agent's questions and recommendations and the owner's verbatim replies on 2026-11-28 closing out `PO-12a`, selecting the live `WP-3B` LLM endpoint, and choosing local Docker Compose hosting during qualification. Local Markdown file links (`file://...`) in agent questions are stripped to plain paths; all other words are verbatim.

## 1. Decision round presented at 04:55 CST and owner reply at 05:04 CST

**Owner prompt (04:55 CST, verbatim):**

> what do you need my decisions on?

**Agent decision round (04:55 CST, verbatim with `file://` links stripped to plain names):**

> I need five decisions from you to close out `PO-12a` and move from offline in-process tests to live deployment. Three belong to the PPC-REVIEW-005 sign-off table, one picks the live LLM endpoint for `WP-3B`, and one authorizes live infrastructure work.
>
> 1. Plant volumetric gain criterion (`PPC-REVIEW-005` Decision 1)
>
> `PO-12a` currently asks for a plant C5+ volumetric gain of +4% to +10%. The merged Refinery A kernel produces -3.48% to -4.98% for plant C5+ gain and +3.00% to +3.99% for plant C3+ gain because Refinery A v1 has no delayed coker and loses C5+ liquid volume in the crude LPG cut, reformer, and FCC.
>
> I recommend option A. Restate the `PO-12a` plant gain criterion in an ADR to match the actual v1 flowsheet basis (for example, plant C3+ volumetric gain of +2.5% to +4.5%, plus a registered unit-level HCU C5+ gain band of +4% to +10% that is currently only in code). Your other options are option B (reopen `ADR-0054` or `ADR-0056` and change the flowsheet or locked parameters) or option C (keep the +4% to +10% C5+ band and record a v1 deviation).
>
> 2. High-severity FCC gas yield (`PPC-REVIEW-005` Decision 2)
>
> At the 532 °C, 7.0 catalyst-to-oil holdout point, FCC gas yield reaches 22.09 wt% against the 16 to 22 wt% range in ADR-0056. The four 525 °C modes sit inside the range at 20.58 wt%.
>
> I recommend option 1 (accept 22.09 wt% as expected above nominal severity, and add FCC yield checks to the benchmark gate so future drift is caught). Your other options are option 2 (widen the `ADR-0056` gas yield range in an ADR) or option 3 (recalibrate the FCC kinetic constants).
>
> 3. Process-engineering reviewer disposition (`PPC-REVIEW-005` sign-off)
>
> ADR-0056 `G3-d` calls for a benchmark report prepared by a process-engineering reviewer who did not write the kernel. Claude Fable 5.2 wrote PPC-REVIEW-005 independently of the coding session, and its section 2 notes that an AI model is not a human process engineer and did not cross-check primary editions of Gary–Handwerk, Maples, or GPSA.
>
> I recommend accepting PPC-REVIEW-005 with conditions for v1 synthetic qualification, or telling me if you want to hold `PO-12a` open until you or a human process engineer reviews the numbers.
>
> 4. Live LLM endpoint for `WP-3B`
>
> All `WP-3B` and `WP-5` agent tests currently run on committed offline fixtures in `scn_a_t125_recorded.json` because ADR-0059 reserves paid model selection for you.
>
> Please tell me which provider and model you want wired into `WP-3B` (for example, Anthropic Claude, OpenAI, or Gemini using the API keys in `/Users/hamidadesokan/.config`), or tell me to keep `WP-3B` in offline fixture mode for now.
>
> 5. Live infrastructure and remaining work packages
>
> The remaining items in PPC-PLAN-001 involve live hosting, cloud resources, or manual steps that were outside the overnight brief. Please tell me which of these you want to authorize next.
> - Provision the 12 GB `exe.dev` VM (`WP-4B`)
> - Wire live Databricks Free Edition sync (`WP-8A`)
> - Implement the NOAA hurricane regression (`WP-7`)
> - Add a Quint runner to CI
>
> You can reply with your choices in one line (for example, "1A with C3+ 2.5-4.5% and HCU 4-10%, 2.1, accept PPC-REVIEW-005 for v1, use X for WP-3B, and start Y next"), and I will record the ADR and sign-off updates before continuing.

**Owner verbatim reply (05:04 CST):**

> Yes to all your recommendation. comments below:
> 4. use this model with the openrouter key in ~/.config >> model: "thinkingmachines/inkling-small",
> 5. can we host 12GB on exe.dev

## 2. Hosting follow-up and owner decision at 05:16 CST

Following live account inspection (`ssh exe.dev billing plan` on 2026-11-28 showing the active $15/month Personal plan has 2 vCPUs and 4 GB RAM shared across all VMs, with Personal tiers in 4 GB / 8 GB / 16 GB steps) and owner questions comparing Cloudflare Containers (`05:09 CST`: `"should we use cloudfare for #5? What will that cost us? and how will that change the plan?"`) and Neon / alternative VPS hosts (`05:12 CST`: `"what about Neon or other hosting options may be cheaper"`), the agent gave the following recommendation at 05:14 CST:

**Agent recommendation (05:14 CST, verbatim):**

> Run Docker Compose locally on your Mac for $0 extra while we finish qualification and keep your current $15 per month `exe.dev` plan untouched. When you are ready for an always-on cloud VM for the full 12 GB stack, Hetzner EU `CAX31` (~$24 per month) is the cheapest clean drop-in, and `exe.dev` 8 GB ($35 per month) is the simplest option with no new vendor.
>
> Which option do you want for #5, and should I start implementing your approved Decisions 1 through 4 now?

**Owner verbatim reply (05:16 CST):**

> lets go with your recommendation of a local hosting.
