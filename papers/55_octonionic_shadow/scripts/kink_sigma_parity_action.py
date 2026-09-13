#!/usr/bin/env python3
"""
kink_sigma_parity_action.py — 093-F5: outer Spin(8) triality σ action on Φ_MDL kink sector.

Investigates all three routes:
  (a) Algebraic: trace σ through 𝔽₄ labels → generation labels → (Q_φ,Q_χ) labels
  (b) F₂₁-equivariance: does σ's induced action correspond to an automorphism of F₂₁?
  (c) Target-space: what target-space map does σ's action correspond to in V(φ)?

Tautology risk is flagged explicitly.
"""

import signal, sys, json, itertools
import time

TIMEOUT_SECONDS = 120

def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

t0 = time.time()

# ─────────────────────────────────────────────────────────────────────────────
# 1. KINK QUANTUM NUMBERS (certified: PhiMDLKinkQuantumNumbers.lean)
# ─────────────────────────────────────────────────────────────────────────────
# (Q_phi mod 7, Q_chi mod 3) — note gen3 has Q_phi=3, gen1/gen2 have Q_phi=4
KINK = {
    'vacuum': (0, 0),
    'gen3':   (3, 1),
    'gen1':   (4, 1),
    'gen2':   (4, 2),
}

print("=" * 68)
print("KINK QUANTUM NUMBERS (Lean-certified, PhiMDLKinkQuantumNumbers.lean)")
print("=" * 68)
for name, (qp, qc) in KINK.items():
    print(f"  {name:8s}: Q_phi={qp}, Q_chi={qc}")

# ─────────────────────────────────────────────────────────────────────────────
# 2. TRIALITY σ action on SLOTS (certified: TrialityInterface.lean G4)
# ─────────────────────────────────────────────────────────────────────────────
# spinorSwapPerm = [0, 2, 1]  (Lean: slot 0=V fixed, slots 1=S+ and 2=S- swapped)
# From G4_equivariant_dictionary:
#   sigma fixes kleinCenter1 (V slot)
#   sigma swaps kleinCenter2 (S+) <-> kleinCenter3 (S-)
SIGMA_SLOT = {'V': 'V', 'S+': 'S-', 'S-': 'S+'}  # σ: V fixed, S+↔S-
print("\n" + "=" * 68)
print("σ ACTION ON TRIALITY SLOTS (Lean-certified, TrialityInterface G4)")
print("=" * 68)
for s, t in SIGMA_SLOT.items():
    print(f"  σ({s}) = {t}")

# ─────────────────────────────────────────────────────────────────────────────
# 3. ROUTE (a) ALGEBRAIC: σ action on (Q_phi, Q_chi) under each identification
# ─────────────────────────────────────────────────────────────────────────────
# The three key identifications (from prior session Test B):
#   gen1↔V: gen1→V, gen2→S+, gen3→S-   (U_1 pinning, Frobenius)
#   gen3↔V: gen3→V, gen1→S+, gen2→S-   (U_3 pinning)
#   gen2↔V: gen2→V, gen3→S+, gen1→S-   (U_2 pinning)

IDENTIFICATIONS = {
    'gen1→V (Eisenstein/Frobenius)': {'gen1': 'V', 'gen2': 'S+', 'gen3': 'S-'},
    'gen3→V (Furey-Hughes)':         {'gen3': 'V', 'gen1': 'S+', 'gen2': 'S-'},
    'gen2→V':                         {'gen2': 'V', 'gen3': 'S+', 'gen1': 'S-'},
}

print("\n" + "=" * 68)
print("ROUTE (a): σ TRANSFORMATION LAW ON (Q_phi, Q_chi) PER IDENTIFICATION")
print("TAUTOLOGY RISK: This route ASSUMES the identification to compute σ's action.")
print("It can show consistency/inconsistency but cannot SELECT the identification.")
print("=" * 68)

route_a_results = {}
for id_name, gen_to_slot in IDENTIFICATIONS.items():
    # Build slot→gen map
    slot_to_gen = {v: k for k, v in gen_to_slot.items()}
    
    # σ acts on slots; compose gen→slot→σ(slot)→gen to get permutation of gens
    sigma_on_gens = {}
    for gen in ['gen1', 'gen2', 'gen3']:
        slot = gen_to_slot[gen]
        sigma_slot = SIGMA_SLOT[slot]
        sigma_gen = slot_to_gen[sigma_slot]
        sigma_on_gens[gen] = sigma_gen
    
    # Now compute (Q_phi, Q_chi) transformation
    sigma_on_kink = {}
    for gen in ['gen1', 'gen2', 'gen3']:
        src_kink = KINK[gen]
        dst_gen = sigma_on_gens[gen]
        dst_kink = KINK[dst_gen]
        sigma_on_kink[src_kink] = dst_kink
    
    # Include vacuum (should be fixed)
    sigma_on_kink[(0,0)] = (0,0)  # V is fixed, vacuum corresponds to V fixed point
    
    # Check Q_phi preservation on spinor pair
    spinor_pair = [g for g in ['gen1','gen2','gen3'] if gen_to_slot[g] != 'V']
    spinor_qphi = set(KINK[g][0] for g in spinor_pair)
    qphi_preserved = all(KINK[sigma_on_gens[g]][0] == KINK[g][0] for g in spinor_pair)
    qchi_preserved = all(KINK[sigma_on_gens[g]][1] == KINK[g][1] for g in spinor_pair)
    
    print(f"\n  [{id_name}]")
    print(f"    Gen permutation under σ: {sigma_on_gens}")
    for gen in ['gen1','gen2','gen3']:
        src = KINK[gen]
        dst = KINK[sigma_on_gens[gen]]
        print(f"    {gen}({src[0]},{src[1]}) → {sigma_on_gens[gen]}({dst[0]},{dst[1]})")
    print(f"    Spinor pair {spinor_pair}: Q_phi = {[KINK[g][0] for g in spinor_pair]}")
    print(f"    Q_phi preserved on spinor pair? {qphi_preserved}")
    print(f"    Q_chi preserved on spinor pair? {qchi_preserved}")
    
    # Characterize the (Q_phi,Q_chi) map
    dp = KINK[spinor_pair[0]][0]  # Q_phi of S+ gen
    dm = KINK[spinor_pair[1]][0]  # Q_phi of S- gen
    cp = KINK[spinor_pair[0]][1]  # Q_chi of S+ gen
    cm = KINK[spinor_pair[1]][1]  # Q_chi of S- gen
    
    # After σ: S+ gen → S- gen, S- gen → S+ gen
    dp_after = KINK[sigma_on_gens[spinor_pair[0]]][0]  # Q_phi of S- gen (what S+ became)
    cp_after = KINK[sigma_on_gens[spinor_pair[0]]][1]  # Q_chi of S- gen
    
    route_a_results[id_name] = {
        'sigma_on_gens': sigma_on_gens,
        'sigma_on_kink': {str(k): v for k,v in sigma_on_kink.items()},
        'qphi_preserved': qphi_preserved,
        'qchi_preserved': qchi_preserved,
        'spinor_pair_qphi': [KINK[g][0] for g in spinor_pair],
    }

signal.alarm(0)  # reset alarm
signal.alarm(TIMEOUT_SECONDS)

# ─────────────────────────────────────────────────────────────────────────────
# 4. ROUTE (b): F₂₁ equivariance — what automorphisms of F₂₁ act on kink labels
# ─────────────────────────────────────────────────────────────────────────────
# F₂₁ = ℤ₇⋊ℤ₃ with multiplication (a,b)·(c,d) = (a + 2^b·c mod 7, b+d mod 3)
# The kink labels live at (Q_phi, Q_chi) ∈ ℤ₇×ℤ₃, a SUBSET of F₂₁

print("\n" + "=" * 68)
print("ROUTE (b): F₂₁ AUTOMORPHISM ANALYSIS")
print("What automorphisms of F₂₁ = ℤ₇⋊ℤ₃ restrict to valid maps on kink labels?")
print("=" * 68)

def f21_mul(a, b, c, d):
    """F₂₁ multiplication: (a,b)·(c,d) = (a + 2^b·c mod 7, b+d mod 3)"""
    return ((a + pow(2, b, 7) * c) % 7, (b + d) % 3)

def is_automorphism_f21(perm_dict):
    """Check if a map on F₂₁ elements is a group automorphism."""
    elements = [(a, b) for a in range(7) for b in range(3)]
    for x in elements:
        if x not in perm_dict:
            return False
    for x in elements:
        for y in elements:
            xy = f21_mul(x[0], x[1], y[0], y[1])
            phixy = perm_dict.get(xy)
            phix_phiy = f21_mul(perm_dict[x][0], perm_dict[x][1],
                                  perm_dict[y][0], perm_dict[y][1])
            if phixy != phix_phiy:
                return False
    return True

# The kink label set (Q_phi, Q_chi):
kink_set = {(0,0), (3,1), (4,1), (4,2)}

# Candidate σ-actions on the kink label set (involutions fixing vacuum):
# Under gen1↔V: (4,2)↔(3,1), (4,1) and (0,0) fixed
# Under gen3↔V: (4,1)↔(4,2), (3,1) and (0,0) fixed
# Under gen2↔V: (3,1)↔(4,1), (4,2) and (0,0) fixed

sigma_kink_actions = {
    'sigma_gen1V': {(0,0):(0,0), (4,1):(4,1), (4,2):(3,1), (3,1):(4,2)},  # gen1↔V
    'sigma_gen3V': {(0,0):(0,0), (3,1):(3,1), (4,1):(4,2), (4,2):(4,1)},  # gen3↔V
    'sigma_gen2V': {(0,0):(0,0), (4,2):(4,2), (3,1):(4,1), (4,1):(3,1)},  # gen2↔V
}

print("\n  Checking whether each σ action on kink labels extends to")
print("  an automorphism of F₂₁ on the FULL group F₂₁:")

# For each kink σ-action, try to extend it to a full F₂₁ automorphism
# by checking: is there a full F₂₁ automorphism that restricts to this action on kink_set?

# Enumerate all automorphisms of F₂₁ via analytic formula.
# Every automorphism is of the form φ_{k,a} for k ∈ {1,...,6}, a ∈ {0,...,6}:
#   φ_{k,a}(m, 0) = (mk mod 7, 0)
#   φ_{k,a}(m, 1) = ((mk + a) mod 7, 1)
#   φ_{k,a}(m, 2) = ((mk + 3a) mod 7, 2)
# Key property: ALL automorphisms preserve the ℤ₃ component (b-value).
# This gives 6 × 7 = 42 automorphisms (proved analytically from the semidirect structure).
elements = [(a, b) for a in range(7) for b in range(3)]
all_auts = []
for k in range(1, 7):       # k ∈ {1,...,6} (units mod 7)
    for a_shift in range(7):  # a ∈ {0,...,6}
        phi = {}
        for (m, b) in elements:
            if b == 0:
                phi[(m, b)] = (m * k % 7, 0)
            elif b == 1:
                phi[(m, b)] = ((m * k + a_shift) % 7, 1)
            else:  # b == 2
                phi[(m, b)] = ((m * k + 3 * a_shift) % 7, 2)
        # Verify this is indeed an automorphism (assertion)
        assert is_automorphism_f21(phi), f"φ_{{{k},{a_shift}}} fails automorphism check"
        all_auts.append(phi)

print(f"\n  Total automorphisms of F₂₁: {len(all_auts)}")

# Now for each σ-action on kink labels, check if any automorphism restricts to it
route_b_results = {}
for action_name, action in sigma_kink_actions.items():
    extending_auts = []
    for aut in all_auts:
        # Check if this automorphism agrees with action on all kink elements
        matches = all(aut.get(k) == v for k, v in action.items())
        if matches:
            extending_auts.append(aut)
    
    print(f"\n  {action_name}:")
    print(f"    Action on kink labels: {action}")
    print(f"    Number of F₂₁ automorphisms extending this action: {len(extending_auts)}")
    if extending_auts:
        # Show the first one's structure
        aut = extending_auts[0]
        # Determine action on ℤ₇ generators (a=1,b=0)
        img_gen_z7 = aut[(1, 0)]
        img_gen_z3 = aut[(0, 1)]
        print(f"    Example automorphism: (1,0)→{img_gen_z7}, (0,1)→{img_gen_z3}")
        # Check if it's an involution
        aut_sq = {k: aut[aut[k]] for k in elements}
        is_involution = all(aut_sq[k] == k for k in elements)
        print(f"    Is an involution: {is_involution}")
    else:
        print(f"    NO F₂₁ automorphism extends this kink action")
    
    route_b_results[action_name] = {
        'num_extending_auts': len(extending_auts),
        'has_extension': len(extending_auts) > 0,
    }

signal.alarm(0)
signal.alarm(TIMEOUT_SECONDS)

# ─────────────────────────────────────────────────────────────────────────────
# 5. ROUTE (b) DEEPER: Characterize all F₂₁ automorphisms
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 68)
print("ROUTE (b) DEEPER: Characterize all F₂₁ automorphisms")
print("=" * 68)

print(f"\n  All {len(all_auts)} automorphisms of F₂₁:")
print("  (a,b) → φ(a,b): showing action on generators (1,0) and (0,1)")
aut_data = []
for i, aut in enumerate(all_auts):
    img_z7 = aut[(1,0)]
    img_z3 = aut[(0,1)]
    # Characterize: is it order 2?
    aut_sq = {k: aut[aut[k]] for k in elements}
    order_2 = all(aut_sq[k] == k for k in elements)
    # Restriction to kink set
    kink_restriction = {k: aut[k] for k in kink_set}
    # Check if restriction is one of our three σ-actions
    match = None
    for n, action in sigma_kink_actions.items():
        if kink_restriction == action:
            match = n
            break
    aut_data.append({'i': i, 'img_z7': img_z7, 'img_z3': img_z3,
                     'order_2': order_2, 'kink_restriction': kink_restriction,
                     'matches_sigma': match})
    print(f"  Aut {i}: (1,0)→{img_z7}, (0,1)→{img_z3}; order_2={order_2}; kink_restriction={kink_restriction}; σ-match={match}")

signal.alarm(0)
signal.alarm(TIMEOUT_SECONDS)

# ─────────────────────────────────────────────────────────────────────────────
# 6. ROUTE (c): TARGET SPACE — what does each σ-action correspond to on V(φ)?
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 68)
print("ROUTE (c): TARGET-SPACE SYMMETRY ANALYSIS")
print("Φ_MDL potential: V(φ) = (m²/49)(1 - cos(7φ)), 7 vacua at φ = 2πn/7")
print("Kink Q_phi = winding number mod 7 in target space S¹(period 7).")
print("=" * 68)

import math

def v_phimdl(phi, m_sq=1.0):
    """V(φ) = (m²/49)(1 - cos(7φ))"""
    return (m_sq / 49.0) * (1 - math.cos(7 * phi))

# Target-space symmetries of V(φ) = (m²/49)(1 - cos(7φ)):
# Z₇: φ → φ + 2πk/7 (translation by k vacua) — acts as Q_phi → Q_phi + k mod 7
# Z₂: φ → -φ (reflection) — acts as Q_phi → -Q_phi mod 7

# Under target-space reflection φ → -φ: Q_phi → -Q_phi mod 7
def reflect_qphi(q):
    return (-q) % 7

# Under Z₇ translation by k: Q_phi → Q_phi + k mod 7
def translate_qphi(q, k):
    return (q + k) % 7

print("\n  Target-space symmetries:")
print("  Z₂ (reflection φ→-φ): Q_phi → (-Q_phi) mod 7")
print("  Z₇ (translation φ→φ+2πk/7): Q_phi → (Q_phi + k) mod 7")

print("\n  Effect of reflection on kink Q_phi values:")
for name, (qp, qc) in KINK.items():
    print(f"  Q_phi({name}) = {qp} → reflect → {reflect_qphi(qp)}")

# Check: under gen1↔V, σ maps (4,2)→(3,1) and (3,1)→(4,2).
# Q_phi: 4→3 and 3→4. Is this the reflection? reflect(4) = -4 mod 7 = 3. YES!
#                                                reflect(3) = -3 mod 7 = 4. YES!
print("\n  Under gen1↔V: σ maps Q_phi 4→3 and 3→4.")
print(f"  reflect(4) = {reflect_qphi(4)}, reflect(3) = {reflect_qphi(3)}")
gen1V_matches_reflect = (reflect_qphi(4) == 3 and reflect_qphi(3) == 4)
print(f"  gen1↔V σ action on Q_phi matches target-space REFLECTION: {gen1V_matches_reflect}")

# Check: under gen3↔V, σ maps (4,1)→(4,2) and (4,2)→(4,1).
# Q_phi: 4→4. This is the identity on Q_phi.
print("\n  Under gen3↔V: σ maps Q_phi 4→4 (identity on Q_phi).")
print(f"  reflect(4) = {reflect_qphi(4)}, identity(4) = 4")
gen3V_matches_identity = True  # Q_phi stays 4
print(f"  gen3↔V σ action on Q_phi matches target-space IDENTITY: {gen3V_matches_identity}")

# Can Z₇ translation explain the gen1↔V Q_phi change 4→3?
print("\n  Can a Z₇ translation explain Q_phi: 4→3 AND 3→4 simultaneously?")
for k in range(7):
    t4 = translate_qphi(4, k)
    t3 = translate_qphi(3, k)
    if t4 == 3 and t3 == 4:
        print(f"  Translation by k={k}: Q_phi 4→{t4}, 3→{t3} — THIS MATCHES gen1↔V")
        break
else:
    print("  No single translation maps both 4→3 AND 3→4 simultaneously.")
    print("  (Translation maps all Q_phi by the same shift; 4→3 requires k=-1=6, but 3→4 requires k=1)")
    t4_6 = translate_qphi(4, 6)
    t3_6 = translate_qphi(3, 6)
    print(f"  k=6: 4→{t4_6}, 3→{t3_6}   k=1: 4→{translate_qphi(4,1)}, 3→{translate_qphi(3,1)}")

# Verify V(φ) reflection symmetry
print("\n  Verifying V(φ) reflection symmetry: V(-φ) = V(φ):")
test_phis = [0.1, 0.5, 1.0, math.pi/7]
for phi in test_phis:
    v_pos = v_phimdl(phi)
    v_neg = v_phimdl(-phi)
    print(f"  φ={phi:.4f}: V(φ)={v_pos:.6f}, V(-φ)={v_neg:.6f}, equal={abs(v_pos-v_neg)<1e-12}")

signal.alarm(0)
signal.alarm(TIMEOUT_SECONDS)

# ─────────────────────────────────────────────────────────────────────────────
# 7. TAUTOLOGY RISK ANALYSIS (Adam's challenge)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 68)
print("TAUTOLOGY RISK ANALYSIS — Route (a)")
print("=" * 68)
print("""
Route (a) CIRCULARITY DIAGNOSIS:
- Route (a) takes as INPUT: identification gen_i ↔ slot
- It COMPUTES: what σ does to the kink labels under that identification
- It CONCLUDES: whether σ "preserves Q_phi" under that identification

This IS circular for SELECTION purposes: asking "does σ preserve Q_phi under gen1↔V?"
is equivalent to asking "is the Q_phi structure of the gen1↔V spinor pair such that σ
maps it to equal Q_phi?" — which depends entirely on the Q_phi values of the generations
that land in the S+/S- slots, which depends on the identification.

THEREFORE: Route (a) cannot SELECT the identification. It can only CHARACTERIZE
the σ-action under each assumed identification.

Non-circular use of route (a): route (a) shows that the two identifications produce
QUALITATIVELY DIFFERENT σ-actions (reflection vs identity on Q_phi). The question of
which is physically correct must be answered by a DIFFERENT argument.

Routes (b) and (c) are less circular:
- Route (b) asks: which σ-action on kink labels EXTENDS to an automorphism of F₂₁?
  This is a group-theoretic question with a definite answer independent of the identification.
- Route (c) asks: which σ-action on kink Q_phi corresponds to a known target-space symmetry?
  This maps the identification question to a question about Lagrangian symmetries.
""")

# ─────────────────────────────────────────────────────────────────────────────
# 8. ROUTE (b) VERDICT: which σ-action on kink labels extends to F₂₁ automorphism?
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 68)
print("ROUTE (b) VERDICT: F₂₁ AUTOMORPHISM EXTENSION")
print("=" * 68)

for action_name, result in route_b_results.items():
    ext = result['has_extension']
    n = result['num_extending_auts']
    print(f"  {action_name}: extends to F₂₁ automorphism = {ext} ({n} automorphisms)")

# Also check if the order-2 automorphisms of F₂₁ exist and which σ-action they induce
order_2_auts = [d for d in aut_data if d['order_2'] and d['i'] > 0]  # exclude identity
print(f"\n  Order-2 (involutive) F₂₁ automorphisms: {len(order_2_auts)}")
for d in order_2_auts:
    print(f"  Aut {d['i']}: (1,0)→{d['img_z7']}, (0,1)→{d['img_z3']}; kink_action={d['kink_restriction']}; σ-match={d['matches_sigma']}")

signal.alarm(0)
signal.alarm(TIMEOUT_SECONDS)

# ─────────────────────────────────────────────────────────────────────────────
# 9. ROUTE (c) VERDICT: V(φ) symmetry and σ-action
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 68)
print("ROUTE (c) VERDICT: TARGET-SPACE SYMMETRY")
print("=" * 68)
print("""
V(φ) = (m²/49)(1 - cos(7φ)) has symmetry group:
  Z₇ (translations φ→φ+2πk/7): Q_phi → Q_phi + k mod 7
  Z₂ (reflection φ→-φ):        Q_phi → -Q_phi mod 7

Under gen1↔V: σ acts on Q_phi as REFLECTION (4→3, 3→4 = -4 mod 7, -3 mod 7)
  → This corresponds to target-space parity φ→-φ, a VALID Lagrangian symmetry.

Under gen3↔V: σ acts on Q_phi as IDENTITY (4→4)
  → This corresponds to target-space identity (trivial), also valid.

CONCLUSION: BOTH σ-actions correspond to valid target-space symmetries of V(φ).
  Neither is forbidden. Route (c) does NOT select one identification over the other.
  
IMPORTANT: The Z₂ reflection is a PHYSICAL symmetry of the Lagrangian, not just
a formal coincidence. Under gen1↔V, σ acts as the target-space Z₂.
""")

# ─────────────────────────────────────────────────────────────────────────────
# 10. F₂₁ AUTOMORPHISM STRUCTURE: deeper analysis
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 68)
print("F₂₁ AUTOMORPHISM STRUCTURE: which identifications are group-theoretically natural?")
print("=" * 68)

# Which F₂₁ automorphisms are involutions (order 2)?
# These are the natural candidates for σ (which has order 2: σ² = id)
print(f"\n  Full automorphism group of F₂₁ has order {len(all_auts)}")
print(f"  Non-identity involutive automorphisms: {len(order_2_auts)}")

for d in order_2_auts:
    kink_act = d['kink_restriction']
    # Describe the action on ℤ₇ component
    # aut maps (1,0)→img_z7, (0,1)→img_z3
    # aut on (a,b) = (k*a + something, ...)
    print(f"\n  Involutive Aut {d['i']}: (1,0)→{d['img_z7']}, (0,1)→{d['img_z3']}")
    print(f"    Restriction to kink labels: {kink_act}")
    print(f"    Matches σ under: {d['matches_sigma']}")
    # Check Q_phi behavior
    qphi_fixed = [q for q in [0,3,4] if kink_act.get((q,0),(q,0))[0] == q or
                  any(kink_act.get((q,c),(q,c))[0] == q for c in range(3))]

# Compute action on ALL kink elements for all involutive auts
print("\n  Summary: which σ-action(s) arise from involutive F₂₁ automorphisms?")
sigma_matches = {}
for d in aut_data:
    if d['matches_sigma'] is not None:
        if d['matches_sigma'] not in sigma_matches:
            sigma_matches[d['matches_sigma']] = []
        sigma_matches[d['matches_sigma']].append({'order_2': d['order_2'],
                                                   'img_z7': d['img_z7'],
                                                   'img_z3': d['img_z3']})

for sig_name, entries in sigma_matches.items():
    order2_entries = [e for e in entries if e['order_2']]
    other_entries = [e for e in entries if not e['order_2']]
    print(f"\n  {sig_name}: total F₂₁ auts with this kink restriction = {len(entries)}")
    print(f"    of which are order-2 (involutions): {len(order2_entries)}")
    if order2_entries:
        for e in order2_entries[:3]:
            print(f"      involution: (1,0)→{e['img_z7']}, (0,1)→{e['img_z3']}")

signal.alarm(0)
signal.alarm(TIMEOUT_SECONDS)

# ─────────────────────────────────────────────────────────────────────────────
# 11. ROUTE (a) DEEPER: Q_chi behavior and F₂₁ structure
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 68)
print("ROUTE (a) DEEPER: Q_phi AND Q_chi TRANSFORMATION LAWS")
print("=" * 68)

print("\n  Complete σ-action on (Q_phi, Q_chi) under each identification:")
for id_name in ['gen1→V (Eisenstein/Frobenius)', 'gen3→V (Furey-Hughes)']:
    res = route_a_results[id_name]
    print(f"\n  [{id_name}]:")
    print(f"    gen permutation: {res['sigma_on_gens']}")
    print(f"    (Q_phi,Q_chi) map:")
    for gen in ['gen1','gen2','gen3']:
        src = KINK[gen]
        dst = KINK[res['sigma_on_gens'][gen]]
        dqp = (dst[0] - src[0]) % 7
        dqc = (dst[1] - src[1]) % 3
        print(f"      {gen}: ({src[0]},{src[1]}) → ({dst[0]},{dst[1]})  ΔQ_phi={dqp}, ΔQ_chi={dqc}")
    
    # Check if action is negation: (q,c) → (-q,-c)
    gen1_src = KINK['gen1']; gen1_dst = KINK[res['sigma_on_gens']['gen1']]
    gen2_src = KINK['gen2']; gen2_dst = KINK[res['sigma_on_gens']['gen2']]
    gen3_src = KINK['gen3']; gen3_dst = KINK[res['sigma_on_gens']['gen3']]
    
    is_negation = (gen1_dst == ((-gen1_src[0])%7, (-gen1_src[1])%3) and
                   gen2_dst == ((-gen2_src[0])%7, (-gen2_src[1])%3) and
                   gen3_dst == ((-gen3_src[0])%7, (-gen3_src[1])%3))
    is_qphi_negate = (gen2_dst[0] == (-gen2_src[0])%7 and gen3_dst[0] == (-gen3_src[0])%7)
    is_qchi_negate = (gen2_dst[1] == (-gen2_src[1])%3 and gen3_dst[1] == (-gen3_src[1])%3)
    
    print(f"    Is full F₂₁ negation (a,b)→(-a,-b)? {is_negation}")
    print(f"    Is Q_phi negation only? {is_qphi_negate}")
    print(f"    Is Q_chi negation only? {is_qchi_negate}")
    print(f"    Q_phi preserved: {res['qphi_preserved']}")

# ─────────────────────────────────────────────────────────────────────────────
# 12. FINAL SYNTHESIS: 093-F5 VERDICT
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 68)
print("FINAL SYNTHESIS: 093-F5 VERDICT")
print("=" * 68)

print("""
THREE-ROUTE AGREEMENT/DISAGREEMENT SUMMARY:

Route (a) [algebraic, circular for SELECTION]:
  gen1↔V: σ acts as (Q_phi,Q_chi) → (-Q_phi,-Q_chi) on the spinor pair
           = full negation: gen2(4,2)↔gen3(3,1)
  gen3↔V: σ acts as (Q_phi,Q_chi) → (Q_phi,-Q_chi) on the spinor pair
           = Q_chi-only negation: gen1(4,1)↔gen2(4,2)

Route (b) [F₂₁ automorphism, non-circular]:
  Determine above which σ-actions extend to involutive F₂₁ automorphisms.
  (Results printed above — decisive for the ROUTE B verdict.)

Route (c) [target-space, non-circular]:
  gen1↔V: σ = target-space Z₂ parity (φ→-φ) — Q_phi: 4→3=(-4 mod 7)
           V(φ) = (m²/49)(1-cos7φ) IS Z₂-symmetric → valid Lagrangian symmetry
  gen3↔V: σ = target-space identity — Q_phi preserved
           Also a valid (trivial) Lagrangian symmetry
  → BOTH are valid. Route (c) does NOT discriminate. ✗ decisive

ROUTE (b) is the KEY: does the F₂₁ automorphism group contain an involution whose
restriction to kink labels matches the expected σ-action?
  - If ONLY one identification yields an extending F₂₁ involution → that one is selected.
  - If BOTH do → F₂₁ automorphism alone does not discriminate.
  - If NEITHER → σ cannot be interpreted as an F₂₁ automorphism; the question remains.

The Level 0-1 Eisenstein argument for gen1↔V is:
  b_gen1=73=N(9+ω) is Eisenstein norm; b_gen2=42, b_gen3=275 are NOT.
  → uniquely places gen1 at Frobenius-fixed 1∈𝔽₄ → gen1→V is forced at Level 0-1.
  → this is a THEOREM, not a desideratum.

The Level 3 Q_phi-symmetry argument for gen3↔V is:
  If σ must preserve Q_phi, only gen3↔V works.
  → this is a DESIDERATUM (naturalness), NOT a theorem from the Lagrangian.
  → V(φ) has Z₂ parity as a symmetry, so gen1↔V is not forbidden at Level 3 either.

093-F5 VERDICT:
  σ's Q_phi transformation law under each identification is explicitly computed:
    gen1↔V: σ = Z₂ target-space parity (Q_phi: 4↔3 = negation mod 7)
    gen3↔V: σ = trivial on Q_phi (Q_phi preserved)
  
  Neither is forbidden by the Lagrangian.
  Route (b) F₂₁-automorphism analysis is DECISIVE if it selects one identification.
  The result is printed above under 'ROUTE (b) VERDICT'.
""")

# ─────────────────────────────────────────────────────────────────────────────
# 13. SAVE RESULTS
# ─────────────────────────────────────────────────────────────────────────────
output = {
    'kink_quantum_numbers': {k: {'Q_phi': v[0], 'Q_chi': v[1]} for k, v in KINK.items()},
    'sigma_slot_action': SIGMA_SLOT,
    'route_a': route_a_results,
    'route_b': {
        'total_f21_automorphisms': len(all_auts),
        'involutive_f21_automorphisms': len(order_2_auts),
        'sigma_matches_involutive': {name: [d for d in aut_data
                                            if d['matches_sigma'] == name and d['order_2']]
                                     for name in sigma_kink_actions.keys()},
        'by_action': route_b_results,
    },
    'route_c': {
        'gen1V_matches_reflection': gen1V_matches_reflect,
        'gen3V_matches_identity': gen3V_matches_identity,
        'V_phi_Z2_symmetric': True,  # verified
        'both_valid_lagrangian_symmetries': True,
    },
    'elapsed_s': round(time.time() - t0, 2),
}

import os
os.makedirs('/Users/nova/ugp-physics/research-sandbox/epic_093', exist_ok=True)
with open('/Users/nova/ugp-physics/papers/55_octonionic_shadow/scripts/sigma_kink_action_results.json', 'w') as f:
    json.dump(output, f, indent=2, default=str)

print(f"\nResults saved to papers/55_octonionic_shadow/scripts/sigma_kink_action_results.json")
print(f"Total elapsed: {time.time()-t0:.2f}s")

signal.alarm(0)
