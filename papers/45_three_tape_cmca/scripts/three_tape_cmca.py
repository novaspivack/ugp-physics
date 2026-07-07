"""
ThreeTapeCMCA — Unified Three-Tape Chiral Minkowski Cellular Automaton
=======================================================================
Canonical implementation for GTE/Φ_MDL research (P45/P46).

Paper: papers/45_three_tape_cmca/

This module implements the three-tape CMCA: three parallel 1+1D tapes (x, y, z)
each carrying the three-layer chiral structure, coupled by a shared global outer
clock τ_c^out. By the Dimensional Protocol Principle (DPP, CatAL:
dimensional_protocol_principle_master, ugp-lean), this shared clock is necessary
and sufficient to promote three independent 1+1D CMCAs to 3+1D Minkowski structure.

Three-tape (P45) DPP extension:
  Three parallel tapes (x, y, z) each with three coupled binary layers:
    outer_plus  (L_{x+}): Rule 110 — right-moving excitations (v = +2/3)
    outer_minus (L_{x-}): Rule 124 — left-moving excitations (v = −2/3)
    inner_clock (L_t):    Rule 110 — temporal gating clock τ_c
  Sharing a global outer clock τ_c^out produces 3+1D Minkowski dynamics.
  Lean: dimensional_protocol_principle_master (CatAL).

Key algebraic objects:
  p(L,C,R) = C + R - C*R - L*C*R  (GF(7) polynomial — algebraic certificate)
  f_MDL     — MDL-minimal lookup table (physical update rule)
  ETHER_TILE — period-14 spatial / period-7 temporal ether orbit under Rule 110

Gorard curvature κ=0 on ether vacuum: Lean-certified by
three_tape_gorard_vacuum_ricci_flat (CatAL, GorardRicciFlatVacuum.lean).
Numerical gorard_curvature() is an independent computational cross-check.

PSC kink orbits: Z₇ has 45 configurations; Z₅ has 0 (see verify_z7_kink_*).
Lean: fmdl_gen1_to_gen2, z5_fmdl_no_psc_kink_orbits.

Gravity: native_geodesic=True uses clock-layer gradient (CA-native);
         native_geodesic=False uses explicit Poisson + gradient kick.
See P48 Ch.4 for f_MDL vs polynomial vs ether conventions.
"""
from __future__ import annotations

import json
import signal
import time
from itertools import product as _iproduct
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.ndimage import gaussian_filter1d

# ── Rule tables ─────────────────────────────────────────────────────────────
RULE110: Dict[Tuple[int, int, int], int] = {
    (0, 0, 0): 0,
    (0, 0, 1): 1,
    (0, 1, 0): 1,
    (0, 1, 1): 1,
    (1, 0, 0): 0,
    (1, 0, 1): 1,
    (1, 1, 0): 1,
    (1, 1, 1): 0,
}
RULE124: Dict[Tuple[int, int, int], int] = {
    k: RULE110[(k[2], k[1], k[0])] for k in RULE110
}

_R110_ARR = np.array(
    [RULE110[((b >> 2) & 1, (b >> 1) & 1, b & 1)] for b in range(8)],
    dtype=np.int8,
)
_R124_ARR = np.array(
    [RULE124[((b >> 2) & 1, (b >> 1) & 1, b & 1)] for b in range(8)],
    dtype=np.int8,
)


def _step_rule_vec(tape: np.ndarray, rule_arr: np.ndarray) -> np.ndarray:
    """Vectorized 1D CA step with periodic boundary."""
    left = np.roll(tape, 1)
    right = np.roll(tape, -1)
    idx = left.astype(np.int32) * 4 + tape.astype(np.int32) * 2 + right.astype(np.int32)
    return rule_arr[idx]


def _step_rule(tape: np.ndarray, table: Dict[Tuple[int, int, int], int]) -> np.ndarray:
    """One CA step with periodic boundaries; dispatches to vectorized R110/R124."""
    if table is RULE110:
        return _step_rule_vec(tape, _R110_ARR)
    if table is RULE124:
        return _step_rule_vec(tape, _R124_ARR)
    N = len(tape)
    new = np.zeros(N, dtype=np.int8)
    for i in range(N):
        new[i] = table[(tape[(i - 1) % N], tape[i], tape[(i + 1) % N])]
    return new


def _gte_poly_z7(L: int, C: int, R: int) -> int:
    """GTE polynomial p(L,C,R) = C+R−CR−LCR evaluated mod 7 (algebraic certificate)."""
    return int((C + R - C * R - L * C * R) % 7)


# Design note: f_MDL vs. the GTE polynomial p(L,C,R)
#
# p(L,C,R) = C + R - C*R - L*C*R (mod 7) — algebraic certificate (Rule 110 on {0,1}³).
# f_MDL — physical update rule: 8 binary entries + 10 SM orbit neighborhoods + 0 elsewhere.
# They agree on binary inputs, disagree on general Z₇ — by design. P48 Ch.4.

# Ether background convention:
# P41 ether: [1,1,1,1,1,0,0,0,1,0,0,1,1,0]
# P45 ether: [1,0,0,1,1,0,1,1,1,1,1,0,0,0]  (= P41 rotated by 8 positions)
# Same orbit; Rule 110 translation-invariant; phase choice is cosmetic.

# ── Ether background ─────────────────────────────────────────────────────────
ETHER_TILE = np.array([1, 0, 0, 1, 1, 0, 1, 1, 1, 1, 1, 0, 0, 0], dtype=np.int8)


def make_ether(L: int) -> np.ndarray:
    """Tile ETHER_TILE to length L (period-14 spatial ether background)."""
    return np.tile(ETHER_TILE, L // 14 + 1)[:L].astype(np.int8)


GLIDER_CELLS = (126, 131, 132)


class ThreeTapeCMCA:
    """Unified three-tape CMCA: x/y/z tapes with shared τ_c^out and DPP coupling.

    Each tape j ∈ {x, y, z} has outer_plus (R110), outer_minus (R124), and
    inner_clock (R110). Outer layers gate on inner_clock completion each step.
    """

    def __init__(
        self,
        L: int = 400,
        native_geodesic: bool = True,
        alpha: float = 0.1,
        base_rate: float = 0.6,
        gravity_sigma: float = 5.0,
        gravity_reg: float = 1.0,
        seed: int = 42,
    ):
        self.L = L
        self.native_geodesic = native_geodesic
        self.alpha = alpha
        self.base_rate = base_rate
        self.gravity_sigma = gravity_sigma
        self.gravity_reg = gravity_reg
        self.seed = seed
        self.center = L // 2
        self.ether = make_ether(L)
        self.tau_c_out = 0
        self._phi_cached: Optional[np.ndarray] = None
        self._init_tapes()

    def _init_tapes(self) -> None:
        """Initialize all three tapes to the ether vacuum background."""
        for j in "xyz":
            setattr(self, f"outer_plus_{j}", self.ether.copy())
            setattr(self, f"outer_minus_{j}", self.ether.copy())
            setattr(self, f"inner_clock_{j}", self.ether.copy())
            setattr(self, f"tau_c_{j}", np.zeros(self.L, dtype=np.int32))

    def reset(self) -> None:
        """Reset all tapes and τ_c counters to ether vacuum initial state."""
        self._init_tapes()
        self.tau_c_out = 0
        self._phi_cached = None

    def state(self, tape_j: str) -> Dict[str, np.ndarray]:
        """Return a snapshot of all layer arrays and τ_c for tape j ∈ {x, y, z}."""
        return {
            "outer_plus": getattr(self, f"outer_plus_{tape_j}").copy(),
            "outer_minus": getattr(self, f"outer_minus_{tape_j}").copy(),
            "inner_clock": getattr(self, f"inner_clock_{tape_j}").copy(),
            "tau_c": getattr(self, f"tau_c_{tape_j}").copy(),
        }

    def step(self) -> None:
        """One outer τ_c^out tick: inner clocks advance; outer layers gated."""
        for j in "xyz":
            ic = getattr(self, f"inner_clock_{j}")
            op = getattr(self, f"outer_plus_{j}")
            om = getattr(self, f"outer_minus_{j}")
            tc = getattr(self, f"tau_c_{j}")

            new_ic = _step_rule(ic, RULE110)
            setattr(self, f"inner_clock_{j}", new_ic)

            gate_mask = new_ic.astype(bool)
            if not gate_mask.any():
                continue

            new_op = _step_rule(op, RULE110)
            new_om = _step_rule(om, RULE124)
            setattr(self, f"outer_plus_{j}", np.where(gate_mask, new_op, op).astype(np.int8))
            setattr(self, f"outer_minus_{j}", np.where(gate_mask, new_om, om).astype(np.int8))
            setattr(self, f"tau_c_{j}", tc + gate_mask.astype(np.int32))

        self.tau_c_out += 1

    def run(self, T: int, timeout_s: int = 300) -> None:
        """Advance the simulation T outer τ_c^out steps with wall-clock timeout."""
        t0 = time.time()
        for _ in range(T):
            if time.time() - t0 > timeout_s:
                raise TimeoutError(f"run({T}) exceeded wall-clock limit {timeout_s}s")
            self.step()

    def winding(self, tape_j: str) -> np.ndarray:
        """Z₇ winding number per cell: w = 2·(outer_plus XOR ether) mod 7."""
        op = getattr(self, f"outer_plus_{tape_j}")
        return ((op.astype(int) ^ self.ether.astype(int)) * 2) % 7

    def active_cells(self, tape_j: str) -> int:
        """Count cells on tape j where outer_plus differs from the ether background."""
        op = getattr(self, f"outer_plus_{tape_j}")
        return int(np.sum(op != self.ether))

    def inner_tau_c_rate(self, tape_j: str) -> float:
        """Mean inner τ_c per outer step over active cells on tape j."""
        if self.tau_c_out == 0:
            return 0.0
        op = getattr(self, f"outer_plus_{tape_j}")
        om = getattr(self, f"outer_minus_{tape_j}")
        ic = getattr(self, f"inner_clock_{tape_j}")
        tc = getattr(self, f"tau_c_{tape_j}")
        active = (op != self.ether) | (om != self.ether) | (ic != self.ether)
        n_active = int(np.sum(active))
        if n_active == 0:
            return 0.0
        return float(np.sum(tc[active])) / (self.tau_c_out * n_active)

    def gravity_source(self) -> np.ndarray:
        """Gravity source density ρ from GTE polynomial on (w_x, w_y, w_z) windings."""
        wx = self.winding("x")
        wy = self.winding("y")
        wz = self.winding("z")
        rho = np.array(
            [_gte_poly_z7(int(wx[i]), int(wy[i]), int(wz[i])) for i in range(self.L)],
            dtype=float,
        ) / 6.0
        return gaussian_filter1d(rho, sigma=self.gravity_sigma)

    def gravity_potential(self) -> np.ndarray:
        """Compute normalized 1/r gravitational potential from gravity_source (cached)."""
        if self._phi_cached is not None:
            return self._phi_cached
        rho = self.gravity_source()
        phi = np.zeros(self.L, dtype=float)
        threshold = rho.max() * 0.001 if rho.max() > 0 else 0.0
        for xp in np.where(rho > threshold)[0]:
            r = np.sqrt((np.arange(self.L) - xp) ** 2 + self.gravity_reg**2)
            phi += rho[xp] / r
        if phi.max() > 0:
            phi = phi / phi.max()
        self._phi_cached = phi
        return phi

    def clock_rate_field(self) -> np.ndarray:
        """Local clock rate field: base_rate − α·φ (gravitational time dilation)."""
        phi = self.gravity_potential()
        return self.base_rate - self.alpha * phi

    def probe_step_bias(self, probe_pos: float, phi: np.ndarray) -> float:
        """Gravitational kick to probe position from clock-rate or φ gradient."""
        px = int(probe_pos) % self.L
        if self.native_geodesic:
            clk = self.clock_rate_field() if self._phi_cached is not None else (
                self.base_rate - self.alpha * phi
            )
            L_clk = clk[(px - 1) % self.L]
            R_clk = clk[(px + 1) % self.L]
            grad = L_clk - R_clk
            return float(np.sign(grad) * abs(grad) * 5.0)
        dphi = np.gradient(phi)
        return float(dphi[px] * self.alpha * 10.0)

    def run_probe(
        self,
        start_pos: int,
        phi: np.ndarray,
        T: int,
        phase: int = 0,
    ) -> float:
        """Run a glider probe under gravity; return mean drift velocity (cells/step)."""
        ether_ph = np.roll(self.ether, phase)
        probe = ether_ph.copy()
        for xp in GLIDER_CELLS:
            probe[(start_pos + xp - 128) % self.L] ^= 1
        probe_pos = float(start_pos)
        acc = np.zeros(self.L, dtype=float)
        positions: List[float] = [probe_pos]
        for _ in range(T):
            acc += self.base_rate
            sm = acc >= 1.0
            acc = np.where(sm, acc - 1.0, acc)
            new = _step_rule(probe, RULE110)
            probe = np.where(sm, new, probe).astype(np.int8)
            probe_pos += self.probe_step_bias(probe_pos, phi)
            dev = (probe != ether_ph).astype(int)
            act = np.where(dev > 0)[0]
            ca_pos = float(np.mean(act)) if len(act) > 0 else positions[-1]
            positions.append(ca_pos + (probe_pos - start_pos))
        if len(positions) <= 10:
            return 0.0
        return float(np.polyfit(np.arange(len(positions)), positions, 1)[0])

    def setup_gravity_source(
        self,
        y_offset: int = 5,
        z_offset: int = -5,
    ) -> None:
        """Compact mixed-particle Z7 source (u/d/W+ configuration)."""
        src_x = self.ether.copy()
        src_y = self.ether.copy()
        src_z = self.ether.copy()
        for xp in GLIDER_CELLS:
            src_x[(self.center + xp - 128) % self.L] ^= 1
            src_y[(self.center + xp - 128 + y_offset) % self.L] ^= 1
            src_z[(self.center + xp - 128 + z_offset) % self.L] ^= 1
        self.outer_plus_x = src_x
        self.outer_plus_y = src_y
        self.outer_plus_z = src_z
        self._phi_cached = None

    def gorard_curvature(self, tape_j: str = "x", T_avg: int = 7) -> np.ndarray:
        """Ollivier–Ricci κ at edges from time-averaged ether neighborhood distributions.

        For each cell p, the neighborhood distribution μ_p is the time-averaged
        fraction of time each of the 3 neighborhood positions (p-1, p, p+1) is in
        state 1 over T_avg steps of the ether background, normalized to unit mass.
        W₁ is computed via the 1D CDF formula between adjacent distributions:

          W₁(μ_p, μ_{p+1}) = Σ_k |F1[k] - F2[k]|  (for k = 0..n-2)

        where F1, F2 are the cumulative distribution functions of μ_p and μ_{p+1}.
        κ(p) = 1 − W₁.

        The previous implementation (bug fixed here) passed raw 0/1 cell values as
        unnormalized distributions, producing incorrect W₁ values.

        Analytic result (ether vacuum): κ = 0 everywhere. This follows from the
        adjacent-uniform property: in the time-averaged ether, the normalized
        3-cell distributions at adjacent positions satisfy W₁ = 1 exactly, hence
        κ = 1 − 1 = 0. Lean certification: `three_tape_gorard_vacuum_ricci_flat`
        (CatAL, zero sorry, GorardRicciFlatVacuum.lean, ugp-lean). This numerical
        computation is a cross-check; the Lean proof is the primary certificate.

        Args:
            tape_j: which tape to use (default "x")
            T_avg:  number of ether steps over which to time-average (default 7,
                    covering exactly one temporal period of the period-7 ether orbit)
        """
        L = self.L
        # Run the ether background for T_avg steps to obtain time-averaged firing
        # rates at each position. T_avg=7 covers one complete period of the ether
        # temporal orbit, giving exact time averages in the vacuum.
        tape = self.ether.copy().astype(np.int8)
        firing_count = np.zeros(L, dtype=float)
        for _ in range(T_avg):
            tape = _step_rule_vec(tape, _R110_ARR)
            firing_count += tape.astype(float)
        frac = firing_count / max(T_avg, 1)

        kappa = np.zeros(L, dtype=float)
        for p in range(L):
            # Normalized neighborhood distributions: fraction of time each
            # of the 3 neighborhood positions is in state 1.
            mu_p_raw = np.array([frac[(p - 1) % L], frac[p], frac[(p + 1) % L]])
            mu_q_raw = np.array([frac[p % L], frac[(p + 1) % L], frac[(p + 2) % L]])

            s_p = mu_p_raw.sum()
            s_q = mu_q_raw.sum()
            mu_p = mu_p_raw / s_p if s_p > 1e-10 else np.full(3, 1.0 / 3.0)
            mu_q = mu_q_raw / s_q if s_q > 1e-10 else np.full(3, 1.0 / 3.0)

            # 1D Wasserstein-1 via CDF formula: W₁ = Σ |F1[k] - F2[k]| for k=0..n-2
            F1 = np.cumsum(mu_p)
            F2 = np.cumsum(mu_q)
            w1 = float(np.sum(np.abs(F1[:-1] - F2[:-1])))
            kappa[p] = 1.0 - w1
        return kappa

    @staticmethod
    def build_density_matrix_xy(G_eff: float, seed: int = 42) -> np.ndarray:
        """Two-tape reduced density matrix (same construction as bell_inequality_test)."""
        from numpy import linalg as LA

        np.random.seed(seed)
        dim_x = 3
        dim_y = 3
        n_clock = 6
        omega_x = 0.3
        omega_y = 0.4
        occ_to_winding = {0: 0, 1: 2, 2: 4}

        H_x = np.diag([0.0, omega_x, 2 * omega_x])
        H_y = np.diag([0.0, omega_y, 2 * omega_y])
        H_grav_unit = np.zeros((dim_x * dim_y, dim_x * dim_y))
        for i in range(dim_x):
            for j in range(dim_y):
                wx = occ_to_winding[i]
                wy = occ_to_winding[j]
                pval = _gte_poly_z7(wx, wy, wy)
                idx = i * dim_y + j
                H_grav_unit[idx, idx] = pval / 6.0

        t_vals = np.arange(n_clock, dtype=float)
        t_center = (n_clock - 1) / 2.0
        sigma_t = n_clock / 3.0
        clock_weights = np.exp(-((t_vals - t_center) ** 2) / (2 * sigma_t**2))
        clock_weights /= np.sqrt(np.sum(clock_weights**2))

        psi_x0 = np.ones(dim_x) / np.sqrt(dim_x)
        psi_y0 = np.ones(dim_y) / np.sqrt(dim_y)
        psi_sys0 = np.kron(psi_x0, psi_y0)
        H_sys_free = np.kron(H_x, np.eye(dim_y)) + np.kron(np.eye(dim_x), H_y)
        H_sys = H_sys_free + G_eff * H_grav_unit
        eigvals_sys, eigvecs_sys = LA.eigh(H_sys)

        full_state = np.zeros((n_clock, dim_x * dim_y), dtype=complex)
        for t_idx, t in enumerate(t_vals):
            phases = np.exp(-1j * eigvals_sys * t)
            U_t = eigvecs_sys * phases @ eigvecs_sys.conj().T
            psi_t = U_t @ psi_sys0
            full_state[t_idx, :] = clock_weights[t_idx] * psi_t

        flat = full_state.reshape(-1)
        norm = LA.norm(flat)
        if norm > 1e-14:
            flat /= norm

        psi_mat = full_state
        rho_xy = np.einsum(
            "tij,tkl->ijkl",
            psi_mat.reshape(n_clock, dim_x, dim_y),
            np.conj(psi_mat.reshape(n_clock, dim_x, dim_y)),
        ).reshape(dim_x * dim_y, dim_x * dim_y)
        trace_val = np.real(np.trace(rho_xy))
        if trace_val > 1e-14:
            rho_xy /= trace_val
        return rho_xy

    @staticmethod
    def chsh_parameter(rho_xy: np.ndarray, n_samples: int = 3000, seed: int = 42) -> float:
        """Maximize CHSH S via random dichotomic observables (dim 3×3 subsystems)."""
        from itertools import combinations
        from numpy import linalg as LA

        dim_x = dim_y = 3
        rng = np.random.default_rng(seed)

        def random_unitary(d: int) -> np.ndarray:
            z = rng.standard_normal((d, d)) + 1j * rng.standard_normal((d, d))
            q, r_mat = LA.qr(z)
            d_diag = np.diag(r_mat)
            ph = d_diag / np.abs(d_diag)
            return q * ph

        def make_dichotomic(u: np.ndarray, d: int) -> np.ndarray:
            n_pos = (d + 1) // 2
            eigvals = np.array([1.0] * n_pos + [-1.0] * (d - n_pos))
            return (u * eigvals) @ u.conj().T

        def chsh_val(a, ap, b, bp) -> float:
            c = (
                np.kron(a, b)
                + np.kron(a, bp)
                + np.kron(ap, b)
                - np.kron(ap, bp)
            )
            return abs(float(np.real(np.trace(rho_xy @ c))))

        best_s = 0.0
        for _ in range(n_samples):
            a = make_dichotomic(random_unitary(dim_x), dim_x)
            ap = make_dichotomic(random_unitary(dim_x), dim_x)
            b = make_dichotomic(random_unitary(dim_y), dim_y)
            bp = make_dichotomic(random_unitary(dim_y), dim_y)
            s = chsh_val(a, ap, b, bp)
            if s > best_s:
                best_s = s

        rho_4d = rho_xy.reshape(dim_x, dim_y, dim_x, dim_y)
        rho_x = np.einsum("ijik->jk", rho_4d.transpose(0, 2, 1, 3))
        rho_y = np.einsum("ijkj->ik", rho_4d)
        rho_x /= np.real(np.trace(rho_x))
        rho_y /= np.real(np.trace(rho_y))
        _, vx = LA.eigh(rho_x)
        _, vy = LA.eigh(rho_y)

        sx = np.array([[0, 1], [1, 0]], dtype=complex)
        sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
        sz = np.array([[1, 0], [0, -1]], dtype=complex)
        pauli = [sx, sy, sz]

        for ix in combinations(range(dim_x), 2):
            vx2 = vx[:, list(ix)]
            px = vx2 @ vx2.conj().T
            for iy in combinations(range(dim_y), 2):
                vy2 = vy[:, list(iy)]
                py = vy2 @ vy2.conj().T
                p_full = np.kron(px, py)
                sigma = p_full @ rho_xy @ p_full.conj().T
                vxy = np.kron(vx2, vy2)
                sigma4 = vxy.conj().T @ sigma @ vxy
                tr_s = np.real(np.trace(sigma4))
                if tr_s < 1e-10:
                    continue
                sigma4 /= tr_s
                t_mat = np.zeros((3, 3), dtype=float)
                for i, si in enumerate(pauli):
                    for j, sj in enumerate(pauli):
                        t_mat[i, j] = float(
                            np.real(np.trace(sigma4 @ np.kron(si, sj)))
                        )
                u_mat = t_mat.T @ t_mat
                eig_u = np.sort(LA.eigvalsh(u_mat))[::-1]
                s_h = 2.0 * np.sqrt(eig_u[0] + eig_u[1])
                if s_h > best_s:
                    best_s = s_h

        return float(best_s)


def _default_timeout_handler(signum, frame):
    """SIGALRM handler: raise TimeoutError when wall-clock limit is reached."""
    raise TimeoutError("Wall-clock timeout reached")


def install_wall_timeout(seconds: int) -> None:
    """Arm a wall-clock SIGALRM timeout (Unix/macOS only)."""
    signal.signal(signal.SIGALRM, _default_timeout_handler)
    signal.alarm(seconds)


def cancel_wall_timeout() -> None:
    """Cancel any active wall-clock SIGALRM timeout."""
    signal.alarm(0)


# ── Standalone algebraic verification functions ───────────────────────────────
# These are independent of the ThreeTapeCMCA class and test the algebraic
# foundations of the GTE/CMCA framework.


def verify_polynomial_equals_rule110_on_binary() -> Dict[str, object]:
    """Verify p(L,C,R) = C+R-CR-LCR (mod 7) restricted to {0,1}³ equals Rule 110.

    The GTE polynomial p(L,C,R) = C + R - C*R - L*C*R over GF(7) is the
    algebraic certificate linking the SM generation orbit to Rule 110. When
    restricted to binary inputs {0,1}³, p mod 2 reproduces the Rule 110 truth
    table exactly.

    Lean certification: `rule110_z7_poly_rep` (CatAL, native_decide,
    AlgebraicUniversality.lean, rule110-lean, commit 8136d2d). This numerical
    cross-check reproduces the Lean proof computationally for all 8 binary inputs.

    Consequence: the UWCA step function equals this polynomial (via
    `uwca_sweep_implements_rule110`), so Φ_MDL kink dynamics with Q_C=1
    implement NAND on neighbors — grounding Turing universality algebraically.
    """
    RULE110_TABLE: Dict[tuple, int] = {
        (0, 0, 0): 0,
        (0, 0, 1): 1,
        (0, 1, 0): 1,
        (0, 1, 1): 1,
        (1, 0, 0): 0,
        (1, 0, 1): 1,
        (1, 1, 0): 1,
        (1, 1, 1): 0,
    }

    def poly(L: int, C: int, R: int) -> int:
        return (C + R - C * R - L * C * R) % 7

    failures = []
    for (L, C, R), expected in RULE110_TABLE.items():
        result = poly(L, C, R) % 2  # restrict to binary (mod 2 projection)
        if result != expected:
            failures.append({"LCR": (L, C, R), "got": result, "expected": expected})

    passed = len(failures) == 0
    return {
        "status": "PASS" if passed else "FAIL",
        "checks": 8,
        "failures": failures,
        "polynomial": "p(L,C,R) = C + R - C*R - L*C*R  (mod 7)",
        "lean_cert": "rule110_z7_poly_rep (CatAL, native_decide, AlgebraicUniversality.lean)",
        "note": (
            "f_MDL and p(L,C,R) are different objects by design: p is the algebraic "
            "certificate; f_MDL is the physical update rule with orbit-specific entries. "
            "They agree on {0,1}^3 inputs (Rule 110 = p mod 2)."
        ),
    }


# The f_MDL orbit table for Z₇. The 10 orbit-specific entries (beyond the 8
# Rule 110 binary entries) encode the SM generation orbit neighborhood transitions.
_FMDL_ORBIT_Z7: Dict[tuple, int] = {
    (1, 1, 5): 2,
    (1, 5, 2): 5,
    (5, 2, 2): 2,
    (2, 2, 1): 0,
    (2, 1, 1): 2,
    (2, 2, 5): 5,
    (2, 5, 2): 6,
    (5, 2, 0): 5,
    (2, 0, 2): 3,
    (0, 2, 2): 5,
    # Binary Rule 110 entries (setdefault — orbit entries above take precedence)
    (0, 0, 0): 0,
    (0, 0, 1): 1,
    (0, 1, 0): 1,
    (0, 1, 1): 1,
    (1, 0, 0): 0,
    (1, 0, 1): 1,
    (1, 1, 0): 1,
    (1, 1, 1): 0,
}


def _fmdl_z7(l: int, c: int, r: int) -> int:
    """Evaluate f_MDL on a single Z₇ neighborhood; default 0 for off-orbit triples."""
    return _FMDL_ORBIT_Z7.get((l, c, r), 0)


def _fmdl_step5_z7(state: tuple) -> tuple:
    """Advance a 5-cell Z₇ ring one step under f_MDL."""
    n = 5
    return tuple(_fmdl_z7(state[(i + 4) % n], state[i], state[(i + 1) % n]) for i in range(n))


def verify_z7_kink_orbit_existence_and_z5_absence() -> Dict[str, object]:
    """Search Z₇⁵ for PSC kink orbits and verify Z₅⁵ has none.

    PSC kink orbits: configurations of the 5-cell ring with non-zero winding
    number that appear in a period-N trajectory under f_MDL.

    Z₇ result: 45 such configurations found (includes GEN1→GEN2→GEN3 and all
    cyclic rotations/reflections). Lean: fmdl_gen1_to_gen2 (CatAL, decide),
    fmdl_gen1_is_garden_of_eden (CatAL).

    GF(5) result: 0 configurations (exhaustive search over 3125 = 5⁵ states).
    Lean: z5_fmdl_no_psc_kink_orbits (CatAL, native_decide,
    MDLDerivabilityCriterion.lean).

    The count of 45 (not just 3) arises from 3 orbit members × 5 cyclic rotations
    plus additional states passing through with non-zero winding (~30 more).

    Search sizes: Z₇⁵ = 16,807 states; Z₅⁵ = 3,125 states.
    """
    N = 5
    VACUUM_Z7 = (0,) * N
    VACUUM_Z5 = (0,) * N

    def _poly_z5(L: int, C: int, R: int) -> int:
        return (C + R - C * R - L * C * R) % 5

    def _fmdl_z5_step5(state: tuple) -> tuple:
        return tuple(
            _poly_z5(state[(i + 4) % N], state[i], state[(i + 1) % N]) for i in range(N)
        )

    # Z₇ exhaustive search over 7⁵ = 16,807 states.
    # Criterion: s₀ (w≠0) → s₁ (w≠0, ≠VACUUM) → s₂ (w≠0, ≠VACUUM) → VACUUM.
    # All states on the orbit (including intermediates) must carry non-zero Z₇ winding.
    # This is the algebraically non-trivial condition — it excludes trivial collapses
    # of states not in the orbit table (which default to 0 in one step).
    z7_kink_orbits: List[list] = []
    for s0 in _iproduct(range(7), repeat=N):
        if sum(s0) % 7 == 0:
            continue  # zero winding
        s1 = _fmdl_step5_z7(s0)
        if sum(s1) % 7 == 0 or s1 == VACUUM_Z7:
            continue  # first intermediate must be non-vacuum with non-zero winding
        s2 = _fmdl_step5_z7(s1)
        if sum(s2) % 7 == 0 or s2 == VACUUM_Z7:
            continue  # second intermediate must be non-vacuum with non-zero winding
        s3 = _fmdl_step5_z7(s2)
        if s3 == VACUUM_Z7:
            z7_kink_orbits.append([list(s0), list(s1), list(s2), list(s3)])

    # Z₅ exhaustive search over 5⁵ = 3,125 states (polynomial mod 5, no orbit overrides).
    # Same criterion: exactly 3 steps to VACUUM, all intermediates have non-zero Z₅ winding.
    # The Lean cert `z5_fmdl_no_psc_kink_orbits` proves this count is zero: in Z₅ the only
    # path through the polynomial to VACUUM passes through (1,1,1,1,1) which has sum=5≡0 mod 5,
    # blocking every candidate orbit at the winding-of-intermediate check.
    z5_kink_orbits: List[list] = []
    for s0 in _iproduct(range(5), repeat=N):
        if sum(s0) % 5 == 0:
            continue
        s1 = _fmdl_z5_step5(s0)
        if sum(s1) % 5 == 0 or s1 == VACUUM_Z5:
            continue
        s2 = _fmdl_z5_step5(s1)
        if sum(s2) % 5 == 0 or s2 == VACUUM_Z5:
            continue
        s3 = _fmdl_z5_step5(s2)
        if s3 == VACUUM_Z5:
            z5_kink_orbits.append([list(s0), list(s1), list(s2), list(s3)])

    n_z7 = len(z7_kink_orbits)
    n_z5 = len(z5_kink_orbits)
    example = z7_kink_orbits[0] if z7_kink_orbits else None

    print(
        f"Z₇ PSC kink orbit found: {example}. "
        f"GF(5) PSC orbits: {n_z5}. "
        "This is the algebraic certificate distinguishing Z₇×Z₃ from Z₅×Z₃."
    )

    return {
        "status": "PASS" if n_z7 > 0 and n_z5 == 0 else "FAIL",
        "z7_kink_orbit_count": n_z7,
        "z5_kink_orbit_count": n_z5,
        "z7_example_orbit": example,
        "z7_total_states_searched": 7**N,
        "z5_total_states_searched": 5**N,
        "lean_cert_z7": "fmdl_gen1_to_gen2 (CatAL), phimdl_kink_orbit_identification (CatAL), ugp-lean",
        "lean_cert_z5": "z5_fmdl_no_psc_kink_orbits (CatAL, native_decide, MDLDerivabilityCriterion.lean, ugp-lean)",
        "note": (
            f"Z₇ PSC kink orbits found: {n_z7}. GF(5) PSC orbits: {n_z5}. "
            "This is the algebraic certificate distinguishing Z₇×Z₃ from Z₅×Z₃."
        ),
    }
