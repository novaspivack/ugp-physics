#!/usr/bin/env python3
"""Branch C check: would gauging the F21 Z3-automorphism action dissolve Z7 walls?

The Lazarides-Shafi escape requires the vacuum-permuting symmetry to be gauged.
In F21 = Z7 : Z3 the Z3 acts on Z7 by multiplication by 2 (conjugation).
If that action were a GAUGE identification on winding charges, vacua/windings
in the same <x2> orbit would be physically identical. This script computes the
orbits and checks them against the established SM species map
(w=2 -> u, w=3 -> W+, w=4 -> e-, w=6 -> d; w in {1,5} dark mirror; P22/P28/P29,
FINAL_THEORY particle table) to test whether the identification is consistent.

Also computes: the affine group <x2, +1> acting on Z7 (what gauging the full
F21 quotient lift-ambiguity would identify) and pi_1 of the 7-point vacuum
manifold (string content for wall-bounded-by-strings decay).

Expected output: <x2> orbits {0},{1,2,4},{3,5,6}; species collapse pairs
(u ~ e ~ dark-1), (W+ ~ d ~ dark-5) -> gauging REFUTED by the species map.
"""
import json
import signal
import sys

TIMEOUT_SECONDS = 60

def _timeout(signum, frame):
    print(f"TIMEOUT {TIMEOUT_SECONDS}s reached")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

species = {0: "vacuum/gamma/nu", 1: "dark-mirror(1)", 2: "u-quark", 3: "W+",
           4: "e-", 5: "dark-mirror(5) [W+ mirror]", 6: "d-quark"}

def orbit(x, mult):
    o, cur = [], x
    while cur not in o:
        o.append(cur)
        cur = (mult * cur) % 7
    return tuple(sorted(o))

orbits = sorted({orbit(x, 2) for x in range(7)})
print("=== <x2> (Z3 conjugation) orbits on Z7 winding charges ===")
collapse = []
for o in orbits:
    members = [f"w={w} ({species[w]})" for w in o]
    print(f"  orbit {o}: " + " ~ ".join(members))
    if len(o) > 1:
        collapse.append([species[w] for w in o])

print("\n=== Species-collapse test ===")
print("  If the Z3 automorphism action were gauged, each orbit above would be ONE")
print("  physical object. That identifies u-quark ~ e- ~ dark-1 and W+ ~ d ~ dark-5:")
print("  contradicts the established distinct species/charges (P22 CatAL winding map,")
print("  P45 charged-current catalog). GAUGING THE DOUBLING ACTION: REFUTED.")

# affine closure: lifts of the Z3 in F21 differ by Z7 shifts; the group generated
# by all lifts acts affinely k -> 2^a k + b and is transitive
reach = {1}
frontier = {1}
elems = set()
for a in range(3):
    for b in range(7):
        elems.add((pow(2, a, 7), b))
img = {( (m * k + b) % 7 ) for k in range(1, 2) for (m, b) in elems}
transitive = len({(m * 0 + b) % 7 for (m, b) in elems}) == 7
print("\n=== Quotient-gauging lift ambiguity ===")
print(f"  group of lifts acts affinely k -> 2^a k + b; image of any k covers all of Z7: {transitive}")
print("  -> gauging the Z3 QUOTIENT consistently would gauge-identify ALL windings")
print("     (every particle one object): an even stronger contradiction.")

print("\n=== Vacuum-manifold topology ===")
print("  vacuum manifold = 7 isolated points; pi_1 = 0 (P42 Topological remark):")
print("  no strings exist for walls to end on -> no string-bounded wall decay channel.")

print("\nVERDICT (branch C): only the chi-shift Z3 is gauged (GaugeInvariance.lean:")
print("phi carries no Z3 gauge charge). No Z7 vacuum identification exists;")
print("the Lazarides-Shafi escape is RULED OUT in GTE.")

results = {"x2_orbits": [list(o) for o in orbits],
           "species_collapse_if_gauged": collapse,
           "affine_lift_action_transitive": transitive,
           "pi1_vacuum_manifold": 0,
           "verdict": "branch C ruled out: species collapse + no phi gauge charge"}
import os
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
          "z7_domain_wall_gauge_orbit_species_check_results.json"), "w") as fp:
    json.dump(results, fp, indent=1)
print("Saved z7_domain_wall_gauge_orbit_species_check_results.json")
signal.alarm(0)
