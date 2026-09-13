"""
kink_pole_mass_dhn_benchmarks.py

Benchmark validation of the spectral (phase-shift) machinery for one-loop
soliton/wall mass corrections, prior to the Phi_MDL (Z7) application.

Validates against the two exact 1+1D Dashen-Hasslacher-Neveu results
(Phys. Rev. D 10, 4130 (1974); values cross-checked against
Nucl. Phys. B 852 (2011) 696 and arXiv:1912.08507):

  sine-Gordon kink:  Delta M = -m/pi                    = -0.3183099 m
  phi^4 kink:        Delta M = m (1/(4 sqrt 3) - 3/(2 pi)) = -0.3331267 m

(m = meson mass in both cases.)

Method: interface formula of Graham-Jaffe-Quandt-Weigel (PRL 87, 131601
(2001), hep-th/0103010) at n = 0 trivial dimensions, real scalar, with the
no-tadpole renormalization scheme (= the DHN mass counterterm):

  E1 = g * [ sum_j (omega_j - m + kappa_j^2/(2m))
             + int_0^inf dk/pi (omega(k) - m - k^2/(2m)) d/dk(delta - delta_1) ]

where delta(k) is the total (both-parity) spatial phase shift,
delta_1 = -(1/2k) int U dz is its first Born approximation, omega = sqrt(k^2+m^2),
bound states have omega_j = sqrt(m^2 - kappa_j^2). The global factor g for a
real scalar is pre-registered to be resolved by the SG benchmark from
{1/4, 1/2, 1} and then FROZEN for phi^4 (no freedom) and for the 3+1D wall.

Also validates:
  - second Born phase shift  delta_2(k) = -(1/4k^2) int_0^inf W(s) sin(2ks) ds,
    W(s) = int U(y) U(y+s) dy, against the exact large-k asymptotics;
  - Levinson sum rule:    int dk/pi delta'        = -(number of bound states)
  - GJQW sum rule (8):    int dk/pi k^2 (delta-delta_1)'        = sum_j kappa_j^2
  - GJQW sum rule (16):   int dk/pi k^4 (delta-delta_1-delta_2)' = -sum_j kappa_j^4

Expected output: both benchmarks reproduced to <0.1%, all sum rules <1e-6 relative.
"""

import signal, sys, json
import numpy as np
from scipy import integrate

TIMEOUT = 600

def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: {TIMEOUT}s wall-clock limit reached.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT)

results = {"description": "1+1D DHN benchmark validation of the spectral machinery",
           "external_anchors": {
               "DHN": "Dashen, Hasslacher, Neveu, Phys. Rev. D 10, 4130 (1974)",
               "cross_check": "Alonso-Izquierdo & Mateos Guilarte, Nucl. Phys. B 852 (2011) 696",
               "interface_formalism": "Graham, Jaffe, Quandt, Weigel, PRL 87, 131601 (2001), hep-th/0103010"},
           "models": {}}

# ===========================================================================
# Model definitions (units m = 1, m = meson mass)
# ===========================================================================
# sine-Gordon kink: fluctuation potential U(z) = -2 sech^2(z)
#   bound states: omega_0 = 0 (kappa = 1)
#   exact total phase shift: delta(k) = 2 arctan(1/k)
# phi^4 kink: fluctuation potential U(z) = -(3/2) sech^2(z/2)
#   bound states: omega_0 = 0 (kappa = 1), omega_1 = sqrt(3)/2 (kappa = 1/2)
#   exact total phase shift: delta(k) = 2 [arctan(1/(2k)) + arctan(1/k)]

MODELS = {
    "sine_gordon": {
        "U": lambda z: -2.0 / np.cosh(z)**2,
        "intU": -4.0,
        "delta": lambda k: 2.0 * np.arctan(1.0 / k),
        "ddelta": lambda k: -2.0 / (k**2 + 1.0),
        "kappas": [1.0],
        "DHN_exact": -1.0 / np.pi,
        "zrange": 30.0,
    },
    "phi4": {
        "U": lambda z: -1.5 / np.cosh(z / 2.0)**2,
        "intU": -6.0,
        "delta": lambda k: 2.0 * (np.arctan(0.5 / k) + np.arctan(1.0 / k)),
        "ddelta": lambda k: 2.0 * (-0.5 / (k**2 + 0.25) - 1.0 / (k**2 + 1.0)),
        "kappas": [1.0, 0.5],
        "DHN_exact": 1.0 / (4.0 * np.sqrt(3.0)) - 3.0 / (2.0 * np.pi),
        "zrange": 60.0,
    },
}

def autocorrelation(U, zmax, s):
    """W(s) = int U(y) U(y+s) dy (even in s)."""
    val, _ = integrate.quad(lambda y: U(y) * U(y + s), -zmax, zmax,
                            limit=400, epsrel=1e-11, epsabs=1e-14)
    return val

def make_delta2(U, zmax):
    """delta_2(k) = -(1/4k^2) int_0^inf W(s) sin(2ks) ds via cached W spline."""
    s_grid = np.linspace(0.0, 2.0 * zmax, 1200)
    W_grid = np.array([autocorrelation(U, zmax, s) for s in s_grid])
    from scipy.interpolate import CubicSpline
    Wsp = CubicSpline(s_grid, W_grid)
    s_end = s_grid[-1]

    def delta2(k):
        # oscillatory integral with sin(2ks): use scipy weighted quad
        val, _ = integrate.quad(lambda s: Wsp(s), 0.0, s_end,
                                weight='sin', wvar=2.0 * k,
                                limit=800, epsrel=1e-10, epsabs=1e-13)
        return -val / (4.0 * k**2)
    return delta2, Wsp

print("=" * 72)
print("1+1D DHN BENCHMARKS — spectral machinery validation")
print("=" * 72)

# global normalization candidates (pre-registered; SG decides, then frozen)
G_CANDIDATES = [0.25, 0.5, 1.0]
g_frozen = None

for name, M in MODELS.items():
    print("\n" + "=" * 64)
    print(f"MODEL: {name}")
    print("=" * 64)
    U, delta, ddelta = M["U"], M["delta"], M["ddelta"]
    kappas = M["kappas"]
    intU = M["intU"]
    zmax = M["zrange"]

    # --- check int U numerically
    intU_num, _ = integrate.quad(U, -zmax, zmax, limit=400, epsrel=1e-12)
    print(f"int U dz: numeric {intU_num:.10f} vs exact {intU:.10f}")
    assert abs(intU_num - intU) < 1e-8

    # --- Born 1: delta_1 = -intU/(2k)
    delta1 = lambda k: -intU / (2.0 * k)
    ddelta1 = lambda k: intU / (2.0 * k**2)

    # --- Levinson: int dk/pi delta' = -(n_bound)
    lev, _ = integrate.quad(lambda k: ddelta(k) / np.pi, 0, np.inf,
                            limit=600, epsrel=1e-12)
    print(f"Levinson: int delta'/pi = {lev:.10f}  [expect {-len(kappas)}]")

    # --- sum rule (8): int dk/pi k^2 (delta-delta_1)' = sum kappa^2
    sr8, _ = integrate.quad(lambda k: k**2 * (ddelta(k) - ddelta1(k)) / np.pi,
                            0, np.inf, limit=800, epsrel=1e-12)
    sum_k2 = sum(K**2 for K in kappas)
    print(f"Sum rule (8): int k^2 (d-d1)'/pi = {sr8:.10f}  [expect {sum_k2:.10f}]")

    # --- delta_2 machinery + asymptotics check
    delta2, Wsp = make_delta2(U, zmax)
    W0 = Wsp(0.0)
    print(f"W(0) = int U^2 = {W0:.10f}")
    print("delta_2 large-k check: k^3 * delta_2(k) -> -W(0)/8 =", -W0 / 8.0)
    for k in [5.0, 10.0, 20.0]:
        d2 = delta2(k)
        print(f"  k={k:5.1f}: k^3 delta_2 = {k**3 * d2:.6f}")

    # exact delta - delta1 - delta2 decay check + sum rule (16)
    def dd_sub2(k, h=1e-4):
        # derivative of (delta - delta1 - delta2) via exact ddelta, ddelta1 and numeric delta2'
        d2p = (delta2(k + h) - delta2(k - h)) / (2.0 * h)
        return ddelta(k) - ddelta1(k) - d2p

    sr16_parts = []
    # integrate sum rule (16): int dk/pi k^4 (delta-delta1-delta2)' + sum kappa^4 = 0
    val16, _ = integrate.quad(lambda k: k**4 * dd_sub2(k) / np.pi,
                              1e-3, 60.0, limit=400, epsrel=1e-8)
    sum_k4 = sum(K**4 for K in kappas)
    print(f"Sum rule (16): int k^4 (d-d1-d2)'/pi = {val16:.8f}  [expect {-sum_k4:.8f}]")

    # --- DHN energy (n = 0): bracket = bound + continuum
    bound = sum(np.sqrt(max(1.0 - K**2, 0.0)) - 1.0 + K**2 / 2.0 for K in kappas)
    # note omega_j = sqrt(m^2 - kappa^2) with m = 1

    def integrand(k):
        w = np.sqrt(k**2 + 1.0)
        return (w - 1.0 - k**2 / 2.0) * (ddelta(k) - ddelta1(k)) / np.pi

    cont, cont_err = integrate.quad(integrand, 0, np.inf, limit=1000, epsrel=1e-12)
    bracket = bound + cont
    print(f"bound = {bound:.10f}, continuum = {cont:.10f} (err {cont_err:.1e})")
    print(f"bracket = {bracket:.10f}")

    exact = M["DHN_exact"]
    print(f"DHN exact = {exact:.10f}")
    for g in G_CANDIDATES:
        print(f"  g = {g}: E1 = {g * bracket:.10f}  (ratio to exact: {g * bracket / exact:.8f})")

    if g_frozen is None:
        # SG decides
        ratios = {g: abs(g * bracket / exact - 1.0) for g in G_CANDIDATES}
        g_frozen = min(ratios, key=ratios.get)
        print(f"  --> FROZEN global factor g = {g_frozen} (from SG benchmark)")

    E1 = g_frozen * bracket
    rel = E1 / exact - 1.0
    print(f"  E1 (g={g_frozen}) = {E1:.10f}; relative deviation from exact: {rel:.3e}")

    results["models"][name] = {
        "levinson": lev, "sum_rule_8": sr8, "sum_rule_8_expect": sum_k2,
        "sum_rule_16": val16, "sum_rule_16_expect": -sum_k4,
        "W0": float(W0), "bound_term": bound, "continuum_term": cont,
        "bracket": bracket, "g_frozen": g_frozen,
        "E1": E1, "DHN_exact": exact, "relative_deviation": rel,
    }

results["g_frozen"] = g_frozen
out = "/Users/nova/ugp-physics/papers/42_phimdl_field/scripts/kink_pole_mass_dhn_benchmarks_results.json"
with open(out, "w") as f:
    json.dump(results, f, indent=2)
print("\nResults saved to:", out)

signal.alarm(0)
print("Done.")
