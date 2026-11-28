#!/usr/bin/env python3
"""Tests for WP-6 Scenario B (S2-* crude-quality rejection & delayed lab correction restatement)."""
from __future__ import annotations

import unittest

from evaluations.scenario_b_slice import run_scenario_b_walkthrough


class TestWP6ScenarioB(unittest.TestCase):
    def test_scenario_b_s2_timeline_idempotency_and_zero_temporal_leakage(self):
        ev = run_scenario_b_walkthrough()
        self.assertEqual(ev["qualification_verdict"], "QUALIFIED_PROVISIONAL")
        # INT-RETRY-01: duplicate S2-M1 produces exactly 500 bbl, never 1000 bbl
        self.assertAlmostEqual(ev["tank_tk101h_bbl"], 500.0, places=9)
        self.assertEqual(ev["m1_outcomes"]["first"], "APPLIED")
        self.assertEqual(ev["m1_outcomes"]["duplicate"], "IDEMPOTENT_DUPLICATE")
        self.assertEqual(ev["m1_outcomes"]["conflict"], "CONFLICT_QUARANTINED")
        # 10:00 decision S2-D1 sees failed S2-P1 + S2-L1; 13:15 sees corrected S2-P2 + S2-L2
        self.assertEqual(ev["decision_s2_d1_1000"]["publication_id"], "S2-P1")
        self.assertEqual(ev["decision_s2_d1_1000"]["release_id"], "S2-L1")
        self.assertEqual(ev["decision_s2_d1_1000"]["disposition"], "QUALITY_HOLD")
        self.assertEqual(ev["restated_1315"]["publication_id"], "S2-P2")
        self.assertEqual(ev["restated_1315"]["release_id"], "S2-L2")
        self.assertEqual(ev["restated_1315"]["disposition"], "RELEASE")
        # Replay at 10:00 after 13:15 restatement NEVER leaks S2-P2 or S2-L2
        self.assertTrue(ev["replay_exact_match"])
        # Unauthorized role sees opaque UNRESOLVED
        self.assertEqual(ev["unauthorized_view"]["status"], "UNRESOLVED")


if __name__ == "__main__":
    unittest.main()
