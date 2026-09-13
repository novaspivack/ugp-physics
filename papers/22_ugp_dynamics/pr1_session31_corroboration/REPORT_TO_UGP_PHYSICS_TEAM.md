# PR-1 / Logos CA Computational Bridge Report

**From:** Nova Spivack, Particle Derivations repo (PR-1 CA experiments)  
**To:** ugp-physics team  
**Date:** 2026-04-25  
**Session:** session 31_UGP_DYNAMICS_BRIDGE  
**Source spec:** `WORKING_NOTES/PR1_DYNAMICS_BRIDGE.md` (from internal spec note 017-097)  
**Status:** Corroborating computational evidence — see limitations section before use

---

## Purpose and Scope

This report delivers the three experimental measurements requested in the PR1_DYNAMICS_BRIDGE spec, plus one additional comparison test. The experiments run PR-1 CA simulations and measure whether the computational structure found in Sept–Oct 2025 corresponds quantitatively to the formal results proved in the P23 dynamics-paper Lean layer.

**These results are intended as corroboration only.** They do not constitute formal proofs. They cannot substitute for Lean theorems. They provide computational backing for observations already noted qualitatively in internal spec note 017-097 and cross-referenced in MASTER_STATUS.md. See the limitations section before drawing any conclusions.

---

## ⚠️ LIMITATIONS AND CAVEATS (Read First)

**1. Braid detection is not the standard pipeline for Actions 2 and 3.**  
The standard PR-1 particle detection pipeline (BraidExtractor + TopologicalSpectrometer) uses m-field kinks to identify particles. In the Logos Alpha rule (`p3:p3, identity, q1, g0!=g1`), the X clause has `x_transform='id'` (identity) — meaning the m field is **frozen at its initial values throughout the simulation**. The standard pipeline would detect only static initial m-domain walls, not dynamically formed particles. Action 2 uses a simplified domain-wall proxy (g-field based) as a substitute. This is NOT comparable to previous PR-1 session results and should not be cited alongside them.

**2. Initial conditions matter and required correction.**  
The initial Action 1 run used simple random initialization, which gave meaningless results (~25%). The correct canonical initialization — two-cluster (60% density in two spatial clusters, zero background) — is what the historical PR-1 experiments used and is what gives physically meaningful results. All reported results use canonical initialization. Simulations without two-cluster initialization of the correct form cannot reproduce these results.

**3. The bijection methodology required correction.**  
The bijection between Z₄ and SM winding must be applied to **pre-R g values** (the particle-identity g field before the R clause scrambles it) not to post-R values. Using post-R values gives ~25% (noise). All reported results use pre-R values. This distinction is specific to the Logos Alpha rule where R always fires unconditionally.

**4. These are single-field approximations.**  
The PR-1 CA has four fields: g (Z₄ phase), l (Z₈ slope), mu (signed slope change), m (parity bit). The Logos Alpha rule makes only g and l dynamic (mu and m are frozen). The results here measure the g-field correspondence to SM winding only. The full four-field structure may give different results and is not tested here.

**5. Python 3.9 compatibility note.**  
The main PR-1 CA engine file uses Python 3.10+ syntax (union type hints). These experiments use a self-contained Python 3.9-compatible reimplementation of the Logos Alpha rule kernel, validated to match the engine's g-field and l-field dynamics for this specific rule. Results are consistent with the documented rule behavior.

---

## Action 1 — Z₄ → Winding Bijection

### Question
Does the Z₄ phase field of the Logos Alpha CA empirically correspond to the SM winding table {−3, 0, +2, −1}?

### Method
Run Logos Alpha (`p3:p3, identity, q1, g0!=g1`) with canonical two-cluster initialization (N=256, 500 steps per seed, 8 seeds: 42, 0, 7, 13, 99, 123, 256, 777; total 1,024,000 pair-interaction events). Apply the natural P23 bijection (φ: 0→ν(W=0), 1→d(W=−1), 2→u(W=+2), 3→e(W=−3)) to pre-R g values. Classify each event against the C4 condition (SM-allowed ↔ |ΔW|∈{0,3}).

### Results

**87.38% consistency** with the C4 condition (range 83.1%–90.2% across 8 seeds).

Confusion matrix (1,024,000 events combined):

```
                        |ΔW|∈{0,3}     |ΔW|∉{0,3}
  S-fired (True):   A = 518,672    B = 129,252
  S-fired (False):  C =       0    D = 376,076
```

**C = 0 exactly across all seeds.** Every non-firing event is correctly classified as a non-SM-allowed interaction (D quadrant).

Distribution of pre-R Δg values (canonical init):
- pre-R Δg=0 (same-type, |ΔW|=0): ~36.7% → post-R Δg=2 → S fires → A (correct)
- pre-R Δg=1 (mixed): ~13.3% → fires → 50% A (doublet), 50% B (forbidden)
- pre-R Δg=2 (|ΔW|=2, forbidden): ~36.7% → post-R Δg=0 → S does NOT fire → D (correct)
- pre-R Δg=3 (mixed): ~13.3% → fires → 50% A (doublet), 50% B (forbidden)

**All 24 bijections ranked:** The top 16 bijections (ranks 1–16) all achieve C=0 and split into two tiers (87.38% and 86.01%). The natural P23 bijection is co-best at rank 4 (tied with 7 others). The bottom 8 bijections have C≠0 and achieve only ~36.6%.

### Key Structural Finding

The R clause (p3 rotation, always fires) maps every pre-R Δg=2 pair to post-R Δg=0 (no fire). Under the natural bijection, ALL pre-R Δg=2 pairs have |ΔW|=2 — exactly the cross-family forbidden interaction class. R completely and selectively suppresses this class with zero exceptions. This is not statistical: C=0 is exact.

The 12.62% residual inconsistency (B quadrant) comes from pre-R Δg∈{1,3} pairs where |ΔW|=3 (SM doublet, should fire) and |ΔW|=1 or |ΔW|=5 (forbidden, should not fire) cannot be distinguished by the g-field alone.

### Verdict

**YES — strong corroborating evidence.** The Z₄ phase field encodes the SM winding table at 87.38% fidelity under the natural P23 bijection. The R clause mechanically implements the |ΔW|=2 suppression exactly (C=0). The natural bijection is co-optimal among all 24.

**Relevance to the P23 dynamics-paper Lean layer:**
- **Spec 017-22 (Topological Minimality):** Quantifies primitive cobordism selection rate at 87.38%. The R-clause mechanism is the CA model for |ΔW|=2 exclusion.
- **Spec 017-25 (Discrete Action):** Quantifies the Logos condition's action-minimization fidelity at 87.38%. stepCost=0 interactions are selected at this rate.

---

## Action 2 — Dark Sector Gap

### Question
Do stable exotic braid configurations (not matching SM particles) cluster at the predicted dark sector winding values W ∈ {1, −2, 4}?

### Method
Run Logos Alpha with canonical two-cluster initialization across 37 runs (7 NPZ archives + 30 new runs, N=128, 500 steps, seeds 0–29). Detect stable domain-wall bracket pairs (proxy for braid configurations). Classify by interior g-value mapped through natural bijection.

### Results

- 38,552 braid structures detected, **100% SM-compatible** winding
- **0 exotic braids** (W ∉ {−3, 0, +2, −1}) detected

SM winding distribution:
- W=0 (neutrino-like): 50.7%
- W=+2 (quark-like): 45.6%
- W=−3 (electron-like): 1.9%
- W=−1 (down-quark-like): 1.8%

### Verdict

**INCONCLUSIVE — method insufficient.** The domain-wall proxy is by construction limited to structures whose interior g-value maps into the Z₄ set (which by definition gives only SM winding values). Detecting exotic multi-domain topological braids — which is what the dark sector gap prediction requires — needs the full TopologicalSpectrometer with a Logos-appropriate (g+l-field based) particle detection method.

**The zero-exotic result is NOT evidence that exotic braids don't exist.** It is evidence that this simplified method cannot find them.

**Side finding (potentially meaningful):** The SM winding distribution is strongly asymmetric — W=0 and W=+2 dominate (96%). The mean net Z₄ topological winding of the field is ~71 (non-zero), suggesting the Logos Alpha dynamics break Z₄ symmetry and favor a specific topological sector. This is unexpected and may be worth investigating separately.

**Spec 017-098 §2.2 status:** Remains [O]. Full spectrometer run needed.

---

## Action 3 — Hypercharge Slope Factor

### Question
Does the q1 shear in the Logos Alpha rule encode the hypercharge factor of 2 (Y₃ = 2W)?

### Method
Run Logos Alpha and three shear variants (q0, q1, q2, q3) with N=64, 500 steps, seed=42. Record Δl (slope change) and |ΔW| (winding difference under natural bijection) at each S-firing event. Compute mean Δl_total/ΔW ratio.

### Results

| Shear | Δl_per_cell | Mean Δl_total/ΔW | Δl_total/ΔW for |ΔW|=3 specifically |
|-------|------------|-----------------|--------------------------------------|
| q0 | 0 | 0.000 | 0 |
| q1 | 1 | **0.955** | **0.667** |
| q2 | 2 | 1.910 | 1.333 |
| **q3** | **3** | **2.865** | **2.000 exactly** |

**ΔW distribution across all S-firings:** |ΔW|=3 (SM doublet) = 33.7% — the most common single type.

No stable particle worldlines could be extracted (g-field changes every step due to R always firing; requires m-field kink tracking for worldline analysis, which is unavailable in Logos Alpha since m is frozen).

### Verdict

**INCONCLUSIVE for q1, PARTIAL for q3.** The Y=2W factor of 2 does not hold for q1 shear at doublet interactions (Δl_total/ΔW = 0.667, not 2.0). However, under **q3 shear**, the Y=2W relationship holds **exactly** (Δl_total/ΔW = 6/3 = 2.000) for all SM doublet transitions (|ΔW|=3, which are the most common firing type at 33.7%).

The q1 shear gives Δl_total/ΔW = 2.000 for |ΔW|=1 transitions (non-doublet, cross-family). So q1 encodes Y=2W but for the wrong interaction class.

**Research lead for Spec 017-27:** If the COM search were rerun with q3 shear and evaluated with a hypercharge-correspondence criterion in addition to particle detection, q3 might be competitive with q1. The factor-of-2 is present in the slope dynamics but is in the q3 channel, not q1.

---

## Action 4 — Full 3-Involution Rule Comparison (Additional)

### Question
Does Rule R580997408235520 (`p1, swap_mu_flip_m, q1, g0!=g1`) — which uses X≠identity and makes mu and m dynamic — achieve higher SM bijection consistency than Logos Alpha?

### Method
Same setup as Action 1. Run R580997408235520 alongside Logos Alpha for comparison.

### Results

| Rule | Consistency | C=0? | Change vs Logos Alpha |
|------|------------|------|-----------------------|
| **Logos Alpha** | **87.38%** | **YES** | baseline |
| R580997408235520 | 69.04% | NO (31,687) | **−18.33%** |

**Why R580 is worse:** The `r_forbidden_mask=16` in R580 means R does not fire when Δl=4. For pre-R Δg=2 (|ΔW|=2 forbidden) pairs with Δl=4: R doesn't suppress them → S fires on them → forbidden |ΔW|=2 interactions leak through. The X clause fires only 1.5% of events — insufficient to compensate.

### Verdict

**Logos Alpha is the better rule for SM interaction selection.** The simpler "always-fire R" design achieves 100% |ΔW|=2 suppression. The conditional R in R580 breaks this guarantee. Adding X≠identity and dynamic mu/m fields does not improve and in this case substantially degrades the correspondence.

This does not mean R580 is a worse rule overall — it was optimal for different criteria (COM score, particle detection by other methods). It means the Logos Alpha rule's simple unconditional structure is specifically optimal for the bijection correspondence test.

---

## Summary Table

| Action | Verdict | Key Metric | P23 Target |
|--------|---------|-----------|----------------|
| 1 — Z₄ Bijection | **YES (strong)** | **87.38%**, C=0 exactly | 017-22, 017-25 |
| 2 — Dark Sector Gap | INCONCLUSIVE | 0 exotic found (method limited) | 017-098 §2.2 |
| 3 — Hypercharge | PARTIAL (q3 not q1) | q3 gives Δl/ΔW=2.000 for doublets | 017-27 |
| 4 — Better Rule | Logos Alpha wins | 87.38% vs 69.04% | 017-22, 017-25 |

---

## Recommended Use of These Results

**For Spec 017-22 and 017-25 (ready to use now):**
- The 87.38% figure and the C=0 result can be cited as computational corroboration of the C4 theorem's implementation
- The R-clause |ΔW|=2 suppression mechanism can be used as a concrete model for the primitive cobordism selection criterion in the Lean definition
- Cite as: "session 31 Action 1 (corrected): 87.38% ± 3% consistency with natural P23 bijection, C=0, N=256, 8 seeds, 1.02M events"

**For Spec 017-098 §2.2 (not ready):**
- Do not cite the zero-exotic result — it is a method artifact
- A proper test requires: TopologicalSpectrometer with g+l-field particle detection (not m-field kinks) on long runs (N≥512, T≥2000 steps)

**For Spec 017-27 (research lead only):**
- Note the q3 shear result as a research lead: "q3 shear gives Δl_total/ΔW = 2.000 exactly for SM doublet transitions"
- This is a lead for investigation, not a result to cite

**Do not cite Action 2 braid counts alongside previous PR-1 session results** — they use incompatible detection methods.

---

## Files

All session files are in:
```
Particle Derivations/Optimizer new tests/PR-1_UGP_Loop_CA/logos_search/
logos_derivation_experiment/SESSIONS/session 31_UGP_DYNAMICS_BRIDGE/
```

Key files:
- `action1_corrected_results.json` — full bijection data (1.02M events, 24 bijections, 8 seeds)
- `action4_results.json` — Logos Alpha vs R580 comparison
- `session 31_4_SYNTHESIS_AND_FINDINGS.md` — full internal session synthesis
- `session 31_5_ACTION4_BETTER_RULE_SPEC.md` — Action 4 spec

Scripts (committed to session, usable for replication):
- `action1_z4_winding_bijection_corrected.py`
- `action4_better_rule_comparison.py`
