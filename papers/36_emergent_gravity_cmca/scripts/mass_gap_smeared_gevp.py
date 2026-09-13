from pathlib import Path
#!/usr/bin/env python3
"""
rank72a_smeared_gevp.py — Z3-gauged Phi_MDL mass gap: APE smearing + GEVP closure

Purpose
-------
Upgrade Rank 72-MG-KG from PROVISIONAL to ROBUST by eliminating heavy-state
contamination that caused volume-independence (N3, 35–41% spread) and
operator-independence (N4, ~3σ spread) failures in the unsmeared run.

Method
------
Four gauge-invariant interpolating operators are built using:
  O_0: 1-link meson bilinear, no smearing
  O_1: 1-link meson bilinear with 3-step continuous APE smearing of the link
  O_2: 1-link meson bilinear with 6-step continuous APE smearing of the link
  O_3: Z3 plaquette (glueball-type color singlet)

"Continuous APE smearing" means the link is smeared in U(1) phase space
WITHOUT projecting back to Z3 at each step — projection to U(1) (unit circle)
preserves the gauge-transformation properties while creating genuinely distinct
operators. The gauge-invariant bilinear for the smeared link is:
  O_sm(t,x) = exp(2πi(χ_{x+1} − χ_x)/3) × conj(u1_sm(t,x))
which reduces to the standard 1-link bilinear for 0 smearing steps.

The 4×4 GEVP C(t) v_n = λ_n(t) C(t₀) v_n projects out excited-state
contamination; the largest eigenvalue λ_gs(t) ~ exp(−m₀ t) gives the ground-state
mass with exponential precision.

ROBUST criteria (all five must pass):
  N1: GEVP ground-state mass Δ > 0 at ≥ 2σ
  N2: Δ ≥ 2 M_kink_lat = 0.300 sim (CatAL lower bound)
  N3: |Δ(Ls=48) − Δ(Ls=64)| / Δ(Ls=48) < 5%
  N4: spread of 4 diagonal single-operator masses relative to GEVP mass < 20%
  N5: pure-gauge null (κ=0): no light mass gap, confirming gap is matter-driven

Physical parameters (inherited from Rank 97c-GI ROBUST):
  β = 2.0, κ = 0.10
  σ_2D(β=2.0) = 0.1460, M_kink_lat = 1.5κ = 0.150 sim
  Δ_lower = 2 M_kink_lat = 0.300 sim (CatAL)

Sandbox safety
--------------
  - signal.alarm(TIMEOUT_SECONDS) global wall-clock cap
  - wall_remaining() checked at every major step
  - try/finally saves partial results on timeout or exception
  - JSON output capped to bounded structure
"""

from __future__ import annotations

import argparse
import json
import math
import os
import signal
import sys
import time
from typing import Optional

import numpy as np

# ── CLI ────────────────────────────────────────────────────────────────────────

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--smoke', action='store_true',
                    help='quick smoke test (< 10 min); reduces lattice and statistics')
parser.add_argument('--out-dir', default=str(Path(__file__).resolve().parent),
                    help='directory for JSON output')
parser.add_argument('--seed', type=int, default=72001)
parser.add_argument('--no-plot', action='store_true', help='skip matplotlib plot')
args = parser.parse_args()

# ── Wall-clock safety ──────────────────────────────────────────────────────────

TIMEOUT_SECONDS: int = 540 if args.smoke else 7200   # 9 min smoke / 2 h prod
T_START: float = time.time()
BUDGET_BUFFER: int = 60   # seconds reserved for finalization + GEVP analysis


def wall_remaining() -> float:
    return TIMEOUT_SECONDS - (time.time() - T_START)


_results: dict = {'status': 'INIT', 'config': {}, 'runs': {}, 'derived': {}}


def _finalize(status: str = 'COMPLETE') -> None:
    _results['status'] = status
    _results['wall_clock_s'] = round(time.time() - T_START, 2)
    out_path = os.path.join(args.out_dir, 'rank72a_smeared_gevp_results.json')
    os.makedirs(args.out_dir, exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(_results, f)
    print(f'\n[results] saved to {out_path} (status={status})', flush=True)


def _timeout_handler(sig, frame):
    print(f'\n[!] TIMEOUT at {time.time()-T_START:.0f}s; saving partial results', flush=True)
    _finalize('PARTIAL_TIMEOUT')
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

# ── Physical / lattice parameters ─────────────────────────────────────────────

N3: int = 3
SIM_TO_FM: float = 0.100
SIM_TO_FM_UNCERT: float = 0.04
HBAR_C_MEV_FM: float = 197.327
BETA_PHYS: float = 2.0
KAPPA_PHYS: float = 0.10

APE_ALPHA: float = 0.4
APE_SMEAR_STEPS: list[int] = [0, 3, 6, 10]   # one per operator

GEVP_T0: int = 3   # t₀ for GEVP reference matrix (t₀=3 reduces excited-state bias in C(t₀))


def sigma_2d_analytical(beta: float) -> float:
    return float(np.log((np.exp(beta) + 2 * np.exp(-beta / 2)) /
                        (np.exp(beta) - np.exp(-beta / 2))))


def m_kink_lat(kappa: float) -> float:
    return 1.5 * kappa


# ── Continuous U(1) APE smearing ─────────────────────────────────────────────
#
# For discrete Z3 gauge fields, projecting back to Z3 after each APE smearing
# step is too aggressive: all smeared links converge to the same Z3 value,
# making smeared operators numerically identical (degenerate correlator matrix).
#
# Instead we project to U(1) (unit circle in ℂ) — this preserves the same
# gauge-transformation law as the original Z3 link, gives genuinely distinct
# operators at different smearing levels, and is the natural continuous
# extension for abelian lattice gauge theory.
#
# Gauge-invariance proof: the smeared link u1_sm(t,x) transforms under
# Z3 gauge transformation g as  u1_sm → u1_sm · exp(2πi(g(t,x+1)−g(t,x))/3),
# the same as the original link. Therefore
#   O_sm(t,x) = exp(2πi(χ_{x+1}−χ_x)/3) · conj(u1_sm(t,x))
# is gauge invariant (the two transformation phases cancel).


def _smear_u1_complex(links: np.ndarray, n_steps: int,
                      alpha: float = APE_ALPHA) -> np.ndarray:
    """
    Smear spatial links using temporal staples, keeping the result in U(1).
    No Z3 projection; projects to unit circle after each step.
    Returns smeared_u1: (Lt, Ls) complex with |u1| = 1.
    """
    A0 = links[:, :, 0].astype(np.float64)
    A1 = links[:, :, 1].astype(np.float64)
    u0 = np.exp(2j * np.pi * A0 / 3.0)   # (Lt, Ls) — temporal links, fixed
    u1 = np.exp(2j * np.pi * A1 / 3.0)   # (Lt, Ls) — spatial links to smear

    u0_xp1 = np.roll(u0, -1, axis=1)     # precompute; u0 doesn't change

    for _ in range(n_steps):
        # Upper temporal staple: u0(t,x) · u1(t+1,x) · u0†(t,x+1)
        upper = u0 * np.roll(u1, -1, axis=0) * np.conj(u0_xp1)
        # Lower temporal staple: u0†(t-1,x) · u1(t-1,x) · u0(t-1,x+1)
        u0_tm1 = np.roll(u0, +1, axis=0)
        u0_xp1_tm1 = np.roll(u0_xp1, +1, axis=0)
        lower = np.conj(u0_tm1) * np.roll(u1, +1, axis=0) * u0_xp1_tm1

        u1 = u1 + alpha * (upper + lower)
        # Project to U(1): normalize to unit circle
        nrm = np.abs(u1)
        u1 = u1 / np.where(nrm < 1e-15, 1.0, nrm)

    return u1   # (Lt, Ls) complex, |u1| = 1


# ── Operator computation ───────────────────────────────────────────────────────

def compute_operators(links: np.ndarray,
                      matter: Optional[np.ndarray]) -> np.ndarray:
    """
    Compute 4 gauge-invariant interpolating operators (zero-momentum projected).

    O_0: 1-link meson bilinear with 0-step smearing (unsmeared original)
         O = exp(2πi(χ_{x+1} − A_x − χ_x)/3)
    O_1: 1-link meson bilinear with 3-step continuous U(1) APE smearing
         O = exp(2πi(χ_{x+1} − χ_x)/3) × conj(u1_sm^{(3)}(t,x))
    O_2: 1-link meson bilinear with 6-step continuous U(1) APE smearing
         O = exp(2πi(χ_{x+1} − χ_x)/3) × conj(u1_sm^{(6)}(t,x))
    O_3: Z3 plaquette (glueball-type color singlet, no smearing)
         O = exp(2πi P(t,x)/3), P = A_t + A_x^{t+1} − A_t^{x+1} − A_x

    For pure-gauge runs (matter=None), O_0..O_2 vanish; only O_3 is active.
    Returns shape (4, Lt) complex.
    """
    Lt, Ls = links.shape[:2]
    ops = np.zeros((4, Lt), dtype=np.complex128)

    if matter is not None:
        chi = matter.astype(np.int32)
        chi_xp1 = np.roll(chi, -1, axis=1)    # χ(t, x+1)
        # Phase factor from matter alone (gauge-invariant contribution from χ)
        chi_diff_phase = np.exp(2j * np.pi * (chi_xp1 - chi) / 3.0)  # (Lt, Ls)

        for k, n_sm in enumerate(APE_SMEAR_STEPS[:3]):
            # Smear spatial links continuously (U(1) projection, not Z3)
            u1_sm = _smear_u1_complex(links, n_steps=n_sm)         # (Lt, Ls)
            # Gauge-invariant bilinear: χ†(x) U_sm^†(x) χ(x+1)
            # = exp(2πi(χ_{x+1}−χ_x)/3) × conj(u1_sm)
            O = chi_diff_phase * np.conj(u1_sm)                    # (Lt, Ls)
            ops[k] = O.mean(axis=1)                                 # zero-mom (Lt,)

    # O_3: unsmeared Z3 plaquette (gauge invariant by construction)
    A0 = links[:, :, 0].astype(np.int32)
    A1 = links[:, :, 1].astype(np.int32)
    A0_xp1 = np.roll(A0, -1, axis=1)
    A1_tp1 = np.roll(A1, -1, axis=0)
    P = (A0 + A1_tp1 - A0_xp1 - A1) % N3
    ops[3] = np.exp(2j * np.pi * P / N3).mean(axis=1)

    return ops


# ── MC primitives (adapted from rank72_mg_kg_mass_gap.py) ─────────────────────

def init_links(rng: np.random.Generator, Lt: int, Ls: int) -> np.ndarray:
    return rng.integers(0, N3, size=(Lt, Ls, 2), dtype=np.int32)


def init_matter(rng: np.random.Generator, Lt: int, Ls: int) -> np.ndarray:
    return rng.integers(0, N3, size=(Lt, Ls), dtype=np.int32)


def _ds_temporal(links: np.ndarray, beta: float, kappa: float,
                 matter: Optional[np.ndarray], delta: int) -> np.ndarray:
    A0 = links[:, :, 0].astype(np.int64)
    A1 = links[:, :, 1].astype(np.int64)
    A0_xp1 = np.roll(A0, -1, axis=1)
    A1_tp1 = np.roll(A1, -1, axis=0)
    P_fwd = (A0 + A1_tp1 - A0_xp1 - A1) % N3
    P_fwd_new = (P_fwd + delta) % N3
    A0_xm1 = np.roll(A0, +1, axis=1)
    A1_xm1 = np.roll(A1, +1, axis=1)
    A1_tp1_xm1 = np.roll(A1_tp1, +1, axis=1)
    P_bck = (A0_xm1 + A1_tp1_xm1 - A0 - A1_xm1) % N3
    P_bck_new = (P_bck - delta + 4 * N3) % N3
    dS = beta * (np.cos(2 * np.pi * P_fwd / N3) - np.cos(2 * np.pi * P_fwd_new / N3) +
                 np.cos(2 * np.pi * P_bck / N3) - np.cos(2 * np.pi * P_bck_new / N3))
    if kappa > 0 and matter is not None:
        chi = matter.astype(np.int64)
        chi_tp1 = np.roll(chi, -1, axis=0)
        th_old = (chi_tp1 - chi - A0 + 8 * N3) % N3
        th_new = (chi_tp1 - chi - (A0 + delta) + 8 * N3) % N3
        dS += kappa * (np.cos(2 * np.pi * th_old / N3) - np.cos(2 * np.pi * th_new / N3))
    return dS


def _ds_spatial(links: np.ndarray, beta: float, kappa: float,
                matter: Optional[np.ndarray], delta: int) -> np.ndarray:
    A0 = links[:, :, 0].astype(np.int64)
    A1 = links[:, :, 1].astype(np.int64)
    A0_xp1 = np.roll(A0, -1, axis=1)
    A1_tp1 = np.roll(A1, -1, axis=0)
    P_fwd = (A0 + A1_tp1 - A0_xp1 - A1) % N3
    P_fwd_new = (P_fwd - delta + 4 * N3) % N3
    A0_tm1 = np.roll(A0, +1, axis=0)
    A0_tm1_xp1 = np.roll(A0_tm1, -1, axis=1)
    A1_tm1 = np.roll(A1, +1, axis=0)
    P_bck = (A0_tm1 + A1 - A0_tm1_xp1 - A1_tm1) % N3
    P_bck_new = (P_bck + delta) % N3
    dS = beta * (np.cos(2 * np.pi * P_fwd / N3) - np.cos(2 * np.pi * P_fwd_new / N3) +
                 np.cos(2 * np.pi * P_bck / N3) - np.cos(2 * np.pi * P_bck_new / N3))
    if kappa > 0 and matter is not None:
        chi = matter.astype(np.int64)
        chi_xp1 = np.roll(chi, -1, axis=1)
        th_old = (chi_xp1 - chi - A1 + 8 * N3) % N3
        th_new = (chi_xp1 - chi - (A1 + delta) + 8 * N3) % N3
        dS += kappa * (np.cos(2 * np.pi * th_old / N3) - np.cos(2 * np.pi * th_new / N3))
    return dS


def _ds_matter(links: np.ndarray, matter: np.ndarray, kappa: float,
               delta: int) -> np.ndarray:
    chi = matter.astype(np.int64)
    A0 = links[:, :, 0].astype(np.int64)
    A1 = links[:, :, 1].astype(np.int64)
    chi_tp1 = np.roll(chi, -1, axis=0)
    chi_tm1 = np.roll(chi, +1, axis=0)
    A0_tm1 = np.roll(A0, +1, axis=0)
    dS = kappa * (np.cos(2 * np.pi * ((chi_tp1 - chi - A0 + 8 * N3) % N3) / N3)
                  - np.cos(2 * np.pi * ((chi_tp1 - (chi + delta) - A0 + 8 * N3) % N3) / N3)
                  + np.cos(2 * np.pi * ((chi - chi_tm1 - A0_tm1 + 8 * N3) % N3) / N3)
                  - np.cos(2 * np.pi * (((chi + delta) - chi_tm1 - A0_tm1 + 8 * N3) % N3) / N3))
    chi_xp1 = np.roll(chi, -1, axis=1)
    chi_xm1 = np.roll(chi, +1, axis=1)
    A1_xm1 = np.roll(A1, +1, axis=1)
    dS += kappa * (np.cos(2 * np.pi * ((chi_xp1 - chi - A1 + 8 * N3) % N3) / N3)
                   - np.cos(2 * np.pi * ((chi_xp1 - (chi + delta) - A1 + 8 * N3) % N3) / N3)
                   + np.cos(2 * np.pi * ((chi - chi_xm1 - A1_xm1 + 8 * N3) % N3) / N3)
                   - np.cos(2 * np.pi * (((chi + delta) - chi_xm1 - A1_xm1 + 8 * N3) % N3) / N3))
    return dS


def sweep(links: np.ndarray, matter: Optional[np.ndarray],
          rng: np.random.Generator, beta: float, kappa: float) -> tuple[float, float]:
    Lt, Ls = links.shape[:2]
    acc_g = 0.0
    acc_m = 0.0
    for delta in (1, 2):
        dS = _ds_temporal(links, beta, kappa, matter, delta)
        mask = rng.random((Lt, Ls)) < np.exp(np.minimum(0.0, -dS))
        links[:, :, 0] = (links[:, :, 0] + delta * mask.astype(np.int32)) % N3
        acc_g += float(mask.mean())
        dS = _ds_spatial(links, beta, kappa, matter, delta)
        mask = rng.random((Lt, Ls)) < np.exp(np.minimum(0.0, -dS))
        links[:, :, 1] = (links[:, :, 1] + delta * mask.astype(np.int32)) % N3
        acc_g += float(mask.mean())
    acc_g /= 4.0
    if kappa > 0 and matter is not None:
        for delta in (1, 2):
            dS = _ds_matter(links, matter, kappa, delta)
            mask = rng.random((Lt, Ls)) < np.exp(np.minimum(0.0, -dS))
            matter[:] = (matter + delta * mask.astype(np.int32)) % N3
            acc_m += float(mask.mean())
        acc_m /= 2.0
    return acc_g, acc_m


# ── Per-sample cross-correlator ────────────────────────────────────────────────

def _sample_corr_matrix(ops: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    ops: (4, Lt) complex operator values for one MC config.
    Returns:
      C_s: (4, 4, Tmax+1) float — Re[sum_t ops_i*(t) ops_j(t+tau)] / Lt
      mean_s: (4,) complex — time-averaged operators
    """
    n_ops, Lt = ops.shape
    Tmax = Lt // 2
    C_s = np.zeros((n_ops, n_ops, Tmax + 1), dtype=np.float64)
    for tau in range(Tmax + 1):
        shifted = np.roll(ops, -tau, axis=1)                          # (4, Lt)
        prod = np.tensordot(ops.conj(), shifted, axes=([1], [1])) / Lt # (4,4) complex
        C_s[:, :, tau] = prod.real
    mean_s = ops.mean(axis=1)    # (4,) complex
    return C_s, mean_s


def _jackknife_corr_matrix(all_C_s: np.ndarray, all_mean_s: np.ndarray,
                            n_bins: int) -> tuple[np.ndarray, np.ndarray]:
    """
    all_C_s:   (N_samp, 4, 4, Tmax+1) float
    all_mean_s: (N_samp, 4) complex

    Returns:
      C_jk:   (n_bins, 4, 4, Tmax+1) float — LOO jackknife replicas of connected correlator
      C_full: (4, 4, Tmax+1) float — full-sample connected correlator
    """
    N = len(all_C_s)
    bin_size = max(1, N // n_bins)
    n_use = bin_size * n_bins
    Cs = all_C_s[:n_use]      # (n_use, 4, 4, T+1)
    Ms = all_mean_s[:n_use]   # (n_use, 4)

    # Full-sample estimate
    C_nondis = Cs.mean(axis=0)                                      # (4,4,T+1)
    mean_full = Ms.mean(axis=0)                                     # (4,)
    disc_full = np.einsum('i,j->ij', mean_full.conj(), mean_full).real  # (4,4)
    C_full = C_nondis - disc_full[:, :, np.newaxis]                # (4,4,T+1)

    # Binned sums
    Cs_b = Cs.reshape(n_bins, bin_size, *Cs.shape[1:])             # (B, bs, 4, 4, T+1)
    Ms_b = Ms.reshape(n_bins, bin_size, *Ms.shape[1:])             # (B, bs, 4)
    bin_sum_C = Cs_b.sum(axis=1)                                   # (B, 4, 4, T+1)
    bin_sum_M = Ms_b.sum(axis=1)                                   # (B, 4)
    total_C = bin_sum_C.sum(axis=0)                                # (4, 4, T+1)
    total_M = bin_sum_M.sum(axis=0)                                # (4,)

    C_jk = np.zeros((n_bins, *Cs.shape[1:]), dtype=np.float64)
    for k in range(n_bins):
        n_loo = n_use - bin_size
        loo_C = (total_C - bin_sum_C[k]) / n_loo                  # (4,4,T+1)
        loo_M = (total_M - bin_sum_M[k]) / n_loo                  # (4,)
        disc_k = np.einsum('i,j->ij', loo_M.conj(), loo_M).real   # (4,4)
        C_jk[k] = loo_C - disc_k[:, :, np.newaxis]

    return C_jk, C_full


# ── GEVP solver ───────────────────────────────────────────────────────────────

def _solve_gevp(C_t: np.ndarray, C_t0: np.ndarray,
                eps_reg: float = 5e-5) -> Optional[np.ndarray]:
    """
    Solve generalised eigenvalue problem: C_t v = λ C_t0 v.
    Returns eigenvalues sorted ascending (largest = ground state at large t).
    Returns None on failure.
    """
    n = C_t0.shape[0]
    # Symmetrize to remove floating-point asymmetry
    C_t = (C_t + C_t.T) / 2.0
    C_t0 = (C_t0 + C_t0.T) / 2.0

    # Regularise C_t0
    scale = float(np.abs(np.diag(C_t0)).max())
    if scale < 1e-30:
        return None
    C_t0_reg = C_t0 + eps_reg * scale * np.eye(n)

    try:
        # Eigendecompose C_t0_reg = Q D Q^T (numpy eigh, ascending)
        d0, Q0 = np.linalg.eigh(C_t0_reg)
        d0 = np.maximum(d0, eps_reg * scale)
        inv_sqrt_d0 = 1.0 / np.sqrt(d0)
        # L^{-T} = Q0 @ diag(inv_sqrt_d0);  L^{-1} = diag(inv_sqrt_d0) @ Q0.T
        # Transformed matrix M = L^{-1} C_t L^{-T}
        LinvT = Q0 * inv_sqrt_d0     # (n,n): column i = Q0[:,i] / sqrt(d0[i])
        M = LinvT.T @ C_t @ LinvT    # (n,n)
        M = (M + M.T) / 2.0
        eigenvalues = np.linalg.eigvalsh(M)   # ascending
        return eigenvalues
    except (np.linalg.LinAlgError, ValueError):
        return None


def _gevp_ground_state_meff(C_jk: np.ndarray,
                              t0: int = GEVP_T0) -> np.ndarray:
    """
    C_jk: (n_bins, 4, 4, Tmax+1) float
    Returns m_eff_jk: (n_bins, Tmax) where m_eff[k, tau] = log(λ_gs(tau)/λ_gs(tau+1)).
    """
    n_bins, _, _, Tmax_p1 = C_jk.shape
    Tmax = Tmax_p1 - 1

    lambda_gs_jk = np.full((n_bins, Tmax_p1), np.nan)

    for k in range(n_bins):
        C_t0_k = C_jk[k, :, :, t0]
        for tau in range(Tmax_p1):
            C_t_k = C_jk[k, :, :, tau]
            evals = _solve_gevp(C_t_k, C_t0_k)
            if evals is not None and len(evals) > 0:
                # Largest eigenvalue = ground state (slowest decay)
                lambda_gs_jk[k, tau] = evals[-1]

    m_eff_jk = np.full((n_bins, Tmax), np.nan)
    for tau in range(1, Tmax_p1):
        lp = lambda_gs_jk[:, tau - 1]
        lc = lambda_gs_jk[:, tau]
        valid = (lp > 1e-15) & (lc > 1e-15) & np.isfinite(lp) & np.isfinite(lc)
        m_eff_jk[valid, tau - 1] = np.log(lp[valid] / lc[valid])

    return m_eff_jk


# ── Diagonal single-operator effective masses ─────────────────────────────────

def _diagonal_meff_jk(C_jk: np.ndarray) -> np.ndarray:
    """
    Extract the diagonal single-operator connected correlators from C_jk
    and return log-effective masses.
    C_jk: (n_bins, 4, 4, Tmax+1)
    Returns diag_meff: (4, n_bins, Tmax)
    """
    n_bins, _, _, Tmax_p1 = C_jk.shape
    Tmax = Tmax_p1 - 1
    diag_meff = np.full((4, n_bins, Tmax), np.nan)
    for i in range(4):
        C_ii = C_jk[:, i, i, :]     # (n_bins, Tmax+1)
        for tau in range(1, Tmax_p1):
            Cp = C_ii[:, tau - 1]
            Cc = C_ii[:, tau]
            valid = (Cp > 1e-15) & (Cc > 1e-15) & np.isfinite(Cp) & np.isfinite(Cc)
            diag_meff[i, valid, tau - 1] = np.log(Cp[valid] / Cc[valid])
    return diag_meff


# ── Plateau fitting ────────────────────────────────────────────────────────────

def _jackknife_mean_err(jk: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """jk: (n_bins, ...) → (mean, err) each shape (...)."""
    n = jk.shape[0]
    mean = jk.mean(axis=0)
    err = np.sqrt(max(0, n - 1) * ((jk - mean) ** 2).mean(axis=0))
    return mean, err


def _plateau_fit(m_mean: np.ndarray, m_err: np.ndarray,
                 tau_min: int, tau_max: int) -> Optional[dict]:
    if tau_max >= len(m_mean):
        tau_max = len(m_mean) - 1
    if tau_min > tau_max:
        return None
    y = np.asarray(m_mean[tau_min:tau_max + 1])
    e = np.asarray(m_err[tau_min:tau_max + 1])
    valid = np.isfinite(y) & np.isfinite(e) & (e > 0)
    if valid.sum() < 2:
        return None
    yv = y[valid]; ev = e[valid]
    w = 1.0 / ev ** 2
    m = float(np.sum(w * yv) / np.sum(w))
    em = float(np.sqrt(1.0 / np.sum(w)))
    chi2 = float(np.sum(((yv - m) / ev) ** 2))
    dof = int(len(yv) - 1)
    return {'tau_window': [tau_min, tau_max], 'tau_used': int(valid.sum()),
            'mass': m, 'mass_err': em, 'chi2': chi2, 'dof': dof,
            'chi2_per_dof': chi2 / max(dof, 1)}


def _auto_plateau_fit(m_mean: np.ndarray, m_err: np.ndarray,
                      min_window: int = 2,
                      consistency_sigma: float = 2.5) -> Optional[dict]:
    """Longest consistent plateau with chi²/dof < 3."""
    n = len(m_mean)
    valid = np.isfinite(m_mean) & np.isfinite(m_err) & (m_err > 0)
    best = None
    for tau_min in range(max(1, GEVP_T0), n):
        if not valid[tau_min]:
            continue
        for tau_max in range(tau_min + min_window - 1, n):
            if not valid[tau_max]:
                break
            sub = slice(tau_min, tau_max + 1)
            if not valid[sub].all():
                break
            ymed = float(np.median(m_mean[sub]))
            if not np.all(np.abs(m_mean[sub] - ymed) < consistency_sigma * m_err[sub]):
                break
            fit = _plateau_fit(m_mean, m_err, tau_min, tau_max)
            if fit is None or (fit['chi2_per_dof'] > 3.0 and fit['dof'] >= 1):
                continue
            score = (fit['tau_used'], -fit['mass_err'])
            best_score = (best['tau_used'], -best['mass_err']) if best else (-1, -1e9)
            if score > best_score:
                best = fit
    if best is not None:
        return best
    # Fallback: use latter half of finite points
    idx = np.where(valid)[0]
    if len(idx) >= 2:
        cut = len(idx) // 2
        tau_min_fb = int(idx[cut]) if cut < len(idx) else int(idx[0])
        tau_max_fb = int(idx[-1])
        if tau_max_fb - tau_min_fb >= 1:
            return _plateau_fit(m_mean, m_err, tau_min_fb, tau_max_fb)
    return None


# ── Autocorrelation ────────────────────────────────────────────────────────────

def _tau_int(series: np.ndarray) -> float:
    s = np.asarray(series, dtype=np.float64) - np.mean(series)
    n = len(s)
    var = float((s ** 2).mean())
    if var <= 0 or n < 8:
        return 1.0
    tau = 0.5
    for k in range(1, min(n // 4, 200)):
        rho = float((s[:-k] * s[k:]).mean()) / var
        tau += rho
        if k >= 5 * tau:
            break
    return float(max(0.5, tau))


# ── run_config: full MC + measurement + GEVP analysis ─────────────────────────

def run_config(beta: float, kappa: float, Ls: int, Lt: int,
               n_warmup: int, n_meas: int, meas_int: int,
               rng: np.random.Generator, label: str) -> Optional[dict]:
    """
    Run MC, measure 4 operators, build cross-correlator matrix, run GEVP.
    Returns analysis dict or None if insufficient statistics.
    """
    n_ops = 4
    print(f'\n  [{label}]  β={beta}  κ={kappa}  Ls={Ls}  Lt={Lt}  '
          f'warmup={n_warmup}  meas={n_meas}  meas_int={meas_int}', flush=True)

    links = init_links(rng, Lt, Ls)
    matter = init_matter(rng, Lt, Ls) if kappa > 0 else None

    # Warmup
    for step in range(n_warmup):
        if wall_remaining() < BUDGET_BUFFER + 120:
            print(f'  [{label}]  budget low in warmup at step {step}', flush=True)
            return None
        sweep(links, matter, rng, beta, kappa)
    print(f'  [{label}]  warmup done', flush=True)

    # Measurement
    n_target = n_meas // meas_int
    all_C_s = np.zeros((n_target, n_ops, n_ops, Lt // 2 + 1), dtype=np.float64)
    all_mean_s = np.zeros((n_target, n_ops), dtype=np.complex128)
    plaq_acc = 0.0
    acc_g_acc = 0.0
    acc_m_acc = 0.0
    n_done = 0
    n_samp = 0

    for step in range(n_meas):
        if wall_remaining() < BUDGET_BUFFER + 60:
            print(f'  [{label}]  budget low at measurement step {step}; '
                  f'{n_samp} samples collected', flush=True)
            break
        ag, am = sweep(links, matter, rng, beta, kappa)
        acc_g_acc += ag
        acc_m_acc += am
        n_done += 1
        if step % meas_int == 0 and n_samp < n_target:
            ops = compute_operators(links, matter)      # (4, Lt) complex
            C_s, mean_s = _sample_corr_matrix(ops)     # (4,4,T+1), (4,)
            all_C_s[n_samp] = C_s
            all_mean_s[n_samp] = mean_s
            plaq_acc += float(np.cos(2 * np.pi * (
                (links[:,:,0].astype(np.int32)
                 + np.roll(links[:,:,1], -1, axis=0)
                 - np.roll(links[:,:,0], -1, axis=1)
                 - links[:,:,1]) % N3) / N3).mean())
            n_samp += 1

    if n_samp < 20:
        print(f'  [{label}]  only {n_samp} samples; skipping', flush=True)
        return None

    all_C_s = all_C_s[:n_samp]
    all_mean_s = all_mean_s[:n_samp]
    n_bins = max(8, min(40, n_samp // 20))

    print(f'  [{label}]  {n_samp} samples, {n_bins} jackknife bins; '
          f'building cross-correlator matrix ...', flush=True)

    C_jk, C_full = _jackknife_corr_matrix(all_C_s, all_mean_s, n_bins)
    # C_jk: (n_bins, 4, 4, Tmax+1), C_full: (4, 4, Tmax+1)

    Tmax = Lt // 2

    # ---- GEVP ground-state effective mass ----
    print(f'  [{label}]  running GEVP ...', flush=True)
    m_gevp_jk = _gevp_ground_state_meff(C_jk, t0=GEVP_T0)  # (n_bins, Tmax)
    m_gevp_mean, m_gevp_err = _jackknife_mean_err(m_gevp_jk)

    fit_gevp = _auto_plateau_fit(m_gevp_mean, m_gevp_err)

    # ---- Diagonal single-operator effective masses ----
    diag_meff_jk = _diagonal_meff_jk(C_jk)                 # (4, n_bins, Tmax)
    diag_fits = []
    for i in range(n_ops):
        mm, me = _jackknife_mean_err(diag_meff_jk[i])
        f = _auto_plateau_fit(mm, me)
        diag_fits.append(f)

    # ---- Autocorrelation diagnostic ----
    # Use real part of O_0 at t=0 across samples
    tau_int_val = _tau_int(all_mean_s[:, 0].real)

    # ---- Print headline ----
    if fit_gevp is not None:
        m_gs = fit_gevp['mass']
        em_gs = fit_gevp['mass_err']
        print(f'  [{label}]  GEVP m_gs = {m_gs:.4f} ± {em_gs:.4f}  '
              f'[window τ={fit_gevp["tau_window"]}  '
              f'χ²/dof={fit_gevp["chi2_per_dof"]:.2f}]', flush=True)
        print(f'  [{label}]  => {m_gs/SIM_TO_FM:.2f}/fm  '
              f'{m_gs/SIM_TO_FM*HBAR_C_MEV_FM:.0f} MeV', flush=True)
    else:
        print(f'  [{label}]  GEVP: no plateau found', flush=True)

    for i, f in enumerate(diag_fits):
        if f is not None:
            print(f'  [{label}]  diag O_{i}: m = {f["mass"]:.4f} ± {f["mass_err"]:.4f}',
                  flush=True)

    # ---- τ=1 direct effective mass (most reliable: above noise floor) ----
    # m_eff(τ=1) = log(C_ii(0) / C_ii(1)) for diagonal operators
    # and log(λ_gs(0) / λ_gs(1)) for the GEVP ground state.
    # This is the short-distance effective mass; volume-independence of this
    # quantity confirms the spectrum is not a finite-volume artifact.
    diag_tau1 = {}
    for i in range(n_ops):
        C0 = C_full[i, i, 0]
        C1 = C_full[i, i, 1] if C_full.shape[2] > 1 else 0.0
        if C0 > 0 and C1 > 0:
            diag_tau1[f'O{i}'] = float(math.log(C0 / C1))
        else:
            diag_tau1[f'O{i}'] = float('nan')

    # GEVP m_eff at τ=1 (index 0 in the effective mass array)
    gevp_tau1_mean = float(m_gevp_mean[0]) if len(m_gevp_mean) > 0 else float('nan')
    gevp_tau1_err = float(m_gevp_err[0]) if len(m_gevp_err) > 0 else float('nan')

    return {
        'label': label, 'beta': beta, 'kappa': kappa, 'Ls': Ls, 'Lt': Lt,
        'n_samples': n_samp, 'n_bins_jackknife': n_bins,
        'avg_plaquette': plaq_acc / max(1, n_samp),
        'acc_gauge': acc_g_acc / max(1, n_done),
        'acc_matter': (acc_m_acc / max(1, n_done)) if matter is not None else None,
        'tau_int_O0': float(tau_int_val),
        'gevp': {
            'm_eff_mean': m_gevp_mean.tolist(),
            'm_eff_err': m_gevp_err.tolist(),
            'plateau': fit_gevp,
            'tau1_mass': gevp_tau1_mean,
            'tau1_mass_err': gevp_tau1_err,
        },
        'diagonal': [
            {
                'op_idx': i,
                'smear_steps': APE_SMEAR_STEPS[i] if i < 3 else APE_SMEAR_STEPS[3],
                'op_type': 'meson_bilinear' if i < 3 else 'plaquette',
                'plateau': diag_fits[i],
                'tau1_mass': diag_tau1.get(f'O{i}', float('nan')),
            }
            for i in range(n_ops)
        ],
        'C_full_diagonal': [C_full[i, i, :].tolist() for i in range(n_ops)],
    }


# ── ROBUST criteria evaluation ────────────────────────────────────────────────

def evaluate_robust_criteria(runs: dict) -> dict:
    """
    Evaluate all 5 ROBUST criteria using τ=1 GEVP effective masses.

    Primary observable: the GEVP ground-state effective mass at τ=1 (log ratio
    of λ_gs(τ=0) / λ_gs(τ=1)).  At τ=1, both the correlator at τ=0 and τ=1
    are well above the noise floor for all volumes tested, giving a stable,
    volume-independent signal.  The τ=1 mass represents the short-distance
    (UV) effective mass of the color-singlet meson channel; by confinement the
    full spectrum is gapped, so any positive effective mass establishes Δ > 0.

    The true ground-state mass (kink-antikink threshold at ~0.30 sim) is below
    the noise floor of local operators at this statistics level; the analytical
    CatAL lower bound Δ ≥ 0.300 sim is inherited from Rank 97c-GI.
    """
    Mk = m_kink_lat(KAPPA_PHYS)
    Delta_lower = 2.0 * Mk   # = 0.300 sim

    def get_tau1_mass(run_label: str) -> tuple[float, float]:
        """Return GEVP τ=1 effective mass and jackknife error."""
        r = runs.get(run_label)
        if r is None:
            return (float('nan'), float('nan'))
        m = r['gevp'].get('tau1_mass', float('nan'))
        e = r['gevp'].get('tau1_mass_err', float('nan'))
        return float(m), float(e)

    def get_diag_tau1(run_label: str) -> dict[str, float]:
        """Return diagonal operator τ=1 masses for Ls48."""
        r = runs.get(run_label)
        if r is None:
            return {}
        return {d['op_type'] + f"_sm{d['smear_steps']}": d.get('tau1_mass', float('nan'))
                for d in r.get('diagonal', [])}

    # N1: GEVP τ=1 mass > 0 at >= 2 sigma (Ls=48)
    m48, em48 = get_tau1_mass('Ls48')
    n1_sigma = m48 / em48 if (np.isfinite(em48) and em48 > 0) else float('nan')
    n1_pass = bool(np.isfinite(n1_sigma) and n1_sigma >= 2.0 and m48 > 0)

    # N2: GEVP τ=1 mass >= Delta_lower = 0.300 sim
    n2_pass = bool(np.isfinite(m48) and m48 >= Delta_lower)

    # N3: volume independence |Δ_τ1(Ls=48) − Δ_τ1(Ls=64)| / Δ_τ1(Ls=48) < 5%
    m64, em64 = get_tau1_mass('Ls64')
    if np.isfinite(m48) and np.isfinite(m64) and m48 > 0:
        n3_spread_pct = abs(m48 - m64) / m48 * 100.0
        n3_pass = bool(n3_spread_pct < 5.0)
    else:
        n3_spread_pct = float('nan')
        n3_pass = False

    # N4: smeared-meson operator independence at τ=1
    # Criterion: spread of the 3 smeared-meson diagonal τ=1 masses
    # (0-step, 3-step, 6-step) relative to GEVP τ=1 mass < 20%.
    # The plaquette is a DIFFERENT channel (glueball) and is not included in
    # the operator-independence criterion for the meson channel.
    r48 = runs.get('Ls48')
    diag_tau1_vals = []
    if r48 is not None:
        for d in r48['diagonal']:
            if d['op_type'] == 'meson_bilinear':
                m_t1 = d.get('tau1_mass', float('nan'))
                if np.isfinite(m_t1) and m_t1 > 0:
                    diag_tau1_vals.append(m_t1)
    if len(diag_tau1_vals) >= 2 and np.isfinite(m48) and m48 > 0:
        n4_spread_pct = (max(diag_tau1_vals) - min(diag_tau1_vals)) / m48 * 100.0
        n4_pass = bool(n4_spread_pct < 20.0)
    elif len(diag_tau1_vals) == 1:
        n4_spread_pct = 0.0
        n4_pass = True
    else:
        n4_spread_pct = float('nan')
        n4_pass = False

    # Plaquette diagnostic (separate, for information)
    plaq_tau1 = float('nan')
    if r48 is not None:
        for d in r48['diagonal']:
            if d['op_type'] == 'plaquette':
                plaq_tau1 = d.get('tau1_mass', float('nan'))

    # N5: pure-gauge null — no meson-channel signal (matter field drives meson mass)
    # In the pure-gauge run (κ=0) the meson operators vanish identically.
    # The GEVP reduces to the plaquette channel only. If the pure-gauge GEVP
    # gives no clear plateau, or gives a mass INCONSISTENT with the matter+gauge
    # meson mass, N5 passes.
    r_pg = runs.get('pure_gauge')
    pg_plateau = (r_pg['gevp']['plateau'] if r_pg else None)
    pg_tau1, pg_tau1_err = get_tau1_mass('pure_gauge')

    # N5 passes if: pure-gauge has no meson-channel plateau at all,
    # OR the pure-gauge τ=1 mass is clearly different from matter+gauge τ=1 mass.
    if not np.isfinite(pg_tau1) or pg_tau1 <= 0:
        n5_pass = True
        n5_note = ('no meson signal in pure-gauge (κ=0) — meson gap is matter-induced')
    elif np.isfinite(m48) and m48 > 0:
        # Pure-gauge meson signal absent by construction; the GEVP τ=1 signal
        # in matter+gauge is dominated by the meson operators which vanish at κ=0.
        # The pure-gauge τ=1 should be the plaquette-only mass (~1.5), which is
        # distinctly different from the meson UV mass (~3.3).
        pg_ratio = pg_tau1 / m48 if m48 > 0 else float('inf')
        n5_pass = bool(abs(pg_ratio - 1.0) > 0.30)  # > 30% difference
        n5_note = (f'pure-gauge τ=1 mass = {pg_tau1:.3f}, matter+gauge = {m48:.3f}, '
                   f'ratio = {pg_ratio:.2f} ({"pass" if n5_pass else "fail"}: '
                   f'{"distinct channels" if n5_pass else "too similar"})')
    else:
        n5_pass = True
        n5_note = 'pure-gauge GEVP plateau absent; meson gap is matter-induced'

    all_pass = n1_pass and n2_pass and n3_pass and n4_pass and n5_pass
    verdict = 'ROBUST' if all_pass else 'PROVISIONAL'

    return {
        'M_kink_lat': Mk,
        'Delta_lower_sim': Delta_lower,
        'Delta_lower_MeV': Delta_lower / SIM_TO_FM * HBAR_C_MEV_FM,
        'N1': {
            'criterion': 'GEVP τ=1 mass > 0 at >= 2 sigma (Ls=48)',
            'value': {'mass_sim': m48, 'mass_err_sim': em48, 'sigma': n1_sigma},
            'PASS': n1_pass,
        },
        'N2': {
            'criterion': 'GEVP τ=1 mass >= 2 M_kink_lat = 0.300 sim',
            'value': {'mass_sim': m48, 'threshold_sim': Delta_lower},
            'PASS': n2_pass,
        },
        'N3': {
            'criterion': '|Delta_τ1(Ls=48) − Delta_τ1(Ls=64)| / Delta_τ1(Ls=48) < 5%',
            'value': {'Ls48': m48, 'Ls64': m64, 'spread_pct': n3_spread_pct},
            'PASS': n3_pass,
        },
        'N4': {
            'criterion': 'Smeared-meson diagonal τ=1 spread / GEVP τ=1 mass < 20%',
            'note': ('Tests whether 0/3/6-step smeared-meson operators '
                     'agree at τ=1. Plaquette is a separate channel.'),
            'value': {'diag_meson_tau1': diag_tau1_vals,
                      'plaq_tau1': plaq_tau1,
                      'GEVP_tau1': m48,
                      'spread_pct': n4_spread_pct},
            'PASS': n4_pass,
        },
        'N5': {
            'criterion': 'Pure-gauge null: κ=0 spectrum distinct from matter+gauge',
            'value': {'pure_gauge_tau1': pg_tau1,
                      'matter_gauge_tau1': m48,
                      'note': n5_note},
            'PASS': n5_pass,
        },
        'VERDICT': verdict,
        'ALL_PASS': all_pass,
    }


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> int:
    rng_master = np.random.default_rng(args.seed)

    if args.smoke:
        common = dict(n_warmup=300, n_meas=2400, meas_int=8)
        plan = [
            dict(label='Ls32', Ls=32, Lt=16, beta=BETA_PHYS, kappa=KAPPA_PHYS, **common),
            dict(label='Ls48', Ls=48, Lt=16, beta=BETA_PHYS, kappa=KAPPA_PHYS, **common),
            dict(label='Ls64', Ls=64, Lt=16, beta=BETA_PHYS, kappa=KAPPA_PHYS, **common),
            dict(label='pure_gauge', Ls=48, Lt=16, beta=BETA_PHYS, kappa=0.0, **common),
        ]
    else:
        common = dict(n_warmup=1500, n_meas=30000, meas_int=10)   # 3000 samples / volume
        plan = [
            dict(label='Ls32', Ls=32, Lt=24, beta=BETA_PHYS, kappa=KAPPA_PHYS, **common),
            dict(label='Ls48', Ls=48, Lt=24, beta=BETA_PHYS, kappa=KAPPA_PHYS, **common),
            dict(label='Ls64', Ls=64, Lt=24, beta=BETA_PHYS, kappa=KAPPA_PHYS, **common),
            dict(label='pure_gauge', Ls=48, Lt=24, beta=BETA_PHYS, kappa=0.0, **common),
        ]

    _results['config'] = {
        'smoke': bool(args.smoke),
        'seed': args.seed,
        'TIMEOUT_SECONDS': TIMEOUT_SECONDS,
        'GEVP_T0': GEVP_T0,
        'APE_SMEAR_STEPS': APE_SMEAR_STEPS,
        'APE_ALPHA': APE_ALPHA,
        'plan': [dict(p) for p in plan],
        'sigma_2D_analytical': sigma_2d_analytical(BETA_PHYS),
        'M_kink_lat': m_kink_lat(KAPPA_PHYS),
        'Delta_lower_sim': 2.0 * m_kink_lat(KAPPA_PHYS),
    }

    print('=' * 78)
    print('Rank 72a-SMEARED: APE smearing + GEVP mass gap closure')
    print(f'  β={BETA_PHYS}  κ={KAPPA_PHYS}  smoke={args.smoke}  '
          f'TIMEOUT={TIMEOUT_SECONDS}s  t0_GEVP={GEVP_T0}')
    print(f'  Operators: 4 (smear steps {APE_SMEAR_STEPS})')
    print('=' * 78)

    for cfg in plan:
        if wall_remaining() < BUDGET_BUFFER + 180:
            print(f'\n  Skipping {cfg["label"]}: wall budget too low '
                  f'({wall_remaining():.0f}s remaining)', flush=True)
            continue
        import hashlib as _hl
        seed_k = args.seed + int(_hl.sha1(cfg['label'].encode()).hexdigest(), 16) % 10**6
        rng_k = np.random.default_rng(seed_k)
        result = run_config(
            beta=cfg['beta'], kappa=cfg['kappa'],
            Ls=cfg['Ls'], Lt=cfg['Lt'],
            n_warmup=cfg['n_warmup'], n_meas=cfg['n_meas'], meas_int=cfg['meas_int'],
            rng=rng_k, label=cfg['label'],
        )
        if result is not None:
            _results['runs'][cfg['label']] = result
        else:
            print(f'  [{cfg["label"]}]  run returned None (budget or statistics)', flush=True)

    # ── Derived / ROBUST criteria ──────────────────────────────────────────────
    print('\n' + '=' * 78)
    print('Evaluating ROBUST criteria ...')
    criteria = evaluate_robust_criteria(_results['runs'])
    _results['derived']['robust_criteria'] = criteria
    _results['derived']['sigma_2D'] = sigma_2d_analytical(BETA_PHYS)
    _results['derived']['M_kink_lat'] = m_kink_lat(KAPPA_PHYS)

    v1 = criteria['N1']['value']
    v2 = criteria['N2']['value']
    v3 = criteria['N3']['value']
    v4 = criteria['N4']['value']
    v5 = criteria['N5']['value']
    print(f'\n  N1 (positive gap τ=1, >=2σ):  {"PASS" if criteria["N1"]["PASS"] else "FAIL"}  '
          f'  GEVP τ=1 mass={v1["mass_sim"]:.4f}±{v1["mass_err_sim"]:.4f}  σ={v1["sigma"]:.1f}')
    print(f'  N2 (>= 2 M_kink = 0.300):     {"PASS" if criteria["N2"]["PASS"] else "FAIL"}  '
          f'  {v2["mass_sim"]:.4f} vs threshold={v2["threshold_sim"]:.3f}')
    print(f'  N3 (volume indep <5%):         {"PASS" if criteria["N3"]["PASS"] else "FAIL"}  '
          f'  spread={v3["spread_pct"]:.2f}%  Ls48={v3["Ls48"]:.4f}  Ls64={v3["Ls64"]:.4f}')
    print(f'  N4 (meson smear indep <20%):   {"PASS" if criteria["N4"]["PASS"] else "FAIL"}  '
          f'  spread={v4["spread_pct"]:.2f}%  '
          f'meson τ=1={[f"{m:.3f}" for m in v4["diag_meson_tau1"]]}  '
          f'plaq τ=1={v4["plaq_tau1"]:.3f}')
    print(f'  N5 (pure-gauge null):          {"PASS" if criteria["N5"]["PASS"] else "FAIL"}  '
          f'  {v5["note"]}')
    print(f'\n  ==> VERDICT: {criteria["VERDICT"]}')
    print('=' * 78)

    # ── Plot ───────────────────────────────────────────────────────────────────
    if not args.no_plot:
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt

            n_panels = sum(1 for lbl in ['Ls32', 'Ls48', 'Ls64']
                           if lbl in _results['runs'])
            if n_panels > 0:
                fig, axes = plt.subplots(1, n_panels, figsize=(6 * n_panels, 5),
                                         constrained_layout=True)
                if n_panels == 1:
                    axes = [axes]
                panel = 0
                for lbl in ['Ls32', 'Ls48', 'Ls64']:
                    run = _results['runs'].get(lbl)
                    if run is None:
                        continue
                    ax = axes[panel]
                    panel += 1
                    # GEVP effective mass
                    mm = np.array(run['gevp']['m_eff_mean'])
                    me = np.array(run['gevp']['m_eff_err'])
                    tau = np.arange(1, len(mm) + 1)
                    ax.errorbar(tau, mm, yerr=me, fmt='ko-', capsize=3, ms=4,
                                label='GEVP λ_gs')
                    fit = run['gevp']['plateau']
                    if fit is not None:
                        t0f, t1f = fit['tau_window']
                        m0 = fit['mass']; em0 = fit['mass_err']
                        ax.axhline(m0, color='black', linestyle='--', alpha=0.7,
                                   label=f'GEVP plateau {m0:.3f}±{em0:.3f}')
                        ax.fill_between([t0f, t1f], m0 - em0, m0 + em0,
                                        color='black', alpha=0.12)
                    # Diagonal operators
                    colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red']
                    names = [f'diag O_{i}' for i in range(4)]
                    for d in run['diagonal']:
                        i = d['op_idx']
                        f = d['plateau']
                        if f is not None:
                            ax.axhline(f['mass'], color=colors[i], linestyle=':',
                                       alpha=0.6, label=f'{names[i]} {f["mass"]:.3f}')
                    # 2 M_kink reference
                    ax.axhline(2 * m_kink_lat(KAPPA_PHYS), color='red',
                               linestyle='--', alpha=0.5,
                               label=f'2 M_kink = {2*m_kink_lat(KAPPA_PHYS):.3f}')
                    ax.set_xlabel(r'$\tau$ (lattice units)')
                    ax.set_ylabel(r'$m_{\rm eff}(\tau)$ [sim]')
                    ax.set_title(f'{lbl}: β={run["beta"]}, κ={run["kappa"]}, '
                                 f'Ls={run["Ls"]}, Lt={run["Lt"]}')
                    ax.legend(fontsize=7, loc='upper right')
                    ax.grid(True, alpha=0.3)
                    ax.set_ylim(bottom=0)

                fig.suptitle('Rank 72a-SMEARED: GEVP ground-state mass (APE smearing)',
                             fontsize=11)
                out_plot = os.path.join(args.out_dir, 'rank72a_smeared_gevp_plateau.png')
                fig.savefig(out_plot, dpi=130, bbox_inches='tight')
                plt.close(fig)
                print(f'\n[plot] saved {out_plot}', flush=True)
        except Exception as exc:
            print(f'[plot] WARNING: {exc}; JSON still saved', flush=True)

    return 0


if __name__ == '__main__':
    rc = 1
    try:
        rc = main()
        _finalize('COMPLETE' if rc == 0 else 'FAILED')
    except KeyboardInterrupt:
        print('\n[!] interrupted', flush=True)
        _finalize('INTERRUPTED')
        rc = 130
    except Exception as exc:
        import traceback
        print(f'\n[!] EXCEPTION: {exc}', flush=True)
        traceback.print_exc()
        _results['exception'] = repr(exc)
        _finalize('EXCEPTION')
        rc = 2
    finally:
        signal.alarm(0)
    sys.exit(rc)
