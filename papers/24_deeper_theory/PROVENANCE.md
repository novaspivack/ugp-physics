# Provenance — Paper 24: The Arithmetic Uniqueness of the Standard Model

**File:** `papers/24_deeper_theory/ugp_deeper_theory.tex`
**Public repo:** [github.com/novaspivack/ugp-physics](https://github.com/novaspivack/ugp-physics)

---

## Summary

This paper proves the Arithmetic Uniqueness of the Standard Model parameter spectrum:
the UGP seed (n=10, b₁=73, seed=(1,73,823)) is the unique survivor of the joint
arithmetic admissibility sieve and physical viability constraint across all n ∈ ℕ.

All main theorems are Lean 4 certified in `ugp-lean` (zero sorry; the 110th module
`MassRelations.NeutrinoFroggattNielsen` is referenced from the companion neutrino paper).

The paper additionally collects three structural results in §9:
- §9.5: SM winding numbers `{N_c−1, −1, 0, −N_c}` derived from `N_c` (`BraidAtlas.ChargeDerivation`).
- §9.6: Residual Classification (RCC) as a theorem over all compact simple Lie groups
  (`PSC.RCCInfiniteFamilies` for infinite classical families; extended TE2.2 certificate
  for exceptional groups).
- §9.7: Audit of UGP-internal derivability showing that anomaly cancellation is the
  unique force of `N_c = 3` (clean negative; structural finding).

---

## Lean 4 Theorems (all zero sorry)

| Theorem | Module | Description |
|---------|--------|-------------|
| `asymptotic_sparsity_universal` | `Phase4.AsymptoticSparsity` | (n=10,b₁=73) unique for ALL n∈ℕ |
| `positive_root_theorem` | `Phase4.PositiveRootTheorem` | \|Φ⁺(G)\| = SU(N)₁ factor count |
| `chirality_arithmetic` | `BraidAtlas.ChiralitySquaring` | g₃² num is perfect square; g₂² is not |
| `galois_layer_stability` | `GaloisStructure.CyclotomicLayers` | Kernel and Koide layers in different Galois orbits |
| `q_zeta_120_is_minimal_conductor` | `GaloisStructure.MinimalCyclotomic` | 120 = lcm(20,24) minimal cyclotomic conductor |
| `mersenne_ladder_structure` | `GaloisStructure.MinimalCyclotomic` | {4,10,16} = {2F(3),2F(5),2F(6)}, step=2Nc |
| `vv_mechanism_algebraic` | `MassRelations.VVMechanism` | VV = GUT power law ∘ UCL log map |
| `vv_all_coefficients_from_Nc` | `MassRelations.VVAllCoefficientsFromNc` | All three VV exponents from N_c=3 alone |
| `prime_137_structural_origin` | `GaloisStructure.MinimalCyclotomic` | 137 = 2^0+2^Nc+2^δ |
| `sm_winding_numbers_from_Nc` | `BraidAtlas.ChargeDerivation` ✓ (zero sorry, 2026-05-08) | SM winding pattern {N_c−1,−1,0,−N_c} from N_c |
| `anomaly_cancellation_from_windings` | `BraidAtlas.ChargeDerivation` | Anomaly sum vanishes at N_c=3 |
| `y_ql_unifies_vv_and_winding` | `BraidAtlas.ChargeDerivation` ✓ (zero sorry, 2026-05-08) | Y_QL = 1/(2N_c) ties VV slope and braid charge |
| `rcc_all_classical_families` | `PSC.RCCInfiniteFamilies` | RCC over B_n, C_n, D_n, A_n |
| `bn_all_irreps_self_dual` / `cn_all_irreps_self_dual` | `PSC.RCCInfiniteFamilies` | w₀ = −id ⇒ no complex reps |
| `dn_odd_spinorDim_exceeds_threshold` | `PSC.RCCInfiniteFamilies` | D_n odd, n≥5: spinor dim ≥ 16 |
| `an_adjDim_ge_15` | `PSC.RCCInfiniteFamilies` | A_n, n≥3: adj dim ≥ 15 |
| `b1_unique_at_n10` | `Phase4.AsymptoticSparsity` | Both Stage-1 survivor pairs at n=10 give b₁=73 identically |

---

## Computational Artifacts

In `papers/24_deeper_theory/`:

| Script | Output | Description |
|--------|--------|-------------|
| `run_all.py` | (calls all below) | Runs full investigation in < 1s |
| `01_asymptotic_sieve.py` | `results/01_asymptotic_sieve.txt` | Stage-1+2 sieve n=4..60; analytic bound n≥13 |
| `02_diophantine_analysis.py` | `results/02_diophantine_analysis.txt` | Quadratic structure; near-integer solutions |
| `03_t6_root_hypothesis.py` | `results/03_t6_root_hypothesis.txt` | Positive Root Theorem verification |
| `04_galois_orbits.py` | `results/04_galois_orbits.txt` | Galois stability; minimal polynomials |
| `05_wzw_structure.py` | `results/05_wzw_structure.txt` | WZW structure and T4 falsification |
| `06_synthesis.py` | `results/06_synthesis.txt` | Synthesis; deeper law statement |
| `toda_masses.py` | (stdout) | ADE Toda mass spectra; Q(ζ₁₂₀) containment / E7 falsifier [graduated 2026-05-12] |
| `pslq_e8_exact.py` | (stdout) | E8 mass ratios: minimal polynomials + PSLQ precision table [graduated 2026-05-12] |
| `wzw_dimensions.py` | (stdout) | WZW quantum dims: Q(ζ₁₂₀) iff (k+2)\|120; falsifiers at k=16,22 [graduated 2026-05-12] |
| `pslq_known_models.py` | (stdout) | PSLQ pipeline validation on 2D Ising / tricritical Ising (pipeline sanity check) [graduated 2026-05-12] |

In `papers/01_SM/canonical_run/` (cross-referenced from this paper):

| Script | Pre-commit SHA | Section | Description |
|--------|----------------|---------|-------------|
| `comp_p23_SP1_rcc_extended_scan.py` | `639cf67a…` | §9.6 | Extended RCC scan: 11 new gauge groups (E7, E8, F4, SO(12-18), SU(7-10)) all fail PSC |
| `comp_p24_SP3_Nc_independence_audit.py` | `daed8ad6…` | §9.7 | Audit verifying anomaly cancellation is the unique non-circular force of N_c=3 |
| `comp_p25_alpha_precision_floor.py` | `a0e8debe…` | §9.8 | 60-digit verification of C_alg, delta_target, b1_required, residual = 2.39 ppm |
| `comp_p25_residual_structural_search.py` | `d4dbd923…` | §9.8 | Null-disciplined structural search; verdict NO_MATCH at depth ≤ 1 |
| `comp_p25_galois_protection_probe.py` | `c8fa7cb3…` | §9.8 | O4a Galois census: 9/9 one-loop transcendentals outside Q(ζ₁₂₀); GALOIS_PROTECTION_SUPPORTED |
| `comp_p25_o4b_sensitivity_probe.py` | `f076a10b…` | §9.8 | O4b sensitivity: dC/dk_gen2 ≈ 1.504; 583 ppm naive one-loop = 244× R_real |
| `comp_p25_o3_scale_probe.py` | — | §9.8 | O3: matching scale Q ≈ m_e from two independent approaches |
| `comp_p25_o4b_analytic_proof.py` | `ddce23d3…` | §9.8 | O4b analytic proof: Baker + T/T† pairing → one-loop cancellation; ANALYTIC_PROOF_COMPLETE |
| `comp_p25_o3_two_loop_coefficient.py` | `62109971…` | §9.8 | O3: R_real = (8/9)×α²/(2π²); MATCH_WITHIN_PRECISION (Lean: Phase4.TwoLoopCoefficient) |

The §9.8 "Precision Frontier" subsection is now **complete**:
- One-loop cancellation proved analytically and Lean-certified (Phase4.GaloisProtection)
- Two-loop coefficient = (Nc²-1)/Nc² = 8/9 Lean-certified (Phase4.TwoLoopCoefficient)
- Residual R_real = (8/9) × α²/(2π²) = 2.39 ppm is a structurally derived, not just characterized, quantity.
- Open items: O1 (NLO UCL cross-check) and O2 (field-theory perspective) — verification, not missing derivations.

---

## Residual: 2.39 ppm

The residual between the structural prediction `delta_UGP = C_alg/73` and
the non-circular CODATA-derived target is **2.39 ppm** in α (the TE1.P
deviation documented in `Spivack2026_SM_UGP` §5.5), corresponding to
`b1_required = 73.000174`.  The non-circular derivation chain is the
TE1.P bridge recorded in `uniqueness/canonical_run/delta_noncircular.json`.

---

## Dependencies

- Python 3.8+ with `sympy`, `numpy` (for computation scripts)
- `ugp-lean` (Lean 4, see companion formalization paper~\cite{SpivackUGPFormalization}): `https://github.com/novaspivack/ugp-lean`
- `ugp-physics` repo: `https://github.com/novaspivack/ugp-physics`

---

## Reproducibility

```bash
cd papers/24_deeper_theory
python3 run_all.py          # All paper-internal results in < 1 second
```

For the Lean checks see `REPRODUCE.md`.
