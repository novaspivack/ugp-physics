#!/usr/bin/env python3
"""
COMP-P16-B: PT^{-1} as Explicit Quantum Circuit
================================================

Constructs PT^{-1} explicitly for the JT-like toy model as
U† from the Stinespring dilation applied to the system-environment pair.

Physical claim being tested:
    Starting from the thermal steady state ρ_th (the fixed point of the
    GKSL evaporation), apply:
        U†(ρ_th ⊗ |env⟩⟨env|)U
    and check whether partial trace over the environment recovers the
    initial vacuum state |0,0,0⟩⟨0,0,0|.

This tests whether PT^{-1} (the Stinespring adjoint) is operationally
meaningful as an information recovery circuit for this specific toy BH.

Why DSAC does NOT already prove this:
    DSAC proves PT has a computational architecture for δ-machines 
    (in Lean 4, over GTE computational states). 
    This computation tests whether PT^{-1} recovers quantum information
    in the Hilbert-space representation of the toy JT-like BH.
    These are different mathematical domains; one does not imply the other.

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
from typing import Dict
from pathlib import Path
from scipy.linalg import expm

from te2_4_hilbert_space import (
    HorizonHilbertSpace, HilbertSpaceConfig
)
from te2_4_gksl_constructor import GKSLMasterEquation, GKSLConfig
from te2_4_stinespring import StinespringDilation


def sha256_of_dict(d: dict) -> str:
    serialised = json.dumps(d, sort_keys=True, default=lambda x: x.tolist()
                             if hasattr(x, 'tolist') else float(x)).encode()
    return hashlib.sha256(serialised).hexdigest()


def fidelity(rho: NDArray, sigma: NDArray) -> float:
    """F(ρ,σ) = Tr(√(√ρ σ √ρ))² """
    sqrt_rho = np.linalg.matrix_power(
        np.linalg.cholesky(rho + 1e-12 * np.eye(rho.shape[0])), 1
    )
    # Use eigenvalue approach for stability
    M = sqrt_rho @ sigma @ sqrt_rho.conj().T
    eigvals = np.maximum(np.linalg.eigvalsh(M), 0)
    return float(np.sum(np.sqrt(eigvals)) ** 2)


def build_stinespring_unitary(H_space: HorizonHilbertSpace,
                               gksl: GKSLMasterEquation,
                               dt: float = 0.01) -> NDArray:
    """
    Build the full Stinespring unitary U on H_sys ⊗ H_E.
    
    U is a (d_sys * d_E) × (d_sys * d_E) unitary matrix constructed
    from the Kraus operators by:
        U = [K_0  K_1 ...]  (column blocks, then completed to unitary via QR)
    
    Returns U as a numpy array of shape (d_sys*d_E, d_sys*d_E).
    """
    dim = H_space.total_dim
    H_mat = H_space.hamiltonian()
    lindblad_ops = [entry[2] for entry in gksl.lindblad_operators]
    lindblad_rates = [entry[2] for entry in gksl.lindblad_rates]
    n_lindblad = len(lindblad_ops)
    dim_env = 1 + n_lindblad

    # First-order Kraus operators (consistent with te2_4_stinespring.py)
    sum_LdL = np.zeros((dim, dim), dtype=np.complex128)
    for Lk, gk in zip(lindblad_ops, lindblad_rates):
        sum_LdL += gk * Lk.conj().T @ Lk

    K0 = np.eye(dim, dtype=np.complex128) - (1j * H_mat + 0.5 * sum_LdL) * dt
    Ks = [K0]
    for Lk, gk in zip(lindblad_ops, lindblad_rates):
        Ks.append(np.sqrt(gk * dt) * Lk)

    # Assemble isometry V: H_sys → H_sys ⊗ H_E
    # V = [K_0; K_1; ...; K_m] as a (dim*dim_env) × dim matrix
    V = np.vstack(Ks)  # shape: (dim*dim_env, dim)

    # Complete V to a square unitary U via QR decomposition
    # V has dim_env*dim rows and dim columns; we need to complete to square
    full_dim = dim * dim_env
    assert V.shape == (full_dim, dim), f"V shape mismatch: {V.shape} vs ({full_dim}, {dim})"

    # Build full_dim × full_dim unitary: first dim columns are V
    # Remaining full_dim - dim columns: QR orthogonal complement
    Q, _ = np.linalg.qr(V, mode='complete')  # Q is full_dim × full_dim unitary
    # Q[:, :dim] should approximate V (up to phase); take first dim columns
    # Assemble U = [Q[:, :dim], Q[:, dim:]]
    U = Q  # full_dim × full_dim unitary

    # Verify: Tr_E[U(ρ ⊗ |0⟩⟨0|)U†] ≈ Φ(ρ) for a test state
    rho_test = np.zeros((dim, dim), dtype=np.complex128)
    rho_test[0, 0] = 1.0  # vacuum

    # Extend to enlarged space: ρ_ext = ρ ⊗ |0⟩⟨0|_E
    env_zero = np.zeros(dim_env, dtype=np.complex128)
    env_zero[0] = 1.0
    env_zero_proj = np.outer(env_zero, env_zero.conj())
    rho_ext = np.kron(rho_test, env_zero_proj)

    # Evolve: ρ_ext' = U ρ_ext U†
    rho_ext_evolved = U @ rho_ext @ U.conj().T

    # Partial trace over environment to get system state
    # Reshape: (dim, dim_env, dim, dim_env)
    rho_sys = np.einsum('iajb->ij',
                         rho_ext_evolved.reshape(dim, dim_env, dim, dim_env))

    # Compare with direct GKSL propagation
    liouv = _build_liouvillian_fast(H_mat, lindblad_ops, lindblad_rates)
    rho_gksl = rho_test + (liouv @ rho_test.reshape(-1) * dt).reshape(dim, dim)
    rho_gksl = (rho_gksl + rho_gksl.conj().T) / 2
    rho_gksl /= np.real(np.trace(rho_gksl))

    fid_check = fidelity(
        rho_sys + 1e-12 * np.eye(dim),
        rho_gksl + 1e-12 * np.eye(dim)
    )
    print(f"  Stinespring construction verification: F(Stinespring, GKSL) = {fid_check:.8f}")

    return U, dim, dim_env


def _build_liouvillian_fast(H_op, lindblad_ops, rates):
    d = H_op.shape[0]
    I = np.eye(d, dtype=np.complex128)
    L = -1j * (np.kron(H_op, I) - np.kron(I, H_op.T))
    for Lk, gk in zip(lindblad_ops, rates):
        LkLk = Lk.conj().T @ Lk
        L += gk * (np.kron(Lk, Lk.conj()) - 0.5*np.kron(LkLk, I) - 0.5*np.kron(I, LkLk.T))
    return L


def run_pt_inverse_circuit(
    T_H: float = 0.003979,
    n_modes: int = 3,
    d_levels: int = 2,
    coupling: float = 0.01,
    dt: float = 0.01,
    n_thermalization_steps: int = 20000,
) -> Dict:
    """
    Test PT^{-1} as explicit quantum circuit (Stinespring adjoint).

    Protocol:
    1. Thermalize: start from |0,0,0⟩, evolve under GKSL for many steps
    2. Apply PT^{-1} = U†: to (ρ_thermal ⊗ |env_ref⟩⟨env_ref|)
    3. Partial trace over environment
    4. Measure fidelity with original vacuum state

    Prediction: F(PT^{-1}(ρ_thermal ⊗ |0_E⟩), |0,0,0⟩) ≈ 1 - ε
    where ε ~ O(Δt²) ≈ 10^{-4} from the Kraus approximation.
    """
    print("=" * 60)
    print("COMP-P16-B: PT^{-1} as Explicit Quantum Circuit")
    print("=" * 60)
    print(f"  T_H = {T_H:.6f}")
    print(f"  n_modes = {n_modes}, d_levels = {d_levels}")
    print(f"  coupling = {coupling}")
    print(f"  Thermalization: {n_thermalization_steps} steps × dt={dt}")
    print()

    # Build system
    mode_freqs = (np.arange(n_modes) + 0.5) * np.pi * T_H
    hilbert_config = HilbertSpaceConfig(
        n_modes=n_modes, n_levels_per_mode=d_levels,
        hawking_temperature=T_H, mode_frequencies=mode_freqs
    )
    H_space = HorizonHilbertSpace(hilbert_config)
    gksl_config = GKSLConfig(
        hilbert_config=hilbert_config, coupling_strength=coupling,
        hawking_temperature=T_H, check_detailed_balance=True, check_cptp=True
    )
    gksl = GKSLMasterEquation(gksl_config, H_space)
    dim = H_space.total_dim

    # ── Build Stinespring unitary ────────────────────────────────────
    print("Building Stinespring unitary U...")
    t0 = time.time()
    U, dim_sys, dim_env = build_stinespring_unitary(H_space, gksl, dt=dt)
    t1 = time.time()
    print(f"  U shape: {U.shape[0]}×{U.shape[1]}")
    print(f"  Build time: {t1-t0:.2f}s")
    print(f"  U unitarity check: ||UU†-I||_F = {np.linalg.norm(U @ U.conj().T - np.eye(U.shape[0])):.2e}")

    # ── Initial vacuum state ─────────────────────────────────────────
    rho_vacuum = np.zeros((dim, dim), dtype=np.complex128)
    rho_vacuum[0, 0] = 1.0

    # ── Thermalization phase ─────────────────────────────────────────
    print(f"\nThermalization ({n_thermalization_steps} GKSL steps)...")
    H_mat = H_space.hamiltonian()
    lindblad_ops = [entry[2] for entry in gksl.lindblad_operators]
    lindblad_rates = [entry[2] for entry in gksl.lindblad_rates]
    liouv = _build_liouvillian_fast(H_mat, lindblad_ops, lindblad_rates)

    rho = rho_vacuum.copy()
    for step in range(n_thermalization_steps):
        rho_flat = rho.reshape(-1) + liouv @ rho.reshape(-1) * dt
        rho = rho_flat.reshape(dim, dim)
        rho = (rho + rho.conj().T) / 2
        rho /= np.real(np.trace(rho))

    rho_thermal_achieved = rho.copy()
    rho_thermal_true = H_space.thermal_state()

    S_achieved = float(-np.sum(
        e * np.log(e) for e in np.maximum(np.linalg.eigvalsh(rho_thermal_achieved), 1e-15)
    ))
    S_ideal = float(-np.sum(
        e * np.log(e) for e in np.maximum(np.linalg.eigvalsh(rho_thermal_true), 1e-15)
    ))

    F_thermal = fidelity(rho_thermal_achieved + 1e-12*np.eye(dim),
                          rho_thermal_true + 1e-12*np.eye(dim))
    purity = float(np.real(np.trace(rho_thermal_achieved @ rho_thermal_achieved)))

    print(f"  Achieved entropy: {S_achieved:.4f} / ideal: {S_ideal:.4f}")
    print(f"  Fidelity with ideal thermal state: {F_thermal:.6f}")
    print(f"  Purity: {purity:.4f}")

    # ── Apply PT^{-1} = U† ─────────────────────────────────────────
    # Protocol: (ρ_th ⊗ |0_E⟩⟨0_E|) → U† → partial trace over E
    print("\nApplying PT^{-1} = U†...")

    # Reference environment state |0_E⟩
    env_zero = np.zeros(dim_env, dtype=np.complex128)
    env_zero[0] = 1.0
    env_zero_proj = np.outer(env_zero, env_zero.conj())

    # Extend thermal state: ρ_ext = ρ_th ⊗ |0_E⟩⟨0_E|
    rho_ext = np.kron(rho_thermal_achieved, env_zero_proj)

    # Apply U†: ρ_ext' = U† ρ_ext U
    t0 = time.time()
    rho_ext_recovered = U.conj().T @ rho_ext @ U
    t1 = time.time()

    # Partial trace over environment → recovered system state
    full_dim = dim * dim_env
    rho_recovered = np.einsum(
        'iajb->ij',
        rho_ext_recovered.reshape(dim, dim_env, dim, dim_env)
    )
    rho_recovered = (rho_recovered + rho_recovered.conj().T) / 2
    trace_recovered = np.real(np.trace(rho_recovered))
    rho_recovered /= trace_recovered

    # ── Compute recovery fidelity ───────────────────────────────────
    F_recovery = fidelity(
        rho_recovered + 1e-12 * np.eye(dim),
        rho_vacuum + 1e-12 * np.eye(dim)
    )
    purity_recovered = float(np.real(np.trace(rho_recovered @ rho_recovered)))
    S_recovered = float(-np.sum(
        e * np.log(e) for e in np.maximum(np.linalg.eigvalsh(rho_recovered), 1e-15)
    ))

    print(f"  Apply time: {t1-t0:.2f}s")
    print(f"\n  Recovery results:")
    print(f"    F(PT^{{-1}}(ρ_th), |vacuum⟩) = {F_recovery:.8f}")
    print(f"    Expected (Kraus approx):     ≥ {1 - dt**2:.8f}")
    print(f"    Purity of recovered state:   {purity_recovered:.6f}")
    print(f"    Entropy of recovered state:  {S_recovered:.6f}")
    print(f"    (Ideal: purity=1, entropy=0)")

    # Physical interpretation
    expected_fidelity = 1.0 - dt**2  # O(Δt²) bound
    pt_inverse_operational = F_recovery >= 0.99  # within 1% of vacuum

    print(f"\n  PT^{{-1}} operational? {pt_inverse_operational} (F={F_recovery:.4f})")
    if pt_inverse_operational:
        print("  ✓ PT^{-1} recovers vacuum to fidelity ≥ 0.99")
        print("  ✓ Information recovery is demonstrated in this toy model")
    else:
        print(f"  Partial recovery: F={F_recovery:.4f} < 0.99")
        print(f"  Note: thermalization fraction = {S_achieved/S_ideal:.3f} (not fully thermal)")

    # ── Alternative: apply PT^{-1} to the true thermal state ───────
    print("\n  Applying PT^{-1} to IDEAL thermal state (ground truth)...")
    rho_ext_ideal = np.kron(rho_thermal_true, env_zero_proj)
    rho_ext_ideal_recovered = U.conj().T @ rho_ext_ideal @ U
    rho_recovered_ideal = np.einsum(
        'iajb->ij',
        rho_ext_ideal_recovered.reshape(dim, dim_env, dim, dim_env)
    )
    rho_recovered_ideal = (rho_recovered_ideal + rho_recovered_ideal.conj().T) / 2
    rho_recovered_ideal /= np.real(np.trace(rho_recovered_ideal))

    F_recovery_ideal = fidelity(
        rho_recovered_ideal + 1e-12 * np.eye(dim),
        rho_vacuum + 1e-12 * np.eye(dim)
    )
    print(f"  F(PT^{{-1}}(ρ_th_ideal), |vacuum⟩) = {F_recovery_ideal:.8f}")

    # ── Results ───────────────────────────────────────────────────
    results = {
        "config": {
            "T_H": T_H, "n_modes": n_modes, "d_levels": d_levels,
            "coupling": coupling, "dt": dt,
            "n_thermalization_steps": n_thermalization_steps,
        },
        "thermalization": {
            "entropy_achieved": S_achieved,
            "entropy_ideal": S_ideal,
            "fidelity_with_ideal_thermal": F_thermal,
            "purity": purity,
        },
        "pt_inverse_circuit": {
            "F_recovery_from_achieved_thermal": F_recovery,
            "F_recovery_from_ideal_thermal": F_recovery_ideal,
            "expected_fidelity_kraus_approx": expected_fidelity,
            "purity_recovered": purity_recovered,
            "entropy_recovered": S_recovered,
            "pt_inverse_operational": pt_inverse_operational,
            "interpretation": (
                f"PT^{{-1}} = U† recovers the vacuum state from the thermal state "
                f"to fidelity F={F_recovery:.6f}. "
                + (
                    "Information recovery is demonstrated: applying the Stinespring adjoint "
                    "to the (thermalized system ⊗ reference environment) pair returns "
                    "the system to its pre-evaporation state to high fidelity."
                    if pt_inverse_operational else
                    f"Partial recovery only (F={F_recovery:.4f}). The system has not fully "
                    f"thermalized ({S_achieved/S_ideal:.1%} of thermal entropy reached); "
                    "incomplete thermalization limits the recovery demonstration."
                )
            ),
        },
    }

    return results


def main():
    out_dir = Path(__file__).resolve().parents[1] / "results" / "pt_inverse_circuit"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "final_results.json"

    results = run_pt_inverse_circuit(
        n_thermalization_steps=50000,  # run until very close to thermal
        dt=0.01,
    )

    sha = sha256_of_dict(results)
    results["sha256"] = sha

    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved: {out_path}")
    print(f"SHA-256: {sha}")

    pt = results["pt_inverse_circuit"]
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  F(PT^{{-1}}(ρ_th), |vacuum⟩) = {pt['F_recovery_from_achieved_thermal']:.6f}")
    print(f"  F(PT^{{-1}}(ρ_th_ideal), |vacuum⟩) = {pt['F_recovery_from_ideal_thermal']:.6f}")
    print(f"  PT^{{-1}} operational: {pt['pt_inverse_operational']}")
    print(f"\n  {pt['interpretation']}")


if __name__ == "__main__":
    main()
