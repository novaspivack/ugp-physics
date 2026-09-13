"""
Refined 2D spin-7 Monte Carlo: longer runs, better convergence.
Focuses on transition region, uses multiple seeds for error bars.
H = sum_{i,j} [p(s_{i-1,j}, s_{i,j}, s_{i+1,j}) + p(s_{i,j-1}, s_{i,j}, s_{i,j+1})]
"""

import signal, sys, json, time
import numpy as np

TIMEOUT = 270
T_START = time.time()

def _timeout_handler(signum, frame):
    elapsed = time.time() - T_START
    print(f"\nTIMEOUT at {TIMEOUT}s. Saving partial results.")
    save_and_exit()

def save_and_exit():
    out = {
        'all_results': all_results,
        'ground_state_analysis': gs_analysis,
        'total_elapsed_s': float(time.time() - T_START),
        'status': 'partial',
    }
    with open("spin7_2d_refined_results.json", "w") as f:
        json.dump(out, f, indent=2)
    print("Saved partial results.")
    sys.exit(0)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT)

p_table = np.zeros((7, 7, 7), dtype=np.int32)
for L in range(7):
    for C in range(7):
        for R in range(7):
            p_table[L, C, R] = (C + R - C*R - L*C*R) % 7

# Ground state analysis: which uniform spins have p(s,s,s)=0?
uniform_gs = [s for s in range(7) if p_table[s, s, s] == 0]
print(f"Uniform ground state spins (p(s,s,s)=0): {uniform_gs}")
print(f"  = Z_7 values: {uniform_gs}  (count: {len(uniform_gs)})")

# 2D ground states: for a torus, a state is a ground state if ALL triplets = 0
# Only uniform configurations with s in {0,1,5} qualify for arbitrary L
# (since non-uniform states would need periodic consistency)
print("\nChecking 2D ground states for L=3 torus (small):")
L3_gs = []
from itertools import product
for config in product(range(7), repeat=9):
    grid = np.array(config, dtype=np.int32).reshape(3, 3)
    is_gs = True
    for i in range(3):
        for j in range(3):
            if p_table[grid[(i-1)%3, j], grid[i, j], grid[(i+1)%3, j]] != 0:
                is_gs = False; break
            if p_table[grid[i, (j-1)%3], grid[i, j], grid[i, (j+1)%3]] != 0:
                is_gs = False; break
        if not is_gs:
            break
    if is_gs:
        L3_gs.append(config)

print(f"  2D ground states on 3x3 torus: {len(L3_gs)}")
if L3_gs:
    for gs in L3_gs[:5]:
        print(f"    {gs}")

gs_analysis = {
    'uniform_ground_state_spins': uniform_gs,
    'L3_torus_ground_states': len(L3_gs),
    'L3_ground_state_configs': L3_gs[:10],
}

all_results = []

def site_energy_contrib(spins, i, j, s, Lsize):
    im1 = (i-1)%Lsize; ip1 = (i+1)%Lsize; ip2 = (i+2)%Lsize; im2 = (i-2)%Lsize
    jm1 = (j-1)%Lsize; jp1 = (j+1)%Lsize; jp2 = (j+2)%Lsize; jm2 = (j-2)%Lsize
    return (int(p_table[spins[im1,j], s, spins[ip1,j]])
          + int(p_table[spins[im2,j], spins[im1,j], s])
          + int(p_table[s, spins[ip1,j], spins[ip2,j]])
          + int(p_table[spins[i,jm1], s, spins[i,jp1]])
          + int(p_table[spins[i,jm2], spins[i,jm1], s])
          + int(p_table[s, spins[i,jp1], spins[i,jp2]]))

def compute_energy(spins, Lsize):
    E = 0
    for i in range(Lsize):
        for j in range(Lsize):
            E += int(p_table[spins[(i-1)%Lsize,j], spins[i,j], spins[(i+1)%Lsize,j]])
            E += int(p_table[spins[i,(j-1)%Lsize], spins[i,j], spins[i,(j+1)%Lsize]])
    return E

def order_parameter_3way(spins, gs_spins=[0, 1, 5]):
    """Order parameter = fraction of sites in one of the 3 uniform GS values."""
    frac = sum((spins == s).sum() for s in gs_spins) / spins.size
    return float(frac)

def run_mc_refined(Lsize, beta, n_therm=2000, n_meas=4000, seed=42):
    rng = np.random.default_rng(seed)
    N = Lsize * Lsize
    # Start from random initial state
    spins = rng.integers(0, 7, size=(Lsize, Lsize), dtype=np.int32)

    def mc_sweep():
        for _ in range(N):
            i = int(rng.integers(0, Lsize))
            j = int(rng.integers(0, Lsize))
            s_old = int(spins[i, j])
            s_new = int(rng.integers(0, 7))
            if s_new == s_old:
                continue
            e_old = site_energy_contrib(spins, i, j, s_old, Lsize)
            e_new = site_energy_contrib(spins, i, j, s_new, Lsize)
            dE = e_new - e_old
            if dE <= 0 or rng.random() < np.exp(-beta * dE):
                spins[i, j] = s_new

    for _ in range(n_therm):
        mc_sweep()

    energies, order_params, vac_fracs = [], [], []
    for sweep_idx in range(n_meas):
        mc_sweep()
        if sweep_idx % 20 == 0:
            E = compute_energy(spins, Lsize)
            M = order_parameter_3way(spins)
            vac = float((spins == 0).sum() / N)
            energies.append(E)
            order_params.append(M)
            vac_fracs.append(vac)

    E_arr = np.array(energies, dtype=float)
    M_arr = np.array(order_params)
    n_samp = len(E_arr)

    mean_E = float(E_arr.mean())
    var_E = float(E_arr.var())
    mean_M = float(M_arr.mean())
    var_M = float(M_arr.var())

    C_V = beta**2 * var_E / N
    chi = N * var_M

    return {
        'L': Lsize, 'beta': beta,
        'mean_E_per_site': mean_E / N,
        'specific_heat': C_V,
        'mean_M': mean_M,
        'chi': chi,
        'mean_vac': float(np.array(vac_fracs).mean()),
        'n_samples': n_samp,
    }

# ---- Main scan ----
# Dense beta grid to find the transition region
betas_fine = [0.3, 0.5, 0.7, 0.9, 1.1, 1.3, 1.5, 1.7, 2.0, 2.5]
sizes = [4, 8, 12]

print(f"\n=== Refined MC scan (L={sizes}, {len(betas_fine)} beta values) ===")
print(f"{'L':>4} {'beta':>6} {'E/N':>8} {'C_V':>9} {'M_gs':>8} {'chi':>8} {'vac%':>6}")
print("-" * 62)

for Lsize in sizes:
    for beta in betas_fine:
        if time.time() - T_START > TIMEOUT - 30:
            print("  [Time budget reached — stopping]")
            break
        # Multiple seeds averaged
        results_seeds = []
        for seed in [42, 123, 777]:
            r = run_mc_refined(Lsize, beta, n_therm=800, n_meas=2000, seed=seed)
            results_seeds.append(r)
        # Average over seeds
        keys = ['mean_E_per_site', 'specific_heat', 'mean_M', 'chi', 'mean_vac']
        avg = {k: float(np.mean([x[k] for x in results_seeds])) for k in keys}
        avg['L'] = Lsize
        avg['beta'] = beta
        all_results.append(avg)
        print(f"{Lsize:>4} {beta:>6.2f} {avg['mean_E_per_site']:>8.4f} "
              f"{avg['specific_heat']:>9.4f} {avg['mean_M']:>8.4f} "
              f"{avg['chi']:>8.4f} {100*avg['mean_vac']:>5.1f}%")
    print()

# ---- Summary: find phase transition ----
print("=== Phase transition analysis ===")
print("\nC_V peaks by L:")
for Lsize in sizes:
    data = [(r['beta'], r['specific_heat']) for r in all_results if r['L'] == Lsize]
    if data:
        peak_beta, peak_cv = max(data, key=lambda x: x[1])
        print(f"  L={Lsize}: peak C_V = {peak_cv:.4f} at beta_c ≈ {peak_beta:.2f}")

print("\nOrder parameter M_gs at all L (3-way GS fraction):")
for beta in betas_fine:
    vals = [(r['L'], r['mean_M']) for r in all_results if abs(r['beta']-beta)<0.01]
    vals.sort()
    line = f"  beta={beta:.2f}: " + " ".join(f"L={L}:{M:.3f}" for L,M in vals)
    print(line)

signal.alarm(0)

out = {
    'all_results': all_results,
    'ground_state_analysis': gs_analysis,
    'total_elapsed_s': float(time.time() - T_START),
    'status': 'complete',
}
with open("spin7_2d_refined_results.json", "w") as f:
    json.dump(out, f, indent=2)
print(f"\nTotal elapsed: {time.time()-T_START:.1f}s. Saved.")
