
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Constraint solver & verifier for the Elegant Kernel palette.

Implements:
  - Quarter-Lock plane: k_M = k_gen2 + (1/4) k_L2
  - Fixed algebraic constants from FPSM:
        k_L2 = 7/512, k_gen2 = -phi/2, k_gen = pi/2, (k_a,k_b,k_c)=(1/8,-3/2,4/3)
  - Derived linear terms (FPSM reparametrization):
        k_L = -2*k_L2*(-3/2*log(phi)),
        k_const = -1/(2*pi) + k_L2*(-3/2*log(phi))**2
  - Mobius invariants L = log(|b|/|c|), M = mu(a)mu(b)mu(c), g in {1,2,3}
  - Cf = exp( k_const + k_L L + k_L2 L^2 + k_gen g + k_gen2 g^2 + k_M M + k_a mu(a) + k_b mu(b) + k_c mu(c) )
  - Verifies QL orthogonality with n = (-1/4, -1, 1) dot (k_L2, k_gen2, k_M) = 0

Also includes a small catalogue of canonical triples (FPSM sec. 4.7) for quick checks.

References:
  - FPSM, sec. 4.7 eqs. (10)-(13) (Quarter-Lock kernel & coefficients). 
  - MFRR, sec. 9.1-9.4 (Quarter-Lock preservation; PT-induced normal step).
"""
import math
from fractions import Fraction

# ---------- Constants & palette ----------

phi = (1 + 5**0.5)/2  # golden ratio
logphi = math.log(phi)

# Exact rationals where possible
k_L2   = Fraction(7, 512)            # 7/512
k_gen2 = -phi/2.0                    # -phi/2  (irrational)
k_gen  = math.pi/2.0                 # pi/2
k_a, k_b, k_c = Fraction(1,8), Fraction(-3,2), Fraction(4,3)

# FPSM reparam (Sec. 4.7 eq. 12-13)
k_L    = float(-2.0*float(k_L2) * (-1.5*logphi))  # = 3 * k_L2 * logphi
k_M    = float(k_gen2 + 0.25*float(k_L2))
k_const= float(-1.0/(2.0*math.pi) + float(k_L2) * (-1.5*logphi)**2)

# Quarter-Lock plane normal n for (k_L2, k_gen2, k_M)
n = (-0.25, -1.0, 1.0)

def dot_n(kL2, kgen2, kM):
    return n[0]*kL2 + n[1]*kgen2 + n[2]*kM

# ---------- Mobius function ----------
def mobius(n_val:int) -> int:
    """Return Mobius mu(n)."""
    if n_val == 0:
        raise ValueError("mu(0) undefined")
    x, p, cnt = abs(n_val), 2, 0
    while p*p <= x:
        if x % p == 0:
            x //= p
            cnt += 1
            if x % p == 0:
                return 0
            while x % p == 0:
                x //= p
        p += 1 if p == 2 else 2
    if x > 1:
        cnt += 1
    return -1 if (cnt % 2 == 1) else 1

def invariants(a:int,b:int,c:int,g:int):
    L = math.log(abs(b)/abs(c))
    M = mobius(a)*mobius(b)*mobius(c)
    return L, M, g

def cf_log(L,M,g, mu_a, mu_b, mu_c):
    """Return log Cf per FPSM eq. (10)-(13)."""
    L2 = L*L
    out = (
        k_const
      + k_L*L
      + float(k_L2)*L2
      + k_gen*float(g)
      + k_gen2*(g*g)
      + k_M*float(M)
      + float(k_a)*mu_a + float(k_b)*mu_b + float(k_c)*mu_c
    )
    return out

def cf_value(a:int,b:int,c:int,g:int, add_urc:float=0.0):
    L, M, g = invariants(a,b,c,g)
    mu_a, mu_b, mu_c = mobius(a), mobius(b), mobius(c)
    lc = cf_log(L,M,g, mu_a, mu_b, mu_c) + float(add_urc)
    return math.exp(lc), lc

# ---------- Canonical triples (FPSM sec. 4.7 Table 10) ----------
canon = {
    "electron": (1, 73, 823, 1),
    "muon":     (9, 42, 1023, 2),
    "tau":      (5, 275, 65535, 3),
}

# URC delta (from lab audit; adjust as needed)
URC_DELTA_LOGCF = 0.0528893151

def main():
    # QL orthogonality check
    ndk = dot_n(float(k_L2), float(k_gen2), float(k_M))
    print(f"[QL] n·k = {ndk:+.12e} (should be ~ 0)")
    print(f"[Palette] k_L2={float(k_L2):.12f}, k_gen2={k_gen2:.12f}, k_M={k_M:.12f}")
    print(f"[Palette] k_L={k_L:.12f}, k_const={k_const:.12f}, k_gen={k_gen:.12f}, (ka,kb,kc)=({float(k_a):.6f},{float(k_b):.6f},{float(k_c):.6f})")

    # Evaluate Cf for canonical leptons (with & without URC)
    for name, (a,b,c,g) in canon.items():
        cf_base, lbase = cf_value(a,b,c,g, add_urc=0.0)
        cf_urc, lurc = cf_value(a,b,c,g, add_urc=URC_DELTA_LOGCF)
        print(f"\n[{name}] (a,b,c;g)=({a},{b},{c};{g})")
        print(f"  log Cf (base) = {lbase:+.9f}  =>  Cf_base = {cf_base:.9f}")
        print(f"  log Cf (+URC) = {lurc:+.9f}  =>  Cf_URC  = {cf_urc:.9f}")

if __name__ == '__main__':
    main()
