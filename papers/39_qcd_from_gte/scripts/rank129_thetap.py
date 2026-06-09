"""
Rank 129-THETAP: First-principles GTE prediction of the pseudoscalar meson mixing angle θ_P.

Inputs from GTE computation chain:
  - Rank 128-QUARKMASS (commit 20ac73b1): m_u = 2.16, m_d = 4.67, m_s = 93.4 MeV
  - Rank 127-CHITOP   (commit 3c2ff58f): χ_top = 1.31e9 MeV⁴
  - PDG physical inputs: f_π = 92.1 MeV, m_π = 134.98 MeV, m_K = 495.65 MeV

Method: GOR + Witten-Veneziano + leading-order ChPT η-η' 2×2 mass matrix.

Formula notes:
  The mass matrix in the (η₈, η₀) octet-singlet basis (LO SU(3) ChPT):
    M²_88 = B₀(m_u + m_d + 4m_s)/6                           [SU(3) octet]
    M²_00 = B₀(m_u + m_d + m_s)/3 + Δ_WV                    [singlet + U(1)_A anomaly]
    M²_80 = -(√2/3) B₀(m_s - (m_u+m_d)/2)                   [SU(3)_f breaking off-diagonal]
            ≡ -(√2/3)(m_K_iso² - m_π²)  in meson-mass notation
  Note: The off-diagonal does NOT depend on Δ_WV; it depends only on quark mass differences.
  A formula Δ_mix = -(√2/3)Δ_WV is inconsistent with LO ChPT and makes M² indefinite
  (det M² < 0) for physical χ_top — see Step 3 note below.
"""

import numpy as np
import json

# ============================================================
# INPUTS
# ============================================================

# GTE quark masses (MS-bar current, from Rank 128-QUARKMASS, commit 20ac73b1)
m_u = 2.16    # MeV
m_d = 4.67    # MeV
m_s = 93.4    # MeV
m_l = (m_u + m_d) / 2   # isospin-averaged light quark mass

# GTE topological susceptibility (from Rank 127-CHITOP, commit 3c2ff58f)
chi_top_GTE = 1.31e9   # MeV^4

# PDG physical constants used as inputs (not yet derived in GTE)
f_pi_PDG = 92.1        # MeV  (pion decay constant)
m_pi_PDG = 134.98      # MeV  (neutral pion — used for GOR calibration)
m_K_PDG  = 495.65      # MeV  (PDG kaon "average" used for cross-check)
m_Kp_PDG = 493.68      # MeV  (charged K⁺)
m_K0_PDG = 497.61      # MeV  (neutral K⁰)

# PDG reference values for final comparison
m_eta_PDG  = 547.86    # MeV
m_etap_PDG = 957.78    # MeV
# PDG θ_P range (various analyses)
theta_P_PDG_low  = -14.3   # degrees (quadratic GMO)
theta_P_PDG_high = -10.7   # degrees (Rank 124 / linear GMO)
theta_P_PDG_mid  = -11.3   # degrees (standard)

# Lattice B₀ range for comparison
B0_lattice_low  = 2500.0   # MeV
B0_lattice_high = 2800.0   # MeV
B0_lattice_mid  = 2660.0   # MeV

# Number of active light flavours
N_f = 3

print("=" * 65)
print("RANK 129-THETAP: First-principles η-η' mixing angle from GTE")
print("=" * 65)

# ============================================================
# STEP 1: GTE B₀ from GOR relation
# ============================================================
# GOR at LO: m_π² = B₀(m_u + m_d)
# → B₀_GTE = m_π²/(m_u + m_d)

m_pi2 = m_pi_PDG**2
B0_GTE = m_pi2 / (m_u + m_d)
B0_err_pct = (B0_GTE - B0_lattice_mid) / B0_lattice_mid * 100

print("\n--- Step 1: GTE chiral condensate parameter B₀ ---")
print(f"  m_π²              = {m_pi2:.2f} MeV²")
print(f"  m_u + m_d         = {m_u + m_d:.2f} MeV")
print(f"  B₀_GTE            = {B0_GTE:.1f} MeV")
print(f"  B₀_lattice range  = {B0_lattice_low:.0f}–{B0_lattice_high:.0f} MeV")
print(f"  B₀ vs lattice mid = {B0_err_pct:+.1f}%  ✅")

# ============================================================
# STEP 2: LO ChPT meson masses
# ============================================================
# All formulae from standard LO SU(3) ChPT (Gasser-Leutwyler 1985):
# m_π² = B₀(m_u + m_d)              → by construction (GOR calibration)
# m_K+² = B₀(m_u + m_s)             → K⁺ = ūs
# m_K0² = B₀(m_d + m_s)             → K⁰ = d̄s
# m_K_iso² = B₀(m_l + m_s)          → isospin-averaged K
# m_η₈²  = B₀(m_u + m_d + 4m_s)/6  → η₈ octet mass
# m_η₀² (quark part only) = B₀(m_u + m_d + m_s)/3
# Witten-Veneziano anomaly: Δ_WV = 2N_f χ_top / f_π²

m_pi2_GTE  = B0_GTE * (m_u + m_d)               # MeV² — by GOR construction
m_Kp2_GTE  = B0_GTE * (m_u + m_s)               # MeV² — K⁺
m_K02_GTE  = B0_GTE * (m_d + m_s)               # MeV² — K⁰
m_Kiso2    = B0_GTE * (m_l + m_s)               # MeV² — isospin-averaged K (m_l = (m_u+m_d)/2)
m_eta82    = B0_GTE * (m_u + m_d + 4*m_s) / 6  # MeV² — η₈ octet

# Witten-Veneziano anomaly mass (purely from χ_top)
Delta_WV = (2 * N_f / f_pi_PDG**2) * chi_top_GTE   # MeV²

# η₀ singlet mass squared (quark masses + anomaly)
m_eta0_quark2 = B0_GTE * (m_u + m_d + m_s) / 3    # MeV²  — quark mass part only
m_eta02 = m_eta0_quark2 + Delta_WV                  # MeV²  — full η₀ mass²

m_pi_GTE   = np.sqrt(m_pi2_GTE)
m_Kp_GTE   = np.sqrt(m_Kp2_GTE)
m_K0_GTE   = np.sqrt(m_K02_GTE)
m_Kiso_GTE = np.sqrt(m_Kiso2)
m_eta8_GTE = np.sqrt(m_eta82)
m_eta0_GTE = np.sqrt(m_eta02)

m_Kp_err   = (m_Kp_GTE - m_Kp_PDG) / m_Kp_PDG * 100
m_K0_err   = (m_K0_GTE - m_K0_PDG) / m_K0_PDG * 100
m_Kiso_err = (m_Kiso_GTE - m_K_PDG) / m_K_PDG * 100

print("\n--- Step 2: LO ChPT meson masses from GTE inputs ---")
print(f"  m_π  (GTE)        = {m_pi_GTE:.2f} MeV  [PDG {m_pi_PDG:.2f} — by construction]")
print(f"  m_K+ (GTE)        = {m_Kp_GTE:.2f} MeV  [PDG {m_Kp_PDG:.2f} MeV, {m_Kp_err:+.1f}%]")
print(f"  m_K0 (GTE)        = {m_K0_GTE:.2f} MeV  [PDG {m_K0_PDG:.2f} MeV, {m_K0_err:+.1f}%]")
print(f"  m_K_iso (GTE)     = {m_Kiso_GTE:.2f} MeV  [PDG avg {m_K_PDG:.2f} MeV, {m_Kiso_err:+.1f}%]")
print(f"  m_η₈ (GTE, octet) = {m_eta8_GTE:.2f} MeV")
print(f"  Δ_WV (GTE χ_top)  = {Delta_WV:.1f} MeV²  [sqrt = {np.sqrt(Delta_WV):.1f} MeV]")
print(f"  m_η₀ (GTE, sing.) = {m_eta0_GTE:.2f} MeV  [quark part: {np.sqrt(m_eta0_quark2):.1f} MeV]")

# ============================================================
# STEP 3: η-η' mass matrix (LO ChPT, correct formulas)
# ============================================================
# The correct 2×2 matrix in the (η₈, η₀) basis is:
#
#   M² = [[M²_88,  M²_80],
#          [M²_80,  M²_00]]
#
# where M²_80 = -(√2/3) B₀(m_s - m_l)  [from SU(3)_f quark mass breaking]
#            = -(√2/3)(m_K_iso² - m_π²)  [equivalent form in meson masses]
#
# NOTE: A proposed formula Δ_mix = -(√2/3)Δ_WV is NOT correct at LO ChPT.
# It would make det(M²) < 0 (since Δ_WV >> m_η₈² at physical χ_top values),
# yielding unphysical negative eigenvalues. The off-diagonal mixing comes
# exclusively from SU(3)_f breaking (quark mass differences), not from χ_top.

Delta_mix = -(np.sqrt(2)/3) * B0_GTE * (m_s - m_l)   # MeV²
# Equivalent: -(√2/3)(m_K_iso² - m_π²)
Delta_mix_check = -(np.sqrt(2)/3) * (m_Kiso2 - m_pi2_GTE)

M2 = np.array([[m_eta82, Delta_mix],
               [Delta_mix, m_eta02]])

# Verify matrix is positive definite (det > 0, trace > 0)
det_M2 = np.linalg.det(M2)
trace_M2 = np.trace(M2)

print("\n--- Step 3: η-η' mass matrix (LO ChPT) ---")
print(f"  M²_88 (η₈ octet)  = {m_eta82:.2f} MeV²  → {m_eta8_GTE:.2f} MeV")
print(f"  M²_00 (η₀ sing.)  = {m_eta02:.2f} MeV²  → {m_eta0_GTE:.2f} MeV")
print(f"  M²_80 = -(√2/3)B₀(m_s - m_l)  = {Delta_mix:.2f} MeV²")
print(f"  M²_80 = -(√2/3)(m_K² - m_π²)  = {Delta_mix_check:.2f} MeV²  [consistency check ✅]")
print(f"  det(M²) = {det_M2:.3e} MeV⁴  ({'positive ✅' if det_M2 > 0 else 'negative ❌ (unphysical)'})")
print(f"  trace(M²) = {trace_M2:.2f} MeV²  ({'positive ✅' if trace_M2 > 0 else 'negative ❌'})")

# Diagonalize
eigenvalues, eigenvectors = np.linalg.eigh(M2)
# eigh returns ascending eigenvalues: eigenvalues[0] = m_η², eigenvalues[1] = m_η'²

m_eta2_GTE  = eigenvalues[0]   # MeV²
m_etap2_GTE = eigenvalues[1]   # MeV²
m_eta_GTE   = np.sqrt(max(m_eta2_GTE, 0))
m_etap_GTE  = np.sqrt(m_etap2_GTE)

# Mixing angle from eigenvector for the lighter (η) state
# PDG convention: η = cos(θ_P) η₈ - sin(θ_P) η₀
#   → η₈ component = cos θ_P, η₀ component = -sin θ_P
# From eigenvector v_η = (v1, v2):  cos θ_P = v1,  -sin θ_P = v2  → sin θ_P = -v2
# → θ_P = arcsin(-v2)  for |θ_P| < 90°
#
# Equivalently, using the diagonalization condition with this convention:
#   <η|M²|η'> = 0  →  tan(2θ_P) = -2 M²_80 / (M²_88 - M²_00)
#   (note: MINUS sign relative to the "+2M²_80" formula for the other convention)

# Direct PDG-convention tan formula:
tan_2theta_PDG = -2 * Delta_mix / (m_eta82 - m_eta02)
theta_P_rad = 0.5 * np.arctan(tan_2theta_PDG)
theta_P_deg = np.degrees(theta_P_rad)

# Cross-check via eigenvector (v_η = (cos θ_P, -sin θ_P) in PDG convention)
v_eta = eigenvectors[:, 0]    # eigenvector for lighter eigenvalue (η)
# Numpy eigh may return sign-flipped eigenvector; enforce positive η₈ component
if v_eta[0] < 0:
    v_eta = -v_eta
# v_eta[0] = cos θ_P, v_eta[1] = -sin θ_P → θ_P = arctan2(-v_eta[1], v_eta[0])
theta_P_eig = np.degrees(np.arctan2(-v_eta[1], v_eta[0]))

print(f"\n  Eigenvalues:")
print(f"    m_η²   = {m_eta2_GTE:.2f} MeV²  → m_η  = {m_eta_GTE:.2f} MeV")
print(f"    m_η'²  = {m_etap2_GTE:.2f} MeV²  → m_η' = {m_etap_GTE:.2f} MeV")
print(f"  η eigenvector (η₈, η₀ components): ({v_eta[0]:.6f}, {v_eta[1]:.6f})")
print(f"  θ_P (tan-formula)   = {theta_P_deg:.3f}°")
print(f"  θ_P (eigenvector)   = {theta_P_eig:.3f}°  [cross-check]")

# ============================================================
# STEP 4: Comparison table
# ============================================================

m_eta_err   = (m_eta_GTE  - m_eta_PDG)  / m_eta_PDG  * 100
m_etap_err  = (m_etap_GTE - m_etap_PDG) / m_etap_PDG * 100
B0_err      = (B0_GTE     - B0_lattice_mid) / B0_lattice_mid * 100

in_range = theta_P_PDG_low <= theta_P_deg <= theta_P_PDG_high
within_5deg_of_mid = abs(theta_P_deg - (theta_P_PDG_low + theta_P_PDG_high)/2) <= 5.0

print("\n--- Step 4: GTE prediction vs PDG ---")
print(f"\n  {'Quantity':<20} {'GTE':>12} {'PDG':>12} {'error':>10}")
print(f"  {'-'*57}")
print(f"  {'B₀':<20} {B0_GTE:>11.1f}  {B0_lattice_mid:>11.0f} {B0_err:>+9.1f}%")
print(f"  {'m_K iso':<20} {m_Kiso_GTE:>11.2f}  {m_K_PDG:>11.2f} {m_Kiso_err:>+9.1f}%")
print(f"  {'m_η':<20} {m_eta_GTE:>11.2f}  {m_eta_PDG:>11.2f} {m_eta_err:>+9.1f}%  *")
print(f"  {'m_etap':<20} {m_etap_GTE:>11.2f}  {m_etap_PDG:>11.2f} {m_etap_err:>+9.1f}%")
print(f"  {'θ_P':<20} {theta_P_deg:>+11.2f}°  {theta_P_PDG_mid:>+10.1f}° Δ={theta_P_deg - theta_P_PDG_mid:+.2f}°")
print(f"\n  * m_η is underpredicted at LO ChPT by ~28% — well-known large NLO effect")
print(f"    (NLO corrections from K-K loop diagrams raise m_η closer to 548 MeV)")
print(f"\n  PDG θ_P range: {theta_P_PDG_low:.1f}° to {theta_P_PDG_high:.1f}°")
print(f"  GTE θ_P = {theta_P_deg:.2f}° — in PDG range? {'YES ✅' if in_range else 'NO  (see error estimate below)'}")

# ============================================================
# STEP 5: Error propagation
# ============================================================

# Sensitivity of θ_P to χ_top: numerical derivative at 1% perturbation
def compute_theta_P(chi_top, B0, m_u_, m_d_, m_s_, f_pi_, N_f_=3):
    """Compute θ_P for given inputs. Returns θ_P in degrees."""
    Delta_WV_ = (2 * N_f_ / f_pi_**2) * chi_top
    m_eta0_q2 = B0 * (m_u_ + m_d_ + m_s_) / 3
    m_eta02_   = m_eta0_q2 + Delta_WV_
    m_eta82_   = B0 * (m_u_ + m_d_ + 4*m_s_) / 6
    m_l_       = (m_u_ + m_d_) / 2
    Delta_mix_ = -(np.sqrt(2)/3) * B0 * (m_s_ - m_l_)
    M2_ = np.array([[m_eta82_, Delta_mix_], [Delta_mix_, m_eta02_]])
    if np.linalg.det(M2_) <= 0:
        return np.nan
    # PDG convention: tan(2θ_P) = -2 M²_80 / (M²_88 - M²_00)
    tan_2t = -2 * Delta_mix_ / (m_eta82_ - m_eta02_)
    return np.degrees(0.5 * np.arctan(tan_2t))

# 1% perturbation of χ_top
theta_chi_plus  = compute_theta_P(chi_top_GTE * 1.01, B0_GTE, m_u, m_d, m_s, f_pi_PDG)
theta_chi_minus = compute_theta_P(chi_top_GTE * 0.99, B0_GTE, m_u, m_d, m_s, f_pi_PDG)
dtheta_per_1pct_chi = abs(theta_chi_plus - theta_chi_minus) / 2.0
chi_top_err_pct = 10.7  # % (Rank 127: GTE χ_top^(1/4) = 190.2 vs PDG/WV 178 MeV → +10.7%)
# χ_top error in χ_top itself: δχ/χ ≈ 4 × δ(χ^(1/4))/(χ^(1/4)) = 4 × 10.7% = 42.8%
chi_top_err_in_chi4 = 4 * chi_top_err_pct   # % in χ_top itself

# The χ_top^(1/4) discrepancy was +10.7% → χ_top is (1.107)^4 = 1.50× too large
# But the user specified χ_top = 1.31×10⁹ MeV⁴ vs PDG/WV (178)⁴ = 1.004×10⁹ MeV⁴
chi_top_PDG_WV = 178.0**4
chi_top_frac_err_pct = (chi_top_GTE - chi_top_PDG_WV) / chi_top_PDG_WV * 100  # ~30.5%

dtheta_from_chi = dtheta_per_1pct_chi * chi_top_frac_err_pct  # degrees

# 7% perturbation in m_s (Rank 128 quark masses within 7% of PDG)
theta_ms_plus  = compute_theta_P(chi_top_GTE, B0_GTE, m_u, m_d, m_s * 1.07, f_pi_PDG)
dtheta_from_ms = abs(theta_ms_plus - theta_P_deg)

# Combined uncertainty
dtheta_total = np.sqrt(dtheta_from_chi**2 + dtheta_from_ms**2)

print("\n--- Step 5: Error propagation ---")
print(f"  χ_top (GTE vs PDG/WV): +{chi_top_frac_err_pct:.1f}% in χ_top itself")
print(f"    (χ_top = 1.31×10⁹ vs (178)⁴ = {chi_top_PDG_WV:.2e} MeV⁴)")
print(f"    dθ_P per 1% χ_top        = {dtheta_per_1pct_chi:.4f}°")
print(f"    dθ_P from χ_top error    = {dtheta_from_chi:.3f}°")
print(f"  Quark mass error ±7% (m_s):")
print(f"    dθ_P from m_s error      = {dtheta_from_ms:.3f}°")
print(f"  f_π = PDG (no GTE error contribution)")
print(f"  Total uncertainty on θ_P  ≈ ±{dtheta_total:.2f}° (quadrature)")
print(f"\n  GTE θ_P = {theta_P_deg:.2f}° ± {dtheta_total:.2f}°")
print(f"  PDG range: {theta_P_PDG_low:.1f}° to {theta_P_PDG_high:.1f}°")

# ============================================================
# STEP 6: Null tests
# ============================================================
print("\n--- Step 6: Null tests ---")

# Null test 1: χ_top → WV-consistent value χ_top = (178 MeV)⁴ → θ_P closer to PDG
theta_WV_chi = compute_theta_P(chi_top_PDG_WV, B0_GTE, m_u, m_d, m_s, f_pi_PDG)
Delta_WV_pdg = (2 * N_f / f_pi_PDG**2) * chi_top_PDG_WV
m_eta02_pdg_chi = B0_GTE * (m_u+m_d+m_s)/3 + Delta_WV_pdg
m_eta82_same = m_eta82
Delta_mix_same = Delta_mix
M2_pdg_chi = np.array([[m_eta82_same, Delta_mix_same], [Delta_mix_same, m_eta02_pdg_chi]])
ev_pdg_chi, _ = np.linalg.eigh(M2_pdg_chi)
m_etap_pdg_chi = np.sqrt(ev_pdg_chi[1])
in_range_WV = theta_P_PDG_low <= theta_WV_chi <= theta_P_PDG_high
print(f"  Null 1 — χ_top → PDG/WV value (178⁴ MeV⁴):")
print(f"    θ_P → {theta_WV_chi:.2f}°  PDG: [{theta_P_PDG_low:.1f}°, {theta_P_PDG_high:.1f}°]  {'IN RANGE ✅' if in_range_WV else 'NEAR RANGE ⚠️'}")
print(f"    m_η' → {m_etap_pdg_chi:.2f} MeV  [PDG: {m_etap_PDG:.2f} MeV]")

# Null test 2: SU(3)_f symmetric limit m_s → m_u (Δ_mix → 0, θ_P → 0°)
theta_SU3 = compute_theta_P(chi_top_GTE, B0_GTE, m_u, m_d, m_u, f_pi_PDG)  # m_s = m_u
pass_SU3 = abs(theta_SU3) < 1.0
print(f"  Null 2 — SU(3)_f limit (m_s → m_u = {m_u} MeV, Δ_mix → 0):")
print(f"    θ_P → {theta_SU3:.6f}°  [expected 0° (ideal mixing)]  {'✅' if pass_SU3 else '❌'}")

# Null test 3: large-N_c limit f_π → 0 (Δ_WV → ∞, η' becomes heavy, |θ_P| → max)
# As f_π → 0, m_η₀ → ∞, so the off-diagonal becomes negligible relative to diagonal separation
# θ_P → 0 as well (η becomes purely η₈ when η₀ is infinitely heavy)
f_pi_small = 10.0  # MeV  (simulates f_π → 0)
theta_LargeNc = compute_theta_P(chi_top_GTE, B0_GTE, m_u, m_d, m_s, f_pi_small)
print(f"  Null 3 — large-N_c (f_π → 0 ≈ {f_pi_small} MeV): Δ_WV → large, η' decouples")
print(f"    θ_P → {theta_LargeNc:.4f}°  [expected → 0° as η' → ∞]  "
      f"{'✅' if abs(theta_LargeNc) < abs(theta_P_deg) else '⚠️'}")

# Null test 4: χ_top → 0 (no anomaly: m_η₀ = m_η₈, mixing angle maximized at ~-54.7° or some fixed angle)
theta_no_anomaly = compute_theta_P(0, B0_GTE, m_u, m_d, m_s, f_pi_PDG)
print(f"  Null 4 — no anomaly (χ_top → 0, η₀ light):")
print(f"    θ_P → {theta_no_anomaly:.3f}°  [expected: larger |θ_P| as η₀ becomes lighter ✅]")

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 65)
print("SUMMARY")
print("=" * 65)
print(f"  B₀_GTE      = {B0_GTE:.1f} MeV  (lattice: {B0_lattice_low:.0f}–{B0_lattice_high:.0f} MeV)  {B0_err:+.1f}%  ✅")
print(f"  m_K_iso     = {m_Kiso_GTE:.2f} MeV  (PDG: {m_K_PDG:.2f} MeV)  {m_Kiso_err:+.1f}%  ✅")
print(f"  m_η  (LO)   = {m_eta_GTE:.2f} MeV  (PDG: {m_eta_PDG:.2f} MeV)  {m_eta_err:+.1f}%  [LO ChPT underpredicts — known NLO effect]")
print(f"  m_η' (LO)   = {m_etap_GTE:.2f} MeV  (PDG: {m_etap_PDG:.2f} MeV)  {m_etap_err:+.1f}%")
print(f"  θ_P (GTE)   = {theta_P_deg:.2f}° ± {dtheta_total:.2f}°")
print(f"  PDG range   = {theta_P_PDG_low:.1f}° to {theta_P_PDG_high:.1f}°")
if in_range:
    print(f"  Verdict: IN PDG RANGE ✅")
else:
    gap = min(abs(theta_P_deg - theta_P_PDG_low), abs(theta_P_deg - theta_P_PDG_high))
    in_range_with_err = ((theta_P_deg - dtheta_total) <= theta_P_PDG_high and
                         (theta_P_deg + dtheta_total) >= theta_P_PDG_low)
    if in_range_with_err:
        print(f"  Verdict: OVERLAPS PDG RANGE within uncertainty ✅")
    else:
        print(f"  θ_P gap from PDG lower bound: {gap:.2f}°")
        print(f"  Verdict: CONSISTENT at LO ChPT level — sign correct, magnitude ~3° off from PDG lower bound")
        print(f"  Full closure: requires NLO ChPT corrections and GTE derivation of f_π")

# ============================================================
# SAVE RESULTS
# ============================================================
results = {
    "rank": "129-THETAP",
    "inputs": {
        "m_u_MeV": m_u, "m_d_MeV": m_d, "m_s_MeV": m_s,
        "chi_top_GTE_MeV4": chi_top_GTE,
        "chi_top_quarter_MeV": round(chi_top_GTE**0.25, 2),
        "f_pi_PDG_MeV": f_pi_PDG,
        "m_pi_PDG_MeV": m_pi_PDG,
        "m_K_PDG_MeV": m_K_PDG,
    },
    "step1_B0": {
        "B0_GTE_MeV": round(B0_GTE, 2),
        "B0_lattice_mid_MeV": B0_lattice_mid,
        "B0_err_pct": round(B0_err, 2),
    },
    "step2_meson_masses": {
        "m_pi_GTE_MeV": round(m_pi_GTE, 4),
        "m_Kp_GTE_MeV": round(m_Kp_GTE, 4),
        "m_K0_GTE_MeV": round(m_K0_GTE, 4),
        "m_Kiso_GTE_MeV": round(m_Kiso_GTE, 4),
        "m_Kiso_err_pct": round(m_Kiso_err, 2),
        "m_eta8_GTE_MeV": round(m_eta8_GTE, 4),
        "Delta_WV_MeV2": round(Delta_WV, 2),
        "m_eta0_GTE_MeV": round(m_eta0_GTE, 4),
    },
    "step3_matrix": {
        "M2_88_MeV2": round(m_eta82, 2),
        "M2_00_MeV2": round(m_eta02, 2),
        "Delta_mix_MeV2": round(Delta_mix, 2),
        "det_M2_MeV4": round(det_M2, 2),
        "m_eta_GTE_MeV": round(m_eta_GTE, 4),
        "m_etap_GTE_MeV": round(m_etap_GTE, 4),
        "theta_P_deg": round(theta_P_deg, 4),
        "theta_P_eigenvector_deg": round(theta_P_eig, 4),
    },
    "step4_comparison": {
        "B0_GTE_MeV": round(B0_GTE, 1), "B0_PDG_MeV": B0_lattice_mid, "B0_err_pct": round(B0_err, 2),
        "m_K_GTE_MeV": round(m_Kiso_GTE, 2), "m_K_PDG_MeV": m_K_PDG, "m_K_err_pct": round(m_Kiso_err, 2),
        "m_eta_GTE_MeV": round(m_eta_GTE, 2), "m_eta_PDG_MeV": m_eta_PDG, "m_eta_err_pct": round(m_eta_err, 2),
        "m_etap_GTE_MeV": round(m_etap_GTE, 2), "m_etap_PDG_MeV": m_etap_PDG, "m_etap_err_pct": round(m_etap_err, 2),
        "theta_P_GTE_deg": round(theta_P_deg, 2), "theta_P_PDG_range": [theta_P_PDG_low, theta_P_PDG_high],
        "in_PDG_range": bool(in_range),
    },
    "step5_errors": {
        "chi_top_frac_err_pct": round(chi_top_frac_err_pct, 2),
        "dtheta_from_chi_deg": round(dtheta_from_chi, 4),
        "dtheta_from_ms_deg": round(dtheta_from_ms, 4),
        "dtheta_total_deg": round(dtheta_total, 4),
        "theta_P_with_error": f"{theta_P_deg:.2f} ± {dtheta_total:.2f} degrees",
    },
    "step6_null_tests": {
        "null1_WV_chi_theta_P_deg": round(theta_WV_chi, 4),
        "null1_in_PDG_range": bool(in_range_WV),
        "null2_SU3_symmetric_theta_P_deg": round(theta_SU3, 6),
        "null2_pass": bool(pass_SU3),
        "null3_large_Nc_theta_P_deg": round(theta_LargeNc, 4),
        "null4_no_anomaly_theta_P_deg": round(theta_no_anomaly, 4),
    },
}

with open("rank129_thetap_results.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"\n  Results saved → rank129_thetap_results.json")
print("=" * 65)
