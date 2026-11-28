#!/usr/bin/env python3
"""Offline tests for WP-4A R2 op budget check (C9), RECOVERY_GAP checker, and stub restore drill."""
from __future__ import annotations

import unittest

from infra.backup.r2_op_budget_check import SyncStreamSpec, evaluate_r2_op_budget
from infra.backup.recovery_gap_checker import check_recovery_gaps
from infra.backup.stub_restore_drill import run_sqlite_stub_restore_drill


class TestWP4ABackupAndRecovery(unittest.TestCase):
    def test_c9_slice1_60s_backup_cadence_stays_inside_r2_free_tier(self):
        report = evaluate_r2_op_budget()
        self.assertEqual(report["provenance_class"], "DERIVED")
        self.assertEqual(report["status"], "PASSED")
        self.assertTrue(report["within_free_tier"])
        self.assertTrue(report["within_safety_margin"])
        self.assertLess(report["total_monthly_class_a_ops"], 500_000)

        # Negative test: 1-second sync across 1 stream exceeds 1,000,000 Class A ops/month
        bad = evaluate_r2_op_budget([SyncStreamSpec("too_fast", 1, 1, "1s flood")])
        self.assertEqual(bad["status"], "EXCEEDED")
        self.assertFalse(bad["within_free_tier"])

    def test_recovery_gap_checker_detects_missing_receipts_holes_and_digest_conflicts(self):
        outbox = [
            {"source_system": "logistics_mysql", "branch_id": "baseline", "source_sequence": 1, "delivery_key": "k1", "payload_digest": "aaa"},
            {"source_system": "logistics_mysql", "branch_id": "baseline", "source_sequence": 2, "delivery_key": "k2", "payload_digest": "bbb"},
        ]
        inbox = [
            {"source_system": "logistics_mysql", "branch_id": "baseline", "source_sequence": 1, "delivery_key": "k1", "payload_digest": "aaa"},
            {"source_system": "logistics_mysql", "branch_id": "baseline", "source_sequence": 2, "delivery_key": "k2", "payload_digest": "bbb"},
        ]
        self.assertEqual(check_recovery_gaps(outbox, inbox)["status"], "CLEAN")

        # Missing InboxReceipt for sequence 2 -> RECOVERY_GAP
        missing = check_recovery_gaps(outbox, inbox[:1])
        self.assertEqual(missing["status"], "RECOVERY_GAP")
        self.assertEqual(missing["gaps"][0]["kind"], "RECOVERY_GAP_UNAPPLIED_OUTBOX")

        # Sequence hole (1 -> 3 skipping 2) -> RECOVERY_GAP_SEQUENCE_HOLE
        hole_out = [outbox[0], {**outbox[1], "source_sequence": 3, "delivery_key": "k3"}]
        hole_in = [inbox[0], {**inbox[1], "source_sequence": 3, "delivery_key": "k3"}]
        hole = check_recovery_gaps(hole_out, hole_in)
        self.assertEqual(hole["status"], "RECOVERY_GAP")
        self.assertEqual(hole["gaps"][0]["kind"], "RECOVERY_GAP_SEQUENCE_HOLE")

        # Digest mismatch -> PAYLOAD_DIGEST_CONFLICT
        bad_in = [inbox[0], {**inbox[1], "payload_digest": "CORRUPT"}]
        conflict = check_recovery_gaps(outbox, bad_in)
        self.assertEqual(conflict["status"], "RECOVERY_GAP")
        self.assertEqual(conflict["conflicts"][0]["kind"], "PAYLOAD_DIGEST_CONFLICT")

    def test_sqlite_stub_writer_corruption_and_restore_drill_passes(self):
        drill = run_sqlite_stub_restore_drill(row_count=30)
        self.assertEqual(drill["status"], "PASSED")
        self.assertTrue(drill["hash_equal"])
        self.assertTrue(drill["rto_within_1h_target"])
        self.assertEqual(drill["recovery_gap_status"], "CLEAN")


if __name__ == "__main__":
    unittest.main()
