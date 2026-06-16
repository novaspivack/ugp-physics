# Direction H: PSC Entropy Functional for EW Phase Transition

**Status:** Long-term programme (estimated 3–5 years)  
**Difficulty:** Requires fundamentally new theoretical concepts  
**EPIC:** EPIC_051 Round 2, Direction H  
**Date:** 2026-05-15

---

## What Would Be Needed

The PSC cosmological constant derivation (P01 §SM-17) used a specific counting argument:

```
L_model = log₂(D₁ × 5³ / orbit_length) = log₂(2000/3) ≈ 9.38 bits
Λ_vac = (ln 2 / π) × L_model × H₀² / c²   → Λ at 0.31σ (Planck 2018)
```

where D₁ = 2000 = 2⁴ × 5³ arises from the GTE orbital degree-of-freedom count, and orbit_length = 3 from the PSC closure condition.

An analogous EW derivation would require all of:

1. A "PSC entropy of the EW vacuum state" S_PSC(v) at scale v
2. A closure condition δS_PSC/δv = 0 (or PSC minimality condition) that selects v
3. The integers {D_EW, ℓ_EW, ...} that parameterize the EW sector's PSC orbit structure
4. A Lean-certified computation of v from those integers

---

## Why This Is Hard

Unlike the cosmological constant case, the EW scale has no natural PSC orbital home:

- **L_model = log₂(2000/3)** uses the GTE orbit structure (D₁ = 2000, orbit = 3) which is directly given by the UGP machinery and has a clear combinatorial interpretation (degrees of freedom in the 5-prong GTE branching × 5³ from the three-prong recursion, normalized by the 3-element orbit of the PSC closure).

- **For the EW scale**, there is no known UGP orbital parameter at the EW energy scale. The VEV v is set by the Fermi constant G_F (which parameterizes 4-fermion interactions at low energies), which is a completely different physical mechanism from the UGP orbit structure. G_F has no known expression in UGP integers.

- **The hierarchy problem itself** (why v ≪ M_Planck) reflects the absence of any natural PSC orbit at v. If PSC had an orbit at v, the hierarchy would be explained — but that is precisely what we do not have.

- **Round 1 exhausted the search space** for PSC-type orbital formulas. Direction B (PSC orbital scan, Round 1) showed analytically that no combination of UGP-motivated integers D ∈ {2ⁿ·3ᵐ·5ᵖ} and ℓ ∈ {1,...,20} produces v at PDG precision. The analytical bound showed the required D/ℓ ratio (≈ 10^{65.2}) is not reachable with small-integer PSC parameters.

---

## Necessary Theoretical Prerequisites (in order)

These are non-trivial prerequisites, each requiring independent research:

### P1: UGP/PSC theory of spontaneous symmetry breaking (SSB)
- Current state: SRRG (P27) constrains the Higgs quartic coupling but does not derive v.
- What is missing: A PSC description of the Higgs field as a flow variable (not just a spectator).
- Estimated effort: 1–2 years.

### P2: Definition of "PSC entropy of the Higgs potential"
- The Higgs potential V(φ) = −μ²φ²/2 + λφ⁴/4 has two parameters: μ² and λ.
- λ is now UGP-derived (φ/(4π), MDL-certified). But μ² is not.
- "PSC entropy" would need to assign a bit-count to vacuum configurations, analogous to L_model above.
- What is missing: A definition of this entropy functional that does not reduce to just counting Higgs quanta (which would give μ² = M_Planck², not μ² ≈ v²).
- Estimated effort: 1 year of theoretical work once P1 is established.

### P3: Derivation of how PSC closure selects the SSB minimum
- PSC closure (the fixed-point condition of the PSC flow) selects special configurations.
- For the cosmological constant, closure selects the minimal description length.
- For the Higgs sector, closure would need to select the minimum of V(φ) at φ = v.
- What is missing: A PSC flow equation on the space of EW vacuum configurations.
- Estimated effort: 1–2 years.

### P4: Identification of the UGP integers that quantize the EW scale
- The key integers for Λ_vac are {D₁ = 2000, orbit = 3, H₀}.
- For v, we need analogous integers {D_EW, ℓ_EW, ...} from the UGP algebra.
- Current searches (Directions B, D in Round 1) found no such integers.
- This is the most speculative step: it may require discovering entirely new UGP structure.
- Estimated effort: Unknown — could be 1 year or could be intractable.

### P5: Lean-certified computation of v from those integers
- This step is tractable once P4 is established.
- The Lean machinery already exists (GaugeCouplings.lean, BraidAtlas/EWBosons.lean).
- Estimated effort: 3–6 months once P4 is done.

---

## Connection to Existing Work

| Work | Relevance | Status |
|------|-----------|--------|
| PSC cosmological constant (P01 SM-17) | Closest analogue — template for the programme | Lean-certified, published |
| SRRG Higgs quartic (P27 App B) | Structural consistency; λ_H constraint | B-grade, published |
| MFRR T8 universal holographic closure | Failed (81% error) but framework could be adapted | NEGATIVE |
| Direction B PSC orbital scan (Round 1) | Hard no-go for small-integer PSC parameters | NEGATIVE (analytical) |
| Direction C SRRG no-go (Round 1) | β_η flow cannot produce DT | NEGATIVE (analytical) |
| Direction F Higgs β_λ (Round 2) | β_λ ∝ λ² → DT integral diverges | NEGATIVE (Round 2) |

---

## What the Programme Is NOT

This programme does NOT include:

- Adjusting λ_H (already derived from MDL/SRRG). The quartic is settled.
- Improving the Level 1 m_H result (already done in Phase 1 of EPIC_051).
- Any model with new free parameters tuned to hit v = 246.22 GeV.
- Any result that cannot survive adversarial peer review.

---

## Recommended First Step (when resources allow)

Study the PSC cosmological constant derivation in depth (P01 §SM-17, MFRR paper §4–5) and ask:

> **What is the EW analogue of the orbital counting {D₁ = 2000, 5³ = 125, orbit = 3}?**
> Is there a UGP description of the Higgs field at the orbit level?

Specifically: the integer 2000 = D₁ counts something about the GTE spectrum. Is there a GTE orbit or mode at the EW scale that has a counting number of similar structure? If such an orbit exists, even approximately, it would be the seed of this programme.

---

## Milestone Structure (if pursued)

| Milestone | Deliverable | Estimated timeline |
|-----------|-------------|-------------------|
| M1 | PSC theory of SSB: first principles paper or tech note | Year 1–2 |
| M2 | PSC entropy functional S_PSC(v) defined and computable | Year 2–3 |
| M3 | Closure condition δS_PSC/δv = 0 formalized | Year 3–4 |
| M4 | UGP integers {D_EW, ℓ_EW} identified and motivated | Year 3–5 |
| M5 | Lean-certified v derivation, zero sorry | Year 4–5+ |

---

## Summary

Direction H is a genuine long-term open programme, not a near-term task. It is documented here to:

1. Record the structure of what would be needed for a Level 2 structural VEV derivation.
2. Prevent future rounds from re-discovering the same obstacles (Directions A–G are exhausted).
3. Orient future work: **the first step is finding a UGP orbital structure at the EW scale**.
4. Prevent premature closure: this problem is open and should remain open in all publications until solved.
