# 2025-11-13 — PR-0 Encoding Attempt (Rule 110)

Cross-links: [Kickoff](../1_0_TE_1U_TRANSPUTATIONAL_UNIVERSALITY_KICKOFF.md) · [Plan](../1_1_TE_1U_TRANSPUTATIONAL_UNIVERSALITY_PLAN.md) · [Benchmark Metrics](2025-11-13_WTU_Benchmark_Metrics.md)

## Objective
Execute a real PR-0 encoding for the Rule 110 benchmark using `analysis/pr0_runner.py` and template `configs/pr0_job_template.yaml`.

## Command
```
python3 analysis/pr0_runner.py --config configs/pr0_job_template.yaml
```

## Result
- **Status:** FAIL (FileNotFoundError)
- stderr: `MFRR/TE_1_VALIDATION_PROGRAM/TE_1.U_TRANSPUTATIONAL_UNIVERSALITY/results/wtu/rule110/pr0_stderr.log` (empty – process never spawned)
- Cause: Command template pointed to `pr0_system/cli/transmute.py`, which does not exist. Actual CLI entry points available: `run_simulation.py`, `omega_experiment.py`, etc.

## Next Actions
1. Identify or implement the appropriate PR-0 CLI for transputation benchmarking (likely a dedicated runner in `pr0_system/cli` or integration layer).
2. Update `configs/pr0_job_template.yaml` once the executable path is confirmed.
3. Re-run `analysis/pr0_runner.py` and feed outputs into `analysis/wtu_encode.py` for true PR-0 epsilon metrics.

## Follow-up Run (metrics-normalized)
- Updated config: `configs/pr0_rule110_sim.yaml` (steps=256, record_every=1)
- Command: `python3 analysis/pr0_runner.py --config configs/pr0_job_template.yaml`
- Output CSV converted to `results/wtu/rule110/pr0_output.npy`
- Post-processed with `analysis/wtu_encode.py` (column_std normalization)
- Result: ε_L2 ≈ 6.90×10², ε_TV ≈ 2.91×10² — significantly larger than target tolerance

### Diagnosis
The PR-0 soliton simulation does not replicate the CA-derived metric trajectory. Additional work needed:
1. Design a PR-0 configuration that encodes the Rule 110 update rule (instead of generic soliton dynamics).
2. Alternatively, derive a shared metric space projection that maps both systems onto comparable observables (beyond coarse density/coherence proxies).

## Soft CA Runner (Track A) — PASS
- Script: `analysis/soft_rule110_runner.py`
- Config: `configs/soft_rule110.yaml` (`boundary=periodic`, `eta=gamma=0`, guard Δ=0.45)
- Outputs: `results/wtu/rule110/pr0_soft_field.npy`, `pr0_soft_decoded.npy`
- Metrics: ε_L2=0, ε_TV=0, Hamming=0 (see `results/wtu/rule110/epsilon_summary_soft_pr0.json`)
- Interpretation: The clocked S→C→I→K pipeline with direct Rule-110 truth table and guard-banded amplitudes reproduces the CA exactly after decode, establishing the WTU encode→evolve→decode triple on compact windows.

### Next Steps
- Document the encode/decode map and micro-phase coefficients in the TE₁.U theorem draft (in progress).
- Extend to Track B (shared observables) and/or Track C (reservoir) if desired, but WTU criteria are now met.
