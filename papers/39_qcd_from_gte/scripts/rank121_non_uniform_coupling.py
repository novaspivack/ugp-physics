"""
Non-uniform coupling search: period-14, mirror, and anti-ether couplings
as candidate escapes from the Rank 118/119 gcd(3,14)=1 no-go.

The no-go (Rank 118, CatA) applies only to UNIFORM (spatially homogeneous) couplings.
This script tests three classes of non-uniform couplings:

  Idea 1 — Period-14 coupling (4 variants):
      Coupling strength varies with ether phase (i%14).
      Period-14 modulation may be "ether-transparent" to the period-3 glider.

  Idea 2 — Mirror (chirally-inverted) coupling:
      Layer 110 → Layer 124 correction uses RULE124 applied to tape_110.
      Layer 124 → Layer 110 correction uses RULE110 applied to tape_124.
      Respects the mirror symmetry of the {Rule 110, Rule 124} pair.

  Idea 3 — Anti-ether coupling:
      Injects the complement of the ether phase to cancel ether modulation.

Measurement: for each coupling, measure v_R (Layer 110 C₂ glider, target +2/3)
and v_L (Layer 124 mirror-C₂ glider, target −2/3) using the base-vs-perturbed
difference method established in Rank 111.
"""

import numpy as np

RULE110 = {(1,1,1): 0, (1,1,0): 1, (1,0,1): 1, (1,0,0): 0,
           (0,1,1): 1, (0,1,0): 1, (0,0,1): 1, (0,0,0): 0}
RULE124 = {(l,c,r): RULE110[(r,c,l)] for l in range(2) for c in range(2) for r in range(2)}

ETHER_110 = [1,1,1,1,1,0,0,0,1,0,0,1,1,0]
ETHER_124 = [0,1,1,0,0,1,0,0,0,1,1,1,1,1]


# ─────────────────────────────────────────────────────────────────────────────
# Coupling step functions
# ─────────────────────────────────────────────────────────────────────────────

def step_uniform_baseline(tape_110, tape_124):
    """No coupling — baseline reference."""
    L = len(tape_110)
    new_110 = []
    new_124 = []
    for i in range(L):
        b110 = RULE110[(tape_110[(i-1)%L], tape_110[i], tape_110[(i+1)%L])]
        b124 = RULE124[(tape_124[(i-1)%L], tape_124[i], tape_124[(i+1)%L])]
        new_110.append(b110)
        new_124.append(b124)
    return new_110, new_124


def step_period14_ether1_sites(tape_110, tape_124):
    """
    Period-14 Variant A: couple only at ether-1 sites.
    At cell i: if ETHER_124[i%14]==1, inject tape_124[i] XOR into b110 (124→110).
               if ETHER_110[i%14]==1, inject tape_110[i] XOR into b124 (110→124).
    """
    L = len(tape_110)
    new_110 = []
    new_124 = []
    for i in range(L):
        b110 = RULE110[(tape_110[(i-1)%L], tape_110[i], tape_110[(i+1)%L])]
        b124 = RULE124[(tape_124[(i-1)%L], tape_124[i], tape_124[(i+1)%L])]
        if ETHER_124[i % 14] == 1:
            b110 = (b110 ^ tape_124[i]) % 2
        if ETHER_110[i % 14] == 1:
            b124 = (b124 ^ tape_110[i]) % 2
        new_110.append(b110)
        new_124.append(b124)
    return new_110, new_124


def step_period14_ether0_sites(tape_110, tape_124):
    """
    Period-14 Variant B: couple only at ether-0 sites.
    """
    L = len(tape_110)
    new_110 = []
    new_124 = []
    for i in range(L):
        b110 = RULE110[(tape_110[(i-1)%L], tape_110[i], tape_110[(i+1)%L])]
        b124 = RULE124[(tape_124[(i-1)%L], tape_124[i], tape_124[(i+1)%L])]
        if ETHER_124[i % 14] == 0:
            b110 = (b110 ^ tape_124[i]) % 2
        if ETHER_110[i % 14] == 0:
            b124 = (b124 ^ tape_110[i]) % 2
        new_110.append(b110)
        new_124.append(b124)
    return new_110, new_124


def step_period14_phase_weight(tape_110, tape_124):
    """
    Period-14 Variant C: coupling strength = ether phase itself (0 or 1) × XOR.
    Functionally equivalent to Variant A since ether_phase ∈ {0,1}.
    Included explicitly for documentation clarity.
    """
    return step_period14_ether1_sites(tape_110, tape_124)


def step_period14_complement_phase(tape_110, tape_124):
    """
    Period-14 Variant D: couple with COMPLEMENT of ether phase.
    At cell i: coupling at ether-0 sites of ETHER_124 (for 124→110)
               coupling at ether-0 sites of ETHER_110 (for 110→124).
    """
    return step_period14_ether0_sites(tape_110, tape_124)


def step_mirror_cross_rule(tape_110, tape_124):
    """
    Mirror (chirally-inverted) coupling.
    Layer 124 sees Layer 110 through RULE124 applied to tape_110.
    Layer 110 sees Layer 124 through RULE110 applied to tape_124.
    XOR injection into each layer's base output.
    """
    L = len(tape_110)
    new_110 = []
    new_124 = []
    for i in range(L):
        b110 = RULE110[(tape_110[(i-1)%L], tape_110[i], tape_110[(i+1)%L])]
        b124 = RULE124[(tape_124[(i-1)%L], tape_124[i], tape_124[(i+1)%L])]
        # Mirror coupling: apply each rule to the OTHER tape
        b110_via_mirror = RULE124[(tape_110[(i-1)%L], tape_110[i], tape_110[(i+1)%L])]
        b124_via_mirror = RULE110[(tape_124[(i-1)%L], tape_124[i], tape_124[(i+1)%L])]
        new_b110 = (b110 ^ b124_via_mirror) % 2
        new_b124 = (b124 ^ b110_via_mirror) % 2
        new_110.append(new_b110)
        new_124.append(new_b124)
    return new_110, new_124


def step_mirror_reflected_position(tape_110, tape_124):
    """
    Mirror coupling variant: Layer 110 at i perturbs Layer 124 at (L-1-i)%L.
    Spatially reflected injection.
    """
    L = len(tape_110)
    new_110 = []
    new_124_base = []
    # First compute base outputs
    for i in range(L):
        b110 = RULE110[(tape_110[(i-1)%L], tape_110[i], tape_110[(i+1)%L])]
        b124 = RULE124[(tape_124[(i-1)%L], tape_124[i], tape_124[(i+1)%L])]
        new_110.append(b110)
        new_124_base.append(b124)
    # Inject mirror coupling
    new_124 = new_124_base[:]
    for i in range(L):
        mirror_i = (L - 1 - i) % L
        new_124[mirror_i] = (new_124[mirror_i] ^ tape_110[i]) % 2
    return new_110, new_124


def step_anti_ether(tape_110, tape_124):
    """
    Anti-ether coupling: inject the complement of the ether phase to cancel
    ether modulation explicitly.
    """
    L = len(tape_110)
    new_110 = []
    new_124 = []
    for i in range(L):
        b110 = RULE110[(tape_110[(i-1)%L], tape_110[i], tape_110[(i+1)%L])]
        b124 = RULE124[(tape_124[(i-1)%L], tape_124[i], tape_124[(i+1)%L])]
        anti_ether_124 = 1 - ETHER_124[i % 14]
        anti_ether_110 = 1 - ETHER_110[i % 14]
        new_b110 = (b110 ^ (anti_ether_124 & tape_124[i])) % 2
        new_b124 = (b124 ^ (anti_ether_110 & tape_110[i])) % 2
        new_110.append(new_b110)
        new_124.append(new_b124)
    return new_110, new_124


def step_anti_ether_full_xor(tape_110, tape_124):
    """
    Anti-ether variant: inject anti-ether as a global XOR (not gated by tape value).
    """
    L = len(tape_110)
    new_110 = []
    new_124 = []
    for i in range(L):
        b110 = RULE110[(tape_110[(i-1)%L], tape_110[i], tape_110[(i+1)%L])]
        b124 = RULE124[(tape_124[(i-1)%L], tape_124[i], tape_124[(i+1)%L])]
        anti_ether_124 = 1 - ETHER_124[i % 14]
        anti_ether_110 = 1 - ETHER_110[i % 14]
        new_b110 = (b110 ^ anti_ether_124) % 2
        new_b124 = (b124 ^ anti_ether_110) % 2
        new_110.append(new_b110)
        new_124.append(new_b124)
    return new_110, new_124


def step_period14_xor_neighbor(tape_110, tape_124):
    """
    Period-14 Variant E: coupling uses XOR of tape_124[i] with ETHER_124[i%14]
    as the signal to inject into Layer 110 (ether-relative correction).
    At cell i: inject (tape_124[i] XOR ETHER_124[i%14]) into b110.
    This is the "ether deviation" of Layer 124 as seen by Layer 110.
    """
    L = len(tape_110)
    new_110 = []
    new_124 = []
    for i in range(L):
        b110 = RULE110[(tape_110[(i-1)%L], tape_110[i], tape_110[(i+1)%L])]
        b124 = RULE124[(tape_124[(i-1)%L], tape_124[i], tape_124[(i+1)%L])]
        # Coupling signal = deviation of each layer from its own ether
        dev_124 = tape_124[i] ^ ETHER_124[i % 14]
        dev_110 = tape_110[i] ^ ETHER_110[i % 14]
        new_b110 = (b110 ^ dev_124) % 2
        new_b124 = (b124 ^ dev_110) % 2
        new_110.append(new_b110)
        new_124.append(new_b124)
    return new_110, new_124


def step_period14_ether_gated_deviation(tape_110, tape_124):
    """
    Period-14 Variant F: couple ONLY the ether-deviation signal, AND only at
    ether-active sites. Double gating: site must be ether-active AND deviation is non-zero.
    """
    L = len(tape_110)
    new_110 = []
    new_124 = []
    for i in range(L):
        b110 = RULE110[(tape_110[(i-1)%L], tape_110[i], tape_110[(i+1)%L])]
        b124 = RULE124[(tape_124[(i-1)%L], tape_124[i], tape_124[(i+1)%L])]
        dev_124 = tape_124[i] ^ ETHER_124[i % 14]
        dev_110 = tape_110[i] ^ ETHER_110[i % 14]
        # Only inject if site is ether-active (=1) in RECEIVING layer's ether
        if ETHER_110[i % 14] == 1:
            b110 = (b110 ^ dev_124) % 2
        if ETHER_124[i % 14] == 1:
            b124 = (b124 ^ dev_110) % 2
        new_110.append(b110)
        new_124.append(b124)
    return new_110, new_124


# ─────────────────────────────────────────────────────────────────────────────
# Velocity measurement
# ─────────────────────────────────────────────────────────────────────────────

def measure_v_R(step_fn, L=840, T=300, phase_110=1, phase_124=0):
    """
    Measure right-front propagation speed for Layer 110 C₂ glider.
    Base-vs-perturbed difference method (Rank 111 protocol).
    Single-bit flip perturbation at center of Layer 110.
    """
    ether_110 = [ETHER_110[(i + phase_110) % 14] for i in range(L)]
    ether_124 = [ETHER_124[(i + phase_124) % 14] for i in range(L)]

    base_110 = ether_110[:]
    base_124 = ether_124[:]
    pert_110 = ether_110[:]
    pert_110[L // 2] = 1 - pert_110[L // 2]
    pert_124 = ether_124[:]

    right_fronts = []
    for t in range(1, T + 1):
        base_110, base_124 = step_fn(base_110, base_124)
        pert_110, pert_124 = step_fn(pert_110, pert_124)
        diff = [pert_110[i] != base_110[i] for i in range(L)]
        if any(diff):
            right_front = max(i for i, d in enumerate(diff) if d)
            right_fronts.append((t, right_front))

    if len(right_fronts) < 10:
        return None
    # Linear regression over last 9 points
    ts = np.array([p[0] for p in right_fronts[-9:]], dtype=float)
    xs = np.array([p[1] for p in right_fronts[-9:]], dtype=float)
    if len(ts) < 2:
        return None
    coeffs = np.polyfit(ts, xs, 1)
    return float(coeffs[0])


def measure_v_L(step_fn, L=840, T=300, phase_110=1, phase_124=3):
    """
    Measure left-front propagation speed for Layer 124 mirror-C₂ glider.
    Single-bit flip perturbation at center of Layer 124, track left front.
    Phase 3 for Layer 124 is the working phase (established Rank 111).
    Returns the raw slope of min-diff-position vs t (negative = leftward).
    """
    ether_110 = [ETHER_110[(i + phase_110) % 14] for i in range(L)]
    ether_124 = [ETHER_124[(i + phase_124) % 14] for i in range(L)]

    base_110 = ether_110[:]
    base_124 = ether_124[:]
    pert_110 = ether_110[:]
    pert_124 = ether_124[:]
    pert_124[L // 2] = 1 - pert_124[L // 2]

    left_fronts = []
    for t in range(1, T + 1):
        base_110, base_124 = step_fn(base_110, base_124)
        pert_110, pert_124 = step_fn(pert_110, pert_124)
        diff = [pert_124[i] != base_124[i] for i in range(L)]
        if any(diff):
            left_front = min(i for i, d in enumerate(diff) if d)
            left_fronts.append((t, left_front))

    if len(left_fronts) < 10:
        return None
    ts = np.array([p[0] for p in left_fronts[-9:]], dtype=float)
    xs = np.array([p[1] for p in left_fronts[-9:]], dtype=float)
    if len(ts) < 2:
        return None
    n = len(ts)
    slope = (n * np.dot(ts, xs) - ts.sum() * xs.sum()) / \
            (n * np.dot(ts, ts) - ts.sum() ** 2)
    return float(slope)


def classify(v, target, tol=0.05):
    if v is None:
        return "NONE"
    return "✓" if abs(v - target) < tol else "✗"


# ─────────────────────────────────────────────────────────────────────────────
# Main search
# ─────────────────────────────────────────────────────────────────────────────

COUPLINGS = [
    ("no_coupling",                         step_uniform_baseline),
    ("period14_ether1_sites (Idea1-A)",     step_period14_ether1_sites),
    ("period14_ether0_sites (Idea1-B)",     step_period14_ether0_sites),
    ("period14_complement_phase (Idea1-D)", step_period14_complement_phase),
    ("period14_xor_neighbor (Idea1-E)",     step_period14_xor_neighbor),
    ("period14_ether_gated_dev (Idea1-F)",  step_period14_ether_gated_deviation),
    ("mirror_cross_rule (Idea2)",           step_mirror_cross_rule),
    ("mirror_reflected_position (Idea2b)",  step_mirror_reflected_position),
    ("anti_ether_gated (Idea3)",            step_anti_ether),
    ("anti_ether_full_xor (Idea3b)",        step_anti_ether_full_xor),
]

TARGET_R = 2.0 / 3.0
TARGET_L = -2.0 / 3.0

print("=" * 72)
print("Rank 121 — Non-uniform coupling search: escapes from gcd(3,14) no-go")
print("=" * 72)
print(f"  L=840  T=300  target v_R={TARGET_R:.4f}  target v_L={TARGET_L:.4f}  tol=0.05")
print()

print("Phase 1: v_R measurement (Layer 110, C₂ glider, target +2/3)")
print("-" * 72)
print(f"{'Coupling':<42}  {'v_R':>8}  {'Pass?':>6}")
print("-" * 72)

phase1_survivors = []
for name, fn in COUPLINGS:
    vR = measure_v_R(fn)
    passR = classify(vR, TARGET_R)
    vR_str = f"{vR:.6f}" if vR is not None else "   None"
    print(f"{name:<42}  {vR_str:>8}  {passR:>6}")
    if passR == "✓":
        phase1_survivors.append((name, fn, vR))

print()
print(f"Phase 1 survivors ({len(phase1_survivors)}):", [s[0] for s in phase1_survivors])
print()

print("Phase 2: v_L measurement (Layer 124, mirror-C₂ glider, target −2/3)")
print("  — only testing Phase 1 survivors —")
print("-" * 72)
print(f"{'Coupling':<42}  {'v_R':>8}  {'v_L':>9}  {'Both?':>6}")
print("-" * 72)

winners = []
for name, fn, vR in phase1_survivors:
    vL = measure_v_L(fn)
    passL = classify(vL, TARGET_L)
    vL_str = f"{vL:.6f}" if vL is not None else "   None"
    both = "YES" if passL == "✓" else "NO"
    print(f"{name:<42}  {vR:.6f}  {vL_str:>9}  {both:>6}")
    if both == "YES":
        winners.append((name, vR, vL))

print()
print("=" * 72)
print("FINAL RESULTS")
print("=" * 72)
if winners:
    print(f"  NON-TRIVIAL WINNERS ({len(winners)} non-trivial if not just 'no_coupling'):")
    for name, vR, vL in winners:
        marker = " *** NON-TRIVIAL ***" if name != "no_coupling" else " (trivial baseline)"
        print(f"    {name}: v_R={vR:.6f}, v_L={vL:.6f}{marker}")
else:
    print("  NO coupling preserves both v_R ≈ +2/3 AND v_L ≈ −2/3.")
    print("  Non-uniform couplings also fail — no-go extends beyond uniform case.")

non_trivial_winners = [w for w in winners if w[0] != "no_coupling"]
if non_trivial_winners:
    print()
    print("  *** BREAKTHROUGH: Non-trivial coupling(s) found! ***")
    for name, vR, vL in non_trivial_winners:
        print(f"      {name}: v_R={vR:.6f} (target {TARGET_R:.4f}), "
              f"v_L={vL:.6f} (target {TARGET_L:.4f})")
else:
    print()
    print("  No-go confirmed for all tested non-uniform variants.")
    print("  The gcd(3,14)=1 incommensurability is robust beyond the uniform class.")

print()
print("Done.")
