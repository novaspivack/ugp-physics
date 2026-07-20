#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Reference: TE_1.R plan (1_1_TE_1R_PLAN.md)
"""
Parameter scan for FRW + Psi solver to validate robustness (Step E follow-up).

Runs frw_psi_evolve across ±50% variations of (lambda_eff, m, beta, omega_bar)
and records late-time equation-of-state diagnostics.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import numpy as np

from frw_psi_solver import frw_psi_evolve, V_eff


@dataclass
class ScanPoint:
    label: str
    params: Dict[str, float]


def equation_of_state(psi: float, psidot: float, params: Dict[str, float]) -> float:
    kinetic = 0.5 * psidot * psidot
    potential = V_eff(psi, params["m"], params["beta"], params["omega_bar"], params["V0"])
    denom = kinetic + potential
    if denom == 0.0:
        return -1.0
    return (kinetic - potential) / denom


def run_scan(base_params: Dict[str, float], variations: List[ScanPoint], t_max: float, dt: float):
    records = []
    for point in variations:
        params = base_params.copy()
        params.update(point.params)
        result = frw_psi_evolve(
            t_max=t_max,
            dt=dt,
            a0=1.0,
            psi0=params["psi0"],
            psidot0=params["psidot0"],
            rho_m0=params["rho_m0"],
            Lambda_eff=params["Lambda_eff"],
            m=params["m"],
            beta=params["beta"],
            omega_bar=params["omega_bar"],
            V0=params["V0"],
            Gtilde=params["Gtilde"],
        )
        psi_final = result["psi"][-1]
        psidot_final = result["psidot"][-1]
        w_final = equation_of_state(psi_final, psidot_final, params)
        records.append(
            {
                "label": point.label,
                **params,
                "w_final": w_final,
                "rhoPsi_final": result["rhoPsi"][-1],
                "rhoL_final": result["rho_L"][-1],
                "rhoM_final": result["rho_m"][-1],
            }
        )
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="FRW + Psi parameter scan.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/frw_scan"),
        help="Output directory (default: results/frw_scan).",
    )
    parser.add_argument("--t-max", type=float, default=2.0, help="Integration horizon.")
    parser.add_argument("--dt", type=float, default=1e-3, help="Time step size.")
    args = parser.parse_args()

    base_params = {
        "psi0": 0.05,
        "psidot0": 0.0,
        "rho_m0": 0.3,
        "Lambda_eff": 0.7,
        "m": 0.0,
        "beta": 0.0,
        "omega_bar": 0.0,
        "V0": 0.0,
        "Gtilde": 1.0,
    }

    variations = [
        ScanPoint("baseline", {}),
        ScanPoint("Lambda_plus50", {"Lambda_eff": base_params["Lambda_eff"] * 1.5}),
        ScanPoint("Lambda_minus50", {"Lambda_eff": base_params["Lambda_eff"] * 0.5}),
        ScanPoint("beta_plus50", {"beta": 0.5}),
        ScanPoint("beta_minus50", {"beta": -0.5}),
        ScanPoint("m_plus", {"m": 0.1}),
        ScanPoint("m_minus", {"m": -0.1}),
        ScanPoint("omega_plus", {"omega_bar": 0.5}),
        ScanPoint("omega_minus", {"omega_bar": -0.5}),
    ]

    records = run_scan(base_params, variations, t_max=args.t_max, dt=args.dt)
    args.output.mkdir(parents=True, exist_ok=True)
    out_path = args.output / "scan_summary.json"
    out_path.write_text(json.dumps(records, indent=2))

    print(f"[FRW] W_final mean = {np.mean([r['w_final'] for r in records]):.6f}")


if __name__ == "__main__":
    main()

