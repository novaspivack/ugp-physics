"""
Direction 6 — Origin of Life: Phase 1
Autocatalytic Network Gen/Drain Calculator

The UGP prediction: among all possible chemical reaction networks,
the unique self-replicating minimal network that crosses the IPT threshold
(Gen/Drain > 1.13) is the one that gave rise to the genetic code.

This connects to Direction 1: the genetic code alphabet (20 AAs) and
codon assignment might be the unique Stage 2 viability-maximizing choice
for the autocatalytic network that achieves Gen > IPT × Drain.

Phase 1 Goal: Build a Gen/Drain calculator for simple autocatalytic networks
and test whether IPT = 1.13 is a natural threshold.

Model:
  - Molecules: small set (amino acids, nucleotides, simple metabolites)
  - Reactions: catalysis, ligation, hydrolysis
  - Gen = rate of key molecule production
  - Drain = rate of degradation + diffusion loss
  - IPT check: Gen/Drain > 1.13 for viable (self-sustaining) network
"""

import numpy as np
from itertools import combinations

IPT = 1.1309  # Information Profit Threshold

# ─────────────────────────────────────────────────────────────────────────────
# Simplified prebiotic chemistry model
# Molecules: the 10 most prebiotically accessible amino acids + ribose + phosphate
# ─────────────────────────────────────────────────────────────────────────────

MOLECULES = {
    # (name, prebiotic_concentration_norm, self_cat_rate)
    'Gly':  ('glycine',       1.0,  0.05),
    'Ala':  ('alanine',       0.9,  0.04),
    'Val':  ('valine',        0.7,  0.03),
    'Asp':  ('aspartate',     0.8,  0.04),
    'Glu':  ('glutamate',     0.7,  0.04),
    'Ser':  ('serine',        0.6,  0.03),
    'Pro':  ('proline',       0.5,  0.02),
    'Thr':  ('threonine',     0.5,  0.02),
    'Leu':  ('leucine',       0.4,  0.02),
    'Ile':  ('isoleucine',    0.4,  0.02),
}

def gen_drain_network(network_molecules, n_template=5, hydrolysis_rate=0.1):
    """
    Compute Gen/Drain for a network of molecules that form a simple
    autocatalytic system via template-directed ligation.

    Model:
    - Template = a sequence of n_template molecules
    - Generation rate: product of prebiotic concentrations of constituent molecules
      (joint probability of all monomers being available)
    - Drain rate: hydrolysis_rate × template length (longer = more fragile)
    - IPT check: Gen/Drain > 1.13

    This is a toy model — real prebiotic chemistry is far more complex.
    """
    if len(network_molecules) < n_template:
        return 0.0, 0.0, False

    # Gen: product of concentrations (probability all needed monomers present)
    # Weighted by their catalytic rates
    concs = [MOLECULES[m][1] for m in network_molecules[:n_template]]
    cats  = [MOLECULES[m][2] for m in network_molecules[:n_template]]

    gen = np.prod(concs) * np.mean(cats) * n_template

    # Drain: hydrolysis + diffusion (scales with template length)
    drain = hydrolysis_rate * n_template

    ratio = gen / drain if drain > 0 else 0.0
    viable = ratio > IPT

    return gen, drain, viable, ratio


def scan_networks():
    """
    Scan all subsets of prebiotic molecules for autocatalytic viability.
    Find which subsets achieve Gen/Drain > IPT.
    """
    print("=" * 65)
    print("D6 ORIGIN OF LIFE — AUTOCATALYTIC NETWORK GEN/DRAIN SCAN")
    print(f"IPT threshold = {IPT}")
    print("=" * 65)
    print()

    mols = list(MOLECULES.keys())
    viable_networks = []
    n_tested = 0

    # Test all subsets of size 3-10
    for size in range(3, len(mols)+1):
        for subset in combinations(mols, size):
            for template_len in [3, 4, 5]:
                if template_len > size:
                    continue
                n_tested += 1
                gen, drain, viable, ratio = gen_drain_network(
                    list(subset), n_template=template_len)
                if viable:
                    viable_networks.append({
                        'molecules': list(subset),
                        'template_len': template_len,
                        'ratio': ratio,
                        'gen': gen,
                        'drain': drain,
                    })

    print(f"Networks tested: {n_tested}")
    print(f"Viable (Gen/Drain > {IPT}): {len(viable_networks)}")
    print(f"Viability fraction: {len(viable_networks)/n_tested:.3%}")
    print()

    if viable_networks:
        # Sort by ratio
        viable_networks.sort(key=lambda x: -x['ratio'])
        print("Top 5 viable networks:")
        for net in viable_networks[:5]:
            print(f"  Molecules: {net['molecules']}")
            print(f"  Template len: {net['template_len']}, "
                  f"Gen/Drain = {net['ratio']:.4f}  (IPT = {IPT:.4f})")
            print()

        # Does the standard first-wave set (Gly, Ala, Asp, Glu, Val) achieve viability?
        first_wave = ['Gly', 'Ala', 'Asp', 'Glu', 'Val']
        _, _, fw_viable, fw_ratio = gen_drain_network(first_wave, n_template=5)
        print(f"First-wave set {first_wave}:")
        print(f"  Gen/Drain = {fw_ratio:.4f}  {'VIABLE ✓' if fw_viable else 'NOT VIABLE ✗'}")

    return viable_networks


def ipt_threshold_scan():
    """
    Scan different IPT thresholds and find the 'natural' threshold where
    viability transitions from rare to common.
    """
    print()
    print("IPT THRESHOLD SENSITIVITY:")
    print(f"  {'Threshold':>10}  {'Viable networks':>16}  {'Fraction':>10}")
    print("  " + "─" * 42)

    mols = list(MOLECULES.keys())
    for threshold in [0.5, 0.8, 1.0, 1.05, 1.10, 1.13, 1.15, 1.20, 1.30, 1.50]:
        count = 0
        total = 0
        for size in range(3, len(mols)+1):
            for subset in combinations(mols, size):
                for template_len in [3, 4, 5]:
                    if template_len > size:
                        continue
                    total += 1
                    _, _, _, ratio = gen_drain_network(list(subset), n_template=template_len)
                    if ratio > threshold:
                        count += 1

        marker = " ← IPT" if abs(threshold - IPT) < 0.01 else ""
        print(f"  {threshold:>10.3f}  {count:>16d}  {count/total:>10.3%}{marker}")


if __name__ == "__main__":
    viable = scan_networks()
    ipt_threshold_scan()

    print()
    print("=" * 65)
    print("PHASE 1 CONCLUSION")
    print("=" * 65)
    print()
    print("This is a toy model. Real prebiotic chemistry requires:")
    print("  1. Thermodynamic free energy calculations for each reaction")
    print("  2. Kinetic rate constants from experiment or quantum chemistry")
    print("  3. Compartmentalization (lipid vesicle confinement effects)")
    print("  4. Template copying fidelity (error rates)")
    print()
    print("Phase 1 result: IPT threshold scan works in principle.")
    print("Phase 2 plan: Replace toy model with actual prebiotic chemistry")
    print("  network (Miller-Urey product database, Sutherland group chemistry).")
    print()
    print("Connection to D1 (genetic code):")
    print("  If a minimal viable autocatalytic network uses the first-wave AAs")
    print("  and requires a specific template length → codon assignment is constrained")
    print("  by the network's Gen/Drain optimization. This IS the Stage 2 criterion")
    print("  that would complete the genetic code uniqueness proof.")
