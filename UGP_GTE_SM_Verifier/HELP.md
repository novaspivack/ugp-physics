# UGP GTE SM Verifier — modes and commands

Version: 2.0.0-v7-DUAL-PATH

## What each mode demonstrates

| Mode | CLI | Active UCL | Typical primary σ | Claim |
|------|-----|------------|---------------------|-------|
| Empirical benchmark | default / dual-path empirical arm | UCL2.3 fit | ~0.003% | Functional form fits data (not a precision claim) |
| Dual-path theoretical (P01 headline) | `--run-dual-path` | UCL2.3 + derived renorm_K + URC | ~0.29% | Locked zero-fit-at-prediction-time spectrum |
| Bare Elegant Kernel limit | `--coeffs-source limit --run-fully-theoretical` | THEORETICAL_COEFF_VECTOR | ~1.1% | Kernel targets vs empirical palette |
| CMCA IMT mixer | `--imt-mixer-mode cmca` | (either coeffs) | ≈ v12 for masses today | Structural mixer audit |

**Important:** `--run-dual-path` does **not** substitute Elegant Kernel coefficients into the mass pipeline.
The theoretical arm only changes renorm_K (and URC). Coefficient targets are compared in
`dual_path_comparison.json` / `theoretical_coefficients.json`.

`k_gen` in the theoretical vector is φ·cos(π/10) ≈ 1.5388 (Lean `thm_ucl2_fully_unconditional`), not π/2.

## Canonical commands

```bash
# Full P01 artifact battery
python3 UGP_GTE_SM_Verifier.py --preset-fullstack --n 10 --full-derivation 1

# Dual-path (headline 0.29% theoretical arm)
python3 UGP_GTE_SM_Verifier.py --n 10 --mode phys --quiet \
  --coeffs-source empirical --imt-mixer-mode v12 --run-dual-path

# Bare kernel limit (~1.1%)
python3 UGP_GTE_SM_Verifier.py --n 10 --mode phys --quiet \
  --coeffs-source limit --imt-mixer-mode v12 --run-fully-theoretical

# Reference regression
python3 UGP_GTE_SM_Verifier.py --verify-reference --n 10

# Regenerate this file
python3 UGP_GTE_SM_Verifier.py --write-help-md
```

## Canonical knobs

| Knob | Value | Flag |
|------|-------|------|
| Phase mode | legacy (reference lock) | `--phase-mode legacy` |
| Phase k | 2.0 | `--phase-k 2.0` |
| renorm_K | 1400 (empirical path) | `--renorm-K 1400` |

P01 frozen audit: `papers/01_SM/canonical_run/comp_p01_ucl_coeff_audit.py`


Verifier modes (P01 / coefficient audit)
----------------------------------------
--run-dual-path
  Paper headline comparison. BOTH arms use frozen UCL2.3 (empirical coeffs).
  Empirical arm: renorm_K=1400  -> primary sigma ~0.003% (functional-form benchmark).
  Theoretical arm: derived renorm_K + URC -> primary sigma ~0.29% (Table theoretical path).
  Writes dual_path_comparison.json (includes coeff target table; not a bare-kernel mass run).

--run-fully-theoretical
  Bare Elegant Kernel: THEORETICAL_COEFF_VECTOR + calculate_theoretical_E_base().
  Use with --coeffs-source limit (or theoretical/elegant). Primary sigma ~1.1%.
  Demonstrates empirical UCL converging to kernel targets; NOT the 0.293% headline.

--coeffs-source empirical|limit|theoretical|elegant
  empirical = UCL2.3 fit (default). limit* = Elegant Kernel algebraic vector.

--imt-mixer-mode v12|cmca
  v12 = embedded Phase/Binding (default). cmca = structural CMCA two-anchor mixer.

--write-help-md
  Write HELP.md (this summary + command examples) next to the script.

See UGP_GTE_SM_Verifier/README.md and papers/01_SM/REPRODUCE.md.

