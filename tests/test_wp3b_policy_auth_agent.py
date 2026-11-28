#!/usr/bin/env python3
"""ENG-V08b and PO-10 Security, RBAC, Policy Gate, and Offline Recorded-Response Agent Tests (WP-3B)."""
from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from api.auth_and_context import AuthRBACStore
from automation.offline_agent import RecordedResponseAgentAdapter, redact_otel_attributes
from policy.engine import PolicyGateService, canonical_digest

REPO_ROOT = Path(__file__).resolve().parents[1]
THRESHOLDS = REPO_ROOT / "schemas" / "policy_thresholds.yaml"
RECORDED_FIXTURE = REPO_ROOT / "fixtures" / "golden" / "agent_recorded_responses" / "scn_a_t125_recorded.json"


class TestWP3BPolicyAuthAndOfflineAgent(unittest.TestCase):
    def test_po10_policy_gate_negative_security_battery(self):
        t0 = datetime(2026, 6, 15, 8, 40, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory(prefix="ppc-wp3b-pol-") as tmp:
            gate = PolicyGateService(THRESHOLDS, Path(tmp) / "policy.db")
            auth = AuthRBACStore(Path(tmp) / "auth.db", signing_secret="test-signing-secret-32-bytes-long")
            try:
                self.assertEqual(auth.seed_fixture_accounts("strong-test-pass"), 7)
                # Second seed inserts 0 new rows (accurate rowcount)
                self.assertEqual(auth.seed_fixture_accounts("strong-test-pass"), 0)

                sup_tok = auth.issue_token("shift_supervisor", "strong-test-pass")
                agent_tok = auth.issue_token("ppc_agent_1", "strong-test-pass")
                self.assertIsNotNone(sup_tok)
                self.assertIsNotNone(agent_tok)

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
                self.assertEqual(p_prohib["authority_class"], "PROHIBITED")
                self.assertEqual(p_prohib["policy_result"], "DENIED")
                auth_prohib = gate.authorize_proposal_with_session(
                    auth_store=auth,
                    token=sup_tok,
                    auth_id="AUTH-PROHIB",
                    proposal_id="PROP-PROHIB",
                    branch_id="baseline",
                    payload_digest=p_prohib["payload_digest"],
                    now_utc=t0,
                )
                self.assertEqual(auth_prohib["status"], "DENIED")
                self.assertEqual(auth_prohib["reason"], "PROHIBITED_ACTION_CANNOT_BE_APPROVED")

                # 2. Payload-to-metrics smuggling MUST escalate (100,000 bbl/day payload cannot hide under 1,500 metrics)
                p_smuggle = gate.submit_proposal(
                    proposal_id="PROP-SMUGGLE",
                    branch_id="baseline",
                    action_type="feed_rate_change_inside_envelope",
                    proposer_id="usr-agent-1",
                    proposer_is_agent=True,
                    payload={"unit": "4B", "feed_bbl_per_day": 100000.0},
                    metrics={"margin_effect_usd": 1000.0, "rate_change_bbl_per_day": 1500.0, "rate_change_pct": 5.0},
                    now_utc=t0,
                )
                self.assertEqual(p_smuggle["authority_class"], "ESCALATE")

                # 3. Missing required rate_change_bbl_per_day MUST escalate (ADR-0056 missing_estimate_counts_as_exceeded)
                p_missing = gate.submit_proposal(
                    proposal_id="PROP-MISSING-RATE",
                    branch_id="baseline",
                    action_type="feed_rate_change_inside_envelope",
                    proposer_id="usr-agent-1",
                    proposer_is_agent=True,
                    payload={"unit": "4B", "feed_bbl_per_day": 28500.0},
                    metrics={"margin_effect_usd": 1000.0},
                    now_utc=t0,
                )
                self.assertEqual(p_missing["authority_class"], "ESCALATE")

                # 4. Tier 1 proposal with complete, consistent metrics
                payload = {
                    "unit": "4B",
                    "baseline_feed_bbl_per_day": 30000.0,
                    "feed_bbl_per_day": 28500.0,
                    "rate_change_bbl_per_day": 1500.0,
                    "rate_change_pct": 5.0,
                }
                p1 = gate.submit_proposal(
                    proposal_id="PROP-T1",
                    branch_id="baseline",
                    action_type="feed_rate_change_inside_envelope",
                    proposer_id="usr-agent-1",
                    proposer_is_agent=True,
                    payload=payload,
                    metrics={"margin_effect_usd": 185000.0, "rate_change_bbl_per_day": 1500.0, "rate_change_pct": 5.0},
                    now_utc=t0,
                    expected_source_revision="rev-42",
                )
                self.assertEqual(p1["authority_class"], "REQUIRE_APPROVAL")
                self.assertEqual(p1["tier"], 1)
                self.assertEqual(p1["required_approver_role"], "Shift Supervisor")

                # 5. Session-bound authorization blocks agent even with forged X-Role header!
                agent_try = gate.authorize_proposal_with_session(
                    auth_store=auth,
                    token=agent_tok,
                    headers={"X-Role": "Shift Supervisor"},
                    auth_id="AUTH-AGENT",
                    proposal_id="PROP-T1",
                    branch_id="baseline",
                    payload_digest=p1["payload_digest"],
                    now_utc=t0,
                )
                self.assertEqual(agent_try["status"], "DENIED")
                self.assertEqual(agent_try["reason"], "AGENT_CANNOT_APPROVE")

                # 6. Legitimate human Shift Supervisor session authorizes
                ok_auth = gate.authorize_proposal_with_session(
                    auth_store=auth,
                    token=sup_tok,
                    auth_id="AUTH-OK-1",
                    proposal_id="PROP-T1",
                    branch_id="baseline",
                    payload_digest=p1["payload_digest"],
                    now_utc=t0 + timedelta(minutes=2),
                )
                self.assertEqual(ok_auth["status"], "AUTHORIZED")

                # 7. Missing current_source_revision, stale source_revision, mutated payload, cross-branch, and expiry MUST be rejected
                missing_rev = gate.execute_authorized_action(
                    idempotency_key="IDEM-NOREV",
                    proposal_id="PROP-T1",
                    auth_id="AUTH-OK-1",
                    branch_id="baseline",
                    payload=payload,
                    now_utc=t0 + timedelta(minutes=3),
                    current_source_revision=None,
                )
                self.assertEqual(missing_rev["reason"], "MISSING_CURRENT_SOURCE_REVISION")

                stale = gate.execute_authorized_action(
                    idempotency_key="IDEM-STALE",
                    proposal_id="PROP-T1",
                    auth_id="AUTH-OK-1",
                    branch_id="baseline",
                    payload=payload,
                    now_utc=t0 + timedelta(minutes=3),
                    current_source_revision="rev-43",
                )
                self.assertEqual(stale["reason"], "SOURCE_REVISION_STALE")

                mut = gate.execute_authorized_action(
                    idempotency_key="IDEM-MUT",
                    proposal_id="PROP-T1",
                    auth_id="AUTH-OK-1",
                    branch_id="baseline",
                    payload={**payload, "feed_bbl_per_day": 39999.0},
                    now_utc=t0 + timedelta(minutes=3),
                    current_source_revision="rev-42",
                )
                self.assertEqual(mut["reason"], "MUTATED_PAYLOAD_REJECTED")

                xbr = gate.execute_authorized_action(
                    idempotency_key="IDEM-XBR",
                    proposal_id="PROP-T1",
                    auth_id="AUTH-OK-1",
                    branch_id="child-branch-1",
                    payload=payload,
                    now_utc=t0 + timedelta(minutes=3),
                    current_source_revision="rev-42",
                )
                self.assertEqual(xbr["reason"], "CROSS_BRANCH_EXECUTION_FORBIDDEN")

                exp = gate.execute_authorized_action(
                    idempotency_key="IDEM-EXP",
                    proposal_id="PROP-T1",
                    auth_id="AUTH-OK-1",
                    branch_id="baseline",
                    payload=payload,
                    now_utc=t0 + timedelta(minutes=45),
                    current_source_revision="rev-42",
                )
                self.assertEqual(exp["reason"], "AUTHORIZATION_EXPIRED")

                # 8. Valid execution -> EXECUTED; identical key -> IDEMPOTENT_REPLAY; new key -> clean DENIED (no crash!)
                ex1 = gate.execute_authorized_action(
                    idempotency_key="IDEM-OK-1",
                    proposal_id="PROP-T1",
                    auth_id="AUTH-OK-1",
                    branch_id="baseline",
                    payload=payload,
                    now_utc=t0 + timedelta(minutes=5),
                    current_source_revision="rev-42",
                )
                self.assertEqual(ex1["status"], "EXECUTED")
                ex2 = gate.execute_authorized_action(
                    idempotency_key="IDEM-OK-1",
                    proposal_id="PROP-T1",
                    auth_id="AUTH-OK-1",
                    branch_id="baseline",
                    payload=payload,
                    now_utc=t0 + timedelta(minutes=6),
                    current_source_revision="rev-42",
                )
                self.assertEqual(ex2["status"], "IDEMPOTENT_REPLAY")

                # Double execution under a FRESH idempotency key returns clean DENIED and leaves gate usable!
                ex_double = gate.execute_authorized_action(
                    idempotency_key="IDEM-FRESH-DOUBLE",
                    proposal_id="PROP-T1",
                    auth_id="AUTH-OK-1",
                    branch_id="baseline",
                    payload=payload,
                    now_utc=t0 + timedelta(minutes=7),
                    current_source_revision="rev-42",
                )
                self.assertEqual(ex_double["status"], "DENIED")
                self.assertEqual(ex_double["reason"], "PROPOSAL_ALREADY_EXECUTED")

                # 9. AUTO_EXECUTE zero-effect limit enforcement: non-zero volume/margin MUST escalate out of AUTO_EXECUTE!
                p_auto_nonzero = gate.submit_proposal(
                    proposal_id="AUTO-NONZERO",
                    branch_id="baseline",
                    action_type="raise_alert",
                    proposer_id="usr-agent-1",
                    proposer_is_agent=True,
                    payload={"volume_bbl_60f": 60000.0, "margin_effect_usd": 999999.0},
                    metrics={"volume_bbl_60f": 60000.0, "margin_effect_usd": 999999.0},
                    now_utc=t0 + timedelta(minutes=9),
                )
                self.assertNotEqual(p_auto_nonzero["authority_class"], "AUTO_EXECUTE")

                # 10. AUTO_EXECUTE hourly rate cap (20/agent/hour) enforced BOTH at classification AND on bulk-submit execution!
                for i in range(25):
                    pa = gate.submit_proposal(
                        proposal_id=f"AUTO-{i}",
                        branch_id="baseline",
                        action_type="raise_alert",
                        proposer_id="usr-agent-1",
                        proposer_is_agent=True,
                        payload={"alert": i},
                        metrics={},
                        now_utc=t0 + timedelta(minutes=10),
                        expected_source_revision="rev-42",
                    )
                    self.assertEqual(pa["authority_class"], "AUTO_EXECUTE")
                for i in range(20):
                    er = gate.execute_authorized_action(
                        idempotency_key=f"IDEM-AUTO-{i}",
                        proposal_id=f"AUTO-{i}",
                        auth_id=None,
                        branch_id="baseline",
                        payload={"alert": i},
                        now_utc=t0 + timedelta(minutes=10),
                        current_source_revision="rev-42",
                    )
                    self.assertEqual(er["status"], "EXECUTED")
                # 21st pre-submitted AUTO_EXECUTE MUST be denied at execution time (blocks bulk-submit bypass!)
                er21 = gate.execute_authorized_action(
                    idempotency_key="IDEM-AUTO-20",
                    proposal_id="AUTO-20",
                    auth_id=None,
                    branch_id="baseline",
                    payload={"alert": 20},
                    now_utc=t0 + timedelta(minutes=10),
                    current_source_revision="rev-42",
                )
                self.assertEqual(er21["status"], "DENIED")
                self.assertEqual(er21["reason"], "AUTO_EXECUTE_RATE_LIMIT_EXCEEDED")
                # Subsequent submission also escalates to Tier 1
                p26 = gate.submit_proposal(
                    proposal_id="AUTO-25",
                    branch_id="baseline",
                    action_type="raise_alert",
                    proposer_id="usr-agent-1",
                    proposer_is_agent=True,
                    payload={"alert": 25},
                    metrics={},
                    now_utc=t0 + timedelta(minutes=11),
                )
                self.assertEqual(p26["authority_class"], "REQUIRE_APPROVAL")
                self.assertTrue(p26.get("rate_limit_escalated"))
            finally:
                gate.close()
                auth.close()

    def test_auth_rbac_ignores_forged_role_header_and_offline_agent_redacts_otel(self):
        with tempfile.TemporaryDirectory(prefix="ppc-wp3b-auth-") as tmp:
            store = AuthRBACStore(Path(tmp) / "auth.db", signing_secret="test-signing-secret-32-bytes-long")
            try:
                self.assertEqual(store.seed_fixture_accounts("strong-test-pass"), 7)
                tok = store.issue_token("planner_1", "strong-test-pass")
                self.assertIsNotNone(tok)
                self.assertIsNone(store.issue_token("planner_1", "wrong-pass"))
                # Forged X-Role header MUST be ignored in favor of DB role_assignments
                ctx = store.authenticate_request(tok, headers={"X-Role": "VP Supply and Operations"})
                self.assertIsNotNone(ctx)
                self.assertEqual(ctx["roles"], ["Planner"])
                self.assertFalse(ctx["is_agent"])
            finally:
                store.close()

        # Recursive OTel redaction catches auth_token, Authorization: Bearer, mid-string secrets, and dicts inside lists
        redacted = redact_otel_attributes(
            {
                "auth_token": "sk-live-abc123",
                "Authorization": "Bearer eyJsecret",
                "detail": "request failed for Authorization: Bearer abc123",
                "header": "token=xyz999",
                "events": [{"secret": "leaked", "password": "p", "safe": "ok"}],
                "nested": {"access_token": "tok-xyz", "note": "Bearer raw-val"},
            }
        )
        self.assertEqual(redacted["auth_token"], "[REDACTED]")
        self.assertEqual(redacted["Authorization"], "[REDACTED]")
        self.assertEqual(redacted["detail"], "[REDACTED]")
        self.assertEqual(redacted["header"], "[REDACTED]")
        self.assertEqual(redacted["events"][0]["secret"], "[REDACTED]")
        self.assertEqual(redacted["events"][0]["password"], "[REDACTED]")
        self.assertEqual(redacted["events"][0]["safe"], "ok")
        self.assertEqual(redacted["nested"]["access_token"], "[REDACTED]")
        self.assertEqual(redacted["nested"]["note"], "[REDACTED]")

        # Offline recorded-response agent runs deterministically with zero live LLM calls (ADR-0059)
        agent = RecordedResponseAgentAdapter(RECORDED_FIXTURE)
        self.assertEqual(agent.mode, "OFFLINE_RECORDED_FIXTURE_ONLY")
        out = agent.run_investigation("SCN-A-T125", "2026-06-15T08:40:00Z", "Planner")
        self.assertEqual(out["model_quantified_cards"][0]["binding_constraint"], "compressor_circulation_cap")
        self.assertEqual(out["otel_span"]["restricted_payload"], "[REDACTED]")
        self.assertEqual(len(canonical_digest(out)), 64)


if __name__ == "__main__":
    unittest.main()
