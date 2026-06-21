# PROVENANCE — Mathematical Foundations of Reflexive Reality (MFRR)

**Workspace root (this tree):** `MFRR/`  
**Primary manuscript:** `Mathematical_Foundations_of_Reflexive_Reality.tex` 

## Repository snapshot (reference)

- Always read the current git revision (`git rev-parse HEAD`) when you need a citeable snapshot — do not copy a SHA from this file.

## Canonical validation bundles (policy)

| Program | Canonical artifact location | Notes |
|---------|----------------------------|--------|
| **TE₁.A TFT** | `TE_1_VALIDATION_PROGRAM/TE_1.A_TFT/results/run_20251107_210503/` | See `TE_1.A_TFT/results/CANONICAL_RUN.txt`. Non-canonical `run_*` dirs may exist historically; **do not** treat as citeable unless explicitly promoted. |
| **E-level scripts** | MFRR tree root (`E*.py`, `e*.py`, `g*.py` as in monograph § Code) | JSON/CSV/plot outputs alongside scripts or under `*_outputs/`. |
| **SRRG TS / V** | `SRRG_VALIDATION_PROGRAM/scripts/` | Data inputs under `SRRG_VALIDATION_PROGRAM/data/` (e.g. `canonical_sm_triples.json`). Outputs under `SRRG_VALIDATION_PROGRAM/outputs/` per script. |
| **BH tests** | `BH_REFLEXIVE_REALITY/scripts/` | CSV under `csv/`, figures under `figs/` **relative to cwd when script is run** from `scripts/`. |
| **Steel-man (Part V)** | `TE_2_Advanced_Explorations/TE_2_1_Recursive_Fidelity_Experiments/STEELMAN_V3/` | Monograph cites **`MFRR_*_Steelman.py`** at MFRR root; **thin wrappers** there delegate to this directory (`REPRODUCE.md`). |

## External / sibling repositories

| Asset | Status |
|-------|--------|
| **`../Delta_machine/...` figures** | Produced by the separate [delta-machine repo](https://github.com/novaspivack/delta-machine) (DOI: 10.5281/zenodo.19429884). The manuscript uses `\IfFileExists` guards so it compiles without them; to include them, clone delta-machine as a sibling directory alongside `MFRR/` and run the relevant DSAC scenarios per that repo's `REPRODUCE.md`. |
| **`pr0_system`** | Imported by TE₁.A; lives at `pr0_system/` in the root of the `ugp-physics` repository (sibling of `MFRR/`). |

## P13 Revision — 2026-04-20

### New Artifacts

| Artifact | Path | Date | Notes |
|----------|------|------|-------|
| `MFRR_Physics_Survey.tex` | `papers/21_mfrr_physics_survey/` | 2026-04-20 | PRIMARY: Portal paper — journal submission vehicle (moved to P21 folder) |
| `MFRR_Physics_Survey.pdf` | `papers/21_mfrr_physics_survey/` | 2026-04-20 | Compiled portal paper (12 pages, 0 errors) |

### Monograph Fixes Applied (2026-04-20)

| Fix | Location | Status |
|-----|----------|--------|
| G0-6: `SpivackPR1Operator` → `SpivackUGPFormalization,ugp-lean` | Lines 677, 685 | ✅ Done |
| COMP-13-B: gravity exponent framing (2.60 = intermediate regime, asymptotes to r⁻²) | Lines 176, 333, 387, 575, 10278, 10309, 10333, 11848 | ✅ Done |
| TE2.4 reframe: "worked toy-model example, not a proof of BH unitarity" | Line 11590 | ✅ Done |
| COMP-13-C: Added [T/B/C/I] claim-type column to theorem inventory table | Lines 1421–1528 | ✅ Done |
| COMP-13-D: Added IPT Conjecture box (Remark rem:IPT-conjecture) | After line 5590 | ✅ Done |
| T8 Holographic Closure: retagged [B]; note added in table caption | Table note | ✅ Done |

## Deprecations

- None centrally listed here — see `INVENTORY_AND_RUN_MATRIX.md` and `MASTER_STATUS.md`.
