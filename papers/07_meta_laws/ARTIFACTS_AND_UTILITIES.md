# Artifacts and utilities — UGP Meta-Laws (publication bundle checklist)

This document collects **everything** needed to (1) reproduce empirical claims in `papers/07_meta_laws/ugp_meta_laws.tex`, and (2) ship a **standalone repository** later. Items are grouped by role.

### Publication scope (Zipf vs Meta-Laws)

Legacy Zipf draft materials (not bundled in this repository) are **not** a separate submission: empirical Zipf validation and the worked example live **only** in `ugp_meta_laws.tex` (ML-7). The Zipf batch code (`UGP_theory_cross_domain_proofs.py`) exists to reproduce **those** tables and figures for the Meta-Laws paper. ML-7’s claim (UGP-eligible ranked systems → Zipf-critical law) stands on the monograph’s own axioms; no change to that section is required when deprecating a separate Zipf publication.

---

## 1. Core manuscript (required)

| Item | Location |
|------|----------|
| LaTeX | `papers/07_meta_laws/ugp_meta_laws.tex` |
| PDF | `ugp_meta_laws.pdf` (build artifact; typically next to the `.tex` or under `figures/`) |
| Global Zipf montage | `global_rank_surprisal_montage.png` (generated; may live in `figures/` if you prefer) |
| Bibliography | `papers/bib/Spivack_Papers_Bibliography.bib` — for a spin-out, export **only** the keys `\cite{...}` in this paper into `references.bib`. |

---

## 2. ML-7 — Zipf corpora pipeline (required for empirical Zipf section)

| Item | Location | Notes |
|------|----------|--------|
| **Implementation** | `papers/07_meta_laws/UGP_theory_cross_domain_proofs.py` | Single-file batch; produces CSV, TeX snippets, PNGs, global montage. |
| **Default output directory** | `papers/07_meta_laws/zipf_outputs/` (created when you run the script from that folder) | Contains `batch_zipf_summary.csv`, `books/`, per-corpus plots. |
| **Legacy / duplicate trees** | Not bundled — any older `zipf_outputs/` snapshots are author-local | **Canonical publication path is this paper folder + `UGP_theory_cross_domain_proofs.py`.** Freeze outputs under `papers/07_meta_laws/zipf_outputs/` for reproducibility and record hashes in `PROVENANCE.md`. |
| **Monte Cristo row** | Included when `zipf_test_monte_christo.txt` is analyzed (see script `FILE` / batch paths in `main()`) | Present in e.g. `zipf_outputs/batch_zipf_summary.csv` rows. |

**Publication note:** The manuscript calls this pipeline `zipf_validation` in prose; the repository name is the Python script above. Keep that naming alignment in the Code Availability section.

---

## 3. ML-8 / ML-9 — GTE statistics (Discovery Lab) (required)

| Item | Location |
|------|----------|
| Package | `ugp_discovery_lab/` at the repository root (install `-e ".[plots]"`, `scipy`) |
| Deep trajectories | `ugp_discovery_lab/configs/experiments/gte_deep_trajectories_paper.yaml` → experiment `gte_deep_trajectories` |
| Q4 basin analysis | `ugp_discovery_lab/ugp_discovery_lab/experiments/gte_q4_basin_analysis.py` + `ugp_discovery_lab/configs/experiments/gte_q4_basin_paper.yaml` |
| Entropy vs attractor | `ugp_discovery_lab/configs/experiments/gte_entropy_attractor_paper.yaml` |
| Run outputs | `UGP_discovery_lab_runs/<run_id>/results/reports/*.json` and `.md` |

**Dependency:** Q4 and entropy YAMLs reference a **specific** `experiment_results.json` from a deep-trajectory run; see `REPRODUCE.md` for the regeneration order.

**Cross-paper:** The same pipeline is documented for the PRE Dynamics paper (`papers/04_dynamics_universality/`). Prefer **one canonical run id** and cite identical JSON in both PDFs.

---

## 4. Companion utilities (optional — narrative / pedagogy / other papers)

These tools support the **broader UGP program** (ridge exploration, “Universe Finder” UI). They are **not** the computational source of the ML-8/ML-9 numbers in the monograph unless you explicitly add citations to them.

| Utility | Location | Purpose |
|---------|----------|-----------|
| **Universe Finder** (Streamlit) | `papers/08_ugp_foundational_monograph/ugp_release/streamlit_universe_finder.py` | Interactive exploration of prime-locked “universes” / ridge diagnostics. |
| **CLI + core math** | `papers/08_ugp_foundational_monograph/ugp_release/ugp_cli.py`, `ugp_tools.py` | `scan`, tables, CSVs for figures. |
| **Tests** | `papers/08_ugp_foundational_monograph/ugp_release/test_phase3.py` | Sanity check for plotting + CSV build (`python3 test_phase3.py`). |
| **README** | `papers/08_ugp_foundational_monograph/ugp_release/README.md` | Quick start (`streamlit run streamlit_universe_finder.py`). |
| **Requirements** | `papers/08_ugp_foundational_monograph/ugp_release/requirements.txt` | Pin for reproducible Streamlit/CLI environment. |

**Spin-out suggestion:** Copy `papers/08_ugp_foundational_monograph/ugp_release/` into `tools/universe_explorer/` (or similar) under the future paper repo, keep `LICENSE.txt`, and document Python version + `pip install -r requirements.txt`.

---

## 5. Other “explorer” scripts in the monorepo (informational)

These are **not** required for `ugp_meta_laws.tex` unless you add new citations. Listed so you do not confuse them with ML-8/ML-9:

| Script | Location | Role |
|--------|----------|------|
| Path B improvement explorer | `ugp_discovery_lab/pathb_improvement_explorer.py` | Systematic non-triple modification tests |
| Breakthrough PMNS explorer | `ugp_discovery_lab/breakthrough_pmns_explorer.py` | PMNS sector search (flavor physics) |

---

## 6. Formal verification (external, immutable)

| Item | Citation |
|------|----------|
| `ugp-lean` | Published Zenodo/GitHub — see `\cite{ugp-lean}`; **do not** treat as a build artifact in this repo (SD-0). |

---

## 7. Minimal standalone repo layout (recommended)

```
ugp-meta-laws-paper/
  README.md                 # points to REPRODUCE.md
  ugp_meta_laws.tex         # copy from papers/07_meta_laws/ugp_meta_laws.tex
  figures/                  # optional
  references.bib            # extracted cites (from papers/bib/…)
  reproduce/
    zipf/                   # snapshot of papers/07_meta_laws/zipf_outputs/ OR submodule
    discovery_lab_pin.txt   # commit hash + run ids
  tools/ugp_release/        # optional: copy from papers/08_ugp_foundational_monograph/ugp_release/
```

Keep **`REPRODUCE.md`**, **`PROVENANCE.md`**, and this file at the repo root next to the TeX when publishing.
