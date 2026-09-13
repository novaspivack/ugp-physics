#!/usr/bin/env python3
"""
Parity-projection forcing battery, Tier 3: vacuity of the unrestricted
reduction space (pre-registered P5).

In the unrestricted space -- arbitrary assignments of GF(7) symbols to the
14 distinct canonical triples (the only internal constraint being the
duplicate e_gen3 = u_gen2 = (5,275,65535)) -- forcing cannot single out any
rule: an adversary can paint the orbit of a rule of their choosing.  This
script produces the explicit certificate, in the strongest (shadow-closed)
form:

  For each vacuum-transparent elementary CA rule tau, search the 32 binary
  gen1 vectors v1 on the 5-ring; evolve v2 = tau(v1), v3 = tau(v2); accept if
  the duplicate constraint v3[0] == v2[1] holds and the 10 ring evaluations
  + vacuum transparency have rank 8 over GF(7).  Any accept yields a lookup
  "reduction" (triple -> symbol) that FORCES the unique multilinear GF(7)
  lift of tau -- which is closed on {0,1} by construction (SCC-respecting).
  If tau is not Rule 110, the forced rule is not p (nor, generically, any
  GF(7)^x conjugate); forcing in the unrestricted space is therefore
  vacuous EVEN WITH the shadow-closure coherence condition.

Artifact: parity_projection_unrestricted_vacuity_results.json
"""

import itertools
import json
import os
import signal
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))

TIMEOUT_SECONDS = 600


def _t(signum, frame):
    print(f"TIMEOUT: {TIMEOUT_SECONDS}s limit reached.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _t)
signal.alarm(TIMEOUT_SECONDS)

MONOMIALS = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1),
             (1, 1, 0), (1, 0, 1), (0, 1, 1), (1, 1, 1)]
P_COEFFS = [0, 0, 1, 1, 0, 0, 6, 6]
TRIPLES = {
    "e":   [(1, 73, 823), (9, 42, 1023), (5, 275, 65535)],
    "u":   [(5, 9, 275), (5, 275, 65535), (76, 337920, -1)],
    "d":   [(9, 5, 42), (9, 186, 1023), (5, 8191, 65535)],
    "nuR": [(2, 5, 5), (7, 11, 13), (17, 19, 23)],
    "nuL": [(1, 1, 823), (9, 1, 1023), (5, 1, 65535)],
}
ORDER = ["e", "u", "d", "nuR", "nuL"]


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
            return None
    if rank < 8:
        return None
    sol = [0] * 8
    for r, col in enumerate(pivots):
        sol[col] = rows[r][8]
    return sol


def eca_step(rule, cells):
    return [(rule >> (cells[(i - 1) % 5] * 4 + cells[i] * 2
                      + cells[(i + 1) % 5])) & 1 for i in range(5)]


def conjugates_of_p():
    conj = []
    for t in range(1, 7):
        coeffs = []
        for (eL, eC, eR), c in zip(MONOMIALS, P_COEFFS):
            d = eL + eC + eR
            coeffs.append(c * pow(t, (1 - d) % 6, 7) % 7)
        conj.append(coeffs)
    return conj


CONJ = conjugates_of_p()

certificates = []
rules_forced = set()
for tau in range(0, 256, 2):  # vacuum-transparent ECA rules (bit 0 = 0)
    for bits in range(32):
        v1 = [(bits >> i) & 1 for i in range(5)]
        v2 = eca_step(tau, v1)
        v3 = eca_step(tau, v2)
        if v3[0] != v2[1]:  # duplicate triple constraint e_g3 == u_g2
            continue
        pm = {}
        ok = True
        for src, dst in ((v1, v2), (v2, v3)):
            for i in range(5):
                pt = (src[(i - 1) % 5], src[i], src[(i + 1) % 5])
                if pt in pm and pm[pt] != dst[i]:
                    ok = False
                pm[pt] = dst[i]
        if not ok or pm.get((0, 0, 0), 0) != 0:
            continue
        pm[(0, 0, 0)] = 0
        sol = gf7_solve(pm)
        if sol is None:
            continue
        rules_forced.add(tau)
        if len(certificates) < 12 and tau not in {c["eca_rule"] for c in certificates}:
            # explicit lookup table: triple -> symbol
            lookup = {}
            for gi, v in enumerate((v1, v2, v3)):
                for fi, f in enumerate(ORDER):
                    lookup[str(TRIPLES[f][gi])] = v[fi]
            certificates.append({
                "eca_rule": tau, "gen1": v1, "gen2": v2, "gen3": v3,
                "forced_gf7_lift": sol,
                "is_p_conjugate": sol in CONJ,
                "lookup_reduction_triple_to_symbol": lookup})
        break

non_p = sorted(r for r in rules_forced if r not in (110,))
print(f"vacuum-transparent ECA rules forceable by an unrestricted lookup "
      f"reduction (shadow-closed on {{0,1}} by construction): "
      f"{len(rules_forced)} of 128")
print(f"non-Rule-110 examples: {non_p[:20]}{'...' if len(non_p) > 20 else ''}")
for c in certificates[:5]:
    print(f"  tau={c['eca_rule']}: orbit {c['gen1']}->{c['gen2']}->{c['gen3']} "
          f"forces lift {c['forced_gf7_lift']} (p-conjugate: {c['is_p_conjugate']})")

results = {
    "n_vt_eca_rules_forceable": len(rules_forced),
    "rules_forceable": sorted(rules_forced),
    "n_non_rule110": len(non_p),
    "vacuity_established": len(non_p) > 0,
    "certificates": certificates,
    "interpretation": (
        "In the unrestricted lookup space the cascade data forces nothing: "
        "dozens of vacuum-transparent ECA shadows (all closed on {0,1}) can "
        "each be painted by a lookup reduction and are then FORCED as unique "
        "multilinear GF(7) rules. Forcing theorems can only exist for "
        "structure-preserving reduction classes."),
}
with open(os.path.join(_HERE, "parity_projection_unrestricted_vacuity_results.json"),
          "w") as f:
    json.dump(results, f, indent=1)
print("\nArtifact: parity_projection_unrestricted_vacuity_results.json")
signal.alarm(0)
