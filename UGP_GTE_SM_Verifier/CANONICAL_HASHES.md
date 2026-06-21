# Canonical hashes — P01 verifier bundle (2026-06-11)

Frozen after the `m_W` PDG 2024 target alignment (80369.2 MeV) and documentation-flag
cleanup in `UGP_GTE_SM_Verifier.py`. Supersedes the 2026-05-30 freeze (`k_gen = φ cos(π/10)`
alignment); all per-particle masses and both primary σ values are unchanged from that freeze.

## Verifier identity (default path: empirical UCL + v12 mixer)

| Field | Value |
|-------|--------|
| `version` | `2.0.0-v7-DUAL-PATH` |
| `coeffs_sha256` (EMPIRICAL_COEFF_VECTOR) | `132149e9eabcb0643ecd11649e969972f05151f67b3496de60405da73d30c4f6` |
| `triples_sha256` | `f2e113a4b819099a1304d580cb03f89df62de6827d7cc3830184d34836899936` |
| `code_sha256` (verifier source, 2026-06-11) | `92eadeaaf214cc9cfca503038d3e33a75a109a48253e397cc45b065fcb8a8ce2` |

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
| `dual_path_comparison.json` | `923366a25cb7d8d083ec27b3ad4e3758f7073971eaabc85e13148a3a3e5d007e` |
| `theoretical_coefficients.json` | `71b1c683b7554698c7c92a5b354c84d484caec9558be278a120e82d98cb54d63` |
| `fully_theoretical_results.json` | `424ac947c7ed7e43490c9faa8722085311503c78cf2ad2aba75e79e663cc0df9` |
| `reference_lock.json` | `b277506a879363aefef09a163a8387169b216fbbdbeaa6d26ba87dc82cb44fae` |

Regenerate with `python3 comp_p01_ucl_coeff_audit.py` (run record:
`Verifier_reports/ucl_coeff_audit_20260611-054600/`).

## Dual-path summary (inside `dual_path_comparison.json`)

| Path | Primary σ |
|------|-----------|
| Empirical (UCL2.3) | **0.00295%** |
| Theoretical (dual-path: empirical UCL + theoretical renorm_K) | **0.295%** |

The theoretical-path primary σ is `0.29528216785481204%` (RMS over the nine charged
fermions plus the W-ρ invariant, PDG 2022 targets); per-particle values are in
`dual_path_comparison.{json,md}` and are reproduced in `tab:theoretical_primary` of the paper.

## Elegant Kernel `k_gen` (inside `theoretical_coefficients.json`)

`1.5388417685876268` = `φ cos(π/10)` (Lean: `thm_ucl2_fully_unconditional`).
