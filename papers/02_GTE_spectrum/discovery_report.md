# Particle Discovery Run Report
**Run UUID:** `afcaab68-454c-421b-a800-e7842f0750f9`
## Run Summary
- **Total Particles Analyzed:** 1,000,079
- **High-Confidence Candidates:** 60,033 (6.0%)
  - **Green Light Candidates:** 20,001
  - **Blue Light Candidates:** 40,003
  - **Canonical SM Particles Identified:** 29

## Theory-Guided Discovery Parameters

This discovery run uses a theory-guided filtering system that ensures only physically viable particles are reported. The color hierarchy represents experimental viability within theory-valid particles:

### Theory-Guided Thresholds
- **Minimum Theory Confidence:** 70% (all discoveries)
- **Minimum GTE Score:** 60% (all discoveries)
- **Minimum Viability Score:** 30% (all discoveries)

### Log-Scale Experimental Prioritization (Theory-Valid Particles Only)
- **🟢 Green:** 23.5%+ viability (top 2% - best experimental targets)
- **🔵 Blue:** 21.9%-23.5% viability (next 4% - high priority)
- **🟣 Purple:** 20.0%-21.9% viability (next 8% - medium priority)
- **🟠 Orange:** 17.7%-20.0% viability (next 16% - low priority)
- **🔴 Red:** <17.7% viability (bottom 70% - very low priority)
- **🟣 Purple (filtered):** Below theory thresholds (filtered out)


## Calibration Validation Summary

| Metric | Value | Status |
|--------|-------|--------|
| **Overall RMSE (log)** | 0.0008 | ✅ |
| **Overall MAE (log)** | 0.0003 | ✅ |
| **Overall MAPE (%)** | 0.07% | ✅ |
| **Top Quark Hold-out Test** | 0.00% error | ✅ PASS |
| **Monotonicity Check** | 1.0000 | ✅ PASS |

### Sector-wise Performance

| Sector | Particles | RMSE (log) | MAE (log) | MAPE (%) |
|--------|-----------|------------|-----------|----------|
| Leptons | 3 | 0.0000 | 0.0000 | 0.00% |
| Up Quarks | 3 | 0.0010 | 0.0006 | 0.13% |
| Down Quarks | 3 | 0.0011 | 0.0006 | 0.14% |

## 🔬 Calibration & Diagnostics Report
**Calibration Status:** Fitted
**Training Samples:** 9 (SM Particles)

**Methodology:** A high-precision calibration model was fitted to the Standard Model particles. Only new particle candidates whose raw parameters fall within the energy range bracketed by the SM are considered high-confidence. All other particles are discarded from the final results for scientific rigor.

### High-Confidence Zone (Interpolation)
- **Model:** Cubic Spline
- **Applicable Range (Raw GTE Mass):** 0.51 MeV to 172759.90 MeV
- **Action:** Particles in this zone are calibrated and reported with a search window of +/- 5%.

### Low-Confidence Zone (Extrapolation)
- **Boundary Definition:** A Linear Regression model (`log10(M_cal) = 0.999957721523803 * log10(M_raw) + -0.000303112587236`) was fitted to the SM data to define the high-confidence boundary.
- **Action:** All particles with a raw GTE mass outside the applicable range shown above were discarded and are not included in this report.

### Confidence Statement
**High Precision:** "The reported mass of a hypothetical particle is our best estimate, with a high-confidence search window of approximately +/- 5%. This precision is achieved because the particle's raw parameters place it within the energy regime bracketed by known Standard Model particles (from **0.51 MeV to 172759.90 MeV**), allowing for a high-fidelity spline interpolation."

**High Structural Confidence:** "The existence of these particles in these specific mass regions is a direct consequence of the GTE theory's structure. Their appearance is not random but is predicted by the same mathematical framework that successfully organizes the Standard Model."

**Clear Limitations:** "We are explicitly not reporting on particles outside this high-confidence zone. While the GTE framework does predict particles at higher masses, we currently lack the ground-truth data to calibrate our model with sufficient accuracy in that regime."

## Standard Model Particles Identified

### Candidate: `hypo_electron_neutrino_165cdd42` (Confidence: 1.000)
- **Classification:** Green - *Best experimental target: 100.0% viability (top 2%)*
- **Calibrated Mass:** 0.000 MeV
- **Region of Interest:** 0.000 to 0.000 MeV
- **Calibration Method:** Outside High-Precision Zone (rejected)
### Candidate: `hypo_electron_neutrino_804ad112` (Confidence: 1.000)
- **Classification:** Green - *Best experimental target: 100.0% viability (top 2%)*
- **Calibrated Mass:** 0.000 MeV
- **Region of Interest:** 0.000 to 0.000 MeV
- **Calibration Method:** Outside High-Precision Zone (rejected)
### Candidate: `hypo_electron_neutrino_73ec56e6` (Confidence: 1.000)
- **Classification:** Green - *Best experimental target: 100.0% viability (top 2%)*
- **Calibrated Mass:** 0.000 MeV
- **Region of Interest:** 0.000 to 0.000 MeV
- **Calibration Method:** Outside High-Precision Zone (rejected)
### Candidate: `particle_electron` (Confidence: 0.983)
- **Classification:** Green - *Best experimental target: 100.0% viability (top 2%)*
- **Calibrated Mass:** 0.511 MeV
- **Region of Interest:** 0.507 to 0.515 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `particle_up` (Confidence: 0.983)
- **Classification:** Green - *Best experimental target: 100.0% viability (top 2%)*
- **Calibrated Mass:** 2.160 MeV
- **Region of Interest:** 2.142 to 2.178 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `particle_down` (Confidence: 0.983)
- **Classification:** Green - *Best experimental target: 100.0% viability (top 2%)*
- **Calibrated Mass:** 4.670 MeV
- **Region of Interest:** 4.632 to 4.708 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `particle_proton` (Confidence: 0.983)
- **Classification:** Green - *Best experimental target: 100.0% viability (top 2%)*
- **Calibrated Mass:** 933.923 MeV
- **Region of Interest:** 926.336 to 941.509 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `particle_neutron` (Confidence: 0.983)
- **Classification:** Green - *Best experimental target: 100.0% viability (top 2%)*
- **Calibrated Mass:** 935.208 MeV
- **Region of Interest:** 927.611 to 942.804 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `particle_lambda` (Confidence: 0.983)
- **Classification:** Green - *Best experimental target: 100.0% viability (top 2%)*
- **Calibrated Mass:** 1110.605 MeV
- **Region of Interest:** 1101.584 to 1119.626 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `particle_sigma_plus` (Confidence: 0.983)
- **Classification:** Green - *Best experimental target: 100.0% viability (top 2%)*
- **Calibrated Mass:** 1184.236 MeV
- **Region of Interest:** 1174.617 to 1193.855 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `particle_sigma_zero` (Confidence: 0.983)
- **Classification:** Green - *Best experimental target: 100.0% viability (top 2%)*
- **Calibrated Mass:** 1187.509 MeV
- **Region of Interest:** 1177.863 to 1197.155 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `particle_sigma_minus` (Confidence: 0.983)
- **Classification:** Green - *Best experimental target: 100.0% viability (top 2%)*
- **Calibrated Mass:** 1192.318 MeV
- **Region of Interest:** 1182.633 to 1202.003 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `particle_xi_zero` (Confidence: 0.983)
- **Classification:** Green - *Best experimental target: 100.0% viability (top 2%)*
- **Calibrated Mass:** 1310.031 MeV
- **Region of Interest:** 1299.390 to 1320.672 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `particle_xi_minus` (Confidence: 0.983)
- **Classification:** Green - *Best experimental target: 100.0% viability (top 2%)*
- **Calibrated Mass:** 1316.921 MeV
- **Region of Interest:** 1306.224 to 1327.618 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `particle_omega_minus` (Confidence: 0.983)
- **Classification:** Green - *Best experimental target: 100.0% viability (top 2%)*
- **Calibrated Mass:** 1671.519 MeV
- **Region of Interest:** 1657.942 to 1685.097 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `particle_W_boson` (Confidence: 0.983)
- **Classification:** Green - *Best experimental target: 100.0% viability (top 2%)*
- **Calibrated Mass:** 80379.031 MeV
- **Region of Interest:** 79726.124 to 81031.937 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `particle_Z_boson` (Confidence: 0.983)
- **Classification:** Green - *Best experimental target: 100.0% viability (top 2%)*
- **Calibrated Mass:** 91187.637 MeV
- **Region of Interest:** 90446.934 to 91928.340 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `particle_Higgs_boson` (Confidence: 0.983)
- **Classification:** Green - *Best experimental target: 100.0% viability (top 2%)*
- **Calibrated Mass:** 125090.060 MeV
- **Region of Interest:** 124073.973 to 126106.147 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `particle_top` (Confidence: 0.977)
- **Classification:** Green - *Best experimental target: 100.0% viability (top 2%)*
- **Calibrated Mass:** 172760.000 MeV
- **Region of Interest:** 171356.697 to 174163.303 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `particle_strange` (Confidence: 0.899)
- **Classification:** Green - *Best experimental target: 100.0% viability (top 2%)*
- **Calibrated Mass:** 93.000 MeV
- **Region of Interest:** 92.245 to 93.755 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `particle_tau` (Confidence: 0.878)
- **Classification:** Green - *Best experimental target: 100.0% viability (top 2%)*
- **Calibrated Mass:** 1776.860 MeV
- **Region of Interest:** 1762.427 to 1791.293 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `particle_bottom` (Confidence: 0.775)
- **Classification:** Green - *Best experimental target: 100.0% viability (top 2%)*
- **Calibrated Mass:** 4180.000 MeV
- **Region of Interest:** 4146.047 to 4213.953 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `particle_charm` (Confidence: 0.757)
- **Classification:** Green - *Best experimental target: 100.0% viability (top 2%)*
- **Calibrated Mass:** 1270.000 MeV
- **Region of Interest:** 1259.684 to 1280.316 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `particle_muon` (Confidence: 0.742)
- **Classification:** Green - *Best experimental target: 100.0% viability (top 2%)*
- **Calibrated Mass:** 105.658 MeV
- **Region of Interest:** 104.800 to 106.517 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `particle_electron_neutrino` (Confidence: 0.550)
- **Classification:** Green - *Best experimental target: 100.0% viability (top 2%)*
- **Calibrated Mass:** nan MeV
- **Region of Interest:** 0.000 to 0.000 MeV
- **Calibration Method:** Rejected - No Raw Mass
### Candidate: `particle_muon_neutrino` (Confidence: 0.550)
- **Classification:** Green - *Best experimental target: 100.0% viability (top 2%)*
- **Calibrated Mass:** nan MeV
- **Region of Interest:** 0.000 to 0.000 MeV
- **Calibration Method:** Rejected - No Raw Mass
### Candidate: `particle_tau_neutrino` (Confidence: 0.550)
- **Classification:** Green - *Best experimental target: 100.0% viability (top 2%)*
- **Calibrated Mass:** nan MeV
- **Region of Interest:** 0.000 to 0.000 MeV
- **Calibration Method:** Rejected - No Raw Mass
### Candidate: `particle_photon` (Confidence: 0.550)
- **Classification:** Green - *Best experimental target: 100.0% viability (top 2%)*
- **Calibrated Mass:** nan MeV
- **Region of Interest:** 0.000 to 0.000 MeV
- **Calibration Method:** Massless (no calibration)
### Candidate: `particle_gluon` (Confidence: 0.550)
- **Classification:** Green - *Best experimental target: 100.0% viability (top 2%)*
- **Calibrated Mass:** nan MeV
- **Region of Interest:** 0.000 to 0.000 MeV
- **Calibration Method:** Massless (no calibration)

## Top 50 High-Confidence Hypothetical Candidates

### Candidate: `hypo_ugp_n10_our_branch_g23_8357f437` (Confidence: 0.860)
- **Classification:** Green - *Best experimental target: 46.0% viability (top 2%)*
- **Calibrated Mass:** 2.973 MeV
- **Region of Interest:** 2.949 to 2.997 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_our_branch_g31_608e4504` (Confidence: 0.860)
- **Classification:** Green - *Best experimental target: 46.0% viability (top 2%)*
- **Calibrated Mass:** 18.528 MeV
- **Region of Interest:** 18.377 to 18.678 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_our_branch_g25_28e35f49` (Confidence: 0.860)
- **Classification:** Green - *Best experimental target: 46.0% viability (top 2%)*
- **Calibrated Mass:** 18.730 MeV
- **Region of Interest:** 18.578 to 18.882 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_our_branch_g1_aa04737e` (Confidence: 0.860)
- **Classification:** Green - *Best experimental target: 46.0% viability (top 2%)*
- **Calibrated Mass:** 20.975 MeV
- **Region of Interest:** 20.805 to 21.146 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_mirror_branch_g32_69aa75d1` (Confidence: 0.859)
- **Classification:** Green - *Best experimental target: 45.9% viability (top 2%)*
- **Calibrated Mass:** 27.483 MeV
- **Region of Interest:** 27.260 to 27.706 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_mirror_branch_g28_11bc4d38` (Confidence: 0.859)
- **Classification:** Green - *Best experimental target: 45.9% viability (top 2%)*
- **Calibrated Mass:** 27.535 MeV
- **Region of Interest:** 27.311 to 27.759 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_our_branch_g24_52975419` (Confidence: 0.859)
- **Classification:** Green - *Best experimental target: 45.9% viability (top 2%)*
- **Calibrated Mass:** 29.457 MeV
- **Region of Interest:** 29.218 to 29.696 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_our_branch_g29_816a18de` (Confidence: 0.859)
- **Classification:** Green - *Best experimental target: 45.9% viability (top 2%)*
- **Calibrated Mass:** 30.895 MeV
- **Region of Interest:** 30.644 to 31.146 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_our_branch_g26_2f205887` (Confidence: 0.859)
- **Classification:** Green - *Best experimental target: 45.9% viability (top 2%)*
- **Calibrated Mass:** 33.027 MeV
- **Region of Interest:** 32.759 to 33.296 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_our_branch_g22_d4144b0e` (Confidence: 0.859)
- **Classification:** Green - *Best experimental target: 45.8% viability (top 2%)*
- **Calibrated Mass:** 107.410 MeV
- **Region of Interest:** 106.537 to 108.282 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_our_branch_g30_3bb74d04` (Confidence: 0.859)
- **Classification:** Green - *Best experimental target: 45.8% viability (top 2%)*
- **Calibrated Mass:** 109.927 MeV
- **Region of Interest:** 109.034 to 110.820 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_mirror_branch_g30_1c41a32f` (Confidence: 0.859)
- **Classification:** Green - *Best experimental target: 45.8% viability (top 2%)*
- **Calibrated Mass:** 124.863 MeV
- **Region of Interest:** 123.849 to 125.878 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_mirror_branch_g26_eae3316e` (Confidence: 0.859)
- **Classification:** Green - *Best experimental target: 45.7% viability (top 2%)*
- **Calibrated Mass:** 127.072 MeV
- **Region of Interest:** 126.040 to 128.104 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_mirror_branch_g24_a0507522` (Confidence: 0.859)
- **Classification:** Green - *Best experimental target: 45.7% viability (top 2%)*
- **Calibrated Mass:** 128.203 MeV
- **Region of Interest:** 127.161 to 129.244 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_our_branch_g2_d0f04d1d` (Confidence: 0.859)
- **Classification:** Green - *Best experimental target: 45.7% viability (top 2%)*
- **Calibrated Mass:** 136.967 MeV
- **Region of Interest:** 135.854 to 138.080 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_mirror_branch_g25_aa48a683` (Confidence: 0.859)
- **Classification:** Green - *Best experimental target: 45.6% viability (top 2%)*
- **Calibrated Mass:** 211.940 MeV
- **Region of Interest:** 210.219 to 213.662 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_our_branch_g27_f67771db` (Confidence: 0.858)
- **Classification:** Green - *Best experimental target: 45.4% viability (top 2%)*
- **Calibrated Mass:** 297.966 MeV
- **Region of Interest:** 295.546 to 300.386 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_mirror_branch_g27_89a627b9` (Confidence: 0.858)
- **Classification:** Green - *Best experimental target: 45.4% viability (top 2%)*
- **Calibrated Mass:** 299.335 MeV
- **Region of Interest:** 296.903 to 301.766 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_our_branch_g33_42fa7bfe` (Confidence: 0.858)
- **Classification:** Green - *Best experimental target: 45.2% viability (top 2%)*
- **Calibrated Mass:** 394.023 MeV
- **Region of Interest:** 390.822 to 397.224 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_our_branch_g37_76be8593` (Confidence: 0.858)
- **Classification:** Green - *Best experimental target: 45.2% viability (top 2%)*
- **Calibrated Mass:** 403.028 MeV
- **Region of Interest:** 399.754 to 406.301 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_our_branch_g38_a1515bc3` (Confidence: 0.858)
- **Classification:** Green - *Best experimental target: 45.2% viability (top 2%)*
- **Calibrated Mass:** 405.171 MeV
- **Region of Interest:** 401.880 to 408.462 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_mirror_branch_g39_978847c3` (Confidence: 0.858)
- **Classification:** Green - *Best experimental target: 45.2% viability (top 2%)*
- **Calibrated Mass:** 407.113 MeV
- **Region of Interest:** 403.806 to 410.420 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_mirror_branch_g41_c234ae4f` (Confidence: 0.858)
- **Classification:** Green - *Best experimental target: 45.2% viability (top 2%)*
- **Calibrated Mass:** 411.215 MeV
- **Region of Interest:** 407.875 to 414.555 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_mirror_branch_g43_98a56816` (Confidence: 0.858)
- **Classification:** Green - *Best experimental target: 45.2% viability (top 2%)*
- **Calibrated Mass:** 415.179 MeV
- **Region of Interest:** 411.806 to 418.551 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_our_branch_g46_1cac189a` (Confidence: 0.858)
- **Classification:** Green - *Best experimental target: 45.2% viability (top 2%)*
- **Calibrated Mass:** 421.033 MeV
- **Region of Interest:** 417.613 to 424.453 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_mirror_branch_g51_c46a906d` (Confidence: 0.858)
- **Classification:** Green - *Best experimental target: 45.2% viability (top 2%)*
- **Calibrated Mass:** 429.857 MeV
- **Region of Interest:** 426.366 to 433.349 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_our_branch_g51_4a0b8bb3` (Confidence: 0.858)
- **Classification:** Green - *Best experimental target: 45.2% viability (top 2%)*
- **Calibrated Mass:** 429.991 MeV
- **Region of Interest:** 426.498 to 433.484 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_our_branch_g54_ece82494` (Confidence: 0.858)
- **Classification:** Green - *Best experimental target: 45.1% viability (top 2%)*
- **Calibrated Mass:** 435.077 MeV
- **Region of Interest:** 431.543 to 438.611 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_mirror_branch_g56_b46245d5` (Confidence: 0.858)
- **Classification:** Green - *Best experimental target: 45.1% viability (top 2%)*
- **Calibrated Mass:** 438.235 MeV
- **Region of Interest:** 434.675 to 441.795 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_mirror_branch_g57_8941f3db` (Confidence: 0.858)
- **Classification:** Green - *Best experimental target: 45.1% viability (top 2%)*
- **Calibrated Mass:** 439.848 MeV
- **Region of Interest:** 436.275 to 443.421 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_our_branch_g59_3f74b37b` (Confidence: 0.858)
- **Classification:** Green - *Best experimental target: 45.1% viability (top 2%)*
- **Calibrated Mass:** 443.137 MeV
- **Region of Interest:** 439.538 to 446.737 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_mirror_branch_g61_e410f503` (Confidence: 0.858)
- **Classification:** Green - *Best experimental target: 45.1% viability (top 2%)*
- **Calibrated Mass:** 446.112 MeV
- **Region of Interest:** 442.488 to 449.735 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_mirror_branch_g63_53aded22` (Confidence: 0.858)
- **Classification:** Green - *Best experimental target: 45.1% viability (top 2%)*
- **Calibrated Mass:** 449.138 MeV
- **Region of Interest:** 445.490 to 452.787 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_our_branch_g63_6efb76ec` (Confidence: 0.858)
- **Classification:** Green - *Best experimental target: 45.1% viability (top 2%)*
- **Calibrated Mass:** 449.254 MeV
- **Region of Interest:** 445.605 to 452.903 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_our_branch_g66_c4b829af` (Confidence: 0.858)
- **Classification:** Green - *Best experimental target: 45.1% viability (top 2%)*
- **Calibrated Mass:** 453.669 MeV
- **Region of Interest:** 449.984 to 457.354 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_mirror_branch_g68_ce5bfc20` (Confidence: 0.858)
- **Classification:** Green - *Best experimental target: 45.1% viability (top 2%)*
- **Calibrated Mass:** 456.427 MeV
- **Region of Interest:** 452.720 to 460.135 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_our_branch_g69_374e6962` (Confidence: 0.858)
- **Classification:** Green - *Best experimental target: 45.1% viability (top 2%)*
- **Calibrated Mass:** 457.949 MeV
- **Region of Interest:** 454.229 to 461.669 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_mirror_branch_g72_c62bfbfb` (Confidence: 0.858)
- **Classification:** Green - *Best experimental target: 45.1% viability (top 2%)*
- **Calibrated Mass:** 461.999 MeV
- **Region of Interest:** 458.246 to 465.752 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_our_branch_g77_23edadcd` (Confidence: 0.857)
- **Classification:** Green - *Best experimental target: 45.1% viability (top 2%)*
- **Calibrated Mass:** 468.776 MeV
- **Region of Interest:** 464.968 to 472.583 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_our_branch_g28_a641c1f5` (Confidence: 0.857)
- **Classification:** Green - *Best experimental target: 45.1% viability (top 2%)*
- **Calibrated Mass:** 470.934 MeV
- **Region of Interest:** 467.109 to 474.759 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_mirror_branch_g79_8959a5e6` (Confidence: 0.857)
- **Classification:** Green - *Best experimental target: 45.1% viability (top 2%)*
- **Calibrated Mass:** 471.263 MeV
- **Region of Interest:** 467.435 to 475.091 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_mirror_branch_g81_14929ebf` (Confidence: 0.857)
- **Classification:** Green - *Best experimental target: 45.1% viability (top 2%)*
- **Calibrated Mass:** 473.807 MeV
- **Region of Interest:** 469.958 to 477.655 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_our_branch_g81_1f5290f4` (Confidence: 0.857)
- **Classification:** Green - *Best experimental target: 45.1% viability (top 2%)*
- **Calibrated Mass:** 473.904 MeV
- **Region of Interest:** 470.055 to 477.753 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_our_branch_g82_98000b9d` (Confidence: 0.857)
- **Classification:** Green - *Best experimental target: 45.1% viability (top 2%)*
- **Calibrated Mass:** 475.159 MeV
- **Region of Interest:** 471.300 to 479.019 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_mirror_branch_g83_6480c0b1` (Confidence: 0.857)
- **Classification:** Green - *Best experimental target: 45.1% viability (top 2%)*
- **Calibrated Mass:** 476.308 MeV
- **Region of Interest:** 472.439 to 480.177 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_our_branch_g83_1d8c3ac6` (Confidence: 0.857)
- **Classification:** Green - *Best experimental target: 45.1% viability (top 2%)*
- **Calibrated Mass:** 476.404 MeV
- **Region of Interest:** 472.534 to 480.274 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_our_branch_g86_e2fa34ad` (Confidence: 0.857)
- **Classification:** Green - *Best experimental target: 45.1% viability (top 2%)*
- **Calibrated Mass:** 480.079 MeV
- **Region of Interest:** 476.179 to 483.978 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_mirror_branch_g87_e20e1dba` (Confidence: 0.857)
- **Classification:** Green - *Best experimental target: 45.0% viability (top 2%)*
- **Calibrated Mass:** 481.192 MeV
- **Region of Interest:** 477.283 to 485.100 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_our_branch_g87_ee3011bd` (Confidence: 0.857)
- **Classification:** Green - *Best experimental target: 45.0% viability (top 2%)*
- **Calibrated Mass:** 481.285 MeV
- **Region of Interest:** 477.375 to 485.194 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV
### Candidate: `hypo_ugp_n10_our_branch_g90_d421b89f` (Confidence: 0.857)
- **Classification:** Green - *Best experimental target: 45.0% viability (top 2%)*
- **Calibrated Mass:** 484.846 MeV
- **Region of Interest:** 480.908 to 488.785 MeV
- **Calibration Method:** PCHIP (monotone) + LOO-CV