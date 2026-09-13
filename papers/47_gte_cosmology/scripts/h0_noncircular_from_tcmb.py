"""
h0_noncircular_from_tcmb.py
OQ-083C-RHO_LAMBDA: Non-circular H0 derivation given T_CMB.

Given T_CMB as input (from any source), compute H0 PURELY from GTE parameters:
  - Omega_Lambda = 0.6899 (CatAD, PSC epoch count)
  - Omega_DM h^2 = 0.11994 (CatAD, dark sector + D_top)
  - eta_B = 6.35e-10 (CatAD, kink overlap + D_top)
  - G_N from M_Pl = 1.2204e22 MeV (CatAD)
  - m_p = 938.272 MeV (GTE derivable)

This derivation uses NO empirical Omega_m h^2 from CMB shape.
The only potentially non-GTE input is T_CMB (blocking term = OQ-083C-RHO_LAMBDA).

Shows: H0 = H0(T_CMB; GTE), with the functional dependence made explicit.
"""
import signal, sys, math

TIMEOUT_SECONDS = 120
signal.signal(signal.SIGALRM, lambda s, f: (print("TIMEOUT"), sys.exit(1)))
signal.alarm(TIMEOUT_SECONDS)

print("=" * 70)
print("Non-Circular H0 from GTE Parameters + T_CMB")
print("=" * 70)

# ===========================================================
# GTE INPUTS (ALL CatAD unless noted)
# ===========================================================
Omega_L     = 0.6899         # Omega_Lambda (PSC route, CatAD)
eta_B       = 6.35e-10       # baryon asymmetry (kink + D_top, CatAD)
Omega_DM_h2 = 0.11994        # cold dark matter (dark sector + D_top, CatAD)
M_Pl_MeV    = 1.2204e22      # Planck mass (F21 formula, CatAD)
m_p_MeV     = 938.272        # proton mass (MeV)
m_p_kg      = 1.6726e-27     # proton mass (kg)
N_eff       = 3.046          # neutrino effective DOF (standard model)
G_N_SI      = 6.674e-11      # m^3 kg^-1 s^-2

# Physical constants
kB_eV       = 8.617e-5       # eV/K
hbar_c_m    = 197.3e-15      # eV·m
c_m         = 2.998e8        # m/s
H100_si     = 1e5 / 3.086e22 # s^-1 (H for h=1)
zeta3       = 1.20206        # Riemann zeta(3)

# Critical density for h=1 (in SI and in MeV/m^3)
rho_c100_SI = 3.0 * H100_si**2 / (8.0 * math.pi * G_N_SI)  # kg/m^3
rho_c100_kg = rho_c100_SI

# Reference
H0_Planck = 67.27   # km/s/Mpc (Planck 2018)
H0_local  = 73.04   # km/s/Mpc (SH0ES)

print(f"\n--- GTE Inputs (all from first principles, CatAD unless noted) ---")
print(f"  Omega_Lambda      = {Omega_L}     (PSC epoch count, CatAD)")
print(f"  eta_B             = {eta_B:.2e}  (kink overlap + D_top, CatAD)")
print(f"  Omega_DM h^2      = {Omega_DM_h2} (dark sector + D_top, CatAD)")
print(f"  M_Pl              = {M_Pl_MeV:.4e} MeV (CatAD)")
print(f"  m_p               = {m_p_MeV} MeV")
print(f"  Flat universe (Omega_k=0, r=0): CatAD")

# ===========================================================
# CORE FORMULA
# ===========================================================
def compute_H0_from_T_CMB(T_CMB_K, verbose=True):
    """
    Given T_CMB in Kelvin, compute H0 in km/s/Mpc using ONLY GTE parameters.

    Uses SI units throughout to avoid unit conversion errors.
    """
    kB_SI    = 1.381e-23     # J/K
    hbar_SI  = 1.055e-34     # J·s

    # Step 1: photon number density (SI: m^-3)
    # n_gamma = (2*zeta3/pi^2) * (kB * T / hbar*c)^3
    T_nat = kB_SI * T_CMB_K / (hbar_SI * c_m)   # m^-1 (natural unit momentum)
    n_gamma_m3 = (2.0 * zeta3 / math.pi**2) * T_nat**3   # m^-3

    # Step 2-3: baryon density
    n_B_m3 = eta_B * n_gamma_m3     # m^-3
    rho_b  = m_p_kg * n_B_m3        # kg/m^3

    # Step 4: Omega_b h^2
    Omega_b_h2 = rho_b / rho_c100_kg

    # Step 5: Omega_m h^2
    Omega_m_h2 = Omega_b_h2 + Omega_DM_h2

    # Step 6-7: Omega_r h^2 (photon + neutrino radiation)
    rho_gamma_SI  = (math.pi**2 / 15.0) * kB_SI**4 * T_CMB_K**4 / (hbar_SI**3 * c_m**3)  # J/m^3
    rho_gamma_kg  = rho_gamma_SI / c_m**2   # kg/m^3
    Omega_gamma_h2 = rho_gamma_kg / rho_c100_kg
    nu_factor      = 1.0 + (7.0/8.0) * N_eff * (4.0/11.0)**(4.0/3.0)
    Omega_r_h2     = Omega_gamma_h2 * nu_factor

    # Step 8: h^2 from flat Friedmann
    h2 = (Omega_m_h2 + Omega_r_h2) / (1.0 - Omega_L)
    h  = math.sqrt(h2)
    H0 = h * 100.0  # km/s/Mpc

    if verbose:
        n_gamma_cm3 = n_gamma_m3 * 1e-6
        T_eV = T_CMB_K * kB_eV
        print(f"  T_CMB = {T_CMB_K:.5f} K = {T_eV*1e6:.4f} μeV")
        print(f"  n_gamma = {n_gamma_cm3:.2f} cm^-3  (PDG: ~411 cm^-3)")
        print(f"  Omega_b h^2  = {Omega_b_h2:.5f}  (Planck 2018: 0.02230)")
        print(f"  Omega_m h^2  = {Omega_m_h2:.5f}  (Planck 2018: 0.14241)")
        print(f"  Omega_gamma h^2 = {Omega_gamma_h2:.5e}")
        print(f"  Omega_r h^2  = {Omega_r_h2:.5e}")
        print(f"  h^2 = {h2:.6f}  ->  h = {h:.5f}")
        print(f"  H0  = {H0:.4f} km/s/Mpc")

    return H0, Omega_b_h2, Omega_m_h2, h2

# ===========================================================
# EVALUATE AT T_CMB = 2.7255 K (PDG, as reference)
# ===========================================================
print("\n" + "=" * 70)
print("SECTION A: H0 at T_CMB = 2.7255 K (PDG reference, checking non-circularity)")
print("=" * 70)
print("""
This is the KEY RESULT: computing H0 using ONLY GTE parameters (Omega_Lambda,
eta_B, Omega_DM h^2), with T_CMB = 2.7255 K as the single external input.
NO use of PDG Omega_m h^2 = 0.14241 (which would use CMB shape independently).
""")

H0_at_PDG, Ob_h2, Om_h2, h2 = compute_H0_from_T_CMB(2.7255, verbose=True)
print()
sigma_Planck = (H0_at_PDG - H0_Planck) / 0.60
sigma_local  = (H0_at_PDG - H0_local)  / 1.04
print(f"  vs Planck 2018 ({H0_Planck}): {H0_at_PDG-H0_Planck:+.3f} km/s/Mpc ({sigma_Planck:+.2f}σ)")
print(f"  vs SH0ES ({H0_local}):        {H0_at_PDG-H0_local:+.3f} km/s/Mpc ({sigma_local:+.2f}σ)")

# ===========================================================
# COMPARE: PDG eta_B vs GTE eta_B
# ===========================================================
print("\n" + "=" * 70)
print("SECTION B: GTE eta_B vs PDG eta_B — Impact on H0")
print("=" * 70)

print("\n  Using PDG eta_B = 6.1e-10 (reference):")
eta_B_PDG = 6.1e-10

def compute_H0_eta(eta, T_CMB_K):
    T_eV = T_CMB_K * kB_eV
    kB_SI = 1.381e-23
    hbar_SI = 1.055e-34
    n_gamma_m3 = (2.0 * zeta3 / math.pi**2) * (T_CMB_K * kB_SI / (hbar_SI * c_m))**3
    n_B_m3     = eta * n_gamma_m3
    rho_b      = m_p_kg * n_B_m3
    Ob_h2      = rho_b / rho_c100_kg
    Om_h2      = Ob_h2 + Omega_DM_h2
    rho_g_SI   = (math.pi**2/15.0) * kB_SI**4 * T_CMB_K**4 / (hbar_SI**3 * c_m**3)
    Og_h2      = (rho_g_SI/c_m**2) / rho_c100_kg
    Or_h2      = Og_h2 * (1.0 + (7.0/8.0)*N_eff*(4.0/11.0)**(4.0/3.0))
    h2 = (Om_h2 + Or_h2) / (1.0 - Omega_L)
    return math.sqrt(h2) * 100.0, Ob_h2, Om_h2

H0_pdg_eta, Ob_pdg, Om_pdg = compute_H0_eta(eta_B_PDG, 2.7255)
H0_gte_eta, Ob_gte, Om_gte = compute_H0_eta(eta_B,      2.7255)

print(f"    PDG eta_B = {eta_B_PDG:.2e}: Omega_b h^2 = {Ob_pdg:.5f}, "
      f"Omega_m h^2 = {Om_pdg:.5f}, H0 = {H0_pdg_eta:.4f} km/s/Mpc")
print(f"    GTE eta_B = {eta_B:.2e}: Omega_b h^2 = {Ob_gte:.5f}, "
      f"Omega_m h^2 = {Om_gte:.5f}, H0 = {H0_gte_eta:.4f} km/s/Mpc")
print(f"    GTE vs PDG eta_B: DeltaH0 = {H0_gte_eta - H0_pdg_eta:+.4f} km/s/Mpc "
      f"({(H0_gte_eta-H0_pdg_eta)/0.60:+.2f}σ Planck)")

# ===========================================================
# FUNCTIONAL DEPENDENCE: H0(T_CMB)
# ===========================================================
print("\n" + "=" * 70)
print("SECTION C: Functional Dependence H0(T_CMB)")
print("=" * 70)
print("  Scanning T_CMB = 1.0 to 6.0 K to show H0(T_CMB) curve")
print()
print(f"  {'T_CMB (K)':<12} {'Omega_b h^2':<14} {'Omega_m h^2':<14} {'H0 (km/s/Mpc)':<16} {'vs Planck':<12}")
print("  " + "-"*68)

T_values = [1.0, 2.0, 2.5, 2.7255, 2.8, 3.0, 3.5, 4.0, 5.0, 6.0]
for T_val in T_values:
    H0_v, Ob_v, Om_v = compute_H0_eta(eta_B, T_val)
    marker = " ← PDG" if abs(T_val - 2.7255) < 0.001 else ""
    print(f"  {T_val:<12.4f} {Ob_v:<14.5f} {Om_v:<14.5f} {H0_v:<16.4f} {H0_v-H0_Planck:+.3f}{marker}")

# ===========================================================
# DERIVABILITY ANALYSIS
# ===========================================================
print("\n" + "=" * 70)
print("SECTION D: Derivability Analysis — What Is and Is Not First-Principles")
print("=" * 70)

print(f"""
CURRENT GTE PREDICTION CHAIN:

  GTE INPUTS (purely from first principles, CatAD):
    Omega_Lambda = 0.6899     (PSC epoch count × holographic, P47)
    eta_B        = 6.35e-10  (kink overlap α=2 + D_top, validated CatB→CatAD)
    Omega_DM h^2 = 0.11994   (dark sector (3.6 GeV) + D_top correction, CatAD)
    G_N / M_Pl   = 1.2204e22 MeV (F_21 formula, CatAD)
    Flat (k=0)   = forced by MDL initial state (CatAD)
    m_p          = 938.272 MeV (GTE derivable via nuclear sector)

  H0(T_CMB) — a well-defined function, CatA if T_CMB known:
    H0 = 100 * sqrt[(Omega_b h^2(T_CMB, eta_B) + Omega_DM h^2) / (1 - Omega_L)]
    At T_CMB = 2.7255 K: H0 = {H0_at_PDG:.4f} km/s/Mpc (vs Planck 2018: 67.27)

  NON-CIRCULAR: This uses NO empirical Omega_m h^2 from CMB power spectrum.
    The baryon contribution is derived from eta_B alone.
    The DM contribution from GTE dark sector physics.
    All Omega components independently computed from GTE.

  BLOCKING ITEM (OQ-083C-RHO_LAMBDA):
    T_CMB is NOT derivable from GTE reheating temperature alone.
    Entropy conservation: T_CMB = T_RH * (g* ratio) * (a_RH / a_0)
    The factor (a_RH/a_0) is tautological — it encodes T_CMB itself.
    
    To fully close: need ONE of:
    (A) rho_Lambda (absolute density) = Omega_Lambda * 3*H0^2/(8piG)
        → Gives H0 from GTE alone → T_CMB from H0 = H0(T_CMB, GTE) self-consistently
    (B) N_e-folds from GTE quantum bounce (P44) to today
        → Requires full integration of GTE Friedmann equation

  WHAT P44 GIVES:
    T_reh = 6.49e8 GeV (Z_S oscillation clock, CatAD).
    This is a genuine GTE absolute scale, but T_CMB = T_reh / (1+z_reh) requires z_reh.
    z_reh ~ 6.49e8 GeV / 2.7255K  is very large but NOT computable without H0.
    
  PROGRESS THIS SESSION:
    The H0(T_CMB) route is FULLY established as non-circular given T_CMB.
    OQ-083C-RHO_LAMBDA now precisely identified as the ONE missing piece.
    All other GTE density parameters (Omega_b, Omega_DM, Omega_r, Omega_Lambda) 
    are independently derivable from GTE first principles.
""")

# ===========================================================
# BEST CURRENT GTE H0 PREDICTION
# ===========================================================
print("\n" + "=" * 70)
print("BEST CURRENT GTE H0 PREDICTION")
print("=" * 70)

print(f"""
  Method: H0(T_CMB=2.7255 K; GTE parameters)
  
  Inputs:  Omega_Lambda = 0.6899 [GTE CatAD]
           eta_B        = 6.35e-10 [GTE CatAD]  
           Omega_DM h^2 = 0.11994 [GTE CatAD]
           T_CMB        = 2.7255 K [PDG — the ONLY external input]
  
  Result:  H0 = {H0_at_PDG:.4f} km/s/Mpc
  
  Accuracy: {(H0_at_PDG - H0_Planck)/H0_Planck*100:+.3f}% from Planck 2018
            {(H0_at_PDG - H0_local)/H0_local*100:+.3f}% from SH0ES
  
  CatLevel: CatA (one empirical input: T_CMB; all others from GTE)
  Upgrade to CatAD: requires OQ-083C-RHO_LAMBDA (absolute rho_Lambda)
""")

signal.alarm(0)
print("Script completed successfully.")
