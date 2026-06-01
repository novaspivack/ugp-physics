# neutrino_canonical.py
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import argparse
import json
import csv
import os

# ---- Small data holder (mirrors your Triple / GTETriple shape) ----
@dataclass
class NTriple:
    a: int
    b: int
    c: int
    gen: int
    name: str = "neutrino"

# ---- Minimal number theory (copied pattern from UGP v2, trimmed) ----
def mobius(n: int) -> int:
    n = abs(n)
    if n == 0: return 0
    if n == 1: return 1
    m = n
    f: Dict[int,int] = {}
    d = 2
    while d * d <= m:
        while m % d == 0:
            f[d] = f.get(d, 0) + 1
            m //= d
        d += 1 if d == 2 else 2
    if m > 1: f[m] = f.get(m, 0) + 1
    for e in f.values():
        if e >= 2: return 0
    return -1 if (len(f) % 2 == 1) else 1

def is_probable_prime(n: int) -> bool:
    if n < 2: return False
    small = (2,3,5,7,11,13,17,19,23,29,31,37)
    if n in small: return True
    if any(n % p == 0 for p in small): return False
    # Miller–Rabin for 64-bit safety
    d = n - 1; s = 0
    while d % 2 == 0: d //= 2; s += 1
    for a in (2,3,5,7,11,13,17):
        if a >= n: continue
        x = pow(a, d, n)
        if x == 1 or x == n-1: continue
        for _ in range(s-1):
            x = (x * x) % n
            if x == n-1: break
        else:
            return False
    return True

def divisors(n: int) -> List[int]:
    if n <= 0: return []
    r = int(math.isqrt(n))
    out = []
    for i in range(1, r+1):
        if n % i == 0:
            out.append(i)
            j = n // i
            if j != i: out.append(j)
    return sorted(out)

def ridge_value(n: int) -> int:
    return (1 << n) - 16

def enumerate_prime_locked_seeds(n: int) -> List[Dict[str,int]]:
    """
    Matches the UGP v2 prime-lock construction:
      R = 2^n - 16
      pick b2 | R with b2 > 15
      q2 = R / b2
      b1 = b2 + q2 + 7
      q1 = q2 - 13
      c1 = b1*q1 + 20   (must be prime for 'prime-locked')
    """
    R = ridge_value(n)
    out = []
    for b2 in divisors(R):
        if b2 <= 15: continue
        q2 = R // b2
        b1 = b2 + q2 + 7
        q1 = q2 - 13
        c1 = b1 * q1 + 20
        out.append({
            "n": n, "R": R,
            "b2": b2, "q2": q2, "b1": b1, "q1": q1,
            "c1": c1, "c1_is_prime": is_probable_prime(c1)
        })
    return out

def choose_canonical_seed(seeds: List[Dict[str,int]]) -> Optional[Dict[str,int]]:
    primed = [s for s in seeds if s["c1_is_prime"]]
    if not primed: return None
    primed.sort(key=lambda s: (s["b1"], s["b2"], s["q2"]))
    return primed[0]

def find_mirror(seeds: List[Dict[str,int]], canon: Dict[str,int]) -> Optional[Dict[str,int]]:
    idx = {(s["b2"], s["q2"]): s for s in seeds}
    key = (canon["q2"], canon["b2"])
    m = idx.get(key)
    if m and m["c1_is_prime"]:
        return m
    return None

def mirror_invariant_c(n: int) -> Tuple[int, Optional[Tuple[int,int]]]:
    """
    Return c_anchor and (c_primary, c_mirror) (if mirror exists).
    """
    seeds = enumerate_prime_locked_seeds(n)
    canon = choose_canonical_seed(seeds)
    if not canon:
        raise ValueError(f"No prime-locked seed at n={n}.")
    mir = find_mirror(seeds, canon)
    if mir:
        c_anchor = min(canon["c1"], mir["c1"])
        return c_anchor, (canon["c1"], mir["c1"])
    return canon["c1"], None

# ---- Universal law (CR1 coefficients, same as verifiers) ----
CR1 = {
    "const": 0.46628393930689865,
    "L":    -0.11840028502574501,
    "L2":    0.015298276550094339,
    "gen":  -1.3311566280619973,
    "gen2":  0.20254057938869213,
    "M":    -0.26443985830013417,
    "mu_a": -0.48403462203073427,
    "mu_b": -0.92493933577666199,
    "mu_c": -0.10926515575407812,
}

def solve_L_for_target(target: float, gen: int, mu_a: int, mu_b: int, mu_c: int) -> List[float]:
    """
    Solve for L given target Cf using CR1:
      log Cf = k0 + k1 L + k2 L^2 + kg gen + kg2 gen^2 + kM M + ka mu_a + kb mu_b + kc mu_c
    """
    Mprod = mu_a * mu_b * mu_c
    k0 = (CR1["const"] + CR1["gen"]*gen + CR1["gen2"]*(gen*gen) +
          CR1["M"]*Mprod + CR1["mu_a"]*mu_a + CR1["mu_b"]*mu_b + CR1["mu_c"]*mu_c)
    rhs = math.log(target) - k0
    a = CR1["L2"]; b = CR1["L"]; c = -rhs
    disc = b*b - 4*a*c
    if disc < 0:
        return []
    s = math.sqrt(disc)
    # two roots
    L1 = (-b + s) / (2*a)
    L2 = (-b - s) / (2*a)
    return [L1, L2]

def nearest_squarefree_with_mobius(start: int, mu_b_target: int, search: int = 10000) -> int:
    """
    Search around |start| for a square-free integer whose mobius equals mu_b_target.
    """
    if start == 0: start = 1
    # search increasing radius
    for radius in range(0, search+1):
        for cand in (start - radius, start + radius) if radius else (start,):
            if cand == 0: continue
            if mobius(cand) == mu_b_target:
                return cand
    raise RuntimeError("No nearby square-free integer with required Möbius sign found.")

def build_neutrino_from_ugp(
    n: int = 10,
    target: float = 1.0000,
    mu_a: int = +1,
    mu_b: int = +1,
    mu_c: int = -1,
    gen: int = 1,
    a_val: int = 1,
    tolerance: float = 5e-3,
) -> Tuple[NTriple, Dict[str, object]]:
    """
    Deterministic neutrino constructor:
      1) UGP mirror-invariant c anchor at given n
      2) Solve CR1 quadratic for L with fixed (mu_a, mu_b, mu_c, gen) and target
      3) Choose the root whose |b| = |c|*exp(L) gives an integer b nearest to square-free with Möbius=mu_b
      4) Return triple and diagnostics (Cf, delta, chosen root)
    """
    c_anchor, _pair = mirror_invariant_c(n)
    roots = solve_L_for_target(target, gen, mu_a, mu_b, mu_c)
    if not roots:
        raise ValueError("No real L solves the target with given μ pattern.")
    # Evaluate both roots and pick the one that yields smaller |Δ| after snapping b
    best: Optional[Tuple[float, float, float, int, float]] = None
    for L in roots:
        b_real = math.exp(L) * abs(c_anchor)
        b_int = int(round(b_real))
        b_sqf = nearest_squarefree_with_mobius(b_int, mu_b)
        # Evaluate Cf with snapped b
        L_eff = math.log(abs(b_sqf) / abs(c_anchor))
        log_cf = (CR1["const"] + CR1["L"]*L_eff + CR1["L2"]*(L_eff*L_eff) +
                  CR1["gen"]*gen + CR1["gen2"]*(gen*gen) +
                  CR1["M"]*(mu_a*mu_b*mu_c) + CR1["mu_a"]*mu_a +
                  CR1["mu_b"]*mu_b + CR1["mu_c"]*mu_c)
        cf = math.exp(log_cf)
        delta = abs(cf - target)
        rec = (delta, cf, L, b_sqf, L_eff)
        if best is None or rec < best:
            best = rec
    
    if best is None:
        raise ValueError("No valid solution found for the given parameters.")
    
    delta, cf, L_chosen, b_sqf, L_eff = best
    triple = NTriple(a=a_val, b=b_sqf, c=c_anchor, gen=gen, name="neutrino")
    return triple, {
        "c_anchor": float(c_anchor),
        "L_chosen": L_chosen,
        "L_effective": L_eff,
        "Cf": cf,
        "delta": delta,
        "pass": (delta <= tolerance),
        "params": {
            "target": target, "tolerance": tolerance,
            "mu_a": mu_a, "mu_b": mu_b, "mu_c": mu_c, "gen": gen, "a": a_val,
        }
    }

# ---- Convenience: evaluate with UGP_GTE_SM_Verifier if present ----
def eval_with_verifier(triple: NTriple) -> Optional[Tuple[float, float]]:
    try:
        import UGP_GTE_SM_Verifier as M
    except Exception:
        return None
    cf = float(M.predict_cf([M.Triple(triple.a, triple.b, triple.c, triple.gen, triple.name)])[0])
    return cf, math.nan

# ============================
# CLI / Sweep utilities
# ============================

def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def _evaluate_cf_local(a: int, b: int, c: int, gen: int, mu_a: int, mu_b: int, mu_c: int) -> float:
    # Use local CR1 to evaluate Cf (so this helper is standalone)
    L_eff = math.log(abs(b)/abs(c))
    log_cf = (CR1["const"] + CR1["L"]*L_eff + CR1["L2"]*(L_eff*L_eff) +
              CR1["gen"]*gen + CR1["gen2"]*(gen*gen) +
              CR1["M"]*(mu_a*mu_b*mu_c) + CR1["mu_a"]*mu_a +
              CR1["mu_b"]*mu_b + CR1["mu_c"]*mu_c)
    return math.exp(log_cf)

def sweep_neutrino_atlas(n0: int, n1: int,
                         target: float = 1.0,
                         mu_a: int = +1, mu_b: int = +1, mu_c: int = -1,
                         gen: int = 1, a_val: int = 1,
                         tolerance: float = 5e-3,
                         out_dir: str = "./neutrino_out",
                         try_mu_grid: bool = False) -> Dict[str, object]:
    """
    Build a mini-atlas for neutrino construction across n in [n0, n1].
    If try_mu_grid=True, evaluates a small grid of μ-patterns and keeps the best per n.
    Writes JSON and CSV; returns the JSON object.
    """
    _ensure_dir(out_dir)
    rows = []
    results = []
    # small μ grid (complements Higgs): keep product M = -1 as baseline, but allow a tiny set
    mu_grid = [(+1,+1,-1)]
    if try_mu_grid:
        mu_grid = [
            (+1,+1,-1), (+1,-1,+1), (-1,+1,+1),  # M = -1
            (+1,-1,-1), (-1,+1,-1), (-1,-1,+1)   # M = +1 alternatives to probe
        ]
    for n in range(n0, n1+1):
        best = None
        best_info = None
        for (mua, mub, muc) in mu_grid:
            try:
                T, info = build_neutrino_from_ugp(
                    n=n, target=target, mu_a=mua, mu_b=mub, mu_c=muc,
                    gen=gen, a_val=a_val, tolerance=tolerance
                )
                rec = (info["delta"], T, info, (mua, mub, muc))
                if best is None or rec < best:
                    best = rec
            except Exception as e:
                # No prime-locked seeds or no real roots, record failure later
                continue
        if best is None:
            rows.append({
                "n": n, "status": "FAIL", "message": "no prime-locked seed or no solution",
                "a": None, "b": None, "c": None, "gen": None,
                "mu_a": None, "mu_b": None, "mu_c": None,
                "Cf": None, "delta": None, "pass": False
            })
            continue
        delta, T, info, (mua, mub, muc) = best
        rows.append({
            "n": n, "status": "OK",
            "a": T.a, "b": T.b, "c": T.c, "gen": T.gen,
            "mu_a": mua, "mu_b": mub, "mu_c": muc,
            "Cf": info["Cf"], "delta": info["delta"], "pass": info["pass"]
        })
        results.append({"n": n, "triple": T.__dict__, "info": info, "mu": {"a": mua, "b": mub, "c": muc}})
    # Write JSON
    json_path = os.path.join(out_dir, f"neutrino_atlas_{n0}_{n1}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"range": [n0, n1], "target": target, "tolerance": tolerance, "rows": rows}, f, indent=2)
    # Write CSV
    csv_path = os.path.join(out_dir, f"neutrino_atlas_{n0}_{n1}.csv")
    fieldnames = ["n","status","message","a","b","c","gen","mu_a","mu_b","mu_c","Cf","delta","pass"]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    # Console summary (first 10)
    print("\nNeutrino mini-atlas")
    print("-"*72)
    for r in rows[:10]:
        if r["status"] == "OK":
            print(f"n={r['n']:>2}  ν=({r['a']},{r['b']},{r['c']},{r['gen']})  μ=({r['mu_a']:+d},{r['mu_b']:+d},{r['mu_c']:+d})  Cf={r['Cf']:.6f}  Δ={r['delta']:.6f}  PASS={r['pass']}")
        else:
            print(f"n={r['n']:>2}  FAIL  ({r['message']})")
    if len(rows) > 10:
        print(f"... ({len(rows)-10} more)")
    print(f"\nJSON: {json_path}\nCSV:  {csv_path}")
    return {"json": json_path, "csv": csv_path, "rows": rows}

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Deterministic neutrino constructor / sweep (UGP→GTE, CR1).")
    p.add_argument("--n", type=int, help="Single n to construct neutrino for.")
    p.add_argument("--atlas", nargs=2, type=int, metavar=("N0","N1"), help="Run neutrino mini-atlas sweep over [N0, N1].")
    p.add_argument("--target", type=float, default=1.0, help="Neutrino target scalar (default 1.0000).")
    p.add_argument("--tol", type=float, default=5e-3, help="Tolerance for pass/fail (default 0.005).")
    p.add_argument("--mu-a", dest="mu_a", type=int, default=+1, choices=[-1,0,1], help="Möbius sign for a (default +1).")
    p.add_argument("--mu-b", dest="mu_b", type=int, default=+1, choices=[-1,0,1], help="Möbius sign for b (default +1).")
    p.add_argument("--mu-c", dest="mu_c", type=int, default=-1, choices=[-1,0,1], help="Möbius sign for c (default -1).")
    p.add_argument("--gen", type=int, default=1, help="Generation index g (default 1).")
    p.add_argument("--aval", type=int, default=1, help="Value for a in the triple (default 1).")
    p.add_argument("--out", type=str, default="./neutrino_out", help="Output directory for atlas files.")
    p.add_argument("--mu-grid", action="store_true", help="Try a small grid of μ patterns and keep the best per n.")
    return p.parse_args()

if __name__ == "__main__":
    ns = parse_args()
    if ns.atlas:
        n0, n1 = ns.atlas
        sweep_neutrino_atlas(n0, n1,
                             target=ns.target, mu_a=ns.mu_a, mu_b=ns.mu_b, mu_c=ns.mu_c,
                             gen=ns.gen, a_val=ns.aval, tolerance=ns.tol,
                             out_dir=ns.out, try_mu_grid=ns.mu_grid)
    else:
        # Single n (default to 10 if not provided)
        n = ns.n if ns.n is not None else 10
        T, info = build_neutrino_from_ugp(n=n, target=ns.target, mu_a=ns.mu_a, mu_b=ns.mu_b, mu_c=ns.mu_c,
                                          gen=ns.gen, a_val=ns.aval, tolerance=ns.tol)
        print(f"n={n}  ν=({T.a},{T.b},{T.c},{T.gen})  Cf={info['Cf']:.6f}  Δ={info['delta']:.6f}  PASS={info['pass']}")
        try:
            m = eval_with_verifier(T)
            if m:
                print(f"UGP_GTE_SM_Verifier Cf = {m[0]:.6f}")
        except Exception:
            pass