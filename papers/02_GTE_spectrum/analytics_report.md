# Curve Mining Summary (mass < 173.0 GeV)

## Counts by branch and c-state

|                            |   count |
|:---------------------------|--------:|
| ('mirror', 'latched_15')   |  499972 |
| ('mirror', 'transitional') |      14 |
| ('our', 'latched_15')      |  499973 |
| ('our', 'ridge_65535')     |       3 |
| ('our', 'transitional')    |      15 |


## Top Curves with Physics Interpretation

### [1] log10(m) = 2.97885 + 0.000033·k
- family: `line`  
- theta: `(2.9788546329593544, 3.342672503084773e-05)`  
- score: **24.64**, inliers: **7**, SM hits: **7**, BIC: -59.1
- **Physics Classification**: mass_independent_constant (ultra_stable)
- **Significance Score**: 8.5/10
- **SM Enrichment**: 100.0%
- **Stability Enrichment**: 100.0%

### [2] log10(m) = 3.07639
- family: `const`  
- theta: `(3.0763922678688522,)`  
- score: **10.99**, inliers: **6**, SM hits: **6**, BIC: -41.4
- **Physics Classification**: constant_regime (stable)
- **Significance Score**: 7.5/10
- **SM Enrichment**: 100.0%
- **Stability Enrichment**: 100.0%

### [3] log10(m) = 2.97885 + 0.000033·k
- family: `line`  
- theta: `(2.9788546329593544, 3.342672503084773e-05)`  
- score: **3.58**, inliers: **7**, SM hits: **7**, BIC: -59.1
- **Physics Classification**: mass_independent_constant (ultra_stable)
- **Significance Score**: 8.5/10
- **SM Enrichment**: 100.0%
- **Stability Enrichment**: 100.0%

### [4] log10(m) = 3.84217 + 0.000001·k
- family: `line`  
- theta: `(3.8421702164702793, 1.0039071435817744e-06)`  
- score: **16561.36**, inliers: **16561**, SM hits: **0**, BIC: -111466.6
- **Physics Classification**: mass_independent_constant (ultra_stable)
- **Significance Score**: 7.0/10
- **SM Enrichment**: 0.0%
- **Stability Enrichment**: 0.0%
- **Oscillatory (fast FFT check)**: period ≈ 16561.0 steps
- **Per-curve oscillation (strict)**: P≈16560.00, z≈144.90, n=16561
- **Per-curve CV RMSE**: 0.0272 (log10 units)

### [5] log10(m) = 3.89256 + 0.000004·(k−52608) + -0.000003·max(0, k−52608)
- family: `hinge_centered`  
- theta: `(3.8925635420918643, 4.012136429103031e-06, -3.1323664550552675e-06, 52608.0)`  
- score: **6479.86**, inliers: **18693**, SM hits: **0**, BIC: -127271.9
- **Physics Classification**: beyond_sm_scale (ultra_stable_plateau)
- **Significance Score**: 8.0/10
- **SM Enrichment**: 0.0%
- **Stability Enrichment**: 0.0%
- **Hinge alignment to 233**: {'k0_mod233_dist': 50.0}
- **Oscillatory (fast FFT check)**: period ≈ 18693.0 steps
- **Per-curve oscillation (strict)**: P≈18692.00, z≈153.95, n=18693
- **Per-curve CV RMSE**: 0.0305 (log10 units)
- **Bootstrap hinges**: {'k0_mean': 147798.28105263156, 'k0_std': 10329.708085562332, 'k0_ci5': 135566.1089473684, 'k0_ci95': 158018.62210526314}

### [6] log10(m) = 0.00000 + -0.000073·(k−52608) + -0.000010·max(0, k−52608) + 0.000084·max(0, k−5398)
- family: `hinge2_centered`  
- theta: `(3.322155024499582e-09, -7.331041653645474e-05, -1.0171216311943012e-05, 52608.0, 8.352852217017027e-05, 5398.0)`  
- score: **5087.06**, inliers: **9294**, SM hits: **0**, BIC: -55763.9
- **Physics Classification**: multi_phase_transition (piecewise_evolving)
- **Significance Score**: 8.5/10
- **SM Enrichment**: 0.0%
- **Stability Enrichment**: 0.0%
- **Hinge alignment to 233**: {'k0_mod233_dist': 50.0, 'k1_mod233_dist': 39.0}
- **Oscillatory (fast FFT check)**: period ≈ 9294.0 steps
- **Per-curve oscillation (strict)**: P≈4646.50, z≈38.76, n=9294
- **Per-curve CV RMSE**: 0.0383 (log10 units)
- **Bootstrap hinges**: {'k0_mean': 29049.19833333334, 'k0_std': 3950.2460235263957, 'k0_ci5': 27390.0, 'k0_ci95': 30095.408333333344, 'k1_mean': 130769.41444444444, 'k1_std': 4632.33407637014, 'k1_ci5': 128072.46277777781, 'k1_ci95': 132466.41611111112}



## Oscillation (strict detrend + AR(1) whiten + block permutation)

- segment (branch=our, c_state=latched_15): P≈499972.00 steps, z≈4707.37, n=499973
- segment (branch=mirror, c_state=latched_15): P≈499971.00 steps, z≈4581.16, n=499972


## Mass–k Sector Summary

| sector | n_curves | median BIC | median CV RMSE (log m) |
|---|---:|---:|---:|
| composite | 3 | -59.1 | nan |
| fermion | 3 | -111466.6 | 0.0305 |

## Mass–k Meta-Law (linear diagnostic)
- BIC (pooled linear): -2781776.8
- BIC (sector-interact linear): -2781824.1
- Verdict: **sector_interact** (diagnostic only)


## Lifetime–Mass (mode=auto)

### Top curves

- [1] log10(τ) = 30.00000  
  family: `const`, inliers: **999973**, SM hits: **8**, score: 1003972.85

- [2] log10(τ) = 30.00000  
  family: `const`, inliers: **999973**, SM hits: **8**, score: 250994.30

- [3] log10(τ) = 30.00000  
  family: `const`, inliers: **999973**, SM hits: **8**, score: 100398.59

- **power_law** : log10(τ) = 29.99154 + 0.002051·log10(m)  BIC: -5190207.4, R²: 0.0001
- **broken_power_law** (winner): log10(τ) = 30.00000 + 0.448856·(log10(m)−3.12) + -0.448863·max(0, log10(m)−3.12)  BIC: -5193634.6, R²: 0.0035

- Meta-Law:
  BIC (pooled): -5190207.4, BIC (sector-interactions): -5234945.8
  CV RMSE (pooled): 0.0576, CV RMSE (sector-interactions): 0.0613
  Verdict: **sector_interact**

## Multivariate Surfaces (low-rank)

### Mass surface (k, I_c15, I_our)

- log10(m)=A + B·k + C·I_c15 + D·I_our + E·max(0,k−100011)  
  BIC: -2862755.2, R²: 0.3341

### Lifetime surface (log10 m, I_c15, I_our)

- log10(τ)=A + B·log10(m) + C·I_c15 + D·I_our + E·max(0,log10(m)−3.81)  
  BIC: -5274531.4, R²: 0.0810


## Interpretation (conditional)

- Catalog size: 999977; Green: 19900 (2.0%); Blue: 40003 (4.0%)
- Shared hinge slopes (median): B≈4.012e-06, D≈-3.132e-06; IQR ranges suggest tight slope concentration.
- Hinges align near even-step harmonics: median distance to harmonic ≈ 50.0 k-units.
- Significant oscillations in mass–k (FDR q<0.05): 2 segments; strongest period ~ 499972 steps.
- Mass surface (k, c-state, branch) explains R²≈0.334 with hinge at k≈100011.
- Lifetime surface (log m, c-state, branch) explains R²≈0.081 with hinge at log m≈3.810071489436947.
- Greens concentrate near k≈12072 vs catalog mean k≈250007, suggesting selective sub-trajectories within the ladder.
- Blues show mean log mass≈3.52 vs catalog mean≈4.05, indicating viable but unstable states occupy a distinct mass band.

**Takeaway.** The laws we recover (hinges at even-step harmonics, broken lifetime power, oscillations with FDR control) are consistent with a deterministic ladder. More importantly, the **stable/viable subsets** occupy specific sub-trajectories and bands, which can be formulated as falsifiable hypotheses about where stability emerges (in k and log m). These are lateral insights beyond generation rules: they prioritize which GTE sub-trajectories are **significant**, and offer concrete targets for physics proofs or empirical checks.
