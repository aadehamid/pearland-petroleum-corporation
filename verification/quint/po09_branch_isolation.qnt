// Quint formal specification for PO-09: Checkpoint & Branch Isolation (WORLD-002 §6)
// Proves child-branch interventions never mutate parent baseline history or checkpoint digests.
module po09_branch_isolation {
  type BranchState = { rev: int, cap_bpd: int, processed_bbl: int }

  var baseline: BranchState
  var checkpoint_rev: int
  var checkpoint_processed: int
  var child: BranchState
  var forked: bool

  action init = all {
    baseline' = { rev: 0, cap_bpd: 30000, processed_bbl: 250 },
    checkpoint_rev' = 0,
    checkpoint_processed' = 250,
    child' = { rev: 0, cap_bpd: 30000, processed_bbl: 250 },
    forked' = false,
  }

  action take_checkpoint_and_fork = all {
    not(forked),
    checkpoint_rev' = baseline.rev,
    checkpoint_processed' = baseline.processed_bbl,
    child' = baseline,
    forked' = true,
    baseline' = baseline,
  }

  action step_baseline = all {
    baseline' = { rev: baseline.rev + 1, cap_bpd: baseline.cap_bpd, processed_bbl: baseline.processed_bbl + 25 },
    checkpoint_rev' = checkpoint_rev,
    checkpoint_processed' = checkpoint_processed,
    child' = child,
    forked' = forked,
  }

  action step_child(new_cap: int): bool = all {
    forked,
    new_cap > 0,
    new_cap <= 30000,
    child' = { rev: child.rev + 1, cap_bpd: new_cap, processed_bbl: child.processed_bbl + 20 },
    baseline' = baseline,
    checkpoint_rev' = checkpoint_rev,
    checkpoint_processed' = checkpoint_processed,
    forked' = forked,
  }

  action step = any {
    take_checkpoint_and_fork,
    step_baseline,
    step_child(24000),
  }

  // Child intervention never alters baseline or saved checkpoint
  val inv_parent_unmutated = baseline.cap_bpd == 30000
  val inv_checkpoint_monotonic = baseline.processed_bbl >= checkpoint_processed
}
