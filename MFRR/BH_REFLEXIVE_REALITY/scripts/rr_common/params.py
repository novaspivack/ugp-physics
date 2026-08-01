#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shared parameter dataclasses + defaults for the BH test suite.

Reference: MFRR Paper, Appendix: Computational Tests for Black Holes
Date: November 4, 2025
"""

from dataclasses import dataclass

@dataclass
class QNMParams:
    M: float = 1.0                # BH mass (G=c=1)
    l: int = 2                    # angular index
    n: int = 0                    # overtone
    rmin: float = 2.0001          # start (just outside horizon for M=1)
    rmax: float = 80.0            # radial max
    Nr: int = 20000               # radial samples (fine near peak)
    # RR shell:
    rs: float = 2.4               # shell start radius
    dlt: float = 0.1              # shell width Δ
    psi0: float = 0.02            # coherence amplitude
    mpsi: float = 0.0             # optional mass for Psi profile (0=const in shell)
    lamPsi: float = 1.0           # λ_Ψ
    alpha1: float = 1e-6
    alpha2: float = 1e-6
    seed: int = 12345

@dataclass
class TOVPsiParams:
    M: float = 1.0
    rs: float = 2.4
    dlt: float = 0.1
    psi0: float = 0.02
    lamPsi: float = 1.0
    alpha1: float = 1e-6
    alpha2: float = 1e-6
    Nr: int = 5000
    rmax: float = 50.0

@dataclass
class JTParams:
    lamPsi: float = 1.0
    gamma1: float = 1.0
    psi2_bar: float = 1e-4         # ⟨Ψ^2⟩ at QES
    phi_QES: float = 1.0           # dilaton value at QES (units where 4G2=1)
    dlogphi_dlogA: float = 1.0     # ∂φ/∂log A (JT toy, typically ~1)

