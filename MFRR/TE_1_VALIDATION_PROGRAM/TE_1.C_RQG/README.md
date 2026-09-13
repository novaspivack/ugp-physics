# TE_1.C — Reflexive Quantum Gravity (RQG EFT)

Cross-links: [TE_1 Kickoff](../1_1_TE_1_KICKOFF.md), [TE_1 Summary](../TE_1_SUMMARY.md), [TE_1.C Plan](TE_1.C.1_PLAN.md), [Phase 2 analytic note](TE_1.C.2_PHASE2_ANALYTIC_NOTE.md), [Analytic slow-roll derivation](TE_1.C.3_Analytic_SlowRoll_Derivation.md), [Interim status](TE_1.C.4_Interim_Status.md)

## 1. Run Metadata
- **Execution**: 2025-11-12, `Python 3.10.8` (Anaconda), `numpy 1.26.4`, `scipy 1.13.1`, `pandas 2.3.3`, on Apple M1 Max (macOS 15.5). Phase 1 pipeline invoked via  
  `PYTHONPATH='.' python MFRR/TE_1_VALIDATION_PROGRAM/TE_1.C_RQG/src/pipeline.py`.
- **Code modules** (all cross-referencing `TE_1.C.1_PLAN.md`):  
  • FRW solver — `MFRR/TE_1_VALIDATION_PROGRAM/TE_1.C_RQG/src/frw_background.py`  
  • RG running — `MFRR/TE_1_VALIDATION_PROGRAM/TE_1.C_RQG/src/g_running.py`  
  • Ringdown diagnostics — `MFRR/TE_1_VALIDATION_PROGRAM/TE_1.C_RQG/src/ringdown.py`  
  • Yukawa/PPN analysis — `MFRR/TE_1_VALIDATION_PROGRAM/TE_1.C_RQG/src/yukawa_ppn.py`  
  • Stability sweeps — `MFRR/TE_1_VALIDATION_PROGRAM/TE_1.C_RQG/src/stability.py`.  
  • Analytic spectra — `MFRR/TE_1_VALIDATION_PROGRAM/TE_1.C_RQG/src/spectra_analytic.py` (supersedes the retired multiprocessing perturbation solver).  
  • Slow-roll tuner — `MFRR/TE_1_VALIDATION_PROGRAM/TE_1.C_RQG/src/tune_slow_roll.py`.
- **Configs** (YAML, committed):  
  `configs/frw.yaml`, `configs/g_running.yaml`, `configs/ringdown.yaml`, `configs/yukawa.yaml`, `configs/stability.yaml`, `configs/spectra_slow_roll.yaml`.  
  Master seed `seed_master=1729` (propagated to stability trials); ODE tolerances `rtol=1e-7`, `atol=1e-9`; FRW grid spans 81 points across `m∈{0,0.01,0.05}`, `β∈{0,0.01,0.03}`, `ω̄∈{0,0.01,0.03}`, `R̄_F∈{0.68,0.70,0.72}` with `z_max=2`, `nsteps=1600`.

## 2. Methods Summary
- **FRW + Ψ background** (`frw_background.py`): integrates the reflexive Friedmann system using `scipy.integrate.solve_ivp`, evaluates energy densities, and fits CPL parameters `w(z)=w_0+w_a z/(1+z)` for both Ψ-sector (`w_ψ`) and total effective equation of state (`w_eff`). Figures `figs/H_*`, `figs/psi_*`, `figs/w_*` visualize Hubble ratios, coherence fields, and `w(z)` trends per grid point. The analytic mode toggles now exposes potential-based slow-roll diagnostics (`epsilon_potential`, `eta_potential`) for downstream use.
- **Renormalization running** (`g_running.py`): solves the one-loop inspired RG flow `G(k)=G_0/[1+β̂ G_0 \,ln(k/k_0)]` with `β̂ = α_reflexive + ω_sensitivity·Λ_slope`. Λ slope is imported from Moonshot 1 PSC Completeness (1.174×10⁻⁹ m⁻²). Outputs include `results/g_running.csv` and `figs/g_running.png`.
- **Ringdown diagnostics** (`ringdown.py`): starts from the Berti–Cardoso–Will Kerr fits for the `ℓ=2, n=0` mode and introduces adjudicative corrections proportional to `β_mix · ∇Ψ`. Produces fractional frequency/damping shifts and polarization mixing, persisted in `results/ringdown_summary.json` and `figs/ringdown_*`.
- **Yukawa & PPN** (`yukawa_ppn.py`): synthesizes the scalar-mediated potential `Φ(r) = -GM (1+α e^{-m_ψ r})/r`, fits `(α, m_ψ)` via log-linear regression, and evaluates the PPN parameter `γ(r)`. See `results/yukawa_profile.csv`, `results/yukawa_summary.json`, `figs/yukawa_*`.
- **Stability / energy conditions** (`stability.py`): perturbs initial conditions by Gaussian noise (`σ = 5×10⁻⁴`) across 24 realizations, re-integrates FRW, and records minimum DEC (`ρ - |p|`) and SEC (`ρ + 3p`). Logged in `logs/stability_*.json`.
- **Analytic spectra** (`spectra_analytic.py` + `tune_slow_roll.py`): constructs a slow-roll-compatible plateau via the analytic epsilon profile `ε(ψ)=ε₀ e^{-β(ψ-ψ_ref)}` (see `TE_1.C.3_Analytic_SlowRoll_Derivation.md`), integrates the background with forward e-folds (3.5 N), and evaluates horizon-exit spectra using the potential-based slow-roll arrays.

## 3. Results Summary
- **FRW attractor** — `w_ψ = -1.0000000006 ± 1.7×10⁻⁹`, `|w_a,ψ| ≤ 3.9×10⁻⁸` across 81 cases ⇒ **PASS** (target `|w_a| < 10⁻³`). Total `w_eff` reproduces ΛCDM-like behavior with matter-era excursions (see `results/frw_eos.csv`).
- **Running Newton constant** — relative excursion `ΔG/G₀ = 2.46×10⁻¹¹` over `k∈[10⁻⁶, 10²] m⁻¹`, consistent with Moonshot 1 Λ slope ⇒ **PASS** (no detectable Landau pole; see `results/g_running_summary.json`).
- **Ringdown sector** — fractional QNM shifts `Δω_R/ω_R = 8.4×10⁻⁶`, `Δ|ω_I|/|ω_I| = 4.2×10⁻⁶`, polarization mixing `2.0×10⁻⁴`; all well below current LIGO/Virgo tolerances ⇒ **PASS** for Phase 1 benchmarks.
- **Yukawa / PPN** — recovered `α = 2.50×10⁻⁵`, `m_ψ = 1.00×10⁻¹¹ m⁻¹`; Cassini-bound-compliant `|γ − 1| = 1.12×10⁻⁵ < 2.3×10⁻⁵` ⇒ **PASS**.
- **Stability** — DEC/SEC minima non-negative (DEC touches machine precision zero, SEC ≥ 3.4×10⁻⁹), no instabilities across 24 trials ⇒ **PASS**; detailed traces in `logs/stability_realizations.json`.
- **Curvature-tuned slow-roll spectra** — `configs/spectra_slow_roll.yaml` now uses the curvature kernel (`analytic_curvature_amp=5.2×10⁻⁵`, `center=4.008`, `width=0.614`) together with `analytic_eps0=3.961×10⁻³`, `ψ₀=4.0822`, `ψ_ref=2.591586`. The resulting horizon-exit point satisfies `ε_* = 5.67×10⁻³`, `η_* = 2.37×10⁻²`, `n_s = 0.96498`, `r = 0.0907` and is documented in `results/slow_roll_search_run3.json`. A ±2% robustness sweep (`results/slow_roll_search_run4.json`) shows `n_s` confined to [0.9631, 0.9668] and `r` to [0.0889, 0.0925]. Figures remain under `figs/spectra/`.

Supporting plots:  
`figs/g_running.png`, `figs/ringdown_frequencies.png`, `figs/ringdown_diagnostics.png`, `figs/yukawa_potential.png`, `figs/yukawa_ppn.png`, the FRW grid overlays in `figs/H_*`, `figs/psi_*`, `figs/w_*`, and slow-roll spectra figures in `figs/spectra/`.

## 4. Files
- `configs/` — reproducible YAML inputs (see absolute paths above).  
- `results/` — CSV/JSON artifacts: `frw_eos.csv`, `frw_eos_summary.json`, `g_running.csv`, `g_running_summary.json`, `ringdown_summary.json`, `yukawa_profile.csv`, `yukawa_summary.json`, `spectra_slow_roll.csv`, `spectra_slow_roll_summary.json`, `phase1_summary.json`.  
- `figs/` — visualization outputs enumerated above.  
- `logs/` — energy-condition diagnostics (`stability_realizations.json`, `stability_summary.json`).  
- `results/repro_bundle/` — manifest and README for external reruns.

## 5. Anomalies / Notes
- Numerical integration remains stable; all 81 FRW runs converge with default tolerances. `w_eff` shows the expected matter-era excursion (|w_eff|≈1 near z≈2); only `w_ψ` is used for PASS criteria.
- DEC minima reach machine precision zero under a few perturbations; values remain ≥0 without sign flips.
- RG denominator safeguarded against Landau poles; minimum denominator = 0.999999999754, well above the cutoff.
- Long FRW integrations (16k steps) show no drift: tail-window stats give `ε_mean ≈ 3.0`, `η_mean ≈ 1.1×10⁻⁷` for both the tuned configuration and a +1% curvature perturbation (`results/long_frw_baseline.json`, `results/long_frw_curvature_plus.json`).
- Robustness sweep confirms `(n_s, r)` remain inside [0.963, 0.967] × [0.089, 0.093]; see `results/slow_roll_search_run4.json`.
- Next steps: fold Phase 1 metrics into the TE₁ summary row and execute the remaining locks (continuum proof sketch, graviton scattering, BH microstates) per `TE_1.C.1_PLAN.md`.
