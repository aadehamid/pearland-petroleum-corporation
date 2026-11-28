// PO-10: Service-Side Policy Authorization, Separation of Duties, and One-Time Execution
// Governing authorities: ADR-0056 G3-b, AGENT-001 §1, PPC-REVIEW-004 PO-10
// Verified with `quint verify --invariant safety_all`.
module po10_policy_authorization {
  type PropId = str
  type Actor = str
  type Branch = str
  type Digest = str

  var proposals: PropId -> { proposer: Actor, cls: str, branch: Branch, digest: Digest }
  var authorizations: PropId -> { approver: Actor, branch: Branch, digest: Digest }
  var receipts: Set[PropId]
  var denied_attempts: int

  action init = all {
    proposals' = Map(
      "P_OK" -> { proposer: "agent1", cls: "REQUIRE_APPROVAL", branch: "b1", digest: "D1" },
      "P_PROHIB" -> { proposer: "agent1", cls: "PROHIBITED", branch: "b1", digest: "D2" }
    ),
    authorizations' = Map(),
    receipts' = Set(),
    denied_attempts' = 0,
  }

  // Attempt authorization for any proposal/actor; denied attempts leave authorizations unchanged
  action try_authorize(pid: PropId, approver: Actor, approver_is_agent: bool, br: Branch, dig: Digest): bool =
    if (
      pid.in(proposals.keys())
      and proposals.get(pid).cls != "PROHIBITED"
      and (not(approver_is_agent))
      and approver != proposals.get(pid).proposer
      and br == proposals.get(pid).branch
      and dig == proposals.get(pid).digest
    ) all {
      authorizations' = authorizations.put(pid, { approver: approver, branch: br, digest: dig }),
      proposals' = proposals,
      receipts' = receipts,
      denied_attempts' = denied_attempts,
    } else all {
      authorizations' = authorizations,
      proposals' = proposals,
      receipts' = receipts,
      denied_attempts' = denied_attempts + 1,
    }

  action try_execute(pid: PropId, br: Branch, dig: Digest): bool =
    if (
      pid.in(authorizations.keys())
      and not(pid.in(receipts))
      and proposals.get(pid).cls != "PROHIBITED"
      and authorizations.get(pid).branch == br
      and authorizations.get(pid).digest == dig
    ) all {
      receipts' = receipts.union(Set(pid)),
      proposals' = proposals,
      authorizations' = authorizations,
      denied_attempts' = denied_attempts,
    } else all {
      receipts' = receipts,
      proposals' = proposals,
      authorizations' = authorizations,
      denied_attempts' = denied_attempts + 1,
    }

  action step = any {
    try_authorize("P_OK", "shift_sup", false, "b1", "D1"),
    try_authorize("P_OK", "agent1", true, "b1", "D1"),
    try_authorize("P_OK", "shift_sup", false, "b2", "D1"),
    try_authorize("P_PROHIB", "shift_sup", false, "b1", "D2"),
    try_execute("P_OK", "b1", "D1"),
    try_execute("P_OK", "b1", "D_MUTATED"),
    try_execute("P_PROHIB", "b1", "D2"),
  }

  val prohibited_never_executed = not("P_PROHIB".in(receipts))
  val separation_of_duties = authorizations.keys().forall(pid =>
    authorizations.get(pid).approver != proposals.get(pid).proposer
  )
  val safety_all = prohibited_never_executed and separation_of_duties
}
