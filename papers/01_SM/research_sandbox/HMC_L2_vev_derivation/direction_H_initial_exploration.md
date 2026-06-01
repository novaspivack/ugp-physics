# Direction H Initial Exploration: PSC Entropy Functional for EW Phase Transition
**Date:** 2026-05-15  
**EPIC:** EPIC_051 Round 2 / Direction H  
**Status:** Initial exploration complete — four findings, one significant lead

---

## 1. PSC Cosmological Constant Formula — Exact Decoded

From P01 §SM-17 (confirmed via numerical script):

```
L_model = log₂(D₁ × 5³ / 3)
        = log₂(2⁴ × 5³ / 3)
        = log₂(2000/3)
        ≈ 9.3808 bits

Λ = (ln2/π) × L_model × H₀²/c²
```

Verified at **+0.84% = 0.27σ** from Planck 2018 (paper quotes 0.31σ; small difference from precise H₀ value used).

### Meaning of each factor

| Factor | Value | Physical origin |
|--------|-------|-----------------|
| D₁ = 2⁴ | 16 | Discrete charge invariant (U(1) gauge normalization, CKM scaling) |
| 5³ | 125 | Rank-3 golden volume (golden-field exponent γ=3 acting on seed a₁=5) |
| orbit = 3 | 3 | Three-generation S₃ permutation quotient (electrons, muons, taus share seed) |
| ln2/π | 0.2206 | Kraft-length coefficient from MDL-minimal encoding |
| H₀ | measured | Hubble rate (external input; makes Λ dimensional) |

**Structural content:** The formula Λ = (ln2/π) × L_model × H₀² says the vacuum energy density is proportional to H₀² (the squared Hubble rate) with a structural proportionality factor (ln2/π) × L_model ≈ 2.07 that is purely combinatorial (MDL-forced, Lean-certified).

This formula is **not** an exponential hierarchy generator. It is a linear proportionality Λ ~ L × H₀². It works because Λ and H₀² are cosmologically coincident scales — both near the inverse-Hubble-radius-squared. The information content L ≈ 9.4 is an O(10) correction factor, not an exponential suppressor.

---

## 2. New Identity: L_model = log₂(D₁²/(3g₁²_bare))

This is a new algebraic observation not stated explicitly in the existing papers:

**Derivation:**  
From the gauge coupling master formula (P01 §gauge):
```
g₁² = L_{U(1)} × D_{U(1)} / 5^γ_{U(1)} = 1 × 16/5³ = D₁/5³
```
Since g₁² = D₁/5³, we have 5³ = D₁/g₁², and therefore:
```
D₁ × 5³ = D₁ × (D₁/g₁²) = D₁²/g₁²
```
Thus:
```
L_model = log₂(D₁ × 5³ / 3) = log₂(D₁²/(3g₁²))
```

Numerically: D₁²/(3g₁²) = 256/(3 × 16/125) = 256 × 125/48 = 2000/3 ✓

**Rewritten cosmological formula:**
```
Λ = (ln2/π) × log₂(D₁²/(3g₁²_bare)) × H₀²/c²
```

This connects the cosmological vacuum energy directly to the bare hypercharge coupling g₁. It shows that L_model is fundamentally an information measure about the **ratio of the U(1) charge invariant to the bare hypercharge coupling squared.**

---

## 3. SU(2) Structural Analogue: L_EW = log₂(D_SU2²/(3g₂²))

Given the identity in Section 2, the natural SU(2) structural analogue is:

```
L_EW = log₂(D_SU2² / (3g₂²_bare))
```

where:
- D_SU2 = 2329/432 (harmonic-mean invariant for SU(2), from P01 §gauge)
- g₂² = 2329/5400 (bare weak isospin coupling, Lean-certified)

**Numerical result:**
```
D_SU2²/(3g₂²) = (2329/432)² / (3 × 2329/5400)
               = 2329 × 5400 / (432² × 3)
               = 12,576,600 / 559,872
               = 22.4633

L_EW = log₂(22.4633) = 4.4895 bits
```

Note: For U(1), g₁² = D₁/5³ (Weyl order L_{U1}=1), so the formula D₁ × 5³ = D₁²/g₁² is exact.  
For SU(2), g₂² = 2 × D_SU2/5² (Weyl order L_{SU2}=2), so D_SU2 × 5² = (g₂²/2) × (5²/D_SU2) × D_SU2² = g₂² × 5⁴/2. The Weyl factor of 2 means:
```
Candidate 1 (no Weyl): log₂(D_SU2 × 5^γ / 3) = log₂(44.93) = 5.4895 bits
Candidate 2 (D²/3g²): log₂(D_SU2² / (3g₂²))  = log₂(22.46) = 4.4895 bits  ← chosen
Candidate 3 (+Weyl):   log₂(2 × D_SU2² / (3g₂²)) = log₂(44.93) = 5.4895 bits
```

Candidates 1 and 3 are identical (which makes sense: D_SU2 × 5^γ / 3 = L_{SU2} × D_SU2² / (3g₂²) since g₂² = 2 × D_SU2/5²).

---

## 4. Key Finding: L_EW ≈ π/ln2 (Self-Referential Near-Identity)

```
π/ln2 = 4.5324 bits
L_EW  = 4.4895 bits
Difference: −0.95%
```

The significance: if L_EW = π/ln2 *exactly*, then:
```
(ln2/π) × L_EW = 1
```

and the PSC EW formula `v² = (ln2/π) × L_EW × M_ref²` becomes **v² = M_ref²**, a self-referential fixed point. This would make `v` its own reference scale — a PSC attractor that "selects itself."

**Numerical check of this near-identity:**
- L_EW = log₂(D_SU2²/(3g₂²)) = log₂(22.463) = 4.4895 bits
- π/ln2 requires the argument to be 2^(π/ln2) = e^π = 23.141
- Actual argument: 22.463
- Discrepancy: (23.141 − 22.463)/23.141 = 2.9%

**The near-identity is NOT exact** at the level of the known rational values of D_SU2 and g₂². It would require:

```
D_SU2² / (3g₂²) = e^π  exactly
```

which is a transcendental number, and D_SU2, g₂² are rational. So this cannot hold as an algebraic identity. However, the 0.95% discrepancy is intriguing and may reflect a deeper near-resonance in the UGP algebra.

**What the self-referential formula would mean physically:**  
If (ln2/π) × L_EW = 1, the formula `v² = (ln2/π) × L_EW × v²` has any v as a solution. The condition would not *select* v — it would make v a *consistent* scale for any value. This is not a derivation of v but a self-consistency condition. The physical content would be: "the EW VEV satisfies a PSC self-referential closure condition with L_EW = π/ln2 bits of EW vacuum information." The *magnitude* of v would still require an external scale anchor.

---

## 5. Form C — The Most Striking Numerical Finding

Testing the formula `v² = (ln2/π) × L_EW × M_ref²`:

If L_EW = 4.4895 bits:
```
M_ref² = v_PDG² / ((ln2/π) × L_EW)
M_ref  = 246.22 / √(0.2206 × 4.4895)
       = 246.22 / 0.9953
       = 247.39 GeV
```

**The required reference scale is M_ref = 247.39 GeV, only 0.48% above v_PDG = 246.22 GeV.**

This is the most striking numerical result of this exploration. Under the formula v² = (ln2/π) × L_EW × M_ref², the self-consistent solution is nearly M_ref ≈ v — within 0.48%.

**Interpretation:** The formula `v² = (ln2/π) × L_EW × v²` would require (ln2/π) × L_EW = 1 exactly for self-consistency. We get (ln2/π) × 4.4895 = 0.9905, a 0.95% deficit. This is NOT a derivation of v — it says v is approximately (but not exactly) a self-referential PSC fixed point under the EW gauge structure.

**What additional precision is needed:** If the SU(2) coupling structure were corrected by loop running at scale v, perhaps the running L_EW(μ=v) shifts from 4.4895 to exactly π/ln2 = 4.5324 bits. This is a concrete calculable target.

---

## 6. Why the PSC Linear Formula Cannot Generate the EW Hierarchy

**The fundamental obstacle** (proven by the exploration):

The PSC cosmological formula Λ = (ln2/π) × L × H₀² is a *linear* formula that relates two nearly-equal scales. It explains WHY Λ ~ H₀² (cosmological coincidence) by saying Λ/H₀² = (ln2/π) × L ≈ 2, an O(1) structural ratio.

For the EW VEV, v/M_Pl ~ 2 × 10⁻¹⁷. The required quantities are:

| Formula form | L_EW required | Comment |
|-------------|---------------|---------|
| v² = (ln2/π) × L × M_Pl² | ~10⁻³³ bits | Non-physical |
| v = M_Pl × 2^(−L) | 55.5 bits | No symmetry counting gives 55 bits |
| v² = (ln2/π) × L × v² | L = π/ln2 = 4.53 bits | Self-referential — doesn't fix magnitude |

**Conclusion:** No PSC-type linear or simple exponential formula can derive v from M_Pl using small-integer EW symmetry counts. The hierarchy is real and requires a genuinely different mechanism (RG running, dimensional transmutation, or a novel PSC flow equation on the Higgs potential — see Direction H programme).

---

## 7. GTE Orbit Structure at EW Scale

The GTE orbit parameters (n=10, seed (1, 73, 823), R₁₀ = 1008, D₁ = 16) operate at the MeV-scale:

| Ratio | Value | Status |
|-------|-------|--------|
| v/E_base | 537,012 | Not a simple structural integer |
| v/m_e | 481,840 | Requires calibrated m_e |
| v/seed_b (in MeV/73) | 3,373 MeV | No structural meaning |
| v/m_H | 1.967 ≈ 1/√(2λ_H) | Forced by λ_H = φ/(4π) |
| v/m_t | 1.426 ≈ √2/y_t | Yukawa y_t ≈ 0.935 |

The GTE orbit does not connect to the EW scale. E_base requires calibration and cannot anchor a structural derivation. The ratio v/m_H = 1/√(2λ_H) ≈ 1.97 is structurally forced once λ_H = φ/(4π) is known — but this just links v to m_H, not to any UGP-structural mass scale.

---

## 8. Best Leads for Round 3 of Direction H

### Lead H.1 (Best): The Loop-Corrected L_EW Question

**Question:** Does L_EW(μ=v) = π/ln2 when computed using the **running** g₂(v) rather than the bare g₂?

Under RG running: g₂_bare ≈ 0.6567 → g₂(M_Z) ≈ 0.6516 (from SPEC_046_MWR).  
The running D_SU2(μ) would shift L_EW(μ). Compute:

```
L_EW(μ=v) = log₂(D_SU2²(μ=v) / (3g₂²(μ=v)))
```

If this equals π/ln2 = 4.5324 bits at μ = v (where v is the physical EW VEV), then:
- The self-referential condition (ln2/π) × L_EW = 1 would be satisfied exactly at μ = v
- This would provide a **PSC closure condition** selecting μ = v as the unique fixed point
- It would be a genuine Level 2 result: v defined as the scale where the EW PSC entropy achieves self-referential closure

**This is the most concrete calculable target emerging from this exploration.**

### Lead H.2: The Rational Near-Miss

**Question:** Is D_SU2²/(3g₂²) = 22.463 close to 22 = 2 × 11, 22.5 = 45/2, or some other simple rational with structural meaning?

- 22.463 ≈ 22 + 0.463 ≈ 22.5 − 0.037 ≈ 45/2 − small
- 45/2 = 22.5: log₂(22.5) = 4.4919 bits (vs 4.4895; difference of 0.024 bits)
- 22 = 2 × 11 = 2c(W) where c(W) = 11 (Lean-certified EW boson braid number!): log₂(22) = 4.4594 bits

**Specifically:** D_SU2²/(3g₂²) ≈ 2 × c(W) = 22?  
Exact: D_SU2²/(3g₂²) = 22.4633 vs 2 × 11 = 22 → difference 2.1%. Not exact, but intriguing given c(W) = 11 is Lean-certified.

### Lead H.3: The PSC Entropy Definition Question

**The theoretical prerequisite:** Direction H programme identifies P1 (UGP/PSC theory of SSB) as the missing prerequisite. Before any formula can be verified, we need a principled definition of "PSC entropy of the Higgs vacuum."

**Proposal for first-principles approach:**  
The Higgs vacuum |φ₀|² = v²/2 breaks U(1)×SU(2) → U(1)_EM. In UGP language, each vacuum configuration is an orbit of the PSC flow. The PSC entropy S_PSC(v) of a vacuum at scale v would be:

```
S_PSC(v) = − ∑ p_i log₂(p_i)  over PSC orbits at scale v
```

The closure condition δS_PSC/δv = 0 selects the physical vacuum. If S_PSC(v) can be computed from UGP structure (using G₁, D_SU2, g₁, g₂), its minimum/fixed-point selects v.

**What's missing:** The mapping from UGP orbit structure to Higgs vacuum orbits. This is the M-year research programme.

---

## 9. Summary Table

| Finding | Status | Significance |
|---------|--------|--------------|
| L_model = log₂(D₁²/(3g₁²)) | **NEW EXACT IDENTITY** | Connects cosmological bit-length to bare U(1) coupling |
| L_EW = log₂(D_SU2²/(3g₂²)) = 4.490 bits | **NEW STRUCTURAL QUANTITY** | Natural SU(2) analogue of L_model |
| L_EW ≈ π/ln2 = 4.532 bits within 0.95% | **NEAR-IDENTITY** | Would be exact self-referential PSC fixed point if equality held |
| M_ref = 247.4 GeV for Form C | **0.48% from v_PDG** | PSC formula self-consistent near v |
| Loop correction L_EW(μ=v) = π/ln2? | **OPEN LEAD** | Most concrete calculable target for Round 3 |
| PSC linear formula fails for hierarchy | **PROVEN NO-GO** | Requires different mechanism than cosmo analogy |
| GTE orbit doesn't connect to EW scale | **CONFIRMED NO-GO** | v/E_base not a structural integer |
| D_SU2²/(3g₂²) ≈ 2×c(W) = 22 | **SUGGESTIVE** | 2.1% off; c(W)=11 is Lean-certified |

---

## 10. What Round 3 of Direction H Should Be

**Priority 1 (concrete, calculable):**  
Compute L_EW(μ) = log₂(D_SU2(μ)²/(3g₂(μ)²)) as a function of renormalization scale μ, using the two-loop running code in SPEC_046_MWR. Check whether L_EW(μ=v) = π/ln2 exactly (or to what precision). If the gap closes under running, report the scale at which it closes.

**Priority 2 (structural):**  
Investigate whether D_SU2²/(3g₂²) ≈ 2 × c(W) is an exact algebraic identity in the UGP algebra (unlikely given rational D_SU2, g₂², but should be checked). If not exact, determine what rational number D_SU2²/(3g₂²) equals and whether it has a structural interpretation.

**Priority 3 (theoretical):**  
Draft the first-principles definition of S_PSC(v) — the PSC entropy of the EW vacuum — using the UGP orbit structure. This is the M1 milestone of the Direction H programme. It requires understanding what "orbits" the Higgs vacuum configuration lives on under the PSC flow, which is the key open theoretical question.

---

## Script and Artifacts

Script: `papers/01_SM/research_sandbox/HMC_L2_vev_derivation/direction_H_psc_exploration.py`  
Run: `python3 direction_H_psc_exploration.py` (produces all numerical results above)
