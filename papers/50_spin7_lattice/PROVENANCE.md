# PROVENANCE — Paper 50: The Spin-7 Lattice Model

**Series:** UGP Physics Series, Paper 50  
**Title:** The Spin-7 Lattice Model: Phase Transitions and Statistical Mechanics of the GTE Polynomial  
**Author:** Nova Spivack  
**Date:** June 2026  
**Status:** Draft preprint  

## Zenodo

DOI pending publication. Hub concept DOI: 10.5281/zenodo.20168144

## Sources and Provenance

### Main derivation
- The spin-7 model is defined by interpreting $p(L,C,R) = C+R-CR-LCR \pmod 7$ as an interaction energy, following the definition of Object 0 in the GTE derivation tower (P49).
- Transfer matrix spectral data: computed numerically in `scripts/spin7_transfer_matrix.py`.
- 2D Monte Carlo results: computed in `scripts/spin7_2d_phase.py` and `scripts/spin7_2d_fss.py`.
- Ground-state algebra ($p(x,x,x) = -x(x-1)(x-5)$): computed in `scripts/spin7_gs_algebra.py`.
- CMCA entropy rate connection: computed in `scripts/spin7_cmca_connection.py` (original in `research-sandbox/`).

### Key results traceability
| Result | Source | Certification |
|--------|--------|---------------|
| $43 = \Phi_6(7)$ local ground states | P49 Theorem 4.6; Lean cert `poly_p_zero_variety_count_gf7` | CatAL |
| GS roots $\{0,1,5\}$ of $p(x,x,x)$ | Computation; Lab Note R06 | CatAD |
| Transfer matrix eigenvalues at $\beta=1$: $(10.42, 6.73, ...)$ | Numerical; Table 1 | CatA |
| $\beta_c \approx 0.35$, $T_c \approx 2.86J$ | Monte Carlo; Lab Note R06 | CatA |
| CMCA entropy rate $S = \log(10.42) = 2.343$ nats | Numerical; Lab Note R06 | CatA |
| Walsh NL identity $\mathrm{NL}(p) = 1 - c_H/7^2$ | P49 Theorem 4.7 (CatAD) | CatAD |

### Dependencies
- Paper P49: `papers/49_gte_polynomial_wolfram/` — Polynomial properties, MDL selection, Cyclotomic Point Count (Theorem 4.6), Walsh NL theorem (Theorem 4.7)
- Paper P41 (SpivackCMCA): CMCA definition
- Paper P45 (SpivackThreeTapeCMCA): Three-tape CMCA, DPP
- Paper P46 (SpivackGTEPolynomialUFT): Gauge couplings
- Paper P48 (SpivackGTECompleteFramework): GTE framework overview
