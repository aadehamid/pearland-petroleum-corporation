# PPC-REVIEW-002 — Governing Refinery Equations, Control Volumes, and Shift Trace

| Document control | Value |
|---|---|
| Artifact ID | `PPC-REVIEW-002` |
| Version / date | `1.1.0` / `2026-11-26` (revised after external Codex and Claude reviews) |
| Governing ADRs | [ADR-0040](../../adr/0040-staged-mechanistic-refinery-model-and-closed-flowsheet.md), [ADR-0043](../../adr/0043-refinery-v1-unit-physics-and-hybrid-clock.md), [ADR-0049](../../adr/0049-v1-business-use-cases.md) |
| Linked specifications | [PPC-ENG-001](../02-industrial-engineering/PPC-ENG-001_Physical_and_Numerical_Engineering.md), [PPC-WORLD-001](../01-enterprise-world/PPC-WORLD-001_Canonical_Enterprise_World.md), [PPC-WORLD-002](../01-enterprise-world/PPC-WORLD-002_Simulation_Time_Replay_and_Branches.md), [PPC-VERIFY-001](../07-scenarios-verification/PPC-VERIFY-001_Verification_and_Release_Qualification.md), [PPC-SCENARIO-001](../07-scenarios-verification/PPC-SCENARIO-001_Golden_Enterprise_Scenarios.md) |
| Scope | Documents and paper mathematics only. No executable simulator is implemented, calibrated, or qualified here. |

## 1. End-to-end shift trace and flowsheet closure across Refinery A v1

Refinery A v1 ([ADR-0040](../../adr/0040-staged-mechanistic-refinery-model-and-closed-flowsheet.md)) models one fictional Gulf Coast refinery on a hybrid 1-minute process and exact-event-split clock ([ADR-0043](../../adr/0043-refinery-v1-unit-physics-and-hybrid-clock.md)) to support use cases `UC-1` through `UC-6` ([ADR-0049](../../adr/0049-v1-business-use-cases.md)).

### Critical flowsheet closure finding requiring WP-0 owner disposition (Proposed Amendment to `ADR-0040`)

Independent external refining review proved two physical-feasibility gaps in the original `ADR-0040` bounded-interface list (`NHT/DHT`, `SRU`, `steam/power`):

1. **Hydrogen production closure:** A refinery running a hydrocracker and distillate hydrotreater needs a declared hydrogen source control volume. Without a **Steam Methane Reformer (SMR)** or an explicit **purchased pipeline hydrogen** boundary import, the plant-wide hydrogen balance (`EQ-07`) has no producer.
2. **Gasoline octane and Tier 3 sulfur closure:** FCC naphtha from unhydrotreated VGO carries `100` to `1,500 ppmw` sulfur, which cannot meet EPA Tier 3 (`<= 10 ppmw` refinery annual average, `<= 80 ppmw` cap, 40 CFR 1090) without an **FCC gasoline selective HDS post-treater** (or VGO pretreater). Furthermore, without a **Catalytic Reformer** (or purchased high-octane reformate/alkylate) and terminal **10 vol% ethanol** blending, the gasoline pool cannot hit finished `87 / 91 (R+M)/2` grades or provide an outlet for hydrotreated heavy straight-run naphtha.

Because `ADR-0040` is an owner-approved decision, this review does **not** silently alter it. Instead, `WP-0` presents two physically closed options for owner sign-off before Phase 0:

- **Option A (Recommended):** Amend `ADR-0040` to include **SMR** (natural gas feed → $\text{H}_2$, fuel gas, $\text{CO}_2$), **Catalytic Reformer** (hydrotreated heavy naphtha → reformate + byproduct $\text{H}_2$), and **FCC Naphtha Selective HDS** as declared bounded interface units alongside NHT/DHT, SRU, and steam/power, plus a **terminal 10 vol% ethanol** blend boundary.
- **Option B (Boundary-import alternative):** Retain only NHT/DHT, SRU, and steam/power inside Refinery A v1, export heavy naphtha, and declare **purchased pipeline $\text{H}_2$, purchased reformate/alkylate, and terminal ethanol** as explicit external boundary streams.

In **both** options, **FCC Light Cycle Oil (LCO)**, straight-run kerosene, and atmospheric gas oil (AGO) **must route through the Diesel Hydrotreater (DHT)** before ULSD blending. Unhydrotreated LCO (`0.2` to `2.0 wt%` sulfur, cetane `20` to `25`) never enters ULSD blending directly.

```mermaid
flowchart LR
    CR["1. Crude Receipt & LIMS\n(Segregated Hold Tank TK-101H)"] --> CT["2. Crude Tank Farm\n& Charge Pumps"]
    CT --> CDU["3. CDU + VDU\n(TBP Cut-Point Split)"]
    CDU -->|"VGO"| FCC["4A. FCC Unit\n(Lee 4-Lump + Heat Bal.)"]
    CDU -->|"VGO"| HCU["4B. Hydrocracker\n(Polytropic Comp. + H2/Quench)"]
    CDU -->|"Kero / AGO"| DHT["5A. DHT Interface\n(Feed-Dependent S, Cetane, H2)"]
    FCC -->|"LCO"| DHT
    FCC -->|"FCC Naphtha"| FDS["5B. FCC Selective HDS\n(or Boundary Spec Route)"]
    CDU -->|"Heavy Naphtha"| REF["5C. Reformer / Import Boundary\n(Pending ADR-0040 WP-0 Choice)"]
    SMR["6. H2 Supply Boundary (SMR +\nReformer or Pipeline H2) & Utilities"] <--> HCU
    SMR <--> DHT
    SMR <--> FDS
    DHT -->|"Hydrotreated Dist."| BL["7. Product Blending\n(BOB 84/88 + ULSD) & Quality Hold"]
    HCU -->|"ULSD, Naphtha, LPG"| BL
    FDS -->|"Treated FCC Naphtha"| BL
    REF -->|"Reformate / Purchased Octane"| BL
    BL --> FT["8. Finished Tankage, Terminal E10\n& Pipeline / Truck / Marine Dispatch"]
```

### Physical boundaries and explicit v1 exclusions

| Stage / boundary | v1 fidelity class | Decisions supported | Behaviors outside v1 scope |
|---|---|---|---|
| Crude receipt & LIMS assay | Exact custody mass, standard volume, revisioned assay lot, segregated hold tank `TK-101H` (or pre-discharge hold) | `UC-2` crude rejection, `UC-4` crude-slate swing, `UC-3` backcasting | Online NIR analyzer dynamics; marine unloading vapor flash |
| Tankage & transfer headers | Transient mass and component balance with exact intra-step bound crossings; Darcy–Weisbach and pump head curves | `UC-1`, `UC-2`, `UC-5` tank bounds, overfill prevention, pump-swap routing | Tank thermal stratification; water-bottom emulsification; water hammer |
| CDU + VDU | Assay TBP/D86 cut-point separation with zero-sum overlap/tail shift, Watson $K_w$, API gravity, cut sulfur | `UC-4` max-distillate vs max-gasoline cut swing; `UC-2` crude quality impact | Tray-by-tray rigorous MESH flash; pumparound fouling dynamics |
| Hydrocracker (HCU) + recycle compressor | Polytropic compressor head curve coupled to recycle $\text{H}_2$ mass flow, inter-bed quench duty, $P_{\text{H2}}$ purity balance, lumped conversion, and net $\text{H}_2$ stoichiometry | `UC-1` compressor derate; `UC-3` and `UC-4` ULSD yield and $\text{H}_2$ contention | Multi-bed axial temperature profiles; multi-year catalyst deactivation |
| FCC | Lee et al. (1989) 4-lump kinetics with inlet CCR split + reactor–regenerator coke/heat balance bounded by air-blower coke burn | `UC-4` gasoline vs LCO swing; `UC-3` LP calibration vs actual conversion | Riser two-phase slip hydrodynamics; flue-gas scrubber chemistry |
| DHT bounded interface | Feed-dependent bounded hydrotreater: $\text{H}_2$ uptake, sulfur removal, and cetane uplift depend linearly on LCO vs straight-run distillate feed mass fraction | `UC-4` max-distillate LCO routing and $\text{H}_2$ demand shift | Reactor bed radial flow maldistribution |
| H2 supply, Reformer/Octane, FCC HDS, SRU, Utilities | Declared bounded mass, sulfur, $\text{H}_2$, and utility interfaces (Option A vs Option B locked in WP-0) | Closes sitewide mass, sulfur, $\text{H}_2$, octane, and variable utility cost | Internal Claus converter thermodynamics; steam pressure waves |
| Blending & quality release | Exact mass sulfur and density; Chevron RVP, Ethyl RT-70 octane, Wickey–Chittenden flash, Hu–Burns/Riazi cloud, ASTM D975 cetane; refinery BOB gate + terminal E10 ethanol | `UC-1`, `UC-2`, `UC-4`, `UC-5` spec compliance, giveaway, quality hold | Inline blend-header analyzer dead-time PID tuning |

## 2. Primary-sourced governing equation register

SI mass (`kg` or metric tonnes `t`) is the sole conservation basis. Standard liquid volumes (`bbl` at `60 °F / 15.56 °C`, `14.696 psia`, API MPMS Chapter 11.1) convert to mass only through a declared density $\rho_{\text{ref}}$ at compatible reference conditions. Barrels of different densities are never summed as conserved mass.

### EQ-01 — Reference volume, density, and API gravity conversion

- **Class:** Physical definition and unit conversion (exact).
- **Primary source:** API MPMS Chapter 11.1 (2004/2019); M. R. Riazi, *Characterization and Properties of Petroleum Fractions*, ASTM Manual 50 (2005), Ch. 2, Eq. 2.4.
- **Equations:**
  $$\text{SG}_{60/60} = \frac{141.5}{\text{API} + 131.5}, \qquad \rho_{\text{ref}} = \text{SG}_{60/60} \cdot \rho_{w,60^\circ\text{F}}, \qquad m = V_{\text{std}} \cdot c_{\text{bbl}} \cdot \rho_{\text{ref}}$$
- **Constants & units:** $\rho_{w,60^\circ\text{F}} = 999.016\text{ kg/m}^3$; $c_{\text{bbl}} = 0.158987294928\text{ m}^3/\text{bbl}$; $V_{\text{std}}$ in standard bbl; $m$ in kg.
- **Valid range & rules:** Liquid phase at `60 °F`, $10 \le \text{API} \le 90$. Observed volumes at $T \neq 60^\circ\text{F}$ require an API MPMS 11.1 Volume Correction Factor ($\text{VCF}$) before mass conversion. Missing density returns `INSUFFICIENT_INPUT`. Pin reference densities as exact rational numbers for deterministic arithmetic oracles (`WORLD-002 §7`).

### EQ-02 — Transient control-volume mass, component, and transit conservation

- **Class:** Conservation law (exact).
- **Primary source:** R. H. Perry & D. W. Green, *Perry's Chemical Engineers' Handbook*, 9th ed. (McGraw-Hill, 2019), Section 4.
- **Equations:**
  $$M_k(t_1) = M_k(t_0) + \int_{t_0}^{t_1}\!\left(\sum_{i \in \text{in}(k)} \dot{m}_i - \sum_{j \in \text{out}(k)} \dot{m}_j - \dot{m}_{\text{loss},k}\right)dt, \qquad M_{k,\min} \le M_k(t) \le M_{k,\max}\;\; \forall t \in [t_0, t_1]$$
  $$\frac{d(M_k w_{k,c})}{dt} = \sum_{i \in \text{in}(k)} \dot{m}_i w_{i,c} - \sum_{j \in \text{out}(k)} \dot{m}_j w_{k,c} - \dot{m}_{\text{loss},k} w_{k,c}, \qquad M_{\text{transit},e}(t_1) = M_{\text{transit},e}(t_0) + \int_{t_0}^{t_1} (\dot{m}_{\text{send},e} - \dot{m}_{\text{recv},e})\,dt \ge 0$$
- **Update rule:** Rates stay piecewise constant across each 1-minute step $[t_0, t_0+\Delta t)$ unless an intra-step boundary crossing $t^* = t_0 + (M_{\text{bound}} - M_k(t_0)) / \dot{M}_{\text{net}}$ occurs inside $(t_0, t_0+\Delta t)$. When a crossing occurs, the engine splits the step at $t^*$ and applies the declared operating rule (throttle, divert, or block). End-of-step clipping is forbidden (`PO-01`).
- **Element balances & residual tolerance:** Total sulfur (including $\text{H}_2\text{S}$ to SRU) and total hydrogen (makeup, recycle, chemical uptake, dissolved gas, purge) obey exact conservation. Mass residual tolerance is $|r_M| \le 10^{-9}\cdot\max(1\text{ kg}, M_{\text{throughput}})$ in floating-point execution and exactly `0` in rational fixtures.

### EQ-03 — Pipe transfer hydraulics and pump head bounds

- **Class:** Mechanical energy balance (semi-empirical).
- **Primary source:** *Perry's Chemical Engineers' Handbook*, 9th ed. (2019), Section 6 (Darcy–Weisbach, Colebrook–White, centrifugal pump affinity laws); S. W. Churchill, *Chem. Eng.* 84(24), 91–92 (1977) (continuous all-regime friction factor); Hydraulic Institute ANSI/HI 9.6.7 (viscous-liquid pump correction).
- **Equations:**
  $$h_f = \left(f \frac{L}{D} + \sum K_{\text{fit}}\right)\frac{v^2}{2g}, \qquad H_{\text{pump}}(Q, N, \mu) = C_H(\mu)\left[\left(\frac{N}{N_0}\right)^2 H_0 - c_p Q^2\right] \ge \Delta z + \frac{P_{\text{dest}} - P_{\text{src}}}{\rho g} + h_f(Q)$$
- **Friction regime coverage:** Use $f = 64/\text{Re}$ for laminar flow ($\text{Re} \le 2100$), Colebrook–White for turbulent flow ($\text{Re} \ge 4000$), and the smooth Churchill (1977) interpolation across the transition band $2100 < \text{Re} < 4000$ so no Reynolds gap exists. Apply ANSI/HI 9.6.7 viscosity derating factor $C_H(\mu) \le 1$ for heavy crude or vacuum-residue pumping.

### EQ-04 — Crude assay characterization and CDU/VDU cut-point separation

- **Class:** Empirical petroleum characterization plus exact mass-fraction separation.
- **Primary source:** Riazi, ASTM Manual 50 (2005), Ch. 2–3 (Watson $K_w$, ASTM D2892 TBP ↔ ASTM D86); J. H. Gary, G. E. Handwerk, & M. J. Kaiser, *Petroleum Refining: Technology and Economics*, 5th ed. (CRC Press, 2007), Ch. 3–4.
- **Equations:**
  $$K_w = \frac{T_b^{1/3}}{\text{SG}_{60/60}}\;\;(T_b\text{ in }^\circ\text{R}), \qquad y_{c,j}(T_{j-1}^{\text{cut}}, T_j^{\text{cut}}) = F_c^{\text{TBP}}(T_j^{\text{cut}}) - F_c^{\text{TBP}}(T_{j-1}^{\text{cut}}) + \delta_{\text{overlap},j}$$
  $$\sum_{j=1}^{J} \delta_{\text{overlap},j} = 0, \qquad \sum_{j=1}^{J} y_{c,j} + y_{c,\text{loss}} = 1, \qquad \dot{m}_j = \sum_c \dot{m}_{\text{crude},c}\, y_{c,j}, \qquad w_{j,S} = \frac{\sum_c \dot{m}_{\text{crude},c}\, y_{c,j}\, w_{c,j,S}}{\dot{m}_j}$$
- **Zero-sum overlap rule:** Adjacent-cut fractionation overlap shifts mass only between neighboring cuts so $\sum_j \delta_{\text{overlap},j} = 0$ identically, while broadening cut boiling tails (T90/T95 and flash point). Cut-point shifts stay within $\pm 15^\circ\text{C}$ of nominal column design.

### EQ-05 — Hydrocracker recycle-gas compressor, quench, $P_{\text{H2}}$, and lumped conversion

- **Class:** Real-gas polytropic thermodynamics (GPSA) plus lumped hydrocracking kinetics, quench thermal bound, and mass-basis stoichiometry.
- **Primary source:** *GPSA Engineering Data Book*, 14th ed. (2016), Section 13 (polytropic head and exponent); Gary, Handwerk, & Kaiser, 5th ed. (2007), Ch. 8; R. E. Maples, *Petroleum Refinery Process Economics*, 2nd ed. (PennWell, 2000), Ch. 11.
- **Equations (all feed bounds strictly on SI mass-rate basis `kg/s` or `t/day`):**
  1. *Polytropic head and driver-limited recycle mass flow (SI):*
     $$\frac{n}{n-1} = \left(\frac{k}{k-1}\right)\eta_p, \qquad H_p = \frac{Z_{\text{avg}} R T_1}{MW_{\text{gas}}} \left(\frac{n}{n-1}\right)\!\left[\left(\frac{P_2}{P_1}\right)^{\frac{n-1}{n}} - 1\right], \qquad \dot{m}_{\text{rec,max}}(s_{\text{comp}}) = \frac{\eta_p \eta_m W_{\text{driver,max}}(s_{\text{comp}})}{H_p}$$
  2. *Dimensionally consistent mass-basis H2-to-oil conversion:*
     Given volumetric standard minimum $\text{H}_2$-to-oil ratio $R_{\min,\text{vol}}$ (in $\text{SCF }\text{H}_2/\text{bbl}$ at `60 °F, 14.696 psia` where $V_{m,\text{std}} = 379.48\text{ SCF/lbmol}$ and $M_{\text{H2}} = 2.01588\text{ lb/lbmol}$, or $\text{Nm}^3/\text{m}^3$ at `0 °C, 1 atm`), convert explicitly to a dimensionless **mass-per-mass ratio** $R_{\min,\text{mass}}$ (`kg pure H2 / kg VGO feed`) using feed reference density $\rho_{\text{feed}}$ (`EQ-01`):
     $$R_{\min,\text{mass}} = \frac{R_{\min,\text{vol}} \cdot (M_{\text{H2}} / V_{m,\text{std}}) \cdot 0.45359237}{\rho_{\text{feed}} \cdot c_{\text{bbl}}}$$
     With recycle-gas $\text{H}_2$ mass fraction $w_{\text{H2,rec}}$, the circulation-bounded feed mass rate is $\dot{m}_{\text{HCU,circ}}^{\max} = (w_{\text{H2,rec}}\,\dot{m}_{\text{rec,max}}) / R_{\min,\text{mass}}$ (exact units: `kg/s`).
  3. *Lumped inter-bed quench thermal bound:*
     Because hydrocracking is strongly exothermic (typically $70$ to $130^\circ\text{C}$ total adiabatic temperature rise at $1{,}200\text{ SCF/bbl}$ uptake), reduced recycle gas directly limits quench cooling:
     $$\dot{m}_{\text{rec,quench}}\, C_{p,\text{gas}} (T_{\text{bed,max}} - T_{\text{quench}}) \ge \dot{m}_{\text{feed}}\,\xi\,(-\Delta h_{\text{rxn}}) - \dot{m}_{\text{feed}}\, C_{p,\text{oil}}\,\Delta T_{\text{bed,allow}}$$
     giving a separate quench-bounded feed mass rate $\dot{m}_{\text{HCU,quench}}^{\max}(s_{\text{comp}})$.
  4. *Recycle loop $\text{H}_2$ partial-pressure closure:*
     $$P_{\text{H2}} = P_{\text{loop}} \cdot y_{\text{H2,rec}}, \qquad y_{\text{H2,rec}} = \frac{\dot{n}_{\text{H2,makeup}} - \dot{n}_{\text{H2,chem}} - \dot{n}_{\text{H2,diss}}}{\dot{n}_{\text{purge,total}}}$$
     linking makeup purity, chemical uptake, dissolved losses, and purge rate directly to reactor partial pressure $P_{\text{H2}}$.
  5. *Unified mass-rate feed cap, lumped conversion, and net H2 draw:*
     $$\dot{m}_{\text{HCU,feed}}^{\max} = \min\!\left(\dot{m}_{\text{mech,max}},\; \frac{w_{\text{H2,rec}}\,\dot{m}_{\text{rec,max}}(s_{\text{comp}})}{R_{\min,\text{mass}}},\; \dot{m}_{\text{HCU,quench}}^{\max}(s_{\text{comp}}),\; \frac{\dot{m}_{\text{H2,alloc}}}{c_{\text{H2,net}}(\xi)},\; \dot{m}_{\text{feed,avail}},\; \dot{m}_{\text{downstream,cap}}\right)$$
     $$\xi = 1 - \exp\!\left(-\frac{k_0 \exp(-E_a / R T_{\text{rxr}})\, P_{\text{H2}}^{\alpha}}{\text{LHSV}}\right), \qquad c_{\text{H2,net}}(\xi) = c_{\text{H2,chem}}(\xi) + c_{\text{H2,purge+diss}}$$
     $$\sum_{p \in \text{liquids}} \dot{m}_p + \dot{m}_{\text{drygas+LPG}} + \dot{m}_{\text{H2S+NH3}} = \dot{m}_{\text{feed}} + \dot{m}_{\text{H2,chem}}$$
- **Calibration status:** Valid for $P_{\text{H2}} \in [80, 180]\text{ bar}$, $T_{\text{rxr}} \in [360, 430]^\circ\text{C}$, $\xi \in [0.40, 0.95]$. Because reducing feed at fixed $T_{\text{rxr}}$ lowers LHSV and raises $\xi$ (increasing $c_{\text{H2,chem}}$), the solver iterates $(\dot{m}_{\text{feed}}, \xi)$ unless reactor temperature is adjusted to hold constant conversion. All synthetic kinetic parameters remain subject to process-engineer sign-off (`PPC-REVIEW-004 §4`); Scenario A's `30,000 bbl/day` cap is labeled `SCENARIO_ASSUMPTION` (assuming the unit sits at $R_{\min}$ at 40,000 bbl/day with quench and shared $\text{H}_2$ non-binding).

### EQ-06 — FCC 4-lump kinetics and reactor–regenerator heat/coke balance

- **Class:** Lumped catalytic kinetics plus macroscopic energy balance.
- **Primary sources:** L.-S. Lee, Y.-W. Chen, T.-N. Huang, & W.-Y. Chen, *Can. J. Chem. Eng.* 67(4), 615–619 (1989) (4-lump FCC kinetic model with separate coke lump, extending the 3-lump model of V. W. Weekman Jr. & D. M. Nace, *AIChE J.* 16(3), 397–404 (1970)); Gary, Handwerk, & Kaiser, 5th ed. (2007), Ch. 6.
- **Equations (strictly mass-conservative inlet CCR split):**
  1. *Initial condition at riser inlet ($\tau = 0$):* Partition feed Conradson Carbon Residue (`CCR`) additive coke strictly into initial coke precursor so the sum of mass fractions equals `1` at $\tau = 0$:
     $$y_D(0) = f_{\text{add}}\, w_{\text{CCR,feed}} \quad (f_{\text{add}} \in [0.5, 1.0]), \qquad y_A(0) = 1 - y_D(0), \qquad y_B(0) = 0, \qquad y_C(0) = 0$$
  2. *Dimensionless riser kinetic ODEs ($\tau \in [0, 1]$, catalyst deactivation $\phi(\tau) = \exp(-\alpha_d \tau)$, rate constants $k_i$ dimensionless on $\tau$):*
     $$\frac{dy_A}{d\tau} = -\phi(k_1 + k_3 + k_4)\,y_A^2, \qquad \frac{dy_B}{d\tau} = \phi(k_1 y_A^2 - k_2 y_B)$$
     $$\frac{dy_C}{d\tau} = \phi(k_3 y_A^2 + \beta_{BC} k_2 y_B), \qquad \frac{dy_D}{d\tau} = \phi(k_4 y_A^2 + (1 - \beta_{BC}) k_2 y_B)$$
     Summing all four derivatives yields $\frac{d}{d\tau}(y_A + y_B + y_C + y_D) = 0$ **identically** for every $\tau \ge 0$ and every positive feed CCR.
  3. *Reactor–regenerator heat balance and air-blower coke-burn ceiling:*
     $$\dot{m}_{\text{cat}} C_{p,\text{cat}}(T_{\text{regen}} - T_{\text{rxr}}) = \dot{m}_{\text{feed}}\!\left[\Delta h_{\text{vap+sens}} + \Delta h_{\text{rxn}}(y_A, y_B)\right] + Q_{\text{loss,rxr}}$$
     $$\dot{m}_{\text{coke}}\Delta h_{\text{comb}} = \dot{m}_{\text{cat}} C_{p,\text{cat}}(T_{\text{regen}} - T_{\text{spent}}) + \dot{m}_{\text{flue}}\bar{C}_{p,\text{flue}}(T_{\text{regen}} - T_{\text{air}}) + Q_{\text{loss,regen}}$$
     $$\dot{m}_{\text{coke}} = \dot{m}_{\text{feed}}\,y_D(1) \le \dot{m}_{\text{coke,max}}(\dot{m}_{\text{air,max}}), \qquad T_{\text{regen}} \le T_{\text{regen,max}}$$
- **Valid range:** $T_{\text{rxr}} \in [495, 550]^\circ\text{C}$, $T_{\text{regen}} \in [670, 740]^\circ\text{C}$, cat-to-oil ratio $\in [4, 9]$.

### EQ-07 — Shared hydrogen and utility header network balance

- **Class:** Exact network conservation law plus feed-dependent bounded interface rules.
- **Primary source:** *Perry's Chemical Engineers' Handbook*, 9th ed. (2019), Section 4; Gary, Handwerk, & Kaiser, 5th ed. (2007), Ch. 16.
- **Equations:**
  $$\sum_{p \in \text{H2 prod}} \dot{m}_{\text{H2},p}(t) - \sum_{u \in \text{H2 users}} \dot{m}_{\text{H2,net},u}(t) - \dot{m}_{\text{H2,loss}}(t) = \frac{dM_{\text{H2,header}}}{dt}$$
  $$\dot{m}_{\text{H2,alloc},u} \le \max\!\left(0,\; \dot{m}_{\text{H2,supply}} - \dot{m}_{\text{H2,loss}} - \sum_{v \neq u} \dot{m}_{\text{H2,committed},v}\right)$$
- **Feed-dependent DHT interface closure:** For the DHT receiving straight-run distillate mass fraction $w_{\text{SR}}$ and FCC LCO mass fraction $w_{\text{LCO}}$ ($w_{\text{SR}} + w_{\text{LCO}} = 1$), net DHT $\text{H}_2$ uptake scales linearly with feed blend: $c_{\text{H2,DHT}} = w_{\text{SR}}\,c_{\text{H2,SR}} + w_{\text{LCO}}\,c_{\text{H2,LCO}}$, and treated diesel cetane/sulfur reflects the feed LCO penalty. Same single-header balance governs fuel gas, steam, power, and cooling water. Internal unit recycle cancels within its accounting boundary (`PO-04`).

### EQ-08 — Product blending properties and fuel specification gates

- **Class:** Exact mass-basis mixing (sulfur, density) plus primary empirical blending indices.
- **Primary sources:**
  - *Sulfur & density:* Exact mass conservation (ASTM D4294; EPA 40 CFR 1090 Tier 3; API MPMS).
  - *RVP:* Chevron VPBI (`1.25` exponent), Gary, Handwerk, & Kaiser, 5th ed. (2007), Ch. 13.
  - *RON / MON:* W. C. Healy Jr., C. W. Maassen, & R. T. Peterson, *Proc. API Div. Refining* 39(III), 132–143 (1959) (Ethyl RT-70).
  - *Flash point:* R. O. Wickey & D. H. Chittenden, *Hydrocarbon Processing* 42(6), 157–158 (1963).
  - *Cloud point:* J. Hu & A. M. Burns, *Hydrocarbon Processing* 49(11), 213–216 (1970); Riazi, ASTM Manual 50 (2005), Ch. 10.
  - *Diesel cetane:* ASTM D975 (ASTM D613 Cetane Number $\ge 40$, or alternative ASTM D4737 Cetane Index $\ge 40$ paired with max 35 vol% aromatics).
- **Equations:**
  1. *Mass-basis sulfur and ideal-volume density:*
     $$w_{S,\text{blend}} = \frac{\sum_i m_i w_{S,i}}{\sum_i m_i}, \qquad \rho_{\text{blend}} = \frac{\sum_i m_i}{\sum_i (m_i / \rho_i)}$$
  2. *Chevron RVP blending index (volume fractions $x_{v,i}$, psi at `100 °F`):*
     $$\text{RVP}_{\text{blend}} = \left[\sum_i x_{v,i}\,(\text{RVP}_i)^{1.25}\right]^{0.8}$$
  3. *Ethyl RT-70 nonlinear RON and MON interaction model (verify exact regression constants against Healy et al. 1959 primary tables before WP-1 coding):*
     $$\text{RON}_{\text{blend}} = \bar{r} + a_1(\overline{rs} - \bar{r}\bar{s}) + a_2(\overline{O^2} - \bar{O}^2)$$
     $$\text{MON}_{\text{blend}} = \bar{m} + b_1(\overline{ms} - \bar{m}\bar{s}) + b_2(\overline{O^2} - \bar{O}^2) + b_3\frac{\overline{A^2} - \bar{A}^2}{100}$$
     where $s_i = \text{RON}_i - \text{MON}_i$ (sensitivity), $O_i$ is vol% olefins, $A_i$ is vol% aromatics, and published reference values are $a_1 \approx 0.03224$, $a_2 \approx 0.00101$.
  4. *Wickey–Chittenden flash point ($T_{\text{fp},i}$ in °F) and Hu–Burns / Riazi cloud point ($T_{\text{cp},i}$ in K):*
     $$\log_{10}(I_{\text{fp},i}) = -6.1188 + \frac{4345.2}{T_{\text{fp},i} + 383}, \quad I_{\text{fp,blend}} = \sum_i x_{v,i}\, I_{\text{fp},i}, \qquad T_{\text{cp,blend}} = \left(\sum_i x_{v,i}\, T_{\text{cp},i}^{20}\right)^{0.05}$$
- **Release specification gates:**
  - **ULSD (ASTM D975 S15):** sulfur $\le 15\text{ ppmw}$, flash point $\ge 52^\circ\text{C}$, ASTM D613 Cetane Number $\ge 40$ (or D4737 Cetane Index $\ge 40$ with aromatics $\le 35\text{ vol}\%$), cloud point $\le T_{\text{seasonal}}$.
  - **Gasoline blendstock at refinery gate (RBOB / CBOB before 10 vol% ethanol):** sub-octane blendstock `(R+M)/2 >= 84.0` (regular BOB) or `>= 88.0` (premium BOB), seasonal BOB RVP cap, Tier 3 sulfur `<= 10 ppmw` annual refinery average and `<= 80 ppmw` per-gallon cap (40 CFR 1090). Terminal splash-blending with `10 vol%` denatured ethanol (`E10`, effective blending octane `~113 (R+M)/2`) raises finished retail grades to `87.0` (regular) and `91.0` (premium).

### EQ-09 — Economic objective, planning LP separation, and fair backcasting

- **Class:** Commercial accounting identity plus deliberately separated Planning LP (`UC-3`, `ADR-0048`).
- **Primary source:** Maples, *Petroleum Refinery Process Economics*, 2nd ed. (2000); `PPC-005`, `PPC-008`, `PPC-ANALYTICS-001`.
- **Equations:**
  $$\Pi = \sum_p P_p V_p - \sum_c P_c V_c - C_{\text{var,util}} - C_{\text{logistics}} - C_{\text{penalty/demurrage}}$$
  $$\Delta \Pi_{\text{total}} = \underbrace{(\Pi_{\text{recal-plan}} - \Pi_{\text{orig-plan}})}_{\text{LP calibration effect}} + \underbrace{(\Pi_{\text{feasible-alt}} - \Pi_{\text{recal-plan}})}_{\text{decision-time opportunity}} + \underbrace{(\Pi_{\text{actual}} - \Pi_{\text{feasible-alt}})}_{\text{execution and exogenous residual}}$$
- **Planning LP versus World Kernel separation (fixing `UC-3` measurability):** The **Planning LP** (Pyomo + HiGHS) is a deliberately reduced linear model using base-plus-delta unit yield vectors, linearized blend indices, and vintage-pinned lagged assays. The **Canonical World Kernel** (`EQ-01`–`EQ-08`) uses the full nonlinear/mechanistic physics. Keeping the planning LP structurally distinct from the world kernel guarantees that the **LP calibration effect** $(\Pi_{\text{recal-plan}} - \Pi_{\text{orig-plan}})$ is real and measurable during operational and opportunity-based backcasting (`UC-3`).

## 3. Python-verified worked examples

All figures below were verified to full double precision using $\rho_{w,60^\circ\text{F}} = 999.016\text{ kg/m}^3$ and $c_{\text{bbl}} = 0.158987294928\text{ m}^3/\text{bbl}$.

1. **Tank conservation and intermediate overflow (`EQ-01`, `EQ-02`, `PO-01`):**
   - Constant $\text{SG}_{60/60} = 0.840$ gives $\rho_{\text{ref}} = 839.173440\text{ kg/m}^3$ (`133.417915 kg/bbl`).
   - *Baseline `T125`:* $V(0) = 10{,}000\text{ bbl}$ (`1,334,179.15 kg`), working cap `12,000 bbl`, inflow `500 bbl/h` (`66,708.96 kg/h`), outflow `700 bbl/h` (`93,392.54 kg/h`) for `2 h`. Closing stock is `9,600 bbl` (`1,280,811.99 kg`), mass residual `0.00 kg`.
   - *Intermediate overflow fixture:* $V(0) = 11{,}800\text{ bbl}$ (`1,574,331.40 kg`), cap `12,000 bbl`. Hour 1 net `+400 bbl/h` (`600 in / 200 out`), hour 2 net `-500 bbl/h` (`0 in / 500 out`). An unsplit 2-hour balance yields `11,700 bbl` (`1,560,989.61 kg`), falsely appearing legal while hiding a `200 bbl` overflow at hour 1 (`12,200 bbl` = `1,627,698.57 kg`). Exact crossing detection splits at $t^* = (12{,}000 - 11{,}800)/400 = 0.5\text{ h}$.
2. **HCU compressor derate, complete product/coproduct mass slate, and liquid volumetric gain (`EQ-01`, `EQ-05`, `EQ-07`):**
   - Nominal VGO charge `40,000 bbl/day` at $\text{SG}_{60/60} = 0.910$ equals `5,781.44 t/day`. Under the `SCENARIO_ASSUMPTION` compressor derate (assuming the unit runs at $R_{\min}$ at `40,000 bbl/day` with quench and shared $\text{H}_2$ non-binding), feasible feed drops to `30,000 bbl/day` (`4,336.08 t/day`).
   - Unit cancellation check for `EQ-05`: for `R_{min,vol} = 4,000 SCF H2 / bbl` at `60 °F, 14.696 psia`, $R_{\min,\text{mass}} = (4000 \times 2.01588 / 379.48 \times 0.45359237) / (909.10456 \times 0.158987294928) = 0.06669\text{ kg pure H}_2/\text{kg feed}$. A nominal pure-$\text{H}_2$ recycle flow of `385.56 t/day` (`w_H2,rec * m_dot_rec`) supports `385.56 / 0.06669 = 5,781.44 t/day` (`40,000 bbl/day`); cutting recycle to 75% (`289.17 t/day`) yields `289.17 / 0.06669 = 4,336.08 t/day` (`30,000 bbl/day`).
   - With `2.0 wt%` synthetic chemical $\text{H}_2$ uptake (`86.72 t/day`, equivalent to `1,199.7 SCF/bbl` — a synthetic mild-to-moderate conversion figure), total input mass is `4,422.80 t/day`. The complete synthetic output slate closes mass identically (`0.000000 t/day` residual) while separating non-liquid gas/acid-gas streams from liquid barrels:

   | Output stream | wt% of total input | Mass (`t/day`) | $\text{SG}_{60/60}$ | Liquid volume (`bbl/day`) |
   |---|---:|---:|---:|---:|
   | Acid gas ($\text{H}_2\text{S} + \text{NH}_3$) | 1.50% | 66.34 | gas | n/a |
   | Dry gas ($\text{C}_1$–$\text{C}_2$) | 1.00% | 44.23 | gas | n/a |
   | LPG ($\text{C}_3$–$\text{C}_4$) | 3.50% | 154.80 | 0.540 | 1,804.8 |
   | Light Naphtha | 10.00% | 442.28 | 0.675 | 4,125.3 |
   | Heavy Naphtha | 14.00% | 619.19 | 0.755 | 5,163.5 |
   | Jet / Kerosene | 20.00% | 884.56 | 0.810 | 6,875.6 |
   | ULSD | 40.00% | 1,769.12 | 0.840 | 13,260.0 |
   | Unconverted Oil (UCO) | 10.00% | 442.28 | 0.865 | 3,219.2 |
   | **Total** | **100.00%** | **4,422.80** | — | **32,643.6 ($\text{C}_5+$) / 34,448.4 ($\text{C}_3+$)** |

   - Liquid $\text{C}_5+$ volumetric gain vs `30,000 bbl/day` feed is `+8.81%` (`+14.83%` including LPG), while total mass residual is `0.00 t/day`.
   - *Constant-uptake shared-$\text{H}_2$ boundary check (zero purge/dissolved loss, fixed $\xi$):* If shared $\text{H}_2$ headroom is `75.00 t/day`, constant `2.0 wt%` uptake caps feed at `75.00 / 0.02 = 3,750.00 t/day` (`25,945 bbl/day`). In full runtime mode, `c_H2,net(ξ)` includes purge/dissolved loss and updates $\xi$ at lower LHSV.
3. **FCC 4-lump mass-closure countercheck with positive CCR (`EQ-06`, Lee et al. 1989):**
   - Feed `w_CCR,feed = 0.04` with $f_{\text{add}} = 0.75$ gives $y_D(0) = 0.030$, $y_A(0) = 0.970$, $y_B(0) = y_C(0) = 0$. Integrating with synthetic test constants $(k_1=2.2, k_2=0.35, k_3=0.55, k_4=0.18, \beta_{BC}=0.80, \alpha_d=0.40)$ to $\tau = 1$ yields $y_A = 0.290206$, $y_B = 0.419304$, $y_C = 0.200504$, $y_D = 0.089986$; sum $= 1.000000000000$ (exact closure).
4. **Realistic summer gasoline RVP blending check (`EQ-08`):**
   - `95 vol%` summer RBOB base (`7.00 psi`, $BI = 11.3860$) plus `5 vol%` $n$-butane (`52.00 psi`, $BI = 139.6382$) gives $BI_{\text{blend}} = 17.7986$ and $\text{RVP}_{\text{blend}} = 10.01\text{ psi}$ (versus linear average `9.25 psi`, a `+0.76 psi` error that pushes a `9.50 psi` summer gasoline blend off-spec).
5. **Mass sulfur blending check (`T24`, `EQ-08`):**
   - `100 t` at `10 ppmw` sulfur plus $x$ tonnes at `100 ppmw` $\le 15\text{ ppmw}$ requires $x \le 100/17\text{ t}$ (`5.88235 t`). At `5 t`, $w_S = 100/7$ (`14.286 ppmw`, PASS); at `6 t`, $w_S = 800/53$ (`15.094 ppmw`, HOLD).
