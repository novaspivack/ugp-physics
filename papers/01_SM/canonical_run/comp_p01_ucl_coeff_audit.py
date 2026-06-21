#!/usr/bin/env python3
"""
Regenerate P01 UCL coefficient audit artifacts after k_gen = phi*cos(pi/10) fix.

Writes into canonical_run/ (frozen bundle) and a timestamped Verifier_reports/ subdir.
Wall-clock cap: 10 minutes.
"""
from __future__ import annotations

import json
import os
import signal
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

TIMEOUT_SECONDS = 600

SCRIPT_DIR = Path(__file__).resolve().parent
VERIFIER_PATH = SCRIPT_DIR / "UGP_GTE_SM_Verifier.py"
CANONICAL_ARTIFACTS = [
    "dual_path_comparison.json",
    "dual_path_comparison.md",
    "theoretical_coefficients.json",
    "fully_theoretical_results.json",
    "fully_theoretical_grand_synthesis.md",
    "reference_lock.json",
    "reference_verify_result.json",
]


def _timeout_handler(_signum, _frame):
    print(f"TIMEOUT: {TIMEOUT_SECONDS}s wall-clock limit reached.", file=sys.stderr)
    sys.exit(1)


if hasattr(signal, "SIGALRM"):
    signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(TIMEOUT_SECONDS)


def load_verifier():
    import importlib.util

    spec = importlib.util.spec_from_file_location("ugp_verifier_audit", VERIFIER_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["ugp_verifier_audit"] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    t0 = time.time()
    v = load_verifier()

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = SCRIPT_DIR / "Verifier_reports" / f"ucl_coeff_audit_{ts}"
    run_dir.mkdir(parents=True, exist_ok=True)
    v.RUN_DIR = str(run_dir)
    os.chdir(SCRIPT_DIR)

    v.apply_coeffs_source("empirical")
    v.apply_imt_mixer_mode("v12")

    print("[audit] dual-path comparison (empirical UCL + renorm_K paths)...")
    dual = v.run_dual_path_comparison(write_artifacts=True)

    print("[audit] fully theoretical grand synthesis (THEORETICAL_COEFF_VECTOR)...")
    ft = v.run_fully_theoretical_grand_synthesis(write_artifacts=True)

    v.write_theoretical_coeffs_artifact(
        v.THEORETICAL_COEFF_VECTOR,
        v.THEORETICAL_COMPONENTS,
        out_json="theoretical_coefficients.json",
    )

    v.set_engine_config(phase_mode="legacy", phase_k=2.0, renorm_k=1400.0)
    v.write_reference_lock("reference_lock.json")
    verify = v.verify_reference_lock("reference_lock.json")
    if not verify.get("ok"):
        print("[audit] WARNING: reference_lock verify failed:", verify, file=sys.stderr)

    summary = {
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "k_gen_theoretical": float(v.THEORETICAL_COEFF_VECTOR[3]),
        "k_gen_empirical": float(v.EMPIRICAL_COEFF_VECTOR[3]),
        "dual_path_gof_empirical_percent": dual["summary"]["gof_empirical_percent"],
        "dual_path_gof_theoretical_percent": dual["summary"]["gof_theoretical_percent"],
        "fully_theoretical": ft.get("results", {}),
        "run_dir": str(run_dir),
        "reference_lock_ok": verify.get("ok"),
        "coeffs_sha256": v.coeffs_sha256(),
        "code_sha256": v.compute_code_sha256(),
        "elapsed_s": time.time() - t0,
    }
    summary_path = run_dir / "ucl_coeff_audit_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, default=str))

    for name in CANONICAL_ARTIFACTS:
        src = run_dir / name
        if src.is_file():
            shutil.copy2(src, SCRIPT_DIR / name)
            print(f"[audit] copied {name} -> canonical_run/")

    print(json.dumps(summary, indent=2, default=str))
    if hasattr(signal, "SIGALRM"):
        signal.alarm(0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
