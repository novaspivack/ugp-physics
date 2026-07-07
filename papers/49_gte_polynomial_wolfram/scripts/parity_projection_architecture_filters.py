#!/usr/bin/env python3
"""
Architecture-filter autopsy for the parity-projection battery's FORCED +
shadow-closed non-parity exceptions.

Loads the exceptions recorded by parity_projection_homomorphism_battery.py
(Tier 1: the two leaky homomorphism cases, re-derived here) and
parity_projection_local_function_battery.py (Tier 2: all SCC-closed
factorization violations), and tests each forced rule against two
pre-existing certified architectural criteria -- applied as filters, with
the parity survivors run as positive controls first:

  F1 (unique vacuum): the rule's homogeneous fixed points r(x,x,x) = x over
     GF(7) must be {0} -- the displaced-vacuum exclusion used to remove
     GF(5) in the modulus chain (`vacuum_unique_fixed_point_z7` for p).
  F2 (gen1 Garden-of-Eden): the shadow's gen1 vector has no predecessor on
     the 5-ring (tested both within the shadow alphabet and over the full
     GF(7) alphabet).  Reported only if the parity controls themselves pass
     it; the certified GoE statement is for f_MDL on the Z7 orbit, so this
     filter must EARN its applicability on the shadow level.

Artifact: parity_projection_architecture_filters_results.json
"""

import itertools
import json
import os
import signal
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))

TIMEOUT_SECONDS = 900


def _t(signum, frame):
    print(f"TIMEOUT: {TIMEOUT_SECONDS}s limit reached.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _t)
signal.alarm(TIMEOUT_SECONDS)

MONOMIALS = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1),
             (1, 1, 0), (1, 0, 1), (0, 1, 1), (1, 1, 1)]
TRIPLES = {
    "e":   [(1, 73, 823), (9, 42, 1023), (5, 275, 65535)],
    "u":   [(5, 9, 275), (5, 275, 65535), (76, 337920, -1)],
    "d":   [(9, 5, 42), (9, 186, 1023), (5, 8191, 65535)],
    "nuR": [(2, 5, 5), (7, 11, 13), (17, 19, 23)],
    "nuL": [(1, 1, 823), (9, 1, 1023), (5, 1, 65535)],
}
ORDER = ["e", "u", "d", "nuR", "nuL"]


def eval_rule(coeffs, L, C, R):
    return sum(c * pow(L, e[0], 7) * pow(C, e[1], 7) * pow(R, e[2], 7)
               for e, c in zip(MONOMIALS, coeffs)) % 7


def diagonal_fixed_points(coeffs):
    return [x for x in range(7)
            if eval_rule(coeffs, x, x, x) == x]


def has_predecessor(coeffs, target, alphabet):
    for x in itertools.product(alphabet, repeat=5):
        if all(eval_rule(coeffs, x[(i - 1) % 5], x[i], x[(i + 1) % 5])
               == target[i] for i in range(5)):
            return True
    return False


def pattern_setup(m):
    pos_pat = []
    for g in range(3):
        for f in ORDER:
            a, b, c = TRIPLES[f][g]
            pos_pat.append((a % m, b % m, c % m))
    pats = sorted(set(pos_pat))
    free = [p for p in pats if p != (0, 0, 0)]
    idx = [free.index(p) if p != (0, 0, 0) else -1 for p in pos_pat]
    return free, idx


def vecs_of(values, idx):
    flat = [0 if i < 0 else values[i] for i in idx]
    return [flat[0:5], flat[5:10], flat[10:15]]


def conjugates_of_p():
    P_COEFFS = [0, 0, 1, 1, 0, 0, 6, 6]
    conj = {}
    for t in range(1, 7):
        coeffs = []
        for (eL, eC, eR), c in zip(MONOMIALS, P_COEFFS):
            d = eL + eC + eR
            coeffs.append(c * pow(t, (1 - d) % 6, 7) % 7)
        conj[t] = coeffs
    return conj


results = {"controls": {}, "exceptions": [], "summary": {}}

# ---------------- positive controls: the parity survivors -----------------
PARITY = [[sum(TRIPLES[f][g]) % 2 for f in ORDER] for g in range(3)]
CONJ = conjugates_of_p()
for t, coeffs in CONJ.items():
    g1 = [t * PARITY[0][i] % 7 for i in range(5)]
    fp = diagonal_fixed_points(coeffs)
    goe_shadow = not has_predecessor(coeffs, g1, [0, t])
    goe_full = not has_predecessor(coeffs, g1, list(range(7)))
    results["controls"][t] = {"diag_fixed_points": fp,
                              "unique_vacuum": fp == [0],
                              "gen1_goe_within_shadow": goe_shadow,
                              "gen1_goe_full_gf7": goe_full}
    print(f"control g_{t}: fixed points {fp} | gen1 GoE within shadow: "
          f"{goe_shadow} | gen1 GoE full GF(7): {goe_full}")

controls_uv = all(c["unique_vacuum"] for c in results["controls"].values())
controls_goe_shadow = all(c["gen1_goe_within_shadow"]
                          for c in results["controls"].values())
controls_goe_full = all(c["gen1_goe_full_gf7"]
                        for c in results["controls"].values())
print(f"controls: unique vacuum {controls_uv} | GoE(shadow) "
      f"{controls_goe_shadow} | GoE(full) {controls_goe_full}")

# ---------------- exceptions: Tier 1 (recomputed) + Tier 2 (loaded) -------
exceptions = []

t1 = json.load(open(
    os.path.join(_HERE, "parity_projection_homomorphism_battery_results.json")))
for f in t1["tier1_gf7"]["forced_survivors"]:
    if not f["shadow_closed"]:
        exceptions.append({"source": "tier1", "label": f"form {f['form']} mod {f['m']}",
                           "rule": f["rule_coeffs"],
                           "image": f["image"], "g1": None})

t2 = json.load(open(
    os.path.join(_HERE, "parity_projection_local_function_battery_results.json")))
for cls, data in t2["classes"].items():
    m = data["m"]
    free, idx = pattern_setup(m)
    for v in data["scc_nonparity_violations"]:
        vecs = vecs_of(v["values_on_free_patterns"], idx)
        img = sorted(set(v["values_on_free_patterns"]) | {0})
        exceptions.append({"source": cls,
                           "label": f"{cls} vals={v['values_on_free_patterns']}",
                           "rule": v["rule_coeffs"], "image": img,
                           "g1": vecs[0]})

n_displaced, n_uv_pass = 0, 0
uv_survivors = []
for ex in exceptions:
    fp = diagonal_fixed_points(ex["rule"])
    ex["diag_fixed_points"] = fp
    ex["unique_vacuum"] = fp == [0]
    if ex["unique_vacuum"]:
        n_uv_pass += 1
        if ex["g1"] is not None:
            ex["gen1_goe_within_shadow"] = not has_predecessor(
                ex["rule"], ex["g1"], ex["image"])
            ex["gen1_goe_full_gf7"] = not has_predecessor(
                ex["rule"], ex["g1"], list(range(7)))
        uv_survivors.append(ex)
    else:
        n_displaced += 1

print(f"\nexceptions total: {len(exceptions)}")
print(f"F1 displaced vacuum (excluded): {n_displaced}")
print(f"F1 unique-vacuum survivors: {n_uv_pass}")
goe_kill_shadow = sum(1 for e in uv_survivors
                      if e.get("gen1_goe_within_shadow") is False)
goe_kill_full = sum(1 for e in uv_survivors
                    if e.get("gen1_goe_full_gf7") is False)
print(f"F2 of those, gen1 has a within-shadow predecessor (GoE fails): "
      f"{goe_kill_shadow}")
print(f"F2 of those, gen1 has a full-GF(7) predecessor: {goe_kill_full}")
both_pass = [e for e in uv_survivors
             if e.get("gen1_goe_within_shadow") and e.get("gen1_goe_full_gf7")]
print(f"exceptions passing F1 + F2(both): {len(both_pass)}")
for e in both_pass[:10]:
    print("  PASSES ALL:", e["label"], "rule", e["rule"], "fp", e["diag_fixed_points"])

results["exceptions"] = exceptions
results["summary"] = {
    "controls_unique_vacuum": controls_uv,
    "controls_gen1_goe_within_shadow": controls_goe_shadow,
    "controls_gen1_goe_full_gf7": controls_goe_full,
    "n_exceptions": len(exceptions),
    "n_displaced_vacuum": n_displaced,
    "n_unique_vacuum_survivors": n_uv_pass,
    "n_goe_shadow_killed": goe_kill_shadow,
    "n_goe_full_killed": goe_kill_full,
    "n_passing_all_filters": len(both_pass),
}

with open(os.path.join(_HERE, "parity_projection_architecture_filters_results.json"),
          "w") as f:
    json.dump(results, f, indent=1)
print("\nArtifact: parity_projection_architecture_filters_results.json")
signal.alarm(0)
