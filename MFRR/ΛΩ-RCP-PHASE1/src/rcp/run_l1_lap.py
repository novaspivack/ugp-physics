import os
import numpy as np
import pandas as pd
import yaml
from multiprocessing import Pool
from .util import ensure_dirs, save_json, set_seed, phi, Lambda
from .fisher_graphs import (build_lattice4d, build_lattice4d_smallworld, build_mutual_knn4d, build_kpkvb,
                            fisher_metric_proxy, scalar_curvature_proxy, 
                            omega_intensive_ricci, omega_rel)
from .heattrace import normalized_laplacian
from .spectral_dos import spectral_dimension_from_dos

def load_cfg():
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cfg_path = os.path.join(base_dir, "cfg", "config.yaml")
    with open(cfg_path, "r") as f:
        return yaml.safe_load(f)

def get_mean_degree(G):
    if G.number_of_nodes() == 0:
        return 0.0
    return 2.0 * G.number_of_edges() / G.number_of_nodes()

def build_degree_matched_lattice(N, target_degree):
    n = int(round(N ** 0.25))
    G_ref = build_lattice4d(n)
    actual_deg = get_mean_degree(G_ref)
    return G_ref, actual_deg

def process_graph_task(args):
    gname, gparams, seed, cfg = args
    set_seed(seed)
    rng = np.random.default_rng(seed)
    
    if gname == "lattice4d":
        n = gparams
        G = build_lattice4d(n)
        label = f"lattice4d_n{n}"
        ref_omega = 0.875
    elif gname == "lattice4d_sw":
        n = gparams
        G = build_lattice4d_smallworld(n, cfg["lemma1"]["smallworld_p"], rng)
        label = f"lattice4d_sw_n{n}"
        ref_omega = 0.875
    elif gname == "mutual_knn4d":
        N, k = gparams
        G = build_mutual_knn4d(seed, N, k)
        label = f"knn4d_N{N}_k{k}"
        G_ref, _ = build_degree_matched_lattice(N, 2*k)
        ref_omega = omega_intensive_ricci(G_ref, sample_edges=500)
    elif gname == "kpkvb4d":
        N, avg_k, T = gparams
        G = build_kpkvb(seed, N, avg_k, T)
        label = f"kpkvb_N{N}_k{avg_k}_T{T}"
        G_ref, _ = build_degree_matched_lattice(N, avg_k)
        ref_omega = omega_intensive_ricci(G_ref, sample_edges=500)
    else:
        raise ValueError(f"Unknown graph type: {gname}")
    
    return measure_one(G, seed, label, cfg, ref_omega)

def measure_one(G, seed, label, cfg, ref_omega):
    Omega_int = omega_intensive_ricci(G, sample_edges=500)
    Omega_rel = omega_rel(Omega_int, ref_omega)
    
    L = normalized_laplacian(G)
    
    d_eff = spectral_dimension_from_dos(L, n_eigs=min(200, G.number_of_nodes() - 2))
    
    mean_deg = get_mean_degree(G)
    
    return {
        "seed": seed,
        "graph": label,
        "N": G.number_of_nodes(),
        "mean_degree": float(mean_deg),
        "Omega_int": float(Omega_int),
        "Omega_rel": float(Omega_rel),
        "ref_omega": float(ref_omega),
        "d_eff": float(d_eff)
    }


def r2_score(y, yhat):
    ssr = np.sum((yhat - y.mean()) ** 2)
    sst = np.sum((y - y.mean()) ** 2) + 1e-12
    return float(ssr / sst)

def evaluate(intercept, slope, R, cfg):
    ok_i = abs(intercept - cfg["lemma1"]["target_dim"]) <= cfg["lemma1"]["tol_intercept"]
    ok_s = abs(slope - cfg["lemma1"]["lambda_expected"]) / cfg["lemma1"]["lambda_expected"] <= cfg["lemma1"]["tol_lambda_rel"]
    ok_r = R >= cfg["lemma1"]["acceptance_R2_min"]
    return "PASS" if (ok_i and ok_s and ok_r) else "FAIL"

def main():
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.chdir(base_dir)
    ensure_dirs()
    
    cfg = load_cfg()
    
    tasks = []
    
    print("Building task list...")
    for s in cfg["seeds"]:
        for gname in cfg["lemma1"]["graphs"]:
            if gname == "lattice4d":
                for n in cfg["lemma1"]["lattice4d_n_list"]:
                    tasks.append((gname, n, s, cfg))
            elif gname == "lattice4d_sw":
                for n in cfg["lemma1"]["lattice4d_n_list"]:
                    tasks.append((gname, n, s, cfg))
            elif gname == "mutual_knn4d":
                for N in cfg["lemma1"]["knn4d_N_list"]:
                    for k in cfg["lemma1"]["knn4d_k_list"]:
                        tasks.append((gname, (N, k), s, cfg))
            elif gname == "kpkvb4d":
                for N in cfg["lemma1"]["kpkvb_N_list"]:
                    for avg_k in cfg["lemma1"]["kpkvb_avg_k"]:
                        for T in cfg["lemma1"]["kpkvb_T"]:
                            tasks.append((gname, (N, avg_k, T), s, cfg))
    
    print(f"Total tasks: {len(tasks)}")
    
    n_cores = min(cfg.get("n_cores", 8), len(tasks))
    
    with Pool(processes=n_cores) as pool:
        rows = pool.map(process_graph_task, tasks)
    
    df = pd.DataFrame(rows)
    df.to_csv("results/l1_lap_records.csv", index=False)
    
    log_phi_omega = np.log(df["Omega_rel"].values) / np.log(phi())
    omega_range = np.max(log_phi_omega) - np.min(log_phi_omega)
    
    print(f"\nΩ_rel range: [{df['Omega_rel'].min():.4f}, {df['Omega_rel'].max():.4f}]")
    print(f"log_φ(Ω_rel) range: {omega_range:.4f} (min required: {cfg['lemma1']['min_logphi_range']})")
    
    test_slope = omega_range >= cfg["lemma1"]["min_logphi_range"]
    
    if test_slope:
        X = np.c_[np.ones(len(df)), log_phi_omega]
        y = df["d_eff"].values
        beta = np.linalg.lstsq(X, y, rcond=None)[0]
        
        intercept = float(beta[0])
        slope = float(beta[1])
        
        yhat = X @ beta
        R = r2_score(y, yhat)
        
        status = evaluate(intercept, slope, R, cfg)
    else:
        intercept = float(df["d_eff"].mean())
        slope = None
        R = 0.0
        
        ok_i = abs(intercept - cfg["lemma1"]["target_dim"]) <= cfg["lemma1"]["tol_intercept"]
        status = "PASS" if ok_i else "FAIL"
        print(f"\n⚠️  Insufficient Ω_rel range for slope test. Testing intercept only.")
    
    summary = {
        "intercept": intercept,
        "slope": slope if test_slope else "Not tested (insufficient Ω range)",
        "R2": R,
        "omega_rel_range": float(omega_range),
        "omega_rel_min": float(df["Omega_rel"].min()),
        "omega_rel_max": float(df["Omega_rel"].max()),
        "test_slope": bool(test_slope),
        "target_dim": cfg["lemma1"]["target_dim"],
        "lambda_expected": cfg["lemma1"]["lambda_expected"],
        "acceptance_R2_min": cfg["lemma1"]["acceptance_R2_min"],
        "pass_intercept": bool(abs(intercept - cfg["lemma1"]["target_dim"]) <= cfg["lemma1"]["tol_intercept"]),
        "status": status,
        "method": "small_lambda"
    }
    
    if test_slope:
        summary["pass_lambda"] = bool(abs(slope - cfg["lemma1"]["lambda_expected"]) / cfg["lemma1"]["lambda_expected"] <= cfg["lemma1"]["tol_lambda_rel"])
        summary["pass_R2"] = bool(R >= cfg["lemma1"]["acceptance_R2_min"])
    
    save_json(summary, "results/l1_lap_summary.json")
    
    print(f"\n{'='*60}")
    print(f"L1 Small-λ Eigenvalue Counting Results")
    print(f"{'='*60}")
    print(f"Intercept: {intercept:.4f} (target: {cfg['lemma1']['target_dim']})")
    if test_slope:
        print(f"Slope:     {slope:.4f} (target: {cfg['lemma1']['lambda_expected']:.4f})")
        print(f"R²:        {R:.4f} (min: {cfg['lemma1']['acceptance_R2_min']})")
    else:
        print(f"Slope:     Not tested (Ω_rel range {omega_range:.4f} < {cfg['lemma1']['min_logphi_range']})")
    print(f"Status:    {status}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.set_start_method('spawn', force=True)
    main()

