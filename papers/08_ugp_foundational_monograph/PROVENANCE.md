# PROVENANCE — Foundational UGP monograph (`UGP Paper/`)

**Manuscript:** `Universal_Generative_Principle_UGP_Paper.tex` — *From UGP to GTE: Prime-Locked Universes, Minimality, and the Emergence of Our World*  
**Bibliography (shared):** `../Master_Bibliography/Spivack_Papers_Bibliography.bib` (compile from this folder so the relative path resolves).

## Frozen references (public)

| Artifact | Role | Pointer |
|----------|------|---------|
| **ugp-lean** (source) | Machine-checked Lean 4 formalization | GitHub: `https://github.com/novaspivack/ugp-lean`; Zenodo version DOI **10.5281/zenodo.19554700** (bib key `ugp-lean`) |
| **Formalization paper** | Companion write-up to the Lean artifact | Zenodo **10.5281/zenodo.19433538** (bib key `SpivackUGPFormalization`; concept DOI noted in `.bib`) |
| **RSUC / Lepton seed hub** | Certified uniqueness context for `(1,73,823)` | `SpivackUnifiedRigidity` in master bib |

**SD-0:** The `ugp-lean` repository is a **reference artifact**, not edited from this epic; this folder updates **manuscript and bibliography keys only** when aligning citations.

## Data and graphics hooks in the TeX

The preamble defines `\DataDir` (default `.`), `\AtlasDirA` (`./ugp_v2_out/atlas`), `\AtlasDirB` (`./ugp_v2_out/atlas_alt`). Figures and tables **conditionally** load:

- `survivors.csv`, `orders.csv` (ridge / universe scan outputs)
- `fib_index_hist.csv` (histogram data for plots)
- `basin_plot.png`, `fib_index_hist.png`, `mini_atlas_counts_10_22.png`, `mini_atlas_density_10_22.png`
- Optional verifier bundle: `full_referee_report.json`, `code_sha.txt`, `coeffs_sha.txt`, `triples_sha.txt` under `\DataDir`

If files are absent, the document uses placeholders or schematic fallbacks where implemented.

## Primary code locations (this tree)

- **`ugp_release/`** — Phase 3 toolkit: `ugp_cli.py`, `ugp_tools.py`, `streamlit_universe_finder.py`, `build_paper.py`, `test_phase3.py`, `requirements.txt`, `atlas/` assets.
- **Root helpers:** `main_n10_ridge.py`, `helper_1.py`, `helper_2.py`, `Paper_Updates_UGP_atlas.py`, `Paper_2_updates_2_final_additions.py`.
- **UWCA reference implementation:** `scripts/UGP_GTE_UWCA_rule.py` — (A) GTE-as-UWCA-program macro witness on the canonical n=10 orbit, emitting `gte_uwca_trace.csv`; (B) the survivor-window UWCA (per-coordinate prime alphabets, clopen penalty, deterministic sweep) and (C) the register-rail P1–P4 realization, both running Rule 110 on non-trivial tapes with cell-exact verification at every step against an independent native Rule 110 implementation, emitting `uwca_rule110_sidebyside.png` (spacetime diagram, UWCA-emulated vs native) and `uwca_rule110_verification.json` (verification summary).
- **Demos (optional, not required for PDF numbers):** `GTE_UWCA_DEMO.html`, `UWCA_1D_CA_Emulator_DEMO.html`.
- **Deprecated:** `Previous ugp release - superceded - deprecated/` — retained for history; use **`ugp_release/`** for current workflows.

## Policy on duplicates and backups

- Files matching `* copy.*` or `*.bak` are **non-authoritative**; prefer the non-copy filename or `ugp_release/` when documenting reproduction. (A redundant `main_n10_ridge copy.py` was removed in favor of `main_n10_ridge.py`, which includes the mirror-dual check.)
- Do not delete deprecated folders without a migration note in this file and in `REPRODUCE.md`.

## Revision history

| Round | Date | Commits | Key Changes |
|-------|------|---------|-------------|
| Round 1 | 2026-04-20 | `ce90fffc` | k_gen corrigendum, c₃ tcolorbox, claim legend, PR-1/App K reframe, §A.2 Transputation, ugp-lean 86 modules, P18/P19 refs |
| Round 2 | 2026-04-20 | `f87bfc6c` | §1.6 uniqueness fix (n=13/n=22), Nexus boxed theorem, DOF ledger (Appendix DOF), Conjecture C rename, classifying topos demoted, bootloader softened, Zeta-Mersenne pre-reg label, Bridges cross-refs (NEMS 45-47, 79-80) |
| Round 3 | 2026-04-20 | `a3ad1d0c` | NEMS Suite table (Appendix), Lean proof appendix T1-T12 (Appendix), B★ convention disclosure (§C.1 remark), bib entries SpivackNEMS36/76/77 |

**Current state (2026-04-20):** Content-complete, submission-ready. All adversarial review items resolved. Zero errors, zero undefined refs. 123 pages.

## Revision note

Internal development specs and process docs are **not** part of the public provenance story; this file describes **shippable paths and public DOIs** only.
