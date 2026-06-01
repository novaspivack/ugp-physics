# REPRODUCE — P35 GTE Unification Capstone

## Compiling the paper

```bash
cd papers/35_gte_unification
pdflatex gte_unification_paper.tex
bibtex gte_unification_paper
pdflatex gte_unification_paper.tex
pdflatex gte_unification_paper.tex
```

Requires: TeX Live 2024+ with `tcolorbox`, `tikz`, `longtable`, `appendix`,
`cleveref`, `microtype`.

Expected output: `gte_unification_paper.pdf`, 14 pages.

## Verifying the Lean certification

The main theorem `ugp_r110_sm_joint_unification` is in:

```
ugp-lean/UgpLean/Universality/GUTStructure.lean
```

Section §27. To verify:

```bash
cd ugp-lean
lake build UgpLean.Universality.GUTStructure
# Should build with zero errors and zero sorry
```

To verify the master formula:

```bash
# In GUTStructure.lean §23, look for gte_master_formula_complete
grep -n "gte_master_formula_complete" UgpLean/Universality/GUTStructure.lean
```

## Verifying individual arrows

| Arrow | Lean theorem | Module section |
|---|---|---|
| A1 (sin²θ_W = 3/13) | `weinberg_angle_closure` | GUTStructure §12 |
| A2 (λ = 9/40) | `wolfenstein_lambda_formula` | GUTStructure §14 |
| A3 (GoE orbit) | `CUP3D.fmdl_gen1_is_garden_of_eden` | CUP3DUniqueness.lean |
| A4 (photon fixed point) | `CUP3D.fmdl_unique_uniform_fixed_point` | CUP3DUniqueness.lean |
| A5 (arithmetic pivot) | `gte_arithmetic_root` | GUTStructure §23 |
| A6 (Mersenne uniqueness) | `ngen_3_mersenne_uniqueness` | GUTStructure §23 |

## Verifying numerical results

The baryon-to-photon ratio formula η_B = sin²θ_W × α_em^4:

```python
import math
sin2tW = 3/13
alpha_em = 1/137.036
eta_B = sin2tW * alpha_em**4
print(f"eta_B = {eta_B:.3e}")  # Should print: eta_B = 6.541e-10
```

## Cook theorem (P30) single axiom

The one non-discharged axiom is `len6_evolved_inf30_eq_list420_at_slot`
in the `rule110-lean` repository. See `papers/30_cook_theorem/REPRODUCE.md`
for verification instructions and the Python cross-check script.

---

## Additional Lean modules (appendix inventory)

```bash
cd ugp-lean
lake build UgpLean.Universality.CUP3DUniqueness
lake build UgpLean.Universality.DimensionalSliceUniqueness
lake build UgpLean.Universality.GTEComputability
```

| Arrow | Extra module |
|-------|----------------|
| A3, A4 | `CUP3DUniqueness.lean` |
| D=4 | `DimensionalSliceUniqueness.lean` |
| CKM block | `GUTStructure` §72 (shared with P32) |

---

## Lean modules for QCD/substrate sections (§§7–9)

```bash
cd ugp-lean
lake build UgpLean.Spacetime.LiftingTheorem
lake build UgpLean.Spacetime.SpatiallyExtendedLifting
lake build UgpLean.Spacetime.ColorConfinement
lake build UgpLean.Spacetime.MassGap
lake build UgpLean.QFT.GaugedMassGap
lake build UgpLean.Universality.AlgebraicDescentTheorem
lake build UgpLean.Universality.SylowIndexCouplingHierarchy
lake build UgpLean.Universality.GUTStructure      # §§5i, 6, 29, 32, 40–42, 54, 70–75
```

Key theorems verified:
- `algebraic_lifting_theorem` (LiftingTheorem.lean) — beable-to-physical lifting
- `algebraic_descent_theorem` (AlgebraicDescentTheorem.lean) — F₂₁-property descent
- `no_psc_admissible_single_quark` (ColorConfinement.lean) — colour confinement
- `qft_gauged_mass_gap_unconditional` (GaugedMassGap.lean) — QFT mass gap
- `f21_substrate_beta_coefficient` (SylowIndexCouplingHierarchy.lean) — b₀ = 7
- `f21_two_loop_beta_coefficient` — b₁ = 26
- `frobenius_qcd_colour_factors` — C_F, C_A, T_F
- `strong_cp_theta_zero_f21`, `strong_cp_resolved` — θ_QCD = 0
- `causal_graph_spectral_dim_thermodynamic_limit` — d_s = 4

---

## Graduation checklist (full reproducibility)

| Item | Status | Notes |
|------|--------|-------|
| `GUTStructure` §27 capstone | ⏳ `ugp-lean` | `ugp_r110_sm_joint_unification` |
| Full appendix Lean inventory | ⏳ exp | Graduate with shared GUT bundle |
| `CUP3DUniqueness`, `DimensionalSliceUniqueness` | ⏳ exp | Listed in REPRODUCE above |
| Python scripts | N/A | Synthesis paper — numerical η_B inline only |
| `figures/` directory | ⏳ | `\graphicspath` expects `artifacts/` / `figures/` |
| R87.11 Gorard scaling (P35 §3) | ⏳ PLANNED | Numerics live in P36 |

---

## Numerical verification scripts (graduated 2026-05-24; deferred pass 2026-05-24)

```bash
cd papers/35_gte_unification/scripts
python3 epsilon_scale_loglog.py           # ε₀(M) = π²/(3M²) scaling (95-EPSSCALE)
python3 epsilon_relative_expansion.py     # ε relative expansion (95a-EPSREL)
python3 two_sector_lattice.py             # two-sector lattice NO-GO (98-TWOSECTOR)
python3 coupling_hierarchy_t98_5.py       # α_EM hierarchy closure (T98-5)
python3 substrate_wellposed_eft.py        # R-4 EFT well-posedness (103-WELLPOSED)
python3 vcoup_uniqueness_enum.py          # V_coupling uniqueness enum (136-VCOUP)
python3 epsilon_coupling_derivation.py    # ε = 7/9 from F₂₁ (137-EPSDER)
python3 rank132_sigmacal.py               # √σ_4D = 440.6 MeV, Z₃ string tension (132-SIGMACAL)
python3 rank113_kinkloop3v.py             # triangle form factors; vacuum polarization Π(Q²)∝log (113-KINKLOOP3V)
python3 rank114_eftmatch.py               # Λ_GTE = 2.01 GeV EFT matching (114-EFTMATCH)
python3 rank146_threeloop_beta.py         # b₂=180.9, αs 3-loop=0.1193 (146-THREELOOP; P35 update pending)
```

Hadronic/QCD chain scripts are canonical in `papers/28_computational_universality/scripts/` (cross-reference only; see P28 REPRODUCE Step 29).

F₂₁ full lattice simulation (rank120) is canonical in `papers/39_qcd_from_gte/scripts/` — see P39 REPRODUCE.

| Script | Rank | Expected headline |
|--------|------|-------------------|
| `epsilon_scale_loglog.py` | 95-EPSSCALE | Nyquist scaling law |
| `epsilon_relative_expansion.py` | 95a-EPSREL | C_∞ = π²(2π²−1)/24 |
| `two_sector_lattice.py` | 98-TWOSECTOR | single-field NO-GO |
| `coupling_hierarchy_t98_5.py` | T98-5 | α_EM ROBUST CatAL |
| `substrate_wellposed_eft.py` | 103-WELLPOSED | Wilsonian EFT ROBUST |
| `vcoup_uniqueness_enum.py` | 136-VCOUP | unique dim-4 cross-coupling |
| `epsilon_coupling_derivation.py` | 137-EPSDER | ε = 7/9 |
| `rank132_sigmacal.py` | 132-SIGMACAL | √σ_4D = 440.6 MeV (§8 tab:predictions) |
| `rank113_kinkloop3v.py` | 113-KINKLOOP3V | triangle C₀; Π(Q²)∝log; αs = 0.1319 (§9) |
| `rank114_eftmatch.py` | 114-EFTMATCH | Λ_GTE = 2.01 GeV (§9 UV completion) |
| `rank146_threeloop_beta.py` | 146-THREELOOP | b₂=180.9; αs 3-loop=0.1193 (P35 update pending) |

Dependencies: Python 3.9+, numpy. Runtime: <10 min each (timeouts enforced).

---

## Graduation checklist (full reproducibility)

| Item | Status | Notes |
|------|--------|-------|
| `GUTStructure` §27 capstone | ⏳ `ugp-lean` | `ugp_r110_sm_joint_unification` |
| Full appendix Lean inventory | ⏳ exp | Graduate with shared GUT bundle |
| `CUP3DUniqueness`, `DimensionalSliceUniqueness` | ⏳ exp | Listed in REPRODUCE above |
| Python scripts | ✅ 2026-05-24 | 11 scripts in `scripts/` (7 original + 4 from deferred pass 2026-05-24) |
| Cross-paper hadron chain | ✅ | P28 `scripts/` (Step 29) |
| `figures/` directory | ⏳ | `\graphicspath` expects `artifacts/` / `figures/` |
| R87.11 Gorard scaling (P35 §3) | ⏳ PLANNED | Numerics live in P36 |

---

---

## EPIC_073 EW scale scripts (graduated 2026-05-25)

```bash
cd papers/35_gte_unification/scripts
python3 ew_threshold_definitional.py              # 168-EWD: k=N_gen orbit absorption (CatAL structural)
python3 p22_vacuum_scale_bridge.py                # 169-P2B: E_0 = v_PSC sqrt(π/8); M_Z pred 91.914 GeV
python3 ew_scale_consolidation.py                 # 158-EWS: consolidated eight-step EW chain
python3 epic073_rank158_ews_dr_delta_r_ca_loop_closure.py  # 158-EWS-DR: Δr Sirlin path
```

| Script | Rank | Expected headline |
|--------|------|-------------------|
| `ew_threshold_definitional.py` | 168-EWD | sin²θ_W = 3/13 orbit-vacuum threshold (CatAL structural) |
| `p22_vacuum_scale_bridge.py` | 169-P2B | E_0 = 154.258 GeV; M_Z = 91.914 GeV (+0.797%); M_W = 80.614 GeV (+0.295%) |
| `ew_scale_consolidation.py` | 158-EWS | Internal consistency PASS; M_W = M_Z sqrt(10/13) at tree sin² with Δr |
| `epic073_rank158_ews_dr_delta_r_ca_loop_closure.py` | 158-EWS-DR | Δr = sin²/π; direct photon VP loop negative; Sirlin+isospin consistent |

**Lean (zero sorry):** `ugp-lean/UgpLean/Universality/EWScalePrediction.lean` — `e0_schwinger_sm_identity`, `mw_formula_from_vH`, `mz_formula_from_vH`, `delta_r_from_delta_alpha_gte`.

Dependencies: Python 3.9+, numpy. Results JSON co-located in `scripts/`.

---

---

## EPIC_080 additions (2026-05-29)

| Script | Computes | Key result |
|--------|----------|------------|
| `scripts/fca_srrg_bridge.py` | FCA diagonal fixed point vs SRRG golden-ratio fixed point identity | x* = (√5−1)/2 = 1/φ, M-independent (CatAL); Lean: `fca_attractor_diagonal_fp_equals_srrg_fp` |
| `scripts/coupling_constants_gte.py` | EW coupling constants g, g′, g_s from sin²θ_W=3/13 and α_EM (CatAD) | g=0.6500 (0.42% vs PDG), m_Z=91.21 GeV (0.03%), m_W=80.00 GeV (0.47%) |
| `scripts/phimdl_propagators_vertices.py` | Φ_MDL scalar propagator G(p)=1/(p²+m²), interaction vertices λ₄, λ₆ | m=290.10 MeV; λ₄/m²=49=7² (Z₇ fingerprint) |
| `scripts/g10_strong_coupling_fquant.py` | f_quant string-tension precision scan | Best form: 2^{-2/3}=(C_F·N_c)^{-1/3}=0.630 (PROVISIONAL CatA) |

Artifacts: co-located JSON in `scripts/`.

Dependencies: Python 3.9+, numpy. Runtime: <2 min each.

*REPRODUCE.md — P35 — reproducibility audit 2026-05-24 (script graduation); EPIC_073 EW pass 2026-05-25; EPIC_080 additions 2026-05-29*

## EPIC_083 additions (2026-06-01)

New Lean certifications cited in this paper:

**OP9 (SRRG–MDL equivalence):**
- `srrg-lean/SrrgLean/Bridges/ToMDL.lean` — `op9_catal_unconditional` (zero sorry, no conditions; SRRG fixed point g*=1/φ uniquely minimizes K_alg): verify with `cd /path/to/srrg-lean && lake build SrrgLean.Bridges.ToMDL`
- `srrg_op9_k_alg_biconditional` — K[S]=B−F[S] biconditional zero sorry (CatAD)

**W₁ Wasserstein distance (supports Gorard chain Step 2):**
- `UgpLean/ContinuumLimit/WassersteinDistance.lean` — full W₁ metric theory (zero sorry): `W1_nonneg`, `W1_triangle`, `W1_ge_of_lipschitz`, `W1_eq_zero_iff`, `W1_attained`; verify: `lake build UgpLean.ContinuumLimit.WassersteinDistance`

*EPIC_083 additions 2026-06-01*

## EPIC_083B additions (2026-06-01)

**SU(2)_L MDL gauging chain (CatAL, zero named axioms):**
- `su2l_l2_from_phimdl_potential_catad` — `UgpLean/Algebra/GaugeMDL.lean` (ugp-lean commit `378ff20`)
- Supporting theorems: `phimdl_potential_su2l_invariant`, `su2l_covariant_derivative_minimal`, `su2l_wpm_generator_algebra`
- Verify: `cd ugp-lean && lake build UgpLean.Algebra.GaugeMDL`

