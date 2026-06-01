# ugp-physics

Companion repository for the **Universal Generative Principle (UGP)** physics paper series by Nova Spivack. This archive contains **peer-facing paper materials** (PDFs, LaTeX, figures, provenance) and **replication code** for the associated analyses.

Separate formalizations and tooling live in other public repositories; see [Related archives](#related-archives).

## Licenses

- **Code, scripts, configs, and bundled data files** (repository root and code directories): [PolyForm Noncommercial License 1.0.0](LICENSE) unless a subdirectory specifies otherwise.
- **Research prose** under `papers/` (LaTeX, BibTeX, figures, PDFs): [Creative Commons BY-NC-ND 4.0](papers/LICENSE).

**Local-only (gitignored):** internal specs under `specs/`, discovery lab notebooks under `ugp_discovery_lab/lab_notebooks/`, MFRR engineering notes under `MFRR/**/notes/`, large chat-export markdown (`*Massive_chat*.md`), and accidental `# UGP_lab*.sty` duplicates under `ugp_discovery_lab/`. They are not included in the public repository.

## Lean Formalization

The **ugp-lean** companion library provides machine-checked proofs for the UGP framework in Lean 4 (Mathlib). Current status: **286 modules, zero `sorry`, zero custom axioms** (standard Mathlib axiom signature). Every Category-A physics theorem has axiom closure exactly `{propext, Classical.choice, Quot.sound}` — the standard Mathlib signature.

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
- **Dark energy Ω_Λ = 0.6899** from PSC reflexive-closure count (CatAD, `psc_epoch_count`)
- **CMB tilt n_s = 0.96488** — 14 zero-sorry theorems (`n_s_formula`, P47)
- **SR clock ratio τ = 3/7** — derived from ether proper-time rate (`EtherProperTimeRate.lean`, CatAD)
- **SM gauge group SU(3)×SU(2)_L×U(1)_Y** — via three Z₇ channel identifications (`sm_gauge_group_certificate`)
- **SU(2)_L MDL gauging** — zero named axioms; bundle `su2l_l2_from_phimdl_potential_catad` (083B)
- **MDL Tower** — three nested MDL roles unified (`mdl_tower_bundle`, 083B)
- **PSC incompleteness → Ω_Λ** — `incompleteness_implies_nonzero_omega_lambda` (083B)
- **Particles–Computation–Spacetime Trinity** — `particles_computation_spacetime_trinity` (083B)
- **GTE polynomial five roles** — single-source principle (`gte_polynomial_five_roles_k_extra_zero`, 083B)
- **ΦMDL uniqueness** — no finite-resolution CA can exactly replicate its Lorentz invariance (`no_finite_ca_exact_lorentz_replica`)
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

To compile all papers: `bash compile_all_papers.sh --skip-mfrr` (48 papers, ~120 s).

## Replication scripts

Each paper folder includes `REPRODUCE.md` with step-by-step replication instructions and `PROVENANCE.md` with artifact lineage. Computational scripts live in `papers/NN_*/scripts/` or `papers/NN_*/canonical_run/`. Key verification tools include the **UGP_GTE_SM_Verifier** (see `UGP_GTE_SM_Verifier/`) which runs full-stack verification of all Standard Model predictions against PDG values.

## Related archives

- **ugp-lean** — Lean 4 formalization companion. GitHub: [novaspivack/ugp-lean](https://github.com/novaspivack/ugp-lean). Zenodo: [10.5281/zenodo.19433538](https://doi.org/10.5281/zenodo.19433538) (paper record), [10.5281/zenodo.19554700](https://doi.org/10.5281/zenodo.19554700) (source archive). **286 modules, zero sorry.**
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
