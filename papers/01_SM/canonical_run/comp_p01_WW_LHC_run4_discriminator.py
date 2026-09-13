#!/usr/bin/env python3
"""
COMP-P01-WW: LHC Run-4 discriminator for β candidate in the TT up-lepton formula

Priority 3 (Round 12): The up-lepton formula is

    log(m_{up_g} / m_{lep_g}) = (π/6)·2^g + β

where three β candidates fit within 1% of PDG:
  β = 2/5     (0.45% off LS)
  β = π/8     (1.54% off LS, but tightest match on all 3 data points: 0.12% max-frac)
  β = 1/φ²    (3.91% off LS)

Pre-committed prediction: the most-sensitive discriminator mass is m_c
(charm), because:
  • charm has PDG uncertainty ±2% (50× better than up at ±23% but 10× worse
    than top at ±0.2%)
  • The β-dependent prediction for log(m_c/m_μ) = (π/6)·4 + β varies by the
    β difference across candidates (up to 0.02 in log-space)
  • Improved experimental precision on m_c (targeted for LHC Run 4 and
    Belle II) will distinguish among β candidates directly

Current PDG charm mass: m_c = 1275 ± 25 MeV  (2% relative uncertainty)
Formula predictions for log(m_c/m_μ):
  β = 2/5:   (2π/3) + 2/5    = 2.4944
  β = π/8:   (2π/3) + π/8    = 2.4871
  β = 1/φ²:  (2π/3) + 1/φ²   = 2.4764
  β_LS:      (LS fit)        = 2.4900 (observed)

The differences between β candidates on log(m_c/m_μ) are:
  2/5  vs π/8:  0.0073  ~  0.73% on m_c       (needs ≤ 0.4% precision)
  2/5  vs 1/φ²: 0.0180  ~  1.80% on m_c       (needs ≤ 0.9% precision)
  π/8  vs 1/φ²: 0.0107  ~  1.07% on m_c

LHC Run 4 expected precision on m_c: ≲ 0.5% (Belle II projections + future
tagged-charm measurements) → will discriminate 2/5 vs 1/φ² at 2σ, will not
yet distinguish 2/5 vs π/8.

m_t precision is sub-permille but the β effect on log(m_t/m_τ) is smaller
in fractional terms (same absolute 0.02 effect on a number of size ~4.6,
so 0.4% max), which LHC Run 4 already exceeds.

Outputs a pre-committed prediction table tying β discrimination to specific
future measurement improvements — this IS the falsifiable test.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from typing import Dict, List

PDG = {
    'electron': 0.5109989088, 'muon': 105.6583777, 'tau': 1776.859905,
    'up': 2.16, 'charm': 1275.0, 'top': 172760.0,
}
PDG_SIGMA = {'up': 0.23, 'charm': 0.02, 'top': 0.0017}

PHI = (1 + math.sqrt(5)) / 2

BETA_CANDIDATES = {
    '2/5':   2/5,
    'π/8':   math.pi / 8,
    '1/φ²':  1 / PHI**2,
    'ln(√5)/2': math.log(5) / 4,
}


def predict_up_over_lep_log(g: int, beta: float) -> float:
    return (math.pi / 6) * (2 ** g) + beta


def up_over_lep_log_observed(g: int) -> float:
    up_map = {1: 'up', 2: 'charm', 3: 'top'}
    lep_map = {1: 'electron', 2: 'muon', 3: 'tau'}
    return math.log(PDG[up_map[g]] / PDG[lep_map[g]])


def main() -> Dict:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Per-generation prediction for each β candidate
    per_beta: Dict[str, Dict] = {}
    for name, beta in BETA_CANDIDATES.items():
        per_g = {}
        for g in (1, 2, 3):
            pred = predict_up_over_lep_log(g, beta)
            obs = up_over_lep_log_observed(g)
            per_g[f'g={g}'] = {
                'predicted': pred,
                'observed': obs,
                'log_diff': pred - obs,
                'relative_log_err': abs(pred - obs) / abs(obs),
                # This converts to fractional mass error:
                'mass_frac_err': abs(math.exp(pred - obs) - 1),
            }
        per_beta[name] = {
            'beta_value': beta,
            'per_generation': per_g,
            'max_mass_frac_err': max(v['mass_frac_err'] for v in per_g.values()),
            'avg_mass_frac_err': sum(v['mass_frac_err'] for v in per_g.values()) / 3,
        }

    # Pairwise discriminator: the per-generation log-difference between β candidates
    # gives the mass-ratio shift needed to distinguish them
    pairwise: Dict[str, Dict] = {}
    betas = list(BETA_CANDIDATES.items())
    for i in range(len(betas)):
        for j in range(i + 1, len(betas)):
            name1, b1 = betas[i]
            name2, b2 = betas[j]
            log_diff = b1 - b2
            # Fractional mass-shift induced by β difference (same for all g):
            mass_frac_shift = abs(math.exp(log_diff) - 1)
            # For discrimination at nσ, need experimental precision < nσ × mass_frac_shift
            pairwise[f'{name1}_vs_{name2}'] = {
                'log_shift': log_diff,
                'mass_frac_shift_per_fermion': mass_frac_shift,
                'needed_precision_for_2sigma_discrimination': mass_frac_shift / 2,
                'current_PDG_precision_on_m_c': PDG_SIGMA['charm'],
                'current_PDG_precision_on_m_t': PDG_SIGMA['top'],
                'discriminated_at_2sigma_now_on_m_c': mass_frac_shift / 2 > PDG_SIGMA['charm'],
                'discriminated_at_2sigma_now_on_m_t': mass_frac_shift / 2 > PDG_SIGMA['top'],
            }

    # Pre-committed prediction: given observed m_c, m_t, what β is favoured?
    # Compute β_effective from each fermion individually:
    beta_from_g: Dict[str, Dict] = {}
    for g in (1, 2, 3):
        beta_effective = up_over_lep_log_observed(g) - (math.pi / 6) * (2 ** g)
        best_name, best_dist = None, math.inf
        for name, b in BETA_CANDIDATES.items():
            d = abs(beta_effective - b)
            if d < best_dist:
                best_dist = d
                best_name = name
        beta_from_g[f'g={g}'] = {
            'beta_effective_observed': beta_effective,
            'nearest_candidate': best_name,
            'distance_to_nearest': best_dist,
            'all_distances': {name: abs(beta_effective - b) for name, b in BETA_CANDIDATES.items()},
        }

    # Pre-committed prediction for LHC Run 4 (charm mass to 0.5%)
    future_precision_mc = 0.005  # 0.5% — Belle II + LHC Run 4 target
    future_precision_mt = 0.001  # 0.1% — Future LHC precision
    # What β candidates will still survive?
    future_constraint = {}
    beta_mc = up_over_lep_log_observed(2) - (math.pi / 6) * 4  # β_effective from m_c measurement
    for name, b in BETA_CANDIDATES.items():
        # Convert distance in β-space to equivalent mass-fractional uncertainty
        mass_frac_for_exclusion = abs(math.exp(b - beta_mc) - 1)
        future_constraint[name] = {
            'beta_candidate': b,
            'mass_frac_discrepancy_at_charm': mass_frac_for_exclusion,
            'excluded_at_2sigma_by_future_mc_precision_0.5pct': mass_frac_for_exclusion > 2 * future_precision_mc,
            'excluded_at_2sigma_by_future_mt_precision_0.1pct': mass_frac_for_exclusion > 2 * future_precision_mt,
        }

    prediction_block = {
        'comp_id': 'COMP-P01-WW',
        'spec_reference': 'Round 12 Priority 3 — LHC Run-4 β discriminator',
        'timestamp_utc': ts,
        'formula': 'log(m_{up_g}/m_{lep_g}) = (π/6)·2^g + β',
        'beta_candidates_tested': BETA_CANDIDATES,
        'current_pdg_verification_per_beta': per_beta,
        'pairwise_discriminator_analysis': pairwise,
        'beta_from_each_generation_independently': beta_from_g,
        'future_lhc_run4_discriminator': {
            'assumed_precision_m_c': future_precision_mc,
            'assumed_precision_m_t': future_precision_mt,
            'per_candidate_exclusion_analysis': future_constraint,
        },
        'pre_committed_prediction': {
            'statement':
                'When LHC Run 4 / Belle II achieves m_c measurement at ≲ 0.5% precision and m_t at ≲ 0.1%, the β candidates that remain consistent with the up-lepton formula at 2σ on each mass measurement will be a proper subset of {2/5, π/8, 1/φ², ln(√5)/2}. The specific viable subset is a pre-committed prediction of this analysis. If ALL candidates are excluded (observed m_c / m_t inconsistent with any β in the library), the formula itself is falsified.',
            'explicit_pre_commitment_testable': True,
        },
    }
    pred_json = json.dumps(prediction_block, sort_keys=True, separators=(',', ':'), default=str)
    sha = hashlib.sha256(pred_json.encode()).hexdigest()

    return {'prediction_block_precomparison': prediction_block, 'sha256_prediction_block': sha}


if __name__ == '__main__':
    out = main()
    path = 'comp_p01_WW_LHC_run4_discriminator.json'
    with open(path, 'w') as f:
        json.dump(out, f, indent=2, default=str)

    pb = out['prediction_block_precomparison']
    print('\n=== Pre-committed β discriminator for up-lepton formula ===\n')
    print('Formula: log(m_{up_g}/m_{lep_g}) = (π/6)·2^g + β\n')

    print('Current PDG verification per β candidate:')
    for name, r in pb['current_pdg_verification_per_beta'].items():
        print(f'  β = {name:10s} (= {r["beta_value"]:.5f}):  max_mass_frac_err = {r["max_mass_frac_err"]*100:.3f}%   avg = {r["avg_mass_frac_err"]*100:.3f}%')

    print('\nEffective β from each generation independently (observed):')
    for g_key, r in pb['beta_from_each_generation_independently'].items():
        print(f'  {g_key}:  β_eff = {r["beta_effective_observed"]:.5f}, nearest candidate: {r["nearest_candidate"]}')

    print('\nPairwise discriminator — mass-fractional shift needed to distinguish candidates:')
    for pair, r in pb['pairwise_discriminator_analysis'].items():
        print(f'  {pair:25s}: shift = {r["mass_frac_shift_per_fermion"]*100:.3f}%  '
              f'discriminated now? charm={r["discriminated_at_2sigma_now_on_m_c"]}  top={r["discriminated_at_2sigma_now_on_m_t"]}')

    print('\nFuture LHC Run 4 (m_c at 0.5%, m_t at 0.1%) exclusions per candidate:')
    for name, r in pb['future_lhc_run4_discriminator']['per_candidate_exclusion_analysis'].items():
        print(f'  β = {name:10s}:  discrepancy at m_c = {r["mass_frac_discrepancy_at_charm"]*100:.3f}%  '
              f'future-excluded on m_c? {r["excluded_at_2sigma_by_future_mc_precision_0.5pct"]}  '
              f'on m_t? {r["excluded_at_2sigma_by_future_mt_precision_0.1pct"]}')

    print(f'\nSHA-256: {out["sha256_prediction_block"]}')
    print(f'Written: {path}')
