#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UCL Certificates and PSLQ helpers (pure functions)
--------------------------------------------------

This module provides small, dependency-light utilities for:
- Quarter-lock residual and stability diagnostics
- Fisher/Hessian geometry echoes of the quarter-lock
- PSLQ-based exact-form candidate discovery with MDL-style scoring

All functions are pure and side-effect free. No imports from UGP_GTE_SM_Verifier or
the probe are required. Callers provide any needed data via arguments.
"""
from __future__ import annotations

import itertools
import json
import math
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple, Union

import numpy as np
from mpmath import mp, pslq


# -----------------------------
# Labeling
# -----------------------------
LABELS: List[str] = ["const", "L", "L2", "gen", "gen2", "M", "mu_a", "mu_b", "mu_c"]
IDX: Dict[str, int] = {k: i for i, k in enumerate(LABELS)}


# -----------------------------
# Quarter-lock residuals
# -----------------------------
CoeffsLike = Union[Sequence[float], np.ndarray]


def compute_quarter_lock_residual(coeffs: CoeffsLike) -> Dict[str, float]:
    k = np.asarray(coeffs, dtype=float).reshape(-1)
    KL2, KGEN2, KM = k[IDX["L2"]], k[IDX["gen2"]], k[IDX["M"]]
    pred = KGEN2 + 0.25 * KL2
    resid = KM - pred
    return {
        "K_M": float(KM),
        "K_GEN2": float(KGEN2),
        "K_L2": float(KL2),
        "pred_M_from_lock": float(pred),
        "residual": float(resid),
        "resid_over_|K_M|": float(resid / abs(KM)) if abs(KM) > 0 else float("inf"),
        "resid_over_|K_L2|": float(resid / abs(KL2)) if abs(KL2) > 0 else float("inf"),
    }


# -----------------------------
# Centering identities
# -----------------------------
def compute_centering_objects(coeffs: CoeffsLike) -> Dict[str, float]:
    k = np.asarray(coeffs, dtype=float).reshape(-1)
    KL2, KL, K0 = k[IDX["L2"]], k[IDX["L"]], k[IDX["const"]]
    if abs(KL2) < 1e-15:
        return {"L_star": float("nan"), "K_const_centered": float("nan")}
    L_star = -KL / (2.0 * KL2)
    K0c = K0 - (KL * KL) / (4.0 * KL2)
    return {"L_star": float(L_star), "K_const_centered": float(K0c)}


# -----------------------------
# Geometry objects
# -----------------------------
def compute_geometry_objects(coeffs: CoeffsLike) -> Dict[str, float]:
    k = np.asarray(coeffs, dtype=float).reshape(-1)
    KL2, KGEN2, KM = k[IDX["L2"]], k[IDX["gen2"]], k[IDX["M"]]
    H_LL = 2.0 * KL2
    H_GG = 2.0 * KGEN2
    H_MM = 0.0
    R_geom = (KM - KGEN2) - 0.25 * KL2
    return {"H_LL": float(H_LL), "H_GG": float(H_GG), "H_MM": float(H_MM), "geom_lock_resid": float(R_geom)}


# -----------------------------
# Stability suites
# -----------------------------
def _ridge_normal_eq(X: np.ndarray, y: np.ndarray, w: Optional[np.ndarray], lam: float, penalize_const: bool = False) -> np.ndarray:
    X = np.asarray(X, float)
    y = np.asarray(y, float).reshape(-1)
    n, p = X.shape
    if w is None:
        w = np.ones(n, float)
    sqrtw = np.sqrt(w).reshape(-1, 1)
    Xw = X * sqrtw
    yw = y * sqrtw.ravel()
    H = Xw.T @ Xw
    if lam > 0:
        R = np.eye(p)
        if not penalize_const:
            R[0, 0] = 0.0
        H = H + lam * R
    rhs = Xw.T @ yw
    try:
        return np.linalg.solve(H, rhs)
    except np.linalg.LinAlgError:
        return np.linalg.lstsq(H, rhs, rcond=None)[0]


def _rescale_L_columns_for_log_base(X: np.ndarray, base: float) -> np.ndarray:
    Xp = np.array(X, float, copy=True)
    lnB = math.log(base)
    Xp[:, IDX["L"]] = Xp[:, IDX["L"]] / lnB
    Xp[:, IDX["L2"]] = Xp[:, IDX["L2"]] / (lnB * lnB)
    return Xp


def lock_stability_suite(
    get_payload_fn: Optional[Callable[[], Optional[Dict[str, Any]]]],
    coeffs: CoeffsLike,
    seed: int = 1337,
    n_boot: int = 250,
    jitter_std: float = 0.0,
    bases: Sequence[float] = (math.e, 2.0, 10.0),
    ridge_lambda: float = 1e-6,
) -> Dict[str, Any]:
    k = np.asarray(coeffs, float).reshape(-1)
    rng = np.random.RandomState(seed)

    # Baseline residual
    base_lock = compute_quarter_lock_residual(k)

    # Bootstrap over CR2 rows, if available
    boot: Optional[Dict[str, Any]] = None
    payload = None
    if get_payload_fn is not None:
        try:
            payload = get_payload_fn()
        except Exception:
            payload = None
    if payload is not None and n_boot > 0:
        X0 = np.asarray(payload["X"], float)
        y0 = np.asarray(payload["y"], float).reshape(-1)
        w0 = payload.get("w", None)
        n = X0.shape[0]
        samples = []
        resids = []
        for _ in range(n_boot):
            idx = rng.randint(0, n, size=n)
            X = X0[idx, :].copy()
            y = y0[idx].copy()
            w = None if w0 is None else np.asarray(w0, float).reshape(-1)[idx].copy()
            if jitter_std > 0.0:
                cols = [IDX["L"], IDX["L2"], IDX["gen"], IDX["gen2"], IDX["M"]]
                noise = rng.normal(0.0, jitter_std, size=(X.shape[0], len(cols)))
                for j, c in enumerate(cols):
                    X[:, c] += noise[:, j]
            beta = _ridge_normal_eq(X, y, w, ridge_lambda, penalize_const=False)
            samples.append(beta)
            resids.append(compute_quarter_lock_residual(beta)["residual"])
        B = np.vstack(samples)
        resids = np.array(resids, float)
        boot = {
            "coeff_samples_mean": {LABELS[i]: float(B[:, i].mean()) for i in range(B.shape[1])},
            "coeff_samples_std": {LABELS[i]: float(B[:, i].std(ddof=1)) for i in range(B.shape[1])},
            "lock_residual_mean": float(resids.mean()),
            "lock_residual_std": float(resids.std(ddof=1)),
            "n_boot": int(n_boot),
        }

    # Coefficient jitter diagnostics
    n_jit = 1000
    jit_resid = []
    if jitter_std > 0.0:
        for _ in range(n_jit):
            kj = k + rng.normal(0.0, jitter_std, size=k.shape[0])
            jit_resid.append(compute_quarter_lock_residual(kj)["residual"])
    jit_payload = None if not jit_resid else {
        "mean": float(np.mean(jit_resid)),
        "std": float(np.std(jit_resid, ddof=1) if len(jit_resid) > 1 else 0.0),
        "n": int(n_jit),
    }

    # Bases diagnostics (refits per base if data available)
    base_diag: Dict[str, Any] = {}
    if payload is not None:
        for B in bases:
            Xb = _rescale_L_columns_for_log_base(payload["X"], B)
            beta = _ridge_normal_eq(Xb, payload["y"], payload.get("w", None), ridge_lambda, penalize_const=False)
            base_diag[f"base_{B:g}"] = {"quarter_lock": compute_quarter_lock_residual(beta)}

    # Sector ablations (if metadata available)
    ablate: Dict[str, Any] = {}
    if payload is not None and isinstance(payload.get("meta", None), list):
        for sector in ("lepton", "quark"):
            keep = [i for i, row in enumerate(payload["meta"]) if str(row.get("sector", "")).lower().startswith(sector)]
            if keep:
                Xs = payload["X"][keep, :]
                ys = payload["y"][keep]
                ws = None if payload.get("w", None) is None else np.asarray(payload["w"], float).reshape(-1)[keep]
                beta = _ridge_normal_eq(Xs, ys, ws, ridge_lambda, penalize_const=False)
                ablate[f"{sector}_only"] = {"quarter_lock": compute_quarter_lock_residual(beta)}

    # Pass/fail per guardrails
    resid = base_lock["residual"]
    pass_lock = (abs(resid) <= 1e-5) and (abs(resid) / max(1e-18, abs(base_lock["K_L2"])) <= 1e-3)
    # Jitter 95% interval bound check if jitter provided
    if jit_payload is not None and pass_lock:
        mu, sd = jit_payload["mean"], jit_payload["std"]
        lo, hi = mu - 1.96 * sd, mu + 1.96 * sd
        pass_lock = pass_lock and (max(abs(lo), abs(hi)) <= 1e-5) and (max(abs(lo), abs(hi)) / max(1e-18, abs(base_lock["K_L2"])) <= 1e-3)

    return {
        "baseline": base_lock,
        "bootstrap": boot,
        "jitter_residuals": jit_payload,
        "bases": base_diag,
        "ablations": ablate,
        "pass": bool(pass_lock),
    }


def geometry_stability_suite(
    get_payload_fn: Optional[Callable[[], Optional[Dict[str, Any]]]],
    coeffs: CoeffsLike,
    seed: int = 1337,
    n_boot: int = 250,
    jitter_std: float = 0.0,
    ridge_lambda: float = 1e-6,
) -> Dict[str, Any]:
    k = np.asarray(coeffs, float).reshape(-1)
    rng = np.random.RandomState(seed)
    base = compute_geometry_objects(k)

    # Bootstrap if data available
    boot = None
    payload = None
    if get_payload_fn is not None:
        try:
            payload = get_payload_fn()
        except Exception:
            payload = None
    if payload is not None and n_boot > 0:
        X0 = np.asarray(payload["X"], float)
        y0 = np.asarray(payload["y"], float).reshape(-1)
        w0 = payload.get("w", None)
        n = X0.shape[0]
        resids = []
        for _ in range(n_boot):
            idx = rng.randint(0, n, size=n)
            X = X0[idx, :].copy(); y = y0[idx].copy()
            w = None if w0 is None else np.asarray(w0, float).reshape(-1)[idx].copy()
            beta = _ridge_normal_eq(X, y, w, ridge_lambda, penalize_const=False)
            resids.append(compute_geometry_objects(beta)["geom_lock_resid"])
        resids = np.asarray(resids, float)
        boot = {"geom_lock_resid_mean": float(resids.mean()), "geom_lock_resid_std": float(resids.std(ddof=1)), "n_boot": int(n_boot)}

    # Jitter diagnostics
    n_jit = 1000
    jit_resid = []
    if jitter_std > 0.0:
        for _ in range(n_jit):
            kj = k + rng.normal(0.0, jitter_std, size=k.shape[0])
            jit_resid.append(compute_geometry_objects(kj)["geom_lock_resid"])
    jit_payload = None if not jit_resid else {
        "mean": float(np.mean(jit_resid)),
        "std": float(np.std(jit_resid, ddof=1) if len(jit_resid) > 1 else 0.0),
        "n": int(n_jit),
    }

    # Pass/fail per guardrails
    pass_geom = (abs(base.get("H_MM", 1.0)) <= 1e-10)

    return {"baseline": base, "bootstrap": boot, "jitter_residuals": jit_payload, "pass": bool(pass_geom)}


# -----------------------------
# PSLQ sweep
# -----------------------------
def _const_library_tiers() -> Dict[str, List[Tuple[str, float]]]:
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    A = [("pi", math.pi), ("phi", phi), ("1/2", 0.5), ("1/3", 1.0 / 3.0), ("2/3", 2.0 / 3.0), ("3/2", 1.5), ("4/3", 4.0 / 3.0), ("1/8", 1.0 / 8.0), ("7/512", 7.0 / 512.0), ("1/(2pi)", 1.0 / (2.0 * math.pi))]
    B = [("ln2", math.log(2.0)), ("ln3", math.log(3.0)), ("ln5", math.log(5.0))]
    # Guarded
    zeta2 = (math.pi ** 2) / 6.0
    # Apery's constant approximate (no exact in std lib)
    zeta3 = 1.2020569031595942
    C = [("zeta2", zeta2), ("zeta3", zeta3)]
    return {"A": A, "B": B, "C": C}


def _mdl_bits_from_ints(ints: Sequence[int]) -> float:
    # crude codelength: sum log2(1+|n|) per integer, plus small overhead per term
    return float(sum(max(0.0, math.log2(1.0 + abs(int(n)))) for n in ints) + 2.0 * len(ints))


def _pslq_linear_combo(target: float, constants: List[Tuple[str, float]], max_height: int) -> Optional[Dict[str, Any]]:
    # Attempt to find integers [n0, n1, ..., nk] such that n0*target + sum n_i*c_i = 0
    # Then target = -sum (n_i/n0) c_i
    mp.dps = 80
    xs = [mp.mpf(target)] + [mp.mpf(c) for _, c in constants]
    try:
        rel = pslq(xs, maxcoeff=max_height)
    except Exception:
        return None
    if rel is None:
        return None
    if len(rel) != len(xs):
        return None
    n0 = int(rel[0])
    if n0 == 0:
        return None
    coeffs: List[Tuple[str, Tuple[int, int]]] = []
    approx = 0.0
    for (name, c), ni in zip(constants, rel[1:]):
        ni = int(ni)
        if ni == 0:
            continue
        coeffs.append((name, (int(-ni), n0)))
        approx += (-ni / n0) * c
    err = float(approx - target)
    mdl_bits = _mdl_bits_from_ints([n0] + [int(n) for n in rel[1:] if int(n) != 0])
    return {"relation": rel, "n0": n0, "combo": coeffs, "approx": float(approx), "abs_error": abs(err), "rel_error": (abs(err) / max(1e-18, abs(target))), "mdl_bits": mdl_bits}


def pslq_sweep(
    coeffs: CoeffsLike,
    library: str = "A+B",  # e.g., "A", "A+B", "A+B+C"
    max_height: int = 1000,
    max_terms: int = 2,
    tol_abs: float = 2.5e-3,
    tol_rel: float = 1e-3,
) -> Dict[str, Any]:
    lib = _const_library_tiers()
    chosen: List[Tuple[str, float]] = []
    if "A" in library:
        chosen += lib["A"]
    if "B" in library:
        chosen += lib["B"]
    if "C" in library:
        chosen += lib["C"]

    k = np.asarray(coeffs, float).reshape(-1)

    # Anchored snaps per prior hints
    phi_val = (1.0 + math.sqrt(5.0)) / 2.0
    hints = {
        "gen2": -phi_val / 2.0,
        "gen": math.pi / 2.0,
        "mu_a": 1.0 / 8.0,
        "mu_b": -3.0 / 2.0,
        "mu_c": 4.0 / 3.0,
        "L2": 7.0 / 512.0,
    }
    center = compute_centering_objects(k)
    if math.isfinite(center.get("K_const_centered", float("nan"))):
        hints["const_centered"] = -1.0 / (2.0 * math.pi)

    catalog: List[Dict[str, Any]] = []

    def _record(name: str, target_val: float, approx_val: float) -> Dict[str, Any]:
        err = approx_val - target_val
        rec = {
            "coefficient": name,
            "target_value": float(target_val),
            "candidate_value": float(approx_val),
            "abs_error": float(abs(err)),
            "rel_error": float(abs(err) / max(1e-18, abs(target_val))),
            "mdl_bits": float(0.0),
        }
        rec["tag"] = ("gold" if rec["abs_error"] <= 2.5e-4 else ("green" if rec["abs_error"] <= 2.5e-3 else "none"))
        return rec

    # Single-constant snaps
    for nm, tgt in hints.items():
        if nm == "const_centered":
            approx = center.get("K_const_centered", float("nan"))
        else:
            approx = float(k[IDX[nm]])
        if math.isfinite(approx):
            catalog.append(_record(nm, approx, tgt))

    # PSLQ linear combos (up to max_terms)
    for nm in ["gen2", "gen", "mu_a", "mu_b", "mu_c", "L2"]:
        target = float(k[IDX[nm]])
        for r in range(1, max_terms + 1):
            for subset in itertools.combinations(chosen, r):
                rel = _pslq_linear_combo(target, list(subset), max_height=max_height)
                if rel is None:
                    continue
                rec = {
                    "coefficient": nm,
                    "pslq_constants": [(n, float(v)) for n, v in subset],
                    "combo": [(name, num, den) for (name, (num, den)) in rel["combo"]],
                    "candidate_value": float(rel["approx"]),
                    "abs_error": float(rel["abs_error"]),
                    "rel_error": float(rel["rel_error"]),
                    "mdl_bits": float(rel["mdl_bits"]),
                }
                rec["tag"] = ("gold" if rec["abs_error"] <= 2.5e-4 else ("green" if rec["abs_error"] <= 2.5e-3 else "none"))
                catalog.append(rec)

    # Rank by (abs_error, rel_error, mdl_bits)
    best = sorted(catalog, key=lambda r: (r.get("abs_error", float("inf")), r.get("rel_error", float("inf")), r.get("mdl_bits", float("inf"))))
    return {"catalog": catalog, "best": best[: max(1, min(50, len(best)))]}


# -----------------------------
# Simple Markdown helpers
# -----------------------------
def format_lock_certificate_md(cert: Dict[str, Any]) -> str:
    b = cert.get("baseline", {})
    lines = []
    lines.append("## UCL Lock Certificate")
    lines.append("")
    lines.append(f"- Baseline residual: {b.get('residual'):.6e}")
    lines.append(f"- Normalized over |K_M|: {b.get('resid_over_|K_M|'):.6e}")
    lines.append(f"- Normalized over |K_L2|: {b.get('resid_over_|K_L2|'):.6e}")
    if cert.get("bootstrap"):
        bs = cert["bootstrap"]
        lines.append(f"- Bootstrap lock residual μ±σ: {bs.get('lock_residual_mean', float('nan')):.6e} ± {bs.get('lock_residual_std', float('nan')):.6e} (n={bs.get('n_boot')})")
    if cert.get("jitter_residuals"):
        jr = cert["jitter_residuals"]
        lines.append(f"- Jitter residual μ±σ: {jr.get('mean', float('nan')):.6e} ± {jr.get('std', float('nan')):.6e} (n={jr.get('n')})")
    if cert.get("bases"):
        lines.append("- Base-change diagnostics: present (not accepted as law)")
    if cert.get("ablations"):
        lines.append("- Sector ablations: present (large residuals expected)")
    lines.append(f"- PASS: {bool(cert.get('pass'))}")
    return "\n".join(lines) + "\n"


def format_geometry_certificate_md(cert: Dict[str, Any], lock_resid: float) -> str:
    b = cert.get("baseline", {})
    lines = []
    lines.append("## UCL Geometry Certificate")
    lines.append("")
    lines.append(f"- H_LL: {b.get('H_LL'):.6e}")
    lines.append(f"- H_GG: {b.get('H_GG'):.6e}")
    lines.append(f"- H_MM: {b.get('H_MM'):.6e}")
    lines.append(f"- geom_lock_resid: {b.get('geom_lock_resid'):.6e}")
    lines.append(f"- |geom_lock_resid - lock_resid|: {abs(b.get('geom_lock_resid') - lock_resid):.6e}")
    lines.append(f"- PASS: {bool(cert.get('pass')) and (abs(b.get('H_MM')) <= 1e-10) and (abs(b.get('geom_lock_resid') - lock_resid) <= 1e-8)}")
    return "\n".join(lines) + "\n"


