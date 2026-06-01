"""
SPEC_030_NIP — Nuclear IPT Reconciliation
Does the nuclear spin-orbit coupling ratio κ_emp/κ_min ≈ IPT = 1.13?

The P15 (Information Profit Principle) accounting reconciliation shows:
- Standard measurements map IPT=1.13 exactly to 1.0 in full-drain accounting
- The buffer zone [1.0, 1.13) companies fail more than above-1.13 companies

Nuclear analog question:
- What is κ_min (the minimum κ for ANY shell gap to appear in the Nilsson model)?
- Does κ_emp/κ_min ≈ 1.13?

If yes: the nuclear spin-orbit threshold is the IPT in the right normalization.

Also tests:
- First 2+ excitation energies: do magic nuclei have significantly higher E(2+)
  than near-magic (buffer zone) nuclei? This mirrors the P15 buffer-zone test.
"""

import math
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from magic_sieve_v2 import (
    build_nilsson_levels, energy_gaps_at_kappa, magic_numbers_from_kappa,
    KNOWN_MAGIC
)

IPT = 1.1309  # Information Profit Threshold from P15

# ─────────────────────────────────────────────────────────────────────────────
# APPROACH 1: Find κ_min (minimum κ for any gap > 0.3 ℏω₀ to appear)
# ─────────────────────────────────────────────────────────────────────────────

def find_kappa_min(levels, gap_threshold=0.3, max_cum=130):
    """
    Find the minimum κ at which the FIRST NON-HARMONIC-OSCILLATOR magic number
    (N=28) appears as a gap > threshold.

    At κ=0: HO gives 2,8,20,40,70 (but NOT 28,50,82,126).
    At κ_min: N=28 gap first exceeds threshold.
    
    This is the nuclear 'viability threshold' — the minimum spin-orbit coupling
    for the nuclear magic structure to emerge beyond HO.
    """
    # Scan κ from 0 upward looking specifically for N=28 gap
    for kappa_100 in range(1, 300):  # start at 0.001
        kappa = kappa_100 / 1000.0
        gaps = energy_gaps_at_kappa(levels, kappa, mu=0.35, max_cum=max_cum)
        if gaps.get(28, 0) > gap_threshold:
            return kappa
    return None


def kappa_threshold_analysis():
    """
    Test: κ_emp / κ_min ≈ IPT ?
    
    κ_min = minimum κ for shell structure to emerge
    κ_emp ≈ 0.050 (empirical Nilsson value)
    
    If the nuclear system satisfies the IPT viability condition:
    κ_emp / κ_min should equal or exceed IPT ≈ 1.13
    """
    print("=" * 65)
    print("SPEC_030: NUCLEAR IPT RECONCILIATION — κ_emp/κ_min TEST")
    print("=" * 65)
    print()

    levels = build_nilsson_levels(max_N=7)

    # Find κ_min
    kappa_min = find_kappa_min(levels, gap_threshold=0.3)
    kappa_emp = 0.050  # empirical Nilsson value

    print(f"κ_min (first gap > 0.3 ℏω₀): {kappa_min:.4f}")
    print(f"κ_emp (empirical Nilsson):    {kappa_emp:.4f}")
    print(f"Ratio κ_emp/κ_min:            {kappa_emp/kappa_min:.4f}")
    print(f"IPT (from P15):               {IPT:.4f}")
    print()

    ratio = kappa_emp / kappa_min
    pct_diff = abs(ratio - IPT) / IPT * 100

    if ratio > IPT:
        print(f"  κ_emp/κ_min = {ratio:.4f} > IPT = {IPT:.4f}  →  ABOVE IPT ✓")
    elif abs(ratio - IPT) < 0.05:
        print(f"  κ_emp/κ_min = {ratio:.4f} ≈ IPT = {IPT:.4f}  →  MATCHES IPT ({pct_diff:.1f}% diff) ✓")
    else:
        print(f"  κ_emp/κ_min = {ratio:.4f} ≠ IPT = {IPT:.4f}  →  DIFFERS BY {pct_diff:.1f}%")

    # What magic numbers does κ_min give?
    magic_at_min = magic_numbers_from_kappa(levels, kappa_min, mu=0.35,
                                             gap_threshold=0.3, max_cum=130)
    magic_at_emp = magic_numbers_from_kappa(levels, kappa_emp, mu=0.35,
                                             gap_threshold=0.3, max_cum=130)

    print()
    print(f"Magic numbers at κ_min={kappa_min:.3f}: {magic_at_min}")
    print(f"Magic numbers at κ_emp={kappa_emp:.3f}: {magic_at_emp}")
    print(f"Known magic numbers:          {KNOWN_MAGIC}")

    return kappa_min, kappa_emp, ratio


# ─────────────────────────────────────────────────────────────────────────────
# APPROACH 2: Scan κ_min for each SPECIFIC magic number
# What is the minimum κ needed for each magic number's gap to exceed threshold?
# ─────────────────────────────────────────────────────────────────────────────

def per_magic_kappa_min(levels, magic_nums, gap_threshold=0.3):
    """
    For each magic number, find the minimum κ that opens a gap there.
    Then check if κ_emp/κ_min(N) ≈ IPT for each N.
    """
    print()
    print("PER-MAGIC-NUMBER κ_min ANALYSIS:")
    print(f"  {'N':>4}  {'κ_min':>7}  {'κ_emp/κ_min':>12}  {'vs IPT':>10}  Notes")
    print("  " + "─" * 55)

    results = {}
    kappa_emp = 0.050

    for N in magic_nums:
        if N > 130:
            continue
        # Find minimum κ that opens gap at this N
        kappa_n_min = None
        for kappa_100 in range(0, 300):
            kappa = kappa_100 / 1000.0
            gaps = energy_gaps_at_kappa(levels, kappa, mu=0.35, max_cum=N+5)
            if gaps.get(N, 0) > gap_threshold:
                kappa_n_min = kappa
                break

        if kappa_n_min is None or kappa_n_min == 0.0:
            print(f"  {N:>4}  {'N/A':>7}  {'—':>12}  {'—':>10}  (HO magic, no κ needed)")
            continue

        ratio = kappa_emp / kappa_n_min
        pct = (ratio - IPT) / IPT * 100
        ipt_status = f"+{pct:.1f}%" if ratio > IPT else f"{pct:.1f}%"

        marker = "✓" if abs(ratio - IPT) < 0.15 else ("HIGH" if ratio > IPT + 0.15 else "LOW")
        print(f"  {N:>4}  {kappa_n_min:>7.4f}  {ratio:>12.4f}  {ipt_status:>10}  {marker}")

        results[N] = {'kappa_min': kappa_n_min, 'ratio': ratio}

    return results


# ─────────────────────────────────────────────────────────────────────────────
# APPROACH 3: Buffer-zone test (mirror of P15 economic buffer-zone test)
# Published data on first 2+ excitation energies E(2+) for nuclei
# near vs. at magic numbers
# ─────────────────────────────────────────────────────────────────────────────

# Published E(2+) energies (MeV) from NNDC / literature
# For doubly-magic nuclei and near-magic nuclei (N close to magic)
# Source: ENSDF database, standard nuclear structure compilations

E2_DATA = {
    # (Z, N, E2+_MeV, notes)
    # At magic N=20
    (20, 20, 3.737, "40Ca — doubly magic, N=Z=20"),
    (20, 22, 1.524, "42Ca — N=22, just above magic-20"),
    (20, 24, 1.157, "44Ca — N=24, buffer zone"),
    (20, 18, 1.944, "38Ca — N=18, just below magic-20"),
    # At magic N=28
    (20, 28, 3.832, "48Ca — doubly magic-28 neutron"),
    (20, 26, 1.283, "46Ca — N=26, buffer zone [20,28)"),
    (28, 28, 3.263, "56Ni — doubly magic Z=N=28"),
    (28, 26, 1.450, "54Ni — N=26, buffer zone"),
    # At magic N=50
    (50, 50, 4.041, "100Sn — doubly magic, Z=N=50"),
    (40, 50, 1.761, "90Zr — N=50, Z=40 (below magic-Z)"),
    (40, 48, 0.919, "88Zr — N=48, buffer zone [28,50)"),
    (40, 46, 0.589, "86Zr — N=46, further below"),
    # At magic N=82
    (50, 82, 1.258, "132Sn — doubly magic Z=50,N=82"),
    (50, 80, 0.725, "130Sn — N=80, buffer zone [50,82)"),
    (50, 78, 0.587, "128Sn — N=78, further below"),
}

def buffer_zone_test():
    """
    Test: Do nuclei with N in buffer zone [N_magic - δ, N_magic) 
    have LOWER E(2+) than exactly-magic nuclei?
    
    This mirrors the P15 test: companies in [1.0, 1.13) fail more than above-1.13.
    If the analogy holds, magic nuclei should have systematically higher E(2+)
    than near-magic ones.
    """
    print()
    print("BUFFER-ZONE TEST (mirror of P15 economic buffer-zone test):")
    print("  Prediction: E(2+) at magic N > E(2+) in buffer zone [magic-4, magic)")
    print()

    magic_set = set(KNOWN_MAGIC)

    exactly_magic = [(z, n, e2, note) for z, n, e2, note in E2_DATA
                     if n in magic_set]
    buffer_zone   = [(z, n, e2, note) for z, n, e2, note in E2_DATA
                     if n not in magic_set]

    e2_magic  = [e2 for _, _, e2, _ in exactly_magic]
    e2_buffer = [e2 for _, _, e2, _ in buffer_zone]

    mean_magic  = sum(e2_magic)  / len(e2_magic)
    mean_buffer = sum(e2_buffer) / len(e2_buffer)

    print(f"  At-magic nuclei (n={len(e2_magic)}):  mean E(2+) = {mean_magic:.3f} MeV")
    for z, n, e2, note in sorted(exactly_magic, key=lambda x: x[2], reverse=True):
        print(f"    N={n:3d}, Z={z:3d}: E(2+)={e2:.3f} MeV  [{note}]")

    print()
    print(f"  Buffer-zone nuclei (n={len(e2_buffer)}):  mean E(2+) = {mean_buffer:.3f} MeV")
    for z, n, e2, note in sorted(buffer_zone, key=lambda x: x[2], reverse=True):
        print(f"    N={n:3d}, Z={z:3d}: E(2+)={e2:.3f} MeV  [{note}]")

    print()
    ratio_e2 = mean_magic / mean_buffer
    print(f"  Ratio E(2+)[magic] / E(2+)[buffer] = {ratio_e2:.4f}")
    print(f"  IPT = {IPT:.4f}")
    print()

    if ratio_e2 > 1.0:
        pct_diff = abs(ratio_e2 - IPT) / IPT * 100
        print(f"  Magic > Buffer: YES ✓ ({ratio_e2:.4f} > 1.0)")
        print(f"  Ratio vs IPT: {pct_diff:.1f}% difference")
        if pct_diff < 20:
            print(f"  *** NOTABLE: E(2+) ratio ({ratio_e2:.4f}) within 20% of IPT ({IPT:.4f}) ***")
    else:
        print(f"  Magic > Buffer: NO ✗ (ratio = {ratio_e2:.4f})")

    return ratio_e2


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    levels = build_nilsson_levels(max_N=7)

    # Approach 1: κ_emp/κ_min ≈ IPT?
    kappa_min, kappa_emp, ratio = kappa_threshold_analysis()

    # Approach 2: Per-magic-number κ_min
    per_results = per_magic_kappa_min(levels, KNOWN_MAGIC)

    # Approach 3: Buffer-zone E(2+) test
    e2_ratio = buffer_zone_test()

    # Summary
    print()
    print("=" * 65)
    print("SUMMARY — NUCLEAR IPT RECONCILIATION")
    print("=" * 65)
    print()
    print(f"Approach 1 (global κ_emp/κ_min):")
    print(f"  κ_min = {kappa_min:.4f}, κ_emp = {kappa_emp:.4f}")
    print(f"  Ratio = {ratio:.4f}  vs  IPT = {IPT:.4f}  ({abs(ratio-IPT)/IPT*100:.1f}% diff)")
    print()
    print(f"Approach 3 (E(2+) buffer-zone test):")
    print(f"  E(2+)[magic] / E(2+)[buffer] = {e2_ratio:.4f}  vs  IPT = {IPT:.4f}")
    print()
    print("P15 accounting reconciliation note:")
    print("  In P15, standard accounting maps IPT=1.13 → 1.0 in full-drain accounting.")
    print("  The correct nuclear test may need a specific normalization:")
    print("  'structural drain' = κ_min, 'actual generation' = κ_emp")
    print("  Then κ_emp/κ_min represents the nuclear viability ratio.")
    print()
    print("OPEN QUESTION: What is the correct 'drain' in the nuclear context?")
    print("  Option A: κ_min = minimum κ for ANY gap (tested above)")
    print("  Option B: κ_threshold = κ at which the specific magic N first appears")
    print("  Option C: the binding energy ratio BE(magic)/BE(smooth) [earlier attempt]")
