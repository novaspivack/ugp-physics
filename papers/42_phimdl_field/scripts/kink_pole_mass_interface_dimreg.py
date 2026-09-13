"""
kink_pole_mass_interface_dimreg.py

Independent one-loop quantum mass of the Phi_MDL kink via the renormalized
3+1D domain-wall (interface) tension, using the channel-resolved dimensional-
regularization interface formalism of Graham-Jaffe-Quandt-Weigel
(PRL 87, 131601 (2001), hep-th/0103010), specialized to n = 2 trivial
dimensions and the s = 1 Poschl-Teller fluctuation spectrum (CatAL,
phimdl_fluctuation_is_poschl_teller) shared by the sine-Gordon-family kink.

Machinery validated upstream by kink_pole_mass_dhn_benchmarks.py
(DHN sine-Gordon -m/pi and phi^4 1/(4 sqrt3) - 3/(2pi), both to 3e-14).

Master formula (real scalar, no-tadpole scheme, units m = 1):

  sigma_1(mu) = -(1/12 pi) * B  +  F2bar(mu)
  B  = 1/2  -  (3/pi) int_0^inf k (omega - 1) (delta - delta_1 - delta_2) dk
  F2bar(mu) = +(1/64 pi^2) int_0^inf (dq/pi) Utilde(q)^2
                 int_0^1 dx ln((1 + x(1-x) q^2)/mu^2) dq
       [= -(1/4) int (dq/pi) Utilde^2 * B4_MSbar(q; mu), B4 = -(1/16pi^2) int ln(Delta/mu^2)]

with, for the s=1 PT wall (U = -2 sech^2 z):
  delta(k)  = 2 arctan(1/k)            [exact; Levinson-consistent: delta' < 0]
  delta_1   = 2/k                       [first Born]
  delta_2(k)= -(1/4k^2) int_0^inf W(s) sin(2ks) ds,
  W(s)      = 16 (s cosh s - sinh s)/sinh^3 s    [exact autocorrelation of U]
  Utilde(q) = -2 pi q / sinh(pi q / 2)           [exact FT of U]
  zero mode bound term: omega_0 = 0, kappa_0 = 1 -> 0 - 1 + 3/2 = +1/2.

Renormalization conditions reported:
  - no-tadpole + MSbar bubble at mu (primary family; the corpus convention point
    is mu = m_phi); exact flow dsigma/dlnmu = -1/(6 pi^2)
  - no-tadpole + on-shell two-point subtraction at timelike q^2 = m^2 (GJQW)
  - mu in [m/2, 2m] band; mu at both Lambda_GTE readings

Mass bridge (named assumption BA-AREA, the corpus convention):
  Delta M(mu) = sigma_1(mu) / m^2,  M^Q = M_cl + Delta M, M_cl = (8/49) m_tau.

Expected output: B of order 1; Delta M of order tens of MeV; full scheme table.
"""

import signal, sys, json
import numpy as np
from scipy import integrate

TIMEOUT = 900

def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: {TIMEOUT}s wall-clock limit reached.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT)

m_tau = 1776.86          # MeV (PDG 2024)
M_cl  = 8.0 * m_tau / 49.0

print("=" * 72)
print("Phi_MDL kink: independent one-loop wall mass (GJQW interface dim-reg)")
print("=" * 72)
print(f"m_phi = m_tau = {m_tau} MeV; M_cl = 8m/49 = {M_cl:.4f} MeV")

# ===========================================================================
# Section 1: exact ingredients + verification battery
# ===========================================================================
print("\n--- Section 1: ingredient verification battery ---")

def W_exact(s):
    """W(s) = int U(y)U(y+s) dy for U = -2 sech^2; exact closed form."""
    if s < 1e-4:
        return 16.0/3.0 - (64.0/15.0)*s**2/2.0*2.0/2.0  # series 16(1/3 - (2/15)s^2)
    sh = np.sinh(s)
    return 16.0 * (s*np.cosh(s) - sh) / sh**3

# verify against numeric autocorrelation
def W_numeric(s):
    f = lambda y: 4.0/(np.cosh(y)**2 * np.cosh(y+s)**2)
    val, _ = integrate.quad(f, -40, 40, limit=400, epsrel=1e-12)
    return val

errs = [abs(W_exact(s)-W_numeric(s)) for s in [0.05, 0.5, 1.0, 3.0, 8.0]]
print(f"W(s) closed form vs numeric autocorrelation: max abs err = {max(errs):.2e}")
assert max(errs) < 1e-9

# series coefficients
print(f"W(0) = {W_exact(1e-6):.10f}  [expect 16/3 = {16/3:.10f}]")

def Utilde_exact(q):
    """FT of U = -2 sech^2 z: Utilde(q) = -2 pi q / sinh(pi q / 2)."""
    if abs(q) < 1e-8:
        return -4.0
    return -2.0*np.pi*q/np.sinh(np.pi*q/2.0)

Ut_num, _ = integrate.quad(lambda z: -2.0/np.cosh(z)**2*np.cos(1.3*z), -40, 40,
                           limit=400, epsrel=1e-12)
print(f"Utilde(1.3): closed {Utilde_exact(1.3):.10f} vs numeric {Ut_num:.10f}")
assert abs(Utilde_exact(1.3)-Ut_num) < 1e-9

# Parseval: int_0^inf (dq/pi) Utilde^2 = int U^2 = W(0)
pars, _ = integrate.quad(lambda q: Utilde_exact(q)**2/np.pi, 0, 60,
                         limit=400, epsrel=1e-12)
print(f"Parseval: int (dq/pi) Utilde^2 = {pars:.10f}  [expect {16/3:.10f}]")
assert abs(pars - 16.0/3.0) < 1e-8

# heat-kernel referee: int dz [(V''_K)^2 - m^4] = int (2 m^2 U + U^2) dz = -8/3
hk = 2.0*(-4.0) + 16.0/3.0
print(f"int dz [(V''_K)^2 - m^4] = 2 int U + int U^2 = {hk:.10f}  [expect -8/3 = {-8/3:.10f}]")

# ===========================================================================
# Section 2: delta_2 and the subtracted phase shift
# ===========================================================================
print("\n--- Section 2: delta_2(k) for s=1 PT ---")

S_END = 60.0

def S_of_k(k):
    """S(k) = int_0^inf W(s) sin(2ks) ds (W decays as 64 s e^{-2s})."""
    val, _ = integrate.quad(W_exact, 0.0, S_END, weight='sin', wvar=2.0*k,
                            limit=1000, epsrel=1e-11, epsabs=1e-14)
    return val

def delta2(k):
    return -S_of_k(k)/(4.0*k**2)

# asymptotics check: delta_2 = -(2/3)k^-3 - (2/15)k^-5 + ...
print("delta_2 asymptotics [expect k^3 d2 -> -2/3; k^5 (d2 + 2/(3k^3)) -> -2/15]:")
for k in [4.0, 8.0, 16.0, 32.0]:
    d2 = delta2(k)
    print(f"  k={k:5.1f}: k^3 d2 = {k**3*d2:+.8f};  k^5 (d2+2/(3k^3)) = {k**5*(d2+2.0/(3.0*k**3)):+.6f}")

def delta(k):  return 2.0*np.arctan(1.0/k)
def delta1(k): return 2.0/k

def dsub(k):
    """delta - delta_1 - delta_2; exact tail (8/15)k^-5 for k > K_SW."""
    return delta(k) - delta1(k) - delta2(k)

print("subtracted phase tail [expect k^5 * dsub -> 8/15 = 0.5333]:")
for k in [4.0, 8.0, 16.0, 32.0]:
    print(f"  k={k:5.1f}: k^5 dsub = {k**5*dsub(k):+.6f}")

# ===========================================================================
# Section 3: the bracket B (mu-independent, finite)
# ===========================================================================
print("\n--- Section 3: bracket B ---")

BOUND = 0.5   # zero mode: 0 - 1 + 3/2

def cont_integrand(k):
    w = np.sqrt(k*k + 1.0)
    return k*(w - 1.0)*dsub(k)

K_CUT = 40.0
cont_main, err_main = integrate.quad(cont_integrand, 1e-6, K_CUT,
                                     limit=1200, epsrel=1e-10, epsabs=1e-13)
# analytic tail: integrand ~ k*(k-1+1/(2k))*(8/15)k^-5 ~ (8/15)(k^-3 - k^-4 + (1/2) k^-5)
tail = (8.0/15.0)*( 1.0/(2.0*K_CUT**2) - 1.0/(3.0*K_CUT**3) + 1.0/(8.0*K_CUT**4) )
cont = -(3.0/np.pi)*(cont_main + tail)
print(f"continuum piece: main = {cont_main:.10f} (err {err_main:.1e}), tail = {tail:.2e}")
print(f"continuum term  = {cont:+.10f}")

# convergence diagnostic in K_CUT
for K2 in [25.0, 32.0]:
    cm, _ = integrate.quad(cont_integrand, 1e-6, K2, limit=1200, epsrel=1e-10)
    tl = (8.0/15.0)*( 1.0/(2.0*K2**2) - 1.0/(3.0*K2**3) + 1.0/(8.0*K2**4) )
    print(f"  K_CUT={K2:5.1f}: continuum = {-(3.0/np.pi)*(cm+tl):+.10f}")

B = BOUND + cont
print(f"B = bound(+1/2) + continuum = {B:+.10f}")

# ===========================================================================
# Section 4: F2bar(mu) and schemes
# ===========================================================================
print("\n--- Section 4: renormalized two-point add-back F2bar ---")

def feyn_x_log(q2, mu2):
    """int_0^1 dx ln((1 + x(1-x) q2)/mu2); q2 = Euclidean q^2 (>=0) or timelike (<0)."""
    f = lambda x: np.log((1.0 + x*(1.0-x)*q2)/mu2)
    val, _ = integrate.quad(f, 0.0, 1.0, limit=200, epsrel=1e-12)
    return val

def F2bar_MSbar(mu):
    """+(1/64 pi^2) int_0^inf (dq/pi) Utilde^2 * int_0^1 ln((1+x(1-x)q^2)/mu^2)."""
    g = lambda q: Utilde_exact(q)**2/np.pi * feyn_x_log(q*q, mu*mu)
    val, _ = integrate.quad(g, 0.0, 60.0, limit=600, epsrel=1e-11)
    return val/(64.0*np.pi**2)

# mu-flow verification: dsigma/dlnmu = -1/(6 pi^2)
f1, f2 = F2bar_MSbar(1.0), F2bar_MSbar(np.e)
flow = (f2 - f1)  # per unit ln mu
print(f"flow check: F2bar(e)-F2bar(1) = {flow:.10f}  [expect -1/(6 pi^2) = {-1/(6*np.pi**2):.10f}]")
assert abs(flow + 1.0/(6.0*np.pi**2)) < 1e-8

# CW normalization cross-check at constant-U level (analytic identity already
# verified in derivation; here verify B4(0) consistency):
B4_0 = -feyn_x_log(0.0, 1.0)/(16.0*np.pi**2)
print(f"B4_MSbar(q=0; mu=m) = {B4_0:.3e}  [expect 0]")

PREF = -1.0/(12.0*np.pi)

def sigma1_MSbar(mu):
    return PREF*B + F2bar_MSbar(mu)

def sigma1_onshell_timelike():
    """GJQW on-shell flavor: two-point subtracted at timelike q^2 = m^2.
    B4_OS(q) = B4(q;mu) - B4(q_t = m; mu)  ->  equivalent to MSbar at
    mu_eff^2 = exp(int_0^1 ln(1-x(1-x)) dx)."""
    c = feyn_x_log(-1.0, 1.0)   # int ln(1 - x(1-x))
    mu_eff = np.exp(0.5*c)
    return sigma1_MSbar(mu_eff), mu_eff

print("\n--- Section 5: results (units m^3 for sigma; BA-AREA: DM = sigma/m^2) ---")
print(f"bracket term: PREF*B = {PREF*B:+.8f}")

schemes = {}
LAM_TREE = (8.0/7.0)            # Lambda_GTE tree reading in units of m_phi
for label, mu in [("MSbar mu=m/2", 0.5), ("MSbar mu=m (primary)", 1.0),
                  ("MSbar mu=2m", 2.0), ("MSbar mu=Lambda_tree(8/7 m)", LAM_TREE)]:
    s1 = sigma1_MSbar(mu)
    dM = s1*m_tau     # sigma/m^2 in MeV: sigma[m^3]*m = (units m=1: value*m_tau)
    schemes[label] = {"mu_over_m": mu, "sigma1_m3": s1, "DeltaM_MeV": dM,
                      "MQ_MeV": M_cl + dM}
    print(f"{label:32s}: sigma1 = {s1:+.8f} m^3; DM = {dM:+8.3f} MeV; M^Q = {M_cl+dM:8.3f} MeV")

s1_os, mu_eff = sigma1_onshell_timelike()
dM_os = s1_os*m_tau
schemes["on-shell timelike q2=m2"] = {"mu_over_m": mu_eff, "sigma1_m3": s1_os,
                                      "DeltaM_MeV": dM_os, "MQ_MeV": M_cl + dM_os}
print(f"{'on-shell (q^2=m^2), mu_eff=%.4f' % mu_eff:32s}: sigma1 = {s1_os:+.8f} m^3; "
      f"DM = {dM_os:+8.3f} MeV; M^Q = {M_cl+dM_os:8.3f} MeV")

# self-consistent pole reading: mu = Lambda/m = 7 M^Q / m_tau, M^Q = M_cl + DM(mu)
muc = 7.0*(M_cl)/m_tau
for _ in range(40):
    s1 = sigma1_MSbar(muc)
    MQ = M_cl + s1*m_tau
    mu_new = 7.0*MQ/m_tau
    if abs(mu_new - muc) < 1e-12:
        muc = mu_new
        break
    muc = mu_new
s1_sc = sigma1_MSbar(muc)
dM_sc = s1_sc*m_tau
schemes["MSbar mu=7M^Q self-consistent"] = {"mu_over_m": muc, "sigma1_m3": s1_sc,
                                            "DeltaM_MeV": dM_sc, "MQ_MeV": M_cl + dM_sc}
print(f"{'MSbar mu=7M^Q self-consistent':32s}: mu/m = {muc:.5f}; DM = {dM_sc:+8.3f} MeV; "
      f"M^Q = {M_cl+dM_sc:8.3f} MeV")

# ===========================================================================
# Section 6: comparison with the corpus computation
# ===========================================================================
print("\n--- Section 6: corpus comparison (P42 / 083C dim-reg) ---")
C_zero, C_logfin = 1.0/3.0, -0.707032607769
def dM_corpus(mu):
    return m_tau*(C_zero/(4.0*np.pi) + (C_logfin + np.log(mu))/(8.0*np.pi**2))
print(f"corpus DM(mu=m)   = {dM_corpus(1.0):+8.3f} MeV  (M^Q = {M_cl+dM_corpus(1.0):8.3f})")
print(f"corpus flow dDM/dlnmu = {m_tau/(8*np.pi**2):+.4f} MeV  [= m/(8 pi^2)]")
print(f"ours   flow dDM/dlnmu = {-m_tau/(6*np.pi**2):+.4f} MeV  [= -m/(6 pi^2), no-tadpole+MSbar]")
print(f"full-MSbar (CW) flow  = {+m_tau/(12*np.pi**2):+.4f} MeV  [= +m/(12 pi^2)]")
print("=> corpus running matches NO consistent scheme (audit finding).")

results = {
    "description": "Independent one-loop Phi_MDL kink mass via GJQW interface dim-reg (s=1 PT wall)",
    "rank": "088-R14",
    "machinery_validation": "kink_pole_mass_dhn_benchmarks.py (DHN SG and phi4 to 3e-14)",
    "named_assumptions": {
        "BA-AREA": "Delta M = sigma_1 / m^2 (corpus transverse-cell convention, P42)",
        "scheme": "no-tadpole (DHN-normalized mass CT) + stated bubble subtraction"},
    "bracket": {"bound": BOUND, "continuum": cont, "B": B, "PREF_times_B": PREF*B},
    "flow_check": {"dF2bar_dlnmu": flow, "expect": -1.0/(6.0*np.pi**2)},
    "schemes_MeV": schemes,
    "corpus": {"C_zero": C_zero, "C_logfin": C_logfin,
               "DM_mu_eq_m_MeV": dM_corpus(1.0),
               "corpus_flow_MeV_per_lnmu": m_tau/(8*np.pi**2),
               "our_flow_MeV_per_lnmu": -m_tau/(6*np.pi**2),
               "full_MSbar_CW_flow_MeV_per_lnmu": m_tau/(12*np.pi**2)},
    "M_cl_MeV": M_cl,
}

out = "/Users/nova/ugp-physics/papers/42_phimdl_field/scripts/kink_pole_mass_interface_dimreg_results.json"
with open(out, "w") as f:
    json.dump(results, f, indent=2)
print("\nResults saved to:", out)

signal.alarm(0)
print("Done.")
