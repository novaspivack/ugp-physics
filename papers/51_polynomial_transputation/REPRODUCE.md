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

## Lean verification

All theorems in Appendix A can be verified by building ugp-lean and srrg-lean:

```bash
cd /path/to/ugp-lean && lake build UgpLean
cd /path/to/srrg-lean && lake build
```

Key modules:
- `UgpLean/Polynomial/PolyExplorations.lean` — psc_projection_gives_fmdl, kl_divergence_fmdl_p_nonzero
- `UgpLean/GTE/Z7InvariantSubsets.lean` — p_poly_agrees_fmdl_on_binary
- `UgpLean/Universality/CUP3DUniqueness.lean` — fmdl_gen1_is_garden_of_eden, fmdl_z7_three_generation_orbit
- `UgpLean/Polynomial/PolyExplorations.lean` — period_475_returns, period_475_is_minimal
- `SRRGCABridge.lean` (srrg-lean) — gte_poly_srrg_bridge
- `UgpLean/Framework/MDLTower.lean` — mdl_tower_bundle, mdl_tower_three_levels_non_circular
