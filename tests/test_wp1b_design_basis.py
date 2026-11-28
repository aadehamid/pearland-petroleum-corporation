#!/usr/bin/env python3
"""Independent verification tests for WP-1b design basis, CFG-0 DEXPI topology, and OT tags."""
from __future__ import annotations

import json
import math
import unittest
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DESIGN_BASIS_PATH = REPO_ROOT / "fixtures" / "golden" / "refinery_a_design_basis.yaml"
CFG0_PATH = REPO_ROOT / "fixtures" / "golden" / "cfg0_dexpi_topology.json"
OT_TAGS_PATH = REPO_ROOT / "fixtures" / "golden" / "refinery_a_ot_tags.yaml"

C_BBL_M3 = 0.158987294928
RHO_W_60F = 999.016
G_ACCEL = 9.80665


def churchill_friction_factor(re_num: float, rel_rough: float) -> float:
    """Churchill (1977) smooth all-regime Darcy friction factor."""
    a = (2.457 * math.log(1.0 / ((7.0 / re_num) ** 0.9 + 0.27 * rel_rough))) ** 16
    b = (37530.0 / re_num) ** 16
    return 8.0 * ((8.0 / re_num) ** 12 + 1.0 / ((a + b) ** 1.5)) ** (1.0 / 12.0)


class TestWP1bDesignBasis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = yaml.safe_load(DESIGN_BASIS_PATH.read_text(encoding="utf-8"))
        cls.cfg0 = json.loads(CFG0_PATH.read_text(encoding="utf-8"))
        cls.ot = yaml.safe_load(OT_TAGS_PATH.read_text(encoding="utf-8"))

    def test_three_assays_hit_adr0054_and_adr0056_targets(self):
        assays = self.db["crude_assays"]
        self.assertEqual(len(assays), 3)
        blend_w = self.db["crude_slate"]["design_blend_vol_frac"]
        blend_cuts = [0.0] * 7

        for a in assays:
            self.assertGreaterEqual(len(a["tbp_points_vol_pct_c"]), 12)
            # Monotonic TBP curve
            pts = a["tbp_points_vol_pct_c"]
            for i in range(len(pts) - 1):
                self.assertLess(pts[i][0], pts[i + 1][0])
                self.assertLess(pts[i][1], pts[i + 1][1])

            cuts = a["cuts"]
            self.assertEqual(len(cuts), 7)
            self.assertAlmostEqual(sum(c["vol_pct"] for c in cuts), 100.0, places=6)

            # Volume-weighted whole-crude SG -> API
            whole_sg = sum((c["vol_pct"] / 100.0) * c["sg_60_60"] for c in cuts)
            whole_api = 141.5 / whole_sg - 131.5
            self.assertAlmostEqual(whole_api, a["target_api_gravity"], delta=0.05)

            # Mass-weighted whole-crude sulfur
            masses = [(c["vol_pct"] / 100.0) * c["sg_60_60"] for c in cuts]
            tot_m = sum(masses)
            whole_s = sum((m / tot_m) * c["sulfur_wt_pct"] for m, c in zip(masses, cuts))
            self.assertAlmostEqual(whole_s, a["target_sulfur_wt_pct"], delta=0.01)

            w = blend_w[a["id"]]
            for i, c in enumerate(cuts):
                blend_cuts[i] += w * c["vol_pct"]

        expected_blend = [2.0, 6.0, 12.0, 10.0, 17.0, 32.0, 21.0]
        for got, exp in zip(blend_cuts, expected_blend):
            self.assertAlmostEqual(got, exp, delta=0.1)

    def test_eq03_hydraulic_transfer_lines_have_positive_pump_margin(self):
        pumps_by_line = {}
        for p in self.db["pumps"]:
            pumps_by_line.setdefault(p["line_id"], []).append(p)

        self.assertEqual(len(self.db["transfer_lines"]), 6)
        for ln in self.db["transfer_lines"]:
            q_m3_s = ln["nominal_flow_bbl_per_day"] * C_BBL_M3 / 86400.0
            d = ln["diameter_m"]
            area = math.pi * d * d / 4.0
            v = q_m3_s / area
            rho = ln["fluid_sg"] * RHO_W_60F
            re_num = rho * v * d / ln["fluid_viscosity_pa_s"]
            f = churchill_friction_factor(re_num, ln["roughness_m"] / d)
            hf = (f * (ln["length_m"] / d) + ln["k_fittings"]) * (v * v) / (2.0 * G_ACCEL)
            h_req = ln["delta_z_m"] + ln["delta_p_pa"] / (rho * G_ACCEL) + hf

            primary = [p for p in pumps_by_line[ln["id"]] if p["role"] == "primary"][0]
            # Conservative ANSI/HI 9.6.7 viscous derating check for viscous services
            c_h = 0.85 if primary["viscous_service"] else 1.0
            h_avail = c_h * (primary["h0_m"] - primary["cp_s2_per_m5"] * (q_m3_s ** 2))
            self.assertGreater(
                h_avail, h_req,
                f"Line {ln['id']} pump {primary['id']} head {h_avail:.2f}m <= required {h_req:.2f}m (Re={re_num:.0f})",
            )

    def test_cfg0_and_ot_tags_align_with_design_basis(self):
        self.assertEqual(self.cfg0["configuration_id"], "CFG-0")
        self.assertEqual(self.cfg0["provenance_class"], "SYNTHETIC")
        cfg0_tags = {e["tag"] for e in self.cfg0["equipment"]}
        for t in self.db["tanks"]:
            self.assertIn(t["id"], cfg0_tags)
        for p in self.db["pumps"]:
            self.assertIn(p["id"], cfg0_tags)
        for u in self.db["units"]:
            self.assertIn(u["id"], cfg0_tags)

        # Every OT tag references a valid equipment entity
        valid_eq = {u["id"] for u in self.db["units"]} | {t["id"] for t in self.db["tanks"]}
        self.assertGreaterEqual(len(self.ot["tags"]), 20)
        for tag in self.ot["tags"]:
            self.assertIn(tag["equipment_id"], valid_eq)
            self.assertEqual(tag["provenance_class"], "SYNTHETIC")
        # 1-second compressor telemetry present per ADR-0043 / PPC-OT-001
        one_sec = [t for t in self.ot["tags"] if t["sample_seconds"] == 1]
        self.assertGreaterEqual(len(one_sec), 3)


if __name__ == "__main__":
    unittest.main()
