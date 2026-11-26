# PPC risks and open questions

Reconciled tracker, 2026-11-26. [ARCH-000 §12](../00-master-index/PPC-ARCH-000_Master_Architecture_Index_and_Authority_Baseline.md#12-open-issues-and-evidence-gaps-must-not-silently-close) tracks `GAP-001`–`012`. Architectural choices previously open (Delta Lake on R2, `exe.dev` hosting, RPO/RTO, NATS/outbox, Git Turtle/`pyshacl`→Neo4j, Pyomo/HiGHS, Relate WASM Slice 1.5, Quint/Z3 verification, legacy-data quarantine) are now decided in [ADR-0040](../../adr/0040-staged-mechanistic-refinery-model-and-closed-flowsheet.md)–[ADR-0053](../../adr/0053-legacy-data-quarantine-and-world-export-bundle.md).

| Gap | Remaining decision or runtime evidence needed | Owner for disposition |
|---|---|---|
| `GAP-001`, `004`–`006` | Upstream releases for `DS_Business_Process`, ICE mapping YAML, EDI flat extraction, ECE schemas (decoupled via provisional adapters in `ADR-0042`) | Upstream owners and PPC owner |
| `GAP-007`, `009` | Single-writer Delta-on-R2 commit/restore verification (`WP-0`/`WP-4`) and DuckDB/Databricks parity (`WP-8`) | Data/platform reviewers |
| `GAP-008` | Process/controls engineer sign-off on Refinery A v1 synthetic parameters and tolerances (`PPC-REVIEW-004 §4`); runtime execution of `PO-01`–`PO-12` | Process/controls engineer & PPC owner |
| `GAP-010`, `011` | `WP-4` `exe.dev` restore drill (`RTO <= 1 hour`) and `WP-5B` Relate WASM security/Cypher gate | Platform & UX/security reviewers |
| `GAP-012` (4 WP-0 items) | (1) Named steward for conflicting identity mappings; (2) numeric `AUTO_EXECUTE` vs `REQUIRE_APPROVAL` thresholds; (3) `exe.dev` VM RAM/CPU sizing; (4) synthetic Refinery A calibration sign-off | PPC owner (WP-0 gate before Phase 0 code) |

Previously open architecture questions now closed: Delta Lake single-writer protocol (`ADR-0045`), Refinery A v1 numerical envelope (`ADR-0040`, `0043`, `PPC-REVIEW-002`), RPO/RTO targets (`ADR-0051`: RPO = last committed R2 manifest/WAL, RTO <= 1 hour), and planner availability channel rule (`INFO-001 §3`).
