# Canonical hashes — P01 verifier bundle (2026-05-30)

Frozen after `k_gen = φ cos(π/10)` alignment in `UGP_GTE_SM_Verifier.py` and `comp_p01_ucl_coeff_audit.py`.

## Verifier identity (default path: empirical UCL + v12 mixer)

| Field | Value |
|-------|--------|
| `version` | `2.0.0-v7-DUAL-PATH` |
| `coeffs_sha256` (EMPIRICAL_COEFF_VECTOR) | `132149e9eabcb0643ecd11649e969972f05151f67b3496de60405da73d30c4f6` |
| `triples_sha256` | `f2e113a4b819099a1304d580cb03f89df62de6827d7cc3830184d34836899936` |
| `code_sha256` (verifier source, 2026-05-30) | `fe1897d96dd7129167dd553ec9403fe08adc5d942be332a115f1be231dc2c4db` |

Empirical coefficients unchanged; `code_sha256` updates when verifier source changes (flags, k_gen fix, CMCA hook).

## Reference lock (`reference_lock.json`)

| Field | Value |
|-------|--------|
| `primary_sigma_percent` | `0.0029473871430684808` |
| `w_rho` | `1.0489985693848354` |
| `quarter_lock_residual` | `-1.5047500000031633e-05` |
| `engine` | `phase_mode=legacy`, `phase_k=2.0`, `renorm_K=1400.0` |

Verify: `python3 UGP_GTE_SM_Verifier.py --verify-reference --preset-reference --n 10 --ref-path reference_lock.json`

## UCL audit artifacts (SHA-256 of committed JSON)

| File | SHA-256 |
|------|---------|
| `dual_path_comparison.json` | `6415ad0bd8e6ce74e7521c13c222fb8851f0fd583805b39644b1f6c0f7e310dc` |
| `theoretical_coefficients.json` | `71b1c683b7554698c7c92a5b354c84d484caec9558be278a120e82d98cb54d63` |
| `fully_theoretical_results.json` | `da87115a43fe5f120035ceddb8af719488788039c8adfe58f73b6204a7df0063` |
| `reference_lock.json` | `865f618f28ec1f3d2481635fd13b21a15974b0fc2b335dd04b5679d239dca9e0` |

## Dual-path summary (inside `dual_path_comparison.json`)

| Path | Primary σ |
|------|-----------|
| Empirical (UCL2.3) | **0.00295%** |
| Theoretical (dual-path: empirical UCL + theoretical renorm_K) | **0.295%** |

## Elegant Kernel `k_gen` (inside `theoretical_coefficients.json`)

`1.5388417685876268` = `φ cos(π/10)` (Lean: `thm_ucl2_fully_unconditional`).
