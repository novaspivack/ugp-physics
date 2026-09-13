#!/usr/bin/env python3
"""
cc_floor_orientation_arithmetic.py — Measurement-free arithmetic core of the
CC bracket orientation lemma (floor-half session).

Verifies, in 50-digit arithmetic with directed rational bounds:

  (A1) Inter-route ordering at N = 3 (claim F1):
       Omega_holo = 3*pi/14  <  Omega_census = (ln 2 / 3 pi) * log2(2000/3),
       with the closed-form margin
       margin = [14*ln(2000/3) - 9*pi^2] / (42*pi)
       and the equivalent GTE-atom inequality 14*ln(2000/3) > 9*pi^2,
       i.e. 2*|Z7|*ln(D^2*N_fam^3/N_gen) > N_gen^2*pi^2.
  (A2) Equivalence web: F1 <=> (G02 ratio = 14 ln(2000/3)/(9 pi^2) > 1)
       <=> (pure-DPP boundary N* = 3*sqrt(ratio) > 3).
  (A3) Rational certificate: explicit rationals r1 < ln(2000/3) and
       r2 > pi^2 with 14*r1 > 9*r2 — a finite, checkable witness of F1
       (the shape a Lean norm_num/interval proof takes).
  (A4) N-generalized F1: census(N) >= floor(N) iff N <= 3 under the
       canonical orbit-count ansatz AND under the fully generalized
       ansatz (the two R23 endpoints of the slot family).
  (A5) Measurement-audit: the symbol table of every input used above —
       none equals, approximates, or is calibrated to Planck 0.6889.
       (The Planck value appears in this script ONLY in the audit list
       as the excluded constant.)

Expected: A1–A5 all PASS; margin = 0.0167159889...; ratio = 1.02483...;
N* = 3.03702...; rational witness found at denominator <= 10^6.
"""
import json
import math
import signal
import sys
from fractions import Fraction

import mpmath as mp

TIMEOUT_SECONDS = 120


def _timeout(signum, frame):
    print(f"TIMEOUT {TIMEOUT_SECONDS}s — exiting")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

mp.mp.dps = 50

# GTE atoms (all structural; see audit table below)
N_GEN = 3
N_FAM = 5
D = 4            # = N_gen + 1, DPP (CatAL)
Z7 = 7           # |Z7| alphabet (CatAL)
ORBIT = Fraction(D**2 * N_FAM**3, N_GEN)   # 2000/3 (CatAL gauge_spectrum_total)

# ---- A1: inter-route ordering at N = 3 ---------------------------------------
ln_orbit = mp.log(mp.mpf(ORBIT.numerator) / ORBIT.denominator)
omega_census = ln_orbit / (3 * mp.pi)            # = (ln2/3pi)*log2(2000/3)
omega_holo = 3 * mp.pi / 14
margin = omega_census - omega_holo
margin_closed_form = (14 * ln_orbit - 9 * mp.pi**2) / (42 * mp.pi)
atom_lhs = 14 * ln_orbit          # 2*|Z7| * ln(orbit)
atom_rhs = 9 * mp.pi**2           # N_gen^2 * pi^2
a1 = {
    "omega_census": mp.nstr(omega_census, 30),
    "omega_holo_3pi_14": mp.nstr(omega_holo, 30),
    "margin": mp.nstr(margin, 30),
    "margin_matches_closed_form": abs(margin - margin_closed_form) < mp.mpf("1e-45"),
    "gte_atom_inequality_14ln_gt_9pisq": atom_lhs > atom_rhs,
    "atom_lhs_14_ln_2000_3": mp.nstr(atom_lhs, 30),
    "atom_rhs_9_pi_sq": mp.nstr(atom_rhs, 30),
    "F1_holds": omega_holo < omega_census,
}

# ---- A2: equivalence web ------------------------------------------------------
ratio_g02 = atom_lhs / atom_rhs                  # 14 ln(2000/3) / (9 pi^2)
n_star = 3 * mp.sqrt(ratio_g02)
a2 = {
    "g02_ratio": mp.nstr(ratio_g02, 30),
    "ratio_gt_1_iff_F1": (ratio_g02 > 1) == a1["F1_holds"],
    "pure_dpp_boundary_n_star": mp.nstr(n_star, 30),
    "n_star_gt_3_iff_F1": (n_star > 3) == a1["F1_holds"],
    "n_star_matches_R23_value_3.0370": abs(n_star - mp.mpf("3.037018")) < 1e-5,
}

# ---- A3: rational certificate -------------------------------------------------
# Directed rational bounds: r1 < ln(2000/3), r2 > pi^2, check 14*r1 > 9*r2.
r1 = Fraction(int(mp.floor(ln_orbit * 10**6)), 10**6)        # lower bound
r2 = Fraction(int(mp.ceil(mp.pi**2 * 10**6)), 10**6)         # upper bound
cert_lower_ok = mp.mpf(r1.numerator) / r1.denominator < ln_orbit
cert_upper_ok = mp.mpf(r2.numerator) / r2.denominator > mp.pi**2
cert_ineq = 14 * r1 > 9 * r2
a3 = {
    "r1_lower_ln_2000_3": str(r1),
    "r2_upper_pi_sq": str(r2),
    "r1_is_strict_lower_bound": bool(cert_lower_ok),
    "r2_is_strict_upper_bound": bool(cert_upper_ok),
    "finite_rational_witness_14r1_gt_9r2": bool(cert_ineq),
    "witness_slack": str(14 * r1 - 9 * r2),
}

# ---- A4: N-generalized F1 (both R23 ansatz endpoints) -------------------------
def census_canonical(n):
    return mp.log(mp.mpf(D**2 * N_FAM**3) / n) / (n * mp.pi)

def floor_canonical(n):
    return (mp.mpf(n) / Z7) * (mp.pi / 2)

def census_general(n):
    return mp.log(mp.mpf((n + 1)**2) * mp.mpf(N_FAM)**n / n) / (n * mp.pi)

def floor_general(n):
    return (mp.mpf(n) / (2 * n + 1)) * (mp.pi / 2)

a4_rows = []
for n in range(1, 11):
    a4_rows.append({
        "N": n,
        "canonical_oriented_nonempty": bool(census_canonical(n) >= floor_canonical(n)),
        "general_oriented_nonempty": bool(census_general(n) >= floor_general(n)),
    })
a4 = {
    "flip_at_4_canonical": [r["N"] for r in a4_rows if r["canonical_oriented_nonempty"]] == [1, 2, 3],
    "flip_at_4_general": [r["N"] for r in a4_rows if r["general_oriented_nonempty"]] == [1, 2, 3],
    "table": a4_rows,
}

# ---- A5: measurement audit ----------------------------------------------------
PLANCK_2018 = 0.6889   # appears ONLY here, as the excluded constant
inputs = {
    "N_gen=3": "GTE structural (PSC enumeration CatAL psc_enumeration_forces_ngen_3)",
    "N_fam=5": "Z5 ring structure (P01, CatAL)",
    "D=4": "DPP dimensional_protocol_principle_master (CatAL)",
    "|Z7|=7": "alphabet/group order (CatAL)",
    "orbit=2000/3": "gauge_spectrum_total (CatAL)",
    "tau=3/7": "ether proper-time rate tau_three_sevenths_from_ether (CatAD)",
    "ln2, pi": "mathematical constants",
    "Friedmann 1/3, 8pi/3": "critical-density normalization (derived GR, CatAD)",
}
audit = {
    "planck_used_in_any_formula": False,
    "census_minus_planck": mp.nstr(omega_census - PLANCK_2018, 10),
    "floor_minus_planck": mp.nstr(omega_holo - PLANCK_2018, 10),
    "note": ("neither route equals Planck; both formulas are functions of the "
             "structural inputs only; Planck enters a-posteriori comparison "
             "elsewhere, never this theorem"),
    "inputs": inputs,
}

results = {
    "A1_inter_route_ordering": a1,
    "A2_equivalence_web": a2,
    "A3_rational_certificate": a3,
    "A4_n_generalized_F1": a4,
    "A5_measurement_audit": audit,
    "ALL_PASS": bool(a1["F1_holds"] and a1["gte_atom_inequality_14ln_gt_9pisq"]
                     and a2["ratio_gt_1_iff_F1"] and a2["n_star_gt_3_iff_F1"]
                     and a3["finite_rational_witness_14r1_gt_9r2"]
                     and cert_lower_ok and cert_upper_ok
                     and a4["flip_at_4_canonical"] and a4["flip_at_4_general"]),
}

signal.alarm(0)
import os
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
          "cc_floor_orientation_arithmetic_results.json"), "w") as f:
    json.dump(results, f, indent=2)
print(json.dumps(results, indent=2))
