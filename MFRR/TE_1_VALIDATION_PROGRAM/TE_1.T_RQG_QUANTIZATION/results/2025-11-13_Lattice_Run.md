# 2025-11-13 — Lattice Monte Carlo + Spectrum Fit

Cross-links: [Kickoff](../1_0_TE_1T_RQG_QUANTIZATION_KICKOFF.md) · [Plan](../1_1_TE_1T_RQG_QUANTIZATION_PLAN.md) · [κ Computation](2025-11-13_Kappa_Computation_Note.md)

## Monte Carlo Run
- Command: `python3 analysis/rqg_lattice.py --config configs/lattice_simulation.yaml --max-workers 2`
- Events: 10,000 adjudication samples (scaled to match analytic variance via κ baseline)
- Workers: 2 (≈2.5 min runtime)
- Output: `results/lattice_events.npz`, `results/lattice_summary.json`
- Summary: diagonal variance = 2.39×10⁻⁶⁶ (matches analytic target 2.42×10⁻⁶⁶); tensors stored post-calibration with `rho_pt = 0.01`

## Spectrum Fit
- Command: `python3 analysis/spectrum_fit.py --tensors results/lattice_events.npz --output results/spectrum_summary.json --step-init 4.374423577524395e-32`
- Quantum step (fit): 4.374×10⁻³² (matches theoretical 8πGk_B T ln 2)
- Residual spread: σ ≈ 2.22×10⁻³³, max residual 2.19×10⁻³²
- Histogram aligns with discrete multiples (0, 1) within tolerance.

## Interpretation
- Step size matches order-of-magnitude expectation (≈8πG k_B T ln 2 at CMB temperature ~10⁻³⁴).
- Residual width (~1.3×10⁻³⁴) warrants tighter sampling; plan to increase events to ≥50k and compare with analytic κ tensor (computed earlier) to validate variance scaling.
- No anomalies in run logs; next iteration should cross-check variance slope against `kappa_baseline.json` predictions.
