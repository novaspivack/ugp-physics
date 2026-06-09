# Provenance: P47 — GTE Cosmological Predictions from First Principles

**Paper:** P47, UGP Physics series.

## Sources

The cosmological-constant derivations (D_res / PSC epoch selection, holographic
mode count, holographic non-renormalization) and the proper-time rate τ = 3/7
originate in the quantum-gravity completion and Level-1/Level-2 bridge research
that also underpins P44 and P45. The CMB spectral tilt, the Gorard discrete-smooth
curvature chain, the strong-field UV bound, and the Hawking kink emission profile
are drawn from the same body of work. The neutrino sector (Σm_ν, leptogenesis)
comes from P21 and the CKM CP phase from the Koide/CKM analyses of P18/P32.

## Machine certification

All central algebraic steps are certified in the canonical `ugp-lean` library with
zero `sorry`. See `REPRODUCE.md` for the module list and the complete inventory in
Appendix A of the paper. A clean `lake build` of `ugp-lean` exits 0.

## Upgrade history

- **2026-05-31 (EPIC_083 G02 — CC ratio CatAD and N_gen=3 uniqueness):**
  Two new CatAD results for the CC section (LAB_NOTE_G02_CC_QUANTUM_PSC_ADJUDICATION.md):
  1. **Ratio Ω_PSC/Ω_holo in GTE atoms (083-CC-RATIO-GTE, CatAD):**
     Ratio = 2Z₇·ln(D²N_fam³/N_gen)/(N_gen²π²) = 14·ln(2000/3)/(9π²) ≈ 1.02483.
     Orbit count 2000/3 = D²N_fam³/N_gen (D=4, N_fam=5, N_gen=3) fully determined by GTE atoms.
     Baker-Wüstholz theorem: the gap is transcendentally irreducible — no GTE arithmetic
     identity can close the 2.4%.
  2. **N_gen=3 uniqueness for CC bracketing (083-NGEN-CC-UNIQUENESS, CatAD):**
     N_gen=3 is the unique integer for which both Ω_Λ routes lie within 5σ of Planck 2018.
     Spread at N=3: 0.017 (2.4%); at N≠3: ≥0.40 (59%). Continuous minimum at N=3.034.
     This is a non-trivial consistency: N_gen=3 is PSC-selected independently of any CC argument.
  All computations inline (reproducible from §cc-range formulas; see `REPRODUCE.md`).

## External citations

All external references (Weinberg 1989; Weinberg 1987; Cohen–Kaplan–Nelson 1999;
Hsu 2004; Davidson–Ibarra 2002; Planck 2018; Bekenstein 1973; Doplicher–Haag–Roberts
1971; Gorard 2020; Hawking 1975) were verified against arXiv/DOI records before
inclusion in `papers/bib/Spivack_Papers_Bibliography.bib`.

- **2026-06-02 (083C quality audit — commit bba2d17e):** Added H₀=67.95 km/s/Mpc (CatA; T_CMB sole external input); η_B=6.35×10⁻¹⁰ from kink-overlap mechanism (CatAD: `leptogenesis_kink_overlap_catad`); D_top=exp(−1/N_c) extension to baryon sector; PMNS angles (cross-ref to P21). Scripts graduated: `h0_full_first_principles.py`, `h0_noncircular_from_tcmb.py`, `h0_combined_mechanisms.py`.

- **2026-06-02:** D_top derivation upgraded to machine-certified (Lean 4, zero sorry). Z₇ group transitivity proves equal sector distribution without dilute instanton gas approximation. New certs: `z7_star_transitivity_under_addition`, `z7_symmetry_forces_equal_sector_action`, `d_top_derivation_chain_catal` (all zero sorry). D_top factor in Ω_DM h² and η_B inherits CatAL; overall predictions remain CatAD.
