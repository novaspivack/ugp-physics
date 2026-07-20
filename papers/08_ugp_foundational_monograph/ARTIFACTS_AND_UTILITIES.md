# ARTIFACTS AND UTILITIES — `UGP Paper/` tree

**Minimal** paths needed to build the PDF vs **optional** extras for exploration and tooling.

## Publication-critical (PDF + bibliography)

| Item | Purpose |
|------|---------|
| `Universal_Generative_Principle_UGP_Paper.tex` | Main manuscript |
| `../Master_Bibliography/Spivack_Papers_Bibliography.bib` | Shared bibliography (path relative to this folder) |
| `ugp_v2_out/atlas/` (or `\DataDir` you pass) | Generated CSV/PNG/PDF for data-driven figures when reproducing plots |

## `ugp_release/` — supported toolkit

| File / dir | Purpose | Required for paper numbers? |
|------------|---------|-------------------------------|
| `requirements.txt` | Pinned Python deps for Phase 3 | **Yes** (for scripted regeneration) |
| `test_phase3.py` | Smoke test for build/plot pipeline | **Yes** (verification) |
| `ugp_cli.py` | CLI entry | Often |
| `ugp_tools.py` | Library / helpers | Often |
| `build_paper.py` | Automation helper | Optional |
| `streamlit_universe_finder.py` | Interactive UI | **No** |
| `PHASE3_README.md`, `README.md` | Docs | Optional |
| `atlas/` | Bundled atlas-related assets | As needed for your workflow |

## Root-level scripts (monorepo)

| File | Purpose | Required? |
|------|---------|-----------|
| `main_n10_ridge.py` | Ridge / n=10 mirror-dual + prime-lock check | Context-dependent |
| `helper_1.py`, `helper_2.py` | Helpers | Optional |
| `Paper_Updates_UGP_atlas.py`, `Paper_2_updates_2_final_additions.py` | Paper/atlas automation | Optional |
| `UGP_GTE_UWCA_rule.py` | UWCA rule experimentation | Optional |

## Interactive / visual (optional)

| File | Purpose |
|------|---------|
| `GTE_UWCA_DEMO.html` | Browser demo |
| `UWCA_1D_CA_Emulator_DEMO.html` | Emulator demo |

## Documentation

| File | Purpose |
|------|---------|
| `UGP_BUILD_INSTRUCTIONS.md` | Atlas + LaTeX `\DataDir` |
| `How_to_Use_Sage_for_UGP_Project.md` | Sage (optional) |

## Deprecated

| Path | Note |
|------|------|
| `Previous ugp release - superceded - deprecated/` | Superseded by `ugp_release/`; keep for archaeology only |

## External (not in this folder)

- **ugp-lean** — Lean 4 repo + Zenodo; see `PROVENANCE.md`.
