# AGENTS.md

Guidance for AI coding agents working in the Pearland Petroleum Corporation (PPC) repository.

## Standing rules

- **Writing.** Before writing anything a person will read, load the `clear-writing` skill and follow it — every reply, status update, email, doc, README, commit and PR description, post, and any text the user asks to edit. It applies to subagents too.
- **Working on a repository.** Before changing anything, load the `way-of-working` skill and follow it — how decisions get recorded, the pull request every change goes through, the checks before each push, the independent review before a PR opens, watching an open PR until it merges, and the retro that improves the standard.
- **Project memory.** Every agent shares one Relate memory through `scripts/memory.sh`. At session start run `scripts/memory.sh brief`; before you finish, save decisions, corrections and findings. Read `.agents/skills/project-memory/SKILL.md` before your first save (`ADR-0058`).

Run `scripts/check.sh` before every push. CI runs the same script. Use `REVIEW_STANDARDS.md` for review. Before wiring the tracked pre-push hook, check the conditions in `way-of-working/references/guardrails.md`; when they hold, run `git config core.hooksPath scripts/hooks`.

## Start here

1. `README.md` and `GLOSSARY.md` (canonical domain vocabulary)
2. `docs/PPC-000_Master_Index_and_Architecture_Guide.md`
3. `docs/enterprise-architecture/00-master-index/PPC-ARCH-000_Master_Architecture_Index_and_Authority_Baseline.md` and `docs/adr/README.md` (`ADR-0040` onward, preserving `docs/PPC-REG-001_Architecture_Decision_Register.md` verbatim). To see which later decisions changed a decision, run `scripts/adr_graph.py changed ADR-NNN`
4. `docs/PPC-015_Three_Repository_Operating_Model.md`
5. `docs/PPC-016_Evidence_Decision_Provenance_and_Evaluation_Architecture.md` before working on evidence, decision provenance, agents or evaluations.
6. `docs/PPC-017_EPM_Dependency_Semantic_Authority_and_Process_Conformance_Contract.md` before consuming EPM artifacts, defining KPIs or validating process behavior.
7. `docs/PPC-018_Enterprise_Evidence_Corpus_and_Unstructured_Data_Generation_Strategy.md` before generating documents, messages or other unstructured data.
8. `docs/enterprise-architecture/08-implementation/PPC-PLAN-001_Implementation_Work_Packages_and_Readiness.md` (authoritative reconciled plan; supersedes linear Phase 0–12 tool order in historical `docs/PPC-014_Implementation_Roadmap_and_Build_Runbook.md`) before changing implementation code.

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
