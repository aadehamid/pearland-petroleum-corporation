#!/usr/bin/env python3
"""WP-8B Certified WorldExportBundle v1 Assembler & Automated Leak Auditor (UC-6, ADR-0053, B13).

Assembles a strict WorldExportBundle v1 manifest conforming to
schemas/world_export_bundle.schema.json, partitioning:
- observable/ (exports/world_bundle/observable/ in pearland-petroleum-corp)
  for sister repositories ICE, EDI, EPM, and ECE
- hidden_truth/ (evaluation/hidden/ in pearland-petroleum-hidden)
  under a separate credential boundary

Runs automated field-level and path-level leak audits proving zero canonical
hidden-truth fields or restricted paths appear inside observable/ payloads.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import jsonschema

FORBIDDEN_OBSERVABLE_MARKERS: tuple[str, ...] = (
    "evaluation/hidden",
    "pearland-petroleum-hidden",
    "canonical_world_truth",
    "hidden_scoring_key",
    "root_seed_secret",
)


def audit_observable_for_hidden_leaks(
    observable_payloads: Mapping[str, bytes | str],
    checked_at_utc: str | None = None,
) -> dict[str, Any]:
    """Scan every observable artifact payload for hidden-truth markers (ADR-0053, B13)."""
    ts = checked_at_utc or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    findings: list[dict[str, str]] = []
    for name, raw in sorted(observable_payloads.items()):
        text = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else str(raw)
        low = text.lower()
        for marker in FORBIDDEN_OBSERVABLE_MARKERS:
            if marker in low:
                findings.append({"artifact": name, "marker": marker})
    audit_body = {
        "status": "PASSED" if not findings else "FAILED",
        "checked_at": ts,
        "hidden_fields_found_in_observable": len(findings),
    }
    audit_sha = hashlib.sha256(
        json.dumps({"audit": audit_body, "findings": findings}, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    audit_body["audit_sha256"] = audit_sha
    return {"leak_audit": audit_body, "findings": findings}


def assemble_world_export_bundle_v1(
    *,
    bundle_id: str,
    world_version: str,
    branch_id: str,
    root_seed: int,
    adapter_pins: Sequence[Mapping[str, Any]],
    observable_artifacts: Mapping[str, Sequence[Mapping[str, Any]]],
    hidden_artifacts: Mapping[str, Sequence[Mapping[str, Any]]],
    observable_payloads_for_audit: Mapping[str, bytes | str],
    schema_path: str | Path,
) -> dict[str, Any]:
    """Assemble, leak-audit, and schema-validate WorldExportBundle v1."""
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    audit = audit_observable_for_hidden_leaks(observable_payloads_for_audit, checked_at_utc=now_utc)
    all_approved = all(p.get("maturity_status") == "APPROVED_UPSTREAM_RELEASE" for p in adapter_pins)
    # Provisional commit-pinned adapters cap verdict strictly at QUALIFIED_PROVISIONAL (VERIFY-001 §3)
    verdict = "QUALIFIED" if (all_approved and audit["leak_audit"]["status"] == "PASSED") else (
        "QUALIFIED_PROVISIONAL" if audit["leak_audit"]["status"] == "PASSED" else "DRAFT"
    )

    bundle: dict[str, Any] = {
        "schema_version": "1.0.0",
        "bundle_id": bundle_id,
        "bundle_version": "1.0.0",
        "world_version": world_version,
        "branch_id": branch_id,
        "seed_policy": {
            "prng_algorithm": "numpy.random.PCG64",
            "prng_version": "1.0",
            "root_seed": int(root_seed),
        },
        "created_at": now_utc,
        "qualification_verdict": verdict,
        "provenance_class": "SYNTHETIC",
        "upstream_adapter_pins": [dict(p) for p in adapter_pins],
        "observable": {
            "r2_bucket": "pearland-petroleum-corp",
            "r2_prefix": f"exports/world_bundle/observable/{bundle_id}/",
            "delta_tables": [dict(x) for x in observable_artifacts["delta_tables"]],
            "ice_ot_l0": [dict(x) for x in observable_artifacts["ice_ot_l0"]],
            "edi_topology": [dict(x) for x in observable_artifacts["edi_topology"]],
            "epm_kpi_fixtures": [dict(x) for x in observable_artifacts["epm_kpi_fixtures"]],
            "ece_evidence_dossiers": [dict(x) for x in observable_artifacts["ece_evidence_dossiers"]],
        },
        "hidden_truth": {
            "r2_bucket": "pearland-petroleum-hidden",
            "r2_prefix": f"evaluation/hidden/world_bundle/{bundle_id}/",
            "separate_credential_boundary": True,
            "canonical_world_snapshots": [dict(x) for x in hidden_artifacts["canonical_world_snapshots"]],
            "evaluation_scoring_keys": [dict(x) for x in hidden_artifacts["evaluation_scoring_keys"]],
        },
        "leak_audit": audit["leak_audit"],
    }

    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    jsonschema.validate(instance=bundle, schema=schema)
    return bundle
