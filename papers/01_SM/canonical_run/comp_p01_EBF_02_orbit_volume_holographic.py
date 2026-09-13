#!/usr/bin/env python3
"""
comp_p01_EBF_02_orbit_volume_holographic.py
EPIC 8 — E_base Foundations, Sub-project B, Computation 2

QUESTION:
    Does the GTE orbit volume — |a·b·c|, |det M|, log-scale combinations,
    or RSUC-invariant products — function as the correct holographic quantity
    mapping GTE triples to particle masses?

    The naive Bekenstein bridge used N_eff = |b| and failed catastrophically
    (lepton order wrong, ratios off by orders of magnitude).  This script
    tests whether a MORE GENERAL function of the triple (beyond just |b|) can
    reproduce:
      (i)  the correct mass ordering: m_e < m_u < m_d < m_s < m_c < m_b < m_t
           (quarks) and m_e < m_mu < m_tau (leptons)
      (ii) the inter-generational R_g = E_base_g / E_base_electron ratios to
           better than the Bekenstein bridge.

TRIPLES (canonical):
    Lepton:    e=(1,73,823), μ=(9,42,1023), τ=(5,275,65535)
    Up quarks: u=(5,9,275),  c=(5,275,65535), t=(76,337920,-1)
    Down quarks: d=(9,5,42), s=(9,186,1023), b=(5,8191,65535)

ORBIT INVARIANTS TESTED:
    - |a|, |b|, |c|
    - a+b+c, |a·b·c|
    - log|c|, log|b|, log|a·b·c|
    - (a+b)·c, a·(b+c)
    - |c - b|, |c - a|, c/b (where defined)
    - Möbius: μ(a)·μ(b)·μ(c) (already in UCL; include for completeness)
    - RSUC invariants: N_eff = a+b+c, L = log(|b|/|c|), L^2
    - det of generation matrix (per lepton/up/down sector)

VERDICT CRITERION:
    SUCCESS:     a single invariant reproduces all 9 R_g ratios within 10%.
    PARTIAL:     reproduces correct mass ordering AND some sector within 10%.
    INFORMATIVE: correct mass ordering but wrong ratio magnitudes (useful data).
    FAIL:        wrong mass ordering or all > 50% off.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from typing import Dict, List

# ────────────────────────────────────────────────────────────────────────────
# 1. Canonical GTE triples and PDG masses
# ────────────────────────────────────────────────────────────────────────────

PARTICLES = [
    # name, type, gen,  a,       b,       c,        m_MeV
    ("electron", "lepton",    1,  1,       73,      823,      0.51099895),
    ("muon",     "lepton",    2,  9,       42,      1023,     105.6583755),
    ("tau",      "lepton",    3,  5,       275,     65535,    1776.86),
    ("up",       "up_type",   1,  5,       9,       275,      2.16),
    ("charm",    "up_type",   2,  5,       275,     65535,    1275.0),
    ("top",      "up_type",   3,  76,      337920,  -1,       172760.0),
    ("down",     "down_type", 1,  9,       5,       42,       4.67),
    ("strange",  "down_type", 2,  9,       186,     1023,     93.4),
    ("bottom",   "down_type", 3,  5,       8191,    65535,    4180.0),
]

# Reference particle: electron
M_ELECTRON = 0.51099895  # MeV

# ────────────────────────────────────────────────────────────────────────────
# 2. GTE generation matrices per sector (for det computation)
# ────────────────────────────────────────────────────────────────────────────

def det3(rows):
    """3x3 determinant."""
    (a1,b1,c1),(a2,b2,c2),(a3,b3,c3) = rows
    return (a1*(b2*c3 - b3*c2)
          - b1*(a2*c3 - a3*c2)
          + c1*(a2*b3 - a3*b2))

LEPTON_MATRIX    = [(1,73,823),(9,42,1023),(5,275,65535)]
UP_MATRIX        = [(5,9,275),(5,275,65535),(76,337920,-1)]
DOWN_MATRIX      = [(9,5,42),(9,186,1023),(5,8191,65535)]

DET_LEPTON  = det3(LEPTON_MATRIX)
DET_UP      = det3(UP_MATRIX)
DET_DOWN    = det3(DOWN_MATRIX)

# ────────────────────────────────────────────────────────────────────────────
# 3. Orbit invariant functions
# ────────────────────────────────────────────────────────────────────────────

def mobius_mu(n: int) -> int:
    n = abs(n)
    if n == 0: return 0
    if n == 1: return 1
    out = 1; p = 2
    while p * p <= n:
        if n % p == 0:
            cnt = 0
            while n % p == 0:
                n //= p; cnt += 1
            if cnt >= 2: return 0
            out = -out
        p += 1
    if n > 1: out = -out
    return out

def invariants(name, a, b, c):
    abs_a, abs_b, abs_c = abs(a), abs(b), abs(c)
    abc = abs_a * abs_b * abs_c
    ab = abs_a * abs_b
    bc = abs_b * abs_c
    ac = abs_a * abs_c

    log_c   = math.log(abs_c) if abs_c > 0 else 0.0
    log_b   = math.log(abs_b) if abs_b > 0 else 0.0
    log_a   = math.log(abs_a) if abs_a > 0 else 0.0
    log_abc = math.log(abc)   if abc > 0 else 0.0

    # L = log(|b/c|) — the UCL feature
    L    = math.log(abs_b / abs_c) if abs_c > 0 and abs_b > 0 else 0.0

    mu_prod = float(mobius_mu(a) * mobius_mu(b) * mobius_mu(c))

    return {
        # Raw triple components
        "|a|":          float(abs_a),
        "|b|":          float(abs_b),
        "|c|":          float(abs_c),
        "a+b+c":        float(abs_a + abs_b + abs_c),
        "|a*b*c|":      float(abc),
        "|a*b|":        float(ab),
        "|b*c|":        float(bc),
        "|a*c|":        float(ac),
        "a+b":          float(abs_a + abs_b),
        "b+c":          float(abs_b + abs_c),
        "|c-b|":        float(abs(abs_c - abs_b)),
        "|c-a|":        float(abs(abs_c - abs_a)),
        # Logarithmic
        "log|c|":       log_c,
        "log|b|":       log_b,
        "log|a|":       log_a,
        "log|a*b*c|":   log_abc,
        "log|b*c|":     math.log(bc) if bc > 0 else 0.0,
        "log|a*c|":     math.log(ac) if ac > 0 else 0.0,
        # UCL L-feature
        "L=log(b/c)":   L,
        "L^2":          L * L,
        # Ratios
        "c/b":          float(abs_c / abs_b) if abs_b > 0 else 0.0,
        "c/a":          float(abs_c / abs_a) if abs_a > 0 else 0.0,
        "b/a":          float(abs_b / abs_a) if abs_a > 0 else 0.0,
        "c/(a*b)":      float(abc / (ab * abs_a)) if ab > 0 else 0.0,
        "log(c/b)":     math.log(abs_c / abs_b) if abs_c > 0 and abs_b > 0 else 0.0,
        "log(c/a)":     math.log(abs_c / abs_a) if abs_c > 0 and abs_a > 0 else 0.0,
        # Möbius
        "mu(a)*mu(b)*mu(c)": mu_prod,
        # Powers
        "|b|^2":        float(abs_b ** 2),
        "|c|^(2/3)":    float(abs_c ** (2.0/3.0)) if abs_c > 0 else 0.0,
        "|a*b*c|^(1/3)": float(abc ** (1.0/3.0)) if abc > 0 else 0.0,
        "|a*b*c|^(1/2)": float(abc ** 0.5) if abc > 0 else 0.0,
        "log(|a*b*c|)^2": log_abc ** 2,
        "a^2*c":        float(abs_a**2 * abs_c),
        "b^2*c":        float(abs_b**2 * abs_c),
        "a*c^2":        float(abs_a * abs_c**2),
        # Information-capacity motivated: c+1 (Mersenne pattern)
        "c+1":          float(abs_c + 1),
        "log2(c+1)":    math.log2(abs_c + 1) if abs_c >= 0 else 0.0,
        "2^log2(c+1)":  float(abs_c + 1),  # same as c+1, kept for clarity
        # N_eff from RSUC
        "N_eff=a+b":    float(abs_a + abs_b),
        "N_eff=b":      float(abs_b),
    }

# ────────────────────────────────────────────────────────────────────────────
# 4. Compute all invariants for all particles
# ────────────────────────────────────────────────────────────────────────────

particle_data = []
for name, ptype, gen, a, b, c, m_MeV in PARTICLES:
    inv = invariants(name, a, b, c)
    R_g = m_MeV / M_ELECTRON  # actual mass ratio
    particle_data.append({
        "name": name, "type": ptype, "gen": gen,
        "a": a, "b": b, "c": c,
        "m_MeV": m_MeV, "R_g": R_g,
        "inv": inv,
    })

# ────────────────────────────────────────────────────────────────────────────
# 5. For each invariant, check:
#    (a) Does it give correct mass ordering?
#    (b) What power alpha makes m_g = (inv_g / inv_e)^alpha × m_e?
#        (only if ordering is correct)
#    (c) If alpha is consistent across all pairs, what is it?
# ────────────────────────────────────────────────────────────────────────────

ELECTRON = particle_data[0]
assert ELECTRON["name"] == "electron"

def check_invariant(key):
    vals = [(p["name"], p["inv"][key], p["R_g"]) for p in particle_data]
    # Order by invariant value
    vals_sorted_by_inv = sorted(vals, key=lambda x: x[1])
    names_by_inv = [v[0] for v in vals_sorted_by_inv]
    # Order by mass
    vals_sorted_by_mass = sorted(vals, key=lambda x: x[2])
    names_by_mass = [v[0] for v in vals_sorted_by_mass]
    # Check if orderings match
    ordering_match = (names_by_inv == names_by_mass)

    # For lepton sector: check if invariant ratio gives correct ordering
    leptons = [(p["name"], p["inv"][key], p["R_g"]) for p in particle_data if p["type"] == "lepton"]
    lepton_inv_order = sorted(leptons, key=lambda x: x[1])
    lepton_mass_order = sorted(leptons, key=lambda x: x[2])
    lepton_ordering_match = ([v[0] for v in lepton_inv_order] ==
                              [v[0] for v in lepton_mass_order])

    # Compute power alpha from each particle to electron
    inv_e = ELECTRON["inv"][key]
    R_e   = ELECTRON["R_g"]
    alphas = []
    for p in particle_data:
        if p["name"] == "electron":
            continue
        inv_p = p["inv"][key]
        R_p = p["R_g"]
        if inv_e <= 0 or inv_p <= 0 or inv_e == inv_p:
            alphas.append(None)
        else:
            try:
                alpha = math.log(R_p / R_e) / math.log(inv_p / inv_e)
                alphas.append(alpha)
            except (ValueError, ZeroDivisionError):
                alphas.append(None)

    valid_alphas = [a for a in alphas if a is not None]
    if valid_alphas:
        alpha_mean = sum(valid_alphas) / len(valid_alphas)
        alpha_std = math.sqrt(sum((a - alpha_mean)**2 for a in valid_alphas) / len(valid_alphas))
        alpha_cv = alpha_std / abs(alpha_mean) if alpha_mean != 0 else float('inf')
    else:
        alpha_mean = alpha_std = alpha_cv = None

    # Compute predicted R_g using mean alpha
    predicted_Rg = {}
    max_dev = 0.0
    if alpha_mean is not None:
        for p in particle_data:
            inv_p = p["inv"][key]
            if inv_e > 0 and inv_p > 0:
                pred = (inv_p / inv_e) ** alpha_mean
                dev = abs(pred - p["R_g"]) / p["R_g"]
                predicted_Rg[p["name"]] = {"pred": pred, "actual": p["R_g"], "dev_pct": dev*100}
                max_dev = max(max_dev, dev)

    return {
        "key": key,
        "lepton_ordering_correct": lepton_ordering_match,
        "all_ordering_correct": ordering_match,
        "alpha_mean": alpha_mean,
        "alpha_std": alpha_std,
        "alpha_cv": alpha_cv,
        "max_dev_pct": max_dev * 100 if max_dev > 0 else None,
        "predicted_Rg": predicted_Rg,
    }

inv_keys = list(particle_data[0]["inv"].keys())
results = [check_invariant(k) for k in inv_keys]

# Sort: first by lepton ordering correct, then by max_dev_pct
results_lepton_ok = [r for r in results if r["lepton_ordering_correct"]]
results_lepton_fail = [r for r in results if not r["lepton_ordering_correct"]]

results_lepton_ok.sort(key=lambda r: r.get("max_dev_pct") or 1e9)

# ────────────────────────────────────────────────────────────────────────────
# 6. Special: lepton sector analysis
# ────────────────────────────────────────────────────────────────────────────

print("=" * 72)
print("COMP-P01-EBF-02 — GTE Orbit Volume as Holographic Quantity")
print("=" * 72)
print("\nLepton triples:")
for p in particle_data[:3]:
    print(f"  {p['name']:10s}: (a={p['a']:2d}, b={p['b']:4d}, c={p['c']:6d}), "
          f"m={p['m_MeV']:.3f} MeV, R_g={p['R_g']:.3f}")

print("\nAll particles |a*b*c| values (orbit product):")
for p in particle_data:
    abc = p["inv"]["|a*b*c|"]
    print(f"  {p['name']:10s}: |abc|={abc:15,.0f}, m={p['m_MeV']:12.3f} MeV, R_g={p['R_g']:10.3f}")

print("\n--- LEPTON SECTOR: ordering analysis ---")
for key in ["lepton_ordering_correct"]:
    pass

# Print top invariants that get lepton ordering right
print(f"\nInvariants with correct lepton ordering ({len(results_lepton_ok)}/{len(results)} total):")
print(f"{'Key':>25}  {'AlphaMean':>10}  {'AlphaCV':>10}  {'MaxDev%':>10}  LeptonOK  AllOK")
print("-"*80)
for r in results_lepton_ok[:20]:
    alpha_s = f"{r['alpha_mean']:.3f}" if r['alpha_mean'] is not None else "N/A"
    cv_s = f"{r['alpha_cv']:.3f}" if r['alpha_cv'] is not None else "N/A"
    dev_s = f"{r['max_dev_pct']:.1f}" if r['max_dev_pct'] is not None else "N/A"
    print(f"  {r['key']:>25}  {alpha_s:>10}  {cv_s:>10}  {dev_s:>10}  "
          f"{'YES':8s}  {'YES' if r['all_ordering_correct'] else 'NO'}")

# ────────────────────────────────────────────────────────────────────────────
# 7. Focus analysis: log|a*b*c| — the orbit hypervolume in log scale
# ────────────────────────────────────────────────────────────────────────────

print("\n--- DEEP DIVE: log|a*b*c| orbit volume ---")
log_abc_res = check_invariant("log|a*b*c|")
print(f"Lepton ordering correct: {log_abc_res['lepton_ordering_correct']}")
print(f"All ordering correct:    {log_abc_res['all_ordering_correct']}")
if log_abc_res['alpha_mean']:
    print(f"Best-fit power alpha:    {log_abc_res['alpha_mean']:.4f} ± {log_abc_res['alpha_std']:.4f} (CV={log_abc_res['alpha_cv']:.3f})")
    print(f"Max deviation:           {log_abc_res['max_dev_pct']:.1f}%")
    print("\nPer-particle predictions under best-fit alpha:")
    print(f"  {'Particle':12s}  {'Predicted R_g':>15}  {'Actual R_g':>12}  {'Dev%':>8}")
    for name, vals in log_abc_res["predicted_Rg"].items():
        print(f"  {name:12s}  {vals['pred']:>15.3f}  {vals['actual']:>12.3f}  {vals['dev_pct']:>8.1f}%")

# ────────────────────────────────────────────────────────────────────────────
# 8. Focus: log|c| alone (monotone for leptons; c=log-information-capacity)
# ────────────────────────────────────────────────────────────────────────────

print("\n--- DEEP DIVE: log|c| ---")
log_c_res = check_invariant("log|c|")
print(f"Lepton ordering correct: {log_c_res['lepton_ordering_correct']}")
if log_c_res['alpha_mean']:
    print(f"Best-fit power alpha:    {log_c_res['alpha_mean']:.4f} ± {log_c_res['alpha_std']:.4f} (CV={log_c_res['alpha_cv']:.3f})")
    print(f"Max deviation:           {log_c_res['max_dev_pct']:.1f}%")
    # print lepton only
    print("\nLepton predictions only:")
    for name in ["electron","muon","tau"]:
        if name in log_c_res["predicted_Rg"]:
            v = log_c_res["predicted_Rg"][name]
            print(f"  {name:12s}: pred={v['pred']:.3f}  actual={v['actual']:.3f}  dev={v['dev_pct']:.1f}%")

# ────────────────────────────────────────────────────────────────────────────
# 9. Key ratio diagnostic: lepton mass ratios vs. triple-component ratios
# ────────────────────────────────────────────────────────────────────────────

print("\n--- LEPTON MASS RATIOS vs. TRIPLE-COMPONENT RATIOS ---")
e, mu, tau = particle_data[0], particle_data[1], particle_data[2]
print(f"m_mu/m_e = {mu['R_g']:.4f};  m_tau/m_e = {tau['R_g']:.4f};  m_tau/m_mu = {tau['m_MeV']/mu['m_MeV']:.4f}")
print()
for key in ["|a*b*c|", "log|a*b*c|", "log|c|", "|c|", "|b|", "c/b", "log2(c+1)"]:
    ve = e["inv"][key]; vmu = mu["inv"][key]; vtau = tau["inv"][key]
    print(f"  {key:>18s}: e={ve:12.3f}, mu={vmu:12.3f}, tau={vtau:12.3f}  "
          f"|  mu/e={vmu/ve if ve>0 else 'inf':.3f}, tau/e={vtau/ve if ve>0 else 'inf':.3f}")

# ────────────────────────────────────────────────────────────────────────────
# 10. Generation matrix determinants
# ────────────────────────────────────────────────────────────────────────────

print("\n--- GENERATION MATRIX DETERMINANTS ---")
print(f"  det(lepton matrix) = {DET_LEPTON:,d}")
print(f"  det(up_type matrix) = {DET_UP:,d}")
print(f"  det(down_type matrix) = {DET_DOWN:,d}")
print(f"  Ratios: up/lepton = {DET_UP/DET_LEPTON:.4f},  down/lepton = {DET_DOWN/DET_LEPTON:.4f}")

# ────────────────────────────────────────────────────────────────────────────
# 11. Build output JSON
# ────────────────────────────────────────────────────────────────────────────

# Find best invariant overall (lepton correct, min max_dev)
best = results_lepton_ok[0] if results_lepton_ok else None

if best and best["max_dev_pct"] is not None:
    if best["max_dev_pct"] < 10.0:
        verdict = (f"SUCCESS: '{best['key']}' gives correct lepton ordering AND "
                   f"all R_g within {best['max_dev_pct']:.1f}% under alpha={best['alpha_mean']:.3f}.")
    elif best["max_dev_pct"] < 50.0:
        verdict = (f"INFORMATIVE: '{best['key']}' gives correct lepton ordering "
                   f"but R_g deviations reach {best['max_dev_pct']:.1f}% (not < 10%). "
                   f"Orbit volume gives correct ORDER but wrong RATIOS.")
    else:
        verdict = f"FAIL: best matching invariant still has {best['max_dev_pct']:.1f}% max deviation."
else:
    verdict = "FAIL: no invariant gives correct lepton ordering."

lepton_correct_keys = [r["key"] for r in results_lepton_ok]
lepton_wrong_keys   = [r["key"] for r in results_lepton_fail]

output = {
    "experiment_id": "COMP-P01-EBF-02",
    "epic": "EPIC_8_EBASE_FOUNDATIONS",
    "question": "Does GTE orbit volume (|a*b*c| or variants) function as holographic quantity?",
    "lepton_triples": {
        "electron": {"a":1,"b":73,"c":823,"m_MeV":0.511},
        "muon":     {"a":9,"b":42,"c":1023,"m_MeV":105.66},
        "tau":      {"a":5,"b":275,"c":65535,"m_MeV":1776.86},
    },
    "generation_matrix_dets": {
        "lepton": DET_LEPTON,
        "up_type": DET_UP,
        "down_type": DET_DOWN,
    },
    "n_invariants_tested": len(inv_keys),
    "n_with_correct_lepton_ordering": len(results_lepton_ok),
    "n_with_correct_all_ordering": sum(1 for r in results if r["all_ordering_correct"]),
    "best_invariant_lepton_sector": best,
    "top10_lepton_ok": [
        {k: v for k, v in r.items() if k != "predicted_Rg"}
        for r in results_lepton_ok[:10]
    ],
    "lepton_ordering_CORRECT_keys": lepton_correct_keys,
    "lepton_ordering_WRONG_keys":   lepton_wrong_keys,
    "verdict": verdict,
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
}

sha = hashlib.sha256(json.dumps({k: output[k] for k in output if k != "timestamp_utc"},
                                sort_keys=True).encode()).hexdigest()
output["sha256"] = sha

out_path = "comp_p01_EBF_02_orbit_volume_holographic.json"
with open(out_path, "w") as f:
    json.dump(output, f, indent=2, default=str)

print(f"\n\nVERDICT: {verdict}")
print(f"\nResults written to {out_path}")
