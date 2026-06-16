# ugp-physics

Companion repository for the **Universal Generative Principle (UGP)** physics paper series by Nova Spivack. This archive contains **peer-facing paper materials** (PDFs, LaTeX, figures, provenance) and **replication code** for the associated analyses.

**Main Synthesis Monograph (Paper 48) — [The Complete GTE Framework](https://doi.org/10.5281/zenodo.20560550):** Standard Model, Gravity, Quantum Mechanics, and Cosmology from Φ_MDL. This is the primary reference for the full theory. DOI: [10.5281/zenodo.20560550](https://doi.org/10.5281/zenodo.20560550)

Separate formalizations and tooling live in other public repositories; see [Related archives](#related-archives).

## Licenses

- **Code, scripts, configs, and bundled data files** (repository root and code directories): [PolyForm Noncommercial License 1.0.0](LICENSE) unless a subdirectory specifies otherwise.
- **Research prose** under `papers/` (LaTeX, BibTeX, figures, PDFs): [Creative Commons BY-NC-ND 4.0](papers/LICENSE).

**Local-only (gitignored):** internal specs under `specs/`, discovery lab notebooks under `ugp_discovery_lab/lab_notebooks/`, MFRR engineering notes under `MFRR/**/notes/`, large chat-export markdown (`*Massive_chat*.md`), and accidental `# UGP_lab*.sty` duplicates under `ugp_discovery_lab/`. They are not included in the public repository.

## Lean Formalization

The **ugp-lean** companion library provides machine-checked proofs for the UGP framework in Lean 4 (Mathlib). Current status: **360+ modules; zero `sorry` in all core results** (the only `sorry` placeholders are six documented scaffold stubs outside the core theorem path). Most structural results have axiom closure exactly `{propext, Classical.choice, Quot.sound}` — the standard Mathlib signature.

Key certified results include:
- **Weinberg angle** — sin²θ_W = 3/13 (tree-level) and 384729/1664000 (threshold-corrected), both zero sorry (`weinberg_angle_closure`, `weinberg_two_term_prediction`)
- **Wolfenstein λ = 9/40** — 0.000σ from PDG, exact arithmetic derivation
- **Strong CP: θ_QCD = 0** — exact, from F₂₁ discrete group theory, three independent proofs (`f21_theta_term_vanishes`)
- **QCD β-function** — b₀ = 7 = |Z₇| and b₁ = 26 from F₂₁ substrate (`b0_eq_z7_order`)
- **QCD mass gap Δ > 0** — unconditionally from orbit arithmetic (`no_psc_admissible_single_quark`)
- **Born rule** — P(k) = |c_k|² derived from Z₇ kink superselection with zero custom axioms
- **Koide relation** — Q = 2/3 as theorem; phase θ = 2/9 from N_c = 3 alone (`koide_angle_from_N_c_pure`)
- **CKM CP phase** — δ_CP = π/2 − 3/8 = 68.51°, zero sorry (`CKMCPPhase.lean`)
- **Newton's constant hierarchy** — M_Pl/m_τ = 21^10 · 7^(7/2) at 0.040% (`planck_density_bound_via_lifting`)
- **Classical Λ = 0** — exact from Z₇-symmetry at all seven vacua (`phimdl_potential_at_vacuum_zero`)
- **Dark energy Ω_Λ = 0.6899** from PSC reflexive-closure count (`psc_epoch_count`)
- **CMB tilt n_s = 0.96488** — 14 zero-sorry theorems (`n_s_formula`, P47)
- **SR clock ratio τ = 3/7** — derived from ether proper-time rate (`EtherProperTimeRate.lean`)
- **SM gauge group SU(3)×SU(2)_L×U(1)_Y** — via three Z₇ channel identifications (`sm_gauge_group_certificate`)
- **SU(2)_L MDL gauging** — zero named axioms; bundle `su2l_l2_from_phimdl_potential_catad`
- **MDL Tower** — three nested MDL roles unified (`mdl_tower_bundle`)
- **PSC incompleteness → Ω_Λ** — `incompleteness_implies_nonzero_omega_lambda`
- **Particles–Computation–Spacetime Trinity** — `particles_computation_spacetime_trinity`
- **GTE polynomial five roles** — single-source principle (`gte_polynomial_five_roles_k_extra_zero`)
- **ΦMDL uniqueness** — no finite-resolution CA can exactly replicate its Lorentz invariance (`no_finite_ca_exact_lorentz_replica`)
- **FGCI (Frobenius-Generation Coincidence Identity)** — a single identity unifies the arithmetic of {3, 7, 13, 73} (the generation count, strong coupling group order, Weinberg running denominator, and lepton N_eff seed) at N_c = 3; formally proved in Lean 4 (`FrobeniusChain.lean`, zero sorry)
- **PMNS neutrino mixing angles** — sin²θ₁₂ = 4/13, sin²θ₂₃ = 19/42, sin θ₁₃ = 11/73; zero free parameters; formally proved in Lean 4 (`NeutrinoSector.lean`, zero sorry)
- **Baryon asymmetry η_B = 6.109×10⁻¹⁰** vs PDG 6.10×10⁻¹⁰ (+0.15σ); derived via Φ_MDL kink–top coupling (FKTT); machine-certified CatAL (`FKTTCoupling.lean`: `fktt_coupling_bundle`, `kink_top_coupling_eq_eps_FN`, zero sorry, zero axioms)
- **Pion mass m_π = 139.5703 MeV** — 0.001% from PDG, derived via chiral condensate kink identification and Gell-Mann–Oakes–Renner; formally proved in Lean 4 (`chiral_condensate_kink_identification`, `pion_mass_from_gor`, zero sorry)
- **Hubble constant H₀ = 67.95 km/s/Mpc** — non-circular derivation from T_CMB; numerically confirmed (one external input: T_CMB)
- **Higgs quartic corrected** — λ = φ/(4π)(1 + ln φ/(54 ln 2π)), yielding m_H = 125.2499 GeV (0.0003σ from PDG); formally proved in Lean 4 (`HiggsQuartic.lean`, zero sorry)
- **Kink mass M^Q = 281 ± 21 MeV** — one-loop GJQW interface dim-reg (corrects prior log-cutoff value; consistent with classical BPS mass M_kink = 290.10 MeV within the scheme band)
- **Z₇ domain-wall network** — zero surviving domain-wall relic after the ordering crossover; gravitational-wave ceiling Ω_GW h² ≲ 3×10⁻⁴⁷ at f ≈ 0.02 Hz; ΔN_eff ≈ 0; parameter-free falsifiable prediction (P47)
- **Master quadratic** — the GTE polynomial's diagonal p(x,x,x)−x = −x(x²+x−1) unifies the Higgs-VEV derivation (SRRG ℝ-root 1/φ) and Rule 110 uniqueness (GF(7) rootlessness) as the archimedean and 7-adic completions of a single ℤ-quadratic; machine-certified (`gte_diagonal_quadratic_factorization`, `golden_floor_duality_bundle`, zero sorry)
- **Direct-Interpolation Lift** — the GTE polynomial rule is forced by UGP generation-orbit data alone, with no reference to the Rule 110 truth table: unique multilinear GF(7) rule from orbit ring evaluations, MDL sparsity floor, and a chirality census whose survivor set is exactly the chiral pair {Rule 110, Rule 124}; Rule 110 follows as the binary corollary; machine-certified (`ugp_orbit_interpolation_lift`, `orbit_chirality_census`, zero sorry)
- **Exact chiral gap law** — Spin-7 lattice interface gap Δ(β) = e^(−3β/2)[1 + ½e^(−β/2) + …] with the amplitude derived (not fitted) and the ratio law Δ₃ = 2Δ₂; wall energies machine-certified (`SpinSevenWallSpectroscopy`)
- **Derived tape spacing** — the matter-sector lattice spacing a = ℏc/Λ_GTE ≈ 0.0972 fm follows from MDL saturation (Tape Saturation Theorem, `tape_saturation_theorem`; conditional on the single named Compton-Support Criterion, proven minimal), with exact fixed-point signature ξ_kink = |Z₇| = 7 lattice sites
- **Nine charged-fermion masses at 0.295% RMS** — theoretical path with zero active parameters at prediction time (locked PDG-2022 benchmark; 0.261% vs PDG 2024); 1000-permutation null confirms arithmetic structure
- All bare gauge couplings, Koide phase, neutrino FN texture, and more

The **srrg-lean** library formalizes the Self-Referential Renormalization Group (SRRG). Key result: **EW VEV = 246.16 GeV** (−0.024% from v_PDG = 246.22 GeV), derived structurally via PSC entropy + S³ Goldstone manifold (zero sorry in core).

See [ugp-lean](https://github.com/novaspivack/ugp-lean) for the full theorem inventory.

## Installation

Requires **Python 3.10+** (`ugp_discovery_lab` enforces this in `pyproject.toml`). On macOS, the default **`python3` is often 3.9.x** (Apple's stub or an older Xcode toolchain), which is too old — create the venv with a 3.10+ interpreter instead (e.g. `python3.12 -m venv .venv`, Homebrew Python, pyenv, or conda).

```bash
python3.12 -m venv .venv   # or: /path/to/python3.10+ -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e ugp_discovery_lab/
```

Repeatable **post-clone smoke test** (venv, `ugp`, UGP_GTE_SM_Verifier, discovery engine, cleanup): see [`docs/CLONE_SMOKE_TEST.md`](docs/CLONE_SMOKE_TEST.md).

### Lean↔Python consistency tests

A regression test suite (`tests/lean_python_consistency/`) checks that all Python implementations match the Lean-certified structural constants:

```bash
python3 -m pytest tests/lean_python_consistency/ -v   # ~0.06 s, 28 tests
```

This suite catches the class of "formula drift" bugs where a Python implementation diverges from the Lean-authoritative formula. See `ugp_lean_canon/canonical_values.py` for the single source of truth for all Lean-certified constants.

### IDE / type-checker setup

The repository ships a `pyrightconfig.json` (Pyright / Cursor Pyright / Pylance). It sets `typeCheckingMode` to `basic` and suppresses several rule categories that produce false positives on scientific Python code.

If you use Cursor or VS Code, point the Python interpreter at your environment. Large artifacts are tracked with **Git LFS** (see `.gitattributes`: `*.csv`, `*.pkl`, `*.json`, `*.parquet`, `*.h5`).

## Paper index and replication

Each paper folder includes `REPRODUCE.md` (step-by-step replication) and `PROVENANCE.md` (artifact lineage).

| # | Topic | Folder |
|---|-------|--------|
| 00 | Survey and reader's guide (+ theory overview, master index) | `papers/00_survey_guide/` |
| 01 | Standard Model from UGP | `papers/01_SM/` |
| 02 | GTE particle spectrum | `papers/02_GTE_spectrum/` |
| 03 | Nuclear binding & periodic table | `papers/03_nuclear/` |
| 04 | Dynamics & universality | `papers/04_dynamics_universality/` |
| 05 | Uniqueness sieve | `papers/05_uniqueness/` |
| 06 | Algebraic & geometric foundations | `papers/06_math_foundations/` |
| 07 | Meta-laws | `papers/07_meta_laws/` |
| 08 | Foundational monograph | `papers/08_ugp_foundational_monograph/` |
| 09 | Architecture of a computable universe | `papers/09_architecture/` |
| 10 | Reflexive reality and self-defining physical law | `papers/10_reflexive_law/` |
| 11 | Ontological dissonance minimization | `papers/11_ontological_dissonance/` |
| 12 | Unified Rigidity Theorem (capstone) | `papers/12_unified_rigidity/` |
| 13 | MFRR foundational monograph | `papers/13_MFRR_foundational_monograph/` |
| 14 | PSC Concordance | `papers/14_psc_concordance/` |
| 15 | Information Profit Principle | `papers/15_information_profit/` |
| 16 | BH Reflexive Unitarity | `papers/16_bh_unitarity/` |
| 17 | Braid Atlas v2 | `papers/17_braid_atlas/` |
| 18 | Koide Cyclotomic Closed Form | `papers/18_koide_cyclotomic/` |
| 19 | Cyclotomic Mass Structure | `papers/19_cyclotomic_mass_structure/` |
| 20 | MFRR Physics Survey | `papers/20_mfrr_physics_survey/` |
| 21 | Neutrino Masses from Braid Atlas | `papers/21_neutrino_masses/` |
| 22 | UGP Dynamics (Interaction Skeleton) | `papers/22_ugp_dynamics/` |
| 23 | Closure Structure | `papers/23_closure_structure/` |
| 24 | Arithmetic Uniqueness of the Standard Model | `papers/24_deeper_theory/` |
| 25 | Genetic Code from UGP | `papers/25_genetic_code/` |
| 26 | General Selection Theory | `papers/26_general_selection/` |
| 27 | Self-Referential Renormalization Group (SRRG) | `papers/27_SRRG/` |
| 28 | Computational Universality and the Standard Model (Rule 110, Z₅ Rings, Mod-7 Structure) | `papers/28_computational_universality/` |
| 29 | The Mirror Branch Braid Atlas: Parameter-Free Dark Sector from UGP | `papers/29_dark_sector_braid_atlas/` |
| 30 | Machine-Certified Formalization of Cook's Rule 110 Universality Theorem in Lean 4 | `papers/30_cook_theorem/` |
| 31 | Arithmetic Derivation of the Electroweak Mixing Angle from Rule 110 Orbit Arithmetic | `papers/31_weinberg_angle/` |
| 32 | The CKM Wolfenstein Parameters from GTE Orbit Arithmetic | `papers/32_ckm_matrix/` |
| 33 | Deeper Consequences of Arithmetic Universality in the Standard Model | `papers/33_deeper_consequences/` |
| 34 | The GTE-Möbius Architecture: Arithmetic Unification of Computation and Transputation | `papers/34_gte_mobius_substrate/` |
| 35 | GTE Unification: Rule 110 Orbit Arithmetic ↔ SM Electroweak Sector | `papers/35_gte_unification/` |
| 36 | Emergent Gravity from Rule 110 Cellular Automaton | `papers/36_emergent_gravity_cmca/` |
| 37 | Quantum Mechanics from Rule 110: Hilbert Space, Hamiltonian, and Born Rule | `papers/37_quantum_mechanics/` |
| 38 | Emergent Gravity from the ΦMDL Field: Einstein Equations, Kink Sources, and Quantum Gravity Scale | `papers/38_emergent_gravity_phimdl/` |
| 39 | QCD Structure from the GTE Substrate: Asymptotic Freedom, Confinement, and Hadron Spectroscopy | `papers/39_qcd_from_gte/` |
| 40 | Algebraic Characterization of Rule 110 over GF(7) and Cook-Independent Turing Universality | `papers/40_gf7_polynomial_universality/` |
| 41 | The Three-Layer Chiral Minkowski Cellular Automaton: A Unified Discrete Spacetime Model | `papers/41_three_layer_chiral_minkowski_ca/` |
| 42 | The ΦMDL Field: Quantum Structure, Born Rule, and Continuum Completion of the Chiral Minkowski CA | `papers/42_phimdl_field/` |
| 43 | The Complete ΦMDL Framework: Algebraic Necessity, Quantum Mechanics, Emergent Gravity, and Uniqueness | `papers/43_phimdl_completeness/` |
| 44 | Quantum Gravity in the GTE/ΦMDL Framework: Functional Completeness | `papers/44_quantum_gravity/` |
| 45 | The Three-Tape Chiral Minkowski Cellular Automaton: Spacetime, Particles, and Gravity from a Shared Clock Protocol | `papers/45_three_tape_cmca/` |
| 46 | The GTE Polynomial as Unified Field Theory: One 19-Bit Description for Spatial Dynamics, Gauge Coupling, Gravity, Entanglement, and Baryon Number | `papers/46_gte_polynomial_uft/` |
| 47 | Cosmological Predictions of the GTE/ΦMDL Framework: Dark Energy, CMB Spectral Tilt, and Gravitational Signatures | `papers/47_gte_cosmology/` |
| 48 | The Complete GTE Framework: Standard Model, Gravity, Quantum Mechanics, and Cosmology from Φ_MDL | `papers/48_gte_complete_theory/` |
| 49 | MDL Selects the Wolfram Rule: Z₇ Dynamics, Algebraic Structure, and Standard Model Encoding of the GTE Polynomial | `papers/49_gte_polynomial_wolfram/` |
| 50 | The Spin-7 Lattice Model: Phase Transitions and Statistical Mechanics of the GTE Polynomial | `papers/50_spin7_lattice/` |
| 51 | Polynomial Transputation: Quantum Measurement, Computability Classification, and the SRRG Bridge | `papers/51_polynomial_transputation/` |
| 52 | The PSL(2,7) Algebraic Structure of the Generative Triple Evolution Framework | `papers/52_psl27_unification/` |
| 53 | The GTE Framework: A Comparative Assessment — Why a One-Field, Zero-Parameter, Machine-Certified Theory Bears Serious Consideration | `papers/53_gte_framework_assessment/` |
| 54 | The Fire in the Equations: Consciousness, Physics, and the Primordial Ground — A Synthesis of the GTE and NEMS Frameworks | `papers/54_fire_in_the_equations/` |

To compile all papers: `bash compile_all_papers.sh --skip-mfrr` (55 papers, ~120 s).

## Tutorials

The `tutorials/` directory contains a series of **26 accessible standalone tutorials** on the GTE framework — the **UGP Physics Tutorial Series**. Each tutorial is a self-contained PDF with worked examples, plain-English explanations, TikZ diagrams, and a Further Reading section with Zenodo DOIs. They require no prior expertise in advanced mathematics or physics.

| Tutorial | Topic |
|---|---|
| `problem_of_physics/` | The problem of physics: why the Standard Model needs an explanation |
| `polynomial_cheatsheet/` | The GTE polynomial p(L,C,R): what it is, term by term, and why it matters |
| `uwca_tutorial/` | How the UWCA works and how it runs Rule 110 on the UGP substrate |
| `wolfram_bridge/` | The GTE–Wolfram bridge: Rule 110, the causal graph, and the selection principle |
| `ugp_gte_masses/` | UGP → GTE orbit → N_eff cascade → InformationMassTransformer → fermion masses |
| `golden_quadratic/` | The master quadratic x²+x−1: Higgs VEV (real root) and Rule 110 (GF(7) rootlessness) |
| `levels_of_theory/` | The coarse two-level and fine four-level architecture; Lifting and Descent theorems |
| `psc_mdl/` | Perfect Self-Containment and MDL: why the universe has to select itself |
| `mdl_selection/` | How MDL eliminates 10^290 candidates to select the 19-bit polynomial |
| `phimdl_field/` | Φ_MDL: from discrete certificate to continuum quantum field |
| `particles_kinks/` | Particles as topological kinks: from the Φ_MDL field to the SM spectrum |
| `quantum_numbers/` | SM quantum numbers (charge, color, generations) from Z₇×Z₃ |
| `forces/` | How SU(3)×SU(2)×U(1) emerges from the polynomial |
| `strong_cp/` | Strong CP solved: θ_QCD = 0 exactly from F₂₁ group theory |
| `weinberg_angle/` | Weinberg angle, fine-structure constant, and gauge couplings from the polynomial |
| `hierarchy_problem/` | The hierarchy problem dissolved: deriving the Higgs mass and electroweak scale |
| `gravity/` | Gravity from description-length minimization: the MDL-Lovelock principle |
| `born_rule/` | The Born rule as a theorem; quantum measurement at Turing degree 0′ |
| `cosmological_constant/` | The cosmological constant: classical Λ=0 + structural bracket [3π/14, 0.6899] |
| `defect_cosmology/` | Z₇ defect cosmology: domain walls, phase transition, and the zero-relic prediction |
| `cmb_inflation/` | CMB, baryon asymmetry, and why there was no inflation field |
| `transputation/` | Transputation and degree 0′: quantum measurement as a computability theorem |
| `universality_undecidability/` | Computational universality, the Physical Incompleteness Theorem, and why the universe can't fully know itself |
| `three_tape_cmca/` | The three-tape CMCA: how 3+1D spacetime emerges from three synchronized 1D rules |
| `new_physics/` | New physics predictions: what GTE predicts will and won't be found |
| `falsifiability/` | The complete falsifiability register: all predictions with experimental status |

All tutorials follow a standardized format (series header, prerequisites/navigation box, Further Reading with Zenodo DOIs, central bibliography).

### Interactive Explainer

`tutorials/interactive_explainer/` is a self-contained browser-based tutorial series. Open `tutorials/interactive_explainer/index.html` in any browser — no server or installation required. Path 1 (Foundations) is complete with 7 lessons covering the problem of physics, PSC/MDL, the GTE polynomial, the UGP state space, the UWCA, GTE orbits, and the Triangle theorem. Additional paths are in development.

## Replication scripts

Each paper folder includes `REPRODUCE.md` with step-by-step replication instructions and `PROVENANCE.md` with artifact lineage. Computational scripts live in `papers/NN_*/scripts/` or `papers/NN_*/canonical_run/`. Key verification tools include the **UGP_GTE_SM_Verifier** (see `UGP_GTE_SM_Verifier/`) which runs full-stack verification of all Standard Model predictions against PDG values.

## Related archives

- **ugp-lean** — Lean 4 formalization companion. GitHub: [novaspivack/ugp-lean](https://github.com/novaspivack/ugp-lean). Zenodo: [10.5281/zenodo.19433538](https://doi.org/10.5281/zenodo.19433538) (paper record), [10.5281/zenodo.19554700](https://doi.org/10.5281/zenodo.19554700) (source archive). **360+ modules; zero `sorry` in all core results.**
- **srrg-lean** — Lean 4 formalization of the Self-Referential Renormalization Group (SRRG). Key result: EW VEV = 246.16 GeV derived structurally. GitHub: [novaspivack/srrg-lean](https://github.com/novaspivack/srrg-lean).
- **rule110-lean** — Lean 4 formalization of Rule 110 Turing universality. GitHub: [novaspivack/rule110-lean](https://github.com/novaspivack/rule110-lean).
- **unified-rigidity-lean** — Lean 4 bridge library for the Unified Rigidity capstone theorem. GitHub: [novaspivack/unified-rigidity-lean](https://github.com/novaspivack/unified-rigidity-lean).
- **delta-machine** — Published software archive; see the project repository for the current DOI.

## Citing this repository

```bibtex
@misc{spivack_ugp_physics_repo,
  title        = {ugp-physics: code and data for the {UGP} physics paper series},
  author       = {Spivack, Nova},
  year         = {2026},
  howpublished = {\url{https://github.com/novaspivack/ugp-physics}},
  note         = {Companion code and paper materials; use the Zenodo DOI for a versioned archive when available}
}
```

## Master bibliography

A single bibliography file for LaTeX builds lives at `papers/bib/Spivack_Papers_Bibliography.bib`.
<!-- NOVA_ZPO_ZENODO_PAPER_BEGIN -->
**Archival paper (Zenodo preprint) (Zenodo):** https://doi.org/10.5281/zenodo.20702407
<!-- NOVA_ZPO_ZENODO_PAPER_END -->
