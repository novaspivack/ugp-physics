"""
Z7-KG engine.

Single-component Klein-Gordon field with Z_N periodic potential

    V(phi) = (m^2 / N^2)(1 - cos(N phi))

For small amplitudes this reduces to the linear KG equation, so Z7-KG
provides the cleanest test bed for Lorentz invariance, dispersion, and
SR clock-rate experiments. Larger amplitudes probe the sine-Gordon
Duffing-type nonlinearity that distinguishes Phi_MDL from a free field.

Integrator: spectral Verlet (FFT Laplacian, exact dispersion to grid
resolution) by default; finite-difference Laplacian available for speed.
"""

from __future__ import annotations

import numpy as np

from ugp_viz.engines.base import (
    FieldSnapshot,
    InitialCondition,
    InjectionSpec,
    SimEngine,
)


class Z7KG(SimEngine):

    model_name = "z7_kg"
    spatial_dim = 1
    default_params = {
        "N": 512,
        "dx": 1.0,
        "dt": 0.01,
        "c": 1.0,
        "m": 0.5,
        "N_sym": 7,
        "spectral": True,
        "tau_c_inner_M": 7,
        "backend": "numpy",  # "numpy" | "taichi" (taichi only for non-spectral)
    }

    def _setup(self) -> None:
        N = int(self.params["N"])
        self.phi = np.zeros(N, dtype=np.float64)
        self.phi_old = np.zeros(N, dtype=np.float64)
        dx = float(self.params["dx"])
        self._x = np.arange(N, dtype=np.float64) * dx
        self._k = 2.0 * np.pi * np.fft.rfftfreq(N, d=dx)
        self._k2 = self._k ** 2
        self._tau_phase_table: np.ndarray | None = None
        self._ti_state: dict | None = None
        if (self.params.get("backend") == "taichi"
                and not self.params.get("spectral", True)):
            self._init_taichi()

    def _init_taichi(self) -> None:
        from ugp_viz.engines.taichi_runtime import is_available, taichi_or_none
        if not is_available():
            self.params["backend"] = "numpy"
            return
        ti = taichi_or_none()
        # Metal / Vulkan only support f32; keep f32 on device.
        N = int(self.params["N"])
        phi = ti.field(dtype=ti.f32, shape=N)
        phi_old = ti.field(dtype=ti.f32, shape=N)
        phi_new = ti.field(dtype=ti.f32, shape=N)

        # See PhiMDL1D._init_taichi for why we attach __annotations__ manually.
        def step_kernel(dt2, dx2, c2, m, N_sym):
            for i in range(N):
                ip1 = (i + 1) % N
                im1 = (i - 1 + N) % N
                lp = (phi[ip1] + phi[im1] - 2.0 * phi[i]) / dx2
                a = c2 * lp - (m * m / N_sym) * ti.sin(N_sym * phi[i])
                phi_new[i] = 2.0 * phi[i] - phi_old[i] + dt2 * a

        step_kernel.__annotations__ = {
            "dt2": ti.f32, "dx2": ti.f32, "c2": ti.f32,
            "m": ti.f32, "N_sym": ti.i32,
        }
        step_kernel = ti.kernel(step_kernel)

        def swap_kernel():
            for i in range(N):
                phi_old[i] = phi[i]
                phi[i] = phi_new[i]

        swap_kernel = ti.kernel(swap_kernel)

        self._ti_state = {
            "phi": phi, "phi_old": phi_old, "phi_new": phi_new,
            "step_kernel": step_kernel, "swap_kernel": swap_kernel,
        }

    def _laplacian(self, f: np.ndarray) -> np.ndarray:
        if self.params["spectral"]:
            N = f.shape[0]
            return np.fft.irfft(-self._k2 * np.fft.rfft(f), N)
        dx = float(self.params["dx"])
        return (np.roll(f, -1) + np.roll(f, 1) - 2.0 * f) / (dx * dx)

    def _accel(self, f: np.ndarray) -> np.ndarray:
        c = float(self.params["c"])
        m = float(self.params["m"])
        N_sym = int(self.params["N_sym"])
        return c * c * self._laplacian(f) - (m * m / N_sym) * np.sin(N_sym * f)

    def _step_impl(self, n_steps: int) -> None:
        if self._ti_state is not None:
            return self._step_taichi(n_steps)
        dt = float(self.params["dt"])
        dt2 = dt * dt
        for _ in range(n_steps):
            a = self._accel(self.phi)
            phi_new = 2.0 * self.phi - self.phi_old + dt2 * a
            self.phi_old, self.phi = self.phi, phi_new
            self._step += 1
            self._time += dt

    def _step_taichi(self, n_steps: int) -> None:
        s = self._ti_state
        dt = float(self.params["dt"])
        dx = float(self.params["dx"])
        c = float(self.params["c"])
        m = float(self.params["m"])
        N_sym = int(self.params["N_sym"])
        s["phi"].from_numpy(self.phi.astype(np.float32))
        s["phi_old"].from_numpy(self.phi_old.astype(np.float32))
        for _ in range(n_steps):
            s["step_kernel"](dt * dt, dx * dx, c * c, m, N_sym)
            s["swap_kernel"]()
            self._step += 1
            self._time += dt
        self.phi = s["phi"].to_numpy().astype(np.float64)
        self.phi_old = s["phi_old"].to_numpy().astype(np.float64)

    def _energy_density(self) -> np.ndarray:
        dx = float(self.params["dx"])
        dt = float(self.params["dt"])
        m = float(self.params["m"])
        N_sym = int(self.params["N_sym"])
        dphi_dt = (self.phi - self.phi_old) / dt
        grad_phi = (np.roll(self.phi, -1) - np.roll(self.phi, 1)) / (2.0 * dx)
        V = (m * m / N_sym ** 2) * (1.0 - np.cos(N_sym * self.phi))
        return 0.5 * dphi_dt ** 2 + 0.5 * grad_phi ** 2 + V

    def _tau_c_proxy(self) -> np.ndarray:
        if self._tau_phase_table is None:
            from ugp_viz.engines.fca_sync import build_tau_phase_table
            inner_M = int(self.params["tau_c_inner_M"])
            self._tau_phase_table = build_tau_phase_table(inner_M, inner_M * 5)
        N = self.phi.shape[0]
        inner_M = int(self.params["tau_c_inner_M"])
        phases = np.arange(N, dtype=np.int32) % 14
        N_sym = int(self.params["N_sym"])
        half = (2.0 * np.pi / N_sym) * 0.5
        outer = (self.phi > half).astype(np.int32)
        return self._tau_phase_table[phases, outer]

    def snapshot(self) -> FieldSnapshot:
        ed = self._energy_density()
        return FieldSnapshot(
            step=self._step,
            time=self._time,
            model=self.model_name,
            phi=self.phi.copy(),
            energy_density=ed,
            tau_c=self._tau_c_proxy(),
            extra={
                "total_energy": float(ed.sum() * float(self.params["dx"])),
            },
        )

    def reset(self, ic: InitialCondition | None = None) -> None:
        ic = ic or InitialCondition(kind="vacuum")
        N = int(self.params["N"])
        if ic.kind == "vacuum":
            self.phi[:] = 0.0
        elif ic.kind == "random":
            rng = np.random.default_rng(int(ic.params.get("seed", 0)))
            self.phi[:] = float(ic.params.get("amp", 0.05)) * rng.standard_normal(N)
        elif ic.kind == "load":
            if not ic.path:
                raise ValueError("ic 'load' requires path")
            self.load_state(ic.path)
            return
        else:
            raise ValueError(f"unknown ic kind '{ic.kind}'")
        self.phi_old = self.phi.copy()
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
        N_sym = int(entry.get("N_sym", self.params["N_sym"]))
        v = float(spec.velocity if spec.velocity is not None else
                  entry.get("velocity", 0.0))
        gamma = 1.0 / np.sqrt(max(1e-9, 1.0 - v * v / c / c))
        m_eff = m * gamma
        pos = spec.position
        if pos is None:
            pos = float(entry.get("default_position", N // 2))
        pos = float(pos) * dx
        x = self._x

        if kind_type == "kink":
            arg = np.clip(m_eff * (x - pos), -500.0, 500.0)
            self.phi[:] = (4.0 / N_sym) * np.arctan(np.exp(arg))
        elif kind_type == "antikink":
            arg = np.clip(m_eff * (x - pos), -500.0, 500.0)
            self.phi[:] = (4.0 / N_sym) * np.arctan(np.exp(-arg))
        elif kind_type == "wave_packet":
            sigma = float(entry.get("sigma", 25.0)) * dx
            amplitude = float(entry.get("amplitude", 0.1))
            k0 = gamma * m * v
            envelope = amplitude * np.exp(-(x - pos) ** 2 / (2.0 * sigma ** 2))
            self.phi[:] = envelope * np.cos(k0 * (x - pos))
        else:
            raise ValueError(f"unknown catalog type '{kind_type}'")

        dx_phi = (np.roll(self.phi, -1) - np.roll(self.phi, 1)) / (2.0 * dx)
        dt = float(self.params["dt"])
        self.phi_old = self.phi - dt * (-v * dx_phi)
