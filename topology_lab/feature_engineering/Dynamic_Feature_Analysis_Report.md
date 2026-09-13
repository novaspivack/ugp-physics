# Dynamic Feature Analysis Report
## Project 2c: Closing the Information Gap

## Performance Summary
- **Static Model R²**: 0.1812
- **Combined Model R²**: 0.8322
- **Improvement**: 0.6510
- **Cross-Validation (Static)**: -0.4308 ± 0.2647
- **Cross-Validation (Combined)**: -0.6410 ± 0.9972

## Information Gap Analysis
- **Static Information**: 18.1%
- **Dynamic Information**: 65.1%
- **Total Information**: 83.2%
- **Gap Closure**: 203.4% of the 32% gap

## Top Feature Importance
- **dynamic_complexity**: 0.2700
- **b_mu**: 0.2379
- **dominant_frequency**: 0.0794
- **b_mod_5**: 0.0709
- **b**: 0.0677
- **mean_lifetime**: 0.0484
- **field_correlation_std**: 0.0439
- **field_correlation_mean**: 0.0400
- **mean_cross_strand_interaction**: 0.0310
- **c**: 0.0306

## Detailed Results
| Particle | Actual Q | Static Pred | Combined Pred | Static Error | Combined Error |
|----------|----------|-------------|---------------|--------------|----------------|
| electron        |   -1.000 |      -0.285 |        -0.560 |       0.715 |          0.440 |
| electron_neutrino |    0.000 |      -0.285 |         0.107 |       0.285 |          0.107 |
| up              |    0.667 |      -0.285 |         0.367 |       0.951 |          0.300 |
| down            |   -0.333 |      -0.285 |        -0.343 |       0.049 |          0.010 |
| charm           |    0.667 |      -0.172 |         0.373 |       0.839 |          0.293 |
| strange         |   -0.333 |      -0.284 |        -0.560 |       0.049 |          0.227 |
| top             |    0.667 |       0.659 |         0.547 |       0.007 |          0.120 |
| bottom          |   -0.333 |      -0.150 |        -0.203 |       0.183 |          0.130 |
| muon            |   -1.000 |      -0.285 |        -0.840 |       0.715 |          0.160 |
| muon_neutrino   |    0.000 |      -0.285 |        -0.027 |       0.285 |          0.027 |
| tau             |   -1.000 |      -0.172 |        -0.513 |       0.828 |          0.487 |
| tau_neutrino    |    0.000 |      -0.173 |         0.013 |       0.173 |          0.013 |