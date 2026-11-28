#!/usr/bin/env python3
"""Git Turtle + pyshacl -> Idempotent Neo4j Cypher MERGE Projection Loader (WP-3, ADR-0044, GRAPH-001).

Validates PPC's authoritative Git Turtle ontology against SHACL shapes using rdflib/pyshacl,
generates deterministic branch-scoped Cypher MERGE statements for Neo4j Community GraphSnapshot
projections, and emits an explicit RDF-to-LPG loss report documenting every omitted RDF construct
(blank nodes, rdfs:subClassOf axioms, language tags, etc.).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pyshacl import validate
from rdflib import BNode, Graph, Literal, RDF, RDFS, URIRef


def _local_name(uri: URIRef) -> str:
    s = str(uri)
    if "#" in s:
        return s.rsplit("#", 1)[1]
    return s.rstrip("/").rsplit("/", 1)[-1]


def validate_and_project_rdf_to_cypher(
    ttl_path: str | Path,
    *,
    branch_id: str,
    snapshot_id: str,
    shacl_path: str | Path | None = None,
) -> dict[str, Any]:
    """Validate Turtle ontology with pyshacl and generate idempotent Cypher MERGE + loss report."""
    g = Graph()
    g.parse(str(ttl_path), format="turtle")

    conforms = True
    shacl_report = "No SHACL shapes provided; RDF syntax validated."
    if shacl_path is not None:
        sp = Path(shacl_path)
        if not sp.is_file():
            raise FileNotFoundError(f"SHACL shapes file not found: {sp}")
        sg = Graph()
        sg.parse(str(sp), format="turtle")
        conforms, _res_graph, shacl_report = validate(g, shacl_graph=sg, inference="rdfs")
        if not conforms:
            raise ValueError(f"SHACL validation failed for {ttl_path}:\n{shacl_report}")

    cypher_statements: list[str] = []
    projected_nodes: dict[str, dict[str, Any]] = {}
    projected_edges: list[tuple[str, str, str]] = []
    loss_items: list[dict[str, str]] = []

    for s, p, o in sorted(g, key=lambda t: (str(t[0]), str(t[1]), str(t[2]))):
        if isinstance(s, BNode) or isinstance(o, BNode):
            loss_items.append({"kind": "BLANK_NODE_OMITTED", "triple": f"{s} {p} {o}"})
            continue
        if not isinstance(s, URIRef) or not isinstance(p, URIRef):
            continue
        sid = str(s)
        if p == RDF.type and isinstance(o, URIRef):
            label = _local_name(o)
            node = projected_nodes.setdefault(sid, {"uri": sid, "labels": set(), "props": {}})
            node["labels"].add(label)
        elif p == RDFS.subClassOf:
            loss_items.append({"kind": "RDFS_AXIOM_NOT_IN_LPG", "triple": f"{s} rdfs:subClassOf {o}"})
        elif isinstance(o, Literal):
            node = projected_nodes.setdefault(sid, {"uri": sid, "labels": set(), "props": {}})
            node["props"][_local_name(p)] = str(o)
            if o.language:
                loss_items.append({"kind": "LITERAL_LANGUAGE_TAG_FLATTENED", "triple": f"{s} {p} @{o.language}"})
        elif isinstance(o, URIRef):
            projected_nodes.setdefault(sid, {"uri": sid, "labels": set(), "props": {}})
            projected_nodes.setdefault(str(o), {"uri": str(o), "labels": set(), "props": {}})
            projected_edges.append((sid, _local_name(p).upper(), str(o)))

    # Emit branch-scoped idempotent GraphSnapshot header + MERGE statements
    cypher_statements.append(
        f"MERGE (snap:GraphSnapshot {{snapshot_id: {json.dumps(snapshot_id)}, branch_id: {json.dumps(branch_id)}}});"
    )
    for uri, info in sorted(projected_nodes.items()):
        lbls = ":".join(sorted(info["labels"]) or ["RDFResource"])
        props = dict(sorted(info["props"].items()))
        props["uri"] = uri
        props["branch_id"] = branch_id
        props["snapshot_id"] = snapshot_id
        cypher_statements.append(
            f"MERGE (n:{lbls} {{uri: {json.dumps(uri)}, branch_id: {json.dumps(branch_id)}}}) "
            f"SET n += {json.dumps(props, sort_keys=True)};"
        )
    for src, rel, dst in sorted(set(projected_edges)):
        cypher_statements.append(
            f"MATCH (a {{uri: {json.dumps(src)}, branch_id: {json.dumps(branch_id)}}}), "
            f"(b {{uri: {json.dumps(dst)}, branch_id: {json.dumps(branch_id)}}}) "
            f"MERGE (a)-[r:{rel} {{branch_id: {json.dumps(branch_id)}, snapshot_id: {json.dumps(snapshot_id)}}}]->(b);"
        )

    cypher_text = "\n".join(cypher_statements) + "\n"
    return {
        "conforms": conforms,
        "branch_id": branch_id,
        "snapshot_id": snapshot_id,
        "rdf_triple_count": len(g),
        "lpg_node_count": len(projected_nodes),
        "lpg_edge_count": len(set(projected_edges)),
        "loss_count": len(loss_items),
        "loss_report": loss_items,
        "cypher_sha256": hashlib.sha256(cypher_text.encode("utf-8")).hexdigest(),
        "cypher_statements": cypher_statements,
        "provenance_class": "DERIVED",
    }
