#!/usr/bin/env python3
"""
Parity-projection forcing battery, Tier 2: local residue functions.

A local mod-m reduction is any map rho(a,b,c) = f(a mod m, b mod m, c mod m),
vacuum-normalized (f(0,0,0) = 0). On the 15 canonical GTE triples only the
values of f on the occurring residue patterns matter, so each class is finite:

  EXHAUSTIVE (every class with lookup cost at or near the 19-bit rule cost):
    E1: m=2, codomain Z_2     -- 2^5  = 32          (10.0 bits incl. embeddings)
    E2: m=2, codomain GF(7)   -- 7^5  = 16,807      (14.0 bits)
    E3: m=3, codomain Z_3     -- 3^10 = 59,049      (15.8 bits)
    E4: m=4, codomain Z_4     -- 4^7  = 16,384      (14.0 bits)
    E5: m=4, codomain GF(7)   -- 7^7  = 823,543     (19.7 bits)
  SAMPLED (classes above the 19-bit reduction-cost line; fixed seed):
    S1: m=3, codomain GF(7)   (28.1 bits)  2e6 samples
    S2: m=5, codomain Z_5     (27.9 bits)  2e6
    S3: m=6, codomain Z_6     (28.4 bits)  2e6
    S4: m=7, codomain Z_7     (36.5 bits)  2e6
    S5: m=8..13, codomain GF(7) (~31-39 bits; m=11 has 14 patterns = the full
        lookup space on the 14 distinct triples) 2e5 each

Survivor criterion (pre-registered): FORCED (rank-8 unique multilinear GF(7)
rule under the 10 ring evaluations + vacuum transparency) AND shadow-closed
(the forced rule maps im(rho)^3 into im(rho) -- the invariant-subalphabet
coherence condition, P28/P49).

Pre-registered predictions:
  P2': E2 SCC-survivors = exactly the six relabeled parities (1 -> t),
       forcing the t-conjugates g_t of p.
  P3': every SCC-survivor in E1-E5 agrees with t * (total parity) on the 15
       canonical triples.
  P4': zero sampled SCC-survivor violates that factorization.
Per-class deterministic controls: the relabeled-parity assignment is
constructed and verified FORCED+SCC wherever parity is pattern-expressible
(m = 2,3,4,6,7,...); mod 5 the tau triple (5,275,65535) = (0,0,0) mod 5
collides with the vacuum at parity 1, so no mod-5 local function can express
the parity shadow (verified).

Artifact: parity_projection_local_function_battery_results.json
"""

import itertools
import json
import os
import random
import signal
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))

TIMEOUT_SECONDS = 1800


def _t(signum, frame):
    print(f"TIMEOUT: {TIMEOUT_SECONDS}s wall-clock limit reached.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _t)
signal.alarm(TIMEOUT_SECONDS)

TRIPLES = {
    "e":   [(1, 73, 823), (9, 42, 1023), (5, 275, 65535)],
    "u":   [(5, 9, 275), (5, 275, 65535), (76, 337920, -1)],
    "d":   [(9, 5, 42), (9, 186, 1023), (5, 8191, 65535)],
    "nuR": [(2, 5, 5), (7, 11, 13), (17, 19, 23)],
    "nuL": [(1, 1, 823), (9, 1, 1023), (5, 1, 65535)],
}
ORDER = ["e", "u", "d", "nuR", "nuL"]
PARITY = [[sum(TRIPLES[f][g]) % 2 for f in ORDER] for g in range(3)]

MONOMIALS = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1),
             (1, 1, 0), (1, 0, 1), (0, 1, 1), (1, 1, 1)]
P_COEFFS = [0, 0, 1, 1, 0, 0, 6, 6]


def monomial_row(L, C, R):
    return [pow(L, eL, 7) * pow(C, eC, 7) * pow(R, eR, 7) % 7
            for (eL, eC, eR) in MONOMIALS]


def gf7_solve(pm):
    rows = [monomial_row(*pt) + [out % 7] for pt, out in pm.items()]
    rank, pivots = 0, []
    for col in range(8):
        piv = next((r for r in range(rank, len(rows)) if rows[r][col] % 7), None)
        if piv is None:
            continue
        rows[rank], rows[piv] = rows[piv], rows[rank]
        inv = pow(rows[rank][col], 5, 7)
        rows[rank] = [(x * inv) % 7 for x in rows[rank]]
        for r in range(len(rows)):
            if r != rank and rows[r][col] % 7:
                f = rows[r][col]
                rows[r] = [(a - f * b) % 7 for a, b in zip(rows[r], rows[rank])]
        pivots.append(col)
        rank += 1
    for r in range(rank, len(rows)):
        if rows[r][8] % 7:
            return "NO_MULTILINEAR", 0, None
    if rank < 8:
        return "UNDERDETERMINED", 7 ** (8 - rank), None
    sol = [0] * 8
    for r, col in enumerate(pivots):
        sol[col] = rows[r][8]
    return "FORCED", 1, sol


def eval_rule(coeffs, L, C, R):
    return sum(c * pow(L, e[0], 7) * pow(C, e[1], 7) * pow(R, e[2], 7)
               for e, c in zip(MONOMIALS, coeffs)) % 7


def shadow_closed(coeffs, image):
    return all(eval_rule(coeffs, x, y, z) in image
               for x in image for y in image for z in image)


def conjugates_of_p():
    conj = {}
    for t in range(1, 7):
        coeffs = []
        for (eL, eC, eR), c in zip(MONOMIALS, P_COEFFS):
            d = eL + eC + eR
            coeffs.append(c * pow(t, (1 - d) % 6, 7) % 7)
        conj[t] = coeffs
    return conj


CONJ = conjugates_of_p()


def pattern_setup(m):
    """Returns (pattern list excluding the vacuum pattern, position index map,
    vacuum pattern occurs in data flag, per-pattern parity or None)."""
    pos_pat = []
    for g in range(3):
        for f in ORDER:
            a, b, c = TRIPLES[f][g]
            pos_pat.append((a % m, b % m, c % m))
    pats = sorted(set(pos_pat))
    par_by_pat = {}
    consistent = True
    for (f, g) in [(f, g) for g in range(3) for f in ORDER]:
        a, b, c = TRIPLES[f][g]
        pat = (a % m, b % m, c % m)
        par = (a + b + c) % 2
        if pat in par_by_pat and par_by_pat[pat] != par:
            consistent = False
        par_by_pat[pat] = par
    vac_in_data = (0, 0, 0) in pats
    free = [p for p in pats if p != (0, 0, 0)]
    idx = [free.index(p) if p != (0, 0, 0) else -1 for p in pos_pat]  # -1 = vacuum-pinned 0
    return free, idx, vac_in_data, (par_by_pat if consistent else None)


def classify_assignment(values, idx):
    """values: tuple of symbols for free patterns; returns status info.
    Vacuum-pinned positions (idx -1) take 0."""
    flat = [0 if i < 0 else values[i] for i in idx]
    vecs = [flat[0:5], flat[5:10], flat[10:15]]
    pm = {}
    for src, dst in ((vecs[0], vecs[1]), (vecs[1], vecs[2])):
        for i in range(5):
            pt = (src[(i - 1) % 5], src[i], src[(i + 1) % 5])
            if pt in pm and pm[pt] != dst[i]:
                return "CONFLICT", None, vecs
            pm[pt] = dst[i]
    if pm.get((0, 0, 0), 0) != 0:
        return "CONFLICT", None, vecs
    pm[(0, 0, 0)] = 0
    status, n, sol = gf7_solve(pm)
    return status, sol, vecs


def parity_factor_t(vecs):
    """If vecs == t * PARITY entrywise for a unit t, return t, else None."""
    for t in range(1, 7):
        if all(vecs[g][i] == t * PARITY[g][i] % 7 and (PARITY[g][i] or vecs[g][i] == 0)
               for g in range(3) for i in range(5)):
            if all(vecs[g][i] == (t if PARITY[g][i] else 0)
                   for g in range(3) for i in range(5)):
                return t
    return None


def run_class(name, m, codomain, mode, n_samples=0, seed=0):
    free, idx, vac_in_data, par_by_pat = pattern_setup(m)
    k = len(free)
    out = {"m": m, "codomain_size": len(codomain), "free_patterns": k,
           "vacuum_pattern_in_data": vac_in_data,
           "parity_pattern_expressible": par_by_pat is not None,
           "mode": mode, "status_counts": {}, "forced_total": 0,
           "scc_survivors": [], "scc_nonparity_violations": []}
    space = (itertools.product(codomain, repeat=k) if mode == "exhaustive"
             else None)
    rng = random.Random(seed)
    total = len(codomain) ** k if mode == "exhaustive" else n_samples
    it = space if mode == "exhaustive" else (
        tuple(rng.choice(codomain) for _ in range(k)) for _ in range(n_samples))
    for values in it:
        status, sol, vecs = classify_assignment(values, idx)
        out["status_counts"][status] = out["status_counts"].get(status, 0) + 1
        if status == "FORCED":
            out["forced_total"] += 1
            image = set(values) | {0}
            if shadow_closed(sol, image):
                t = parity_factor_t(vecs)
                tmatch = next((u for u, c in CONJ.items() if c == sol), None)
                rec = {"values_on_free_patterns": list(values),
                       "rule_coeffs": sol, "parity_factor_t": t,
                       "rule_is_conjugate_g_t": tmatch}
                if t is None or tmatch != t:
                    out["scc_nonparity_violations"].append(rec)
                elif len(out["scc_survivors"]) < 24:
                    out["scc_survivors"].append(rec)
                else:
                    out["scc_survivors_overflow"] = True
    out["n_scc_survivors"] = (len(out["scc_survivors"])
                              if not out.get("scc_survivors_overflow") else ">=24")
    out["enumerated_or_sampled"] = total
    print(f"{name} (m={m}, |cod|={len(codomain)}, {mode}, n={total}): "
          f"statuses={out['status_counts']} | SCC-survivors="
          f"{out['n_scc_survivors']} | factorization violations="
          f"{len(out['scc_nonparity_violations'])}")
    return out


def parity_control(m, codomain):
    """Construct t*parity as a local mod-m assignment where expressible;
    verify FORCED + SCC + rule == g_t."""
    free, idx, vac_in_data, par_by_pat = pattern_setup(m)
    if par_by_pat is None:
        return {"expressible": False,
                "reason": "a parity-1 triple shares a residue pattern with a "
                          "parity-0 triple (or the vacuum)"}
    if par_by_pat.get((0, 0, 0), 0) != 0:
        return {"expressible": False,
                "reason": "vacuum pattern carries parity 1 on the data"}
    res = {"expressible": True, "verified_t": []}
    for t in range(1, 7):
        if t not in codomain:
            continue
        values = tuple(t * par_by_pat[p] for p in free)
        status, sol, vecs = classify_assignment(values, idx)
        ok = (status == "FORCED" and sol == CONJ[t]
              and shadow_closed(sol, {0, t}))
        if ok:
            res["verified_t"].append(t)
    return res


results = {"classes": {}, "parity_controls": {}, "summary": {}}

# exhaustive classes
results["classes"]["E1_m2_codZ2"] = run_class("E1", 2, [0, 1], "exhaustive")
results["classes"]["E2_m2_codGF7"] = run_class("E2", 2, list(range(7)), "exhaustive")
results["classes"]["E3_m3_codZ3"] = run_class("E3", 3, [0, 1, 2], "exhaustive")
results["classes"]["E4_m4_codZ4"] = run_class("E4", 4, [0, 1, 2, 3], "exhaustive")
results["classes"]["E5_m4_codGF7"] = run_class("E5", 4, list(range(7)), "exhaustive")

# sampled classes
results["classes"]["S1_m3_codGF7"] = run_class(
    "S1", 3, list(range(7)), "sampled", 2_000_000, seed=20260611)
results["classes"]["S2_m5_codZ5"] = run_class(
    "S2", 5, list(range(5)), "sampled", 2_000_000, seed=20260612)
results["classes"]["S3_m6_codZ6"] = run_class(
    "S3", 6, list(range(6)), "sampled", 2_000_000, seed=20260613)
results["classes"]["S4_m7_codZ7"] = run_class(
    "S4", 7, list(range(7)), "sampled", 2_000_000, seed=20260614)
for m in range(8, 14):
    results["classes"][f"S5_m{m}_codGF7"] = run_class(
        f"S5(m={m})", m, list(range(7)), "sampled", 200_000, seed=20260600 + m)

# per-class relabeled-parity deterministic controls
for m, cod in [(2, list(range(7))), (3, [0, 1, 2]), (4, list(range(7))),
               (5, [0, 1, 2, 3, 4]), (6, [0, 1, 2, 3, 4, 5]),
               (7, list(range(7))), (8, list(range(7))), (11, list(range(7))),
               (13, list(range(7)))]:
    results["parity_controls"][m] = parity_control(m, cod)
    print(f"parity control m={m}: {results['parity_controls'][m]}")

# summary checks
e2 = results["classes"]["E2_m2_codGF7"]
results["summary"]["P2prime_pass"] = (
    e2["n_scc_survivors"] == 6 and not e2["scc_nonparity_violations"]
    and sorted(s["parity_factor_t"] for s in e2["scc_survivors"]) == [1, 2, 3, 4, 5, 6])
results["summary"]["P3prime_pass"] = all(
    not results["classes"][c]["scc_nonparity_violations"]
    for c in ("E1_m2_codZ2", "E2_m2_codGF7", "E3_m3_codZ3",
              "E4_m4_codZ4", "E5_m4_codGF7"))
results["summary"]["P4prime_pass"] = all(
    not v["scc_nonparity_violations"]
    for k, v in results["classes"].items() if k.startswith("S"))
print(f"\nP2' (E2 survivors = six relabeled parities): "
      f"{results['summary']['P2prime_pass']}")
print(f"P3' (exhaustive classes: every SCC-survivor factors through t*parity): "
      f"{results['summary']['P3prime_pass']}")
print(f"P4' (sampled classes: zero factorization violations): "
      f"{results['summary']['P4prime_pass']}")

with open(os.path.join(_HERE, "parity_projection_local_function_battery_results.json"),
          "w") as f:
    json.dump(results, f, indent=1)
print("\nArtifact: parity_projection_local_function_battery_results.json")
signal.alarm(0)
