#!/usr/bin/env python3
"""ENG-V08b and PO-10 Security, RBAC, Policy Gate, and Offline Recorded-Response Agent Tests (WP-3B)."""
from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from api.auth_and_context import AuthRBACStore
from automation.offline_agent import RecordedResponseAgentAdapter
from policy.engine import PolicyGateService, canonical_digest

REPO_ROOT = Path(__file__).resolve().parents[1]
THRESHOLDS = REPO_ROOT / "schemas" / "policy_thresholds.yaml"
RECORDED_FIXTURE = REPO_ROOT / "fixtures" / "golden" / "agent_recorded_responses" / "scn_a_t125_recorded.json"


class TestWP3BPolicyAuthAndOfflineAgent(unittest.TestCase):
    def test_po10_policy_gate_negative_security_battery(self):
        t0 = datetime(2026, 6, 15, 8, 40, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory(prefix="ppc-wp3b-pol-") as tmp:
            gate = PolicyGateService(THRESHOLDS, Path(tmp) / "policy.db")
            try:
                # 1. PROHIBITED action MUST return DENIED and cannot be authorized or executed
                p_prohib = gate.submit_proposal(
                    proposal_id="PROP-PROHIB",
                    branch_id="baseline",
                    action_type="release_lot_from_quality_hold",
                    proposer_id="usr-agent-1",
                    proposer_is_agent=True,
                    payload={"lot_id": "LOT-1"},
                    metrics={"margin_effect_usd": 1000.0},
                    now_utc=t0,
                )
                self.assertEqual(p_prohib["policy_result"], "DENIED")
                auth_prohib = gate.authorize_proposal(
                    auth_id="AUTH-PROHIB",
                    proposal_id="PROP-PROHIB",
                    approver_id="usr-vp-ops",
                    approver_role="VP Supply and Operations",
                    approver_is_agent=False,
                    branch_id="baseline",
                    payload_digest=p_prohib["payload_digest"],
                    now_utc=t0,
                )
                self.assertEqual(auth_prohib["status"], "DENIED")
                exec_prohib = gate.execute_authorized_action(
                    idempotency_key="IDEM-PROHIB",
                    proposal_id="PROP-PROHIB",
                    auth_id=None,
                    branch_id="baseline",
                    payload={"lot_id": "LOT-1"},
                    now_utc=t0,
                )
                self.assertEqual(exec_prohib["status"], "DENIED")

                # 2. Tier-1 proposal: valid submission
                payload = {"unit": "4B", "feed_bbl_per_day": 28500.0}
                p1 = gate.submit_proposal(
                    proposal_id="PROP-T1",
                    branch_id="child-1",
                    action_type="feed_rate_change_inside_envelope",
                    proposer_id="usr-planner",
                    proposer_is_agent=False,
                    payload=payload,
                    metrics={"margin_effect_usd": 185000.0, "rate_change_bbl_per_day": 1500.0},
                    now_utc=t0,
                )
                self.assertEqual(p1["tier"], 1)
                self.assertEqual(p1["required_approver_role"], "Shift Supervisor")

                # Negative: proposer self-approval DENIED
                self.assertEqual(
                    gate.authorize_proposal(
                        auth_id="A-SELF",
                        proposal_id="PROP-T1",
                        approver_id="usr-planner",
                        approver_role="Shift Supervisor",
                        approver_is_agent=False,
                        branch_id="child-1",
                        payload_digest=p1["payload_digest"],
                        now_utc=t0,
                    )["reason"],
                    "PROPOSER_CANNOT_APPROVE",
                )
                # Negative: agent approval DENIED
                self.assertEqual(
                    gate.authorize_proposal(
                        auth_id="A-AGENT",
                        proposal_id="PROP-T1",
                        approver_id="usr-agent-1",
                        approver_role="Shift Supervisor",
                        approver_is_agent=True,
                        branch_id="child-1",
                        payload_digest=p1["payload_digest"],
                        now_utc=t0,
                    )["reason"],
                    "AGENT_CANNOT_APPROVE",
                )
                # Negative: wrong role DENIED
                self.assertEqual(
                    gate.authorize_proposal(
                        auth_id="A-ROLE",
                        proposal_id="PROP-T1",
                        approver_id="usr-comm-mgr",
                        approver_role="Commercial Manager",
                        approver_is_agent=False,
                        branch_id="child-1",
                        payload_digest=p1["payload_digest"],
                        now_utc=t0,
                    )["status"],
                    "DENIED",
                )
                # Negative: cross-branch approval DENIED
                self.assertEqual(
                    gate.authorize_proposal(
                        auth_id="A-BRANCH",
                        proposal_id="PROP-T1",
                        approver_id="usr-shift-sup",
                        approver_role="Shift Supervisor",
                        approver_is_agent=False,
                        branch_id="baseline",
                        payload_digest=p1["payload_digest"],
                        now_utc=t0,
                    )["reason"],
                    "CROSS_BRANCH_APPROVAL_FORBIDDEN",
                )

                # Valid authorization by Shift Supervisor
                auth_ok = gate.authorize_proposal(
                    auth_id="AUTH-T1-OK",
                    proposal_id="PROP-T1",
                    approver_id="usr-shift-sup",
                    approver_role="Shift Supervisor",
                    approver_is_agent=False,
                    branch_id="child-1",
                    payload_digest=p1["payload_digest"],
                    now_utc=t0 + timedelta(minutes=5),
                )
                self.assertEqual(auth_ok["status"], "AUTHORIZED")

                # Negative: mutated payload rejected
                self.assertEqual(
                    gate.execute_authorized_action(
                        idempotency_key="IDEM-MUT",
                        proposal_id="PROP-T1",
                        auth_id="AUTH-T1-OK",
                        branch_id="child-1",
                        payload={"unit": "4B", "feed_bbl_per_day": 39999.0},
                        now_utc=t0 + timedelta(minutes=6),
                    )["reason"],
                    "MUTATED_PAYLOAD_REJECTED",
                )
                # Negative: expired authorization rejected (>30 min)
                self.assertEqual(
                    gate.execute_authorized_action(
                        idempotency_key="IDEM-EXP",
                        proposal_id="PROP-T1",
                        auth_id="AUTH-T1-OK",
                        branch_id="child-1",
                        payload=payload,
                        now_utc=t0 + timedelta(minutes=35),
                    )["reason"],
                    "AUTHORIZATION_EXPIRED",
                )
                # Valid execution + idempotent replay
                ex1 = gate.execute_authorized_action(
                    idempotency_key="IDEM-T1-1",
                    proposal_id="PROP-T1",
                    auth_id="AUTH-T1-OK",
                    branch_id="child-1",
                    payload=payload,
                    now_utc=t0 + timedelta(minutes=10),
                )
                self.assertEqual(ex1["status"], "EXECUTED")
                ex2 = gate.execute_authorized_action(
                    idempotency_key="IDEM-T1-1",
                    proposal_id="PROP-T1",
                    auth_id="AUTH-T1-OK",
                    branch_id="child-1",
                    payload=payload,
                    now_utc=t0 + timedelta(minutes=11),
                )
                self.assertEqual(ex2["status"], "IDEMPOTENT_REPLAY")
                self.assertEqual(canonical_digest(payload), p1["payload_digest"])
            finally:
                gate.close()

    def test_auth_rbac_ignores_forged_role_header_and_offline_agent_redacts_otel(self):
        with tempfile.TemporaryDirectory(prefix="ppc-wp3b-auth-") as tmp:
            store = AuthRBACStore(Path(tmp) / "auth.db", signing_secret="test-secret-key-at-least-16-bytes")
            try:
                self.assertEqual(store.seed_fixture_accounts("fixture-pass-123"), 7)
                tok = store.issue_token("planner_1", "fixture-pass-123")
                self.assertIsNotNone(tok)
                assert tok is not None
                # Forged X-Role header MUST be ignored in favor of DB role_assignments
                ctx = store.authenticate_request(tok, headers={"X-Role": "VP Supply and Operations"})
                self.assertIsNotNone(ctx)
                assert ctx is not None
                self.assertEqual(ctx["roles"], ["Planner"])
                # Tampered token rejected
                self.assertIsNone(store.authenticate_request(tok + "tamper"))
            finally:
                store.close()

        adapter = RecordedResponseAgentAdapter(RECORDED_FIXTURE)
        res = adapter.run_investigation("SCN-A-T125", "2026-06-15T08:40:00Z", "Planner")
        self.assertEqual(res["potential_exposure_paths"][0]["badge"], "POTENTIAL_EXPOSURE")
        self.assertEqual(res["model_quantified_cards"][0]["badge"], "MODEL_QUANTIFIED")
        trace_blob = json.dumps(res["otel_span"])
        self.assertNotIn("SHOULD_NEVER_APPEAR_IN_TRACE", trace_blob)
        self.assertEqual(res["otel_span"]["restricted_payload"], "[REDACTED]")


if __name__ == "__main__":
    unittest.main()
