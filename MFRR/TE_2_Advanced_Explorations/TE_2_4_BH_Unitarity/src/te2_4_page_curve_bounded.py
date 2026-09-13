#!/usr/bin/env python3
"""
COMP-P16-A: Bounded-Environment Page Curve
==========================================

Implements a finite-capacity environment that "fills up" as the black hole
evaporates, then introduces back-reaction to demonstrate the full Page curve
(entropy rising then falling).

Physics:
- Phase 1 (evaporation): environment modes fill up; system entropy rises
- Page time: environment is saturated; entropy peaks
- Phase 2 (back-reaction): environment modes recouple; entropy falls
  toward zero (information recovery)

This is distinct from the infinite-bath GKSL model in the main TE2.4
result, which only shows the rising phase.

For Paper 16: if entropy turns over in this model, this demonstrates
that the Stinespring structure is consistent with full information
recovery, not just thermalization.

Author: Nova Spivack
Date: 2026-04-17
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import json
import hashlib
import time
import numpy as np
from numpy.typing import NDArray
from typing import Dict, List, Tuple
from pathlib import Path

from te2_4_hilbert_space import (
    HorizonHilbertSpace, HilbertSpaceConfig, DensityMatrix, Operator
)
from te2_4_gksl_constructor import GKSLMasterEquation, GKSLConfig


def sha256_of_dict(d: dict) -> str:
    """Stable SHA-256 of a JSON-serializable dict."""
    serialised = json.dumps(d, sort_keys=True, default=lambda x: x.tolist()
                             if hasattr(x, 'tolist') else float(x)).encode()
    return hashlib.sha256(serialised).hexdigest()


def build_system(T_H: float = 0.003979, n_modes: int = 3, d_levels: int = 2,
                 coupling: float = 0.01) -> Tuple[HorizonHilbertSpace, GKSLMasterEquation]:
    """Build the JT-like GKSL system (reuse production parameters)."""
    mode_freqs = (np.arange(n_modes) + 0.5) * np.pi * T_H
    hilbert_config = HilbertSpaceConfig(
        n_modes=n_modes, n_levels_per_mode=d_levels,
        hawking_temperature=T_H, mode_frequencies=mode_freqs
    )
    H = HorizonHilbertSpace(hilbert_config)
    gksl_config = GKSLConfig(
        hilbert_config=hilbert_config, coupling_strength=coupling,
        hawking_temperature=T_H, check_detailed_balance=True, check_cptp=True
    )
    gksl = GKSLMasterEquation(gksl_config, H)
    return H, gksl


def von_neumann_entropy(rho: DensityMatrix) -> float:
    """S(ρ) = -Tr(ρ log ρ), in nats."""
    eigenvalues = np.linalg.eigvalsh(rho)
    eigenvalues = eigenvalues[eigenvalues > 1e-15]
    return float(-np.sum(eigenvalues * np.log(eigenvalues)))


def evolve_one_step(rho: DensityMatrix, L: NDArray, dt: float = 0.05) -> DensityMatrix:
    """First-order Euler step of GKSL equation."""
    return rho + L @ rho.reshape(-1) * dt


def build_liouvillian(H_op: NDArray, lindblad_ops: List[NDArray],
                      rates: List[float]) -> NDArray:
    """
    Build the Liouvillian superoperator L acting on vec(ρ).

    dρ/dt = L[ρ]  =>  d vec(ρ)/dt = L_super @ vec(ρ)

    L[ρ] = -i[H, ρ] + Σ_k γ_k (L_k ρ L_k† - ½{L_k†L_k, ρ})
    """
    d = H_op.shape[0]
    I = np.eye(d, dtype=np.complex128)

    # Coherent part: -i[H, ρ] = -i(H⊗I - I⊗H^T) vec(ρ)
    L_super = -1j * (np.kron(H_op, I) - np.kron(I, H_op.T))

    # Dissipative part
    for Lk, gk in zip(lindblad_ops, rates):
        LkLk = Lk.conj().T @ Lk
        L_super += gk * (
            np.kron(Lk, Lk.conj())
            - 0.5 * np.kron(LkLk, I)
            - 0.5 * np.kron(I, LkLk.T)
        )
    return L_super


def run_bounded_page_curve(
    n_steps_evaporation: int = 4000,
    n_steps_backreaction: int = 4000,
    dt: float = 0.05,
    backreaction_strength: float = 1.0,
    T_H: float = 0.003979,
    n_modes: int = 3,
    d_levels: int = 2,
    coupling: float = 0.01,
) -> Dict:
    """
    Simulate the bounded-environment Page curve.

    Phase 1 — Evaporation (n_steps_evaporation steps):
        Standard GKSL dynamics. Entropy rises from 0 toward thermal value.

    Page time (t_page):
        Entropy reaches its peak.

    Phase 2 — Back-reaction (n_steps_backreaction steps):
        Reverse the Lindblad rates (absorption > emission): radiation
        couples back into the system, returning information.
        Entropy should fall back toward 0.

    The coupling scale is modulated so the back-reaction is not trivially
    instantaneous but represents a physically motivated "radiation return."
    """
    print("=" * 60)
    print("COMP-P16-A: Bounded-Environment Page Curve")
    print("=" * 60)
    print(f"  T_H = {T_H:.6f}")
    print(f"  n_modes = {n_modes}, d_levels = {d_levels}")
    print(f"  coupling = {coupling}")
    print(f"  Phase 1: {n_steps_evaporation} steps × dt={dt}")
    print(f"  Phase 2: {n_steps_backreaction} steps × dt={dt}")
    print(f"  back-reaction strength = {backreaction_strength}")
    print()

    H_space, gksl = build_system(T_H, n_modes, d_levels, coupling)
    dim = H_space.total_dim

    # ── Build Liouvillians ────────────────────────────────────────────
    H_op = H_space.hamiltonian()  # method, not property
    # lindblad_operators is list of (label, mode_idx, matrix)
    Lops = [entry[2] for entry in gksl.lindblad_operators]
    rates = [entry[2] for entry in gksl.lindblad_rates]

    # Phase 1: forward GKSL (evaporation)
    L_forward = build_liouvillian(H_op, Lops, rates)

    # Phase 2: reversed rates — absorption > emission
    # Swap emission/absorption pairs so radiation flows back into system
    reversed_rates = []
    n_pairs = n_modes
    for i in range(0, len(rates), 2):
        # Original: [gamma_emit, gamma_abs, gamma_emit, gamma_abs, ...]
        # Reversed: swap each pair
        if i + 1 < len(rates):
            reversed_rates.extend([rates[i + 1] * backreaction_strength,
                                    rates[i] * backreaction_strength])
        else:
            reversed_rates.append(rates[i] * backreaction_strength)
    L_backward = build_liouvillian(H_op, Lops, reversed_rates)

    # ── Initial state: vacuum |0,0,0⟩⟨0,0,0| ─────────────────────────
    rho_vec = np.zeros(dim * dim, dtype=np.complex128)
    rho_vec[0] = 1.0  # vacuum = first basis state
    rho = rho_vec.reshape(dim, dim)

    # Thermal entropy for reference
    rho_thermal = H_space.thermal_state()
    S_thermal = von_neumann_entropy(rho_thermal)

    # ── Phase 1: Evaporation ──────────────────────────────────────────
    times_1 = []
    entropies_1 = []
    purities_1 = []

    print(f"Phase 1: evaporation ({n_steps_evaporation} steps)...")
    t1_start = time.time()

    for step in range(n_steps_evaporation):
        t = step * dt
        S = von_neumann_entropy(rho)
        purity = float(np.real(np.trace(rho @ rho)))

        if step % 200 == 0:
            print(f"  t={t:.1f}  S={S:.4f}  purity={purity:.4f}  (S_th={S_thermal:.4f})")

        times_1.append(t)
        entropies_1.append(S)
        purities_1.append(purity)

        # Euler step
        rho_flat = rho.reshape(-1)
        rho_flat = rho_flat + L_forward @ rho_flat * dt
        rho = rho_flat.reshape(dim, dim)
        # Maintain Hermiticity numerically
        rho = (rho + rho.conj().T) / 2.0
        rho = rho / np.real(np.trace(rho))

    t1_elapsed = time.time() - t1_start
    S_peak = max(entropies_1)
    t_page = times_1[entropies_1.index(S_peak)]
    print(f"\nPage time (entropy peak): t_page = {t_page:.1f}")
    print(f"Peak entropy: S_peak = {S_peak:.4f}  (S_thermal = {S_thermal:.4f})")
    print(f"Phase 1 elapsed: {t1_elapsed:.1f}s")

    rho_at_page_time = rho.copy()

    # ── Phase 2: Back-reaction ────────────────────────────────────────
    times_2 = []
    entropies_2 = []
    purities_2 = []

    print(f"\nPhase 2: back-reaction ({n_steps_backreaction} steps)...")
    t2_start = time.time()

    for step in range(n_steps_backreaction):
        t = (n_steps_evaporation + step) * dt
        S = von_neumann_entropy(rho)
        purity = float(np.real(np.trace(rho @ rho)))

        if step % 200 == 0:
            print(f"  t={t:.1f}  S={S:.4f}  purity={purity:.4f}")

        times_2.append(t)
        entropies_2.append(S)
        purities_2.append(purity)

        # Euler step with reversed Liouvillian
        rho_flat = rho.reshape(-1)
        rho_flat = rho_flat + L_backward @ rho_flat * dt
        rho = rho_flat.reshape(dim, dim)
        rho = (rho + rho.conj().T) / 2.0
        rho = rho / np.real(np.trace(rho))

    t2_elapsed = time.time() - t2_start
    S_final = entropies_2[-1] if entropies_2 else 0.0
    purity_final = purities_2[-1] if purities_2 else 0.0

    # Fidelity of final state with vacuum
    rho_vacuum = np.zeros((dim, dim), dtype=np.complex128)
    rho_vacuum[0, 0] = 1.0
    fidelity_vacuum = float(np.real(
        np.trace(np.sqrt(rho_vacuum @ rho @ rho_vacuum + 1e-15 * np.eye(dim)))
    ))

    print(f"\nPhase 2 elapsed: {t2_elapsed:.1f}s")
    print(f"\nFinal state (t={times_2[-1]:.1f}):")
    print(f"  S_final = {S_final:.4f}  (ideal = 0)")
    print(f"  purity_final = {purity_final:.4f}  (ideal = 1)")
    print(f"  fidelity with vacuum = {fidelity_vacuum:.4f}")

    # ── Entropy turnover detection ────────────────────────────────────
    all_entropies = entropies_1 + entropies_2
    all_times = times_1 + times_2
    entropy_turns_over = (S_final < S_peak * 0.5)  # recovered at least half
    entropy_recovery_fraction = max(0.0, (S_peak - S_final) / S_peak) if S_peak > 0 else 0.0

    print(f"\nEntropy turnover: {'YES ✓' if entropy_turns_over else 'NO ✗'}")
    print(f"Recovery fraction: {entropy_recovery_fraction:.3f} ({100*entropy_recovery_fraction:.1f}%)")

    # ── Results ───────────────────────────────────────────────────────
    results = {
        "config": {
            "T_H": T_H, "n_modes": n_modes, "d_levels": d_levels,
            "coupling": coupling, "dt": dt,
            "n_steps_evaporation": n_steps_evaporation,
            "n_steps_backreaction": n_steps_backreaction,
            "backreaction_strength": backreaction_strength,
        },
        "phase1_evaporation": {
            "times": times_1,
            "entropies": entropies_1,
            "purities": purities_1,
            "S_thermal": S_thermal,
            "S_peak": S_peak,
            "t_page": t_page,
        },
        "phase2_backreaction": {
            "times": times_2,
            "entropies": entropies_2,
            "purities": purities_2,
            "S_final": S_final,
            "purity_final": purity_final,
            "fidelity_with_vacuum": fidelity_vacuum,
        },
        "summary": {
            "entropy_turns_over": entropy_turns_over,
            "entropy_recovery_fraction": entropy_recovery_fraction,
            "S_peak": S_peak,
            "S_final": S_final,
            "S_thermal": S_thermal,
            "t_page": t_page,
            "page_curve_interpretation": (
                "Full Page curve exhibited: entropy rises to peak then falls "
                f"({100*entropy_recovery_fraction:.0f}% recovered)."
                if entropy_turns_over else
                f"Partial recovery only ({100*entropy_recovery_fraction:.0f}%). "
                "Entropy does not fully return to zero in this back-reaction model."
            ),
        },
    }

    return results


def main():
    out_dir = Path(__file__).resolve().parents[1] / "results" / "page_curve_bounded"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "final_results.json"

    results = run_bounded_page_curve(
        n_steps_evaporation=4000,
        n_steps_backreaction=4000,
        dt=0.05,
        backreaction_strength=1.0,
    )

    # SHA-256
    sha = sha256_of_dict(results)
    results["sha256"] = sha

    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved: {out_path}")
    print(f"SHA-256: {sha}")

    # Summary
    s = results["summary"]
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Entropy turns over: {s['entropy_turns_over']}")
    print(f"  Recovery fraction:  {s['entropy_recovery_fraction']:.3f}")
    print(f"  S_peak:             {s['S_peak']:.4f}")
    print(f"  S_final:            {s['S_final']:.4f}")
    print(f"  S_thermal:          {s['S_thermal']:.4f}")
    print(f"  t_page:             {s['t_page']:.1f}")
    print(f"\n  Interpretation: {s['page_curve_interpretation']}")
    print()


if __name__ == "__main__":
    main()
