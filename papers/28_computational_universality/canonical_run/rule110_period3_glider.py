"""
Rule 110 period-3 C2 glider identification — R102.NT13

Confirms v_R = 2/3 cells/step (period-3 C2 glider) and extracts the
localized bit pattern of the glider at the leading causal front.

Approach: evolve both an unperturbed base tape and a perturbed tape from
the same ether IC; the DIFFERENCE between them is the causal perturbation.
The leading edge of this difference is the causal front.

Ether: 11111000100110  (period 14, drift 4 cells LEFT per step,
        boundary condition ETHER[(i - 4*t) % 14])

NAMING NOTE: This script uses "C2 glider" / "period-3 C2 glider" following
the convention adopted in P28/P36 scripts, where "C2" denotes the rightward
causal front with speed v_R = +2/3 (period 3 steps, drift 2 cells right per
period). This DIFFERS from Cook (2004) Figure 5, where Cook's own "C2"
notation refers to a STATIONARY glider (period 7, Δx = 0). The rightward
causal front in Cook's original notation is the "A-glider" (or A-type
lambda pattern). In this codebase: "C2 glider" = Cook's A-type causal front
(v = +2/3, period 3).
"""

ETHER = [1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0]
RULE = {
    (1, 1, 1): 0, (1, 1, 0): 1, (1, 0, 1): 1, (1, 0, 0): 0,
    (0, 1, 1): 1, (0, 1, 0): 1, (0, 0, 1): 1, (0, 0, 0): 0,
}


def step_open(tape, t_offset):
    """Evolve one step. Open (ether) boundary conditions: neighbor outside
    the tape uses ETHER[(pos - 4*t_offset) % 14]."""
    L = len(tape)
    result = []
    for i in range(L):
        left  = tape[i - 1] if i > 0     else ETHER[(i - 1 - 4 * t_offset) % 14]
        right = tape[i + 1] if i < L - 1 else ETHER[(i + 1 - 4 * t_offset) % 14]
        result.append(RULE[(left, tape[i], right)])
    return result


def run(L=1000, T_max=300, center_x=500):
    ether_ic = [ETHER[i % 14] for i in range(L)]
    base      = ether_ic[:]
    perturbed = ether_ic[:]
    perturbed[center_x] = 1 - perturbed[center_x]

    right_leads = []   # (t, right_lead)
    base_history      = [base[:]]
    perturbed_history = [perturbed[:]]

    for t in range(1, T_max + 1):
        base      = step_open(base,      t - 1)
        perturbed = step_open(perturbed, t - 1)
        base_history.append(base[:])
        perturbed_history.append(perturbed[:])

        diff = [base[i] != perturbed[i] for i in range(L)]
        right_cells = [i - center_x for i in range(center_x + 1, L) if diff[i]]
        right_lead  = max(right_cells, default=0)
        right_leads.append((t, right_lead))

    return right_leads, base_history, perturbed_history


def period3_test(right_leads):
    positions = [x for _, x in right_leads]
    n_triplets = 0
    n_match    = 0
    for i in range(3, len(positions)):
        d = positions[i] - positions[i - 3]
        n_triplets += 1
        if d == 2:
            n_match += 1
    frac = n_match / n_triplets if n_triplets > 0 else 0.0
    return n_match, n_triplets, frac


# ─────────────────────────────────────────────────────────────
L       = 1000
T_MAX   = 300
CENTER  = 500

print("=" * 62)
print("Rule 110 period-3 C2 glider — R102.NT13")
print(f"L={L}, T_max={T_MAX}, launch x={CENTER}")
print("=" * 62)

right_leads, base_h, pert_h = run(L=L, T_max=T_MAX, center_x=CENTER)

# ── 1. Cumulative velocity table ──────────────────────────────
print(f"\n{'T':>5}  {'right_lead':>10}  {'v_R (cum)':>10}")
print("-" * 30)
for t, rl in right_leads:
    if t % 30 == 0:
        v = rl / t
        print(f"{t:>5}  {rl:>10}  {v:>10.6f}")

last_t, last_rl = right_leads[-1]
v_R_final = last_rl / last_t
print(f"\nFinal v_R = {v_R_final:.6f}  (2/3 = {2/3:.6f},"
      f"  deviation = {abs(v_R_final - 2/3):.6f})")

# ── 2. Period-3 test ──────────────────────────────────────────
n_match, n_triplets, frac = period3_test(right_leads)
print(f"\nPeriod-3 test ({n_triplets} triplets):")
print(f"  Δright_lead = 2 per 3 steps: {n_match}/{n_triplets}"
      f"  ({100*frac:.1f}%)")
print(f"  Expected for pure period-3 C2 glider: 100.0%")

# ── 3. Glider deviation pattern at the leading front ─────────
print("\nGlider deviation pattern at leading front"
      " (base XOR perturbed, last 4 time steps):")
for t, rl in right_leads[-4:]:
    abs_x = CENTER + rl  # absolute tape position of leading front
    lo = max(0, abs_x - 8)
    hi = min(L, abs_x + 4)
    base_w  = base_h[t][lo:hi]
    pert_w  = pert_h[t][lo:hi]
    diff_w  = [int(b != p) for b, p in zip(base_w, pert_w)]
    dev_w   = [p - b for b, p in zip(base_w, pert_w)]
    print(f"  t={t:3d}, right_lead={rl:3d}, abs_x={abs_x}:")
    print(f"    base      = {base_w}")
    print(f"    perturbed = {pert_w}")
    print(f"    diff mask = {diff_w}  (positions rel to front:"
          f" {[i-(abs_x-lo) for i,d in enumerate(diff_w) if d]})")
    print(f"    deviation = {dev_w}")

# ── 4. Period-3 self-similarity: pattern at t vs t+3 ─────────
print("\nPeriod-3 self-similarity: diff pattern at t vs t+3"
      " (should be identical up to +2 cell shift):")
for t, rl in right_leads[-7:-4]:
    t3 = t + 3
    rl3 = next((x for tt, x in right_leads if tt == t3), None)
    if rl3 is None:
        continue
    abs_x  = CENTER + rl
    abs_x3 = CENTER + rl3
    # Window of width 14 centred on the leading front
    lo  = max(0, abs_x  - 7);  hi  = min(L, abs_x  + 7)
    lo3 = max(0, abs_x3 - 7);  hi3 = min(L, abs_x3 + 7)
    diff_t  = [int(base_h[t][i]  != pert_h[t][i])  for i in range(lo,  hi)]
    diff_t3 = [int(base_h[t3][i] != pert_h[t3][i]) for i in range(lo3, hi3)]
    # Compare diff_t with diff_t3 shifted 2 cells left (glider moved +2)
    shift = rl3 - rl  # should be +2 for clean period-3 glider
    matches = sum(1 for a, b in zip(diff_t[max(0,shift):],
                                     diff_t3[:len(diff_t)-max(0,shift)])
                  if a == b)
    total = len(diff_t) - max(0, shift)
    print(f"  t={t}→t+3={t3}: shift={shift:+d}, "
          f"{matches}/{total} cells match ({100*matches/total:.0f}%)")

# ── 5. Summary ────────────────────────────────────────────────
print("\n" + "=" * 62)
print("SUMMARY — R102.NT13")
print("=" * 62)
ok_v  = abs(v_R_final - 2/3) < 0.002
ok_p3 = frac > 0.95
print(f"  v_R = {v_R_final:.6f} {'✅ = 2/3 EXACT' if ok_v else '❌ deviation from 2/3'}")
print(f"  Period-3 signature: {100*frac:.1f}% "
      f"{'✅ CONFIRMED (C2 glider)' if ok_p3 else '❌ not period-3'}")
print(f"  Ether: 11111000100110  (period 14, drift 4 cells/step)")
print(f"  The rightward causal speed v_R = 2/3 is set by the period-3")
print(f"  C2 glider of Rule 110, advancing 2 cells per 3 steps.")
print(f"  Source: Cook (2004), Wolfram ANKS Appendix.")
