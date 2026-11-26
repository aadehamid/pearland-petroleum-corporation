# PPC-INFO-001 — Enterprise Ontology, Identity and Time

Draft for independent review. Baseline [PPC main at 3cb75a8](https://github.com/aadehamid/pearland-petroleum-corporation/tree/3cb75a8a2e548f658fab130bfb91286d943598fd). Decision question: which meaning and which entity could a planner legitimately associate with a source record at a specified decision time?

## 1. Meaning, release authority and ownership

[ADR-033, 035, 038 and 039](../../PPC-REG-001_Architecture_Decision_Register.md) and [PPC-017](../../PPC-017_EPM_Dependency_Semantic_Authority_and_Process_Conformance_Contract.md) govern the existing EPM dependency, process conformance, artifact maturity and KPI alignment. The owner's later direction assigns development of the generalized downstream process vocabulary to a separate upstream effort. Preserve the existing ADRs. Record a proposed clarification of ADR-035 for owner disposition before representing the revised division of authority as ratified.

| Question | Authority | PPC consumption rule |
|---|---|---|
| What is a generic downstream process? | Future approved DS_Business_Process release | At the ARCH-000 inspection both upstream branches pointed to ddf6b68b. A branch name provides no approval. Keep the binding pending and exclude it from claims of conformance. |
| Which process or KPI definition governs performance reporting? | Versioned EPM bundle and module approval | Bind the approved definition, grain and formula version to an execution or value. Preserve historical bindings across restatements. |
| Which process actually ran, on which branch? | PPC execution records and governed identity mappings | Assign an immutable local execution ID, link evidence and record conformance separately. A reference to an industry concept cannot prove execution. |
| Which public terms may be reused? | Upstream publisher for meaning and licensing, adopting owner for local mapping | [PPC-019](../../PPC-019_Public_Ontology_Reuse_and_Implementation_Guide.md) lists candidates. Record release, license, dependency closure, term category and reviewed mapping before adoption. |

Example: give a fictional demand-forecast run its own ID and branch today. Keep its candidate generic process binding pending. An approved EPM forecast-accuracy definition, when available, can independently govern evaluation of that run. Later process approval creates a new mapping version with its own knowledge time.

## 2. Identity and mapping contract (proposed)

Mint opaque canonical IDs per entity kind. Retain renamed labels and source aliases with their validity. Scope native keys by source, site, object kind and source incarnation where keys are recycled. Preserve the source payload and revision. A corrected association adds history. Splits and merges create signed-off successor mappings with evidence, and leave old IDs resolvable for replay.

| Identity boundary | Cardinality and evidence on a selected branch and time slice |
|---|---|
| Physical asset, functional position, installed equipment | Distinguish an identified physical item from the role it fills. Many occupants across time. For a single-slot position, permit at most one accepted occupant at an instant. Multi-slot assemblies need explicit numbered slots. |
| Engineering object and drawing symbol | Several appearances can depict one object. Bind sheet, revision and publication to the engineering object. Use EDI's reviewed publication and the PPC adoption record for operating context. |
| Tag assignment and observation | A tag can be reused. Bind a point to a canonical measured property, unit, basis and asset or position with an effective interval. Keep raw timestamp, quality and source key on each observation. A position sensor alone cannot identify the installed item. |
| Source record and business entity | Multiple records can describe one entity. A document covering several entities needs typed role links, such as seller and buyer. A matching display name creates a candidate for review. |
| Concept, KPI definition, KPI value | Preserve the released concept IRI and version, the governed metric definition/version and the separate value ID with dimensional grain, branch, computation and restatement. |
| Scenario, decision dossier, evidence | Decision ID identifies the decision on a branch. A dossier references many versioned evidence artifacts. Reuse requires release membership, decision-time availability and reader permission. |

Each mapping assertion records its own ID, source and target kinds and IDs, relation, scope, valid and recorded intervals, mapping version, upstream package, assertion status, accountable steward and evidence locator. Proposed lifecycle: candidate → accepted or rejected. Superseding an accepted assertion preserves its recorded history. Missing, low-confidence and conflicting candidates are visible for stewardship. Consumers that require unique identity must return unresolved if zero or multiple eligible mappings survive.

Use typed instance links for installation and observation. Apply SKOS mapping relations only to appropriate concepts. Class equivalence requires review of both class extensions; individual equivalence asserts the two identifiers denote the same individual. Neither follows from shared labels. Projections carry the assertion ID, source version and conversion rule. Flag unsupported constructs and block release if a required construct changes meaning.

## 3. Worked reconstruction

Illustrative `SYNTHETIC` UTC fixture on November 1, 2026. At 08:00 the baseline register shows pump A in slot S. A field swap occurs at 10:00. The source records a correction at 12:00 but releases it to this planner at 13:00. The last authorized publication P1, still identifying A, becomes available at 12:30. Recorded and available time are separate. Intervals are half-open; infinity means an open end.

| Publication | Slot S occupant | Valid interval | Recorded at | Available to planner | Branch |
|---|---|---|---|---|---|
| P0 | A | [08:00, ∞) | 08:00 | 08:00 | baseline |
| P1 | A | [08:00, ∞) | 12:30 | 12:30 | baseline |
| P2 correction | B | [10:00, ∞) | 12:00 | 13:00 | baseline |

Select the pinned release and branch snapshot, apply authorization, then require valid_start ≤ event_time < valid_end, recorded_at ≤ cutoff and recipient availability ≤ cutoff. Among eligible publications, apply authorized supersession as known at that cutoff. P2 supersedes P1 only after P2 becomes available to the planner. Materialize authorized inheritance at the fork for a child snapshot; later parent corrections require explicit adoption. Branch-specific overrides replace the scoped inherited assertion and retain lineage.

At event time 10:30, the 12:45 cutoff returns A from P1, with its age and uncertainty. If P1 and P0 were unavailable or unauthorized, the result is `UNRESOLVED`. At the 13:00 cutoff, the planner may use P2 and return B if receipt and authorization are established. At event time 09:59 and the 13:00 cutoff, the result is A; at exactly 10:00 it is B. The correction's planner-availability delay after the physical swap is three hours. Replaying the 12:45 dossier still returns A. A sibling's proposed pump C cannot enter these baseline results. A second accepted occupant at the same effective time must fail uniqueness. Withhold P2 from a consumer and require the result to disclose no restricted identity or correction existence; authorization is not permission to guess an occupant.

## 4. Consumer compatibility and acceptance evidence

Pin the RDF bundle, shape and competency suite, EPM manifest and maturity, PPC mapping release, projection rules and input snapshot. Compare changed IRIs, scope, unit basis, status, constraints and metric versions. Preserve tombstones and successor links for withdrawn terms. A breaking change requires reviewed migration and impact analysis before a new consumer release. Historical dossiers pin their old manifests. Keep the last compatible release available for replay.

| Proposed challenge | Expected result and evidence required |
|---|---|
| Identity and history (SEM-01–03, 07–08) | Run the §3 lookups, duplicate-key, wrong-site, future-evidence and sibling-branch tests. Record IDs, release, query, cutoff and exact result. Old KPI values retain their original definition. |
| Projection and conversion (SEM-04–06, 09) | Rebuild RDF and property-graph views from pinned inputs, compare typed edges, mapping IDs and loss reports. Missing required meaning fails acceptance. Ossie/OGS are evaluation candidates. GRAPH-001 owns projection detail. |
| Measure portability (SEM-10) | DATA-001 compares approved EPM formula and consumer output on identical grain, units and null policy. Store per-row discrepancies and approved tolerances. |
| Release challenge (EA05C-01–14) | Exercise stable IRIs, rejected false equivalence, shape violations, engineering mappings, conversion loss, metric parity, both time axes, branch isolation, incompatible releases, round trips, reproducibility, incompatible edge measurements and permission-filtered retrieval. Retain failure fixtures as well as successful results. |

Checked here: the §3 baseline interval predicates and elapsed time on synthetic rows. Runtime SHACL, graph reconstruction, source-system identity resolution, consumer parity, authorization and rollback remain unqualified. GAP-001 blocks approved generic process binding; GAP-004 affects OT mapping evidence. Reviewer questions: Can a release change reinterpret an old dossier? Who may resolve a disputed installation? Which required semantic constructs cannot survive conversion? Record evidence and disposition before promoting a mapping.

## 5. Discussion traceability

The [exchange register](../registers/PPC-Discussion-Decision-Traceability.md) and [source locators](../registers/PPC-Discussion-Source-Locators.csv) identify individual prompts and source checks. T6–8, T32, T89–93 and T131–135 inform §1, including the owner's separate-release clarification. T56–57 and T68–70 inform §2 on OT identity. T62, T98–99 and T101–105 inform §§2–4 on translation, metric ownership, time and conversion loss. T103 lines 25518–25527 and T105 lines 26553–26566 provide the named verification targets in §4. The fixture and acceptance design are PPC proposals.
