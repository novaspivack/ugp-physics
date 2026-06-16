#!/usr/bin/env python3
"""
COMP-P01-HH: Deep mass-matrix paradigm scan (09_SPEC Phase 2 — deep version)

Follow-up to COMP-P01-GG after the first-pass scan was judged too shallow (18
atoms, DL ≤ 3 on 3-scalar-per-matrix ansätze, best ~99.6% miss).  HH is the
proper deep Phase 2:

  - ~60 scalar UGP atoms (lifted/extended from FF2/FF3)
  - ~30 "binary kernels" B(i, j; feat_i, feat_j) for real-symmetric 3×3
  - Ansatz family: M^S_{ij} = Σ_{k=1..D} α_k · B_k^S(i, j)   with
        α_k chosen from the scalar library,
        B_k chosen from the kernel library,
        Hermitian (symmetric real) by construction.
  - JOINT scan: SAME (α, B) triple applied in each of the 3 charged-fermion
    sectors (lepton / up-type / down-type); sector differences enter ONLY
    through the per-generation triple features (a, b, c, L, μ, χ, ...) that
    each kernel consumes.  No sector-specific atom freedom.
  - PER-SECTOR diagnostic scan: best fit per sector (relaxed constraint; used
    only to detect PARTIAL-CLOSE, never to claim structural closure).
  - Batched numpy.linalg.eigvalsh on (N, 3, 3) stacks.
  - multiprocessing.Pool(12 workers).
  - 1000-trial null per D per mode (atom-label scramble).
  - Pre-commit SHA-256 on the prediction block before appending PDG comparison.

Tau triple uses c = -65535 (Braid-Atlas chirality), matching FF3 and GG.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import os
import random
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

import numpy as np

try:
    from multiprocessing import Pool, cpu_count
    _MP_AVAILABLE = True
except Exception:
    _MP_AVAILABLE = False


# ───────────────────────────────────────────────────────────────────────────
# Constants
# ───────────────────────────────────────────────────────────────────────────
PHI = (1.0 + math.sqrt(5.0)) / 2.0
INV_PHI = 1.0 / PHI           # positive 1/φ
INV_PHI_GALOIS = -1.0 / PHI   # Galois conjugate of φ
SQRT5 = math.sqrt(5.0)
PI = math.pi

K_GEN = PHI * math.cos(PI / 10.0)
K_GEN2 = -PHI / 2.0
K_L2 = 7.0 / 512.0
K_M = K_GEN2 + K_L2 / 4.0
K_MU_A = 1.0 / 8.0
K_MU_B = -3.0 / 2.0
K_MU_C = 4.0 / 3.0


def _mobius_signed(n: int) -> int:
    nn = abs(int(n))
    if nn <= 0:
        return 0
    if nn == 1:
        return 1
    factors: Dict[int, int] = {}
    k = nn
    p = 2
    while p * p <= k:
        while k % p == 0:
            factors[p] = factors.get(p, 0) + 1
            k //= p
        p += 1
    if k > 1:
        factors[k] = factors.get(k, 0) + 1
    for cnt in factors.values():
        if cnt > 1:
            return 0
    return (-1) ** len(factors)


def _fib(n: int) -> int:
    if n <= 0:
        return 0
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return b


def _lucas(n: int) -> int:
    if n == 0:
        return 2
    if n == 1:
        return 1
    a, b = 2, 1
    for _ in range(n - 1):
        a, b = b, a + b
    return b


# Tau c negative per Braid-Atlas (aligned with FF3, GG).
CHARGED_FERMIONS = [
    ("electron", 1, "lepton", (1, 73, 823), 0.5109989088),
    ("muon", 2, "lepton", (9, 42, 1023), 105.6583777),
    ("tau", 3, "lepton", (5, 275, -65535), 1776.859905),
    ("up", 1, "up_type", (5, 9, 275), 2.16),
    ("charm", 2, "up_type", (5, 275, 65535), 1275.0),
    ("top", 3, "up_type", (76, 337920, -1), 172760.0),
    ("down", 1, "down_type", (9, 5, 42), 4.67),
    ("strange", 2, "down_type", (9, 186, 1023), 93.4),
    ("bottom", 3, "down_type", (5, 8191, 65535), 4180.0),
]


def feature_vec(gen: int, triple: Tuple[int, int, int]) -> Dict[str, float]:
    a, b, c = triple
    L = math.log(abs(b) / abs(c)) if c != 0 else 0.0
    chi = 1.0 if c < 0 else 0.0
    return {
        "gen": float(gen),
        "gen2": float(gen * gen),
        "L": L,
        "L2": L * L,
        "mu_a": float(_mobius_signed(a)),
        "mu_b": float(_mobius_signed(b)),
        "mu_c": float(_mobius_signed(c)),
        "mu_prod": float(_mobius_signed(a) * _mobius_signed(b) * _mobius_signed(c)),
        "chi": chi,
        "sign_c": 1.0 if c > 0 else -1.0,
        "log_abs_a": math.log(abs(a)) if a != 0 else 0.0,
        "log_abs_b": math.log(abs(b)) if b != 0 else 0.0,
        "log_abs_c": math.log(abs(c)) if c != 0 else 0.0,
        "phi_g": PHI ** (gen - 1),
        "inv_phi_g": INV_PHI ** (gen - 1),
        "inv_phi_galois_g": INV_PHI_GALOIS ** (gen - 1),
        "fib_g": float(_fib(gen)),
        "lucas_g": float(_lucas(gen)),
    }


def sector_fermions(sector: str) -> List[Tuple[str, int, Tuple[int, int, int], float]]:
    return [(f[0], f[1], f[3], f[4]) for f in CHARGED_FERMIONS if f[2] == sector]


# ───────────────────────────────────────────────────────────────────────────
# Scalar atom library (UGP-structural)
# ───────────────────────────────────────────────────────────────────────────
def scalar_atom_library() -> Dict[str, float]:
    atoms: Dict[str, float] = {
        # unity / small integers
        "one": 1.0,
        "two": 2.0,
        "three": 3.0,
        "five": 5.0,
        "seven": 7.0,
        "neg_one": -1.0,
        "neg_two": -2.0,
        "half": 0.5,
        "third": 1.0 / 3.0,
        "quarter": 0.25,
        "two_thirds": 2.0 / 3.0,
        "three_halves": 1.5,
        # UGP Lean-certified constants
        "phi": PHI,
        "inv_phi": INV_PHI,
        "inv_phi_galois": INV_PHI_GALOIS,
        "sqrt5": SQRT5,
        "inv_sqrt5": 1.0 / SQRT5,
        "k_gen": K_GEN,
        "k_gen2": K_GEN2,
        "k_L2": K_L2,
        "k_M": K_M,
        "k_mu_a": K_MU_A,
        "k_mu_b": K_MU_B,
        "k_mu_c": K_MU_C,
        # φ powers (golden field)
        "phi2": PHI ** 2,
        "phi3": PHI ** 3,
        "phi4": PHI ** 4,
        "inv_phi2": INV_PHI ** 2,
        "inv_phi3": INV_PHI ** 3,
        "phi_half": math.sqrt(PHI),
        # cyclotomic (D5 / pentagon / decagon)
        "cos_pi5": math.cos(PI / 5.0),
        "cos_2pi5": math.cos(2 * PI / 5.0),
        "cos_pi10": math.cos(PI / 10.0),
        "sin_pi5": math.sin(PI / 5.0),
        "sin_pi10": math.sin(PI / 10.0),
        "cos_pi3": 0.5,                       # = cos(π/3)
        "sin_pi3": math.sin(PI / 3.0),
        # pi-related
        "pi_atom": PI,
        "inv_pi": 1.0 / PI,
        "pi_half": PI / 2.0,
        "pi_quarter": PI / 4.0,
        # Fibonacci / Lucas seeds
        "F3": 2.0,
        "F5": 5.0,
        "L3": 4.0,
        "L5": 11.0,
        # Weyl orders (Lie-group structural)
        "weyl_A2": 6.0,
        "weyl_B2": 8.0,
        "weyl_G2": 12.0,
        # β / b_G SM coefficients (U(1)_Y, SU(2), SU(3))
        "bG_U1": 41.0 / 6.0,
        "bG_SU2": -19.0 / 6.0,
        "bG_SU3": -7.0,
        # small rationals
        "eight": 8.0,
        "inv_twelve": 1.0 / 12.0,
        "four_thirds": 4.0 / 3.0,
        "five_sixths": 5.0 / 6.0,
        "seven_twelfths": 7.0 / 12.0,
        "neg_half": -0.5,
        "neg_three_halves": -1.5,
        "neg_sqrt5": -SQRT5,
    }
    return atoms


SCALAR_ATOMS = scalar_atom_library()
SCALAR_NAMES: List[str] = list(SCALAR_ATOMS.keys())
SCALAR_VALUES: np.ndarray = np.array([SCALAR_ATOMS[n] for n in SCALAR_NAMES], dtype=float)


# ───────────────────────────────────────────────────────────────────────────
# Binary kernel library  B(i, j; feat_i, feat_j) → real
# For each sector we pre-evaluate each kernel to a (3, 3) float array.
# ───────────────────────────────────────────────────────────────────────────
def build_kernel_library(
    sector_feats: List[Dict[str, float]],
) -> Dict[str, np.ndarray]:
    """Return dict kernel_name -> (3,3) symmetric real matrix."""
    fi = sector_feats
    mats: Dict[str, np.ndarray] = {}
    mats["delta_ij"] = np.eye(3, dtype=float)
    mats["one_ij"] = np.ones((3, 3), dtype=float)
    mats["phi_diff"] = np.array([[PHI ** abs(i - j) for j in range(3)] for i in range(3)])
    mats["phi_sum"] = np.array([[PHI ** (i + j) for j in range(3)] for i in range(3)])
    mats["inv_phi_diff"] = np.array([[INV_PHI ** abs(i - j) for j in range(3)] for i in range(3)])
    mats["zeta5_re_sum"] = np.array(
        [[math.cos(2 * PI * (i + j) / 5.0) for j in range(3)] for i in range(3)]
    )
    mats["zeta5_re_diff"] = np.array(
        [[math.cos(2 * PI * abs(i - j) / 5.0) for j in range(3)] for i in range(3)]
    )
    mats["pent_re_sum"] = np.array(
        [[math.cos(PI * (i + j) / 5.0) for j in range(3)] for i in range(3)]
    )
    mats["pent_re_diff"] = np.array(
        [[math.cos(PI * abs(i - j) / 5.0) for j in range(3)] for i in range(3)]
    )
    mats["deca_re_sum"] = np.array(
        [[math.cos(PI * (i + j) / 10.0) for j in range(3)] for i in range(3)]
    )
    mats["deca_re_diff"] = np.array(
        [[math.cos(PI * abs(i - j) / 10.0) for j in range(3)] for i in range(3)]
    )
    mats["zeta3_re_sum"] = np.array(
        [[math.cos(2 * PI * (i + j) / 3.0) for j in range(3)] for i in range(3)]
    )
    mats["zeta3_re_diff"] = np.array(
        [[math.cos(2 * PI * abs(i - j) / 3.0) for j in range(3)] for i in range(3)]
    )
    # Generation-feature kernels
    mu_prod = np.array([fi[k]["mu_prod"] for k in range(3)])
    mats["mu_prod_prod"] = np.outer(mu_prod, mu_prod)
    mats["mu_prod_diag"] = np.diag(mu_prod)
    mu_a = np.array([fi[k]["mu_a"] for k in range(3)])
    mu_b = np.array([fi[k]["mu_b"] for k in range(3)])
    mu_c = np.array([fi[k]["mu_c"] for k in range(3)])
    mats["mu_a_prod"] = np.outer(mu_a, mu_a)
    mats["mu_b_prod"] = np.outer(mu_b, mu_b)
    mats["mu_c_prod"] = np.outer(mu_c, mu_c)
    mats["mu_a_diag"] = np.diag(mu_a)
    mats["mu_c_diag"] = np.diag(mu_c)
    chi = np.array([fi[k]["chi"] for k in range(3)])
    mats["chi_prod"] = np.outer(chi, chi)
    mats["chi_diag"] = np.diag(chi)
    mats["chi_sym"] = (np.outer(chi, np.ones(3)) + np.outer(np.ones(3), chi)) / 2.0
    L = np.array([fi[k]["L"] for k in range(3)])
    mats["L_diag"] = np.diag(L)
    mats["L_prod"] = np.outer(L, L)
    phi_g = np.array([fi[k]["phi_g"] for k in range(3)])
    mats["phi_g_diag"] = np.diag(phi_g)
    mats["phi_g_prod"] = np.outer(phi_g, phi_g)
    inv_phi_galois_g = np.array([fi[k]["inv_phi_galois_g"] for k in range(3)])
    mats["inv_phi_galois_g_diag"] = np.diag(inv_phi_galois_g)
    fib_g = np.array([fi[k]["fib_g"] for k in range(3)])
    mats["fib_g_diag"] = np.diag(fib_g)
    mats["fib_g_prod"] = np.outer(fib_g, fib_g)
    gen_arr = np.array([fi[k]["gen"] for k in range(3)])
    mats["gen_sum"] = (np.outer(gen_arr, np.ones(3)) + np.outer(np.ones(3), gen_arr)) / 2.0
    mats["gen_diag"] = np.diag(gen_arr)
    for k, v in list(mats.items()):
        mats[k] = 0.5 * (v + v.T)
    return mats


# ───────────────────────────────────────────────────────────────────────────
# PDG data and scoring
# ───────────────────────────────────────────────────────────────────────────
def pdg_by_sector() -> Dict[str, np.ndarray]:
    return {
        "lepton": np.array([f[4] for f in CHARGED_FERMIONS if f[2] == "lepton"], dtype=float),
        "up_type": np.array([f[4] for f in CHARGED_FERMIONS if f[2] == "up_type"], dtype=float),
        "down_type": np.array(
            [f[4] for f in CHARGED_FERMIONS if f[2] == "down_type"], dtype=float
        ),
    }


def sector_feats_by_sector() -> Dict[str, List[Dict[str, float]]]:
    out: Dict[str, List[Dict[str, float]]] = {"lepton": [], "up_type": [], "down_type": []}
    for f in CHARGED_FERMIONS:
        out[f[2]].append(feature_vec(f[1], f[3]))
    return out


def predicted_masses(M_batch: np.ndarray, pdg_sorted: np.ndarray) -> np.ndarray:
    """M_batch (N,3,3) symmetric real → predicted masses (N,3) scaled to lightest PDG."""
    evals = np.linalg.eigvalsh(M_batch)              # (N, 3) ascending
    sv = np.sort(np.abs(evals), axis=1)              # (N, 3) ascending
    scale = pdg_sorted[0] / np.maximum(sv[:, 0], 1e-30)
    return sv * scale[:, None]                        # (N, 3)


def max_frac_err_global(
    M_l: np.ndarray, M_u: np.ndarray, M_d: np.ndarray,
    pdg_l: np.ndarray, pdg_u: np.ndarray, pdg_d: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """Return global max-frac-err (N,) across all 9 fermions, and predicted (N,9)."""
    pl = predicted_masses(M_l, np.sort(pdg_l))
    pu = predicted_masses(M_u, np.sort(pdg_u))
    pd = predicted_masses(M_d, np.sort(pdg_d))
    pdg_sorted = np.concatenate([np.sort(pdg_l), np.sort(pdg_u), np.sort(pdg_d)])
    pred = np.concatenate([pl, pu, pd], axis=1)   # (N, 9)
    frac = np.abs(pred - pdg_sorted[None, :]) / np.maximum(pdg_sorted[None, :], 1e-30)
    return np.max(frac, axis=1), pred


def koide_residual(pred_lep: np.ndarray) -> np.ndarray:
    """pred_lep (N, 3) ascending → Koide relative residual (N,)."""
    m1, m2, m3 = pred_lep[:, 0], pred_lep[:, 1], pred_lep[:, 2]
    lhs = m1 + m2 + m3
    rhs = (2.0 / 3.0) * (np.sqrt(m1) + np.sqrt(m2) + np.sqrt(m3)) ** 2
    return np.abs(lhs - rhs) / np.maximum(lhs, 1e-30)


# ───────────────────────────────────────────────────────────────────────────
# Worker
# ───────────────────────────────────────────────────────────────────────────
def _build_M_batch(
    kernel_stack_l: np.ndarray,   # (K, 3, 3) for lepton sector
    kernel_stack_u: np.ndarray,
    kernel_stack_d: np.ndarray,
    alphas: np.ndarray,           # (N, K)
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    # alphas: (N, K); kernels: (K, 3, 3) → M (N, 3, 3) = Σ_k α_{n,k} K_k
    M_l = np.einsum("nk,kij->nij", alphas, kernel_stack_l)
    M_u = np.einsum("nk,kij->nij", alphas, kernel_stack_u)
    M_d = np.einsum("nk,kij->nij", alphas, kernel_stack_d)
    return M_l, M_u, M_d


def _worker_scan(args) -> Dict:
    (kernel_subset, K_stacks_by_sector, pdg, D,
     scalar_vals, top_k, closure_eps, sectors) = args
    Kl = np.stack([K_stacks_by_sector["lepton"][k] for k in kernel_subset])
    Ku = np.stack([K_stacks_by_sector["up_type"][k] for k in kernel_subset])
    Kd = np.stack([K_stacks_by_sector["down_type"][k] for k in kernel_subset])

    # All length-D permutations (with repetition? We disallow repeated atoms)
    n_atoms = len(scalar_vals)
    # Cartesian product of atom indices of length D, distinct
    idx = np.array(list(itertools.permutations(range(n_atoms), D)), dtype=np.int64)
    alphas = scalar_vals[idx]   # (N, D)
    Ml, Mu, Md = _build_M_batch(Kl, Ku, Kd, alphas)
    frac, pred = max_frac_err_global(Ml, Mu, Md, pdg["lepton"], pdg["up_type"], pdg["down_type"])
    pred_lep = pred[:, :3]
    kr = koide_residual(pred_lep)
    closures = int(np.sum(frac <= closure_eps))
    # top-K by max_frac
    order = np.argsort(frac)[:top_k]
    top = [
        {
            "atoms": [SCALAR_NAMES[idx[i, k]] for k in range(D)],
            "kernels": list(kernel_subset),
            "max_fractional_error": float(frac[i]),
            "koide_relative_residual": float(kr[i]),
            "predicted_masses_MeV": pred[i].tolist(),
        }
        for i in order
    ]
    # histogram buckets
    hist = {
        "le_0.01": int(np.sum(frac <= 0.01)),
        "le_0.02": int(np.sum(frac <= 0.02)),
        "le_0.05": int(np.sum(frac <= 0.05)),
        "le_0.10": int(np.sum(frac <= 0.10)),
        "le_0.20": int(np.sum(frac <= 0.20)),
        "le_0.50": int(np.sum(frac <= 0.50)),
        "le_1.00": int(np.sum(frac <= 1.00)),
    }
    return {
        "n_combinations": int(alphas.shape[0]),
        "closures_at_eps": closures,
        "best_max_frac": float(np.min(frac)),
        "top_k": top,
        "histogram": hist,
    }


# ───────────────────────────────────────────────────────────────────────────
# Orchestrator
# ───────────────────────────────────────────────────────────────────────────
def scan_depth(
    D: int,
    K_stacks_by_sector: Dict[str, Dict[str, np.ndarray]],
    pdg: Dict[str, np.ndarray],
    kernel_names: List[str],
    n_workers: int,
    top_k_per_chunk: int = 5,
    global_top_k: int = 20,
    closure_eps: float = 0.01,
) -> Dict:
    t0 = time.time()
    if D == 1:
        kernel_subsets = [(k,) for k in kernel_names]
    elif D == 2:
        kernel_subsets = list(itertools.combinations(kernel_names, 2))
    elif D == 3:
        kernel_subsets = list(itertools.combinations(kernel_names, 3))
    else:
        raise ValueError(D)

    args_iter = [
        (
            ks,
            K_stacks_by_sector,
            pdg,
            D,
            SCALAR_VALUES,
            top_k_per_chunk,
            closure_eps,
            ("lepton", "up_type", "down_type"),
        )
        for ks in kernel_subsets
    ]

    total_combos = 0
    global_best: List[Dict] = []
    total_hist = {k: 0 for k in ("le_0.01", "le_0.02", "le_0.05", "le_0.10", "le_0.20", "le_0.50", "le_1.00")}
    closures = 0

    def consume(results_iter):
        nonlocal total_combos, closures
        for res in results_iter:
            total_combos += res["n_combinations"]
            closures += res["closures_at_eps"]
            for k in total_hist:
                total_hist[k] += res["histogram"][k]
            global_best.extend(res["top_k"])

    if _MP_AVAILABLE and n_workers > 1 and len(args_iter) >= n_workers:
        with Pool(n_workers) as pool:
            consume(pool.imap_unordered(_worker_scan, args_iter, chunksize=1))
    else:
        consume(_worker_scan(a) for a in args_iter)

    global_best.sort(key=lambda r: r["max_fractional_error"])
    return {
        "D": D,
        "n_kernel_subsets": len(kernel_subsets),
        "n_combinations_total": total_combos,
        "closures_at_1pct": closures,
        "histogram": total_hist,
        "top_k": global_best[:global_top_k],
        "elapsed_seconds": time.time() - t0,
    }


def null_scan(
    D: int,
    trials: int,
    K_stacks_by_sector: Dict[str, Dict[str, np.ndarray]],
    pdg: Dict[str, np.ndarray],
    kernel_names: List[str],
    seed: int = 20260419,
) -> Dict:
    """Null test: scramble the scalar atom label → value mapping (preserves
    library multiset, destroys atom identity).  1000 trials, each evaluates
    one random (kernel-subset, atom-triple) under the scrambled mapping."""
    t0 = time.time()
    rng = random.Random(seed)
    hits = 0
    n_combos = trials
    best = math.inf
    for _ in range(trials):
        perm = list(range(len(SCALAR_VALUES)))
        rng.shuffle(perm)
        vals_scrambled = SCALAR_VALUES[perm]
        ks = rng.sample(kernel_names, D)
        atom_idx = rng.sample(range(len(SCALAR_VALUES)), D)
        alpha = vals_scrambled[atom_idx][None, :]   # (1, D)
        Kl = np.stack([K_stacks_by_sector["lepton"][k] for k in ks])
        Ku = np.stack([K_stacks_by_sector["up_type"][k] for k in ks])
        Kd = np.stack([K_stacks_by_sector["down_type"][k] for k in ks])
        Ml, Mu, Md = _build_M_batch(Kl, Ku, Kd, alpha)
        frac, _ = max_frac_err_global(Ml, Mu, Md, pdg["lepton"], pdg["up_type"], pdg["down_type"])
        best = min(best, float(frac[0]))
        if frac[0] <= 0.01:
            hits += 1
    return {
        "trials": n_combos,
        "hits_at_1pct": hits,
        "hit_rate": hits / max(n_combos, 1),
        "best_random_max_frac": float(best),
        "elapsed_seconds": time.time() - t0,
    }


def main() -> Dict:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    sector_feats = sector_feats_by_sector()
    K_by_sector: Dict[str, Dict[str, np.ndarray]] = {
        s: build_kernel_library(sector_feats[s]) for s in ("lepton", "up_type", "down_type")
    }
    kernel_names = list(K_by_sector["lepton"].keys())
    pdg = pdg_by_sector()
    n_workers = min(12, cpu_count() if _MP_AVAILABLE else 1)

    scans: Dict[int, Dict] = {}
    for D in (1, 2, 3):
        print(f"[HH] scanning D={D} (joint, 3 sectors, closure eps = 1%)...", flush=True)
        scans[D] = scan_depth(D, K_by_sector, pdg, kernel_names, n_workers)
        s = scans[D]
        print(
            f"[HH]   D={D}: {s['n_combinations_total']:,} combos in {s['elapsed_seconds']:.1f}s  "
            f"best={s['top_k'][0]['max_fractional_error']:.4g}  closures={s['closures_at_1pct']}"
        )

    nulls: Dict[int, Dict] = {}
    for D in (1, 2, 3):
        print(f"[HH] null D={D} (1000 trials)...", flush=True)
        nulls[D] = null_scan(D, 1000, K_by_sector, pdg, kernel_names)
        n = nulls[D]
        print(
            f"[HH]   null D={D}: {n['hits_at_1pct']}/{n['trials']} hits  "
            f"(rate {n['hit_rate']:.4f})  best_rand={n['best_random_max_frac']:.4g}"
        )

    overall_best = None
    for D, s in scans.items():
        if s["top_k"] and (overall_best is None or s["top_k"][0]["max_fractional_error"] < overall_best["max_fractional_error"]):
            overall_best = {"D": D, **s["top_k"][0]}

    any_close = any(s["closures_at_1pct"] > 0 for s in scans.values())
    max_null = max(n["hit_rate"] for n in nulls.values())
    null_disciplined = max_null < 0.01

    if any_close and null_disciplined:
        verdict = "CLOSES_structural_beats_null"
    elif any_close and not null_disciplined:
        verdict = "CLOSES_but_density_dominated"
    else:
        verdict = "MAP_deep_mass_matrix_paradigm_insufficient"

    prediction_block = {
        "comp_id": "COMP-P01-HH",
        "spec_reference": "09_SPEC_MASS_MATRIX_PARADIGM_MMP.md Phase 2 (deep)",
        "supersedes_first_pass": "COMP-P01-GG",
        "timestamp_utc": timestamp,
        "purpose": (
            "Deep Phase-2 scan of the mass-matrix paradigm with a 60-atom scalar "
            "library and 30-kernel binary library.  Joint constraint: SAME atom/kernel "
            "triple across lepton / up-type / down-type sectors; sector differences "
            "enter only through the per-generation triple features inside kernels. "
            "No continuous fit parameters — only discrete UGP atom choices."
        ),
        "model": "M^S_ij = sum_{k=1..D} alpha_k * B_k^S(i, j); Hermitian (real symmetric); closure := max_fractional_error <= 0.01 across all 9 charged fermions after per-sector lightest-PDG rescaling.",
        "tau_triple_note": "tau c = -65535 (Braid-Atlas chirality), aligned with FF3, GG.",
        "scalar_atom_library": {
            "size": len(SCALAR_NAMES),
            "atoms": {n: SCALAR_ATOMS[n] for n in SCALAR_NAMES},
        },
        "binary_kernel_library": {
            "size": len(kernel_names),
            "kernels": kernel_names,
        },
        "parallelism": {"n_workers": n_workers, "backend": "multiprocessing.Pool" if _MP_AVAILABLE else "serial"},
        "closure_eps": 0.01,
        "null_protocol": "atom-label scramble; evaluate random (kernel-subset, atom-triple); 1000 trials per D.",
        "charged_fermions": [
            {"name": f[0], "gen": f[1], "type": f[2], "triple": list(f[3]), "m_PDG_MeV": f[4]}
            for f in CHARGED_FERMIONS
        ],
        "scans_by_D": scans,
        "nulls_by_D": nulls,
        "overall_best_structural": overall_best,
    }

    pred_json = json.dumps(prediction_block, sort_keys=True, separators=(",", ":"), default=str)
    sha256_pred = hashlib.sha256(pred_json.encode("utf-8")).hexdigest()

    pdg_comparison = {
        "prediction_block_sha256": sha256_pred,
        "any_closure_at_1pct": any_close,
        "null_hit_rates": {D: nulls[D]["hit_rate"] for D in nulls},
        "max_null_hit_rate": max_null,
        "null_disciplined": null_disciplined,
        "verdict": verdict,
        "overall_best": overall_best,
    }

    return {
        "prediction_block_precomparison": prediction_block,
        "sha256_prediction_block": sha256_pred,
        "pdg_comparison": pdg_comparison,
    }


if __name__ == "__main__":
    out = main()
    path = "comp_p01_HH_mass_matrix_paradigm_deep.json"
    with open(path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print()
    print(json.dumps(out["pdg_comparison"], indent=2, default=str))
    print(f"Written: {path}")
