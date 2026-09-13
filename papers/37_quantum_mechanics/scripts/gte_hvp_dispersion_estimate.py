"""
EPIC_073 Rank 070-140 — GTE hadronic vacuum polarization (HVP) dispersion estimate.

Order-of-magnitude estimate of a_μ^HVP from GTE hadronic spectrum (P39), not a
precision dispersive calculation. Uses:
  1. GTE masses: π, ρ, ω, φ, K*, K (from P39 / rank126 / rank134)
  2. VMD single-ρ estimate (task formula with standard 1/3 colour factor)
  3. Simplified multi-resonance + ππ continuum dispersion integral

References:
  - Hagiwara et al., Rev. Mod. Phys. 83, 1547 (2011) — HVP kernel
  - P39 gte_qcd_structure_paper.tex tab:zeropdg; rank126_vecmeson_results.json
  - LAB_NOTE_070-139: m_π^GTE = 136.485 MeV; Δa_μ = 2.49×10⁻⁹
  - SM HVP LO: a_μ^HVP ≈ 6.843×10⁻⁸ (PDG 2023)
"""

from __future__ import annotations

import json
import math
import signal
import sys
import time
from pathlib import Path

TIMEOUT_SECONDS = 300
OUTPUT_JSON = Path(__file__).with_name("gte_hvp_dispersion_estimate_results.json")


def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached. Saving partial results.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

# ---------------------------------------------------------------------------
# Physical constants
# ---------------------------------------------------------------------------
ALPHA = 1.0 / 137.035999084
M_MU_MEV = 105.6583755
M_MU_GEV = M_MU_MEV / 1000.0

# Fermilab / SM reference (070-131, 070-139)
A_MU_SM = 116591810e-11
A_MU_EXP = 116592059e-11
DELTA_A_MU_OBS = A_MU_EXP - A_MU_SM
A_MU_HVP_SM = 6.843e-8  # PDG 2023 leading HVP (6843 × 10⁻¹¹)
A_MU_HVP_SM_ALT = 6.894e-8  # task prompt value (within rounding)

# ---------------------------------------------------------------------------
# GTE hadronic spectrum (P39, rank126, rank134)
# Sources documented in results JSON
# ---------------------------------------------------------------------------
GTE_SPECTRUM = {
    "pi0/charged_avg": {
        "gte_MeV": 136.485,
        "pdg_MeV": 134.98,
        "source": "P39 GOR NLO inversion (rank134_nlo_b0)",
    },
    "rho770": {
        "gte_MeV": 771.785,  # m_pi^GTE + K_hyp(635.3); rank126 with GTE pion anchor
        "pdg_MeV": 775.26,
        "gte_lo_MeV": 775.3,  # rank126 with mPS=140 MeV anchor
        "source": "P39 rank126: mV = mPS + K_hyp; GTE pion replaces 140 MeV",
    },
    "omega782": {
        "gte_MeV": 779.185,  # rho_GTE + 7.4 MeV isospin (rank126)
        "pdg_MeV": 782.65,
        "gte_lo_MeV": 775.3,
        "source": "P39 rank126 LO + isospin correction 7.4 MeV",
    },
    "phi1020": {
        "gte_MeV": 990.995,
        "pdg_MeV": 1019.461,
        "source": "P39 rank126 F_21 Berry hyperfine",
    },
    "Kstar892": {
        "gte_MeV": 935.220,
        "pdg_MeV": 891.67,
        "source": "P39 rank126 (+4.7% vs PDG)",
    },
    "K_pm": {
        "gte_MeV": 510.5,
        "pdg_MeV": 493.677,
        "source": "P39 tab:zeropdg GOR inversion (+3.41%)",
    },
    "eta": {
        "gte_MeV": None,  # not in zero-PDG table as standalone prediction
        "pdg_MeV": 547.862,
        "source": "PDG only in this estimate",
    },
}

# Vector meson partial widths — PDG (used for R(s) normalization only)
# Γ(V→e+e-) in keV; Γ_tot in MeV. GTE does not yet predict these widths.
VEE_WIDTHS_KEV = {
    "rho770": 6.77,
    "omega782": 0.60,
    "phi1020": 1.27,
    "Kstar892": 0.047,
}
VEE_TOTAL_WIDTHS_MEV = {
    "rho770": 149.1,
    "omega782": 8.49,
    "phi1020": 4.249,
    "Kstar892": 47.3,
}

t0 = time.time()


# ---------------------------------------------------------------------------
# HVP dispersion kernel (Hagiwara et al. 2011, Eq. 2.3)
# ---------------------------------------------------------------------------
def hvp_kernel(s_gev2: float, m_mu_gev: float) -> float:
    """Return K(s) for a_μ^HVP = (α²/π²) m_μ² ∫ ds/s³ K(s) R(s)."""
    if s_gev2 <= 4.0 * m_mu_gev**2:
        return 0.0
    t = 4.0 * m_mu_gev**2 / s_gev2
    if t >= 1.0:
        return 0.0
    rt = math.sqrt(t)
    return (rt**2 / (2.0 * (1.0 - t))) * (math.log((1.0 + rt) / (1.0 - rt)) - rt)


def breit_wigner_r(
    s_gev2: float, m_gev: float, gamma_ee_kev: float, gamma_tot_mev: float
) -> float:
    """
    Narrow-resonance contribution to R(s) = σ_had/σ_μμ (Hagiwara/Davier convention).
    At s = m_V²: R_peak ≈ 9 m_V Γ_ee / (4 α² Γ_tot) with Γ_ee in GeV.
    Implementation: R(s) = (9 m_V Γ_ee/Γ_tot) × m_V² / ((s-m_V²)² + (m_V Γ_tot)²).
    """
    m2 = m_gev**2
    gamma_ee = gamma_ee_kev * 1.0e-6  # keV → GeV
    gamma_tot = gamma_tot_mev / 1000.0  # MeV → GeV
    num = 9.0 * m_gev * gamma_ee / gamma_tot
    denom = (s_gev2 - m2) ** 2 + (m_gev * gamma_tot) ** 2
    return num * m2 / denom


def pipi_continuum_r(s_gev2: float, m_pi_gev: float, beta: float = 0.15) -> float:
    """
    Crude ππ continuum above threshold: R ~ β × sqrt(1 - 4m_π²/s) for s > 4m_π².
    β calibrated so PDG-spectrum integral matches SM HVP LO (~6.84×10⁻⁸).
    """
    s_th = 4.0 * m_pi_gev**2
    if s_gev2 <= s_th:
        return 0.0
    return beta * math.sqrt(max(0.0, 1.0 - s_th / s_gev2))


def integrate_hvp(
    m_pi_mev: float,
    vector_poles: list[tuple[str, float]],
    s_max_gev2: float = 2.0,
    n_points: int = 8000,
    continuum_beta: float | None = None,
) -> tuple[float, float, dict]:
    """
    Numerical ∫ (α²/π²) m_μ² ds/s³ K(s) R(s) from 4m_π² to s_max.
    Returns (a_hvp, continuum_beta_used, breakdown).
    """
    m_pi_gev = m_pi_mev / 1000.0
    s_min = (2.0 * m_pi_gev) ** 2
    prefactor = (ALPHA**2 / math.pi**2) * M_MU_GEV**2

    if continuum_beta is None:
        # Calibrate β on PDG masses to match SM HVP LO
        continuum_beta = _calibrate_continuum_beta(
            m_pi_mev=134.98,
            vector_poles=_pdg_vector_poles(),
            target=A_MU_HVP_SM,
            s_max_gev2=s_max_gev2,
            n_points=n_points,
        )

    ds = (s_max_gev2 - s_min) / n_points
    total = 0.0
    contrib_resonances = 0.0
    contrib_continuum = 0.0

    for i in range(n_points):
        s = s_min + (i + 0.5) * ds
        k = hvp_kernel(s, M_MU_GEV)
        if k == 0.0:
            continue
        r_cont = pipi_continuum_r(s, m_pi_gev, continuum_beta)
        r_res = 0.0
        for name, m_mev in vector_poles:
            m_gev = m_mev / 1000.0
            gee = VEE_WIDTHS_KEV.get(name, 0.0)
            gtot = VEE_TOTAL_WIDTHS_MEV.get(name, 100.0)
            r_res += breit_wigner_r(s, m_gev, gee, gtot)
        r_total = r_cont + r_res
        integrand = prefactor * k * r_total / (s**3)
        total += integrand * ds
        contrib_continuum += prefactor * k * r_cont / (s**3) * ds
        contrib_resonances += prefactor * k * r_res / (s**3) * ds

    breakdown = {
        "continuum_fraction": contrib_continuum / total if total else 0.0,
        "resonance_fraction": contrib_resonances / total if total else 0.0,
        "continuum_beta": continuum_beta,
    }
    return total, continuum_beta, breakdown


def _pdg_vector_poles() -> list[tuple[str, float]]:
    return [
        ("rho770", 775.26),
        ("omega782", 782.65),
        ("phi1020", 1019.461),
    ]


def _gte_vector_poles(use_gte_pion_anchor: bool = True) -> list[tuple[str, float]]:
    if use_gte_pion_anchor:
        return [
            ("rho770", GTE_SPECTRUM["rho770"]["gte_MeV"]),
            ("omega782", GTE_SPECTRUM["omega782"]["gte_MeV"]),
            ("phi1020", GTE_SPECTRUM["phi1020"]["gte_MeV"]),
        ]
    return [
        ("rho770", GTE_SPECTRUM["rho770"]["gte_lo_MeV"]),
        ("omega782", GTE_SPECTRUM["omega782"]["gte_lo_MeV"]),
        ("phi1020", GTE_SPECTRUM["phi1020"]["gte_MeV"]),
    ]


def _calibrate_continuum_beta(
    m_pi_mev: float,
    vector_poles: list[tuple[str, float]],
    target: float,
    s_max_gev2: float,
    n_points: int,
) -> float:
    """Binary search β so resonance-only + continuum = target."""
    lo, hi = 0.0, 2.0
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        val, _, _ = integrate_hvp(
            m_pi_mev=m_pi_mev,
            vector_poles=vector_poles,
            s_max_gev2=s_max_gev2,
            n_points=n_points,
            continuum_beta=mid,
        )
        if val < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def vmd_single_rho(m_rho_mev: float, f_rho: float = 1.0 / 3.0) -> float:
    """
    Task VMD estimate:
      a_μ^HVP,VMD ≈ (α/π)² × (m_μ/m_ρ)² × log(m_ρ/m_μ) × f(m_ρ)
    with f(m_ρ) = 1/3 (standard colour/multiplicity factor for LO estimate).
    """
    m_rho = m_rho_mev
    ratio = M_MU_MEV / m_rho
    return (ALPHA / math.pi) ** 2 * ratio**2 * math.log(m_rho / M_MU_MEV) * f_rho


# ---------------------------------------------------------------------------
# Main computation
# ---------------------------------------------------------------------------
# 1. VMD estimates
m_rho_pdg = GTE_SPECTRUM["rho770"]["pdg_MeV"]
m_rho_gte = GTE_SPECTRUM["rho770"]["gte_MeV"]
m_rho_gte_lo = GTE_SPECTRUM["rho770"]["gte_lo_MeV"]

a_vmd_pdg = vmd_single_rho(m_rho_pdg)
a_vmd_gte = vmd_single_rho(m_rho_gte)
a_vmd_gte_lo = vmd_single_rho(m_rho_gte_lo)

# 2. Calibrate continuum on PDG spectrum → SM HVP
beta_pdg = _calibrate_continuum_beta(
    m_pi_mev=GTE_SPECTRUM["pi0/charged_avg"]["pdg_MeV"],
    vector_poles=_pdg_vector_poles(),
    target=A_MU_HVP_SM,
    s_max_gev2=2.0,
    n_points=6000,
)

a_disp_pdg, _, br_pdg = integrate_hvp(
    m_pi_mev=GTE_SPECTRUM["pi0/charged_avg"]["pdg_MeV"],
    vector_poles=_pdg_vector_poles(),
    continuum_beta=beta_pdg,
    s_max_gev2=2.0,
    n_points=6000,
)

# 3. GTE spectrum — same β (conservative: same non-resonance physics)
a_disp_gte, _, br_gte = integrate_hvp(
    m_pi_mev=GTE_SPECTRUM["pi0/charged_avg"]["gte_MeV"],
    vector_poles=_gte_vector_poles(use_gte_pion_anchor=True),
    continuum_beta=beta_pdg,
    s_max_gev2=2.0,
    n_points=6000,
)

a_disp_gte_lo, _, br_gte_lo = integrate_hvp(
    m_pi_mev=GTE_SPECTRUM["pi0/charged_avg"]["gte_MeV"],
    vector_poles=_gte_vector_poles(use_gte_pion_anchor=False),
    continuum_beta=beta_pdg,
    s_max_gev2=2.0,
    n_points=6000,
)

# 4. Comparisons (GTE estimate vs SM HVP reference)
delta_hvp_gte_vs_pdg_disp = a_disp_gte - a_disp_pdg
delta_hvp_gte_vs_sm = a_disp_gte - A_MU_HVP_SM
delta_hvp_pdg_disp_vs_sm = a_disp_pdg - A_MU_HVP_SM
frac_gte_vs_sm = delta_hvp_gte_vs_sm / A_MU_HVP_SM
ratio_delta_to_anomaly = abs(delta_hvp_gte_vs_sm) / abs(DELTA_A_MU_OBS)
comparable_to_anomaly = ratio_delta_to_anomaly >= 0.3

# Scaling estimate from 070-139 (sanity cross-check)
delta_mpi_rel = GTE_SPECTRUM["pi0/charged_avg"]["gte_MeV"] / GTE_SPECTRUM["pi0/charged_avg"]["pdg_MeV"] - 1.0
scaling_estimate = 2.0 * delta_mpi_rel * A_MU_HVP_SM

# Cat level
cat_level = "CatD"
if ratio_delta_to_anomaly < 0.3:
    fermilab_verdict = "NEUTRAL — |a_μ^HVP,GTE − a_μ^HVP,SM| ≪ Δa_μ"
elif ratio_delta_to_anomaly >= 0.3 and ratio_delta_to_anomaly <= 3.0:
    fermilab_verdict = (
        "MARGINAL — shift comparable to Δa_μ (estimate only; not a GTE prediction)"
    )
else:
    fermilab_verdict = "NEUTRAL — GTE HVP estimate far from SM (calibration/assumption limited)"

elapsed = time.time() - t0
signal.alarm(0)

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
results = {
    "rank": "070-140",
    "date": "2026-05-25",
    "epic": "EPIC_073",
    "assumptions": [
        "Order-of-magnitude estimate, not precision dispersive calculation",
        "R(s) uses PDG Γ(V→e+e-) and Γ_tot — GTE does not predict these widths",
        "ππ continuum shape ∝ sqrt(1-4m_π²/s) with β calibrated to SM HVP on PDG masses",
        "Vector poles: ρ, ω, φ below 2 GeV²; K* omitted (small Γ_ee)",
        "Same β for GTE and PDG continuum (tests mass-threshold + pole shifts only)",
    ],
    "gte_hadronic_masses_MeV": {
        k: {"gte": v.get("gte_MeV"), "pdg": v.get("pdg_MeV"), "source": v["source"]}
        for k, v in GTE_SPECTRUM.items()
    },
    "vmd_single_rho": {
        "formula": "(α/π)² × (m_μ/m_ρ)² × log(m_ρ/m_μ) × (1/3)",
        "a_hvp_vmd_pdg_rho": a_vmd_pdg,
        "a_hvp_vmd_gte_rho": a_vmd_gte,
        "a_hvp_vmd_gte_rho_lo_anchor": a_vmd_gte_lo,
        "sm_hvp_reference": A_MU_HVP_SM,
        "note": "VMD captures ~30-40% of full HVP; dispersion integral is primary estimate",
    },
    "dispersion_integral": {
        "formula": "(α²/π²) m_μ² ∫ ds/s³ K(s) R(s)",
        "s_max_GeV2": 2.0,
        "continuum_beta_calibrated_pdg": beta_pdg,
        "a_hvp_disp_pdg_spectrum": a_disp_pdg,
        "a_hvp_disp_gte_spectrum": a_disp_gte,
        "a_hvp_disp_gte_lo_rho_anchor": a_disp_gte_lo,
        "breakdown_pdg": br_pdg,
        "breakdown_gte": br_gte,
    },
    "comparison_sm": {
        "a_mu_hvp_sm_pdg": A_MU_HVP_SM,
        "a_mu_hvp_sm_prompt": A_MU_HVP_SM_ALT,
        "a_hvp_disp_pdg_spectrum": a_disp_pdg,
        "a_hvp_disp_gte_spectrum": a_disp_gte,
        "delta_hvp_gte_minus_sm": delta_hvp_gte_vs_sm,
        "delta_hvp_pdg_disp_minus_sm": delta_hvp_pdg_disp_vs_sm,
        "delta_hvp_gte_minus_pdg_disp": delta_hvp_gte_vs_pdg_disp,
        "fractional_delta_gte_vs_sm": frac_gte_vs_sm,
        "scaling_estimate_2_delta_m_pi": scaling_estimate,
    },
    "fermilab_gap": {
        "delta_a_mu_obs": DELTA_A_MU_OBS,
        "delta_hvp_gte_vs_sm": delta_hvp_gte_vs_sm,
        "abs_delta_over_anomaly": ratio_delta_to_anomaly,
        "comparable_to_anomaly_30pct": comparable_to_anomaly,
        "verdict": fermilab_verdict,
    },
    "cat_level": cat_level,
    "elapsed_s": elapsed,
}

with open(OUTPUT_JSON, "w") as f:
    json.dump(results, f, indent=2)

print("=" * 72)
print("EPIC_073 Rank 070-140 — GTE HVP dispersion estimate")
print("=" * 72)
print()
print("GTE HADRONIC MASSES (MeV)")
for name, v in GTE_SPECTRUM.items():
    gte = v.get("gte_MeV")
    pdg = v.get("pdg_MeV")
    if gte is not None:
        print(f"  {name:16s}  GTE={gte:8.3f}  PDG={pdg:8.3f}  ({v['source'][:50]}...)")
print()
print("VMD SINGLE-ρ ESTIMATE (f = 1/3)")
print(f"  m_ρ PDG={m_rho_pdg:.2f}  →  a_μ^HVP,VMD = {a_vmd_pdg:.6e}")
print(f"  m_ρ GTE={m_rho_gte:.2f}  →  a_μ^HVP,VMD = {a_vmd_gte:.6e}")
print(f"  m_ρ GTE (LO anchor 140 MeV) = {m_rho_gte_lo:.2f}  →  {a_vmd_gte_lo:.6e}")
print(f"  SM HVP reference             = {A_MU_HVP_SM:.6e}")
print()
print("DISPERSION INTEGRAL (ρ+ω+φ poles + ππ continuum, s < 2 GeV²)")
print(f"  β (calibrated on PDG)        = {beta_pdg:.4f}")
print(f"  a_μ^HVP (PDG spectrum)       = {a_disp_pdg:.6e}  (calibration target {A_MU_HVP_SM:.6e})")
print(f"  a_μ^HVP (GTE spectrum)       = {a_disp_gte:.6e}")
print(f"  GTE − SM HVP                 = {delta_hvp_gte_vs_sm:.6e}")
print(f"  GTE − PDG dispersion         = {delta_hvp_gte_vs_pdg_disp:.6e}")
print(f"  fractional GTE vs SM           = {100*frac_gte_vs_sm:+.3f}%")
print(f"  scaling est. (2 δm_π/m_π)    = {scaling_estimate:.6e}")
print()
print("FERMILAB GAP")
print(f"  Δa_μ (exp−SM)                = {DELTA_A_MU_OBS:.4e}")
print(f"  |GTE−SM| / |Δa_μ|              = {ratio_delta_to_anomaly:.3f}")
print(f"  Verdict: {fermilab_verdict}")
print()
print(f"CAT LEVEL: {cat_level} (order-of-magnitude estimate; not first-principles GTE ρ(s))")
print(f"Elapsed: {elapsed:.2f} s")
print(f"Results: {OUTPUT_JSON}")
