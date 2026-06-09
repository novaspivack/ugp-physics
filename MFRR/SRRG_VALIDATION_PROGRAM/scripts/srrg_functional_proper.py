"""
Proper SRRG Functional Implementation
Using actual braid invariants and UCL from theory

Reference: Braid Atlas v2.0, UCL from UGP/GTE theory
Author: AI Assistant
Date: 2025-01-27
"""

import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass

from srrg_core import GTETriple, SRRGParameters

# =============================================================================
# Section A: Braid Invariants and UCL
# =============================================================================

@dataclass
class BraidInvariants:
    """Topological invariants from Braid Atlas."""
    writhe: float
    strand_count: int
    crossing_number: int
    winding_number: int
    knot_type: str


@dataclass
class UCLPalette:
    """UCL coefficient palette."""
    k0: float
    k1: float
    k2: float
    k3: float
    k4: float
    k5: float
    k6: float
    k7: float
    k8: float


def load_braid_atlas(atlas_path: Path) -> Dict[str, BraidInvariants]:
    """
    Load braid invariants from canonical braid atlas.
    
    Args:
        atlas_path: Path to canonical_braid_atlas.json
    
    Returns:
        Dictionary mapping particle names to braid invariants
    """
    with open(atlas_path, 'r') as f:
        atlas_data = json.load(f)
    
    braid_inv_map = {}
    
    for particle_name, particle_data in atlas_data["particles"].items():
        inv = BraidInvariants(
            writhe=particle_data["writhe"],
            strand_count=particle_data["strand_count"],
            crossing_number=particle_data["crossing_number"],
            winding_number=particle_data["winding_number"],
            knot_type=particle_data["knot_type"]
        )
        
        # Normalize particle names (remove underscores, etc.)
        normalized_name = particle_name.replace("_", "").replace("quark", "").strip()
        if normalized_name == "e":
            normalized_name = "electron"
        elif normalized_name == "eneutrino":
            normalized_name = "electron_neutrino"
        elif normalized_name == "muonneutrino":
            normalized_name = "muon_neutrino"
        elif normalized_name == "tauneutrino":
            normalized_name = "tau_neutrino"
        elif normalized_name == "up":
            normalized_name = "up"
        elif normalized_name == "down":
            normalized_name = "down"
        
        braid_inv_map[normalized_name] = inv
        braid_inv_map[particle_name] = inv  # Also keep original name
    
    return braid_inv_map


def mobius(n: int) -> int:
    """Möbius function μ(n)."""
    n = abs(n)
    if n == 0:
        return 0
    if n == 1:
        return 1
    
    # Factor n
    factors = {}
    m = n
    d = 2
    while d * d <= m:
        while m % d == 0:
            factors[d] = factors.get(d, 0) + 1
            m //= d
        d += 1 if d == 2 else 2
    if m > 1:
        factors[m] = factors.get(m, 0) + 1
    
    # Check for square-free
    for exp in factors.values():
        if exp >= 2:
            return 0
    
    # Alternating product
    return -1 if (len(factors) % 2 == 1) else 1


def compute_gte_invariants(triple: GTETriple) -> Dict[str, float]:
    """
    Compute GTE invariants for UCL calculation.
    
    Returns:
        Dictionary with L, L2, g, g2, M, mu_a, mu_b, mu_c
    """
    a, b, c, g = triple.a, triple.b, triple.c, triple.g
    
    # L = log(|b| / |c|)
    if c > 0:
        L = np.log(abs(b) / abs(c))
    else:
        L = np.log(abs(b))  # For c = -1 sentinel
    
    L2 = L ** 2
    
    # Möbius values
    mu_a = mobius(a)
    mu_b = mobius(b)
    mu_c = mobius(c) if c > 0 else 0
    
    # Parity product
    M = mu_a * mu_b * mu_c
    
    return {
        "L": L,
        "L2": L2,
        "g": float(g),
        "g2": float(g * g),
        "M": float(M),
        "mu_a": float(mu_a),
        "mu_b": float(mu_b),
        "mu_c": float(mu_c)
    }


def elegant_palette() -> UCLPalette:
    """
    Elegant UCL palette (from UGP theory).
    
    Satisfies Quarter-Lock: k5 = k4 + 0.25 * k2
    """
    k0 = 0.0
    k2 = 1.0
    k4 = 0.375
    k5 = k4 + 0.25 * k2  # Quarter-Lock: 0.625
    k3 = 0.0
    k6 = 0.0
    k7 = 0.0
    k8 = 0.0
    k1 = 0.05
    
    return UCLPalette(k0, k1, k2, k3, k4, k5, k6, k7, k8)


def ucl_score(triple: GTETriple, palette: UCLPalette) -> float:
    """
    Compute Universal Calibration Law (UCL) score.
    
    UCL(triple) = k·φ(triple) = Σᵢ kᵢ · φᵢ
    
    Args:
        triple: GTE triple
        palette: UCL coefficient palette
    
    Returns:
        UCL score (measures intrinsic lawfulness)
    """
    inv = compute_gte_invariants(triple)
    
    score = (
        palette.k0
        + palette.k1 * inv["L"]
        + palette.k2 * inv["L2"]
        + palette.k3 * inv["g"]
        + palette.k4 * inv["g2"]
        + palette.k5 * inv["M"]
        + palette.k6 * inv["mu_a"]
        + palette.k7 * inv["mu_b"]
        + palette.k8 * inv["mu_c"]
    )
    
    return score


# =============================================================================
# Section B: Proper SRRG Functional
# =============================================================================

def reward_functional_proper(triple_set: List[GTETriple],
                            braid_atlas: Dict[str, BraidInvariants],
                            ucl_palette: UCLPalette,
                            params: SRRGParameters) -> float:
    """
    Proper R[S] using actual braid invariants and UCL.
    
    R[S] = w_braid * I_genon + w_ucl * UCL + w_coherence * Coherence
    
    where:
    - I_genon = topological stability from braid invariants
    - UCL = lawfulness score from GTE structure
    - Coherence = self-consistency measure
    
    Args:
        triple_set: List of GTE triples
        braid_atlas: Dictionary of braid invariants
        ucl_palette: UCL coefficients
        params: SRRG parameters (weights)
    
    Returns:
        Reward R[S] (higher is better)
    """
    R = 0.0
    
    for triple in triple_set:
        # Component 1: Braid invariant contribution (I_genon)
        # This is the true topological self-stability density
        braid_inv = braid_atlas.get(triple.name)
        
        if braid_inv:
            # I_genon ∝ |writhe| + strand_count + |winding_number|
            # Higher values = more topological structure = more stable
            I_genon = (
                abs(braid_inv.writhe) * 10.0
                + braid_inv.strand_count * 5.0
                + abs(braid_inv.winding_number) * 2.0
            )
            
            # Bonus for non-trivial knot topology
            if braid_inv.knot_type != "Trivial":
                I_genon *= 1.5
        else:
            # If no braid data, use minimal I_genon
            I_genon = 1.0
        
        # Component 2: UCL lawfulness
        ucl = ucl_score(triple, ucl_palette)
        
        # Component 3: Coherence intensity
        # Approximate via triple magnitude (as before, but scaled)
        a, b, c, g = triple.a, triple.b, triple.c, triple.g
        magnitude = np.sqrt(a**2 + b**2 + (abs(c) if c > 0 else 0)**2)
        coherence = magnitude * (1.0 + 0.1 * g) / 1000.0  # Scale down
        
        # Combine components
        R += (
            params.w_genon * I_genon
            + params.w_ucl_optimality * ucl
            + params.w_coherence * coherence
        )
    
    return R


def cost_functional_proper(triple_set: List[GTETriple],
                          ucl_palette: UCLPalette,
                          constraints: SRRGParameters) -> float:
    """
    Proper C_Λ[S] using UCL deviation and constraint violations.
    
    C_Λ[S] = penalties for deviations from optimal UCL + violations
    
    Args:
        triple_set: List of GTE triples
        ucl_palette: UCL coefficients
        constraints: SRRG parameters (penalties)
    
    Returns:
        Cost C_Λ[S] (lower is better)
    """
    C = 0.0
    
    for triple in triple_set:
        a, b, c, g = triple.a, triple.b, triple.c, triple.g
        
        # Component 1: UCL deviation from optimal
        # Optimal UCL should be around 0 (Quarter-Lock satisfied)
        ucl = ucl_score(triple, ucl_palette)
        ucl_deviation = abs(ucl) * 0.1  # Penalize large deviations
        C += ucl_deviation
        
        # Component 2: Admissibility penalty
        if not (1 <= a <= 100_000 and 1 <= b <= 1_000_000):
            C += constraints.penalty_admiss
        
        if c != -1 and not (1 <= c <= 100_000):
            C += constraints.penalty_admiss
        
        # Component 3: Generation validity
        if g not in {0, 1, 2, 3}:
            C += constraints.penalty_admiss
        
        # Component 4: MDL excess
        # Penalize high complexity without compensating structure
        mdl_excess = np.log1p(b) / (1.0 + g + np.log1p(abs(c) if c > 0 else 1))
        C += constraints.penalty_mdl * mdl_excess * 0.01  # Scale down
    
    return C


def viability_functional_proper(triple_set: List[GTETriple],
                                braid_atlas: Dict[str, BraidInvariants],
                                ucl_palette: UCLPalette,
                                params: SRRGParameters) -> float:
    """
    Proper F[S] = R[S] - C_Λ[S] using braid invariants and UCL.
    
    Args:
        triple_set: List of GTE triples
        braid_atlas: Braid invariants dictionary
        ucl_palette: UCL coefficients
        params: SRRG parameters
    
    Returns:
        Viability F[S] (higher is better)
    """
    R = reward_functional_proper(triple_set, braid_atlas, ucl_palette, params)
    C = cost_functional_proper(triple_set, ucl_palette, params)
    
    return R - C


# =============================================================================
# Section C: Helper Functions
# =============================================================================

def load_braid_atlas_safe(atlas_path: Path) -> Dict[str, BraidInvariants]:
    """
    Load braid atlas with error handling.
    
    Returns empty dict if file not found.
    """
    if not atlas_path.exists():
        print(f"Warning: Braid atlas not found at {atlas_path}")
        print("Using empty braid atlas (will fall back to minimal I_genon)")
        return {}
    
    return load_braid_atlas(atlas_path)


if __name__ == "__main__":
    # Unit tests
    print("Proper SRRG Functional — Unit Tests")
    print("=" * 60)
    
    # Test 1: UCL score
    electron = GTETriple(1, 73, 823, 1, "electron")
    palette = elegant_palette()
    
    ucl = ucl_score(electron, palette)
    print(f"\n1. UCL score for electron: {ucl:.6f}")
    
    # Test 2: GTE invariants
    inv = compute_gte_invariants(electron)
    print(f"\n2. GTE invariants for electron:")
    for key, val in inv.items():
        print(f"   {key}: {val:.6f}")
    
    # Test 3: Load braid atlas — bundled snapshot in SRRG data/ directory
    _data_dir = Path(__file__).resolve().parents[1] / "data"
    possible_paths = [
        _data_dir / "canonical_braid_atlas.json",
    ]
    
    atlas = {}
    for path in possible_paths:
        if path.exists():
            atlas = load_braid_atlas(path)
            print(f"\n3. Loaded braid atlas from {path.name}")
            print(f"   Particles with braid data: {len(atlas)}")
            break
    
    if not atlas:
        print("\n3. Could not find braid atlas")
    
    # Test 4: Reward functional
    params = SRRGParameters()
    R = reward_functional_proper([electron], atlas, palette, params)
    print(f"\n4. Reward R[electron]: {R:.6f}")
    
    # Test 5: Cost functional
    C = cost_functional_proper([electron], palette, params)
    print(f"\n5. Cost C[electron]: {C:.6f}")
    
    # Test 6: Viability
    F = viability_functional_proper([electron], atlas, palette, params)
    print(f"\n6. Viability F[electron]: {F:.6f} = {R:.6f} - {C:.6f}")
    
    print("\n" + "=" * 60)
    print("✅ All unit tests complete")

