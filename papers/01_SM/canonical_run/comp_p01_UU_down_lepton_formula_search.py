#!/usr/bin/env python3
"""
COMP-P01-UU: Down-type-lepton formula search (Round 8)

Data: log(m_{d_g}/m_{lep_g}) = (+2.213, -0.123, +0.855) for g = 1, 2, 3.
Non-monotonic: positive, negative, positive.

Search 9 functional-form families for UGP-atom-native 2- or 3-parameter fits
matching all 3 data points at ≤0.5% max-frac-err, with disciplined null.

Families tested:
  F1:  α · 2^g + β                  (up-type shape, expected to fail)
  F2:  α · 3^g + β
  F3:  α · (-2)^g + β               (hypercharge-signed geometric)
  F4:  α · (-1)^g · 2^g + β         (alternating)
  F5:  α · cos(ω·g) + β (with ω scanned over UGP-native angles)
  F6:  α · Fib(g) + β
  F7:  α · g + β · (-1)^g + γ       (3-param, trivially fits 3 points)
  F8:  α · log|c_dn_g| + β
  F9:  α · log(c_dn_g/b_dn_g) + β
  F10: α · sign(c_dn_g) · 2^g + β   (chirality-sign-modulated)
  F11: α · (2^g - 1) + β · (-1)^g + γ  (3-param Mersenne + alternating)

Zero-parameter identity tests (analog of up-type β-free):
  After finding best formula, check whether β cancels in inter-generational
  differences and extracts a clean UGP-native relation.

Null protocol per family: random coefficients from UGP atom value range,
10000 trials per family, hit rate at 0.5% on all 3 data points.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import random
import time
from datetime import datetime, timezone
from typing import Callable, Dict, List, Tuple

import numpy as np

# PDG masses (MeV)
PDG = {
    'electron': 0.5109989088, 'muon': 105.6583777, 'tau': 1776.859905,
    'down': 4.67, 'strange': 93.4, 'bottom': 4180.0,
}
PHI = (1 + math.sqrt(5)) / 2

# Down-type triples (from Braid-Atlas)
TRIPLES_DN = {1: (9, 5, 42), 2: (9, 186, 1023), 3: (5, 8191, 65535)}
TRIPLES_LEP = {1: (1, 73, 823), 2: (9, 42, 1023), 3: (5, 275, -65535)}


def obs(g: int) -> float:
    dn_map = {1: 'down', 2: 'strange', 3: 'bottom'}
    lep_map = {1: 'electron', 2: 'muon', 3: 'tau'}
    return math.log(PDG[dn_map[g]] / PDG[lep_map[g]])


OBS = {g: obs(g) for g in (1, 2, 3)}


def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return b


# Feature functions h(g) to scan
def get_features() -> Dict[str, Callable[[int], float]]:
    feats: Dict[str, Callable[[int], float]] = {
        '2^g': lambda g: 2.0 ** g,
        '3^g': lambda g: 3.0 ** g,
        '(-2)^g': lambda g: (-2.0) ** g,
        '(-1)^g * 2^g': lambda g: ((-1) ** g) * (2.0 ** g),
        '(-1)^g * 3^g': lambda g: ((-1) ** g) * (3.0 ** g),
        'Fib(g)': lambda g: float(fib(g)),
        'Fib(g+1)': lambda g: float(fib(g + 1)),
        '(-1)^g': lambda g: (-1.0) ** g,
        'g': lambda g: float(g),
        'g^2': lambda g: float(g * g),
        '2^g - 1': lambda g: 2.0 ** g - 1.0,
        'phi^g': lambda g: PHI ** g,
        '(-1/phi)^g': lambda g: (-1.0 / PHI) ** g,
        'log|c_dn|': lambda g: math.log(abs(TRIPLES_DN[g][2])),
        'log|b_dn|': lambda g: math.log(abs(TRIPLES_DN[g][1])),
        'log(|c_dn|/|b_dn|)': lambda g: math.log(abs(TRIPLES_DN[g][2]) / abs(TRIPLES_DN[g][1])),
        'log(|b_dn|/|a_dn|)': lambda g: math.log(abs(TRIPLES_DN[g][1]) / abs(TRIPLES_DN[g][0])),
    }
    # cyclotomic cosines for several integer divisors of 2π
    for k in [3, 4, 5, 6, 7, 8, 10, 12]:
        feats[f'cos(2πg/{k})'] = (lambda k=k: lambda g: math.cos(2 * math.pi * g / k))()
        feats[f'sin(2πg/{k})'] = (lambda k=k: lambda g: math.sin(2 * math.pi * g / k))()
    for k in [3, 4, 5, 6, 10]:
        feats[f'cos(πg/{k})'] = (lambda k=k: lambda g: math.cos(math.pi * g / k))()
    return feats


def ugp_atom_library() -> Dict[str, float]:
    atoms: Dict[str, float] = {}
    # rationals
    for n in range(1, 13):
        for d in range(2, 13):
            if math.gcd(n, d) == 1 and n < 3 * d and abs(n / d) < 5:
                atoms[f'{n}/{d}'] = n / d
                atoms[f'-{n}/{d}'] = -n / d
    atoms['0'] = 0.0
    atoms['1'] = 1.0
    atoms['-1'] = -1.0
    atoms['2'] = 2.0
    atoms['-2'] = -2.0
    atoms['3'] = 3.0
    atoms['-3'] = -3.0
    # golden field
    for p in (-4, -3, -2, -1, 1, 2, 3, 4):
        atoms[f'phi^{p}'] = PHI ** p
        atoms[f'-phi^{p}'] = -(PHI ** p)
    atoms['sqrt5'] = math.sqrt(5)
    atoms['-sqrt5'] = -math.sqrt(5)
    # pi-related
    for k in [3, 4, 5, 6, 7, 8, 10, 12]:
        atoms[f'pi/{k}'] = math.pi / k
        atoms[f'-pi/{k}'] = -math.pi / k
    for k in [3, 5, 7]:
        atoms[f'2pi/{k}'] = 2 * math.pi / k
        atoms[f'-2pi/{k}'] = -2 * math.pi / k
    # UGP constants
    atoms['k_L2'] = 7 / 512
    atoms['k_mu_a'] = 1 / 8
    atoms['k_mu_b'] = -3 / 2
    atoms['k_mu_c'] = 4 / 3
    atoms['ln(2)'] = math.log(2)
    atoms['ln(3)'] = math.log(3)
    atoms['ln(phi)'] = math.log(PHI)
    return atoms


def fit_2param(feat_h: Callable, tol: float, atoms: Dict[str, float]) -> List[Dict]:
    """Find UGP-atom (α, β) fits to obs_g = α·h(g) + β at ≤ tol max-frac-err."""
    h_vals = {g: feat_h(g) for g in (1, 2, 3)}
    hits = []
    for a_name, a in atoms.items():
        for b_name, b in atoms.items():
            errs = [abs(a * h_vals[g] + b - OBS[g]) / max(abs(OBS[g]), 0.01) for g in (1, 2, 3)]
            if max(errs) <= tol:
                hits.append({
                    'alpha_atom': a_name, 'alpha_val': a,
                    'beta_atom': b_name, 'beta_val': b,
                    'max_frac_err': max(errs),
                    'predictions': {g: a * h_vals[g] + b for g in (1, 2, 3)},
                })
    return hits


def null_2param_random(feat_h: Callable, alpha_range: Tuple[float, float],
                        beta_range: Tuple[float, float], n_trials: int,
                        tol: float, seed: int) -> Dict:
    rng = random.Random(seed)
    h_vals = {g: feat_h(g) for g in (1, 2, 3)}
    hits = 0
    for _ in range(n_trials):
        a = rng.uniform(*alpha_range)
        b = rng.uniform(*beta_range)
        errs = [abs(a * h_vals[g] + b - OBS[g]) / max(abs(OBS[g]), 0.01) for g in (1, 2, 3)]
        if max(errs) <= tol:
            hits += 1
    return {'trials': n_trials, 'hits': hits, 'density': hits / n_trials}


def least_squares_fit(feat_h: Callable) -> Tuple[float, float, float]:
    """Return (alpha_LS, beta_LS, residual_max)."""
    h_vec = np.array([feat_h(g) for g in (1, 2, 3)])
    y = np.array([OBS[g] for g in (1, 2, 3)])
    A = np.column_stack([h_vec, np.ones(3)])
    coef, _, _, _ = np.linalg.lstsq(A, y, rcond=None)
    pred = A @ coef
    resid = np.abs(pred - y).max()
    return float(coef[0]), float(coef[1]), float(resid)


def main():
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    feats = get_features()
    atoms = ugp_atom_library()

    tol = 0.005  # 0.5% max frac err
    results: Dict[str, Dict] = {}

    print(f"Atom library: {len(atoms)}")
    print(f"Feature families: {len(feats)}")
    print(f"Down-type data: {OBS}")
    print()

    atom_range = (min(v for v in atoms.values() if abs(v) < 5),
                    max(v for v in atoms.values() if abs(v) < 5))

    for fname, fn in feats.items():
        try:
            hits = fit_2param(fn, tol, atoms)
        except Exception:
            continue
        alpha_LS, beta_LS, resid = least_squares_fit(fn)
        nul = null_2param_random(fn, atom_range, atom_range, 10000, tol, seed=20260419)
        results[fname] = {
            'feature': fname,
            'LS_alpha': alpha_LS, 'LS_beta': beta_LS, 'LS_max_resid_abs': resid,
            'LS_max_frac_err': resid / max(abs(v) for v in OBS.values()),
            'ugp_atom_hits': hits,
            'n_atom_hits': len(hits),
            'null_random_density': nul['density'],
            'null_hits': nul['hits'],
        }
        pass_atom = len(hits) > 0
        pass_null = nul['density'] < 1e-3
        print(f"  {fname:30s}  LS_resid={resid:.3f}  LS_frac={results[fname]['LS_max_frac_err']:.4f}  "
              f"atom_hits={len(hits):3d}  null_density={nul['density']:.4f}  "
              f"{'✓pass_both' if pass_atom and pass_null else ('near' if pass_atom else '—')}")

    # Also: 3-param linear-alternating-const (overfitted, but check for UGP-atom coincidence)
    # obs(g) = α·g + β·(-1)^g + γ
    # 3 eqs, 3 unknowns — exactly solvable
    A_3 = np.array([[1, -1, 1], [2, 1, 1], [3, -1, 1]], dtype=float)
    y = np.array([OBS[g] for g in (1, 2, 3)])
    c_3 = np.linalg.solve(A_3, y)
    alpha_3, beta_3, gamma_3 = c_3
    # Find nearest UGP atoms
    def nearest(v):
        bn, bv, bd = None, None, math.inf
        for name, val in atoms.items():
            d = abs(val - v)
            if d < bd:
                bd = d
                bn = name
                bv = val
        return bn, bv, bd
    a3_name, a3_val, a3_err = nearest(alpha_3)
    b3_name, b3_val, b3_err = nearest(beta_3)
    c3_name, c3_val, c3_err = nearest(gamma_3)
    results['3param_linear_plus_alternating_plus_const'] = {
        'formula': 'obs(g) = α·g + β·(-1)^g + γ',
        'exact_alpha': alpha_3, 'exact_beta': beta_3, 'exact_gamma': gamma_3,
        'nearest_alpha_atom': (a3_name, a3_val, a3_err, 100*a3_err/abs(alpha_3)),
        'nearest_beta_atom': (b3_name, b3_val, b3_err, 100*b3_err/abs(beta_3)),
        'nearest_gamma_atom': (c3_name, c3_val, c3_err, 100*c3_err/abs(gamma_3)),
    }
    print()
    print(f"3-param linear+alt+const fit:")
    print(f"  α={alpha_3:.4f}  nearest: {a3_name}={a3_val:.4f} (err {100*a3_err/abs(alpha_3):.2f}%)")
    print(f"  β={beta_3:.4f}  nearest: {b3_name}={b3_val:.4f} (err {100*b3_err/abs(beta_3):.2f}%)")
    print(f"  γ={gamma_3:.4f}  nearest: {c3_name}={c3_val:.4f} (err {100*c3_err/abs(gamma_3):.2f}%)")

    # Find best candidate overall
    best_2p = None
    for fname, r in results.items():
        if 'n_atom_hits' not in r:
            continue
        if r['n_atom_hits'] > 0 and r['null_random_density'] < 1e-3:
            if best_2p is None or r['LS_max_frac_err'] < best_2p['LS_max_frac_err']:
                best_2p = r

    prediction_block = {
        'comp_id': 'COMP-P01-UU',
        'spec_reference': 'Team Round 8 — down-type-lepton formula search',
        'timestamp_utc': ts,
        'down_type_log_ratios': OBS,
        'atoms_library_size': len(atoms),
        'families_tested': list(results.keys()),
        'per_family_results': results,
        'best_2param_structurally_disciplined': best_2p,
    }
    pred_json = json.dumps(prediction_block, sort_keys=True, separators=(',', ':'), default=str)
    sha = hashlib.sha256(pred_json.encode()).hexdigest()

    if best_2p is not None:
        verdict = f"DOWN_TYPE_2PARAM_MATCH_{best_2p['feature']}"
    else:
        verdict = "DOWN_TYPE_NO_2PARAM_UGP_STRUCTURAL_MATCH_AT_0.5PCT"

    pdg_cmp = {
        'prediction_block_sha256': sha,
        'best_2param_match': best_2p,
        'verdict': verdict,
    }
    return {'prediction_block_precomparison': prediction_block,
            'sha256_prediction_block': sha,
            'pdg_comparison': pdg_cmp}


if __name__ == '__main__':
    out = main()
    path = 'comp_p01_UU_down_lepton_formula_search.json'
    with open(path, 'w') as f:
        json.dump(out, f, indent=2, default=str)
    print()
    print(json.dumps(out['pdg_comparison'], indent=2, default=str))
    print(f"Written: {path}")
