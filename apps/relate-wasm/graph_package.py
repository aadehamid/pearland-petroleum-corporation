#!/usr/bin/env python3
"""WP-5B Server-Side Permission-Filtered Relate WASM Graph Package Serializer (ADR-0052, PO-08).

Builds authorized browser-side graph packages for the Relate WASM Interactive
Enterprise Context Explorer strictly BEFORE serialization so zero unauthorized
nodes, edges, or property bytes ever enter the browser payload. Enforces:
- Role-based filtering on every node and edge before serialization
- Temporal publication cutoff filtering (published_at_utc <= reader_cutoff_utc)
- Explicit badge separation: POTENTIAL_EXPOSURE (graph path) vs MODEL_QUANTIFIED (LP/KPI)
- Deterministic Cypher parity verification subset against Neo4j Community
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence


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
    visible_nodes: list[dict[str, Any]] = []
    visible_ids: set[str] = set()
    for n in nodes:
        if n.get("branch_id") != branch_id:
            continue
        if str(n.get("published_at_utc", "")) > reader_cutoff_utc:
            continue
        if reader_role not in n.get("allowed_roles", ()):
            continue
        clean_node = {
            "id": str(n["id"]),
            "label": str(n["label"]),
            "name": str(n.get("name", n["id"])),
            "badge": str(n.get("badge", "POTENTIAL_EXPOSURE")),
            "provenance_class": str(n.get("provenance_class", "SYNTHETIC")),
            "properties": dict(n.get("properties", {})),
        }
        visible_nodes.append(clean_node)
        visible_ids.add(clean_node["id"])

    visible_edges: list[dict[str, Any]] = []
    for e in edges:
        if e.get("branch_id") != branch_id:
            continue
        if str(e.get("published_at_utc", "")) > reader_cutoff_utc:
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

    visible_cards = [
        {
            "card_id": str(c["card_id"]),
            "badge": "MODEL_QUANTIFIED",
            "model_run_id": str(c["model_run_id"]),
            "kpi_name": str(c["kpi_name"]),
            "value": float(c["value"]),
            "unit": str(c["unit"]),
            "provenance_class": str(c.get("provenance_class", "DERIVED")),
        }
        for c in kpi_cards
        if c.get("branch_id") == branch_id
        and str(c.get("published_at_utc", "")) <= reader_cutoff_utc
        and reader_role in c.get("allowed_roles", ())
    ]

    visible_nodes.sort(key=lambda x: x["id"])
    visible_edges.sort(key=lambda x: (x["source"], x["type"], x["target"]))
    visible_cards.sort(key=lambda x: x["card_id"])

    pkg = {
        "schema_version": "1.0.0",
        "explorer_runtime": "relate-wasm",
        "branch_id": branch_id,
        "reader_role": reader_role,
        "reader_cutoff_utc": reader_cutoff_utc,
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
    adj: dict[str, list[str]] = {}
    for e in pkg.get("edges", []):
        adj.setdefault(str(e["source"]), []).append(str(e["target"]))
    visited: set[str] = set()
    stack = [start_node_id]
    while stack:
        curr = stack.pop()
        for nxt in adj.get(curr, []):
            if nxt not in visited:
                visited.add(nxt)
                stack.append(nxt)
    return sorted(visited)
