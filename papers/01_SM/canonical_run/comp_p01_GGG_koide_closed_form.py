"""
COMP-P01-GGG: Koide algebraic closed form and cyclotomic-12 identification
              (Priority 7 / 03_SPEC / OP(vii), Round 33).

CLAIM R33-A: Koide Q(v) = 2/3 is EXACTLY the statement that v = (√m_e,
             √m_μ, √m_τ) makes a 45° angle with the democratic axis
             ê = (1,1,1)/√3.  (Geometric reformulation.)

CLAIM R33-B: Given r_e and r_μ, the Koide-conforming r_τ is the positive
             root of z² - 4z(x+y) + (x²+y²-4xy) = 0 with (x,y) = (r_e,r_μ):

                r_τ = 2(r_e + r_μ) + √3 · √(r_e² + 4·r_e·r_μ + r_μ²)

CLAIM R33-C: The coefficients in the solved form are CYCLOTOMIC-12 UGP atoms:
             (2 + √3) = 4·cos²(π/12)              (exact)
             (1 + √3) = 2√2 · cos(π/12)            (exact)
             This ties Koide to the π/12 (same family as α = π/6 in
             Round 13's TT derivation).

CLAIM R33-D: At PDG precision, m_τ predicted from m_e and m_μ via R33-B
             reproduces PDG to <= 1e-4, limited only by Koide's own
             deviation from Q = 2/3 at PDG.

NULL DISCIPLINE:
  - Random v in ℝ³: prob(on 45° cone) = 0 (measure-zero).
  - 10^6-trial uniform-random log-mass triples vs Koide hit-rate.
  - Test predictive power: given random (r_e, r_μ) in a physical range,
    the Koide-predicted r_τ should NOT match random third-generation values.
"""

import math, json, hashlib, datetime, os, sys
import numpy as np

# =====================================================================
# PDG 2022 charged-lepton masses (GeV)
# =====================================================================
m_e_PDG = 0.0005109989461     # electron
m_mu_PDG = 0.1056583755       # muon
m_tau_PDG = 1.77686           # tau (central)
m_tau_PDG_err = 0.00012       # tau uncertainty

r_e  = math.sqrt(m_e_PDG)
r_mu = math.sqrt(m_mu_PDG)
r_tau_PDG = math.sqrt(m_tau_PDG)

# =====================================================================
# Claim R33-A: angle interpretation
# =====================================================================
print("=" * 72)
print("COMP-P01-GGG: Koide algebraic closed form (Round 33 / OP(vii))")
print("=" * 72)
print()
print("PDG charged-lepton sqrt-masses (GeV^{1/2}):")
print(f"  r_e  = {r_e:.8f}")
print(f"  r_mu = {r_mu:.8f}")
print(f"  r_tau = {r_tau_PDG:.8f}  (PDG)")
print()

v = np.array([r_e, r_mu, r_tau_PDG])
e_hat = np.array([1.0, 1.0, 1.0]) / math.sqrt(3)
cos_theta = np.dot(v, e_hat) / np.linalg.norm(v)
theta_rad = math.acos(cos_theta)
theta_deg = math.degrees(theta_rad)

print(f"Claim R33-A: angle(v, e_hat) = {theta_deg:.6f}° (expected 45.000000°)")
print(f"  Deviation from 45°: {theta_deg - 45.0:+.6f}° = {(theta_deg-45.0)*3600:+.2f} arcsec")
print(f"  Cos(angle) = {cos_theta:.8f} (expected 1/√2 = {1/math.sqrt(2):.8f})")
print()

# Koide Q value
Q_val = (m_e_PDG + m_mu_PDG + m_tau_PDG) / (r_e + r_mu + r_tau_PDG)**2
print(f"Koide Q(v) = {Q_val:.8f} (expected 2/3 = {2/3:.8f})")
print(f"  Deviation from 2/3: {Q_val - 2/3:+.2e} = {(Q_val-2/3)/(2/3)*100:+.4f}%")

# =====================================================================
# Claim R33-B: solved form of Koide (positive root)
# =====================================================================
print()
print("Claim R33-B: Koide solved form")
print("  r_τ = 2(r_e + r_μ) + √3 · √(r_e² + 4·r_e·r_μ + r_μ²)")

disc = r_e**2 + 4*r_e*r_mu + r_mu**2
r_tau_pred = 2*(r_e + r_mu) + math.sqrt(3) * math.sqrt(disc)
r_tau_pred_minus = 2*(r_e + r_mu) - math.sqrt(3) * math.sqrt(disc)

print(f"  r_τ predicted (+ root): {r_tau_pred:.8f}")
print(f"  r_τ predicted (- root): {r_tau_pred_minus:.8f}")
print(f"  r_τ PDG:                {r_tau_PDG:.8f}")
print(f"  Δr_τ  = {r_tau_pred - r_tau_PDG:+.2e} ({(r_tau_pred-r_tau_PDG)/r_tau_PDG*100:+.5f}%)")

m_tau_pred = r_tau_pred**2
print(f"  m_τ predicted: {m_tau_pred:.6f} GeV")
print(f"  m_τ PDG:       {m_tau_PDG:.6f} GeV")
print(f"  Δm_τ  = {m_tau_pred - m_tau_PDG:+.2e} GeV")
print(f"  Rel. err: {(m_tau_pred-m_tau_PDG)/m_tau_PDG*1e6:+.2f} ppm")
print(f"  PDG σ on m_τ: {m_tau_PDG_err:.2e} GeV")
print(f"  Deviation in σ_PDG: {abs(m_tau_pred-m_tau_PDG)/m_tau_PDG_err:.2f}σ")

# =====================================================================
# Claim R33-C: cyclotomic-12 UGP atom identification
# =====================================================================
print()
print("Claim R33-C: Cyclotomic-12 UGP atom identification")
# (2+√3) = 4·cos²(π/12)
lhs = 2 + math.sqrt(3)
rhs = 4 * math.cos(math.pi/12)**2
print(f"  (2+√3)      = {lhs:.12f}")
print(f"  4·cos²(π/12) = {rhs:.12f}")
print(f"  Match: {abs(lhs-rhs):.2e} (expected 0 exactly)")

# (1+√3) = 2√2·cos(π/12)
lhs2 = 1 + math.sqrt(3)
rhs2 = 2 * math.sqrt(2) * math.cos(math.pi/12)
print(f"  (1+√3)      = {lhs2:.12f}")
print(f"  2√2·cos(π/12) = {rhs2:.12f}")
print(f"  Match: {abs(lhs2-rhs2):.2e} (expected 0 exactly)")

# Koide leading-order ratio m_τ/m_μ
print()
leading_ratio = (2+math.sqrt(3))**2  # (2+√3)² = 7+4√3
print(f"  Leading-order (r_e → 0) : r_τ/r_μ → 2+√3 = {(2+math.sqrt(3)):.4f}")
print(f"                            m_τ/m_μ → (2+√3)² = 7+4√3 = {leading_ratio:.4f}")
print(f"  PDG m_τ/m_μ = {m_tau_PDG/m_mu_PDG:.4f}")
print(f"  Relative correction from finite r_e: {((m_tau_PDG/m_mu_PDG)/leading_ratio - 1)*100:+.2f}%")

# =====================================================================
# Null discipline
# =====================================================================
print()
print("=" * 72)
print("Null discipline:")
print("=" * 72)

# Null 1: random (r_e, r_μ) in physical range, see if Koide-predicted r_τ
# matches random r_τ samples from a physical range
np.random.seed(42)
N = 100000
# r_e uniform in [0.001, 0.1], r_μ uniform in [0.1, 1.0], r_τ uniform in [0.5, 5.0]
re_rand = np.random.uniform(0.001, 0.1, N)
rmu_rand = np.random.uniform(0.1, 1.0, N)
rtau_rand = np.random.uniform(0.5, 5.0, N)
rtau_koide = 2*(re_rand + rmu_rand) + np.sqrt(3)*np.sqrt(re_rand**2 + 4*re_rand*rmu_rand + rmu_rand**2)

# Count fraction where Koide-predicted rtau matches the RANDOM rtau within 1%
match_pct_1 = np.mean(np.abs(rtau_rand - rtau_koide)/rtau_koide < 0.01) * 100
match_pct_10 = np.mean(np.abs(rtau_rand - rtau_koide)/rtau_koide < 0.10) * 100
print(f"N = {N} random (r_e, r_μ, r_τ) triples:")
print(f"  Koide-prediction matches random r_τ within 1%:  {match_pct_1:.2f}%")
print(f"  Koide-prediction matches random r_τ within 10%: {match_pct_10:.2f}%")

# Null 2: test the geometric claim — random v in R^3 vs 45° cone
N2 = 1000000
v_rand = np.random.uniform(0.01, 2.0, (N2, 3))
dots = v_rand @ e_hat
norms = np.linalg.norm(v_rand, axis=1)
cos_thetas = dots / norms
theta_devs = np.abs(np.arccos(cos_thetas) - math.pi/4) * 180/math.pi
within_1deg = np.sum(theta_devs < 1.0)
within_0p1deg = np.sum(theta_devs < 0.1)
print()
print(f"N2 = {N2} random v ∈ [0.01, 2]³:")
print(f"  Within 1° of 45° cone: {within_1deg}/{N2} = {within_1deg/N2*100:.4f}%")
print(f"  Within 0.1° of 45° cone: {within_0p1deg}/{N2} = {within_0p1deg/N2*100:.6f}%")
print(f"  PDG lepton v: 45° to {abs(theta_deg-45.0)*60:.4f} arcmin")

# =====================================================================
# Artifact
# =====================================================================
prediction = {
    "experiment_id": "COMP-P01-GGG",
    "title": "Koide algebraic closed form + cyclotomic-12 identification (Priority 7 / OP(vii))",
    "date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "inputs": {
        "m_e_PDG_GeV": m_e_PDG,
        "m_mu_PDG_GeV": m_mu_PDG,
        "m_tau_PDG_GeV": m_tau_PDG,
    },
    "claims": {
        "R33_A_geometric_angle_deg": theta_deg,
        "R33_A_expected_deg": 45.0,
        "R33_A_deviation_arcsec": (theta_deg-45.0)*3600,
        "R33_B_r_tau_predicted": r_tau_pred,
        "R33_B_r_tau_PDG": r_tau_PDG,
        "R33_B_m_tau_predicted_GeV": m_tau_pred,
        "R33_B_m_tau_PDG_GeV": m_tau_PDG,
        "R33_B_m_tau_rel_err_ppm": (m_tau_pred-m_tau_PDG)/m_tau_PDG*1e6,
        "R33_B_m_tau_sigma_PDG": abs(m_tau_pred-m_tau_PDG)/m_tau_PDG_err,
        "R33_C_two_plus_sqrt3": 2+math.sqrt(3),
        "R33_C_4_cos_sq_pi12": 4*math.cos(math.pi/12)**2,
        "R33_C_match_check": abs((2+math.sqrt(3))-4*math.cos(math.pi/12)**2),
    },
    "null_test": {
        "N_random_triples": N,
        "match_within_1pct_pct": float(match_pct_1),
        "match_within_10pct_pct": float(match_pct_10),
        "N_random_v3": N2,
        "within_1deg_of_45": int(within_1deg),
        "within_0p1deg_of_45": int(within_0p1deg),
    },
    "verdict": (
        "STRUCTURAL PROGRESS ON OP(vii): Koide identified as (1) v on 45° cone "
        "about (1,1,1) axis [R33-A]; (2) exact algebraic z-root formula "
        "r_τ = 2(r_e+r_μ) + √3·√(r_e²+4r_e r_μ+r_μ²) predicting m_τ from "
        "m_e, m_μ at <{:.1f} ppm = {:.2f}σ_PDG [R33-B]; (3) cyclotomic-12 "
        "atom identification (2+√3) = 4·cos²(π/12), (1+√3) = 2√2·cos(π/12), "
        "tying Koide to same π/12 family as α=π/6 in Round 13's TT "
        "derivation [R33-C].  Not full Lean flow theorem (OP(vii) remains "
        "partially open), but structural content of Koide identified."
    ).format(abs(m_tau_pred-m_tau_PDG)/m_tau_PDG*1e6, abs(m_tau_pred-m_tau_PDG)/m_tau_PDG_err),
}
block = json.dumps(prediction, sort_keys=True, indent=2, default=str)
prediction["pre_commit_sha256"] = hashlib.sha256(block.encode("utf-8")).hexdigest()
out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "comp_p01_GGG_koide_closed_form.json")
with open(out, "w") as f:
    json.dump(prediction, f, indent=2, sort_keys=True, default=str)
with open(out, "rb") as f:
    full_sha = hashlib.sha256(f.read()).hexdigest()
print()
print(f"Pre-commit SHA-256: {prediction['pre_commit_sha256'][:16]}...")
print(f"Full-file SHA-256:  {full_sha[:16]}...")
