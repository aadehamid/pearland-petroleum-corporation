#!/usr/bin/env python3
"""Verification tests for WP-4A R2 op-budget (C9), RECOVERY_GAP checker, and stub restore drill."""
from __future__ import annotations

import unittest

from infra.backup.r2_op_budget_check import SyncStreamSpec, evaluate_r2_op_budget
from infra.backup.recovery_gap_checker import check_recovery_gaps
from infra.backup.stub_restore_drill import run_sqlite_stub_restore_drill


class TestWP4ABackupAndRecovery(unittest.TestCase):
    def test_c9_slice1_60s_backup_cadence_stays_inside_r2_free_tier(self):
        report = evaluate_r2_op_budget()
        self.assertEqual(report["provenance_class"], "ESTIMATED")
        self.assertEqual(report["status"], "PASSED")
        self.assertTrue(report["within_free_tier"])
        self.assertTrue(report["within_safety_margin"])
        self.assertLess(report["total_monthly_class_a_ops"], 500_000)

        # Safety-margin-only zone (between 500k and 1M) must be distinguished from free-tier exceeded
        margin_only = evaluate_r2_op_budget(
            streams=(SyncStreamSpec("mid_freq", 30, 6, "535k ops/month"),),
        )
        self.assertTrue(margin_only["within_free_tier"])
        self.assertFalse(margin_only["within_safety_margin"])
        self.assertEqual(margin_only["status"], "SAFETY_MARGIN_EXCEEDED")

        # Aggressive 1-second sync must be flagged as FREE_TIER_EXCEEDED
        bad = evaluate_r2_op_budget(streams=(SyncStreamSpec("too_fast", 1, 1, "1s flood"),))
        self.assertEqual(bad["status"], "FREE_TIER_EXCEEDED")
        self.assertFalse(bad["within_free_tier"])

    def test_recovery_gap_checker_detects_missing_receipts_tail_loss_holes_dups_and_conflicts(self):
        outbox = [
            {"source_system": "refinery_sqlite", "branch_id": "baseline", "partition_key": "default", "source_sequence": 1, "delivery_key": "k1", "payload_digest": "d1"},
            {"source_system": "refinery_sqlite", "branch_id": "baseline", "partition_key": "default", "source_sequence": 2, "delivery_key": "k2", "payload_digest": "d2"},
        ]
        inbox = [dict(r) for r in outbox]
        r2_ok = {("refinery_sqlite", "baseline", "default"): 2}
        clean_res = check_recovery_gaps(outbox, inbox, r2_raw_high_water=r2_ok)
        self.assertEqual(clean_res["status"], "CLEAN")
        self.assertEqual(clean_res["r2_evidence_consulted_streams"], ["refinery_sqlite:baseline:default"])

        # 0. Missing, zero/lagging, or negative R2 raw-log evidence MUST fail closed (PPC-REVIEW-003 §2)
        no_r2 = check_recovery_gaps(outbox, inbox, r2_raw_high_water={})
        self.assertEqual(no_r2["status"], "RECOVERY_GAP")
        self.assertTrue(any(g["kind"] == "RECOVERY_GAP_MISSING_R2_EVIDENCE" for g in no_r2["gaps"]))
        zero_r2 = check_recovery_gaps(outbox, inbox, r2_raw_high_water={("refinery_sqlite", "baseline", "default"): 0})
        self.assertEqual(zero_r2["status"], "RECOVERY_GAP")
        self.assertTrue(any(g["kind"] == "RECOVERY_GAP_R2_LAGS_OUTBOX" for g in zero_r2["gaps"]))
        with self.assertRaises(ValueError):
            check_recovery_gaps(outbox, inbox, r2_raw_high_water={("refinery_sqlite", "baseline", "default"): -1})
        # Full-scope check (expected_streams=None) MUST halt if R2 proves a totally lost OR hw=0 second stream!
        mixed_loss = check_recovery_gaps(
            outbox,
            inbox,
            r2_raw_high_water={("refinery_sqlite", "baseline", "default"): 2, ("other_store", "baseline", "p"): 9},
        )
        self.assertEqual(mixed_loss["status"], "RECOVERY_GAP")
        self.assertTrue(any(g["kind"] == "RECOVERY_GAP_MISSING_OUTBOX_VS_R2" for g in mixed_loss["gaps"]))
        zero_other = check_recovery_gaps(
            outbox,
            inbox,
            r2_raw_high_water={("refinery_sqlite", "baseline", "default"): 2, ("other_store", "baseline", "p"): 0},
        )
        self.assertEqual(zero_other["status"], "RECOVERY_GAP")
        self.assertTrue(any(g["kind"] == "RECOVERY_GAP_MISSING_R2_EVIDENCE" for g in zero_other["gaps"]))
        # Explicit partial-store restore scope (expected_streams) tracks other R2 streams without false halt
        partial_ok = check_recovery_gaps(
            outbox,
            inbox,
            r2_raw_high_water={("refinery_sqlite", "baseline", "default"): 2, ("other_store", "baseline", "p"): 9},
            expected_streams=[("refinery_sqlite", "baseline", "default")],
        )
        self.assertEqual(partial_ok["status"], "CLEAN")
        self.assertEqual(partial_ok["out_of_scope_r2_streams"], ["other_store:baseline:p"])
        # Malformed expected_streams or missing binding fields MUST raise loudly
        with self.assertRaises(ValueError):
            check_recovery_gaps([], [], {("s", "b", "p"): 1}, expected_streams=["abc"])  # type: ignore[list-item]
        with self.assertRaises(ValueError):
            check_recovery_gaps(
                [{"source_system": "s", "branch_id": "b", "partition_key": "p", "source_sequence": 1}],
                [{"source_system": "s", "branch_id": "b", "partition_key": "p", "source_sequence": 1}],
                r2_raw_high_water={("s", "b", "p"): 1},
            )

        # 1. Missing receipt for seq 2 -> RECOVERY_GAP_UNAPPLIED_OUTBOX
        missing = check_recovery_gaps(outbox, inbox[:1], r2_raw_high_water=r2_ok)
        self.assertEqual(missing["status"], "RECOVERY_GAP")
        self.assertEqual(missing["gaps"][0]["kind"], "RECOVERY_GAP_UNAPPLIED_OUTBOX")

        # 2. Lost outbox tail (inbox has seq 1..3, restored outbox truncated at 1..2) -> RECOVERY_GAP_MISSING_OUTBOX_TAIL
        inbox_tail = inbox + [
            {"source_system": "refinery_sqlite", "branch_id": "baseline", "partition_key": "default", "source_sequence": 3, "delivery_key": "k3", "payload_digest": "d3"}
        ]
        tail_loss = check_recovery_gaps(outbox, inbox_tail, r2_raw_high_water=r2_ok)
        self.assertEqual(tail_loss["status"], "RECOVERY_GAP")
        self.assertTrue(any(g["kind"] == "RECOVERY_GAP_MISSING_OUTBOX_TAIL" for g in tail_loss["gaps"]))

        # 3. R2 raw log proves higher sequence than restored outbox -> RECOVERY_GAP_MISSING_OUTBOX_VS_R2
        r2_tail = check_recovery_gaps(outbox, inbox, r2_raw_high_water={("refinery_sqlite", "baseline", "default"): 4})
        self.assertEqual(r2_tail["status"], "RECOVERY_GAP")
        self.assertTrue(any(g["kind"] == "RECOVERY_GAP_MISSING_OUTBOX_VS_R2" for g in r2_tail["gaps"]))
        with self.assertRaises(ValueError):
            check_recovery_gaps(outbox, inbox, r2_raw_high_water={("refinery_sqlite", "baseline"): 4})  # type: ignore[dict-item]

        # 4. Cross-sequence delivery_key reuse with different digest MUST fail as conflict (PPC-INT-001 §2)
        reused_key_outbox = [
            {"source_system": "s", "branch_id": "b", "partition_key": "p", "source_sequence": 1, "delivery_key": "k1", "payload_digest": "d1"},
            {"source_system": "s", "branch_id": "b", "partition_key": "p", "source_sequence": 2, "delivery_key": "k1", "payload_digest": "d2"},
        ]
        reused_res = check_recovery_gaps(reused_key_outbox, [dict(r) for r in reused_key_outbox], r2_raw_high_water={("s", "b", "p"): 2})
        self.assertEqual(reused_res["status"], "RECOVERY_GAP")
        self.assertTrue(any(c["kind"] == "PAYLOAD_DIGEST_CONFLICT" for c in reused_res["conflicts"]))

        # 5. Sequence hole (1 -> 3) -> RECOVERY_GAP_SEQUENCE_HOLE
        hole_outbox = [outbox[0], {**outbox[1], "source_sequence": 3, "delivery_key": "k3"}]
        hole_inbox = [inbox[0], {**inbox[1], "source_sequence": 3, "delivery_key": "k3"}]
        hole = check_recovery_gaps(hole_outbox, hole_inbox, r2_raw_high_water={("refinery_sqlite", "baseline", "default"): 3})
        self.assertEqual(hole["status"], "RECOVERY_GAP")
        self.assertTrue(any(g["kind"] == "RECOVERY_GAP_SEQUENCE_HOLE" for g in hole["gaps"]))

        # 6. Delivery key mismatch at same sequence -> DELIVERY_KEY_MISMATCH
        dkey_bad = check_recovery_gaps(outbox, [inbox[0], {**inbox[1], "delivery_key": "k2-other"}], r2_raw_high_water=r2_ok)
        self.assertEqual(dkey_bad["status"], "RECOVERY_GAP")
        self.assertTrue(any(c["kind"] == "DELIVERY_KEY_MISMATCH" for c in dkey_bad["conflicts"]))

        # 7. Duplicate outbox sequence with distinct delivery_key -> duplicate_outbox
        dup_outbox = outbox + [{**outbox[0], "delivery_key": "k1-dup"}]
        dup_res = check_recovery_gaps(dup_outbox, inbox, r2_raw_high_water=r2_ok)
        self.assertEqual(dup_res["status"], "RECOVERY_GAP")
        self.assertEqual(len(dup_res["duplicate_outbox"]), 1)

        # 8. Digest conflict -> PAYLOAD_DIGEST_CONFLICT
        conflict = check_recovery_gaps(outbox, [inbox[0], {**inbox[1], "payload_digest": "DIFFERENT"}], r2_raw_high_water=r2_ok)
        self.assertEqual(conflict["status"], "RECOVERY_GAP")
        self.assertEqual(conflict["conflicts"][0]["kind"], "PAYLOAD_DIGEST_CONFLICT")

        # 9. Multi-partition streams (same source+branch, distinct partition_key) MUST pass CLEAN (PPC-INT-001 §2)
        multi_part_outbox = [
            {"source_system": "refinery_sqlite", "branch_id": "baseline", "partition_key": "P1", "source_sequence": 1, "delivery_key": "k1:p1", "payload_digest": "d1"},
            {"source_system": "refinery_sqlite", "branch_id": "baseline", "partition_key": "P1", "source_sequence": 2, "delivery_key": "k2:p1", "payload_digest": "d2"},
            {"source_system": "refinery_sqlite", "branch_id": "baseline", "partition_key": "P2", "source_sequence": 1, "delivery_key": "k1:p2", "payload_digest": "d3"},
            {"source_system": "refinery_sqlite", "branch_id": "baseline", "partition_key": "P2", "source_sequence": 2, "delivery_key": "k2:p2", "payload_digest": "d4"},
        ]
        multi_part_inbox = [dict(r) for r in multi_part_outbox]
        multi_r2 = {("refinery_sqlite", "baseline", "P1"): 2, ("refinery_sqlite", "baseline", "P2"): 2}
        self.assertEqual(check_recovery_gaps(multi_part_outbox, multi_part_inbox, r2_raw_high_water=multi_r2)["status"], "CLEAN")

    def test_sqlite_stub_writer_corruption_and_restore_drill_passes(self):
        result = run_sqlite_stub_restore_drill(row_count=25)
        self.assertEqual(result["status"], "PASSED")
        self.assertEqual(result["provenance_class"], "SYNTHETIC")
        self.assertTrue(result["hash_equal"])
        self.assertEqual(result["stub_drill_scope"], "sqlite_only_baseline_not_wp4b_live_rto_proof")
        self.assertEqual(result["recovery_gap_status"], "CLEAN")
        self.assertLess(result["stub_drill_elapsed_seconds"], 60.0)


if __name__ == "__main__":
    unittest.main()
