#!/usr/bin/env python3
"""
electroweak_housing_closure.py

Dynamical housing closure: verifies that the Koide charged-lepton mass ladder is a
function on the triality orbit, and computes the electroweak charge spectrum.

Inputs read from the UGP Lean corpus:
  * KoideAngle.lean:      koideThetaUGP = 2/9
  * KoideClosedForm.lean: Koide = 45 deg to democratic axis, S3-equivariant
  * GUTStructure.lean:    b_gen1, b_gen2, b_gen3 = 73, 42, 275
  * FrobeniusChain.lean:  tower 7, 73, 703 = 19*37 (terminates)

RESULTS PROVED / VERIFIED BELOW:

  (O1) ELECTROWEAK CHARGE CLOSURE. On the chiral ideal of C ⊗ H (a 2-dim doublet
       carrying su(2)_L with I3 = +-1/2, constructed from quaternion one-sided
       multiplication, NOT postulated) tensored with the octonionic factor C^8 carrying
       B-L = (2N-3)/3 (quaternion_electroweak_shadow.py theorem):
           Q  =  I3 + (B-L)/2  =  I3 + (2N-3)/6
       has spectrum EXACTLY the Standard-Model left-chiral charge multiset of one
       generation plus its conjugates: { nu:0, e:-1, u:2/3 x3, d:-1/3 x3,
       dbar:1/3 x3, ubar:-2/3 x3, e+:1, nubar:0 }. Every ingredient is
       design-theoretic: I3 from the Z/3 rung (quaternions), B-L from the Z/7 rung
       (pencil number operator).
  (H1) G2 = Fix(triality); GAUGE UNIVERSALITY ACROSS GENERATIONS. Diagonal triples
       (P,P,P) are related iff P is an octonion automorphism: verified positively for
       the Singer and doubling automorphisms, negatively for a random rotation. Hence
       the diagonal G2 (and its color SU(3) = Stab(apex)) acts by the SAME matrices
       in all three triality slots, so each slot carries the identical color
       decomposition 1 + 3 + 3bar + 1. Three slots = three identical color-generations;
       the generation-independence of gauge couplings = triality-invariance of the
       gauge sector.
  (H2) THE KOIDE LADDER IS A FUNCTION ON THE TRIALITY ORBIT. The UGP/Koide
       charged-lepton parametrization
           sqrt(m_k) = A (1 + sqrt2 * Re(z * w^k)),  w = e^{2 pi i/3},  z = e^{i delta}
       is manifestly a real function on the Z3-torsor {1, w, w^2} -- which
       positive_triality_theorems.py identifies with the triality orbit {V, S+, S-}.
       Verified numerically on PDG masses: the parametrization reconstructs (m_e, m_mu,
       m_tau) exactly; the fitted delta agrees with koideThetaUGP = 2/9 (deviation
       reported); Koide Q = 2/3 to ~1e-5 (the 45-degree statement of KoideClosedForm).
       Covariance: mu3 (generation cycling) acts as w^k -> w^{k+1}; U (mu-tau
       exchange) acts as complex conjugation z -> zbar, fixing gen 1 and swapping
       gens 2,3 -- i.e. fixing V and swapping S+ <-> S-. The mass ladder's symmetric
       point delta = 0 is the spinor-swap-symmetric configuration; delta = 2/9
       measures the dynamical breaking of the spinor swap. gen1 sits at V, per the
       rigidity theorem (P7 in positive_triality_theorems.py).
  (H3) THE SEED ARITHMETIC LIVES IN THE FLAVOR RING. The Frobenius chain of
       FrobeniusChain.lean is exactly the Eisenstein norm ladder:
       7 = N(3 + w), 73 = N(9 + w), 703 = N(27 + w) = 19 x 37 (composite: tower
       stops), with N the Z[omega] norm -- the SAME ring Z[omega] whose unit group
       mu3 is the generation cycling. Honest negative: b_gen2 = 42 and b_gen3 = 275
       are NOT Eisenstein norms (each has a prime = 2 mod 3 to an odd power), so the
       Eisenstein structure certifies the CHAIN and the FLAVOR GROUP, not the
       individual gen-2/3 seeds.
"""

import itertools
import numpy as np
from fractions import Fraction

TOL = 1e-10

# ---------- octonion + quaternion tables (apex-0 / standard) -------------
MUL = {}
for t in range(7):
    a, b, c = t % 7, (t+1) % 7, (t+3) % 7
    for (x, y, z) in [(a,b,c),(b,c,a),(c,a,b)]:
        MUL[(x,y)] = (z,+1); MUL[(y,x)] = (z,-1)
E8 = np.eye(8)
def omul_vec(x, y):
    z = np.zeros(8); z[7] = x[7]*y[7]
    for i in range(7):
        z[7] -= x[i]*y[i]; z[i] += x[7]*y[i] + x[i]*y[7]
    for i in range(7):
        if x[i] == 0: continue
        for j in range(7):
            if i == j or y[j] == 0: continue
            k, s = MUL[(i,j)]
            z[k] += s*x[i]*y[j]
    return z
def OL(i):
    return np.column_stack([omul_vec(E8[:,i], E8[:,j]) for j in range(8)])

QMUL = {}
for t in range(3):
    a, b, c = t % 3, (t+1) % 3, (t+2) % 3
    for (x, y, z) in [(a,b,c),(b,c,a),(c,a,b)]:
        QMUL[(x,y)] = (z,+1); QMUL[(y,x)] = (z,-1)
def QLmat(i):
    M = np.zeros((4,4)); M[i,3]=1.0; M[3,i]=-1.0
    for j in range(3):
        if j==i: continue
        k,s = QMUL[(i,j)]; M[k,j]=s
    return M
def QRmat(i):
    M = np.zeros((4,4)); M[i,3]=1.0; M[3,i]=-1.0
    for j in range(3):
        if j==i: continue
        k,s = QMUL[(j,i)]; M[k,j]=s
    return M

# =========================================================================
# (O1) electroweak charge closure
# =========================================================================
# chiral ideal of C (x) H: eigenspace of R_k (k = e_2) with eigenvalue -i
Rk = QRmat(2); Lk = QLmat(2); L0, L1 = QLmat(0), QLmat(1)
w_r, V_r = np.linalg.eig(Rk.astype(complex))
sel = [i for i in range(4) if np.allclose(w_r[i], -1j, atol=1e-9)]
assert len(sel) == 2
Pcols = V_r[:, sel]                                  # basis of the chiral ideal
def restrict(M):
    return np.linalg.pinv(Pcols) @ M @ Pcols
I3 = restrict(-0.5j * Lk)
Ip = restrict(-0.5j * L0); Iq = restrict(-0.5j * L1)
comm = Ip @ Iq - Iq @ Ip
assert np.allclose(comm, 1j * I3, atol=1e-8) or np.allclose(comm, -1j * I3, atol=1e-8)
i3ev = np.round(np.linalg.eigvals(I3).real, 9)
assert sorted(i3ev) == [-0.5, 0.5]
print("[O1a] chiral ideal of C(x)H: left multiplications restrict to the")
print("      spin-1/2 rep, I3 spectrum {+1/2, -1/2} (derived, not postulated): OK")

Lo = {i: OL(i) for i in range(7)}
pairs7 = [(1,3),(2,6),(4,5)]
alpha = [0.5*(-Lo[a] + 1j*Lo[b]) for (a,b) in pairs7]
Noct = sum(A.conj().T @ A for A in alpha)
BL_half = (2*Noct - 3*np.eye(8)) / 6                 # (B-L)/2

Qop = np.kron(I3, np.eye(8)) + np.kron(np.eye(2), BL_half)
qev = np.round(np.linalg.eigvals(Qop).real, 6)
from collections import Counter
spec = Counter(qev)
sm_left = Counter({round(0,6):2, round(-1,6):1, round(1,6):1,
                   round(2/3,6):3, round(-1/3,6):3,
                   round(1/3,6):3, round(-2/3,6):3})
print(f"[O1b] Q = I3 + (B-L)/2 spectrum on the 16-dim chiral sector:")
for v in sorted(spec): print(f"        Q = {v:+.4f}  x {spec[v]}")
assert spec == sm_left, (spec, sm_left)
print("      = { nu, e-, u x3, d x3 } + conjugates: the EXACT one-generation")
print("      left-chiral SM charge multiset. I3 from the Z/3 rung, B-L from")
print("      the Z/7 pencil: the electroweak charge formula is design-theoretic.")

# =========================================================================
# (H1) G2 = Fix(triality); identical color content per slot
# =========================================================================
def related(A, B, C, tol=1e-8):
    for a in range(8):
        for b in range(8):
            if np.max(np.abs(A @ omul_vec(E8[:,a], E8[:,b])
                             - omul_vec(B @ E8[:,a], C @ E8[:,b]))) > tol:
                return False
    return True
sigma_p = [(x+1) % 7 for x in range(7)]
mu_p    = [(2*x) % 7 for x in range(7)]
def perm8(p):
    P = np.zeros((8,8)); P[7,7] = 1.0
    for x in range(7): P[p[x], x] = 1.0
    return P
Ps, Pm = perm8(sigma_p), perm8(mu_p)
assert related(Ps, Ps, Ps) and related(Pm, Pm, Pm)
# a generic rotation is NOT diagonally related
th = 0.3
Rrot = np.eye(8); Rrot[0,0]=np.cos(th); Rrot[7,7]=np.cos(th)
Rrot[0,7]=-np.sin(th); Rrot[7,0]=np.sin(th)
assert not related(Rrot, Rrot, Rrot)
print("[H1] diagonal triples (P,P,P) related for the Singer and doubling")
print("     automorphisms; NOT related for a generic rotation:")
print("     G2 = Fix(triality). The diagonal G2 (and SU(3) = Stab(apex))")
print("     acts by identical matrices in all three slots => every slot")
print("     carries the same color content 1+3+3bar+1 (furey_cl6_comparison.py):")
print("     three identical color-generations; generation-universality of")
print("     the gauge couplings = triality-invariance of the gauge sector.")

# =========================================================================
# (H2) the Koide ladder as a function on the triality orbit
# =========================================================================
m = np.array([0.51099895e-3, 105.6583755e-3, 1776.86e-3])   # GeV (PDG)
r = np.sqrt(m)
Qk = m.sum() / r.sum()**2
print(f"[H2a] Koide Q = {Qk:.7f} (2/3 = {2/3:.7f}; deviation {abs(Qk-2/3):.2e})")
A = r.mean()
wc = np.exp(2j*np.pi/3)
resid = r/A - 1.0
zbar_comp = (resid @ np.array([wc**(-k) for k in range(3)])) * (2/3) / np.sqrt(2)
z = np.conj(zbar_comp)
recon = A * (1 + np.sqrt(2)*np.real(np.conj(z) * np.array([wc**k for k in range(3)])))
# orientation bookkeeping: accept either conjugation convention
if not np.allclose(recon, r, atol=1e-12):
    z = zbar_comp
    recon = A * (1 + np.sqrt(2)*np.real(np.conj(z) * np.array([wc**k for k in range(3)])))
assert np.allclose(recon, r, atol=1e-10), (recon, r)
delta = np.angle(z); modz = np.abs(z)
fold = delta % (2*np.pi/3)
if fold > np.pi/3: fold -= 2*np.pi/3
print(f"[H2b] sqrt(m_k) = A(1 + sqrt2 |z| cos(delta - 2 pi k/3)) reconstructs the")
print(f"      PDG ladder exactly; |z| = {modz:.6f} (Koide <=> |z| = 1;")
print(f"      dev {abs(modz-1):.1e}); raw delta = {delta:.6f} rad;")
print(f"      torsor-invariant angle |delta mod 2pi/3| = {abs(fold):.9f} rad")
print(f"      UGP koideThetaUGP = 2/9 = {2/9:.9f}; deviation = {abs(abs(fold)-2/9):.2e}")
print(f"      (the mod-2pi/3 and sign ambiguities ARE the Z3-torsor basepoint")
print(f"       and conjugation freedoms of the Interface Theorem: the Koide")
print(f"       angle is well-defined exactly on the triality orbit.)")
assert abs(abs(fold) - 2/9) < 1e-4
# covariance: conjugation z -> zbar swaps the k=1,2 values, fixes k=0
recon_conj = A * (1 + np.sqrt(2)*np.real(np.conj(np.conj(z)) *
                                          np.array([wc**k for k in range(3)])))
assert np.allclose(recon_conj[0], recon[0], atol=1e-12)
assert np.allclose(sorted(recon_conj[1:]), sorted(recon[1:]), atol=1e-12)
assert np.allclose(recon_conj[1], recon[2], atol=1e-12)
print("[H2c] U-covariance verified: z -> zbar fixes gen1 and swaps gen2 <-> gen3")
print("      -- i.e. fixes V and swaps S+ <-> S- under the Interface Theorem.")
print("      The sqrt-mass ladder is a real function on the Z3-torsor {w^k}")
print("      = the triality orbit {V, S+, S-}; delta = 2/9 is the dynamical")
print("      breaking of the spinor swap; gen1 occupies V (rigidity, P7).")

# =========================================================================
# (H3) the seed arithmetic lives in Z[omega]
# =========================================================================
def eis_norm(a, b):     # N(a + b w) = a^2 - a b + b^2
    return a*a - a*b + b*b
chain = [(3,1), (9,1), (27,1)]
vals = [eis_norm(a,b) for (a,b) in chain]
print(f"[H3a] Eisenstein norm ladder: N(3+w), N(9+w), N(27+w) = {vals}")
assert vals == [7, 73, 703] and 703 == 19*37
print("      = the FrobeniusChain tower {7, 73, 703 = 19x37 (stop)};")
print("      b_gen1 = 73 = N(9 + w): the seed ring IS the flavor ring Z[w].")
def is_eis_norm(n):
    for a in range(-60, 61):
        for b in range(-60, 61):
            if eis_norm(a,b) == n: return True
    return False
print(f"[H3b] honesty check: b_gen2 = 42 Eisenstein norm? {is_eis_norm(42)}; "
      f"b_gen3 = 275? {is_eis_norm(275)}")
assert not is_eis_norm(42) and not is_eis_norm(275)
print("      (42 = 2*3*7 and 275 = 5^2*11 each contain a prime = 2 mod 3 to an")
print("      odd power.) The Eisenstein structure certifies the chain and the")
print("      flavor group -- not the individual gen-2/3 seeds. Reported as is.")

print("\nDynamical housing closure: the per-generation UGP quantity (Koide sqrt-mass")
print("ladder, delta = 2/9) is a function on the triality orbit; slots carry identical")
print("one-generation color content (H1); the electroweak charge spectrum per")
print("chiral sector is exact (O1). Frontier beyond finite mathematics: the")
print("Lagrangian-level assignment of Phi_MDL fermion fields to the three")
print("related-triple slots.")
