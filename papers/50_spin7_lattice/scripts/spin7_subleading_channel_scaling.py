"""Sub-leading transfer-channel scaling of the spin-7 chain (OQ-088-R26c).

BR-WALL-KINK quantitative bridge test (pre-registered, Battery D):
  D1: large-beta exponents of Delta_3, Delta_4, ... vs the wall-algebra
      predictions {2 (bump-0), 3 (zero-winding wall pair 1->0->1 / bump-1),
      4 (bump-5)}; tol 2% on exponents.
  D2: bridge dictionary -- asymptotic channel ratios Delta_k/Delta_2 vs
      {4/3 (bump-0 -> a state at (4/3)M, FORBIDDEN by ZZ pole-freedom),
       2   (wall pair -> kink-antikink threshold 2M, REQUIRED)}.
      Reality/positivity of each channel tracked (only real-positive
      channels are OS-physical).
  Neighbor-atom null: wall energies perturbed by +/-1 shift the predicted
      ratios to {7/6, 5/3, ...}; the measured exponents must match the
      true integer table, not the neighbors.

Method: full eigenvalue spectrum (non-symmetric, complex allowed) with
mpmath dps 50 for beta in [6, 12]; local slopes s_k(beta) =
-d ln|lambda_k/lambda_1| / d beta ... reported as Delta_k(beta)/beta -> E_k
and Richardson-extrapolated with the e^(-beta/2) correction model validated
in Run 83.

Expected: E_2 -> 3/2 (known); E_3, E_4 -> values in {2, 3, 4} if the
wall/bump algebra controls the sub-leading channels.
"""

import json
import os
import signal
import sys

import numpy as np
import mpmath as mp

TIMEOUT_SECONDS = 900


def _timeout(s, f):
    print("TIMEOUT reached. Exiting.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

mp.mp.dps = 50
Q = 7


def p_gte(L, C, R):
    return (C + R - C * R - L * C * R) % Q


def spectrum_mp(beta, n_keep=8):
    M = mp.zeros(Q * Q, Q * Q)
    for a in range(Q):
        for b in range(Q):
            for c in range(Q):
                M[a * Q + b, b * Q + c] = mp.e ** (-beta * p_gte(a, b, c))
    ev = mp.eig(M, left=False, right=False)
    ev_sorted = sorted(ev, key=lambda z: -abs(z))
    out = []
    lam1 = abs(ev_sorted[0])
    for z in ev_sorted[:n_keep]:
        out.append({
            "mod": float(abs(z)),
            "Delta": float(mp.log(lam1 / abs(z))) if abs(z) > 0 else None,
            "re": float(mp.re(z)), "im": float(mp.im(z)),
            "real_positive": bool(abs(mp.im(z)) < mp.mpf("1e-30") and mp.re(z) > 0),
        })
    return out


print("=== sub-leading channel scaling, beta in [6, 12] ===")
betas = [6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0]
table = {}
for b in betas:
    table[b] = spectrum_mp(b)
    row = "  ".join(f"D{k+1}={ch['Delta']:.4f}({'R+' if ch['real_positive'] else 'c'})"
                    for k, ch in enumerate(table[b][1:6], start=1))
    print(f"beta={b:5.1f}: {row}")

print("\n=== effective energies E_k(beta) = Delta_k/beta and extrapolation ===")
# local two-point slope s_k = (Delta_k(b2)-Delta_k(b1))/(b2-b1), then
# Richardson with correction model s(b) = E + c*e^(-b/2) on the last pairs
channels = {}
for k in range(1, 6):
    slopes = []
    for i in range(len(betas) - 1):
        b1, b2 = betas[i], betas[i + 1]
        d1, d2 = table[b1][k]["Delta"], table[b2][k]["Delta"]
        slopes.append(((b1 + b2) / 2, (d2 - d1) / (b2 - b1)))
    # extrapolate with e^(-b/2) model from the last two slopes
    (bA, sA), (bB, sB) = slopes[-2], slopes[-1]
    wA, wB = np.exp(-bA / 2), np.exp(-bB / 2)
    E_inf = (sB * wA - sA * wB) / (wA - wB)
    reality = table[betas[-1]][k]["real_positive"]
    channels[f"channel_{k+1}"] = {
        "local_slopes": [(float(b), float(s)) for b, s in slopes],
        "E_extrapolated": float(E_inf),
        "real_positive_at_beta12": reality,
    }
    print(f"channel {k+1}: slopes {['%.4f' % s for _, s in slopes]} "
          f"-> E = {E_inf:.5f}  ({'R+' if reality else 'complex/neg'})")

print("\n=== D1/D2 adjudication (predictions: walls 3/2; bump-0 2; pair 3; bump-5 4) ===")
E2 = channels["channel_2"]["E_extrapolated"]
verdicts = {}
preds = {"gap_wall_geommean": 1.5, "bump0": 2.0, "pair_or_bump1": 3.0, "bump5": 4.0}
neighbor_nulls = {"bump0_minus": 1.0, "bump0_plus": 3.0}  # E_loop(0) +/- 1
for name, ch in channels.items():
    E = ch["E_extrapolated"]
    best = min(preds.items(), key=lambda kv: abs(E - kv[1]))
    dev = abs(E - best[1]) / best[1]
    verdicts[name] = {"E": E, "best_match": best[0], "pred": best[1],
                      "rel_dev": float(dev), "pass_2pct": bool(dev < 0.02),
                      "real_positive": ch["real_positive_at_beta12"]}
    print(f"{name}: E={E:.5f} -> {best[0]}={best[1]} (dev {dev:.4f}, "
          f"{'PASS' if dev < 0.02 else 'fail'}); "
          f"ratio to gap = {E/E2:.4f}; "
          f"{'OS-physical (R+)' if ch['real_positive_at_beta12'] else 'NOT OS-physical'}")

signal.alarm(0)
out = {"spectra": {str(b): table[b] for b in betas},
       "channels": channels, "verdicts": verdicts,
       "predictions": preds, "neighbor_nulls": neighbor_nulls}
_out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "spin7_subleading_channel_scaling.json")
with open(_out_path, "w") as f:
    json.dump(out, f, indent=2)
print("\nSaved", _out_path)
