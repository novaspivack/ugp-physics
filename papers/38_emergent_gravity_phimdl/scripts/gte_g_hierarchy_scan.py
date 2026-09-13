"""
Pre-registered Z7/F21 arithmetic scan for Newton's G hierarchy.

Pre-registered form class (Adam + Jane, EPIC_075 Session 3, 2026-05-26):
  7^a × 3^b × 21^c × N_gen^d × π^e / K
  a ∈ [0,30], b,c,d ∈ [0,15], e ∈ [0,6], K ∈ {1,2,4,8,16,3,7,9,14,21,49}

Targets:
  ratio_m_tau  = M_Pl / m_tau  = 6.872e18  (M_Pl = 1.221e19 GeV, m_tau = 1776.86 MeV)
  ratio_m_kink = M_Pl / m_kink = 4.210e22  (m_kink = 290.10 MeV)

Tolerance: 0.10% (pre-registered, not adjusted post-hoc)

Null tests:
  null_me  = M_Pl / m_e = 2.389e22  (electron mass -- unphysical in GTE)
"""

import itertools, math, json, signal, sys, time

TIMEOUT = 600
def _timeout(sig, frm):
    print("TIMEOUT reached. Saving partial results.")
    sys.exit(1)
signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT)

t0 = time.time()

# Physical constants (PDG 2024)
M_Pl_GeV = 1.22089e19          # reduced: 2.435e18; conventional: 1.22089e19
m_tau_MeV = 1776.86
m_kink_MeV = 290.10             # GTE kink mass = M_kink from BPS
m_e_MeV = 0.51099895

# Targets
ratio_m_tau  = (M_Pl_GeV * 1e3) / m_tau_MeV    # MeV/MeV
ratio_m_kink = (M_Pl_GeV * 1e3) / m_kink_MeV
ratio_m_e    = (M_Pl_GeV * 1e3) / m_e_MeV      # null test target

TOLERANCE = 1e-3   # 0.1% pre-registered

N_gen = 3
PI = math.pi

# Denominators allowed
K_vals = [1, 2, 4, 8, 16, 3, 7, 9, 14, 21, 49]

def scan_target(target, label, max_a=30, max_bcd=15, max_e=6):
    hits = []
    log_t = math.log(target)
    log_7 = math.log(7)
    log_3 = math.log(3)
    log_21 = math.log(21)
    log_3g = math.log(N_gen)
    log_pi = math.log(PI)
    for K in K_vals:
        log_K = math.log(K)
        for a in range(0, max_a+1):
            la = a * log_7 - log_K
            for b in range(0, max_bcd+1):
                lb = la + b * log_3
                for c in range(0, max_bcd+1):
                    lc = lb + c * log_21
                    for d in range(0, max_bcd+1):
                        ld = lc + d * log_3g
                        for e in range(0, max_e+1):
                            val_log = ld + e * log_pi
                            rel_err = abs(val_log - log_t) / log_t
                            if rel_err < TOLERANCE:
                                val = 7**a * 3**b * 21**c * N_gen**d * PI**e / K
                                actual_err = abs(val - target) / target
                                if actual_err < TOLERANCE:
                                    hits.append({
                                        "formula": f"7^{a} * 3^{b} * 21^{c} * {N_gen}^{d} * pi^{e} / {K}",
                                        "a": a, "b": b, "c": c, "d": d, "e": e, "K": K,
                                        "value": val,
                                        "target": target,
                                        "rel_err": actual_err,
                                        "label": label
                                    })
    return hits

print(f"Scanning {['ratio_m_tau', 'ratio_m_kink', 'null_me']}...")
print(f"Targets: ratio_m_tau={ratio_m_tau:.6e}, ratio_m_kink={ratio_m_kink:.6e}, null_me={ratio_m_e:.6e}")
print(f"Tolerance: {TOLERANCE*100:.2f}% (pre-registered)")
print()

hits_tau  = scan_target(ratio_m_tau,  "M_Pl/m_tau",  max_a=30, max_bcd=15, max_e=6)
hits_kink = scan_target(ratio_m_kink, "M_Pl/m_kink", max_a=30, max_bcd=15, max_e=6)
hits_me   = scan_target(ratio_m_e,    "null_me",     max_a=30, max_bcd=15, max_e=6)

elapsed = time.time() - t0

print(f"=== RESULTS ({elapsed:.1f}s) ===")
print(f"\nM_Pl/m_tau hits ({len(hits_tau)}):")
for h in hits_tau:
    print(f"  {h['formula']} = {h['value']:.6e}  (err {h['rel_err']*100:.4f}%)")

print(f"\nM_Pl/m_kink hits ({len(hits_kink)}):")
for h in hits_kink:
    print(f"  {h['formula']} = {h['value']:.6e}  (err {h['rel_err']*100:.4f}%)")

print(f"\nNULL TEST — M_Pl/m_e hits ({len(hits_me)}):")
for h in hits_me:
    print(f"  {h['formula']} = {h['value']:.6e}  (err {h['rel_err']*100:.4f}%)")

# Neighbor test for known 7^23/4 hit
print(f"\n=== NEIGHBOR ATOM TEST for 7^23/4 ===")
base_val = 7**23 / 4
print(f"7^23 / 4 = {base_val:.6e}  (target: {ratio_m_tau:.6e}, err: {abs(base_val-ratio_m_tau)/ratio_m_tau*100:.3f}%)")
for da in [-2,-1,1,2]:
    val = 7**(23+da) / 4
    err = abs(val - ratio_m_tau)/ratio_m_tau
    print(f"  7^{23+da}/4 = {val:.6e}  (err {err*100:.2f}%)")

results = {
    "pre_registered_form_class": "7^a * 3^b * 21^c * N_gen^d * pi^e / K",
    "exponent_ranges": {"a": "0..30", "b,c,d": "0..15", "e": "0..6", "K": K_vals},
    "tolerance_pct": 0.1,
    "targets": {
        "ratio_m_tau": ratio_m_tau,
        "ratio_m_kink": ratio_m_kink,
        "null_me": ratio_m_e
    },
    "hits_m_tau": hits_tau,
    "hits_m_kink": hits_kink,
    "null_hits_me": hits_me,
    "elapsed_s": elapsed
}

import pathlib as _pl
_out = str(_pl.Path(__file__).resolve().parent / "gte_g_hierarchy_scan_results.json")
with open(_out, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to {_out}")
signal.alarm(0)
