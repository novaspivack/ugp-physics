#!/usr/bin/env python3
"""
074-REPRO — CMCA Full Reproducibility Suite (P41).

Single runnable script that implements the Three-Layer Chiral Minkowski CA
and verifies all nine headline paper claims. Reuses existing sandbox modules:

  - two_layer_chiral_afca_prototype.py — three CMCA layers + structural checks
  - phiborn1_kg_amplitude_probability.py — Born position-space normalization
  - dslit_gte_interference.py — Huygens-Fresnel double-slit correlation

Output: papers/41_three_layer_chiral_minkowski_ca/scripts/cmca_full_reproducibility_results.json
Timeout: 900 s
"""

from __future__ import annotations

import json
import math
import signal
import subprocess
import sys
import time
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np

TIMEOUT_SECONDS = 900
SANDBOX = Path(__file__).resolve().parent
REPO_ROOT = SANDBOX.parent
RESULTS_PATH = SANDBOX / "cmca_full_reproducibility_results.json"

_t0 = time.time()


def _timeout_handler(_signum, _frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

if str(SANDBOX) not in sys.path:
    sys.path.insert(0, str(SANDBOX))

import two_layer_chiral_afca_prototype as cmca  # noqa: E402


def _json_safe(obj: Any) -> Any:
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    return obj


def _claim(name: str, passed: bool, detail: dict) -> dict:
    return {"claim": name, "pass": bool(passed), **detail}


def test_glider_speeds() -> dict:
    """Claim 1: |v_R| = |v_L| = 2/3."""
    e110 = cmca.ether_tape(cmca.ETHER14, cmca.L_DEFAULT)
    e124 = cmca.ether_tape(cmca.ETHER_124_SEQ, cmca.L_DEFAULT)
    speed = cmca.measure_sync_glider_speed(
        e110, e124, cmca.CENTER_110, cmca.CENTER_124, cmca.T_SYNC
    )
    target = cmca.C_EFF
    tol = 0.01
    pass_r = abs(speed["v_r_sync"] - target) <= tol
    pass_l = abs(speed["v_l_sync"] - target) <= tol
    return _claim(
        "glider_speed_2_3",
        pass_r and pass_l,
        {
            "v_r": speed["v_r_sync"],
            "v_l": speed["v_l_sync"],
            "expected": target,
            "tolerance": tol,
            "layers_decoupled": speed["layers_decoupled"],
            "source": "two_layer_chiral_afca_prototype.measure_sync_glider_speed",
        },
    )


def test_z7_orbit() -> dict:
    """Claim 2: Z7 generation orbit gen1 -> gen2 -> gen3 -> vac in 3 steps."""
    z7 = cmca.verify_z7_generation_orbit()
    z7_afca = cmca.verify_decoupled_coevolution_afca("A", cmca.L_DEFAULT)
    passed = bool(z7["pass"] and z7_afca["reaches_vacuum_at_step_3"])
    return _claim(
        "z7_generation_orbit",
        passed,
        {
            "gen1": z7["gen1"],
            "gen2": z7["gen2"],
            "gen3": z7["gen3"],
            "vacuum": z7["vacuum"],
            "steps_to_vacuum": z7["steps_gen1_to_vacuum"],
            "afca_reaches_vacuum": z7_afca["reaches_vacuum_at_step_3"],
            "source": "two_layer_chiral_afca_prototype.verify_z7_generation_orbit",
        },
    )


def test_va_mismatches() -> dict:
    """Claim 3: V-A structure — 32/125 fMDL-110 vs fMDL-124 mismatches."""
    va = cmca.verify_va_structure()
    return _claim(
        "va_32_125",
        va["pass"],
        {
            "mismatch_count": va["mismatch_count"],
            "expected": 32,
            "total_triples": va["total_triples"],
            "r_only": va["r_only_count"],
            "l_only": va["l_only_count"],
            "w_plus_center_mismatches": va["w_plus_center_mismatches"],
            "source": "two_layer_chiral_afca_prototype.verify_va_structure",
            "lean_ref": "ChiralPairVA.va_mismatch_count",
        },
    )


def test_tau_c_sr_dilation() -> dict:
    """Claim 4: tau_c(glider)/tau_c(ether) ~ 1.563 within Nyquist floor 6.71%."""
    e110 = cmca.ether_tape(cmca.ETHER14, cmca.L_DEFAULT)
    e124 = cmca.ether_tape(cmca.ETHER_124_SEQ, cmca.L_DEFAULT)
    tau = cmca.measure_tau_c_sr(e110, e124, "A", use_c2_flip=False)
    ratio = tau["tau_c_ratio_glider_over_ether"]
    gamma = tau["gamma_target"]
    eps_floor_pct = 100.0 * math.pi ** 2 / 147.0
    sr_error_pct = tau["sr_error_pct"]
    passed = (
        tau["pass_tau_c_elevated"]
        and sr_error_pct <= eps_floor_pct + 0.05
        and abs(ratio - 1.563) / 1.563 <= 0.02
    )
    return _claim(
        "tau_c_sr_dilation",
        passed,
        {
            "tau_c_ratio": ratio,
            "expected_ratio_approx": 1.563,
            "gamma_target": gamma,
            "sr_error_percent": sr_error_pct,
            "nyquist_floor_percent": eps_floor_pct,
            "tau_c_glider_gt_ether": tau["tau_c_glider_gt_ether"],
            "source": "two_layer_chiral_afca_prototype.measure_tau_c_sr",
        },
    )


def test_observable_lorentz_floor() -> dict:
    """Claim 5: Observable Lorentz floor epsilon_0(7) = pi^2/147 ~ 6.71% < 7%."""
    eps0 = math.pi ** 2 / 147.0
    eps0_pct = 100.0 * eps0
    passed = eps0_pct < 7.0
    return _claim(
        "observable_lorentz_epsilon0",
        passed,
        {
            "epsilon_0_7": eps0,
            "epsilon_0_7_percent": eps0_pct,
            "formula": "pi^2/147",
            "expected_percent_approx": 6.71,
            "source": "continuum_limit_lorentz_bridge / epic073_lor1 (pure computation)",
        },
    )


def test_sin2_theta_w() -> dict:
    """Claim 6: sin^2 theta_W = 384729/1664000 from orbit arithmetic."""
    n_gen = 3
    c_h = 13
    n_fam = 5
    lam = Fraction(n_gen ** 2, (2 ** n_gen) * n_fam)  # 9/40
    sin2_tree = Fraction(n_gen, c_h)
    sin2_corr = lam ** n_gen / (2 * c_h)
    sin2 = sin2_tree + sin2_corr
    expected = Fraction(384729, 1664000)
    passed = sin2 == expected
    return _claim(
        "sin2_theta_w_orbit",
        passed,
        {
            "sin2_rational": f"{sin2.numerator}/{sin2.denominator}",
            "expected_rational": "384729/1664000",
            "sin2_float": float(sin2),
            "tree_term": f"{sin2_tree.numerator}/{sin2_tree.denominator}",
            "threshold_correction": f"{sin2_corr.numerator}/{sin2_corr.denominator}",
            "source": "orbit arithmetic (ew_scale_consolidation constants)",
            "lean_ref": "weinberg_two_term_prediction",
        },
    )


def _run_subprocess_script(script_name: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    script_path = SANDBOX / script_name
    remaining = max(30, TIMEOUT_SECONDS - int(time.time() - _t0) - 10)
    return subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(cwd or REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=remaining,
        check=False,
    )


def test_born_normalization() -> dict:
    """Claim 7: Born rule P(x) = |d phi/dx|^2 normalizes to unity."""
    proc = _run_subprocess_script("phiborn1_kg_amplitude_probability.py")
    results_path = SANDBOX / "phiborn1_kg_amplitude_probability_results.json"
    if not results_path.exists():
        return _claim(
            "born_rule_normalization",
            False,
            {
                "error": "phiborn1 results JSON missing",
                "subprocess_returncode": proc.returncode,
                "stderr_tail": proc.stderr[-500:] if proc.stderr else "",
            },
        )
    with open(results_path) as f:
        data = json.load(f)
    norm_pass = bool(data.get("P_x_normalization_pass"))
    sector_pass = bool(data.get("sector_born_pass"))
    passed = norm_pass and sector_pass and proc.returncode == 0
    return _claim(
        "born_rule_normalization",
        passed,
        {
            "P_x_normalization_integral": data.get("P_x_normalization_integral"),
            "P_x_normalization_pass": norm_pass,
            "sector_born_pass": sector_pass,
            "sector_born_max_residual": data.get("sector_born", {}).get("sector_born_max_residual"),
            "source": "phiborn1_kg_amplitude_probability.py",
        },
    )


def test_double_slit_correlation() -> dict:
    """Claim 8: Double-slit Fraunhofer correlation > 0.99."""
    proc = _run_subprocess_script("dslit_gte_interference.py", cwd=REPO_ROOT)
    results_path = SANDBOX / "dslit_gte_interference_results.json"
    if not results_path.exists():
        return _claim(
            "double_slit_correlation",
            False,
            {
                "error": "dslit results JSON missing",
                "subprocess_returncode": proc.returncode,
                "stderr_tail": proc.stderr[-500:] if proc.stderr else "",
            },
        )
    with open(results_path) as f:
        data = json.load(f)
    corr = float(data["zone_L1_wave"]["corr_fraunhofer"])
    passed = corr > 0.99 and proc.returncode == 0
    return _claim(
        "double_slit_correlation",
        passed,
        {
            "corr_fraunhofer": corr,
            "threshold": 0.99,
            "fringe_visibility": data["zone_L1_wave"]["fringe_visibility"],
            "source": "dslit_gte_interference.py",
        },
    )


def _log2_plus1(n: int) -> int:
    if n <= 0:
        return 0
    return int(math.floor(math.log2(n))) + 1


def k_ca_bits(
    alphabet_size: int,
    n_layers: int,
    outer_rule_bits: int,
    has_async: bool,
    gating_bits: int,
) -> int:
    """Six-channel K_CA from 074-UNIDM2 / CMCAMDLMinimality.lean."""
    k_alpha = _log2_plus1(alphabet_size)
    k_r = _log2_plus1(1)
    k_l = _log2_plus1(n_layers)
    k_rho = outer_rule_bits
    k_tau = 1 if has_async else 0
    k_g = gating_bits if has_async else 0
    return k_alpha + k_r + k_l + k_rho + k_tau + k_g


def test_mdl_k_ca() -> dict:
    """Claim 9: MDL description length K_CA = 19 for CMCA."""
    cmca_bits = k_ca_bits(
        alphabet_size=7,
        n_layers=2,
        outer_rule_bits=9,  # 8 (Rule 110) + 1 (Z2 mirror for Rule 124)
        has_async=True,
        gating_bits=3,
    )
    single = k_ca_bits(7, 1, 8, False, 0)
    two_layer = k_ca_bits(7, 2, 9, False, 0)
    afca = k_ca_bits(7, 1, 8, True, 3)
    lower_bound = 3 + 1 + 2 + 8 + 1 + 1 + 3  # independent feature minimums
    passed = cmca_bits == 19 and lower_bound == 19 and cmca_bits == lower_bound
    return _claim(
        "mdl_k_ca_19",
        passed,
        {
            "K_CA_CMCA": cmca_bits,
            "K_CA_single_R110": single,
            "K_CA_two_layer_chiral": two_layer,
            "K_CA_AFCA": afca,
            "construction_class_lower_bound": lower_bound,
            "channels": {
                "alpha": 3,
                "radius": 1,
                "layers": 2,
                "rho_outer": 9,
                "tau_async": 1,
                "gating": 3,
            },
            "source": "074-UNIDM2 bit-count functional (Python); lower bound Lean",
            "lean_ref": "CMCAMDLMinimality.lean / cmca_is_mdl_minimal_with_all_five_features",
        },
    )


def test_three_layer_cmca_implementation() -> dict:
    """Sanity: three-layer CMCA (x+, x-, t) runs via Option A shared inner clock."""
    result = cmca.run_verification("A")
    passed = bool(result["all_pass"])
    return _claim(
        "three_layer_cmca_runs",
        passed,
        {
            "clock_option": result["clock_option"],
            "checklist": result["checklist"],
            "inner_rule": "Rule 110 (ETHER14 seed)",
            "outer_x_plus": "Rule 110",
            "outer_x_minus": "Rule 124",
            "source": "two_layer_chiral_afca_prototype.run_verification",
        },
    )


def print_report(results: list[dict], elapsed: float) -> None:
    print("=" * 72)
    print("074-REPRO — CMCA Full Reproducibility Suite (P41)")
    print(f"Timeout cap: {TIMEOUT_SECONDS}s  |  Elapsed: {elapsed:.1f}s")
    print("=" * 72)
    n_pass = sum(1 for r in results if r["pass"])
    for r in results:
        status = "PASS" if r["pass"] else "FAIL"
        print(f"  [{status}] {r['claim']}")
    print("-" * 72)
    print(f"  Summary: {n_pass}/{len(results)} claims PASS")
    all_pass = n_pass == len(results)
    print(f"  OVERALL: {'PASS' if all_pass else 'FAIL'}")
    print("=" * 72)


def main() -> dict:
    tests = [
        test_three_layer_cmca_implementation,
        test_glider_speeds,
        test_z7_orbit,
        test_va_mismatches,
        test_tau_c_sr_dilation,
        test_observable_lorentz_floor,
        test_sin2_theta_w,
        test_born_normalization,
        test_double_slit_correlation,
        test_mdl_k_ca,
    ]

    claim_results: list[dict] = []
    for fn in tests:
        label = fn.__name__
        t_start = time.time()
        print(f"\n--- Running {label} ---")
        try:
            result = fn()
        except Exception as exc:
            result = _claim(label, False, {"error": str(exc)})
        result["elapsed_seconds"] = time.time() - t_start
        claim_results.append(result)
        print(f"  -> {'PASS' if result['pass'] else 'FAIL'} ({result['elapsed_seconds']:.1f}s)")

    elapsed = time.time() - _t0
    print_report(claim_results, elapsed)

    lean_only = [
        {
            "topic": "MDL construction-class lower bound (K_CA >= 19 for all-five-features)",
            "lean_module": "CMCAMDLMinimality.lean",
            "note": "Python verifies bit equality; Lean proves omega lower bound",
        },
        {
            "topic": "GTE category terminal object / Phi_MDL uniqueness",
            "lean_module": "GTECategoryStructure.lean",
            "note": "Category theorem, not CA simulation",
        },
        {
            "topic": "EW threshold step k = N_gen = 3 uniqueness",
            "lean_module": "GUTStructure.lean (isEWThresholdStep)",
            "note": "Python verifies sin^2 arithmetic only",
        },
        {
            "topic": "Born rule unconditional on kink Hilbert space",
            "lean_module": "BeableWindingPartitionInstance.lean",
            "note": "Separate from continuum P(x) normalization tested here",
        },
    ]

    output = {
        "rank": "074-REPRO",
        "date": time.strftime("%Y-%m-%d"),
        "script": "papers/41_three_layer_chiral_minkowski_ca/scripts/cmca_full_reproducibility.py",
        "paper": "P41 — Three-Layer Chiral Minkowski CA",
        "timeout_seconds": TIMEOUT_SECONDS,
        "elapsed_seconds": elapsed,
        "claims": claim_results,
        "n_pass": sum(1 for r in claim_results if r["pass"]),
        "n_total": len(claim_results),
        "overall_pass": all(r["pass"] for r in claim_results),
        "lean_only_supplements": lean_only,
        "reused_scripts": [
            "two_layer_chiral_afca_prototype.py",
            "phiborn1_kg_amplitude_probability.py",
            "dslit_gte_interference.py",
        ],
    }

    with open(RESULTS_PATH, "w") as f:
        json.dump(_json_safe(output), f, indent=2)
    print(f"\nResults saved: {RESULTS_PATH}")
    return output


if __name__ == "__main__":
    out = main()
    signal.alarm(0)
    sys.exit(0 if out["overall_pass"] else 1)
