"""Spectral census of the spin-7 transfer matrix at the CMCA physical point.

Consequence check of the MDL-saturation derivation (OQ-088-R26b): if the
physical point a = hbar*c/Lambda_GTE is where the tape's faithful channel
content exactly matches the F21 EFT window, the transfer spectrum at
beta* = 1.53459777 (xi = 7 exact) should show structure at the lattice-units
EFT boundary Delta = a*Lambda/hbar*c = 1.

PRE-REGISTERED battery (declared before computation):
  A1: count of channels with Delta_k = ln(lambda_1/|lambda_k|) <= 1
      candidates {7, 14, 21, 49} (exact integer match)
  A2: count of real-positive eigenvalues (OS-positive physical channels)
      candidates {7, 14, 21, 49} (exact)
  A3: does the real-positive set terminate at Delta = 1?  (binary)
  nulls (n-a): same counts at beta in {1.0, 1.2, 1.8, 2.0, 2.5}
  nulls (n-b): same census for two non-GTE GF(7) multilinear rules at their
      own xi = 7 points (mirror-composite rule; pseudo-random rule seed 88)
  A4: entropy capacities S*.xi vs {ln3, 1} tol 1%; h*.xi vs {6ln2, 4, ln70}
      tol 0.5%; with candidate-density disclosure (ln-integer count in window)

Expected output ranges: beta* ~ 1.5346, Delta_2 = 1/7; census counts unknown
(that is the point of the test).
"""

import json
import os
import signal
import sys

import numpy as np

TIMEOUT_SECONDS = 600


def _timeout(s, f):
    print("TIMEOUT reached. Exiting.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

Q = 7


def p_gte(L, C, R):
    return (C + R - C * R - L * C * R) % Q


def p_mirror_comp(L, C, R):
    # non-GTE null rule 1: L+C-LC-LCR (structurally similar, not MDL-selected)
    return (L + C - L * C - L * C * R) % Q


_rng = np.random.default_rng(88)
_COEF = _rng.integers(0, Q, size=8)  # 1,L,C,R,LC,LR,CR,LCR


def p_random(L, C, R):
    c = _COEF
    return int(c[0] + c[1] * L + c[2] * C + c[3] * R + c[4] * L * C
               + c[5] * L * R + c[6] * C * R + c[7] * L * C * R) % Q


def transfer(beta, rule):
    M = np.zeros((Q * Q, Q * Q))
    for a in range(Q):
        for b in range(Q):
            for c in range(Q):
                M[a * Q + b, b * Q + c] = np.exp(-beta * rule(a, b, c))
    return M


def census(beta, rule, tol_imag=1e-9):
    ev = np.linalg.eigvals(transfer(beta, rule))
    order = np.argsort(-np.abs(ev))
    ev = ev[order]
    lam1 = np.abs(ev[0])
    delta = np.log(lam1 / np.abs(ev))
    real_pos = (np.abs(ev.imag) < tol_imag * lam1) & (ev.real > 0)
    real_neg = (np.abs(ev.imag) < tol_imag * lam1) & (ev.real < 0)
    n_le1 = int(np.sum(delta <= 1.0 + 1e-12))
    n_rp = int(np.sum(real_pos))
    rp_deltas = np.sort(delta[real_pos])
    nonrp_deltas = np.sort(delta[~real_pos])
    # A3: all real-positive Delta <= 1 AND all Delta > 1 non-real-positive?
    a3 = bool(rp_deltas.size and rp_deltas[-1] <= 1.0 + 1e-9
              and (nonrp_deltas.size == 0 or nonrp_deltas[0] > 1.0 - 1e-9))
    return {
        "beta": float(beta),
        "lambda1": float(lam1),
        "Delta_spectrum_first12": [float(d) for d in delta[:12]],
        "n_channels_Delta_le_1": n_le1,
        "n_real_positive": n_rp,
        "n_real_negative": int(np.sum(real_neg)),
        "n_complex": int(Q * Q - n_rp - np.sum(real_neg)),
        "max_Delta_real_positive": float(rp_deltas[-1]) if rp_deltas.size else None,
        "min_Delta_non_real_positive": float(nonrp_deltas[0]) if nonrp_deltas.size else None,
        "real_positive_Deltas": [float(d) for d in rp_deltas],
        "A3_rp_terminates_at_1": a3,
    }


def xi(beta, rule):
    ev = np.sort(np.abs(np.linalg.eigvals(transfer(beta, rule))))[::-1]
    return 1.0 / np.log(ev[0] / ev[1])


def solve_beta_xi7(rule):
    lo, hi = 0.3, 6.0
    if (xi(lo, rule) - 7.0) * (xi(hi, rule) - 7.0) > 0:
        return None
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if xi(mid, rule) < 7.0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


print("=== Battery A: spectral census at the physical point ===")
beta_star = solve_beta_xi7(p_gte)
print(f"beta* (GTE rule, xi = 7) = {beta_star:.8f}")
c_star = census(beta_star, p_gte)
print(json.dumps({k: v for k, v in c_star.items()
                  if k != "real_positive_Deltas"}, indent=2))
print("real-positive Delta ladder:",
      ["%.5f" % d for d in c_star["real_positive_Deltas"]])

print("\n--- null (n-a): same census at other beta ---")
nulls_beta = {}
for b in [1.0, 1.2, 1.8, 2.0, 2.5]:
    c = census(b, p_gte)
    nulls_beta[str(b)] = c
    print(f"beta={b}: n(Delta<=1)={c['n_channels_Delta_le_1']}, "
          f"n_real_pos={c['n_real_positive']}, "
          f"maxDelta_rp={c['max_Delta_real_positive']:.4f}, A3={c['A3_rp_terminates_at_1']}")

print("\n--- null (n-b): non-GTE rules at their own xi = 7 points ---")
nulls_rule = {}
for name, rule in [("mirror_composite", p_mirror_comp), ("random_seed88", p_random)]:
    bs = solve_beta_xi7(rule)
    if bs is None:
        print(f"{name}: no xi = 7 point in beta range [0.3, 6] -- recorded")
        nulls_rule[name] = {"beta_star": None}
        continue
    c = census(bs, rule)
    nulls_rule[name] = c
    print(f"{name}: beta*={bs:.5f}, n(Delta<=1)={c['n_channels_Delta_le_1']}, "
          f"n_real_pos={c['n_real_positive']}, "
          f"maxDelta_rp={c['max_Delta_real_positive']:.4f}, A3={c['A3_rp_terminates_at_1']}")

print("\n=== A4: entropy capacities (with density disclosure) ===")
S_star = np.log(c_star["lambda1"])
h_eps = 1e-5
lp = np.log(np.sort(np.abs(np.linalg.eigvals(transfer(beta_star + h_eps, p_gte))))[-1])
lm = np.log(np.sort(np.abs(np.linalg.eigvals(transfer(beta_star - h_eps, p_gte))))[-1])
u_star = -(lp - lm) / (2 * h_eps)
h_star = S_star + beta_star * u_star
cap_S = 7 * S_star
cap_h = 7 * h_star
print(f"S* = {S_star:.8f}; h* = {h_star:.8f}")
print(f"S*.xi = {cap_S:.6f}: vs ln3={np.log(3):.6f} "
      f"(dev {abs(cap_S-np.log(3))/np.log(3):.4f}), vs 1 (dev {abs(cap_S-1):.4f})")
print(f"h*.xi = {cap_h:.6f}: vs 6ln2={6*np.log(2):.6f} "
      f"(dev {abs(cap_h-6*np.log(2))/(6*np.log(2)):.4f}), "
      f"vs 4 (dev {abs(cap_h-4)/4:.4f}), vs ln70={np.log(70):.6f} "
      f"(dev {abs(cap_h-np.log(70))/np.log(70):.4f})")
# density disclosure: ln-integer candidates within tolerance windows
win_S = [n for n in range(2, 30) if abs(cap_S - np.log(n)) / np.log(n) < 0.01]
win_h = [n for n in range(2, 200) if abs(cap_h - np.log(n)) / np.log(n) < 0.005]
print(f"density: ln-integers within 1% of S*.xi: {win_S}")
print(f"density: ln-integers within 0.5% of h*.xi: {win_h}")

signal.alarm(0)
out = {
    "beta_star": beta_star,
    "census_at_physical_point": c_star,
    "nulls_beta": nulls_beta,
    "nulls_rule": nulls_rule,
    "entropy_capacity": {
        "S_star": float(S_star), "h_star": float(h_star),
        "S_xi": float(cap_S), "h_xi": float(cap_h),
        "ln_integer_density_S_1pct": win_S,
        "ln_integer_density_h_0p5pct": win_h,
    },
}
_out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "cmca_spectral_census_physical_point.json")
with open(_out_path, "w") as f:
    json.dump(out, f, indent=2)
print("\nSaved", _out_path)
