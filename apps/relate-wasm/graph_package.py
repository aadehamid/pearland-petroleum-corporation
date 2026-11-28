#!/usr/bin/env python3
"""WP-5B Server-Side Permission-Filtered Relate WASM Graph Package Serializer (ADR-0052, PO-08).

Builds authorized browser-side graph packages for the Relate WASM Interactive
Enterprise Context Explorer strictly BEFORE serialization so zero unauthorized
nodes, edges, or property bytes ever enter the browser payload. Enforces:
- Role-based filtering on every node, edge, and KPI card before serialization
- Timezone-aware UTC temporal publication cutoff filtering (published_at_utc <= reader_cutoff_utc),
  failing closed when published_at_utc is missing or unparseable, plus cutoff-scoped retraction
- Explicit badge separation: POTENTIAL_EXPOSURE (graph path) vs MODEL_QUANTIFIED (LP/KPI)
- Non-finite value rejection on KPI cards and deterministic Cypher reachability parity
"""
from __future__ import annotations

import hashlib
import json
import math
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
        if reader_role not in n.get("allowed_roles", ()):
            continue
        raw_props = dict(n.get("properties", {}))
        prop_roles: Mapping[str, Sequence[str]] = n.get("property_allowed_roles", {})
        clean_props = {
            str(k): v
            for k, v in raw_props.items()
            if not str(k).startswith("_")
            and (str(k) not in prop_roles or reader_role in prop_roles[str(k)])
        }
        clean_node = {
            "id": str(n["id"]),
            "label": str(n["label"]),
            "name": str(n.get("name", n["id"])),
            "badge": str(n.get("badge", "POTENTIAL_EXPOSURE")),
            "provenance_class": str(n.get("provenance_class", "SYNTHETIC")),
            "properties": clean_props,
        }
        visible_nodes.append(clean_node)
        visible_ids.add(clean_node["id"])

    visible_edges: list[dict[str, Any]] = []
    for e in edges:
        if e.get("branch_id") != branch_id:
            continue
        if not _is_visible_at_cutoff(e, cutoff_dt):
            continue
        if reader_role not in e.get("allowed_roles", ()):
            continue
        src = str(e["source"])
        dst = str(e["target"])
        # Edge only visible if BOTH endpoints are authorized and visible (PO-08 non-interference)
        if src not in visible_ids or dst not in visible_ids:
            continue
        visible_edges.append(
            {
                "source": src,
                "target": dst,
                "type": str(e["type"]),
                "badge": str(e.get("badge", "POTENTIAL_EXPOSURE")),
                "provenance_class": str(e.get("provenance_class", "SYNTHETIC")),
            }
        )

    visible_cards: list[dict[str, Any]] = []
    for c in kpi_cards:
        if c.get("branch_id") != branch_id:
            continue
        if not _is_visible_at_cutoff(c, cutoff_dt):
            continue
        if reader_role not in c.get("allowed_roles", ()):
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
        "reader_cutoff_utc": cutoff_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
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
    """Evaluate directed exposure reachability inside a Relate WASM package (Cypher parity check)."""
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
