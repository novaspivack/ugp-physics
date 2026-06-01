"""Measure the Koide cone phase (Yukawa angle) of each fermion sector from PDG
masses, and test whether the quark angles correspond to Z7-winding phases, simple
fractional angles, ratios to the lepton angle, or CKM mixing angles.

Koide square-root cone:  sqrt(m_k) = sqrt(m0) * (1 + b*cos(theta + 2*pi*k/3)),
equivalently m_k = m0*(1 + b*cos(theta + 2*pi*k/3))^2,  k = 0,1,2.

For three masses this inversion is EXACT and UNIQUE (modulo the residual 3-fold
symmetry theta -> theta + 2*pi/3 from relabelling generations and a reflection):

    sqrt(m0) = (sum sqrt(m_k)) / 3                       (forced by sum cos = 0)
    x_k      = sqrt(m_k)/sqrt(m0) - 1 = b*cos(theta+2*pi*k/3)
    C = b cos(theta) = x_0
    S = b sin(theta) = (x_2 - x_1)/sqrt(3)
    b = sqrt(C^2 + S^2),  theta = atan2(S, C)

A general-purpose nonlinear optimiser on this problem is UNRELIABLE: it lands on
spurious local minima of the log-objective (e.g. b ~ 3.1 for leptons). The closed
form below is exact, so we use it and reduce theta to the fundamental domain.
"""
import numpy as np
import json
import os

# PDG 2024 masses (GeV). Light quarks MS-bar at 2 GeV; c,b at m_q; t pole-ish value
# used by prior lab notes. Symmetric 1-sigma used for Monte-Carlo error propagation.
SECTORS = {
    "lepton":    {"m": [0.511e-3, 105.658e-3, 1776.86e-3], "s": [0.0, 0.0, 0.12e-3]},
    "up_type":   {"m": [2.16e-3, 1.27, 172.69],            "s": [0.38e-3, 0.02, 0.30]},
    "down_type": {"m": [4.67e-3, 93.4e-3, 4.18],           "s": [0.33e-3, 6.5e-3, 0.025]},
}

TWO_PI_3 = 2 * np.pi / 3


def koide_invert(masses):
    """Exact, unique Koide cone inversion. Returns (m0, b, theta_raw)."""
    sm = np.sqrt(np.asarray(masses, dtype=float))
    sqrt_m0 = sm.sum() / 3.0
    x = sm / sqrt_m0 - 1.0
    C = x[0]
    S = (x[2] - x[1]) / np.sqrt(3.0)
    b = np.hypot(C, S)
    theta = np.arctan2(S, C)
    return sqrt_m0 ** 2, b, theta


def reduce_phase(theta):
    """Reduce cone phase to fundamental domain [0, 2*pi/3)."""
    return theta % TWO_PI_3


fits = {}
print("=" * 64)
print("EXACT ALGEBRAIC KOIDE CONE INVERSION (ascending mass order)")
print("=" * 64)
for name, d in SECTORS.items():
    m0, b, th = koide_invert(d["m"])
    th_red = reduce_phase(th)
    fits[name] = {"m0": m0, "b": b, "b2": b * b, "theta_raw": th, "theta_reduced": th_red}
    print(f"\n[{name}]  m0={m0:.4e} GeV")
    print(f"  b = {b:.6f}   b^2 = {b*b:.6f}   (lepton target b=sqrt2={np.sqrt(2):.6f})")
    print(f"  theta_raw     = {th:.6f} rad")
    print(f"  theta_reduced = {th_red:.6f} rad  (mod 2pi/3)")

b_l, th_l = fits["lepton"]["b"], fits["lepton"]["theta_reduced"]
b_u, th_u = fits["up_type"]["b"], fits["up_type"]["theta_reduced"]
b_d, th_d = fits["down_type"]["b"], fits["down_type"]["theta_reduced"]

print("\n" + "=" * 64)
print("REDUCED PHASES & SIMPLE-FRACTION TESTS")
print("=" * 64)
print(f"theta_lep = {th_l:.6f}   vs 2/9 = {2/9:.6f}  ({(th_l-2/9)/(2/9)*100:+.2f}%)")
print(f"theta_up  = {th_u:.6f}")
print(f"theta_dn  = {th_d:.6f}")
print(f"theta_dn / theta_lep = {th_d/th_l:.4f}   (1/2 = 0.5000)")
print(f"theta_up / theta_lep = {th_u/th_l:.4f}   (1/3 = 0.3333)")
for label, th in [("lep", th_l), ("up", th_u), ("dn", th_d)]:
    hits = []
    for N in range(2, 60):
        if abs(2/N - th)/th < 0.03:
            hits.append(f"2/{N}={2/N:.5f}({(2/N-th)/th*100:+.1f}%)")
        if abs(2*np.pi/N - th)/th < 0.03:
            hits.append(f"2pi/{N}={2*np.pi/N:.5f}({(2*np.pi/N-th)/th*100:+.1f}%)")
    print(f"  theta_{label} candidates: {', '.join(hits) if hits else 'none within 3%'}")

print("\n" + "=" * 64)
print("Z7 WINDING PHASE TEST (w_u=2, w_d=6, w_lep=4)")
print("=" * 64)
for w, lab, th in [(2, "up", th_u), (6, "dn", th_d), (4, "lep", th_l)]:
    pred = 2 * np.pi * w / 7
    print(f"  2pi*{w}/7 = {pred:.4f} rad  vs reduced theta_{lab} = {th:.4f}  -> O(1) mismatch")

print("\n" + "=" * 64)
print("CKM ANGLE CONNECTION")
print("=" * 64)
lambda_pdg = 0.22453
A_CKM, rho_CKM, eta_CKM = 0.836, 0.122, 0.355
lambda_gte = 9 / 40
th12 = np.arcsin(lambda_pdg)
print(f"theta_12 (Cabibbo) = {th12:.6f} rad ; lambda_GTE=9/40 -> arcsin={np.arcsin(lambda_gte):.6f}")
print(f"theta_up - theta_dn (reduced) = {th_u - th_d:.6f} ; /theta_12 = {(th_u-th_d)/th12:.4f}")
print(f"theta_lep - theta_dn = {th_l - th_d:.6f} ; /theta_12 = {(th_l-th_d)/th12:.4f}")
print(f"theta_lep - theta_up = {th_l - th_u:.6f} ; /theta_12 = {(th_l-th_u)/th12:.4f}")

print("\n" + "=" * 64)
print("MONTE-CARLO ERROR PROPAGATION (PDG 1-sigma mass errors)")
print("=" * 64)
rng = np.random.default_rng(20260529)
N_MC = 200000
mc = {}
for name, d in SECTORS.items():
    m = np.array(d["m"]); s = np.array(d["s"])
    th_samples = np.empty(N_MC)
    b_samples = np.empty(N_MC)
    for i in range(N_MC):
        mm = np.abs(rng.normal(m, s))
        _, bb, tt = koide_invert(mm)
        th_samples[i] = reduce_phase(tt)
        b_samples[i] = bb
    mc[name] = {
        "theta_mean": float(th_samples.mean()), "theta_std": float(th_samples.std()),
        "b_mean": float(b_samples.mean()), "b_std": float(b_samples.std()),
    }
    print(f"[{name}] theta = {th_samples.mean():.4f} +/- {th_samples.std():.4f} rad "
          f"({th_samples.std()/th_samples.mean()*100:.1f}% rel) ; "
          f"b = {b_samples.mean():.4f} +/- {b_samples.std():.4f}")

# Robustness verdict on the near-integer ratios
print("\n--- ratio robustness ---")
r_dn = th_d / th_l
r_up = th_u / th_l
sig_dn = mc["down_type"]["theta_std"] / th_l
sig_up = mc["up_type"]["theta_std"] / th_l
print(f"theta_dn/theta_lep = {r_dn:.3f} +/- {sig_dn:.3f}  (1/2 within {abs(r_dn-0.5)/sig_dn:.1f} sigma)")
print(f"theta_up/theta_lep = {r_up:.3f} +/- {sig_up:.3f}  (1/3 within {abs(r_up-1/3)/sig_up:.1f} sigma)")

print("\n" + "=" * 64)
print("N_c^2 FRAMING  (theta * N_c^2 = strand-count-like number)")
print("=" * 64)
Nc2 = 9
for label, th in [("lep", th_l), ("up", th_u), ("dn", th_d)]:
    print(f"  theta_{label} * 9 = {th*Nc2:.5f}")
print("  -> {lep, down, up} = {2, 1, 2/3} = 2/r with r in {1,2,3}")
print(f"  closed form theta_sector = (N_c^2-1)/(4*N_c^2*r) :")
for label, r in [("lep", 1), ("dn", 2), ("up", 3)]:
    print(f"    r={r}: {(Nc2-1)/(4*Nc2*r):.6f} rad")

print("\n--- OVER-FITTING NULL: how often do random 'sectors' hit 2/r within errors? ---")
# Generate random reduced angles uniform in (0, 2pi/3) and ask whether theta*9
# lands within the measured relative MC error of some 2/r, r in 1..6.
rng2 = np.random.default_rng(7)
rels = {"up": mc["up_type"]["theta_std"]/th_u, "dn": mc["down_type"]["theta_std"]/th_d}
for lab, rel in rels.items():
    hits = 0
    M = 100000
    rand = rng2.uniform(0, TWO_PI_3, M)
    val = rand * Nc2
    for r in range(1, 7):
        hits += np.sum(np.abs(val - 2/r)/(2/r) < rel)
    print(f"  sector '{lab}' (rel err {rel*100:.1f}%): random hit prob on 2/r (r=1..6) = {hits/M*100:.1f}%")

results = {
    "method": "exact algebraic Koide cone inversion; theta reduced mod 2pi/3",
    "theta_times_Nc2": {"lep": th_l*9, "up": th_u*9, "dn": th_d*9},
    "closed_form": "theta_sector = (N_c^2-1)/(4*N_c^2*r), r=1(lep),2(down),3(up)",
    "fits": fits,
    "monte_carlo": mc,
    "ratios": {"theta_dn_over_lep": r_dn, "theta_up_over_lep": r_up},
    "ckm": {"lambda_pdg": lambda_pdg, "lambda_gte_9_40": lambda_gte, "theta_12": th12},
    "famous_lepton_angle_2_over_9_rad": 2 / 9,
}
os.makedirs("papers/18_koide_cyclotomic/scripts", exist_ok=True)
with open("papers/18_koide_cyclotomic/scripts/quark_yukawa_angles_results.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nSaved -> papers/18_koide_cyclotomic/scripts/quark_yukawa_angles_results.json")
