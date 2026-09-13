# Provenance — P51: The Polynomial Certificate of Transputation

## Paper

**Title:** The Polynomial Certificate of Transputation: MDL Unification, Quantum Measurement, and the SRRG Fixed Point  
**Author:** Nova Spivack  
**Series:** UGP Physics Series, Paper 51  
**DOI:** 10.5281/zenodo.20611502 (Zenodo concept DOI)

## Prior papers this builds on

| Paper | Key contribution cited |
|-------|----------------------|
| P37 (SpivackQMFromR110) | Hilbert space and Born rule from f_MDL ring |
| P48 (SpivackGTECompleteFramework) | Transputation D1–D5 framework; MDL three-roles non-circularity |
| P49 (SpivackGTEPolynomialWolfram) | Four-object tower; p vs f_MDL distinction; period-475 attractor |
| P27 (SpivackSRRG) | SRRG fixed point φ; Higgs VEV |
| P34 (SpivackGTEMobius) | GTE-Möbius architecture (A, e, [D]) |
| P13 (SpivackMFRR) | DSAC architecture; PR-0 field substrate |
| P28 (SpivackCompUniversality) | CUP-4; Rule 110 from SM orbit |

## Lean certifications

All theorems cited as CatAL are machine-verified in Lean 4 with zero sorry:
- `ugp-lean` (canonical): psc_projection_gives_fmdl, p_poly_agrees_fmdl_on_binary,
  p_fmdl_disagree_on_orbit, kl_divergence_fmdl_p_nonzero, fmdl_z7_three_generation_orbit,
  fmdl_gen1_is_garden_of_eden, period_475_returns, period_475_is_minimal,
  born_rule_unconditional, mdl_tower_bundle, mdl_tower_three_levels_non_circular,
  mdl_ca_rule_coding_closed, asr_rt_not_computable
- `srrg-lean` (canonical): gte_poly_srrg_bridge, srrg_equals_mdl_minimization
- `transputation-lean` (canonical): closed_choice_forces_transputation,
  pt_diagonal_manyOne_degree_halting; pt_limit_computable and pt_diagonal_degree_halting
  carry their stage-convergence and mind-change premises as named structures
  (`StageConvergence`, `MindChangeBounded`) — conditionality disclosed in Appendix A
- `nems-lean` (canonical): rt_sigma1_complete_on_diagonal, halting_manyOne_reducible_to_RT,
  rt_manyOne_reducible_to_halting_zero, no_computable_convergence_modulus

## External citations (computability classification)

- Gold, E. M., "Limiting recursion", J. Symbolic Logic 30(1) (1965) 28–48, doi:10.2307/2270580
- Putnam, H., "Trial and error predicates and the solution to a problem of Mostowski",
  J. Symbolic Logic 30(1) (1965) 49–57, doi:10.2307/2270581
- Shoenfield, J. R., "On degrees of unsolvability", Ann. of Math. 69(3) (1959) 644–653

## Scripts and artifacts

| File | What it produces |
|------|-----------------|
| `scripts/p_transputation_kl_divergence.py` | KL(f̃_MDL‖p̃) = 7.71/4.62 bits; entropy; φ verification |
| `scripts/p_transputation_formal_analysis.py` | Level-raising structure; improved f_MDL model |
| `scripts/p_transputation_kl_results.json` | JSON record of all numerical results |
| `scripts/transputation_limit_stage_convergence.py` | Stage-convergence structure of [D]-adjudication: diagonal 1-mind-change family (conv. stage = halting time); k = 5 sector mind-change bound (500 trials, max 3 vs bound 8); Lyapunov dissonance relaxation; no-computable-modulus phenomenology |
| `scripts/transputation_limit_stage_convergence_results.json` | JSON record of all four stage-convergence experiments |
