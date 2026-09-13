"""Quark-sector Koide b^2 — GTE / Z7 mechanism search (negative result).

Companion to ``quark_koide_analysis.py``. That script established that the
quark sectors do not satisfy the lepton Koide value Q = 2/3:

    b^2 = 2(3Q - 1):   b2_lep = 2.000 (exact),
                        b2_up  = 3.094 (u,c,t, Z7 winding w=2),
                        b2_down = 2.389 (d,s,b, Z7 winding w=6).

This script searches for a first-principles GTE/Z7 closed form for the quark
b^2 deviations and documents that none survives the null tests. The candidate
mechanisms examined and their verdicts:

  1. Product hypothesis b2_up * b2_down = |Z7| = 7  -> 5.6% off, rejected.
  2. Z7-potential scaling b2(w) = 2 V(w)/V(4),
     V(w) = 1 - cos(2 pi w / 7) (the unique normalization that fixes the
     lepton value at w=4) -> -58% / -83%, rejected.
  3. Additive form 2 + V(w) -> fails the lepton sector consistency check
     (gives 3.90 at w=4, not 2), rejected.
  4. Bounded GTE-atom grammar scan -> the up sector has no hit below 1.5%,
     and an arbitrary control target receives MORE near-hits than the physical
     targets, i.e. the grammar is rich enough to fit anything (numerology),
     rejected.
  5. Log-mass-hierarchy correlation -> broken by the leptons, which carry the
     second-largest hierarchy yet have b^2 exactly 2, rejected.

Conclusion: there is no GTE-derivable closed form for the quark b^2. The Koide
amplitude b^2 is a reparametrization of the Yukawa eigenvalues; for the quark
sectors, whose generation S3 is broken by CKM mixing, b^2 is fixed by the full
Yukawa eigenvalue structure and is not a simple function of the Z7 winding.

PDG 2024 inputs (GeV): light quarks MS-bar at 2 GeV, heavy quarks MS-bar at m_q.
"""

import itertools
import json
import math
import os

import numpy as np

# --- PDG 2024 inputs (GeV) ---------------------------------------------------
m_u, m_c, m_t = 2.16e-3, 1.27, 172.69
m_d, m_s, m_b = 4.67e-3, 93.4e-3, 4.18
m_e, m_mu, m_tau = 0.511e-3, 105.658e-3, 1776.86e-3

# --- GTE / group-theory constants -------------------------------------------
w_up, w_down, w_lep, w_nu = 2, 6, 4, 0
N_c, C_F, N_gen, Z7 = 3, 4.0 / 3.0, 3, 7


def koide_Q(m1, m2, m3):
    s = math.sqrt(m1) + math.sqrt(m2) + math.sqrt(m3)
    return (m1 + m2 + m3) / s ** 2


def b2_from_Q(Q):
    return 2 * (3 * Q - 1)


def z7_potential(w):
    return 1 - math.cos(2 * math.pi * w / 7)


b2_lep = b2_from_Q(koide_Q(m_e, m_mu, m_tau))
b2_up = b2_from_Q(koide_Q(m_u, m_c, m_t))
b2_down = b2_from_Q(koide_Q(m_d, m_s, m_b))

results = {"targets": {"b2_lep": b2_lep, "b2_up": b2_up, "b2_down": b2_down},
           "windings": {"up": w_up, "down": w_down, "lep": w_lep}}

print("=" * 70)
print("TARGETS  (b^2 = 2(3Q-1), PDG 2024)")
print("=" * 70)
print(f"b2_lep  = {b2_lep:.5f}  (exact, CatAD)")
print(f"b2_up   = {b2_up:.5f}  (w=2)")
print(f"b2_down = {b2_down:.5f}  (w=6)")

# --- mechanism 1: product hypothesis ----------------------------------------
prod = b2_up * b2_down
results["product_hypothesis"] = {"value": prod, "target": 7,
                                 "dev_pct": (prod - 7) / 7 * 100}
print("\n[1] PRODUCT b2_up*b2_down vs |Z7|=7")
print(f"    {prod:.5f}  dev {(prod-7)/7*100:+.3f}%  -> REJECT")

# --- mechanism 2 & 3: Z7-potential forms (sector consistency required) -------
V_lep = z7_potential(w_lep)
scaling = {w: 2 * z7_potential(w) / V_lep for w in (w_lep, w_up, w_down)}
additive = {w: 2 + z7_potential(w) for w in (w_lep, w_up, w_down)}
results["z7_potential"] = {
    "scaling_2V_over_Vlep": {"lep": scaling[w_lep], "up": scaling[w_up],
                             "down": scaling[w_down]},
    "additive_2_plus_V": {"lep": additive[w_lep], "up": additive[w_up],
                          "down": additive[w_down]},
}
print("\n[2] Z7-potential scaling 2*V(w)/V(4)  (fixes lepton=2 by construction)")
print(f"    up   = {scaling[w_up]:.4f}  dev {(scaling[w_up]-b2_up)/b2_up*100:+.1f}%")
print(f"    down = {scaling[w_down]:.4f}  dev {(scaling[w_down]-b2_down)/b2_down*100:+.1f}%  -> REJECT")
print("\n[3] Additive 2 + V(w)  (lepton consistency check)")
print(f"    lep  = {additive[w_lep]:.4f}  (must be 2.0)  -> FAILS lepton -> REJECT")

# --- mechanism 4: bounded GTE-atom grammar scan + null test -----------------
def scan(target, w, label, thr=1.5):
    atoms = {"1": 1, "2": 2, "3": 3, "N_c": 3, "7": 7, "C_F": C_F,
             "N_gen": 3, "5": 5, f"w({label})": w}
    names = list(atoms)
    vals = [atoms[n] for n in names]
    hits = []
    for A in (0, 1, 2, 3):
        for bi, ci in itertools.product(range(len(vals)), repeat=2):
            B, C = vals[bi], vals[ci]
            if C == 0:
                continue
            for form, expr in (("+", A + B / C),
                               ("*/", A * B / C if A else B / C)):
                err = (expr - target) / target * 100
                if abs(err) < thr:
                    desc = (f"{A}+{names[bi]}/{names[ci]}" if form == "+"
                            else f"{A}*{names[bi]}/{names[ci]}")
                    hits.append((abs(err), desc, expr, err))
    hits.sort()
    return hits


hits_up = scan(b2_up, w_up, "up")
hits_down = scan(b2_down, w_down, "down")
hits_null = scan(2.70, 5, "null")   # arbitrary control target
results["grammar_scan"] = {
    "up_hits_lt_1.5pct": len(hits_up),
    "down_hits_lt_1.5pct": len(hits_down),
    "null_target_2.70_hits": len(hits_null),
    "down_best": [h[1:] for h in hits_down[:3]],
}
print("\n[4] Bounded GTE-atom grammar scan (null test)")
print(f"    up hits <1.5%   = {len(hits_up)}")
print(f"    down hits <1.5% = {len(hits_down)}  (best: "
      f"{hits_down[0][1] if hits_down else 'none'})")
print(f"    NULL target 2.70 hits = {len(hits_null)}  "
      f"-> null >= signal => numerology -> REJECT")

# --- mechanism 5: log-hierarchy correlation ---------------------------------
hier = [("lep", b2_lep - 2, math.log(m_tau / m_e)),
        ("up", b2_up - 2, math.log(m_t / m_u)),
        ("down", b2_down - 2, math.log(m_b / m_d))]
results["hierarchy"] = {lab: {"db2": db, "log_span": h} for lab, db, h in hier}
print("\n[5] db^2 vs log-mass-hierarchy")
for lab, db, h in hier:
    print(f"    {lab:4s}: db2={db:+.4f}  log-span={h:.3f}")
print("    leptons: largest-but-one span yet db2=0 -> no single-slope law -> REJECT")

# --- verdict -----------------------------------------------------------------
results["verdict"] = ("NO GTE-derivable closed form for quark b^2. All five "
                      "candidate mechanisms rejected (product 5.6% off; Z7 "
                      "scaling -58/-83%; additive fails lepton; grammar scan "
                      "numerological null>signal; hierarchy broken by leptons).")
print("\n" + "=" * 70)
print("VERDICT: " + results["verdict"])
print("=" * 70)

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "quark_koide_z7_analysis_results.json")
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"Artifact written: {out_path}")
