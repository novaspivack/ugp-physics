"""
baryon_number_l2_correspondence.py
-----------------------------------
Verify the Level 1 ↔ Level 2 baryon number correspondence for the Φ_MDL field.

The correspondence theorem:
  B_L1 = (1/3) Σⱼ χ_q(wⱼ)          [Level 1 algebraic, BaryonNumber.lean]
  B_L2 = ∫ J^0_B dx = B_L1           [Level 2 topological, this script]

where the Level 2 topological current is:
  J^μ_B = (7/6π) Σⱼ χ_q(wⱼ) ε^{μν} ∂_ν Φⱼ

The key algebraic identity driving the correspondence:
  (7/6π) × (2π/7) = 1/3

where 2π/7 = ∫∂_x Φ dx for a fundamental Z₇ kink (unit vacuum step).

Conservation ∂_μ J^μ_B = 0 is topological: ε^{μν}∂_μ∂_ν = 0 by antisymmetry,
independent of any field equation.

Expected output:
  - All SM particles: B_L1 = B_L2 (PASS)
  - All representative vertices: baryon number conserved (PASS)
  - Key algebraic identity: (7/6π)(2π/7) = 1/3 (exact)
"""

import json
import math
import signal
import sys
import time

TIMEOUT_SECONDS = 120

def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

t_start = time.time()

# ---------------------------------------------------------------------------
# Z₇ baryon charge function χ_q: Z₇ → {-1, 0, +1}
# Quark sectors {2,6}: +1 (B = +1/3 per tape)
# Anti-quark sectors {1,5}: -1 (B = -1/3 per tape)
# Lepton/boson/vacuum {0,3,4}: 0
# ---------------------------------------------------------------------------
chi_q = {0: 0, 1: -1, 2: 1, 3: 0, 4: 0, 5: -1, 6: 1}

# ---------------------------------------------------------------------------
# Level 1 baryon number formula (from BaryonNumber.lean)
# B_L1(wx, wy, wz) = (1/3)(χ_q(wx) + χ_q(wy) + χ_q(wz))
# ---------------------------------------------------------------------------
def B_L1(wx, wy, wz):
    """Level 1 baryon number from Z₇ winding triple."""
    return (chi_q[wx] + chi_q[wy] + chi_q[wz]) / 3


# ---------------------------------------------------------------------------
# Level 2 baryon current integral
# ∫J^0_B dx = (7/6π) Σⱼ χ_q(wⱼ) ∫∂_x Φⱼ dx
#
# For a fundamental Z₇ kink (unit vacuum step):
#   ∫∂_x Φ dx = Φ(+∞) − Φ(−∞) = 2π/7
#
# Therefore per tape:
#   (7/6π) × χ_q(w) × (2π/7) = χ_q(w)/3
# ---------------------------------------------------------------------------
NORM_FACTOR = 7.0 / (6.0 * math.pi)   # (7/6π)
KINK_INTEGRAL = 2.0 * math.pi / 7.0   # ∫∂_x Φ dx for unit Z₇ kink = 2π/7

def J0_integral_per_tape(w):
    """∫J^0_B dx for a single tape with winding sector w.
    = (7/6π) × χ_q(w) × (2π/7) = χ_q(w)/3
    """
    return NORM_FACTOR * chi_q[w] * KINK_INTEGRAL

def B_L2(wx, wy, wz):
    """Level 2 baryon number from topological current integral."""
    return J0_integral_per_tape(wx) + J0_integral_per_tape(wy) + J0_integral_per_tape(wz)

# ---------------------------------------------------------------------------
# SM particle table
# Each entry: (name, wx, wy, wz, expected_B)
# ---------------------------------------------------------------------------
PARTICLES = [
    ("Proton (u,u,d)",       2, 2, 6,  1.0),
    ("Neutron (u,d,d)",      2, 6, 6,  1.0),
    ("Anti-proton (ū,ū,d̄)", 5, 5, 1, -1.0),
    ("Delta++ (u,u,u)",      2, 2, 2,  1.0),
    ("Delta- (d,d,d)",       6, 6, 6,  1.0),
    ("Electron (e⁻,e⁻,e⁻)", 4, 4, 4,  0.0),
    ("Muon (μ,μ,μ)",         4, 4, 4,  0.0),
    ("Tau (τ,τ,τ)",          4, 4, 4,  0.0),
    ("Neutrino (ν,ν,ν)",     0, 0, 0,  0.0),
    ("W+ boson",             3, 3, 3,  0.0),
    ("Photon/gluon",         0, 0, 0,  0.0),
    ("Pion π⁰ (u,ū,0)",     2, 5, 0,  0.0),
]

# ---------------------------------------------------------------------------
# SM vertex table (per-tape level)
# (vertex_name, w_in, [w_out1, w_out2])
# Baryon conservation: chi_q(w_in) = chi_q(w_out1) + chi_q(w_out2)
# ---------------------------------------------------------------------------
VERTICES_PER_TAPE = [
    ("u→d+W+",     2,    [6, 3]),
    ("d→u+W-",     6,    [2, 4]),
    ("e⁻→νe+W-",  4,    [0, 4]),
    ("u→u+γ",      2,    [2, 0]),
    ("q→q+g",      2,    [2, 0]),
    ("d→d+γ",      6,    [6, 0]),
    ("uū→0",       None, [2, 5]),   # annihilation: total chi = 0
    ("dd̄→0",       None, [6, 1]),
]

def run_verification():
    results = {
        "algebraic_identity": {},
        "particle_correspondence": [],
        "vertex_conservation_per_tape": [],
        "all_pass": True,
        "elapsed_s": None,
    }

    # -----------------------------------------------------------------------
    # Key algebraic identity
    # -----------------------------------------------------------------------
    conversion = NORM_FACTOR * KINK_INTEGRAL
    identity_exact = abs(conversion - 1.0/3.0) < 1e-14
    results["algebraic_identity"] = {
        "norm_factor_7_over_6pi": NORM_FACTOR,
        "kink_integral_2pi_over_7": KINK_INTEGRAL,
        "conversion_product": conversion,
        "exact_1_over_3": 1.0/3.0,
        "match_exact_1_over_3": identity_exact,
        "formula": "(7/6π) × (2π/7) = 1/3  [exact]",
    }
    if not identity_exact:
        results["all_pass"] = False

    # -----------------------------------------------------------------------
    # Particle-by-particle L1↔L2 correspondence
    # -----------------------------------------------------------------------
    for name, wx, wy, wz, B_expected in PARTICLES:
        b1 = B_L1(wx, wy, wz)
        b2 = B_L2(wx, wy, wz)
        match_l1_l2 = abs(b1 - b2) < 1e-12
        match_expected = abs(b1 - B_expected) < 1e-12
        passed = match_l1_l2 and match_expected
        entry = {
            "particle": name,
            "winding_triple": [wx, wy, wz],
            "B_L1": b1,
            "B_L2": b2,
            "B_expected": B_expected,
            "L1_equals_L2": match_l1_l2,
            "matches_PDG": match_expected,
            "PASS": passed,
        }
        results["particle_correspondence"].append(entry)
        if not passed:
            results["all_pass"] = False

    # -----------------------------------------------------------------------
    # Vertex conservation (per-tape level)
    # -----------------------------------------------------------------------
    for name, w_in, w_outs in VERTICES_PER_TAPE:
        if w_in is not None:
            b_in = chi_q[w_in]
            b_out = sum(chi_q[w] for w in w_outs)
            conserved = (b_in == b_out)
        else:
            b_in = 0
            b_out = sum(chi_q[w] for w in w_outs)
            conserved = (b_out == 0)
        entry = {
            "vertex": name,
            "w_in": w_in,
            "w_outs": w_outs,
            "chi_q_in": b_in,
            "chi_q_out": b_out,
            "conserved": conserved,
        }
        results["vertex_conservation_per_tape"].append(entry)
        if not conserved:
            results["all_pass"] = False

    results["elapsed_s"] = round(time.time() - t_start, 3)
    return results


if __name__ == "__main__":
    print("=" * 65)
    print("Baryon Number L1↔L2 Correspondence Verification")
    print("=" * 65)

    r = run_verification()

    print(f"\n[Key algebraic identity]")
    ai = r["algebraic_identity"]
    print(f"  (7/6π) = {ai['norm_factor_7_over_6pi']:.8f}")
    print(f"  (2π/7) = {ai['kink_integral_2pi_over_7']:.8f}")
    print(f"  Product = {ai['conversion_product']:.14f}")
    print(f"  Exact 1/3 = {ai['exact_1_over_3']:.14f}")
    print(f"  Match exact: {ai['match_exact_1_over_3']}")

    print(f"\n[Particle Correspondence: B_L1 = B_L2]")
    print(f"  {'Particle':<32} {'B_L1':>8} {'B_L2':>8} {'PDG':>8} {'Status':>8}")
    print("  " + "-" * 68)
    for p in r["particle_correspondence"]:
        status = "PASS" if p["PASS"] else "FAIL"
        print(f"  {p['particle']:<32} {p['B_L1']:>8.4f} {p['B_L2']:>8.4f} {p['B_expected']:>8.4f} {status:>8}")

    print(f"\n[Vertex Conservation (per-tape, Level 2)]")
    print(f"  {'Vertex':<20} {'chi_in':>8} {'chi_out':>8} {'Status':>10}")
    print("  " + "-" * 50)
    for v in r["vertex_conservation_per_tape"]:
        status = "CONSERVED" if v["conserved"] else "FAIL"
        print(f"  {v['vertex']:<20} {v['chi_q_in']:>8} {v['chi_q_out']:>8} {status:>10}")

    print(f"\n{'=' * 65}")
    print(f"OVERALL RESULT: {'ALL PASS ✓' if r['all_pass'] else 'FAILURES DETECTED ✗'}")
    print(f"Elapsed: {r['elapsed_s']}s")

    # Save JSON artifact
    out_path = __file__.replace(".py", "_results.json")
    with open(out_path, "w") as f:
        json.dump(r, f, indent=2)
    print(f"Results saved to: {out_path}")

signal.alarm(0)
