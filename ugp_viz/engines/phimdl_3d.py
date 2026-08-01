"""
Phi_MDL 3D engine.

Coupled (phi, chi) Klein-Gordon field on a 3D periodic cubic lattice.

    d^2 phi / dt^2 = c^2 nabla^2 phi - (m^2 / N1) sin(N1 phi)
    d^2 chi / dt^2 = c^2 nabla^2 chi - (g^2 / N2) sin(N2 chi)

Domain walls in 3D have tension sigma_wall = 8 m / N^2; spherical kink loops
follow the area law E_loop ~ 4 pi R^2 sigma_wall in the limit R >> 1/m.

Integrator: velocity-Verlet with 7-point finite-difference Laplacian (NumPy).
Default grid is 64^3 to keep single-step memory under ~50 MB. The engine
exposes axis-aligned slice views for the GUI; full volume rendering is the
GUI's responsibility.
"""

from __future__ import annotations

import numpy as np

from ugp_viz.engines.base import (
    FieldSnapshot,
    InitialCondition,
    InjectionSpec,
    SimEngine,
)


class PhiMDL3D(SimEngine):

    model_name = "phimdl_3d"
    spatial_dim = 3
    default_params = {
        "Nx": 64,
        "Ny": 64,
        "Nz": 64,
        "dx": 1.0,
        "dt": 0.01,
        "c": 1.0,
        "m": 0.5,
        "g": 0.5,
        "N_phi": 7,
        "N_chi": 3,
        "backend": "numpy",  # "numpy" | "taichi"
    }

    def _setup(self) -> None:
        shape = self._shape()
        self.phi = np.zeros(shape, dtype=np.float64)
        self.phi_old = np.zeros(shape, dtype=np.float64)
        self.chi = np.zeros(shape, dtype=np.float64)
        self.chi_old = np.zeros(shape, dtype=np.float64)
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
        # for portability. NumPy snapshots are upcast back to f64.
        Nx, Ny, Nz = self._shape()
        phi = ti.field(dtype=ti.f32, shape=(Nx, Ny, Nz))
        phi_old = ti.field(dtype=ti.f32, shape=(Nx, Ny, Nz))
        chi = ti.field(dtype=ti.f32, shape=(Nx, Ny, Nz))
        chi_old = ti.field(dtype=ti.f32, shape=(Nx, Ny, Nz))
        phi_new = ti.field(dtype=ti.f32, shape=(Nx, Ny, Nz))
        chi_new = ti.field(dtype=ti.f32, shape=(Nx, Ny, Nz))

        # See PhiMDL1D._init_taichi for why we attach __annotations__ manually.
        def step_kernel(dt2, dx2, c2, m, g, Nphi, Nchi):
            for i, j, k in ti.ndrange(Nx, Ny, Nz):
                ip = (i + 1) % Nx
                im = (i - 1 + Nx) % Nx
                jp = (j + 1) % Ny
                jm = (j - 1 + Ny) % Ny
                kp = (k + 1) % Nz
                km = (k - 1 + Nz) % Nz
                lp_phi = (
                    phi[ip, j, k] + phi[im, j, k]
                    + phi[i, jp, k] + phi[i, jm, k]
                    + phi[i, j, kp] + phi[i, j, km]
                    - 6.0 * phi[i, j, k]
                ) / dx2
                lp_chi = (
                    chi[ip, j, k] + chi[im, j, k]
                    + chi[i, jp, k] + chi[i, jm, k]
                    + chi[i, j, kp] + chi[i, j, km]
                    - 6.0 * chi[i, j, k]
                ) / dx2
                a_phi = c2 * lp_phi - (m * m / Nphi) * ti.sin(Nphi * phi[i, j, k])
                a_chi = c2 * lp_chi - (g * g / Nchi) * ti.sin(Nchi * chi[i, j, k])
                phi_new[i, j, k] = 2.0 * phi[i, j, k] - phi_old[i, j, k] + dt2 * a_phi
                chi_new[i, j, k] = 2.0 * chi[i, j, k] - chi_old[i, j, k] + dt2 * a_chi

        step_kernel.__annotations__ = {
            "dt2": ti.f32, "dx2": ti.f32, "c2": ti.f32,
            "m": ti.f32, "g": ti.f32,
            "Nphi": ti.i32, "Nchi": ti.i32,
        }
        step_kernel = ti.kernel(step_kernel)

        def swap_kernel():
            for i, j, k in ti.ndrange(Nx, Ny, Nz):
                phi_old[i, j, k] = phi[i, j, k]
                chi_old[i, j, k] = chi[i, j, k]
                phi[i, j, k] = phi_new[i, j, k]
                chi[i, j, k] = chi_new[i, j, k]

        swap_kernel = ti.kernel(swap_kernel)

        self._ti_state = {
            "phi": phi, "phi_old": phi_old, "phi_new": phi_new,
            "chi": chi, "chi_old": chi_old, "chi_new": chi_new,
            "step_kernel": step_kernel, "swap_kernel": swap_kernel,
        }

    def _shape(self) -> tuple[int, int, int]:
        return (int(self.params["Nx"]),
                int(self.params["Ny"]),
                int(self.params["Nz"]))

    def _laplacian(self, f: np.ndarray) -> np.ndarray:
        dx2 = float(self.params["dx"]) ** 2
        return (
            np.roll(f, 1, 0) + np.roll(f, -1, 0)
            + np.roll(f, 1, 1) + np.roll(f, -1, 1)
            + np.roll(f, 1, 2) + np.roll(f, -1, 2)
            - 6.0 * f
        ) / dx2

    def _accel(self, f: np.ndarray, mass: float, N_sym: int) -> np.ndarray:
        c = float(self.params["c"])
        return c * c * self._laplacian(f) - (mass * mass / N_sym) * np.sin(N_sym * f)

    def _step_impl(self, n_steps: int) -> None:
        if self._ti_state is not None:
            return self._step_taichi(n_steps)
        dt = float(self.params["dt"])
        dt2 = dt * dt
        m = float(self.params["m"])
        g = float(self.params["g"])
        Nphi = int(self.params["N_phi"])
        Nchi = int(self.params["N_chi"])
        for _ in range(n_steps):
            a_phi = self._accel(self.phi, m, Nphi)
            a_chi = self._accel(self.chi, g, Nchi)
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
        s["phi"].from_numpy(self.phi.astype(np.float32))
        s["phi_old"].from_numpy(self.phi_old.astype(np.float32))
        s["chi"].from_numpy(self.chi.astype(np.float32))
        s["chi_old"].from_numpy(self.chi_old.astype(np.float32))
        for _ in range(n_steps):
            s["step_kernel"](dt * dt, dx * dx, c * c, m, g, Nphi, Nchi)
            s["swap_kernel"]()
            self._step += 1
            self._time += dt
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
        grad2_phi = sum(
            ((np.roll(self.phi, -1, ax) - np.roll(self.phi, 1, ax)) / (2.0 * dx)) ** 2
            for ax in range(3)
        )
        grad2_chi = sum(
            ((np.roll(self.chi, -1, ax) - np.roll(self.chi, 1, ax)) / (2.0 * dx)) ** 2
            for ax in range(3)
        )
        V_phi = (m * m / Nphi ** 2) * (1.0 - np.cos(Nphi * self.phi))
        V_chi = (g * g / Nchi ** 2) * (1.0 - np.cos(Nchi * self.chi))
        return (0.5 * dphi_dt ** 2 + 0.5 * grad2_phi + V_phi
                + 0.5 * dchi_dt ** 2 + 0.5 * grad2_chi + V_chi)

    def snapshot(self) -> FieldSnapshot:
        ed = self._energy_density()
        dx = float(self.params["dx"])
        total_E = float(ed.sum() * dx ** 3)
        return FieldSnapshot(
            step=self._step,
            time=self._time,
            model=self.model_name,
            extra={
                "total_energy": total_E,
                "shape": list(self._shape()),
                "dx": dx,
                "dt": float(self.params["dt"]),
            },
        )

    def get_volume_phi(self) -> np.ndarray:
        return self.phi

    def get_volume_chi(self) -> np.ndarray:
        return self.chi

    def get_volume_energy(self) -> np.ndarray:
        return self._energy_density()

    def get_slice(self, axis: int, index: int, field: str = "phi") -> np.ndarray:
        """Return a 2D slice along `axis` at integer position `index`."""
        if axis not in (0, 1, 2):
            raise ValueError("axis must be 0, 1, or 2")
        if field == "phi":
            arr = self.phi
        elif field == "chi":
            arr = self.chi
        elif field == "energy":
            arr = self._energy_density()
        elif field == "kink_charge":
            arr = self._kink_charge_density()
        else:
            raise ValueError(f"unknown field '{field}'")
        return np.take(arr, indices=index, axis=axis)

    def _kink_charge_density(self) -> np.ndarray:
        """|grad phi|^2 (proxy for domain-wall presence)."""
        dx = float(self.params["dx"])
        return sum(
            ((np.roll(self.phi, -1, ax) - np.roll(self.phi, 1, ax)) / (2.0 * dx)) ** 2
            for ax in range(3)
        )

    def reset(self, ic: InitialCondition | None = None) -> None:
        ic = ic or InitialCondition(kind="vacuum")
        if ic.kind == "vacuum":
            self.phi[...] = 0.0
            self.chi[...] = 0.0
        elif ic.kind == "random":
            rng = np.random.default_rng(int(ic.params.get("seed", 0)))
            amp = float(ic.params.get("amp", 0.05))
            self.phi[...] = amp * rng.standard_normal(self._shape())
            self.chi[...] = amp * rng.standard_normal(self._shape())
        elif ic.kind == "load":
            if not ic.path:
                raise ValueError("ic 'load' requires path")
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
        Nx, Ny, Nz = self._shape()
        dx = float(self.params["dx"])
        m = float(entry.get("m", self.params["m"]))
        g = float(entry.get("g", self.params["g"]))
        Nphi = int(entry.get("N_phi", self.params["N_phi"]))
        Nchi = int(entry.get("N_chi", self.params["N_chi"]))

        ix = np.arange(Nx, dtype=np.float64)[:, None, None] * dx
        iy = np.arange(Ny, dtype=np.float64)[None, :, None] * dx
        iz = np.arange(Nz, dtype=np.float64)[None, None, :] * dx

        def _or(*vals, default=None):
            for v in vals:
                if v is not None:
                    return v
            return default

        if kind_type == "spherical_kink":
            R = float(_or(spec.params.get("R"), entry.get("R"),
                          default=10.0))
            cx = float(_or(spec.params.get("cx"), entry.get("cx"),
                           default=Nx * dx / 2.0))
            cy = float(_or(spec.params.get("cy"), entry.get("cy"),
                           default=Ny * dx / 2.0))
            cz = float(_or(spec.params.get("cz"), entry.get("cz"),
                           default=Nz * dx / 2.0))
            r = np.sqrt((ix - cx) ** 2 + (iy - cy) ** 2 + (iz - cz) ** 2)
            w = max(2.0, 1.5 / m)
            half_phi = 2.0 * np.pi / Nphi
            half_chi = 2.0 * np.pi / Nchi
            self.phi[...] = half_phi * 0.5 * (1.0 - np.tanh((r - R) / w))
            self.chi[...] = half_chi * 0.5 * (1.0 - np.tanh((r - R) / w))
        elif kind_type == "domain_wall_slab":
            # Position may be None (use catalog default or Nx/4), a scalar
            # (x lattice index), or a 3-tuple from the GUI's "center" preset.
            # In the tuple case we take the x component since the slab is
            # x-aligned. Without this guard, `float((32, 32, 32))` raises
            # a TypeError that the Tk event loop silently swallows, leaving
            # phi at vacuum — which is exactly the "two empty blue boxes"
            # symptom that motivated this fix.
            pos = spec.position
            if pos is None:
                x0_idx = float(entry.get("default_position", Nx / 4))
            elif isinstance(pos, (tuple, list, np.ndarray)):
                x0_idx = float(pos[0])
            else:
                x0_idx = float(pos)
            x0 = x0_idx * dx
            arg = np.clip(m * (ix - x0), -500.0, 500.0)
            self.phi[...] = (4.0 / Nphi) * np.arctan(np.exp(arg))
            self.chi[...] = (4.0 / Nchi) * np.arctan(np.exp(g * (ix - x0) / m))
        elif kind_type == "kink_antikink_slab_pair":
            d = float(spec.params.get("separation", entry.get("separation", 16.0)))
            x1 = Nx * dx / 4.0
            x2 = x1 + d * dx
            half_phi = 2.0 * np.pi / Nphi
            half_chi = 2.0 * np.pi / Nchi
            kink_phi = (4.0 / Nphi) * np.arctan(
                np.exp(np.clip(m * (ix - x1), -500.0, 500.0)))
            anti_phi = (4.0 / Nphi) * np.arctan(
                np.exp(np.clip(-m * (ix - x2), -500.0, 500.0)))
            kink_chi = (4.0 / Nchi) * np.arctan(
                np.exp(np.clip(g * (ix - x1), -500.0, 500.0)))
            anti_chi = (4.0 / Nchi) * np.arctan(
                np.exp(np.clip(-g * (ix - x2), -500.0, 500.0)))
            self.phi[...] = (kink_phi + anti_phi - half_phi)
            self.chi[...] = (kink_chi + anti_chi - half_chi)
        elif kind_type == "cylindrical_flux_tube":
            cy = Ny * dx / 2.0
            cz = Nz * dx / 2.0
            R = float(spec.params.get("R", entry.get("R", 6.0)))
            rho = np.sqrt((iy - cy) ** 2 + (iz - cz) ** 2)
            w = max(2.0, 1.5 / m)
            half_phi = 2.0 * np.pi / Nphi
            half_chi = 2.0 * np.pi / Nchi
            self.phi[...] = half_phi * 0.5 * (1.0 - np.tanh((rho - R) / w))
            self.chi[...] = half_chi * 0.5 * (1.0 - np.tanh((rho - R) / w))
        else:
            raise ValueError(f"unknown catalog type '{kind_type}'")
        self.phi_old = self.phi.copy()
        self.chi_old = self.chi.copy()
