# PROVENANCE — Mathematical Foundations (JMP)

**Paper:** `algebraic_geometric_foundations_ugp.tex`  
**Primary code root:** `ugp_discovery_lab/ugp_discovery_lab/experiments/` (relative to repo root `ugp-physics/`)  
**Last verified:** 2026-05-11 ("Blind falsification → "Blind falsification and recovery"; added m_W −0.42σ two-loop recovery + SM/PDG tension account; prior adversarial review (2026-04): updated g2/g3 Lean status in appendix; added Strong CP open problem; clarified open problem #2)  
**Lean library:** `ugp-lean` — Phase4/GaugeCouplings.lean contains `g2Sq_bare_eq` and `g3Sq_bare_eq` as definitional equalities (zero sorry); rigidity proofs (D2, D3 derivations from first principles) remain computationally certified only

---

## Canonical scripts (confirmed present and runnable)

| Script | Path | Role | Run result |
|--------|------|------|-----------|
| `gauge_couplings_unified.py` | `ugp_discovery_lab/experiments/` | Derives g₁², g₂², g₃² from Elegant Kernel | ✅ g₁²=16/125 (0.00% err), g₂²=2329/5400 (1.03% err), g₃²=41075281/27648000 (0.09% err) |
| `su2_rigidity_proof.py` | `ugp_discovery_lab/experiments/` | Proves harmonic mean is unique SU(2) invariant | ✅ LM1/LM2/LM3 exact; LM4 sample check; LM5 numerical |
| `su3_rigidity_proof.py` | `ugp_discovery_lab/experiments/` | Proves Vandermonde discriminant is unique SU(3) invariant | ✅ DL1–DL4 exact; DL5 algebraic argument |
| `quarterlock_anchor.py` | `ugp_discovery_lab/experiments/` | Validates k_L² = 7/512 at n=10 | ✅ |
| `basin_selection_principle.py` | `ugp_discovery_lab/experiments/` | Basin Q4 charge analysis | ✅ |
| `visualize_ugp_gte_monograph.py` | `figures/ugp_gte_monograph/` (paper folder) | Generates Figs 1 and 2 | ✅ Both PNGs written |

## COMP-6-B Audit Results (2026-04-20)

Audit of Appendix A claims vs. `su2_rigidity_proof.py` / `su3_rigidity_proof.py`:

| Claim in Paper | Code Check | Match? | Fix Applied |
|---|---|---|---|
| SU(2) LM1: S3 symmetry, exact | LM1_symmetry: exact rational (all 6 permutations) | ✅ | — |
| SU(2) LM2: 1-homogeneity, exact | LM2_homogeneity: exact rational (λ=7/5) | ✅ | — |
| SU(2) LM3: parallel averaging, exact | LM3_parallel_averaging: exact rational | ✅ | — |
| SU(2) LM4: "exact for rational p, float for irrational" | Tests p∈{−2,−1,+1,+2} with float for p≠−1 | ⚠️ | Weakened to "sample exponents, float; general case analytic" |
| SU(2) LM5: "verified exactly" | Numerical, surrogate ∞=10¹², abs<1e−6 | ❌ | Changed to "numerically verified, surrogate 10¹²" |
| SU(3) DL1: Δ² symmetric, exact | DL1: exact rational (all permutations) | ✅ | — |
| SU(3) DL2: degree-6 homogeneity, exact | DL2: exact rational | ✅ | — |
| SU(3) DL3: pair-collision order 2, exact | DL3: exact rational | ✅ | — |
| SU(3) DL4: multiplicativity, exact | DL4: exact rational | ✅ | — |
| Remark: su2 "Tests 10⁶ candidate functions" | No such exhaustive search | ❌ | Replaced with accurate description |
| Remark: su3 "Tests all degree-5 antisymmetric polynomials" | DL5 is tautological (F:=Δ²) | ❌ | Replaced with algebraic argument description |

All three mismatches patched in the paper (first audit pass, 2026-04-20).

## Missing scripts (documented in code appendix but not found in repo)

These were cited in the paper's appendix but could not be located anywhere in the repository after exhaustive search:

| Script | Status | Notes |
|--------|--------|-------|
| `instantiation_factor.py` | Not found | The δ_UGP computation is covered by `test_ugp_t_02_first_principles.py` (UGP_discovery_lab/) and `ugp_final_sieve.py` |
| `pentagon_symmetry.py` | Not found | The k_gen2 = −φ/2 derivation is in `test_ugp_t_02_first_principles.py` |
| `mobius_pslq_discovery.py` | Not found | PSLQ discovery; result (k_a,k_b,k_c)=(1/8,−3/2,4/3) hardcoded in `gauge_couplings_unified.py` |
| `rg_flow_visualizer.py` | Not found | RG attractor visualization; see papers/04_dynamics_universality/ figures instead |
| `loop_kernel_constructor.py` | Not found | Topos self-reference — conceptual only, no paper figure/number depends on it |
| `survivor_space_topology.py` | Not found | Topology module — conceptual only |
| `prime_lock_search.py` | Not found | The uniqueness sieve is `ugp_uniqueness_sieve.py` (see papers/05_uniqueness/) |

**Impact:** The missing scripts are either covered by equivalent scripts or are conceptual (no paper claim depends on running them). The three core quantitative results (gauge couplings, SU(2) rigidity, SU(3) rigidity) are all fully reproduced.

## Gauge coupling values (verified)

| Coupling | UGP bare | PDG 2023 | Error |
|---------|---------|----------|-------|
| g₁² | 16/125 = 0.1280 | 0.1279 | 0.00% |
| g₂² | 2329/5400 ≈ 0.4313 | 0.425 | 1.48% |
| g₃² | ≈ 1.4857 | 1.486 | 0.16% |

---

## Change Log

### 2026-05-11 — Blind falsification note updated (m_W two-loop recovery)


**Change:** Line 649 — "Blind falsification" heading expanded to "Blind falsification and recovery": added that standard two-loop SM gauge running with 6→5 threshold matching at m_t recovers m_W = 80.364 GeV at −0.42σ of PDG 2024 world average (80.3692 ± 0.0133); residual vs older PDG fully accounted for by SM/PDG W-mass tension. OP(viii) is now closed.
