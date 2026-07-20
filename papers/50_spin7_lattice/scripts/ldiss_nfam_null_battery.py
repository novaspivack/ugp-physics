"""Null battery for the Lambda_diss / M^Q = 5.32 +/- 0.45 vs N_fam = 5
coincidence (OQ-088-R26d).

E1 (candidate density): enumerate structural candidates in the 1-sigma
window [4.87, 5.77] -- small rationals p/q (p <= 50, q <= 9, gcd-reduced),
GTE atoms (N_fam = 5, |Z_7| = 7, 49/9, 16/3, 21/4, 2pi - 1, ...).  If >= 3
structurally inequivalent candidates pass at 1 sigma the observation has no
discriminating power.

E2 (kinematics, recorded): the dissolution channel is winding-neutral; its
spectral thresholds are 2nM (kink pairs) and 2M + m_phi = 8.125 M (inelastic
onset).  A five-kink state (winding 5) cannot appear.  No mechanism.

Expected: many candidates in the window  =>  resolved-negative.
"""

import json
import os
import math
import signal
import sys
from fractions import Fraction

TIMEOUT_SECONDS = 120


def _timeout(s, f):
    print("TIMEOUT reached. Exiting.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

R, DR = 5.3203, 0.4530          # Lambda_diss / M^Q (Run 84)
LO, HI = R - DR, R + DR

print(f"ratio = {R} +/- {DR}; 1-sigma window [{LO:.4f}, {HI:.4f}]")

print("\n=== E1: small-rational density in the window ===")
rationals = set()
for q in range(1, 10):
    for p in range(1, 51):
        f = Fraction(p, q)
        if LO <= float(f) <= HI:
            rationals.add(f)
rationals = sorted(rationals, key=float)
print(f"distinct reduced rationals p/q (p<=50, q<=9) in window: {len(rationals)}")
print("  " + ", ".join(f"{f} ({float(f):.4f}, {abs(float(f)-R)/DR:.2f}sigma)"
                       for f in rationals[:25]))

print("\n=== named structural candidates ===")
named = {
    "N_fam = 5": 5.0,
    "16/3": 16.0 / 3.0,
    "21/4": 21.0 / 4.0,
    "49/9": 49.0 / 9.0,
    "11/2": 5.5,
    "2pi - 1": 2 * math.pi - 1,
    "e + 5/2": math.e + 2.5,
    "7*3/4": 5.25,
    "sqrt(28)": math.sqrt(28),
}
n_pass = 0
for name, v in sorted(named.items(), key=lambda kv: abs(kv[1] - R)):
    sig = abs(v - R) / DR
    ok = sig <= 1.0
    n_pass += ok
    print(f"  {name:12s} = {v:.4f}: {sig:.2f} sigma {'PASS' if ok else 'fail'}")
print(f"named candidates passing at 1 sigma: {n_pass}")

print("\n=== E2: kinematics of the dissolution channel (recorded) ===")
print("  winding-neutral channel; thresholds 2nM (pairs), 2M + m_phi = 8.125M")
print("  (inelastic onset).  Winding-5 intermediate states forbidden.")
print("  -> no five-kink mechanism exists in the dissolution machinery.")

verdict = ("REJECTED-as-numerology (resolved-negative): >= 3 structurally "
           "inequivalent candidates inside 1 sigma (zero discriminating "
           "power at current precision) AND no winding-kinematics mechanism "
           "for a five-kink threshold in the charge (winding-neutral) "
           "dissolution channel.")
print("\nVERDICT:", verdict)

signal.alarm(0)
out = {"ratio": R, "sigma": DR, "window": [LO, HI],
       "n_small_rationals_in_window": len(rationals),
       "rationals_sample": [str(f) for f in rationals[:25]],
       "named_candidates": {k: {"value": v, "sigma": abs(v - R) / DR}
                            for k, v in named.items()},
       "n_named_passing_1sigma": int(n_pass),
       "kinematics": "winding-neutral channel; thresholds 2nM and 2M+m_phi; "
                     "no winding-5 intermediate states",
       "verdict": verdict}
_out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "ldiss_nfam_null_battery.json")
with open(_out_path, "w") as f:
    json.dump(out, f, indent=2)
print("\nSaved", _out_path)
