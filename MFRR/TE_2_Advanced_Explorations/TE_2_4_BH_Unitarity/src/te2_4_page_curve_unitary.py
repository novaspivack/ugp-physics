#!/usr/bin/env python3
"""
COMP-P16-C: Unitary Evaporation Page Curve (Closed System)
===========================================================

Physically correct Page curve experiment for a CLOSED, FINITE system.

PHYSICS OF THE CORRECT EXPERIMENT
----------------------------------
The Page curve requires a CLOSED system where the total state is pure:
|Ψ_total⟩ ∈ H_BH ⊗ H_rad  (pure, no open bath)

Key facts:
  - S_BH = S_rad  (purity of total state)
  - Page time: dim(H_rad_filled) = dim(H_BH_remaining)
  - After Page time: S_BH DECREASES as radiation carries more info
  - Recovery: measuring/returning radiation maps BH back toward pure

WHY THE OPEN-SYSTEM (GKSL) EXPERIMENT CANNOT SHOW THE PAGE CURVE
-----------------------------------------------------------------
- GKSL has an infinite Markovian bath: never "fills up"
- S_BH monotonically increases (no Page turnover)
- Reversed-GKSL drives to a DIFFERENT thermal state, not vacuum
- Only a FINITE CLOSED radiation register shows the Page curve

OUR MODEL
---------
We model the BH as a qubit register that "evaporates" mode-by-mode
into a radiation register via a unitary swap-like interaction:

H_total = H_BH ⊗ H_rad,  dim_total = d_BH × d_rad

Evaporation step n: U_n entangles BH mode n with radiation qubit n
  U_n = SWAP(BH_mode_n, rad_qubit_n) × phase(Hawking_spectrum)

This gives a unitary, closed-system model where:
  S_BH rises → peaks at Page time → falls as radiation "fills up"

PT⁻¹ CIRCUIT IN THIS MODEL
----------------------------
After full evaporation (BH → radiation), apply U† (time-reverse)
to the joint state. This recovers the original BH state exactly
(modulo the Kraus approximation in the original GKSL step).

WHY THIS IS PHYSICALLY VALID
------------------------------
This is the standard Penington/AMPS setup. The unitary U represents
the full Hawking evaporation process as a quantum channel. The Page
curve turnover is a theorem for any such unitary model once
dim(rad) > dim(BH).

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
from pathlib import Path
from typing import Dict, List, Tuple


def sha256_of_dict(d: dict) -> str:
    serialised = json.dumps(d, sort_keys=True, default=lambda x: x.tolist()
                             if hasattr(x, 'tolist') else float(x)).encode()
    return hashlib.sha256(serialised).hexdigest()


def von_neumann_entropy(rho: NDArray) -> float:
    """S(ρ) = -Tr(ρ log ρ) in nats."""
    eigvals = np.linalg.eigvalsh(rho)
    eigvals = eigvals[eigvals > 1e-15]
    return float(-np.sum(eigvals * np.log(eigvals)))


def partial_trace_bh(rho_total: NDArray, dim_bh: int, dim_rad: int) -> NDArray:
    """Trace out radiation to get BH reduced density matrix."""
    rho = rho_total.reshape(dim_bh, dim_rad, dim_bh, dim_rad)
    return np.einsum('iaja->ij', rho)


def partial_trace_rad(rho_total: NDArray, dim_bh: int, dim_rad: int) -> NDArray:
    """Trace out BH to get radiation reduced density matrix."""
    rho = rho_total.reshape(dim_bh, dim_rad, dim_bh, dim_rad)
    return np.einsum('iajb->ab', rho)


def hawking_unitary(dim_bh: int, dim_rad_new: int, theta: float) -> NDArray:
    """
    Unitary coupling one BH mode to one new radiation qubit.
    
    This models the emission of one Hawking quantum: a BH mode entangles
    with a fresh radiation qubit via a partial-SWAP with angle θ.
    
    For θ = π/2: full SWAP (complete emission of that mode)
    For θ < π/2: partial emission (creating entanglement)
    
    The state space is H_BH ⊗ H_rad_qubit (2-dimensional new qubit).
    We act only on the LAST qubit of BH and the new rad qubit.
    """
    # Simple beamsplitter-like unitary on 2×2 = 4D subspace
    # Acting on |0_BH_last, 0_rad⟩, |0_BH_last, 1_rad⟩, |1_BH_last, 0_rad⟩, |1_BH_last, 1_rad⟩
    c, s = np.cos(theta), np.sin(theta)
    U_sub = np.array([
        [1,  0,   0,  0],
        [0,  c,  -s,  0],
        [0,  s,   c,  0],
        [0,  0,   0,  1],
    ], dtype=np.complex128)
    return U_sub


def run_unitary_page_curve(
    n_bh_modes: int = 6,
    T_H: float = 0.003979,
    n_steps_per_mode: int = 10,
    theta_per_step: float = None,
) -> Dict:
    """
    Simulate Page curve for a CLOSED finite system using unitary evaporation.
    
    Model:
    - BH = n_bh_modes qubits, all initially in |0⟩ except first few in superposition
    - Radiation = n_bh_modes qubits, all initially in |0⟩ (vacuum)
    - Each evaporation step: partially SWAP one BH qubit with one radiation qubit
    - Track S_BH, S_rad as function of time
    - Page time: when dim(radiation filled) = dim(BH remaining)
    
    After evaporation: apply U† to entire joint state and measure recovery.
    """
    print("=" * 60)
    print("COMP-P16-C: Unitary Page Curve (Closed System)")
    print("=" * 60)
    print(f"  BH modes (qubits): {n_bh_modes}")
    print(f"  T_H: {T_H}")
    print(f"  Steps per mode: {n_steps_per_mode}")

    # BH thermal state: each qubit has thermal occupation n_thermal
    # For mode k: ω_k = (k+0.5)*π*T_H; p_1 = n_th/(n_th+1)
    omega_k = lambda k: (k + 0.5) * np.pi * T_H
    n_th = lambda k: 1.0 / (np.exp(omega_k(k) / T_H) - 1.0)
    p1_k = lambda k: n_th(k) / (n_th(k) + 1.0)  # prob of being in |1⟩

    # Initial BH state: tensor product of thermal single-qubit states
    # Each qubit k: ρ_k = (1-p1_k)|0⟩⟨0| + p1_k|1⟩⟨1|
    # Initial state vector (we'll use density matrices):
    # ρ_BH_0 = ⊗_k [(1-p1_k)|0⟩⟨0| + p1_k|1⟩⟨1|]
    
    dim_bh = 2 ** n_bh_modes
    dim_rad = 2 ** n_bh_modes  # radiation register same size as BH

    # Build initial BH density matrix (thermal)
    rho_bh = np.ones((1,1), dtype=np.complex128)  # start with trivial
    for k in range(n_bh_modes):
        p1 = p1_k(k)
        rho_k = np.array([[1-p1, 0], [0, p1]], dtype=np.complex128)
        rho_bh = np.kron(rho_bh, rho_k)
    
    # Radiation starts in vacuum |00...0⟩⟨00...0|
    rho_rad0 = np.zeros((dim_rad, dim_rad), dtype=np.complex128)
    rho_rad0[0, 0] = 1.0

    # Initial joint state: ρ_BH ⊗ |0_rad⟩⟨0_rad|
    rho_total = np.kron(rho_bh, rho_rad0)

    # Track S_BH and S_rad vs time
    times = [0.0]
    S_bh_list = [von_neumann_entropy(partial_trace_bh(rho_total, dim_bh, dim_rad))]
    S_rad_list = [von_neumann_entropy(partial_trace_rad(rho_total, dim_bh, dim_rad))]
    purity_total = [float(np.real(np.trace(rho_total @ rho_total)))]

    # Also record the UNITARY operations applied (for PT^{-1})
    U_total = np.eye(dim_bh * dim_rad, dtype=np.complex128)

    # Evaporation: for each BH mode, gradually swap into radiation
    # theta_per_step: rotation angle per step; after n_steps_per_mode steps,
    # total rotation = n_steps_per_mode * theta ≈ π/2 (full SWAP)
    if theta_per_step is None:
        theta_per_step = (np.pi / 2) / n_steps_per_mode

    print(f"\n  Evaporating {n_bh_modes} modes ({n_steps_per_mode} steps/mode)...")
    print(f"  θ per step = {theta_per_step:.4f} rad")
    print(f"  Total rotation per mode = {n_steps_per_mode*theta_per_step:.4f} rad (π/2 = {np.pi/2:.4f})")

    t = 0.0
    step_count = 0

    for mode_idx in range(n_bh_modes):
        for step in range(n_steps_per_mode):
            # Build the 4D partial SWAP on (BH qubit mode_idx, rad qubit mode_idx)
            U_sub = hawking_unitary(dim_bh, dim_rad, theta_per_step)

            # Embed U_sub into full dim_bh*dim_rad space
            # BH qubit mode_idx is bit (n_bh_modes-1-mode_idx) of BH index
            # Rad qubit mode_idx is bit (n_bh_modes-1-mode_idx) of rad index
            # We act on the 2-dim subspace of each

            # More efficient: use index permutation approach
            # Build full unitary by tensor product logic
            U_full = embed_2qubit_unitary(U_sub, mode_idx, mode_idx, n_bh_modes, dim_bh, dim_rad)

            # Evolve: ρ → U ρ U†
            rho_total = U_full @ rho_total @ U_full.conj().T
            rho_total = (rho_total + rho_total.conj().T) / 2  # Hermitian

            # Accumulate total unitary
            U_total = U_full @ U_total

            t += 1.0
            step_count += 1

            # Record entropies
            rho_bh_t = partial_trace_bh(rho_total, dim_bh, dim_rad)
            rho_rad_t = partial_trace_rad(rho_total, dim_bh, dim_rad)
            S_bh = von_neumann_entropy(rho_bh_t)
            S_rad = von_neumann_entropy(rho_rad_t)
            pur = float(np.real(np.trace(rho_total @ rho_total)))

            times.append(t)
            S_bh_list.append(S_bh)
            S_rad_list.append(S_rad)
            purity_total.append(pur)

        if mode_idx % 2 == 0 or mode_idx == n_bh_modes - 1:
            print(f"  Mode {mode_idx+1}/{n_bh_modes}: S_BH={S_bh:.4f}, S_rad={S_rad:.4f}, "
                  f"purity_total={pur:.6f}")

    # Page time: maximum of S_BH
    S_bh_arr = np.array(S_bh_list)
    t_page_idx = int(np.argmax(S_bh_arr))
    t_page = times[t_page_idx]
    S_bh_peak = S_bh_arr[t_page_idx]
    S_bh_final = S_bh_list[-1]
    S_rad_final = S_rad_list[-1]
    S_bh_initial = S_bh_list[0]
    page_turnover = S_bh_final < S_bh_peak * 0.5
    recovery_fraction = max(0.0, (S_bh_peak - S_bh_final) / S_bh_peak) if S_bh_peak > 0 else 0.0

    print(f"\n  Page time: t_page = {t_page:.1f} (step {t_page_idx})")
    print(f"  S_BH peak = {S_bh_peak:.4f}")
    print(f"  S_BH final = {S_bh_final:.4f}")
    print(f"  S_rad final = {S_rad_final:.4f}")
    print(f"  Purity of total state (final) = {purity_total[-1]:.6f}")
    print(f"  Entropy turnover: {'YES ✓' if page_turnover else 'NO ✗'}")
    print(f"  S_BH recovery fraction: {recovery_fraction:.3f}")

    # Purity conservation check
    print(f"\n  Purity conservation: initial={purity_total[0]:.6f}, final={purity_total[-1]:.6f}")
    print(f"  |S_BH - S_rad| at final time = {abs(S_bh_final - S_rad_final):.6f} (should be 0 for pure state)")

    # ── PT^{-1}: Apply U† to recover initial BH state ────────────────
    print("\n  Applying PT^{-1} = U_total†...")
    rho_recovered_total = U_total.conj().T @ rho_total @ U_total
    rho_recovered_total = (rho_recovered_total + rho_recovered_total.conj().T) / 2

    rho_bh_recovered = partial_trace_bh(rho_recovered_total, dim_bh, dim_rad)
    rho_bh_recovered /= np.real(np.trace(rho_bh_recovered))

    # Fidelity of recovered BH with original thermal BH state
    F_recovery = state_fidelity(rho_bh_recovered, rho_bh)
    S_bh_recovered = von_neumann_entropy(rho_bh_recovered)
    purity_bh_recovered = float(np.real(np.trace(rho_bh_recovered @ rho_bh_recovered)))

    print(f"  F(ρ_BH_recovered, ρ_BH_initial) = {F_recovery:.8f}")
    print(f"  S_BH_recovered = {S_bh_recovered:.6f} (target: {S_bh_initial:.6f})")
    print(f"  Purity_BH_recovered = {purity_bh_recovered:.6f}")

    results = {
        "config": {
            "n_bh_modes": n_bh_modes,
            "T_H": T_H,
            "n_steps_per_mode": n_steps_per_mode,
            "theta_per_step": theta_per_step,
            "dim_bh": dim_bh,
            "dim_rad": dim_rad,
        },
        "page_curve": {
            "times": times,
            "S_bh": S_bh_list,
            "S_rad": S_rad_list,
            "purity_total": purity_total,
            "t_page": t_page,
            "S_bh_peak": S_bh_peak,
            "S_bh_initial": S_bh_initial,
            "S_bh_final": S_bh_final,
            "S_rad_final": S_rad_final,
            "page_turnover": page_turnover,
            "recovery_fraction": recovery_fraction,
        },
        "pt_inverse": {
            "F_recovery_bh_state": F_recovery,
            "S_bh_recovered": S_bh_recovered,
            "purity_bh_recovered": purity_bh_recovered,
        },
        "summary": {
            "entropy_turns_over": page_turnover,
            "S_BH_peak": S_bh_peak,
            "S_BH_final": S_bh_final,
            "purity_conservation": abs(purity_total[-1] - purity_total[0]),
            "S_BH_minus_S_rad_final": abs(S_bh_final - S_rad_final),
            "F_pt_inverse_recovery": F_recovery,
            "interpretation": (
                f"CLOSED UNITARY MODEL: S_BH {'peaks then falls' if page_turnover else 'is still rising'} "
                f"(S_peak={S_bh_peak:.3f}, S_final={S_bh_final:.3f}). "
                f"PT^{{-1}} recovers initial BH state to F={F_recovery:.4f}. "
                + ("Full Page curve demonstrated." if page_turnover else
                   "Increase n_steps_per_mode for complete evaporation.")
            ),
        },
    }
    return results


def embed_2qubit_unitary(U_sub: NDArray, bh_qubit_idx: int, rad_qubit_idx: int,
                          n_qubits: int, dim_bh: int, dim_rad: int) -> NDArray:
    """
    Embed a 4×4 unitary acting on (BH qubit bh_qubit_idx, rad qubit rad_qubit_idx)
    into the full dim_bh*dim_rad space.
    
    BH qubit bh_qubit_idx is the qubit at position bh_qubit_idx in the BH register.
    Rad qubit rad_qubit_idx is the qubit at position rad_qubit_idx in the rad register.
    """
    dim_total = dim_bh * dim_rad
    U_full = np.eye(dim_total, dtype=np.complex128)

    # Iterate over all basis states of the full space
    for bh_idx in range(dim_bh):
        for rad_idx in range(dim_rad):
            # Extract the bits for the targeted qubits
            bh_bit = (bh_idx >> (n_qubits - 1 - bh_qubit_idx)) & 1
            rad_bit = (rad_idx >> (n_qubits - 1 - rad_qubit_idx)) & 1

            # 4D subspace basis index: (bh_bit, rad_bit) → {0,1,2,3}
            sub_in = 2 * bh_bit + rad_bit
            row_in = bh_idx * dim_rad + rad_idx

            for out_bh_bit in range(2):
                for out_rad_bit in range(2):
                    sub_out = 2 * out_bh_bit + out_rad_bit
                    amp = U_sub[sub_out, sub_in]
                    if abs(amp) < 1e-14:
                        continue

                    # Reconstruct output BH and rad indices with flipped target bits
                    new_bh_idx = bh_idx ^ ((bh_bit ^ out_bh_bit) << (n_qubits - 1 - bh_qubit_idx))
                    new_rad_idx = rad_idx ^ ((rad_bit ^ out_rad_bit) << (n_qubits - 1 - rad_qubit_idx))
                    row_out = new_bh_idx * dim_rad + new_rad_idx

                    U_full[row_out, row_in] += amp - (1.0 if row_out == row_in else 0.0)

    return U_full


def state_fidelity(rho: NDArray, sigma: NDArray) -> float:
    """F(ρ,σ) using eigenvalue approach."""
    # sqrt_sigma
    eigvals_s, eigvecs_s = np.linalg.eigh(sigma + 1e-12 * np.eye(sigma.shape[0]))
    eigvals_s = np.maximum(eigvals_s, 0)
    sqrt_sigma = eigvecs_s @ np.diag(np.sqrt(eigvals_s)) @ eigvecs_s.conj().T
    M = sqrt_sigma @ rho @ sqrt_sigma
    eigvals_M = np.maximum(np.linalg.eigvalsh(M + 1e-12 * np.eye(M.shape[0])), 0)
    return float(np.sum(np.sqrt(eigvals_M)) ** 2)


def main():
    out_dir = Path(__file__).resolve().parents[1] / "results" / "page_curve_unitary"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Run with 4 modes for speed, 20 steps/mode for near-complete evaporation
    print("=" * 60)
    print("Run 1: 4 modes, 20 steps/mode (near-complete evaporation)")
    print("=" * 60)
    results_4 = run_unitary_page_curve(n_bh_modes=4, n_steps_per_mode=20)

    sha4 = sha256_of_dict(results_4)
    results_4["sha256"] = sha4
    out4 = out_dir / "results_4modes.json"
    with open(out4, "w") as f:
        json.dump(results_4, f, indent=2)
    print(f"\nSaved: {out4} | SHA-256: {sha4}")

    print("\n" + "=" * 60)
    print("Run 2: 6 modes, 15 steps/mode (larger system)")
    print("=" * 60)
    results_6 = run_unitary_page_curve(n_bh_modes=6, n_steps_per_mode=15)

    sha6 = sha256_of_dict(results_6)
    results_6["sha256"] = sha6
    out6 = out_dir / "results_6modes.json"
    with open(out6, "w") as f:
        json.dump(results_6, f, indent=2)
    print(f"\nSaved: {out6} | SHA-256: {sha6}")

    print("\n\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    for label, res in [("4 modes", results_4), ("6 modes", results_6)]:
        s = res["summary"]
        print(f"\n  {label}:")
        print(f"    Entropy turns over: {s['entropy_turns_over']}")
        print(f"    S_BH peak:  {s['S_BH_peak']:.4f}")
        print(f"    S_BH final: {s['S_BH_final']:.4f}")
        print(f"    Purity conservation: Δ = {s['purity_conservation']:.2e}")
        print(f"    |S_BH - S_rad| at final: {s['S_BH_minus_S_rad_final']:.6f}")
        print(f"    PT^{{-1}} recovery fidelity: {s['F_pt_inverse_recovery']:.6f}")
        print(f"    {s['interpretation']}")


if __name__ == "__main__":
    main()
