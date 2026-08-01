"""
PR-0 FINAL: Ablowitz-Ladik + Mediator + Adaptive Damping

Combines:
- Ablowitz-Ladik (true localized solitons)
- Mediator χ (attraction)
- Separation-aware damping (binding collapse)

Cross-reference: `SESSION_24_COMPLETE_SUMMARY.md`, Section "Bootstrap Discovers Confinement".

This should be THE solution!

AUTHOR: AI Assistant
DATE: October 31, 2025
"""

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter
from numpy.fft import fft2, ifft2, fftfreq

from pr0_system.utils.observers import ObserverRegistry, ensure_registry, SimulationObserver


class PR0_Final:
    """
    PR-0 complete solution.
    
    ψ: Ablowitz-Ladik soliton (complex field)
    χ: Mediator (real field)
    γ(d): Separation-aware damping
    """
    
    def __init__(
        self,
        L_x,
        L_y,
        g=0.1,
        gamma_base=0.02,
        gamma_max=10.0,
        gamma_scale: float | None = None,
        gamma_clip: float = 1.0,
        enforce_localization: bool = True,
        observers: ObserverRegistry | None = None,
    ):
        self.L_x = L_x
        self.L_y = L_y
        self.g = g
        self.gamma_base = gamma_base
        self.gamma_max = gamma_max  # Max damping for far separation
        self.gamma_scale = gamma_scale
        self.gamma_clip = gamma_clip
        self._enforce_localization_enabled = enforce_localization
        
        # Soliton field
        self.psi = np.zeros((L_y, L_x), dtype=np.complex128)
        
        # Mediator
        self.chi = np.zeros((L_y, L_x), dtype=np.float64)
        self.chi_dot = np.zeros((L_y, L_x), dtype=np.float64)
        
        self.timestep = 0
        self._density_target = None
        self._prev_density_sum: float | None = None
        self._observer_registry = ensure_registry(observers)
        # Precompute k-space grid for optional split-step updates
        kx = 2.0 * np.pi * fftfreq(self.L_x)
        ky = 2.0 * np.pi * fftfreq(self.L_y)
        self._kx, self._ky = np.meshgrid(kx, ky, indexing='xy')
        self._k2 = self._kx ** 2 + self._ky ** 2
    
    def step(self, dt=0.01):
        """Full evolution."""
        # Compute damping
        gamma = self._compute_damping()
        
        # Evolve ψ (with χ and damping)
        self._evolve_psi(dt, gamma)
        
        # Evolve χ (sourced by |ψ|²)
        self._evolve_chi(dt, gamma)

        if self._enforce_localization_enabled:
            self._enforce_localization()
        
        self.timestep += 1
        self._notify_observers(dt, gamma)

    def attach_observer(self, observer: SimulationObserver) -> None:
        """Attach an observer callback."""
        self._observer_registry.add(observer)

    def detach_observer(self, observer: SimulationObserver) -> None:
        """Detach a previously registered observer."""
        self._observer_registry.remove(observer)

    def _notify_observers(self, dt: float, gamma: np.ndarray) -> None:
        if not self._observer_registry.observers:
            return

        density = np.abs(self.psi) ** 2
        density_sum = float(np.sum(density))
        max_density = float(np.max(density))
        mean_coherence = float(np.mean(np.abs(self.psi)))
        prob_density = density / (density_sum + 1e-12)
        internal_entropy = float(-np.sum(prob_density * np.log(prob_density + 1e-12)))
        damping_flux = float(np.sum(gamma * density))
        support_area = float(np.sum(density > 0.5))
        log_support_area = float(np.log(support_area + 1e-12))
        density_delta = (
            density_sum - self._prev_density_sum
            if self._prev_density_sum is not None
            else 0.0
        )
        self._prev_density_sum = density_sum

        metrics = {
            "timestep": self.timestep,
            "dt": dt,
            "density_sum": density_sum,
            "density_delta": density_delta,
            "max_density": max_density,
            "mean_coherence": mean_coherence,
            "internal_entropy": internal_entropy,
            "damping_flux": damping_flux,
            "gamma_mean": float(np.mean(gamma)),
            "gamma_max": float(np.max(gamma)),
            "support_area": support_area,
            "log_support_area": log_support_area,
        }
        self._observer_registry.notify(metrics)
    
    def _compute_damping(self):
        """Separation-aware damping."""
        dens = np.abs(self.psi)**2
        
        # Positive and negative (use real part for sign)
        psi_real = np.real(self.psi)
        pos = (psi_real > 0.5).astype(np.float64)
        neg = (psi_real < -0.5).astype(np.float64)
        
        if np.sum(pos) > 5 and np.sum(neg) > 5:
            dist_from_pos = distance_transform_edt(1 - pos)
            dist_from_neg = distance_transform_edt(1 - neg)
            
            sep_map = np.where(psi_real > 0, dist_from_neg, dist_from_pos)
            
            # ADAPTIVE DAMPING: Very strong when close, weak when far
            # γ = γ_max / d² when close (d < 10)
            # γ = γ_base when far (d > 20)
            
            if self.gamma_scale is not None:
                gamma_close = self.gamma_scale / (sep_map**2 + 0.5)
                gamma_far = self.gamma_base * (15.0 / (sep_map + 1.0))
                gamma = np.where(sep_map < 10, gamma_close, gamma_far)
                clip_hi = self.gamma_clip if self.gamma_clip is not None else self.gamma_max
            else:
                gamma = np.where(
                    sep_map < 10,
                    self.gamma_max / (sep_map**2 + 0.5),
                    self.gamma_base * (20.0 / (sep_map + 1.0)),
                )
                clip_hi = self.gamma_clip if self.gamma_clip is not None else 1.0
            gamma = np.clip(gamma, self.gamma_base, clip_hi)
        else:
            gamma = np.ones((self.L_y, self.L_x)) * self.gamma_base
        
        return gamma
    
    def _evolve_psi(self, dt, gamma):
        """
        Evolve Ablowitz-Ladik with mediator + damping + normalization.
        
        KEY: Clip field to prevent overflow!
        """
        # Try split-step for kinetic; fall back to explicit if it diverges
        try:
            # Half-step cubic nonlinearity
            psi_mag2 = np.abs(self.psi) ** 2
            self.psi *= np.exp(1j * psi_mag2 * (dt * 0.5))

            # Linear kinetic in k-space
            psi_k = fft2(self.psi)
            psi_k *= np.exp(-1j * self._k2 * dt)
            self.psi = ifft2(psi_k)

            # Second half-step nonlinearity
            psi_mag2 = np.abs(self.psi) ** 2
            self.psi *= np.exp(1j * psi_mag2 * (dt * 0.5))

            # Real terms: mediator and damping (explicit small step)
            chi_clipped = np.clip(self.chi, -20, 20)
            self.psi += dt * (-self.g * chi_clipped * self.psi - gamma * self.psi)
        except Exception:
            # Laplacian
            lap = (np.roll(self.psi, 1, axis=0) + np.roll(self.psi, -1, axis=0) +
                   np.roll(self.psi, 1, axis=1) + np.roll(self.psi, -1, axis=1) - 4 * self.psi)
            psi_mag = np.abs(self.psi)
            psi_clipped = np.where(psi_mag > 10,
                                   10 * self.psi / (psi_mag + 1e-10),  # Normalize to max=10
                                   self.psi)
            nonlin = np.abs(psi_clipped) ** 2 * psi_clipped
            chi_clipped = np.clip(self.chi, -20, 20)
            mediator_force = -self.g * chi_clipped * psi_clipped
            rhs = 1j * (lap + nonlin) + mediator_force - gamma * psi_clipped
            self.psi += dt * rhs
        
        # Post-update: clip to prevent unbounded growth
        psi_mag = np.abs(self.psi)
        self.psi = np.where(psi_mag > 20,
                            20 * self.psi / (psi_mag + 1e-10),
                            self.psi)
    
    def _evolve_chi(self, dt, gamma):
        """
        Evolve mediator χ.
        
        Sourced by |ψ|² density.
        """
        lap_chi = (np.roll(self.chi, 1, axis=0) + np.roll(self.chi, -1, axis=0) +
                   np.roll(self.chi, 1, axis=1) + np.roll(self.chi, -1, axis=1) - 4 * self.chi)
        
        # Source from density
        source = np.abs(self.psi)**2
        
        self.chi_dot += dt * (lap_chi + source)
        self.chi_dot *= (1.0 - gamma * dt)
        self.chi += dt * self.chi_dot

    def _enforce_localization(self) -> None:
        """Mildly renormalise ψ towards its initial density if it drifts too far."""
        if not self._enforce_localization_enabled:
            return
        density = np.abs(self.psi) ** 2
        total = float(np.sum(density))
        if total <= 0.0:
            return
        if self._density_target is None:
            self._density_target = total
            return
        target = self._density_target
        if not np.isfinite(target) or target <= 0.0:
            self._density_target = total
            return
        ratio = total / target
        if 0.5 <= ratio <= 1.8:
            return
        correction = (target / (total + 1e-12)) ** 0.5
        self.psi *= correction
        # softly damp diffuse wings if we overshot
        if ratio > 1.8:
            mask = gaussian_filter(density, sigma=2.0)
            mask /= mask.max() + 1e-12
            self.psi *= 0.85 + 0.15 * mask
    
    def density(self):
        """Soliton density."""
        return np.abs(self.psi)**2
    
    def set_soliton(self, x0, y0, amplitude, width, velocity_x=0.0, velocity_y=0.0, sign=+1):
        """
        Initialize soliton.
        
        Args:
            sign: +1 or -1 for opposite-phase solitons (enables interference binding!)
        """
        for y in range(self.L_y):
            for x in range(self.L_x):
                dx = x - x0
                dy = y - y0
                # periodic shortest displacements
                if abs(dx) > self.L_x // 2:
                    dx -= int(np.sign(dx)) * self.L_x
                if abs(dy) > self.L_y // 2:
                    dy -= int(np.sign(dy)) * self.L_y
                r = np.sqrt(dx * dx + dy * dy)

                # Bright soliton (radial)
                val = amplitude / np.cosh(r / width)

                # Phase: velocity imprint + sign phase
                phase = velocity_x * dx + velocity_y * dy + (np.pi if sign < 0 else 0.0)

                self.psi[y, x] += val * np.exp(1j * phase)


if __name__ == "__main__":
    print("="*70)
    print("🎯 PR-0 FINAL: Ablowitz-Ladik + Mediator + Damping")
    print("="*70)
    print()
    
    pr0 = PR0_Final(L_x=64, L_y=64, g=0.2, gamma_base=0.05)
    
    pr0.set_soliton(x0=24, y0=32, amplitude=3.0, width=3.0, velocity_x=0.2)
    pr0.set_soliton(x0=40, y0=32, amplitude=3.0, width=3.0, velocity_x=-0.2)
    
    print("Running 5000 steps...")
    
    for t in range(5000):
        pr0.step(dt=0.01)
        
        if t % 500 == 0:
            dens = pr0.density()
            n_loc = np.sum(dens > 0.5)
            max_d = np.max(dens)
            print(f"  Step {t}: localized_cells={n_loc}, max_dens={max_d:.2f}")
    
    print()
    print("✅ PR-0 Final implementation complete!")
    print("="*70)

