import numpy as np

# === GTE SECTOR STRUCTURE ===
# S3 subgroup chain: |H_lep|=6, |H_down|=3, |H_up|=2
# Sector cone angles: theta_k = |H_k|/27 = |H_k|/N_c^3
theta_lep = 6/27   # 2/9 (CatAL, Lean-certified)
theta_down = 3/27  # 1/9
theta_up = 2/27

print("=== BLOCKER 1: A parameter from subgroup geometry ===")
# Hypothesis: A = sin(pi / |H_sector|) for the down sector
# |H_down| = |A3| = |Z3| = 3
H_down = 3  # size of down-sector residual symmetry group
A_GTE = np.sin(np.pi / H_down)  # sin(pi/3) = sqrt(3)/2
A_PDG = 0.836
print(f"A (GTE: sin(pi/|H_down|) = sin(pi/3)) = {A_GTE:.6f}")
print(f"A (PDG) = {A_PDG}")
print(f"Match: {abs(A_GTE - A_PDG)/A_PDG*100:.2f}% off")

# Cross-check for other sectors:
print(f"\nCross-checks:")
print(f"sin(pi/|H_lep|=6) = sin(pi/6) = {np.sin(np.pi/6):.4f}  (= 1/2)")
print(f"sin(pi/|H_up|=2) = sin(pi/2) = {np.sin(np.pi/2):.4f}  (= 1)")
# sin(pi/6) = 0.5: for leptons this would be the leptonic mixing A ~ 0.5?
# sin(pi/2) = 1: for up quarks, A_up = 1?

# Full CKM from this:
lambda_CKM = np.sqrt(4.67e-3 / 93.4e-3)  # GST: sqrt(m_d/m_s)
V_cb = A_GTE * lambda_CKM**2
print(f"\nUsing A = sin(pi/3):")
print(f"lambda = sqrt(m_d/m_s) = {lambda_CKM:.4f} (PDG: 0.2245)")
print(f"|V_cb| = A * lambda^2 = {V_cb:.4f} (PDG: 0.04186)")
print(f"|V_cb| match: {abs(V_cb - 0.04186)/0.04186*100:.1f}% off")

print("\n=== BLOCKER 2: CP phase = pi/2 - (theta_up + theta_down) ===")
# Hypothesis: delta_CP = pi/2 - (theta_up + theta_down) = pi/2 - 5/27
delta_GTE = np.pi/2 - (theta_up + theta_down)
delta_PDG = 1.196  # radians (PDG 2024: 69.6 +- 3.3 degrees)
print(f"delta_CP (GTE: pi/2 - 5/27) = {delta_GTE:.6f} rad = {np.degrees(delta_GTE):.2f} deg")
print(f"delta_CP (PDG) = {delta_PDG:.6f} rad = {np.degrees(delta_PDG):.2f} deg")
print(f"Match: {abs(delta_GTE - delta_PDG)/delta_PDG*100:.2f}% off")

# Geometric justification:
print(f"\nGeometric argument:")
print(f"  pi/2 = 'maximal CP violation' axis")
print(f"  theta_up + theta_down = 5/27 = 'total quark deviation from CP-conserving axis'")
print(f"  delta_CP = pi/2 - 5/27 = angle from quark system to pi/2 axis")
print(f"  = {delta_GTE:.4f} rad = pi/2 - 5/27 = {np.pi/2:.4f} - {5/27:.4f}")

print("\n=== FULL JARLSKOG J WITH BOTH GTE INPUTS ===")
# Using: lambda from GST, A = sin(pi/3), delta = pi/2 - 5/27
# sin(theta_13) from sqrt(m_u/m_t)
m_u, m_t = 2.16e-3, 172.69
sin_theta13 = np.sqrt(m_u/m_t)
sin_theta23 = V_cb / lambda_CKM  # = A * lambda
sin_theta12 = lambda_CKM

print(f"CKM angles:")
print(f"  sin(theta_12) = {sin_theta12:.4f} (Cabibbo)")
print(f"  sin(theta_23) = {sin_theta23:.4f} (from A*lambda)")
print(f"  sin(theta_13) = {sin_theta13:.4e}")
print(f"  delta_CP = {np.degrees(delta_GTE):.2f} deg")

# Jarlskog invariant
# J = c12^2 * c23^2 * s12 * s13 * s23 * sin(delta)
c12 = np.sqrt(1 - sin_theta12**2)
c23 = np.sqrt(1 - sin_theta23**2)
J_GTE = c12**2 * c23**2 * sin_theta12 * sin_theta13 * sin_theta23 * np.sin(delta_GTE)
J_PDG = 3.18e-5

print(f"\nJarlskog J:")
print(f"  J (GTE, full) = {J_GTE:.3e}")
print(f"  J (PDG) = {J_PDG:.3e}")
print(f"  Ratio: {J_GTE/J_PDG:.3f}")
print(f"  Match: {abs(J_GTE-J_PDG)/J_PDG*100:.1f}% off")

# Null test: check GST for 23 sector differently
# Alternative A: sin(theta_23) from sector angle ratio?
sin23_alt1 = theta_down * lambda_CKM  # = (3/27) * 0.22 = 0.024
sin23_alt2 = np.sin(theta_down)  # = sin(1/9) = 0.110
sin23_alt3 = theta_down * np.sin(theta_down + theta_up)  #
print(f"\nAlternative theta_23 formulas:")
print(f"  theta_down * lambda = {sin23_alt1:.4f} (PDG: {V_cb/lambda_CKM:.4f} = A*lambda)")
print(f"  sin(theta_down) = {sin23_alt2:.4f}")
# What value gives the correct J?
sin23_needed = 0.04186 / lambda_CKM  # = |V_cb|/lambda = A*lambda
print(f"  Needed: |V_cb|/lambda = A*lambda = {sin23_needed:.4f}")
print(f"  GTE gives A = sin(pi/3) = {A_GTE:.4f} -> A*lambda = {A_GTE*lambda_CKM:.4f}")

# ===== H0 CHAIN: LEPTOGENESIS =====
print("\n" + "="*50)
print("=== H0 CHAIN: Leptonic J from GTE delta_lep ===")
# Baryon asymmetry from J (leptogenesis route, not EWBG)
# In leptogenesis: eta_B ~ (1/100) * J_lep where J_lep is the leptonic Jarlskog
# The leptonic J might be much larger than the quark J
# Leptonic Wolfenstein: for leptons with theta_lep = 2/9
theta_lep = 6/27
# PMNS mixing angles: theta_12 ~ 33 deg, theta_23 ~ 45 deg, theta_13 ~ 8.6 deg
# The GTE leptonic CP phase could be: delta_lep = pi/2 - theta_lep = pi/2 - 6/27 = pi/2 - 2/9
delta_lep_GTE = np.pi/2 - theta_lep
print(f"\nLeptonic CP phase: delta_lep = pi/2 - theta_lep = pi/2 - 2/9 = {np.degrees(delta_lep_GTE):.2f} deg")
# PMNS deltas_CP range: unknown, hinted around 195 deg (not well measured)
# The leptonic Jarlskog: J_lep ~ s12*s13*s23*sin(delta_lep) * c12^2*c23^2
# PMNS mixing: s12=sin(33)=0.545, s23=sin(45)=0.707, s13=sin(8.6)=0.149
s12_PMNS, s23_PMNS, s13_PMNS = 0.545, 0.707, 0.149
J_lep = s12_PMNS * s13_PMNS * s23_PMNS * np.sin(delta_lep_GTE) * (1-s12_PMNS**2) * (1-s23_PMNS**2)
print(f"Leptonic J (GTE delta_lep) ~ {J_lep:.3e}")
print(f"(PDG leptonic J best fit: ~0.03)")
