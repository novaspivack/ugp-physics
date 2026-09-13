# Verifier companion archive — Standard Model from UGP

This folder holds reproducible JSON traces referenced by the manuscript `standard_model_from_ugp.tex`.

## `cosmological_lambda_L_model_trace.json`

Canonical numerical trace for **Theorem (Cosmological Constant)** (paper §9; LaTeX label `eq:lambda`) with
$\Lambda = (\ln 2/\pi)\,L_{\mathrm{model}}\,(H_0^2/c^2)$:

- **$L_{\mathrm{model}}$** is computed as $\log_2\bigl((2^4\cdot 5^3)/3\bigr)$ (not hardcoded).
- **$\Lambda_{\mathrm{pred}}$** uses $\Lambda = (\ln 2/\pi)\,L_{\mathrm{model}}\,(H_0^2/c^2)$ with the same SI conventions as `frw_psi_scan.py` ($H_0 = 70\,\mathrm{km\,s^{-1}\,Mpc^{-1}}$ baseline).
- **$\Lambda_{\mathrm{obs}}$** is the CODATA 2018 target $1.1056\times 10^{-52}\,\mathrm{m}^{-2}$ used across the TE\_1 validation program.

Discrete-token verification of $L_{\mathrm{model}}$ (wedge factors and $S_3$ quotient) lives in:

`ugp_discovery_lab/results/lambda_normalization_proof.json` (paths relative to the repository root)

## `te1e_frw_validation_run_20251110_230054_summary.json`

Copy of the TE\_1.E\_Lambda FRW+$\Psi$ pipeline run (`run_20251110_230054`). It checks dynamical consistency (CPL $w_0\approx -1$, linear $\langle\Omega\rangle$–$\Lambda$ response) against the same $\Lambda_{\mathrm{obs}}$ target. **It does not compute $L_{\mathrm{model}}$**; keep it separate from the information-theoretic trace above.
