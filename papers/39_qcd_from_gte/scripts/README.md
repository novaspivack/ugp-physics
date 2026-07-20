# P39 Scripts Directory

**Paper:** P39 — QCD Structure from the Generative Triple Evolution Substrate

**Graduation status:** All scripts graduated 2026-05-24.

---

## Gauge-invariant confinement and Wilson loops

| Script | What it computes | P39 section |
|---|---|---|
| `rank90_gauge_invariant_confinement.py` | Gauge-invariant static theory; σ=0 in Higgs phase | §5.1 |
| `rank91_wilson_loop_z3_confinement.py` | Wilson loop Z₃ confinement test; area law at β≤β_c | §5.1 |
| `rank91_t1_coupled_wilson_loop.py` | Coupled Wilson loop (T1 task) | §5.1 |
| `rank91_g2_robustness_bundle.py` | G2 robustness bundle; FSS confirms deconfinement; ROBUST | §5.1 |
| `rank92_phonon_mass_zn.py` | Phonon/photon mass in Z_N limit; G4 ROBUST | §5.1 |
| `rank92_t2_spectral_validation.py` | T2 spectral validation (SC1/SC2/SC3 subchecks) | §5.1 |
| `rank92_t2_route_b_fix.py` | Route B matrix phonon mass fix | §5.1 |
| `rank93_vxcatalog.py` | Gauged vertex recovery catalog; G3 PASS 7/7 | §5.1 |

## MDL uniqueness and kink calibration

| Script | What it computes | P39 section |
|---|---|---|
| `rank96_l1_potential_mdl_closure.py` | L1 SM-dependence elimination (potential form) | §5.2 |
| `rank96_mdl_score.py` | MDL score ΔL=+23.75 bits; Z₇ wins all scenarios | §2.4 |
| `rank96_t96_04_kink_charge_derivation.py` | Kink charges from first principles (T96-04) | §5.2 |
| `rank96_z2_competitor_elimination.py` | Z₂ competitor elimination | §2.4 |
| `rank96_z5_orbit_analysis.py` | Z₅ orbit analysis (competitor) | §2.4 |
| `rank97a_bvp_kink_energy.py` | BPS kink energy via BVP shooting; E_BPS exact | §5.2 |
| `rank97b_dbreakqcd_calibration.py` | Physical scale calibration v1 (Route A/B) | §5.2 |
| `rank97b_dbreakqcd_calibration_v2.py` | Physical scale calibration v2 (Routes A'/B'/C'); sim_to_fm=0.112 fm/sim | §5.2 |
| `rank97c_gi_string_breaking.py` | Gauge-invariant string breaking; σ_2D=0.1460 analytic; ROBUST | §5.2 |
| `rank97c_dynamic_string_breaking.py` | Dynamic string breaking (non-GI) | §5.2 |

## F₂₁ substrate identification and colour factors

| Script | What it computes | P39 section |
|---|---|---|
| `rank112_frobenius_f21.py` | F₂₁ = Z₇⋊Z₃ full algebraic verification; C_F=4/3, C_A=3, all f^{abc} | §2 |
| `rank113_kinkloop3v.py` | Three-gauge-vertex amplitude from F₂₁ kink loops; LEP colour factors 1σ | §2.4 |

## Asymptotic freedom and β-function

| Script | What it computes | P39 section |
|---|---|---|
| `rank117_afrgcheck_beta.py` | One-loop β = −7g³/(16π²) from F₂₁ substrate; b₀=7 | §3.1 |
| `rank117_parity_violation_two_layer.py` | Parity violation two-layer check | §3 |
| `rank119_twoloop_beta.py` | Two-loop b₁=26 from F₂₁; α_s(M_Z) two-loop | §3.2–3.3 |
| `rank146_threeloop_beta.py` | Three-loop b₂=180.91; α_s(M_Z)=0.1193 (+1.10% vs PDG) | §3.4 |

## F₂₁ → SU(3) deconstruction and lattice

| Script | What it computes | P39 section |
|---|---|---|
| `rank115_deconstruct.py` | F₂₁ → SU(3) deconstruction; b₀=7; vacuum polarization | §8.2 |
| `rank120_lattice32_f21.py` | 4D F₂₁ Wilson lattice simulation round 1 | §8 |
| `rank120_lattice32_f21_full.py` | 4D F₂₁ Wilson lattice simulation round 2 (canonical) | §8 |
| `rank120_asymmetric_coupling_mode.py` | Asymmetric coupling mode study | §8 |

## Berry holonomy and gauge architecture

| Script | What it computes | P39 section |
|---|---|---|
| `rank121_berry21_su3_holonomy.py` | F₂₁ non-abelian SU(3) Berry holonomy; 5/5 tests PASS | §6.1 |
| `rank121_non_uniform_coupling.py` | Non-uniform coupling study | §6.1 |
| `rank122_normberry.py` | A′_μ coupling normalization from F₂₁ Berry holonomy; OPTION A | §6.2 |

## Hadron multiplets and baryon spin

| Script | What it computes | P39 section |
|---|---|---|
| `rank106_hadmult.py` | Meson nonet, baryon octet/decuplet from GTE kink composites | §7.2 |
| `rank123_octet2.py` | Second baryon octet suppression; δK=log₂3=1.585 bits | §7.2 |
| `rank123_particle_level_coupling.py` | Particle-level coupling study | §7.2 |
| `rank125_jpspin.py` | J^P=1/2⁺ derivation via [D]/MDL chain | §7.2 |
| `rank126_vecmeson.py` | Vector meson nonet masses from Berry hyperfine; 3.2% RMS | §7.2 |

## Quark masses and strong CP

| Script | What it computes | P39 section |
|---|---|---|
| `rank128_quarkmass.py` | All 6 quark current masses; r_s/d=20.00 (+1.0%) | §7.1 |
| `rank128_wboson_vertex.py` | W-boson vertex study | §6.5 |
| `rank127_chitop.py` | χ_top^(1/4) preliminary (superseded by rank130) | §7.4 |
| `rank127_diagonal_coupling.py` | Diagonal coupling check | §7.4 |
| `rank130_chitop2.py` | χ_top^(1/4)=166.5 MeV (−6.4% vs PDG); Lüscher correction | §7.4 |

## Chiral sector: f_π, B₀, m_π, θ_P

| Script | What it computes | P39 section |
|---|---|---|
| `rank131_fpigte.py` | f_π = m_kink/π = 91.35 MeV (−0.81% vs PDG) | §7.3 |
| `rank132_sigmacal.py` | 4D string tension √σ_4D=440.6 MeV; N₃/N₇=3/7 | §7.4 |
| `rank133_pimassgge.py` | B₀_GTE=2398 MeV from BPS condensate (LO) | §7.5 |
| `rank134_nlo_b0.py` | NLO B₀=2727 MeV; m_π_NLO=136.5 MeV (+1.11%); θ_P=−13.08°±3.74° | §7.5–7.6 |
| `rank144_pimassfp.py` | m_π^GTE=136.49 MeV from GOR inversion (zero PDG input) | §7.6 |
| `rank129_thetap.py` | η–η′ mixing angle θ_P (v1) | §7.5 |
| `rank129_thetap_v2.py` | θ_P = −13.08°±3.74° in PDG range (v2, canonical) | §7.5 |

## Companion structural scripts (graduated earlier)

| Script | What it computes | P39 section |
|---|---|---|
| `aprime_lagrangian_extension.py` | A′_μ minimal Lagrangian extension; e′=e | §6.2 |
| `fradkin_shenker_confinement.py` | Fradkin–Shenker FS-C1/C2/C3 verification | §6.4 |
| `nonabelian_berry_holonomy_su3.py` | Non-abelian SU(3) Berry holonomy | §6.1 |
| `rank146_threeloop_beta.py` | Three-loop β coefficient (see β-function section above) | §3.4 |
| `second_cartan_gauge_field.py` | Second Cartan field A′_μ identification | §6.2 |
| `strong_cp_f21.py` | Strong CP θ_QCD=0 via three independent F₂₁ arguments | §4 |

---

## To reproduce headline numbers

```bash
cd papers/39_qcd_from_gte/scripts
python rank131_fpigte.py           # f_pi = 91.35 MeV  (-0.81% vs PDG)
python rank134_nlo_b0.py           # B0_NLO, m_pi_NLO, theta_P
python rank144_pimassfp.py         # m_pi^GTE = 136.49 MeV (+1.11% vs PDG, zero PDG input)
python rank146_threeloop_beta.py   # alpha_s(M_Z) = 0.1193 (+1.10% vs PDG)
python rank130_chitop2.py          # chi_top^(1/4) = 166.5 MeV (-6.4% vs PDG)
python rank97b_dbreakqcd_calibration_v2.py  # physical scale calibration routes
```

See `../REPRODUCE.md` for Lean build commands and full reproducibility instructions.
