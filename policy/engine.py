#!/usr/bin/env python3
"""Service-side ACID Policy-as-Code Gate (WP-3B, ADR-0056 G3-b, AGENT-001 §1, PO-10).

Reads schemas/policy_thresholds.yaml directly and enforces server-side:
- PROHIBITED actions always resolve to DENIED (never approvable or executable).
- AUTO_EXECUTE enforces zero physical/commercial/financial effect limits across all 7 effect
  magnitudes (and rejects non-finite NaN/Inf estimates) plus the 20/agent/logical-hour rate cap
  at BOTH classification and execution time.
- Required numeric estimates per action class: missing estimate counts as exceeded and escalates tier.
- Payload-to-metrics cross-check (_effective_metrics) prevents smuggling large payloads under small metrics;
  payload_digest binds the canonical payload and is verified at authorization and execution;
  expected_source_revision is persisted on the proposal and verified at execution, while policy_version
  is persisted on proposal and authorization rows and verified at both authorization and execution;
  metrics and decision_id are persisted on action_proposals (metrics conservatively merged at submission).
- proposer != approver and agents can never approve; supports session-bound authorization via AuthRBACStore.
- Clean single-use ActionReceipt execution with transaction rollback on error and mandatory
  current_source_revision freshness check (fails closed if omitted).
"""
from __future__ import annotations

import hashlib
import json
import math
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

import yaml


# Required numeric estimates per action_type (ADR-0056 G3-b: missing required estimate escalates tier)
REQUIRED_ACTION_METRICS: dict[str, tuple[str, ...]] = {
    "feed_rate_change_inside_envelope": ("margin_effect_usd", "rate_change_bbl_per_day", "rate_change_pct"),
    "unit_mode_change_inside_envelope": ("margin_effect_usd",),
    "cdu_vdu_cut_point_shift": ("margin_effect_usd", "cut_point_shift_c"),
    "in_refinery_tank_transfer": ("margin_effect_usd", "volume_bbl_60f"),
    "larger_feed_rate_change": ("margin_effect_usd", "volume_bbl_60f"),
    "max_distillate_or_max_gasoline_mode_swing": ("margin_effect_usd",),
    "inter_terminal_transfer": ("margin_effect_usd", "volume_bbl_60f"),
    "spot_purchase_or_sale": ("margin_effect_usd", "volume_bbl_60f", "notional_usd"),
    "delivery_reschedule": ("margin_effect_usd", "delivery_reschedule_hours"),
    "reroute_held_lot_to_another_hold": ("margin_effect_usd", "volume_bbl_60f"),
}


# Server-side Tier 2 action_type -> domain mapping (ADR-0056 G3-b; never taken from caller metrics["domain"])
TIER2_ACTION_DOMAIN: dict[str, str] = {
    "feed_rate_change_inside_envelope": "physical",
    "unit_mode_change_inside_envelope": "physical",
    "cdu_vdu_cut_point_shift": "physical",
    "in_refinery_tank_transfer": "physical",
    "larger_feed_rate_change": "physical",
    "max_distillate_or_max_gasoline_mode_swing": "physical",
    "reroute_held_lot_to_another_hold": "physical",
    "inter_terminal_transfer": "commercial",
    "spot_purchase_or_sale": "commercial",
    "delivery_reschedule": "commercial",
}


def canonical_digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _effective_metrics(payload: Mapping[str, Any], metrics: Mapping[str, Any]) -> dict[str, Any]:
    """Cross-check and derive threshold magnitudes from payload + metrics using conservative max magnitudes."""
    merged = dict(metrics)
    for field in (
        "margin_effect_usd",
        "rate_change_bbl_per_day",
        "rate_change_pct",
        "cut_point_shift_c",
        "volume_bbl_60f",
        "notional_usd",
        "delivery_reschedule_hours",
    ):
        p_val = payload.get(field)
        m_val = merged.get(field)
        if p_val is not None:
            pf = float(p_val)
            if not math.isfinite(pf):
                raise ValueError(f"Non-finite payload metric {field}={p_val!r}")
        if m_val is not None:
            mf = float(m_val)
            if not math.isfinite(mf):
                raise ValueError(f"Non-finite metric {field}={m_val!r}")
        if p_val is not None and m_val is not None:
            if abs(float(p_val)) > abs(float(m_val)):
                merged[field] = float(p_val)
        elif p_val is not None and m_val is None:
            merged[field] = float(p_val)

    # Reject non-finite auxiliary numeric fields in BOTH payload and metrics
    for aux_field in ("feed_bbl_per_day", "baseline_feed_bbl_per_day", "pinned_price_usd_per_bbl"):
        for container_name, container in (("payload", payload), ("metrics", merged)):
            aux_val = container.get(aux_field)
            if aux_val is not None:
                af = float(aux_val)
                if not math.isfinite(af):
                    raise ValueError(f"Non-finite {container_name} field {aux_field}={aux_val!r}")

    # Derive rate_change_bbl_per_day AND rate_change_pct from feed_bbl_per_day + baseline_feed_bbl_per_day
    feed_val = payload.get("feed_bbl_per_day") if payload.get("feed_bbl_per_day") is not None else merged.get("feed_bbl_per_day")
    base_val = (
        payload.get("baseline_feed_bbl_per_day")
        if payload.get("baseline_feed_bbl_per_day") is not None
        else merged.get("baseline_feed_bbl_per_day")
    )
    if feed_val is not None:
        feed_f = float(feed_val)
        if base_val is not None:
            base_f = float(base_val)
            if base_f <= 0.0:
                raise ValueError(f"baseline_feed_bbl_per_day must be positive, got {base_val!r}")
            implied_delta = abs(feed_f - base_f)
            implied_pct = 100.0 * implied_delta / base_f
            if merged.get("rate_change_bbl_per_day") is None or implied_delta > abs(float(merged["rate_change_bbl_per_day"])):
                merged["rate_change_bbl_per_day"] = implied_delta
            if merged.get("rate_change_pct") is None or implied_pct > abs(float(merged["rate_change_pct"])):
                merged["rate_change_pct"] = implied_pct
        elif abs(feed_f) > 50000.0:
            # Exceeds Tier 2 absolute volume envelope without baseline proof -> force conservative magnitude
            merged["rate_change_bbl_per_day"] = max(
                abs(float(merged.get("rate_change_bbl_per_day") or 0.0)), abs(feed_f)
            )
            merged["volume_bbl_60f"] = max(
                abs(float(merged.get("volume_bbl_60f") or 0.0)), abs(feed_f)
            )

    # Derive notional_usd per schemas/policy_thresholds.yaml formula: volume_bbl_60F * pinned_price_usd_per_bbl
    price_val = (
        payload.get("pinned_price_usd_per_bbl")
        if payload.get("pinned_price_usd_per_bbl") is not None
        else merged.get("pinned_price_usd_per_bbl")
    )
    vol_val = merged.get("volume_bbl_60f")
    if vol_val is not None and price_val is not None:
        implied_notional = abs(float(vol_val)) * abs(float(price_val))
        if not math.isfinite(implied_notional):
            raise ValueError("Derived notional_usd overflowed to non-finite value")
        if merged.get("notional_usd") is None or implied_notional > abs(float(merged["notional_usd"])):
            merged["notional_usd"] = implied_notional

    return merged


class PolicyGateService:
    """ACID ActionProposal -> ActionAuthorization -> ActionReceipt engine."""

    def __init__(self, thresholds_path: str | Path, db_path: str | Path):
        self.thresholds = yaml.safe_load(Path(thresholds_path).read_text(encoding="utf-8"))
        self.policy_version = str(self.thresholds.get("policy_version", "1.0.0"))
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path), isolation_level=None)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS action_proposals (
                proposal_id TEXT PRIMARY KEY,
                decision_id TEXT NOT NULL,
                branch_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                proposer_id TEXT NOT NULL,
                proposer_is_agent INTEGER NOT NULL,
                authority_class TEXT NOT NULL,
                required_tier INTEGER,
                required_approver_role TEXT,
                policy_result TEXT NOT NULL,
                policy_version TEXT NOT NULL,
                expected_source_revision TEXT NOT NULL,
                payload_digest TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                metrics_json TEXT NOT NULL,
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
                policy_version TEXT NOT NULL,
                authorized_at_utc TEXT NOT NULL,
                expires_at_utc TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS action_receipts (
                idempotency_key TEXT PRIMARY KEY,
                proposal_id TEXT NOT NULL UNIQUE,
                auth_id TEXT,
                branch_id TEXT NOT NULL,
                proposer_id TEXT NOT NULL,
                authority_class TEXT NOT NULL,
                payload_digest TEXT NOT NULL,
                source_revision TEXT NOT NULL,
                execution_status TEXT NOT NULL,
                executed_at_utc TEXT NOT NULL
            );
            """
        )

    def _auto_execute_count_last_hour(self, proposer_id: str, now_utc: datetime) -> int:
        cutoff = (now_utc - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        row = self.conn.execute(
            """
            SELECT COUNT(*) AS cnt FROM action_receipts
            WHERE proposer_id = ? AND authority_class = 'AUTO_EXECUTE' AND executed_at_utc >= ?
            """,
            (proposer_id, cutoff),
        ).fetchone()
        return int(row["cnt"]) if row else 0

    def classify_proposal(
        self,
        action_type: str,
        metrics: Mapping[str, Any],
        payload: Mapping[str, Any] | None = None,
        *,
        proposer_id: str | None = None,
        now_utc: datetime | None = None,
    ) -> dict[str, Any]:
        """Classify an action against schemas/policy_thresholds.yaml (ADR-0056 G3-b)."""
        classes = self.thresholds["authority_classes"]
        eff_metrics = _effective_metrics(payload or {}, metrics)

        if action_type in classes["PROHIBITED"]["prohibited_actions"]:
            return {
                "authority_class": "PROHIBITED",
                "policy_result": "DENIED",
                "tier": None,
                "required_approver_role": None,
                "expiry_minutes": None,
                "policy_version": self.policy_version,
            }

        if action_type in classes["AUTO_EXECUTE"]["allowed_actions"]:
            auto_lim = classes["AUTO_EXECUTE"]["limits"]
            max_hr = int(auto_lim["max_executions_per_agent_per_logical_hour"])
            exceeds_auto_limits = (
                abs(float(eff_metrics.get("volume_bbl_60f") or 0.0)) > float(auto_lim["max_volume_bbl_60f"])
                or abs(float(eff_metrics.get("margin_effect_usd") or 0.0)) > float(auto_lim["max_margin_effect_usd"])
                or abs(float(eff_metrics.get("notional_usd") or 0.0)) > float(auto_lim["max_notional_usd"])
                or abs(float(eff_metrics.get("rate_change_bbl_per_day") or 0.0)) > 0.0
                or abs(float(eff_metrics.get("rate_change_pct") or 0.0)) > 0.0
                or abs(float(eff_metrics.get("cut_point_shift_c") or 0.0)) > 0.0
                or abs(float(eff_metrics.get("delivery_reschedule_hours") or 0.0)) > 0.0
            )
            rate_exceeded = bool(
                proposer_id and now_utc and self._auto_execute_count_last_hour(proposer_id, now_utc) >= max_hr
            )
            if not exceeds_auto_limits and not rate_exceeded:
                return {
                    "authority_class": "AUTO_EXECUTE",
                    "policy_result": "AUTO_EXECUTED",
                    "tier": 0,
                    "required_approver_role": None,
                    "expiry_minutes": None,
                    "policy_version": self.policy_version,
                }
            if rate_exceeded and not exceeds_auto_limits:
                t1 = classes["REQUIRE_APPROVAL_TIER_1"]
                return {
                    "authority_class": "REQUIRE_APPROVAL",
                    "policy_result": "PENDING_APPROVAL",
                    "tier": 1,
                    "required_approver_role": t1["approver_roles"]["default"],
                    "expiry_minutes": int(t1["expiry_logical_minutes"]),
                    "policy_version": self.policy_version,
                    "rate_limit_escalated": True,
                }
            # Exceeding AUTO_EXECUTE zero-effect limits falls through to higher-tier evaluation/escalation!

        required = REQUIRED_ACTION_METRICS.get(action_type, ("margin_effect_usd",))
        missing_required = any(eff_metrics.get(k) is None for k in required)

        margin_usd = eff_metrics.get("margin_effect_usd")
        vol_bbl = eff_metrics.get("volume_bbl_60f")
        notional_usd = eff_metrics.get("notional_usd")
        rate_chg_bbl = eff_metrics.get("rate_change_bbl_per_day")
        rate_chg_pct = eff_metrics.get("rate_change_pct")
        cut_shift_c = eff_metrics.get("cut_point_shift_c")
        resched_h = eff_metrics.get("delivery_reschedule_hours")

        t1 = classes["REQUIRE_APPROVAL_TIER_1"]
        t2 = classes["REQUIRE_APPROVAL_TIER_2"]

        if not missing_required and action_type in t1["allowed_actions"]:
            lim = t1["limits"]
            within_t1 = (
                margin_usd is not None
                and abs(float(margin_usd)) <= lim["max_margin_effect_usd"]
                and (rate_chg_bbl is None or abs(float(rate_chg_bbl)) <= lim["max_rate_change_bbl_per_day"])
                and (rate_chg_pct is None or abs(float(rate_chg_pct)) <= lim["max_rate_change_pct"])
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
                    "policy_version": self.policy_version,
                }

        if not missing_required and (action_type in t2["allowed_actions"] or action_type in t1["allowed_actions"]):
            lim = t2["limits"]
            within_t2 = (
                margin_usd is not None
                and abs(float(margin_usd)) <= lim["max_margin_effect_usd"]
                and (vol_bbl is None or abs(float(vol_bbl)) <= lim["max_volume_bbl_60f"])
                and (rate_chg_bbl is None or abs(float(rate_chg_bbl)) <= lim["max_volume_bbl_60f"])
                and (notional_usd is None or abs(float(notional_usd)) <= lim["max_notional_usd"])
                and (cut_shift_c is None or abs(float(cut_shift_c)) <= lim["max_cut_point_shift_c"])
                and (resched_h is None or abs(float(resched_h)) <= lim["max_delivery_reschedule_hours"])
            )
            if within_t2 and action_type in TIER2_ACTION_DOMAIN:
                domain = TIER2_ACTION_DOMAIN[action_type]
                role = t2["approver_roles"][domain]
                return {
                    "authority_class": "REQUIRE_APPROVAL",
                    "policy_result": "PENDING_APPROVAL",
                    "tier": 2,
                    "required_approver_role": role,
                    "expiry_minutes": int(t2["expiry_logical_minutes"]),
                    "policy_version": self.policy_version,
                }

        # ESCALATE expiry uses YAML ESCALATE.expiry_logical_minutes if defined, else Tier 2 expiry from YAML
        esc_expiry = int(classes["ESCALATE"].get("expiry_logical_minutes", t2["expiry_logical_minutes"]))
        return {
            "authority_class": "ESCALATE",
            "policy_result": "ESCALATED",
            "tier": 3,
            "required_approver_role": classes["ESCALATE"]["approver_roles"]["default"],
            "expiry_minutes": esc_expiry,
            "policy_version": self.policy_version,
            "requires_new_decision_id": bool(classes["ESCALATE"].get("requires_new_decision_id", True)),
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
        decision_id: str | None = None,
        expected_source_revision: str = "rev-0",
    ) -> dict[str, Any]:
        eff_metrics = _effective_metrics(payload, metrics)
        cls = self.classify_proposal(
            action_type, eff_metrics, payload, proposer_id=proposer_id, now_utc=now_utc
        )
        eff_decision_id = decision_id or f"DEC-{proposal_id}"
        digest = canonical_digest(payload)
        expires = (
            (now_utc + timedelta(minutes=cls["expiry_minutes"])).strftime("%Y-%m-%dT%H:%M:%SZ")
            if cls["expiry_minutes"] is not None
            else None
        )
        cur = self.conn.cursor()
        cur.execute("BEGIN IMMEDIATE")
        try:
            cur.execute(
                """
                INSERT INTO action_proposals (
                    proposal_id, decision_id, branch_id, action_type, proposer_id, proposer_is_agent,
                    authority_class, required_tier, required_approver_role, policy_result,
                    policy_version, expected_source_revision,
                    payload_digest, payload_json, metrics_json, created_at_utc, expires_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    proposal_id,
                    eff_decision_id,
                    branch_id,
                    action_type,
                    proposer_id,
                    1 if proposer_is_agent else 0,
                    cls["authority_class"],
                    cls["tier"],
                    cls["required_approver_role"],
                    cls["policy_result"],
                    self.policy_version,
                    expected_source_revision,
                    digest,
                    json.dumps(payload, sort_keys=True, separators=(",", ":")),
                    json.dumps(eff_metrics, sort_keys=True, separators=(",", ":")),
                    now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    expires,
                ),
            )
            cur.execute("COMMIT")
        except Exception:
            cur.execute("ROLLBACK")
            raise
        return {
            "proposal_id": proposal_id,
            "decision_id": eff_decision_id,
            "branch_id": branch_id,
            "expected_source_revision": expected_source_revision,
            "payload_digest": digest,
            "expires_at_utc": expires,
            **cls,
        }

    def authorize_proposal_with_session(
        self,
        *,
        auth_store: Any,
        token: str,
        headers: Mapping[str, str] | None = None,
        auth_id: str,
        proposal_id: str,
        branch_id: str,
        payload_digest: str,
        now_utc: datetime,
    ) -> dict[str, Any]:
        """Authorize a proposal deriving verified approver_id, roles, and is_agent strictly from AuthRBACStore."""
        ctx = auth_store.authenticate_request(token, headers=headers)
        if ctx is None:
            return {"status": "DENIED", "reason": "UNAUTHENTICATED_SESSION"}
        row = self.conn.execute(
            "SELECT required_approver_role FROM action_proposals WHERE proposal_id = ?", (proposal_id,)
        ).fetchone()
        req_role = row["required_approver_role"] if row else None
        matched_role = req_role if (req_role and req_role in ctx["roles"]) else (ctx["roles"][0] if ctx["roles"] else "")
        return self.authorize_proposal(
            auth_id=auth_id,
            proposal_id=proposal_id,
            approver_id=ctx["user_id"],
            approver_role=matched_role,
            approver_is_agent=bool(ctx["is_agent"]),
            branch_id=branch_id,
            payload_digest=payload_digest,
            now_utc=now_utc,
        )

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
        if row["authority_class"] == "ESCALATE" or row["policy_result"] == "ESCALATED":
            return {"status": "DENIED", "reason": "ESCALATED_PROPOSAL_IS_TERMINAL_REQUIRES_NEW_DECISION_ID"}
        if approver_is_agent:
            return {"status": "DENIED", "reason": "AGENT_CANNOT_APPROVE"}
        if approver_id == row["proposer_id"]:
            return {"status": "DENIED", "reason": "PROPOSER_CANNOT_APPROVE"}
        if branch_id != row["branch_id"]:
            return {"status": "DENIED", "reason": "CROSS_BRANCH_APPROVAL_FORBIDDEN"}
        if payload_digest != row["payload_digest"]:
            return {"status": "DENIED", "reason": "PAYLOAD_DIGEST_MISMATCH"}
        if row["policy_version"] != self.policy_version:
            return {"status": "DENIED", "reason": "POLICY_VERSION_MISMATCH"}
        if row["required_approver_role"] and approver_role != row["required_approver_role"]:
            return {"status": "DENIED", "reason": f"ROLE_MISMATCH (required {row['required_approver_role']})"}
        if row["expires_at_utc"]:
            exp = datetime.fromisoformat(row["expires_at_utc"].replace("Z", "+00:00"))
            if now_utc > exp:
                return {"status": "DENIED", "reason": "PROPOSAL_EXPIRED"}

        cur = self.conn.cursor()
        cur.execute("BEGIN IMMEDIATE")
        try:
            cur.execute(
                """
                INSERT INTO action_authorizations (
                    auth_id, proposal_id, branch_id, approver_id, approver_role,
                    payload_digest, policy_version, authorized_at_utc, expires_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    auth_id,
                    proposal_id,
                    branch_id,
                    approver_id,
                    approver_role,
                    payload_digest,
                    self.policy_version,
                    now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    row["expires_at_utc"] or now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                ),
            )
            cur.execute("COMMIT")
        except Exception:
            cur.execute("ROLLBACK")
            raise
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
        current_source_revision: str | None = None,
    ) -> dict[str, Any]:
        """Execute an authorized (or AUTO_EXECUTE) action with exact digest, branch, revision, expiry, and single-use checks."""
        digest = canonical_digest(payload)
        cur = self.conn.cursor()
        cur.execute("BEGIN IMMEDIATE")
        try:
            prior = cur.execute(
                "SELECT * FROM action_receipts WHERE idempotency_key = ?", (idempotency_key,)
            ).fetchone()
            if prior is not None:
                cur.execute("ROLLBACK")
                if prior["payload_digest"] == digest and prior["proposal_id"] == proposal_id:
                    return {"status": "IDEMPOTENT_REPLAY", "idempotency_key": idempotency_key, "proposal_id": proposal_id}
                return {"status": "DENIED", "reason": "IDEMPOTENCY_KEY_CONFLICT"}

            existing_prop_receipt = cur.execute(
                "SELECT idempotency_key FROM action_receipts WHERE proposal_id = ?", (proposal_id,)
            ).fetchone()
            if existing_prop_receipt is not None:
                cur.execute("ROLLBACK")
                return {
                    "status": "DENIED",
                    "reason": "PROPOSAL_ALREADY_EXECUTED",
                    "prior_idempotency_key": existing_prop_receipt["idempotency_key"],
                }

            prop = cur.execute(
                "SELECT * FROM action_proposals WHERE proposal_id = ?", (proposal_id,)
            ).fetchone()
            if prop is None:
                cur.execute("ROLLBACK")
                return {"status": "DENIED", "reason": "UNKNOWN_PROPOSAL"}
            if prop["authority_class"] == "PROHIBITED":
                cur.execute("ROLLBACK")
                return {"status": "DENIED", "reason": "PROHIBITED_ACTION_DENIED"}
            if prop["authority_class"] == "ESCALATE" or prop["policy_result"] == "ESCALATED":
                cur.execute("ROLLBACK")
                return {"status": "DENIED", "reason": "ESCALATED_PROPOSAL_IS_TERMINAL_REQUIRES_NEW_DECISION_ID"}
            if prop["branch_id"] != branch_id:
                cur.execute("ROLLBACK")
                return {"status": "DENIED", "reason": "CROSS_BRANCH_EXECUTION_FORBIDDEN"}
            if prop["payload_digest"] != digest:
                cur.execute("ROLLBACK")
                return {"status": "DENIED", "reason": "MUTATED_PAYLOAD_REJECTED"}
            if prop["policy_version"] != self.policy_version:
                cur.execute("ROLLBACK")
                return {"status": "DENIED", "reason": "POLICY_VERSION_MISMATCH"}
            if not current_source_revision:
                cur.execute("ROLLBACK")
                return {"status": "DENIED", "reason": "MISSING_CURRENT_SOURCE_REVISION"}
            eff_rev = str(current_source_revision)
            if eff_rev != prop["expected_source_revision"]:
                cur.execute("ROLLBACK")
                return {"status": "DENIED", "reason": "SOURCE_REVISION_STALE"}

            if prop["authority_class"] == "AUTO_EXECUTE":
                max_hr = int(
                    self.thresholds["authority_classes"]["AUTO_EXECUTE"]["limits"][
                        "max_executions_per_agent_per_logical_hour"
                    ]
                )
                cutoff_hr = (now_utc - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
                cnt_row = cur.execute(
                    """
                    SELECT COUNT(*) AS cnt FROM action_receipts
                    WHERE proposer_id = ? AND authority_class = 'AUTO_EXECUTE' AND executed_at_utc >= ?
                    """,
                    (prop["proposer_id"], cutoff_hr),
                ).fetchone()
                if int(cnt_row["cnt"]) >= max_hr:
                    cur.execute("ROLLBACK")
                    return {"status": "DENIED", "reason": "AUTO_EXECUTE_RATE_LIMIT_EXCEEDED"}
            else:
                if not auth_id:
                    cur.execute("ROLLBACK")
                    return {"status": "DENIED", "reason": "MISSING_AUTHORIZATION"}
                auth = cur.execute(
                    "SELECT * FROM action_authorizations WHERE auth_id = ? AND proposal_id = ?",
                    (auth_id, proposal_id),
                ).fetchone()
                if auth is None:
                    cur.execute("ROLLBACK")
                    return {"status": "DENIED", "reason": "INVALID_AUTHORIZATION"}
                if auth["branch_id"] != branch_id:
                    cur.execute("ROLLBACK")
                    return {"status": "DENIED", "reason": "CROSS_BRANCH_APPROVAL_REUSE_FORBIDDEN"}
                if auth["payload_digest"] != digest:
                    cur.execute("ROLLBACK")
                    return {"status": "DENIED", "reason": "AUTHORIZATION_DIGEST_MISMATCH"}
                if auth["policy_version"] != self.policy_version:
                    cur.execute("ROLLBACK")
                    return {"status": "DENIED", "reason": "POLICY_VERSION_MISMATCH"}
                exp = datetime.fromisoformat(auth["expires_at_utc"].replace("Z", "+00:00"))
                if now_utc > exp:
                    cur.execute("ROLLBACK")
                    return {"status": "DENIED", "reason": "AUTHORIZATION_EXPIRED"}

            cur.execute(
                """
                INSERT INTO action_receipts (
                    idempotency_key, proposal_id, auth_id, branch_id, proposer_id,
                    authority_class, payload_digest, source_revision, execution_status, executed_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'EXECUTED', ?)
                """,
                (
                    idempotency_key,
                    proposal_id,
                    auth_id,
                    branch_id,
                    prop["proposer_id"],
                    prop["authority_class"],
                    digest,
                    eff_rev,
                    now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                ),
            )
            cur.execute("COMMIT")
            return {
                "status": "EXECUTED",
                "idempotency_key": idempotency_key,
                "proposal_id": proposal_id,
                "auth_id": auth_id,
                "payload_digest": digest,
                "source_revision": eff_rev,
            }
        except Exception:
            cur.execute("ROLLBACK")
            raise

    def close(self) -> None:
        self.conn.close()
