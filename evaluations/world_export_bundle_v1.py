#!/usr/bin/env python3
"""WP-8B Certified WorldExportBundle v1 Assembler & Automated Leak Auditor (UC-6, ADR-0053, B13).

Assembles a strict WorldExportBundle v1 manifest conforming to
schemas/world_export_bundle.schema.json, partitioning:
- observable/ (exports/world_bundle/observable/ in pearland-petroleum-corp)
  for sister repositories ICE, EDI, EPM, and ECE
- hidden_truth/ (evaluation/hidden/ in pearland-petroleum-hidden)
  under a separate credential boundary

Scans both the observable manifest metadata and supplied observable payloads
across UTF-8, UTF-16LE/BE (even and odd byte offsets), UTF-32LE/BE, gzip/zlib,
base64, and hex encodings for declared hidden-truth markers (ADR-0053, B13).
"""
from __future__ import annotations

import base64
import gzip
import hashlib
import json
import re
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import jsonschema

FORBIDDEN_OBSERVABLE_MARKERS: tuple[str, ...] = (
    "evaluation/hidden",
    "pearland-petroleum-hidden",
    "hidden_truth",
    "canonical_world_snapshots",
    "evaluation_scoring_keys",
    "separate_credential_boundary",
    "canonical_world_truth",
    "hidden_scoring_key",
    "root_seed_secret",
)

_B64_TOKEN_RE = re.compile(rb"[A-Za-z0-9+/=_-]{16,}")
_HEX_TOKEN_RE = re.compile(rb"[0-9a-fA-F]{16,}")


def _text_views_from_bytes(buf: bytes) -> list[str]:
    views = [
        buf.decode("utf-8", errors="replace").lower(),
        buf.decode("utf-8", errors="ignore").lower(),
    ]
    for offset in (0, 1):
        sliced = buf[offset:]
        for enc in ("utf-16-le", "utf-16-be"):
            try:
                views.append(sliced.decode(enc, errors="ignore").lower())
            except UnicodeError:
                pass
    for offset in (0, 1, 2, 3):
        sliced = buf[offset:]
        for enc in ("utf-32-le", "utf-32-be"):
            try:
                views.append(sliced.decode(enc, errors="ignore").lower())
            except UnicodeError:
                pass
    return views


_MAX_DECOMPRESSED_BYTES = 64 * 1024 * 1024


def _decompress_all_members(buf: bytes) -> list[bytes]:
    """Decompress all members of gzip/zlib/raw-deflate streams tolerating trailing non-member bytes."""
    results: list[bytes] = []
    for wbits in (16 + zlib.MAX_WBITS, zlib.MAX_WBITS, -zlib.MAX_WBITS):
        rem = buf
        chunks: list[bytes] = []
        total_out = 0
        while rem:
            try:
                dobj = zlib.decompressobj(wbits)
                part = dobj.decompress(rem, _MAX_DECOMPRESSED_BYTES - total_out) + dobj.flush()
                if part:
                    total_out += len(part)
                    chunks.append(part)
                    results.append(part)
                    if total_out >= _MAX_DECOMPRESSED_BYTES:
                        break
                nxt = dobj.unused_data
                if not nxt or len(nxt) >= len(rem):
                    break
                rem = nxt
            except Exception:
                break
        if len(chunks) > 1:
            results.append(b"".join(chunks))
    for decompressor in (gzip.decompress, zlib.decompress):
        try:
            unpacked = decompressor(buf)
            if unpacked:
                results.append(unpacked)
        except Exception:
            pass
    return results


def _decode_one_layer(raw_bytes: bytes) -> list[bytes]:
    """Decode one layer of gzip/zlib (incl. multi-member+padded), base64 (offsets 0..3), and hex (offsets 0..1)."""
    out: list[bytes] = []
    out.extend(_decompress_all_members(raw_bytes))

    stripped = re.sub(rb"\s+", b"", raw_bytes)
    for token in (stripped, *_B64_TOKEN_RE.findall(raw_bytes)):
        for offset in (0, 1, 2, 3):
            sub = token[offset:]
            if len(sub) < 16:
                continue
            norm = sub.replace(b"-", b"+").replace(b"_", b"/").rstrip(b"=")
            if len(norm) % 4 == 1:
                continue
            padded = norm + b"=" * ((-len(norm)) % 4)
            try:
                decoded = base64.b64decode(padded, validate=True)
                if decoded:
                    out.append(decoded)
            except Exception:
                pass

    for token in (stripped, *_HEX_TOKEN_RE.findall(raw_bytes)):
        for offset in (0, 1):
            sub = token[offset:]
            even_len = len(sub) - (len(sub) % 2)
            if even_len >= 16:
                try:
                    decoded = bytes.fromhex(sub[:even_len].decode("ascii"))
                    if decoded:
                        out.append(decoded)
                except Exception:
                    pass
    return out


def _decode_variants_for_scan(raw: bytes | str, max_depth: int = 3) -> list[str]:
    """Produce decoded text views recursively (up to max_depth layers) across UTF-8/16/32, gzip/zlib, base64, hex."""
    raw_bytes = raw.encode("utf-8") if isinstance(raw, str) else raw
    seen: set[bytes] = {raw_bytes}
    byte_candidates: list[bytes] = [raw_bytes]
    frontier: list[bytes] = [raw_bytes]
    for _ in range(max_depth):
        next_frontier: list[bytes] = []
        for buf in frontier:
            for child in _decode_one_layer(buf):
                if child not in seen:
                    seen.add(child)
                    byte_candidates.append(child)
                    next_frontier.append(child)
        if not next_frontier:
            break
        frontier = next_frontier

    views: list[str] = []
    if isinstance(raw, str):
        views.append(raw.lower())
    for cand in byte_candidates:
        views.extend(_text_views_from_bytes(cand))
    return views


def audit_observable_for_hidden_leaks(
    observable_payloads: Mapping[str, bytes | str],
    checked_at_utc: str | None = None,
    manifest_json: str | None = None,
) -> dict[str, Any]:
    """Scan observable manifest metadata and supplied observable payloads for hidden-truth markers."""
    ts = checked_at_utc or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    items: list[tuple[str, bytes | str]] = []
    if manifest_json is not None:
        items.append(("manifest:__observable_manifest__", manifest_json))
    for name, raw in sorted(observable_payloads.items()):
        items.append((f"payload:{name}", raw))

    findings: list[dict[str, str]] = []
    for name, raw in items:
        views = _decode_variants_for_scan(raw)
        for marker in FORBIDDEN_OBSERVABLE_MARKERS:
            if any(marker in v for v in views):
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
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    """Assemble, leak-audit, and schema-validate WorldExportBundle v1."""
    if not adapter_pins:
        raise ValueError("adapter_pins must declare at least one pinned upstream adapter")
    now_utc = created_at_utc or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    observable_section = {
        "r2_bucket": "pearland-petroleum-corp",
        "r2_prefix": f"exports/world_bundle/observable/{bundle_id}/",
        "delta_tables": [dict(x) for x in observable_artifacts["delta_tables"]],
        "ice_ot_l0": [dict(x) for x in observable_artifacts["ice_ot_l0"]],
        "edi_topology": [dict(x) for x in observable_artifacts["edi_topology"]],
        "epm_kpi_fixtures": [dict(x) for x in observable_artifacts["epm_kpi_fixtures"]],
        "ece_evidence_dossiers": [dict(x) for x in observable_artifacts["ece_evidence_dossiers"]],
    }
    # Always audit BOTH the observable manifest section itself (unshadowable) AND caller-supplied payloads
    audit = audit_observable_for_hidden_leaks(
        observable_payloads_for_audit,
        checked_at_utc=now_utc,
        manifest_json=json.dumps(observable_section, sort_keys=True),
    )
    all_approved = all(p.get("maturity_status") == "APPROVED_UPSTREAM_RELEASE" for p in adapter_pins)
    # Provisional commit-pinned adapters cap verdict strictly at QUALIFIED_PROVISIONAL (VERIFY-001 §3)
    verdict = (
        "QUALIFIED"
        if (all_approved and audit["leak_audit"]["status"] == "PASSED")
        else ("QUALIFIED_PROVISIONAL" if audit["leak_audit"]["status"] == "PASSED" else "DRAFT")
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
        "observable": observable_section,
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
