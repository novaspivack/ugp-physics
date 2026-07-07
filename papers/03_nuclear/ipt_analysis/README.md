# Nuclear IPT Analysis

Supporting code for the nuclear IPT reconciliation result (§sec:ipt_reconciliation).

## Result
κ_emp/κ_min(N=50) = 1.149 ≈ IPT = 1.131 (1.6% match)

The empirical Nilsson spin-orbit coupling κ = 0.050 equals the Information Profit
Threshold times the minimum coupling for the N=50 shell closure.

## Files
- `nilsson_model.py` — Nilsson single-particle energy level computation
- `nuclear_ipt_analysis.py` — IPT reconciliation analysis

## Requirements
numpy, scipy

## Usage
```bash
python3 nuclear_ipt_analysis.py
```

## Claim grade
[B] Computationally established. The N=50 normalization is physically motivated
(first robust SO-only magic number) but not axiomatically derived.
