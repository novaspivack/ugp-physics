from pathlib import Path
"""
Clock-Gradient Native Geodesic Coupling
========================================
Tests whether the SPATIAL GRADIENT OF THE CLOCK LAYER gives the correct
gravitational force direction, computed purely from nearest-neighbor clock values.

Architecture:
- Inner clock fires at rate: clock_rate(x) = BASE_RATE - alpha*phi(x)
  where phi(x) is the gravitational potential (precomputed from Z7 polynomial source)
- At each step, probe reads L_clk and R_clk (clock rates of left and right neighbors)
- Bias: if L_clk > R_clk (clock slows to right = mass to right), step RIGHT
- This is sign(L_clk - R_clk) = sign(+partial_phi/partial_x) = toward mass

NO global Poisson computation in the probe dynamics — only nearest-neighbor clock comparison.

We DO still need phi to set the initial clock rates (this is the source specification).
The question is whether the PROBE can navigate purely from clock gradients.
"""
import numpy as np
from scipy.ndimage import gaussian_filter1d
import signal, json

TIMEOUT = 250
signal.signal(signal.SIGALRM, lambda s, f: (_ for _ in ()).throw(TimeoutError()))
signal.alarm(TIMEOUT)

rule110_table = {(0,0,0):0,(0,0,1):1,(0,1,0):1,(0,1,1):1,
                 (1,0,0):0,(1,0,1):1,(1,1,0):1,(1,1,1):0}
def step_r110(tape):
    N=len(tape); new=np.zeros(N,dtype=int)
    for i in range(N): new[i]=rule110_table[(tape[(i-1)%N],tape[i],tape[(i+1)%N])]
    return new

def gte_poly_z7(L,C,R): return int((C+R-C*R-L*C*R)%7)

L=600; center=L//2
ether_tile=[1,0,0,1,1,0,1,1,1,1,1,0,0,0]
ether=np.tile(ether_tile,L//14+1)[:L]

SIGMA=5.0; REG=1.0
BASE_RATE=0.6; T_PROBE=300; N_AVG=8

# === Build gravitational potential phi from Z7 compact Poisson ===
# (same as Run 079-015 — this sets the clock rates)
src_x=ether.copy(); src_y=ether.copy(); src_z=ether.copy()
for xp in [126,131,132]:
    src_x[(center+xp-128)%L]^=1
    src_y[(center+xp-128+5)%L]^=1
    src_z[(center+xp-128-5)%L]^=1
wx_raw=((src_x!=ether).astype(int))*2
wy_raw=((src_y!=ether).astype(int))*6
wz_raw=((src_z!=ether).astype(int))*3
rho_raw=np.array([gte_poly_z7(wx_raw[x],wy_raw[x],wz_raw[x]) for x in range(L)],dtype=float)/6.0
rho=gaussian_filter1d(rho_raw,sigma=SIGMA)
phi=np.zeros(L)
for xp in np.where(rho>rho.max()*0.001)[0]:
    r=np.sqrt((np.arange(L)-xp)**2+REG**2)
    phi+=rho[xp]/r
phi_n=phi/phi.max() if phi.max()>0 else phi

# === Clock rate field: clock_rate(x) = BASE_RATE - alpha*phi(x) ===
# Slower clock near mass (gravitational time dilation)

print("CLOCK-GRADIENT NATIVE GEODESIC COUPLING TEST")
print("Probe reads nearest-neighbor clock rates; steps toward slower clock")
print()
print(f"phi field: peak={phi_n.max():.4f}, at b=50: {phi_n[center+50]:.5f}")
print()

# === Experiment: scan alpha values ===
# For each alpha, the clock rate field is clock_rate(x) = BASE_RATE - alpha*phi_n(x)
# The probe reads L_clk=clock_rate(x-1), R_clk=clock_rate(x+1)
# Bias: if L_clk > R_clk → clock slower to right → step RIGHT (toward mass)
# Equivalently: bias_direction = sign(L_clk - R_clk) = sign(-phi_n(x-1)+phi_n(x+1)) = sign(d_phi/dx)

def run_clock_gradient(start_pos, alpha_clk, br, T, ph=0):
    """Run probe using clock-gradient bias (CA-native geodesic)."""
    ether_ph=np.roll(ether,ph); probe=ether_ph.copy()
    for xp in [126,131,132]: probe[(start_pos+xp-128)%L]^=1

    # Probe position accumulator
    probe_pos=float(start_pos)
    acc=np.zeros(L); positions=[probe_pos]

    for t in range(T):
        # Standard CA step
        acc+=br; sm=acc>=1; acc=np.where(sm,acc-1,acc)
        new=step_r110(probe); probe=np.where(sm,new,probe)

        # Clock-gradient bias: read neighbors' clock rates
        px=int(probe_pos)%L
        L_clk = br - alpha_clk*phi_n[(px-1)%L]  # clock rate at left neighbor
        R_clk = br - alpha_clk*phi_n[(px+1)%L]  # clock rate at right neighbor

        # If L_clk > R_clk: clock slower to right = mass to right → step right
        # grad_clock = L_clk - R_clk = alpha_clk*(phi_n(px+1) - phi_n(px-1))
        # = alpha_clk * 2 * d_phi/dx
        # Step direction = sign(grad_clock) = sign(d_phi/dx) = toward mass
        grad_clock = L_clk - R_clk

        # Apply bias as a small fractional step (avoid large jumps)
        step_bias = np.sign(grad_clock) * abs(grad_clock) * 5.0  # scale factor
        probe_pos += step_bias

        # Track position
        dev=(probe!=ether_ph).astype(int); act=np.where(dev>0)[0]
        ca_pos=float(np.mean(act)) if len(act)>0 else positions[-1]
        positions.append(ca_pos+(probe_pos-start_pos))

    return np.polyfit(np.arange(len(positions)),positions,1)[0] if len(positions)>10 else 0.0

def run_base(start_pos, br, T, ph=0):
    ether_ph=np.roll(ether,ph); probe=ether_ph.copy()
    for xp in [126,131,132]: probe[(start_pos+xp-128)%L]^=1
    acc=np.zeros(L); positions=[float(start_pos)]
    for _ in range(T):
        acc+=br; sm=acc>=1; acc=np.where(sm,acc-1,acc)
        new=step_r110(probe); probe=np.where(sm,new,probe)
        act=np.where((probe!=ether_ph)>0)[0]
        positions.append(float(np.mean(act)) if len(act)>0 else positions[-1])
    return np.polyfit(np.arange(len(positions)),positions,1)[0] if len(positions)>10 else 0.0

# === Run with different alpha values ===
impact_params=[30,40,50,70,100]
all_results={}

for alpha_clk in [0.1, 0.3, 0.5]:
    print(f"\n--- Clock-gradient coupling alpha={alpha_clk} ---")
    print(f"Clock rate range: [{BASE_RATE-alpha_clk:.3f}, {BASE_RATE:.3f}]")
    print(f"{'b':>5} {'dv_TRUE':>10} {'SNR':>7} {'T?':>4}")
    print("-"*32)

    results={}
    for b in impact_params:
        if center+b >= L: continue
        vk=[run_clock_gradient(center+b,alpha_clk,BASE_RATE,T_PROBE,ph*3) for ph in range(N_AVG)]
        vb=[run_base(center+b,BASE_RATE,T_PROBE,ph*3) for ph in range(N_AVG)]
        dv=np.mean(vk)-np.mean(vb)
        sem=np.sqrt(np.var(np.array(vk)-np.array(vb))/N_AVG)
        snr=abs(dv)/max(sem,1e-6)
        results[b]={'dv':float(dv),'snr':float(snr)}
        print(f"{b:>5} {dv:>10.5f} {snr:>7.1f} {'✓' if dv<0 else '✗':>4}")

    toward=[(b,abs(results[b]['dv'])) for b in impact_params
            if b in results and results[b]['dv']<0 and results[b]['snr']>0.5]
    if len(toward)>=3:
        ld=np.log([b for b,e in toward]); le=np.log([max(e,1e-8) for b,e in toward])
        pw=np.polyfit(ld,le,1)[0]
        print(f"Power law: b^{pw:.2f}, N_attracted={len(toward)}/{len(impact_params)}")
    else:
        pw=None
        print(f"N_attracted={len(toward)}/{len(impact_params)}")

    all_results[f'alpha={alpha_clk}']={'power_law':float(pw) if pw else None,
                                        'n_attracted':len(toward),'results':results}

# Save
out={'script':'clock_gradient_geodesic.py',
     'description':'CA-native geodesic: clock-layer gradient gives force direction',
     'results':all_results,
     'note':'phi field precomputed from Z7 source; probe reads nearest-neighbor clock rates only'}
with open(str(Path(__file__).parent / 'clock_gradient_results.json'),'w') as f:
    json.dump(out,f,indent=2)
print("\nResults saved to clock_gradient_results.json")
signal.alarm(0)
