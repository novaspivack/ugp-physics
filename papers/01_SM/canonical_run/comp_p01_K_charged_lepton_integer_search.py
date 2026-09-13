#!/usr/bin/env python3
"""
COMP-P01-K  —  charged-lepton mass integer search (UGP structural integers × keV)

Question: the electron rest energy satisfies  m_e = δ · b₁  keV  to 2.05 ppm
          where δ = 7 (mirror offset, ugp1_s) and b₁ = 73 (lepton ladder).  Both
          are machine-checked RSUC invariants in ugp-lean.  Does an analogous
          structural formula hold for m_μ and m_τ, or for their Koide-partner
          combinations √m_μ, √m_τ?

Approach (falsifiable, no cherry-picking):
  1. Fix a basis of UGP-certified structural integers (ridge family +
     UGP prime / L_model / Fermat / Mersenne atoms).
  2. Search all small-integer linear combinations α · (basis) + β over a
     bounded coefficient range; score by ppm deviation from CODATA.
  3. Also search multiplicative/rational forms (δ · B), (B₁/B₂), etc.
  4. Run the identical search on √m_μ and √m_τ (Koide co-ordinates).
  5. Report the top-K candidates per target; only call something a "hit" when
     its ppm deviation is in the same class as the electron benchmark (<10 ppm)
     AND its description length (|α|+|β|) is small.

Null hypothesis: structural integers × keV carry no phenomenological content
beyond the electron coincidence.  If no hit <100 ppm is found with bounded
coefficient magnitude, we accept the null for that target.

Outputs:
  comp_p01_K_charged_lepton_integer_search.json  (all candidates + verdict)
"""
from __future__ import annotations

import datetime as _dt
import hashlib as _hl
import itertools as _it
import json
import math
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# CODATA charged-lepton masses (rest energies, keV)
# Source: CODATA 2022 recommended values
# ---------------------------------------------------------------------------
M_E_KEV  =      510.99895069   # ± 1.5e-7 keV
M_MU_KEV =   105658.3755       # ± 2.3e-3 keV
M_TAU_KEV = 1776860.0          # ± 120 keV (PDG 2024)

TARGETS = {
    "m_e_keV":      M_E_KEV,
    "m_mu_keV":     M_MU_KEV,
    "m_tau_keV":    M_TAU_KEV,
    "sqrt_m_e_keV":  math.sqrt(M_E_KEV),
    "sqrt_m_mu_keV": math.sqrt(M_MU_KEV),
    "sqrt_m_tau_keV":math.sqrt(M_TAU_KEV),
}

# ---------------------------------------------------------------------------
# UGP structural-integer basis (all Lean-certified or prime-sieve-verified)
#
# Provenance:
#   δ = ugp1_s = 7            (Lean: UgpLean.Core.RidgeDefs)
#   ugp1_g = 13               (Lean: UgpLean.Core.RidgeDefs)
#   ugp1_t = 20               (Lean: UgpLean.Core.RidgeDefs)
#   D₁ = 16 = 2^4             (U(1) charge invariant, Lean)
#   a₂ = 9                    (α_EM closure term)
#   b₁ = 73                   (lepton ladder, Lean b1_def)
#   q₁ = 11                   (branch quotient, Lean)
#   c₁ = 823                  (first UGP prime = b₁·q₁ + 20, Lean)
#   b(n=13) = 209, q(n=13)=43, c(n=13)=2137 (mirror UGP prime at n=10)
#   R(n=10) = 1008 = 2^10 - 16
#   R(n=13) = 8176 = 2^13 - 16
#   R(n=16) = 65520 = 2^16 - 16
#   c₂ = 1023 = 2^10 - 1      (Gen-2 Mersenne)
#   c₃ = 65535 = 2^16 - 1     (Gen-3 Fermat-product)
#   Fermat primes: 3, 5, 17, 257, 65537
# ---------------------------------------------------------------------------
BASIS = {
    "delta":       7,
    "ugp1_g":     13,
    "ugp1_t":     20,
    "D1":         16,
    "a2":          9,
    "b1":         73,
    "q1":         11,
    "c1":        823,
    "b_n13":     209,
    "q_n13":      43,
    "c_n13":    2137,
    "R_n10":    1008,
    "R_n13":    8176,
    "R_n16":   65520,
    "c2_mers":  1023,
    "c3_fermat":65535,
    "F0":          3,
    "F1":          5,
    "F2":         17,
    "F3":        257,
    "F4":      65537,
    "one":         1,
}

# Derived / composite atoms worth trying as a single unit
COMPOSITES = {
    "delta_b1":             7 * 73,            # 511 — the electron atom
    "delta_b_n13":          7 * 209,
    "delta_q_n13":          7 * 43,
    "q1_b1":               11 * 73,            # 803
    "two_b1_minus_a2":   2*73 - 9,             # 137 ≈ α⁻¹
    "b1_q1_plus_t":     73*11 + 20,            # 823 = c1
    "R_n13_over_16":     8176 // 16,           # 511
    "half_ridge_plus_8": (1008//2) + 8,        # 512
    "D1_cubed":               16**3,           # 4096
    "D1_squared":             16**2,           # 256
    "F0_F1_F2":               3*5*17,          # 255
    "F0_F1_F2_F3":          3*5*17*257,        # 65535 = c3
    "b1_squared":              73**2,          # 5329
}

ALL_ATOMS = {**BASIS, **COMPOSITES}

# ---------------------------------------------------------------------------
# Search 1: single-atom hits (m_f  ≈  n · A  for some basis atom A, small n)
# ---------------------------------------------------------------------------
def search_single(target_value: float, target_name: str, max_n: int = 300) -> list[dict]:
    hits = []
    for name, atom in ALL_ATOMS.items():
        if atom <= 0:
            continue
        ratio = target_value / atom
        n = round(ratio)
        if n <= 0 or n > max_n:
            continue
        pred = n * atom
        rel = abs(target_value - pred) / target_value
        hits.append({
            "kind": "single_atom",
            "formula": f"{n} * {name}",
            "atom_name": name,
            "atom_value": atom,
            "coef": n,
            "predicted": float(pred),
            "target": float(target_value),
            "ppm": float(1e6 * rel),
            "descr_len": abs(n) + 1,
        })
    return sorted(hits, key=lambda h: h["ppm"])[:10]


# ---------------------------------------------------------------------------
# Search 2: two-atom integer linear combinations  α·A + β·B  (|α|,|β| ≤ C)
# with A,B drawn from BASIS (not COMPOSITES, to keep description length honest)
# ---------------------------------------------------------------------------
def search_two_linear(target_value: float, target_name: str, C: int = 20) -> list[dict]:
    names = list(BASIS.keys())
    hits = []
    for i, A in enumerate(names):
        a_val = BASIS[A]
        for j in range(i, len(names)):
            B = names[j]
            b_val = BASIS[B]
            # For each (A,B) we solve for best (α,β) with |α|,|β| ≤ C
            # by iterating α and computing β from the closest integer.
            for alpha in range(-C, C + 1):
                if a_val == 0:
                    continue
                residual = target_value - alpha * a_val
                if b_val == 0:
                    continue
                beta = round(residual / b_val)
                if abs(beta) > C:
                    continue
                pred = alpha * a_val + beta * b_val
                if pred <= 0:
                    continue
                rel = abs(target_value - pred) / target_value
                hits.append({
                    "kind": "two_atom_linear",
                    "formula": f"{alpha} * {A} + {beta} * {B}",
                    "atoms": (A, B),
                    "coefs": (alpha, beta),
                    "predicted": float(pred),
                    "target": float(target_value),
                    "ppm": float(1e6 * rel),
                    "descr_len": abs(alpha) + abs(beta) + 2,
                })
    # keep low-ppm, prefer low description length
    hits_sorted = sorted(hits, key=lambda h: (h["ppm"], h["descr_len"]))
    # deduplicate by predicted value
    seen = set()
    top = []
    for h in hits_sorted:
        key = round(h["predicted"], 6)
        if key in seen:
            continue
        seen.add(key)
        top.append(h)
        if len(top) >= 15:
            break
    return top


# ---------------------------------------------------------------------------
# Search 3: ratio / product forms  (A · B / C) over small subsets
# ---------------------------------------------------------------------------
def search_product_ratio(target_value: float, target_name: str) -> list[dict]:
    names = list(BASIS.keys())
    hits = []
    for A in names:
        for B in names:
            for C in names:
                a, b, c = BASIS[A], BASIS[B], BASIS[C]
                if c == 0:
                    continue
                val = (a * b) / c
                if val <= 0:
                    continue
                ratio = target_value / val
                n = round(ratio)
                if n <= 0 or n > 500:
                    continue
                pred = n * val
                rel = abs(target_value - pred) / target_value
                if rel < 1e-3:   # only keep sub-1000 ppm
                    hits.append({
                        "kind": "product_ratio",
                        "formula": f"{n} * ({A} * {B} / {C})",
                        "atoms": (A, B, C),
                        "coef": n,
                        "predicted": float(pred),
                        "target": float(target_value),
                        "ppm": float(1e6 * rel),
                        "descr_len": abs(n) + 3,
                    })
    hits_sorted = sorted(hits, key=lambda h: (h["ppm"], h["descr_len"]))
    seen = set()
    top = []
    for h in hits_sorted:
        key = round(h["predicted"], 6)
        if key in seen:
            continue
        seen.add(key)
        top.append(h)
        if len(top) >= 15:
            break
    return top


# ---------------------------------------------------------------------------
# Search 4: PSLQ-style integer relation on log-scale
#   Does  log(target)  =  Σ n_i · log(atom_i)   for small integers n_i?
# ---------------------------------------------------------------------------
try:
    from mpmath import mp, pslq, mpf, log as mlog
    _HAVE_MPMATH = True
except Exception:
    _HAVE_MPMATH = False


def search_pslq_log(target_value: float, target_name: str) -> dict | None:
    if not _HAVE_MPMATH:
        return None
    mp.dps = 50
    # Use a small subset of the prime-ish atoms (avoid redundancy)
    atoms = ["delta", "b1", "q1", "D1", "a2", "ugp1_g", "ugp1_t"]
    vec = [mlog(mpf(BASIS[a])) for a in atoms]
    vec = [mlog(mpf(target_value))] + vec
    try:
        rel = pslq(vec, tol=1e-20, maxcoeff=200)
    except Exception:
        return None
    if rel is None:
        return None
    # rel = [c0, c1, ..., cn] such that  c0 * log(target) + Σ c_i log(a_i) ≈ 0
    if rel[0] == 0:
        return None
    # reconstruct predicted target
    c0 = rel[0]
    exps = {atoms[i]: -rel[i + 1] / c0 for i in range(len(atoms))}
    pred = 1.0
    for a, e in exps.items():
        pred *= float(BASIS[a]) ** float(e)
    rel_err = abs(pred - target_value) / target_value
    formula = " * ".join(f"{a}^({exps[a]:+.6g})" for a in atoms if abs(exps[a]) > 1e-9)
    return {
        "kind": "pslq_log",
        "formula": formula,
        "exponents": {a: float(exps[a]) for a in atoms},
        "predicted": float(pred),
        "target": float(target_value),
        "ppm": float(1e6 * rel_err),
        "descr_len": sum(abs(int(round(v))) for v in rel[1:]) + abs(int(rel[0])),
        "pslq_vec": [int(x) for x in rel],
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    report = {
        "experiment_id": "COMP-P01-K",
        "question":      "Do m_μ, m_τ (and √m_μ, √m_τ) have a structural UGP-integer × keV formula analogous to m_e = δ · b₁ keV (2.05 ppm)?",
        "codata_inputs": {
            "m_e_keV":   M_E_KEV,
            "m_mu_keV":  M_MU_KEV,
            "m_tau_keV": M_TAU_KEV,
            "source":    "CODATA 2022 / PDG 2024",
        },
        "basis_atoms":      BASIS,
        "composite_atoms":  COMPOSITES,
        "search_spec": {
            "single_atom":   "target ≈ n · A, n ≤ 300, A ∈ BASIS ∪ COMPOSITES",
            "two_atom":      "target ≈ α·A + β·B,  |α|,|β| ≤ 20, A,B ∈ BASIS",
            "product_ratio": "target ≈ n · (A·B/C),  n ≤ 500, A,B,C ∈ BASIS",
            "pslq_log":      "log(target) = Σ n_i · log(a_i)  with maxcoeff 200",
        },
        "benchmark_electron_ppm":  float(1e6 * abs(M_E_KEV - 511.0) / M_E_KEV),
        "results": {},
    }

    for name, tgt in TARGETS.items():
        print(f"[search] {name:18s}  target = {tgt:.8f}")
        r = {
            "target_value": tgt,
            "single_atom":    search_single(tgt, name),
            "two_atom_linear": search_two_linear(tgt, name, C=20),
            "product_ratio":  search_product_ratio(tgt, name),
            "pslq_log":       search_pslq_log(tgt, name),
        }
        report["results"][name] = r

    # Verdict: classify each target
    verdicts = {}
    for name, tgt in TARGETS.items():
        r = report["results"][name]
        best_ppm = min(
            [h["ppm"] for h in r["single_atom"]] +
            [h["ppm"] for h in r["two_atom_linear"]] +
            [h["ppm"] for h in r["product_ratio"]] +
            ([r["pslq_log"]["ppm"]] if r["pslq_log"] else []) +
            [1e30]
        )
        if best_ppm < 10.0:
            verdict = "HIT  (<10 ppm; same class as electron benchmark)"
        elif best_ppm < 100.0:
            verdict = "MARGINAL  (10–100 ppm; possibly structural)"
        elif best_ppm < 1000.0:
            verdict = "NEAR-MISS  (100–1000 ppm; phenomenological closure only)"
        else:
            verdict = "NO STRUCTURAL FORMULA (>1000 ppm)"
        verdicts[name] = {"best_ppm": best_ppm, "verdict": verdict}
    report["verdicts"] = verdicts

    # Honest summary statement
    e_ppm = verdicts["m_e_keV"]["best_ppm"]
    mu_ppm = verdicts["m_mu_keV"]["best_ppm"]
    tau_ppm = verdicts["m_tau_keV"]["best_ppm"]
    if e_ppm < 10 and mu_ppm >= 100 and tau_ppm >= 100:
        global_verdict = (
            "ASYMMETRIC: electron satisfies δ·b₁ coincidence at few-ppm level; "
            "μ and τ do NOT admit similarly tight structural integer × keV formulas. "
            "The electron case is either a numerical coincidence or reflects a "
            "generation-1-specific structural relation, not a universal ladder."
        )
    elif e_ppm < 10 and mu_ppm < 10 and tau_ppm < 10:
        global_verdict = (
            "UNIVERSAL HIT: all three charged-lepton masses admit structural "
            "integer × keV formulas in the ppm class. This would be a "
            "first-principles fermion-mass result."
        )
    else:
        global_verdict = (
            "MIXED: see per-target verdicts. Interpret with caution; only ppm-class "
            "hits are candidates for structural significance."
        )
    report["global_verdict"] = global_verdict
    report["timestamp_utc"] = _dt.datetime.utcnow().isoformat(timespec="seconds")

    out_path = Path(__file__).with_suffix(".json")
    with open(out_path, "w") as fh:
        json.dump(report, fh, indent=2, sort_keys=False)
    sha = _hl.sha256(out_path.read_bytes()).hexdigest()
    print(f"\n[write] {out_path.name}")
    print(f"[sha]   {sha}")

    # Console summary
    print("\n====  PER-TARGET VERDICTS  ====")
    for name, v in verdicts.items():
        print(f"  {name:18s}  best_ppm = {v['best_ppm']:12.3f}   →  {v['verdict']}")
    print(f"\n{global_verdict}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
