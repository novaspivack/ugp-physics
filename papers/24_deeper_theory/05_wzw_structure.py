"""
05_wzw_structure.py
-------------------
WZW Structure Summary

Summarizes the relationship between UGP and the WZW theory
SU(2)_8 x SU(3)_3 x SU(2)_10, including:
- Level assignments and their UGP meanings
- Total central charge c = 89/10 = F_11/n_ridge
- Total primaries = Nc^2 * n_ridge * (n_ridge+1)
- Modular weight denominator = 240 = Q(zeta_240) index
- T4 falsification summary

The WZW connections are ALGEBRAIC SHADOWS of Q(zeta_240),
not a parent theory generating UGP.
"""

import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from ugp_core import (
    WZW_FACTORS, C_TOTAL, TOTAL_PRIMARIES,
    Nc, delta, n_ridge, strand_count, FIB,
    G1_SQ, G2_SQ, G3_SQ
)
from fractions import Fraction
import math

os.makedirs('results', exist_ok=True)

def run():
    lines = []
    def p(s=''):
        print(s)
        lines.append(s)

    p("="*65)
    p("TEST 5: WZW STRUCTURE SUMMARY")
    p("="*65)
    p()

    # ── WZW factor table ─────────────────────────────────────────────────────
    p("WZW FACTOR ASSIGNMENTS:")
    p("-"*50)
    p()
    p(f"  {'Factor':<12}  {'Level k':>8}  {'Level meaning':<30}  {'c':>8}  {'Primaries':>10}")
    p("  " + "-"*75)

    for f in WZW_FACTORS:
        p(f"  {f['name']:<12}  {f['level']:>8}  {f['meaning']:<30}  "
          f"{str(f['c']):>8}  {f['primaries']:>10}")

    p()
    p(f"  Level assignments:")
    p(f"    k(SU(2)_8)  = 8  = Nc^2 - 1 = {Nc**2 - 1}  [dim of adjoint of SU(Nc)]")
    p(f"    k(SU(3)_3)  = 3  = Nc = {Nc}              [diagonal level = colour rank]")
    p(f"    k(SU(2)_10) = 10 = n_ridge = {n_ridge}       [ridge level]")
    p()

    # ── Central charge ───────────────────────────────────────────────────────
    p("TOTAL CENTRAL CHARGE:")
    p("-"*50)
    p()
    p(f"  c_total = 12/5 + 4 + 5/2")
    p(f"          = {C_TOTAL}")
    p(f"          = {float(C_TOTAL):.6f}")
    p()
    p(f"  F_11 = {FIB[10]}  (11th Fibonacci number)")
    p(f"  c_total * n_ridge = {C_TOTAL} * {n_ridge} = {C_TOTAL * n_ridge}")
    p()

    if C_TOTAL * n_ridge == FIB[10]:
        p(f"  c_total * n_ridge = F_11 = {FIB[10]}  [EXACT MATCH ✓]")
    else:
        p(f"  c_total * n_ridge = {float(C_TOTAL * n_ridge):.4f}  [no exact match]")

    p()
    p(f"  Interpretation: The total central charge of the WZW theory")
    p(f"  satisfies c_total = F_(n_ridge+1) / n_ridge")
    p(f"  where F_(n_ridge+1) = F_11 = 89 is the (n_ridge+1)-th Fibonacci number.")
    p()

    # ── Primaries ────────────────────────────────────────────────────────────
    p("TOTAL PRIMARIES:")
    p("-"*50)
    p()
    p(f"  9 * 10 * 11 = {TOTAL_PRIMARIES}")
    p(f"  = Nc^2 * n_ridge * (n_ridge+1)")
    p(f"  = {Nc**2} * {n_ridge} * {n_ridge+1}")
    p()
    p(f"  Sum: 9 + 10 + 11 = {9+10+11}")
    p(f"  = 2 * 3 * 5  [UGP field primes!]")
    p()

    # ── Modular weight ───────────────────────────────────────────────────────
    p("MODULAR WEIGHT DENOMINATOR:")
    p("-"*50)
    p()
    p(f"  c_total = 89/10")
    p(f"  c_total/24 = 89/240")
    p(f"  Denominator: 240 = 2^4 * 3 * 5")
    p()
    p(f"  Q(zeta_240) has phi(240) = 64 = 2^6")
    p(f"  240 = same prime structure as the modular weight denominator")
    p()
    p(f"  q-expansion denominator: 720 = 8 * 9 * 10")
    p(f"  = (Nc^2-1) * Nc^2 * n_ridge")
    p(f"  = {Nc**2-1} * {Nc**2} * {n_ridge}")
    p()

    # ── Angle matches ────────────────────────────────────────────────────────
    p("WZW MODULAR ANGLES vs UGP CONSTANTS:")
    p("-"*50)
    p()
    p("  SU(2)_k modular angle = pi/(k+2)")
    p()
    p(f"  {'Factor':<12}  {'k':>4}  {'Angle':>12}  {'UGP match'}")
    p("  " + "-"*55)

    angle_data = [
        ('SU(2)_8',  8,  math.pi/10, 'pi/10 = kernel k_gen angle'),
        ('SU(3)_3',  3,  math.pi/6,  'pi/6  = A2 Weyl chamber (Lean-proved)'),
        ('SU(2)_10', 10, math.pi/12, 'pi/12 = TT cascade angle'),
    ]

    for name, k, angle, match in angle_data:
        p(f"  {name:<12}  {k:>4}  pi/{int(round(math.pi/angle)):>2} = {angle:.6f}  {match}")

    p()

    # ── T4 falsification ─────────────────────────────────────────────────────
    p("T4 FALSIFICATION:")
    p("-"*50)
    p()
    p("  Test: Do Fourier coefficients of Z(tau) encode bare gauge couplings?")
    p()
    p("  Method: Computed q-expansion of Z(tau) for SU(2)_8 x SU(3)_3 x SU(2)_10")
    p("  using WZW characters. Checked all ratios of low-order coefficients")
    p("  against {16/125, 2329/5400, 41075281/27648000}.")
    p()
    p("  Result: NO MATCH within 2%.")
    p()
    p("  Finding 1: q-expansion denominator is 720 (not integer powers of q)")
    p("  Finding 2: Vacuum coefficient a_0 = 1 (consistent)")
    p("  Finding 3: No ratio of Fourier coefficients matches g_i^2")
    p()
    p("  CONCLUSION: T4 FALSIFIED ✗")
    p("  The WZW modular invariant does NOT encode bare gauge couplings.")
    p()

    # ── What the WZW connections mean ────────────────────────────────────────
    p("WHAT THE WZW CONNECTIONS ACTUALLY MEAN:")
    p("-"*50)
    p()
    p("  The WZW angles (pi/10, pi/6, pi/12) and central charge (89/10)")
    p("  are ALGEBRAIC SHADOWS of the same Q(zeta_240) substrate that")
    p("  hosts all UGP constants.")
    p()
    p("  They are NOT a parent theory generating UGP.")
    p("  The gauge couplings flow through cascade arithmetic on the")
    p("  ridge-selected seed (1, 73, 823), not through CFT state counts.")
    p()
    p("  The WZW theory and UGP share the same algebraic substrate")
    p("  Q(zeta_240) but are different mathematical objects within it.")
    p()
    p("  Analogy: Two different functions can both be expressible in")
    p("  terms of pi and sqrt(2) without one being derived from the other.")

    with open('results/05_wzw_structure.txt', 'w') as f:
        f.write('\n'.join(lines))
    print("\n[Saved to results/05_wzw_structure.txt]")

if __name__ == '__main__':
    run()
