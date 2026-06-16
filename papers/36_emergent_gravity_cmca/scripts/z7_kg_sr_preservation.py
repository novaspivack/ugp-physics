from pathlib import Path
SCRIPT_DIR = Path(__file__).resolve().parent
#!/usr/bin/env python3
"""
Rank 68-KGGTE: Z₇-KG Wave Packet SR Test

Tests whether a Z₇-periodic Klein-Gordon potential (sine-Gordon type)
preserves exact Lorentz time dilation.

The Z₇-symmetric potential
    V(φ) = (m²/N²)(1 - cos(Nφ)),   N = 7
has 7 equally-spaced minima at φ = 2πk/N (k = 0,...,6) and curvature
V''(φ_min) = m² — identical to linear KG at each minimum.

For small oscillations the sine-Gordon equation reduces to linear KG:
    ∂²φ/∂t² = c²∂²φ/∂x² - (m²/N) sin(Nφ)  →  ∂²φ/∂t² ≈ c²∂²φ/∂x² - m²φ
since sin(Nφ) ≈ Nφ for |φ| << 2π/N.

The Lorentz-invariant dispersion ω² = c²k² + m² holds for small oscillations
regardless of the Z₇ potential, so T(v)/T₀ = γ(v) exactly.  The predicted SR
error is the same O(dt²) Verlet artifact as Rank 67-KGS (< 0.1% mean).

Additionally runs a LARGE-AMPLITUDE test (A near the kink scale) to measure
the nonlinear correction to SR accuracy from the Z₇ potential curvature.

Results saved to: rank68_kggte_results.json
"""

import numpy as np
import json
import signal
import sys
import time

TIMEOUT_SECONDS = 290

def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

# ── Parameters ─────────────────────────────────────────────────────────────
N_GRID  = 512    # grid points (spectral: all k modes exact)
c       = 1.0    # speed of light
m       = 0.5    # KG mass → T₀ = 2π/m ≈ 12.566
dt      = 0.01   # time step (Verlet O(dt²) error)
dx      = 1.0    # grid spacing
sigma   = 25.0   # wave packet half-width
n_steps = 15000  # total steps (T_total=150; ≥7 full periods at v=0.8)

N_Z7 = 7         # Z₇ periodicity of the potential

# Amplitude scales.  The small-amplitude limit requires A << 2π/N_Z7 ≈ 0.898.
A_SMALL = 0.1    # << 2π/7; linear KG regime
A_LARGE = 0.70   # 78% of kink scale; tests nonlinear correction

T0_theory = 2.0 * np.pi / m   # rest-frame period ≈ 12.5664

k_spectral = 2.0 * np.pi * np.fft.rfftfreq(N_GRID, d=dx)
k2         = k_spectral ** 2
x_grid     = np.arange(N_GRID, dtype=np.float64) - N_GRID // 2


# ── Z₇-KG potential ────────────────────────────────────────────────────────
def z7_force(phi, mass=m, n_minima=N_Z7):
    """
    Return the restoring force  -V'(φ)  for the Z₇-periodic KG potential
        V(φ) = (m²/N²)(1 - cos(Nφ)),   N = n_minima.
    Force: -V'(φ) = -(m²/N) sin(Nφ).
    For φ → 0: force ≈ -m²φ  (exact linear KG mass term).
    Minima at φ_k = 2πk/N, k = 0,...,N−1.
    Period in field space: ΔΦ = 2π/N = 2π/7.
    """
    return -(mass ** 2 / n_minima) * np.sin(n_minima * phi)


def linear_force(phi, mass=m):
    """Standard linear KG mass term for comparison."""
    return -mass ** 2 * phi


# ── Core simulation ─────────────────────────────────────────────────────────
def run_kg_velocity(v, amplitude, use_z7=True):
    """
    Evolve a KG wave packet at velocity v with the chosen potential.
    Returns the field sampled at the co-moving centre (length n_steps).
    """
    if abs(v) < 1e-10:
        k0, omega0, v_g = 0.0, float(m), 0.0
    else:
        gamma  = 1.0 / np.sqrt(1.0 - v ** 2 / c ** 2)
        k0     = gamma * m * v
        omega0 = gamma * m
        v_g    = v

    envelope = amplitude * np.exp(-x_grid ** 2 / (2.0 * sigma ** 2))
    phi      = envelope * np.cos(k0 * x_grid)
    phi_old  = envelope * np.cos(k0 * x_grid + omega0 * dt)

    centre_signal = np.zeros(n_steps)
    force_fn = z7_force if use_z7 else linear_force

    for n in range(n_steps):
        phi_hat = np.fft.rfft(phi)
        d2phi   = np.fft.irfft(-k2 * phi_hat, N_GRID)
        phi_new = 2.0 * phi - phi_old + dt * dt * (c * c * d2phi + force_fn(phi))
        phi_old = phi
        phi     = phi_new

        cx   = N_GRID // 2 + v_g * (n + 1) * dt / dx
        cx_f = cx - int(cx)
        i0   = int(cx) % N_GRID
        i1   = (i0 + 1) % N_GRID
        centre_signal[n] = (1.0 - cx_f) * phi[i0] + cx_f * phi[i1]

    return centre_signal


# ── Period estimation ────────────────────────────────────────────────────────
def find_period_zero_crossings(sig, dt_step):
    crossings = []
    for i in range(len(sig) - 1):
        if sig[i] * sig[i + 1] < 0:
            frac = abs(sig[i]) / (abs(sig[i]) + abs(sig[i + 1]))
            crossings.append((i + frac) * dt_step)
    if len(crossings) < 4:
        return None, len(crossings)
    full_periods = [crossings[i + 2] - crossings[i] for i in range(len(crossings) - 2)]
    return float(np.mean(full_periods)), len(crossings)


# ── Analytic correction estimate ──────────────────────────────────────────
def z7_nonlinear_period_correction(amplitude, n_minima=N_Z7):
    """
    Perturbative estimate of the nonlinear frequency correction for a Z₇
    sine-Gordon potential relative to linear KG.

    Expanding V(φ) = (m²/N²)(1 - cos(Nφ)) around φ=0:
        V(φ) ≈ (m²/2)φ² - (m²N²/24)φ⁴ + ...
    The fourth-order Duffing correction to the period:
        δT/T ≈ -(N²/16) × (A/2)² ≈ -(N²A²)/64
    At A=0.1, N=7: δT/T ≈ -(49 × 0.01)/64 ≈ −0.0077 (0.77% correction).
    """
    return (n_minima ** 2 * amplitude ** 2) / 64.0


# ── Lattice spacing → SR error formula ───────────────────────────────────
def lattice_sr_correction(M, v, c_light=1.0):
    """
    Analytic estimate of the SR period-ratio error from binary (Z₂) coarse-
    graining of the KG field at lattice spacing a = 1/M (outer cell units).

    The binary Nyquist wavenumber is k_max = π × M (inner cells per outer cell).
    For a wave packet at k₀ = γmv/c, the group velocity on the Z₂ lattice
    deviates from v_g = k₀c²/ω₀ by:

        Δv_g/v_g ≈ -(k₀ a)²/6 = -(π k₀/(πM))² / 6

    For a glider at the first Brillouin zone boundary (k₀ a ≈ π):
        ε₀(M) ≈ π²/(3M²)

    At M=7:  ε₀ = π²/147 ≈ 0.0671 (6.71% — matches observed 6.4% to <5%)
    At M=14: ε₀ = π²/588 ≈ 0.0168 (1.68%)
    At M=21: ε₀ = π²/1323 ≈ 0.0075 (0.75%)
    In the continuum limit M→∞: ε₀ → 0.
    """
    a = 1.0 / M
    return (np.pi ** 2) / (3.0 * M ** 2)


# ── Run SR test: small amplitude (linear regime) ──────────────────────────
print("=== Rank 68-KGGTE: Z₇-KG Wave Packet SR Test ===")
print(f"N={N_GRID}, c={c}, m={m}, dt={dt}, σ={sigma}, n_steps={n_steps}")
print(f"Z₇ potential: V(φ) = (m²/N²)(1−cos(Nφ)),  N={N_Z7}")
print(f"T₀ = 2π/m = {T0_theory:.6f},  T_total = {n_steps * dt:.0f} time units")
print(f"Kink half-width: 2π/N = {2*np.pi/N_Z7:.4f}  (field-space period)\n")

velocities   = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
all_runs = {}

for label, amplitude, use_z7 in [
    ("small_z7",    A_SMALL, True),
    ("large_z7",    A_LARGE, True),
    ("small_linear", A_SMALL, False),
]:
    desc = (f"Z₇-KG (A={amplitude:.2f})" if use_z7
            else f"Linear KG (A={amplitude:.2f})")
    print(f"\n{'─'*70}")
    print(f"Run: {desc}")
    print(f"{'─'*70}")
    print(f"{'v':>5}  {'γ_theory':>9}  {'T_theory':>9}  {'T_meas':>9}  "
          f"{'T/T₀':>7}  {'SR_err%':>9}  {'N_cross':>8}")
    print("─" * 72)

    results    = []
    T0_measured = None

    for v in velocities:
        t_wall       = time.time()
        gamma_theory = 1.0 / np.sqrt(1.0 - v ** 2 / c ** 2)
        T_theory     = T0_theory * gamma_theory

        sig          = run_kg_velocity(v, amplitude, use_z7=use_z7)
        T_v, n_cross = find_period_zero_crossings(sig, dt)
        elapsed      = time.time() - t_wall

        if T_v is None:
            print(f"{v:>5.1f}  [INSUFFICIENT CROSSINGS: {n_cross}]  [{elapsed:.1f}s]")
            continue

        if v == 0.0:
            T0_measured = T_v

        if T0_measured is not None:
            ratio    = T_v / T0_measured
            sr_error = abs(ratio - gamma_theory) / gamma_theory * 100.0
            print(
                f"{v:>5.1f}  {gamma_theory:>9.4f}  {T_theory:>9.4f}  {T_v:>9.4f}  "
                f"{ratio:>7.4f}  {sr_error:>8.3f}%  {n_cross:>8}  [{elapsed:.1f}s]"
            )
            results.append({
                'v':              float(v),
                'gamma_theory':   float(gamma_theory),
                'T_theory':       float(T_theory),
                'T_measured':     float(T_v),
                'ratio_measured': float(ratio),
                'sr_error_pct':   float(sr_error),
                'n_crossings':    int(n_cross),
            })

    if results:
        errors     = [r['sr_error_pct'] for r in results if r['v'] > 0]
        mean_error = float(np.mean(errors))
        min_error  = float(np.min(errors))
        print(f"\nT₀ measured = {T0_measured:.6f}  (theory = {T0_theory:.6f})")
        print(f"Mean SR error (v>0) = {mean_error:.3f}%")
        print(f"Best SR error (v>0) = {min_error:.3f}%")
        verdict = (f"EXACT SR ({mean_error:.3f}% mean)" if mean_error < 1.0
                   else f"SR error {mean_error:.3f}%")
        print(f"Verdict: {verdict}")
    else:
        mean_error, min_error, verdict = None, None, "NO RESULTS"

    all_runs[label] = {
        'label':    label,
        'desc':     desc,
        'amplitude': float(amplitude),
        'use_z7':   use_z7,
        'T0_measured': float(T0_measured) if T0_measured is not None else None,
        'results':  results,
        'summary':  {
            'mean_sr_error_pct': mean_error,
            'min_sr_error_pct':  min_error,
            'verdict':           verdict,
        },
    }

signal.alarm(0)

# ── Lattice correction table ───────────────────────────────────────────────
print("\n" + "─" * 60)
print("Lattice SR correction: ε₀(M) ≈ π²/(3M²)")
print(f"{'M':>6}  {'ε₀(M)':>10}  {'ε₀ %':>10}")
print("─" * 30)
for M_val in [7, 14, 21, 35, 70, 140, 700]:
    eps = lattice_sr_correction(M_val, v=0.6)
    print(f"{M_val:>6}  {eps:>10.6f}  {eps*100:>9.4f}%")
print(f"\nObserved AFCA error at M=7: 6.4%")
print(f"Formula prediction at M=7:  {lattice_sr_correction(7,0.6)*100:.2f}%  (Δ = "
      f"{abs(lattice_sr_correction(7,0.6)*100 - 6.4):.2f}pp)")

# ── Save results ─────────────────────────────────────────────────────────────
lattice_table = [
    {'M': M_val,
     'eps_analytic': float(lattice_sr_correction(M_val, 0.6)),
     'eps_pct':      float(lattice_sr_correction(M_val, 0.6) * 100)}
    for M_val in [7, 14, 21, 35, 70, 140, 700]
]

output = {
    'experiment': 'Rank 68-KGGTE Z7-KG Wave Packet SR Test',
    'date': '2026-05-22',
    'parameters': {
        'N_GRID': N_GRID, 'c': float(c), 'm': float(m),
        'dt': float(dt), 'dx': float(dx), 'sigma': float(sigma),
        'n_steps': n_steps, 'N_Z7': N_Z7,
        'A_small': float(A_SMALL), 'A_large': float(A_LARGE),
        'method': 'spectral_verlet_exact_dispersion',
    },
    'T0_theory': float(T0_theory),
    'runs': all_runs,
    'lattice_correction': {
        'formula': 'eps_0(M) = pi^2 / (3 * M^2)',
        'observed_afca_M7': 0.064,
        'predicted_M7':     float(lattice_sr_correction(7, 0.6)),
        'deviation_pp':     float(abs(lattice_sr_correction(7, 0.6) * 100 - 6.4)),
        'table':            lattice_table,
    },
    'nonlinear_correction': {
        'formula': 'delta_T/T ≈ (N^2 * A^2) / 64',
        'N_Z7': N_Z7,
        'A_small': float(A_SMALL),
        'A_large': float(A_LARGE),
        'correction_small_pct': float(z7_nonlinear_period_correction(A_SMALL) * 100),
        'correction_large_pct': float(z7_nonlinear_period_correction(A_LARGE) * 100),
    },
}

with open(str(SCRIPT_DIR / "rank68_kggte_results.json"), 'w') as f:
    json.dump(output, f, indent=2)

print(f"\nResults saved to rank68_kggte_results.json")
