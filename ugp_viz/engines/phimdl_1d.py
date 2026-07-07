"""
Phi_MDL 1D engine.

Coupled (phi, chi) Klein-Gordon field with Z_N1 x Z_N2 periodic potential:

    V(phi, chi) = (m^2 / N1^2)(1 - cos(N1 * phi))
                + (g^2 / N2^2)(1 - cos(N2 * chi))

Field equations (decoupled within the potential; spatially 1D, periodic BC):

    d^2 phi / dt^2 = c^2 d^2 phi / dx^2 - (m^2 / N1) sin(N1 * phi)
    d^2 chi / dt^2 = c^2 d^2 chi / dx^2 - (g^2 / N2) sin(N2 * chi)

Default symmetry: N_phi = 7 (Z_7, three generations of fermion kinks),
N_chi = 3 (Z_3, color triplet). BPS kink mass M = 8 m / N^2.

Integrator: velocity-Verlet with finite-difference Laplacian (periodic BC).
Optional spectral mode uses an FFT Laplacian for higher-accuracy SR tests.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from ugp_viz.engines.base import (
    FieldSnapshot,
    InitialCondition,
    InjectionSpec,
    SimEngine,
)


# ── Physical unit constants (P42, CatAL / CatAD results) ───────────────────
# These constants relate dimensionless lattice units to physical MeV scales.
# They are provided for reference and physics-output mode; the default engine
# operates in dimensionless units for visualization purposes.
#
# m_phi_MeV = m_τ (tau lepton mass), the P42 CatAL identification of the Z_7
#             kink mass with the third-generation lepton mass.
# M_kink_MeV = BPS kink mass M = 8 m_φ / N_φ² = 8 × 1776.86 / 49 = 290.10 MeV.
#             (Lean: kink_mass_formula_catal; P42 §3.)
# f_pi_MeV   = pion decay constant f_π = M_kink / π ≈ 92.34 MeV.
#             (P42 §4, CatAD identification with QCD chiral scale.)
#
# Unit mapping (dimensionless → MeV):
#   physical_mass_MeV  = dimensionless_m  × (m_phi_MeV / m_canonical)
#   where m_canonical = 1.0 (gen2 entry, by convention).
#   Example: gen1 kink mass = 8 × (0.5) / 49 (dim.less) = 8 × (888.43) / 49 MeV
#     where 888.43 MeV = 0.5 × m_phi_MeV is the gen1 effective mass.
PHIMDL_PHYSICAL_UNITS = {
    "m_phi_MeV": 1776.86,   # m_φ = m_τ: Z_7 kink mass (P42, CatAL)
    "M_kink_MeV": 290.10,   # M_kink = 8 m_φ / 49 (P42, CatAD)
    "f_pi_MeV": 92.34,      # f_π = M_kink / π (P42, CatAD)
}


class PhiMDL1D(SimEngine):

    model_name = "phimdl_1d"
    spatial_dim = 1
    default_params = {
        "N": 512,        # lattice sites
        "dx": 1.0,       # lattice spacing
        "dt": 0.01,      # time step
        "c": 1.0,        # speed of light
        "m": 0.5,        # phi-field mass (Z7 sector)
        "g": 0.5,        # chi-field mass (Z3 sector)
        "N_phi": 7,      # Z7 periodicity
        "N_chi": 3,      # Z3 periodicity
        "spectral": False,
        "tau_c_inner_M": 7,
        "backend": "numpy",  # "numpy" | "taichi"
    }

    def _setup(self) -> None:
        N = int(self.params["N"])
        self.phi = np.zeros(N, dtype=np.float64)
        self.phi_old = np.zeros(N, dtype=np.float64)
        self.chi = np.zeros(N, dtype=np.float64)
        self.chi_old = np.zeros(N, dtype=np.float64)
        self._x = np.arange(N, dtype=np.float64) * float(self.params["dx"])
        self._tau_phase_table: np.ndarray | None = None
        self._ti_state: dict | None = None
        if self.params.get("backend") == "taichi":
            self._init_taichi()

    def _init_taichi(self) -> None:
        from ugp_viz.engines.taichi_runtime import is_available, taichi_or_none

        if not is_available():
            self.params["backend"] = "numpy"
            return
        ti = taichi_or_none()
        # Metal / Vulkan only support f32; keep f32 on the device side
        # for portability. NumPy snapshots are upcast back to f64 below.
        N = int(self.params["N"])
        phi = ti.field(dtype=ti.f32, shape=N)
        phi_old = ti.field(dtype=ti.f32, shape=N)
        chi = ti.field(dtype=ti.f32, shape=N)
        chi_old = ti.field(dtype=ti.f32, shape=N)
        phi_new = ti.field(dtype=ti.f32, shape=N)
        chi_new = ti.field(dtype=ti.f32, shape=N)

        # NOTE: this module uses `from __future__ import annotations`, which
        # turns annotations into strings. Taichi parses annotations at
        # kernel construction time and requires real type objects, so we
        # build the function with no annotations and attach __annotations__
        # explicitly before decorating with @ti.kernel.
        def step_kernel(dt2, dx2, c2, m, g, Nphi, Nchi):
            for i in range(N):
                ip1 = (i + 1) % N
                im1 = (i - 1 + N) % N
                lp_phi = (phi[ip1] + phi[im1] - 2.0 * phi[i]) / dx2
                lp_chi = (chi[ip1] + chi[im1] - 2.0 * chi[i]) / dx2
                a_phi = c2 * lp_phi - (m * m / Nphi) * ti.sin(Nphi * phi[i])
                a_chi = c2 * lp_chi - (g * g / Nchi) * ti.sin(Nchi * chi[i])
                phi_new[i] = 2.0 * phi[i] - phi_old[i] + dt2 * a_phi
                chi_new[i] = 2.0 * chi[i] - chi_old[i] + dt2 * a_chi

        step_kernel.__annotations__ = {
            "dt2": ti.f32, "dx2": ti.f32, "c2": ti.f32,
            "m": ti.f32, "g": ti.f32,
            "Nphi": ti.i32, "Nchi": ti.i32,
        }
        step_kernel = ti.kernel(step_kernel)

        def swap_kernel():
            for i in range(N):
                phi_old[i] = phi[i]
                chi_old[i] = chi[i]
                phi[i] = phi_new[i]
                chi[i] = chi_new[i]

        swap_kernel = ti.kernel(swap_kernel)

        self._ti_state = {
            "phi": phi, "phi_old": phi_old, "phi_new": phi_new,
            "chi": chi, "chi_old": chi_old, "chi_new": chi_new,
            "step_kernel": step_kernel, "swap_kernel": swap_kernel,
        }

    @property
    def x(self) -> np.ndarray:
        return self._x

    def _laplacian(self, f: np.ndarray) -> np.ndarray:
        dx = float(self.params["dx"])
        if self.params["spectral"]:
            N = f.shape[0]
            k = 2.0 * np.pi * np.fft.rfftfreq(N, d=dx)
            return np.fft.irfft(-(k ** 2) * np.fft.rfft(f), N)
        return (np.roll(f, -1) + np.roll(f, 1) - 2.0 * f) / (dx * dx)

    def _accel_phi(self, phi: np.ndarray) -> np.ndarray:
        c = float(self.params["c"])
        m = float(self.params["m"])
        Nphi = int(self.params["N_phi"])
        return c * c * self._laplacian(phi) - (m * m / Nphi) * np.sin(Nphi * phi)

    def _accel_chi(self, chi: np.ndarray) -> np.ndarray:
        c = float(self.params["c"])
        g = float(self.params["g"])
        Nchi = int(self.params["N_chi"])
        return c * c * self._laplacian(chi) - (g * g / Nchi) * np.sin(Nchi * chi)

    def _step_impl(self, n_steps: int) -> None:
        if self._ti_state is not None:
            return self._step_taichi(n_steps)
        dt = float(self.params["dt"])
        dt2 = dt * dt
        for _ in range(n_steps):
            a_phi = self._accel_phi(self.phi)
            a_chi = self._accel_chi(self.chi)
            phi_new = 2.0 * self.phi - self.phi_old + dt2 * a_phi
            chi_new = 2.0 * self.chi - self.chi_old + dt2 * a_chi
            self.phi_old, self.phi = self.phi, phi_new
            self.chi_old, self.chi = self.chi, chi_new
            self._step += 1
            self._time += dt

    def _step_taichi(self, n_steps: int) -> None:
        s = self._ti_state
        dt = float(self.params["dt"])
        dx = float(self.params["dx"])
        c = float(self.params["c"])
        m = float(self.params["m"])
        g = float(self.params["g"])
        Nphi = int(self.params["N_phi"])
        Nchi = int(self.params["N_chi"])
        # Sync NumPy(f64) -> Taichi(f32) at the start of the batch.
        s["phi"].from_numpy(self.phi.astype(np.float32))
        s["phi_old"].from_numpy(self.phi_old.astype(np.float32))
        s["chi"].from_numpy(self.chi.astype(np.float32))
        s["chi_old"].from_numpy(self.chi_old.astype(np.float32))
        for _ in range(n_steps):
            s["step_kernel"](dt * dt, dx * dx, c * c, m, g, Nphi, Nchi)
            s["swap_kernel"]()
            self._step += 1
            self._time += dt
        # Sync Taichi(f32) -> NumPy(f64) at the end of the batch.
        self.phi = s["phi"].to_numpy().astype(np.float64)
        self.phi_old = s["phi_old"].to_numpy().astype(np.float64)
        self.chi = s["chi"].to_numpy().astype(np.float64)
        self.chi_old = s["chi_old"].to_numpy().astype(np.float64)

    def _energy_density(self) -> np.ndarray:
        dx = float(self.params["dx"])
        dt = float(self.params["dt"])
        m = float(self.params["m"])
        g = float(self.params["g"])
        Nphi = int(self.params["N_phi"])
        Nchi = int(self.params["N_chi"])
        dphi_dt = (self.phi - self.phi_old) / dt
        dchi_dt = (self.chi - self.chi_old) / dt
        grad_phi = (np.roll(self.phi, -1) - np.roll(self.phi, 1)) / (2.0 * dx)
        grad_chi = (np.roll(self.chi, -1) - np.roll(self.chi, 1)) / (2.0 * dx)
        V_phi = (m * m / Nphi ** 2) * (1.0 - np.cos(Nphi * self.phi))
        V_chi = (g * g / Nchi ** 2) * (1.0 - np.cos(Nchi * self.chi))
        return (0.5 * dphi_dt ** 2 + 0.5 * grad_phi ** 2 + V_phi
                + 0.5 * dchi_dt ** 2 + 0.5 * grad_chi ** 2 + V_chi)

    def _tau_c_proxy(self) -> np.ndarray:
        # τ_c proxy for continuum field: number of inner Rule 110 steps the
        # majority-vote inner CA would require given the local |phi| as the
        # outer-cell value. This lets us reuse the AFCA visualizations on
        # continuum runs as an ontological-time observable.
        if self._tau_phase_table is None:
            from ugp_viz.engines.fca_sync import build_tau_phase_table
            inner_M = int(self.params["tau_c_inner_M"])
            self._tau_phase_table = build_tau_phase_table(inner_M, inner_M * 5)
        N = self.phi.shape[0]
        inner_M = int(self.params["tau_c_inner_M"])
        phases = np.arange(N, dtype=np.int32) % 14
        Nphi = int(self.params["N_phi"])
        half = (2.0 * np.pi / Nphi) * 0.5
        outer = (self.phi > half).astype(np.int32)
        return self._tau_phase_table[phases, outer]

    def snapshot(self) -> FieldSnapshot:
        ed = self._energy_density()
        return FieldSnapshot(
            step=self._step,
            time=self._time,
            model=self.model_name,
            phi=self.phi.copy(),
            chi=self.chi.copy(),
            energy_density=ed,
            tau_c=self._tau_c_proxy(),
            extra={
                "total_energy": float(ed.sum() * float(self.params["dx"])),
                "N": int(self.params["N"]),
                "dx": float(self.params["dx"]),
                "dt": float(self.params["dt"]),
            },
        )

    def reset(self, ic: InitialCondition | None = None) -> None:
        ic = ic or InitialCondition(kind="vacuum")
        N = int(self.params["N"])
        if ic.kind == "vacuum":
            self.phi[:] = 0.0
            self.chi[:] = 0.0
        elif ic.kind == "random":
            rng = np.random.default_rng(int(ic.params.get("seed", 0)))
            amp = float(ic.params.get("amp", 0.05))
            self.phi[:] = amp * rng.standard_normal(N)
            self.chi[:] = amp * rng.standard_normal(N)
        elif ic.kind == "load":
            if not ic.path:
                raise ValueError("InitialCondition(kind='load') requires path")
            self.load_state(ic.path)
            return
        else:
            raise ValueError(f"unknown ic kind '{ic.kind}'")
        self.phi_old = self.phi.copy()
        self.chi_old = self.chi.copy()
        self._step = 0
        self._time = 0.0

    def inject(self, spec: InjectionSpec) -> None:
        from ugp_viz.catalog.manager import load_entry

        entry = load_entry(self.model_name, spec.kind)
        kind_type = entry["type"]
        N = int(self.params["N"])
        dx = float(self.params["dx"])
        c = float(self.params["c"])
        m = float(entry.get("m", self.params["m"]))
        g = float(entry.get("g", self.params["g"]))
        Nphi = int(entry.get("N_phi", self.params["N_phi"]))
        Nchi = int(entry.get("N_chi", self.params["N_chi"]))
        pos = spec.position
        if pos is None:
            pos = float(entry.get("default_position", N // 2))
        pos = float(pos) * dx
        v = spec.velocity
        if v is None:
            v = float(entry.get("velocity", 0.0))
        gamma = 1.0 / np.sqrt(max(1e-9, 1.0 - v * v / c / c))
        m_eff = m * gamma
        g_eff = g * gamma
        x = self._x

        if kind_type == "kink":
            self.phi[:] = _bps_kink(x, pos, Nphi, m_eff)
            self.chi[:] = _bps_kink(x, pos, Nchi, g_eff)
        elif kind_type == "antikink":
            self.phi[:] = _bps_antikink(x, pos, Nphi, m_eff)
            self.chi[:] = _bps_antikink(x, pos, Nchi, g_eff)
        elif kind_type == "kink_antikink_pair":
            d = float(spec.params.get("separation",
                                       entry.get("separation", 20.0))) * dx
            x_k = pos - d / 2.0
            x_a = pos + d / 2.0
            half_phi = (2.0 * np.pi / Nphi)
            half_chi = (2.0 * np.pi / Nchi)
            self.phi[:] = (_bps_kink(x, x_k, Nphi, m_eff)
                           + _bps_antikink(x, x_a, Nphi, m_eff) - half_phi)
            self.chi[:] = (_bps_kink(x, x_k, Nchi, g_eff)
                           + _bps_antikink(x, x_a, Nchi, g_eff) - half_chi)
        elif kind_type == "wave_packet":
            sigma = float(entry.get("sigma", 25.0)) * dx
            amplitude = float(entry.get("amplitude", 0.1))
            k0 = gamma * m * v
            envelope = amplitude * np.exp(-(x - pos) ** 2 / (2.0 * sigma ** 2))
            self.phi[:] = envelope * np.cos(k0 * (x - pos))
            # chi tracks phi by default
            self.chi[:] = envelope * np.cos(k0 * (x - pos))
        else:
            raise ValueError(f"unknown catalog type '{kind_type}'")

        # Initial velocity: set phi_old so finite-difference dphi/dt = -v dphi/dx
        dphi_dx = (np.roll(self.phi, -1) - np.roll(self.phi, 1)) / (2.0 * dx)
        dchi_dx = (np.roll(self.chi, -1) - np.roll(self.chi, 1)) / (2.0 * dx)
        dt = float(self.params["dt"])
        self.phi_old = self.phi - dt * (-v * dphi_dx)
        self.chi_old = self.chi - dt * (-v * dchi_dx)


def _bps_kink(x: np.ndarray, center: float, N_sym: int, m: float) -> np.ndarray:
    arg = np.clip(m * (x - center), -500.0, 500.0)
    return (4.0 / N_sym) * np.arctan(np.exp(arg))


def _bps_antikink(x: np.ndarray, center: float, N_sym: int, m: float) -> np.ndarray:
    arg = np.clip(m * (x - center), -500.0, 500.0)
    return (4.0 / N_sym) * np.arctan(np.exp(-arg))
