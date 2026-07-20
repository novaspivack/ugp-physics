# Section Outline: PSC_Concordance.tex

**Full title:** Formal and Computational Concordance on PSC-Selected Standard Model Structure: Axiomatic Closure Theorems and Finite Universe Enumeration

---

## Abstract

Two-line concordance summary: formal (theorems from Papers 03, 05, 20, 21) and computational (TE2.2 scan over 20,160 universes). Key numbers: 12 PSC-survivors, D_min = 1.0667, sm_rank = 1. Residuals and caveats enumerated.

---

## 1. Introduction

- Central question: is the Standard Model contingent or structurally forced?
- The PSC (Perfect Self-Containedness) programme: overview and motivation
- Formal side: Papers 03, 05, 20, 21 — exclusions and Two-Layer Theorem
- Computational side: TE2.2 dissonance functional over 20,160 candidates
- Key observation: methodological independence and its limits
- **Organization paragraph** — maps to §§2–6 and appendices
- **Novel contribution paragraph** — four new contributions of this paper
- **Conventions paragraph** — notation for G_SM, N_gen, Ψ = (d, G, N_gen, N_obs, Λ, ρ, κ, τ)

---

## 2. The Two-Layer PSC Theorem: Formal Side

### 2.1 PSC, RC, and NM*
- Definition 2.1: Perfect Self-Containedness (five conditions: RC, NM*, Anomaly Cancellation, TV, SA)
- Remark 2.2: Scope of the axiomatic approach
- Theorem 2.3 (PSC Exclusions, Paper 03): GUT groups, vector-like fermions, CP-conserving theories excluded

### 2.2 The Two-Layer PSC Theorem
- Definition 2.4: Layer I (structural) and Layer II (information-theoretic) conditions
- Theorem 2.5 (Two-Layer PSC Theorem, Paper 05): Layer I forces G_SM and N_gen ≥ 3; Layer II selects N_gen = 3
- Remark: two genuinely distinct necessity mechanisms

### 2.3 The PSC Sieve and Residual Classification Conjecture
- Definition 2.6: PSC Sieve (ADMIT/REJECT decision procedure)
- Paper 20: Lean 4 formalization of all sieve constraints; SM passes, all known non-SM theories fail
- Definition 2.7: Residual Classification Conjecture (RCC)
- Theorem 2.8 (Conditional Existential Rigidity, Paper 21): If RCC, then SM is the only PSC-legal foundation

### 2.4 Status of Lean Formalization
- Layer I predicates, anomaly check, RC/NM*, PSC Sieve — all Lean 4
- Machine-verified SM passage certificates
- Zero sorry, no non-standard axioms

---

## 3. The TE2.2 Computational Certificate

### 3.1 Overview and Methodology
- Four-step approach: construct D[Ψ], parameterize, enumerate, identify minimum

### 3.2 The Universe Parameter Space
- Eight-parameter tuple: (d, G, N_gen, N_obs, Λ, ρ, κ, τ)
- Discrete ranges and grid sizes; Cartesian product = 20,160

### 3.3 The Dissonance Functional
- D[Ψ] = Σ w_i ‖C_i[Ψ]‖²  (14 terms, i = 1…14)
- Brief description of each C_i (full definitions in Appendix A)
- Remark: C_i are violation norms, not axioms

### 3.4 Scan Methodology
- Phase 1: Analytic constraint verification; Hessian at Ψ_SM
- Phase 2: Finite exhaustive enumeration; hard-filter pass/fail
- Phase 3: Extension to the continuum (density/continuity/compactness argument; not machine-checked)

### 3.5 Results
- Summary statistics: 20,160 total; 12 PSC-passing (0.06%); all 12 SM-like
- Global minimizer: D_SM = 1.066657903568035; four co-minimizers in (ρ, τ)
- SM rank: #1 out of 20,160
- Top-ranked structure: all four co-minimizers have (d, G, N_gen) = (4, G_SM, 3)
- Hessian stability: λ_min = 2.0 > 0
- PSC rarity: >99.9% rejected
- Table 1: TE2.2 scan summary statistics

### 3.6 Scope and Interpretation
- What the scan proves (computational certificate over discrete grid)
- What the scan does not prove (continuum, RCC, vector-like fermions)
- Relationship to Layer II (C_12, C_13 as necessary conditions from MDL)

---

## 4. Theory–Computation Concordance

### 4.1 Methodological Independence: Extent and Limits
- Formal side: no numerical computation; conclusions conditional on axioms
- Computational side: no deductive logic; conclusions are computational facts
- C_2 and C_3 encode SRRG fixed-point as partial SM prior
- Why partial dependence does not reduce concordance to tautology:
  (a) 12 other constraints are independent; (b) hard filters exclude C_2/C_3; (c) multi-constraint convergence is the core claim
- Recommendation: replace C_2's hardcoded SM check with derived SRRG test in future work

### 4.2 The Concordance Table
- Table 2 (full-width): 11 claims × {formal status, reference, computational status, TE2.2 evidence}
- Symbols: † for C_2/C_3-influenced rows; ‡ for RCC-conditional rows

### 4.3 Why the Agreement Strengthens the Case
- A priori divergence possibilities; neither happened
- Multi-constraint convergence across hard filters (C_2/C_3-free) and soft penalties
- Four specific concordance points:
  - d = 4 selection (C_1 vs RC/NM*)
  - G_SM selection (hard filter C_8 vs Layer I)
  - N_gen = 3 selection (C_2, C_12 vs Layer II/MDL)
  - Cosmological constant (C_14 gap of ~10 vs open formal problem)
  - PSC rarity (0.06% vs formal exclusion implications)

### 4.4 What the Concordance Establishes
- Proposition 4.1 (Concordance Conclusion): (d, G, N_gen) = (4, G_SM, 3) is the uniquely PSC-compatible tuple, formally (cond. on RCC) and computationally (cert. over 20,160)
- Emphasis: Proposition is a synthesis claim, not a deductive theorem

---

## 5. Residuals and Controlled Tensions

### 5.1 The Residual Classification Conjecture
- Most significant open front; what would resolve it
- RCC support: Thm 2.3, Thm 2.5, TE2.2 numerical evidence
- RCC limitation: finite grid does not cover all gauge groups or representations

### 5.2 The Discretization Gap
- Only 7 gauge groups; N_gen ≤ 4; continuous parameters discretized
- Analytic extension provides basis but does not eliminate gap

### 5.3 The Neutrino Sector
- Neither method addresses Dirac/Majorana, mass hierarchy, PMNS CP phase
- Explicit acknowledged scope limitation; further frontier for both methods

### 5.4 Vector-Like Fermion Representations
- Formal Thm 2.3(ii) excludes them; TE2.2 scan does not parameterize chirality
- Scope gap; future TE2.2 variant could close it

### 5.5 Falsifiability
- Formal: RCC falsified by explicit non-SM PSC theory; Lean sieve is machine-checkable
- Computational: falsified by Ψ' with D[Ψ'] < D_SM under same functional; data and code public
- Experimental: fourth chiral generation, GUT observation, or vector-like quarks/leptons at LHC

---

## 6. Conclusion

- Two-method concordance summary
- Formal side: Two-Layer Theorem + PSC Sieve, Lean 4 certified, conditional on RCC
- Computational side: D_min = 1.0667, four co-minimizers, sm_rank = 1, λ_min = 2.0; all 12 PSC-survivors SM-like
- C_2/C_3 partial dependence characterized; 12 independent constraints + hard filters converge
- Principal residuals: RCC, discretization gap, neutrino sector, continuum extension
- Working hypothesis: SM reflects a privileged self-consistent structure, not mere empirical fit
- Unconditional necessity awaits RCC resolution and strengthened independence

---

## Appendix A: The Fourteen TE2.2 Constraint Terms

Analytic definitions of C_1 through C_14 with formulas.

- C_1: Dimensional — (d−4)²
- C_2: SRRG Fixed Point — 1[G ≠ G_SM] + (N_gen − 3)²  [partial SM prior]
- C_3: SRRG Viability — max(0, F_max − F[S;Ψ])²  [partial SM prior]
- C_4: Quarter-Lock — (√3 g_1 − g_2)²
- C_5: RG Flow Stability — max(0, dc/dt)²
- C_6: Kähler Structure — ‖g_Fisher − ω_symp‖²_F  [hard filter]
- C_7: Area Law — (S_EE − A/4ℓ_P² − β log A)²
- C_8: Unitary Evolution — 1[CP-violation absent]  [hard filter]
- C_9: RIET Equivalence — ‖∇R − ∇T − ∇I − ∇C‖²
- C_10: Einstein Equations — ‖G_μν − 8πG T_μν‖²
- C_11: Coherence Field — ‖δS_coh/δΨ‖²
- C_12: Information Profit — max(0, 1.13 − ρ)²  [hard filter]
- C_13: Necessary Observers — max(0, 1 − N_obs)²  [hard filter]
- C_14: Lambda Relation — (log₁₀Λ − log₁₀(ln φ / ln 2π))²

Weight normalization note.

---

## Appendix B: Reproducibility

- Data location in ugp-physics repository
- SHA-256: `f810c1d2b07b598ef301205fee53512310552ea78cf8fb7476b3e9058d5fde93`
- Key JSON fields: total_universes, psc_universes, D_sm, D_min, sm_rank, elapsed_seconds, global_minimizer
- Code modules (seven files in phase2_truncation/ and phase1_constraints/)
- Lean formalization DOI: 10.5281/zenodo.19433538
- Step-by-step reproduction instructions
