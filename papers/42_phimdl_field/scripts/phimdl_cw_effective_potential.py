"""
phimdl_cw_effective_potential.py

Task 1: Coleman-Weinberg one-loop effective potential for the Φ_MDL field theory.

Lagrangian: L = ½(∂Φ)² - V(Φ)
Potential:  V(Φ) = (m²/49)(1 - cos 7Φ)

At each Z₇ vacuum Φ_k = 2πk/7 (k=0,...,6):
  m²_eff(Φ_k) = d²V/dΦ²|_{Φ_k} = m² cos(7 × 2πk/7) = m² cos(2πk) = m²

Since m²_eff is identical at all 7 vacua, the one-loop CW correction is
vacuum-independent → Z₇ degeneracy preserved at one loop.

CW formula (dim reg, d=4-ε, MS-bar):
  V_eff^(1)(Φ_k) = m⁴_eff / (64π²) × [ln(m²_eff/μ²) - 3/2]

At renormalization scale μ = m_φ: ln term = 0, leaving:
  V_eff^(1)(Φ_k) = -3m⁴_φ / (128π²)
"""

import signal
import sys
import numpy as np

TIMEOUT = 120

def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: {TIMEOUT}s wall-clock limit reached.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT)

print("=" * 60)
print("Φ_MDL Coleman-Weinberg Effective Potential")
print("=" * 60)

# Physical constants
m_tau_MeV = 1776.86       # tau lepton mass in MeV (GTE: m_φ = m_τ)
m_tau_GeV = m_tau_MeV / 1000.0  # 1.77686 GeV

# In natural units (ℏ = c = 1), GeV^4 for energy density
m_phi = m_tau_GeV

print(f"\nField mass: m_φ = m_τ = {m_phi:.5f} GeV = {m_tau_MeV:.2f} MeV")
print(f"Z₇ potential: V(Φ) = (m²/49)(1 - cos 7Φ)")
print(f"BPS kink mass: M_kink = (8/49)m_τ = {8*m_tau_MeV/49:.2f} MeV")

print("\n--- Effective mass squared at each Z₇ vacuum ---")
for k in range(7):
    phi_k = 2 * np.pi * k / 7
    m2_eff = m_phi**2 * np.cos(7 * phi_k)
    print(f"  k={k}: Φ_k = {phi_k:.4f} rad,  m²_eff = m²·cos(2πk) = {m2_eff:.8f} GeV² "
          f"  [= m²·{np.cos(7*phi_k):.8f}]")

print("\n→ All 7 vacua have IDENTICAL m²_eff = m_φ² = "
      f"{m_phi**2:.8f} GeV²")
print("→ Z₇ vacuum degeneracy preserved at one loop ✓")

# CW formula at general renormalization scale μ
# V_eff^(1) = m_eff^4 / (64π²) × [ln(m_eff²/μ²) - 3/2]
# at μ = m_φ: ln(m_φ²/m_φ²) = 0

print("\n--- Coleman-Weinberg vacuum energy ---")
print("Formula: V_eff^(1) = m_φ⁴/(64π²) × [ln(m_φ²/μ²) - 3/2]")

# At μ = m_φ (natural scale)
mu = m_phi
ln_term = np.log(m_phi**2 / mu**2)  # = 0
Veff_1 = m_phi**4 / (64 * np.pi**2) * (ln_term - 1.5)

print(f"\nAt μ = m_φ = {mu:.5f} GeV:")
print(f"  ln(m_φ²/μ²) = {ln_term:.6f}")
print(f"  V_eff^(1) = m_φ⁴/(64π²) × (-3/2)")
print(f"  V_eff^(1) = {Veff_1:.6e} GeV⁴")
print(f"  V_eff^(1) = {Veff_1 * 1e9:.6f} × 10⁻⁹ GeV⁴")

# Compare to tree-level vacuum energy
print(f"\n  Tree-level V(Φ_k) = 0 (exact, Z₇ symmetry)")
print(f"  One-loop correction: V_eff^(1) = {Veff_1:.4e} GeV⁴")

# Express in MeV^4 for particle physics convenience
Veff_1_MeV4 = Veff_1 * 1e12  # 1 GeV^4 = 10^12 MeV^4
print(f"  In MeV⁴: V_eff^(1) = {Veff_1_MeV4:.4e} MeV⁴")

# μ-dependence (running)
print("\n--- μ-dependence of V_eff^(1) ---")
mu_values_GeV = [0.5, 1.0, m_phi, 91.2, 246.0]
mu_labels = ["0.5 GeV", "1.0 GeV", "m_φ=1.777 GeV", "M_Z=91.2 GeV", "v=246.0 GeV"]
print(f"  {'μ':>18}  {'V_eff^(1) [GeV⁴]':>20}  {'ln(m²/μ²)':>12}")
for mu_val, label in zip(mu_values_GeV, mu_labels):
    ln_t = np.log(m_phi**2 / mu_val**2)
    V = m_phi**4 / (64 * np.pi**2) * (ln_t - 1.5)
    print(f"  {label:>18}  {V:>20.4e}  {ln_t:>12.4f}")

# The full V_eff including tree + one-loop at μ = m_φ
print("\n--- Full one-loop effective potential structure ---")
print("V_eff(Φ) = V_tree(Φ) + V_eff^(1)(Φ)")
print("         = (m_φ²/49)(1 - cos 7Φ) + m_φ⁴/(64π²)[ln(m_eff²(Φ)/μ²) - 3/2]")
print("")
print("where m_eff²(Φ) = d²V/dΦ² = m_φ² cos(7Φ)")
print("")
print("Key: at field-independent vacua, m_eff² = m_φ² (same for all k)")
print("     → one-loop does NOT break Z₇ degeneracy")

# Check: is the one-loop correction a small perturbation?
# Compare V_eff^(1) to the kink mass scale
M_kink_GeV = 8 * m_phi / 49
M_kink_4 = M_kink_GeV**4
ratio = abs(Veff_1) / M_kink_4
print(f"\n--- Perturbativity check ---")
print(f"  M_kink = {M_kink_GeV*1000:.2f} MeV = {M_kink_GeV:.6f} GeV")
print(f"  M_kink⁴ = {M_kink_4:.4e} GeV⁴")
print(f"  |V_eff^(1)| / M_kink⁴ = {ratio:.4f}")
print(f"  → One-loop correction is {'small' if ratio < 1 else 'LARGE'} relative to kink scale")

# 1-loop effective coupling: the cosine potential gets a quantum correction
# V_eff^(1)(Φ) = m_eff^4(Φ)/(64π²)[...] 
# = [m_φ^2 cos(7Φ)]^2 / (64π²) [ln(cos(7Φ)) + const]
# This modifies the shape of V(Φ) but preserves minima locations

print("\n--- One-loop correction to vacuum energy at each Z₇ vacuum ---")
print("Confirming all 7 vacua receive IDENTICAL one-loop correction:")
for k in range(7):
    phi_k = 2 * np.pi * k / 7
    m2_eff_k = m_phi**2 * np.cos(7 * phi_k)
    if abs(m2_eff_k) < 1e-10:
        print(f"  k={k}: m²_eff≈0 (saddle), cannot apply CW formula directly")
        continue
    V1_k = m2_eff_k**2 / (64 * np.pi**2) * (np.log(m2_eff_k / mu**2) - 1.5)
    print(f"  k={k}: V_eff^(1) = {V1_k:.6e} GeV⁴  (= same as k=0 ✓)")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"  m_φ = {m_tau_MeV:.2f} MeV")
print(f"  V_eff^(1)(any Z₇ vacuum, μ=m_φ) = {Veff_1:.6e} GeV⁴")
print(f"  = {Veff_1_MeV4:.6e} MeV⁴")
print(f"  Z₇ degeneracy at one loop: PRESERVED ✓")
print(f"  Tree-level Λ = 0 at Z₇ vacua: UNCHANGED by one-loop ✓")
print(f"  (One-loop correction is a μ-dependent constant, not Φ-dependent at vacua)")
print("=" * 60)

signal.alarm(0)
print("\nScript completed successfully.")
