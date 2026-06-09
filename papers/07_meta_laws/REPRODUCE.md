# REPRODUCE — UGP Meta-Laws monograph

**Environment:** Python **3.10+** recommended (matches Discovery Lab). All `cd` paths below are relative to the **clone root** of [`ugp-physics`](https://github.com/novaspivack/ugp-physics).

---

## A. Build the PDF

```bash
cd papers/07_meta_laws
latexmk -pdf -interaction=nonstopmode ugp_meta_laws.tex
```

Ensure `global_rank_surprisal_montage.png` is present (see section C) or update `\includegraphics` / `\graphicspath` accordingly.

---

## B. ML-8 / ML-9 — Discovery Lab (GTE)

### B.1 Install the lab

```bash
cd ugp_discovery_lab
python3.10 -m pip install -e ".[plots]"
python3.10 -m pip install scipy
```

### B.2 Regenerate deep trajectories (feeds Q4 + entropy pipelines)

**Bundled shortcut:** `ugp-physics` includes **`UGP_discovery_lab_runs/exp_20260413_deep_trajectories/`** with the canonical JSON referenced by downstream YAMLs — you can skip B.2 and go to B.3 unless you want a fresh run.

To regenerate (match the run ID used in the shipped configs):

```bash
cd ugp_discovery_lab
python3.10 -m ugp_discovery_lab.cli.ugp run-experiment \
  -c configs/experiments/gte_deep_trajectories_paper.yaml --workers 12 \
  --run-name exp_20260413_deep_trajectories
```

**Expected structure:** `24` tasks × `50,000` steps = **1.2×10⁶** total simulated steps (matches the monograph).

### B.3 Point downstream YAMLs at your JSON

The shipped configs already list **`UGP_discovery_lab_runs/exp_20260413_deep_trajectories/results/reports/experiment_results.json`**. If you used a different `--run-name` in B.2, edit the `inputs.runs` entries in:

- `configs/experiments/gte_q4_basin_paper.yaml`
- `configs/experiments/gte_entropy_attractor_paper.yaml`
- `configs/experiments/gte_gsl_fit_paper.yaml`
- `configs/experiments/gte_rg_attractor_real_paper.yaml`

Then run:

```bash
python3.10 -m ugp_discovery_lab.cli.ugp run-experiment \
  -c configs/experiments/gte_q4_basin_paper.yaml --workers 4 \
  --run-name meta_laws_q4_basin

python3.10 -m ugp_discovery_lab.cli.ugp run-experiment \
  -c configs/experiments/gte_entropy_attractor_paper.yaml --workers 2 \
  --run-name meta_laws_entropy_attractor
```

Summaries appear under `UGP_discovery_lab_runs/<run>/results/reports/`.

**Cross-reference:** Step-by-step parity with the PRE paper is documented in  
`papers/04_dynamics_universality/REPRODUCE.md` and `PROVENANCE.md`.

---

## C. ML-7 — Zipf batch + montage

The monograph cites **`zipf_validation`** as the experiment name in prose; in this repository the implementation is the standalone script:

**`papers/07_meta_laws/UGP_theory_cross_domain_proofs.py`**

```bash
cd papers/07_meta_laws
python3.10 -m pip install numpy pandas matplotlib
python3.10 UGP_theory_cross_domain_proofs.py
```

**Outputs (default `OUT_DIR = zipf_outputs`):**

| Output | Purpose |
|--------|---------|
| `batch_zipf_summary.csv` | Table values for ML-7 appendix |
| `global_rank_surprisal_montage.png` | Figure `fig:global-montage` |
| `batch_zipf_summary.tex`, `zipf_methods.tex`, `zipf_results.tex` | Optional LaTeX snippets |
| `books/*.txt` | Cached Gutenberg downloads |
| Per-book `*_loglog_rank_freq.png`, `*_surprisal_vs_logrank.png` | Diagnostics |

Copy `global_rank_surprisal_montage.png` and `batch_zipf_summary.csv` beside `ugp_meta_laws.tex` when preparing a submission bundle (or symlink `figures/`).

**Optional:** set `FILE = "zipf_test_monte_christo.txt"` and place that corpus in `papers/07_meta_laws/` if you need the **Monte Cristo** row; the batch list in the script otherwise mirrors Gutenberg URLs inside the file.

---

## D. Optional companion utilities (not used for ML-8/9 table numbers)

See **`ARTIFACTS_AND_UTILITIES.md`** — **Universe Finder** (`streamlit_universe_finder.py`) and CLI ridge scans in `ugp_release/`. These support the broader UGP/GTE narrative and optional figures; they are **not** the source of the GTE statistics in ML-8/ML-9.

---

## E. Checklist before “reproducibility complete”

- [ ] `gte_deep_trajectories` run finished; JSON path wired into `gte_q4` + `gte_entropy` YAMLs  
- [ ] `gte_q4_basin_analysis` and `gte_entropy_attractor` reports match numbers in `ugp_meta_laws.tex` (or text updated)  
- [ ] `UGP_theory_cross_domain_proofs.py` run complete; `batch_zipf_summary.csv` and montage copied or referenced  
- [ ] `VERSION_TAG` in Zipf script + git commit recorded in `PROVENANCE.md` for the release tag  
