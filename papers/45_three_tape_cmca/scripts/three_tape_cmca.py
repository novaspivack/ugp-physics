"""
ThreeTapeCMCA — Unified Three-Tape Chiral Minkowski Cellular Automaton
=======================================================================
Canonical implementation for GTE/Φ_MDL research (P45/P46).

Architecture per tape j ∈ {x, y, z}:
  outer_plus_j[p]  : Rule 110 (right-chiral), gated by inner clock
  outer_minus_j[p] : Rule 124 (left-chiral), gated by inner clock
  inner_clock_j[p] : Rule 110 (τ_c clock), ALWAYS ticks

Shared clock: tau_c_out (global step counter).
Gating: outer layers update where inner_clock differs from ether after tick.
Winding: w_j[p] = 2 * (outer_plus_j[p] XOR ether[p]) mod 7

Gravity: native_geodesic=True uses clock-layer gradient (CA-native);
         native_geodesic=False uses explicit Poisson + gradient kick.
"""
from __future__ import annotations

import json
import signal
import time
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
    return int((C + R - C * R - L * C * R) % 7)


# ── Ether background ─────────────────────────────────────────────────────────
ETHER_TILE = np.array([1, 0, 0, 1, 1, 0, 1, 1, 1, 1, 1, 0, 0, 0], dtype=np.int8)


def make_ether(L: int) -> np.ndarray:
    return np.tile(ETHER_TILE, L // 14 + 1)[:L].astype(np.int8)


GLIDER_CELLS = (126, 131, 132)


class ThreeTapeCMCA:
    """Unified three-tape CMCA implementation."""

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
        for j in "xyz":
            setattr(self, f"outer_plus_{j}", self.ether.copy())
            setattr(self, f"outer_minus_{j}", self.ether.copy())
            setattr(self, f"inner_clock_{j}", self.ether.copy())
            setattr(self, f"tau_c_{j}", np.zeros(self.L, dtype=np.int32))

    def reset(self) -> None:
        self._init_tapes()
        self.tau_c_out = 0
        self._phi_cached = None

    def state(self, tape_j: str) -> Dict[str, np.ndarray]:
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
        t0 = time.time()
        for _ in range(T):
            if time.time() - t0 > timeout_s:
                raise TimeoutError(f"run({T}) exceeded wall-clock limit {timeout_s}s")
            self.step()

    def winding(self, tape_j: str) -> np.ndarray:
        op = getattr(self, f"outer_plus_{tape_j}")
        return ((op.astype(int) ^ self.ether.astype(int)) * 2) % 7

    def active_cells(self, tape_j: str) -> int:
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
        wx = self.winding("x")
        wy = self.winding("y")
        wz = self.winding("z")
        rho = np.array(
            [_gte_poly_z7(int(wx[i]), int(wy[i]), int(wz[i])) for i in range(self.L)],
            dtype=float,
        ) / 6.0
        return gaussian_filter1d(rho, sigma=self.gravity_sigma)

    def gravity_potential(self) -> np.ndarray:
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
        phi = self.gravity_potential()
        return self.base_rate - self.alpha * phi

    def probe_step_bias(self, probe_pos: float, phi: np.ndarray) -> float:
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

    def gorard_curvature(self, tape_j: str = "x") -> np.ndarray:
        """Ollivier-Ricci κ at edges from steady-state neighborhood distributions."""
        op = getattr(self, f"outer_plus_{tape_j}")
        L = self.L
        kappa = np.zeros(L, dtype=float)
        for p in range(L):
            mu_p = np.array(
                [
                    op[(p - 1) % L],
                    op[p],
                    op[(p + 1) % L],
                ],
                dtype=float,
            )
            mu_q = np.array(
                [
                    op[p % L],
                    op[(p + 1) % L],
                    op[(p + 2) % L],
                ],
                dtype=float,
            )
            w1 = float(np.sum(np.abs(mu_p - mu_q)))
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
    raise TimeoutError("Wall-clock timeout reached")


def install_wall_timeout(seconds: int) -> None:
    signal.signal(signal.SIGALRM, _default_timeout_handler)
    signal.alarm(seconds)


def cancel_wall_timeout() -> None:
    signal.alarm(0)
