---
status: Decided
date: 2026-11-27
amends: ADR-003, ADR-0053
authority: Owner (Hamid Adesokan)
---

# ADR-0057: Two-bucket R2 isolation for hidden canonical truth and retirement of legacy `lagos-chem-l0` bucket

## Context

`ADR-003` (`docs/PPC-REG-001_Architecture_Decision_Register.md`) established one Cloudflare R2 bucket per project, while `ADR-028`, `ADR-0053`, `PPC-013`, `PPC-016`, and `PPC-PLAN-001` (`WP-0`) require separate restricted credentials for `evaluation/hidden/` so operational pipelines and AI agents fail with a real storage-level access denial when attempting to read hidden canonical truth. Static Cloudflare R2 API tokens restrict access at the bucket boundary rather than by object prefix inside one bucket.

Separately, during the `WP-0` read-only R2 inventory on 2026-11-27, the Cloudflare R2 account contained only one pre-existing bucket, `lagos-chem-l0` (18 objects, 2,744,948,808 bytes), created before the PPC first-principles world model existed. `ADR-0053` originally quarantined pre-world-model R2 objects until `WP-1` passed.

## Decision

The PPC owner (Hamid Adesokan) decided both items on 2026-11-27 during `WP-0` execution:

1. **Two-bucket R2 isolation for hidden truth (Option A, clarifying `ADR-003`):**
   - Owner verbatim (2026-11-27): `"3. Option A"` (accepting Option A: a separate restricted R2 bucket for hidden truth with its own bucket-scoped API token, documented as an ADR clarifying `ADR-003`).
   - Operational PPC storage uses bucket `pearland-petroleum-corp` (`raw/`, `delta/`, `cache/`, `manifests/`, `telemetry/otel/`, `exports/world_bundle/observable/`, `models/`, `fixtures/`, `_probe/`), accessed through a bucket-scoped operational token (`~/.config/ppc/r2-standard.env`).
   - Hidden canonical truth and blind evaluation scoring keys use a separate restricted bucket `pearland-petroleum-hidden` (`evaluation/hidden/world_version=.../`, `evaluation/hidden/world_bundle/.../`, `evaluation/hidden/_probe/`), accessed exclusively through a separate bucket-scoped hidden-truth token (`~/.config/ppc/r2-hidden.env`).
   - Operational and hidden-truth credentials live in separate secret files outside Git and never share one `.env` file. Bidirectional `HTTP 403 AccessDenied` enforcement is verified in `WP-0`.

2. **Pre-deletion inventory and retirement of `lagos-chem-l0` (amending `ADR-0053`):**
   - Owner verbatim (2026-11-27): `"On item 2, I think we can delete lagos-chem-l0 this was done when we were not considering the whole system"`
   - Before deletion, all 18 objects in `lagos-chem-l0` (keys, byte sizes, ETags, and last-modified UTC timestamps totaling 2,744,948,808 bytes) were recorded in `infra/r2/legacy_pre_world_model_inventory.json` under label `LEGACY_PRE_WORLD_MODEL`. After verifying the inventory, the 18 objects and `lagos-chem-l0` bucket were retired on 2026-11-27, leaving only `pearland-petroleum-corp` and `pearland-petroleum-hidden` in the Cloudflare R2 account.

## Considered options

- **Single PPC bucket with Cloudflare R2 prefix-scoped Temporary Access Credentials (Option B):** Rejected in favor of Option A because temporary tokens expire (`ttlSeconds`) and require a parent credential-minting service holding broader account permissions, whereas two bucket-scoped static tokens give direct, stateless storage-level isolation.
- **Keeping `lagos-chem-l0` quarantined until `WP-1` exit:** Superseded by explicit owner direction on 2026-11-27 after confirming `lagos-chem-l0` was created prior to the canonical world model and is not read by CI.

## Consequences

- `docs/PPC-REG-001_Architecture_Decision_Register.md` (`ADR-001`–`ADR-039`) remains untouched; `ADR-003` is clarified so PPC uses one operational bucket (`pearland-petroleum-corp`) plus one dedicated restricted hidden-truth bucket (`pearland-petroleum-hidden`).
- `ADR-0053`'s quarantine rule is amended for `lagos-chem-l0` only: its full pre-deletion inventory is preserved in `infra/r2/legacy_pre_world_model_inventory.json` and the bucket itself is retired. Any future legacy pre-world-model fixtures in sister repositories remain governed by `ADR-0053`.
- `WP-0` R2 prefix maps, probes, and `WorldExportBundle` contracts reference `pearland-petroleum-corp` for observable/operational prefixes and `pearland-petroleum-hidden` for `evaluation/hidden/`.
