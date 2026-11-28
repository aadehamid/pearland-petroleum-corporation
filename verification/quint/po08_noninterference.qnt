// PO-08: Temporal and Permission Non-Interference for Reader-as-of Selection
// Governing authorities: INFO-001 §3, DATA-001 §2, PPC-REVIEW-004 PO-08
module po08_noninterference {
  type Role = str
  type Pub = { pub_id: str, pub_time: int, allowed: Set[Role], retracted: bool, secret_val: int }

  var pubs_world_1: Set[Pub]
  var pubs_world_2: Set[Pub]
  var cutoff: int
  var reader_role: Role

  pure def visible(pubs: Set[Pub], role: Role, t_cut: int): Set[Pub] =
    pubs.filter(p => role.in(p.allowed) and p.pub_time <= t_cut and not(p.retracted))

  action init = all {
    cutoff' = 1000,
    reader_role' = "planner",
    // World 1 and World 2 agree on all visible records, differing ONLY on restricted & post-cutoff records
    pubs_world_1' = Set(
      { pub_id: "S2-P1", pub_time: 930, allowed: Set("planner", "analyst"), retracted: false, secret_val: 1 },
      { pub_id: "S2-P2", pub_time: 1300, allowed: Set("planner", "analyst"), retracted: false, secret_val: 2 },
      { pub_id: "RESTRICTED-1", pub_time: 900, allowed: Set("admin"), retracted: false, secret_val: 100 }
    ),
    pubs_world_2' = Set(
      { pub_id: "S2-P1", pub_time: 930, allowed: Set("planner", "analyst"), retracted: false, secret_val: 1 },
      { pub_id: "S2-P2", pub_time: 1300, allowed: Set("planner", "analyst"), retracted: false, secret_val: 999 },
      { pub_id: "RESTRICTED-1", pub_time: 900, allowed: Set("admin"), retracted: false, secret_val: 777 }
    ),
  }

  action step = all {
    pubs_world_1' = pubs_world_1,
    pubs_world_2' = pubs_world_2,
    cutoff' = cutoff,
    reader_role' = reader_role,
  }

  // Non-interference invariant: changing restricted or post-cutoff records never alters reader-visible set
  val non_interference =
    visible(pubs_world_1, reader_role, cutoff) == visible(pubs_world_2, reader_role, cutoff)
}
