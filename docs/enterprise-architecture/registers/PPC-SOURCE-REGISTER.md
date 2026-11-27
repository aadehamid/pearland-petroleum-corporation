# PPC source register

Reconciled navigation record, 2026-11-26. Commits below reflect both the original `ARCH-000` inspection pins and the refreshed 2026-11-26 local verification across all six sister repositories ([PPC-REVIEW-001 §1](../independent-review/PPC-REVIEW-001_Document_Coverage_and_Transcript_Audit.md#sister-repository-revision-deltas-against-ppc-arch-000)). A commit identifies content, not business approval.

| Source | Original ARCH-000 pin | Verified local revision (2026-11-26) | Authority used here | Outstanding check |
|---|---|---|---|---|
| PPC | `01027a84` | `ef4eb08fd09298a8fe64cff4bac52242f6d6b5f6` (`main`; reconciled on `docs/first-principles-refinery-grill`) | Charter, baseline docs, `ADR-001`–`039`, new `ADR-0040`–`053` | Independent external review & Phase 0 authorization |
| EPM | `511a9e8d` | `511a9e8db4008ef43a0dda0f92cef17664e4c995` (`main`) | Performance semantics, Git Turtle + `pyshacl` + Neo4j pattern | Per-module release & parity (`WP-3`, `WP-8`) |
| Downstream ontology release | `ddf6b68b` | Local `share/epm-1.0` @ `2b3f02e`; `ds-business-process/1.0` separate upstream track | `kpi-store/1.2` lineage for generalized `DS_Business_Process` | Pending upstream release (`GAP-001`, `WP-7`) |
| ICE (`scada_harmonization`) | `1467e927` | `30c20c3` (`main`, PR #68); `65ffe10` (`cursor/handoff-close-68`) | L0 contract, 1 s machine stream, Plane 3 split | Mapping YAML pending (`GAP-004`, `WP-2`) |
| EDI (`Engineering_Drawing_to_Graph`) | `12a4a6a6` | `12a4a6a` (`main`, PR #56) | Bounded structured DEXPI contract | Flat drawing & PPC adapter (`GAP-005`, `WP-2`) |
| ECE (`enterprise-context-engineering`) | `750b398b` | `750b398` (`main`, PR #12) | Evidence & decision-provenance patterns | Published reusable schema pending (`GAP-006`, `WP-3`) |
| `enterprise-people-graph` | Not listed | `eb2fdb7` (`teaching/ontology-101`) | Out of PPC v1 scope (`ADR-0042`) | None for v1 |
| Conversation export | T1–T145 (`2026-11-25`) | Full 40,518-line audit complete ([PPC-REVIEW-001 §5](../independent-review/PPC-REVIEW-001_Document_Coverage_and_Transcript_Audit.md#5-audit-of-raw-chatgpt-transcript-t1t145-versus-ef4eb08-ppc-documents-closing-gap-002)) | Discussion provenance and owner directions | 5 external attachments/images unavailable & excluded |

## PPC inspection pins

Individual early drafts originally retained historical inspection commits (`08e7b33`, `6559459`, `35cdd80`, `991a9ef`, `3cb75a8`). The unified reconciled baseline is `ef4eb08` plus branch `docs/first-principles-refinery-grill`.
