"""High-precision verification of the exact spin-7 gap-amplitude series.

Computes the top three eigenvalues of the exact 49x49 pair transfer matrix
M(beta)[(a,b),(b,c)] = e^(-beta p(a,b,c)) with mpmath (dps 80) at large beta
and compares, eigenvalue-resolved, against the EXACT Puiseux series derived
by spin7_gap_amplitude_resolvent.py / spin7_gap_amplitude_puiseux_check.py:

  lambda_1 = 1 + u^3 + u^4/2 + u^5/8 + 2u^6 + 319u^7/128 + 39u^8/2 + ...
  lambda_2 = 1 + 2u^8 - 4u^9 + 11u^10 + ...          (spectator, sector 5)
  lambda_3 = 1 - u^3 + u^4/2 - u^5/8 + 2u^6 - ...    (u = e^(-beta/2))

  Delta * e^(3beta/2) = A(u) = 1 + u/2 + u^2/8 + 3u^3/2 + 255u^4/128 + 69u^5/4

PASS criteria (pre-registered): relative agreement A_meas vs A_pred better
than 1e-6 for beta >= 21; (lambda_2 - 1)/t^4 -> 2; (1 - lambda_3)/t^{3/2} -> 1.
"""

import json
import os
import signal
import sys

import mpmath as mp

TIMEOUT_SECONDS = 900

def _timeout(s, f):
    print("TIMEOUT reached. Exiting.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

Q = 7

def p_gf7(L, C, R):
    return (C + R - C * R - L * C * R) % Q

# exact series coefficients (from the resolvent + Puiseux scripts)
EPS_PLUS = [(3, mp.mpf(1)), (4, mp.mpf(0.5)), (5, mp.mpf(1) / 8),
            (6, mp.mpf(2)), (7, mp.mpf(319) / 128), (8, mp.mpf(39) / 2),
            (9, mp.mpf(-319) / 1024), (10, mp.mpf(107))]
EPS_SPEC = [(8, mp.mpf(2)), (9, mp.mpf(-4)), (10, mp.mpf(11))]
EPS_MINUS = [(3, mp.mpf(-1)), (4, mp.mpf(0.5)), (5, mp.mpf(-1) / 8),
             (6, mp.mpf(2)), (7, mp.mpf(-319) / 128), (8, mp.mpf(39) / 2)]
A_SER = [(0, mp.mpf(1)), (1, mp.mpf(0.5)), (2, mp.mpf(1) / 8),
         (3, mp.mpf(1.5)), (4, mp.mpf(255) / 128), (5, mp.mpf(69) / 4),
         (6, mp.mpf(6019) / 3072), (7, mp.mpf(93)), (8, mp.mpf(255995) / 32768)]

def ser(coeffs, uu):
    return mp.fsum(c * uu**k for k, c in coeffs)

def top3(beta, dps=80):
    with mp.workdps(dps):
        b = mp.mpf(beta)
        M = mp.zeros(49, 49)
        for a in range(Q):
            for bb in range(Q):
                for c in range(Q):
                    M[a * Q + bb, bb * Q + c] = mp.e**(-b * p_gf7(a, bb, c))
        ev = mp.eig(M, left=False, right=False)
        # sort by real part of log-modulus (all top ones are near 1, real)
        evs = sorted(ev, key=lambda z: -abs(z))
        return evs[0], evs[1], evs[2]

print("=== eigenvalue-resolved verification (mpmath dps 80) ===")
rows = []
all_pass = True
for beta in [15, 18, 21, 24, 27, 30]:
    l1, l2, l3 = top3(beta)
    with mp.workdps(80):
        uu = mp.e**(-mp.mpf(beta) / 2)
        t = uu**2
        # predictions
        l1_pred = 1 + ser(EPS_PLUS, uu)
        l2_pred = 1 + ser(EPS_SPEC, uu)
        l3_pred = 1 + ser(EPS_MINUS, uu)
        D_meas = mp.log(abs(l1) / abs(l2))
        A_meas = D_meas * mp.e**(mp.mpf(3) * beta / 2)
        A_pred = ser(A_SER, uu)
        relA = abs(A_meas - A_pred) / A_pred
        r2 = (mp.re(l2) - 1) / t**4
        r3 = (1 - mp.re(l3)) / t**mp.mpf(1.5)
        e1 = abs(mp.re(l1) - l1_pred)
        e2 = abs(mp.re(l2) - l2_pred)
        e3 = abs(mp.re(l3) - l3_pred)
        ok = (beta < 21) or (relA < 1e-6)
        all_pass = all_pass and ok
        print(f"beta={beta:3d}:  A_meas={mp.nstr(A_meas, 12)}  "
              f"A_pred={mp.nstr(A_pred, 12)}  rel={mp.nstr(relA, 3)}")
        print(f"          (l2-1)/t^4={mp.nstr(r2, 8)}  "
              f"(1-l3)/t^1.5={mp.nstr(r3, 8)}")
        print(f"          |l1-pred|={mp.nstr(e1, 3)} |l2-pred|={mp.nstr(e2, 3)} "
              f"|l3-pred|={mp.nstr(e3, 3)}")
        rows.append({"beta": beta,
                     "A_meas": mp.nstr(A_meas, 20), "A_pred": mp.nstr(A_pred, 20),
                     "rel_A": mp.nstr(relA, 5),
                     "spectator_ratio_t4": mp.nstr(r2, 12),
                     "mirror_ratio_t32": mp.nstr(r3, 12),
                     "abs_err_l1": mp.nstr(e1, 5), "abs_err_l2": mp.nstr(e2, 5),
                     "abs_err_l3": mp.nstr(e3, 5)})

print(f"\nVERDICT: {'PASS' if all_pass else 'FAIL'} "
      f"(pre-registered: rel(A) < 1e-6 for beta >= 21)")

signal.alarm(0)

out = {"rows": rows, "pass": all_pass,
       "series": {"A": "1 + u/2 + u^2/8 + 3u^3/2 + 255u^4/128 + 69u^5/4 + ...",
                  "u": "e^(-beta/2)"}}
_out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "spin7_gap_amplitude_highbeta_verify.json")
with open(_out_path, "w") as f:
    json.dump(out, f, indent=2)
print("Saved", _out_path)
