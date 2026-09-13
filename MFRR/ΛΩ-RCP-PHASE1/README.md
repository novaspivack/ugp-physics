# ΛΩ-RCP: Reflexive Closure Program (Λ–Φ–Ω Validation)

## Goals

1. **Lemma 1**: Fisher heat–kernel scaling ⇒ spectral dimension vs. curvature (Λ–Φ duality normalization).

2. **Lemma 2**: Recursive bundle action ⇒ meta-adjudication stress and Landauer hierarchy vs. log(depth).

3. **Lemma 3**: Observer complexity lower bound ⇒ PSC stability vs. observer capacity.

4. **SRRG–RG duality test**: β-function equivalence in Gaussian/ϕ⁴ toy sectors.

5. **Profit–Curvature identity**: log(Gen/Drain) vs. ∫R_F slope ≈ Λ.

## Quick Start

```bash
make init
make all
```

## Outputs

- `results/*.csv` and `results/*.json` with PASS/FAIL status
- Plots: `results/fig_*.png` (if visualization is enabled)

## Acceptance Criteria

- **L1**: intercept≈d within ±0.05; slope within 5–10% of Λ.
- **L2**: after regressing coherence term, total energy slope vs. log(depth) within 10% of k_B T.
- **L3**: threshold capacity c* within 10–20% of generator complexity proxy.
- **RG**: mean relative β-error < 15% in perturbative regime; fixed-point locations match within tolerance.
- **PC**: slope a in log(Gen/Drain)=a∫R_F+b within 10% of Λ; threshold near 1.13 on small positive curvature.

## Structure

```
ΛΩ-RCP/
├── src/rcp/          # Core implementation modules
├── cfg/              # Configuration files
├── data/             # Input data (if needed)
├── results/          # Output files (CSV, JSON, plots)
├── logs/             # Execution logs
├── docs/             # Documentation (.md files)
└── env/              # Virtual environment
```

## References

See documentation in `docs/` for detailed theoretical background and implementation notes.

