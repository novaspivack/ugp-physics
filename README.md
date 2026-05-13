# ugp-physics

Companion repository for the **Universal Generative Principle (UGP)** physics paper series by Nova Spivack. This archive contains **peer-facing paper materials** (PDFs, LaTeX, figures, provenance) and **replication code** for the associated analyses.

Separate formalizations and tooling live in other public repositories; see [Related archives](#related-archives).

## Licenses

- **Code, scripts, configs, and bundled data files** (repository root and code directories): [PolyForm Noncommercial License 1.0.0](LICENSE) unless a subdirectory specifies otherwise.
- **Research prose** under `papers/` (LaTeX, BibTeX, figures, PDFs): [Creative Commons BY-NC-ND 4.0](papers/LICENSE).

**Local-only (gitignored):** internal specs under `specs/`, discovery lab notebooks under `ugp_discovery_lab/lab_notebooks/`, MFRR engineering notes under `MFRR/**/notes/`, large chat-export markdown (`*Massive_chat*.md`), and accidental `# UGP_lab*.sty` duplicates under `ugp_discovery_lab/`. They are not included in the public repository.

## Lean Formalization

The **ugp-lean** companion library provides machine-checked proofs for the UGP framework in Lean 4 (Mathlib). Current status: **112 modules, zero `sorry`, zero custom axioms** (standard Mathlib axiom signature).

Key certified results include:
- **Asymptotic Sparsity Theorem** — unique seed (n=10, b₁=73) for all n ∈ ℕ
- **Residual Classification (RCC)** — established as a theorem over all compact simple Lie groups (`PSC.RCCInfiniteFamilies`)
- **Galois-protection non-renormalization** — one-loop QED correction to C_alg vanishes (`Phase4.GaloisProtection`)
- **Two-loop color coefficient** = (N_c²−1)/N_c² = 8/9 (`Phase4.TwoLoopCoefficient`)
- **SM winding numbers from N_c** (`BraidAtlas.ChargeDerivation`)
- All bare gauge couplings, VV exponents, Koide phase, neutrino FN texture, and more

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

To compile all papers: `bash compile_all_papers.sh --skip-mfrr` (29 papers, ~70 s).

## Precision computation scripts

The `papers/01_SM/canonical_run/` directory contains SHA-256 pre-committed computational certificates. Key precision-derivation scripts for P25:

| Script | Description |
|--------|-------------|
| `comp_p25_alpha_precision_floor.py` | 60-digit verification of C_alg, δ_target, b₁_req |
| `comp_p25_residual_structural_search.py` | Null-disciplined structural search of the 2.39 ppm residual |
| `comp_p25_galois_protection_probe.py` | O4a: Galois-protection census (SUPPORTED) |
| `comp_p25_o4b_analytic_proof.py` | O4b: six-step analytic proof of one-loop cancellation |
| `comp_p25_o3_two_loop_coefficient.py` | O3: R_real = (8/9)×α²/(2π²) (MATCH_WITHIN_PRECISION) |

## Related archives

- **ugp-lean** — Lean 4 formalization companion. GitHub: [novaspivack/ugp-lean](https://github.com/novaspivack/ugp-lean). Zenodo: [10.5281/zenodo.19433538](https://doi.org/10.5281/zenodo.19433538) (paper record), [10.5281/zenodo.19554700](https://doi.org/10.5281/zenodo.19554700) (source archive). **112 modules, zero sorry.**
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
