# PPC architecture requirements coverage

Reconciled routing record, 2026-11-26. All runtime verification obligations remain **planned** until Phase 0 implementation is authorized. [VERIFY-001](../07-scenarios-verification/PPC-VERIFY-001_Verification_and_Release_Qualification.md) and [PPC-REVIEW-004](../independent-review/PPC-REVIEW-004_Proof_Obligation_and_Validation_Register.md) define the complete proof-obligation register (`PO-01`–`PO-12b`).

| Requirement | Contract owner | Governing equations / ADRs / proof IDs | Current evidence |
|---|---|---|---|
| Coherent world, replay and isolation | `WORLD-001/002`, `ENG-001` | `EQ-01`–`EQ-08`; `ADR-0040`, `0043`, `0050`, `0054`, `0056`; `PO-01`, `02`, `04`–`07`, `09`, `11`, `12a` | Paper arithmetic checked (`PPC-REVIEW-002`, `004`); runtime **planned** |
| Source and engineering authority | `OT-001`, `EDI-001`, `INT-001` | `ADR-0042`, `0046`, `0053`, `0056`; `PO-03` | Paper walkthroughs verified (`PPC-REVIEW-003 §4`); runtime **planned** |
| Semantic identity and graph | `INFO-001`, `GRAPH-001` | `ADR-0044`, `0052`; `PO-08` | `INFO-001 §3` synthetic fixture checked by `check_package.py`; runtime **planned** |
| Governed product and KPI | `DATA-001`, `ANALYTICS-001` | `EQ-09`; `ADR-0045`, `0048`, `0055`; `PO-08`, `12b` | `DATA-001 §2` L1/X1 fixture checked by `check_package.py`; runtime **planned** |
| Decision-time context and action | `EVID-001`, `UX-001`, `AGENT-001` | `ADR-0047`, `0048`, `0052`, `0055`, `0056`; `PO-08`, `10` | Contract & state tables reconciled; runtime **planned** |
| Recovery, hosting, and golden scenarios | `PLATFORM-001`, `SCENARIO-001`, `VERIFY-001`, `PLAN-001` | `UC-1`–`UC-6`; `ADR-0049`, `0051`, `0053`, `0055`, `0056`; `PO-01`–`12b` | Detailed work packages (`WP-0`–`WP-8B`) ready; runtime **planned** |
| Coverage, transcript audit, and rationale | `ARCH-000`, `KNOWLEDGE-001`, `PPC-REVIEW-001`–`004` | `ADR-0040`–`0056`; `GAP-002` closed for Markdown transcript | 100% baseline + draft docs read and reconciled |

The temporal check routes to [INFO-001 §3](../03-enterprise-information/PPC-INFO-001_Enterprise_Ontology_Identity_and_Time.md), which owns the full P0/P1/P2 fixture and reader-as-of gate.
