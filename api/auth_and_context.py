#!/usr/bin/env python3
"""Fixture user/role seeder and server-side signed session RBAC for PPC Context API (WP-3B, B14, N10).

Enforces server-side authentication and RBAC backed by users and role_assignments tables:
- Salted scrypt password hashing (never plaintext passwords)
- HMAC-SHA256 signed JWT-style bearer tokens bound to server-side user_id
- Forged client role headers (e.g. X-Role) are strictly ignored in favor of DB role_assignments
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping


SEED_USERS: tuple[tuple[str, str, str, bool], ...] = (
    ("usr-shift-sup", "shift_supervisor", "Shift Supervisor", False),
    ("usr-ref-ops", "refinery_ops_mgr", "Refinery Operations Manager", False),
    ("usr-comm-mgr", "commercial_mgr", "Commercial Manager", False),
    ("usr-vp-ops", "vp_supply_ops", "VP Supply and Operations", False),
    ("usr-planner", "planner_1", "Planner", False),
    ("usr-steward", "identity_steward", "IDENTITY_STEWARD", False),
    ("usr-agent-1", "ppc_agent_1", "Agent", True),
)


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt_b = salt or os.urandom(16)
    dk = hashlib.scrypt(password.encode("utf-8"), salt=salt_b, n=16384, r=8, p=1, dklen=32)
    return f"scrypt${base64.b64encode(salt_b).decode()}${base64.b64encode(dk).decode()}"


def verify_password(password: str, stored_hash: str) -> bool:
    algo, salt_b64, dk_b64 = stored_hash.split("$", 2)
    if algo != "scrypt":
        return False
    salt_b = base64.b64decode(salt_b64)
    expected = base64.b64decode(dk_b64)
    actual = hashlib.scrypt(password.encode("utf-8"), salt=salt_b, n=16384, r=8, p=1, dklen=32)
    return hmac.compare_digest(actual, expected)


class AuthRBACStore:
    """PostgreSQL-compatible users + role_assignments store with signed session tokens."""

    def __init__(self, db_path: str | Path, signing_secret: str):
        if len(signing_secret) < 16:
            raise ValueError("signing_secret must be at least 16 characters")
        self.db_path = Path(db_path)
        self.signing_secret = signing_secret.encode("utf-8")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                is_agent INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS role_assignments (
                user_id TEXT NOT NULL,
                role_name TEXT NOT NULL,
                PRIMARY KEY (user_id, role_name)
            );
            """
        )
        self.conn.commit()

    def seed_fixture_accounts(self, fixture_password: str = "ppc-fixture-dev-only") -> int:
        count = 0
        for uid, uname, role, is_agent in SEED_USERS:
            p_hash = hash_password(fixture_password)
            self.conn.execute(
                "INSERT OR IGNORE INTO users (user_id, username, password_hash, is_agent) VALUES (?, ?, ?, ?)",
                (uid, uname, p_hash, 1 if is_agent else 0),
            )
            self.conn.execute(
                "INSERT OR IGNORE INTO role_assignments (user_id, role_name) VALUES (?, ?)",
                (uid, role),
            )
            count += 1
        self.conn.commit()
        return count

    def issue_token(self, username: str, password: str, ttl_minutes: int = 60) -> str | None:
        row = self.conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if row is None or not verify_password(password, row["password_hash"]):
            return None
        exp = int((datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)).timestamp())
        payload = {"sub": row["user_id"], "exp": exp}
        body = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")).decode("ascii")
        sig = hmac.new(self.signing_secret, body.encode("ascii"), hashlib.sha256).hexdigest()
        return f"{body}.{sig}"

    def authenticate_request(self, token: str, headers: Mapping[str, str] | None = None) -> dict[str, Any] | None:
        """Verify signed token and load authoritative roles from DB (strictly ignoring X-Role headers)."""
        _ = headers  # Forged client role headers are NEVER trusted (B14)
        if "." not in token:
            return None
        body, sig = token.rsplit(".", 1)
        expected_sig = hmac.new(self.signing_secret, body.encode("ascii"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None
        payload = json.loads(base64.urlsafe_b64decode(body.encode("ascii")).decode("utf-8"))
        if int(payload["exp"]) < int(datetime.now(timezone.utc).timestamp()):
            return None
        uid = payload["sub"]
        user = self.conn.execute("SELECT user_id, username, is_agent FROM users WHERE user_id = ?", (uid,)).fetchone()
        if user is None:
            return None
        roles = [
            r["role_name"]
            for r in self.conn.execute("SELECT role_name FROM role_assignments WHERE user_id = ?", (uid,)).fetchall()
        ]
        return {
            "user_id": user["user_id"],
            "username": user["username"],
            "is_agent": bool(user["is_agent"]),
            "roles": roles,
        }

    def close(self) -> None:
        self.conn.close()
