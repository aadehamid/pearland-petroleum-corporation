#!/usr/bin/env python3
"""WP-5B Server-Side Permission-Filtered Relate WASM Graph Package Serializer (ADR-0052).

Builds authorized browser-side graph packages for the Relate WASM Interactive
Enterprise Context Explorer strictly BEFORE serialization so zero unauthorized
nodes, edges, or property bytes enter the browser payload. Enforces:
- Fail-closed role-based filtering on every node, display name, property, edge, and KPI card
  (non-collection role fields such as bare strings fail closed; denial wins)
- Timezone-aware UTC temporal publication cutoff filtering with sub-second precision
  (published_at_utc <= reader_cutoff_utc), failing closed on missing/unparseable timestamps,
  plus cutoff-scoped retraction
- Explicit badge separation: POTENTIAL_EXPOSURE (graph path) vs MODEL_QUANTIFIED (LP/KPI)
- Non-finite value rejection on KPI cards and deterministic directed reachability over
  filtered edges (live Neo4j Cypher parity runs separately once Neo4j Community is wired)
"""
from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence


def _parse_utc(ts: Any) -> datetime | None:
    if not isinstance(ts, str) or not ts.strip():
        return None
    try:
        dt = datetime.fromisoformat(ts.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        return None
    return dt.astimezone(timezone.utc)


def _format_utc(dt: datetime) -> str:
    """Format UTC datetime preserving sub-second precision so cutoff replay is exact."""
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _role_allowed(reader_role: str, allowed_roles: Any) -> bool:
    """Fail-closed RBAC membership check: bare strings, bytes, Mappings, and non-iterables NEVER match."""
    if not isinstance(reader_role, str) or not reader_role:
        return False
    if isinstance(allowed_roles, (str, bytes, bytearray, Mapping)) or not isinstance(allowed_roles, Iterable):
        return False
    return any(isinstance(r, str) and r == reader_role for r in allowed_roles)


def _is_visible_at_cutoff(item: Mapping[str, Any], cutoff_dt: datetime) -> bool:
    pub_dt = _parse_utc(item.get("published_at_utc"))
    if pub_dt is None or pub_dt > cutoff_dt:
        return False
    ret_raw = item.get("retracted_at_utc")
    if ret_raw is not None:
        ret_dt = _parse_utc(ret_raw)
        if ret_dt is None or ret_dt <= cutoff_dt:
            return False
    return True


def build_filtered_graph_package(
    *,
    branch_id: str,
    reader_role: str,
    reader_cutoff_utc: str,
    nodes: Sequence[Mapping[str, Any]],
    edges: Sequence[Mapping[str, Any]],
    kpi_cards: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Filter nodes, edges, and KPI cards strictly server-side before browser serialization."""
    cutoff_dt = _parse_utc(reader_cutoff_utc)
    if cutoff_dt is None:
        raise ValueError(f"Invalid timezone-aware UTC reader_cutoff_utc: {reader_cutoff_utc!r}")

    visible_nodes: list[dict[str, Any]] = []
    visible_ids: set[str] = set()
    for n in nodes:
        if n.get("branch_id") != branch_id:
            continue
        if not _is_visible_at_cutoff(n, cutoff_dt):
            continue
        if not _role_allowed(reader_role, n.get("allowed_roles")):
            continue
        raw_props = dict(n.get("properties", {}))
        node_id = str(n["id"])
        raw_name = str(n.get("name", node_id))
        if "property_allowed_roles" in n and not isinstance(n["property_allowed_roles"], Mapping):
            # Fail closed when property_allowed_roles container is malformed: emit zero properties and redact name
            clean_props = {}
            safe_name = node_id
        else:
            prop_roles: Mapping[str, Any] = n.get("property_allowed_roles") or {}
            clean_props = {
                str(k): v
                for k, v in raw_props.items()
                if not str(k).startswith("_")
                and (str(k) not in prop_roles or _role_allowed(reader_role, prop_roles[str(k)]))
            }
            safe_name = (
                raw_name
                if ("name" not in prop_roles or _role_allowed(reader_role, prop_roles["name"]))
                else node_id
            )
        clean_node = {
            "id": node_id,
            "label": str(n["label"]),
            "name": safe_name,
            # UX-001 / ADR-0052: graph path nodes ALWAYS carry POTENTIAL_EXPOSURE; never copy MODEL_QUANTIFIED
            "badge": "POTENTIAL_EXPOSURE",
            "provenance_class": str(n.get("provenance_class", "SYNTHETIC")),
            "properties": clean_props,
        }
        visible_nodes.append(clean_node)
        visible_ids.add(node_id)

    visible_edges: list[dict[str, Any]] = []
    for e in edges:
        if e.get("branch_id") != branch_id:
            continue
        if not _is_visible_at_cutoff(e, cutoff_dt):
            continue
        if not _role_allowed(reader_role, e.get("allowed_roles")):
            continue
        src = str(e["source"])
        dst = str(e["target"])
        # Edge only visible if BOTH endpoints are authorized and visible
        if src not in visible_ids or dst not in visible_ids:
            continue
        visible_edges.append(
            {
                "source": src,
                "target": dst,
                "type": str(e["type"]),
                # UX-001 / ADR-0052: graph relationship paths ALWAYS carry POTENTIAL_EXPOSURE
                "badge": "POTENTIAL_EXPOSURE",
                "provenance_class": str(e.get("provenance_class", "SYNTHETIC")),
            }
        )

    visible_cards: list[dict[str, Any]] = []
    for c in kpi_cards:
        if c.get("branch_id") != branch_id:
            continue
        if not _is_visible_at_cutoff(c, cutoff_dt):
            continue
        if not _role_allowed(reader_role, c.get("allowed_roles")):
            continue
        val = float(c["value"])
        if not math.isfinite(val):
            raise ValueError(f"Non-finite KPI card value for {c.get('card_id')!r}: {c.get('value')!r}")
        visible_cards.append(
            {
                "card_id": str(c["card_id"]),
                "badge": "MODEL_QUANTIFIED",
                "model_run_id": str(c["model_run_id"]),
                "kpi_name": str(c["kpi_name"]),
                "value": val,
                "unit": str(c["unit"]),
                "provenance_class": str(c.get("provenance_class", "DERIVED")),
            }
        )

    visible_nodes.sort(key=lambda x: x["id"])
    visible_edges.sort(key=lambda x: (x["source"], x["type"], x["target"]))
    visible_cards.sort(key=lambda x: x["card_id"])

    pkg = {
        "schema_version": "1.0.0",
        "explorer_runtime": "relate-wasm",
        "branch_id": branch_id,
        "reader_role": reader_role,
        "reader_cutoff_utc": _format_utc(cutoff_dt),
        "nodes": visible_nodes,
        "edges": visible_edges,
        "model_quantified_cards": visible_cards,
        "provenance_class": "DERIVED",
    }
    pkg["package_sha256"] = hashlib.sha256(
        json.dumps(pkg, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return pkg


def reachable_exposure_ids(pkg: Mapping[str, Any], start_node_id: str) -> list[str]:
    """Evaluate directed exposure reachability inside a filtered Relate WASM graph package."""
    visible_node_ids = {str(n["id"]) for n in pkg.get("nodes", [])}
    if start_node_id not in visible_node_ids:
        return []
    adj: dict[str, list[str]] = {}
    for e in pkg.get("edges", []):
        src = str(e["source"])
        dst = str(e["target"])
        if src in visible_node_ids and dst in visible_node_ids:
            adj.setdefault(src, []).append(dst)
    visited: set[str] = set()
    stack = [start_node_id]
    while stack:
        curr = stack.pop()
        for nxt in adj.get(curr, []):
            if nxt not in visited:
                visited.add(nxt)
                stack.append(nxt)
    return sorted(visited)
