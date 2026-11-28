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

# Locked ADR-0054 / ADR-0056 / PPC-REVIEW-002 baseline constants
ADR_LOCKED_ASSAYS = {
    "ASSAY-LIGHT-SWEET": (39.0, 0.35),
    "ASSAY-MEDIUM-SOUR": (31.0, 1.60),
    "ASSAY-HEAVY-SOUR": (24.0, 2.60),
}
ADR_LOCKED_BLEND = {
    "ASSAY-LIGHT-SWEET": 0.30,
    "ASSAY-MEDIUM-SOUR": 0.50,
    "ASSAY-HEAVY-SOUR": 0.20,
}
ADR_LOCKED_CUT_POINTS_C = [30.0, 85.0, 175.0, 240.0, 360.0, 565.0]
ADR_LOCKED_UNIT_CAPACITIES = {
    "CDU": 190000.0,
    "4A": 30000.0,
    "4B": 40000.0,
    "5A": 60000.0,
    "5B": 18000.0,
    "5C": 30000.0,
    "5D": 36000.0,
}


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

    def test_three_assays_and_units_pin_adr0054_and_adr0056_constants(self):
        # Pin crude slate capacities, blend weights, and TBP cut points against ADR-0054 / ADR-0056
        slate = self.db["crude_slate"]
        self.assertEqual(slate["nominal_charge_bbl_per_day"], 180000.0)
        self.assertEqual(slate["min_charge_bbl_per_day"], 105000.0)
        self.assertEqual(slate["max_charge_bbl_per_day"], 190000.0)
        self.assertEqual(slate["design_blend_vol_frac"], ADR_LOCKED_BLEND)
        self.assertEqual(slate["tbp_cut_points_c"], ADR_LOCKED_CUT_POINTS_C)

        # Pin unit capacities and ADR-0054 G1-4 interface constants
        units_by_id = {u["id"]: u for u in self.db["units"]}
        for uid, expected_cap in ADR_LOCKED_UNIT_CAPACITIES.items():
            self.assertEqual(units_by_id[uid]["capacity_bbl_per_day"], expected_cap)
        self.assertEqual(units_by_id["6"]["smr_max_h2_t_per_day"], 120.0)
        self.assertEqual(units_by_id["6"]["smr_min_turndown_frac"], 0.45)
        self.assertEqual(units_by_id["6"]["smr_gas_per_h2_kg_per_kg"], 3.50)
        self.assertEqual(units_by_id["9"]["sru_capacity_t_per_day"], 250.0)
        self.assertEqual(units_by_id["9"]["sru_recovery_frac"], 0.995)
        self.assertEqual(units_by_id["5A"]["max_lco_wt_frac"], 0.20)
        self.assertEqual(units_by_id["5B"]["octane_loss_aki"], 1.0)
        self.assertEqual(units_by_id["5D"]["max_sulfur_ppmw"], 0.5)

        assays = self.db["crude_assays"]
        self.assertEqual(len(assays), 3)
        blend_w = slate["design_blend_vol_frac"]
        blend_cuts = [0.0] * 7
        blend_sg = 0.0

        for a in assays:
            exp_api, exp_s = ADR_LOCKED_ASSAYS[a["id"]]
            self.assertEqual(a["target_api_gravity"], exp_api)
            self.assertEqual(a["target_sulfur_wt_pct"], exp_s)
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
            self.assertAlmostEqual(whole_api, exp_api, delta=0.05)

            # Mass-weighted whole-crude sulfur
            masses = [(c["vol_pct"] / 100.0) * c["sg_60_60"] for c in cuts]
            tot_m = sum(masses)
            whole_s = sum((m / tot_m) * c["sulfur_wt_pct"] for m, c in zip(masses, cuts))
            self.assertAlmostEqual(whole_s, exp_s, delta=0.01)

            w = blend_w[a["id"]]
            blend_sg += w * whole_sg
            for i, c in enumerate(cuts):
                blend_cuts[i] += w * c["vol_pct"]

        expected_blend = [2.0, 6.0, 12.0, 10.0, 17.0, 32.0, 21.0]
        for got, exp in zip(blend_cuts, expected_blend):
            self.assertAlmostEqual(got, exp, delta=0.1)

        # Verify crude charge tank TK-102 matches the 30/50/20 whole-design-blend SG
        tanks_by_id = {t["id"]: t for t in self.db["tanks"]}
        self.assertAlmostEqual(tanks_by_id["TK-102"]["ref_sg_60_60"], blend_sg, delta=0.002)

    def test_eq03_hydraulic_transfer_lines_have_positive_pump_margin(self):
        pumps_by_line = {}
        for p in self.db["pumps"]:
            pumps_by_line.setdefault(p["line_id"], []).append(p)
        tanks_by_id = {t["id"]: t for t in self.db["tanks"]}

        self.assertEqual(len(self.db["transfer_lines"]), 6)
        for ln in self.db["transfer_lines"]:
            # Every transfer line's fluid SG must match its source tank's declared ref_sg_60_60
            self.assertAlmostEqual(
                ln["fluid_sg"],
                tanks_by_id[ln["source"]]["ref_sg_60_60"],
                places=6,
                msg=f"Transfer line {ln['id']} fluid_sg contradicts source tank {ln['source']}",
            )
            flows_to_check = [ln["nominal_flow_bbl_per_day"]]
            if ln["id"] == "LINE-CRUDE-CHG":
                flows_to_check.append(self.db["crude_slate"]["min_charge_bbl_per_day"])
            for flow_bpd in flows_to_check:
                q_m3_s = flow_bpd * C_BBL_M3 / 86400.0
                d = ln["diameter_m"]
                area = math.pi * d * d / 4.0
                v = q_m3_s / area
                rho = ln["fluid_sg"] * RHO_W_60F
                re_num = rho * v * d / ln["fluid_viscosity_pa_s"]
                f = churchill_friction_factor(re_num, ln["roughness_m"] / d)
                hf = (f * (ln["length_m"] / d) + ln["k_fittings"]) * (v * v) / (2.0 * G_ACCEL)
                h_req = ln["delta_z_m"] + ln["delta_p_pa"] / (rho * G_ACCEL) + hf

                # Verify both primary and standby pumps satisfy positive head margin
                for pump in pumps_by_line[ln["id"]]:
                    # Conservative flat 0.85 viscous head derating multiplier (simplified check;
                    # full ANSI/HI 9.6.7 water-to-viscous Q/H/eta curves apply in detailed sizing)
                    c_h = 0.85 if pump["viscous_service"] else 1.0
                    h_avail = c_h * (pump["h0_m"] - pump["cp_s2_per_m5"] * (q_m3_s ** 2))
                    self.assertGreater(
                        h_avail, h_req,
                        f"Line {ln['id']} pump {pump['id']} head {h_avail:.2f}m <= required {h_req:.2f}m (Re={re_num:.0f})",
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
        for term in self.db["terminals"]:
            self.assertIn(term["id"], cfg0_tags)

        # Every CFG-0 piping connection endpoint and pump must resolve to a declared CFG-0 equipment item
        for conn in self.cfg0["piping_connections"]:
            self.assertIn(conn["from"], cfg0_tags, f"CFG-0 dangling 'from' endpoint {conn['from']}")
            self.assertIn(conn["to"], cfg0_tags, f"CFG-0 dangling 'to' endpoint {conn['to']}")
            for pid in conn["pumps"]:
                self.assertIn(pid, cfg0_tags, f"CFG-0 dangling pump {pid}")

        # Every OT tag references a valid installed equipment entity in CFG-0 (including K-201)
        self.assertGreaterEqual(len(self.ot["tags"]), 20)
        for tag in self.ot["tags"]:
            self.assertIn(tag["equipment_id"], cfg0_tags)
            self.assertEqual(tag["provenance_class"], "SYNTHETIC")
        # 1-second compressor telemetry must attribute to installed compressor K-201 (not parent unit 4B)
        one_sec = [t for t in self.ot["tags"] if t["sample_seconds"] == 1]
        self.assertGreaterEqual(len(one_sec), 3)
        for tag in one_sec:
            self.assertEqual(tag["equipment_id"], "K-201")
            self.assertEqual(tag.get("parent_unit"), "4B")

    def test_commercial_rfg_rvp_and_premium_cap_comply_with_adr0056(self):
        # Houston RFG terminals (TERM-01, TERM-03) must keep E10 RVP <= 7.4 psi (40 CFR 1090.215)
        for term in self.db["terminals"]:
            if term["id"] in ("TERM-01", "TERM-03"):
                self.assertLessEqual(term["rfg_summer_bob_rvp_max_psi"] + term["ethanol_rvp_bump_psi"], 7.4 + 1e-9)
        # Premium gasoline share must be <= 10% of total gasoline pool (ADR-0056 G3-c)
        gas_custs = [c for c in self.db["customers"] if c["product"].startswith("E10_")]
        prem_bpd = sum(c["contract_bbl_per_day"] for c in gas_custs if c["product"] == "E10_PREM")
        tot_gas_bpd = sum(c["contract_bbl_per_day"] for c in gas_custs)
        self.assertLessEqual(prem_bpd / tot_gas_bpd, 0.10)


if __name__ == "__main__":
    unittest.main()
