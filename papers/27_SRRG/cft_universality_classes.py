#!/usr/bin/env python3
"""
SPEC_046_Z9M — ε₃ₛ = MI·ξ/L at critical strip scaling: 2D Ising vs 3-state Potts.

Definitions aligned with EPIC_043 `06_INTERIM_THEORY_STATUS.md` §3.9 (H13a/H16):

- **MI** row–row mutual information (nats) from the cylinder / strip transfer matrix
  stationary pair measure P(i,j) = v_i T_ij v_j / λ₁ with v the Perron–Frobenius
  eigenvector (symmetric T).
- **Ising ξ at T_c:** use locked strip law ξ(L, T_c) = 4L/π from GXT (not TM gap),
  consistent with Δ_σ = 1/8 spectral picture.
- **Potts ξ at T_c:** no locked GXT polynomial; use ξ_TM = 1 / ln(λ₁/λ₂) with λ₂
  the second-largest *positive* eigenvalue (document in JSON).

Run from repo root or this directory. Emits JSON under `results/` and optional PNG.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

# IPT = 1 + ln(φ)/(2 ln(2π)) — match Lean `UgpLean.IPT.IPT_threshold`
PHI = (1.0 + math.sqrt(5.0)) / 2.0
IPT = 1.0 + math.log(PHI) / (2.0 * math.log(2.0 * math.pi))


@dataclass
class StripResult:
    model: str
    L: int
    beta: float
    mutual_information_nats: float
    xi: float
    epsilon3s: float
    lambda_max: float
    notes: str


def _stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, indent=2)


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _ising_config_matrix(L: int) -> np.ndarray:
    """All 2^L spin configurations as rows ∈ {-1,+1}, shape (n, L)."""
    n = 1 << L
    bits = ((np.arange(n, dtype=np.int32)[:, None] >> np.arange(L, dtype=np.int32)) & 1).astype(
        np.float64
    )
    return 1.0 - 2.0 * bits


def _potts_config_matrix(L: int, q: int) -> np.ndarray:
    """All q^L Potts color rows, shape (n, L), values 0..q-1."""
    n = q**L
    idx = np.arange(n, dtype=np.int32)[:, None]
    divs = (q ** np.arange(L, dtype=np.int32))[None, :]
    return (idx // divs) % q


def build_ising_transfer_matrix(L: int, beta: float, J: float = 1.0) -> np.ndarray:
    cfg = _ising_config_matrix(L)
    Eh = -J * np.sum(cfg * np.roll(cfg, -1, axis=1), axis=1)
    vdot = cfg @ cfg.T
    return np.exp(0.5 * beta * (Eh[:, None] + Eh[None, :]) + beta * J * vdot)


def build_potts_transfer_matrix(L: int, q: int, beta: float, J: float = 1.0) -> np.ndarray:
    cfg = _potts_config_matrix(L, q)
    n = cfg.shape[0]
    Eh = -J * np.sum(cfg == np.roll(cfg, -1, axis=1), axis=1).astype(np.float64)
    T = np.empty((n, n), dtype=np.float64)
    # Row-wise: avoid (n,n,L) temporary — EPIC_043 Potts L=8 ⇒ n=6561.
    bhalf = 0.5 * beta
    for a in range(n):
        matches = np.count_nonzero(cfg[a] == cfg, axis=1).astype(np.float64)
        Ev = -J * matches
        T[a, :] = np.exp(bhalf * (Eh[a] + Eh) + beta * Ev)
    return T


def mutual_information_from_transfer(T: np.ndarray) -> Tuple[float, float, np.ndarray]:
    """Return (MI_nats, lambda_max, eigenvector_unit)."""
    # Symmetric PSD check (numerical)
    if np.linalg.norm(T - T.T) > 1e-10 * np.linalg.norm(T):
        raise ValueError("Transfer matrix not symmetric — check construction.")
    w, v = np.linalg.eigh(T)
    lam1 = float(w[-1])
    vec = v[:, -1].astype(np.float64)
    nrm = float(np.linalg.norm(vec))
    if nrm <= 0:
        raise ValueError("Zero eigenvector from eigh.")
    vec /= nrm
    n = T.shape[0]
    P = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            P[i, j] = vec[i] * T[i, j] * vec[j] / lam1
    s = float(np.sum(P))
    if abs(s - 1.0) > 1e-8:
        raise RuntimeError(f"Joint not normalized: sum(P)={s}")

    px = np.sum(P, axis=1)
    py = np.sum(P, axis=0)

    def H(p: np.ndarray) -> float:
        eps = 1e-300
        return -float(np.sum(p * np.log(np.clip(p, eps, 1.0))))

    hxy = -float(np.sum(P * np.log(np.clip(P, 1e-300, 1.0))))
    mi = H(px) + H(py) - hxy
    if mi < -1e-8:
        raise RuntimeError(f"Negative MI {mi} — numerical failure.")
    mi = max(0.0, mi)
    return mi, lam1, vec


def second_eigenvalue_scale(T: np.ndarray) -> float:
    """λ₂ for correlation length: ξ = 1 / ln(λ₁/λ₂), take second-largest eigenvalue."""
    w = np.linalg.eigvalsh(T)
    if len(w) < 2:
        raise ValueError("Matrix too small for gap.")
    lam1 = w[-1]
    lam2 = w[-2]
    if lam2 <= 0 or lam1 <= lam2:
        raise ValueError(f"No positive gap: λ1={lam1}, λ2={lam2}")
    return float(lam1 / lam2)


def run_ising_row(L: int) -> StripResult:
    beta_c = 0.5 * math.log(1.0 + math.sqrt(2.0))  # J=1: Onsager isotropic square lattice
    T = build_ising_transfer_matrix(L, beta_c, J=1.0)
    mi, lam1, _ = mutual_information_from_transfer(T)
    xi = 4.0 * float(L) / math.pi
    eps = mi * xi / float(L)
    return StripResult(
        model="2D_Ising_strip",
        L=L,
        beta=beta_c,
        mutual_information_nats=mi,
        xi=xi,
        epsilon3s=eps,
        lambda_max=lam1,
        notes="xi uses EPIC_043 locked ξ=4L/π at T_c (H13a); not TM gap.",
    )


def run_potts3_row(L: int) -> StripResult:
    q = 3
    # 2D square-lattice critical point: e^{β_c} = 1 + sqrt(q)
    beta_c = math.log(1.0 + math.sqrt(float(q)))
    T = build_potts_transfer_matrix(L, q, beta_c, J=1.0)
    mi, lam1, _ = mutual_information_from_transfer(T)
    ratio = second_eigenvalue_scale(T)
    xi = 1.0 / math.log(ratio)
    eps = mi * xi / float(L)
    return StripResult(
        model="2D_Potts3_strip",
        L=L,
        beta=beta_c,
        mutual_information_nats=mi,
        xi=xi,
        epsilon3s=eps,
        lambda_max=lam1,
        notes="ξ from TM eigenvalue gap ξ=1/ln(λ1/λ2); Potts has no GXT H13a polynomial in this epic.",
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--L", type=int, nargs="+", default=[4, 6, 8], help="Strip widths")
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "results",
        help="JSON + figure output directory",
    )
    ap.add_argument("--plot", action="store_true", help="Write PNG if matplotlib available")
    args = ap.parse_args()

    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    rows: List[Dict[str, Any]] = []
    for L in args.L:
        if L < 2:
            raise SystemExit(f"L must be >= 2, got {L}")
        rows.append(asdict(run_ising_row(L)))
        # Potts matrix is q^L — cap at L=8 by default for RAM
        if L <= 8:
            rows.append(asdict(run_potts3_row(L)))
        else:
            rows.append(
                {
                    "model": "2D_Potts3_strip",
                    "L": L,
                    "skipped": True,
                    "reason": "L>8 Potts3 state space q^L too large for default run",
                }
            )

    payload: Dict[str, Any] = {
        "spec": "SPEC_046_Z9M",
        "epic": "EPIC_046_SRRG",
        "ipt_reference": IPT,
        "phi": PHI,
        "rows": rows,
        "hypothesis_note": (
            "H1 strong universality requires ε₃ₛ crossing IPT at common L_c across classes; "
            "this script reports ε₃ₛ(L) at each class's critical β only — compare columns to IPT."
        ),
    }

    body = _stable_json(payload).encode("utf-8")
    digest = _sha256_bytes(body)
    out_json = out_dir / f"cft_universality_{digest[:16]}.json"
    out_json.write_bytes(body)

    print(_stable_json({**payload, "artifact": str(out_json), "sha256": digest}))

    if args.plot:
        try:
            import matplotlib.pyplot as plt
        except ImportError as e:
            raise RuntimeError(
                "SPEC_046_Z9M --plot requested but matplotlib not installed."
            ) from e

        ising_pts = [(r["L"], r["epsilon3s"]) for r in rows if r.get("model") == "2D_Ising_strip"]
        potts_pts = [(r["L"], r["epsilon3s"]) for r in rows if r.get("model") == "2D_Potts3_strip" and not r.get("skipped")]
        if ising_pts or potts_pts:
            plt.figure(figsize=(7, 4))
            if ising_pts:
                xs, ys = zip(*sorted(ising_pts))
                plt.plot(xs, ys, "o-", label="Ising ε₃ₛ(L)")
            if potts_pts:
                xs, ys = zip(*sorted(potts_pts))
                plt.plot(xs, ys, "s-", label="Potts-3 ε₃ₛ(L)")
            plt.axhline(IPT, color="k", linestyle="--", label=f"IPT={IPT:.4f}")
            plt.xlabel("L")
            plt.ylabel("ε₃ₛ = MI·ξ/L")
            plt.legend()
            plt.title("SPEC_046_Z9M: critical-strip ε₃ₛ vs L (two universality classes)")
            fig_path = out_dir / f"epsilon3s_{digest[:16]}.png"
            plt.savefig(fig_path, dpi=150)
            plt.close()
            print(f"wrote {fig_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
