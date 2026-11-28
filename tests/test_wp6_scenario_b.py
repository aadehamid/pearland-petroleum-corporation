#!/usr/bin/env python3
"""Tests for WP-6 Scenario B (S2-* crude-quality rejection & delayed lab correction restatement)."""
from __future__ import annotations

import unittest

from evaluations.scenario_b_slice import run_scenario_b_walkthrough


class TestWP6ScenarioB(unittest.TestCase):
    def test_scenario_b_s2_timeline_idempotency_and_zero_temporal_leakage(self):
        ev = run_scenario_b_walkthrough()
        self.assertEqual(ev["qualification_verdict"], "QUALIFIED_PROVISIONAL")
        self.assertEqual(ev["provenance_class"], "SYNTHETIC")

        # INT-RETRY-01 & EQ-02: Crash Point 1 + duplicate S2-M1 yields exactly 500 bbl in TK-101H, never 1000 bbl
        self.assertAlmostEqual(ev["tank_tk101h_bbl"], 500.0, places=9)
        self.assertAlmostEqual(ev["tank_mass_residual_kg"], 0.0, places=9)
        self.assertEqual(ev["delta_movement_row_count"], 1)
        self.assertEqual(ev["quarantine_count"], 1)
        self.assertEqual(ev["m1_outcomes"]["first"], "APPLIED")
        self.assertEqual(ev["m1_outcomes"]["duplicate"], "IDEMPOTENT_DUPLICATE")
        self.assertEqual(ev["m1_outcomes"]["conflict"], "CONFLICT_QUARANTINED")
        self.assertEqual(ev["m1_outcomes"]["delta_publish"], "PUBLISHED")
        self.assertEqual(ev["m1_outcomes"]["delta_publish_retry"], "IDEMPOTENT_ALREADY_PUBLISHED")
        self.assertEqual(ev["watermarks"]["published_seq"], 1)

        # 10:00 decision S2-D1 sees failed S2-P1 + S2-L1; 13:05 (before S2-L2 cut) STILL sees S2-P1 + S2-L1
        self.assertEqual(ev["decision_s2_d1_1000"]["status"], "RESOLVED")
        self.assertEqual(ev["decision_s2_d1_1000"]["publication_id"], "S2-P1")
        self.assertEqual(ev["decision_s2_d1_1000"]["release_id"], "S2-L1")
        self.assertEqual(ev["decision_s2_d1_1000"]["payload"]["disposition"], "QUALITY_HOLD")

        self.assertEqual(ev["pre_release_1305"]["status"], "RESOLVED")
        self.assertEqual(ev["pre_release_1305"]["publication_id"], "S2-P1")
        self.assertEqual(ev["pre_release_1305"]["release_id"], "S2-L1")

        # 13:15 sees restated passing S2-P2 + S2-L2
        self.assertEqual(ev["restated_1315"]["status"], "RESOLVED")
        self.assertEqual(ev["restated_1315"]["publication_id"], "S2-P2")
        self.assertEqual(ev["restated_1315"]["release_id"], "S2-L2")
        self.assertEqual(ev["restated_1315"]["payload"]["disposition"], "RELEASE")

        # Replay at 10:00 after 13:15 restatement reproduces S2-D1 identically with ZERO leakage of S2-P2/S2-L2
        self.assertTrue(ev["replay_exact_match"])

        # Unauthorized role sees opaque UNRESOLVED with zero payload disclosure
        self.assertEqual(ev["unauthorized_view"]["status"], "UNRESOLVED")
        self.assertIsNone(ev["unauthorized_view"]["payload"])

        # Determinism check: second independent run produces identical evidence SHA-256
        ev2 = run_scenario_b_walkthrough()
        self.assertEqual(ev["evidence_sha256"], ev2["evidence_sha256"])


if __name__ == "__main__":
    unittest.main()
