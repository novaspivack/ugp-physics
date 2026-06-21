"""
2D spin-7 lattice model phase diagram.
H = sum_{i,j} [p(s_{i-1,j}, s_{i,j}, s_{i+1,j}) + p(s_{i,j-1}, s_{i,j}, s_{i,j+1})]
where p(L,C,R) = C+R-CR-LCR mod 7.

Runs Metropolis MC for L=4,8,12,16 at beta=0.5,1.0,1.5,2.0,2.5,3.0.
Looks for peak in specific heat (phase transition signature).
"""

import signal, sys, json, time
import numpy as np

TIMEOUT = 290
T_START = time.time()

def _timeout_handler(signum, frame):
    elapsed = time.time() - T_START
    print(f"\nTIMEOUT: {TIMEOUT}s wall-clock reached after {elapsed:.1f}s. Saving partial results.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT)

# ---- p table (precomputed for speed) ----
p_table = np.zeros((7, 7, 7), dtype=np.int32)
for L in range(7):
    for C in range(7):
        for R in range(7):
            p_table[L, C, R] = (C + R - C*R - L*C*R) % 7

def site_energy(spins, i, j, s, Lsize):
    """Energy contribution from all triplets containing site (i,j) with spin s."""
    im1 = (i - 1) % Lsize
    ip1 = (i + 1) % Lsize
    ip2 = (i + 2) % Lsize
    im2 = (i - 2) % Lsize
    jm1 = (j - 1) % Lsize
    jp1 = (j + 1) % Lsize
    jp2 = (j + 2) % Lsize
    jm2 = (j - 2) % Lsize

    # Horizontal: site as L, C, R in three different triplets
    # Center of triplet: contribution p(left, s, right)
    e_hc = p_table[spins[im1, j], s, spins[ip1, j]]
    # As right neighbor of (i-1)-centered triplet: p(i-2, i-1, i)
    e_hr = p_table[spins[im2, j], spins[im1, j], s]
    # As left neighbor of (i+1)-centered triplet: p(i, i+1, i+2)
    e_hl = p_table[s, spins[ip1, j], spins[ip2, j]]

    # Vertical: site as L, C, R
    e_vc = p_table[spins[i, jm1], s, spins[i, jp1]]
    e_vr = p_table[spins[i, jm2], spins[i, jm1], s]
    e_vl = p_table[s, spins[i, jp1], spins[i, jp2]]

    return int(e_hc) + int(e_hr) + int(e_hl) + int(e_vc) + int(e_vr) + int(e_vl)

def compute_total_energy(spins, Lsize):
    """Full energy: sum over all sites of center-position contribution (horizontal + vertical)."""
    E = 0
    for i in range(Lsize):
        for j in range(Lsize):
            im1 = (i - 1) % Lsize
            ip1 = (i + 1) % Lsize
            jm1 = (j - 1) % Lsize
            jp1 = (j + 1) % Lsize
            E += int(p_table[spins[im1, j], spins[i, j], spins[ip1, j]])
            E += int(p_table[spins[i, jm1], spins[i, j], spins[i, jp1]])
    return E

def compute_order_parameter(spins):
    """Complex Z_7 order parameter: |<exp(2pi i s/7)>|."""
    phases = np.exp(2j * np.pi * spins.astype(float) / 7.0)
    return float(np.abs(phases.mean()))

def compute_vacuum_fraction(spins):
    """Fraction of sites with spin=0 (vacuum sector)."""
    return float((spins == 0).sum() / spins.size)

def run_mc(Lsize, beta, n_therm_sweeps=600, n_meas_sweeps=1200, seed=None):
    """
    Metropolis MC for Lsize x Lsize spin-7 lattice.
    Returns thermodynamic observables.
    """
    rng = np.random.default_rng(seed)
    N = Lsize * Lsize
    spins = rng.integers(0, 7, size=(Lsize, Lsize), dtype=np.int32)

    # Pre-compute Boltzmann factors for dE in range [-36, +36]
    # (max |dE| = 6*6 = 36 from 6 triplets each with energy 0-6)
    boltz = {}
    for dE_val in range(-42, 43):
        if dE_val <= 0:
            boltz[dE_val] = 2.0  # accept always
        else:
            boltz[dE_val] = float(np.exp(-beta * dE_val))

    def mc_sweep():
        for _ in range(N):
            i = int(rng.integers(0, Lsize))
            j = int(rng.integers(0, Lsize))
            s_old = int(spins[i, j])
            s_new = int(rng.integers(0, 7))
            if s_new == s_old:
                continue
            dE = site_energy(spins, i, j, s_new, Lsize) - site_energy(spins, i, j, s_old, Lsize)
            if boltz.get(dE, np.exp(-beta * dE) if dE > 0 else 2.0) >= rng.random():
                spins[i, j] = s_new

    # Thermalization
    for _ in range(n_therm_sweeps):
        mc_sweep()

    # Measurement
    energies = []
    order_params = []
    vac_fracs = []

    for sweep_idx in range(n_meas_sweeps):
        mc_sweep()
        if sweep_idx % 10 == 0:
            E = compute_total_energy(spins, Lsize)
            M = compute_order_parameter(spins)
            v = compute_vacuum_fraction(spins)
            energies.append(E)
            order_params.append(M)
            vac_fracs.append(v)

    E_arr = np.array(energies, dtype=float)
    M_arr = np.array(order_params)
    V_arr = np.array(vac_fracs)

    mean_E = float(E_arr.mean())
    mean_E2 = float((E_arr**2).mean())
    C_V = beta**2 * (mean_E2 - mean_E**2) / N
    mean_M = float(M_arr.mean())
    mean_M2 = float((M_arr**2).mean())
    chi = N * (mean_M2 - mean_M**2)
    mean_vac = float(V_arr.mean())

    return {
        'L': Lsize,
        'beta': beta,
        'mean_E_per_site': mean_E / N,
        'specific_heat': C_V,
        'mean_M': mean_M,
        'susceptibility': chi,
        'mean_vac_fraction': mean_vac,
        'n_samples': len(E_arr),
    }

# ============================================================
# Phase scan: L=4,8,12,16 x beta=0.5,1.0,...,3.0
# ============================================================
betas = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
sizes = [4, 8, 12, 16]

print("=== 2D Spin-7 Phase Diagram: Metropolis MC ===")
print(f"H = sum_{{i,j}} [p(s_{{i-1,j}}, s_{{i,j}}, s_{{i+1,j}}) + p(s_{{i,j-1}}, s_{{i,j}}, s_{{i,j+1}})]")
print(f"p(L,C,R) = C+R-CR-LCR mod 7")
print()

all_results = []
header = f"{'L':>4} {'beta':>6} {'E/N':>9} {'C_V':>9} {'M':>9} {'chi':>9} {'vac%':>7}"
print(header)
print("-" * len(header))

for Lsize in sizes:
    for beta in betas:
        elapsed = time.time() - T_START
        if elapsed > TIMEOUT - 30:
            print(f"  [Time budget exhausted after {elapsed:.0f}s — stopping early]")
            break

        # Adjust sweep counts based on L (larger L needs fewer sweeps per site)
        n_therm = max(200, 600 // (Lsize // 4))
        n_meas = max(400, 1200 // (Lsize // 4))

        result = run_mc(Lsize, beta, n_therm_sweeps=n_therm, n_meas_sweeps=n_meas, seed=42 + Lsize + int(beta*10))
        all_results.append(result)

        print(f"{Lsize:>4} {beta:>6.2f} {result['mean_E_per_site']:>9.4f} "
              f"{result['specific_heat']:>9.4f} {result['mean_M']:>9.4f} "
              f"{result['susceptibility']:>9.4f} {100*result['mean_vac_fraction']:>6.1f}%")

    print()

# ============================================================
# Identify phase transition: peak in specific heat by L
# ============================================================
print("\n=== Specific heat C_V by L (look for peak) ===")
print(f"{'beta':>6}", end="")
for Lsize in sizes:
    print(f"  C_V(L={Lsize})", end="")
print()

for beta in betas:
    print(f"{beta:>6.2f}", end="")
    for Lsize in sizes:
        r = next((x for x in all_results if x['L'] == Lsize and abs(x['beta'] - beta) < 0.01), None)
        if r:
            print(f"  {r['specific_heat']:>10.4f}", end="")
        else:
            print(f"  {'---':>10}", end="")
    print()

# Find beta_c estimate (peak of C_V for largest L)
L_max = max(sizes)
cv_data = [(r['beta'], r['specific_heat']) for r in all_results if r['L'] == L_max]
if cv_data:
    beta_peak, cv_peak = max(cv_data, key=lambda x: x[1])
    print(f"\nPeak C_V for L={L_max}: {cv_peak:.4f} at beta={beta_peak:.2f}")
    print(f"Estimated beta_c ≈ {beta_peak:.2f}  (T_c ≈ {1/beta_peak:.2f})")

# Check finite-size scaling: does peak grow with L?
print("\n=== Finite-size scaling: peak C_V vs L ===")
peaks = []
for Lsize in sizes:
    cv_by_beta = [(r['beta'], r['specific_heat']) for r in all_results if r['L'] == Lsize]
    if cv_by_beta:
        peak_beta, peak_cv = max(cv_by_beta, key=lambda x: x[1])
        peaks.append((Lsize, peak_beta, peak_cv))
        print(f"  L={Lsize}: peak C_V = {peak_cv:.4f} at beta={peak_beta:.2f}")

if len(peaks) >= 2:
    # If C_V_max grows with L, it signals a true phase transition
    cv_vals = [p[2] for p in peaks]
    growing = all(cv_vals[i] <= cv_vals[i+1] for i in range(len(cv_vals)-1))
    print(f"\n  Peak C_V growing with L: {'YES — consistent with true phase transition' if growing else 'NO — may be crossover or finite-size artifact'}")

# ============================================================
# CMCA transfer matrix connection
# ============================================================
print("\n=== CMCA Transfer Matrix Connection ===")
print("The 1D transfer matrix T[b,c] = sum_a exp(-beta * p(a,b,c))")
print("encodes a single step of CMCA spacetime evolution.")
print("The 2D partition function Z_2D = Tr(T^{L_y}) where L_y = spatial extent.")
print()

# Recompute 1D transfer matrix and verify connection
def build_1d_transfer_matrix(beta):
    T = np.zeros((7, 7))
    for b in range(7):
        for c in range(7):
            T[b, c] = sum(np.exp(-beta * p_table[a, b, c]) for a in range(7))
    return T

for beta_val in [1.0, 2.0]:
    T1D = build_1d_transfer_matrix(beta_val)
    evals = np.sort(np.abs(np.linalg.eigvals(T1D)))[::-1]
    xi = 1.0 / np.log(evals[0] / evals[1]) if evals[1] > 1e-10 else float('inf')
    entropy_rate = float(np.log(evals[0]))
    print(f"beta={beta_val}: lambda_1={evals[0]:.4f}, lambda_2={evals[1]:.4f}, "
          f"xi={xi:.4f}, CMCA entropy rate=log(lambda_1)={entropy_rate:.4f} nats/step")

# ============================================================
# Ground state structure
# ============================================================
print("\n=== Ground State Analysis ===")
# A global ground state of the 2D model must satisfy p(L,C,R)=0 for ALL triplets
# Check: can uniform configurations be ground states?
for s_val in range(7):
    e_horiz = p_table[s_val, s_val, s_val]
    print(f"  Uniform spin={s_val}: triplet energy p({s_val},{s_val},{s_val}) = {e_horiz}")

# Check: how many 1D ground state configurations exist for small chain?
def find_1d_ground_states(Lchain):
    """Configurations where p(s_{i-1},s_i,s_{i+1})=0 for all i (periodic BC)."""
    count = 0
    for config in np.ndindex(*([7]*Lchain)):
        ok = True
        for i in range(Lchain):
            if p_table[config[(i-1)%Lchain], config[i], config[(i+1)%Lchain]] != 0:
                ok = False
                break
        if ok:
            count += 1
    return count

print()
for chain_len in [4, 5, 6]:
    gs_count = find_1d_ground_states(chain_len)
    print(f"  1D ground states (L={chain_len}, periodic BC): {gs_count}")

signal.alarm(0)

# Save results
out = {
    'mc_results': all_results,
    'peaks': peaks if 'peaks' in dir() else [],
    'beta_c_estimate': float(beta_peak) if 'beta_peak' in dir() else None,
    'cv_peak_value': float(cv_peak) if 'cv_peak' in dir() else None,
    'total_elapsed_s': float(time.time() - T_START),
}

with open("spin7_2d_phase_results.json", "w") as f:
    json.dump(out, f, indent=2)

print(f"\nTotal elapsed: {time.time()-T_START:.1f}s")
print("Results saved to spin7_2d_phase_results.json")
