# PPC risks and open questions

Draft tracker, 2026-11-25. [ARCH-000 §12](../00-master-index/PPC-ARCH-000_Master_Architecture_Index_and_Authority_Baseline.md#12-open-issues-and-evidence-gaps-must-not-silently-close) retains GAP-001–012. This companion routes the gaps; it does not close them.

| Gap | Decision or evidence needed | Owner for disposition |
|---|---|---|
| 001, 004–007 | Approved upstream process, ICE, EDI, ECE and KPI Store compatibility | Upstream owners and PPC owner |
| 002 | Item-level OT/EA and original attachment trace | PPC architecture reviewer |
| 003, 012 | Technology and ADR changes | PPC owner |
| 008–009 | Independent equations and multi-store release | Engineering/data reviewers |
| 010–011 | Browser authorization and actual integrated deployment | UX/security/operations reviewers |

Open questions: Which publication channel proves planner availability? Who resolves competing identity mappings? Which Delta writer and restore protocol can meet PPC's consistency needs? What numerical envelope is acceptable for the first derate slice? What recovery point and time are required? Record answers with evidence and owner words, not inferred consensus.
