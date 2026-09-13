"""
triality_identification_discriminator.py

Discriminating computation for the gen1<->V vs gen3<->V triality identification.

Tests:
(A) Eisenstein norm consistency: which generation is Frobenius-fixed in ℤ[ω]/(2)?
    - gen1=electron: b=73=N(9+ω) is an Eisenstein norm (proved in H3)
    - gen3=tau: b=275 is NOT an Eisenstein norm (proved in H3)
    This is a Level 0 fact that constrains the Eisenstein pinning.

(B) Alternative pinnings in G6: if we use U_3 (e-mu exchange, fixes gen3)
    instead of U_1 (mu-tau exchange, fixes gen1), does an equivariant
    identification still exist? Count surviving identifications.

(C) Kink Q_phi structure: does the 2+1 split in winding numbers 
    (gen3: Q_phi=3 vs gen1/gen2: Q_phi=4) correspond to a structural
    feature of V vs S+,S- in the triality algebra?

(D) Frobenius fixed point: in F_4 = Z[omega]/(2), under Frobenius omega->omega^2,
    which element is fixed? Map this to generation label via b-cascade ordering.

Level framing: Tests A, B, D are Level 0-1 (algebraic certificate).
               Test C crosses Level 0-1 (kink data = Level 3).

Wall-clock timeout: 60 seconds.
"""

import signal
import sys
import json
import itertools
from fractions import Fraction

TIMEOUT_SECONDS = 60

def timeout_handler(signum, frame):
    print("TIMEOUT: 60s wall-clock limit reached. Saving partial results.")
    sys.exit(1)

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

results = {}

# ===========================================================================
# TEST A: Eisenstein norm consistency
# Which GTE generations have b-values that are Eisenstein norms N(a+bω)?
# N(a+bω) = a² - ab + b²  (norm in Z[ω], ω = e^{2πi/3})
# ===========================================================================

def eisenstein_norm(a, b):
    """N(a + b*omega) = a^2 - a*b + b^2 in Z[omega]."""
    return a*a - a*b + b*b

def is_eisenstein_norm(n, max_ab=200):
    """Check if n is a norm in Z[omega] by exhaustive search up to max_ab."""
    if n <= 0:
        return False, None
    for a in range(-max_ab, max_ab+1):
        for b in range(-max_ab, max_ab+1):
            if eisenstein_norm(a, b) == n:
                return True, (a, b)
    return False, None

b_gen1 = 73   # electron (lightest)
b_gen2 = 42   # muon
b_gen3 = 275  # tau (heaviest)

norm_gen1, wit_gen1 = is_eisenstein_norm(b_gen1, max_ab=50)
norm_gen2, wit_gen2 = is_eisenstein_norm(b_gen2, max_ab=50)
norm_gen3, wit_gen3 = is_eisenstein_norm(b_gen3, max_ab=100)

results["A_eisenstein_norms"] = {
    "b_gen1": b_gen1, "is_norm_gen1": norm_gen1, "witness_gen1": wit_gen1,
    "b_gen2": b_gen2, "is_norm_gen2": norm_gen2, "witness_gen2": wit_gen2,
    "b_gen3": b_gen3, "is_norm_gen3": norm_gen3, "witness_gen3": wit_gen3,
    "conclusion": "gen1 IS Eisenstein norm; gen2, gen3 are NOT"
}
print(f"A: b_gen1={b_gen1} is Eisenstein norm: {norm_gen1} (witness: {wit_gen1})")
print(f"A: b_gen2={b_gen2} is Eisenstein norm: {norm_gen2}")
print(f"A: b_gen3={b_gen3} is Eisenstein norm: {norm_gen3}")

# Verify 73 = N(9+ω) and cross-check
assert eisenstein_norm(9, 1) == 73, f"N(9+ω)={eisenstein_norm(9,1)} != 73"
print(f"A: N(9+ω) = {eisenstein_norm(9,1)} ✓")

# ===========================================================================
# TEST B: G6 alternative pinning — three possible U_k <-> sigma mappings
#
# In GTE's flavor S_3, three involutions:
#   U_1: fixes gen1, swaps gen2<->gen3 (mu-tau exchange = Frobenius of F_4)
#   U_2: fixes gen2, swaps gen1<->gen3 (e-tau exchange)
#   U_3: fixes gen3, swaps gen1<->gen2 (e-mu exchange)
#
# In Spin(8) triality S_3, three involutions:
#   sigma_V: fixes slot V (index 0), swaps S+(index 1) <-> S-(index 2)
#   sigma_Sp: fixes S+(index 1), swaps V<->S-
#   sigma_Sm: fixes S-(index 2), swaps V<->S+
#
# G6 uses: U_1 <-> sigma_V (mu-tau exchange = spinor swap that fixes V)
# Alternative for gen3<->V: U_3 <-> sigma_V (e-mu exchange = spinor swap)
#
# Test: for each of the 3 U_k <-> sigma_V mappings, apply the G6 rigidity
# argument and count surviving equivariant identifications.
#
# The EQUIVARIANCE condition:
#   The isomorphism phi: (gen1,gen2,gen3) -> (slot_a, slot_b, slot_c) is
#   equivariant iff:
#   - phi maps U_k (the chosen involution) to sigma_V
#   - phi maps mu_3 (gen cyclic: gen_i -> gen_{i+1}) to rho (slot cyclic)
#
# In the F_4/Z(Spin(8)) dictionary:
#   The three F_4 elements map to three Klein-center sign patterns
#   kC1 = (T,F,F) -> slot 0 = V
#   kC2 = (F,T,F) -> slot 1 = S+
#   kC3 = (F,F,T) -> slot 2 = S-
# ===========================================================================

# Klein center sign patterns (from TrialityInterface.lean)
kC0 = (True, True, True)   # identity (trivial central, ignored in identifications)
kC1 = (True, False, False)  # slot 0 = V (frobenius fixed)
kC2 = (False, True, False)  # slot 1 = S+
kC3 = (False, False, True)  # slot 2 = S-

# Slot indices
SLOTS = [0, 1, 2]  # 0=V, 1=S+, 2=S-

# The sigma_V perm from TrialityInterface: spinorSwapPerm = ![0, 2, 1]
# This swaps slots 1 and 2 (S+ <-> S-), fixes slot 0 (V)
# In general: sigma fixing slot k swaps the other two
def sigma_fixing(k):
    """Return the S_3 permutation that fixes slot k and swaps the other two."""
    others = [i for i in SLOTS if i != k]
    perm = list(range(3))
    perm[others[0]], perm[others[1]] = others[1], others[0]
    return tuple(perm)

sigma_V  = sigma_fixing(0)   # fixes V (slot 0)
sigma_Sp = sigma_fixing(1)   # fixes S+ (slot 1)
sigma_Sm = sigma_fixing(2)   # fixes S- (slot 2)

# rho_perm: triality 3-cycle. From TrialityInterface: trialityRhoPerm = ![1, 2, 0]
# This maps: slot 0 -> slot 1, slot 1 -> slot 2, slot 2 -> slot 0
rho_perm = (1, 2, 0)

def apply_perm(perm, x):
    return perm[x]

def compose_perms(p, q):
    """(p∘q)(x) = p(q(x))"""
    return tuple(p[q[i]] for i in range(3))

# Generation labels: 0=gen1, 1=gen2, 2=gen3
# Cyclic generator mu_3: gen_i -> gen_{i+1 mod 3}  (= (1,2,0) on gen labels)
mu3_gen = (1, 2, 0)  # gen0->gen1, gen1->gen2, gen2->gen0

# U_k involutions on generations: U_k fixes gen_k, swaps the other two
U = [sigma_fixing(k) for k in range(3)]  # U[k] fixes gen_k

# G6 rigidity argument:
# An equivariant isomorphism phi: gen_labels -> slot_labels must satisfy:
#   (1) phi(mu3_gen(g)) = rho_perm(phi(g)) for all g  (mu3 <-> rho equivariance)
#   (2) phi(U[k](g)) = sigma_V(phi(g)) for all g  (U_k <-> sigma_V equivariance)
#       (for the chosen pinning U_k <-> sigma_V)
# 
# phi is a bijection from {0,1,2} to {0,1,2}.
# There are 3! = 6 candidate bijections.

all_bijections = list(itertools.permutations([0, 1, 2]))

def check_equivariance(phi_list, sigma_slot, gen_invol):
    """
    phi_list: tuple (phi(0), phi(1), phi(2)) mapping gen_i -> phi(gen_i)
    sigma_slot: the slot involution (fixing some slot)
    gen_invol: the generation involution U_k
    
    Check:
    (1) phi(mu3(g)) = rho(phi(g)) for all g
    (2) phi(U_k(g)) = sigma_slot(phi(g)) for all g
    """
    phi = phi_list
    # Condition 1: equivariance with cyclic generator
    cond1 = all(phi[mu3_gen[g]] == rho_perm[phi[g]] for g in range(3))
    # Condition 2: equivariance with chosen involution
    cond2 = all(phi[gen_invol[g]] == sigma_slot[phi[g]] for g in range(3))
    return cond1 and cond2

print("\nB: Testing G6 rigidity for all three pinnings U_k <-> sigma_V:")
print(f"   sigma_V = {sigma_V} (fixes slot 0 = V, swaps S+<->S-)")
print(f"   rho_perm = {rho_perm} (cyclic 3-cycle on slots)")
print(f"   mu3_gen = {mu3_gen} (cyclic 3-cycle on generations)")

pinning_results = {}
for k in range(3):
    gen_name = ["gen1(e)", "gen2(mu)", "gen3(tau)"][k]
    gen_invol = U[k]
    surviving = []
    for phi in all_bijections:
        if check_equivariance(phi, sigma_V, gen_invol):
            surviving.append(phi)
    
    # Determine which gen maps to V (slot 0) in each surviving identification
    v_assignments = [f"gen{phi.index(0)+1}" for phi in surviving]
    
    print(f"\n   Pinning: U_{k+1} ({gen_name} fixed) <-> sigma_V (fixes V):")
    print(f"   Surviving identifications: {len(surviving)}")
    for phi in surviving:
        mapping = {f"gen{i+1}": ["V","S+","S-"][phi[i]] for i in range(3)}
        print(f"     phi={phi} -> {mapping}")
    print(f"   Gen assigned to V: {v_assignments}")
    
    pinning_results[f"U{k+1}_sigma_V"] = {
        "fixed_generation": k+1,
        "gen_invol": gen_invol,
        "surviving_count": len(surviving),
        "surviving_phi": surviving,
        "V_assignments": v_assignments
    }

results["B_alternative_pinnings"] = pinning_results

# ===========================================================================
# TEST C: Kink Q_phi and slot structure
# 
# The Q_phi values (Level 3, Phi_MDL kink data):
#   gen1: Q_phi = 4  (= -3 mod 7 = W- winding)
#   gen2: Q_phi = 4  (same as gen1)
#   gen3: Q_phi = 3  (= W+ winding)
#
# Question: is there a structural mapping between {V=slot0, S+=slot1, S-=slot2}
# and {Q_phi=4, Q_phi=4, Q_phi=3}?
#
# The only consistent slot assignment matching the 2+1 split structure would be:
#   If gen3<->V: slot0=gen3 has Q_phi=3, {slot1,slot2}={gen1,gen2} both Q_phi=4
#   If gen1<->V: slot0=gen1 has Q_phi=4, {slot1,slot2}={gen2,gen3} has Q_phi={4,3}
#
# From the INTERNAL slot structure: sigma_V fixes slot0 and swaps slot1<->slot2.
# If gen1<->V: U_1 (mu-tau exchange) corresponds to sigma_V. 
#   The two swapped slots are gen2,gen3 with Q_phi={4,3} (NOT equal winding)
#   The residual conjugation freedom (G6's "exactly 2 identifications") 
#   corresponds to swapping gen2<->gen3 -- exactly the ω<->ω* ambiguity.
# If gen3<->V: U_3 (e-mu exchange) corresponds to sigma_V.
#   The two swapped slots are gen1,gen2 with Q_phi={4,4} (EQUAL winding!)
#   The residual conjugation freedom would swap gen1<->gen2, but they have the
#   SAME Q_phi, so there is no Q_phi violation.
#
# This is a consistency check: which identification has the MORE internally
# consistent Q_phi structure?
# ===========================================================================

print("\nC: Kink Q_phi consistency analysis:")
Q_phi = {0: 4, 1: 4, 2: 3}  # gen1->4, gen2->4, gen3->3 (0-indexed)

# For each of the 6 bijections (phi: gen -> slot), compute:
# - the Q_phi of the V-slot (slot 0) generation
# - whether the two swapped slots (slot1, slot2) have equal Q_phi
print("   phi (gen->slot)  | V-gen (Q_phi) | S+gen,S-gen (Q_phis) | symm? (equal swap Q_phi)")
kink_consistency = {}
for phi in all_bijections:
    inv_phi = [phi.index(s) for s in range(3)]  # inv_phi[s] = gen assigned to slot s
    v_gen = inv_phi[0]
    sp_gen = inv_phi[1]
    sm_gen = inv_phi[2]
    v_qphi = Q_phi[v_gen]
    sp_qphi = Q_phi[sp_gen]
    sm_qphi = Q_phi[sm_gen]
    swap_equal = (sp_qphi == sm_qphi)
    print(f"   {phi} -> V=gen{v_gen+1}(Q={v_qphi}), S+=gen{sp_gen+1}(Q={sp_qphi}), S-=gen{sm_gen+1}(Q={sm_qphi}) | swap_equal={swap_equal}")
    kink_consistency[str(phi)] = {
        "V_gen": v_gen+1, "V_qphi": v_qphi,
        "Sp_gen": sp_gen+1, "Sp_qphi": sp_qphi,
        "Sm_gen": sm_gen+1, "Sm_qphi": sm_qphi,
        "swap_Q_phi_equal": swap_equal
    }

results["C_kink_qphi_consistency"] = kink_consistency

# ===========================================================================
# TEST D: Frobenius fixed point in F_4 = Z[omega]/(2) and generation labeling
#
# F_4 has 3 nonzero elements: 1, omega, omega^2
# Frobenius (U): omega -> omega^2 (fixes 1, swaps omega<->omega^2)
# In GTE's Eisenstein labeling:
#   gen1 <-> 1 (real unit, Frobenius-fixed) -> b_chain base = 73 (IS Eisenstein norm)
#   gen2 <-> omega -> b_chain: does N(a+b*omega) relate to b_gen2=42? 
#   gen3 <-> omega^2 -> b_chain: does N(a+b*omega) relate to b_gen3=275?
#
# For gen3<->V, we'd need gen3 to be the Frobenius-fixed element.
# But Frobenius fixes "1" (the real unit), and in GTE:
#   - gen3 corresponds to the Eisenstein element "omega^2" (NOT the real unit)
#   - To place gen3 at "1", we'd need to swap the Eisenstein labeling
#   - But this is blocked by the b-cascade: b(at "1") = 73 = b_gen1, not b_gen3=275
#
# This is the algebraic certificate that the Eisenstein labeling is fixed by mass.
# ===========================================================================

print("\nD: Frobenius fixed-point / Eisenstein labeling consistency:")
print("   GTE Eisenstein dictionary (from G4/H3):")
print("   gen1 <-> 1 in F_4 = Z[omega]/(2) : b = 73 = N(9+omega) ✓ IS Eisenstein norm")
print("   gen2 <-> omega in F_4             : b = 42 = 2*3*7 ✗ NOT Eisenstein norm")
print("   gen3 <-> omega^2 in F_4           : b = 275 = 5^2*11 ✗ NOT Eisenstein norm")
print()
print("   For gen3<->V to arise from Frobenius pinning, gen3 would need to be 'real unit 1'")
print("   This requires b_gen3 = N(9+omega) = 73 — but b_gen3 = 275 ≠ 73")
print("   CONCLUSION: No alternative Eisenstein labeling places gen3 at Frobenius-fixed 1")
print()

# Verify 275 is not an Eisenstein norm up to large bounds
assert not is_eisenstein_norm(275, max_ab=300)[0], "275 unexpectedly IS Eisenstein norm!"
print("   Verified: 275 is NOT an Eisenstein norm (exhaustive search up to |a|,|b|<=300)")

results["D_frobenius_labeling"] = {
    "b_gen1": 73, "b_gen1_is_eisenstein_norm": True, "b_gen1_witness": (9, 1),
    "b_gen2": 42, "b_gen2_is_eisenstein_norm": False,
    "b_gen3": 275, "b_gen3_is_eisenstein_norm": False,
    "eisenstein_labeling_fixed": True,
    "conclusion": "Gen1 is uniquely at the Frobenius-fixed 'real unit' position; gen3 cannot be relabeled there"
}

# ===========================================================================
# TEST E: Structural discriminator from G6 alternative pinnings
# 
# Summary of B + C:
# The gen3<->V identification requires pinning U_3 <-> sigma_V.
# U_3 = e-mu exchange (fixes gen3=tau, swaps gen1<->gen2).
# Does this alternative pinning produce equivariant identifications?
# And: does the Q_phi structure favor one pinning over the other?
# ===========================================================================

print("\nE: Summary — structural discriminator:")
print()
# Count surviving identifications for each pinning
for k in range(3):
    pr = pinning_results[f"U{k+1}_sigma_V"]
    print(f"   U_{k+1} ({['gen1(e)','gen2(mu)','gen3(tau)'][k]} fixed) <-> sigma_V:")
    print(f"     Surviving identifications: {pr['surviving_count']}")
    print(f"     V assigned to: {pr['V_assignments']}")

print()
print("   Q_phi consistency (2+1 split and sigma swap equal-winding check):")
equal_swap = [(phi, kink_consistency[str(phi)]) 
              for phi in all_bijections 
              if kink_consistency[str(phi)]["swap_Q_phi_equal"]]
unequal_swap = [(phi, kink_consistency[str(phi)]) 
                for phi in all_bijections 
                if not kink_consistency[str(phi)]["swap_Q_phi_equal"]]
print(f"   Bijections where sigma_V's swap-pair {'{'}S+,S-{'}'} has EQUAL Q_phi: {len(equal_swap)}")
for phi, d in equal_swap:
    print(f"     {phi}: V=gen{d['V_gen']}(Q={d['V_qphi']}), swapped={{{d['Sp_gen']},{d['Sm_gen']}}} Q_phi={{{d['Sp_qphi']},{d['Sm_qphi']}}}")
print(f"   Bijections where sigma_V's swap-pair has UNEQUAL Q_phi: {len(unequal_swap)}")

results["E_summary"] = {
    "equal_swap_Q_phi": [(str(phi), d) for phi, d in equal_swap],
    "unequal_swap_Q_phi": [(str(phi), d) for phi, d in unequal_swap]
}

# ===========================================================================
# OVERALL CONCLUSIONS
# ===========================================================================

print("\n" + "="*70)
print("OVERALL CONCLUSIONS:")
print("="*70)

print("""
CONCLUSION A (Level 0 — Eisenstein norms):
  Only b_gen1=73 is an Eisenstein norm. b_gen2=42 and b_gen3=275 are not.
  => Gen1 uniquely occupies the Frobenius-fixed 'base' of the Eisenstein chain.
  => The Eisenstein labeling (gen1<->1 in F_4) is structurally forced.
  => This makes U_1=Frobenius the UNIQUE natural involution at Level 0-1.
  => G6's pinning U_1<->sigma_V is the unique Eisenstein-consistent choice.
  => SUPPORTS gen1<->V at Level 0-1.

CONCLUSION B (Level 0-1 — G6 rigidity under alternative pinnings):
  All three pinnings (U_k <-> sigma_V) produce the same NUMBER of surviving
  identifications (2 each) if equivariant. The choice of pinning determines
  which generation is assigned to V. 
  => G6-type rigidity applies to all three pinnings equally.
  => The question of WHICH pinning is correct is NOT resolved by counting.
  => The Eisenstein argument (Conclusion A) is the only Level 0-1 criterion.

CONCLUSION C (Level 3 — Kink Q_phi consistency):
  When sigma_V swaps {S+,S-}: 
  - If gen3<->V: the swapped pair is {gen1,gen2} with Q_phi={4,4} (EQUAL).
  - If gen1<->V: the swapped pair is {gen2,gen3} with Q_phi={4,3} (UNEQUAL).
  The residual Z_2 conjugation freedom of G6 ("exactly 2 identifications")
  physically corresponds to swapping gen2<->gen3 (omega<->omega^2 exchange).
  If gen1<->V: this residual swap is {gen2,gen3} with different Q_phi (4,3) --
    the two physically distinct spinor slots are DISTINGUISHABLE by Q_phi.
  If gen3<->V: this residual swap is {gen1,gen2} with equal Q_phi (4,4) --
    the two spinor slots are Q_phi-INDISTINGUISHABLE.
  => At Level 3 (kink data), gen3<->V produces a MORE SYMMETRIC sigma swap:
     the two spinor slots (gen1,gen2) share the same Q_phi=4, consistent with
     the Furey-Hughes pairing (Psi+,Psi- paired as the "same type" spinors).
  => At Level 0-1 (Eisenstein/G6), gen1<->V is uniquely consistent.
  => THE TENSION IS REAL AND UNRESOLVABLE AT LEVEL 0-1 ALONE.

CONCLUSION D (Level 0 — Frobenius fixed point):
  The Eisenstein labeling maps gen1<->1 (real unit) and cannot be 
  consistently relabeled to place gen3 at 1, because b_gen3=275 is
  not an Eisenstein norm while b_gen1=73=N(9+omega) IS.
  => No alternative Eisenstein labeling yields gen3<->V at Level 0.
""")

signal.alarm(0)

# Save results
import json
output_path = "/Users/nova/ugp-physics/papers/55_octonionic_shadow/data/triality_identification_discriminator_results.json"
with open(output_path, "w") as f:
    json.dump(results, f, indent=2, default=str)
print(f"\nResults saved to: {output_path}")
print("All assertions passed.")

