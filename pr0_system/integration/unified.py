"""
Unified PR-0 integrator that composes AL + mediator + adaptive damping with
optional EM/Weak/Gravity overlays.

Cross-reference: SESSIONS/SESSION_26_COMPLETE_STANDARD_MODEL
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import Iterable


@dataclass
class OverlayConfig:
    enable_em: bool = True
    enable_weak: bool = False
    enable_gravity: bool = False
    enable_strong: bool = False
    em_scale: float = 0.15
    weak_scale: float = 0.03
    gravity_scale: float = 0.10
    strong_scale: float = 0.50
    weak_gate_distance: float = 5.0
    density_threshold: float = 0.5
    gravity_curv_quantile: float = 0.90


class UnifiedPR0:
    def __init__(
        self,
        L_x: int,
        L_y: int,
        overlay: OverlayConfig | None = None,
        core_mode: str = "strong",
        observers: Iterable | None = None,
    ):
        # Base evolution
        if core_mode == "strong":
            from pr0_system.forces import strong
            self.core = strong.BootstrapPR0(L_x=L_x, L_y=L_y)
        else:
            from pr0_system.evolution.ablowitz_ladik import PR0_Final
            self.core = PR0_Final(L_x=L_x, L_y=L_y, observers=observers)

        # Force layers for potential fields / curvature
        from pr0_system.forces import em, weak, gravity, strong
        self.em_layer = em.BootstrapEM_Final(L_x=L_x, L_y=L_y)
        self.weak_layer = weak.BootstrapWeak_Final(L_x=L_x, L_y=L_y)
        self.gravity_layer = gravity.BootstrapGravity(L_x=L_x, L_y=L_y)
        self.strong_layer = strong.BootstrapPR0(L_x=L_x, L_y=L_y)

        self.L_x, self.L_y = L_x, L_y
        self.overlay = overlay or OverlayConfig()
        self.timestep = 0

        if core_mode == "strong" and observers:
            attach = getattr(self.core, "attach_observer", None)
            if callable(attach):
                for obs in observers:
                    attach(obs)

    @property
    def psi(self):
        return self.core.psi

    @psi.setter
    def psi(self, v):
        self.core.psi = v

    def density(self):
        return np.abs(self.core.psi) ** 2

    def set_soliton(self, *args, **kwargs):
        if 'charge' in kwargs and 'sign' not in kwargs:
            kwargs['sign'] = kwargs.pop('charge')
        return self.core.set_soliton(*args, **kwargs)

    def _apply_em_overlay(self, dt: float):
        if not self.overlay.enable_em:
            return
        self.em_layer.psi = self.core.psi.copy()
        V = self.em_layer._compute_potential_field()
        self.core.psi *= np.exp(-1j * (self.overlay.em_scale * V * dt))
        # Preserve norm
        norm = float(np.sqrt(np.sum(np.abs(self.core.psi)**2)))
        if norm > 1e-12:
            self.core.psi /= norm

    def _apply_weak_overlay(self, dt: float):
        if not self.overlay.enable_weak:
            return
        from scipy.ndimage import distance_transform_edt
        self.weak_layer.psi = self.core.psi.copy()
        V = self.weak_layer._compute_potential_field()
        dens = self.density()
        mask = (dens > self.overlay.density_threshold).astype(float)
        sep_map = distance_transform_edt(1.0 - mask)
        near = (sep_map <= self.overlay.weak_gate_distance)
        V_eff = self.overlay.weak_scale * V * near
        self.core.psi *= np.exp(-1j * (V_eff * dt))
        norm = float(np.sqrt(np.sum(np.abs(self.core.psi)**2)))
        if norm > 1e-12:
            self.core.psi /= norm

    def _apply_gravity_overlay(self, dt: float):
        if not self.overlay.enable_gravity:
            return
        self.gravity_layer.psi = self.core.psi.copy()
        self.gravity_layer.chi[:] = 0.0
        self.gravity_layer._update_curvature()
        curvature_safe = np.clip(self.gravity_layer.curvature, 0, 5.0)
        gamma_base, gamma_scale = 0.013, 0.644
        gamma_loc = gamma_base + gamma_scale * curvature_safe / (curvature_safe + 1.0)
        gamma_loc = np.clip(gamma_loc, gamma_base, 1.0)
        thr = np.quantile(curvature_safe, self.overlay.gravity_curv_quantile)
        mask = (curvature_safe >= thr)
        gamma_eff = self.overlay.gravity_scale * gamma_loc * mask
        self.core.psi += (-gamma_eff * self.core.psi) * dt

    def _apply_strong_overlay(self, dt: float):
        if not self.overlay.enable_strong:
            return
        self.strong_layer.psi = self.core.psi.copy()
        # Strong layer computes chi via AL coupling during its step; we extract mediator field
        # Simple proxy: use |psi|^2 overlap as confinement potential (V ~ sum density^2)
        dens = np.abs(self.core.psi)**2
        V_strong = dens * dens.sum()
        self.core.psi *= np.exp(-1j * (self.overlay.strong_scale * V_strong * dt))
        norm = float(np.sqrt(np.sum(np.abs(self.core.psi)**2)))
        if norm > 1e-12:
            self.core.psi /= norm

    def step(self, dt: float = 0.01):
        self.core.step(dt=dt)
        self._apply_strong_overlay(dt)
        self._apply_em_overlay(dt)
        self._apply_weak_overlay(dt)
        self._apply_gravity_overlay(dt)
        self.timestep += 1

    def attach_observer(self, observer) -> None:
        attach = getattr(self.core, "attach_observer", None)
        if callable(attach):
            attach(observer)



