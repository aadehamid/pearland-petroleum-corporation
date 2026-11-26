# PPC risks and open questions

Reconciled tracker, 2026-11-26 (revised after external Codex and Claude reviews). [ARCH-000 §12](../00-master-index/PPC-ARCH-000_Master_Architecture_Index_and_Authority_Baseline.md#12-open-issues-and-evidence-gaps-must-not-silently-close) tracks `GAP-001`–`012`. Architectural choices previously open are now decided in [ADR-0040](../../adr/0040-staged-mechanistic-refinery-model-and-closed-flowsheet.md)–[ADR-0053](../../adr/0053-legacy-data-quarantine-and-world-export-bundle.md); remaining owner decisions and runtime qualification gates are listed explicitly below.

| Gap | Remaining decision or runtime evidence needed | Owner for disposition |
|---|---|---|
| `GAP-001`, `004`–`006` | Upstream releases for `DS_Business_Process`, ICE mapping YAML, EDI flat extraction, ECE schemas (decoupled via provisional adapters in `ADR-0042`) | Upstream owners and PPC owner |
| `GAP-007`, `009` | `delta-rs` `aws_conditional_put="etag"` dual-writer conflict test and Databricks Free Edition synced-copy ingest probe (`WP-0`); DuckDB/Databricks parity (`WP-8`) | Data/platform reviewers |
| `GAP-008` | **WP-0:** Owner choice on proposed `ADR-0040` flowsheet closure (Option A: SMR + Reformer + FCC Selective HDS + E10 vs Option B: boundary imports) and parameter-range ownership. **WP-1 exit:** Process/controls engineer numeric calibration sign-off (`PPC-REVIEW-004 §4`) and execution of `PO-01`–`PO-12`. | PPC owner & process/controls engineer |
| `GAP-010`, `011` | `WP-4A`/`WP-4B` full per-store restore drill (`RTO <= 1 hour` for `<= 5 GB` compressed) and `WP-5B` Relate WASM byte-level security/Cypher gate | Platform & UX/security reviewers |
| `GAP-012` (WP-0 owner gates) | (1) `ADR-0040` Option A vs Option B flowsheet closure; (2) `ADR-0045`/`0051` confirmation on T86 Free Edition ingest, `exe.dev` RAM sizing (`16 GB` two-VM split with ClickHouse-backed Langfuse v3 vs `12 GB` lightweight Slice 1 OTel collector), and Cloudflare D1 retention vs Postgres consolidation; (3) identity-conflict steward role; (4) numeric `AUTO_EXECUTE` vs `REQUIRE_APPROVAL` thresholds | PPC owner (WP-0 gate before Phase 0 code) |
