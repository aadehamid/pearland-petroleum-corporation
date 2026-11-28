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


_COMPRESSED_MAGIC_PREFIXES: tuple[bytes, ...] = (b"\x1f\x8b", b"\x78\x01", b"\x78\x5e", b"\x78\x9c", b"\x78\xda")


def _find_next_magic_offset(buf: bytes) -> int | None:
    """Return earliest offset > 0 of an embedded gzip/zlib header inside buf, or None."""
    best: int | None = None
    for magic in _COMPRESSED_MAGIC_PREFIXES:
        idx = buf.find(magic, 1)
        if idx != -1 and (best is None or idx < best):
            best = idx
    return best


def _recover_partial_stream(wbits: int, data: bytes, remaining_budget: int) -> tuple[bytes, bool, bool]:
    """Recover as much decompressed output as possible before a corrupt trailer or mid-stream error.

    Returns (recovered_bytes, budget_hit, reached_eof).
    """
    if remaining_budget <= 0 or not data:
        return b"", False, False
    dobj = zlib.decompressobj(wbits)
    out = bytearray()
    budget_hit = False
    chunk_size = 1024
    pos = 0
    n = len(data)
    while pos < n:
        rem_cap = remaining_budget - len(out)
        if rem_cap <= 0:
            budget_hit = True
            break
        end = min(pos + chunk_size, n)
        try:
            piece = dobj.decompress(data[pos:end], rem_cap)
            if piece:
                out.extend(piece)
            if dobj.unconsumed_tail:
                budget_hit = True
                break
            if dobj.eof:
                break
            pos = end
        except zlib.error:
            if chunk_size > 1:
                # Re-attempt byte-by-byte inside the failing block with a fresh decompressor
                # replayed cleanly up to `pos`, so everything before the bad byte/trailer is kept.
                dobj = zlib.decompressobj(wbits)
                out = bytearray()
                try:
                    if pos > 0:
                        prefix_piece = dobj.decompress(data[:pos], remaining_budget)
                        out.extend(prefix_piece)
                except zlib.error:
                    break
                for b_idx in range(pos, end):
                    rem_cap = remaining_budget - len(out)
                    if rem_cap <= 0:
                        budget_hit = True
                        break
                    try:
                        piece = dobj.decompress(data[b_idx : b_idx + 1], rem_cap)
                        if piece:
                            out.extend(piece)
                        if dobj.unconsumed_tail:
                            budget_hit = True
                            break
                        if dobj.eof:
                            break
                    except zlib.error:
                        break
            break
    try:
        rem_cap = remaining_budget - len(out)
        if rem_cap > 0 and not budget_hit:
            flushed = dobj.flush(rem_cap)
            if flushed:
                out.extend(flushed[:rem_cap])
    except zlib.error:
        pass
    return bytes(out), budget_hit, bool(dobj.eof)


def _is_clean_utf8_text(buf: bytes) -> bool:
    """Return True iff buf is valid UTF-8 text with no NUL or non-whitespace C0 control bytes."""
    try:
        text = buf.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return False
    for ch in text:
        code = ord(ch)
        if code < 32 and ch not in ("\t", "\n", "\r"):
            return False
    return True


def _decompress_all_members(buf: bytes) -> tuple[list[tuple[bytes, bool]], bool, bool]:
    """Decompress gzip/zlib members (resuming after garbage gaps between intact gzip/zlib headers) and raw-deflate streams.

    Returns ([(buffer, is_speculative), ...], budget_exceeded, fully_decompressed_cleanly).
    `fully_decompressed_cleanly` is True iff a gzip or zlib pass consumed `buf` cleanly to EOF with no errors.
    """
    results: list[tuple[bytes, bool]] = []
    budget_exceeded = False
    fully_decompressed_cleanly = False
    for wbits in (16 + zlib.MAX_WBITS, zlib.MAX_WBITS, -zlib.MAX_WBITS):
        rem = buf
        chunks: list[bytes] = []
        total_out = 0
        had_error = False
        had_clean_member = False
        is_raw_probe = wbits == -zlib.MAX_WBITS
        while rem:
            remaining_budget = _MAX_DECOMPRESSED_BYTES - total_out
            if remaining_budget <= 0:
                budget_exceeded = True
                had_error = True
                break
            try:
                dobj = zlib.decompressobj(wbits)
                part = dobj.decompress(rem, remaining_budget)
                if dobj.unconsumed_tail:
                    budget_exceeded = True
                    had_error = True
                    if part:
                        chunks.append(part)
                        results.append((part, True))
                    break
                part += dobj.flush()
                if not dobj.eof:
                    # Truncated stream without reaching deflate EOF
                    had_error = True
                    if part:
                        total_out += len(part)
                        chunks.append(part)
                        results.append((part, True))
                    break
                if part:
                    total_out += len(part)
                    chunks.append(part)
                    results.append((part, is_raw_probe))
                had_clean_member = True
                nxt = dobj.unused_data
                if not nxt:
                    rem = b""
                    break
                if len(nxt) >= len(rem):
                    had_error = True
                    break
                rem = nxt
            except zlib.error:
                had_error = True
                # Recover any bytes decompressed before a corrupt trailer or mid-stream error
                # instead of silently discarding them; also probe past corrupt 2-byte zlib / 10-byte gzip headers.
                partial, partial_budget, _ = _recover_partial_stream(wbits, rem, remaining_budget)
                header_skip_partial = b""
                if not partial and wbits == zlib.MAX_WBITS and len(rem) > 2:
                    cand, skip_budget, _ = _recover_partial_stream(-zlib.MAX_WBITS, rem[2:], remaining_budget)
                    header_skip_partial = cand
                    partial_budget = partial_budget or skip_budget
                elif not partial and wbits == 16 + zlib.MAX_WBITS and len(rem) > 10:
                    cand, skip_budget, _ = _recover_partial_stream(-zlib.MAX_WBITS, rem[10:], remaining_budget)
                    header_skip_partial = cand
                    partial_budget = partial_budget or skip_budget
                recovered = partial or header_skip_partial
                if partial_budget:
                    budget_exceeded = True
                if recovered:
                    total_out += len(recovered)
                    chunks.append(recovered)
                    results.append((recovered, True))
                next_off = _find_next_magic_offset(rem)
                if next_off is None:
                    break
                rem = rem[next_off:]
        if len(chunks) > 1:
            results.append((b"".join(chunks), is_raw_probe or had_error))
        if not is_raw_probe and had_clean_member and not had_error and not rem:
            fully_decompressed_cleanly = True
    return results, budget_exceeded, fully_decompressed_cleanly


def _decode_one_layer(raw_bytes: bytes, *, speculative: bool) -> tuple[list[tuple[bytes, bool]], bool, bool]:
    """Decode one layer of gzip/zlib (incl. multi-member+padded), base64 (offsets 0..3), and hex (offsets 0..1).

    Returns ([(child_bytes, child_is_speculative), ...], budget_exceeded, corrupt_unscanned).
    Only non-speculative binary buffers that fail clean gzip/zlib decompression emit `corrupt_unscanned`,
    preventing both false positives on speculative ASCII offset slices and fail-open on corrupt archives.
    """
    decompressed, budget_exceeded, cleanly_decompressed = _decompress_all_members(raw_bytes)
    out: list[tuple[bytes, bool]] = [(buf, speculative or child_spec) for buf, child_spec in decompressed]

    corrupt_unscanned = (
        (not speculative)
        and bool(raw_bytes)
        and (not _is_clean_utf8_text(raw_bytes))
        and (not cleanly_decompressed)
    )

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
                    # Base64/hex decodings are speculative probes (plain ASCII words can decode as
                    # random bytes), so they are scanned for markers without triggering corrupt-binary FPs.
                    out.append((decoded, True))
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
                        out.append((decoded, True))
                except Exception:
                    pass
    return out, budget_exceeded, corrupt_unscanned


def _decode_variants_for_scan(raw: bytes | str, max_depth: int = 3) -> tuple[list[str], bool, bool]:
    """Produce decoded text views recursively (up to max_depth layers) plus fail-closed budget/corrupt flags."""
    raw_bytes = raw.encode("utf-8") if isinstance(raw, str) else raw
    # Track best (least-speculative) state seen per byte buffer so a non-speculative path is never shadowed
    seen: dict[bytes, bool] = {raw_bytes: False}
    byte_candidates: list[bytes] = [raw_bytes]
    frontier: list[tuple[bytes, bool]] = [(raw_bytes, False)]
    budget_exceeded = False
    corrupt_unscanned = False
    for _ in range(max_depth):
        next_frontier: list[tuple[bytes, bool]] = []
        for buf, is_spec in frontier:
            children, exceeded, corrupt = _decode_one_layer(buf, speculative=is_spec)
            budget_exceeded = budget_exceeded or exceeded
            corrupt_unscanned = corrupt_unscanned or corrupt
            for child, child_spec in children:
                prev_spec = seen.get(child)
                if prev_spec is None:
                    seen[child] = child_spec
                    byte_candidates.append(child)
                    next_frontier.append((child, child_spec))
                elif prev_spec and not child_spec:
                    seen[child] = False
                    next_frontier.append((child, False))
        if not next_frontier:
            break
        frontier = next_frontier

    views: list[str] = []
    if isinstance(raw, str):
        views.append(raw.lower())
    for cand in byte_candidates:
        views.extend(_text_views_from_bytes(cand))
    return views, budget_exceeded, corrupt_unscanned


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
        views, budget_exceeded, corrupt_unscanned = _decode_variants_for_scan(raw)
        if budget_exceeded:
            findings.append({"artifact": name, "marker": "DECOMPRESSION_BUDGET_EXCEEDED_UNSCANNED"})
        if corrupt_unscanned:
            findings.append({"artifact": name, "marker": "DECOMPRESSION_ERROR_UNSCANNED"})
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
