# Owner Stand-In Ruling — Physical-Model Consistency Graph (`scripts/physical_graph.py`, 2026-11-28)

Ruling issued by **Claude Fable 5.2** (`claude -p --model fable --permission-mode plan`) acting as owner-delegated stand-in for Hamid Adesokan under [ADR-0059](../0059-overnight-night-run-delegation-and-standin-authority.md).

## 1. Proposal submitted to Claude Fable 5.2 (verbatim)

> # Proposal: PPC Physical-Model Consistency Graph (`scripts/physical_graph.py`)
>
> This proposal covers the design of `scripts/physical_graph.py` for `pearland-petroleum-corporation` under the `consistency-graph` skill and the owner's physical-model specification.
>
> ## 1. Sources (rebuilt from files on every run)
>
> Every node, link, count, classification, and boundary edge is parsed directly from repository files (never typed into the script):
>
> ### Present now (checked immediately on `main` after WP-0)
> 1. `docs/enterprise-architecture/independent-review/PPC-REVIEW-002_Governing_Refinery_Equations_and_Balances.md`
>    - Declares Refinery A v1 main units (`CDU + VDU`, `FCC`, `Hydrocracker`), bounded interfaces (`SMR`, `NHT`, `Catalytic Reformer`, `FCC Selective HDS`, `DHT`, `SRU`, `Steam and Power`, `Terminal Ethanol`), product pools / boundary sinks, the stream-to-sink closure table, the 13-tank register (`TK-101`, `TK-101H`, `TK-102`–`TK-104`, `TK-201`–`TK-202`, `TK-301`–`TK-304`, `TK-401`–`TK-402`), the 6 `EQ-03` hydraulic transfer lines (`LINE-CRUDE-CHG`, `LINE-VGO-HCU`, `LINE-ULSD-DISP`, `LINE-BOB-DISP`, `LINE-JET-EXP`, `LINE-RESID-EXP`), and pumps (`P-101A/B`..`P-402`), plus promised counts (3 crude assays, 3 terminals `TERM-01`..`03`, tank multiplicity `(3x)`/`(2x)`).
> 2. `docs/enterprise-architecture/01-enterprise-world/PPC-WORLD-001_Canonical_Enterprise_World.md`
>    - Declares facility `Refinery A`, promised entity counts (`1` refinery, `3` terminals, `12` customers, `12` months history), allowed provenance classifications (`OBSERVED`, `DERIVED`, `ESTIMATED`, `SYNTHETIC`, `SCENARIO_ASSUMPTION`), and hidden canonical world boundary (`evaluation/hidden/`).
> 3. `docs/PPC-017_EPM_Dependency_Semantic_Authority_and_Process_Conformance_Contract.md` and `semantic/adapters/epm.adapter.json`
>    - Declares EPM semantic authority over KPIs, measure classes, and data product definitions (pinned commit `511a9e8d`, `CONSUMED_PROVISIONAL` artifacts, and `PENDING_UPSTREAM_RELEASE` `ds-business-process/1.0`).
> 4. `docs/PPC-REG-003_KPI_Metric_and_Data_Product_Register.md`
>    - Declares PPC's 7 seed data products and 15 initial KPI candidates.
> 5. `semantic/ontology/ppc_core.ttl`
>    - Declares PPC core OWL classes (`Site`, `ProcessUnit`, `StorageTank`, `SourceRecord`, `ReleaseManifest`, `DecisionDossier`), `ppc:RefineryA` (`SITE-REF-A`, `provenanceClass: SYNTHETIC`), and the closed `provenanceClass` comment vocabulary.
> 6. `schemas/policy_thresholds.yaml`, `schemas/runtime_freeze.yaml`, and `schemas/*.schema.json`
>    - Declares provenance classifications on governance/runtime configs and schema-level hidden-truth guards (`evaluation/hidden/`, `pearland-petroleum-hidden`).
> 7. Integration/runtime directories (`integration/`, `source-systems/`, `ot/`, `lakehouse/`, `api/`, `apps/`)
>    - Parsed via static AST/import and string/path reference scanning to extract `Pipeline` -> target `DataStore`/`Module` links and enforce zero integration links to canonical hidden world paths (`evaluation/hidden/`, `pearland-petroleum-hidden`, or hidden world generator modules).
>
> ### Planned sources (parsed automatically when added in WP-1 through WP-8B; reported as `pending` until present, never falsely failing before their WP)
> 8. `fixtures/golden/refinery_a_design_basis.yaml` (WP-1) — authoritative machine-readable units, tanks, lines, pumps, crude assays, process streams (with explicit `source`, `destination`, `phase`, `mass_unit`, `volume_unit`, `provenance_class`), and commercial world counts (`terminals`, `customers`).
> 9. `fixtures/golden/refinery_a_ot_tags.yaml` (WP-1) — native OT tags bound to units/tanks/pumps with native units and provenance class.
> 10. `fixtures/golden/cfg0_dexpi*.json|yaml|xml` (WP-1) — baseline `CFG-0` engineering topology.
> 11. `semantic/mappings/epm_kpi_bindings.yaml` (WP-1/WP-3) — explicit mapping from PPC KPIs and data products to EPM semantic IRIs/IDs (with explicit `PPC_EXTENSION` or `PENDING_UPSTREAM_RELEASE` disposition where EPM has no approved ID yet).
> 12. `generators/` configuration & generated data manifests (`fixtures/golden/*_manifest.json`, `fixtures/golden/*_oracle.json`, WP-1+) — added as sources of the same graph so `check` compares generated data against documents and configs.
>
> ## 2. Node labels and link types
>
> ### Node labels
> - `Facility` (`SITE-REF-A`, `TERM-01`..`03`)
> - `Unit` (process units and Option A bounded interfaces, e.g. `CDU_VDU`, `FCC`, `HCU`, `SMR`, `NHT`, `REFORMER`, `FCC_HDS`, `DHT`, `SRU`, `STEAM_POWER`, `BLENDING`, `BOUNDARY_EXPORTS`)
> - `Tank` (`TK-101`, `TK-101H`, `TK-102`..`TK-402`)
> - `TransferLine` (`LINE-CRUDE-CHG`, `LINE-VGO-HCU`, `LINE-ULSD-DISP`, `LINE-BOB-DISP`, `LINE-JET-EXP`, `LINE-RESID-EXP`)
> - `Pump` (`P-101A`, `P-101B`, ..., `P-402`)
> - `Stream` (process and utility streams connecting `Unit`/`Tank`/`Facility` endpoints, carrying `phase`, `mass_unit`, `volume_unit`, `provenance_class`)
> - `CrudeAssay` (3 TBP crude assays)
> - `KPI` (KPI candidates / governed KPIs, carrying `measure_class` and `epm_ref`)
> - `DataProduct` (PPC data products, carrying `epm_portfolio_ref`)
> - `EPMArtifact` (pinned upstream EPM artifacts from `semantic/adapters/epm.adapter.json`)
> - `Pipeline` (integration, source-system, OT, lakehouse, API, and app modules/jobs)
> - `HiddenWorld` (canonical synthetic world stores/prefixes: `evaluation/hidden/`, `pearland-petroleum-hidden`, `generators.canonical_world`)
> - `Classification` (the 5 legal provenance classes: `OBSERVED`, `DERIVED`, `ESTIMATED`, `SYNTHETIC`, `SCENARIO_ASSUMPTION`)
> - `Source` (each parsed file, attached via `STATED_IN` or node `source` property so every disagreement names the exact files)
>
> ### Link types (directed)
> - `(:Unit|:Tank|:TransferLine|:Pump)-[:LOCATED_AT]->(:Facility)`
> - `(:Stream)-[:FROM_ENDPOINT]->(:Unit|:Tank|:Facility)`
> - `(:Stream)-[:TO_ENDPOINT]->(:Unit|:Tank|:Facility)`
> - `(:TransferLine)-[:CONNECTS_FROM]->(:Tank|:Unit)` and `-[:CONNECTS_TO]->(:Tank|:Unit|:Facility)`
> - `(:Pump)-[:DRIVES]->(:TransferLine)`
> - `(:KPI|:DataProduct)-[:DEFINED_BY_EPM]->(:EPMArtifact)`
> - `(:Unit|:Tank|:Stream|:KPI|:CrudeAssay)-[:SOURCED_FROM]->(:Source)`
> - `(:Unit|:Tank|:Stream|:KPI|:DataProduct|:CrudeAssay)-[:CLASSIFIED_AS]->(:Classification)`
> - `(:Pipeline)-[:READS_OR_WRITES]->(:HiddenWorld)` (forbidden link — any instance is a finding!)
>
> ## 3. Checks (tied to `consistency-graph/references/check-catalog.md`)
>
> 1. **Source provenance (`Element with a required link missing`)**:
>    - Every equipment item (`Unit`, `Tank`, `TransferLine`, `Pump`), `Stream`, and `KPI` defined in generator configs or generated manifests must trace back to an architecture doc or EPM source (`SOURCED_FROM` both doc/EPM and generator config; generator-only invented items fail).
>    - Every `KPI` and `DataProduct` must reference EPM semantic authority (`DEFINED_BY_EPM` or explicit `PPC_EXTENSION` / `PENDING_UPSTREAM_RELEASE` status per `PPC-017` and `ADR-0042`); any PPC file that redefines an EPM KPI formula/meaning without an EPM binding fails.
> 2. **Stream endpoint, unit, and phase agreement (`Link to nothing` + `Two-sided link disagreement`)**:
>    - Every `Stream` must have both `FROM_ENDPOINT` and `TO_ENDPOINT` resolving to declared `Unit`/`Tank`/`Facility` nodes.
>    - Endpoint `phase` (`liquid`, `gas`, `solid`, `utility`) and unit basis (`kg`/`t` SI mass; `bbl_60F` standard volume only for liquid phase; gas streams must not declare liquid `bbl` volume) must agree on both ends.
> 3. **Promised counts vs defined entities (`Count that does not add up`)**:
>    - Reads promised counts directly from `PPC-REVIEW-002` and `PPC-WORLD-001` (never hardcoded):
>      - Tank table multiplicity (`3x` crude charge tanks, `2x` ULSD tanks, `2x` BOB tanks -> 13 tanks total).
>      - `EQ-03` hydraulic transfer lines (`6` named in `PPC-REVIEW-002 §1`).
>      - Bounded interfaces (`8` rows in `PPC-REVIEW-002 §1` table including terminal ethanol).
>      - Promised WP-1 entities (`3` crude assays, `3` terminals `TERM-01`..`03`, `12` customers, `12` months history): reported as **pending** in `planned` mode until `fixtures/golden/refinery_a_design_basis.yaml` exists, then enforced strictly in `built` mode!
> 4. **Material provenance classification (`Field that means something else` / `Element with a required link missing`)**:
>    - Every material value/config/entity record must carry exactly one valid classification in `{OBSERVED, DERIVED, ESTIMATED, SYNTHETIC, SCENARIO_ASSUMPTION}`. Missing or invalid values fail.
> 5. **Hidden-world isolation (`One element, two places that conflict` / forbidden edge)**:
>    - No integration pipeline (`integration/`, `source-systems/`, `ot/`, `lakehouse/`, `api/`, `apps/`) may import canonical world internals or reference `evaluation/hidden/` or `pearland-petroleum-hidden` (only `generators/` canonical snapshot writers, `verification/` evaluation harnesses, and `WP-8B` `WorldExportBundle` `hidden_truth` packager are permitted).
> 6. **Name consistency & unreadable source form (`Name stated two ways` + `Unreadable source form`)**:
>    - Flags unparseable markdown tables/YAML/TTL rows instead of silently dropping them.
>    - Preserves distinct spellings across sources (for example, `P-101A/B` vs `P-101A`, `P-101B` or `Hydrocracker` vs `HCU`) via an explicit alias table parsed from sources, flagging unmapped alias clashes rather than silently normalizing them away.
>
> ## 4. First-pass findings already visible across current PPC sources (rulings needed)
>
> Running a manual first pass over the current repository files surfaces three items where a ruling is requested before writing code:
>
> 1. **Ruling Q1 — KPI & Data Product EPM binding scope before WP-3 (`PPC-REG-003` vs `PPC-017` / `epm.adapter.json`):**
>    - `PPC-REG-003` lists 7 seed Data Products and 15 initial KPI candidates, while `semantic/adapters/epm.adapter.json` pins EPM `511a9e8d` (`PROVISIONAL_COMMIT_PIN`) and `ds-business-process/1.0` is `PENDING_UPSTREAM_RELEASE`. No machine-readable `semantic/mappings/epm_kpi_bindings.yaml` exists yet.
>    - **Recommendation:** In `planned` mode (prior to `WP-3` KPI Store implementation), treat `PPC-REG-003`'s 15 KPI candidates and 7 data products as **pending** EPM bindings (reported in `summary` and `check` output without failing the `scripts/check.sh` gate), while failing immediately if any generator, lakehouse, or API code defines a KPI without an EPM binding or explicit `PPC_EXTENSION` record. Switch KPI EPM-binding checks to strict failure once `semantic/mappings/epm_kpi_bindings.yaml` is introduced in `WP-1`/`WP-3`.
>
> 2. **Ruling Q2 — `PPC-REG-002` baseline register vs reconciled `ADR-0045`/`0046`/`0055`:**
>    - `PPC-REG-002` still lists legacy baseline technologies (`Debezium→Kafka`, `D1`, `DuckLake`) from the pre-ADR baseline, while `ADR-0045`, `ADR-0046`, `ADR-0055`, `PPC-INT-001`, and `PPC-DATA-001` lock `NATS JetStream + Outbox`, `PostgreSQL`, and `Delta Lake on R2`.
>    - **Recommendation:** Do NOT parse `PPC-REG-002`'s stale baseline technology column as the active pipeline authority in `physical_graph.py`; instead use `PPC-INT-001`, `PPC-DATA-001`, `infra/docker-compose.yml`, and the actual `integration/`/`source-systems/`/`ot/`/`lakehouse/` code as the pipeline authority (and note `PPC-REG-002` as a baseline document superseded by `ADR-0045`/`0046`/`0055`).
>
> 3. **Ruling Q3 — Mode reporting and gate placement in `scripts/check.sh`:**
>    - **Recommendation:** Implement `scripts/physical_graph.py` with explicit mode reporting (`mode: planned` while WP-1 fixtures/generators do not yet exist, automatically switching sections to `built` as `fixtures/golden/refinery_a_design_basis.yaml`, `generators/`, and `semantic/mappings/epm_kpi_bindings.yaml` appear) and wire `python3 scripts/physical_graph.py check` directly into `scripts/check.sh` (plus one pointer line in `AGENTS.md`) as soon as `check` exits 0 on all active checks.

## 2. Claude Fable 5.2 stand-in ruling (verbatim, 2026-11-28)

> # Stand-in ruling: physical-model consistency graph (`scripts/physical_graph.py`)
>
> Ruling by Claude Fable 5.2 as owner-delegated stand-in under ADR-0059, 2026-11-28. I checked the proposal against the repository read-only: local `main` at `5377c68` and `origin/feat/wp0-schemas-pins-probes`.
>
> ## A. Overall design
>
> **Approved to build, with conditions C1 to C7.** The sources, node labels, directed link types and six checks are sound and match the `consistency-graph` skill. Start the tool with the skill's `start.py`, and ship it through the normal pull request with its tests.
>
> - **C1. Branch from current `origin/main`.** GitHub reports PR #23 (WP-0) as merged, but local `main` at `5377c68` has no `schemas/*.json`, `semantic/adapters/` or `ppc_core.ttl`. Fetch first so that sources 3, 5 and 6 exist.
> - **C2. Take node IDs from sources.** `CDU_VDU`, `HCU`, `REFORMER`, `FCC_HDS`, `STEAM_POWER`, `BLENDING` and `BOUNDARY_EXPORTS` appear in no source. Until `refinery_a_design_basis.yaml` supplies IDs, use the names and codes that `PPC-REVIEW-002` states (`4A`, `4B`, `5A`–`5D`, `BL`, `FT`). No source holds an alias table today, so report spellings such as `Hydrocracker`/`HCU` as "name stated two ways" findings.
> - **C3. Count the interfaces as the source states them.** `PPC-REVIEW-002` section 1 lists 7 internal bounded interfaces in its text and 8 rows in its table. The eighth row is Terminal Ethanol, which sits in the terminals. Check 7 + 1, and do not link Terminal Ethanol to `SITE-REF-A`.
> - **C4. Check only counts that a source promises.** I confirmed 13 tanks and 6 lines. No source promises a pump count or the 7 data products and 15 KPI candidates, so report those as derived counts. `PPC-WORLD-001` gives its counts in words ("three terminals", "twelve customers"). Read them or report them as unreadable.
> - **C5. Make check 5 pass the WP-0 isolation probe from a source.** `lakehouse/delta/wp0_probes.py` references `evaluation/hidden/_probe/` and the hidden bucket to prove that access is denied. Allow only the probe prefix that `infra/r2/r2_prefix_map.yaml` declares. Read the list of permitted writers from a source too (ADR-0053, ADR-0057 or the prefix map). If no source states it, report that. `generators.canonical_world` is named in no document, so read the module name from `generators/` when it exists.
> - **C6. Report a missing directory as pending.** `ot/`, `api/` and `verification/` do not exist yet. The output must list them as pending so that they do not count as a silent pass.
> - **C7. Scope check 4 to machine-readable records.** These are fixtures, schema configs, ontology individuals and manifests. For a document table, read the table's own classification statement.
>
> ## B. Rulings
>
> **Q1: approved, with one amendment.** The 15 KPI candidates and 7 data products are pending EPM bindings in `planned` mode. Code that defines a KPI without a binding fails from the first run. The check turns strict when the bindings file exists.
>
> The amendment: `PPC_EXTENSION` is not approved. It appears in no PPC document, and it would let PPC define KPI meaning, which `AGENTS.md` and `PPC-017` forbid. The allowed states are the adapter's `CONSUMED_PROVISIONAL` and `PENDING_UPSTREAM_RELEASE`, or pending. `semantic/mappings/epm_kpi_bindings.yaml` is also named in no document, so the pull request that introduces it must add it to `PPC-PLAN-001`.
>
> **Q2: amended.** Do not treat `PPC-REG-002` as the pipeline authority. ADR-0045, ADR-0046 and ADR-0055 hold that authority, with `PPC-INT-001`, `PPC-DATA-001`, `infra/docker-compose.yml` and the code.
>
> Do not record `PPC-REG-002` as superseded. `PPC-ARCH-000` says to retain it and reconcile "without superseding it". Parse it as a source and let `check` report its `Debezium→Kafka`, `D1` and `DuckLake` rows as findings. Report the empty `integration/debezium/`, `integration/kafka/` and `lakehouse/ducklake/` scaffold folders the same way. A documentation pull request settles these findings by reconciling the rows and folders with the three ADRs.
>
> **Q3: approved, with the skill's gate order.** Report the mode per section, and decide it only from which files exist. From the first merge, `scripts/check.sh` runs the tool's unit tests as a failing step, and runs `check` and `summary` as a report that cannot fail the build. `check` becomes a failing gate when it reports zero findings. The Q2 findings must be settled before that. Pending items never fail the gate. The one pointer line in `AGENTS.md` is approved.
>
> ## Limits
>
> I did not run `git fetch`, so I read WP-0 files from the remote branch, not from merged `main`. Plan mode blocked writes, so I saved nothing to project memory. The calling agent should record this ruling there.
