#!/usr/bin/env python3
"""
lepton_mass_neff_cascade.py — Charged-lepton mass hierarchy from the GTE N_eff cascade.

Investigates whether the charged-lepton mass ratios
    m_e : m_mu : m_tau = 1 : 206.77 : 3477.2
can be derived from the GTE generation structure (N_eff = |b| cascade values,
c-value branch capacities, Z_7 algebraic factors, generation index) without using
the measured masses as inputs.

Context (established results that any cascade must be consistent with):
  - GTE canonical triples (P01): e=(1,73,823), mu=(9,42,1023), tau=(5,275,65535).
    N_eff = |b|: N_eff(e)=73, N_eff(mu)=42, N_eff(tau)=275 (non-monotonic).
  - Koide relation Q=(sum m)/(sum sqrt m)^2 = 2/3 with phase theta=2/9=(N_c^2-1)/(4N_c^2)
    from N_c=3 (Lean-certified, P01).
  - Koide cyclotomic-12 closed form predicts m_tau from (m_e,m_mu) to 61 ppm (P01).
  - Direct cogwheel eigenvalue E_k ~ mass FAILS by >10^4% (P37 eigenvalue_mass_correspondence.py).

Pass criterion (gap-closure-pipeline rule): a SINGLE exponent alpha plus a SIMPLE
Z_7/GTE algebraic factor reproducing BOTH log-ratios to <10%, surviving a wrong-target
null (same form on a different ratio) and a neighbor-atom null (perturbed exponents).

Expected output: prints all hypothesis tests; writes lepton_mass_neff_cascade_results.json.
The honest expected outcome is that NO single-alpha N_eff power-law cascade works (the
b-values are non-monotonic), and that the established Koide closed form remains the
operative Level-2 lepton-mass content.
"""

import json
import math
import os
import signal
import sys
import itertools

TIMEOUT_SECONDS = 120


def _timeout(signum, frame):
    print(f"\nTIMEOUT: {TIMEOUT_SECONDS}s wall-clock limit reached. Exiting.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PHI = (1 + math.sqrt(5)) / 2

# PDG charged-lepton masses (MeV)
M = {"e": 0.51099895, "mu": 105.6583755, "tau": 1776.86}

# GTE canonical triples (a, b, c); N_eff = |b|
TRIP = {"e": (1, 73, 823), "mu": (9, 42, 1023), "tau": (5, 275, 65535)}
B = {k: TRIP[k][1] for k in TRIP}
C = {k: TRIP[k][2] for k in TRIP}
A = {k: TRIP[k][0] for k in TRIP}
C_H = 13
N_GEN = 3
N_FAM = 5

GENS = ["e", "mu", "tau"]

results = {"constants": {"phi": PHI, "c_H": C_H, "N_gen": N_GEN, "N_fam": N_FAM},
           "triples": TRIP, "masses_MeV": M}


def factorint(n):
    n = abs(int(n))
    f = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            f[d] = f.get(d, 0) + 1
            n //= d
        d += 1 if d == 2 else 2
    if n > 1:
        f[n] = f.get(n, 0) + 1
    return f


# ---------------------------------------------------------------------------
# Observed ratios
# ---------------------------------------------------------------------------
r_mue = M["mu"] / M["e"]
r_taumu = M["tau"] / M["mu"]
r_taue = M["tau"] / M["e"]
ln_mue = math.log(r_mue)
ln_taumu = math.log(r_taumu)
ln_taue = math.log(r_taue)

results["observed"] = {
    "m_mu/m_e": r_mue, "m_tau/m_mu": r_taumu, "m_tau/m_e": r_taue,
    "ln(m_mu/m_e)": ln_mue, "ln(m_tau/m_mu)": ln_taumu, "ln(m_tau/m_e)": ln_taue,
}

# ---------------------------------------------------------------------------
# T0: InformationMassTransformer sanity check (documented; module lives outside
# this repo at the Particle Derivations tree). The transformer is a CALIBRATION
# model, not a first-principles derivation: it hardcodes the target lepton masses
# in phase_energy_scales={1:0.511,2:105.66,3:1776.86}, a generation_scaling table
# {1:0.01,2:1.0,3:10.0}, and a 9-parameter log-space "universal calibration law".
# Reproduction command (run 2026-05-29):
#   cd ".../Optimizer new tests/OPTIMIZER" && python3 -c "<import IMT>; \
#   t.information_to_mass(N_eff, gen, 'lepton', particle_name, a, c)"
# Result with canonical triples e=(1,73,823), mu=(9,42,1023), tau=(5,275,65535):
#   electron 0.0493 MeV (PDG 0.511, 90.4% err)
#   muon     61.06  MeV (PDG 105.66, 42.2% err)
#   tau      27891  MeV (PDG 1776.86, 1470% err)
# VERDICT: SANITY CHECK FAILED. The IMT does not reproduce charged-lepton masses
# from the canonical triples and is internally circular (masses hardcoded). It is
# unusable as a derivation for G8 (per understand-code-before-using.mdc -> STOP).
# ---------------------------------------------------------------------------
results["T0_information_mass_transformer"] = {
    "sanity_check": "FAILED",
    "predicted_MeV": {"electron": 0.0493, "muon": 61.063, "tau": 27891.59},
    "pdg_MeV": {"electron": 0.511, "muon": 105.66, "tau": 1776.86},
    "rel_err_pct": {"electron": 90.4, "muon": 42.2, "tau": 1469.7},
    "circular_inputs": {
        "phase_energy_scales": {"1": 0.511, "2": 105.66, "3": 1776.86},
        "generation_scaling": {"1": 0.01, "2": 1.0, "3": 10.0},
        "calibration_law": "9-parameter log-space fit (CR1 Mobius law)",
    },
    "verdict": "Unusable for G8: fails sanity check AND hardcodes target masses.",
}

print("=" * 72)
print("T0: InformationMassTransformer SANITY CHECK -> FAILED (errors 90/42/1470%);")
print("    model hardcodes target masses + 9-param fitted law. Unusable for G8.")
print("=" * 72)
print("OBSERVED CHARGED-LEPTON MASS RATIOS")
print("=" * 72)
print(f"  m_mu/m_e   = {r_mue:.4f}   ln = {ln_mue:.4f}")
print(f"  m_tau/m_mu = {r_taumu:.4f}    ln = {ln_taumu:.4f}")
print(f"  m_tau/m_e  = {r_taue:.4f}  ln = {ln_taue:.4f}")

# ---------------------------------------------------------------------------
# T1: Single-alpha N_eff power-law cascade test
#   m_(k+1)/m_k = (N_eff(k)/N_eff(k+1))^alpha * f_k
# If f_k were 1, a single alpha must satisfy both steps. Test feasibility.
# ---------------------------------------------------------------------------
print("\n" + "=" * 72)
print("T1: SINGLE-ALPHA N_eff POWER-LAW CASCADE (f_k = 1)")
print("=" * 72)
# Step ratios of N_eff
s1 = B["e"] / B["mu"]      # 73/42
s2 = B["mu"] / B["tau"]    # 42/275
# alpha from step 1 alone (f=1): alpha1 = ln(r_mue)/ln(s1)
alpha1 = ln_mue / math.log(s1)
alpha2 = ln_taumu / math.log(s2)
print(f"  N_eff step ratios: s1=73/42={s1:.4f}, s2=42/275={s2:.4f}")
print(f"  alpha from e->mu  (f=1): {alpha1:.4f}")
print(f"  alpha from mu->tau (f=1): {alpha2:.4f}")
print(f"  Consistent single alpha? {'YES' if abs(alpha1-alpha2)/abs(alpha1) < 0.1 else 'NO'} "
      f"(differ by {abs(alpha1-alpha2)/abs(alpha1)*100:.0f}%)")
# Note: s2 < 1 (N_eff increases e->tau across step 2) while s1 > 1, so even the SIGN
# of alpha needed flips between steps. No single alpha works with f=1.
t1_pass = abs(alpha1 - alpha2) / abs(alpha1) < 0.1
results["T1_single_alpha_Neff"] = {
    "alpha_step1": alpha1, "alpha_step2": alpha2,
    "consistent": bool(t1_pass),
    "note": "N_eff non-monotonic (73->42->275): step-1 needs alpha>0, step-2 needs alpha<0; no single power law.",
}

# ---------------------------------------------------------------------------
# T1b: c-value (branch capacity) power law (monotonic 823<1023<65535)
# ---------------------------------------------------------------------------
print("\n" + "-" * 72)
print("T1b: c-VALUE (branch capacity) POWER LAW  m ~ c^p")
print("-" * 72)
p1 = ln_mue / math.log(C["mu"] / C["e"])
p2 = ln_taumu / math.log(C["tau"] / C["mu"])
print(f"  p from e->mu : {p1:.4f}  (c: 823->1023)")
print(f"  p from mu->tau: {p2:.4f}  (c: 1023->65535)")
print(f"  Consistent single p? {'YES' if abs(p1-p2)/abs(p1) < 0.1 else 'NO'}")
results["T1b_cvalue_power"] = {"p_step1": p1, "p_step2": p2,
                               "consistent": bool(abs(p1 - p2) / abs(p1) < 0.1)}

# ---------------------------------------------------------------------------
# T2: Disciplined GTE-atom scan for the INDEPENDENT target m_mu/m_e
#   (Koide closed form already fixes m_tau given m_e, m_mu, so m_mu/m_e is the
#    one genuinely free ratio. Search small integer combinations of GTE atoms.)
#   Null discipline: report wrong-target hits (against m_tau/m_mu) for the SAME
#   grammar to estimate chance-match volume.
# ---------------------------------------------------------------------------
print("\n" + "=" * 72)
print("T2: DISCIPLINED GTE-ATOM SCAN FOR m_mu/m_e = 206.77  (Koide fixes m_tau)")
print("=" * 72)

# GTE atom pool (certified integers/role-quantities only)
ATOMS = {
    "73": 73, "42": 42, "275": 275, "823": 823, "1023": 1023, "65535": 65535,
    "c_H=13": 13, "N_gen=3": 3, "N_fam=5": 5, "7": 7, "49": 49,
    "a_e=1": 1, "a_mu=9": 9, "a_tau=5": 5,
}
atom_items = list(ATOMS.items())

TARGET = r_mue          # 206.7683
WRONG = r_taumu         # 16.817  (wrong-target null)
TOL = 0.10              # 10%

def scan(target, tol):
    """Scan ratios atom_i/atom_j * small_int and atom_i * atom_j for matches."""
    hits = []
    small = [1, 2, 3, 5, 7]
    for (ni, vi) in atom_items:
        for (nj, vj) in atom_items:
            if vj == 0:
                continue
            for s in small:
                for expr, val in (
                    (f"{ni}/{nj}*{s}", vi / vj * s),
                    (f"{ni}*{nj}/{s}", vi * vj / s),
                ):
                    if val <= 0:
                        continue
                    rel = abs(val - target) / target
                    if rel < tol:
                        hits.append((rel, expr, val))
    hits.sort()
    return hits

hits_target = scan(TARGET, TOL)
hits_wrong = scan(WRONG, TOL)
print(f"  Target m_mu/m_e={TARGET:.3f}: {len(hits_target)} hits < {TOL*100:.0f}%")
for rel, expr, val in hits_target[:8]:
    print(f"     {expr:>18} = {val:9.3f}   rel={rel*100:5.2f}%")
print(f"  Wrong-target null m_tau/m_mu={WRONG:.3f}: {len(hits_wrong)} hits < {TOL*100:.0f}%")
print(f"  -> Chance-match volume: a grammar that yields >=O(10) hits per target is "
      f"numerology, not derivation.")
results["T2_scan"] = {
    "target_m_mu/m_e": TARGET,
    "n_hits_target": len(hits_target),
    "top_target_hits": [{"expr": e, "val": v, "rel": r} for r, e, v in hits_target[:10]],
    "n_hits_wrong_null": len(hits_wrong),
}

# ---------------------------------------------------------------------------
# T3: Z_7 / GTE algebraic factor tests for m_mu/m_e directly
# ---------------------------------------------------------------------------
print("\n" + "=" * 72)
print("T3: NAMED Z_7 / GTE ALGEBRAIC CANDIDATES FOR m_mu/m_e")
print("=" * 72)
cand = {
    "275-73 (b_tau - b_e)": 275 - 73,
    "c_H^2 + N_fam (169+5)": 13**2 + 5,
    "c_H^2 + ... 13^2": 13**2,
    "3*49 + ... 7^2*3": 3 * 49,
    "42*5 (b_mu*a_tau)": 42 * 5,
    "N_gen^5 (3^5)": 3**5,
    "2*c_H*N_fam+... ": 2 * 13 * 5,
    "phi^11": PHI**11,
}
for name, val in cand.items():
    rel = abs(val - TARGET) / TARGET
    flag = "  <-- <10%" if rel < 0.10 else ""
    print(f"  {name:>28} = {val:9.3f}   rel={rel*100:6.2f}%{flag}")
results["T3_named_candidates"] = {k: {"val": v, "rel": abs(v - TARGET) / TARGET}
                                  for k, v in cand.items()}

# ---------------------------------------------------------------------------
# T4: SM thermal N_eff at each lepton threshold (EXTERNAL physics, for completeness)
#   Standard relativistic dof g_* = g_bosons + 7/8 * g_fermions in the bath when T~m_k.
# ---------------------------------------------------------------------------
print("\n" + "=" * 72)
print("T4: SM THERMAL g_* AT EACH LEPTON THRESHOLD (external SM counting)")
print("=" * 72)
# Active relativistic species when T ~ m_lepton (rough standard counting):
#   photon(2) + 3 neutrinos(2 each, but fermion factor) etc.
# We use canonical g_* values from the SM thermal history at the relevant scales.
# At T~m_tau (~1.78 GeV): below charm threshold-ish; g_* ~ 69 (PDG/Kolb-Turner band)
# At T~m_mu (~106 MeV): just above muon; g_* ~ 14.25
# At T~m_e (~0.5 MeV): photon + e + nu; g_* ~ 10.75
gstar = {"tau": 69.0, "mu": 14.25, "e": 10.75}
print(f"  g_*(tau)~{gstar['tau']}, g_*(mu)~{gstar['mu']}, g_*(e)~{gstar['e']}")
# Test alpha for (g_*(k)/g_*(k+1))^alpha vs mass ratios
gr1 = gstar["mu"] / gstar["e"]
gr2 = gstar["tau"] / gstar["mu"]
a_g1 = ln_mue / math.log(gr1)
a_g2 = ln_taumu / math.log(gr2)
print(f"  alpha from e->mu  (g_* ratio {gr1:.3f}): {a_g1:.4f}")
print(f"  alpha from mu->tau (g_* ratio {gr2:.3f}): {a_g2:.4f}")
print(f"  Consistent single alpha? {'YES' if abs(a_g1-a_g2)/abs(a_g1) < 0.1 else 'NO'}")
results["T4_SM_thermal"] = {"gstar": gstar, "alpha_step1": a_g1, "alpha_step2": a_g2,
                            "consistent": bool(abs(a_g1 - a_g2) / abs(a_g1) < 0.1),
                            "note": "external SM thermal counting, not a GTE atom; reported for completeness"}

# ---------------------------------------------------------------------------
# T5: Koide consistency (established) — the operative L2 content
# ---------------------------------------------------------------------------
print("\n" + "=" * 72)
print("T5: KOIDE RELATION (established Lean-certified result)")
print("=" * 72)
se, smu, st = (math.sqrt(M[k]) for k in ("e", "mu", "tau"))
Q = (M["e"] + M["mu"] + M["tau"]) / (se + smu + st) ** 2
pred_st = 2 * (se + smu) + math.sqrt(3) * math.sqrt(M["e"] + 4 * math.sqrt(M["e"] * M["mu"]) + M["mu"])
m_tau_pred = pred_st ** 2
print(f"  Q = {Q:.6f}  (target 2/3 = {2/3:.6f})")
print(f"  Koide phase theta = 2/9 = (N_c^2-1)/(4 N_c^2), N_c=3")
print(f"  cyclotomic-12 closed form: m_tau(from m_e,m_mu) = {m_tau_pred:.4f} MeV "
      f"(PDG {M['tau']:.2f}, {abs(m_tau_pred-M['tau'])/M['tau']*1e6:.0f} ppm)")
results["T5_koide"] = {"Q": Q, "Q_target": 2/3,
                       "m_tau_predicted": m_tau_pred, "m_tau_pdg": M["tau"],
                       "ppm_error": abs(m_tau_pred - M["tau"]) / M["tau"] * 1e6}

# ---------------------------------------------------------------------------
# T6: Winding-sector (SCC) test — are the generations topologically distinct?
#   P46 (Lepton-W universality): all three charged lepton generations share w=4.
#   A BPS kink mass in the Z_7 sine-Gordon potential depends only on the winding
#   (topological charge). Equal winding => equal topological kink mass. Hence the
#   hierarchy CANNOT come from the winding number; it must be an INTERNAL
#   excitation/cascade spectrum at fixed topological sector w=4.
# ---------------------------------------------------------------------------
print("\n" + "=" * 72)
print("T6: WINDING-SECTOR (SCC) TEST")
print("=" * 72)
lepton_winding = {"e": 4, "mu": 4, "tau": 4}
print(f"  Charged-lepton windings (P46): {lepton_winding}")
print("  All three generations share w=4 => identical BPS topological kink mass.")
print("  => The mass hierarchy is NOT topological. It must be an internal")
print("     excitation/cascade spectrum at fixed winding (e.g. breather/bound-state)")
print("     indexed by the GTE cascade triple, not by the topological charge.")
results["T6_winding_sector"] = {
    "lepton_winding": lepton_winding,
    "all_share_w4": True,
    "implication": "hierarchy is non-topological; internal excitation spectrum at fixed w=4 (Session-2 target)",
}

# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------
print("\n" + "=" * 72)
print("VERDICT")
print("=" * 72)
verdict = {
    "single_alpha_Neff_cascade_works": bool(t1_pass),
    "cvalue_power_law_works": results["T1b_cvalue_power"]["consistent"],
    "SM_thermal_cascade_works": results["T4_SM_thermal"]["consistent"],
    "koide_holds": abs(Q - 2/3) < 1e-3,
}
for k, v in verdict.items():
    print(f"  {k}: {v}")
results["verdict"] = verdict

signal.alarm(0)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "lepton_mass_neff_cascade_results.json")
with open(out, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nWrote {out}")
