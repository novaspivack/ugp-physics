"""
Finite-size scaling study of 2D spin-7 model near the phase transition.
Focused scan around beta_c ≈ 0.3-0.7 with L=4,8,12,16.
Also: high-beta region to check if C_V peak is real or convergence artifact.
"""

import signal, sys, json, time
import numpy as np

TIMEOUT = 260
T_START = time.time()

def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT. Saving partial.")
    save_results()
    sys.exit(0)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT)

p_table = np.zeros((7, 7, 7), dtype=np.int32)
for L in range(7):
    for C in range(7):
        for R in range(7):
            p_table[L, C, R] = (C + R - C*R - L*C*R) % 7

all_results = []

def save_results():
    with open("spin7_2d_fss_results.json", "w") as f:
        json.dump({
            'all_results': all_results,
            'elapsed': time.time() - T_START,
        }, f, indent=2)

def site_E(spins, i, j, s, Ls):
    im1=(i-1)%Ls; ip1=(i+1)%Ls; ip2=(i+2)%Ls; im2=(i-2)%Ls
    jm1=(j-1)%Ls; jp1=(j+1)%Ls; jp2=(j+2)%Ls; jm2=(j-2)%Ls
    return (int(p_table[spins[im1,j],s,spins[ip1,j]])
          + int(p_table[spins[im2,j],spins[im1,j],s])
          + int(p_table[s,spins[ip1,j],spins[ip2,j]])
          + int(p_table[spins[i,jm1],s,spins[i,jp1]])
          + int(p_table[spins[i,jm2],spins[i,jm1],s])
          + int(p_table[s,spins[i,jp1],spins[i,jp2]]))

def total_E(spins, Ls):
    E = 0
    for i in range(Ls):
        for j in range(Ls):
            E += int(p_table[spins[(i-1)%Ls,j],spins[i,j],spins[(i+1)%Ls,j]])
            E += int(p_table[spins[i,(j-1)%Ls],spins[i,j],spins[i,(j+1)%Ls]])
    return E

def run_mc(Ls, beta, n_therm=1500, n_meas=3000, seed=42):
    rng = np.random.default_rng(seed)
    N = Ls * Ls
    spins = rng.integers(0, 7, size=(Ls, Ls), dtype=np.int32)

    for _ in range(n_therm):
        for __ in range(N):
            i = int(rng.integers(0, Ls)); j = int(rng.integers(0, Ls))
            s_old = int(spins[i, j])
            s_new = int(rng.integers(0, 7))
            if s_new == s_old: continue
            dE = site_E(spins,i,j,s_new,Ls) - site_E(spins,i,j,s_old,Ls)
            if dE <= 0 or rng.random() < np.exp(-beta*dE):
                spins[i,j] = s_new

    Es, Ms = [], []
    for step in range(n_meas):
        for __ in range(N):
            i = int(rng.integers(0, Ls)); j = int(rng.integers(0, Ls))
            s_old = int(spins[i, j])
            s_new = int(rng.integers(0, 7))
            if s_new == s_old: continue
            dE = site_E(spins,i,j,s_new,Ls) - site_E(spins,i,j,s_old,Ls)
            if dE <= 0 or rng.random() < np.exp(-beta*dE):
                spins[i,j] = s_new
        if step % 15 == 0:
            Es.append(total_E(spins, Ls))
            # 3-state order parameter: fraction in {0,1,5}
            Ms.append(float(sum((spins==s).sum() for s in [0,1,5]) / N))

    E_arr, M_arr = np.array(Es, float), np.array(Ms)
    return {
        'L': Ls, 'beta': beta,
        'E_per_site': float(E_arr.mean() / N),
        'C_V': float(beta**2 * E_arr.var() / N),
        'M': float(M_arr.mean()),
        'chi': float(N * M_arr.var()),
        'M_std': float(M_arr.std()),
        'n': len(E_arr),
    }

# === Part 1: Fine scan around primary transition (beta=0.2-0.7) ===
print("=== Part 1: Fine FSS around primary transition ===")
betas1 = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.70]
sizes1 = [4, 8, 12, 16]
print(f"{'L':>4} {'beta':>5} {'E/N':>7} {'C_V':>8} {'M':>7} {'chi':>8}")
print("-"*50)

for Ls in sizes1:
    for beta in betas1:
        if time.time()-T_START > TIMEOUT-40: break
        seeds = [42, 99, 321]
        rows = [run_mc(Ls, beta, n_therm=800, n_meas=2000, seed=s) for s in seeds]
        r = {k: float(np.mean([x[k] for x in rows])) for k in ['E_per_site','C_V','M','chi','M_std']}
        r['L'] = Ls; r['beta'] = beta; r['region'] = 'primary'
        all_results.append(r)
        print(f"{Ls:>4} {beta:>5.2f} {r['E_per_site']:>7.4f} {r['C_V']:>8.4f} {r['M']:>7.4f} {r['chi']:>8.4f}")
    print()

# === Part 2: High-beta check (beta=1.5-3.0) for L=8,12 ===
print("\n=== Part 2: High-beta behavior (convergence check) ===")
betas2 = [1.5, 1.7, 2.0, 2.5, 3.0]
sizes2 = [8, 12]

# Initialize from ORDERED state (all-0) to test ordered phase stability
for Ls in sizes2:
    for beta in betas2:
        if time.time()-T_START > TIMEOUT-40: break
        # Run from both ordered and random initial conditions
        r_rand = run_mc(Ls, beta, n_therm=1000, n_meas=2000, seed=42)
        # Ordered start (all-0)
        rng2 = np.random.default_rng(99)
        spins_ord = np.zeros((Ls, Ls), dtype=np.int32)
        N = Ls*Ls
        # Run from ordered start
        for _ in range(1500):
            for __ in range(N):
                i = int(rng2.integers(0, Ls)); j = int(rng2.integers(0, Ls))
                s_old = int(spins_ord[i,j]); s_new = int(rng2.integers(0,7))
                if s_new==s_old: continue
                dE = site_E(spins_ord,i,j,s_new,Ls) - site_E(spins_ord,i,j,s_old,Ls)
                if dE<=0 or rng2.random()<np.exp(-beta*dE): spins_ord[i,j]=s_new
        # Measure from ordered start
        Es2, Ms2 = [], []
        for step in range(2000):
            for __ in range(N):
                i=int(rng2.integers(0,Ls)); j=int(rng2.integers(0,Ls))
                s_old=int(spins_ord[i,j]); s_new=int(rng2.integers(0,7))
                if s_new==s_old: continue
                dE=site_E(spins_ord,i,j,s_new,Ls)-site_E(spins_ord,i,j,s_old,Ls)
                if dE<=0 or rng2.random()<np.exp(-beta*dE): spins_ord[i,j]=s_new
            if step%15==0:
                Es2.append(total_E(spins_ord,Ls))
                Ms2.append(float(sum((spins_ord==s).sum() for s in [0,1,5])/N))
        E2,M2=np.array(Es2,float),np.array(Ms2)
        r_ord = {'E_per_site':float(E2.mean()/N),'C_V':float(beta**2*E2.var()/N),'M':float(M2.mean())}

        hysteresis = abs(r_rand['M'] - r_ord['M'])
        print(f"L={Ls} beta={beta:.1f}: rand_start M={r_rand['M']:.4f} C_V={r_rand['C_V']:.4f} | "
              f"ord_start M={r_ord['M']:.4f} | hysteresis={hysteresis:.4f}")
        r_rand['region'] = 'high_beta'; r_rand['M_ord'] = r_ord['M']
        r_rand['hysteresis'] = float(hysteresis)
        all_results.append(r_rand)
    print()

signal.alarm(0)

# === Summary: locate beta_c ===
print("\n=== FSS Summary ===")
primary = [r for r in all_results if r.get('region') == 'primary']
print("\nC_V peak vs L (primary transition region):")
for Ls in sizes1:
    data = [(r['beta'], r['C_V']) for r in primary if r['L'] == Ls]
    if data:
        peak = max(data, key=lambda x: x[1])
        print(f"  L={Ls}: peak C_V={peak[1]:.4f} at beta={peak[0]:.2f}")

print("\nM at primary transition region by L:")
for beta in [0.20, 0.30, 0.40, 0.50, 0.60]:
    vals = [(r['L'], r['M']) for r in primary if abs(r['beta']-beta)<0.01]
    vals.sort()
    print(f"  beta={beta:.2f}: " + " ".join(f"L={L}:{M:.3f}" for L,M in vals))

print("\nHigh-beta hysteresis (first-order indicator):")
high = [r for r in all_results if r.get('region') == 'high_beta']
for r in high:
    print(f"  L={r['L']} beta={r['beta']:.1f}: hysteresis={r['hysteresis']:.4f}")

save_results()
print(f"\nTotal elapsed: {time.time()-T_START:.1f}s. Saved.")
