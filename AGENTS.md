# AGENTS.md

Guidance for AI coding agents working in the Pearland Petroleum Corporation (PPC) repository.

## Start here

1. `README.md`
2. `docs/PPC-000_Master_Index_and_Architecture_Guide.md`
3. `docs/PPC-015_Three_Repository_Operating_Model.md`
4. `docs/PPC-016_Evidence_Decision_Provenance_and_Evaluation_Architecture.md` before working on evidence, decision provenance, agents or evaluations.
5. `docs/PPC-017_EPM_Dependency_Semantic_Authority_and_Process_Conformance_Contract.md` before consuming EPM artifacts, defining KPIs or validating process behavior.
6. `docs/PPC-014_Implementation_Roadmap_and_Build_Runbook.md` before changing implementation code.

## Rules

- PPC is a fictional company. Never present synthetic PPC data as fact about a real company.
- Classify every material value as `OBSERVED`, `DERIVED`, `ESTIMATED`, `SYNTHETIC` or `SCENARIO_ASSUMPTION`.
- Consume EPM semantic artifacts. Do not redefine them in PPC.
- Do not commit large generated datasets, model artifacts or synthetic releases. Store them in the PPC Cloudflare R2 project bucket.
- Integration pipelines must not read the canonical synthetic world as a shortcut.
- Follow the source precedence order in `README.md` when sources conflict.
- Write documentation in the ASD-STE100-inspired style described in `README.md`.

## Layout

Folders follow the "Repository structure" section of `README.md`. Documents live in `docs/`. Original delivered baseline archive is in `docs/archive/`.
