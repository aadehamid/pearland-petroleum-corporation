// PO-10: Service-Side Policy Authorization, Separation of Duties, and One-Time Execution
// Governing authorities: ADR-0056 G3-b, AGENT-001 §1, PPC-REVIEW-004 PO-10
module po10_policy_authorization {
  type PropId = str
  type Actor = str
  type Branch = str
  type Digest = str

  var proposals: PropId -> { proposer: Actor, cls: str, branch: Branch, digest: Digest }
  var authorizations: PropId -> { approver: Actor, branch: Branch, digest: Digest }
  var receipts: Set[PropId]

  action init = all {
    proposals' = Map(
      "P_OK" -> { proposer: "agent1", cls: "REQUIRE_APPROVAL", branch: "b1", digest: "D1" },
      "P_PROHIB" -> { proposer: "agent1", cls: "PROHIBITED", branch: "b1", digest: "D2" }
    ),
    authorizations' = Map(),
    receipts' = Set(),
  }

  action authorize(pid: PropId, approver: Actor, br: Branch, dig: Digest) = all {
    pid.in(proposals.keys()),
    proposals.get(pid).cls != "PROHIBITED",
    approver != proposals.get(pid).proposer,
    approver != "agent1",
    br == proposals.get(pid).branch,
    dig == proposals.get(pid).digest,
    authorizations' = authorizations.put(pid, { approver: approver, branch: br, digest: dig }),
    proposals' = proposals,
    receipts' = receipts,
  }

  action execute(pid: PropId, br: Branch, dig: Digest) = all {
    pid.in(authorizations.keys()),
    not(pid.in(receipts)),
    proposals.get(pid).cls != "PROHIBITED",
    authorizations.get(pid).branch == br,
    authorizations.get(pid).digest == dig,
    receipts' = receipts.union(Set(pid)),
    proposals' = proposals,
    authorizations' = authorizations,
  }

  action step = any {
    authorize("P_OK", "shift_sup", "b1", "D1"),
    execute("P_OK", "b1", "D1"),
  }

  val prohibited_never_executed = not("P_PROHIB".in(receipts))
  val separation_of_duties = authorizations.keys().forall(pid =>
    authorizations.get(pid).approver != proposals.get(pid).proposer
  )
}
