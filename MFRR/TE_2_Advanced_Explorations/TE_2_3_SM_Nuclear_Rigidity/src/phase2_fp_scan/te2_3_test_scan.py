#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TE_2.3 Phase 2: Test Fixed Point Scanner

Quick test to understand why no fixed points are being found.
"""

import numpy as np
import jax.numpy as jnp
from scipy.optimize import minimize
import sys
from pathlib import Path

# Import from Phase 1
sys.path.append(str(Path(__file__).parent.parent / "phase1_hessian"))
from te2_3_theory_space import TheorySpace, TheorySpaceConfig
from te2_3_hessian import LyapunovFunctional, HessianConfig

# Initialize
theory_config = TheorySpaceConfig(
    use_running_couplings=True,
    include_yukawa=True,
    gauge_normalization="canonical",
    higgs_parameterization="physical",
)

theory_space = TheorySpace(theory_config)
sm_fp = theory_space.get_sm_fixed_point()

hessian_config = HessianConfig(
    w_mdl=1.0,
    w_psc=10.0,
    w_rg=1.0,
    use_jax=True,
)

lyapunov = LyapunovFunctional(theory_space, hessian_config)

# Test 1: Evaluate at SM
k_sm = sm_fp.k
C_sm = lyapunov(jnp.array(k_sm))
print(f"\n[Test 1] Functional at SM:")
print(f"  C[k_SM] = {C_sm:.6e}")

# Test 2: Evaluate gradient at SM
from jax import grad
grad_func = grad(lyapunov)
grad_sm = grad_func(jnp.array(k_sm))
grad_norm_sm = float(jnp.linalg.norm(grad_sm))
print(f"\n[Test 2] Gradient at SM:")
print(f"  ||∇C||_{'{k_SM}'} = {grad_norm_sm:.6e}")

# Test 3: Try optimization from SM
print(f"\n[Test 3] Optimize from SM (should stay at SM if it's a fixed point):")

def objective(k):
    return float(lyapunov(jnp.array(k)))

def gradient(k):
    return np.array(grad_func(jnp.array(k)))

# Bounds
lower = k_sm * 0.5
upper = k_sm * 1.5
lower = np.maximum(lower, 1e-6)
bounds = list(zip(lower, upper))

result = minimize(
    objective,
    k_sm,
    method='L-BFGS-B',
    jac=gradient,
    bounds=bounds,
    options={'maxiter': 1000, 'ftol': 1e-10}
)

print(f"  Success: {result.success}")
print(f"  Iterations: {result.nit}")
print(f"  Final C: {result.fun:.6e}")
print(f"  Final ||∇C||: {np.linalg.norm(gradient(result.x)):.6e}")
print(f"  Distance from SM: {np.linalg.norm(result.x - k_sm):.6e}")

# Test 4: Try optimization from perturbed SM
print(f"\n[Test 4] Optimize from perturbed SM (+10%):")

k_perturbed = k_sm * 1.1

result2 = minimize(
    objective,
    k_perturbed,
    method='L-BFGS-B',
    jac=gradient,
    bounds=bounds,
    options={'maxiter': 1000, 'ftol': 1e-10}
)

print(f"  Success: {result2.success}")
print(f"  Iterations: {result2.nit}")
print(f"  Final C: {result2.fun:.6e}")
print(f"  Final ||∇C||: {np.linalg.norm(gradient(result2.x)):.6e}")
print(f"  Distance from SM: {np.linalg.norm(result2.x - k_sm):.6e}")

# Test 5: Check if optimizer converges to SM
print(f"\n[Test 5] Does optimizer converge to SM?")
if np.linalg.norm(result2.x - k_sm) < 0.1:
    print(f"  ✓ YES - Converged to within 10% of SM")
else:
    print(f"  ✗ NO - Converged to different point")
    print(f"  Final point / SM:")
    for i, label in enumerate(sm_fp.labels):
        print(f"    {label}: {result2.x[i]:.6e} / {k_sm[i]:.6e} (ratio: {result2.x[i]/k_sm[i]:.3f})")

# Test 6: What is the minimum functional value we can find?
print(f"\n[Test 6] Try multiple random starts:")

best_C = float('inf')
best_k = None
best_grad_norm = None

for i in range(10):
    k_random = np.random.uniform(lower, upper)
    
    result_random = minimize(
        objective,
        k_random,
        method='L-BFGS-B',
        jac=gradient,
        bounds=bounds,
        options={'maxiter': 500, 'ftol': 1e-10}
    )
    
    if result_random.success and result_random.fun < best_C:
        best_C = result_random.fun
        best_k = result_random.x
        best_grad_norm = np.linalg.norm(gradient(best_k))

print(f"  Best C found: {best_C:.6e}")
print(f"  Best ||∇C||: {best_grad_norm:.6e}")
print(f"  Distance from SM: {np.linalg.norm(best_k - k_sm):.6e}")

# Conclusion
print(f"\n[Conclusion]")
print(f"  C[k_SM] = {C_sm:.6e}")
print(f"  ||∇C||_{'{k_SM}'} = {grad_norm_sm:.6e}")
print(f"  Best C found = {best_C:.6e}")
print(f"  Best ||∇C|| = {best_grad_norm:.6e}")

if best_C < C_sm:
    print(f"  ⚠ Found point with C < C[k_SM]!")
    print(f"  This suggests SM is NOT a global minimum of this functional.")
else:
    print(f"  ✓ SM has lowest C value found.")

if grad_norm_sm > 1e-3:
    print(f"  ⚠ Gradient at SM is large (> 10^-3)")
    print(f"  SM is NOT a true fixed point of this functional.")
    print(f"  This is expected for a proxy functional.")
else:
    print(f"  ✓ Gradient at SM is small")

