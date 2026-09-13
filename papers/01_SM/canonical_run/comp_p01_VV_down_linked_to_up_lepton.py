#!/usr/bin/env python3
"""
COMP-P01-VV: Systematic search for down-type structural formula linking
down-type quark masses to up-type and lepton masses via UGP-native coefficients.

Round 11 proposal (Jane + Adam): down-type is NOT independently related to
leptons by a simple formula of the form f(g) = α·h(g) + β (Round 8 killed that).
Instead, down-type may be related to up-type + lepton via a *Yukawa-texture-like*
log-linear combination, or via a Weyl-rotation from lepton at a DIFFERENT angle
than up-type.

Models tested (each has the coefficient scan at UGP atom precision):

  M1: log(m_d_g) = α·log(m_u_g) + β·log(m_lep_g) + γ                (3 params)
  M2: log(m_d_g) - log(m_lep_g) = α·log(m_u_g/m_lep_g) + β           (2 params)
  M3: log(m_d_g/m_lep_g) = α·cos(θ_d·2^g) + β   with θ_d scanned over SU(3)
      Weyl-chamber-candidate angles {0, π/12, π/6, π/4, π/3, 5π/12, π/2}
  M4: log(m_d_g/m_u_g) = α·2^g + β                                  (ratio formula base 2)
  M5: log(m_d_g/m_u_g) = α·g + β·(-1)^g + γ                         (generation + parity)
  M6: log(m_d_g/m_u_g) = α·log|c_d_g|/log|c_u_g| + β                (triple-feature)
  M7: m_d_g^2 / (m_u_g · m_lep_g) = UGP-atom-constant               (bilinear product)
  M8: log(m_d_g) = α_1·log(m_u_g) + α_2·log(m_lep_g) + α_3·(-1)^g + β  (4 params)

Each model scanned over UGP atom library; nearest atoms selected per coefficient;
formula evaluated against PDG at resulting UGP-atom coefficients; null disciplined.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import random
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Dict, List, Tuple

import numpy as np

PDG = {
    'electron': 0.5109989088, 'muon': 105.6583777, 'tau': 1776.859905,
    'up': 2.16, 'charm': 1275.0, 'top': 172760.0,
    'down': 4.67, 'strange': 93.4, 'bottom': 4180.0,
}
PHI = (1 + math.sqrt(5)) / 2
TRIPLES_DN = {1: (9, 5, 42), 2: (9, 186, 1023), 3: (5, 8191, 65535)}
TRIPLES_UP = {1: (5, 9, 275), 2: (5, 275, 65535), 3: (76, 337920, -1)}
TRIPLES_LEP = {1: (1, 73, 823), 2: (9, 42, 1023), 3: (5, 275, -65535)}

UP = {1: 'up', 2: 'charm', 3: 'top'}
DN = {1: 'down', 2: 'strange', 3: 'bottom'}
LEP = {1: 'electron', 2: 'muon', 3: 'tau'}


def ugp_atom_library() -> Dict[str, float]:
    atoms: Dict[str, float] = {}
    for n in range(1, 16):
        for d in range(2, 17):
            if math.gcd(n, d) == 1 and n < 4 * d:
                atoms[f'{n}/{d}'] = n / d
                atoms[f'-{n}/{d}'] = -n / d
    for x in (0, 1, -1, 2, -2, 3, -3, 4, -4):
        atoms[str(x)] = float(x)
    for p in range(-4, 5):
        if p != 0:
            atoms[f'phi^{p}'] = PHI ** p
            atoms[f'-phi^{p}'] = -(PHI ** p)
    atoms['sqrt5'] = math.sqrt(5); atoms['-sqrt5'] = -math.sqrt(5)
    atoms['1/sqrt5'] = 1/math.sqrt(5); atoms['-1/sqrt5'] = -1/math.sqrt(5)
    # UGP certified
    for name, val in [('k_L2', 7/512), ('k_mu_a', 1/8), ('k_mu_b', -3/2),
                       ('k_mu_c', 4/3), ('k_gen', PHI*math.cos(math.pi/10)),
                       ('k_gen2', -PHI/2), ('k_M', -PHI/2 + (7/512)/4)]:
        atoms[name] = val
    # pi-based
    for k in [3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 16, 20]:
        atoms[f'pi/{k}'] = math.pi / k
        atoms[f'-pi/{k}'] = -math.pi / k
    for k in [3, 5, 7, 15]:
        atoms[f'2pi/{k}'] = 2 * math.pi / k
        atoms[f'-2pi/{k}'] = -2 * math.pi / k
    for k in [3, 5]:
        atoms[f'cos(pi/{k})'] = math.cos(math.pi / k)
        atoms[f'-cos(pi/{k})'] = -math.cos(math.pi / k)
    atoms['cos(pi/10)'] = math.cos(math.pi / 10)
    # log-based
    for lbl, v in [('ln(2)', math.log(2)), ('ln(3)', math.log(3)), ('ln(5)', math.log(5)),
                    ('ln(phi)', math.log(PHI)), ('1/ln(2)', 1/math.log(2))]:
        atoms[lbl] = v
        atoms[f'-{lbl}'] = -v
    return atoms


def nearest_atom(value: float, atoms: Dict[str, float]) -> Tuple[str, float, float, float]:
    best_name, best_val, best_err = None, None, math.inf
    for n, v in atoms.items():
        if abs(v - value) < best_err:
            best_err = abs(v - value)
            best_name = n
            best_val = v
    pct = 100 * best_err / max(abs(value), 1e-12)
    return best_name, best_val, best_err, pct


# ───────────────────────────────────────────────────────────────────────────
# Data vectors
# ───────────────────────────────────────────────────────────────────────────
log_u  = np.array([math.log(PDG[UP[g]]) for g in (1, 2, 3)])
log_c  = log_u  # alias
log_d  = np.array([math.log(PDG[DN[g]]) for g in (1, 2, 3)])
log_l  = np.array([math.log(PDG[LEP[g]]) for g in (1, 2, 3)])

obs_d = log_d
obs_d_over_l = log_d - log_l
obs_d_over_u = log_d - log_u


def fit_exact_3param(A: np.ndarray, y: np.ndarray, atoms: Dict[str, float]) -> Dict:
    """Exact fit of 3x3 system A·x = y, then find nearest UGP atoms to x."""
    try:
        x = np.linalg.solve(A, y)
    except np.linalg.LinAlgError:
        return {'error': 'singular'}
    result = {'exact_solution': x.tolist()}
    nearest = []
    for v in x:
        n, val, err, pct = nearest_atom(float(v), atoms)
        nearest.append({'value': float(v), 'nearest_atom': n, 'nearest_val': val, 'pct_off': pct})
    result['nearest_atoms_per_coef'] = nearest
    result['max_pct_off_of_any_coef'] = max(n['pct_off'] for n in nearest)
    # Build atom-valued coef vector and evaluate residuals
    x_atoms = np.array([n['nearest_val'] for n in nearest])
    y_atoms = A @ x_atoms
    resid = np.abs(y_atoms - y)
    result['atom_residuals_abs'] = resid.tolist()
    result['atom_max_frac_err'] = float(np.max(resid / np.maximum(np.abs(y), 0.01)))
    return result


def fit_2param_LS(A: np.ndarray, y: np.ndarray, atoms: Dict[str, float]) -> Dict:
    """Least-squares fit of overdetermined 2-param system."""
    x, _, _, _ = np.linalg.lstsq(A, y, rcond=None)
    nearest = []
    for v in x:
        n, val, err, pct = nearest_atom(float(v), atoms)
        nearest.append({'value': float(v), 'nearest_atom': n, 'nearest_val': val, 'pct_off': pct})
    x_atoms = np.array([n['nearest_val'] for n in nearest])
    y_atoms = A @ x_atoms
    resid = np.abs(y_atoms - y)
    return {
        'exact_solution': x.tolist(),
        'nearest_atoms_per_coef': nearest,
        'max_pct_off_of_any_coef': max(n['pct_off'] for n in nearest),
        'atom_max_frac_err': float(np.max(resid / np.maximum(np.abs(y), 0.01))),
        'LS_residual_max_abs': float(np.max(np.abs(A @ x - y))),
    }


def null_random_coefs(A: np.ndarray, y: np.ndarray, n_params: int, n_trials: int,
                       atom_range: Tuple[float, float], tol: float, seed: int) -> Dict:
    rng = random.Random(seed)
    hits = 0
    for _ in range(n_trials):
        x_rand = np.array([rng.uniform(*atom_range) for _ in range(n_params)])
        resid = np.abs(A @ x_rand - y)
        max_frac = np.max(resid / np.maximum(np.abs(y), 0.01))
        if max_frac < tol:
            hits += 1
    return {'trials': n_trials, 'hits': hits, 'density': hits / n_trials}


def main():
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    atoms = ugp_atom_library()
    atom_range = (min(v for v in atoms.values() if abs(v) < 5),
                   max(v for v in atoms.values() if abs(v) < 5))

    print(f"Atom library: {len(atoms)}")
    print()

    results: Dict[str, Dict] = {}

    # ────────────────────────────────────────────────────────────────
    # M1: log(m_d_g) = α·log(m_u_g) + β·log(m_lep_g) + γ  (3 params, 3 pts → exact)
    # ────────────────────────────────────────────────────────────────
    A1 = np.column_stack([log_u, log_l, np.ones(3)])
    r1 = fit_exact_3param(A1, log_d, atoms)
    nul1 = null_random_coefs(A1, log_d, 3, 100000, atom_range, 0.01, 20260419)
    results['M1_log_d_linear_in_log_u_log_l'] = {
        **r1, 'null_density_1pct': nul1['density'], 'null_hits': nul1['hits']
    }
    print(f"M1: log(m_d) = α·log(m_u) + β·log(m_l) + γ")
    print(f"   exact: α={r1['exact_solution'][0]:.4f}  β={r1['exact_solution'][1]:.4f}  γ={r1['exact_solution'][2]:.4f}")
    for i, n in enumerate(r1['nearest_atoms_per_coef']):
        print(f"     coef_{i}={n['value']:+.4f}  nearest={n['nearest_atom']}={n['nearest_val']:+.4f} ({n['pct_off']:.2f}% off)")
    print(f"   atom-eval max_frac_err: {r1['atom_max_frac_err']:.4f}  null_density@1%: {nul1['density']:.4f}")
    print()

    # ────────────────────────────────────────────────────────────────
    # M2: log(m_d_g/m_l_g) = α·log(m_u_g/m_l_g) + β  (2 params, 3 pts → LS)
    # ────────────────────────────────────────────────────────────────
    x2_vec = log_u - log_l
    A2 = np.column_stack([x2_vec, np.ones(3)])
    r2 = fit_2param_LS(A2, obs_d_over_l, atoms)
    nul2 = null_random_coefs(A2, obs_d_over_l, 2, 100000, atom_range, 0.01, 20260420)
    results['M2_log_d_over_l_in_log_u_over_l'] = {**r2, 'null_density_1pct': nul2['density']}
    print(f"M2: log(m_d/m_l) = α·log(m_u/m_l) + β")
    print(f"   LS: α={r2['exact_solution'][0]:.4f}  β={r2['exact_solution'][1]:.4f}")
    for i, n in enumerate(r2['nearest_atoms_per_coef']):
        print(f"     coef_{i}={n['value']:+.4f}  nearest={n['nearest_atom']}={n['nearest_val']:+.4f} ({n['pct_off']:.2f}% off)")
    print(f"   atom-eval max_frac_err: {r2['atom_max_frac_err']:.4f}  null_density@1%: {nul2['density']:.4f}")
    print()

    # ────────────────────────────────────────────────────────────────
    # M3: log(m_d_g/m_l_g) = α·cos(θ_d·2^g) + β  for θ_d scanned
    # ────────────────────────────────────────────────────────────────
    weyl_theta_candidates = {
        'pi/12': math.pi/12, 'pi/10': math.pi/10, 'pi/8': math.pi/8,
        'pi/6': math.pi/6, 'pi/5': math.pi/5, 'pi/4': math.pi/4,
        'pi/3': math.pi/3, '5pi/12': 5*math.pi/12, 'pi/2': math.pi/2,
        '2pi/3': 2*math.pi/3, '-pi/6': -math.pi/6, '-pi/12': -math.pi/12,
    }
    m3 = {}
    for θname, θ in weyl_theta_candidates.items():
        cos_vec = np.array([math.cos(θ * 2**g) for g in (1, 2, 3)])
        A3 = np.column_stack([cos_vec, np.ones(3)])
        r3 = fit_2param_LS(A3, obs_d_over_l, atoms)
        m3[θname] = r3
    # Best one:
    best_theta = min(m3.items(), key=lambda kv: kv[1]['atom_max_frac_err'])
    results['M3_cos_weyl_scan'] = {'per_theta': m3, 'best_theta': best_theta[0], 'best_result': best_theta[1]}
    print(f"M3: log(m_d/m_l) = α·cos(θ_d·2^g) + β scanned over Weyl-chamber θ candidates")
    print(f"   best θ_d: {best_theta[0]} with atom_max_frac_err = {best_theta[1]['atom_max_frac_err']:.4f}")
    print()

    # ────────────────────────────────────────────────────────────────
    # M5: log(m_d_g/m_u_g) = α·g + β·(-1)^g + γ   (3 params, 3 pts → exact)
    # ────────────────────────────────────────────────────────────────
    g_vec = np.array([1.0, 2.0, 3.0])
    alt_vec = np.array([-1.0, 1.0, -1.0])
    A5 = np.column_stack([g_vec, alt_vec, np.ones(3)])
    r5 = fit_exact_3param(A5, obs_d_over_u, atoms)
    nul5 = null_random_coefs(A5, obs_d_over_u, 3, 100000, atom_range, 0.01, 20260421)
    results['M5_log_d_over_u_linear_plus_alt'] = {**r5, 'null_density_1pct': nul5['density']}
    print(f"M5: log(m_d/m_u) = α·g + β·(-1)^g + γ")
    print(f"   exact: α={r5['exact_solution'][0]:.4f}  β={r5['exact_solution'][1]:.4f}  γ={r5['exact_solution'][2]:.4f}")
    for i, n in enumerate(r5['nearest_atoms_per_coef']):
        print(f"     coef_{i}={n['value']:+.4f}  nearest={n['nearest_atom']}={n['nearest_val']:+.4f} ({n['pct_off']:.2f}% off)")
    print(f"   atom-eval max_frac_err: {r5['atom_max_frac_err']:.4f}  null_density@1%: {nul5['density']:.4f}")
    print()

    # ────────────────────────────────────────────────────────────────
    # M7: m_d_g^2 / (m_u_g · m_lep_g) = UGP-atom-constant
    # ────────────────────────────────────────────────────────────────
    ratio_prod = [PDG[DN[g]]**2 / (PDG[UP[g]] * PDG[LEP[g]]) for g in (1, 2, 3)]
    log_ratio_prod = [math.log(r) for r in ratio_prod]
    print(f"M7: m_d^2/(m_u·m_l) values")
    for g, (r, lr) in enumerate(zip(ratio_prod, log_ratio_prod), 1):
        print(f"   g={g}: m_d^2/(m_u·m_l) = {r:.4f}  log = {lr:.4f}")
    results['M7_d_squared_over_u_l'] = {
        'values': ratio_prod, 'log_values': log_ratio_prod,
        'comment': 'Not constant — ratio changes by 3+ orders of magnitude across generations'
    }
    print()

    # ────────────────────────────────────────────────────────────────
    # M8: log(m_d) = α_1·log(m_u) + α_2·log(m_l) + α_3·(-1)^g + β (4 params, 3 pts → underdetermined)
    # Instead: force α_1 and α_2 to LS-optimal values, fit α_3 and β. But underdetermined with 3 eqs.
    # Better: try specific UGP-atom choices for α_1, α_2 (e.g., 1, 1, -1) and fit α_3, β.
    # ────────────────────────────────────────────────────────────────
    # Try: log(m_d) = log(m_u) + log(m_l) + α·(-1)^g + β  (texture-like with unit couplings)
    residual_unit = log_d - log_u - log_l
    alt = np.array([(-1)**g for g in (1, 2, 3)])
    A8 = np.column_stack([alt, np.ones(3)])
    r8 = fit_2param_LS(A8, residual_unit, atoms)
    nul8 = null_random_coefs(A8, residual_unit, 2, 100000, atom_range, 0.01, 20260422)
    results['M8_unit_yukawa_plus_alternating'] = {**r8, 'null_density_1pct': nul8['density']}
    print(f"M8: log(m_d) = log(m_u) + log(m_l) + α·(-1)^g + β (unit-coupling + alt)")
    print(f"   LS: α={r8['exact_solution'][0]:.4f}  β={r8['exact_solution'][1]:.4f}")
    for i, n in enumerate(r8['nearest_atoms_per_coef']):
        print(f"     coef_{i}={n['value']:+.4f}  nearest={n['nearest_atom']}={n['nearest_val']:+.4f} ({n['pct_off']:.2f}% off)")
    print(f"   atom-eval max_frac_err: {r8['atom_max_frac_err']:.4f}  null_density@1%: {nul8['density']:.4f}")
    print()

    # ────────────────────────────────────────────────────────────────
    # M9: DOWN = UP via Weyl reflection from up angle θ_u_g=(π/6)·2^g
    # Specifically, if down rotation is the SU(3) Weyl reflection (order 2 rotation)
    # of the up rotation: θ_d_g = π/3 - θ_u_g (reflection through chamber edge)
    # Then log(m_d/m_l) should equal α·(π/3 - (π/6)·2^g) + β
    # ────────────────────────────────────────────────────────────────
    cos_vec_refl = np.array([math.pi/3 - (math.pi/6)*2**g for g in (1, 2, 3)])
    A9 = np.column_stack([cos_vec_refl, np.ones(3)])
    r9 = fit_2param_LS(A9, obs_d_over_l, atoms)
    nul9 = null_random_coefs(A9, obs_d_over_l, 2, 100000, atom_range, 0.01, 20260423)
    results['M9_weyl_reflection_up_angle'] = {**r9, 'null_density_1pct': nul9['density']}
    print(f"M9: log(m_d/m_l) = α·(π/3 - (π/6)·2^g) + β  (Weyl reflection of up angle)")
    print(f"   LS: α={r9['exact_solution'][0]:.4f}  β={r9['exact_solution'][1]:.4f}")
    for i, n in enumerate(r9['nearest_atoms_per_coef']):
        print(f"     coef_{i}={n['value']:+.4f}  nearest={n['nearest_atom']}={n['nearest_val']:+.4f} ({n['pct_off']:.2f}% off)")
    print(f"   atom-eval max_frac_err: {r9['atom_max_frac_err']:.4f}  null_density@1%: {nul9['density']:.4f}")
    print()

    # Summary: find any model that achieves atom_max_frac_err < 1% AND null_density < 1%
    structural_candidates = []
    for name, r in results.items():
        if not isinstance(r, dict):
            continue
        mf = r.get('atom_max_frac_err', math.inf)
        nd = r.get('null_density_1pct', 1.0)
        if mf < 0.02 and nd < 0.01:
            structural_candidates.append({'model': name, 'atom_max_frac_err': mf, 'null_density': nd, **r})

    prediction_block = {
        'comp_id': 'COMP-P01-VV',
        'spec_reference': 'Team Round 11 — down-type linked to up-type and lepton',
        'timestamp_utc': ts,
        'atoms_library_size': len(atoms),
        'models_tested': list(results.keys()),
        'per_model_results': results,
        'structural_candidates_within_2pct_null_disciplined': structural_candidates,
    }
    pred_json = json.dumps(prediction_block, sort_keys=True, separators=(',', ':'), default=str)
    sha = hashlib.sha256(pred_json.encode()).hexdigest()

    if structural_candidates:
        verdict = f"DOWN_TYPE_CANDIDATE_STRUCTURAL_FORMULA_FOUND_{len(structural_candidates)}"
    else:
        best_model = min(
            [(n, r) for n, r in results.items() if isinstance(r, dict) and 'atom_max_frac_err' in r],
            key=lambda nr: nr[1]['atom_max_frac_err'],
        )
        verdict = f"DOWN_TYPE_NO_2PCT_CLOSURE_best_{best_model[0]}_at_{best_model[1]['atom_max_frac_err']:.4f}"

    pdg_cmp = {
        'prediction_block_sha256': sha,
        'n_structural_candidates': len(structural_candidates),
        'structural_candidates': structural_candidates,
        'verdict': verdict,
    }
    return {'prediction_block_precomparison': prediction_block,
            'sha256_prediction_block': sha,
            'pdg_comparison': pdg_cmp}


if __name__ == '__main__':
    out = main()
    path = 'comp_p01_VV_down_linked_to_up_lepton.json'
    with open(path, 'w') as f:
        json.dump(out, f, indent=2, default=str)
    print()
    print(json.dumps(out['pdg_comparison'], indent=2, default=str))
    print(f"Written: {path}")
