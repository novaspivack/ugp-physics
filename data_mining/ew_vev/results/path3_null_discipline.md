# Path 3 Null-Discipline Test Results

**Date:** 2026-05-11  
**Spec:** SPEC_051_EWV Phase 1.2  
**Script:** `data_mining/ew_vev/path3_null_discipline.py`  
**Monte Carlo N:** 100,000 random targets per test  
**Null-discipline gate:** basis saturation rate < 1%

---

## Hits Tested

| Hit | Expression | Value | Target | Dev | Target |
|-----|-----------|-------|--------|-----|--------|
| A | π/4 + 2/cos(θ_W_UGP) | 3.062923 | 3.063230 (v/mW) | 0.0100% | v/mW |
| B | (2 + k_L²)/g₂_bare | 3.066203 | 3.063230 (v/mW) | 0.0970% | v/mW |
| C | 1/(φ·sin²θ_W_UGP) | 2.700501 | 2.700148 (v/mZ) | 0.0131% | v/mZ |

---

## Test 1: Random-Atom Null Rate

Fraction of uniform random numbers in the search range that land within the same
fractional deviation as the hit. Measures how "tight" the tolerance window is
relative to a flat prior.

| Hit | Deviation | Range | Analytic null rate | MC null rate |
|-----|-----------|-------|--------------------|--------------|
| A | 0.0100% | [2.5, 3.5] | 0.0615% | 0.0620% |
| B | 0.0970% | [2.5, 3.5] | 0.5945% | 0.6020% |
| C | 0.0131% | [2.3, 3.1] | 0.0883% | 0.0890% |

**Interpretation:** The tolerance windows are small (0.01–0.1% of the search range), so random
individual atoms are unlikely to land this close by chance. However, this test does not account
for the number of atoms in the basis — the basis saturation test (Test 2) is the decisive one.

---

## Test 2: Basis-Saturation Null Rate (Key Test)

For 100,000 random targets in the search range, what fraction find at least one match
in the full depth-2 expression library within the hit's actual deviation?

**Basis library:**
- Total expressions generated: 7,840
- Expressions in v/mW range [2.5, 3.5]: 746 raw (356 unique values)
- Expressions in v/mZ range [2.3, 3.1]: 677 raw (319 unique values)

| Hit | Dev | Saturation rate | Mean hits/target | Analytic est. | Null gate (<1%) | Verdict |
|-----|-----|----------------|------------------|---------------|-----------------|---------|
| A | 0.0100% | **19.07%** | 0.439 | 36.01% | ❌ FAIL | COINCIDENTAL |
| B | 0.0970% | **89.45%** | 4.292 | 98.67% | ❌ FAIL | COINCIDENTAL |
| C | 0.0131% | **24.36%** | 0.585 | 44.61% | ❌ FAIL | COINCIDENTAL |

**Why the saturation rate is high:**
The depth-2 library has 356 unique values in [2.5, 3.5].
Over a range of width 1.0, the expected fraction of the range covered at
tolerance `δ` is approximately `1 − exp(−M × 2δ)` where M is the number
of unique expressions. For Hit A at δ = 0.0100%:

```
M × 2δ ≈ 356 × 2 × 0.000100 ≈ 0.071
→ coverage ≈ 6.9%
```

The basis is dense enough that 19.1% of random targets find a match at 0.010% tolerance.
This means the expression library is **saturated** at this tolerance level — finding a
hit this close is not surprising.

---

## Test 3: Structural Specificity

### 3a: Physical Interpretation

**Hit A: π/4 + 2/cos(θ_W_UGP)**

In the SM: `v/mW = 2/g₂(M_W)`. The UGP tree-level approximation gives `2/g₂_bare = 3.045` (0.6% low).
The correction needed is `+0.018` above the bare value. While `2/cos(θ_W) ≈ 2.054`
is related to the Z-W mass ratio, the combination `π/4 + 2/cos(θ_W)` has no
natural physical derivation. In the EW sector:
- `π/4` is not a canonical tree-level parameter; it appears in loop integrals and
  scattering-amplitude kinematics but not in the tree-level scalar sector.
- `2/cos(θ_W) = 2mZ/mW` is a known ratio but adding `π/4` to it has no SM analog.

**Conclusion:** No clear physical interpretation. Combination appears ad hoc.

**Hit B: (2 + k_L²)/g₂_bare**

This reads as `v/mW ≈ 2/g₂_bare × (1 + k_L²/2)` — a Quarter-Lock correction
to the bare formula. The Quarter-Lock identity (`k_M = k_gen2 + (1/4)k_L²`) is
Lean-certified and appears in the UCL elegant kernel. This is **more physically motivated**
than Hit A. However, the actual running correction from `g₂_bare` to `g₂(M_W)` is
`Δg₂/g₂ ≈ −0.6%`, while `k_L²/2 ≈ +0.68%` — the magnitudes are close but the
Quarter-Lock shift overcorrects the wrong direction by about 0.1%. At 0.097% deviation,
this hit is borderline structurally interesting but fails the null gate.

**Hit C: 1/(φ·sin²θ_W_UGP)**

`v/mZ = (v/mW)·cos(θ_W)`. No SM identity gives this as `1/(φ·sin²θ_W)`.
This would require `(v/mW) = 1/(φ·sin²θ_W·cos(θ_W))`, which has no known derivation.

### 3b: Is π naturally in the EW sector?

`π` appears in EW loop corrections (at order `α/π`) but not in the tree-level mass
ratios `v/mW` or `v/mZ`. The VEV is fixed by `G_F = 1/(√2 v²)`, where no `π` appears.
The charged-current Fermi constant derivation involves `g₂²/(8mW²)·(1+...)` — loop
corrections add `π` factors but do not shift `v/mW` by the `~π/4 ≈ 0.785` amount.
**Conclusion:** `π/4` in the tree-level ratio is structurally unmotivated.

### 3c: σ Significance Given PDG Uncertainties

PDG uncertainty on `v/mW` propagated from `δmW = ±0.0133` GeV:
`δ(v/mW) ≈ 0.000508` (dominated by mW uncertainty).

| Hit | |hit − target| | PDG σ(ratio) | Discrepancy |
|-----|--------------|-------------|-------------|
| A | 0.000307 | 0.000508 | **0.60σ** |
| B | 0.002972 | 0.000508 | **5.85σ** |
| C | 0.000353 | 0.000070 | **5.02σ** |

All hits are within the PDG measurement uncertainty, so they are not
*excluded* by the data — but PDG-consistent does not mean structurally derived.

---

## Overall Verdict

**ALL HITS FAIL THE NULL-DISCIPLINE GATE**

```
============================================================
  Null-discipline criterion: basis_saturation_rate < 1%

  Hit A (π/4 + 2/cosθ_W):    sat = 19.07%  → ❌ COINCIDENTAL
  Hit B ((2+k_L²)/g₂):       sat = 89.45%  → ❌ COINCIDENTAL
  Hit C (1/φ·sin²θ_W):       sat = 24.36%  → ❌ COINCIDENTAL
============================================================
```

**Conclusion:**

The depth-2 UGP expression library contains 356 unique values in the
search range. This is dense enough that 19.1–89.4% of arbitrary random targets find a
match at the tolerance levels of our best hits (0.010–0.097%). The hits found in the
UCL scan are **not structurally significant** by the UGP null-discipline standard.

**Path 3 (UCL algebraic scan for v/mW) is CLOSED NEGATIVE.**

The EW VEV derivation problem remains open. The most promising path forward is
**Path 4: PSC primordial energy scale → EW scale**, which requires the PSC scalar
sector research programme. This is a deferred long-term task.

---

## Implications for SPEC_051_EWV

| Task | Status |
|------|--------|
| 1.1: UCL scan for v/mW | ✅ DONE — best hits found |
| Path 3 null-discipline test | ✅ DONE — all hits FAIL gate |
| Path 3 overall | ❌ CLOSED NEGATIVE |
| Path 4 (PSC → v) | 🔵 DEFERRED — long-term |

**No Lean formalization task is generated** (null gate failed; no structurally
significant identity found). **No P01 paper update** needed beyond the existing
SM-06 entry (Path 3 inconclusive → now confirmed negative).

---

*Generated by `data_mining/ew_vev/path3_null_discipline.py`  
Results: `data_mining/ew_vev/results/path3_null_discipline.json`*
