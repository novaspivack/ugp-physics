"""
Test 3.2: D ≈ β_KL D_KL + β_F Fisher Near Equilibrium

OBJECTIVE:
- Run PR-0 to equilibrium θ*
- Sample perturbations around θ*
- For each, measure D(θ), D_KL(p_θ || p_θ*), ||θ - θ*||²_g
- Fit: D = β₀ + β_KL D_KL + β_F Fisher + ε
- Check R² > 0.8

OUTCOME:
- If pass: D approximates Φ, PR-0 implements AG-1
- If fail: D is not the Reflexive Landauer potential
"""

import numpy as np
import sys
from pathlib import Path

_OPTIMIZER_TESTS = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(_OPTIMIZER_TESTS))

from pr0_system.bootstrap.dissonance import SDSBootstrap, compute_ontological_dissonance
from scipy.stats import linregress
import matplotlib.pyplot as plt


def run_to_equilibrium(n_steps=10000):
    """
    Run PR-0 until D stabilizes

    Returns:
        bootstrap: equilibrium system
        theta_star: equilibrium parameters (g, gamma_base, gamma_scale)
        p_star: equilibrium probability distribution |ψ_*|²/Z
    """
    print("Running PR-0 to equilibrium...")

    L_x, L_y = 64, 64
    bootstrap = SDSBootstrap(L_x, L_y)

    # Initialize
    bootstrap.psi = 0.1 * np.exp(1j * 2*np.pi * np.random.rand(L_y, L_x))
    bootstrap.psi[L_y//2, L_x//2] += 1.0

    # Evolve
    for step in range(n_steps):
        bootstrap.step(dt=0.01)
        if step % 1000 == 0:
            D = compute_ontological_dissonance(bootstrap.psi, bootstrap.chi, list(bootstrap.psi_history))
            print(f"  Step {step}: D = {D:.4f}")

    # Extract equilibrium
    theta_star = np.array([bootstrap.g, bootstrap.gamma_base, bootstrap.gamma_scale])
    psi_star = bootstrap.psi.copy()
    p_star = np.abs(psi_star)**2
    Z_star = np.sum(p_star)
    p_star = p_star / Z_star

    print(f"Equilibrium: θ* = {theta_star}")
    print(f"  D* = {compute_ontological_dissonance(bootstrap.psi, bootstrap.chi, list(bootstrap.psi_history)):.4f}")

    return bootstrap, theta_star, p_star, psi_star


def sample_perturbations(theta_star, n_samples=100, perturbation_scale=0.05):
    """
    Generate random perturbations around θ*

    θ_n = θ* + ε_n where ε_n ~ N(0, perturbation_scale²)

    Returns:
        theta_samples: (n_samples, 3) array
    """
    print(f"\nGenerating {n_samples} perturbations...")

    theta_samples = []
    for i in range(n_samples):
        epsilon = np.random.randn(3) * perturbation_scale
        theta_pert = theta_star + epsilon

        # Clamp to valid ranges
        theta_pert[0] = np.clip(theta_pert[0], 0.01, 1.0)  # g
        theta_pert[1] = np.clip(theta_pert[1], 0.001, 0.1)  # gamma_base
        theta_pert[2] = np.clip(theta_pert[2], 0.1, 2.0)  # gamma_scale

        theta_samples.append(theta_pert)

    theta_samples = np.array(theta_samples)
    print(f"  Perturbations in range: Δθ ∈ [{np.min(theta_samples - theta_star, axis=0)}, {np.max(theta_samples - theta_star, axis=0)}]")

    return theta_samples


def compute_D_KL_Fisher_for_perturbations(bootstrap_ref, theta_star, p_star, psi_star, theta_samples):
    """
    For each θ_n, compute:
    - D(θ_n) via ontological dissonance
    - D_KL(p_θ_n || p_θ*) via KL divergence
    - ||θ_n - θ*||²_g via Fisher metric

    Returns:
        D_values: (n_samples,)
        D_KL_values: (n_samples,)
        Fisher_values: (n_samples,)
    """
    print("\nComputing D, D_KL, Fisher for each perturbation...")

    n_samples = len(theta_samples)
    D_values = np.zeros(n_samples)
    D_KL_values = np.zeros(n_samples)
    Fisher_values = np.zeros(n_samples)

    # Compute Fisher metric at θ* (approximation: use identity for now)
    # TODO: actual Fisher metric from ∂_i log p * ∂_j log p
    g_fisher = np.eye(3)  # Placeholder: assume diagonal Fisher metric

    for i, theta in enumerate(theta_samples):
        # Set parameters
        bootstrap_ref.g, bootstrap_ref.gamma_base, bootstrap_ref.gamma_scale = theta

        # Evolve briefly to get p_θ
        for _ in range(100):  # Short evolution
            bootstrap_ref.step(dt=0.01)

        psi_theta = bootstrap_ref.psi.copy()
        p_theta = np.abs(psi_theta)**2
        Z_theta = np.sum(p_theta)
        p_theta = p_theta / (Z_theta + 1e-10)

        # 1. D(θ)
        D_values[i] = compute_ontological_dissonance(psi_theta, bootstrap_ref.chi, list(bootstrap_ref.psi_history))

        # 2. D_KL(p_θ || p_*)
        # D_KL = Σ p_θ log(p_θ / p_*)
        p_theta_safe = np.maximum(p_theta, 1e-10)
        p_star_safe = np.maximum(p_star, 1e-10)
        D_KL_values[i] = np.sum(p_theta_safe * np.log(p_theta_safe / p_star_safe))

        # 3. ||θ - θ*||²_g
        delta_theta = theta - theta_star
        Fisher_values[i] = delta_theta @ g_fisher @ delta_theta

        if (i+1) % 20 == 0:
            print(f"  Sample {i+1}/{n_samples}: D={D_values[i]:.4f}, D_KL={D_KL_values[i]:.6f}, Fisher={Fisher_values[i]:.6f}")

    return D_values, D_KL_values, Fisher_values


def fit_regression(D_values, D_KL_values, Fisher_values):
    """
    Fit: D = β₀ + β_KL D_KL + β_F Fisher + ε

    Using multiple linear regression.

    Returns:
        beta_0, beta_KL, beta_F: fitted coefficients
        R_squared: goodness of fit
        residuals: ε_i
    """
    print("\nFitting regression D = β₀ + β_KL D_KL + β_F Fisher...")

    # Design matrix: X = [1, D_KL, Fisher]
    n = len(D_values)
    X = np.column_stack([np.ones(n), D_KL_values, Fisher_values])
    y = D_values

    # Least squares: β = (X^T X)^{-1} X^T y
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    beta_0, beta_KL, beta_F = beta

    # Predictions
    y_pred = X @ beta

    # Residuals
    residuals = y - y_pred

    # R²
    SS_res = np.sum(residuals**2)
    SS_tot = np.sum((y - np.mean(y))**2)
    R_squared = 1 - SS_res / SS_tot

    print(f"  β₀ = {beta_0:.4f}")
    print(f"  β_KL = {beta_KL:.4f}")
    print(f"  β_F = {beta_F:.4f}")
    print(f"  R² = {R_squared:.4f}")

    return beta_0, beta_KL, beta_F, R_squared, residuals, y_pred


def plot_results(D_values, D_KL_values, Fisher_values, beta_0, beta_KL, beta_F, R_squared, y_pred):
    """
    Visualize regression fit
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # 1. D vs D_KL
    ax = axes[0, 0]
    ax.scatter(D_KL_values, D_values, alpha=0.5, label='Data')
    # Show D = β₀ + β_KL D_KL (with Fisher = 0)
    D_KL_sorted = np.sort(D_KL_values)
    D_fit_DKL = beta_0 + beta_KL * D_KL_sorted
    ax.plot(D_KL_sorted, D_fit_DKL, 'r-', label=f'D = {beta_0:.2f} + {beta_KL:.2f} D_KL', linewidth=2)
    ax.set_xlabel('D_KL(p_θ || p_*)')
    ax.set_ylabel('D(θ)')
    ax.set_title('D vs D_KL')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 2. D vs Fisher
    ax = axes[0, 1]
    ax.scatter(Fisher_values, D_values, alpha=0.5, label='Data')
    Fisher_sorted = np.sort(Fisher_values)
    D_fit_Fisher = beta_0 + beta_F * Fisher_sorted
    ax.plot(Fisher_sorted, D_fit_Fisher, 'g-', label=f'D = {beta_0:.2f} + {beta_F:.2f} Fisher', linewidth=2)
    ax.set_xlabel('||θ - θ*||²_g (Fisher)')
    ax.set_ylabel('D(θ)')
    ax.set_title('D vs Fisher Quadratic')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 3. Predicted vs Actual
    ax = axes[1, 0]
    ax.scatter(y_pred, D_values, alpha=0.5)
    lims = [min(np.min(y_pred), np.min(D_values)), max(np.max(y_pred), np.max(D_values))]
    ax.plot(lims, lims, 'k--', alpha=0.3, label='Perfect fit')
    ax.set_xlabel('Predicted D')
    ax.set_ylabel('Actual D')
    ax.set_title(f'Predicted vs Actual (R² = {R_squared:.3f})')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 4. Residuals
    ax = axes[1, 1]
    ax.hist(D_values - y_pred, bins=30, alpha=0.7, color='blue')
    ax.set_xlabel('Residuals (D - D_pred)')
    ax.set_ylabel('Count')
    ax.set_title('Residual Distribution')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(Path(__file__).parent / 'test_3_2_results.png', dpi=150)
    print("\nPlot saved: test_3_2_results.png")


def main():
    """
    Full Test 3.2 pipeline
    """
    print("="*60)
    print("AG-1 Test 3.2: D ≈ β_KL D_KL + β_F Fisher")
    print("="*60)

    # 1. Run to equilibrium
    bootstrap, theta_star, p_star, psi_star = run_to_equilibrium(n_steps=5000)

    # 2. Sample perturbations
    theta_samples = sample_perturbations(theta_star, n_samples=50, perturbation_scale=0.03)

    # 3. Compute D, D_KL, Fisher
    D_values, D_KL_values, Fisher_values = compute_D_KL_Fisher_for_perturbations(
        bootstrap, theta_star, p_star, psi_star, theta_samples
    )

    # 4. Regression
    beta_0, beta_KL, beta_F, R_squared, residuals, y_pred = fit_regression(
        D_values, D_KL_values, Fisher_values
    )

    # 5. Visualize
    plot_results(D_values, D_KL_values, Fisher_values, beta_0, beta_KL, beta_F, R_squared, y_pred)

    # Summary
    print("\n" + "="*60)
    print("VERDICT")
    print("="*60)

    if R_squared > 0.8:
        print(f"✓ PASS: R² = {R_squared:.3f} > 0.8")
        print(f"  D(θ) ≈ {beta_0:.2f} + {beta_KL:.2f} D_KL + {beta_F:.2f} Fisher")
        print("  → PR-0's D approximates Φ near equilibrium")
        print("  → D-minimization implements AG-1 analytic gauge")
    else:
        print(f"✗ FAIL: R² = {R_squared:.3f} < 0.8")
        print("  D(θ) is NOT well-approximated by β_KL D_KL + β_F Fisher")
        print("  → AG-1 still valid with Φ = k_B T_eff D_KL")
        print("  → But PR-0's D is not the Reflexive Landauer potential")

    return beta_0, beta_KL, beta_F, R_squared


if __name__ == "__main__":
    beta_0, beta_KL, beta_F, R_squared = main()
