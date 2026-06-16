# PROVENANCE — UGP Survey / Readers Guide

**Paper:** `ugp_survey_readers_guide.tex`  
**Status:** Internal — updated as the corpus evolves; not independently submitted  
**Last verified:** 2026-06-11

---

## Purpose

The Survey / Readers Guide (P00) is a companion document that summarises all papers in the UGP physics series (P01--P51), provides reading-order recommendations, and contains a Predictions \& Verification summary section.

---

## Change Log

### 2026-06-11 — Continuum-limit, triangle-chain, and re-baselined fermion-RMS updates

**Changes to `ugp_survey_readers_guide.tex`:**

| Location | Change |
|----------|--------|
| P48 description + summary row | Page count updated to 346 / fourteen chapters; the Mathematical Substrate chapter (UGP/GTE arithmetic, UWCA, ontological ladder mathematical substrate → certificate → physical substrate) and the sequential MDL selection (Direct-Interpolation Lift, CatAL; Rule 110 as corollary) added |
| P49 description + summary row | T96-02 stated as a chain machine-certified link by link (cross-family coding inequality + within-class Direct-Interpolation Lift); sparsity-floor theorem and chirality census over all 120 family orderings ({Rule 110, Rule 124}, ordering = chirality gauge) added |
| P50 description + summary row | Continuum-limit results added: thermal ensemble as max-entropy shadow of the CMCA tape; exact chiral gap law Δ(β) = e^(−3β/2)(1+O(e^(−β/2))) with half-integer slope as parity-violation signature; Tape Saturation Theorem (conditional on the Compton-Support Criterion, proven minimal) selecting a = ℏc/Λ_GTE ≈ 0.0972 fm; ξ_kink = 7 cells substrate-MC target |
| P42 description + summary row | Lattice-campaign tape spacing noted as derived (Tape Saturation Theorem via P50); am_φ = 7/8 dictionary value; ξ_kink = 7 pre-registered target |
| P01 taxonomy example, headline list, predictions-table row | Charged-fermion RMS aligned to the canonical dual-path benchmark: 0.295% (PDG 2022 targets) and 0.261% (PDG 2024; the top-quark update moves the target toward the prediction) |

**Changes to `ugp_theory_overview.tex`:**

| Location | Change |
|----------|--------|
| Scale-hierarchy table + paragraph | Two-reading form: fine-end working hypothesis row (a ≈ ℓ_Pl) and MDL-saturated matter-sector reading row (a = ℏc/Λ_GTE ≈ 0.097 fm); paragraph rewritten — certificate carries no intrinsic spacing (Algebraic Descent, no-CA-replica); kink = 4.2×10¹⁹ cells at the fine end, exactly 7 cells at the matter-sector reading; separation = the Planck-hierarchy monomial 3¹⁰·7¹⁸/2⁴ |
| Two-level architecture | Ontological-ladder sentence added (roles axis orthogonal to the level scheme; normative statement in P48) |
| New-results narrative | New paragraph: P50 continuum limit, chiral gap law, Tape Saturation physical point, ξ_kink = 7 target; P48 capstone updated to 340+ pages / fourteen chapters with the Mathematical Substrate chapter and sequential selection; P49 sentence updated to the chain-certified T96-02 statement |
| SM headline list | Charged-fermion RMS 0.295% |

**Changes to `ugp_master_index.tex`:**

| Location | Change |
|----------|--------|
| `tab:mi-leptons` | Nine-fermion row re-attributed to the P01 dual-path verifier benchmark (0.295% vs PDG 2022 targets; 0.261% vs PDG 2024) |
| `tab:mi-computational` | New row: Direct-Interpolation Lift (UGP–p triangle spine) with the certified theorem chain (CatAL, zero sorry) |
| `tab:mi-phimdl` | New rows: chiral gap law (CatAD), substrate tape spacing at the matter-sector reading (Tape Saturation Theorem, CatAD conditional), ξ_kink = 7 cells falsifiable substrate-MC target |

### 2026-06-10 — Per-paper description accuracy audit + dependency-figure caption trim

**Changes to `ugp_survey_readers_guide.tex`:**

| Location | Change |
|----------|--------|
| Figure 1 caption | Rewritten to one-third of its prior length (per-paper enumeration removed; all cut content verified present in the body group descriptions); figure + legend + caption now fit one page |
| P27 description + summary row | `v_PSC` grade corrected [A−] → [A_Lean] (zero open axioms; `psc_ew_entropy_maximization` is a proved theorem); OP9 theorem name corrected to `srrg_op9_biconditional`; remaining gap corrected to `UGPSubstrateConstraint` |
| P01/P27 rows (summary + predictions tables) | Same `v_PSC` grade correction |
| P34 description + summary row | Degree-exact TPC shadow (Turing degree exactly 0′) added |
| P38 description | One-loop correction named correctly (Coleman–Weinberg) and hierarchy corrected 10⁴⁵ → 10⁴² |
| P39 description + summary row | Derived seven-kink EFT threshold Λ_GTE = 7·M_kink ≈ 2.0 GeV added |
| P42 description + summary row | Quantum kink mass M^Q = 281 ± 21 MeV, e²(Λ_GTE) = 7/2 scale-band consistency (+1.3–1.5σ), Δα_kink HVP prediction added; thermal-state grade corrected to CatAL conditional |
| P44 description + summary row | Stale initial-condition domain-wall dissolution claim replaced with the dynamical bias-annihilation resolution (P47) |
| P45 summary row | Gravity entry corrected to the continuum-limit force law F = G_eff M/(4πb²) (CatAD) |
| P46 description + summary row | PMDL–Λ duality (record/measure sectors of one generating functional; census-capacity Ω_Λ = 0.6899) added |
| P47 description + summary row | Irreducible-spread sentence replaced by the structural bracket theorem (carrier floor / capacity ceiling, GTE-atom inequality CatAL), the degree-0′ left-c.e. classification of Ω_Λ, and the measurement-free N_gen = 3 pincer; H₀ prediction row grade corrected to B |
| P48 description + summary row | Page count corrected to 320; Three-Level MDL Unification, degree-0′ adjudication, Ω_Λ bracket, and zero-relic defect resolution added |
| P49 description + summary row + Group 9 intro | Master-quadratic duality, Eisenstein residue-field model, biquadratic compositum, AGL(1,7) chiral reflection, Vacuum Uniqueness Theorem, dynamical zeta factorizations, period-475 attractor factorization added; candidate count corrected to 10²⁹⁰ |

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
