# PPC architecture requirements coverage

Draft routing record, 2026-11-25. A linked draft states a proposed contract; this table does not assert implementation or passed tests. [VERIFY-001](../07-scenarios-verification/PPC-VERIFY-001_Verification_and_Release_Qualification.md) defines the evidence package.

| Requirement | Contract owner | Required independent check | Current evidence |
|---|---|---|---|
| Coherent world, replay and isolation | WORLD-001/002, ENG-001 | Conservation, event-order restart, sibling isolation | Draft fixtures only |
| Source and engineering authority | OT-001, EDI-001, INT-001 | Ambiguous mapping, revision adoption, duplicate receipt | Draft obligations only |
| Semantic identity and graph | INFO-001, GRAPH-001 | As-of mapping, shape/round trip, restricted path | Draft obligations only |
| Governed product and KPI | DATA-001, ANALYTICS-001 | Grain, formula parity, feasibility and incomplete release | Draft obligations only |
| Decision-time context and action | EVID-001, UX-001, AGENT-001 | Noon/13:00 cutoff, policy denial, no leak | Draft obligations only |
| Recovery and enterprise scenarios | PLATFORM-001, SCENARIO-001, PLAN-001 | Restore, derate, crude and hurricane regression | No integrated run claimed |
| Decision rationale | ARCH-000, KNOWLEDGE-001 | Source-to-section and ADR disposition audit | GAP-002 open |

All 19 registered specifications have a destination. Coverage of individual OT/EA claims remains open; a destination is not a verified requirement mapping.
