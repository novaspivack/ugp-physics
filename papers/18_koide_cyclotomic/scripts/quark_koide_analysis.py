"""Quark-sector Koide analysis.

Tests whether the canonical Koide relation

    Q = (m1 + m2 + m3) / (sqrt(m1) + sqrt(m2) + sqrt(m3))^2 = 2/3,

established for charged leptons, also holds for the up-type (u,c,t) and
down-type (d,s,b) quark sectors.

The GTE mechanism behind the lepton value (080-KOIDE-EQUALNORM) writes the
generation sqrt-mass vector as a Koide cone

    sqrt(m_k) = A (1 + b cos(theta + 2 pi k / 3)),  k = 0,1,2,

for which Sum sqrt(m) = 3A, Sum m = 3 A^2 (1 + b^2/2), hence

    Q = (1 + b^2 / 2) / 3   <=>   b^2 = 2 (3 Q - 1).

MDL/MaxEnt equipartition of the Frobenius norm across the two S3 irrep types
(trivial d=1, standard d=2) forces equal block norm => b^2 = d_standard = 2
=> Q = 2/3, for any N_gen >= 3 (Q = 2/N_gen). This script measures the actual
sector Q values and the implied b, and (Task 3) inverts Q = 2/3 to predict the
heaviest member of each sector from the two lighter ones.

PDG 2024 inputs (GeV): light quarks MS-bar at 2 GeV, heavy quarks MS-bar at m_q.
"""

import json
import math
import os

import numpy as np

# PDG quark masses (GeV)
m_u, m_c, m_t = 2.16e-3, 1.27, 172.69
m_d, m_s, m_b = 4.67e-3, 93.4e-3, 4.18

# PDG charged-lepton masses (GeV)
m_e, m_mu, m_tau = 0.511e-3, 105.658e-3, 1776.86e-3


def koide_Q(m1, m2, m3):
    """Canonical Koide quotient Q = Sum m / (Sum sqrt(m))^2 in [1/3, 1]."""
    s = math.sqrt(m1) + math.sqrt(m2) + math.sqrt(m3)
    return (m1 + m2 + m3) / s ** 2


def b_from_Q(Q):
    """Koide cone amplitude implied by Q: b^2 = 2(3Q - 1)."""
    val = 2 * (3 * Q - 1)
    return math.sqrt(val) if val >= 0 else float("nan")


def theta_from_masses(m1, m2, m3):
    """Recover the cone phase theta from the three sqrt-masses.

    sqrt(m_k) = A (1 + b cos(theta + 2 pi k / 3)) with A = mean(sqrt(m)).
    Returns theta in [0, 2pi) using the k=0,1 components (least-squares phase).
    """
    v = np.array([math.sqrt(m1), math.sqrt(m2), math.sqrt(m3)])
    A = v.mean()
    d = v / A - 1.0  # = b cos(theta + 2 pi k/3)
    # project onto cos/sin basis of the Z3 mode
    ck = np.cos(2 * np.pi * np.arange(3) / 3)
    sk = np.sin(2 * np.pi * np.arange(3) / 3)
    # d_k = b[cos theta cos(2pik/3) - sin theta sin(2pik/3)]
    X = (2.0 / 3.0) * np.dot(d, ck)   # = b cos theta
    Yc = -(2.0 / 3.0) * np.dot(d, sk)  # = b sin theta
    return math.atan2(Yc, X) % (2 * np.pi)


# ---------------------------------------------------------------------------
# Task 1: canonical Koide Q for each sector
# ---------------------------------------------------------------------------
Q_lep = koide_Q(m_e, m_mu, m_tau)
Q_up = koide_Q(m_u, m_c, m_t)
Q_down = koide_Q(m_d, m_s, m_b)

print("=== Task 1: canonical Koide Q (sqrt-mass form) ===")
print(f"Lepton    Q = {Q_lep:.6f}  (target 2/3 = {2/3:.6f}, dev "
      f"{(Q_lep-2/3)/(2/3)*100:+.3f}%)  b = {b_from_Q(Q_lep):.6f}")
print(f"Up-type   Q = {Q_up:.6f}  (dev {(Q_up-2/3)/(2/3)*100:+.3f}%)"
      f"  b = {b_from_Q(Q_up):.6f}")
print(f"Down-type Q = {Q_down:.6f}  (dev {(Q_down-2/3)/(2/3)*100:+.3f}%)"
      f"  b = {b_from_Q(Q_down):.6f}")
print(f"(lepton reference b = sqrt(2) = {math.sqrt(2):.6f})")

print("\n=== Cone parameters (b from Q, theta from sqrt-mass phases) ===")
fit_summary = {}
two_pi_9 = 2 * math.pi / 9
for label, masses in [("Leptons", (m_e, m_mu, m_tau)),
                      ("Up quarks", (m_u, m_c, m_t)),
                      ("Down quarks", (m_d, m_s, m_b))]:
    Q = koide_Q(*masses)
    b = b_from_Q(Q)
    theta = theta_from_masses(*masses)
    print(f"{label:12s}: Q = {Q:.6f}, b = {b:.6f} (b/sqrt2 = {b/math.sqrt(2):.4f}),"
          f" theta = {theta:.4f} rad = {theta/math.pi:.4f}*pi"
          f" (theta/(2pi/9) = {theta/two_pi_9:.4f})")
    fit_summary[label] = {
        "Q": float(Q),
        "b": float(b),
        "b_over_sqrt2": float(b / math.sqrt(2)),
        "theta_rad": float(theta),
        "theta_over_2pi9": float(theta / two_pi_9),
    }


# ---------------------------------------------------------------------------
# Task 3: invert Q = 2/3 to predict the heaviest member from the two lighter
#   s = sqrt(m3) solves  s^2 - 4 p s + (3 S - 2 p^2) = 0  with p = sqrt(m1)+sqrt(m2),
#   S = m1 + m2  ->  s = 2p +/- sqrt(6 p^2 - 3 S).  Heavy root takes '+'.
# ---------------------------------------------------------------------------
def koide_predict_heavy(m1, m2, target_Q=2/3):
    p = math.sqrt(m1) + math.sqrt(m2)
    S = m1 + m2
    # general target_Q: 3Q s^2 ... derive for target_Q
    # Q = (S + s^2)/(p+s)^2  =>  Q(p+s)^2 = S + s^2
    # (Q-1) s^2 + 2 Q p s + (Q p^2 - S) = 0
    a = (target_Q - 1)
    bb = 2 * target_Q * p
    cc = target_Q * p ** 2 - S
    disc = bb ** 2 - 4 * a * cc
    if disc < 0:
        return float("nan")
    r1 = (-bb + math.sqrt(disc)) / (2 * a)
    r2 = (-bb - math.sqrt(disc)) / (2 * a)
    roots = [r for r in (r1, r2) if r > 0]
    if not roots:
        return float("nan")
    s = max(roots)
    return s ** 2


print("\n=== Task 3: Koide Q=2/3 prediction for heaviest sector member ===")
m_tau_pred = koide_predict_heavy(m_e, m_mu)
m_t_pred = koide_predict_heavy(m_u, m_c)
m_b_pred = koide_predict_heavy(m_d, m_s)
print(f"m_tau pred (m_e,m_mu, Q=2/3) = {m_tau_pred*1000:.3f} MeV "
      f"(PDG {m_tau*1000:.3f} MeV, {(m_tau_pred-m_tau)/m_tau*100:+.3f}%)")
print(f"m_t   pred (m_u,m_c, Q=2/3) = {m_t_pred:.3f} GeV "
      f"(PDG {m_t:.3f} GeV, {(m_t_pred-m_t)/m_t*100:+.2f}%)")
print(f"m_b   pred (m_d,m_s, Q=2/3) = {m_b_pred:.3f} GeV "
      f"(PDG {m_b:.3f} GeV, {(m_b_pred-m_b)/m_b*100:+.2f}%)")


# ---------------------------------------------------------------------------
# Save artifacts
# ---------------------------------------------------------------------------
results = {
    "formula": "Q = (m1+m2+m3) / (sqrt(m1)+sqrt(m2)+sqrt(m3))^2 ; b^2 = 2(3Q-1)",
    "inputs_GeV": {
        "up_type": {"m_u": m_u, "m_c": m_c, "m_t": m_t},
        "down_type": {"m_d": m_d, "m_s": m_s, "m_b": m_b},
        "leptons": {"m_e": m_e, "m_mu": m_mu, "m_tau": m_tau},
    },
    "Q_lepton": float(Q_lep),
    "Q_up_type": float(Q_up),
    "Q_down_type": float(Q_down),
    "target_2_3": 2 / 3,
    "deviation_pct": {
        "lepton": float((Q_lep - 2/3) / (2/3) * 100),
        "up_type": float((Q_up - 2/3) / (2/3) * 100),
        "down_type": float((Q_down - 2/3) / (2/3) * 100),
    },
    "b_implied": {
        "lepton": float(b_from_Q(Q_lep)),
        "up_type": float(b_from_Q(Q_up)),
        "down_type": float(b_from_Q(Q_down)),
        "lepton_target_sqrt2": math.sqrt(2),
    },
    "cone_fits": fit_summary,
    "Q23_predictions": {
        "m_tau_pred_GeV": float(m_tau_pred), "m_tau_pdg_GeV": m_tau,
        "m_tau_err_pct": float((m_tau_pred - m_tau) / m_tau * 100),
        "m_t_pred_GeV": float(m_t_pred), "m_t_pdg_GeV": m_t,
        "m_t_err_pct": float((m_t_pred - m_t) / m_t * 100),
        "m_b_pred_GeV": float(m_b_pred), "m_b_pdg_GeV": m_b,
        "m_b_err_pct": float((m_b_pred - m_b) / m_b * 100),
    },
}

out_dir = os.path.dirname(os.path.abspath(__file__))
out_path = os.path.join(out_dir, "quark_koide_analysis_results.json")
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)

print("\n=== Summary ===")
print(f"Lepton  Q = {Q_lep:.6f}  ({(Q_lep-2/3)/(2/3)*100:+.3f}% from 2/3)  -> Koide HOLDS")
print(f"Up-type Q = {Q_up:.6f}  ({(Q_up-2/3)/(2/3)*100:+.3f}% from 2/3)")
print(f"Down    Q = {Q_down:.6f}  ({(Q_down-2/3)/(2/3)*100:+.3f}% from 2/3)")
print(f"Artifact written: {out_path}")
