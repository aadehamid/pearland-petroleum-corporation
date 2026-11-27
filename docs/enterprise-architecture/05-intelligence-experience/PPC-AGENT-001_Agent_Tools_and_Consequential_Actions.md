# PPC-AGENT-001 — Agent Tools and Consequential Actions

Inspected PPC baseline: [`01027a84be5d453cbb4e2ea091e4884729918b15`](../registers/PPC-SOURCE-REGISTER.md). This commit is the original PPC source-inspection reference, not this draft's content revision or owner approval. Later linked specifications are read at the current branch revision.

| Control | Value |
|---|---|
| ID / status | PPC-AGENT-001 / proposed draft, 0.1.0, 2026-11-25 |
| Authority | [PPC-012](../../PPC-012_Intelligent_Automation_Agent_and_User_Experience.md), [PPC-016](../../PPC-016_Evidence_Decision_Provenance_and_Evaluation_Architecture.md), [PPC-REG-001](../../PPC-REG-001_Architecture_Decision_Register.md) ADR-019, 020, 026, 029 |
| Contract | Role-scoped tool request → cited answer, simulated proposal or separately authorized action receipt |

## 1. Tool and authority boundary

An agent may retrieve authorized evidence, traverse a scoped graph, request governed calculations, simulate an isolated branch and recommend an option. It cannot calculate an official KPI in prose, read hidden truth during blind evaluation or turn its recommendation into approval. Under [ADR-0048](../../adr/0048-pyomo-optimization-and-langgraph-pydantic-agents.md), **LangGraph** orchestrates stateful human-approval and escalation workflows, **Pydantic AI** (or Pydantic-typed tool contracts) enforces strict schema-validated tool calls inside nodes, and **OpenTelemetry** exports traces to **self-hosted Langfuse** (preserving no-paid-runtime compliance), paired with PostgreSQL/pgvector for retrieval and Ollama or configured LLM endpoints. Framework selection never relaxes service-side action policy.

`ToolRequest` has request ID, subject scope, effective time, actor and delegated role, channel, purpose, tool and contract version, branch, pinned release IDs, knowledge cutoff, input digest, requested action and expiry. `ToolResponse` has result ID/status, request ID, branch ID, knowledge cutoff, provenance class, epistemic status, output classification, source/model refs, uncertainty, redaction status and audit ID. `ActionProposal` has proposal ID, decision ID, payload digest, status, authority class, proposing actor, knowledge cutoff, measurement basis and binds exact action type, target, quantity/unit, branch, expected source revisions, policy version, approver role, evidence release, expiry and idempotency key. `ActionAuthorization` has authorization ID and authorized-at time and identifies `proposal_id`, `proposal_payload_digest`, `branch_id`, `authorization_expiry`, the human/role, scope, policy check, `APPROVED|DENIED` decision and signature or equivalent audit evidence. `ActionReceipt` has receipt ID, proposal ID, authorization basis ID, idempotency key, source revisions, execution status and time, business effect ID or blocked reason, and branch. For human approval, the basis ID is the `ActionAuthorization` ID. For `AUTO_EXECUTE`, it is the immutable preapproval policy grant ID and version. A tool cannot broaden an actor's scope.

One transition event records `decision_id`, `proposal_id` when present, prior and next states for each entity, event time, actor, policy version and authorization basis. The dossier and proposal project their states from that event. A dossier without a proposal can move `OPEN → DEFERRED|ESCALATED|EXPIRED`. A linked pair follows this table; each row is one event.

| Proposal transition | Linked dossier transition | Condition |
|---|---|---|
| `DRAFT → POLICY_CHECKED` | Remains `OPEN` | Policy check is current. |
| `DRAFT|POLICY_CHECKED → DENIED|EXPIRED` | `OPEN → REJECTED|EXPIRED`, respectively | Denial and expiry stop the proposal. |
| `POLICY_CHECKED → ESCALATED` | `OPEN → ESCALATED` | A higher authority must decide through a new decision ID. |
| `POLICY_CHECKED → RECOMMENDED` | `OPEN → RECOMMENDED` | Recommendation grants no execution authority. |
| `RECOMMENDED → RECOMMENDED_ONLY` | `RECOMMENDED → RECOMMENDED_ONLY` | `RECOMMEND` ends after proposing. |
| `RECOMMENDED → APPROVED|DENIED|DEFERRED|ESCALATED|EXPIRED` | `RECOMMENDED → APPROVED|REJECTED|DEFERRED|ESCALATED|EXPIRED`, respectively | `REQUIRE_APPROVAL` binds the exact payload and approver. |
| `APPROVED → EXECUTED|FAILED|EXPIRED` | The same transition | Execution checks the authorization and source revision. |
| `POLICY_CHECKED → AUTO_EXECUTED|FAILED` | `OPEN → AUTO_EXECUTED|FAILED` | `AUTO_EXECUTE` needs an immutable preapproval basis for a bounded, reversible action class. |

`DENIED`, `DEFERRED`, `RECOMMENDED_ONLY`, `ESCALATED`, `EXPIRED`, `EXECUTED`, `AUTO_EXECUTED` and `FAILED` are terminal for the proposal. `REJECTED` replaces `DENIED` on the dossier. An execution failure records its reason and no business effect. Retry after a terminal state needs a new proposal and decision ID. Execution requires a current policy check, exact approved payload, valid source revision and one-time business key. A changed quantity or target invalidates approval. `RECOMMEND`, `REQUIRE_APPROVAL` and `ESCALATE` follow PPC-012. An uncertain source or unavailable approver blocks consequential execution.

## 2. Synthetic action fixture

At 10:30 UTC an agent sees an `ESTIMATED` ULSD shortfall on the derate branch and proposes a `SCENARIO_ASSUMPTION` transfer of 5,000 bbl from terminal T. The graph path supplies potential exposure; the planning tool checks inventory and route bounds. The agent may simulate it and recommend it. If policy requires a Commercial Manager, the agent returns `REQUIRE_APPROVAL`. Only that role's authorization for this exact transfer permits execution. A duplicate execution request with the same key returns the original receipt; a different payload with that key is rejected. If the approval expires or inventory revision changes, recheck and request new authority. A baseline branch action cannot use a derate branch approval.

For the historical decision check, use [INFO-001 §3](../03-enterprise-information/PPC-INFO-001_Enterprise_Ontology_Identity_and_Time.md). The tool must pass the same recipient, channel, purpose and cutoff to evidence, graph and product queries. It must not disclose an inaccessible publication in results, traces or errors.

## 3. Qualification and decisions

Test allowed read/simulate/recommend scopes, policy denial, approval replay, exact-payload binding, stale source revision, duplicate/conflicting key, crash after execution, branch isolation, historical cutoff, hidden-truth and restricted-trace leaks. Preserve tool calls, policy versions, approval evidence and expected/observed receipts. No agent evaluation is claimed. Open choices include framework, action-class thresholds, trace retention and human approval channel. T26, T31, T116–118 in the [discussion register](../registers/PPC-Discussion-Decision-Traceability.md) support the proposal.

The [exchange register](../registers/PPC-Discussion-Decision-Traceability.md) routes T116–118 to this draft. `GAP-002` Markdown audit is closed in [PPC-REVIEW-001 §5](../independent-review/PPC-REVIEW-001_Document_Coverage_and_Transcript_Audit.md#5-audit-of-raw-chatgpt-transcript-t1t145-versus-ef4eb08-ppc-documents-closing-gap-002).

[INFO-001 §3](../03-enterprise-information/PPC-INFO-001_Enterprise_Ontology_Identity_and_Time.md) owns the complete P0/P1/P2 publication rows, source-record times, recipient availability and reader-as-of rule used by this draft.
