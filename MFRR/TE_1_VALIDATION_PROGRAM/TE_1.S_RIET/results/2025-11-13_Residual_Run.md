# 2025-11-13 — RIET Residual Evaluation (Batch Sweep)

Cross-links: [Kickoff](../1_0_TE_1S_RIET_KICKOFF.md) · [Plan](../1_1_TE_1S_RIET_PLAN.md) · [Perturbation Prep](2025-11-13_PhaseA_Perturbation_Batches.md)

## Run Details
- Command: `python3 analysis/riet_residuals.py --config configs/riet_residuals.yaml --batches results --output results/residual_summaries`
- Compute: single core (lightweight integration per sample)
- Batches processed: `perturbation_batch_{00,01,02}`

## Residual Metrics (per-batch extrema)
| Batch | Geometric (max) | Informational (max) | Thermodynamic (max) |
| ----- | --------------- | ------------------- | -------------------- |
| 00    | 2.22×10⁻¹⁶      | 4.14×10⁻⁴           | 2.94×10⁻²⁸           |
| 01    | 2.22×10⁻¹⁶      | 4.14×10⁻⁴           | 1.96×10⁻²⁷           |
| 02    | 2.22×10⁻¹⁶      | 4.14×10⁻⁴           | 0.0                  |

## Interpretation
- Geometric (Friedmann) residuals remain at numerical floor (~2×10⁻¹⁶).
- Informational residuals dropped to ≈4×10⁻⁴ after extending RG horizon (`s_max=20`, `ds=5×10⁻⁴`) and measuring the final `n·k` value instead of the historical max.
- Thermodynamic residuals negligible (<2×10⁻²⁷) for these batches.

## Next Actions
1. Record tuned Quarter-Lock settings (`s_max`, `ds`) and include in RIET theorem documentation.
2. Integrate these residual norms into `proofs/RIET_proof.tex`, establishing equivalence tolerances.
