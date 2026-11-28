#!/usr/bin/env python3
"""Service-side ACID Policy-as-Code Gate (WP-3B, ADR-0056 G3-b, AGENT-001 §1, PO-10).

Reads schemas/policy_thresholds.yaml directly and enforces server-side:
- PROHIBITED actions always resolve to DENIED (never approvable).
- Missing numeric estimates count as exceeded and escalate tier.
- proposer != approver and agents can never approve.
- Exact payload_digest binding, branch binding, expiry window, and one-time ActionReceipt idempotency.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

import yaml


def canonical_digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


class PolicyGateService:
    """ACID ActionProposal -> ActionAuthorization -> ActionReceipt engine."""

    def __init__(self, thresholds_path: str | Path, db_path: str | Path):
        self.thresholds = yaml.safe_load(Path(thresholds_path).read_text(encoding="utf-8"))
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS action_proposals (
                proposal_id TEXT PRIMARY KEY,
                branch_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                proposer_id TEXT NOT NULL,
                proposer_is_agent INTEGER NOT NULL,
                authority_class TEXT NOT NULL,
                required_tier INTEGER,
                required_approver_role TEXT,
                policy_result TEXT NOT NULL,
                payload_digest TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at_utc TEXT NOT NULL,
                expires_at_utc TEXT
            );
            CREATE TABLE IF NOT EXISTS action_authorizations (
                auth_id TEXT PRIMARY KEY,
                proposal_id TEXT NOT NULL,
                branch_id TEXT NOT NULL,
                approver_id TEXT NOT NULL,
                approver_role TEXT NOT NULL,
                payload_digest TEXT NOT NULL,
                authorized_at_utc TEXT NOT NULL,
                expires_at_utc TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS action_receipts (
                idempotency_key TEXT PRIMARY KEY,
                proposal_id TEXT NOT NULL UNIQUE,
                auth_id TEXT,
                branch_id TEXT NOT NULL,
                payload_digest TEXT NOT NULL,
                execution_status TEXT NOT NULL,
                executed_at_utc TEXT NOT NULL
            );
            """
        )
        self.conn.commit()

    def classify_proposal(self, action_type: str, metrics: Mapping[str, Any]) -> dict[str, Any]:
        """Classify an action against schemas/policy_thresholds.yaml (ADR-0056 G3-b)."""
        classes = self.thresholds["authority_classes"]
        if action_type in classes["PROHIBITED"]["prohibited_actions"]:
            return {
                "authority_class": "PROHIBITED",
                "policy_result": "DENIED",
                "tier": None,
                "required_approver_role": None,
                "expiry_minutes": None,
            }
        if action_type in classes["AUTO_EXECUTE"]["allowed_actions"]:
            return {
                "authority_class": "AUTO_EXECUTE",
                "policy_result": "AUTO_EXECUTED",
                "tier": 0,
                "required_approver_role": None,
                "expiry_minutes": None,
            }

        # Missing numeric estimate counts as exceeded -> escalates (ADR-0056 global invariant)
        margin_usd = metrics.get("margin_effect_usd")
        vol_bbl = metrics.get("volume_bbl_60f")
        notional_usd = metrics.get("notional_usd")
        rate_chg_bbl = metrics.get("rate_change_bbl_per_day")
        cut_shift_c = metrics.get("cut_point_shift_c")

        t1 = classes["REQUIRE_APPROVAL_TIER_1"]
        t2 = classes["REQUIRE_APPROVAL_TIER_2"]

        if action_type in t1["allowed_actions"]:
            lim = t1["limits"]
            within_t1 = (
                margin_usd is not None
                and abs(float(margin_usd)) <= lim["max_margin_effect_usd"]
                and (rate_chg_bbl is None or abs(float(rate_chg_bbl)) <= lim["max_rate_change_bbl_per_day"])
                and (cut_shift_c is None or abs(float(cut_shift_c)) <= lim["max_cut_point_shift_c"])
                and (vol_bbl is None or abs(float(vol_bbl)) <= lim["max_transfer_volume_bbl_60f"])
            )
            if within_t1:
                return {
                    "authority_class": "REQUIRE_APPROVAL",
                    "policy_result": "PENDING_APPROVAL",
                    "tier": 1,
                    "required_approver_role": t1["approver_roles"]["default"],
                    "expiry_minutes": int(t1["expiry_logical_minutes"]),
                }

        if action_type in t2["allowed_actions"] or action_type in t1["allowed_actions"]:
            lim = t2["limits"]
            within_t2 = (
                margin_usd is not None
                and abs(float(margin_usd)) <= lim["max_margin_effect_usd"]
                and (vol_bbl is None or abs(float(vol_bbl)) <= lim["max_volume_bbl_60f"])
                and (notional_usd is None or abs(float(notional_usd)) <= lim["max_notional_usd"])
                and (cut_shift_c is None or abs(float(cut_shift_c)) <= lim["max_cut_point_shift_c"])
            )
            if within_t2:
                domain = str(metrics.get("domain", "physical"))
                role = t2["approver_roles"].get(domain, t2["approver_roles"]["physical"])
                return {
                    "authority_class": "REQUIRE_APPROVAL",
                    "policy_result": "PENDING_APPROVAL",
                    "tier": 2,
                    "required_approver_role": role,
                    "expiry_minutes": int(t2["expiry_logical_minutes"]),
                }

        return {
            "authority_class": "ESCALATE",
            "policy_result": "ESCALATED",
            "tier": 3,
            "required_approver_role": classes["ESCALATE"]["approver_roles"]["default"],
            "expiry_minutes": 240,
        }

    def submit_proposal(
        self,
        *,
        proposal_id: str,
        branch_id: str,
        action_type: str,
        proposer_id: str,
        proposer_is_agent: bool,
        payload: Mapping[str, Any],
        metrics: Mapping[str, Any],
        now_utc: datetime,
    ) -> dict[str, Any]:
        cls = self.classify_proposal(action_type, metrics)
        digest = canonical_digest(payload)
        expires = (
            (now_utc + timedelta(minutes=cls["expiry_minutes"])).strftime("%Y-%m-%dT%H:%M:%SZ")
            if cls["expiry_minutes"] is not None
            else None
        )
        cur = self.conn.cursor()
        cur.execute("BEGIN IMMEDIATE")
        cur.execute(
            """
            INSERT INTO action_proposals (
                proposal_id, branch_id, action_type, proposer_id, proposer_is_agent,
                authority_class, required_tier, required_approver_role, policy_result,
                payload_digest, payload_json, created_at_utc, expires_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                proposal_id,
                branch_id,
                action_type,
                proposer_id,
                1 if proposer_is_agent else 0,
                cls["authority_class"],
                cls["tier"],
                cls["required_approver_role"],
                cls["policy_result"],
                digest,
                json.dumps(payload, sort_keys=True, separators=(",", ":")),
                now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                expires,
            ),
        )
        self.conn.commit()
        return {
            "proposal_id": proposal_id,
            "branch_id": branch_id,
            "payload_digest": digest,
            "expires_at_utc": expires,
            **cls,
        }

    def authorize_proposal(
        self,
        *,
        auth_id: str,
        proposal_id: str,
        approver_id: str,
        approver_role: str,
        approver_is_agent: bool,
        branch_id: str,
        payload_digest: str,
        now_utc: datetime,
    ) -> dict[str, Any]:
        row = self.conn.execute(
            "SELECT * FROM action_proposals WHERE proposal_id = ?", (proposal_id,)
        ).fetchone()
        if row is None:
            return {"status": "DENIED", "reason": "UNKNOWN_PROPOSAL"}
        if row["authority_class"] == "PROHIBITED":
            return {"status": "DENIED", "reason": "PROHIBITED_ACTION_CANNOT_BE_APPROVED"}
        if approver_is_agent:
            return {"status": "DENIED", "reason": "AGENT_CANNOT_APPROVE"}
        if approver_id == row["proposer_id"]:
            return {"status": "DENIED", "reason": "PROPOSER_CANNOT_APPROVE"}
        if branch_id != row["branch_id"]:
            return {"status": "DENIED", "reason": "CROSS_BRANCH_APPROVAL_FORBIDDEN"}
        if payload_digest != row["payload_digest"]:
            return {"status": "DENIED", "reason": "PAYLOAD_DIGEST_MISMATCH"}
        if row["required_approver_role"] and approver_role != row["required_approver_role"]:
            return {"status": "DENIED", "reason": f"ROLE_MISMATCH (required {row['required_approver_role']})"}
        if row["expires_at_utc"]:
            exp = datetime.fromisoformat(row["expires_at_utc"].replace("Z", "+00:00"))
            if now_utc > exp:
                return {"status": "DENIED", "reason": "PROPOSAL_EXPIRED"}

        cur = self.conn.cursor()
        cur.execute("BEGIN IMMEDIATE")
        cur.execute(
            """
            INSERT INTO action_authorizations (
                auth_id, proposal_id, branch_id, approver_id, approver_role,
                payload_digest, authorized_at_utc, expires_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                auth_id,
                proposal_id,
                branch_id,
                approver_id,
                approver_role,
                payload_digest,
                now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                row["expires_at_utc"] or now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
            ),
        )
        self.conn.commit()
        return {"status": "AUTHORIZED", "auth_id": auth_id, "proposal_id": proposal_id}

    def execute_authorized_action(
        self,
        *,
        idempotency_key: str,
        proposal_id: str,
        auth_id: str | None,
        branch_id: str,
        payload: Mapping[str, Any],
        now_utc: datetime,
    ) -> dict[str, Any]:
        """Execute an authorized (or AUTO_EXECUTE) action with exact digest, branch, expiry, and idempotency checks."""
        digest = canonical_digest(payload)
        prior = self.conn.execute(
            "SELECT * FROM action_receipts WHERE idempotency_key = ?", (idempotency_key,)
        ).fetchone()
        if prior is not None:
            if prior["payload_digest"] == digest and prior["proposal_id"] == proposal_id:
                return {"status": "IDEMPOTENT_REPLAY", "idempotency_key": idempotency_key, "proposal_id": proposal_id}
            return {"status": "DENIED", "reason": "IDEMPOTENCY_KEY_CONFLICT"}

        prop = self.conn.execute(
            "SELECT * FROM action_proposals WHERE proposal_id = ?", (proposal_id,)
        ).fetchone()
        if prop is None:
            return {"status": "DENIED", "reason": "UNKNOWN_PROPOSAL"}
        if prop["authority_class"] == "PROHIBITED":
            return {"status": "DENIED", "reason": "PROHIBITED_ACTION_DENIED"}
        if prop["branch_id"] != branch_id:
            return {"status": "DENIED", "reason": "CROSS_BRANCH_EXECUTION_FORBIDDEN"}
        if prop["payload_digest"] != digest:
            return {"status": "DENIED", "reason": "MUTATED_PAYLOAD_REJECTED"}

        if prop["authority_class"] != "AUTO_EXECUTE":
            if not auth_id:
                return {"status": "DENIED", "reason": "MISSING_AUTHORIZATION"}
            auth = self.conn.execute(
                "SELECT * FROM action_authorizations WHERE auth_id = ? AND proposal_id = ?",
                (auth_id, proposal_id),
            ).fetchone()
            if auth is None:
                return {"status": "DENIED", "reason": "INVALID_AUTHORIZATION"}
            if auth["branch_id"] != branch_id:
                return {"status": "DENIED", "reason": "CROSS_BRANCH_APPROVAL_REUSE_FORBIDDEN"}
            if auth["payload_digest"] != digest:
                return {"status": "DENIED", "reason": "AUTHORIZATION_DIGEST_MISMATCH"}
            exp = datetime.fromisoformat(auth["expires_at_utc"].replace("Z", "+00:00"))
            if now_utc > exp:
                return {"status": "DENIED", "reason": "AUTHORIZATION_EXPIRED"}

        cur = self.conn.cursor()
        cur.execute("BEGIN IMMEDIATE")
        cur.execute(
            """
            INSERT INTO action_receipts (
                idempotency_key, proposal_id, auth_id, branch_id, payload_digest,
                execution_status, executed_at_utc
            ) VALUES (?, ?, ?, ?, ?, 'EXECUTED', ?)
            """,
            (
                idempotency_key,
                proposal_id,
                auth_id,
                branch_id,
                digest,
                now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
            ),
        )
        self.conn.commit()
        return {
            "status": "EXECUTED",
            "idempotency_key": idempotency_key,
            "proposal_id": proposal_id,
            "auth_id": auth_id,
            "payload_digest": digest,
        }

    def close(self) -> None:
        self.conn.close()
