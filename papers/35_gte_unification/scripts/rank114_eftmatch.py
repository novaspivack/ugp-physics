"""
Rank 114-EFTMATCH: EFT Matching Condition — Phi_MDL <-> Conjectured SU(3) UV
Computes Lambda_GTE with uncertainty, classifies IR vs UV predictions,
and prints the field-content and prediction-classification tables.
"""

import signal
import sys

TIMEOUT_SECONDS = 120

def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

# ── Physical constants ─────────────────────────────────────────────────────────
HBAR_C_MEV_FM = 197.3269804  # MeV·fm  (PDG 2022)

# ── GTE substrate parameters ───────────────────────────────────────────────────
N7 = 7                        # Sylow-7 subgroup order; GTE parameter (exact, CatAL)
m_kink_sim = 8 / (N7**2)     # BPS kink mass in sim units: 8/N7^2 = 8/49 (exact, analytical)

# Calibration: sim_to_fm from Rank 97b Route C' self-consistency
# Route C': sigma_sim = sigma_2D AND d_break = d_break_QCD  =>  sim_to_fm = 0.112 fm/sim
# This is the canonical (PROVISIONAL) central value.
sim_to_fm_central = 0.112    # fm/sim  (Rank 97b Route C', PROVISIONAL)
sim_to_fm_hard_lower = 0.100  # fm/sim  (Rank 97b Route A' Compton hard bound)
sim_to_fm_hard_upper = 0.143  # fm/sim  (Rank 97b upper bracket)

# ── Lambda_GTE computation ─────────────────────────────────────────────────────
def compute_lambda_gte(sim_to_fm: float) -> dict:
    """
    Compute Lambda_GTE = N7 * m_kink_phys.
    m_kink_phys = m_kink_sim / sim_to_fm  [fm^-1] * hbar*c  [MeV]
    """
    m_kink_fm_inv = m_kink_sim / sim_to_fm          # fm^-1
    m_kink_mev    = m_kink_fm_inv * HBAR_C_MEV_FM   # MeV
    lambda_gte_mev = N7 * m_kink_mev                # MeV
    lambda_gte_gev = lambda_gte_mev / 1000.0         # GeV
    return {
        "sim_to_fm": sim_to_fm,
        "m_kink_sim": m_kink_sim,
        "m_kink_fm_inv": m_kink_fm_inv,
        "m_kink_mev": m_kink_mev,
        "lambda_gte_mev": lambda_gte_mev,
        "lambda_gte_gev": lambda_gte_gev,
    }

central = compute_lambda_gte(sim_to_fm_central)
lower   = compute_lambda_gte(sim_to_fm_hard_upper)   # larger fm/sim -> smaller Lambda
upper   = compute_lambda_gte(sim_to_fm_hard_lower)   # smaller fm/sim -> larger Lambda

# ── Standard QCD reference scales ─────────────────────────────────────────────
# All values from PDG 2022 / standard references
LAMBDA_QCD_MSBAR_MeV  = (210, 220)   # PDG MSbar scheme, N_f=5 (range)
LAMBDA_CHI_SB_GEV     = (1.0, 1.2)  # chiral symmetry-breaking scale
M_JPSI_GEV            = 3.0969       # J/psi mass (c-cbar threshold proxy), PDG
M_PION_MEV            = 139.57       # pi+/- mass, PDG
M_PROTON_MEV          = 938.272      # proton mass, PDG
LAMBDA_EW_GEV         = 91.2         # Z boson mass / EW scale

print("=" * 72)
print("RANK 114-EFTMATCH: Lambda_GTE Computation")
print("=" * 72)

print(f"\n--- GTE substrate parameters ---")
print(f"  N7               = {N7}        (Sylow-7 subgroup; exact, CatAL)")
print(f"  m_kink_sim       = 8/N7^2 = 8/49 = {m_kink_sim:.6f}  sim (BPS, exact)")
print(f"  sim_to_fm        = {sim_to_fm_central:.3f}  fm/sim  (Rank 97b Route C', PROVISIONAL)")
print(f"  sim_to_fm range  = [{sim_to_fm_hard_lower:.3f}, {sim_to_fm_hard_upper:.3f}]  fm/sim")

print(f"\n--- Central value ---")
print(f"  m_kink_phys      = {central['m_kink_mev']:.2f} MeV")
print(f"  Lambda_GTE       = N7 x m_kink_phys = {central['lambda_gte_mev']:.1f} MeV = {central['lambda_gte_gev']:.3f} GeV")

print(f"\n--- Uncertainty propagation ---")
print(f"  Lower bound (sim_to_fm = {sim_to_fm_hard_upper:.3f}): Lambda_GTE = {lower['lambda_gte_gev']:.3f} GeV")
print(f"  Upper bound (sim_to_fm = {sim_to_fm_hard_lower:.3f}): Lambda_GTE = {upper['lambda_gte_gev']:.3f} GeV")
print(f"  Result: Lambda_GTE = {central['lambda_gte_gev']:.2f} +{upper['lambda_gte_gev'] - central['lambda_gte_gev']:.2f}/-{central['lambda_gte_gev'] - lower['lambda_gte_gev']:.2f} GeV")

print(f"\n--- Comparison to standard QCD scales ---")
print(f"  Lambda_QCD (MSbar, N_f=5) = {LAMBDA_QCD_MSBAR_MeV[0]}–{LAMBDA_QCD_MSBAR_MeV[1]} MeV = "
      f"{LAMBDA_QCD_MSBAR_MeV[0]/1000:.3f}–{LAMBDA_QCD_MSBAR_MeV[1]/1000:.3f} GeV  (PDG)")
print(f"  Lambda_chiSB (chi. symm.) = {LAMBDA_CHI_SB_GEV[0]:.1f}–{LAMBDA_CHI_SB_GEV[1]:.1f} GeV")
print(f"  Lambda_GTE   (this work)  = {lower['lambda_gte_gev']:.1f}–{upper['lambda_gte_gev']:.1f} GeV  (calibration range)")
print(f"  J/psi mass   (c-cbar)     = {M_JPSI_GEV:.4f} GeV  (charm threshold)")
print(f"  M_Z          (EW scale)   = {LAMBDA_EW_GEV:.1f} GeV")
print(f"\n  Hierarchy: Lambda_QCD << Lambda_chiSB < Lambda_GTE < M_J/psi < M_Z")
print(f"  Lambda_GTE sits between chiral-SB scale and charm threshold.")
print(f"  This is physically reasonable for a confined-phase strong-interaction EFT.")

# ── Field content table ────────────────────────────────────────────────────────
print("\n")
print("=" * 72)
print("FIELD CONTENT TABLE: IR vs UV Identification")
print("=" * 72)

fields = [
    ("phi (Z7 winding)",
     "Kink worldline; topological soliton of Z7-KG field",
     "Quark field (Phi_MDL kink ≡ quark at long distance; species indexed by Z7 orbit k)"),
    ("chi (Z3 color phase)",
     "Color phase; Z3 = {1,2,4} C Z7* multiplicative subgroup",
     "Quark color charge (GTE colour ≡ QCD colour; Z3 colour ↔ SU(3) color mod N7)"),
    ("A_mu (Z3 gauge field)",
     "Confining color gluon; generates area-law string tension sigma_2D = 0.1460",
     "lambda_3 Cartan gluon of SU(3) (one of two Cartan generators; field identification conjectural pending Rank 112)"),
    ("A'_mu (predicted; not yet in Lagrangian)",
     "Second Cartan mode; absence implies one missing SU(3) generator",
     "lambda_8 Cartan gluon of SU(3) (Rank 116-SECONDCARTAN open work)"),
    ("m_kink approx 287 MeV",
     "Kink creation threshold; lightest massive excitation in color-singlet sector",
     "Effective quark mass scale at GTE IR (not perturbative quark mass; constituent mass analog)"),
]

col_w = [28, 38, 46]
header = (f"{'Field':{col_w[0]}} | {'IR role (below Lambda_GTE)':{col_w[1]}} | "
          f"{'UV identification (above Lambda_GTE)':{col_w[2]}}")
sep = "-" * (sum(col_w) + 9)
print(header)
print(sep)
for field, ir, uv in fields:
    # Print with line-wrapping for readability
    print(f"{field:{col_w[0]}} | {ir[:col_w[1]]:{col_w[1]}} | {uv[:col_w[2]]}")
    # Continuation lines if needed
    ir_rest = ir[col_w[1]:]
    uv_rest = uv[col_w[2]:]
    while ir_rest or uv_rest:
        ir_line = ir_rest[:col_w[1]]
        uv_line = uv_rest[:col_w[2]]
        print(f"{'':{col_w[0]}} | {ir_line:{col_w[1]}} | {uv_line}")
        ir_rest = ir_rest[col_w[1]:]
        uv_rest = uv_rest[col_w[2]:]

# ── Prediction classification table ───────────────────────────────────────────
print("\n")
print("=" * 72)
print("PREDICTION CLASSIFICATION: IR (within GTE scope) vs UV (conjectural)")
print("=" * 72)
print(f"Boundary: Lambda_GTE = {central['lambda_gte_gev']:.2f} GeV (PROVISIONAL)\n")

predictions = [
    # (Name, Value/Status, IR_or_UV, Confidence, Notes)
    ("alpha_EM = 1/137",
     "1/137.036 (0.026% from PDG)",
     "IR",
     "CatAL ROBUST",
     "Berry holonomy on F_21^ab = Z3; Casimir-level structure well below Lambda_GTE"),
    ("Mass gap Delta_gauge >= 592 MeV",
     "Analytical lower bound: 2 M_kink = 2 x 296 MeV",
     "IR",
     "CatAL ROBUST",
     "Kink pair threshold; confinement scale well below Lambda_GTE; Clay Y-M continuum bridge open"),
    ("sigma_2D = 0.1460",
     "Analytic from Z3 lattice",
     "IR",
     "CatA ROBUST",
     "String tension measured at GTE lattice scales; 2D Euclidean lattice"),
    ("d_s = 4 (spectral dim.)",
     "Exact thermodynamic limit",
     "IR",
     "CatAL (1 documented sorry)",
     "Spectral dimension of causal graph; geometric property of substrate at all scales"),
    ("Color confinement",
     "No PSC-admissible isolated quark",
     "IR",
     "CatAL ROBUST",
     "Color-neutral requirement from GoE + PSC; topological at all scales"),
    ("Three generations (N_gen = 3)",
     "Z7 orbit depth = 3 exactly",
     "IR",
     "CatAL ROBUST",
     "Z7 arithmetic property; generation count is structural, not dynamical"),
    ("SR time dilation (6.4% error)",
     "tau_c ratio = 1.553 vs gamma = 1.659",
     "IR",
     "CatA ROBUST",
     "AFCA inner CA below Lambda_GTE; continuum Lorentz invariance at M -> inf"),
    ("eta_B baryon asymmetry",
     "6.54e-10 (7.2% from Planck)",
     "IR",
     "CatA PROVISIONAL",
     "Derived from N_gen, N_fam at zero free parameters; no UV input required"),
    ("sin^2 theta_W = 3/13",
     "0.23077 (-0.195% from PDG EW)",
     "IR",
     "CatAL ROBUST",
     "Arithmetic from N_gen cascade; EW value; does not require UV structure"),
    ("alpha_s running (beta fn.)",
     "beta = -7g^3/(16pi^2) conjectured",
     "UV CONJECTURAL",
     "Analytical (Rank 117-AFRGCHECK open)",
     "Requires Lambda > Lambda_GTE; depends on F_21 -> SU(3) UV identification"),
    ("Three-gluon amplitude",
     "From F_21 off-diagonal vertices",
     "UV CONJECTURAL",
     "Analytical (Rank 113-KINKLOOP3V open)",
     "Measured at LEP (91 GeV >> Lambda_GTE); UV completion required"),
    ("Asymptotic freedom",
     "b_0 = 7 predicted",
     "UV CONJECTURAL",
     "Analytical (Rank 117-AFRGCHECK open)",
     "AF is a UV (short-distance) property; outside GTE EFT domain"),
    ("High-energy jet cross-sections",
     "Requires full QCD",
     "UV CONJECTURAL",
     "Not yet attempted",
     "Probed at LHC/LEP (>> Lambda_GTE); UV completion required"),
    ("Hadron spectrum above 2 GeV",
     "Charmonium, b-hadrons, etc.",
     "UV CONJECTURAL",
     "Not yet attempted",
     "Above kink-antikin pair threshold by factor ~7; UV regime"),
]

col_widths = [32, 28, 20, 22]
hdr = (f"{'Prediction':{col_widths[0]}} | {'Scope':{col_widths[1]}} | "
       f"{'Classification':{col_widths[2]}} | {'Confidence':{col_widths[3]}}")
print(hdr)
print("-" * (sum(col_widths) + 11))
for name, val, scope, conf, note in predictions:
    print(f"{name:{col_widths[0]}} | {scope + ': ' + val[:20]:{col_widths[1]}} | "
          f"{scope:{col_widths[2]}} | {conf:{col_widths[3]}}")

# ── Matching-scale consistency checks ─────────────────────────────────────────
print("\n")
print("=" * 72)
print("CONSISTENCY CHECKS")
print("=" * 72)

# Check: Lambda_GTE > mass gap (the EFT must contain the mass gap within its domain)
mass_gap_lower_mev = 592.0
assert central['lambda_gte_mev'] > mass_gap_lower_mev, \
    f"FAIL: Lambda_GTE {central['lambda_gte_mev']:.1f} MeV <= mass gap {mass_gap_lower_mev} MeV"
print(f"  [PASS] Lambda_GTE ({central['lambda_gte_mev']:.1f} MeV) > mass gap lower bound ({mass_gap_lower_mev} MeV)")

# Check: Lambda_GTE < J/psi mass (charm threshold)
assert central['lambda_gte_mev'] < M_JPSI_GEV * 1000, \
    f"FAIL: Lambda_GTE {central['lambda_gte_mev']:.1f} MeV >= J/psi {M_JPSI_GEV*1000:.1f} MeV"
print(f"  [PASS] Lambda_GTE ({central['lambda_gte_mev']:.1f} MeV) < J/psi ({M_JPSI_GEV*1000:.1f} MeV)")

# Check: Lambda_GTE > Lambda_chiSB upper (GTE is above chiral symmetry breaking scale)
assert central['lambda_gte_mev'] > LAMBDA_CHI_SB_GEV[1] * 1000, \
    f"FAIL: Lambda_GTE {central['lambda_gte_mev']:.1f} MeV <= Lambda_chiSB upper {LAMBDA_CHI_SB_GEV[1]*1000:.1f} MeV"
print(f"  [PASS] Lambda_GTE ({central['lambda_gte_mev']:.1f} MeV) > Lambda_chiSB upper ({LAMBDA_CHI_SB_GEV[1]*1000:.1f} MeV)")

# Check: m_kink_phys > pion mass (kinks are heavier than pions)
assert central['m_kink_mev'] > M_PION_MEV, \
    f"FAIL: m_kink ({central['m_kink_mev']:.1f} MeV) <= m_pi ({M_PION_MEV} MeV)"
print(f"  [PASS] m_kink ({central['m_kink_mev']:.1f} MeV) > m_pi ({M_PION_MEV:.1f} MeV)")

# Check: Ratio Lambda_GTE / Lambda_QCD
ratio_to_qcd = central['lambda_gte_mev'] / ((LAMBDA_QCD_MSBAR_MeV[0] + LAMBDA_QCD_MSBAR_MeV[1]) / 2.0)
print(f"  [INFO] Lambda_GTE / Lambda_QCD(MSbar) = {ratio_to_qcd:.1f}")
print(f"         (GTE kink threshold is ~{ratio_to_qcd:.0f}x the QCD confinement scale)")

# Ratio to chi-SB
ratio_chisb = central['lambda_gte_mev'] / (LAMBDA_CHI_SB_GEV[1] * 1000)
print(f"  [INFO] Lambda_GTE / Lambda_chiSB(upper) = {ratio_chisb:.2f}")

print(f"\n  [SUMMARY] All 4 consistency checks PASS.")
print(f"  Lambda_GTE = {central['lambda_gte_gev']:.3f} GeV  +{upper['lambda_gte_gev'] - central['lambda_gte_gev']:.3f}/-{central['lambda_gte_gev'] - lower['lambda_gte_gev']:.3f} GeV")
print(f"  (PROVISIONAL — depends on sim_to_fm = 0.112 fm/sim, Rank 97b Route C')")

signal.alarm(0)
print("\nRank 114-EFTMATCH computation complete.")
