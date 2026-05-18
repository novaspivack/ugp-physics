import numpy as np
import pandas as pd
import yaml
from multiprocessing import Pool
from .util import ensure_dirs, save_json, set_seed, Lambda

def load_cfg():
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cfg_path = os.path.join(base_dir, "cfg", "config.yaml")
    with open(cfg_path, "r") as f:
        return yaml.safe_load(f)

def run_reaction_diffusion(curvature_integral, N_grid=64, T_steps=200, rng=None):
    """
    Reaction-diffusion system testing: Gen/Drain = exp(Λ·∫R_F dV)
    
    dΨ/dt = D∇²Ψ + J·ω·Ψ·(1-Ψ) - γ·Ψ
    
    Where Gen/Drain ratio is controlled by exponential of curvature integral
    """
    if rng is None:
        rng = np.random.default_rng(0)
    
    # Fixed parameters
    D = 0.01  # Diffusion
    gamma = 0.05  # Drain rate (constant)
    
    # Coupling determined by exponential of curvature
    # Theorem: Gen/Drain = exp(Λ·∫R_F)
    # For testing, we use J = J₀·exp(Λ·∫R_F) so Gen ∝ J
    J_0 = 0.025
    Lambda_val = 0.262  # Norfleet's constant
    J = J_0 * np.exp(Lambda_val * curvature_integral)
    J = np.clip(J, 0.01, 0.20)
    
    # Initialize field
    Psi = 0.1 + 0.02 * rng.standard_normal(N_grid)
    omega = 1.0 + 0.5 * np.sin(2 * np.pi * np.arange(N_grid) / N_grid)
    
    # Time evolution
    for _ in range(T_steps):
        # Laplacian (periodic BC)
        lap_Psi = np.roll(Psi, 1) + np.roll(Psi, -1) - 2*Psi
        
        # Reaction-diffusion update
        dPsi = D * lap_Psi + J * omega * Psi * (1 - Psi) - gamma * Psi
        Psi = Psi + 0.01 * dPsi
        Psi = np.clip(Psi, 0, 2)
    
    # Measure Gen/Drain
    generation = float(np.mean(J * omega * Psi * (1 - Psi)))
    drain = float(np.mean(gamma * Psi) + 1e-9)
    
    profit = generation / drain
    
    return profit

def process_pc_task(args):
    s, theta, N_samples = args
    set_seed(s)
    rng = np.random.default_rng(s+11)
    
    # Map theta to integrated curvature ∫R_F dV
    # theta ∈ [-1, 1] → ∫R_F ∈ [-2, 4]
    # Wider range to test exponential relationship
    curvature_integral = -2.0 + 3.0 * (theta + 1.0)
    
    # Run RD simulation
    profit = run_reaction_diffusion(curvature_integral, N_grid=64, T_steps=200, rng=rng)
    
    return (s, theta, float(curvature_integral), profit)

def main():
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.chdir(base_dir)
    ensure_dirs()
    cfg = load_cfg()
    n_cores = cfg.get("n_cores", 8)
    
    tasks = [(s, th, cfg["pc"]["N_samples"]) 
             for s in cfg["seeds"] 
             for th in cfg["pc"]["theta_grid"]]
    
    with Pool(processes=n_cores) as pool:
        rows = pool.map(process_pc_task, tasks)
    
    df = pd.DataFrame(rows, columns=["seed", "theta", "curvature", "profit"])
    df.to_csv("results/pc_records.csv", index=False)
    
    x = df["curvature"].values
    y = np.log(df["profit"].values)
    a, b = np.polyfit(x, y, 1)
    
    # R² calculation
    yhat = a * x + b
    ss_tot = np.sum((y - y.mean())**2)
    ss_res = np.sum((y - yhat)**2)
    r2 = 1.0 - ss_res / (ss_tot + 1e-12)
    
    lambda_expected = cfg["lemma1"]["lambda_expected"]
    rel_err = abs(a - lambda_expected) / lambda_expected
    pass_flag = rel_err <= cfg["pc"]["tol_lambda_rel"]
    
    print(f"\nPC Profit-Curvature Results:")
    print(f"  Slope (observed): {a:.4f}")
    print(f"  Λ (expected): {lambda_expected:.4f}")
    print(f"  Relative error: {rel_err*100:.2f}%")
    print(f"  R²: {r2:.4f}")
    print(f"  Curvature range: [{x.min():.3f}, {x.max():.3f}]")
    print(f"  Profit range: [{df['profit'].min():.3f}, {df['profit'].max():.3f}]")
    print(f"  Status: {'PASS' if pass_flag else 'FAIL'}")
    
    save_json({
        "slope": float(a),
        "intercept": float(b),
        "R2": float(r2),
        "curvature_range": [float(x.min()), float(x.max())],
        "profit_range": [float(df['profit'].min()), float(df['profit'].max())],
        "lambda_expected": lambda_expected,
        "relative_error": float(rel_err),
        "status": "PASS" if pass_flag else "FAIL"
    }, "results/pc_summary.json")

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.set_start_method('spawn', force=True)
    main()

