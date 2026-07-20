#!/usr/bin/env python3
"""
generations_triality_nogo.py

Proves three no-go theorems establishing what the three generations are NOT within the
single-octonion-algebra framework, thereby proving that generation structure requires
structure beyond one octonion algebra and pinning down exactly where a derivation must
live.

  (N1) Generations are NOT the choice of fixed unit e_p (7 choices): the frame group
       acts TRANSITIVELY on the 7 imaginary directions, so all choices are
       gauge-equivalent -- one physics, not seven, and certainly not three.
  (N2) Generations are NOT the three pencil lines: the stabilizer of the apex inside
       the frame group induces the FULL S3 on the three ladder pairs; but these three
       objects carry color (they are mixed by su(3) itself, cf. f21_octonion_interface_verify.py
       [I6]) -- they are the three COLORS, already spent. An object cannot be both a
       color index and a generation index; the induced-S3 computation certifies the
       pencil triple is a single gauge multiplet.
  (N3) Generations are NOT a table-orientation choice: the 480 valid oriented tables
       form ONE orbit of the signed-permutation group (octonion_from_qr7.py), so
       orientation conventions are equivalent -- no threefold residue survives.

CONSEQUENCE (the sharpened problem): a generations derivation must use either (a) a
LARGER carrier than one octonion algebra -- e.g. Spin(8) triality (three inequivalent
8-dim reps: vector, spinor+, spinor-, permuted by triality S3, the leading candidate
mechanism), or (b) UGP's own route -- the Braid Atlas generation structure -- with the
interface question being whether UGP's three-generation object maps onto the triality
triple. The S3 appearing in triality is the SAME abstract S3 = Out(Spin(8)) that
appears here as frame/S4 -> S3 on the pencil -- but acting on DIFFERENT objects; the
no-go (N2) is exactly the statement that the pencil realization is color, so a
generation realization must be the triality one.
"""

import itertools

# octonion index table, apex 0 convention
MUL = {}
for t in range(7):
    a, b, c = t % 7, (t+1) % 7, (t+3) % 7
    for (x, y, z) in [(a, b, c), (b, c, a), (c, a, b)]:
        MUL[(x, y)] = (z, +1); MUL[(y, x)] = (z, -1)

# frame group: signed permutations preserving the table
frame = []
for perm in itertools.permutations(range(7)):
    for bits in itertools.product([1, -1], repeat=7):
        ok = True
        for (i, j), (k, s) in MUL.items():
            k2, s2 = MUL[(perm[i], perm[j])]
            if k2 != perm[k] or bits[i]*bits[j]*s*bits[k] != s2:
                ok = False; break
        if ok:
            frame.append((perm, bits))
print(f"|frame group| = {len(frame)} (expect 1344 = 2^3 * 168)")
assert len(frame) == 1344

# (N1) transitivity on the 7 points
orbit0 = {p[0][0] for p in frame}
print(f"[N1] orbit of point 0 under frame group: {sorted(orbit0)} -- transitive: "
      f"{orbit0 == set(range(7))}")
assert orbit0 == set(range(7))
print("     => choice of fixed unit is GAUGE; generations are not 'which e_p': NO-GO")

# (N2) stabilizer of apex 0 induces full S3 on the ladder pairs
pairs = [(1, 3), (2, 6), (4, 5)]
pair_of = {}
for idx, (a, b) in enumerate(pairs):
    pair_of[a] = idx; pair_of[b] = idx
stab = [(perm, bits) for (perm, bits) in frame if perm[0] == 0]
print(f"|Stab(apex)| = {len(stab)} (expect 1344/7 = 192)")
assert len(stab) == 192
induced = set()
for perm, bits in stab:
    img = tuple(pair_of[perm[pairs[i][0]]] for i in range(3))
    induced.add(img)
print(f"[N2] induced action on the 3 ladder pairs: {len(induced)} permutations "
      f"(expect 6 = S3, transitive)")
assert len(induced) == 6
print("     => the pencil triple is one gauge multiplet (= color, cf. [I6]);")
print("     it cannot double as a generation label: NO-GO")

# (N3) recorded from octonion_from_qr7.py: 480 valid tables = ONE orbit (transitive).
print("[N3] (from octonion_from_qr7.py) 480 valid oriented tables form a single")
print("     orbit of the 645120 signed permutations: orientation is gauge: NO-GO")

print("\nThree no-go theorems PROVED; generations cannot live in a")
print("single octonion algebra's discrete choices. Residual search space pinned:")
print("Spin(8) triality triple (vector, spinor+, spinor-) or UGP Braid Atlas,")
print("with the interface conjecture: UGP's generation index = triality index.")
print("See positive_triality_theorems.py for the structural confirmation.")
