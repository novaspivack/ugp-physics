"""
ugp_core.py
-----------
Shared constants, formulas, and utility functions for the UGP investigation.

All constants are derived from the UGP framework as described in:
  - P01: A Deterministic Number-Theoretic Framework for the SM Parameter Spectrum
  - P06: Algebraic and Geometric Foundations of the UGP
  - P12: The Unified Rigidity Theorem
  - MFRR: Mathematical Foundations of Reflexive Reality
"""

import math
from fractions import Fraction

# ── Fundamental UGP structural integers ────────────────────────────────────
Nc = 3          # QCD colour rank (forced by anomaly cancellation)
delta = 7       # Mirror offset: Nc + (Nc^2 - 1)/2
n_ridge = 10    # Ridge level (unique MDL-minimal solution)
strand_count = (Nc**2 - 1) // 4   # = 2, from Braid Atlas

# ── Elegant Kernel constants (Lean-certified) ───────────────────────────────
PHI = (1 + math.sqrt(5)) / 2      # Golden ratio
K_L2 = Fraction(7, 512)           # Geometric curvature: 7/512
K_GEN2_exact = -PHI / 2           # Generational curvature: -φ/2
K_GEN2 = float(K_L2) * 0         # placeholder
K_GEN2 = -PHI / 2

# Quarter-Lock identity: k_M = k_gen2 + (1/4)*k_L2
# This is the fundamental algebraic constraint of UGP
K_M = K_GEN2 + 0.25 * float(K_L2)

# ── δ_UGP formula (Lean-authoritative) ─────────────────────────────────────
# Quarter-Lock algebraic prefactor; UgpLean/Phase4/DeltaUGP.lean line 35:
#   δ_UGP(b1) = (1/b1) * ( -1/(k_gen2 + (1/4)*k_L2)  +  (7/4)*(k_L2/k_gen2) )
C_ALGEBRAIC = (
    (-1.0) / (K_GEN2 + 0.25 * float(K_L2))
    + 1.75 * (float(K_L2) / K_GEN2)
)

# δ_target: non-circularly derived from CODATA α_EM via the TE1.P bridge.
# Canonical record: uniqueness/canonical_run/delta_noncircular.json
#   prefactor_C        = 1.2117384335607098    (= C_ALGEBRAIC, matches Lean)
#   derived_δ_codata   = 0.016599116952229796  (TE1.P-back-extracted value)
#   b1_required_exact  = 73.00017447           (= C/δ_target)
# Residual (b1_req − 73)/73 = 2.39 ppm — the TE1.P deviation cited in P01 §5.5
# and characterized in P25 §9.8.
DELTA_TARGET = 0.016599116952229796

# b1_required: the unique b1 satisfying δ_UGP(b1) = δ_target.
# Equals 73.00017447 — within 2.39 ppm of the sieve-forced integer 73.
B1_REQUIRED = C_ALGEBRAIC / DELTA_TARGET

# ── Lean-certified bare gauge couplings ─────────────────────────────────────
G1_SQ = Fraction(16, 125)                          # U(1) hypercharge
G2_SQ = Fraction(2329, 5400)                       # SU(2) weak isospin
G3_SQ = Fraction((13 * 17 * 29)**2, 27648000)      # SU(3) colour

# ── Fibonacci sequence ───────────────────────────────────────────────────────
def fibonacci(n):
    a, b = 1, 1
    for _ in range(n - 1):
        a, b = b, a + b
    return a

FIB = [fibonacci(i) for i in range(1, 15)]
# FIB[10] = F_11 = 89

# ── Primality test ───────────────────────────────────────────────────────────
def is_prime(n):
    """Miller-Rabin style deterministic primality for n < 3.2e18."""
    if n < 2: return False
    if n < 4: return True
    if n % 2 == 0 or n % 3 == 0: return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True

def get_divisors(n_val):
    """Return all divisors of n_val using sympy factorization (fast for all sizes)."""
    try:
        from sympy import factorint
        factors = factorint(n_val)
    except ImportError:
        # Fallback: trial division (slow for large n_val)
        factors = {}
        d = 2
        temp = n_val
        while d * d <= temp:
            while temp % d == 0:
                factors[d] = factors.get(d, 0) + 1
                temp //= d
            d += 1
        if temp > 1:
            factors[temp] = factors.get(temp, 0) + 1

    # Enumerate all divisors from prime factorization
    divisors = [1]
    for p, e in factors.items():
        divisors = [d * p**i for d in divisors for i in range(e + 1)]
    return sorted(divisors)


# ── Ridge sieve (Stage 1) ────────────────────────────────────────────────────
def ridge_sieve(n):
    """
    Stage-1 arithmetic admissibility sieve at ridge level n.

    Uses sympy factorization to enumerate divisors efficiently — fast even
    for n=60 where R_n = 2^60 - 16 ~ 10^18 (trial division would be O(10^9)).

    Returns list of dicts with keys: n, R, b2, q2, b1, q1, c1
    """
    R = 2**n - 16
    if R <= 0:
        return []
    survivors = []
    seen = set()
    for b2 in get_divisors(R):
        if b2 <= 15:
            continue
        q2 = R // b2
        if q2 <= 15:
            continue
        for (bb2, qq2) in [(b2, q2), (q2, b2)]:
            key = (bb2, qq2)
            if key in seen:
                continue
            seen.add(key)
            b1 = bb2 + qq2 + 7
            q1 = bb2 - 13
            if q1 > 0:
                c1 = b1 * q1 + 20
                if is_prime(c1):
                    survivors.append({
                        'n': n, 'R': R,
                        'b2': bb2, 'q2': qq2,
                        'b1': b1, 'q1': q1, 'c1': c1
                    })
    return survivors

# ── δ-match filter (Stage 2) ─────────────────────────────────────────────────
def delta_UGP(b1):
    """Compute δ_UGP(b1) = C_algebraic / b1."""
    return C_ALGEBRAIC / b1

def delta_match(survivors, tol=1e-5):
    """
    Stage-2 physical viability filter.
    Returns survivors annotated with delta, rel_err, passes.
    """
    results = []
    for s in survivors:
        d = delta_UGP(s['b1'])
        err = abs(d - DELTA_TARGET) / DELTA_TARGET
        results.append({**s, 'delta': d, 'rel_err': err, 'passes': err < tol})
    return results

# ── WZW data ─────────────────────────────────────────────────────────────────
WZW_FACTORS = [
    {'name': 'SU(2)_8',  'level': 8,  'meaning': 'dim(adj SU(Nc)) = Nc^2-1',
     'c': Fraction(12, 5), 'primaries': 9},
    {'name': 'SU(3)_3',  'level': 3,  'meaning': 'Nc (diagonal level)',
     'c': Fraction(4, 1),  'primaries': 10},
    {'name': 'SU(2)_10', 'level': 10, 'meaning': 'n_ridge',
     'c': Fraction(5, 2),  'primaries': 11},
]

C_TOTAL = sum(f['c'] for f in WZW_FACTORS)   # = 89/10
TOTAL_PRIMARIES = 9 * 10 * 11                 # = 990

# ── Galois orbit data ─────────────────────────────────────────────────────────
GALOIS_CONSTANTS = [
    {
        'name': 'phi = (1+sqrt5)/2',
        'value': PHI,
        'min_poly': 'x^2 - x - 1',
        'degree': 2,
        'layer': 'Kernel (k_gen2)',
        'const_term': -1,
        'const_interp': 'trivial'
    },
    {
        'name': 'sqrt(3)',
        'value': math.sqrt(3),
        'min_poly': 'x^2 - 3',
        'degree': 2,
        'layer': 'TT/A2 Weyl',
        'const_term': -3,
        'const_interp': 'Nc (negated)'
    },
    {
        'name': '2*cos(pi/10)',
        'value': 2 * math.cos(math.pi / 10),
        'min_poly': 'x^4 - 5x^2 + 5',
        'degree': 4,
        'layer': 'Kernel (k_gen)',
        'const_term': 5,
        'const_interp': 'pentagon'
    },
    {
        'name': '2*cos(pi/12)',
        'value': 2 * math.cos(math.pi / 12),
        'min_poly': 'x^4 - 4x^2 + 1',
        'degree': 4,
        'layer': 'Koide cyclotomic-12',
        'const_term': 1,
        'const_interp': 'trivial'
    },
    {
        'name': '2*cos(pi/8)',
        'value': 2 * math.cos(math.pi / 8),
        'min_poly': 'x^4 - 4x^2 + 2',
        'degree': 4,
        'layer': 'TT offset beta',
        'const_term': 2,
        'const_interp': 'strand_count'
    },
    {
        'name': '2*cos(pi/6) = sqrt(3)',
        'value': 2 * math.cos(math.pi / 6),
        'min_poly': 'x^2 - 3',
        'degree': 2,
        'layer': 'A2/SU(3)_3',
        'const_term': -3,
        'const_interp': 'Nc (negated)'
    },
]

if __name__ == '__main__':
    print("UGP Core Constants")
    print("="*50)
    print(f"  Nc            = {Nc}")
    print(f"  delta         = {delta}")
    print(f"  n_ridge       = {n_ridge}")
    print(f"  strand_count  = {strand_count}")
    print(f"  phi           = {PHI:.10f}")
    print(f"  k_L2          = {float(K_L2):.10f}  (= 7/512)")
    print(f"  k_gen2        = {K_GEN2:.10f}  (= -phi/2)")
    print(f"  C_algebraic   = {C_ALGEBRAIC:.10f}")
    print(f"  delta_target  = {DELTA_TARGET:.10f}")
    print(f"  b1_required   = {B1_REQUIRED:.6f}")
    print(f"  g1^2          = {G1_SQ}  = {float(G1_SQ):.6f}")
    print(f"  g2^2          = {G2_SQ}  = {float(G2_SQ):.6f}")
    print(f"  g3^2          = {G3_SQ}  = {float(G3_SQ):.6f}")
    print(f"  c_total (WZW) = {C_TOTAL}  = {float(C_TOTAL):.4f}")
    print(f"  F_11          = {FIB[10]}")
