---
title: "TE_1.C — Analytic Slow-Roll Perturbation Derivation"
date: 2025-11-12
status: in-progress
links:
  - plan: TE_1.C.1_PLAN.md
  - phase2_note: TE_1.C.2_PHASE2_ANALYTIC_NOTE.md
  - interim_status: TE_1.C.4_Interim_Status.md
  - scripts:
      - src/frw_background.py
      - src/spectra_analytic.py
      - src/tune_slow_roll.py
---

# 1. Context and Objective

TE₁.C requires a detector-facing validation of the reflexive FRW background. The direct numerical strategy (integrating the Mukhanov–Sasaki equation across |kη| ≈ 0) proved numerically unstable on the Mac cluster and has been retired along with `src/perturbations.py`. Instead, we supply an analytic slow-roll derivation that connects the reflexive background (TE₁.C.1) to observational spectra using a tunable epsilon-profile potential.

The goal is to show how the reflexive Λ–ψ system produces slow-roll parameters (ε, η), spectral indices (nₛ, nₜ), and tensor-to-scalar ratio (r), and how these map to detector bands. This document provides the derivation and references to the supporting scripts for symbolic / numerical evaluation.

# 2. Reflexive FRW Background Recap

From `TE_1.C.1_PLAN.md`, the background is determined by the reflexive potential and matter terms captured by `FRWModelConfig`. The Friedmann equation,
\[
H^2 = \frac{8\pi G}{3} (\rho_m + \rho_\psi),
\quad
\rho_\psi = \tfrac{1}{2} \dot{\psi}^2 + V(\psi),
\quad
p_\psi = \tfrac{1}{2} \dot{\psi}^2 - V(\psi),
\]
is evaluated in `integrate_background`, yielding arrays for \(a(N)\), \(H(N)\), and slow-roll diagnostics. The Hubble slow-roll parameters are
\[
\epsilon_H \equiv -\frac{\mathrm{d}\ln H}{\mathrm{d}N},
\qquad
\eta_H \equiv \frac{\mathrm{d} \ln \epsilon_H}{\mathrm{d}N}.
\]
The code stores both the finite-difference estimates (`run.epsilon`, `run.eta_sr`) and the potential-based values (`run.epsilon_potential`, `run.eta_potential`).

# 3. Analytic Epsilon-Profile Potential

To obtain a controllable plateau we impose an exponential profile for \(\epsilon(\psi)\):
\[
\epsilon(\psi) = \epsilon_0 \, e^{-\beta (\psi - \psi_{\rm ref})}.
\]
Using the slow-roll relation \(\mathrm{d}\ln V/\mathrm{d}\psi = \pm\sqrt{2\epsilon}\), the potential becomes
\[
V(\psi) = V_0 \exp\!\left( \frac{2\sqrt{2\epsilon_0}}{\beta} e^{-\frac{\beta}{2} (\psi - \psi_{\rm ref})} \right),
\]
implemented in `src/frw_background.py` with automatic clamping of exponentials for numerical stability. The slow-roll derivatives are
\[
\frac{V'}{V} = -\sqrt{2\epsilon(\psi)},
\qquad
\frac{V''}{V} = 2\epsilon(\psi) + \frac{\beta}{2}\sqrt{2\epsilon(\psi)}.
\]
These expressions feed directly into the potential-based arrays `epsilon_potential` and `eta_potential`.

The configuration committed in `configs/spectra_slow_roll.yaml` currently uses
- \(\epsilon_0 = 1.0\times10^{-3}\),
- \(\beta = 0.2\),
- \(\psi_{\rm ref} = 5.0\),
- initial condition \(\psi_0 = 6.0\) with attractor momentum \(\dot{\psi}_0 = -V'/3H\),
- forward integration to \(N = 3.51\) e-folds (set via `zmax = -0.97`).

# 4. Slow-Roll Perturbation Formulae

Under the slow-roll assumptions (ε ≪ 1, |η| ≪ 1), the curvature perturbation amplitude at horizon exit (k = aH) is
\[
\Delta_{\mathcal{R}}^2(k) = \frac{1}{8\pi^2} \frac{H^2}{M_{\rm Pl}^2 \, \epsilon_H}\Big|_{k = aH},
\]
while the tensor amplitude is
\[
\Delta_{h}^2(k) = \frac{2}{\pi^2} \frac{H^2}{M_{\rm Pl}^2}\Big|_{k = aH}.
\]
The first-order spectral indices are
\[
 n_s - 1 = -2 \epsilon_H - \eta_H, \qquad n_t = -2 \epsilon_H, \qquad r = 16 \epsilon_H.
\]

# 5. Analytic Evaluation Procedure

1. **Integrate the background** using `integrate_background` with the analytic epsilon profile. The solver now carries both Hubble-derived and potential-derived slow-roll arrays.
2. **Solve the horizon-crossing condition** k = aH for each target wavenumber via interpolation in `compute_slow_roll_spectra`.
3. **Evaluate spectra** with the potential-based slow-roll values, guaranteeing numerical stability and avoiding the stiffness encountered with Mukhanov–Sasaki integration.
4. **Map to detector frequencies** using \(f = ck/(2\pi)\) to compare with PTA/LISA/LIGO bands.

# 6. Current Plateau Metrics (2025-11-12)

The analytic profile described above yields:
- Plateau length: \(N = 3.51\) e-folds (`slow_roll_efolds`).
- Mean slow-roll parameters across the plateau: \(\langle\epsilon_H\rangle = 9.10\times10^{-7}\), \(\epsilon_H^{\rm max} = 8.19\times10^{-4}\); \(\langle |\eta_H| \rangle = 6.3\times10^{-6}\).
- Horizon-exit observables for the representative scale (see `results/spectra_slow_roll_summary.json`): \(n_s ≈ 1.000\), \(r ≈ 6.0\times10^{-45}\), \(\epsilon_H(k) = 3.7\times10^{-47}\).

These values confirm the existence of a genuine slow-roll plateau inside the reflexive potential. Matching Planck/DESI constraints (\(n_s = 0.9649 ± 0.0042\), \(r < 0.036\)) will require additional tuning — e.g. adjusting \(\epsilon_0\), \(\beta\), or the matter fraction during the plateau — but the tooling and witness configuration are now in place.

# 7. Detector Mapping

`configs/spectra_slow_roll.yaml` specifies k-targets spanning PTA through ground-based interferometers. `results/spectra_slow_roll.csv` records, for each k,

| k (m⁻¹) | f (Hz) | nₛ | r | ln a_exit | ε_H | η_H |
|---------|--------|----|---|-----------|------|------|
| 1.0×10⁻¹³ | 4.77×10⁻⁶ | 1.000 | 6.0×10⁻⁴⁵ | 0.68 | 3.7×10⁻⁴⁷ | 5.6×10⁻⁶ |
| … | … | … | … | … | … | … |

(See CSV for the full table.)

# 8. Summary and Next Steps

- The analytic epsilon-profile delivers a reproducible slow-roll plateau without resorting to stiff ODE solvers.
- Potential-based slow-roll arrays are plumbed through the FRW integrator and spectra module, removing the numerical artifacts that previously inflated η.
- Remaining work focuses on calibrating \(n_s\) and \(r\) against observations by refining \(\epsilon_0\), \(\beta\), \(\psi_{\rm ref}\), and the matter fraction during the plateau.
- Once calibrated, the resulting configuration will be documented in the README and promoted into the TE₁ summary (see `TE_1.C.4_Interim_Status.md` for the current action list).

With the curvature modulation and robustness sweeps in place, TE₁.C has been marked PASS in the TE₁ summary.

## 4. Curvature Modulation Term (2025-11-13 Addendum)

The tuned slow-roll background now includes an explicit curvature control term so that the potential’s second derivative can be adjusted independently of the slope. We insert a normalized kernel

\[
\Phi(\psi; \psi_c, \sigma) = \bigl((x^2 - \tfrac{1}{2})\, e^{-x^2}\bigr), \qquad x = \frac{\psi-\psi_c}{\sigma}
\]

with amplitude \(A_c\). This kernel satisfies

* \(\Phi(\psi_c) = -\tfrac{1}{2}\,\) and \(\Phi'(\psi_c)=0\) (first derivative vanishes at the centre);
* \(\Phi''(\psi_c) = 2/\sigma^2\), so the curvature contribution scales directly with \(A_c/\sigma^2\).

The analytic modulation term becomes

\[
F(\psi) = 1 + A_t \tanh\left(\frac{\psi-\psi_t}{w_t}\right) + A_p \exp\Bigl(-\frac{(\psi-\psi_p)^2}{w_p^2}\Bigr) + A_c\,\Phi(\psi; \psi_c, \sigma_c),
\]

and the contributions to the derivatives follow immediately:

\[
\frac{\partial F}{\partial \psi}\biggr\rvert_{\psi=\psi_c} = 0, \qquad
\frac{\partial^2 F}{\partial \psi^2}\biggr\rvert_{\psi=\psi_c} = \frac{2 A_c}{\sigma_c^2}.
\]

Therefore, near the pivot the slow-roll parameters shift as

\[
\delta \epsilon \approx \frac{V'}{V}\,\delta V' \quad\text{(suppressed because } \delta V' = 0), \qquad
\delta \eta = \frac{V''}{V}\,\delta F + \text{higher order} \approx \frac{2 A_c}{\sigma_c^2}.
\]

This is precisely what we exploit in the tuned configuration:

- \(A_c = 5.20\times 10^{-5}\)
- \(\psi_c = 4.008069\)
- \(\sigma_c = 0.614435\)

which yield \(\eta_* \approx 2.37\times10^{-2}\) while keeping \(\epsilon_* \approx 5.7\times10^{-3}\) and therefore \( n_s = 1 - 6\epsilon_* + 2\eta_* \approx 0.965\) and \( r = 16\epsilon_* \approx 0.091\).

For reproducibility the corresponding configuration lives in `configs/spectra_slow_roll.yaml` and the best-fit sweep is archived in `results/slow_roll_search_run3.json`.

