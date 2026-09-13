# hypercharge_model_optimizer_summary

*Generated: 2025-09-18T02:03:47.163224*

# Hypercharge Model Optimizer — Summary

- **Total Tasks:** 1
- **Successful Tasks:** 1
- **Success Rate:** 100.0%
- **Status:** Completed

## Optimization Results
- **Final Error:** 1.8149%
- **Optimization Success:** True
- **Iterations:** 3

## Optimized Parameters
- **g_factor:** 0.100000
- **c_state_latched_15_offset:** 0.166667
- **a_parity_factor:** -0.000655
- **b_parity_factor:** -0.000018
- **c_parity_factor:** 0.000044
- **k_index_factor:** -0.100000

## Data Processing
- **Particle Count:** 399,977

## Interpretation

This optimization refines the hypercharge assignment model by:
- **Including additional GTE properties** (a, b, c parities, k-index)
- **Minimizing the RG running error** as the fitness function
- **Using L-BFGS-B optimization** for parameter tuning

The optimized model should provide better hypercharge assignments
that lead to more accurate RG running predictions.