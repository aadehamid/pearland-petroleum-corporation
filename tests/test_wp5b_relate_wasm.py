#!/usr/bin/env python3
"""Tests for WP-5B Relate WASM server-side filtered graph package serialization."""
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
    def test_server_side_redaction_rbac_string_denial_name_redaction_and_subsecond_replay(self):
        mod = _load_graph_pkg_mod()
        nodes = [
            {
                "id": "4B",
                "label": "ProcessUnit",
                "name": "SECRET_COUNTERPARTY_NAME_ZZZ",
                "branch_id": "baseline",
                "published_at_utc": "2026-06-15T10:00:00.050000Z",
                "allowed_roles": ("Planner", "Executive"),
                "badge": "POTENTIAL_EXPOSURE",
                "properties": {"margin_secret": "TOP_SECRET_MARGIN_888", "unit_code": "4B", "_internal": "HIDE_ME"},
                "property_allowed_roles": {"margin_secret": ("Executive",), "name": ("Executive",)},
            },
            {
                "id": "TK-301",
                "label": "Tank",
                "name": "ULSD Tank 1",
                "branch_id": "baseline",
                "published_at_utc": "2026-06-15T05:00:00.100000-05:00",  # exactly == 10:00:00.100000Z (inclusive)
                "allowed_roles": ("Planner", "Executive"),
                "badge": "POTENTIAL_EXPOSURE",
            },
            {
                "id": "STR-ROLE-LEAK",
                "label": "Contract",
                "name": "STRING_ROLE_SUBSTRING_LEAK",
                "branch_id": "baseline",
                "published_at_utc": "2026-06-15T08:16:00Z",
                "allowed_roles": "Commercial Manager",  # bare string MUST fail closed even for "Commercial"
            },
            {
                "id": "UNPUBLISHED-NODE",
                "label": "Tank",
                "name": "NEVER_PUBLISHED_SECRET",
                "branch_id": "baseline",
                "published_at_utc": "",
                "allowed_roles": ("Planner", "Executive"),
            },
            {
                "id": "RETRACTED-NODE",
                "label": "Assay",
                "name": "RETRACTED_AT_0930",
                "branch_id": "baseline",
                "published_at_utc": "2026-06-15T08:16:00Z",
                "retracted_at_utc": "2026-06-15T09:30:00Z",
                "allowed_roles": ("Planner", "Executive"),
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
                "source": "4B",
                "target": "TK-301",
                "type": "EXEC_ONLY_EDGE",
                "branch_id": "baseline",
                "published_at_utc": "2026-06-15T08:16:00Z",
                "allowed_roles": ("Executive",),
            },
            {
                "source": "4B",
                "target": "TK-301",
                "type": "RETRACTED_EDGE",
                "branch_id": "baseline",
                "published_at_utc": "2026-06-15T08:16:00Z",
                "retracted_at_utc": "2026-06-15T09:00:00Z",
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
            },
            {
                "card_id": "CARD-RETRACTED",
                "model_run_id": "LP-000",
                "kpi_name": "RETRACTED_KPI_999",
                "value": 99.0,
                "unit": "cents/gal",
                "branch_id": "baseline",
                "published_at_utc": "2026-06-15T08:00:00Z",
                "retracted_at_utc": "2026-06-15T09:00:00Z",
                "allowed_roles": ("Planner", "Executive"),
            },
        ]

        cutoff = "2026-06-15T10:00:00.100000Z"
        pkg = mod.build_filtered_graph_package(
            branch_id="baseline",
            reader_role="Planner",
            reader_cutoff_utc=cutoff,
            nodes=nodes,
            edges=edges,
            kpi_cards=cards,
        )
        raw_bytes = json.dumps(pkg)
        for forbidden in (
            "SECRET_COUNTERPARTY_XYZ_999",
            "SECRET_COUNTERPARTY_NAME_ZZZ",
            "EXEC-SECRET-CONTRACT",
            "EXEC_ONLY_EDGE",
            "RETRACTED_EDGE",
            "RETRACTED_KPI_999",
            "FUTURE_CORRECTION_1300Z",
            "NEVER_PUBLISHED_SECRET",
            "RETRACTED_AT_0930",
            "TOP_SECRET_MARGIN_888",
            "HIDE_ME",
            "STRING_ROLE_SUBSTRING_LEAK",
        ):
            self.assertNotIn(forbidden, raw_bytes)

        self.assertEqual([n["id"] for n in pkg["nodes"]], ["4B", "TK-301"])
        self.assertEqual(pkg["nodes"][0]["name"], "4B")
        self.assertEqual(pkg["nodes"][0]["properties"], {"unit_code": "4B"})
        self.assertEqual([(e["source"], e["type"], e["target"]) for e in pkg["edges"]], [("4B", "FEEDS", "TK-301")])
        self.assertEqual([c["card_id"] for c in pkg["model_quantified_cards"]], ["CARD-1"])
        self.assertEqual(pkg["model_quantified_cards"][0]["badge"], "MODEL_QUANTIFIED")
        self.assertEqual(mod.reachable_exposure_ids(pkg, "4B"), ["TK-301"])
        self.assertEqual(mod.reachable_exposure_ids(pkg, "EXEC-SECRET-CONTRACT"), [])

        # Sub-second cutoff preserved verbatim -> replay using pkg["reader_cutoff_utc"] gives identical SHA-256!
        self.assertEqual(pkg["reader_cutoff_utc"], cutoff)
        pkg_replay = mod.build_filtered_graph_package(
            branch_id="baseline",
            reader_role="Planner",
            reader_cutoff_utc=pkg["reader_cutoff_utc"],
            nodes=nodes,
            edges=edges,
            kpi_cards=cards,
        )
        self.assertEqual(pkg_replay["package_sha256"], pkg["package_sha256"])

        # Bare string allowed_roles ("Commercial Manager") MUST fail closed for reader "Commercial"!
        pkg_comm = mod.build_filtered_graph_package(
            branch_id="baseline",
            reader_role="Commercial",
            reader_cutoff_utc=cutoff,
            nodes=nodes,
            edges=edges,
        )
        self.assertEqual(pkg_comm["nodes"], [])

        # Malformed property_allowed_roles container (non-Mapping) AND dict-shaped allowed_roles MUST fail closed!
        malformed_nodes = [
            {
                "id": "MALFORMED-PROP-ROLES",
                "label": "Contract",
                "name": "SECRET_NAME_MUST_REDACT",
                "branch_id": "baseline",
                "published_at_utc": "2026-06-15T08:00:00Z",
                "allowed_roles": ("Planner",),
                "properties": {"margin_secret": "TOP_SECRET_MALFORMED"},
                "property_allowed_roles": "Executive",  # non-Mapping container -> drop all properties & redact name
            },
            {
                "id": "DICT-ROLE-DENY",
                "label": "Contract",
                "name": "DICT_DENY_SECRET",
                "branch_id": "baseline",
                "published_at_utc": "2026-06-15T08:00:00Z",
                "allowed_roles": {"Planner": False},  # Mapping role collection -> MUST fail closed!
            },
        ]
        pkg_mal = mod.build_filtered_graph_package(
            branch_id="baseline",
            reader_role="Planner",
            reader_cutoff_utc=cutoff,
            nodes=malformed_nodes,
            edges=[],
        )
        raw_mal = json.dumps(pkg_mal)
        self.assertNotIn("TOP_SECRET_MALFORMED", raw_mal)
        self.assertNotIn("SECRET_NAME_MUST_REDACT", raw_mal)
        self.assertNotIn("DICT_DENY_SECRET", raw_mal)
        self.assertEqual([n["id"] for n in pkg_mal["nodes"]], ["MALFORMED-PROP-ROLES"])
        self.assertEqual(pkg_mal["nodes"][0]["properties"], {})
        self.assertEqual(pkg_mal["nodes"][0]["name"], "MALFORMED-PROP-ROLES")

        # Cutoff BEFORE retraction (08:45Z) sees RETRACTED-NODE, RETRACTED_EDGE, and CARD-RETRACTED
        pkg_early = mod.build_filtered_graph_package(
            branch_id="baseline",
            reader_role="Planner",
            reader_cutoff_utc="2026-06-15T08:45:00Z",
            nodes=nodes,
            edges=edges,
            kpi_cards=cards,
        )
        self.assertIn("RETRACTED-NODE", [n["id"] for n in pkg_early["nodes"]])
        self.assertIn("CARD-RETRACTED", [c["card_id"] for c in pkg_early["model_quantified_cards"]])

        # Naive cutoff, NaN, and Inf KPI cards MUST raise ValueError
        with self.assertRaises(ValueError):
            mod.build_filtered_graph_package(
                branch_id="baseline",
                reader_role="Planner",
                reader_cutoff_utc="2026-06-15T10:00:00",
                nodes=[],
                edges=[],
            )
        for bad_val in (float("nan"), float("inf"), float("-inf")):
            with self.assertRaises(ValueError):
                mod.build_filtered_graph_package(
                    branch_id="baseline",
                    reader_role="Planner",
                    reader_cutoff_utc=cutoff,
                    nodes=[],
                    edges=[],
                    kpi_cards=[{**cards[0], "value": bad_val}],
                )


if __name__ == "__main__":
    unittest.main()
