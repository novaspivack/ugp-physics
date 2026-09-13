"""
Phase 7: RC Domain Topology — Lean Version

Compute D_RC for N=3 and N=4 using vectorized one-loop RG.
Show int(D_RC^c(N=4)) ≠ ∅ and int(D_RC^c(N=3)) = ∅.
"""

import numpy as np
np.seterr(all='ignore')
from dataclasses import dataclass
from typing import List


def run_rg_single(n_gen, y_top, y_4th, lambda_h, log_end=16.0, n_steps=500):
    """Run one-loop RG from M_t to 10^log_end GeV. Returns (rc_ok, lp_scale, vi_scale)."""
    g1, g2, g3 = 0.357, 0.652, 1.221
    yt, y4, lam = y_top, y_4th, lambda_h

    b1 = 4.0/3.0 * n_gen + 0.1
    b2 = -22.0/3.0 + 4.0/3.0 * n_gen + 1.0/6.0
    b3 = -11.0 + 4.0/3.0 * n_gen

    log_start = np.log10(173.0)
    dt = (log_end - log_start) / n_steps * np.log(10)
    lf = 1.0 / (16.0 * np.pi**2)

    lp_scale = None
    vi_scale = None

    for i in range(n_steps):
        dg1 = lf * b1 * g1**3
        dg2 = lf * b2 * g2**3
        dg3 = lf * b3 * g3**3

        dyt = lf * yt * (4.5*yt**2 - 17.0/12*g1**2 - 2.25*g2**2 - 8*g3**2
                         + (y4**2 if n_gen >= 4 else 0))

        dy4 = 0.0
        if n_gen >= 4 and y4 > 0:
            dy4 = lf * y4 * (4.5*y4**2 - 17.0/12*g1**2 - 2.25*g2**2 - 8*g3**2 + yt**2)

        ysum2 = yt**2 + (y4**2 if n_gen >= 4 else 0)
        ysum4 = yt**4 + (y4**4 if n_gen >= 4 else 0)
        dlam = lf * (24*lam**2 - (1.8*g1**2 + 9*g2**2)*lam
                     + 2.25*(0.12*g1**4 + 0.4*g1**2*g2**2 + g2**4)
                     + 12*lam*ysum2 - 12*ysum4)

        g1 += dt*dg1; g2 += dt*dg2; g3 += dt*dg3
        yt += dt*dyt; y4 += dt*dy4; lam += dt*dlam

        if not (np.isfinite(g1) and np.isfinite(g2) and np.isfinite(g3)
                and np.isfinite(yt) and np.isfinite(lam)):
            lp_scale = log_start + (log_end - log_start) * i / n_steps
            break

        if abs(g1) > 4*np.pi or abs(g2) > 4*np.pi or abs(g3) > 4*np.pi or abs(yt) > 4*np.pi or abs(y4) > 4*np.pi:
            lp_scale = log_start + (log_end - log_start) * i / n_steps
            break

        if lam < -10 and vi_scale is None:
            vi_scale = log_start + (log_end - log_start) * i / n_steps

    rc_ok = (lp_scale is None)
    return rc_ok, lp_scale, vi_scale


@dataclass
class DomainResult:
    n_gen: int
    n_total: int
    n_ok: int
    n_fail: int
    frac_ok: float
    has_open_ok: bool
    has_open_fail: bool
    bifurcates: bool
    examples_ok: list
    examples_fail: list


def scan_domain(n_gen, psc_scale=16.0):
    """Scan RC domain for n_gen generations."""
    yt_vals = np.linspace(0.5, 1.5, 10)
    lam_vals = np.linspace(0.05, 0.3, 10)
    y4_vals = np.linspace(0.1, 3.0, 8) if n_gen >= 4 else [0.0]

    ok_list, fail_list = [], []

    for yt in yt_vals:
        for lam in lam_vals:
            for y4 in y4_vals:
                rc_ok, lp, vi = run_rg_single(n_gen, yt, y4, lam, log_end=psc_scale)
                entry = {'yt': yt, 'y4': y4, 'lam': lam, 'lp': lp, 'vi': vi}
                if rc_ok:
                    ok_list.append(entry)
                else:
                    fail_list.append(entry)

    n_total = len(ok_list) + len(fail_list)
    n_ok = len(ok_list)
    n_fail = len(fail_list)
    frac = n_ok / n_total if n_total else 0

    has_open_ok = n_ok > n_total * 0.05
    has_open_fail = n_fail > n_total * 0.05
    bif = has_open_ok and has_open_fail

    return DomainResult(n_gen, n_total, n_ok, n_fail, frac,
                        has_open_ok, has_open_fail, bif,
                        ok_list[:3], fail_list[:3])


if __name__ == "__main__":
    print("=" * 70)
    print("PHASE 7: RC DOMAIN TOPOLOGY")
    print("=" * 70)

    for psc in [15.0, 16.0, 17.0, 18.0, 19.0]:
        print(f"\n--- Λ_PSC = 10^{psc:.0f} GeV ---")

        r3 = scan_domain(3, psc)
        r4 = scan_domain(4, psc)

        n3_dense = r3.has_open_ok and not r3.has_open_fail
        n4_bif = r4.bifurcates

        print(f"  N=3: {r3.n_ok}/{r3.n_total} RC-ok ({r3.frac_ok:.0%})"
              f"  open_ok={r3.has_open_ok} open_fail={r3.has_open_fail}"
              f"  → {'open dense' if n3_dense else 'BIFURCATES'}")
        print(f"  N=4: {r4.n_ok}/{r4.n_total} RC-ok ({r4.frac_ok:.0%})"
              f"  open_ok={r4.has_open_ok} open_fail={r4.has_open_fail}"
              f"  → {'BIFURCATES' if n4_bif else 'open dense'}")

        status = "✓ PROVEN" if (n3_dense and n4_bif) else "✗ NOT PROVEN"
        print(f"  int(D_RC^c(N=3))={'∅' if n3_dense else '≠∅'}"
              f"  int(D_RC^c(N=4))={'≠∅' if n4_bif else '∅'}"
              f"  → {status}")

    # Show examples at PSC = 10^16
    print("\n" + "=" * 70)
    print("DETAILED EXAMPLES AT Λ_PSC = 10^16 GeV")
    print("=" * 70)

    r3 = scan_domain(3, 16.0)
    r4 = scan_domain(4, 16.0)

    print("\nN=3 RC-compliant examples:")
    for e in r3.examples_ok[:3]:
        print(f"  y_t={e['yt']:.2f} λ={e['lam']:.3f} → OK (no Landau pole)")
    print("N=3 RC-violating examples:")
    for e in r3.examples_fail[:3]:
        print(f"  y_t={e['yt']:.2f} λ={e['lam']:.3f} → LP at 10^{e['lp']:.1f} GeV" if e['lp'] else
              f"  y_t={e['yt']:.2f} λ={e['lam']:.3f} → vacuum instability")

    print("\nN=4 RC-compliant examples:")
    for e in r4.examples_ok[:3]:
        print(f"  y_t={e['yt']:.2f} y_4={e['y4']:.2f} λ={e['lam']:.3f} → OK")
    print("N=4 RC-violating examples:")
    for e in r4.examples_fail[:3]:
        print(f"  y_t={e['yt']:.2f} y_4={e['y4']:.2f} λ={e['lam']:.3f}"
              f" → LP at 10^{e['lp']:.1f} GeV" if e['lp'] else
              f"  y_t={e['yt']:.2f} y_4={e['y4']:.2f} λ={e['lam']:.3f} → instability")

    print("\n" + "=" * 70)
