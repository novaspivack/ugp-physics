# TE₁.C Slow-Roll Validation — Sequenced Plan (Phase 1 Completion)

**Status:** curvature-aware baseline now delivers \(n_s \approx 0.965\), \(r \approx 0.091\) with controller-neutral dynamics (see `configs/spectra_slow_roll.yaml`). This plan records the final steps to secure a scientifically valid PASS and archive the evidence.

---

## 1. Objectives

1. **Theoretical closure** – document how the curvature modulation shapes \(\epsilon\) and \(\eta\) without altering the slope, and link the tuned parameters to the derivation.
2. **Robustness evidence** – show the tuned point is stable under ±2% parameter variation and longer FRW evolutions.
3. **Documentation & cross-links** – refresh README / summary tables, and capture all artefacts required for the final PASS report.

---

## 2. Work Packages & Owners

| # | Work item | Description | Owner | Status |
|---|-----------|-------------|-------|--------|
| 1 | Curvature derivation addendum | Extend `TE_1.C.3_Analytic_SlowRoll_Derivation.md` with the curvature kernel, showing its effect on \(\epsilon\) and \(\eta\), and reference tuned parameters. | GPT-5 Codex | ☑ |
| 2 | Robustness sweep (±2%) | Run `tools/slow_roll_parallel_search.py` around the curvature baseline (≥256 samples, 9 workers) and archive `results/slow_roll_search_run4.json`. summarise `(n_s, r)` distribution. | GPT-5 Codex | ☑ |
| 3 | Long FRW stability checks | Integrate FRW background for ≥16k steps (two variants of `psi0`) and store `results/long_frw_*` diagnostics (ε, η over time). | GPT-5 Codex | ☑ |
| 4 | README / summary refresh | Update `TE_1.C_RQG/README.md`, `SESSIONS/TE_1_SUMMARY.md`, and link robustness artefacts & curvature derivation. | GPT-5 Codex | ☑ |
| 5 | PASS bundle prep | Export plots (`spectra`, `je_hist`, `crooks_ratio`), metrics JSON, robustness histograms into `results/PASS_BUNDLE_YYYYMMDD`. | GPT-5 Codex | ☑ |

---

## 3. Execution Notes

- **Robustness ranges** (±2% about the tuned point)
  - `analytic_eps0 ∈ [0.00388, 0.00404]`
  - `analytic_curvature_amp ∈ [0.000051, 0.000053]`
  - `analytic_curvature_center ∈ [3.93, 4.09]`
  - `analytic_curvature_width ∈ [0.602, 0.627]`
  - `analytic_psiref ∈ [2.54, 2.64]`
  - `analytic_transition_amp ∈ [-0.0028, -0.0018]`
  - `analytic_plateau_amp ∈ [-0.010, -0.0091]`
  - `rf_bar ∈ [0.944, 0.963]`
  - `psi0 ∈ [3.99, 4.17]`

- **Long FRW runs**
  - Temporarily set `nsteps=16000` (or override in script) and record time series of `epsilon`, `eta`, `psi` for two scenarios (baseline and +1% curvature amp).

- **Artefact checklist**
  - `configs/spectra_slow_roll.yaml` (committed)
  - `results/slow_roll_search_run3.json` (best-fit) + `run4` robustness
  - `results/long_frw_baseline.json`, `results/long_frw_curvplus.json`
  - Updated plots in `figs/spectra/`
  - Updated README & summary references
  - Final PASS bundle with metrics JSON + plot snapshots

---

## 4. Signing Off

The plan is complete when:

1. Derivation addendum merged.
2. Robustness sweep summary demonstrates `(n_s, r)` staying within Planck + headroom.
3. Long-run FRW traces show no instabilities.
4. README / summaries cross-link all artefacts.
5. PASS bundle assembled and noted in `TE_1.C.4_Interim_Status.md`.

Final step completed: `TE_1.C_RQG/TE_1.C.4_Interim_Status.md` updated and TE₁ summary now marks PASS.
