"""
Measure diffusion tensor Γ from PR-0 parameter fluctuations

OBJECTIVE:
- Run PR-0 to equilibrium
- Record θ(t) trajectories: (g, gamma_base, gamma_scale)
- Compute autocorrelation ⟨δθ(t) δθ(0)⟩
- Extract diffusion Γ from fluctuation-dissipation

PHYSICS:
For SDE: dθ = -M∇D dt + √(2Γ) dW
Einstein relation: Γ = M k_B T_eff

From equilibrium fluctuations:
⟨δθ_i(t) δθ_j(0)⟩ → 2Γ_ij · exp(-t/τ) at long times
"""

import numpy as np
import sys
from pathlib import Path

_OPTIMIZER_TESTS = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(_OPTIMIZER_TESTS))

from pr0_system.bootstrap.dissonance import SDSBootstrap
import matplotlib.pyplot as plt


def run_to_equilibrium(n_steps=10000, record_every=10):
    """
    Run PR-0 until D stabilizes, recording θ trajectory

    Returns:
        theta_traj: array of shape (n_records, 3) for (g, gamma_base, gamma_scale)
        D_traj: ontological dissonance over time
        times: time indices
    """
    print("Running PR-0 to equilibrium...")

    L_x, L_y = 64, 64
    bootstrap = SDSBootstrap(L_x, L_y)

    # Initialize with small perturbation
    x, y = np.meshgrid(np.arange(L_x), np.arange(L_y))
    bootstrap.psi = 0.1 * np.exp(1j * 2*np.pi * np.random.rand(L_y, L_x))
    bootstrap.psi[L_y//2, L_x//2] += 1.0  # Seed

    theta_traj = []
    D_traj = []
    times = []

    for step in range(n_steps):
        # Evolve system
        bootstrap.step(dt=0.01)

        # Record every N steps
        if step % record_every == 0:
            theta = np.array([bootstrap.g, bootstrap.gamma_base, bootstrap.gamma_scale])
            theta_traj.append(theta)
            D_traj.append(bootstrap.best_dissonance if hasattr(bootstrap, 'best_dissonance') else 0)
            times.append(step)

            if step % 1000 == 0:
                print(f"  Step {step}: D = {D_traj[-1]:.4f}, θ = {theta}")

    theta_traj = np.array(theta_traj)
    D_traj = np.array(D_traj)
    times = np.array(times)

    print(f"Equilibrium reached: D = {D_traj[-1]:.4f}")
    print(f"Final θ*: g={theta_traj[-1,0]:.4f}, γ_base={theta_traj[-1,1]:.4f}, γ_scale={theta_traj[-1,2]:.4f}")

    return theta_traj, D_traj, times


def compute_autocorrelation(theta_traj, equilibrium_fraction=0.5):
    """
    Compute autocorrelation function ⟨δθ(t) δθ(0)⟩

    Use only equilibrium portion (last equilibrium_fraction of trajectory)

    Returns:
        C(τ): autocorrelation matrix (3, 3, n_lags)
        tau: lag times
    """
    print("\nComputing autocorrelation...")

    # Use equilibrium portion only
    n_eq = int(len(theta_traj) * equilibrium_fraction)
    theta_eq = theta_traj[-n_eq:]

    # Compute fluctuations δθ = θ - ⟨θ⟩
    theta_mean = np.mean(theta_eq, axis=0)
    delta_theta = theta_eq - theta_mean

    print(f"  ⟨θ⟩ = {theta_mean}")
    print(f"  std(δθ) = {np.std(delta_theta, axis=0)}")

    # Autocorrelation for each component pair
    n_lags = min(500, n_eq // 2)  # Compute up to half the equilibrium length
    C = np.zeros((3, 3, n_lags))

    for i in range(3):
        for j in range(3):
            for lag in range(n_lags):
                # C_ij(τ) = ⟨δθ_i(t+τ) δθ_j(t)⟩
                C[i, j, lag] = np.mean(delta_theta[lag:, i] * delta_theta[:len(delta_theta)-lag, j])

    tau = np.arange(n_lags)

    return C, tau, delta_theta


def extract_diffusion(C, tau, dt=1.0):
    """
    Extract diffusion tensor Γ from autocorrelation

    For long times: C_ij(τ) ~ 2Γ_ij · exp(-τ/τ_relax)

    At τ=0: C_ij(0) = ⟨δθ_i δθ_j⟩ = equilibrium covariance

    Returns:
        Gamma: diffusion tensor (3, 3)
        tau_relax: relaxation times (3,)
    """
    print("\nExtracting diffusion tensor Γ...")

    # Diagonal elements: C_ii(τ) for autocorrelation
    Gamma_diag = np.zeros(3)
    tau_relax = np.zeros(3)

    for i in range(3):
        # Fit exponential decay C_ii(τ) = A · exp(-τ/τ_i)
        # At long times, A ≈ 2Γ_ii

        # Use first 100 lags for fitting
        C_ii = C[i, i, :100]
        tau_fit = tau[:100] * dt

        # Log-linear fit: log C_ii = log A - τ/τ_i
        # Avoid log(0) issues
        C_ii_safe = np.maximum(C_ii, 1e-10)
        log_C = np.log(C_ii_safe)

        # Fit line
        if np.all(np.isfinite(log_C)):
            slope, intercept = np.polyfit(tau_fit, log_C, 1)
            tau_relax[i] = -1.0 / slope if slope < 0 else np.inf
            A = np.exp(intercept)
            Gamma_diag[i] = A / 2.0
        else:
            tau_relax[i] = np.inf
            Gamma_diag[i] = C[i, i, 0] / 2.0  # Fallback: use τ=0 value

        print(f"  θ_{i}: Γ_{{ii}} = {Gamma_diag[i]:.6f}, τ_relax = {tau_relax[i]:.2f}")

    # Off-diagonal: use covariance at τ=0
    Gamma = np.diag(Gamma_diag)
    for i in range(3):
        for j in range(i+1, 3):
            Gamma[i, j] = C[i, j, 0] / 2.0
            Gamma[j, i] = Gamma[i, j]  # Symmetric

    print(f"\nDiffusion tensor Γ:")
    print(Gamma)

    return Gamma, tau_relax


def plot_results(theta_traj, D_traj, times, C, tau, Gamma):
    """
    Visualize:
    1. θ(t) trajectories
    2. D(t) convergence
    3. Autocorrelation decay
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # 1. Parameter trajectories
    ax = axes[0, 0]
    labels = ['g', 'γ_base', 'γ_scale']
    for i in range(3):
        ax.plot(times, theta_traj[:, i], label=labels[i], alpha=0.7)
    ax.set_xlabel('Time step')
    ax.set_ylabel('θ')
    ax.set_title('Parameter Evolution')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 2. Dissonance convergence
    ax = axes[0, 1]
    ax.plot(times, D_traj, 'k-', alpha=0.7)
    ax.set_xlabel('Time step')
    ax.set_ylabel('D(θ)')
    ax.set_title('Ontological Dissonance')
    ax.grid(True, alpha=0.3)

    # 3. Autocorrelation decay
    ax = axes[1, 0]
    for i in range(3):
        ax.plot(tau, C[i, i, :], label=f'{labels[i]} × {labels[i]}', alpha=0.7)
    ax.set_xlabel('Lag τ')
    ax.set_ylabel('C(τ)')
    ax.set_title('Autocorrelation ⟨δθ(t+τ) δθ(t)⟩')
    ax.set_yscale('log')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 4. Diffusion matrix heatmap
    ax = axes[1, 1]
    im = ax.imshow(Gamma, cmap='RdBu_r', aspect='auto')
    ax.set_xticks([0, 1, 2])
    ax.set_yticks([0, 1, 2])
    ax.set_xticklabels(labels)
    ax.set_yticklabels(labels)
    ax.set_title('Diffusion Tensor Γ')
    plt.colorbar(im, ax=ax)

    # Add values as text
    for i in range(3):
        for j in range(3):
            text = ax.text(j, i, f'{Gamma[i, j]:.2e}',
                          ha="center", va="center", color="black", fontsize=8)

    plt.tight_layout()
    plt.savefig(Path(__file__).parent / 'diffusion_measurement.png', dpi=150)
    print("\nPlot saved: diffusion_measurement.png")


def main():
    """
    Full pipeline:
    1. Run PR-0 to equilibrium
    2. Measure autocorrelation
    3. Extract Γ
    4. Visualize
    """
    print("="*60)
    print("AG-1: Measuring Diffusion Tensor Γ from PR-0")
    print("="*60)

    # 1. Run to equilibrium
    theta_traj, D_traj, times = run_to_equilibrium(n_steps=10000, record_every=10)

    # 2. Autocorrelation
    C, tau, delta_theta = compute_autocorrelation(theta_traj, equilibrium_fraction=0.5)

    # 3. Extract Γ
    Gamma, tau_relax = extract_diffusion(C, tau, dt=10.0)  # dt = record_every

    # 4. Visualize
    plot_results(theta_traj, D_traj, times, C, tau, Gamma)

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Equilibrium D: {D_traj[-1]:.4f}")
    print(f"Diffusion Γ (diagonal): {np.diag(Gamma)}")
    print(f"Relaxation times: {tau_relax}")
    print("\nNext: Use Γ in Onsager-Machlup action S_RL[θ]")

    return Gamma, theta_traj[-1], D_traj[-1]


if __name__ == "__main__":
    Gamma, theta_star, D_star = main()
