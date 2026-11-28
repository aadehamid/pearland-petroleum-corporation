#!/usr/bin/env python3
"""Independent verification tests for WP-1c Refinery A v1 World Kernel (EQ-01 through EQ-08).

Verifies every Python-checked hand fixture in PPC-REVIEW-002 §3, PPC-ENG-001 §4,
PPC-WORLD-001 §5, and WORLD-002 §6, plus step-refinement convergence (60s/10s/1s),
23/25-hour America/Chicago DST parity, checkpoint bit-exact replay, and child-branch isolation.
"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

import yaml

from generators import equations as eq
from generators.world_kernel import (
    RefineryWorldKernel,
    TankState,
    WorldEvent,
    WorldState,
    evaluate_refinery_plant_snapshot,
    local_business_day_elapsed_hours,
    paired_rng,
    run_eng_v07_mode_benchmark,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
DESIGN_BASIS_PATH = REPO_ROOT / "fixtures" / "golden" / "refinery_a_design_basis.yaml"


class TestEquationsExactFixtures(unittest.TestCase):
    def test_eq01_and_eq02_t125_baseline_and_intermediate_overflow_split(self):
        # Exact rational check: SG=0.840 -> rho=839.173440 kg/m3, 133.417915 kg/bbl
        sg = 0.840
        kg_per_bbl = eq.volume_bbl_to_mass_kg(1.0, sg)
        self.assertAlmostEqual(kg_per_bbl, 133.417915, places=6)

        # Missing density returns INSUFFICIENT_INPUT
        with self.assertRaises(eq.InsufficientInputError):
            eq.volume_bbl_to_mass_kg(100.0, None)

        # Baseline T125: 10,000 bbl + 500 bbl/h in - 700 bbl/h out for 2 h = 9,600 bbl
        res = eq.step_tank_with_exact_crossing(
            opening_mass_kg=eq.volume_bbl_to_mass_kg(10000.0, sg),
            min_mass_kg=eq.volume_bbl_to_mass_kg(1000.0, sg),
            max_mass_kg=eq.volume_bbl_to_mass_kg(12000.0, sg),
            inflow_rate_kg_s=eq.volume_bbl_to_mass_kg(500.0, sg) / 3600.0,
            outflow_rate_kg_s=eq.volume_bbl_to_mass_kg(700.0, sg) / 3600.0,
            dt_s=7200.0,
        )
        self.assertFalse(res.crossing_occurred)
        self.assertAlmostEqual(eq.mass_kg_to_volume_bbl(res.closing_mass_kg, sg), 9600.0, places=9)
        self.assertAlmostEqual(res.closing_mass_kg, 1280811.99, places=2)
        self.assertAlmostEqual(res.mass_residual_kg, 0.0, places=12)

        # Intermediate overflow fixture: 11,800 bbl, cap 12,000, hour 1 net +400 bbl/h (600 in / 200 out)
        # MUST split at exact t* = 0.5 h = 1800 s instead of hiding 12,200 bbl overflow!
        res_ovf = eq.step_tank_with_exact_crossing(
            opening_mass_kg=eq.volume_bbl_to_mass_kg(11800.0, sg),
            min_mass_kg=eq.volume_bbl_to_mass_kg(1000.0, sg),
            max_mass_kg=eq.volume_bbl_to_mass_kg(12000.0, sg),
            inflow_rate_kg_s=eq.volume_bbl_to_mass_kg(600.0, sg) / 3600.0,
            outflow_rate_kg_s=eq.volume_bbl_to_mass_kg(200.0, sg) / 3600.0,
            dt_s=3600.0,
            rule="divert",
        )
        self.assertTrue(res_ovf.crossing_occurred)
        self.assertEqual(res_ovf.crossing_bound, "MAX")
        self.assertAlmostEqual(res_ovf.crossing_time_s, 1800.0, places=9)
        self.assertAlmostEqual(eq.mass_kg_to_volume_bbl(res_ovf.closing_mass_kg, sg), 12000.0, places=9)
        self.assertAlmostEqual(eq.mass_kg_to_volume_bbl(res_ovf.diverted_or_blocked_kg, sg), 200.0, places=9)
        self.assertAlmostEqual(res_ovf.mass_residual_kg, 0.0, places=12)

        # Exact rational zero-residual check
        exact_m = eq.volume_bbl_to_mass_kg_exact(Fraction(9600), Fraction("0.840"))
        self.assertEqual(
            exact_m,
            Fraction(9600) * Fraction("0.158987294928") * Fraction("0.840") * Fraction("999.016"),
        )
        self.assertAlmostEqual(float(exact_m), 1280811.99, places=2)

    def test_eq03_friction_all_regimes_continuous(self):
        # Laminar (Re=1500), transition (Re=3000 Churchill), turbulent (Re=50000 Colebrook-White)
        f_lam = eq.darcy_friction_factor(1500.0, 0.0001)
        self.assertAlmostEqual(f_lam, 64.0 / 1500.0, places=12)
        f_trans = eq.darcy_friction_factor(3000.0, 0.0001)
        self.assertTrue(0.03 < f_trans < 0.05)
        f_turb = eq.darcy_friction_factor(50000.0, 0.0001)
        self.assertTrue(0.018 < f_turb < 0.025)

    def test_eq05_and_eq07_scn_a_t125_and_h2cont_exact_fixtures(self):
        # Unit cancellation check: R_min_mass = 0.0666845554 kg H2 / kg VGO feed
        r_m = eq.hcu_r_min_mass(4000.0, 0.910)
        self.assertAlmostEqual(r_m, 0.0666845554, places=9)

        # Normal SCN-A-T125 H2 header: 107 + 73 - 5 - 5 = 170 t/day; headroom = 170 - 5 - 40 = 125 t/day
        h2_norm = eq.h2_header_balance(107.0, 73.0, 5.0, 5.0, 5.0, 40.0)
        self.assertAlmostEqual(h2_norm["net_plant_h2_supply_t_per_day"], 170.0, places=9)
        self.assertAlmostEqual(h2_norm["hcu_headroom_t_per_day"], 125.0, places=9)
        self.assertTrue(h2_norm["no_double_allocation"])

        # 75% compressor derate: binding cap = 30,000 bbl/day = 4,336.08 t/day
        res = eq.hcu_evaluate(
            requested_feed_bbl_per_day=30000.0,
            compressor_circ_fraction=0.75,
            h2_allocable_t_per_day=h2_norm["hcu_headroom_t_per_day"],
            fixture_mode=True,
        )
        self.assertTrue(res["feasible"])
        self.assertEqual(res["binding_constraint"], "compressor_circulation_cap")
        self.assertAlmostEqual(res["max_feed_bbl_per_day"], 30000.0, places=6)
        self.assertAlmostEqual(res["max_feed_t_per_day"], 4336.08, places=2)
        self.assertAlmostEqual(res["h2_chem_t_per_day"], 86.72, places=2)
        self.assertAlmostEqual(res["total_input_mass_t_per_day"], 4422.80, places=2)
        self.assertAlmostEqual(res["mass_residual_t_per_day"], 0.0, places=12)
        self.assertAlmostEqual(res["c5_plus_bbl_per_day"], 32643.6, places=1)
        self.assertAlmostEqual(res["c3_plus_bbl_per_day"], 34448.4, places=1)
        self.assertAlmostEqual(res["liquid_vol_gain_c5_pct"], 8.81, places=2)
        self.assertEqual(res["outputs"]["acid_gas"]["phase"], "gas")
        self.assertIsNone(res["outputs"]["acid_gas"]["volume_bbl_per_day"])

        # 30,001 bbl/day MUST be INFEASIBLE (WORLD-01)
        res_infeas = eq.hcu_evaluate(
            requested_feed_bbl_per_day=30001.0,
            compressor_circ_fraction=0.75,
            h2_allocable_t_per_day=h2_norm["hcu_headroom_t_per_day"],
            fixture_mode=True,
        )
        self.assertFalse(res_infeas["feasible"])
        self.assertEqual(res_infeas["status"], "INFEASIBLE")

        # SCN-A-H2CONT SMR turndown (57 t/day -> 120 net -> 75 headroom): overrides compressor cap at 3,750 t/day (25,945 bbl/day)
        h2_cont = eq.h2_header_balance(57.0, 73.0, 5.0, 5.0, 5.0, 40.0)
        self.assertAlmostEqual(h2_cont["hcu_headroom_t_per_day"], 75.0, places=9)
        res_h2 = eq.hcu_evaluate(
            requested_feed_bbl_per_day=30000.0,
            compressor_circ_fraction=0.75,
            h2_allocable_t_per_day=h2_cont["hcu_headroom_t_per_day"],
            fixture_mode=True,
        )
        self.assertEqual(res_h2["binding_constraint"], "shared_h2_cap")
        self.assertAlmostEqual(res_h2["max_feed_t_per_day"], 3750.0, places=6)
        self.assertAlmostEqual(res_h2["max_feed_bbl_per_day"], 25945.1, delta=1.0)

    def test_eq06_fcc_positive_ccr_exact_fixture_and_wp1_calibration_bounds(self):
        # PPC-REVIEW-002 §3 test constants countercheck
        ya, yb, yc, yd = eq.fcc_4lump_integrate(
            w_ccr_feed=0.04, k1=2.2, k2=0.35, k3=0.55, k4=0.18, beta_bc=0.80, alpha_d=0.40, f_add=0.75
        )
        self.assertAlmostEqual(ya, 0.290206, places=5)
        self.assertAlmostEqual(yb, 0.419304, places=5)
        self.assertAlmostEqual(yc, 0.200504, places=5)
        self.assertAlmostEqual(yd, 0.089986, places=5)
        self.assertAlmostEqual(ya + yb + yc + yd, 1.0, places=12)

        # WP-1 calibrated kinetic set must land strictly inside ADR-0056 G3-c bounds
        cal = eq.fcc_evaluate(feed_t_per_day=3100.0, w_ccr_feed=0.012)
        self.assertTrue(cal["feasible"])
        self.assertLessEqual(abs(cal["mass_residual_t_per_day"]), 1e-9 * 3100.0)
        self.assertLessEqual(abs(cal["sulfur_residual_t_per_day"]), 1e-9 * 3100.0)
        self.assertLessEqual(cal["energy_residual_rel"], 1e-4)
        self.assertTrue(70.0 <= cal["conversion_wt_pct"] <= 78.0, cal["conversion_wt_pct"])
        self.assertTrue(44.0 <= cal["yields_wt_pct"]["naphtha"] <= 52.0, cal["yields_wt_pct"])
        self.assertTrue(16.0 <= cal["yields_wt_pct"]["gas_total"] <= 22.0, cal["yields_wt_pct"])
        self.assertTrue(4.5 <= cal["yields_wt_pct"]["coke"] <= 6.5, cal["yields_wt_pct"])
        self.assertTrue(14.0 <= cal["yields_wt_pct"]["lco"] <= 20.0, cal["yields_wt_pct"])
        self.assertTrue(5.0 <= cal["yields_wt_pct"]["slurry"] <= 9.0, cal["yields_wt_pct"])

    def test_eq08_blending_fixtures_rvp_rt70_sulfur_flash_cloud_and_gates(self):
        # Chevron RVP: 96% @ 6.80 + 4% @ 52.00 = 9.25 psi
        rvp = eq.chevron_rvp_psi([0.96, 0.04], [6.80, 52.00])
        self.assertAlmostEqual(rvp, 9.25, places=2)

        # Mass sulfur T24: 100 t @ 10 ppmw + 5 t @ 100 ppmw = 14.286 (PASS); 6 t = 15.094 (HOLD)
        s_pass = eq.blend_sulfur_ppmw([100.0, 5.0], [10.0, 100.0])
        s_hold = eq.blend_sulfur_ppmw([100.0, 6.0], [10.0, 100.0])
        self.assertAlmostEqual(s_pass, 100.0 / 7.0, places=9)
        self.assertAlmostEqual(s_hold, 800.0 / 53.0, places=9)
        self.assertEqual(eq.evaluate_ulsd_release(s_pass, 60.0, 44.0, 45.0, 28.0, -10.0, -5.0)["disposition"], "RELEASE")
        self.assertEqual(eq.evaluate_ulsd_release(s_hold, 60.0, 44.0, 45.0, 28.0, -10.0, -5.0)["disposition"], "QUALITY_HOLD")
        # Unhydrotreated LCO always holds even if numeric sulfur/flash/cetane look OK
        self.assertEqual(
            eq.evaluate_ulsd_release(10.0, 60.0, 45.0, 45.0, 25.0, -10.0, -5.0, contains_unhydrotreated_lco=True)["disposition"],
            "QUALITY_HOLD",
        )

        # Ethyl RT-70 (PPC-REVIEW-002 §3 #6): RON 91.1960, MON 81.4457, BOB AKI 86.3209, E10 AKI 88.99
        rt70 = eq.ethyl_rt70_octane(
            vol_fracs=[0.40, 0.40, 0.15, 0.05],
            rons=[98.0, 90.0, 68.0, 94.0],
            mons=[87.0, 79.0, 66.0, 90.0],
            olefins_vol_pct=[1.0, 28.0, 1.0, 0.0],
            aromatics_vol_pct=[62.0, 25.0, 3.0, 0.0],
        )
        self.assertAlmostEqual(rt70["ron"], 91.1960, places=4)
        self.assertAlmostEqual(rt70["mon"], 81.4457, places=4)
        self.assertAlmostEqual(rt70["aki"], 86.3209, places=4)
        bob_rel = eq.evaluate_bob_and_e10_release("REGULAR", rt70["aki"], 6.7, 6.8, 8.0)
        self.assertEqual(bob_rel["disposition"], "RELEASE")
        self.assertAlmostEqual(bob_rel["terminal_e10_aki"], 88.99, places=2)
        # Untreated LSR always holds
        self.assertEqual(
            eq.evaluate_bob_and_e10_release("REGULAR", rt70["aki"], 6.7, 6.8, 8.0, contains_untreated_lsr=True)["disposition"],
            "QUALITY_HOLD",
        )

        # Wickey-Chittenden flash and Hu-Burns cloud bounds
        flash = eq.wickey_chittenden_flash_c([0.5, 0.5], [50.0, 70.0])
        self.assertTrue(50.0 < flash < 60.0)  # weighted toward lower flash component
        cloud = eq.hu_burns_cloud_k([0.5, 0.5], [260.0, 275.0])
        self.assertTrue(268.0 < cloud < 275.0)  # weighted toward higher cloud component


class TestWorldKernelReplayBranchesAndDST(unittest.TestCase):
    def test_world002_70min_baseline_vs_0840_child_branch_and_isolation(self):
        t0 = datetime(2026, 6, 15, 8, 0, tzinfo=timezone.utc)
        t_derate = datetime(2026, 6, 15, 8, 10, tzinfo=timezone.utc)
        t_fork = datetime(2026, 6, 15, 8, 40, tzinfo=timezone.utc)
        t_end = datetime(2026, 6, 15, 9, 10, tzinfo=timezone.utc)

        base_state = WorldState(world_version="world-v1.0.0", branch_id="baseline", root_seed=42, current_time_utc=t0)
        base = RefineryWorldKernel(base_state, step_seconds=60, fixture_mode=True)
        base.schedule_event(WorldEvent("EVT-DERATE", t_derate, "HCU_COMPRESSOR_DERATE", {"compressor_circ_fraction": 0.75}))

        # Advance baseline to 08:40 checkpoint
        base.advance_to(t_fork)
        ckpt = base.checkpoint()
        ckpt_digest_before = ckpt["state_digest"]

        # Fork isolated child branch at 08:40 reducing HCU feed to 24,000 bbl/day for final 30 min
        child = RefineryWorldKernel.from_checkpoint(ckpt, branch_id="child-24k")
        child.schedule_event(WorldEvent("EVT-SET-24K", t_fork, "HCU_FEED_SETPOINT", {"requested_feed_bbl_per_day": 24000.0}))

        # Run both to 09:10 UTC
        base.advance_to(t_end)
        child.advance_to(t_end)

        # Exact WORLD-002 §6 / PPC-ENG-001 §4 fixtures:
        # Baseline: 10 min @ 36,000 (250 bbl) + 60 min @ 30,000 (1,250 bbl) = 1,500 bbl
        # Child:    10 min @ 36,000 (250 bbl) + 30 min @ 30,000 (625 bbl) + 30 min @ 24,000 (500 bbl) = 1,375 bbl
        self.assertAlmostEqual(base.state.hcu_cumulative_processed_bbl, 1500.0, places=9)
        self.assertAlmostEqual(child.state.hcu_cumulative_processed_bbl, 1375.0, places=9)
        self.assertAlmostEqual(
            base.state.hcu_cumulative_processed_bbl - child.state.hcu_cumulative_processed_bbl, 125.0, places=9
        )
        # Child never mutated parent checkpoint (PO-09)
        self.assertEqual(ckpt["state"].digest(), ckpt_digest_before)

        # Bit-exact replay from checkpoint
        replay = RefineryWorldKernel.from_checkpoint(ckpt)
        replay.advance_to(t_end)
        self.assertEqual(replay.state.digest(), base.state.digest())

    def test_step_refinement_60s_10s_1s_and_dst_23_25_hours_and_paired_rng(self):
        t0 = datetime(2026, 6, 15, 8, 0, tzinfo=timezone.utc)
        t_derate = datetime(2026, 6, 15, 8, 10, tzinfo=timezone.utc)
        t_end = datetime(2026, 6, 15, 9, 10, tzinfo=timezone.utc)

        totals = {}
        for dt in (60, 10, 1):
            k = RefineryWorldKernel(WorldState("world-v1.0.0", f"dt-{dt}", 42, t0), step_seconds=dt, fixture_mode=True)
            k.schedule_event(WorldEvent("EVT-DERATE", t_derate, "HCU_COMPRESSOR_DERATE", {"compressor_circ_fraction": 0.75}))
            k.advance_to(t_end)
            totals[dt] = k.state.hcu_cumulative_processed_bbl
        self.assertAlmostEqual(totals[60], totals[10], places=9)
        self.assertAlmostEqual(totals[60], totals[1], places=9)

        # America/Chicago DST business days (6 AM to 6 AM): spring forward 2026-03-08 (23h), fall back 2026-11-01 (25h)
        self.assertEqual(local_business_day_elapsed_hours("2026-03-07"), 23.0)
        self.assertEqual(local_business_day_elapsed_hours("2026-10-31"), 25.0)
        self.assertEqual(local_business_day_elapsed_hours("2026-06-15"), 24.0)

        # Semantic-keyed paired PCG64 RNG produces bit-identical sequences across sibling branches
        s1 = paired_rng(42, "exogenous:ambient_temp_day_1").normal(25.0, 2.0, size=5).tolist()
        s2 = paired_rng(42, "exogenous:ambient_temp_day_1").normal(25.0, 2.0, size=5).tolist()
        s3 = paired_rng(42, "exogenous:ambient_temp_day_2").normal(25.0, 2.0, size=5).tolist()
        self.assertEqual(s1, s2)
        self.assertNotEqual(s1, s3)

    def test_po12a_hardening_cdu_overlap_hcu_sulfur_fcc_heat_smr_ramp_and_bob_caps(self):
        # 1. EQ-04: overlap > 2 wt% rejected; valid <= 2 wt% conserves true feed sulfur to <= 1e-12
        dummy_assay = {
            "A1": {
                "tbp_points_vol_pct_c": [[0, 0], [10, 85], [30, 175], [45, 240], [65, 360], [85, 565], [100, 700]],
                "cuts": [
                    {"sg_60_60": 0.54, "sulfur_wt_pct": 0.01},
                    {"sg_60_60": 0.67, "sulfur_wt_pct": 0.05},
                    {"sg_60_60": 0.75, "sulfur_wt_pct": 0.15},
                    {"sg_60_60": 0.81, "sulfur_wt_pct": 0.40},
                    {"sg_60_60": 0.85, "sulfur_wt_pct": 1.20},
                    {"sg_60_60": 0.91, "sulfur_wt_pct": 2.20},
                    {"sg_60_60": 1.01, "sulfur_wt_pct": 3.80},
                ],
            }
        }
        with self.assertRaises(eq.OutOfEnvelopeError):
            eq.cdu_vdu_cut_split({"A1": 10000.0}, dummy_assay, overlap_shifts=[0.0, 0.0, 0.0, 0.0, 0.05, -0.05, 0.0])
        ok_ov = eq.cdu_vdu_cut_split({"A1": 10000.0}, dummy_assay, overlap_shifts=[0.0, 0.0, 0.0, 0.0, 0.02, -0.02, 0.0])
        self.assertLessEqual(abs(ok_ov["mass_residual_t_per_day"]), 1e-9)
        self.assertLessEqual(abs(ok_ov["sulfur_residual_t_per_day"]), 1e-9)

        # 2. EQ-05 runtime mode closes stoichiometric H2S, 30 MJ/kg H2 quench heat, and y_h2_rec
        hcu_rt = eq.hcu_evaluate(
            requested_feed_bbl_per_day=30000.0,
            feed_sulfur_wt_frac=0.022,
            compressor_circ_fraction=0.75,
            fixture_mode=False,
        )
        self.assertTrue(hcu_rt["sulfur_balance"]["acid_gas_covers_stoichiometric_h2s"])
        self.assertLessEqual(abs(hcu_rt["sulfur_balance"]["sulfur_residual_t_per_day"]), 1e-9)
        self.assertLessEqual(abs(hcu_rt["mass_residual_t_per_day"]), 1e-9)
        self.assertGreater(hcu_rt["quench_heat_release_kw"], 25000.0)
        self.assertAlmostEqual(hcu_rt["recycle_h2_purity_y_h2"], 0.85, places=6)

        # 3. EQ-06 Arrhenius T_rxr / CTO genuinely change yields, and heat-deficient corner is INFEASIBLE
        fcc_base = eq.fcc_evaluate(feed_t_per_day=3100.0, t_rxr_c=525.0, cat_to_oil=6.5)
        fcc_hot = eq.fcc_evaluate(feed_t_per_day=3100.0, t_rxr_c=540.0, cat_to_oil=7.5)
        self.assertGreater(fcc_hot["conversion_wt_pct"], fcc_base["conversion_wt_pct"])
        fcc_cold_corner = eq.fcc_evaluate(
            feed_t_per_day=3100.0, w_ccr_feed=0.0, t_rxr_c=495.0, t_regen_c=740.0, cat_to_oil=9.0
        )
        self.assertFalse(fcc_cold_corner["heat_balance_feasible"])
        self.assertFalse(fcc_cold_corner["feasible"])

        # 4. EQ-07 SMR 2%/min ramp limit + DHT shortfall prevents double allocation
        h2_ramp = eq.h2_header_balance(
            smr_h2_t_per_day=60.0,
            reformer_h2_t_per_day=73.0,
            nht_draw_t_per_day=5.0,
            fcc_hds_draw_t_per_day=5.0,
            header_loss_t_per_day=5.0,
            dht_committed_t_per_day=40.0,
            prev_smr_h2_t_per_day=107.0,
            dt_minutes=1.0,
        )
        self.assertFalse(h2_ramp["smr_ramp_feasible"])
        self.assertAlmostEqual(h2_ramp["smr_effective_t_per_day"], 104.6, places=6)
        h2_short = eq.h2_header_balance(20.0, 10.0, 5.0, 5.0, 5.0, 40.0, hcu_requested_t_per_day=25.0)
        self.assertTrue(h2_short["no_double_allocation"])
        self.assertAlmostEqual(h2_short["dht_shortfall_t_per_day"], 25.0, places=6)
        self.assertAlmostEqual(h2_short["hcu_allocated_t_per_day"], 0.0, places=6)

        # 5. EQ-08 enforces <=10% premium pool share and <=10 ppmw Tier 3 annual average sulfur
        self.assertEqual(
            eq.evaluate_bob_and_e10_release("PREMIUM", 89.0, 6.2, 6.4, 8.0, premium_pool_vol_frac=0.12)["disposition"],
            "QUALITY_HOLD",
        )
        self.assertEqual(
            eq.evaluate_bob_and_e10_release("REGULAR", 86.0, 6.2, 6.4, 15.0, annual_avg_sulfur_ppmw=11.0)["disposition"],
            "QUALITY_HOLD",
        )

    def test_kernel_smr_ramp_w202_ordering_digest_checkpoint_and_tank_stepping(self):
        t0 = datetime(2026, 6, 15, 8, 0, tzinfo=timezone.utc)
        t1 = datetime(2026, 6, 15, 8, 10, tzinfo=timezone.utc)
        t2 = datetime(2026, 6, 15, 8, 15, tzinfo=timezone.utc)

        sg = 0.840
        tk = TankState(
            tank_id="TK-TEST",
            min_bbl=1000.0,
            max_bbl=12000.0,
            sg_60_60=sg,
            mass_kg=eq.volume_bbl_to_mass_kg(11950.0, sg),
            inflow_kg_s=eq.volume_bbl_to_mass_kg(600.0, sg) / 3600.0,
            outflow_kg_s=eq.volume_bbl_to_mass_kg(200.0, sg) / 3600.0,
        )
        st = WorldState("world-v1.0.0", "baseline", 42, t0, tanks={"TK-TEST": tk})
        # All mutable physics fields affect digest()
        d_init = st.digest()
        for attr, new_val in (
            ("hcu_mech_cap_bbl_per_day", 38000.0),
            ("hcu_running", False),
            ("reformer_h2_t_per_day", 70.0),
            ("nht_h2_draw_t_per_day", 6.0),
            ("fcc_hds_h2_draw_t_per_day", 6.0),
            ("h2_header_loss_t_per_day", 6.0),
            ("dht_committed_h2_t_per_day", 42.0),
        ):
            orig = getattr(st, attr)
            setattr(st, attr, new_val)
            self.assertNotEqual(st.digest(), d_init, f"digest() missed field {attr}")
            setattr(st, attr, orig)
        self.assertEqual(st.digest(), d_init)

        k = RefineryWorldKernel(st, step_seconds=60, fixture_mode=True)
        # W2-02: Schedule setpoint BEFORE derate at the SAME instant t1 — derate MUST execute first so setpoint is INFEASIBLE!
        k.schedule_event(WorldEvent("EVT-A-SET", t1, "HCU_FEED_SETPOINT", {"requested_feed_bbl_per_day": 36000.0}))
        k.schedule_event(WorldEvent("EVT-Z-DERATE", t1, "HCU_COMPRESSOR_DERATE", {"compressor_circ_fraction": 0.75}))
        k.schedule_event(WorldEvent("EVT-SMR", t1, "SMR_TURNDOWN", {"smr_h2_t_per_day": 60.0}))

        outcomes = k.advance_to(t2)
        self.assertIn("EVT-A-SET", k.state.rejected_events)
        self.assertEqual(k.state.rejected_events["EVT-A-SET"]["status"], "INFEASIBLE")
        self.assertTrue(any(h.get("status") == "INFEASIBLE" and h.get("event_id") == "EVT-A-SET" for h in k.state.history))
        self.assertTrue(any(o.get("status") == "INFEASIBLE" for o in outcomes))

        # SMR ramped 5 minutes from 107.0 at 2%/min of 120 = 2.4 t/day/min -> 95.0 t/day (not instant 60.0!)
        self.assertAlmostEqual(k.state.smr_h2_t_per_day, 95.0, places=6)

        # Tank stepped via EQ-02 exact intra-step t* split and rode exactly at max 12,000 bbl without exceeding
        self.assertAlmostEqual(k.state.tanks["TK-TEST"].volume_bbl, 12000.0, places=6)

        # W2-07: Corrupted state (including tank loss_kg_s) OR corrupted pending event MUST fail integrity check
        ckpt = k.checkpoint()
        ckpt_bad_smr = k.checkpoint()
        ckpt_bad_smr["state"].smr_h2_t_per_day = 55.0
        with self.assertRaises(ValueError):
            RefineryWorldKernel.from_checkpoint(ckpt_bad_smr)

        ckpt_bad_loss = k.checkpoint()
        ckpt_bad_loss["state"].tanks["TK-TEST"].loss_kg_s = 5.0
        with self.assertRaises(ValueError):
            RefineryWorldKernel.from_checkpoint(ckpt_bad_loss)

        for tamper_name, mutator in (
            ("tank_max_bbl", lambda c: setattr(c["state"].tanks["TK-TEST"], "max_bbl", 11900.0)),
            ("tank_min_bbl", lambda c: setattr(c["state"].tanks["TK-TEST"], "min_bbl", 500.0)),
            ("tank_sg", lambda c: setattr(c["state"].tanks["TK-TEST"], "sg_60_60", 0.900)),
            ("root_seed", lambda c: setattr(c["state"], "root_seed", 999)),
            ("history", lambda c: c["state"].history.append({"tampered": True})),
            ("fixture_mode", lambda c: c.__setitem__("fixture_mode", not c["fixture_mode"])),
            ("step_seconds", lambda c: c.__setitem__("step_seconds", 120)),
        ):
            bad_ckpt = k.checkpoint()
            mutator(bad_ckpt)
            with self.assertRaises(ValueError, msg=f"from_checkpoint failed to reject tampered {tamper_name}"):
                RefineryWorldKernel.from_checkpoint(bad_ckpt)

        k_sched = RefineryWorldKernel.from_checkpoint(ckpt)
        k_sched.schedule_event(WorldEvent("EVT-FUT", datetime(2026, 6, 15, 8, 30, tzinfo=timezone.utc), "SMR_TURNDOWN", {"smr_h2_t_per_day": 80.0}))
        ckpt_sched = k_sched.checkpoint()
        ckpt_sched["scheduled"][0].payload["smr_h2_t_per_day"] = 55.0
        with self.assertRaises(ValueError):
            RefineryWorldKernel.from_checkpoint(ckpt_sched)

        # EQ-02 MIN-bound with declared loss > inflow MUST ride strictly on min_mass_kg without going negative or crashing kernel
        loss_only = eq.step_tank_with_exact_crossing(
            opening_mass_kg=eq.volume_bbl_to_mass_kg(2000.0, sg),
            min_mass_kg=eq.volume_bbl_to_mass_kg(1000.0, sg),
            max_mass_kg=eq.volume_bbl_to_mass_kg(12000.0, sg),
            inflow_rate_kg_s=0.0,
            outflow_rate_kg_s=0.0,
            loss_rate_kg_s=eq.volume_bbl_to_mass_kg(200.0, sg) / 3600.0,
            dt_s=86400.0,
            rule="throttle",
        )
        self.assertAlmostEqual(eq.mass_kg_to_volume_bbl(loss_only.closing_mass_kg, sg), 1000.0, places=6)
        self.assertAlmostEqual(loss_only.mass_residual_kg, 0.0, places=12)

        k_loss = RefineryWorldKernel(
            WorldState(
                "world-v1.0.0",
                "loss-test",
                42,
                t0,
                tanks={"TK-LOSS": TankState("TK-LOSS", 1000.0, 12000.0, sg, eq.volume_bbl_to_mass_kg(1200.0, sg))},
            ),
            step_seconds=60,
        )
        k_loss.schedule_event(
            WorldEvent(
                "EVT-LOSS",
                t0,
                "TANK_FLOW_SCHEDULE",
                {"tank_id": "TK-LOSS", "inflow_kg_s": 0.0, "outflow_kg_s": 0.0, "loss_kg_s": eq.volume_bbl_to_mass_kg(400.0, sg) / 3600.0},
            )
        )
        k_loss.advance_to(datetime(2026, 6, 15, 10, 0, tzinfo=timezone.utc))
        self.assertAlmostEqual(k_loss.state.tanks["TK-LOSS"].volume_bbl, 1000.0, places=6)

        # EQ-02 MIN-bound `block` rule MUST NOT re-cross above max_mass_kg over long dt_s
        min_block_long = eq.step_tank_with_exact_crossing(
            opening_mass_kg=eq.volume_bbl_to_mass_kg(1001.0, sg),
            min_mass_kg=eq.volume_bbl_to_mass_kg(1000.0, sg),
            max_mass_kg=eq.volume_bbl_to_mass_kg(12000.0, sg),
            inflow_rate_kg_s=eq.volume_bbl_to_mass_kg(1900.0, sg) / 3600.0,
            outflow_rate_kg_s=eq.volume_bbl_to_mass_kg(2000.0, sg) / 3600.0,
            loss_rate_kg_s=0.0,
            dt_s=86400.0,
            rule="block",
        )
        self.assertAlmostEqual(eq.mass_kg_to_volume_bbl(min_block_long.closing_mass_kg, sg), 12000.0, places=6)
        self.assertAlmostEqual(
            min_block_long.accepted_inflow_kg + min_block_long.accepted_outflow_kg + min_block_long.diverted_or_blocked_kg,
            eq.volume_bbl_to_mass_kg(3900.0, sg) * 24.0,
            places=4,
        )

    def test_coupled_plant_snapshot_and_eng_v07_benchmark_transparency(self):
        design_basis = yaml.safe_load(DESIGN_BASIS_PATH.read_text(encoding="utf-8"))
        # Normal snapshot
        snap = evaluate_refinery_plant_snapshot(design_basis)
        self.assertTrue(snap["hydraulics_all_feasible"])
        self.assertEqual(snap["ulsd_gate"]["disposition"], "RELEASE")
        self.assertEqual(snap["bob_gate"]["disposition"], "RELEASE")
        self.assertGreater(snap["volume_gain_summary"]["hcu_c5_plus_gain_pct"], 4.0)
        self.assertTrue(1000.0 <= snap["volume_gain_summary"]["hcu_h2_uptake_scf_per_bbl"] <= 2500.0)
        # Verify exact EQ-05 H2 SCF/kg factor matches PPC-REVIEW-002 §3 worked example (86.72 t/day / 30k bbl/d = 1,199.7 SCF/bbl)
        expected_h2_scf_per_bbl = (
            float(snap["hcu"]["h2_net_t_per_day"])
            * 1000.0
            * (eq.V_M_STD_SCF_LBMOL / eq.M_H2_LB_LBMOL / eq.LB_TO_KG)
            / float(snap["hcu"]["actual_feed_bbl_per_day"])
        )
        self.assertAlmostEqual(snap["volume_gain_summary"]["hcu_h2_uptake_scf_per_bbl"], expected_h2_scf_per_bbl, places=9)
        self.assertAlmostEqual(
            86.72 * 1000.0 * (eq.V_M_STD_SCF_LBMOL / eq.M_H2_LB_LBMOL / eq.LB_TO_KG) / 30000.0,
            1199.7,
            delta=0.1,
        )
        # Derated snapshot explicitly accounts for unprocessed VGO routed to TK-201
        derated = evaluate_refinery_plant_snapshot(design_basis, hcu_compressor_circ_fraction=0.75)
        self.assertGreater(derated["unprocessed_vgo_to_tk201_bbl_per_day"], 0.0)
        # Non-tautological HCU sulfur check: fixture_mode with high sulfur detects acid_gas deficit
        hcu_fix_hi_s = eq.hcu_evaluate(
            requested_feed_bbl_per_day=30000.0,
            feed_sulfur_wt_frac=0.05,
            compressor_circ_fraction=0.75,
            fixture_mode=True,
        )
        self.assertFalse(hcu_fix_hi_s["sulfur_balance"]["acid_gas_covers_stoichiometric_h2s"])
        self.assertLess(hcu_fix_hi_s["sulfur_balance"]["sulfur_residual_t_per_day"], -1.0)

        # ENG-V07 benchmark transparently reports unit+conservation vs plant C5+ band
        bench = run_eng_v07_mode_benchmark(design_basis)
        self.assertTrue(bench["unit_and_conservation_gates_pass"])
        self.assertLessEqual(bench["max_absolute_residual_t_per_day"], 1e-6)
        self.assertEqual(
            bench["all_holdout_gates_pass"],
            bench["unit_and_conservation_gates_pass"] and bench["po12a_plant_c5_gain_band_pass"],
        )


if __name__ == "__main__":
    unittest.main()
