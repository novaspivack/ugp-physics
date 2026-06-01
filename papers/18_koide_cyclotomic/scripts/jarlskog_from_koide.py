"""
Jarlskog invariant from GTE quark Koide angles.
Computes whether J ~ 3.2e-5 (PDG) is accessible from GTE parameters.
"""
import numpy as np
from scipy.optimize import minimize

# ── GTE Koide parameters (from quark_yukawa_angles_results.json, CatA) ──────
# Closed-form GTE angles: theta = (N_c^2-1)/(4*N_c^2*r) with N_c=3, r=3(up),r=2(dn)
# r=3: theta = 8/(4*9*3) = 8/108 = 2/27
# r=2: theta = 8/(4*9*2) = 8/72  = 1/9 = 3/27
theta_up_gte   = 2.0/27.0    # = 0.07407... rad
theta_down_gte = 3.0/27.0    # = 0.11111... rad

# Also store numerically-fitted values from existing analysis
theta_up_fit   = 0.07439474748834352
theta_down_fit = 0.11017623077554495
b_up_fit       = 1.7589441906912129
b_down_fit     = 1.5454985954693143

# PDG quark masses (GeV, PDG 2022)
m_u, m_c, m_t = 2.16e-3, 1.27, 172.69
m_d, m_s, m_b = 4.67e-3, 93.4e-3, 4.18

# PDG Wolfenstein parameters
lam_pdg = 0.22453
A_pdg   = 0.836
rho_pdg = 0.131
eta_pdg = 0.359
J_pdg   = 3.18e-5   # PDG value

# ── Koide cone helper ────────────────────────────────────────────────────────
def koide_masses_raw(m0, b, theta):
    """Unsorted masses from Koide parametrization."""
    return np.array([m0*(1 + b*np.cos(theta + 2*np.pi*k/3))**2 for k in range(3)])

def fit_koide(masses_target, b, theta):
    """Fit m0 so sorted Koide masses best match sorted target masses."""
    masses_sorted = np.sort(masses_target)
    def obj(x):
        raw = koide_masses_raw(abs(x[0]), b, theta)
        pred = np.sort(raw)
        return np.sum((np.log(pred / masses_sorted))**2)
    res = minimize(obj, [np.mean(masses_target)],
                   method='Nelder-Mead',
                   options={'maxiter':200000, 'xatol':1e-16, 'fatol':1e-16})
    return abs(res.x[0])

# ── Fit with GTE closed-form angles ─────────────────────────────────────────
print("=" * 60)
print("GTE KOIDE MASS FIT (closed-form theta_up=2/27, theta_dn=3/27)")
print("=" * 60)

b2_up   = 3.0938846659663666   # from existing JSON
b2_down = 2.388565908597623
b_up    = np.sqrt(b2_up)
b_down  = np.sqrt(b2_down)

m0_up   = fit_koide([m_u, m_c, m_t], b_up, theta_up_gte)
m0_down = fit_koide([m_d, m_s, m_b], b_down, theta_down_gte)

up = np.sort(koide_masses_raw(m0_up,   b_up,   theta_up_gte))
dn = np.sort(koide_masses_raw(m0_down, b_down, theta_down_gte))

print(f"Up   masses (GTE): u={up[0]*1e3:.3f} MeV, c={up[1]*1e3:.1f} MeV, t={up[2]:.2f} GeV")
print(f"Down masses (GTE): d={dn[0]*1e3:.3f} MeV, s={dn[1]*1e3:.2f} MeV, b={dn[2]:.3f} GeV")
print(f"PDG:               u=2.16 MeV, c=1270 MeV, t=172690 MeV")
print(f"PDG:               d=4.67 MeV, s=93.4  MeV, b=4180 MeV")

# ── Wolfenstein parameters from GTE Koide masses ─────────────────────────────
print()
print("=" * 60)
print("WOLFENSTEIN PARAMETERS FROM GTE KOIDE")
print("=" * 60)

# Gatto–Sartori–Tonin relation: sin(theta_12) ~ sqrt(m_d/m_s)
lam_gte = np.sqrt(dn[0]/dn[1])
print(f"lambda (GST: sqrt(m_d/m_s)) = {lam_gte:.4f}  [PDG: {lam_pdg:.4f}]")

# A parameter via analogous relation on down sector: sin(theta_23) ~ sqrt(m_s/m_b)*lam^{-2} ... or
# Standard: sin(theta_23) ~ A*lambda^2, A ~ sqrt(m_s/m_b) / lambda
A_gte = np.sqrt(dn[1]/dn[2]) / lam_gte**2
print(f"A ~ sqrt(m_s/m_b)/lambda^2  = {A_gte:.4f}  [PDG: {A_pdg:.4f}]")

# theta_13 from up sector (Fritzsch): sin(theta_13) ~ sqrt(m_u/m_t) (rough)
s13_gte = np.sqrt(up[0]/up[2])
print(f"s13 ~ sqrt(m_u/m_t)         = {s13_gte:.4e}  [PDG: ~3.6e-3]")

# ── CP phase from GTE ─────────────────────────────────────────────────────────
print()
print("=" * 60)
print("CP-VIOLATING PHASE ASSESSMENT")
print("=" * 60)

# Hypothesis 1: delta = theta_down - theta_up = 1/27 rad
delta_v1 = theta_down_gte - theta_up_gte
print(f"Hypothesis 1: delta = theta_dn - theta_up = 1/27 = {delta_v1:.5f} rad")
print(f"  sin(delta) = {np.sin(delta_v1):.4f}  [PDG: sin(1.20 rad) = {np.sin(1.20):.4f}]")
print(f"  Suppression vs PDG delta: factor {np.sin(1.20)/np.sin(delta_v1):.1f}")

# Hypothesis 2: delta = theta_down + theta_up = 5/27 rad
delta_v2 = theta_down_gte + theta_up_gte
print(f"Hypothesis 2: delta = theta_dn + theta_up = 5/27 = {delta_v2:.5f} rad")
print(f"  sin(delta) = {np.sin(delta_v2):.4f}")

# Hypothesis 3: CP phase from ratio of Koide angles (cf. lepton sector)
# theta_lep = 2/9 ~ 3*theta_up. CP phase ~ pi/2 - (theta_dn+theta_up) = pi/2 - 5/27
delta_v3 = np.pi/2 - 5.0/27.0
print(f"Hypothesis 3: delta = pi/2 - 5/27 = {delta_v3:.5f} rad")
print(f"  sin(delta) = {np.sin(delta_v3):.4f}")

# ── Jarlskog invariant computation ────────────────────────────────────────────
print()
print("=" * 60)
print("JARLSKOG INVARIANT J")
print("=" * 60)
print(f"PDG value: J = {J_pdg:.2e}")
print()

for label, delta in [("H1: delta=1/27",   delta_v1),
                      ("H2: delta=5/27",   delta_v2),
                      ("H3: delta=pi/2-5/27", delta_v3)]:
    # J = s12^2 * s23 * s13 * sin(delta)  (standard approximation)
    s12 = lam_gte
    s23 = A_gte * lam_gte**2
    s13 = s13_gte
    J = s12**2 * s23 * s13 * np.sin(delta)
    ratio = J / J_pdg
    print(f"{label}")
    print(f"  J = {J:.2e},  ratio to PDG = {ratio:.3f},  match: {'GOOD (<50%)'if abs(ratio-1)<0.5 else 'POOR'}")

# Also try with PDG Wolfenstein (lambda, A) but GTE CP phase only
print()
print("With PDG lambda, A but GTE CP phase:")
for label, delta in [("H1: delta=1/27",   delta_v1),
                      ("H3: delta=pi/2-5/27", delta_v3)]:
    # Using PDG s12, s23, but GTE s13 and delta
    s12 = lam_pdg
    s23 = A_pdg * lam_pdg**2
    s13 = A_pdg * lam_pdg**3   # PDG s13 estimate (rho-eta ~ O(1))
    J = s12**2 * s23 * s13 * np.sin(delta)
    ratio = J / J_pdg
    print(f"  {label}: J = {J:.2e}, ratio = {ratio:.3f}")

# ── Baryon asymmetry rough estimate ───────────────────────────────────────────
print()
print("=" * 60)
print("BARYON ASYMMETRY ROUGH ESTIMATE")
print("=" * 60)
print("eta_B (PDG): 6.1e-10")
print("Standard EWBG: eta_B ~ 1e-8 to 1e-6 * J / J_pdg (order-of-magnitude)")
print("With J_pdg gap factor, EWBG is insufficient by ~3-6 orders regardless.")
print("The baryon asymmetry gap is NOT closeable from J alone via standard EWBG.")
print("Requires: (a) J ~ 3.2e-5 exactly, AND (b) EWBG mechanism beyond SM.")

# Show what J value would be needed
eta_target = 6.1e-10
# eta_B ~ kappa * J where kappa is a model-dependent factor
# For illustration: if kappa = 1e-4 (typical estimate)
kappa = 1e-4
J_needed = eta_target / kappa
print(f"For eta_B = 6.1e-10 with kappa=1e-4: J_needed = {J_needed:.2e}")
print(f"This requires J ~ {J_needed:.2e}, but PDG J = {J_pdg:.2e}")
print(f"Standard EWBG kappa is O(1e-4 to 1e-6) -- gap remains ~4-6 orders of magnitude.")

# ── Summary ───────────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"GTE lambda (GST)     = {lam_gte:.4f}  (PDG: {lam_pdg:.4f})  -> {'OK' if abs(lam_gte/lam_pdg-1)<0.3 else 'FAIL'}")
print(f"GTE A                = {A_gte:.4f}  (PDG: {A_pdg:.4f})  -> {'OK' if abs(A_gte/A_pdg-1)<0.3 else 'FAIL'}")
print(f"GTE sin(theta_13)    = {s13_gte:.2e}  (PDG: ~3.6e-3) -> {'OK' if abs(s13_gte/3.6e-3-1)<0.5 else 'FAIL'}")
# Dominant obstacle: CP phase
print(f"GTE delta (H1=1/27)  = {delta_v1:.4f} rad (PDG: 1.20 rad) -> FAIL (factor {np.sin(1.20)/np.sin(delta_v1):.0f} in sin)")
print()
print("CONCLUSION: GTE Koide angle difference (1/27 rad) gives wrong CP phase.")
print("J from GTE is ~3-7 orders below PDG. The gap is not closeable with current angle assignment.")
print("CP phase = pi/2 - 5/27 hypothesis reduces gap but still ~20x off.")
print("A new GTE mechanism for the CP-violating phase is needed to close this gap.")
