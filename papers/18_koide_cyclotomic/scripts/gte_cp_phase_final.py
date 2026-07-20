"""CKM CP-violating phase from the GTE S3 subgroup chain.

The lepton/down/up generation sectors carry residual flavour symmetries
H_lep = S3 (order 6), H_down = A3 = Z3 (order 3), H_up = Z2 (order 2);
the orders {6, 3, 2} are the GTE-certified subgroup-order set (KoideSectorAngle).

Closed form tested here:

    delta_CP = pi/2 - |H_down| / (|H_lep| + |H_up|) = pi/2 - 3/8
    A        = sin(pi / |H_down|) = sin(pi/3) = sqrt(3)/2

Both feed the Wolfenstein parametrization, with lambda and theta_13 fixed by
Gatto-Sartori-Tonin mass ratios, to give the Jarlskog invariant J.

Null tests vary the subgroup assignment, denominator, and neighbour orders to
confirm the agreement is specific to the {6, 3, 2} assignment.
"""

import numpy as np

# GTE S3 subgroup orders (KoideSectorAngle, Lean-certified)
H_lep = 6   # |S3|
H_down = 3  # |A3| = |Z3|
H_up = 2    # |Z2|

# --- CP phase ---
delta_GTE = np.pi / 2 - H_down / (H_lep + H_up)
delta_PDG = 1.196  # rad (PDG 2024 CKM phase ~ 68.53 deg, uncertainty ~ +/- 3 deg)

print("=== CP PHASE TEST ===")
print(f"delta_CP (GTE: pi/2 - 3/8) = {delta_GTE:.6f} rad = {np.degrees(delta_GTE):.4f} deg")
print(f"delta_CP (PDG)             = {delta_PDG:.6f} rad = {np.degrees(delta_PDG):.4f} deg")
print(f"MATCH: {abs(delta_GTE - delta_PDG) / delta_PDG * 100:.4f}% off")

# --- A parameter ---
A_GTE = np.sin(np.pi / H_down)  # sin(pi/3) = sqrt(3)/2
A_PDG = 0.836
print("\n=== A PARAMETER TEST ===")
print(f"A (GTE: sin(pi/3)) = {A_GTE:.6f}")
print(f"A (PDG)            = {A_PDG}")
print(f"MATCH: {abs(A_GTE - A_PDG) / A_PDG * 100:.2f}% off")

# --- Full Jarlskog from GTE inputs ---
# Quark masses (PDG, GeV)
m_u, m_c, m_t = 2.16e-3, 1.27, 172.69
m_d, m_s, m_b = 4.67e-3, 93.4e-3, 4.18

lambda_CKM = np.sqrt(m_d / m_s)      # Gatto-Sartori-Tonin
sin_theta13 = np.sqrt(m_u / m_t)
V_cb = A_GTE * lambda_CKM**2
sin_theta23 = V_cb                   # |V_cb| = sin(theta_23) at leading order

print("\n=== CKM WOLFENSTEIN PARAMETERS (GTE) ===")
print(f"lambda = sqrt(m_d/m_s) = {lambda_CKM:.4f} (PDG: 0.2245)")
print(f"A = sin(pi/3) = {A_GTE:.4f} (PDG: 0.836)")
print(f"|V_cb| = A*lambda^2 = {V_cb:.5f} (PDG: 0.04186)")
print(f"sin(theta_13) = sqrt(m_u/m_t) = {sin_theta13:.4e} (PDG: ~3.6e-3)")
print(f"delta_CP = pi/2 - 3/8 = {delta_GTE:.4f} rad (PDG: 1.196 rad)")

c12_sq = 1 - lambda_CKM**2
c23_sq = 1 - sin_theta23**2
J_GTE = c12_sq * c23_sq * lambda_CKM * sin_theta13 * sin_theta23 * np.sin(delta_GTE)
J_PDG = 3.18e-5

print("\n=== JARLSKOG INVARIANT ===")
print(f"J (GTE, all inputs) = {J_GTE:.4e}")
print(f"J (PDG)             = {J_PDG:.4e}")
print(f"MATCH: {abs(J_GTE - J_PDG) / J_PDG * 100:.1f}% off")
print(f"Ratio: {J_GTE / J_PDG:.3f}")

# --- Null tests ---
print("\n========== NULL TESTS ==========")

delta_null1 = np.pi / 2 - H_up / (H_lep + H_down)
print("\n=== NULL 1: swap H_down and H_up ===")
print(f"pi/2 - 2/(6+3) = {delta_null1:.4f} rad = {np.degrees(delta_null1):.2f} deg, "
      f"error {abs(delta_null1 - delta_PDG) / delta_PDG * 100:.1f}%")

delta_null2 = np.pi / 2 - H_down / H_lep
print("\n=== NULL 2: denominator = H_lep only ===")
print(f"pi/2 - 3/6 = {delta_null2:.4f} rad = {np.degrees(delta_null2):.2f} deg, "
      f"error {abs(delta_null2 - delta_PDG) / delta_PDG * 100:.1f}%")

delta_null3 = np.pi / 2 - 2 / (H_lep + H_up)
print("\n=== NULL 3: H_down neighbour (2 instead of 3) ===")
print(f"pi/2 - 2/(6+2) = {delta_null3:.4f} rad = {np.degrees(delta_null3):.2f} deg, "
      f"error {abs(delta_null3 - delta_PDG) / delta_PDG * 100:.1f}%")

delta_control = 42.5 * np.pi / 180
print("\n=== NULL 4: wrong target (42.5 deg) ===")
print(f"Formula gives {np.degrees(delta_GTE):.2f} deg, "
      f"error on 42.5 deg control: {abs(delta_GTE - delta_control) / delta_control * 100:.1f}%")
