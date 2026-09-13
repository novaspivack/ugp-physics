# Reproduction Guide — P51: The Polynomial Certificate of Transputation

## LaTeX compilation

```bash
cd papers/51_polynomial_transputation
pdflatex -interaction=nonstopmode polynomial_transputation.tex
bibtex polynomial_transputation
pdflatex -interaction=nonstopmode polynomial_transputation.tex
pdflatex -interaction=nonstopmode polynomial_transputation.tex
```

Expected output: PDF with approximately 20 pages, zero undefined references.

## KL divergence computation (Section 3.2)

```bash
cd papers/51_polynomial_transputation/scripts
python3 p_transputation_kl_divergence.py
```

Expected output:
- `p_transputation_kl_results.json` with all numerical results
- KL(f̃_MDL ‖ p̃) ≈ 7.71 bits (Model A) and ≈ 4.62 bits (Model B)
- SRRG fixed point φ = (√5−1)/2 ≈ 0.618034

## Formal structure analysis

```bash
cd papers/51_polynomial_transputation/scripts
python3 p_transputation_formal_analysis.py
```

## Stage-convergence structure of [D]-adjudication (Section 5.3)

```bash
cd papers/51_polynomial_transputation/scripts
python3 transputation_limit_stage_convergence.py
```

Expected output:
- `transputation_limit_stage_convergence_results.json` with all four experiments
- E1 (diagonal halting-coded family): all halting members converge with exactly 1 mind
  change; convergence stage = halting time (range 1–1132); non-halting members 0 mind
  changes, conservative limit correct
- E2 (compound records, k = 5 winding sectors, 500 trials): max mind changes = 3
  (proved bound 8); all limits equal the true argmin; histogram {0: 115, 1: 257, 2: 119, 3: 9}
- E3 (Lyapunov dissonance relaxation): dissonance monotone non-increasing between
  witness events (2.248 → 0.0); argmin stable over final 200 stages
- E4 (no-computable-modulus phenomenology): median convergence stage 261, max 1132

## Lean verification

All theorems in Appendix A can be verified by building the four public repositories:

```bash
cd /path/to/ugp-lean && lake build UgpLean
cd /path/to/srrg-lean && lake build
cd /path/to/nems-lean && lake build
cd /path/to/transputation-lean && lake build
```

Key modules:
- `UgpLean/Polynomial/PolyExplorations.lean` — psc_projection_gives_fmdl, kl_divergence_fmdl_p_nonzero
- `UgpLean/GTE/Z7InvariantSubsets.lean` — p_poly_agrees_fmdl_on_binary
- `UgpLean/Universality/CUP3DUniqueness.lean` — fmdl_gen1_is_garden_of_eden, fmdl_z7_three_generation_orbit
- `UgpLean/Polynomial/PolyExplorations.lean` — period_475_returns, period_475_is_minimal
- `SRRGCABridge.lean` (srrg-lean) — gte_poly_srrg_bridge
- `UgpLean/Framework/MDLTower.lean` — mdl_tower_bundle, mdl_tower_three_levels_non_circular
- `NemS/Diagonal/Sigma1Completeness.lean` (nems-lean) — rt_sigma1_complete_on_diagonal,
  halting_manyOne_reducible_to_RT, rt_manyOne_reducible_to_halting_zero
- `NemS/Diagonal/NoConvergenceModulus.lean` (nems-lean) — no_computable_convergence_modulus
- `Transputation/Theorems/LimitComputability.lean` (transputation-lean) — pt_limit_computable
  (stage convergence as named structure `StageConvergence`)
- `Transputation/Theorems/DiagonalDegree.lean` (transputation-lean) —
  pt_diagonal_manyOne_degree_halting; pt_diagonal_degree_halting (named structures
  `StageConvergence`, `MindChangeBounded`)
