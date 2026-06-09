# Provenance — P51: The Polynomial Certificate of Transputation

## Paper

**Title:** The Polynomial Certificate of Transputation: MDL Unification, Discrete Measurement, and the SRRG Fixed Point  
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
- `transputation-lean` (canonical): closed_choice_forces_transputation

## Scripts and artifacts

| File | What it produces |
|------|-----------------|
| `scripts/p_transputation_kl_divergence.py` | KL(f̃_MDL‖p̃) = 7.71/4.62 bits; entropy; φ verification |
| `scripts/p_transputation_formal_analysis.py` | Level-raising structure; improved f_MDL model |
| `scripts/p_transputation_kl_results.json` | JSON record of all numerical results |
