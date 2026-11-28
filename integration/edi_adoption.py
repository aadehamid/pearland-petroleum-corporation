#!/usr/bin/env python3
"""EDI Provisional Adapter CFG-0 Adoption Handler (WP-2, EDI-001 §2–§4, B7).

Validates WP-1's structured DEXPI CFG-0 engineering topology (`fixtures/golden/cfg0_dexpi_topology.json`),
enforces directed graph integrity (every piping connection endpoint and pump resolves to declared
equipment), compares the adopted canonical digest against the independent upstream CFG-0 source
digest (B7), and records an idempotent EDI-001 §2 adoption receipt keyed by `request_id`.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


EDI_PROVISIONAL_COMMIT = "12a4a6a"


def canonical_cfg0_digest(topology: Mapping[str, Any]) -> str:
    """Compute canonical SHA-256 digest over CFG-0 configuration_id, site_id, equipment, and piping_connections."""
    equipment = topology.get("equipment", [])
    connections = topology.get("piping_connections", [])
    core = {
        "configuration_id": str(topology["configuration_id"]),
        "site_id": str(topology["site_id"]),
        "equipment": sorted(equipment, key=lambda x: str(x["tag"])),
        "piping_connections": sorted(connections, key=lambda x: str(x["id"])),
    }
    return hashlib.sha256(
        json.dumps(core, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


class EDIAdoptionRegistry:
    """Idempotent EDI-001 §2/§4 adoption registry keyed by request_id."""

    def __init__(self) -> None:
        self._receipts_by_request: dict[str, dict[str, Any]] = {}

    def adopt_cfg0_topology(
        self,
        cfg0_path: str | Path,
        *,
        request_id: str,
        world_id: str,
        branch_id: str,
        authorized_actor: str,
        expected_cfg0_digest: str,
        expected_prior_configuration: str | None = None,
        edi_publication_id: str = "EDI-PUB-CFG0-V1",
        source_approval_evidence: str = "ADR-0054",
        effective_at_utc: str = "2026-06-15T00:00:00Z",
        recorded_at_utc: str | None = None,
    ) -> dict[str, Any]:
        """Validate WP-1 CFG-0 through EDI provisional adapter and return an idempotent EDI-001 §2 receipt."""
        raw = json.loads(Path(cfg0_path).read_text(encoding="utf-8"))
        equipment = raw.get("equipment", [])
        connections = raw.get("piping_connections", [])
        if not equipment or not connections:
            raise ValueError("EDI-001: CFG-0 topology must declare non-empty equipment and piping_connections")

        node_ids = {str(e["tag"]) for e in equipment}
        dangling: list[str] = []
        for conn in connections:
            src = str(conn["from"])
            dst = str(conn["to"])
            if src not in node_ids or dst not in node_ids:
                dangling.append(f"{conn['id']}: {src} -> {dst}")
            for pid in conn.get("pumps", []):
                if str(pid) not in node_ids:
                    dangling.append(f"{conn['id']}: pump {pid}")
        if dangling:
            raise ValueError(f"EDI-001: dangling directed edges or pumps in CFG-0 topology: {dangling}")

        adopted_digest = canonical_cfg0_digest(raw)

        # Idempotent request_id replay vs conflict (EDI-001 §4)
        if request_id in self._receipts_by_request:
            prior = self._receipts_by_request[request_id]
            if prior["adopted_digest"] == adopted_digest and prior["branch_id"] == branch_id:
                return dict(prior)
            return {
                "request_id": request_id,
                "outcome": "CONFLICT",
                "reason": "DIFFERENT_PAYLOAD_FOR_EXISTING_REQUEST_ID",
                "prior_digest": prior["adopted_digest"],
                "incoming_digest": adopted_digest,
                "b7_digest_parity": False,
            }

        # Non-vacuous B7 check: compare adopted topology digest against independent expected upstream CFG-0 digest!
        if adopted_digest != expected_cfg0_digest:
            raise ValueError(
                f"B7 digest parity violation: adopted digest {adopted_digest} != expected upstream CFG-0 digest {expected_cfg0_digest}"
            )

        rec_ts = recorded_at_utc or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        receipt = {
            "adapter_id": "edi-provisional",
            "upstream_commit": EDI_PROVISIONAL_COMMIT,
            "request_id": request_id,
            "world_id": world_id,
            "branch_id": branch_id,
            "expected_prior_configuration": expected_prior_configuration,
            "edi_publication_id": edi_publication_id,
            "source_approval_evidence": source_approval_evidence,
            "authorized_actor": authorized_actor,
            "effective_at_utc": effective_at_utc,
            "recorded_at_utc": rec_ts,
            "outcome": "ADOPTED",
            "configuration_id": str(raw["configuration_id"]),
            "site_id": str(raw["site_id"]),
            "equipment_count": len(equipment),
            "connection_count": len(connections),
            "expected_cfg0_digest": expected_cfg0_digest,
            "adopted_digest": adopted_digest,
            "b7_digest_parity": True,
            "provenance_class": "SYNTHETIC",
        }
        self._receipts_by_request[request_id] = dict(receipt)
        return receipt


def adopt_cfg0_topology(
    cfg0_path: str | Path,
    *,
    request_id: str,
    world_id: str,
    branch_id: str,
    authorized_actor: str,
    expected_cfg0_digest: str,
    expected_prior_configuration: str | None = None,
    edi_publication_id: str = "EDI-PUB-CFG0-V1",
    source_approval_evidence: str = "ADR-0054",
    effective_at_utc: str = "2026-06-15T00:00:00Z",
    recorded_at_utc: str | None = None,
) -> dict[str, Any]:
    """One-shot wrapper around EDIAdoptionRegistry for single-adoption callers."""
    return EDIAdoptionRegistry().adopt_cfg0_topology(
        cfg0_path,
        request_id=request_id,
        world_id=world_id,
        branch_id=branch_id,
        authorized_actor=authorized_actor,
        expected_cfg0_digest=expected_cfg0_digest,
        expected_prior_configuration=expected_prior_configuration,
        edi_publication_id=edi_publication_id,
        source_approval_evidence=source_approval_evidence,
        effective_at_utc=effective_at_utc,
        recorded_at_utc=recorded_at_utc,
    )
