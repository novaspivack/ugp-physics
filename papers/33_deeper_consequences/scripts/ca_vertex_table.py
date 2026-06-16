"""CA Vertex Table — Complete Classification of f_MDL Neighborhoods

Enumerates all 343 neighborhoods (l,c,r) in Z₇³, computes fmdl(l,c,r) for each,
classifies inputs and outputs by SM particle assignment, and cross-checks against
P22's vertex structure.

Role-based name: ca_vertex_table.py
"""

from itertools import product

# ──────────────────────────────────────────────────────────────────────────────
# fmdl definition (MDL-minimal Z₇ CA function, 18 fixed + 325 free=0)
# Matches CUP3DUniqueness.lean exactly.
# ──────────────────────────────────────────────────────────────────────────────

# 10 orbit neighborhood constraints (canonical orbit ordering)
ORBIT_FIXED = {
    (1, 1, 5): 2,
    (1, 5, 2): 5,
    (5, 2, 2): 2,
    (2, 2, 1): 0,
    (2, 1, 1): 2,
    (2, 2, 5): 5,
    (2, 5, 2): 6,
    (5, 2, 0): 5,
    (2, 0, 2): 3,
    (0, 2, 2): 5,
}

# 8 Rule 110 binary sublayer constraints (binary: {0,1}³ → Rule 110 output)
RULE110_FIXED = {
    (0, 0, 0): 0,
    (0, 0, 1): 1,
    (0, 1, 0): 1,
    (0, 1, 1): 1,
    (1, 0, 0): 0,
    (1, 0, 1): 1,
    (1, 1, 0): 1,
    (1, 1, 1): 0,
}

ALL_FIXED = {**ORBIT_FIXED, **RULE110_FIXED}


def fmdl(l: int, c: int, r: int) -> int:
    """MDL-minimal Z₇ CA function. Returns fmdl(l, c, r) ∈ {0,...,6}."""
    key = (l, c, r)
    return ALL_FIXED.get(key, 0)


# ──────────────────────────────────────────────────────────────────────────────
# SM Z₇ particle assignments (P28 §5–§6, Z7ChargeConjugation.lean §5)
# ──────────────────────────────────────────────────────────────────────────────

SM_LABELS = {
    0: "vacuum/ν",
    1: "anti-d",
    2: "u",
    3: "W⁺",
    4: "W⁻/e⁻",
    5: "anti-u",
    6: "d",
}

# P22 winding numbers W in ℤ (from P22 §"Charge and winding")
P22_WINDING = {
    0:  0,   # vacuum/ν: W=0
    1: +1,   # anti-d: W = +1 (= -W(d) = +1)
    2: +2,   # u-quark: W = +2
    3: +3,   # W⁺: W = +3
    4: -3,   # W⁻/e⁻: W = -3 (= -3 mod 7 = 4, but integer W = -3)
    5: -2,   # anti-u: W = -2 (= -W(u) = -2)
    6: -1,   # d-quark: W = -1
}

# P22 gauge boson winding spectrum (the ONLY allowed gauge bosons)
P22_GAUGE_BOSONS = {0, 3, -3}  # γ/Z (W=0), W⁺ (W=+3), W⁻ (W=-3)

# Non-zero SM particles (particles with definite identity beyond vacuum)
SM_NONZERO = {1, 2, 3, 4, 5, 6}


# ──────────────────────────────────────────────────────────────────────────────
# Enumerate all 343 neighborhoods
# ──────────────────────────────────────────────────────────────────────────────

def enumerate_all_neighborhoods():
    """Return list of (l, c, r, output) for all 343 neighborhoods."""
    results = []
    for l, c, r in product(range(7), repeat=3):
        out = fmdl(l, c, r)
        results.append((l, c, r, out))
    return results


def classify_neighborhood(l, c, r, out):
    """
    Classify a single neighborhood by:
    - Whether all inputs are non-vacuum SM particles
    - Whether output is a non-vacuum SM particle
    - Effective boson winding (P22 vertex interpretation)
    - Source: 'orbit', 'rule110', 'free'
    """
    key = (l, c, r)
    if key in ORBIT_FIXED:
        source = "orbit"
    elif key in RULE110_FIXED:
        source = "rule110"
    else:
        source = "free"

    all_inputs_sm_nonzero = (l in SM_NONZERO) and (c in SM_NONZERO) and (r in SM_NONZERO)
    output_sm_nonzero = out in SM_NONZERO
    is_nonzero_output = (out != 0)

    # Center-cell vertex interpretation: c → out mediated by boson with W_B = W(out) - W(c)
    W_c = P22_WINDING[c]
    W_out = P22_WINDING[out]
    effective_W_B = W_out - W_c  # integer winding of "effective boson"
    in_p22_spectrum = effective_W_B in P22_GAUGE_BOSONS

    return {
        "source": source,
        "all_inputs_sm_nonzero": all_inputs_sm_nonzero,
        "output_sm_nonzero": output_sm_nonzero,
        "is_nonzero_output": is_nonzero_output,
        "effective_W_B": effective_W_B,
        "in_p22_spectrum": in_p22_spectrum,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Main analysis
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    all_nh = enumerate_all_neighborhoods()

    # Split into zero and non-zero
    zero_nh = [(l, c, r, o) for (l, c, r, o) in all_nh if o == 0]
    nonzero_nh = [(l, c, r, o) for (l, c, r, o) in all_nh if o != 0]

    print(f"Total neighborhoods: {len(all_nh)}")
    print(f"Zero-output neighborhoods: {len(zero_nh)}")
    print(f"Non-zero-output neighborhoods: {len(nonzero_nh)}")
    print()

    # Output distribution
    print("=== Output distribution (Z₇ → count) ===")
    from collections import Counter
    dist = Counter(o for (_, _, _, o) in all_nh)
    for v in range(7):
        print(f"  Z₇={v} ({SM_LABELS[v]:12s}): {dist[v]:4d} neighborhoods")
    print()

    # The 14 non-zero neighborhoods with full classification
    print("=== The 14 non-zero neighborhoods ===")
    print(f"{'#':>2}  {'(l,c,r)':>10}  {'→':>2}  {'out':>3}  {'particles (l,c,r → out)':>40}  "
          f"{'source':>8}  {'W_B':>5}  {'P22?':>5}")
    print("-" * 100)
    for idx, (l, c, r, o) in enumerate(nonzero_nh):
        cl = classify_neighborhood(l, c, r, o)
        particles = f"({SM_LABELS[l]}, {SM_LABELS[c]}, {SM_LABELS[r]}) → {SM_LABELS[o]}"
        p22_check = "✓" if cl["in_p22_spectrum"] else "✗"
        print(f"{idx+1:>2}  ({l},{c},{r}):  {o}  {particles:50s}  {cl['source']:>8}  "
              f"{cl['effective_W_B']:>+5}  {p22_check}")
    print()

    # Count neighborhoods with all-SM-particle inputs (all Z₇ are assigned particles)
    # Since ALL Z₇ values 0-6 are SM-assigned, this is all 343.
    # More interesting: neighborhoods where l,c,r are all NON-ZERO (specific SM particles)
    all_nonzero_inputs = [(l, c, r, o) for (l, c, r, o) in all_nh
                         if l != 0 and c != 0 and r != 0]
    all_nonzero_inputs_with_sm_output = [(l, c, r, o) for (l, c, r, o) in all_nonzero_inputs
                                          if o != 0]
    print(f"=== Neighborhoods with all-nonzero inputs ===")
    print(f"Total: {len(all_nonzero_inputs)} (of 343)")
    print(f"With non-zero output: {len(all_nonzero_inputs_with_sm_output)}")
    print("Non-zero-output entries with all-nonzero inputs:")
    for (l, c, r, o) in all_nonzero_inputs_with_sm_output:
        cl = classify_neighborhood(l, c, r, o)
        particles = f"({SM_LABELS[l]}, {SM_LABELS[c]}, {SM_LABELS[r]}) → {SM_LABELS[o]}"
        print(f"  ({l},{c},{r}) → {o}: {particles}  [{cl['source']}]")
    print()

    # P22 spectrum coverage analysis
    print("=== P22 Vertex Coverage Analysis (center-cell vertex interpretation) ===")
    print("Effective boson winding W_B = W(output) - W(center) for non-zero neighborhoods:")
    p22_matched = []
    non_p22 = []
    for (l, c, r, o) in nonzero_nh:
        cl = classify_neighborhood(l, c, r, o)
        if cl["in_p22_spectrum"]:
            p22_matched.append((l, c, r, o, cl))
        else:
            non_p22.append((l, c, r, o, cl))
    print(f"  In P22 gauge spectrum {{0, ±3}}: {len(p22_matched)} of 14")
    print(f"  Outside P22 spectrum: {len(non_p22)} of 14")
    print()
    print("Breakdown by effective W_B:")
    wb_counts = Counter(classify_neighborhood(l, c, r, o)["effective_W_B"]
                         for (l, c, r, o) in nonzero_nh)
    for wb, count in sorted(wb_counts.items()):
        in_spec = "✓ (P22)" if wb in P22_GAUGE_BOSONS else "✗"
        print(f"  W_B = {wb:+3d}: {count} neighborhoods  {in_spec}")
    print()

    # Check: does sum rule Z₇(l)+Z₇(c)+Z₇(r) ≡ output (mod 7) hold?
    print("=== Z₇ Sum Rule Check: (l+c+r) mod 7 == output? ===")
    sum_rule_holds = [(l, c, r, o) for (l, c, r, o) in nonzero_nh
                      if (l + c + r) % 7 == o]
    print(f"  Sum rule holds for {len(sum_rule_holds)} of {len(nonzero_nh)} non-zero neighborhoods:")
    for (l, c, r, o) in sum_rule_holds:
        print(f"    ({l},{c},{r}) → {o}: sum={l+c+r} mod 7 = {(l+c+r)%7} ✓")
    print()

    # Check: naive winding conservation for the CENTER CELL
    print("=== Center-Cell Winding Conservation Check ===")
    print("Checking W(l) + W(c) + W(r) == W(output) (mod 7) for each non-zero neighborhood:")
    winding_conserved = []
    for (l, c, r, o) in nonzero_nh:
        wl, wc, wr, wo = P22_WINDING[l], P22_WINDING[c], P22_WINDING[r], P22_WINDING[o]
        total_in = (wl + wc + wr) % 7
        out_mod7 = wo % 7
        if total_in == out_mod7:
            winding_conserved.append((l, c, r, o, wl, wc, wr, wo))
    print(f"  W-sum conservation holds for {len(winding_conserved)} of {len(nonzero_nh)} non-zero neighborhoods:")
    for (l, c, r, o, wl, wc, wr, wo) in winding_conserved:
        print(f"    ({l},{c},{r}) → {o}: W({wl})+W({wc})+W({wr})={wl+wc+wr}≡{(wl+wc+wr)%7} = W({wo})%7={wo%7}")
    print()

    # Cross-check against P22's specific vertices
    print("=== Cross-check: P22 charged-current vertices vs CA neighborhoods ===")
    p22_vertices = [
        # (f₁_Z₇, B_Z₇, f₂_Z₇, description)
        (6, 3, 2, "d + W⁺ → u"),
        (4, 3, 0, "e⁻ + W⁺ → ν"),
        (2, 4, 6, "u + W⁻ → d"),
        (0, 4, 4, "ν + W⁻ → e⁻"),
    ]
    print("P22 3-point vertices (f₁, B, f₂): is there any CA neighborhood (l,c,r)→out matching?")
    for (f1, B, f2, desc) in p22_vertices:
        # CA neighborhood would be (f1, B, f2) → out? Or some other combination?
        ca_out_as_f1B = fmdl(f1, B, f2)
        print(f"  {desc}: fmdl({f1},{B},{f2}) = {ca_out_as_f1B} ({SM_LABELS[ca_out_as_f1B]}) — "
              f"{'non-trivial' if ca_out_as_f1B != 0 else 'transparent (0)'}")
    print()

    # Complete vertex table summary
    print("=== Complete Vertex Table Summary ===")
    print(f"Total entries: 343 (= 7³)")
    print(f"Zero-output (transparency events): {len(zero_nh)}")
    print(f"Non-zero-output (interaction events): {len(nonzero_nh)}")
    print(f"  Orbit-sourced non-zero: {sum(1 for (l,c,r,o) in nonzero_nh if (l,c,r) in ORBIT_FIXED)}")
    print(f"  Rule110-sourced non-zero: {sum(1 for (l,c,r,o) in nonzero_nh if (l,c,r) in RULE110_FIXED)}")
    print(f"Non-zero entries producing W⁺ (Z₇=3): {sum(1 for (_,_,_,o) in nonzero_nh if o == 3)}")
    print(f"Non-zero entries producing d (Z₇=6): {sum(1 for (_,_,_,o) in nonzero_nh if o == 6)}")
    print(f"Non-zero entries producing u (Z₇=2): {sum(1 for (_,_,_,o) in nonzero_nh if o == 2)}")
    print(f"Non-zero entries producing anti-u (Z₇=5): {sum(1 for (_,_,_,o) in nonzero_nh if o == 5)}")
    print(f"Non-zero entries producing anti-d (Z₇=1): {sum(1 for (_,_,_,o) in nonzero_nh if o == 1)}")
    print(f"Entries producing W⁻/e⁻ (Z₇=4): {sum(1 for (_,_,_,o) in all_nh if o == 4)} (CONFIRMED ZERO)")
    print()

    # Completeness assessment: does the CA table contain ALL P22 SM interactions?
    print("=== Completeness Assessment ===")
    print("Question: Is f_MDL table a COMPLETE interaction kernel (all P22 SM vertices present)?")
    print()
    print("P22 vertex types and CA coverage:")
    print("  1. Charged current (W⁺/W⁻ mediated): CA has fmdl(2,0,2)=3 [W⁺ emission]")
    print("     P22 has d+W⁺→u and ν+W⁻→e⁻ style transitions.")
    print("     CA captures W⁺ *emission* from (u,∅,u) but not P22-style *absorption* d+W⁺→u.")
    print("     P22 vertices require input Z₇=6 (d) flanking Z₇=3 (W⁺) → Z₇=2 (u) output.")
    print(f"     Check fmdl(6,3,?)=? or fmdl(?,3,6)=?: "
          f"{[(l,r,fmdl(l,3,r)) for l in range(7) for r in range(7) if fmdl(l,3,r)!=0]}")
    print("  2. Neutral current (γ/Z mediated): CA shows W_B=0 for 5 neighborhoods [transparency]")
    print("     These are 'pass-through' transitions (c stays same particle type), consistent")
    print("     with photon/Z coupling preserving particle identity.")
    print("  3. Quark flavor change: fmdl(2,5,2)=6 [u,anti-u,u → d] — a CA-native quark transition")
    print("     P22 quark transitions go via W±; CA flavor change is an orbital transition.")
    print()
    print("CONCLUSION: The f_MDL table is PARTIAL as a P22 Feynman vertex kernel.")
    print("  - It contains the W⁺ emission vertex and γ/Z-like transparency transitions.")
    print("  - It does NOT contain P22-style 3-point fermion-boson-fermion absorption vertices.")
    print("  - The CA vertex topology (3 cells → 1 output) differs from P22 vertex topology")
    print("    (2 incoming particles + 1 boson exchange → 1 outgoing particle).")
    print("  - The CA vertex table IS complete as a catalog of ALL local CA dynamics.")
    print("  - The CA vertex table is NOT complete as a Feynman vertex set for the SM.")
    print()
    print("  However: every PHYSICALLY NON-TRIVIAL CA output (all 14 non-zero neighborhoods)")
    print("  involves only SM-assigned Z₇ values ({0,1,2,3,5,6}) with no exotic outputs.")
    print("  W⁻/e⁻ (Z₇=4) is confirmed ABSENT as an output (0 of 343). [Lean-certified]")
