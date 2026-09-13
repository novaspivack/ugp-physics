# TE_1.H — Levin Information Profit Experiments

Cross-links: [TE_1 Summary](../TE_1_SUMMARY.md) · [Session 1.6 log](../SESSIONS/1_6_TE_1H_LEVIN_INFORMATION_PROFIT_STUDY.md)

## Scope
- Validate the MFRR Information Profit Principle against Levin/Kolmogorov randomness benchmarks.
- Demonstrate adaptive homeostasis by maintaining target coherence under stochastic shocks.

## Directory Layout
- `information_profit_simulation.py`: Static profit margin sweeps (Gen/Drain/Noise).
- `adaptive_information_profit_simulation.py`: Adaptive homeostasis vs environmental noise shock.
- `te1b_pipeline_levin.py`: TE_1.B reflexive pipeline clone with Levin coherence metrics.
- `run_te1h.py`: Entry point mirroring `run_te1b.py` but emitting Levin coherence diagnostics.
- `configs/`, `data/`, `logs/`: Reserved for downstream integrations with TE_1.B reflexive analytics.
- `results/csv/`: Static coherence traces for baseline experiments.
- `results/adaptive/`: Adaptive vs control coherence and generation histories.
- `figs/`: Diagnostic plots (`adaptive_homeostasis_vs_shock.png`, `mfrr_information_profit_vs_levin_noise.png`).

## Metrics & Findings
- Profit threshold confirmed: only `Gen/Drain > 1.13` maintains increasing coherence.
- High Levin randomness acts as a drain, collapsing coherence in static runs.
- Adaptive controller saturates generation amplitude to sustain coherence post-noise shock.

## Next Actions
- Integrate TE_1.B reflexive pipeline clone within this module for coherence instrumentation.
- Compare adaptive coherence metric against live TE_1.B runs once instrumentation is in place.

