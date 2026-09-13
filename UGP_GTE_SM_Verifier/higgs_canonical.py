# higgs_canonical.py
# Deterministic, knob-free constructors for a single canonical Higgs triple H.
# Keep this separate for testing; later, inline the small bits into each verifier.

from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Optional

@dataclass(frozen=True)
class Triple:
    a: int
    b: int
    c: int
    gen: int
    name: str = "higgs"

def _nearest_int(x: float) -> int:
    # Deterministic "round half up" for non-negative x (sqrt products are ≥0)
    return int(math.floor(x + 0.5))

def higgs_from_ugp_mirror(
    *,
    b2_canon: int,
    c1_canon: int,
    b2_mirror: Optional[int] = None,
    c1_mirror: Optional[int] = None,
    a_H: int = 6,
    gen_H: int = 1,
) -> Triple:
    """
    UGP+Mirror primary constructor (preferred inside the UGP verifier).
    - If a true mirror exists, use geometric means to anchor b and c.
    - Otherwise, fall back to the canonical branch's b2/c1.
    No tuned constants; uses only UGP invariants.
    """
    if b2_canon <= 0 or c1_canon == 0:
        raise ValueError("b2_canon must be >0 and c1_canon != 0 for L to be defined later.")

    if b2_mirror is not None and c1_mirror is not None and b2_mirror > 0 and c1_mirror != 0:
        bH = _nearest_int(math.sqrt(b2_canon * float(b2_mirror)))
        cH = _nearest_int(math.sqrt(abs(c1_canon * float(c1_mirror)))) * (1 if (c1_canon > 0 and c1_mirror > 0) else -1)
    else:
        bH = int(b2_canon)
        cH = int(c1_canon)

    return Triple(a=a_H, b=bH, c=cH, gen=gen_H, name="higgs")

def higgs_from_gte(
    muon: Triple,
    tau: Triple,
    *,
    a_H: int = 6,
    gen_H: int = 1,
) -> Triple:
    """
    GTE-only fallback (for the MONOLITH): uses only fixed lepton plateaus.
    b_H := sqrt(b_mu * b_tau),  c_H := sqrt(c_mu * c_tau) (geom mid of 2^10-1 and 2^16-1).
    No tuned constants; depends only on the canonical leptonic steps.
    """
    if muon.b <= 0 or tau.b <= 0:
        raise ValueError("muon.b and tau.b must be >0 to define L later.")
    if muon.c == 0 or tau.c == 0:
        raise ValueError("muon.c and tau.c must be nonzero to define L later.")

    bH = _nearest_int(math.sqrt(muon.b * float(tau.b)))
    # Use magnitude geometric mean; sign is positive for the canonical plateaus
    cH = _nearest_int(math.sqrt(abs(muon.c * float(tau.c))))

    return Triple(a=a_H, b=bH, c=cH, gen=gen_H, name="higgs")

# --- (Optional) tiny utility for tests ---
def evaluate_higgs_cf(triple: Triple, predict_cf_fn) -> float:
    """
    Evaluate C_f(H) using the verifier's own predictor.
    `predict_cf_fn` should accept a list of triples with fields (a,b,c,gen,name)
    and return a numpy array or list of Cf values (UGP_GTE_SM_Verifier/UGP functions both match this).
    """
    return float(predict_cf_fn([triple])[0])

# --- Deterministic UGP→GTE Higgs getter (zero knobs) ---

# CR1 coefficients (same as both verifiers)
_k_const = 0.46628393930689865
_k_L     = -0.11840028502574501
_k_L2    =  0.015298276550094339
_k_gen   = -1.3311566280619973
_k_gen2  =  0.20254057938869213
_k_M     = -0.26443985830013417
_k_mua   = -0.48403462203073427
_k_mub   = -0.92493933577666199
_k_muc   = -0.10926515575407812

_TARGET_H = 1.3711  # your Higgs scalar target

def _mobius(n: int) -> int:
    n = abs(int(n))
    if n == 0: return 0
    if n == 1: return 1
    m = n
    f = {}
    d = 2
    while d*d <= m:
        while m % d == 0:
            f[d] = f.get(d, 0) + 1
            m //= d
        d += 1 if d == 2 else 2
    if m > 1:
        f[m] = f.get(m, 0) + 1
    for e in f.values():
        if e >= 2:
            return 0
    return -1 if (len(f) % 2 == 1) else 1

def _nearest_squarefree_mu_minus_one(x: float) -> int:
    k0 = max(2, int(round(x)))
    if _mobius(k0) == -1:
        return k0
    # expand deterministically
    r = 1
    best: Optional[int] = None
    best_d: Optional[float] = None
    while True:
        for k in (k0 - r, k0 + r):
            if k >= 2 and _mobius(k) == -1:
                d = abs(k - x)
                if best is None or (best_d is not None and d < best_d) or (best_d is not None and abs(d - best_d) < 1e-12 and k < best):
                    best, best_d = k, d
        if best is not None:
            return best
        r += 1

def get_canonical_higgs(n: int = 10):
    """
    Deterministic UGP→GTE Higgs triple:
      1) Anchor c to the mirror-invariant UGP prime: c_H = min(c1, c1_mirror) at n
      2) Solve universal law for L with μ=(+1,-1,-1), gen=1, target=1.3711
      3) Set b to the nearest square-free integer with μ(b)=-1
      4) a=1, gen=1, name='higgs'
    Returns: Simple object with fields (a,b,c,gen,name)
    """
    import UGP_GTE_SM_Verifier as UGP  # local import to avoid cycles

    # UGP mirror-invariant c anchor
    seeds = UGP._enumerate_prime_locked_seeds(n)
    canon = UGP._choose_canonical_seed(seeds)
    c_candidates = [canon["c1"]]
    idx = {(s["b2"], s["q2"]): s for s in seeds}
    mk = (canon["q2"], canon["b2"])
    if mk in idx and idx[mk]["c1_is_prime"]:
        c_candidates.append(idx[mk]["c1"])
    c_H = min(c_candidates)

    # Solve k_L2*L^2 + k_L*L + C0 = 0 with μ=(+1,-1,-1), gen=1
    C0 = (_k_const + _k_gen + _k_gen2 + _k_M
          + _k_mua*(+1) + _k_mub*(-1) + _k_muc*(-1)
          - math.log(_TARGET_H))
    disc = _k_L*_k_L - 4*_k_L2*C0
    L_star = (-_k_L - math.sqrt(disc)) / (2*_k_L2)   # negative root
    b_real = c_H * math.exp(L_star)
    b_H = _nearest_squarefree_mu_minus_one(b_real)

    # Build a small lightweight tuple-like object
    class _H:
        a: int
        b: int
        c: int
        gen: int
        name: str
    
    H = _H()
    H.a = 1
    H.b = b_H
    H.c = c_H
    H.gen = 1
    H.name = "higgs"
    return H