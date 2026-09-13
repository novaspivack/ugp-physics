#!/usr/bin/env python3
"""
COMP-P01-XX: GUT / Lie-theoretic structural search for the down-type coefficients.

Priority 1 (Round 12): we want to find a structural origin for the down-type
formula coefficients (13/9, -7/6, -5/14) that appear in

    log(m_{d_g}) = (13/9)·log(m_{u_g}) + (-7/6)·log(m_{lep_g}) + (-5/14)

Candidate structural sources tested:

(A) Standard Model hypercharge combinations
    Y_Q = 1/6, Y_u = 2/3, Y_d = -1/3, Y_L = -1/2, Y_e = -1
    Search all bilinear / ratio combinations matching (13/9, -7/6, -5/14)
    at ≤ 1% precision.

(B) SU(5) Georgi-Jarlskog Clebsch-Gordan coefficients
    The 5⊕45 Higgs mix in SU(5) gives (3, 1/3, 1) for (m_d/m_e, m_s/m_μ, m_b/m_τ)
    at GUT scale. Test: do (13/9, -7/6, -5/14) emerge from these?

(C) SO(10) 10⊕126 Higgs mix with Dirac mass relations
    SO(10) predicts specific CG ratios between m_d, m_u, m_lep, m_nu. Check if
    our coefs match.

(D) UGP ridge-derived rationals
    Ridge level n=10, ridge value 2^10 - 16 = 1008 = 2^4 · 3² · 7. Test if coefs
    are simple combinations of ridge factors.

(E) Dimensional/representation-theoretic combinations
    dim(fund SU(3)) = 3, dim(adj SU(3)) = 8, rank(SU(3)) = 2.
    dim(fund SU(2)) = 2, dim(adj SU(2)) = 3, rank(SU(2)) = 1.
    dim(fund SU(5)) = 5, rank(SU(5)) = 4, dim(adj SU(5)) = 24.
    Test combinations.

Outputs: for each coefficient (13/9, -7/6, -5/14), the best structural
explanation candidate from the above sources and its deviation.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from datetime import datetime, timezone
from fractions import Fraction
from typing import Dict, List, Tuple

PHI = (1 + math.sqrt(5)) / 2

TARGET_COEFS = {'13/9': 13/9, '-7/6': -7/6, '-5/14': -5/14}


# Hypercharge library
HYPERCHARGE = {
    'Y_Q': Fraction(1, 6),
    'Y_u': Fraction(2, 3),
    'Y_d': Fraction(-1, 3),
    'Y_L': Fraction(-1, 2),
    'Y_e': Fraction(-1, 1),
    # Normalized SU(5) hypercharge:
    'Y_Q_sqrt53': Fraction(1, 6),
    # Squared hypercharges (for β-function pieces):
    'Y_Q_sq_x_2_x_3c': Fraction(1, 6) ** 2 * 2 * 3,   # = 1/6  (Q doublet, 3 colors)
    'Y_u_sq_x_3c':     Fraction(2, 3) ** 2 * 3,       # = 4/3
    'Y_d_sq_x_3c':     Fraction(-1, 3) ** 2 * 3,      # = 1/3
    'Y_L_sq_x_2':      Fraction(-1, 2) ** 2 * 2,      # = 1/2
    'Y_e_sq':          Fraction(-1, 1) ** 2,          # = 1
}


# Standard group-theory integers
GROUP_INTS = {
    'rank_SU2': 1, 'dim_fund_SU2': 2, 'dim_adj_SU2': 3,
    'rank_SU3': 2, 'dim_fund_SU3': 3, 'dim_adj_SU3': 8,
    'rank_SU5': 4, 'dim_fund_SU5': 5, 'dim_adj_SU5': 24, 'dim_10_SU5': 10, 'dim_45_SU5': 45,
    'rank_SO10': 5, 'dim_fund_SO10': 10, 'dim_spinor_SO10': 16, 'dim_adj_SO10': 45, 'dim_126_SO10': 126,
    'rank_E6': 6, 'dim_fund_E6': 27, 'dim_adj_E6': 78,
    # Ridge-specific UGP integers
    'ridge_n': 10, 'ridge_value_1008': 1008, 'D1': 16, 'mirror_sum': 24 + 42, 'D5_order': 5,
    'S3_order': 6, 'A4_order': 12, 'A5_order': 60,
    # Small primes
    'p_2': 2, 'p_3': 3, 'p_5': 5, 'p_7': 7, 'p_11': 11, 'p_13': 13, 'p_17': 17, 'p_19': 19,
    # Specific
    'Casimir_fund_SU3_times_4': 16,  # 4·C_2(3) with C_2(3) = 4/3
    '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
    '11': 11, '12': 12, '13': 13, '14': 14, '15': 15, '16': 16, '18': 18,
}


def search_rational_from_ratios(target: Fraction, library: Dict[str, int], max_pct: float = 1.0) -> List[Dict]:
    """Search for target = a/b where a, b are in library."""
    target_f = float(target)
    hits = []
    for n_name, n_val in library.items():
        for d_name, d_val in library.items():
            if d_val == 0:
                continue
            for s in (+1, -1):
                candidate = s * n_val / d_val
                if abs(candidate - target_f) / max(abs(target_f), 1e-12) * 100 < max_pct:
                    hits.append({
                        'formula': f'{"+" if s > 0 else "-"}{n_name}/{d_name}',
                        'value': candidate,
                        'target': target_f,
                        'pct_off': abs(candidate - target_f) / max(abs(target_f), 1e-12) * 100,
                    })
    return sorted(hits, key=lambda h: h['pct_off'])[:20]


def search_rational_as_sum_of_two(target: float, library: Dict[str, int], max_pct: float = 0.5) -> List[Dict]:
    """Search for target = a1/b1 + a2/b2 or a1·a2/b with small integers."""
    hits = []
    for n1_name, n1 in library.items():
        for d1_name, d1 in library.items():
            if d1 == 0:
                continue
            for s1 in (+1, -1):
                val1 = s1 * n1 / d1
                for n2_name, n2 in library.items():
                    for d2_name, d2 in library.items():
                        if d2 == 0:
                            continue
                        for s2 in (+1, -1):
                            val2 = s2 * n2 / d2
                            s = val1 + val2
                            if abs(s - target) / max(abs(target), 1e-12) * 100 < max_pct:
                                hits.append({
                                    'formula': f'{"+" if s1>0 else "-"}{n1_name}/{d1_name} {"+" if s2>0 else "-"}{n2_name}/{d2_name}',
                                    'value': s,
                                    'pct_off': abs(s - target) / max(abs(target), 1e-12) * 100,
                                })
    # dedupe by formula
    seen = set()
    out = []
    for h in sorted(hits, key=lambda h: h['pct_off']):
        # normalize formula (sort terms)
        parts = sorted(h['formula'].split())
        k = tuple(parts)
        if k not in seen:
            seen.add(k)
            out.append(h)
        if len(out) >= 20:
            break
    return out


def test_georgi_jarlskog() -> Dict:
    """Standard SU(5) + (5H, 45H) Higgs mix predictions."""
    cg_ratios = {'m_d/m_e': 3, 'm_s/m_μ': Fraction(1, 3), 'm_b/m_τ': 1}
    # Test if our coefs can arise from CG:
    notes = {
        '13/9': 'Not an obvious Georgi-Jarlskog coefficient. GJ gives (3, 1/3, 1) per generation, not a ratio structure across sectors.',
        '-7/6': 'Could relate to GJ via (1 - 1/6) where 1/6 is Y_Q hypercharge.',
        '-5/14': 'Not a standard GJ coefficient.',
    }
    return {'GJ_coefficients': {str(k): float(v) for k, v in cg_ratios.items()}, 'notes': notes}


def main() -> Dict:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    results: Dict[str, Dict] = {}

    # (A) Ratios of group-theory integers
    for coef_name, target in TARGET_COEFS.items():
        target_f = Fraction(target).limit_denominator(1000)
        hits_ratio = search_rational_from_ratios(target_f, GROUP_INTS, max_pct=0.5)
        hits_sum = search_rational_as_sum_of_two(float(target), GROUP_INTS, max_pct=0.3)
        results[coef_name] = {
            'target_value': float(target),
            'target_exact_rational': f'{target_f.numerator}/{target_f.denominator}',
            'ratio_hits': hits_ratio[:10],
            'sum_of_two_hits': hits_sum[:10],
        }

    # (B) Georgi-Jarlskog
    gj = test_georgi_jarlskog()
    results['georgi_jarlskog'] = gj

    # (C) Check key combinations by hand
    hand_checks: List[Dict] = []

    # hand: 13/9 = 1 + 4/9 — where 4/9 could be what?
    hand_checks.append({
        'proposal': '13/9 = 1 + 4/9, with 4/9 = hypercharge ratio?',
        'compute': '1 + (Y_u + Y_d)^2 / ?',
        'raw': 1 + (Fraction(2,3) + Fraction(-1,3))**2,  # = 1 + 1/9 = 10/9; not 13/9
        'match': '10/9 ≠ 13/9',
    })

    hand_checks.append({
        'proposal': '13/9 = 1 + 4/9, where 4/9 = 4·Y_Q_sq = 4·(1/6)² = 1/9; ×4 = 4/9',
        'compute': '1 + 4·Y_Q²·?',
        'raw': float(1 + 4 * Fraction(1,6)**2),  # = 1 + 1/9 = 10/9; not right
        'match': 'Gets us 1 + 1/9 = 10/9, not 13/9',
    })

    # Direct:
    hand_checks.append({
        'proposal': '13/9 from SM anomaly-free condition?',
        'compute': 'Y_u² · 3c / Y_L² · 2 = (4/3) / (1/2) = 8/3 = 24/9; not 13/9',
        'raw': float(Fraction(4,3) / Fraction(1,2)),
        'match': '24/9 = 8/3 ≠ 13/9',
    })

    # -7/6 = Y_Q + something?
    hand_checks.append({
        'proposal': '-7/6 = -1 - 1/6 = -1 - Y_Q',
        'compute': '-(1 + Y_Q) = -(1 + 1/6) = -7/6',
        'raw': float(-(1 + Fraction(1,6))),
        'match': 'EXACT: -7/6 = -(1 + Y_Q_SM_hypercharge)',
    })

    # -5/14 = ???
    hand_checks.append({
        'proposal': '-5/14 = -D_5_order / (2 · p_7)',
        'compute': '-5 / (2·7)',
        'raw': float(Fraction(-5, 14)),
        'match': 'EXACT by construction — but is 2·7 a known UGP integer?',
    })

    # -5/14 = k_L2 / something? 
    # k_L2 = 7/512. -5/14 × (7/512)⁻¹ = -5/14 × 512/7 = -5·512/(14·7) = -2560/98 ≈ -26.12. No.
    # -5/14 expressed using ridge ingredients: ridge_n = 10, D1 = 16, δ = 7.
    # Ridge delta/divisor = 7/divisor. If divisor = -14/5, no.
    # 7/1008 (ridge value) = 1/144, not useful.

    # 13/9 from ridge factor?
    # ridge = 1008 = 2^4 · 3² · 7. 
    # 13/9 is 13/3². 9 = 3² is related to ridge. 13 = ?  Note 13 - 7 = 6 = |S_3|. 
    # 13/9 = (6 + 7)/9 = (|S_3| + 7)/9 = (|S_3| + k_L2_num) / 9
    hand_checks.append({
        'proposal': '13/9 = (|S_3| + 7) / 9 where |S_3| = 6 is Weyl(SU(3)) and 7 is k_L2_numerator',
        'compute': '(6 + 7) / 9 = 13/9',
        'raw': (6 + 7) / 9,
        'match': 'EXACT: numerical identity holds',
        'interpretation': 'Conjectural — |S_3|=6 is Weyl group of SU(3); 7 is UGP k_L² numerator (ridge-derived).'
                          ' 9=3² is rank-squared of SU(3). But this is a numeric rewrite, not a derivation.',
    })

    results['hand_checks'] = hand_checks

    # Important observation: 5/18 = (13/9 + (-7/6))·(-1) — no, let me check
    # 13/9 - 7/6 = 26/18 - 21/18 = 5/18
    # 13/9 + 7/6 = 26/18 + 21/18 = 47/18
    # Not clean
    # (13/9) · (-7/6) = -91/54 — not recognizable
    # 13·7 = 91, which factors as 7·13 (both prime)
    # 9·6 = 54 = 2·27 = 2·3³
    # 13/9 + (-5/14) = 13·14/(9·14) - 5·9/(9·14) = (182-45)/126 = 137/126 (= 1.087)
    # Nothing structural there.

    # Summary and verdict
    summary = {
        'most_compelling_structural_matches': [
            {
                'coefficient': '-7/6',
                'interpretation': '-(1 + Y_Q_SM_hypercharge)  where Y_Q = 1/6 is the SM left-handed quark doublet hypercharge',
                'exactness': 'EXACT',
                'confidence': 'moderate — the association to Y_Q is specific and suggestive, but could be coincidence',
            },
            {
                'coefficient': '13/9',
                'interpretation': '(|W(SU(3))| + k_L²_numerator) / rank(SU(3))² = (6 + 7) / 9 = 13/9',
                'exactness': 'EXACT (by construction)',
                'confidence': 'low-to-moderate — numerical rewrite, not a derivation; needs Lie-theoretic or UGP-ridge justification for why |S_3| and k_L2 enter this combination.',
            },
            {
                'coefficient': '-5/14',
                'interpretation': '-D_5_order / (2·k_L²_numerator) = -5/14',
                'exactness': 'EXACT (by construction)',
                'confidence': 'low — no natural physical motivation for 2·7 as a denominator',
            },
        ],
        'overall_verdict': 'Suggestive but not yet STRUCTURAL. The -7/6 = -(1 + Y_Q) identification is the strongest single piece of evidence for a hypercharge-derived origin. The other two coefficients have exact rational rewrites using UGP-structural integers (|S_3|, k_L², D_5, rank(SU(3))) but no clean geometric / representation-theoretic derivation. Priority 1 verdict: partial progress, requires focused mathematical research to identify the underlying structural theorem.',
        'recommended_next_investigations': [
            '1. Compute SU(5) and SO(10) Clebsch-Gordan decompositions for 10·5̄·45 and 16·16·126 Yukawa terms; check if (13/9, -7/6, -5/14) emerge from specific matrix elements.',
            '2. Test whether the coefficients match ratios of ridge-derived spectra for the Fibonacci characteristic polynomial or the GTE cascade eigenstructure.',
            '3. Search for a common underlying 2-parameter family where the three coefficients are a single tuple — e.g., (α, β, γ) = (p, -q-1/6, -r/q) with p=13/9, q=1 (so -1-1/6 = -7/6), r=5/14/1 ... requires more thought.',
            '4. Explore whether the down-type relation is the image of a UGP operator, where the operator itself has a structural derivation and the coefficients are its eigenvalues/characteristic numbers.',
        ],
    }

    prediction_block = {
        'comp_id': 'COMP-P01-XX',
        'spec_reference': 'Round 12 Priority 1 — GUT / Lie-theoretic search for down-type coefficients',
        'timestamp_utc': ts,
        'target_coefficients': {k: float(v) for k, v in TARGET_COEFS.items()},
        'hypercharge_library': {k: float(v) for k, v in HYPERCHARGE.items()},
        'group_theory_integer_library': GROUP_INTS,
        'results_per_coefficient': results,
        'structural_summary': summary,
    }
    pred_json = json.dumps(prediction_block, sort_keys=True, separators=(',', ':'), default=str)
    sha = hashlib.sha256(pred_json.encode()).hexdigest()

    return {'prediction_block_precomparison': prediction_block, 'sha256_prediction_block': sha}


if __name__ == '__main__':
    out = main()
    path = 'comp_p01_XX_gut_structure_search.json'
    with open(path, 'w') as f:
        json.dump(out, f, indent=2, default=str)
    pb = out['prediction_block_precomparison']
    print('\n=== GUT / Lie-theoretic search for down-type coefficients ===\n')
    for coef_name in ['13/9', '-7/6', '-5/14']:
        r = pb['results_per_coefficient'][coef_name]
        print(f'Coefficient {coef_name} = {r["target_value"]:.5f}')
        print('  Top ratio matches in group-theory integer library:')
        for h in r['ratio_hits'][:3]:
            print(f'    {h["formula"]:30s}  = {h["value"]:.5f}  ({h["pct_off"]:.3f}% off)')
        print('  Top sum-of-two matches:')
        for h in r['sum_of_two_hits'][:3]:
            print(f'    {h["formula"]:50s} = {h["value"]:.5f}  ({h["pct_off"]:.3f}% off)')
        print()
    print('\n=== Hand-checked structural proposals ===')
    for hc in pb['results_per_coefficient']['hand_checks']:
        print(f'  {hc["proposal"]}')
        print(f'    Compute: {hc["compute"]}')
        print(f'    Match: {hc["match"]}')
    print(f'\nOverall verdict: {pb["structural_summary"]["overall_verdict"][:200]}...')
    print(f'\nSHA-256: {out["sha256_prediction_block"]}')
    print(f'Written: {path}')
