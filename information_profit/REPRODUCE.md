# Reproduction Guide — Information Profit Threshold Code

This document describes how to reproduce all computational outputs from the
`information_profit/` code directory and its companion experiments.

---

## Requirements

- Python 3.9 or later
- numpy >= 1.21
- scipy >= 1.7
- matplotlib >= 3.4

Install:

```
cd information_profit/
pip install -r requirements.txt
```

---

## Step 1: Verify the Analytical Derivation

Run the standalone derivation verification script:

```
python verify_ipt_derivation.py
```

This computes phi, Lambda, and IPT from closed-form expressions and verifies the
numerical values match the paper to within tolerance 1e-4.

Expected stdout:

```
=== Information Profit Threshold Derivation Verification ===
phi      = 1.6180339887
ln(phi)  = 0.4812118251
ln(2*pi) = 1.8378770664
Lambda   = 0.2618302572
Lambda/2 = 0.1309151286
IPT      = 1.1309151286
PASS: IPT = 1.1309151286 is within 1e-04 of 1.1309
Result saved to results/ipt_derivation_verification.json
```

Output file: `results/ipt_derivation_verification.json`

SHA-256 of output (for a clean run): computed at runtime; values are deterministic
from closed-form arithmetic and will be identical across runs.

---

## Step 2: TE1.H Simulation

The TE1.H simulator is located in the MFRR validation program directory:

```
cd ../MFRR/TE_1_VALIDATION_PROGRAM/TE_1.H_LEVIN/
python run_te1h.py
```

This runs three scenarios for 400 steps each on a 64x64 grid and writes:
- `results/csv/unprofitable:_gen_drain_≈_0.8_(<_1.13)_coherence_history.csv`
- `results/csv/profitable:_gen_drain_≈_1.4_(>_1.13)_coherence_history.csv`
- `results/csv/profitable_gen_+_high_noise:_gen_drain_<_1.0_coherence_history.csv`

To additionally generate figures:

```
python te1b_pipeline_levin.py
```

Expected coherence slope (Delta-C per step):
- Unprofitable (rho ≈ 0.80): -1.94e-5
- Profitable (rho ≈ 1.40): +1.00e-4
- High Noise (rho < 1.00): -3.51e-5

SHA-256 of pre-computed CSVs:

| File | SHA-256 |
|------|---------|
| profitable CSV | `b63b40598999dc2283215d18a0e96d482092f5468462e416672777979abb7ad4` |
| unprofitable CSV | `ae2d9e96f52a8ce1c398a1c5e1065fe0e184705635873a715f3aa29e1a48fab2` |
| high-noise CSV | `1cc3cb6dccdf5c43e8479236b19ed1f4fc99f87f7dbb004bcfb56b97ae5794cd` |

---

## Step 3: TE2.1 Evolutionary Neural-Agent Experiment

```
cd ../MFRR/TE_2_Advanced_Explorations/TE_2_1_Recursive_Fidelity_Experiments/
python MFRR_Evolutionary_Genesis.py
```

Runs the evolutionary genesis experiment. Results are saved to
`results/MFRR_Evolutionary_Genesis_v2_YYYYMMDD_HHMMSS.json`.

To run the parameter sweep:

```
python MFRR_Evolutionary_Sweep.py
```

Sweep runs a 4x6 metabolic cost x decay rate grid with 3 seeds per point (72 runs total).
Results saved to `results/MFRR_Evolutionary_Sweep_YYYYMMDD_HHMMSS.json`.

**Note on reproducibility:** The genesis and sweep experiments use random initialization.
Re-running will produce new timestamped JSON files with values that may differ slightly
from the paper-reported aggregates (15/124 above IPT; supercritical mean 1.234) due to
different random seeds. The pre-computed result files in `results/` correspond to the
values reported in the paper. To reproduce the exact paper values, use those files
directly rather than re-running.

---

## Step 4: E4 Energy Model Check (Pre-Computed)

The E4 result is pre-computed at:

```
MFRR/E4_reflexive_landauer_results.json
```

SHA-256: `13cf53baaa10f02b9e5cda2b88fafaeff717fafa7057d1da4fcb4f3c938f4071`

Verify integrity:

```
shasum -a 256 ../MFRR/E4_reflexive_landauer_results.json
```

To regenerate from scratch:

```
cd ../MFRR/
python E4_reflexive_landauer_check.py
```

Expected results: 50/50 pass rate, min margin 0.0182, max 4.0798, mean 0.9481.
Exact values may vary slightly on re-run due to random parameter sampling.

---

## Summary of Outputs

| Component | Output file(s) | Deterministic? |
|-----------|---------------|----------------|
| IPT derivation | `results/ipt_derivation_verification.json` | Yes (closed-form) |
| TE1.H scenarios | `MFRR/.../results/csv/*.csv` | Yes (fixed seed) |
| TE2.1 genesis | `MFRR/.../results/MFRR_Evolutionary_Genesis_v2_*.json` | No (random init) |
| TE2.1 sweep | `MFRR/.../results/MFRR_Evolutionary_Sweep_*.json` | No (random init) |
| E4 check | `MFRR/E4_reflexive_landauer_results.json` | No (random params) |
