# PPC-AGENT-001 — Agent Tools and Consequential Actions

Inspected PPC baseline: [`01027a84be5d453cbb4e2ea091e4884729918b15`](../registers/PPC-SOURCE-REGISTER.md). This commit is the original PPC source-inspection reference, not this draft's content revision or owner approval. Later linked specifications are read at the current branch revision.

| Control | Value |
|---|---|
| ID / status | PPC-AGENT-001 / proposed draft, 0.1.0, 2026-11-25 |
| Authority | [PPC-012](../../PPC-012_Intelligent_Automation_Agent_and_User_Experience.md), [PPC-016](../../PPC-016_Evidence_Decision_Provenance_and_Evaluation_Architecture.md), [PPC-REG-001](../../PPC-REG-001_Architecture_Decision_Register.md) ADR-019, 020, 026, 029 |
| Contract | Role-scoped tool request → cited answer, simulated proposal or separately authorized action receipt |

## 1. Tool and authority boundary

An agent may retrieve authorized evidence, traverse a scoped graph, request governed calculations, simulate an isolated branch and recommend an option. It cannot calculate an official KPI in prose, read hidden truth during blind evaluation or turn its recommendation into approval. LangGraph and Langfuse remain baseline choices in PPC-012. Pydantic AI and OpenTelemetry/Logfire are candidates. Framework selection does not change the action policy.

`ToolRequest` has request ID, effective time, actor and delegated role, purpose, tool and contract version, branch, release IDs, knowledge cutoff, input digest, requested action and expiry. `ToolResponse` has result ID/status, request ID, branch ID, knowledge cutoff, provenance class, epistemic status, output classification, source/model refs, uncertainty, redaction status and audit ID. `ActionProposal` has proposal ID, payload digest, status, authority class, proposing actor, knowledge cutoff, measurement basis and binds exact action type, target, quantity/unit, branch, expected source revisions, policy version, approver role, evidence release, expiry and idempotency key. `ActionAuthorization` has authorization ID and authorized-at time and identifies `proposal_id`, `proposal_payload_digest`, `branch_id`, `authorization_expiry`, the human/role, scope, policy check, decision and signature or equivalent audit evidence. `ActionReceipt` has receipt ID, proposal and authorization IDs, idempotency key, source revisions, execution status and time, business effect ID or blocked reason, and branch. A tool cannot broaden an actor's scope.

Proposal transitions areDecision dossiers in [EVID-001 §2](../04-source-integration/PPC-EVID-001_Evidence_and_Decision_Context.md) use `OPEN → RECOMMENDED|DEFERRED|ESCALATED|EXPIRED`, `RECOMMENDED → APPROVED|REJECTED|DEFERRED|ESCALATED|EXPIRED`, and `APPROVED → EXECUTED|FAILED|EXPIRED`. A policy-checked, explicitly preapproved bounded decision may use `RECOMMENDED → AUTO_EXECUTED|FAILED`. `DEFERRED`, `REJECTED`, `ESCALATED`, `EXPIRED`, `EXECUTED`, `AUTO_EXECUTED` and `FAILED` are terminal for that decision ID. Execution blocked by a full receiving tank records `FAILED` and no stock change. A new attempt needs a new decision ID and authority. These decision states are distinct from proposal states below.  `DRAFT → POLICY_CHECKED|DENIED|EXPIRED`, `POLICY_CHECKED → RECOMMENDED|DENIED|ESCALATED|EXPIRED`, `RECOMMENDED → APPROVED|DENIED|ESCALATED|EXPIRED`, and `APPROVED → EXECUTED|FAILED|EXPIRED`. A bounded, reversible, preapproved class may follow `POLICY_CHECKED → AUTO_EXECUTED|FAILED`. `DENIED`, `ESCALATED`, `EXPIRED`, `EXECUTED`, `AUTO_EXECUTED` and `FAILED` are terminal for that proposal. Retry after a terminal state requires a new proposal and authorization. Execution requires a current policy check, exact approved payload, valid source revision and one-time business key. A changed quantity or target invalidates approval. `AUTO_EXECUTE` is only for an explicitly preapproved, bounded, reversible action class. `RECOMMEND`, `REQUIRE_APPROVAL` and `ESCALATE` follow PPC-012. An uncertain source or unavailable approver blocks consequential execution.

## 2. Synthetic action fixture

At 10:30 UTC an agent sees an `ESTIMATED` ULSD shortfall on the derate branch and proposes a `SCENARIO_ASSUMPTION` transfer of 5,000 bbl from terminal T. The graph path supplies potential exposure; the planning tool checks inventory and route bounds. The agent may simulate it and recommend it. If policy requires a Commercial Manager, the agent returns `REQUIRE_APPROVAL`. Only that role's authorization for this exact transfer permits execution. A duplicate execution request with the same key returns the original receipt; a different payload with that key is rejected. If the approval expires or inventory revision changes, recheck and request new authority. A baseline branch action cannot use a derate branch approval.

For the historical decision check, use [INFO-001 §3](../03-enterprise-information/PPC-INFO-001_Enterprise_Ontology_Identity_and_Time.md). The tool must pass the same recipient, channel, purpose and cutoff to evidence, graph and product queries. It must not disclose an inaccessible publication in results, traces or errors.

## 3. Qualification and decisions

Test allowed read/simulate/recommend scopes, policy denial, approval replay, exact-payload binding, stale source revision, duplicate/conflicting key, crash after execution, branch isolation, historical cutoff, hidden-truth and restricted-trace leaks. Preserve tool calls, policy versions, approval evidence and expected/observed receipts. No agent evaluation is claimed. Open choices include framework, action-class thresholds, trace retention and human approval channel. T26, T31, T116–118 in the [discussion register](../registers/PPC-Discussion-Decision-Traceability.md) support the proposal.

The [exchange register](../registers/PPC-Discussion-Decision-Traceability.md) routes T116–118 to this draft. This is topic-level routing; GAP-002 item and original-asset checks remain open.

[INFO-001 §3](../03-enterprise-information/PPC-INFO-001_Enterprise_Ontology_Identity_and_Time.md) owns the complete P0/P1/P2 publication rows, source-record times, recipient availability and reader-as-of rule used by this draft.
