#!/usr/bin/env python3
"""Generalization battery for the period-475 nineteen-factor mechanism (088-R08).

Pre-registered hypotheses (written before execution; see PREREG below):
  H-FORM     structure law (CRT tower) holds for every sigma-linked prime-ring cycle
  H-ZS       value law: d = Zsygmondy prime of q^3 - 1 (q=3->13, 5->31, 11->{7,19}, 13->61)
  H-CARRIER3 value law: ord_d(q) = 3 for the dominant attractor
  H-MDLBITS  value law: d = floor(7 log2 q) (P49 19-bit reading) {3:11, 5:16, 11:24, 13:25}
  H-NFAM     value law: d = 5 mod q ("19 = 5 mod 7" reading)
  H-SUPPORT  dominant chaotic attractor has linear complexity N-1 (full support minus mean)
  H-LINNOGO  no monodromy eigenvalue order divisible by the variant's d

Variants executed exhaustively:
  A. p over GF(q), q in {3, 5, 11, 13}, 5-cell ring (full functional-graph peel)
  B. p over GF(7), rings n in {3, 4, 6, 7}
  C. 12 Rule-110-compatible non-multilinear cubics over GF(7), 5-ring
     (f = p + (L^2-L) l1 + (C^2-C) l2 + (R^2-R) l3, li random linear forms;
      all agree with Rule 110 on the 8 binary points by construction)

Per variant: cycle spectrum; per-cycle sigma-class (k, j) or FREE; d = n-free
part; m = 0 mod d check; symmetric-observable period | k check; BM linear
complexity + factor-degree census for the longest cycle (N <= 1500); monodromy
charpoly + root orders for the dominant attractor. Output: verdict table.
"""
import os
import json
import random
import signal
import sys
from math import gcd, prod, log2, floor

import sympy as sp

TIMEOUT_SECONDS = 1500
signal.signal(signal.SIGALRM, lambda s, f: sys.exit("TIMEOUT"))
signal.alarm(TIMEOUT_SECONDS)

PREREG = {
    "H-ZS": {"3": [13], "5": [31], "11": [7, 19], "13": [61]},
    "H-CARRIER3": "ord_d(q) == 3 for dominant attractor",
    "H-MDLBITS": {"3": 11, "5": 16, "11": 24, "13": 25},
    "H-NFAM": "d == 5 mod q",
    "H-SUPPORT": "linear complexity == N-1 for dominant chaotic attractor",
    "H-LINNOGO": "no monodromy eigenvalue order divisible by d",
}
x = sp.symbols('x')


def make_step(q, n, rule=None):
    if rule is None:
        def f(L, C, R):
            return (C + R - C * R - L * C * R) % q
    else:
        f = rule

    def step(s):
        return tuple(f(s[(i - 1) % n], s[i], s[(i + 1) % n]) for i in range(n))
    return step


def enumerate_cycles(q, n, step):
    """Full functional-graph peel. Returns dict: cycle_len -> list of one
    representative state list per cycle (capped reps)."""
    N = q ** n
    code = {}

    def enc(s):
        v = 0
        for c in s:
            v = v * q + c
        return v

    nxt = [0] * N
    # enumerate states
    state = [0] * n
    for v in range(N):
        # decode
        vv, s = v, [0] * n
        for i in range(n - 1, -1, -1):
            s[i] = vv % q
            vv //= q
        nxt[v] = enc(step(tuple(s)))
    color = [0] * N  # 0 unvisited, 1 in progress path id stored separately
    oncycle = [False] * N
    cyc_of = {}
    cycles = {}
    visited = [False] * N
    for v0 in range(N):
        if visited[v0]:
            continue
        path = []
        pos = {}
        v = v0
        while not visited[v] and v not in pos:
            pos[v] = len(path)
            path.append(v)
            v = nxt[v]
        if v in pos:  # new cycle found
            start = pos[v]
            cyc = path[start:]
            Lc = len(cyc)
            cycles.setdefault(Lc, []).append(cyc[0])
            for u in cyc:
                oncycle[u] = True
        for u in path:
            visited[u] = True
    return cycles


def dec(v, q, n):
    s = [0] * n
    for i in range(n - 1, -1, -1):
        s[i] = v % q
        v //= q
    return tuple(s)


def cycle_states(rep, q, n, step):
    s0 = dec(rep, q, n)
    out = [s0]
    s = step(s0)
    while s != s0:
        out.append(s)
        s = step(s)
    return out


def sigma_class(cyc, n):
    """Minimal (k, j) with T^k = sigma^j on the cycle, or FREE."""
    idx = {st: i for i, st in enumerate(cyc)}
    L = len(cyc)

    def shf(s, j):
        return tuple(s[(i + j) % n] for i in range(n))
    sh1 = shf(cyc[0], 1)
    if sh1 not in idx:
        return None  # free orbit (sigma maps to a different cycle)
    m = idx[sh1]
    if any(idx.get(shf(cyc[i], 1)) != (i + m) % L for i in range(L)):
        return None
    # minimal k with T^k = sigma^j: k minimal such that k = j*m mod L solvable:
    best = None
    for j in range(n):
        k = (j * m) % L
        if k == 0:
            k = L if j == 0 else None
            if j == 0:
                kk = L  # T^L = id = sigma^0
                cand = (kk, 0)
            else:
                cand = None
        else:
            cand = (k, j)
        if cand and (best is None or cand[0] < best[0]):
            best = cand
    return {"m": m, "k": best[0], "j": best[1]}


def nfree(N, n):
    d = N
    while d % n == 0:
        d //= n
    return d


def mult_order(a, mod):
    if mod == 1 or gcd(a, mod) != 1:
        return None
    o, v = 1, a % mod
    while v != 1:
        v = (v * a) % mod
        o += 1
    return o


def bm_gf(seq, q):
    C = [1]; B = [1]; Lc = 0; mm = 1; b = 1
    for nn in range(len(seq)):
        d = seq[nn]
        for i in range(1, Lc + 1):
            d = (d + C[i] * seq[nn - i]) % q
        if d == 0:
            mm += 1
        elif 2 * Lc <= nn:
            T = C[:]
            coef = (d * pow(b, q - 2, q)) % q
            C = C + [0] * (len(B) + mm - len(C))
            for i in range(len(B)):
                C[i + mm] = (C[i + mm] - coef * B[i]) % q
            Lc = nn + 1 - Lc; B = T; b = d; mm = 1
        else:
            coef = (d * pow(b, q - 2, q)) % q
            C = C + [0] * (len(B) + mm - len(C))
            for i in range(len(B)):
                C[i + mm] = (C[i + mm] - coef * B[i]) % q
            mm += 1
    return Lc


def monodromy_orders(cyc, q, n):
    """Charpoly of the full-cycle monodromy of p over GF(q) + root orders."""
    def matmul(A, B):
        return [[sum(A[i][k] * B[k][j] for k in range(n)) % q
                 for j in range(n)] for i in range(n)]
    M = [[1 if i == j else 0 for j in range(n)] for i in range(n)]
    for s in cyc:
        J = [[0] * n for _ in range(n)]
        for i in range(n):
            L_, C_, R_ = s[(i - 1) % n], s[i], s[(i + 1) % n]
            J[i][(i - 1) % n] = (-C_ * R_) % q
            J[i][i] = (1 - R_ - L_ * R_) % q
            J[i][(i + 1) % n] = (1 - C_ - L_ * C_) % q
        M = matmul(J, M)
    cp = sp.Poly(sp.Matrix(M).charpoly(x).as_expr(), x, modulus=q)
    orders = []
    for fac, mult in sp.factor_list(cp, modulus=q)[1]:
        fp = sp.Poly(fac, x, modulus=q)
        k = fp.degree()
        if k == 1 and fp.eval(0) % q == 0:
            orders.append(0)
            continue
        fo = q ** k - 1
        o = fo
        for pr in set(sp.factorint(fo)):
            while o % pr == 0:
                cand = o // pr
                xc = sp.Poly(x, x, modulus=q)
                if sp.rem(xc ** cand, fp, modulus=q) == sp.Poly(1, x, modulus=q):
                    o = cand
                else:
                    break
        orders.append(int(o))
    return str(sp.factor(cp.as_expr(), modulus=q)), orders


def sym_period(cyc, q, n):
    """Period of (e1..en) joint symmetric observable sequence."""
    import itertools as it
    seqs = []
    for k in range(1, n + 1):
        seqs.append([sum(prod(c) % q for c in it.combinations(st, k)) % q
                     for st in cyc])
    L = len(cyc)
    for d in [d for d in range(1, L + 1) if L % d == 0]:
        if all(all(s[t] == s[(t + d) % L] for t in range(L)) for s in seqs):
            return d
    return L


def analyze(q, n, step, label, full_bm_cap=1500):
    cycles = enumerate_cycles(q, n, step)
    spectrum = {Lc: len(reps) for Lc, reps in sorted(cycles.items())}
    rows = []
    dominant = max(cycles)  # longest cycle = dominant attractor
    for Lc, reps in sorted(cycles.items()):
        cyc = cycle_states(reps[0], q, n, step)
        sc = sigma_class(cyc, n)
        d = nfree(Lc, n)
        row = {"N": Lc, "count": len(reps), "sigma_class": sc, "d": d}
        if sc is not None and Lc > 1:
            row["m_mod_d_zero"] = (sc["m"] % d == 0) if d > 1 else True
            row["sym_period"] = sym_period(cyc, q, n)
            row["sym_divides_k"] = (sc["k"] % row["sym_period"] == 0)
            row["ord_d_q"] = mult_order(q, d) if d > 1 else None
        if Lc == dominant and Lc > 1:
            if Lc <= full_bm_cap:
                seq = [st[0] for st in cyc] * 2
                row["lin_complexity"] = bm_gf(seq, q)
                row["full_support"] = (row["lin_complexity"] == Lc - 1)
            cpstr, orders = monodromy_orders(cyc, q, n)
            row["monodromy_charpoly"] = cpstr
            row["monodromy_orders"] = orders
            row["lin_nogo"] = (d <= 1) or all(
                o == 0 or o % d != 0 for o in orders)
        rows.append(row)
    print(f"\n=== {label}: spectrum {spectrum}")
    for r in rows:
        print("   ", r)
    return {"label": label, "spectrum": {str(k): v for k, v in
                                         spectrum.items()}, "cycles": rows}


results = {"prereg": PREREG, "variants": []}

# --- A. p over GF(q), 5-ring ---
for q in (3, 5, 11, 13):
    step = make_step(q, 5)
    results["variants"].append(analyze(q, 5, step, f"p over GF({q}), n=5"))

# --- B. p over GF(7), rings 3, 4, 6, 7 ---
for n in (3, 4, 6, 7):
    step = make_step(7, n)
    results["variants"].append(analyze(7, n, step, f"p over GF(7), n={n}"))

# --- C. Rule-110-compatible non-multilinear cubics over GF(7), 5-ring ---
random.seed(20260609)
null_rows = []
for trial in range(12):
    co = [[random.randrange(7) for _ in range(4)] for _ in range(3)]
    if all(all(c == 0 for c in row) for row in co):
        co[0][0] = 1

    def rule(L, C, R, co=co):
        base = (C + R - C * R - L * C * R)
        vL = (L * L - L) * (co[0][0] + co[0][1] * L + co[0][2] * C + co[0][3] * R)
        vC = (C * C - C) * (co[1][0] + co[1][1] * L + co[1][2] * C + co[1][3] * R)
        vR = (R * R - R) * (co[2][0] + co[2][1] * L + co[2][2] * C + co[2][3] * R)
        return (base + vL + vC + vR) % 7
    # sanity: agrees with Rule 110 on binary points
    r110 = {(1, 1, 1): 0, (1, 1, 0): 1, (1, 0, 1): 1, (1, 0, 0): 0,
            (0, 1, 1): 1, (0, 1, 0): 1, (0, 0, 1): 1, (0, 0, 0): 0}
    assert all(rule(*k) == v for k, v in r110.items())
    step = make_step(7, 5, rule)
    res = analyze(7, 5, step, f"R110-compatible cubic #{trial}", full_bm_cap=0)
    null_rows.append(res)
results["null_rules"] = null_rows

# --- verdict table ---
print("\n========= VERDICT TABLE (5-ring GF(q) dominant attractors) =========")
verdicts = {}
for v in results["variants"][:4]:
    q = int(v["label"].split("GF(")[1].split(")")[0])
    dom = max(v["cycles"], key=lambda r: r["N"])
    d = dom["d"]
    N = dom["N"]
    zs = d in PREREG["H-ZS"][str(q)]
    car3 = (dom.get("ord_d_q") == 3)
    mdl = (d == PREREG["H-MDLBITS"][str(q)])
    nfam = (d % q == 5 % q)
    sup = dom.get("full_support")
    nogo = dom.get("lin_nogo")
    print(f"q={q}: N={N}, d={d}, ord_d(q)={dom.get('ord_d_q')}, "
          f"H-ZS({PREREG['H-ZS'][str(q)]}): {zs}, H-CARRIER3: {car3}, "
          f"H-MDLBITS({PREREG['H-MDLBITS'][str(q)]}): {mdl}, H-NFAM: {nfam}, "
          f"H-SUPPORT: {sup}, H-LINNOGO: {nogo}")
    verdicts[str(q)] = {"N": N, "d": d, "ord_d_q": dom.get("ord_d_q"),
                        "H-ZS": zs, "H-CARRIER3": car3, "H-MDLBITS": mdl,
                        "H-NFAM": nfam, "H-SUPPORT": sup, "H-LINNOGO": nogo}
results["verdicts"] = verdicts

# H-FORM check across all sigma-linked cycles everywhere
form_fails = []
for v in results["variants"] + results["null_rules"]:
    for r in v["cycles"]:
        if r.get("sigma_class") and r["N"] > 1:
            if not r.get("m_mod_d_zero", True) or not r.get("sym_divides_k",
                                                            True):
                form_fails.append((v["label"], r["N"]))
print(f"H-FORM violations across all sigma-linked cycles: {form_fails}")
results["H_FORM_violations"] = form_fails

# null-rule d census on the 5-ring
null_d = {}
for v in null_rows:
    for r in v["cycles"]:
        if r["N"] > 1 and r.get("sigma_class"):
            null_d[r["d"]] = null_d.get(r["d"], 0) + 1
print(f"null-rule sigma-linked d census (12 R110-compatible cubics, n=5): "
      f"{dict(sorted(null_d.items()))}")
results["null_d_census"] = {str(k): v for k, v in sorted(null_d.items())}

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
          "nineteen_factor_generalization_battery_results.json"), "w") as f:
    json.dump(results, f, indent=1)
print("Saved nineteen_factor_generalization_battery_results.json")
signal.alarm(0)
