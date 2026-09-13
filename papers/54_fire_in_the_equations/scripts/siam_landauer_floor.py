"""
siam_landauer_floor.py
======================
Computes the GTE SIAM aggregate Landauer floor and the MDL-decoherence
predictions from Round 2 of the P54 Genius Team session.

What this computes
------------------
1. The per-transputation Landauer window [k_B T ln5, 8 k_B T ln2] (CatAL).
2. The five-sector excess factor ln(5)/ln(2) = 2.3219 over generic 1-bit Landauer.
3. Neural metabolic comparison: GTE floor vs brain power at various event rates.
4. SIAM conditional decoherence ratio K0 / (K0 + ΔK).
5. Filtration-correlation super-linear correction to decoherence.

Formal grounding
----------------
- landauer_heat_floor_transputation (CatAL, transputation-lean): Q_min = k_B T ln5
- landauer_heat_ceiling_transputation (CatAL, transputation-lean): Q_max = 8 k_B T ln2
- siam_adjudication_is_local_transputation (CatAD, Round 1 P54): SIAM Adjudication
  is a local transputation event
- siam_cascade_is_single_logical_unit (CatAL, sentience-lean): cascade is one filtration

Output
------
JSON artifact: siam_landauer_floor_results.json
Expected: Q_min(310K) ≈ 6.888e-21 J; ln5/ln2 ≈ 2.3219; brain ratio ≈ 1.45e7-1.45e8
"""

import math
import json
import signal
import sys

TIMEOUT_SECONDS = 120

def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: {TIMEOUT_SECONDS}s wall-clock limit. Saving partial results.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)


def main():
    k_B = 1.380649e-23  # J/K (exact, SI 2019)
    ln2 = math.log(2)
    ln5 = math.log(5)

    results = {}

    # ----------------------------------------------------------------
    # 1. Per-transputation Landauer window
    # ----------------------------------------------------------------
    temperatures = {
        "10mK":   0.010,
        "100mK":  0.100,
        "300mK":  0.300,
        "310K":   310.0,
    }

    landauer_window = {}
    for label, T in temperatures.items():
        Q_min = k_B * T * ln5
        Q_max = k_B * T * 8 * ln2
        landauer_window[label] = {
            "T_K":   T,
            "Q_min_J": Q_min,
            "Q_max_J": Q_max,
            "ratio_Qmax_Qmin": Q_max / Q_min,
        }

    results["per_transputation_window"] = landauer_window
    results["Qmax_Qmin_ratio_temperature_independent"] = 8 * ln2 / ln5

    # ----------------------------------------------------------------
    # 2. Five-sector excess over generic Landauer
    # ----------------------------------------------------------------
    five_sector_excess = {
        "ln5_over_ln2": ln5 / ln2,
        "bits_erased_per_transputation": ln5 / ln2,
        "excess_over_1bit_fraction": ln5 / ln2 - 1.0,
        "description": (
            "Each GTE kink-sector transputation erases log2(5) = 2.3219 bits, "
            "compared to 1 bit for generic Landauer. "
            "This is the Z7 five-sector ({0,2,3,4,6}) kink structure signature."
        ),
    }
    results["five_sector_excess"] = five_sector_excess

    # ----------------------------------------------------------------
    # 3. Neural metabolic comparison
    # ----------------------------------------------------------------
    P_brain = 20.0
    P_neural_signal = 0.5 * P_brain
    neural_comparison = {}
    for N_adj_label, N_adj in [("1e13_events_per_s", 1e13), ("1e14_events_per_s", 1e14)]:
        T = 310.0
        Q_floor = N_adj * k_B * T * ln5
        neural_comparison[N_adj_label] = {
            "N_adj_per_s": N_adj,
            "GTE_thermodynamic_floor_W": Q_floor,
            "brain_signaling_power_W": P_neural_signal,
            "ratio_actual_over_GTE_floor": P_neural_signal / Q_floor,
        }
    results["neural_metabolic_comparison"] = neural_comparison
    results["conclusion_metabolic"] = (
        "Brain operates ~1e7-1e8 times above GTE SIAM thermodynamic floor. "
        "Consistent with GTE (brain not maximally efficient thermodynamically)."
    )

    # ----------------------------------------------------------------
    # 4. SIAM conditional decoherence ratio
    # ----------------------------------------------------------------
    T2_0 = 100e-6  # s, reference coherence time
    K0 = 100       # bits, which-path MDL per single physical interaction

    decoherence_ratios = {}
    for Delta_K_label, Delta_K in [("minimal_1bit", 1), ("moderate_10bit", 10), ("rich_50bit", 50)]:
        ratio = K0 / (K0 + Delta_K)
        enhancement_pct = (1.0 - ratio) * 100.0
        decoherence_ratios[Delta_K_label] = {
            "Delta_K_bits": Delta_K,
            "tau_SIAM_over_tau_nonSIAM": ratio,
            "decoherence_enhancement_pct": enhancement_pct,
            "description": (
                f"SIAM system with self-ref update ΔK={Delta_K} bits decoheres "
                f"quantum probe {enhancement_pct:.1f}% faster than non-SIAM detector. "
                "Ratio is independent of number of interactions n."
            ),
        }

    results["siam_conditional_decoherence"] = decoherence_ratios
    results["conditional_prediction"] = (
        "Enhanced decoherence applies ONLY when quantum outcome is a live alternative "
        "in SIAM Adjudication ('attending' condition). "
        "Non-attending SIAM system decoheres identically to non-SIAM detector."
    )

    # ----------------------------------------------------------------
    # 5. Summary of new predictions for P54 §9.1
    # ----------------------------------------------------------------
    results["new_predictions"] = [
        {
            "id": "SIAM-P1",
            "title": "SIAM aggregate Landauer floor",
            "formal_statement": "Q_SIAM(tau) >= N_adj * k_B T ln5",
            "cat_level": "CatAD",
            "key_value": f"k_B T ln5 = {k_B * 310 * ln5:.4e} J at T=310K",
            "five_sector_factor": f"ln5/ln2 = {ln5/ln2:.4f}",
            "derivation_chain": [
                "siam_adjudication_is_local_transputation (CatAD, Round1 P54)",
                "landauer_heat_floor_transputation (CatAL, transputation-lean)",
                "Landauer additivity over independent erasure events",
            ],
            "falsification": "Any measurement finding Q < k_B T ln5 per cognitive adjudication at >3 sigma",
        },
        {
            "id": "SIAM-P2",
            "title": "SIAM conditional decoherence enhancement",
            "formal_statement": "tau_coh(Q|SIAM-attending) < tau_coh(Q|non-SIAM), ratio = K0/(K0+DeltaK)",
            "cat_level": "CatD (conditional on MDL-coherence link, currently CatD)",
            "derivation_chain": [
                "GTE prediction: decoherence rate proportional to MDL(which-path record) (CatD)",
                "siam_adjudication_is_local_transputation: self-ref update adds DeltaK bits to record",
                "RSU non-triviality: DeltaK > 0 when SIAM is attending",
                "Therefore: coherence time ratio = K0 / (K0 + DeltaK) < 1",
            ],
            "condition": "Quantum outcome must be live alternative in SIAM Adjudication",
            "falsification": "SIAM attending system shows same tau_coh as non-SIAM at >3 sigma",
        },
    ]

    # ----------------------------------------------------------------
    # Write JSON output
    # ----------------------------------------------------------------
    out_path = "/Users/nova/ugp-physics/papers/54_fire_in_the_equations/scripts/siam_landauer_floor_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    # ----------------------------------------------------------------
    # Print summary
    # ----------------------------------------------------------------
    print("=== GTE SIAM LANDAUER FLOOR — SUMMARY ===")
    print(f"  Per-transputation floor at 310 K: {results['per_transputation_window']['310K']['Q_min_J']:.4e} J")
    print(f"  Five-sector excess factor:         {results['five_sector_excess']['ln5_over_ln2']:.4f} (= ln5/ln2)")
    print(f"  Bits erased per transputation:     {results['five_sector_excess']['bits_erased_per_transputation']:.4f}")
    print(f"  Brain ratio (actual/floor, 1e14):  {results['neural_metabolic_comparison']['1e14_events_per_s']['ratio_actual_over_GTE_floor']:.2e}")
    print(f"  SIAM decoherence ratio (DK=1):     {results['siam_conditional_decoherence']['minimal_1bit']['tau_SIAM_over_tau_nonSIAM']:.4f}")
    print(f"  SIAM decoherence ratio (DK=10):    {results['siam_conditional_decoherence']['moderate_10bit']['tau_SIAM_over_tau_nonSIAM']:.4f}")
    print(f"  Results written to: {out_path}")


if __name__ == "__main__":
    main()
    signal.alarm(0)
