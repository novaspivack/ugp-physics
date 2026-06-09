# ugp_discovery_lab/tools/cp_summary_writer.py
from __future__ import annotations
import os, json, datetime as dt
from typing import Dict, Any
import numpy as np

def _fmt(x, nd=6):
    try:
        return f"{float(x):.{nd}g}"
    except Exception:
        return str(x)

def _deg(x):
    try:
        return f"{float(x):.3f}°"
    except Exception:
        return str(x)

def write_cp_json(out_dir: str, report: Dict[str, Any], filename: str = "cp_probe_report.json") -> str:
    """Write CP probe results to JSON file."""
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, filename)
    with open(path, "w") as f:
        json.dump(report, f, indent=2, default=lambda v: float(v) if isinstance(v, (np.ndarray, np.floating, np.complexfloating)) else v)
    return path

def write_cp_summary_md(out_dir: str, report: Dict[str, Any], filename: str = "cp_summary.md") -> str:
    """Write human-readable CP summary to Markdown file."""
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, filename)

    kern = report.get("kernel", {})
    ckm  = report.get("ckm", {})
    pmns = report.get("pmns", {})
    phases = report.get("phase_tests", {})
    lep   = report.get("leptogenesis_proxy", {})

    # Convenience: angles & deltas
    ckm_ang = ckm.get("angles_deg", {})
    pmns_ang= pmns.get("angles_deg", {})
    dq_deg  = ckm.get("delta_deg", None)
    dl_deg  = pmns.get("delta_deg", None)

    H1 = phases.get("H1_dirac", {})
    H2 = phases.get("H2_majorana", {})

    now = dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    md = []
    md.append(f"# UGP → CP Summary")
    md.append("")
    md.append(f"_Generated_: **{now}**  ")
    md.append(f"_Output folder_: `{out_dir}`  ")
    md.append("")
    md.append("## Kernel (UGP-locked)")
    md.append(f"- `k_gen` = `{_fmt(kern.get('k_gen', ''))}`  ")
    if "phi" in kern:
        md.append(f"- `phi`   = `{_fmt(kern.get('phi',''))}`  ")
    md.append("")

    md.append("## CKM CP Observables")
    if ckm_ang:
        md.append(f"- Angles (deg): θ12={_fmt(ckm_ang.get('theta12', ''))}, "
                  f"θ13={_fmt(ckm_ang.get('theta13',''))}, θ23={_fmt(ckm_ang.get('theta23',''))}")
    if "Jarlskog" in ckm:
        md.append(f"- Jarlskog: `{_fmt(ckm.get('Jarlskog'))}`")
    if dq_deg is not None:
        md.append(f"- δ_q: `{_deg(dq_deg)}`")
    if H1:
        md.append(f"- H1 (Dirac) prediction: best sign = `{H1.get('sign')}`, "
                  f"pred = `{_deg(H1.get('pred_rad',0)*180/3.1415926535)}` "
                  f"→ circular error = `{_deg(H1.get('err_deg',0))}`")
    md.append("")

    md.append("## PMNS CP Observables")
    if pmns_ang:
        md.append(f"- Angles (deg): θ12={_fmt(pmns_ang.get('theta12',''))}, "
                  f"θ13={_fmt(pmns_ang.get('theta13',''))}, θ23={_fmt(pmns_ang.get('theta23',''))}")
    if "Jarlskog" in pmns:
        md.append(f"- Jarlskog: `{_fmt(pmns.get('Jarlskog'))}`")
    if dl_deg is not None:
        md.append(f"- δ_ℓ: `{_deg(dl_deg)}`")
    if H2:
        md.append(f"- H2 (Majorana) prediction: best frac = `{_fmt(H2.get('frac'))}`, "
                  f"sign = `{H2.get('sign')}`, pred = `{_deg(H2.get('pred_rad',0)*180/3.1415926535)}` "
                  f"→ circular error = `{_deg(H2.get('err_deg',0))}`")
    md.append("")

    if lep:
        md.append("## Leptogenesis Proxy (dimensionless)")
        md.append(f"- m₁={_fmt(lep.get('m1'))}, m₂={_fmt(lep.get('m2'))}, m₃={_fmt(lep.get('m3'))}")
        md.append(f"- 𝓗 = `{_fmt(lep.get('H'))}`  (scale-free hierarchy measure)")
        if "J_pmns" in lep:
            md.append(f"- |J_PMNS| = `{_fmt(lep.get('J_pmns'))}`")
        if "J_eff" in lep:
            md.append(f"- J_eff = |J_PMNS|·𝓗 = `{_fmt(lep.get('J_eff'))}`")
        md.append("")

    md.append("## Notes")
    md.append("- CKM/PMNS angles extracted with PDG-like magnitudes (s13=|Ue3|, etc.).")
    md.append("- δ from J using `J = s12 s23 s13 c12 c23 c13^2 sin δ` (sign from J).")
    md.append("- H1/H2 are **discrete** UGP-phase tests (no fitting): Dirac → ±k_gen; Majorana → ±f·k_gen, f∈{1, 1/2, 0}.")
    md.append("")

    with open(path, "w") as f:
        f.write("\n".join(md))
    return path

def write_both(out_dir: str, report: Dict[str, Any]) -> Dict[str, str]:
    """
    Convenience: write JSON + MD, return paths.
    """
    p_json = write_cp_json(out_dir, report)
    p_md   = write_cp_summary_md(out_dir, report)
    return {"json": p_json, "md": p_md}
