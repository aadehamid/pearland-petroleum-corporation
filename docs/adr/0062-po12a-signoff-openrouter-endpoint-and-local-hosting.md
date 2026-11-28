---
status: Decided
date: 2026-11-28
amends: ADR-0055, ADR-0056
authority: Owner (Hamid Adesokan)
source_answers: docs/adr/answers/2026-11-28-owner-po12a-llm-and-hosting-decisions.md
---

# ADR-0062: PO-12a sign-off, restated plant C3+ gain criterion, OpenRouter `thinkingmachines/inkling-small` endpoint, and local Docker Compose hosting

## Context

The overnight execution under [ADR-0059](0059-overnight-night-run-delegation-and-standin-authority.md) merged the offline-executable portions of `WP-0`, `WP-1`, `WP-2`, `WP-3`, `WP-3A`, `WP-3B`, `WP-4A`, `WP-5`, `WP-5B`, `WP-6`, `WP-8A` (in-process parity harness), and `WP-8B` on `main` (`dbc2d5a`), leaving three owner decisions open alongside deferred live/cloud items (`WP-8A` live Databricks sync, `WP-7`, and a CI Quint runner):

1. `PO-12a` owner sign-off on [PPC-REVIEW-005](../enterprise-architecture/independent-review/PPC-REVIEW-005_PO-12a_Refinery_A_Empirical_Plausibility_Benchmark_Report.md), which reported unit and conservation checks passing across all five operating modes, plant C5+ volumetric gain of `-3.48%` to `-4.98%` and plant C3+ volumetric gain of `+3.00%` to `+3.99%` against the original `+4%` to `+10%` `PO-12a` plant C5+ band, and high-severity (`532 °C`, `7.0` catalyst-to-oil) FCC gas yield of `22.09 wt%` against the `16` to `22 wt%` range in [ADR-0056](0056-identity-steward-action-thresholds-and-refinery-a-parameters.md).
2. Live LLM endpoint selection for `WP-3B` ([ADR-0055](0055-slice1-hosting-observability-postgres-workflow-and-databricks-sync.md), [ADR-0059](0059-overnight-night-run-delegation-and-standin-authority.md)).
3. Hosting choice for `WP-4B` Slice 1 integration. Checking live `exe.dev` account state on 2026-11-28 (`ssh exe.dev billing plan` and `ssh exe.dev ls --json`) showed the owner's active `$15/month` Personal plan provides `2 vCPUs` and `4 GB` RAM shared across all VMs (with five existing VMs running), and Personal tiers scale in `4 GB` (`$15/month`), `8 GB` (`$35/month`), and `16 GB` (`$75/month`) steps rather than `12 GB`. Checking local Mac Docker on 2026-11-28 (`docker info --format '{{.ServerVersion}}'`) confirmed Docker `29.8.2` is available locally. Checking `~/.config/openrouter/openrouter.env` key names on 2026-11-28 confirmed the OpenRouter credentials file exists locally.

The full questions, recommendations, and owner replies are saved verbatim in [docs/adr/answers/2026-11-28-owner-po12a-llm-and-hosting-decisions.md](answers/2026-11-28-owner-po12a-llm-and-hosting-decisions.md).

## Decision

The owner (Hamid Adesokan) recorded two verbatim replies on 2026-11-28:

1. At 05:04 CST, accepting the agent's recommendations for items 1 through 3 and specifying the model for item 4:

   > Yes to all your recommendation. comments below:
   > 4. use this model with the openrouter key in ~/.config >> model: "thinkingmachines/inkling-small",
   > 5. can we host 12GB on exe.dev

   The accepted recommendations for items 1 through 3 are:
   - **Item 1 (`PPC-REVIEW-005` Decision 1):** "I recommend option A. Restate the `PO-12a` plant gain criterion in an ADR to match the actual v1 flowsheet basis (for example, plant C3+ volumetric gain of +2.5% to +4.5%, plus a registered unit-level HCU C5+ gain band of +4% to +10% that is currently only in code)."
   - **Item 2 (`PPC-REVIEW-005` Decision 2):** "I recommend option 1 (accept 22.09 wt% as expected above nominal severity, and add FCC yield checks to the benchmark gate so future drift is caught)."
   - **Item 3 (`PPC-REVIEW-005` sign-off):** "I recommend accepting PPC-REVIEW-005 with conditions for v1 synthetic qualification, or telling me if you want to hold `PO-12a` open until you or a human process engineer reviews the numbers."

2. At 05:16 CST, accepting the agent's local hosting recommendation for item 5:

   > lets go with your recommendation of a local hosting.

   The accepted recommendation for item 5 is:
   - "Run Docker Compose locally on your Mac for $0 extra while we finish qualification and keep your current $15 per month `exe.dev` plan untouched."

Items from the item 5 table that the owner did not address (live Databricks Free Edition sync in `WP-8A`, NOAA hurricane regression in `WP-7`, and adding a Quint runner to CI) remain **not decided** and open.

## Considered options

- **PO-12a plant volumetric gain:** Option B (reopen `ADR-0054` or `ADR-0056` and change the flowsheet or locked parameters) and Option C (keep the `+4%` to `+10%` C5+ band and record a v1 deviation) were not chosen.
- **High-severity FCC gas yield (`22.09 wt%` at `532 °C` / `7.0` CTO):** Option 2 (widen the `ADR-0056` nominal gas yield range) and Option 3 (recalibrate the FCC kinetic constants) were not chosen.
- **Live LLM endpoint:** Keeping `WP-3B` offline-only or selecting another provider was not chosen; OpenRouter with `"thinkingmachines/inkling-small"` was chosen.
- **Slice 1 hosting:** Upgrading `exe.dev` to `8 GB` (`$35/month`) or `16 GB` (`$75/month`), moving stateful databases to Cloudflare Containers (`~$790/month` 24/7 with ephemeral disks), splitting Postgres onto Neon with Neo4j Aura, or provisioning a new cloud VPS (Hetzner EU `CAX31`, Netcup, Oracle Cloud Always Free) were not chosen for the qualification stage.

## Evidence

- Independent `PO-12a` benchmark report: [PPC-REVIEW-005](../enterprise-architecture/independent-review/PPC-REVIEW-005_PO-12a_Refinery_A_Empirical_Plausibility_Benchmark_Report.md) (against merged commit `88f5fe4`).
- External state readings (2026-11-28):
  - `ssh exe.dev billing plan`: Personal Plan `$15/month`, `2 vCPUs` and `4 GB` RAM shared across all VMs.
  - `docker info --format '{{.ServerVersion}}'`: `29.8.2` running locally on macOS.
  - `grep -oE '^[A-Za-z_][A-Za-z0-9_]*=' ~/.config/openrouter/openrouter.env`: confirmed credential file present locally (`DECIDER_API_KEY`, `DECIDER_URL`, `DECIDER_MODEL`, `REASON_MODEL`; values never read into repo files or logs).

## Consequences

- [ADR-0056](0056-identity-steward-action-thresholds-and-refinery-a-parameters.md) is amended to restate the `PO-12a` plant volumetric gain criterion to plant C3+ volumetric gain `+2.5%` to `+4.5%` alongside formally registering the unit-level HCU C5+ liquid volume gain band of `+4%` to `+10%`, accept the `22.09 wt%` FCC gas yield at the `532 °C` / `7.0` CTO holdout point as expected above nominal severity, and record Hamid Adesokan's conditional acceptance of [PPC-REVIEW-005](../enterprise-architecture/independent-review/PPC-REVIEW-005_PO-12a_Refinery_A_Empirical_Plausibility_Benchmark_Report.md) for v1 synthetic qualification (conditioned on implementing the three non-physics benchmark follow-ups in `PPC-REVIEW-005` Section 6 plus updating the benchmark gate with the restated `ADR-0062` gain bands from Decision 1 Option A in a follow-up code PR).
- [ADR-0055](0055-slice1-hosting-observability-postgres-workflow-and-databricks-sync.md) is amended so Slice 1 qualification runs on local Mac Docker Compose (`infra/docker-compose.yml`) at `$0` extra spend while keeping the existing `$15/month` `exe.dev` plan untouched and Cloudflare R2 as the durable tier; cloud VM provisioning (`exe.dev` `8 GB`/`16 GB` or Hetzner EU `CAX31`) is deferred until an always-on remote host is needed.
- [ADR-0059](0059-overnight-night-run-delegation-and-standin-authority.md) is clarified to note that the two owner gates reserved there (`PO-12a` sign-off and `WP-3B` live LLM endpoint selection) are now decided.
- `WP-3B` adds an OpenRouter live agent adapter targeting `"thinkingmachines/inkling-small"` using the runtime OpenRouter credentials in `~/.config/openrouter/openrouter.env` (never committed or logged), while `RecordedResponseAgentAdapter` remains the deterministic offline default in `scripts/check.sh`.
- Future work packages not addressed in this round (live Databricks `WP-8A` sync, `WP-7` NOAA hurricane regression, and CI Quint runner) remain open for separate owner confirmation.
