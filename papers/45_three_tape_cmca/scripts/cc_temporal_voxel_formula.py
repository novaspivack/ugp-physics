import numpy as np

# Physical constants
M_Pl = 1.22e19   # GeV
H0_GeV = 1.44e-42  # GeV
rho_obs = (2.3e-12)**4  # GeV^4

# D_res formula (CatAD reference)
L_model = np.log2(2000/3)
Omega_Lambda_Dres = np.log(2)/(3*np.pi) * L_model
rho_crit = 3*H0_GeV**2*M_Pl**2/(8*np.pi)
rho_Lambda_Dres = Omega_Lambda_Dres * rho_crit

print("=== THE FORMULA ===")
print("ρ_CC = (9/(7×D²)) × M_Pl²×H₀²")
print("where:")
print("  9 = 3² = (3 spatial tapes) × (numerator of τ_proper/τ_lab = 3/7)")
print("  7 = denominator of τ_proper/τ_lab = 3/7 (from P45 proper time rate)")
print("  D = 4 = spacetime dimensions (3 spatial + 1 temporal tape)")
print("  D² = 16 = spacetime dimension squared\n")

# Three components:
N_spatial = 3      # spatial tapes
tau_rate_num = 3   # numerator of proper time rate 3/7
tau_rate_den = 7   # denominator of proper time rate 3/7  
D = 4              # spacetime dimensions

numerator = N_spatial * tau_rate_num  # = 9
denominator = tau_rate_den * D**2    # = 7 × 16 = 112

coeff_voxel_temporal = numerator / denominator
rho_CC_formula = coeff_voxel_temporal * M_Pl**2 * H0_GeV**2

print(f"=== NUMERICAL TEST ===")
print(f"9/(7×16) = 9/112 = {9/112:.6f}")
print(f"ρ_CC = 9/112 × M_Pl²×H₀² = {rho_CC_formula:.4e} GeV^4")
print(f"ρ_Λ (D_res, CatAD) = {rho_Lambda_Dres:.4e} GeV^4")
print(f"ρ_obs = {rho_obs:.4e} GeV^4")
print(f"Ratio ρ_CC/ρ_Dres = {rho_CC_formula/rho_Lambda_Dres:.4f}")
print(f"Ratio ρ_CC/ρ_obs = {rho_CC_formula/rho_obs:.3e}")
print(f"Agreement with D_res: {abs(rho_CC_formula/rho_Lambda_Dres - 1)*100:.2f}%")

# Implied Omega_Lambda from this formula:
# ρ_CC = Omega_Lambda_voxel × ρ_crit
Omega_voxel = rho_CC_formula / rho_crit
print(f"\nImplied Ω_Λ from voxel formula: {Omega_voxel:.4f}")
print(f"Ω_Λ from D_res (CatAD): {Omega_Lambda_Dres:.4f}")
print(f"PDG Ω_Λ: 0.6889")
print(f"Voxel vs D_res: {abs(Omega_voxel - Omega_Lambda_Dres)/Omega_Lambda_Dres*100:.2f}% diff")
print(f"Voxel vs PDG: {abs(Omega_voxel - 0.6889)/0.6889*100:.2f}% diff")

# Express Omega from voxel formula:
# rho_CC = 9/(7*16) * M_Pl^2 * H0^2
# Omega_Λ = rho_CC / rho_crit = rho_CC / (3H0^2M_Pl^2/(8pi))
# = (9/112) * M_Pl^2 * H0^2 * 8pi / (3 * H0^2 * M_Pl^2)
# = (9/112) * 8*pi/3
# = 9*8*pi/(112*3)
# = 72*pi/336
# = 3*pi/14
import sympy as sp
exact = sp.Rational(3,14) * sp.pi
print(f"\nExact: Ω_Λ = 3π/14 = {float(exact):.6f}")

# Null tests:
print("\n=== NULL TESTS ===")
# Null 1: Wrong proper time rate (use 4/7 instead of 3/7)
for rate_num, rate_den, label in [(3,7,"3/7 (correct)"), (4,7,"4/7"), (2,7,"2/7"), (1,1,"1/1")]:
    coeff = N_spatial * rate_num / (rate_den * D**2)
    rho = coeff * M_Pl**2 * H0_GeV**2
    print(f"  τ_rate = {rate_num}/{rate_den}: coeff = {coeff:.4f}, ratio to D_res = {rho/rho_Lambda_Dres:.3f}")

# Null 2: Wrong D (use D=3 or D=5)
print()
for D_test, label in [(3,"D=3 (spatial only)"), (4,"D=4 (correct)"), (5,"D=5")]:
    coeff = N_spatial * tau_rate_num / (tau_rate_den * D_test**2)
    rho = coeff * M_Pl**2 * H0_GeV**2
    print(f"  D = {D_test}: coeff = {coeff:.4f}, ratio to D_res = {rho/rho_Lambda_Dres:.3f}")

# Null 3: Different random CC-like target
rho_alt = (1.5e-12)**4  # arbitrary alternative
print(f"\n  Random target ρ_alt = {rho_alt:.2e}")
print(f"  Formula gives {rho_CC_formula:.2e}, ratio = {rho_CC_formula/rho_alt:.3f} (should be >> 1)")

print("\n=== GTE CONSTANTS USED ===")
print(f"  N_spatial = {N_spatial} (three-tape CMCA)")
print(f"  τ_proper/τ_lab = {tau_rate_num}/{tau_rate_den} = 3/7 (P45, special-relativistic time dilation)")
print(f"  D = {D} (spacetime dimensions = 3 spatial + 1 temporal)")
print(f"  All from existing GTE results — no new inputs!")
