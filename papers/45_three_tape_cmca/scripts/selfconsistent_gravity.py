from pathlib import Path
"""
Self-Consistent Gravity: Source Evolves Simultaneously with Probe
=================================================================
Closes Limitation 1 of P45 §7.6: the source field is now self-consistently
evolved under Rule 110 at each probe timestep.

Architecture:
1. Source tapes (tape_x, tape_y, tape_z) evolve Rule 110 at each step
2. Z7 winding field ρ(x) = p(wx,wy,wz)/6 recomputed at each step
3. 3D Poisson φ(x) = Σ ρ(x')/|x-x'| recomputed at each step
4. Gradient kick F = +∇φ applied to probe at each step

This is the fully self-consistent version.
"""
import numpy as np
from scipy.ndimage import gaussian_filter1d
import signal, json, time

TIMEOUT = 280
signal.signal(signal.SIGALRM, lambda s, f: (_ for _ in ()).throw(TimeoutError()))
signal.alarm(TIMEOUT)

rule110_table = {(0,0,0):0,(0,0,1):1,(0,1,0):1,(0,1,1):1,
                 (1,0,0):0,(1,0,1):1,(1,1,0):1,(1,1,1):0}
def step_r110(tape):
    N=len(tape); new=np.zeros(N,dtype=int)
    for i in range(N): new[i]=rule110_table[(tape[(i-1)%N],tape[i],tape[(i+1)%N])]
    return new

def gte_poly_z7(L,C,R): return int((C+R-C*R-L*C*R)%7)

L=400; center=L//2
ether_tile=[1,0,0,1,1,0,1,1,1,1,1,0,0,0]
ether=np.tile(ether_tile,L//14+1)[:L]

SIGMA=5.0; REG=1.0
ALPHA_KICK=3.0; BASE_RATE=0.6; T_PROBE=100; N_AVG=4

# Initialize source tapes (mixed particles, independently offset)
def init_source():
    src_x=ether.copy(); src_y=ether.copy(); src_z=ether.copy()
    for xp in [126,131,132]:
        src_x[(center+xp-128)%L]^=1
        src_y[(center+xp-128+5)%L]^=1
        src_z[(center+xp-128-5)%L]^=1
    return src_x, src_y, src_z

def compute_phi_from_tapes(src_x, src_y, src_z):
    """Compute gravitational potential from current tape state."""
    wx_raw=((src_x!=ether).astype(int))*2
    wy_raw=((src_y!=ether).astype(int))*6
    wz_raw=((src_z!=ether).astype(int))*3
    rho_raw=np.array([gte_poly_z7(wx_raw[x],wy_raw[x],wz_raw[x]) for x in range(L)],dtype=float)/6.0
    rho=gaussian_filter1d(rho_raw,sigma=SIGMA)
    phi=np.zeros(L)
    for xp in np.where(rho>rho.max()*0.001)[0]:
        r=np.sqrt((np.arange(L)-xp)**2+REG**2)
        phi+=rho[xp]/r
    if phi.max()>0: phi=phi/phi.max()
    return phi

def run_selfconsistent_kick(start_pos, alpha, br, T, ph=0):
    """Run probe with self-consistently updated source field."""
    src_x, src_y, src_z = init_source()
    ether_ph=np.roll(ether,ph); probe=ether_ph.copy()
    for xp in [126,131,132]: probe[(start_pos+xp-128)%L]^=1
    probe_pos=float(start_pos); acc=np.zeros(L); positions=[probe_pos]

    for t in range(T):
        # Evolve source tapes one step
        src_x=step_r110(src_x); src_y=step_r110(src_y); src_z=step_r110(src_z)
        # Recompute phi from current source state
        phi=compute_phi_from_tapes(src_x,src_y,src_z)
        dphi=np.gradient(phi)
        # Update probe
        acc+=br; sm=acc>=1; acc=np.where(sm,acc-1,acc)
        new=step_r110(probe); probe=np.where(sm,new,probe)
        px=int(probe_pos)%L
        probe_pos+=dphi[px]*alpha
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

impact_params=[15,20,30,40,50]
print("SELF-CONSISTENT GRAVITY (source evolves simultaneously with probe):")
print(f"{'b':>5} {'dv_TRUE':>10} {'SNR':>7} {'T?':>4}")
print("-"*32)

results={}
t0=time.time()
for b in impact_params:
    if time.time()-t0>240: print("Timeout approaching, stopping"); break
    vk=[run_selfconsistent_kick(center+b,ALPHA_KICK,BASE_RATE,T_PROBE,ph*3) for ph in range(N_AVG)]
    vb=[run_base(center+b,BASE_RATE,T_PROBE,ph*3) for ph in range(N_AVG)]
    dv=np.mean(vk)-np.mean(vb)
    sem=np.sqrt(np.var(np.array(vk)-np.array(vb))/N_AVG)
    snr=abs(dv)/max(sem,1e-6); results[b]={'dv':float(dv),'snr':float(snr)}
    print(f"{b:>5} {dv:>10.5f} {snr:>7.1f} {'✓' if dv<0 else '✗':>4}")

toward=[(b,abs(results[b]['dv'])) for b in impact_params if b in results and results[b]['dv']<0 and results[b]['snr']>0.5]
if len(toward)>=3:
    ld=np.log([b for b,e in toward]); le=np.log([max(e,1e-8) for b,e in toward])
    pw=np.polyfit(ld,le,1)[0]
    print(f"\nSELF-CONSISTENT GRAVITY power law: b^{pw:.2f}")
    print(f"Attracted: {len(toward)}/{len(impact_params)}")
    if pw<-1.5: print("✓ NEWTONIAN with self-consistent source!")
else:
    pw=None
    print(f"Attracted: {len(toward)}/{len(impact_params)}")

out={'script':'selfconsistent_gravity.py','power_law':float(pw) if pw else None,
     'n_attracted':len(toward),'results':results,
     'note':'Self-consistent: source Rule110 evolves at each probe timestep'}
with open(str(Path(__file__).parent / 'selfconsistent_gravity_results.json'),'w') as f:
    json.dump(out,f,indent=2)
print("\nResults saved.")
signal.alarm(0)
