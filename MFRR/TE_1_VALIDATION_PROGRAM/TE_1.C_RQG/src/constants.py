"""
Physical constants shared across TE_1.C simulations.

Reference: TE_1.C.1_PLAN.md (Phase 1 numerical refresh tasks).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PhysicalConstants:
    gravitational_constant: float = 6.67430e-11  # m^3 kg^-1 s^-2
    speed_of_light: float = 299_792_458.0  # m s^-1
    H0_km_s_Mpc: float = 70.0  # baseline H0 for comparison [km s^-1 Mpc^-1]

    @property
    def hubble_constant(self) -> float:
        """Return H0 in SI units (s^-1)."""
        Mpc = 3.085677581e22
        return (self.H0_km_s_Mpc * 1_000.0) / Mpc

    @property
    def rho_crit0(self) -> float:
        """Critical density at z=0 in SI units (J m^-3)."""
        H0 = self.hubble_constant
        G = self.gravitational_constant
        return 3.0 * H0**2 / (8.0 * 3.141592653589793 * G)


CONSTS = PhysicalConstants()

