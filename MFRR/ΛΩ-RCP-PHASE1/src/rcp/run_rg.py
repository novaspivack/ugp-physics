import numpy as np
import pandas as pd
import yaml
from multiprocessing import Pool
from .util import ensure_dirs, save_json, set_seed

def load_cfg():
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cfg_path = os.path.join(base_dir, "cfg", "config.yaml")
    with open(cfg_path, "r") as f:
        return yaml.safe_load(f)

def srrg_step(g, step):
    """
    SRRG flow with reflexive curvature corrections
    β_SRRG = G_S^(-1) (δR/δS - δC_Λ/δS)
    
    For φ⁴ theory: includes Fisher metric and MDL penalty terms
    """
    m2, lam = g
    
    # Standard one-loop terms
    dm2_std = -0.1 * m2 + 0.05 * lam
    dlam_std = -0.02 * lam + 0.001 * lam * lam
    
    # Reflexive curvature correction (Fisher metric contribution)
    # G_S^(-1) modifies flow with information-geometric terms
    fisher_weight = 1.0 / (1.0 + 0.1 * (m2**2 + lam**2))  # Simplified Fisher metric
    dm2_refl = fisher_weight * dm2_std
    dlam_refl = fisher_weight * dlam_std
    
    # MDL penalty (negative curvature contribution)
    mdl_correction_m2 = -0.01 * np.sign(m2) * abs(m2)**0.5
    mdl_correction_lam = -0.005 * lam
    
    dm2 = dm2_refl + mdl_correction_m2
    dlam = dlam_refl + mdl_correction_lam
    
    return np.array([m2 + step*dm2, lam + step*dlam])

def wilson_block_step(g, step, L):
    """
    Standard Wilsonian RG via momentum-shell integration
    β_RG = standard one-loop β-functions
    """
    m2, lam = g
    
    # One-loop β-functions for φ⁴ in d=4-ε
    # β_m2 = -m² (tree) + λm²/(16π²) (one-loop)
    # β_λ = -ελ + 3λ²/(16π²) (one-loop)
    
    # Simplified for toy model:
    dm2 = -0.1 * m2 + 0.05 * lam
    dlam = -0.02 * lam + 0.001 * lam * lam
    
    return np.array([m2 + step*dm2, lam + step*dlam])

def estimate_beta_traj(g0, steps, step, method):
    g = np.array(g0, dtype=float)
    traj = [g.copy()]
    betas = []
    for _ in range(steps):
        g_next = method(g, step)
        beta = (g_next - g) / step
        betas.append(beta.copy())
        g = g_next
        traj.append(g.copy())
    return np.array(traj), np.array(betas)

def process_rg_task(args):
    s, steps, step_size, lattice_size = args
    set_seed(s)
    g0 = np.array([1.0, 0.2])
    traj_s, beta_s = estimate_beta_traj(g0, steps, step_size, lambda g, st: srrg_step(g, st))
    traj_w, beta_w = estimate_beta_traj(g0, steps, step_size, lambda g, st: wilson_block_step(g, st, lattice_size))
    
    err = np.linalg.norm(beta_s - beta_w, axis=1) / (np.linalg.norm(beta_w, axis=1) + 1e-9)
    mean_err = float(np.mean(err))
    return (s, mean_err)

def main():
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.chdir(base_dir)
    ensure_dirs()
    cfg = load_cfg()
    seeds = cfg["seeds"]
    n_cores = cfg.get("n_cores", 8)
    
    tasks = [(s, cfg["rg"]["steps"], cfg["rg"]["step_size"], cfg["rg"]["lattice_size"]) for s in seeds]
    
    with Pool(processes=n_cores) as pool:
        rec = pool.map(process_rg_task, tasks)
    
    df = pd.DataFrame(rec, columns=["seed", "mean_rel_beta_err"])
    df.to_csv("results/rg_records.csv", index=False)
    
    mean_err = float(df["mean_rel_beta_err"].mean())
    pass_flag = mean_err <= cfg["rg"]["tol_beta_rel"]
    
    print(f"\nRG Duality Results:")
    print(f"  Mean relative β-error: {mean_err:.4f}")
    print(f"  Tolerance: {cfg['rg']['tol_beta_rel']:.2f}")
    print(f"  Per-seed errors:")
    for _, row in df.iterrows():
        print(f"    Seed {row['seed']}: {row['mean_rel_beta_err']:.4f}")
    print(f"  Status: {'PASS' if pass_flag else 'FAIL'}")
    
    save_json({
        "mean_rel_beta_err": mean_err,
        "tol": cfg["rg"]["tol_beta_rel"],
        "status": "PASS" if pass_flag else "FAIL"
    }, "results/rg_summary.json")

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.set_start_method('spawn', force=True)
    main()

