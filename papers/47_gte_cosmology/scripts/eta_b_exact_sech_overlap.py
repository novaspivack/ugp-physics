"""
Exact sech overlap computation for GTE leptogenesis kink overlap.

Computes I(r) = integral_{-inf}^{inf} sech(x) * sech(r*x) dx exactly
for r = 5 and r = 11, and checks whether f1*f2 = I(5)^2 * I(11)^2
equals 1/3025 or differs from the asymptotic approximation.
"""

import numpy as np
from scipy import integrate
import signal
import json

TIMEOUT = 120
def _timeout_handler(signum, frame):
    print("TIMEOUT reached. Exiting.")
    import sys; sys.exit(1)
signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT)

def sech_overlap(r, limit=500):
    """I(r) = integral_{-inf}^{inf} sech(x) * sech(r*x) dx"""
    integrand = lambda x: 1/np.cosh(x) * 1/np.cosh(r * x) if r != 0 else 1/np.cosh(x)**2
    result, err = integrate.quad(integrand, -200, 200, limit=limit, epsabs=1e-14, epsrel=1e-14)
    return result, err

print("=" * 70)
print("Exact sech overlap I(r) = int sech(x)*sech(r*x) dx")
print("=" * 70)
print(f"\n{'r':>5}  {'I(r) exact':>14}  {'pi/r (asymp)':>14}  {'ratio I(r)/(pi/r)':>18}  {'err':>10}")
print("-" * 70)

results = {}
for r in [1, 2, 3, 5, 7, 11, 19, 42, 100]:
    I_exact, err = sech_overlap(r)
    I_asymp = np.pi / r
    ratio = I_exact / I_asymp
    print(f"{r:5d}  {I_exact:14.10f}  {I_asymp:14.10f}  {ratio:18.10f}  {err:10.2e}")
    results[str(r)] = {"I_exact": I_exact, "I_asymp": I_asymp, "ratio": ratio, "err": err}

print("\n" + "=" * 70)
print("Key values for eta_B formula: r=5 and r=11")
print("=" * 70)

I5, e5 = sech_overlap(5)
I11, e11 = sech_overlap(11)

print(f"\nI(5)  = {I5:.14f}  (err: {e5:.2e})")
print(f"I(11) = {I11:.14f}  (err: {e11:.2e})")

# Asymptotic values
pi_over_5 = np.pi / 5
pi_over_11 = np.pi / 11
print(f"\npi/5  = {pi_over_5:.14f}")
print(f"pi/11 = {pi_over_11:.14f}")
print(f"\nI(5)/(pi/5)  = {I5/pi_over_5:.10f}  (deviation from 1: {abs(I5/pi_over_5 - 1)*100:.4f}%)")
print(f"I(11)/(pi/11) = {I11/pi_over_11:.10f}  (deviation from 1: {abs(I11/pi_over_11 - 1)*100:.4f}%)")

# Product f1*f2 from exact integrals (squared product)
# In the asymptotic formula: I(r) ~ pi/r, so I(r)/pi = 1/r
# The suppression is defined as f_i = (I(b_R)/(I(b_L)*something))^2
# Need to understand the normalization convention

print("\n" + "=" * 70)
print("Suppression factor analysis")
print("=" * 70)

# Asymptotic convention: I(r) ~ pi/r => normalized overlap = r*I(r)/pi -> 1
# The kink zero-mode integral with normalization factor:
# b_L = 1 (LH fermion), I(1) = integral sech^2(x) dx = 2
I1, _ = sech_overlap(1)
print(f"\nI(1) = integral sech^2(x) dx = {I1:.10f}  (exact = 2.0)")
print(f"      Exact ratio I(1)/2 = {I1/2:.10f}")

# Convention A: f_i = (I(b_R) / 2)^2 * (normalization)
# where normalization = (1/(2*pi))^2 or similar
# For asymptotic: I(b_R) ~ pi/b_R, so (I(b_R)/2)^2 ~ (pi/(2*b_R))^2 = pi^2/(4*b_R^2)

# Convention B: f_i = (I(b_R) / (pi/1))^2 = (b_R * I(b_R) / pi * 1/b_R)^2
# Using r*I(r)/pi -> 1, so b_R*I(b_R)/pi ~ 1, giving f_i ~ 1/b_R^2

# The Lean file uses f_i = b_R^{-2} (α=2 exponent), which is the NORMALIZED result
# after factoring out pi^2 from the formula.

# So the convention is: f_i = (1/b_R)^2 in the asymptotic limit,
# and the exact value is f_i = (I(b_R)*b_R/pi)^2 * (1/b_R^2) = (b_R*I(b_R)/pi)^2 / b_R^2

# Correction factor: how much does the exact f1*f2 differ from 1/3025?
correction_5 = (5 * I5 / np.pi)   # This -> 1 as b_R -> inf
correction_11 = (11 * I11 / np.pi) # This -> 1 as b_R -> inf

print(f"\ncorrection_5  = r*I(r)/pi at r=5:  {correction_5:.10f}")
print(f"correction_11 = r*I(r)/pi at r=11: {correction_11:.10f}")

# In asymptotic convention, f_i = correction_i^2 * 1/b_R^2
# So f1*f2 = correction_5^2 * correction_11^2 * 1/3025
f1_exact = correction_5**2 / 25    # = (5*I5/pi)^2 / 25 = I5^2 * 5^2 / (pi^2 * 25) = I5^2/pi^2
f2_exact = correction_11**2 / 121  # = I11^2 / pi^2
f1f2_exact = f1_exact * f2_exact

print(f"\nf1 exact (asymptotic normalized) = correction_5^2 / 25  = {f1_exact:.10f}")
print(f"f2 exact (asymptotic normalized) = correction_11^2 / 121 = {f2_exact:.10f}")
print(f"f1 * f2 (exact)  = {f1f2_exact:.10f}")
print(f"1/3025           = {1/3025:.10f}")
print(f"f1*f2 / (1/3025) = {f1f2_exact * 3025:.8f}")
print(f"relative error   = {abs(f1f2_exact * 3025 - 1)*100:.4f}%")

# Alternative: what is (I5 * I11)^2?
prod_sq = (I5 * I11)**2
print(f"\n(I(5)*I(11))^2                 = {prod_sq:.14f}")
print(f"1/3025                         = {1/3025:.14f}")
print(f"ratio (I5*I11)^2 / (1/3025)   = {prod_sq * 3025:.10f}")
print(f"This is NOT a meaningful comparison without normalization")

# The meaningful comparison: Lean uses I(b_R) ~ pi/b_R
# so f_i = I(b_R)^2 / (pi/b_R)^2 = (b_R*I(b_R)/pi)^2 -> 1
# The suppression 1/b_R^2 comes AFTER factoring out pi^2 from numerator and denominator
# The 1/3025 = 1/(5*11)^2 / ... wait, 5^2 * 11^2 = 25*121 = 3025. Yes.

# Full calculation: the Yukawa coupling h ~ I(b_R) ~ pi/b_R
# h^2 ~ pi^2/b_R^2
# If we define f_i = h_i^2 / pi^2 * b_R^2 (normalizing out the pi) = (b_R * I(b_R) / pi)^2
# Then f_i -> 1 as b_R -> inf
# The physical suppression is b_R^{-2}, and the normalization is fixed by pi^2

# What the Lean formula actually encodes:
# The ratio f1*f2 = (h1*h2)^2 / h_ref^2 where h_ref is some reference Yukawa
# The denominator 3025 = b_R1^2 * b_R2^2 = 25 * 121
# This is purely arithmetic: the suppression comes from the b_R^2 power law

print("\n" + "=" * 70)
print("eta_B with exact sech overlaps vs asymptotic 1/3025")
print("=" * 70)

D_top = np.exp(-1/3)                # exp(-1/N_c) = exp(-1/3)
sphaleron = 28/79
eps1_CI = 3.98e-5
kappa_K1 = 0.1902

# With asymptotic 1/3025
f1f2_asymp = 1/3025
eta_B_asymp = D_top * sphaleron * eps1_CI * f1f2_asymp * kappa_K1
print(f"\nAsymptotic (1/3025):")
print(f"  eta_B = D_top * (28/79) * eps1^CI * (1/3025) * kappa(K1)")
print(f"        = {D_top:.6f} * {sphaleron:.6f} * {eps1_CI:.4e} * {f1f2_asymp:.8f} * {kappa_K1:.6f}")
print(f"        = {eta_B_asymp:.4e}")
print(f"  PDG:  6.10e-10  |  deviation: {(eta_B_asymp/6.10e-10 - 1)*100:.2f}%")

# With exact correction
# The correction enters as: f1f2_exact = (correction_5 * correction_11)^2 * (1/3025)
full_correction = (correction_5 * correction_11)**2
f1f2_corrected = full_correction * f1f2_asymp
eta_B_exact = D_top * sphaleron * eps1_CI * f1f2_corrected * kappa_K1
print(f"\nExact correction (r*I(r)/pi at r=5,11):")
print(f"  correction_5  = {correction_5:.8f}   (deviation from 1: {abs(correction_5-1)*100:.4f}%)")
print(f"  correction_11 = {correction_11:.8f}  (deviation from 1: {abs(correction_11-1)*100:.4f}%)")
print(f"  (corr_5 * corr_11)^2 = {full_correction:.8f}  (deviation from 1: {abs(full_correction-1)*100:.4f}%)")
print(f"  f1*f2 (corrected) = {f1f2_corrected:.8e}  vs 1/3025 = {1/3025:.8e}")
print(f"  eta_B = {eta_B_exact:.4e}")
print(f"  PDG:  6.10e-10  |  deviation: {(eta_B_exact/6.10e-10 - 1)*100:.2f}%")

print("\n" + "=" * 70)
print("Exact formula for sech overlap integral (no numerics)")
print("=" * 70)
print("""
The exact integral I(r) = integral_{-inf}^{inf} sech(x)*sech(rx) dx has
the known closed form (via residue theorem or Fourier transform):

   I(r) = pi / (r * cosh(pi/(2r)))^{-1} * (2/pi) * ...

Actually, the exact formula via Fourier transform is:
   F[sech(x)](k) = pi * sech(pi*k/2)
   I(r) = (1/r) * integral F[sech](k/r) * F[sech](k) dk / (2*pi)
         = (1/r) * integral pi*sech(pi*k/(2r)) * pi*sech(pi*k/2) dk / (2*pi)
         = (pi/r) * (1/2) * integral sech(pi*k/(2r)) * sech(pi*k/2) dk

This is recursive. Let's use the known result:

   I(r) = (1/cosh(pi/(2r))) * (pi/r) * ... 

The correct formula (via the Beta function / digamma method) is:
   integral_{-inf}^{inf} sech(ax)*sech(bx) dx = (pi/b) * (2/pi) * ...

Let me just verify numerically.
""")

# Verify the exact closed form: there's a known result
# integral_{-inf}^{inf} sech(x)*sech(rx) dx 
# = (pi/r) * sech(pi/(2r)) * ... no, let me compute it differently

# The Fourier transform of sech(x) is pi*sech(pi*k/2)
# I(r) = int sech(x)*sech(rx)dx = (1/r) * int sech(u/r)*sech(u) du
#       = (1/r) * F-convolution...
# Actually: int f(x)*g(x)dx = (1/2pi) * int F[f](k)*conj(F[g](k)) dk
# where F[sech(x)](k) = pi*sech(pi*k/2)  (real, even)
# so I(r) = int sech(x)*sech(rx) dx
#         = int sech(x) * sech(rx) dx
# This is not a standard convolution form.

# Let's use the known formula: 
# int_0^inf sech(ax)*sech(bx) dx = (pi/2) * integral via partial fractions
# From tables: int_{-inf}^{inf} sech(a*x) * sech(b*x) dx = (pi/(a*b)) * 1/...
# Actually from Gradshteyn & Ryzhik: 
# int_0^inf cos(bx)/cosh(ax) dx = (pi/(2a)) * sech(pi*b/(2a))
# So sech via Fourier: F[sech(ax)](xi) = (pi/a)*sech(pi*xi/(2a))

# Therefore:
# I(r) = (1/2pi) * int F[sech(x)](k) * F[sech(rx)](k) dk  (Parseval)
# = (1/2pi) * int (pi*sech(pi*k/2)) * (pi/r * sech(pi*k/(2r))) dk
# = (pi/(2r)) * int sech(pi*k/2) * sech(pi*k/(2r)) dk
# This is still recursive. Let u = pi*k/2:
# = (1/r) * int sech(u) * sech(u/r) du / 2 ... = I(r)/2 ???

# That can't be right. Let me use the direct formula for the r→1 case:
# I(1) = int sech^2(x)dx = [tanh(x)]_{-inf}^{inf} = 1 - (-1) = 2 ✓

# For general r, using the formula:
# I(r) = (pi/r) * sech(pi/2) when... no.

# Let's try the exact formula numerically and look for patterns:
print("Checking for exact closed form via ratio I(r)*r/pi:")
for r in [1, 2, 3, 5, 7, 11, 13, 17, 19, 23, 42, 100]:
    I_r, _ = sech_overlap(r)
    ratio_to_pi = r * I_r / np.pi
    # Check if this equals sech(pi/(2r)) or similar
    sech_pi_2r = 1/np.cosh(np.pi/(2*r))
    print(f"  r={r:3d}: r*I(r)/pi = {ratio_to_pi:.8f}, sech(pi/(2r)) = {sech_pi_2r:.8f}, match = {abs(ratio_to_pi - sech_pi_2r):.2e}")

print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)

signal.alarm(0)

# Save results
summary = {
    "I5": I5, "I5_err": e5,
    "I11": I11, "I11_err": e11,
    "pi_over_5": pi_over_5, "pi_over_11": pi_over_11,
    "correction_5": correction_5, "correction_11": correction_11,
    "f1f2_asymp": f1f2_asymp,
    "f1f2_exact_normalized": f1f2_corrected,
    "full_correction_factor": full_correction,
    "eta_B_asymp": eta_B_asymp,
    "eta_B_exact": eta_B_exact,
    "pdg": 6.10e-10,
    "deviation_asymp_pct": (eta_B_asymp/6.10e-10 - 1)*100,
    "deviation_exact_pct": (eta_B_exact/6.10e-10 - 1)*100,
}
import os
_out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "eta_b_exact_sech_overlap_results.json")
with open(_out_path, "w") as f:
    json.dump(summary, f, indent=2)
print(f"\nResults saved to {_out_path}")
