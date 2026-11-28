# PPC-REVIEW-005 — PO-12a Refinery A empirical plausibility benchmark report

| Document control | Value |
|---|---|
| Document ID | `PPC-REVIEW-005` |
| Status | Accepted with Conditions (Owner Signed 2026-11-28) |
| Report date | `2026-11-28` |
| Reviewed commit | `88f5fe4` (merged `main`, pull request #33) |
| Reviewer | Claude Fable 5.2 (`claude-fable-5-2`), AI automated technical reviewer (separate from the night-run coding session that authored commit `88f5fe4`; not a human process-engineering reviewer — see Section 2). |
| Owner sign-off | Signed by Hamid Adesokan on `2026-11-28` (accepted with conditions; see Section 6 and [ADR-0062](../../adr/0062-po12a-signoff-openrouter-endpoint-and-local-hosting.md)). |
| Governing decisions | [ADR-0056](../../adr/0056-identity-steward-action-thresholds-and-refinery-a-parameters.md) `G3-c` and `G3-d`, [ADR-0059](../../adr/0059-overnight-night-run-delegation-and-standin-authority.md), [ADR-0062](../../adr/0062-po12a-signoff-openrouter-endpoint-and-local-hosting.md), [PPC-REVIEW-004](PPC-REVIEW-004_Proof_Obligation_and_Validation_Register.md) `PO-12a` |
| Code and data reviewed | `generators/equations.py`, `generators/world_kernel.py`, `fixtures/golden/refinery_a_design_basis.yaml` |
| Evidence file | `/tmp/ppc_po12a_benchmark_main.json`, the output of `run_eng_v07_mode_benchmark`, copied in full in Appendix A |
| Provenance class | `SYNTHETIC`. Pearland Petroleum Corporation is fictional. No value in this report describes a real refinery. |

## 1. Verdict

The unit-level and conservation checks pass in all five operating modes. The plant-level `PO-12a` criterion fails in all five. The benchmark reports `all_holdout_gates_pass: false`, and that value is correct. (Dated note, 2026-11-28: this finding is against the original plant C5+ band of `+4%` to `+10%`. [ADR-0062](../../adr/0062-po12a-signoff-openrouter-endpoint-and-local-hosting.md) restated the `PO-12a` plant criterion to plant C3+ volumetric gain `+2.5%` to `+4.5%` and recorded conditional acceptance pending the benchmark gate update in Section 6.)

The following checks pass:

- The CDU/VDU cut split closes mass and sulfur.
- The FCC 4-lump model closes mass and sulfur, and its heat balance is feasible.
- HCU C5+ liquid volume gain is 8.19 to 8.64 percent. The kernel's own `po12a_hcu_gain_in_4_to_10` flag checks a 4 to 10 percent band (not defined in `PPC-REVIEW-004` or `ADR-0056` at review time; see Section 2; dated note 2026-11-28: [ADR-0062](../../adr/0062-po12a-signoff-openrouter-endpoint-and-local-hosting.md) formally registered this unit-level HCU C5+ `+4%` to `+10%` band in `PPC-REVIEW-004` and `ADR-0056`).
- HCU hydrogen uptake is 1,258 to 1,260 SCF/bbl. The band is 1,000 to 2,500 SCF/bbl.
- The shared hydrogen header reports zero double allocation.
- All six `EQ-03` transfer lines are hydraulically feasible.
- The largest mass or sulfur residual is 3.6e-12 t/day. The `ADR-0056` tolerance is 1e-9.

The plant-level criterion in `PO-12a` at review time was a plant C5+ volumetric gain of +4 to +10 percent. The kernel gives -3.48 to -4.98 percent. Plant C3+ gain, which adds LPG, is +3.00 to +3.99 percent. That was also below +4 percent in every mode. (Dated note, 2026-11-28: [ADR-0062](../../adr/0062-po12a-signoff-openrouter-endpoint-and-local-hosting.md) restated the `PO-12a` plant criterion to plant C3+ volumetric gain `+2.5%` to `+4.5%` and registered the unit-level HCU C5+ band `+4%` to `+10%`, keeping the measured results above as the finding against the original C5+ band.)

The benchmark sets `unit_and_conservation_gates_pass: true` and `po12a_plant_c5_gain_band_pass: false`. The overall flag is the logical AND of the two, so it is false. No parameter was tuned to move the plant figure into the band. `ADR-0056` `G3-d` requires that: "If WP-1 cannot close a balance inside a range, it returns to the owner and does not tune silently."

The owner must decide two things before `WP-1` can exit. The first is the measurement basis of the plant gain criterion. The second is one FCC yield that is outside its range. Section 6 states both decisions. (Dated note, 2026-11-28: Hamid Adesokan decided both items and recorded conditional acceptance of `PO-12a` in Section 6 and [ADR-0062](../../adr/0062-po12a-signoff-openrouter-endpoint-and-local-hosting.md).)

## 2. Method

I read the three source files at commit `88f5fe4`. I then ran `run_eng_v07_mode_benchmark` against the design basis with `uv run --no-project --with pyyaml --with numpy`. The result is equal to the evidence file in every field and every digit.

I also ran `evaluate_refinery_plant_snapshot` for each mode to read values that the evidence file does not contain. These are FCC yields, HCU feed rates, cut volumes and the hydrogen header balance. Section 4 reports them and labels them as reviewer reproduction.

I wrote no files and changed no code. I am an AI model, not a human process engineer, and repository git metadata records only the owner's account rather than which model authored commit `88f5fe4`. `ADR-0056` `G3-d` and `PPC-REVIEW-004` require `PO-12a` evidence prepared by a process-engineering reviewer who did not write the kernel. An AI automated technical review does not by itself satisfy a human process-engineering reviewer qualification; Hamid Adesokan must decide whether this automated review suffices or whether to commission a separate human process-engineering review before closing `PO-12a`. (Dated note, 2026-11-28: Hamid Adesokan conditionally accepted this automated review for v1 synthetic qualification in Section 6 and [ADR-0062](../../adr/0062-po12a-signoff-openrouter-endpoint-and-local-hosting.md).)

`PPC-REVIEW-004` names four benchmark sources for `PO-12a`: EIA PADD 3 gain, Gary–Handwerk, Maples, and GPSA. This report checks only the EIA processing-gain definition and the numeric bands already recorded in `ADR-0056`, `PPC-REVIEW-004`, and the kernel code. Primary editions of Gary–Handwerk, Maples, and GPSA are not pinned in this repository and were not cross-checked here. In addition, the unit-level HCU C5+ gain band of 4 to 10 percent appears only in the kernel's `po12a_hcu_gain_in_4_to_10` flag (`generators/world_kernel.py`), not in `PPC-REVIEW-004` or `ADR-0056`. (Dated note, 2026-11-28: [ADR-0062](../../adr/0062-po12a-signoff-openrouter-endpoint-and-local-hosting.md) formally registered the unit-level HCU C5+ `+4%` to `+10%` band in `PPC-REVIEW-004` and `ADR-0056`.)

Claude Fable 5.2 is also the owner stand-in named in `ADR-0059`. That ADR keeps `PO-12a` sign-off with Hamid Adesokan. This report gives findings and a recommendation. It does not sign.

## 3. Benchmark results

All values in sections 3.1 and 3.2 come from the evidence file. Percentages and SCF/bbl values are rounded to four decimal places. Residuals are rounded to three significant figures. Appendix A has the unrounded values.

The five modes are:

| Mode | Set | Crude charge, light / medium / heavy (bbl/day) | Recycle compressor circulation | SMR hydrogen (t/day) | FCC conditions |
|---|---|---|---|---|---|
| `train_nominal_design_blend` | Training | 54,000 / 90,000 / 36,000 | 100% | 107 | 525 °C, catalyst-to-oil 6.5 |
| `train_uc1_compressor_derate_75pct` | Training | 54,000 / 90,000 / 36,000 | 75% | 107 | 525 °C, catalyst-to-oil 6.5 |
| `holdout_uc4_heavy_sour_swing` | Holdout | 36,000 / 72,000 / 72,000 | 100% | 115 | 525 °C, catalyst-to-oil 6.5 |
| `holdout_light_sweet_high_severity_fcc` | Holdout | 90,000 / 72,000 / 18,000 | 100% | 107 | 532 °C, catalyst-to-oil 7.0 |
| `holdout_uc2_smr_h2_constrained` | Holdout | 54,000 / 90,000 / 36,000 | 75% | 60 | 525 °C, catalyst-to-oil 6.5 |

### 3.1 Training modes

| Field | `train_nominal_design_blend` | `train_uc1_compressor_derate_75pct` |
|---|---|---|
| CDU mass residual (t/day) | 3.64e-12 | 3.64e-12 |
| CDU sulfur residual (t/day) | 1.14e-13 | 1.14e-13 |
| FCC mass residual (t/day) | 1.82e-12 | 1.82e-12 |
| FCC sulfur residual (t/day) | 0.0 | 0.0 |
| FCC heat balance feasible | true | true |
| HCU mass residual (t/day) | 0.0 | 0.0 |
| HCU sulfur residual (t/day) | 0.0 | 0.0 |
| HCU acid gas covers stoichiometric H2S | true | true |
| Hydrogen header, no double allocation | true | true |
| Hydraulics all feasible | true | true |
| HCU binding constraint | `shared_h2_cap` | `compressor_circulation_cap` |
| HCU C5+ gain (%) | 8.4442 | 8.4442 |
| HCU hydrogen uptake (SCF/bbl) | 1,259.5924 | 1,259.5924 |
| Plant C5+ gain (%) | -4.1693 | -4.3799 |
| Plant C3+ gain (%) | 3.8273 | 3.4670 |
| HCU gain inside 4 to 10 | true | true |
| HCU hydrogen inside 1,000 to 2,500 | true | true |
| Plant C5+ gain inside 4 to 10 | false | false |

### 3.2 Holdout modes

| Field | `holdout_uc4_heavy_sour_swing` | `holdout_light_sweet_high_severity_fcc` | `holdout_uc2_smr_h2_constrained` |
|---|---|---|---|
| CDU mass residual (t/day) | 0.0 | 0.0 | 3.64e-12 |
| CDU sulfur residual (t/day) | 5.68e-14 | 0.0 | 1.14e-13 |
| FCC mass residual (t/day) | 1.36e-12 | 4.55e-13 | 1.82e-12 |
| FCC sulfur residual (t/day) | 0.0 | 0.0 | 0.0 |
| FCC heat balance feasible | true | true | true |
| HCU mass residual (t/day) | 9.09e-13 | 0.0 | 0.0 |
| HCU sulfur residual (t/day) | 0.0 | 0.0 | 0.0 |
| HCU acid gas covers stoichiometric H2S | true | true | true |
| Hydrogen header, no double allocation | true | true | true |
| Hydraulics all feasible | true | true | true |
| HCU binding constraint | `mechanical_cap` | `mechanical_cap` | `shared_h2_cap` |
| HCU C5+ gain (%) | 8.1895 | 8.6364 | 8.4442 |
| HCU hydrogen uptake (SCF/bbl) | 1,259.2304 | 1,258.0075 | 1,259.5924 |
| Plant C5+ gain (%) | -3.4839 | -4.9808 | -4.6515 |
| Plant C3+ gain (%) | 3.9903 | 3.5682 | 3.0028 |
| HCU gain inside 4 to 10 | true | true | true |
| HCU hydrogen inside 1,000 to 2,500 | true | true | true |
| Plant C5+ gain inside 4 to 10 | false | false | false |

### 3.3 Aggregate flags

| Flag | Value |
|---|---|
| `max_absolute_residual_t_per_day` | 3.637978807091713e-12 |
| `unit_and_conservation_gates_pass` | true |
| `po12a_plant_c5_gain_band_pass` | false |
| `all_holdout_gates_pass` | false |

## 4. Reviewer reproduction

The values in this section are not in the evidence file. I computed them from `evaluate_refinery_plant_snapshot` at commit `88f5fe4` with the same inputs as the benchmark.

### 4.1 FCC yields against ADR-0056 G3-c

`PO-12a` requires FCC yields inside the `ADR-0056` targets. The benchmark does not record or test them.

| Yield (wt% of FCC feed) | `ADR-0056` range | Four modes at 525 °C | High-severity holdout at 532 °C |
|---|---|---|---|
| Conversion | 70 to 78 | 73.54 | 75.34 |
| Naphtha | 44 to 52 | 47.66 | 47.69 |
| Gas (dry gas plus LPG) | 16 to 22 | 20.58 | 22.09 |
| Coke | 4.5 to 6.5 | 5.30 | 5.56 |

The four modes at 525 °C give the same yields because FCC feed quality and severity do not change between them. At the high-severity holdout, gas yield is 22.09 wt%. That is 0.09 wt% above the range.

### 4.2 HCU feed and hydrogen

| Mode | HCU feed requested (bbl/day) | HCU feed processed (bbl/day) | VGO sent to `TK-201` (bbl/day) | HCU net hydrogen (t/day) | Header headroom for HCU (t/day) |
|---|---|---|---|---|---|
| `train_nominal_design_blend` | 34,491 | 34,491 | 0 | 104.68 | 120.48 |
| `train_uc1_compressor_derate_75pct` | 34,491 | 30,000 | 4,491 | 91.05 | 120.48 |
| `holdout_uc4_heavy_sour_swing` | 36,461 | 36,461 | 0 | 110.63 | 122.73 |
| `holdout_light_sweet_high_severity_fcc` | 32,847 | 32,847 | 0 | 99.57 | 127.74 |
| `holdout_uc2_smr_h2_constrained` | 34,491 | 24,212 | 10,279 | 73.48 | 73.48 |

HCU net hydrogen is at or below the header headroom in every mode.

### 4.3 Where the plant C5+ volume goes

The table gives each step's change in C5+ liquid volume as a percentage of crude charge volume. Light straight-run naphtha, kerosene, vacuum residue and unprocessed VGO pass through with no change. The diesel hydrotreater row is the remainder after the other rows.

| Step | Nominal | UC-1 derate | UC-4 heavy sour | Light sweet, high severity | UC-2 hydrogen constrained |
|---|---|---|---|---|---|
| Crude LPG cut, not a C5+ liquid | -2.00 | -2.00 | -1.60 | -2.35 | -2.00 |
| CDU column loss | -0.20 | -0.20 | -0.20 | -0.20 | -0.20 |
| Reformer, heavy naphtha to reformate | -2.06 | -2.06 | -1.77 | -2.35 | -2.06 |
| FCC, feed to naphtha, LCO and slurry | -2.11 | -2.11 | -2.11 | -2.22 | -2.11 |
| HCU, feed to C5+ liquids | +1.62 | +1.41 | +1.66 | +1.58 | +1.14 |
| Diesel hydrotreater density change | +0.58 | +0.58 | +0.53 | +0.56 | +0.58 |
| Plant C5+ gain | -4.17 | -4.38 | -3.48 | -4.98 | -4.65 |

## 5. Engineering diagnosis

### 5.1 Why plant C5+ gain is negative

Refinery A v1 has two conversion units, the FCC and the HCU. It has no coker and no other residue conversion. Vacuum residue leaves the plant unconverted through `STR-CDU-VR-EXP`. It is 19.5 to 28.7 percent of crude by mass and 17.0 to 25.7 percent by volume, depending on the crude blend.

The kernel counts vacuum residue in plant C5+ volume at its own density. It therefore adds no gain and no loss. The effect of the unconverted residue is that a fifth to a quarter of the crude cannot contribute any volume gain.

Only the HCU adds much volume. Its unit gain is +8.2 to +8.6 percent, but its feed is 24,212 to 36,461 bbl/day out of 180,000 bbl/day of crude. That gives +1.1 to +1.7 percent of crude. The diesel hydrotreater adds about +0.5 to +0.6 percent.

Three steps remove more C5+ volume than those two add:

1. The crude contains 1.6 to 2.4 percent LPG by volume. LPG is not a C5+ liquid.
2. The reformer turns heavy naphtha into denser reformate at 86 percent mass yield. The rest becomes hydrogen, LPG and dry gas. This removes 1.8 to 2.4 percent.
3. The FCC turns about 26 to 28 percent of its feed mass into LPG, dry gas and coke. This removes 2.1 to 2.2 percent.

Each of these steps is ordinary refinery behavior, and the unit models conserve mass through each one. The negative plant figure comes from the measurement basis and the flowsheet. It does not come from an arithmetic error.

In my view a coker would not move plant C5+ gain into the band. A coker turns part of the residue into coke and gas. Because the kernel now counts residue as a full-volume liquid, coking would lower C5+ volume.

### 5.2 Why plant C3+ gain is positive

Plant C3+ gain adds LPG from the crude, the reformer, the FCC and the HCU. That returns most of the volume in the three loss steps and gives +3.00 to +3.99 percent. Dry gas, coke, acid gas and reformer hydrogen are still outside the count.

### 5.3 The measurement basis of the PO-12a band

`PPC-REVIEW-004` lists "EIA PADD 3 gain" among four benchmark sources for `PO-12a` alongside the +4 to +10 percent acceptance band without binding that band to a single source. (Dated note, 2026-11-28: [ADR-0062](../../adr/0062-po12a-signoff-openrouter-endpoint-and-local-hosting.md) updated `PPC-REVIEW-004` so the `+4%` to `+10%` band applies to unit-level HCU C5+ gain and restated the plant band to C3+ `+2.5%` to `+4.5%`.) The EIA glossary defines processing gain as "the volumetric amount by which total output is greater than input for a given period of time." Total output is a wider basis than C5+ liquids.

The `PO-12a` text applies that band to C5+ liquids only. On that basis the v1 flowsheet cannot reach +4 percent without changing parameters that `ADR-0056` `G3-c` locks. I did not check which products EIA counts in total output beyond this definition. The owner decision in section 6 should confirm the basis before it is written into `PO-12a`. (Dated note, 2026-11-28: [ADR-0062](../../adr/0062-po12a-signoff-openrouter-endpoint-and-local-hosting.md) restated `PO-12a` to plant C3+ volumetric gain `+2.5%` to `+4.5%` and formally registered the unit-level HCU C5+ band `+4%` to `+10%`.)

### 5.4 Limits on what the passing checks show

These notes do not change the verdict. They limit how much weight the passing checks can carry.

**HCU gain and hydrogen uptake are inputs, not predictions.** `ADR-0056` locks chemical hydrogen at 2.0 wt% of feed and purge at 0.10 wt%. Those two numbers and the VGO density give 1,258 to 1,260 SCF/bbl directly. The locked product selectivities and product densities give the 8.19 to 8.64 percent gain. The check confirms that the locked parameters sit inside the `PPC-REVIEW-004` hydrogen band (1,000 to 2,500 SCF/bbl) and the kernel's unit-level HCU gain flag (4 to 10 percent; dated note 2026-11-28: registered in `PPC-REVIEW-004` and `ADR-0056` by [ADR-0062](../../adr/0062-po12a-signoff-openrouter-endpoint-and-local-hosting.md)).

**Some residuals are zero by construction.** In runtime mode the HCU sizes its acid gas stream from the stoichiometric H2S, so the HCU sulfur residual is always zero. The FCC distributes sulfur by fixed fractions that sum to one. The CDU sulfur residual and all mass residuals are real tests.

**The zero double allocation flag does not include the HCU draw.** The snapshot calls the hydrogen header balance with no HCU request, so `hcu_allocated_t_per_day` is 0.0 in every mode. The flag compares only the diesel hydrotreater draw and header loss against supply. The HCU then takes the remaining headroom as a feed cap. Table 4.2 shows that the property holds. The flag as computed does not prove it.

**The HCU binding constraint label names the smallest cap, not an active limit.** In the nominal mode and in two holdout modes the HCU processes all requested feed, so no cap limits it. The label still reads `shared_h2_cap` or `mechanical_cap`. In the UC-1 and UC-2 modes a cap does limit feed, and the kernel sends 4,491 and 10,279 bbl/day of VGO to `TK-201`. That tank has 60,000 bbl of free working volume at its initial level. It fills in about 13 days and 6 days. Those two snapshots are not sustainable steady states.

**The product release gates use fixed inputs.** The ULSD gate and the BOB gate take hard-coded qualities that are the same in every mode. They are not computed from the snapshot streams. The summer RFG BOB case blends 1 percent n-butane at 52 psi into a 5.6 psi base. The Chevron index gives 6.27 psi, which is below the 6.4 psi cap for Houston RFG BOB. This is a synthetic trim example. It shows that `EQ-08` works. It does not show that Refinery A's gasoline pool meets the cap.

**HCU fixture mode does not close sulfur on sour feed.** The benchmark runs the HCU in runtime mode. In fixture mode the acid gas stream is a fixed 1.5/90 share of converted mass. With these feeds that stream is smaller than the stoichiometric H2S in four of the five modes. The HCU sulfur residual is then -6.3 to -19.3 t/day. Fixture mode reproduces the hand fixture in `PPC-REVIEW-002`. It must not be used for sulfur accounting on these crude blends.

**The benchmark gate has gaps.** `unit_and_conservation_gates_pass` reads holdout modes only. It does not compare residuals with the 1e-9 tolerance, does not test FCC yields, and does not test the FCC coke-burn and feed-rate limits. All of those hold in my reproduction except the FCC gas yield in section 4.1. The benchmark computes no plant-wide mass or sulfur balance. It checks each unit separately.

**Training and holdout differ only in operating point.** The benchmark fits nothing to the training modes. The FCC kinetic constants were calibrated to the `ADR-0056` ranges before this benchmark. The holdout label therefore means a different operating point, not a test of a fit.

**Two volume simplifications affect the plant figure.** The diesel hydrotreater converts feed mass to ULSD volume at a fixed 0.840 specific gravity with no yield loss. That favors the plant gain by about half a percent. The snapshot counts HCU unconverted oil as a product, while the stream register routes it to the FCC through `STR-HCU-UCO-FCC`.

## 6. Owner decision required

This section is for Hamid Adesokan. `ADR-0056` `G3-d` and `ADR-0059` keep `PO-12a` sign-off with the owner. No agent or stand-in has signed or may sign it. (Dated note, 2026-11-28: Hamid Adesokan recorded his owner rulings and conditional sign-off in the Sign-off table below and in [ADR-0062](../../adr/0062-po12a-signoff-openrouter-endpoint-and-local-hosting.md).)

### Decision 1. Plant gain criterion

`PO-12a` requires plant C5+ volumetric gain of +4 to +10 percent. The kernel gives -3.48 to -4.98 percent. (Dated note, 2026-11-28: Hamid Adesokan chose option A below, restating `PO-12a` to plant C3+ volumetric gain `+2.5%` to `+4.5%` and registering unit-level HCU C5+ gain `+4%` to `+10%` in [ADR-0062](../../adr/0062-po12a-signoff-openrouter-endpoint-and-local-hosting.md).) The options are:

| Option | Action | Consequence |
|---|---|---|
| A | Restate the `PO-12a` plant criterion on a basis that matches its cited benchmark, and record the change in an ADR. | The kernel stays as merged. The benchmark gains the new measurement and band. `WP-1` exit then depends on that result. |
| B | Keep the C5+ band and return `WP-1` for a flowsheet or parameter change. | The change must reopen ranges that `ADR-0056` `G3-c` locks, or add a unit to the v1 flowsheet in `ADR-0054`. |
| C | Keep the C5+ band and accept the result as a recorded deviation for v1. | `PO-12a` closes with a known failure on its plant criterion. Later work packages inherit it. |

I recommend option A. The unit models conserve mass and give ordinary yields, and section 5.3 shows that the band and its benchmark use different bases. Plant C3+ gain is also below +4 percent, so a change of basis to C3+ alone does not close the criterion. The new basis and band need the owner's choice. (Dated note, 2026-11-28: Hamid Adesokan chose plant C3+ volumetric gain `+2.5%` to `+4.5%` and registered unit-level HCU C5+ gain `+4%` to `+10%` in Section 6 and [ADR-0062](../../adr/0062-po12a-signoff-openrouter-endpoint-and-local-hosting.md).)

### Decision 2. FCC gas yield at the high-severity holdout

FCC gas yield is 22.09 wt% at 532 °C and catalyst-to-oil 7.0. The `ADR-0056` range is 16 to 22 wt%. The owner must choose one of these (dated note, 2026-11-28: Hamid Adesokan chose option 1 in the Sign-off table below and in [ADR-0062](../../adr/0062-po12a-signoff-openrouter-endpoint-and-local-hosting.md)):

1. Accept the result, because the holdout point is at higher severity than the range was written for.
2. Widen the range in an ADR.
3. Return the FCC kinetics for recalibration.

I recommend that the benchmark record and test FCC yields in every case, because `PO-12a` names them.

### Follow-up work that needs no owner decision

A separate pull request can make these changes to the benchmark. None of them changes kernel physics.

1. Pass the HCU hydrogen request to the header balance so that the zero double allocation flag covers the HCU draw.
2. Add FCC yields, the residual tolerance test and a plant-wide mass and sulfur balance to the gate.
3. Report whether a cap limits HCU feed, in addition to the name of the smallest cap.

### Sign-off

| Item | Entry |
|---|---|
| Decision 1 (A, B or C, with the basis and band if A) | Option A — restate `PO-12a` plant gain to plant C3+ volumetric gain `+2.5%` to `+4.5%` and formally register unit-level HCU C5+ gain `+4%` to `+10%` ([ADR-0062](../../adr/0062-po12a-signoff-openrouter-endpoint-and-local-hosting.md)). |
| Decision 2 (1, 2 or 3) | Option 1 — accept `22.09 wt%` FCC gas yield at the `532 °C` / `7.0` CTO holdout point as expected above nominal severity, and add FCC yield checks to the benchmark gate ([ADR-0062](../../adr/0062-po12a-signoff-openrouter-endpoint-and-local-hosting.md)). |
| `PO-12a` disposition (accepted, accepted with conditions, or returned) | Accepted with conditions for v1 synthetic qualification. |
| Conditions | Implement the three non-physics benchmark follow-ups in Section 6 (include HCU H2 draw in header zero-double-allocation check; add FCC yields, `1e-9` residual tolerance test, and plant-wide mass/sulfur balance to the gate; report whether a cap actively limits HCU feed), and update the benchmark gate with the restated `ADR-0062` gain bands per Decision 1 Option A. Note that review evidence is an AI automated technical review rather than a human process-engineering review (Section 2). |
| Signed: Hamid Adesokan, PPC owner | Hamid Adesokan (recorded verbatim in [docs/adr/answers/2026-11-28-owner-po12a-llm-and-hosting-decisions.md](../../adr/answers/2026-11-28-owner-po12a-llm-and-hosting-decisions.md) and [ADR-0062](../../adr/0062-po12a-signoff-openrouter-endpoint-and-local-hosting.md)) |
| Date | `2026-11-28` |

## Appendix A. Evidence file

This is the content of `/tmp/ppc_po12a_benchmark_main.json`. A fresh run of `run_eng_v07_mode_benchmark` at commit `88f5fe4` gives the same content.

```json
{
  "provenance_class": "SYNTHETIC",
  "training_modes": {
    "train_nominal_design_blend": {
      "cdu_mass_residual_t": 3.637978807091713e-12,
      "cdu_sulfur_residual_t": 1.1368683772161603e-13,
      "fcc_mass_residual_t": 1.8189894035458565e-12,
      "fcc_sulfur_residual_t": 0.0,
      "fcc_heat_feasible": true,
      "hcu_mass_residual_t": 0.0,
      "hcu_sulfur_residual_t": 0.0,
      "hcu_acid_gas_covers_h2s": true,
      "h2_no_double_alloc": true,
      "hydraulics_all_feasible": true,
      "hcu_binding_constraint": "shared_h2_cap",
      "hcu_c5_plus_gain_pct": 8.444157948460296,
      "hcu_h2_uptake_scf_per_bbl": 1259.5923908480981,
      "plant_c5_plus_gain_pct": -4.169264753938884,
      "plant_c3_plus_gain_pct": 3.8272536023388426,
      "po12a_hcu_gain_in_4_to_10": true,
      "po12a_hcu_h2_in_1000_to_2500": true,
      "po12a_plant_c5_gain_in_4_to_10": false
    },
    "train_uc1_compressor_derate_75pct": {
      "cdu_mass_residual_t": 3.637978807091713e-12,
      "cdu_sulfur_residual_t": 1.1368683772161603e-13,
      "fcc_mass_residual_t": 1.8189894035458565e-12,
      "fcc_sulfur_residual_t": 0.0,
      "fcc_heat_feasible": true,
      "hcu_mass_residual_t": 0.0,
      "hcu_sulfur_residual_t": 0.0,
      "hcu_acid_gas_covers_h2s": true,
      "h2_no_double_alloc": true,
      "hydraulics_all_feasible": true,
      "hcu_binding_constraint": "compressor_circulation_cap",
      "hcu_c5_plus_gain_pct": 8.444157948460319,
      "hcu_h2_uptake_scf_per_bbl": 1259.5923908480984,
      "plant_c5_plus_gain_pct": -4.379939258894716,
      "plant_c3_plus_gain_pct": 3.4670441723271495,
      "po12a_hcu_gain_in_4_to_10": true,
      "po12a_hcu_h2_in_1000_to_2500": true,
      "po12a_plant_c5_gain_in_4_to_10": false
    }
  },
  "holdout_modes": {
    "holdout_uc4_heavy_sour_swing": {
      "cdu_mass_residual_t": 0.0,
      "cdu_sulfur_residual_t": 5.684341886080802e-14,
      "fcc_mass_residual_t": 1.3642420526593924e-12,
      "fcc_sulfur_residual_t": 0.0,
      "fcc_heat_feasible": true,
      "hcu_mass_residual_t": 9.094947017729282e-13,
      "hcu_sulfur_residual_t": 0.0,
      "hcu_acid_gas_covers_h2s": true,
      "h2_no_double_alloc": true,
      "hydraulics_all_feasible": true,
      "hcu_binding_constraint": "mechanical_cap",
      "hcu_c5_plus_gain_pct": 8.189505624476023,
      "hcu_h2_uptake_scf_per_bbl": 1259.2304492505891,
      "plant_c5_plus_gain_pct": -3.48388767320178,
      "plant_c3_plus_gain_pct": 3.9902676134570214,
      "po12a_hcu_gain_in_4_to_10": true,
      "po12a_hcu_h2_in_1000_to_2500": true,
      "po12a_plant_c5_gain_in_4_to_10": false
    },
    "holdout_light_sweet_high_severity_fcc": {
      "cdu_mass_residual_t": 0.0,
      "cdu_sulfur_residual_t": 0.0,
      "fcc_mass_residual_t": 4.547473508864641e-13,
      "fcc_sulfur_residual_t": 0.0,
      "fcc_heat_feasible": true,
      "hcu_mass_residual_t": 0.0,
      "hcu_sulfur_residual_t": 0.0,
      "hcu_acid_gas_covers_h2s": true,
      "h2_no_double_alloc": true,
      "hydraulics_all_feasible": true,
      "hcu_binding_constraint": "mechanical_cap",
      "hcu_c5_plus_gain_pct": 8.636357095483582,
      "hcu_h2_uptake_scf_per_bbl": 1258.0075223381214,
      "plant_c5_plus_gain_pct": -4.980847098894281,
      "plant_c3_plus_gain_pct": 3.5681865572172455,
      "po12a_hcu_gain_in_4_to_10": true,
      "po12a_hcu_h2_in_1000_to_2500": true,
      "po12a_plant_c5_gain_in_4_to_10": false
    },
    "holdout_uc2_smr_h2_constrained": {
      "cdu_mass_residual_t": 3.637978807091713e-12,
      "cdu_sulfur_residual_t": 1.1368683772161603e-13,
      "fcc_mass_residual_t": 1.8189894035458565e-12,
      "fcc_sulfur_residual_t": 0.0,
      "fcc_heat_feasible": true,
      "hcu_mass_residual_t": 0.0,
      "hcu_sulfur_residual_t": 0.0,
      "hcu_acid_gas_covers_h2s": true,
      "h2_no_double_alloc": true,
      "hydraulics_all_feasible": true,
      "hcu_binding_constraint": "shared_h2_cap",
      "hcu_c5_plus_gain_pct": 8.444157948460296,
      "hcu_h2_uptake_scf_per_bbl": 1259.5923908480984,
      "plant_c5_plus_gain_pct": -4.65148304802222,
      "plant_c3_plus_gain_pct": 3.0027609714464942,
      "po12a_hcu_gain_in_4_to_10": true,
      "po12a_hcu_h2_in_1000_to_2500": true,
      "po12a_plant_c5_gain_in_4_to_10": false
    }
  },
  "max_absolute_residual_t_per_day": 3.637978807091713e-12,
  "unit_and_conservation_gates_pass": true,
  "po12a_plant_c5_gain_band_pass": false,
  "all_holdout_gates_pass": false
}
```
