# PROVENANCE — P42: The Φ_MDL Field

**Paper:** The Φ_MDL Field: Quantum Structure, Born Rule, and Continuum Completion
of the Chiral Minkowski CA  
**Author:** Nova Spivack  
**Series:** UGP Physics P42  
**Published:** Zenodo (see title page DOI)

---

## Theoretical foundations

- Φ_MDL field definition: P34 (GTE-Möbius Substrate)
- Mass identification m_φ = m_τ: P34, P35
- Algebraic Lifting/Descent theorems: P28
- CMCA as UV completion: P41
- PSC superselection {0,2,3,4,6}: P29, P34

## Computational provenance

### Domain wall tension (σ)
- Script: `scripts/phimdl_3d_domain_wall.py`
- Method: numerical BPS integration on 1D grid; analytic formula σ = (8/49)m_φ
- Result: σ = 7450.31 MeV/fm² (relative error 2.8×10⁻¹³ vs analytic)
- Cross-check: kink mass from ∫T₀₀ dx = 290.10 MeV (relative error < 10⁻⁴)

### Junction tension (λ)
- Script: `scripts/phimdl_vortex_3d.py`
- Method: product ansatz φ(x,y) = kink(x) + kink(y), 256×256 grid
- Result: λ_dim = −0.32653061 ≈ −16/49 (convergence error < 10⁻¹⁰)
- Physical: λ = −1654.77 MeV/fm; |λ/σ| = 2.000 (wall thickness ratio)
- Lean cert: `phimdl_domain_wall_junction_tension_exact`,
  `phimdl_junction_is_attractive`, `phimdl_junction_to_wall_ratio`
  in `WindingCoinDecoupling.lean` (zero sorry)

### Explicit descent map
- Script: `scripts/cmca_algebraic_descent.py`
- Method: Cook A-glider Z₇ winding profile vs. BPS kink at M=7
- Result: RMSD = 5.34%, ε₀(7) = 6.71%, ratio = 0.796, Pearson r = 0.994
- Winding number Q = 1/7 (exact)

### Position Born density
- Script: `phiborn1_kg_amplitude_probability.py` (graduated to `papers/41_three_layer_chiral_minkowski_ca/scripts/`; cross-reference)
- Result: normalization ∫P dx = 1 to relative error 2.82×10⁻¹³

### Dual-frame Born rule
- Script: `phiborn2_kink_overlap_born.py` (`papers/42_phimdl_field/scripts/`, graduated 2026-05-31)
- Result: max residual |P(k)−|c_k|²| < 3.7×10⁻⁸ (well-separated regime)

### Monte Carlo [D]-collapse verification
- Script: `phiborn3_measurement_collapse.py` (`papers/42_phimdl_field/scripts/`, graduated 2026-05-31)
- Result: χ² = 2.997 (crit 12.592 at p=0.05, 6 dof) at 500k trials

## Lean 4 theorem provenance

All theorems listed in Appendix A of paper reside in the `ugp-lean` canonical
public repository. Two auxiliary lemmas (`bps_kink_integral_eq_four`,
`symmetry_integral_vanishes`) carry sorry; all cited theorems in the paper are
zero sorry.

## Update history

| Date | Update |
|------|--------|
| May 2026 | Initial paper with §1–8 and Appendix A |
| May 2026 | Added: junction tension §3.5, descent map §7.2, Discussion §§8.4–8.6, new Lean theorems |
| 2026-06-02 | Added: one-loop CW effective potential (Z₇ degeneracy preserved); Pöschl-Teller fluctuation spectrum (s=1, CatAL); ZZ S-matrix and TBA kernel (CatAD); scripts graduated to `papers/42_phimdl_field/scripts/`. Commit bba2d17e. |
| 2026-06-02 | MS-bar dim-reg quantum kink mass: ΔM=+31.22 MeV, M^Q=321.32±15.6 MeV (CatA; supersedes log-UV M^Q=230.43 MeV). Commit ff6ca728. |
| 2026-06-10 | Correction: quantum kink mass M^Q = 281 ± 21 MeV (ΔM = −7…−10 MeV on-shell/MS̄@m_φ; GJQW interface dim-reg, DHN-benchmark-validated, two independent routes; scripts `kink_pole_mass_*`). Both prior values (321.32 ± 15.6 and 230.43 MeV) superseded as bookkeeping errors (missing diagrammatic add-back; inverted Levinson convention; inconsistent μ-flow / cutoff artifact). `phimdl_casimir_3d1d_correction.py`, `phimdl_casimir_dimreg.py`, `casimir_clogfin_precision.py` marked superseded. |
| 2026-06-10 | Coupling sector: Z₇ degeneracy scope-qualified to the pure-φ sector; V_coupling = ε\|φ\|²(D_μχ)² (ε = 7/2) distinguishes vacua via Z_k = 1+2εφ_k² (Lean: `ZSevenVacuumSelection`); g = m_τ (CatB) and e²(Λ_GTE) = 7/2 (CatAL value) added. New §Gauge-coupling normalization: measured dissolution constant b = 1.189 ± 0.015 (stat) ± 0.047 (syst) (scripts `kink_form_factor_precision_*`), Λ_diss = 1495 ± 61 MeV; verdict +1.5σ (tree) / +1.3σ (quantum mass) — no anomaly. New §Kink-sector HVP: Δα_kink = 3.47–3.70×10⁻⁴ (CatA; script `kink_form_factor_delta_alpha_had.py`). Coupling-sector and form-factor scripts (32) graduated to `scripts/` with campaign data. |
