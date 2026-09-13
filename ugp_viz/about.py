"""
Centralised app-info constants.

All UI surfaces (Tk About modal, CLI ``--version``, README header) read
from this single dict so the displayed identity, attribution, links, and
license string can never disagree across surfaces.
"""

from __future__ import annotations

APP_INFO: dict[str, str] = {
    "name": "UGP VIZLAB",
    "subtitle": "Unified visualization lab for GTE-Möbius substrate simulations",
    "version": "1.0.0",
    "byline": "By Nova Spivack, 2026",
    "programme": "Part of the UGP Physics Programme",
    "website": "https://www.novaspivack.com",
    "repository": "https://github.com/novaspivack/ugp-physics",
    "license": (
        "Same as ugp-physics — see LICENSE file at the repository root"
    ),
    "description": (
        "VIZLAB is an interactive desktop application for running, "
        "visualizing, and recording UGP / GTE simulations. It exposes "
        "every engine in the package (Phi_MDL 1D/3D, Z7-KG, FCA sync, "
        "AFCA, Z7 f_MDL) behind a single SimEngine interface with a CLI, "
        "YAML batch runner, MP4 video exporter, and notebook-grade "
        "matplotlib figure library. The Rule 110 catalog ships with the "
        "complete Cook (2004) named-glider table and the Martinez (2004) "
        "phase catalog (374 entries total)."
    ),
}


__all__ = ["APP_INFO"]
