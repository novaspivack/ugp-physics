# PROVENANCE — UGP Survey / Readers Guide

**Paper:** `ugp_survey_readers_guide.tex`  
**Status:** Internal — updated as the corpus evolves; not independently submitted  
**Last verified:** 2026-06-01

---

## Purpose

The Survey / Readers Guide (P00) is a companion document that summarises all papers in the UGP physics series (P01--P47), provides reading-order recommendations, and contains a Predictions \& Verification summary section.

---

## Change Log

### 2026-06-01 — Prediction register expansion (P02, P03, P29, P47)

**Changes to `ugp_master_index.tex`:**

| Location | Change |
|----------|--------|
| New `tab:mi-novel-particles` | 9 genuinely novel GTE candidates (P02 register) with masses, $n$-values, confidence |
| New `tab:mi-dark-sector` | P29 dark-sector predictions (masses, $Q=0$, $R_{\rm dark}$, $\Lambda_{\rm dark}$, $\eta_\chi$, etc.) |
| `tab:mi-nuclear` | Added $N=184$, IPT $\kappa$ match, $F_{10}$ feature; clarified 6-term stability CV |
| `tab:mi-ew` | Added P14 bare coupling-ratio predictions ($g_1^2/g_2^2$, $g_3^2/g_2^2$) |

**Changes to `ugp_survey_readers_guide.tex`:**

| Location | Change |
|----------|--------|
| Falsifiability table | Scope P01--P47; P03 $\Delta_{\rm pair}$ confirmed; P33 $\eta_B$; P47 $\Omega_\Lambda$, CKM $\delta_{CP}$, $C_{\rm Gorard}$, $\Sigma m_\nu$; forward P47 kink/PBH and $V_{\max}$ |
| P02/P03 narrative | Corrected 9 novel vs 11 candidates; 6-term stability law; cross-refs to Master Index tables |
| Reusable tools | Points to `tab:mi-novel-particles` |

### 2026-05-12 — Cross-paper consistency update

**Changes to `ugp_survey_readers_guide.tex`:**

| Location | Change |
|----------|--------|
| P01 description | Added: Λ at 0.31σ (Planck 2018, SM-17 confirmed); λ_H = φ/(4π) at 0.26σ (SM-18, new); m_H 9.1σ tension; 9-fermion RMS drift 0.293%→0.366% PDG 2024 |
| P01 table row | Added SM-17, SM-18 confirmed; m_H 9.1σ tension; α_s drift noted |
| P02 table row | Added: All 11 GTE mass windows OPEN under lab limits; GTE-P7 Q=0 search = mono-photon/missing energy |
| P03 table row | Corrected: 6-term stability 96.1% CV (threshold bug fixed); 9-term 87.7% OOD; IPT κ ratio 1.1494 (1.63%) |
| P13 table row | Added: w₀=−1 maintained; 3.5σ DESI DR1 tension; DESI DR3 as falsification criterion |
| P21 description | Updated: NuFIT-5.2 → NuFIT 6.0; 0.4% → 0.16σ (0.52%); NH preferred 2.5σ (NuFIT 6.0) |

### 2026-05-11 — P01, P21, P03, P19 updates

| Location | Change |
|----------|--------|
| P01 description, line 177 | α_s σ: +0.36σ → +0.24σ (PDG 2024) |
| P01 description | Added m_W: tree-level +36σ → −0.42σ (PDG 2024); OP(viii) closed |
| P01 summary table row | Updated to α_s +0.24σ (PDG 2024); m_W OP(viii) closed |
| P21 summary table row | Updated to 0.16σ from NuFIT 6.0 (0.52%); NH preferred 2.5σ |
| P03 table row | Oracle stability 98.63% as primary; parsimony limit noted |
| P19 table row | Wolfenstein λ improved to ε₁^{α_d} = 0.2203 (1.9% off PDG; improved from 12%) |

- **2026-06-02:** D_top derivation upgraded to machine-certified (Lean 4, zero sorry). Added `z7_star_transitivity_under_addition`, `z7_symmetry_forces_equal_sector_action`, `d_top_derivation_chain_catal` to Appendix A.13. Updated Ω_DM h² table row and prediction table to reflect D_top CatAL.
