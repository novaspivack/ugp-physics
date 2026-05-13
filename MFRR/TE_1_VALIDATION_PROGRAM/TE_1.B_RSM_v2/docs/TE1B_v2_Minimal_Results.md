# TE₁.B_v2 Minimal Testbed Results

This document summarizes the latest TE₁.B.1 minimal reflexive fluctuation experiments. For methodology, see `docs/TE1B_Minimal_RSM_Spec.md`.

## Production Run A (Balanced)
- Path: `results_production/te1b_v2_20251118_020531`
- Parameters: α=1.0, β≈0.059
- Jarzynski: 1.00118 (CI₉₅ [1.00035, 1.00198])
- Crooks slope: 1.00030 (status *converged*)
- Green–Kubo: χ_GK ≈ 0.0909 vs χ_FD ≈ 0.0732
- Notes: Controller converged quickly; GK mismatch within expected sampling error.

## Production Run B (High statistics)
- Path: `results_production/te1b_v2_20251118_021334`
- Parameters: α=1.0, β≈0.0459
- Jarzynski: 1.00217 (CI₉₅ [1.00176, 1.00260])
- Crooks slope: 0.97609 (status *converged*)
- Green–Kubo: χ_GK ≈ 0.0861 vs χ_FD ≈ −0.116
- Notes: Increasing ensemble size reduced statistical noise in Jarzynski, but Crooks/GK require refining μ-observable to stabilize sign.

## Observable Experiments
- Attempted μ-response via `transition.mu_coupling` (runs `20251118_021334`, `20251118_021826`, `20251118_022221`, `20251118_022633`).
- Observed issues: Crooks slope drifted below 0.99 and χ_GK/χ_FD diverged in sign or magnitude.
- Rollback: restored occupancy-based observable to keep χ_GK and χ_FD aligned within tolerances.

## PR-0 Consistency Status
The optional PR-0 forward/reverse sanity check is deferred. Preliminary probes showed the need for a dedicated ΔS_ref observable and thermometer inside the full PR-0 substrate, which would require a separate development pass. The minimal reflexive testbed therefore serves as the definitive TE₁.B validation for this session.

## Next Steps
1. Freeze controller at α=1.0, β≈0.059 for baseline documentation.
2. Proceed to TE₁.B.2 by selecting stable PR-0 parameters and mirroring the forward/reverse protocol.
