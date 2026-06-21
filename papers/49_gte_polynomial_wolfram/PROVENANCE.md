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

- **Direct-Interpolation Lift Theorem** (CatAL): the total-parity shadow of
  the fifteen canonical GTE cascade triples on the five-family ring, together
  with vacuum transparency, pins exactly one rule among all 7⁸ = 5,764,801
  multilinear GF(7) candidates: p itself; without vacuum transparency exactly
  seven survive. Rule 110 is derived as the binary restriction (corollary,
  not anchor). Certified by two independent routes — exhaustive 7⁸ census
  (`ugp_orbit_interpolation_lift`) and structural Möbius inversion
  (`orbit_interpolation_lift_structural`) — with orbit provenance certified
  against the cascade arithmetic (`gte_orbit_parity_provenance`).

- **MDL Sparsity Floor** (CatAL): any GF(7) polynomial of per-variable degree
  ≤ 6 whose binary restriction is Rule 110 flattens to p under exponent
  flattening and has at least four monomials, with equality exactly at p —
  multilinearity is MDL-forced (`gf7_rule110_sparsity_floor`,
  `rule110_lift_sparsity_floor`). Together with the lift this closes the
  within-k=7 link of the T96-02 selection chain at machine-certified grade,
  and the paper states the certification of T96-02 link by link.

- **Chirality Census** (CatAL): over all 120 orderings of the five families,
  exactly 20 admit an orbit-consistent elementary CA rule; the
  vacuum-transparent survivor union is exactly {Rule 110, Rule 124}, with
  ordering reversal bijecting the ten Rule-110 orderings onto the ten
  Rule-124 orderings (`orbit_chirality_census`) — the unordered UGP data
  forces the CMCA chiral pair; the ordering convention is the chirality
  gauge.

- **Scope of the parity reduction** (CatAD on CatAL anchors): over all 777
  additive reductions ℤ³ → Z_m (m ≤ 7) and all 16,807 mod-2 recodings into
  GF(7), the coherently-forcing reductions are exactly total parity up to
  alphabet units, forcing the unit conjugates of p; the product-parity
  competitor (3-monomial Rule-106 lift) is excluded by the certified
  displaced-vacuum criterion; non-additive recodings beyond mod-2 granularity
  provably break forcing and the unrestricted lookup space is constructively
  vacuous — the scope is maximal. Census counts machine-certified
  (`parity_projection_additive_forcing`,
  `parity_projection_mod2_recoding_forcing`).

- **Directed Interface Spectroscopy** (CatAL): exact integer directed wall
  energies of the 49-node pair digraph — E_w(1→0) = 1, E_w(0→1) = 2,
  E_w(5→0) = 2, E_w(0→5) = E_w(1→5) = E_w(5→1) = 4 with composite hub
  identity E_w(5→1) = E_w(5→0) + E_w(0→1) — and bump energies (2,3,4)
  (`spin7_directed_wall_energies`); the directional asymmetry is the
  arithmetic trace of the AGL(1,7) chiral Z₂, and the half-integer mean 3/2
  is the gap exponent of the associated spin-7 chain.

- **Compton-scale kink injection as a near-term target**: the kink-injection
  open problem now carries a sharp pre-registered pass criterion — under the
  MDL-saturated matter-sector reading a = ℏc/Λ_GTE a physical BPS kink spans
  exactly λ_C/a = |Z₇| = 7 cells, with falsifiable target ξ_kink = 7 cells
  (band 6.78–7.23 ± 0.54); under the fine-end (Planck) working hypothesis it
  spans ~10¹⁹–10²⁰ cells, with both readings now stated explicitly.

- **QNR Binary Floor Uniqueness** (CatAL): {0,1} is the unique non-trivial
  proper invariant subset of p over GF(7) because N_fam = 5 is a quadratic
  non-residue mod 7. Machine-certified: `five_is_qnr_mod7`,
  `kink_fixed_point_eq_no_solution`, `nfam_qnr_explains_binary_floor`
  (Z7InvariantSubsets.lean, zero sorry).

- **Schwartz-Zippel non-polynomial result** (CatA): f_MDL has 325 zeros vs
  maximum 147 for any degree-≤3 polynomial over GF(7), proving f_MDL is
  provably not a polynomial — Objects 0 and 1 are algebraically distinct in kind.

- **Golden-Quadratic Duality** (CatAD; components CatAL): the QNR obstruction
  quadratic m(x) = x²+x−1 (discriminant 5 = N_fam) is the diagonal factor of
  p over every commutative ring (p(x,x,x) − x = −x·m(x), machine-certified
  `gte_diagonal_quadratic_factorization`); split over ℝ where its positive
  root 1/φ is the SRRG fixed point, inert at 7 with no root at any 7-adic
  depth (`master_quadratic_no_root_mod_seven_pow`). All-q splitting dichotomy
  governed by q mod 5 (1229 primes < 10⁴ verified); GF(5) ballistic pathology
  derived from ramification (`second_floor_iff_ramified`); honest negative:
  no golden factor in cycle monodromy spectra (0/20 nulls).

- **Vacuum Uniqueness Theorem** (CatAL): Fix(T_n) = {vacuum} for every ring
  size n, proved via the golden Möbius map μ(x) = (1+x)⁻¹ — a single 8-cycle
  on P¹(GF(7)) (`vacuum_unique_temporal_fixed_point_ring`, zero sorry).
  General-q criterion (5|q) = −1 ∧ π(q)/gcd(π(q),q−1) = q+1 verified for all
  primes q < 200. Exact Artin–Mazur zeta factorizations at n = 5, 7;
  zero-torus-entropy result; drift-3/7 coincidence adjudicated negative.

- **Eisenstein arithmetic** (CatAD; components CatAL): F₂₁ ≅
  (ℤ[ω]/(3+ω))⁺ ⋊ μ₃ (`f21_eisenstein_residue_model`); motivic identity
  [V(p)] = Φ₆(𝕃) verified on 23 prime powers ≤ 49; torus action
  p∘g_u = u⁻¹p with the ether point (−1,0,0) as unique fixed zero
  (`poly_p_torus_equivariance`); Φ₆ ladder identity web I1–I4 with
  pre-registered null batteries; biquadratic compositum ℚ(√−3,√5) of
  conductor 15 = N_gen·N_fam unifying the golden and Eisenstein rings
  (`biquadratic_compositum_alphabet_class`).

- **AGL(1,7) chiral Z₂** (CatAD; CatAL core): the full symmetry group of
  V(p) is AGL(1,7) = F₂₁ ⋊ Z₂ of order 42; the reflection element swaps
  Rule 110 ↔ Rule 124 over GF(7) with zero mismatches
  (`agl17_chiral_z2_mechanism`), inscribing the CMCA chiral pair in the
  arithmetic of Object 0.

- **Attractor Factorization Theorem** (CatAD): the period-475 attractor
  factors as 5 (ring) × 5 (drift) × 19 (drift-invariant inert clock);
  T⁹⁵ = σ³ exact; drift-cancelled return map σ³T⁵ = T¹⁰⁰ of order exactly
  19; GF(7³) trace carrier; linearization no-go (tangent torsion exactly
  μ₃). The value 19 is enumeratively certified, not mechanism-forced
  (0/4 pre-registered cross-field value laws); the prior open problem on
  the period-475 group theory is resolved up to the spectral
  support-pattern law.

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
| `golden_quadratic_*.py` (6 scripts) | Golden-quadratic duality: all-q dichotomy, invariant lattices, 7-adic Hensel, GF(49)/Pisano, exact monodromy + nulls | per-script results JSONs |
| `eisenstein_*.py` (3 scripts) + `phi6_ladder_identities_and_nulls.py` | Eisenstein residue-field model, motivic point count + torus action, Φ₆ ladder + null batteries | per-script results JSONs |
| `artin_mazur_zeta_gte_poly.py`, `gte_poly_glider_cycle_structure.py`, `gte_zeta_*.py` (4 scripts), `cycle_spectrum_null_battery.py` | Dynamical zeta data, vacuum uniqueness certificates, drift tests, torus entropy, null battery | per-script results JSONs |
| `nineteen_factor_*.py` (4 scripts) | Attractor factorization: CRT tower, linearization no-go, generalization battery, extended clock census | per-script results JSONs |
| `triangle_lift_theorem.py`, `triangle_residual_tests.py`, `triangle_projection_battery_regenerate.py` | Direct-Interpolation Lift census (dual method), residual batteries (identity-orbit inconsistency, projection nulls, 120-ordering census, grammar null), four-projection battery artifact | per-script results JSONs |
| `parity_projection_*.py` (4 scripts) | φ-forcing scope batteries: 777 additive forms, exhaustive + sampled recoding classes, architecture filters (displaced vacuum / closure), unrestricted-lookup vacuity certificates | per-script results JSONs |

## Lean Certification

Key Lean modules (all in ugp-lean, zero sorry):

- `UgpLean/Universality/Z7InvariantSubsets.lean` — Invariant Subset Uniqueness
  and QNR Binary Floor theorems
- `UgpLean/Universality/CUP3DUniqueness.lean` — GEN orbit chain theorems
- `UgpLean/Universality/MDLDerivabilityCriterion.lean` — T96-02 closure
- `UgpLean/Universality/PhiMDLUniversality.lean` — `rule110_z7_poly_rep`
- `UgpLean/Gravity/RelationalTime.lean` — `dimensional_protocol_principle_master`
- `UgpLean/Polynomial/GoldenQuadratic.lean` — diagonal factorization, duality
  bundle, 7-adic robustness, splitting law, ramification mechanism, GF(49)
  Frobenius swap, Pisano order (9 theorems)
- `UgpLean/Polynomial/EisensteinIdentities.lean` — F₂₁ residue-field model,
  torus equivariance and orbit decomposition, Φ₆ identity bundle, c_H = Φ₃(N_gen)
  certificates (7 theorems)
- `UgpLean/Polynomial/BiquadraticCompositum.lean` — alphabet-prime Artin class
  q ≡ 7, 13 (mod 15); Φ₆-stability lemma
- `UgpLean/Polynomial/AGL17ChiralZ2.lean` — AGL(1,7) order, reflection order 2,
  Rule 110 ↔ Rule 124 swap, color/chirality commutation
- `UgpLean/Polynomial/DynamicalZeta.lean` — vacuum uniqueness at every ring
  size, Möbius/Fibonacci certificates, de Bruijn certificate, prime-ring cycle
  dichotomy, period-475 attractor certificates (T⁹⁵ = σ³, return-map order 19,
  factorization, zero mean, charpoly certs)
- `UgpLean/Algebra/SRRGCABridge.lean` — `gte_poly_srrg_bridge` (archimedean
  fiber of the master quadratic)
- `UgpLean/Universality/TriangleLiftTheorem.lean` — orbit-parity provenance,
  Direct-Interpolation Lift (7⁸ census route), binary corollary, multilinear
  sparsity floor, chirality census
- `UgpLean/Universality/TriangleLiftStructural.lean` — structural Möbius
  lift route; canonical degree-≤6 sparsity floor
  (`gf7_rule110_sparsity_floor`)
- `UgpLean/Universality/ParityProjectionForcing.lean` — reduction-battery
  census counts (additive + mod-2 recoding)
- `UgpLean/Polynomial/SpinSevenWallSpectroscopy.lean` — directed wall and
  bump tables, composite hub identity, half-integer gap
  (`spin7_directed_wall_energies`)

## Computational Environment

- Python 3.10+ with numpy, matplotlib
- Taichi 1.7.3 (for `glider_search_taichi.py` and `orbit_visitation_rate.py`)
- Wolfram Engine 14.3.0 with SetReplace v0.3.196 (for `.wl` scripts)
- Lean 4 (elan) with Mathlib, as specified in `ugp-lean/lake-manifest.json`

## Related Papers

| Paper | Relation |
|-------|----------|
| P27 (SpivackSRRG) | SRRG fixed point g²+g−1 = 0: the archimedean fiber of the master quadratic |
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
NKS 2002, Cook 2004 (Rule 110 universality), Artin–Mazur 1965 (Ann. Math.
81(1):82–99, doi:10.2307/1970384 — dynamical zeta function), Ireland–Rosen
1990 (Springer — quadratic reciprocity, Eisenstein integers).
