# PROVENANCE — P38 — Emergent Gravity from the Φ_MDL Field

**Paper:** P38 — Emergent Gravity from the Φ_MDL Field: Einstein Equations, Kink Sources, and Quantum Gravity Scale  
**Date written:** 2026-05-26  
**Author:** Nova Spivack

---

## Derivation Record — EPIC_075 Cluster F (Φ_MDL continuum track)

| Round | Rank | Script | Result | Status |
|-------|------|--------|--------|--------|
| R1 | 075-TMUNU | `phimdl_tmunu_full.py` | T_μν fully explicit; ∫T_{00}=290.10 MeV; BPS T_{11}=0; conservation <10⁻¹² | CatAD |
| R2 | 075-KINKSRC | `phimdl_kink_gravitational_source.py` | ∫T_{00}=290.0996 MeV (rel err 1.4×10⁻⁶); FWHM=1.7627/m_φ; form factor (8m/49)(πk/m)/sinh(πk/m) | CatA |
| R3 | 075-COSMO | `phimdl_cosmological_constant.py` | V(Φ_k)=0 at all 7 Z₇ vacua; ΔV_CW=−2.37×10¹⁰ MeV⁴; hierarchy 10⁴⁵ | CatD (open) |
| R4 | 28-QGR | `phimdl_quantum_gravity_regime.py` | M_Pl^GTE=π/√3≈1.81; Γ_OR=1.52×10⁻¹⁵ s⁻¹; τ_OR≈20 Myr | CatAD |
| — | 075-EFE | Analytic derivation | MDL-Lovelock + minimal coupling + variational → G_μν=8πG T_μν (form CatAD) | CatAD (form) |
| — | 32-ALT2 | `AsyncLiftingTheorem.lean` | async_algebraic_lifting_theorem (zero sorry, definitional) | CatAL |

**Key numerical values:**
- m_φ = m_τ = 1776.86 MeV
- M_kink = (8/49)m_φ = 290.0996 MeV
- Classical Λ = 0 (exact, Lean-certified)
- QGR scale: M_Pl^GTE = π/√3 ≈ 1.8138 lattice units
- Penrose OR time: τ_OR ≈ 6.56×10¹⁴ s ≈ 20 million years
- Schwarzschild radius of kink: 7.6×10⁻⁵⁵ m

**Lean certifications (ugp-lean):**
- `StressEnergyTensor.lean`: phimdl_tmunu_symmetric, phimdl_potential_at_vacuum_zero, phimdl_tmunu_vacuum_zero, phimdl_bps_kink_pressure_free (axiom), phimdl_gravity_sector_prerequisites
- `QuantumGravity.lean`: gte_is_beable_level_quantum_gravity, matter_geometry_from_same_rule
- `AsyncLiftingTheorem.lean`: async_algebraic_lifting_theorem, async_color_confinement

---

## Derivation Record — 64-DCG-OR arc (Cluster J, EPIC_073)

(Superseded as primary gravity track; results preserved here for the static κ CatA result)

| Round | Rank | Script | Verdict | Status |
|-------|------|--------|---------|--------|
| R4 | 64-DCG-OR R4 | `dcg_or_static_kappa_round4.py` | Static κ discriminates matter vs vacuum (Gorard sign) | CatA |
| R5 | 64-DCG-OR R5 | `dcg_or_round5_two_defect_binding.py` | Two-defect binding via dynamical κ | CatA negative |
| R6 | 64-DCG-OR R6 | `dcg_or_round6_dynamic_kappa_coupling.py` | κ-weighted Rule 110 coupling | CatA negative |
| R7 | 64-DCG-OR R7 | `dcg_or_round7_edge_weight_fkappa.py` | Edge-weight f(κ) metric deformation | Partial static signal |
| R8 | 64-DCG-R8 | `dcg_or_round8_timelike_geodesic_deviation.py` | Timelike geodesic deviation | CatA negative |
| R9 | 64-DCG-R9 | `dcg_or_round9_selfconsistent_kappa.py` | Self-consistent κ iteration | CatA negative |

**Key R4 values:** κ(EE)=0, κ(SD)=0.769, κ(XD)=−0.901, κ(PE)=0.062 on A-glider/ETHER14.

**Conclusion:** Static Ollivier-Ricci curvature on Rule 110 causal graphs is established (CatA). Discrete Sakharov dynamical gravity mechanism is not confirmed (R5–R9 negative). Primary gravity derivation → Φ_MDL stress-energy / Einstein field equations (this paper).

---

*PROVENANCE.md — P38 — 2026-05-26*

- **2026-06-02 (083C quality audit — commit bba2d17e):** Added quantum kink mass section: Pöschl-Teller spectrum (s=1, CatAL: `phimdl_fluctuation_is_poschl_teller`); ZZ S-matrix S(θ)=(sinhθ−i)/(sinhθ+i) (CatAD); TBA kernel φ(θ)=2/cosh(θ) (CatAD).
- **2026-06-02 (MS-bar dim-reg — commit ff6ca728):** Casimir correction ΔM=+31.22 MeV, M^Q=321.32±15.6 MeV (CatA; supersedes log-UV M^Q=230.43 MeV).
- **2026-06-10 (kink form-factor correction):** The Fourier form factor of the kink energy density T₀₀ = (4m²_φ/49)sech²(m_φ x) is (8m_φ/49)·(πk/2m_φ)/sinh(πk/2m_φ) — corrected from the earlier (πk/m_φ)/sinh(πk/m_φ) (a factor-2 substitution error in the FT of sech²: ∫sech²(ax)e^{ikx}dx = (πk/a²)/sinh(πk/2a)). Both forms share the k→0 limit M_kink, so no integrated quantity changes; paper eq., reviewer's map row, and `phimdl_kink_gravitational_source.py` updated; numerical FT verification to 10⁻⁷. Same pass: T_ij component display and trace sign in §2.2 corrected (η_ij = −δ_ij bookkeeping); FWHM display corrected to 2 arccosh√2/m_φ (numerical value 1.7627/m_φ unchanged).
- **2026-06-10 (quantum kink mass correction):** Both prior M^Q values (321.32±15.6 MeV dim-reg; 230.43 MeV log-cutoff) identified as renormalization-bookkeeping artifacts (missing diagrammatic add-back; inverted Levinson convention; scheme-inconsistent μ-flow). Corrected one-loop result: ΔM = −7.2 MeV (on-shell) / −10.0 MeV (MS-bar at μ=m_φ), **M^Q = 281 ± 21 MeV** (GJQW interface dim-reg, DHN-benchmark-validated to 3×10⁻¹⁴, independent finite-box mode-sum cross-check 3×10⁻⁵; CatA within a CatAD framework). §pt_spectrum rewritten; C_Cas constant withdrawn; `phimdl_casimir_dimreg.py` and `casimir_clogfin_precision.py` marked superseded in REPRODUCE.md; corrected computation reproduced from `papers/42_phimdl_field/scripts/kink_pole_mass_*`.
