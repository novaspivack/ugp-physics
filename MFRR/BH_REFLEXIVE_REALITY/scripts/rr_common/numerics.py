#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Numerical utilities for BH perturbation and ODE solving.

Reference: MFRR Paper, Appendix: Computational Tests for Black Holes
Date: November 4, 2025
"""

import numpy as np

def r_to_rstar(r, M):
    """Schwarzschild tortoise coordinate r* for r>2M."""
    return r + 2*M*np.log(np.maximum(r/(2*M)-1.0, 1e-15))

def V_schwarzschild_axial(r, M, l):
    """Regge–Wheeler axial potential V_l(r)."""
    f = 1.0 - 2.0*M/r
    L = l*(l+1.0)
    return f*(L/r**2 - 6.0*M/r**3)

def find_peak_uniform(r, V):
    """Return index of maximum and arrays; coarse robust."""
    i = np.argmax(V)
    return i

def second_derivative_stencil(x, y, i):
    """
    2nd derivative dy/dx2 at index i via central finite differences in *x* variable.
    Assumes near-uniform spacing in the transformed coordinate (we pass r* arrays).
    """
    # Guard edges:
    if i < 2 or i > len(x)-3:
        # fall back to smaller stencil
        dx1 = x[i+1]-x[i]
        dx0 = x[i]-x[i-1]
        return ( (y[i+1]-y[i])/dx1 - (y[i]-y[i-1])/dx0 ) / (0.5*(dx1+dx0))
    # 5-point central
    dx = x[1]-x[0]
    return ( -y[i+2] + 16*y[i+1] - 30*y[i] + 16*y[i-1] - y[i-2] ) / (12*dx*dx)

def gaussian_window(x, x0, sigma):
    return np.exp(-0.5*((x-x0)/sigma)**2)

def poschl_teller_qnm_from_peak(V0, Vpp, n):
    """
    Pöschl–Teller estimate:
    ω ≈ sqrt(V0 - i (n+1/2) sqrt(-2 Vpp))
    where Vpp is d^2V/dr*^2 at the peak (negative).
    """
    # ensure complex with principal branch:
    w_im_factor = (n+0.5)*np.sqrt(np.maximum(0.0, -2.0*np.real(Vpp)))
    return np.sqrt(V0 - 1j*w_im_factor + 0.0j)

