# Provenance: exp_20260413_deep_trajectories

## What this run is

24 GTE trajectory experiments × 3 law policies × 2 window sizes = deep trajectory generation
at 50,000 evolution steps per configuration. Seeds tested: canonical Lepton Seed (1,73,823),
mirror (1,73,2137), off-residual probes (2,89,1597) and (3,97,2203). Law policies:
mersenne_fib, mersenne_lucas, repunit_fib.

## Primary artifact

`results/reports/experiment_results.json`

**SHA-256:** `bcfaa8334cbbd512bf0e50e7d66853b56cf10708bb493cd3b289f17195ce4842`

This hash is recorded in `computational_concordance/canonical_seed_basin_report.json`
and is the basis for all basin assignment claims in that report.

## Why not pushed to GitHub

The raw `experiment_results.json` is large (Git LFS tracked). The file is retained locally
as the primary evidence archive. The SHA-256 hash above provides cryptographic auditability
without requiring the file to be publicly hosted.

## Summary results

| Seed | Basin (all 6 runs) | q_early_mean_abs |
|------|--------------------|-----------------|
| (1,73,823) canonical | A | 0.0256 |
| (1,73,2137) mirror | A | 0.0173 |
| (2,89,1597) off-residual | C | 0.0061 |
| (3,97,2203) off-residual | B | 0.0673 |

Basin assignments are deterministic across all tested law/window combinations.
Canonical-family seeds (Lepton Seed + mirror) are consistently in basin A;
off-residual seeds land in separate basins B and C.

## How to reproduce

Config file: `ugp_discovery_lab/configs/experiments/gte_deep_trajectories_paper.yaml`

Run from repo root:
```
python -m ugp_discovery_lab.run_experiment \
    --config ugp_discovery_lab/configs/experiments/gte_deep_trajectories_paper.yaml
```

The output `experiment_results.json` should match the SHA-256 above (assuming same
random seed and environment). The full reproduction environment is documented in
`papers/04_dynamics/REPRODUCE.md`.

## Git tracking

`experiment_results.json` is tracked by Git LFS (see root `.gitattributes`: `*.json filter=lfs`).
It is NOT pushed to the public GitHub repository due to size. The file is held locally.

For Lean finite-certificate purposes, `exp_20260412_rg_sweep_full` (224 tasks, smaller)
is the recommended candidate for basin certification — its `experiment_results.json` is
also LFS-tracked and locally present.
