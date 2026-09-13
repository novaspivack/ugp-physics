# REPRODUCE — P38 — Emergent Gravity from the Φ_MDL Field

**Paper:** P38 — Einstein Equations, Kink Sources, and Quantum Gravity Scale  
**Date written:** 2026-05-26  
**Author:** Nova Spivack

---

## Compiling the paper

```bash
cd papers/38_emergent_gravity_phimdl
pdflatex emergent_gravity_gte_phimdl.tex
bibtex emergent_gravity_gte_phimdl
pdflatex emergent_gravity_gte_phimdl.tex
pdflatex emergent_gravity_gte_phimdl.tex
```

Expected output: 17 pages, zero hard LaTeX errors.
Dependencies: TeX Live 2025+, all standard packages (amsmath, tcolorbox, longtable, hyperref, etc.).

---

## Reproducing Φ_MDL gravity results (graduated 2026-05-26)

```bash
cd papers/38_emergent_gravity_phimdl/scripts
python3 phimdl_tmunu_full.py                      # T_μν tensor (075-TMUNU, CatAD)
python3 phimdl_kink_gravitational_source.py        # Kink as gravitational source (075-KINKSRC, CatA)
python3 phimdl_cosmological_constant.py            # Classical Λ=0 + hierarchy (075-COSMO, CatD)
python3 phimdl_quantum_gravity_regime.py           # QGR scale π/√3, Penrose OR (28-QGR, CatAD)
```

| Script | Rank | Expected headline |
|--------|------|-------------------|
| `phimdl_tmunu_full.py` | 075-TMUNU | T_{11}=0 (BPS), T_{22}=-T_{00}, ∫T_{00}=290.10 MeV, conservation max 6×10⁻¹² |
| `phimdl_kink_gravitational_source.py` | 075-KINKSRC | ∫T_{00}=290.0996 MeV (rel err 1.4×10⁻⁶), FWHM=1.7627/m_φ=0.196 fm |
| `phimdl_cosmological_constant.py` | 075-COSMO | V(Φ_k)=0 exactly at all 7 Z₇ vacua; ΔV_CW≈2.4×10¹⁰ MeV⁴; hierarchy 10⁴⁵ |
| `phimdl_quantum_gravity_regime.py` | 28-QGR | M_Pl^GTE=π/√3≈1.81; Γ_OR=1.52×10⁻¹⁵ s⁻¹; τ_OR≈20 Myr |
| `lepton_mass_neff_cascade.py` | 080-G08 | N_eff/c-value/thermal cascades all FAIL (non-monotonic b); atom scan volume-dominated (31 target vs 28 wrong-target hits); Koide closed form holds (m_τ to 61 ppm); hierarchy is non-topological (all leptons w=4) |
| `lepton_mass_session2.py` | 080-G08/KOIDE-L2 | IMT sanity (e/μ 0.000%, τ 0.0054%); breather tower RULED OUT (β²=49 repulsive; tower linear); Koide phase θ=2/9 (from N_c=3) predicts m_μ/m_e=206.770 (0.001%, zero-param) and m_τ/m_μ=16.818 (0.006%); three-tape GTE Hessian not S₃-symmetric |

Results JSON artifacts are co-located with scripts.
Dependencies: Python 3.9+, numpy.

---

## Reproducing DCG-OR static curvature results (graduated 2026-05-25)

```bash
cd papers/38_emergent_gravity_phimdl/scripts
python3 dcg_or_static_kappa_round4.py              # R4: static κ Gorard sign (CatA)
python3 dcg_or_round5_two_defect_binding.py        # R5: two-defect binding negative
python3 dcg_or_round6_dynamic_kappa_coupling.py    # R6: dynamical κ coupling negative
python3 dcg_or_round7_edge_weight_fkappa.py        # R7: inv f(κ) static metric partial
python3 dcg_or_round8_timelike_geodesic_deviation.py  # R8: timelike deviation negative
python3 dcg_or_round9_selfconsistent_kappa.py      # R9: κ iteration diverges
```

| Script | Round | Expected headline |
|--------|-------|-------------------|
| `dcg_or_static_kappa_round4.py` | R4 | κ(EE)=0, κ(SD)=+0.769, κ(XD)=−0.901; matter vs vacuum p=2.5×10⁻³⁶ |
| `dcg_or_round5_two_defect_binding.py` | R5 | No monotonic κ increase as d decreases; binding negative |
| `dcg_or_round6_dynamic_kappa_coupling.py` | R6 | κ-XOR and κ-prob: no glider attraction |
| `dcg_or_round7_edge_weight_fkappa.py` | R7 | inv f(κ): differential geodesic shortening; exp f(κ) anti-attractive |
| `dcg_or_round8_timelike_geodesic_deviation.py` | R8 | Matter paths diverge; no timelike convergence |
| `dcg_or_round9_selfconsistent_kappa.py` | R9 | 0/100 slices converge; max Δκ diverges |

**Cross-ref:** P36 §Gorard chain; P36 §DCG curvature; dynamical gravity via Φ_MDL/EFE track (this paper).

---

## EPIC_080 additions (2026-05-29)

### Casimir one-loop vacuum energy — correct hierarchy 10^42 (G31)

**Script:** `scripts/casimir_one_loop.py`

**Purpose:** Computes the Coleman-Weinberg one-loop correction ΔV_CW using the correct
Φ_MDL kink mass m_kink = (8/49)m_τ = 290.10 MeV (not m_τ).

**Usage:**
```bash
cd papers/38_emergent_gravity_phimdl
python3 scripts/casimir_one_loop.py
```

**Key results to verify:**
- m_kink = 290.10 MeV (correct; m_τ = 1776.86 MeV was wrong input)
- ΔV_CW (μ=m_φ, MS-bar) = −1.682×10⁷ MeV⁴
- Hierarchy: |ΔV_CW|/ρ_Λ^obs ≈ 6×10⁴¹ ~ 10⁴² (not 10⁴⁵)
- Z₇ structure does NOT cancel the CW correction
- NRT mechanism (non-perturbative IR) is additive, not cancelling

**Bug fixed:** Prior versions used m_tau instead of m_kink, inflating the hierarchy
by (49/8)⁴ ≈ 1407×. P38 and P43 both corrected.

---

## 083C additions (2026-06-02): MS-bar dim-reg and C_logfin precision — SUPERSEDED 2026-06-10

| Script | Status |
|---|---|
| `papers/38_emergent_gravity_phimdl/scripts/phimdl_casimir_dimreg.py` | **SUPERSEDED** — produced ΔM = +31.22 MeV, M^Q = 321.32 ± 15.6 MeV via renormalization-bookkeeping errors (missing diagrammatic add-back; inverted Levinson phase-shift convention; scheme-inconsistent μ-flow). Retained for the record; do not use. |
| `papers/38_emergent_gravity_phimdl/scripts/casimir_clogfin_precision.py` | **SUPERSEDED** — precision study of the withdrawn C_logfin coefficient (belongs to the superseded bookkeeping). Retained for the record; do not use. |

## Quantum kink mass — corrected one-loop computation (2026-06-10)

The corrected quantum (pole) kink mass is **M^Q = 281 ± 21 MeV** (ΔM = −7.2 MeV
on-shell / −10.0 MeV MS-bar at μ = m_φ; GJQW interface dimensional regularization,
DHN-benchmark-validated, two independent routes). The computation is owned by P42;
reproduce from the P42 script set:

```bash
cd papers/42_phimdl_field/scripts
python3 kink_pole_mass_dhn_benchmarks.py       # benchmark lock: sine-Gordon −m/π and φ⁴ (1/(4√3)−3/(2π))m to 3×10⁻¹⁴
python3 kink_pole_mass_interface_dimreg.py     # the one-loop wall mass: ΔM/M^Q per renormalization condition
python3 kink_pole_mass_box_modesum_check.py    # independent finite-box mode-sum cross-check (3×10⁻⁵ agreement)
```

| Expected headline | Value |
|---|---|
| ΔM (MS-bar, μ = m_φ) | −10.0 MeV (M^Q = 280.1 MeV) |
| ΔM (on-shell) | −7.2 MeV (M^Q = 282.9 MeV) |
| Scheme envelope μ ∈ [m_φ/2, 2m_φ] + on-shell + self-consistent | M^Q ∈ [259.3, 300.9] MeV ⇒ M^Q = 281 ± 21 MeV |

*REPRODUCE.md — P38 — 2026-05-26; EPIC_080 casimir correction 2026-05-29; quantum kink mass correction 2026-06-10*
