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
- Exact pair-state transfer matrix ($49 \times 49$) spectral data, with exhaustive-enumeration exactness checks: computed in `scripts/spin7_transfer_matrix.py`.
- 2D Monte Carlo results: computed in `scripts/spin7_2d_phase.py` and `scripts/spin7_2d_fss.py`.
- Ground-state algebra ($p(x,x,x) = -x(x-1)(x-5)$): computed in `scripts/spin7_cmca_connection.py`.
- Ground-space rigidity (zero-energy rings = $\{0^n, 1^n, 5^n\}$ for all $n \ge 3$): Lean 4 certification `gte_ring_ground_states_uniform_general` in `UgpLean/Polynomial/SpinSevenGroundSpace.lean` (ugp-lean).
- CMCA entropy rate connection: computed in `scripts/spin7_cmca_connection.py`.
- Constraint-code parameters of the zero-energy ring space ($K(n)=3$, $d(n)=n$; ternary repetition code): computed in `scripts/gte_code_parameters.py`.
- Directed wall/bump spectroscopy of the pair digraph: computed in `scripts/spin7_domain_wall_energy_exact.py`, `scripts/spin7_wall_translation_classes.py`; Lean 4 certification `spin7_directed_wall_energies` + `directed_wall_half_integer_gap` in `UgpLean/Polynomial/SpinSevenWallSpectroscopy.lean` (ugp-lean).
- Exact chiral gap law (slope 3/2, amplitude 1, correction tower): computed in `scripts/spin7_continuum_scaling_law.py`, `scripts/spin7_gap_amplitude_resolvent.py`, `scripts/spin7_gap_amplitude_selfconsistent.py`, `scripts/spin7_gap_amplitude_highbeta_verify.py`, `scripts/spin7_spectator_amplitude_resolution.py`, `scripts/spin7_subleading_channel_scaling.py`; Lean 4 certifications `spin7_gap_amplitude_certificate`, `spin7_spectator_amplitude` (ugp-lean).
- Spectral insensitivity to the deterministic attractor (pre-registered batteries, all null): computed in `scripts/spin7_thermal_spectrum_period475.py`, `scripts/spin7_spectrum_locked_phases_autopsy.py`.
- Physical point and tape saturation: computed in `scripts/cmca_physical_point_calibration.py`, `scripts/mdl_tape_extremization.py`, `scripts/cmca_spectral_census_physical_point.py`, `scripts/ldiss_nfam_null_battery.py`, `scripts/hosting_boundary_csc_free_audit.py`, `scripts/spin7_hosting_boundary_digraph_facts.py`; Lean 4 certifications `tape_saturation_theorem`, `compton_support_derives_mdl_saturation`, `tape_saturation_physical_point_dictionary`, `hosting_boundary_csc_equivalence`, `saturation_alphabet_bijection`, `cmca_physical_point_dictionary` in `UgpLean/Physics/CMCAPhysicalPoint.lean` (ugp-lean).
- Perron–Frobenius hypothesis package for the thermal transfer matrix (all real beta): Lean 4 certification `spin7_transfer_pf_hypotheses` in `UgpLean/Polynomial/SpinSevenTransferPrimitivity.lean` (ugp-lean).

### Key results traceability
| Result | Source | Certification |
|--------|--------|---------------|
| $43 = \Phi_6(7)$ local ground states | P49 Theorem 4.6; Lean cert `poly_p_zero_variety_count_gf7` | CatAL |
| GS roots $\{0,1,5\}$ of $p(x,x,x)$ | Lean cert `poly_p_uniform_gs_roots`; `scripts/spin7_cmca_connection.py` | CatAL |
| Ground-space rigidity: zero-energy rings exactly $\{0^n,1^n,5^n\}$, all $n \ge 3$ | Lean cert `gte_ring_ground_states_uniform_general` (+ converse `uniform_ground_ring_satisfies_zero_energy`), `UgpLean/Polynomial/SpinSevenGroundSpace.lean` | CatAL |
| 2D ground states exactly 3 uniform (torus, $L_x, L_y \ge 3$) | Row/column assembly from the rigidity theorem (Corollary in §2) | CatAD |
| Pair transfer matrix $\lambda_1 = 1.4846$ at $\beta=1$; $Z_N = \mathrm{Tr}(M^N)$ exact | Numerical + enumeration cross-check; `scripts/spin7_transfer_matrix.py` | CatA |
| $\beta_c \approx 0.35$, $T_c \approx 2.86J$ | Monte Carlo; `scripts/spin7_2d_phase.py` | CatA |
| CMCA entropy rate $S = \log(1.4846) = 0.395$ nats/site at $\beta=1$ | Numerical; `scripts/spin7_transfer_matrix.py`, `scripts/spin7_cmca_connection.py` | CatA |
| Constraint code $K(n)=3$, $d(n)=n$ (ternary repetition code) | Exhaustive + transfer matrix; `scripts/gte_code_parameters.py` | CatA |
| Walsh NL identity $\mathrm{NL}(p) = 1 - c_H/7^2$ | P49 Theorem 4.7 (CatAD) | CatAD |
| Directed wall energies $E_w(1{\to}0)=1$, $E_w(0{\to}1)=2$, composite hub identity; bumps $(2,3,4)$ | Lean cert `spin7_directed_wall_energies`; `scripts/spin7_domain_wall_energy_exact.py` | CatAL |
| Chiral gap law $\Delta = e^{-3\beta/2}[1 + \frac12 e^{-\beta/2} + \cdots]$; slope $3/2$, amplitude $1$, ratio law $\Delta_3 = 2\Delta_2$ | Spectator + resolvent routes; `scripts/spin7_gap_amplitude_*.py`, `scripts/spin7_spectator_amplitude_resolution.py`; Lean certs `spin7_gap_amplitude_certificate`, `spin7_spectator_amplitude` | CatAD (counts CatAL) |
| Spectral insensitivity to deterministic attractor periods | One-step activity mechanism; `scripts/spin7_thermal_spectrum_period475.py`, `scripts/spin7_spectrum_locked_phases_autopsy.py` | CatAD mechanism, CatA batteries |
| Tape Saturation Theorem $a\cdot\Lambda_{\rm GTE} = \hbar c$; $a = 0.0972$ fm (tree) | Lean cert `tape_saturation_theorem` (named premise `ComptonSupportCriterion`); `scripts/mdl_tape_extremization.py` | CatAD \| CSC |
| Boundary Equivalence Theorem (CSC ⟺ register-window readability ⟺ κ = 1); saturation bijection ξ* = 7 | Lean certs `hosting_boundary_csc_equivalence`, `saturation_alphabet_bijection`; `scripts/hosting_boundary_csc_free_audit.py` | CatAD \| CSC |
| Physical point β* = 1.53460, Δ(β*) = 1/7, S(β*) = 0.1595 nats/site; dictionary aM = 1/7, am_φ = 7/8 | `scripts/cmca_physical_point_calibration.py`; Lean cert `tape_saturation_physical_point_dictionary` | CatA solve on CatAD-conditional dictionary |
| PF hypothesis package (primitivity k = 2, irreducibility, positive diagonal; all real β) | Lean cert `spin7_transfer_pf_hypotheses` | CatAL |

### Dependencies
- Paper P49: `papers/49_gte_polynomial_wolfram/` — Polynomial properties, MDL selection, Cyclotomic Point Count (Theorem 4.6), Walsh NL theorem (Theorem 4.7)
- Paper P41 (SpivackCMCA): CMCA definition
- Paper P45 (SpivackThreeTapeCMCA): Three-tape CMCA, DPP
- Paper P46 (SpivackGTEPolynomialUFT): Gauge couplings
- Paper P48 (SpivackGTECompleteFramework): GTE framework overview
- Paper P42 (SpivackPhiMDLField): Quantum kink mass $M^Q = 281 \pm 21$ MeV; substrate-regulated lattice campaigns at $am_\varphi = 7/8$; exact kink–kink S-matrix pole-freedom
- Paper P39 (SpivackGTEQCDStructure): Matching scale $\Lambda_{\rm GTE} = 7 M_{\rm kink} = (8/7) m_\tau$ (seven-kink threshold)
- Paper P43 (SpivackCompleteness): Resolution-independence of the algebraic certificate (spacing belongs to a calibration)
- Paper P51 (SpivackPolynomialTransputation): Description-length tower nesting (faithfulness premise of the Tape Saturation Theorem)
