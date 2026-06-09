# Provenance: P49 — MDL Selects the Wolfram Rule

**Paper:** P49, UGP Physics series.

**Title:** MDL Selects the Wolfram Rule: Z₇ Dynamics, Algebraic Structure, and
Standard Model Encoding of the GTE Polynomial

**Author:** Nova Spivack

**Status:** SUBMITTED

## Summary of Contributions

This paper presents the first systematic study of the GTE polynomial
p(L,C,R) = C+R−CR−LCR (mod 7) as a standalone dynamical system (Object 0),
distinct from the previously studied f_MDL lookup table (Object 1 / CMCA).

Key results:

- **T96-02 as Wolfram selection principle** (CatAL): the MDL + PSC criterion
  uniquely selects p from 7^343 ≈ 10^289 Wolfram k=7 rule candidates. This is
  the selection principle the Wolfram Physics Project has lacked.

- **Rule 110 Binary Restriction** (CatAL): p(L,C,R) mod 7 restricted to binary
  inputs equals the Rule 110 truth table exactly (all 8 entries). The ether
  vacuum IS Rule 110. Machine-certified: `rule110_z7_poly_rep`.

- **Invariant Subset Uniqueness** (CatAL): The only non-empty subsets S ⊆ Z₇
  closed under p are {0}, {0,1} (= Rule 110), and Z₇. Rule 110 is the unique
  maximal proper invariant sub-CA of p over GF(7). Machine-certified via
  `native_decide` in `Z7InvariantSubsets.lean` (zero sorry).

- **Polynomial Uniqueness** (CatA): C+R−CR−LCR is the unique degree-≤3
  polynomial over GF(7) reproducing Rule 110 on {0,1}³. 1 of 2401 = 7^4
  candidates.

- **QNR Binary Floor Uniqueness** (CatAL): {0,1} is the unique non-trivial
  proper invariant subset of p over GF(7) because N_fam = 5 is a quadratic
  non-residue mod 7. Machine-certified: `five_is_qnr_mod7`,
  `kink_fixed_point_eq_no_solution`, `nfam_qnr_explains_binary_floor`
  (Z7InvariantSubsets.lean, zero sorry).

- **Schwartz-Zippel non-polynomial result** (CatA): f_MDL has 325 zeros vs
  maximum 147 for any degree-≤3 polynomial over GF(7), proving f_MDL is
  provably not a polynomial — Objects 0 and 1 are algebraically distinct in kind.

- **40% DPP cross-tape fraction** (CatAD): For the three-tape DPP system,
  the cross-tape (gravitational) causal edge fraction is exactly
  (N_TAPES−1)/(N_TAPES+2) = 2/5 = 40%.

- **First k=7 polynomial CA spacetime diagrams** (CatA): behavioral
  classification (Class 3 on generic Z₇, Class 4 on binary sublayer), sector
  comparison for all five SM injection values, glider null result (ROBUST).

## Computational Scripts

All scripts are in `scripts/`. Output figures are written to `scripts/figures/`.
See `REPRODUCE.md` for full reproduction instructions.

| Script | What it computes | Key output |
|--------|-----------------|------------|
| `invariant_subset_classifier.py` | Exhaustive invariant subset check (all 127 non-empty subsets of Z₇) | Printed verification |
| `spacetime_diagram_generator.py` | Z₇ CA spacetime evolution on ether background | `p49_gte_spacetime_perturbed_v2.png` |
| `ppoly_fmdl_contrast.py` | f_MDL vs p_poly comparison: ring evolution, ether response, lookup table | `p49_gen1_fmdl_vs_ppoly.png`, `p49_fmdl_vs_ppoly_table.png` |
| `gen_orbit_ring_visualization.py` | GEN₁→GEN₂→GEN₃→VAC orbit ring diagram | `p49_gte_orbit_rings_v2.png` |
| `wolfram_model_causal_graph.wl` | WolframModel causal graph of GEN orbit (10 generations) | `p49_gte_causal_g10.png` |
| `z7_sector_dynamics.py` | Glider search, two-particle scattering, sector comparison | `p49_z7_color_comparison.png` |
| `three_tape_dpp_visualization.py` | Three-tape DPP architecture figures | `p49_three_tape_dpp_v3.png` |
| `bulk_causal_graph.py` | Combined bulk causal graph (within-tape + cross-tape edges) | `p49_bulk_causal_3d.png`, `p49_causal_comparison.png` |
| `glider_search_taichi.py` | Ether-excluded glider search (Taichi parallel CA) | `p49_z7_excitation_panel.png` |
| `orbit_visitation_rate.py` | SM orbit triple visitation rate in chaotic bulk | `p49_orbit_visitation_rates.png` |
| `three_tape_wolfram_model.wl` | Three-tape GEN orbit as SetReplace hyperedge system | Three-tape causal graph PNGs |

## Lean Certification

Key Lean modules (all in ugp-lean, zero sorry):

- `UgpLean/Universality/Z7InvariantSubsets.lean` — Invariant Subset Uniqueness
  and QNR Binary Floor theorems
- `UgpLean/Universality/CUP3DUniqueness.lean` — GEN orbit chain theorems
- `UgpLean/Universality/MDLDerivabilityCriterion.lean` — T96-02 closure
- `UgpLean/Universality/PhiMDLUniversality.lean` — `rule110_z7_poly_rep`
- `UgpLean/Gravity/RelationalTime.lean` — `dimensional_protocol_principle_master`

## Computational Environment

- Python 3.10+ with numpy, matplotlib
- Taichi 1.7.3 (for `glider_search_taichi.py` and `orbit_visitation_rate.py`)
- Wolfram Engine 14.3.0 with SetReplace v0.3.196 (for `.wl` scripts)
- Lean 4 (elan) with Mathlib, as specified in `ugp-lean/lake-manifest.json`

## Related Papers

| Paper | Relation |
|-------|----------|
| P28 (SpivackCompUniversality) | PSC orbit structure and Z₇ ring foundations |
| P34 (SpivackGTEMobius) | PSC / transputation framework |
| P40 (SpivackGF7Universality) | GF(7) polynomial / f_MDL characterization |
| P41 (SpivackCMCA) | Prior work: f_MDL as Object 1 / CMCA dynamics |
| P43 (SpivackCompleteness) | Why CA is Level 1 certificate only (not substrate) |
| P45 (SpivackThreeTapeCMCA) | Three-tape DPP theorem (CatAL) |
| P46 (SpivackGTEPolynomialUFT) | MDL framework and 19-bit description derivation |
| P47 (SpivackGTECosmology) | Holographic Ω_Λ derivation |
| P48 (SpivackGTECompleteFramework) | Comprehensive GTE monograph |

## External Citations

All external references were verified against arXiv/DOI records before
inclusion in `papers/bib/Spivack_Papers_Bibliography.bib`. Key external
sources: Wolfram 2020 (arXiv:2004.08210), Gorard 2020 Rel/QM, Wolfram
NKS 2002, Cook 2004 (Rule 110 universality).
