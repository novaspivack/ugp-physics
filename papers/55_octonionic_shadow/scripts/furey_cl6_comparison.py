#!/usr/bin/env python3
"""
furey_cl6_comparison.py

The physics-facing bridge between QR(7)-octonions and Furey's Cl(6) construction.
Everything below uses ONLY the octonion table built from the QR(7) difference set
(octonion_from_qr7.py). Construction follows Furey (ℂ⊗𝕆 / Cl(6)), but with the
combinatorial input made explicit. Numerics: numpy complex128; every asserted identity
checked to 1e-12. The matrices have entries in (1/2)Z[i], so all checks are exact in
principle (Lean targets do them over Q(i)). Verifies:

  (C1) Left-multiplication operators L_i = L_{e_i} are 8x8 real antisymmetric
       matrices satisfying the CLIFFORD RELATIONS {L_i, L_j} = -2 delta_ij
       (i,j = 1..6), i.e. the imaginary octonion units generate Cl(0,6) acting on
       R^8 = O. (Consequence of alternativity alone.)
  (C2) The volume element L_1 L_2 L_3 L_4 L_5 L_6 equals ±L_7: the 7th unit is
       the Clifford volume form of the other six.
  (C3) PENCIL -> LADDERS: the three Fano lines through the point 7 are {7,1,3},
       {2,6,7}, {4,5,7}; each contributes an ordered pair (a,b) with e_a e_b = e_7,
       namely (1,3), (2,6), (4,5). Define alpha_k = (1/2)(-L_a + i L_b). Then the
       CAR algebra {alpha_j, alpha_k} = 0, {alpha_j, alpha_k^dag} = delta_jk holds
       EXACTLY: three fermionic ladder operators, one per line of the pencil.
       N_c = 3 = number of lines through a Fano point = |QR(7)| = (7-1)/2.
  (C4) CHARGES: N = sum alpha^dag alpha has spectrum {0,1,2,3} with multiplicities
       {1,3,3,1} on C^8; Q = N/3 has spectrum {0, 1/3, 2/3, 1} x {1,3,3,1} --
       the electric-charge pattern of one generation's isospin-up sector
       (nu, dbar, u, e+), as in Furey's Cl(6) model.
  (C5) COLOR: the bilinears T_A = alpha^dag lambda_A alpha (lambda_A = Gell-Mann)
       close on su(3): [T_A, T_B] = 2i f_ABC T_C with the standard structure
       constants; they commute with N (charge is a color singlet); and the quadratic
       Casimir separates C^8 into 1 + 3 + 3bar + 1 (Casimir 0, 16/3, 16/3, 0).
  (C6) SU(3) fixes the (1, e_7) plane: exp(i theta T_A) acts trivially on the real
       unit and on e_7 -- the infinitesimal check T_A|1> = T_A|e_7> = 0 holds for
       all A. This is the concrete realization of SU(3) = Stab_{G2}(e_7) at the
       level of this representation.
"""

import itertools
import numpy as np

TOL = 1e-12

# ---- rebuild the QR(7) octonion table (self-contained) ----------------
def m7(x): return ((x - 1) % 7) + 1
MUL = {}
for t in range(7):
    a, b, c = m7(1+t), m7(2+t), m7(4+t)
    for (x, y, z) in [(a,b,c),(b,c,a),(c,a,b)]:
        MUL[(x,y)] = (z, +1); MUL[(y,x)] = (z, -1)

def Lmat(i):
    """8x8 real matrix of left multiplication by e_i (i in 1..7)."""
    M = np.zeros((8, 8))
    M[i, 0] = 1.0          # e_i * 1 = e_i
    M[0, i] = -1.0         # e_i * e_i = -1
    for j in range(1, 8):
        if j == i: continue
        k, s = MUL[(i, j)]
        M[k, j] = s
    return M

L = {i: Lmat(i) for i in range(1, 8)}
I8 = np.eye(8)

# ---- (C1) Clifford relations ------------------------------------------
ok = True
for i in range(1, 7):
    for j in range(1, 7):
        anti = L[i] @ L[j] + L[j] @ L[i]
        target = -2.0 * I8 if i == j else np.zeros((8, 8))
        ok &= np.allclose(anti, target, atol=TOL)
    ok &= np.allclose(L[i].T, -L[i], atol=TOL)   # antisymmetry
assert ok
print("[C1] {L_i, L_j} = -2 delta_ij for i,j in 1..6 (Cl(0,6) on R^8): OK")

# ---- (C2) volume element ----------------------------------------------
vol = L[1] @ L[2] @ L[3] @ L[4] @ L[5] @ L[6]
sgn = None
for s in (+1, -1):
    if np.allclose(vol, s * L[7], atol=TOL): sgn = s
assert sgn is not None
print(f"[C2] L1 L2 L3 L4 L5 L6 = {'+' if sgn>0 else '-'}L7 (e_7 = Clifford volume form): OK")

# ---- (C3) pencil through 7 -> ladder operators -------------------------
pencil = []
for t in range(7):
    line = (m7(1+t), m7(2+t), m7(4+t))
    if 7 in line:
        pencil.append(line)
pairs = []
for line in pencil:
    for (a, b) in itertools.permutations([x for x in line if x != 7], 2):
        if MUL[(a, b)] == (7, +1):
            pairs.append((a, b))
            break
print(f"[C3a] pencil of Fano lines through 7: {pencil}")
print(f"[C3b] ordered pairs with e_a e_b = e_7: {pairs}  (N_c = {len(pairs)})")
assert len(pairs) == 3

alpha = [0.5 * (-L[a] + 1j * L[b]) for (a, b) in pairs]
adag  = [A.conj().T for A in alpha]

ok = True
for j in range(3):
    for k in range(3):
        ok &= np.allclose(alpha[j] @ alpha[k] + alpha[k] @ alpha[j],
                          np.zeros((8,8)), atol=TOL)
        anti = alpha[j] @ adag[k] + adag[k] @ alpha[j]
        target = I8 if j == k else np.zeros((8, 8))
        ok &= np.allclose(anti, target, atol=TOL)
assert ok
print("[C3c] CAR algebra {a_j,a_k}=0, {a_j,a_k^dag}=delta_jk: OK (exact ladder ops)")

# ---- (C4) number operator and charges ----------------------------------
N = sum(adag[k] @ alpha[k] for k in range(3))
evals = np.linalg.eigvalsh(N)
evals_r = np.round(evals.real, 9)
from collections import Counter
spec = Counter(evals_r)
print(f"[C4a] spectrum of N = sum a^dag a on C^8: "
      f"{dict(sorted(spec.items()))} (expect {{0:1, 1:3, 2:3, 3:1}})")
assert dict(sorted(spec.items())) == {0.0: 1, 1.0: 3, 2.0: 3, 3.0: 1}
print("[C4b] Q = N/3 spectrum: {0: x1, 1/3: x3, 2/3: x3, 1: x1}")
print("      = charge pattern (nu, dbar_r dbar_g dbar_b, u_r u_g u_b, e+): OK")

# which octonion directions carry which charge?
w, V = np.linalg.eigh(N)
def describe(vec):
    comps = [f"{'1' if i==0 else 'e'+str(i)}" for i in range(8)
             if abs(vec[i]) > 1e-8]
    return "+".join(comps)
zero_modes = [describe(V[:, i]) for i in range(8) if abs(w[i]) < 1e-8]
three_modes = [describe(V[:, i]) for i in range(8) if abs(w[i]-3) < 1e-8]
print(f"[C4c] N=0 eigenvector supported on: {zero_modes}; "
      f"N=3 eigenvector supported on: {three_modes}")
print("      (the singlets live in the (1, e_7) plane -- the fixed flag)")

# ---- (C5) su(3) closure -------------------------------------------------
lam = [np.zeros((3,3), dtype=complex) for _ in range(8)]
lam[0][0,1]=lam[0][1,0]=1
lam[1][0,1]=-1j; lam[1][1,0]=1j
lam[2][0,0]=1;  lam[2][1,1]=-1
lam[3][0,2]=lam[3][2,0]=1
lam[4][0,2]=-1j; lam[4][2,0]=1j
lam[5][1,2]=lam[5][2,1]=1
lam[6][1,2]=-1j; lam[6][2,1]=1j
lam[7][0,0]=lam[7][1,1]=1/np.sqrt(3); lam[7][2,2]=-2/np.sqrt(3)

T = []
for A in range(8):
    TA = np.zeros((8,8), dtype=complex)
    for j in range(3):
        for k in range(3):
            TA += adag[j] * lam[A][j,k] @ alpha[k] if False else lam[A][j,k] * (adag[j] @ alpha[k])
    T.append(TA)

# standard su(3) structure constants f_ABC (1-indexed in literature)
f = {}
def setf(a,b,c,val):
    from itertools import permutations
    for p in permutations((a,b,c)):
        ref = (a,b,c)
        idx = [ref.index(x) for x in p]
        inv = sum(1 for i in range(3) for j in range(i+1,3) if idx[i] > idx[j])
        sign = -1 if inv % 2 else 1
        f[p] = sign * val
setf(1,2,3,1.0)
setf(1,4,7,0.5); setf(1,6,5,0.5)
setf(2,4,6,0.5); setf(2,5,7,0.5)
setf(3,4,5,0.5); setf(3,7,6,0.5)
setf(4,5,8,np.sqrt(3)/2)
setf(6,7,8,np.sqrt(3)/2)

ok = True
maxdev = 0.0
for A in range(8):
    for B in range(8):
        comm = T[A] @ T[B] - T[B] @ T[A]
        rhs = np.zeros((8,8), dtype=complex)
        for C in range(8):
            fabc = f.get((A+1, B+1, C+1), 0.0)
            if fabc: rhs += 2j * fabc * T[C]
        dev = np.max(np.abs(comm - rhs))
        maxdev = max(maxdev, dev)
        ok &= dev < 1e-9
assert ok
print(f"[C5a] su(3) closure [T_A,T_B] = 2i f_ABC T_C with standard Gell-Mann")
print(f"      structure constants: OK (max deviation {maxdev:.2e})")

ok = all(np.max(np.abs(N @ TA - TA @ N)) < TOL for TA in T)
assert ok
print("[C5b] [N, T_A] = 0 for all A (charge is a color singlet): OK")

Casimir = sum(TA @ TA for TA in T)
cw = np.round(np.linalg.eigvalsh(Casimir).real, 9)
cspec = Counter(cw)
print(f"[C5c] quadratic Casimir spectrum on C^8: {dict(sorted(cspec.items()))}")
print(f"      (expect {{0: 2, 16/3 = {round(16/3,9)}: 6}} -> 1 + 3 + 3bar + 1)")
assert dict(sorted(cspec.items())) == {0.0: 2, round(16/3, 9): 6}

# ---- (C6) SU(3) fixes the (1, e_7) flag ---------------------------------
one = np.zeros(8); one[0] = 1
e7  = np.zeros(8); e7[7] = 1
ok = all(np.max(np.abs(TA @ one)) < TOL and np.max(np.abs(TA @ e7)) < TOL for TA in T)
assert ok
print("[C6] T_A |1> = T_A |e_7> = 0 for all A: su(3) fixes the (1, e_7) plane")
print("     -- representation-level witness of SU(3) = Stab_{G2}(e_7): OK")

print("\nALL PHYSICS-BRIDGE CHECKS PASSED.")
print("Color sector summary: N_c = #(lines through a Fano point) = |QR(7)| = 3;")
print("charges quantized in 1/3 because Q = N/3 with N counting pencil lines;")
print("color SU(3) = symmetry mixing the three pencil lines, fixing (1, e_7).")
