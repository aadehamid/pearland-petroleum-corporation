#!/usr/bin/env python3
"""Tests for WP-5B Relate WASM server-filtered graph package and PO-08 zero-byte redaction."""
from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_graph_pkg_mod():
    path = REPO_ROOT / "apps" / "relate-wasm" / "graph_package.py"
    spec = importlib.util.spec_from_file_location("ppc_relate_wasm_graph_pkg", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


class TestWP5BRelateWasmExplorer(unittest.TestCase):
    def test_server_side_redaction_leaves_zero_restricted_or_post_cutoff_bytes_in_package(self):
        mod = _load_graph_pkg_mod()
        nodes = [
            {
                "id": "4B",
                "label": "ProcessUnit",
                "name": "Hydrocracker",
                "branch_id": "baseline",
                "published_at_utc": "2026-06-15T08:16:00Z",
                "allowed_roles": ("Planner", "Executive"),
                "badge": "POTENTIAL_EXPOSURE",
            },
            {
                "id": "TK-301",
                "label": "Tank",
                "name": "ULSD Tank 1",
                "branch_id": "baseline",
                "published_at_utc": "2026-06-15T08:16:00Z",
                "allowed_roles": ("Planner", "Executive"),
                "badge": "POTENTIAL_EXPOSURE",
            },
            {
                "id": "EXEC-SECRET-CONTRACT",
                "label": "Contract",
                "name": "SECRET_COUNTERPARTY_XYZ_999",
                "branch_id": "baseline",
                "published_at_utc": "2026-06-15T08:16:00Z",
                "allowed_roles": ("Executive",),
                "badge": "POTENTIAL_EXPOSURE",
            },
            {
                "id": "FUTURE-NODE",
                "label": "Assay",
                "name": "FUTURE_CORRECTION_1300Z",
                "branch_id": "baseline",
                "published_at_utc": "2026-06-15T13:00:00Z",
                "allowed_roles": ("Planner", "Executive"),
                "badge": "POTENTIAL_EXPOSURE",
            },
        ]
        edges = [
            {
                "source": "4B",
                "target": "TK-301",
                "type": "FEEDS",
                "branch_id": "baseline",
                "published_at_utc": "2026-06-15T08:16:00Z",
                "allowed_roles": ("Planner", "Executive"),
            },
            {
                "source": "TK-301",
                "target": "EXEC-SECRET-CONTRACT",
                "type": "SUPPLIES",
                "branch_id": "baseline",
                "published_at_utc": "2026-06-15T08:16:00Z",
                "allowed_roles": ("Planner", "Executive"),
            },
        ]
        cards = [
            {
                "card_id": "CARD-1",
                "model_run_id": "LP-001",
                "kpi_name": "ULSD Netback CPG",
                "value": 214.5,
                "unit": "cents/gal",
                "branch_id": "baseline",
                "published_at_utc": "2026-06-15T08:30:00Z",
                "allowed_roles": ("Planner", "Executive"),
            }
        ]

        pkg = mod.build_filtered_graph_package(
            branch_id="baseline",
            reader_role="Planner",
            reader_cutoff_utc="2026-06-15T10:00:00Z",
            nodes=nodes,
            edges=edges,
            kpi_cards=cards,
        )
        raw_bytes = json.dumps(pkg)
        # Zero unauthorized or post-cutoff bytes may appear anywhere in serialized browser package
        self.assertNotIn("SECRET_COUNTERPARTY_XYZ_999", raw_bytes)
        self.assertNotIn("EXEC-SECRET-CONTRACT", raw_bytes)
        self.assertNotIn("FUTURE_CORRECTION_1300Z", raw_bytes)
        self.assertEqual([n["id"] for n in pkg["nodes"]], ["4B", "TK-301"])
        self.assertEqual(len(pkg["edges"]), 1)
        self.assertEqual(pkg["model_quantified_cards"][0]["badge"], "MODEL_QUANTIFIED")
        self.assertEqual(mod.reachable_exposure_ids(pkg, "4B"), ["TK-301"])


if __name__ == "__main__":
    unittest.main()
