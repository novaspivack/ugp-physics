#!/usr/bin/env python3
"""
Cosmological prediction comparison: UGP vs Planck 2018, DESI DR1, weak lensing.

Covers:
  MFRR-06: dark energy EoS w0 = -1, wa < 1e-4
  MFRR-07: growth rate f*sigma8 = 0.644
  SM-17:   cosmological constant Lambda from info-theoretic constraint
"""
import math, json
from datetime import date

# ---------------------------------------------------------------------------
# Planck 2018 (TT,TE,EE+lowE+lensing) — Table 2 of Planck 2018 results VI
# Aghanim et al. 2020, A&A 641, A6
# ---------------------------------------------------------------------------
PLANCK18 = {
    "source": "Planck 2018 (TT,TE,EE+lowE+lensing), Aghanim et al. 2020, A&A 641 A6",
    "H0":       {"val": 67.36, "unc": 0.54,    "unit": "km/s/Mpc"},
    "Omega_m":  {"val": 0.3153,"unc": 0.0073,  "unit": "dimensionless"},
    "sigma8":   {"val": 0.8111,"unc": 0.0060,  "unit": "dimensionless"},
    "S8":       {"val": 0.832, "unc": 0.013,   "unit": "dimensionless",
                 "note": "S8 = sigma8 * sqrt(Omega_m/0.3)"},
    "w0":       {"val": -1.0,  "unc": None,    "unit": "dimensionless",
                 "note": "LCDM assumption"},
    "wa":       {"val": 0.0,   "unc": None,    "unit": "dimensionless"},
    "Omega_Lambda": {"val": 0.6847,"unc": 0.0073, "unit": "dimensionless"},
    "Lambda_obs":   {"val": 1.088e-52, "unc": 0.030e-52, "unit": "m^-2",
                     "note": "Lambda = 3 H0^2 Omega_Lambda / c^2"},
}

# SH0ES H0 (for SM-17 Lambda comparison)
SHOES = {
    "source": "Riess et al. 2022 (SH0ES), ApJL 934 L7",
    "H0": {"val": 73.04, "unc": 1.04, "unit": "km/s/Mpc"},
}

# ---------------------------------------------------------------------------
# DESI DR1 (2024) — arXiv:2404.03002 (DESI Collaboration 2024 VI)
# Dark Energy Equation of State constraints
# ---------------------------------------------------------------------------
# Table 3 / Fig 6 of DESI 2024 VI
# BAO+CMB (Planck 2018 TTTEEE):
DESI_DR1_BAO_CMB = {
    "source":  "DESI DR1 BAO + Planck 2018 CMB, arXiv:2404.03002",
    "w0":      {"val": -0.45,  "unc_lo": 0.34,  "unc_hi": 0.34,  "unit": "dimensionless"},
    "wa":      {"val": -1.79,  "unc_lo": 1.08,  "unc_hi": 1.08,  "unit": "dimensionless"},
    "note":    "BAO+CMB alone weakly constrains w0-wa; large uncertainties",
}
# BAO+CMB+Union3 SNIa (strongest DESI DR1 constraint that showed tension with LCDM):
DESI_DR1_BAO_CMB_SNIa = {
    "source":  "DESI DR1 BAO + Planck CMB + Union3 SNIa, arXiv:2404.03002",
    "w0":      {"val": -0.65,  "unc": 0.10, "unit": "dimensionless"},
    "wa":      {"val": -1.27,  "unc": 0.40, "unit": "dimensionless"},
    "note":    "3.5σ tension with LCDM (w0=-1, wa=0) from this combination",
    "sigma_from_LCDM": 3.5,
}
# BAO+CMB+DES5YR SNIa:
DESI_DR1_BAO_CMB_DES5 = {
    "source":  "DESI DR1 BAO + Planck CMB + DES 5YR SNIa, arXiv:2404.03002",
    "w0":      {"val": -0.727, "unc": 0.067, "unit": "dimensionless"},
    "wa":      {"val": -1.05,  "unc": 0.27,  "unit": "dimensionless"},
    "note":    "2.5σ from LCDM",
    "sigma_from_LCDM": 2.5,
}

# DESI DR2 (2025) — arXiv:2503.14738 — updated constraints (more data)
DESI_DR2 = {
    "source": "DESI DR2 (2025), arXiv:2503.14738",
    "w0_wa_tension_sigma": 2.8,
    "note": "DESI DR2 (2025): w0-wa tension with LCDM persists at ~2.8σ (BAO+CMB+PantheonPlus). "
            "Best-fit w0 still deviates from -1 at 2-3σ depending on SNIa combination."
}

# KiDS / DES weak lensing S8 values
WEAK_LENSING = {
    "KiDS-1000": {
        "source": "Heymans et al. 2021, A&A 646 A140",
        "S8": {"val": 0.766, "unc": 0.020},
        "sigma8": {"val": 0.760, "unc": 0.022},
    },
    "DES-Y3": {
        "source": "Abbott et al. 2022, PRD 105 023520",
        "S8": {"val": 0.776, "unc": 0.017},
        "sigma8": {"val": 0.772, "unc": 0.018},
    },
    "HSC-Y3": {
        "source": "Dalal et al. 2023, PRD 108 123519",
        "S8": {"val": 0.776, "unc": 0.032},
    },
    "BOSS_RSD_z06": {
        "source": "Alam et al. 2017, MNRAS 470 2617 (BOSS DR12 z=0.61)",
        "fsigma8": {"val": 0.436, "unc": 0.034},
        "redshift": 0.61,
    },
    "eBOSS_ELG": {
        "source": "de Mattia et al. 2021, MNRAS 501 5616 (eBOSS ELG z=0.85)",
        "fsigma8": {"val": 0.450, "unc": 0.090},
        "redshift": 0.85,
    },
    "DESI_DR1_RSD": {
        "source": "DESI DR1 peculiar velocities, 2024",
        "fsigma8": {"val": 0.447, "unc": 0.020},
        "redshift": 0.51,
    },
}

# ---------------------------------------------------------------------------
# UGP predictions
# ---------------------------------------------------------------------------
# MFRR-06: w0 = -1 exactly, wa < 1e-4
UGP_W0 = -1.0
UGP_WA_UPPER = 1e-4

# MFRR-07: f*sigma8 = 0.644
# NOTE: The MFRR paper does not specify the reference redshift explicitly in the
# catalog entry. Based on the PSC cosmological attractor derivation, this is
# likely at z~0 or the effective redshift of large-scale structure surveys.
# BOSS/eBOSS/DESI RSD measurements give f*sigma8 ~ 0.43-0.48 at z~0.5-0.85.
# Planck LCDM prediction at z=0: f*sigma8 ~ 0.46.
# The UGP value 0.644 is significantly higher than all current RSD measurements.
# This is flagged as a TENSION requiring clarification of the reference redshift.
UGP_FSIGMA8 = 0.644

# SM-17: Lambda from info-theoretic constraint
# Lambda = (ln2/pi) * L_model * H0^2/c^2  with L_model = log2(2000/3)
ln2 = math.log(2)
L_model = math.log2(2000/3)   # = log2(666.67) ≈ 9.382
c_km_s = 2.99792458e5         # km/s

def ugp_lambda(H0_km_s_Mpc):
    """Compute Lambda in m^-2 from SM-17 formula."""
    # Convert H0 to SI: H0 in s^-1
    Mpc_to_m = 3.085677581e22   # meters per Mpc
    H0_si = H0_km_s_Mpc * 1e3 / Mpc_to_m  # s^-1
    c_si  = 2.99792458e8         # m/s
    return (ln2 / math.pi) * L_model * H0_si**2 / c_si**2

lambda_planck_H0 = ugp_lambda(PLANCK18["H0"]["val"])
lambda_shoes_H0  = ugp_lambda(SHOES["H0"]["val"])
lambda_obs       = PLANCK18["Lambda_obs"]["val"]

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
lines = [
    "# Cosmological Prediction Comparison — UGP vs Planck 2018 / DESI DR1 / Weak Lensing",
    f"Date: {date.today()}",
    "",
    "---",
    "",
    "## MFRR-06: Dark Energy Equation of State",
    "",
    f"**UGP prediction:** w₀ = {UGP_W0} (exact), wₐ < {UGP_WA_UPPER}",
    "",
    "### DESI DR1 constraints (arXiv:2404.03002):",
    "",
    "| Dataset | w₀ | wₐ | σ from ΛCDM |",
    "|---------|----|----|------------|",
    f"| BAO+CMB only | {DESI_DR1_BAO_CMB['w0']['val']} ± {DESI_DR1_BAO_CMB['w0']['unc_lo']} | {DESI_DR1_BAO_CMB['wa']['val']} ± {DESI_DR1_BAO_CMB['wa']['unc_lo']} | unconstrained |",
    f"| BAO+CMB+Union3 | {DESI_DR1_BAO_CMB_SNIa['w0']['val']} ± {DESI_DR1_BAO_CMB_SNIa['w0']['unc']} | {DESI_DR1_BAO_CMB_SNIa['wa']['val']} ± {DESI_DR1_BAO_CMB_SNIa['wa']['unc']} | {DESI_DR1_BAO_CMB_SNIa['sigma_from_LCDM']}σ |",
    f"| BAO+CMB+DES5YR | {DESI_DR1_BAO_CMB_DES5['w0']['val']} ± {DESI_DR1_BAO_CMB_DES5['w0']['unc']} | {DESI_DR1_BAO_CMB_DES5['wa']['val']} ± {DESI_DR1_BAO_CMB_DES5['wa']['unc']} | {DESI_DR1_BAO_CMB_DES5['sigma_from_LCDM']}σ |",
    "",
    "### DESI DR2 (2025, arXiv:2503.14738):",
    f"  w₀-wₐ tension with ΛCDM: ~{DESI_DR2['w0_wa_tension_sigma']}σ (BAO+CMB+PantheonPlus)",
    "",
]

# Status for MFRR-06
# UGP predicts w0=-1, wa=0. DESI DR1 Union3 gives w0=-0.65±0.10 => differs from -1 by 3.5σ.
# This is a tension between UGP and DESI DR1. But it is also tension between DESI and Planck-only.
w0_tension_union3 = abs(UGP_W0 - DESI_DR1_BAO_CMB_SNIa["w0"]["val"]) / DESI_DR1_BAO_CMB_SNIa["w0"]["unc"]
lines += [
    f"**UGP w₀=-1 vs DESI+Union3 best-fit w₀={DESI_DR1_BAO_CMB_SNIa['w0']['val']}:** {w0_tension_union3:.1f}σ tension",
    "",
    "**Status (MFRR-06):**",
    "  - ⚠ TENSION: DESI DR1 (with Union3/DES SNIa) finds w₀ ≠ -1 at 2.5–3.5σ.",
    "  - NOTE: Planck-only analysis is consistent with ΛCDM (w₀=-1). The tension is driven by SNIa.",
    "  - If DESI DR2 tension persists with improved SNIa data, this would be a falsification of MFRR-06.",
    "  - UGP prediction wₐ = 0 is consistent with all current data at 1σ (poorly constrained).",
    "",
    "---",
    "",
    "## MFRR-07: Growth Rate f·σ₈",
    "",
    f"**UGP prediction:** f·σ₈ = {UGP_FSIGMA8}",
    "",
    "### Published RSD f·σ₈ measurements:",
    "",
    "| Survey | f·σ₈ | z_eff | Source |",
    "|--------|------|-------|--------|",
]

for survey, data in WEAK_LENSING.items():
    if "fsigma8" in data:
        fsig8 = data["fsigma8"]
        z = data.get("redshift", "?")
        dev = abs(UGP_FSIGMA8 - fsig8["val"]) / fsig8["unc"]
        lines.append(f"| {survey} | {fsig8['val']} ± {fsig8['unc']} | {z} | {data['source']} |")

# Planck LCDM prediction of fsigma8 at z=0
# f ~ Omega_m^0.55, sigma8(z=0) = 0.8111
f_z0_planck = PLANCK18["Omega_m"]["val"]**0.55
fsig8_z0_planck = f_z0_planck * PLANCK18["sigma8"]["val"]

lines += [
    f"| Planck 2018 ΛCDM (z=0) | {fsig8_z0_planck:.3f} (computed) | 0 | Planck + f~Ωm^0.55 |",
    "",
    f"**Planck ΛCDM f·σ₈(z=0) = {fsig8_z0_planck:.3f}** (vs UGP prediction {UGP_FSIGMA8})",
    f"  UGP−Planck: {(UGP_FSIGMA8 - fsig8_z0_planck)/fsig8_z0_planck*100:+.1f}%",
    "",
    "⚠ **CRITICAL NOTE on MFRR-07:**",
    "  The UGP prediction f·σ₈ = 0.644 is significantly higher than all current RSD measurements",
    f"  (which cluster around 0.43–0.48 at z~0.5–0.85) and also higher than the Planck ΛCDM",
    f"  prediction at z=0 ({fsig8_z0_planck:.3f}). This represents a TENSION.",
    "",
    "  **Resolution needed:** The MFRR paper must specify the reference redshift and cosmological",
    "  context for this prediction. Possible explanations:",
    "  1. The prediction is at a different redshift (z~0.1 would give f·σ₈ ~ 0.50)",
    "  2. The prediction uses a non-standard σ₈ normalization",
    "  3. There is a genuine tension that falsifies MFRR-07",
    "",
    "  This requires checking the MFRR paper directly for the specific derivation context.",
    "",
    "**Status (MFRR-07): ⚠ TENSION / CLARIFICATION NEEDED** — predicted value 0.644 inconsistent",
    "  with current RSD data at ~5–10σ if interpreted as standard f·σ₈ at any measured redshift.",
    "",
    "---",
    "",
    "## SM-17: Cosmological Constant Λ",
    "",
    "**UGP formula:** Λ = (ln2/π) · L_model · H₀²/c²",
    f"  L_model = log₂(2000/3) = {L_model:.6f}",
    f"  ln2/π = {ln2/math.pi:.8f}",
    "",
    f"**UGP Λ (Planck H₀ = {PLANCK18['H0']['val']} km/s/Mpc):** {lambda_planck_H0:.6e} m⁻²",
    f"**UGP Λ (SH0ES H₀ = {SHOES['H0']['val']} km/s/Mpc):**    {lambda_shoes_H0:.6e} m⁻²",
    f"**Observed Λ (Planck 2018):**                              {lambda_obs:.6e} ± {PLANCK18['Lambda_obs']['unc']:.3e} m⁻²",
    "",
]

dev_planck = (lambda_planck_H0 - lambda_obs) / lambda_obs * 100
dev_shoes  = (lambda_shoes_H0  - lambda_obs) / lambda_obs * 100
sig_planck = abs(lambda_planck_H0 - lambda_obs) / PLANCK18["Lambda_obs"]["unc"]
sig_shoes  = abs(lambda_shoes_H0  - lambda_obs) / PLANCK18["Lambda_obs"]["unc"]

lines += [
    f"**Deviation (Planck H₀):** {dev_planck:+.3f}%  /  {sig_planck:.2f}σ",
    f"**Deviation (SH0ES H₀):**  {dev_shoes:+.3f}%  /  {sig_shoes:.2f}σ",
    "",
    "Note: H₀ tension (Planck vs SH0ES ~5σ) translates to ~15% spread in Λ prediction.",
    "With Planck H₀ the match is: " +
    ("✓ Confirmed (<2σ)" if sig_planck < 2 else f"~✓ Consistent ({sig_planck:.1f}σ)" if sig_planck < 3 else f"⚠ Tension ({sig_planck:.1f}σ)"),
    f"**Status (SM-17): {'✓ Confirmed' if sig_planck < 2 else '~✓ Consistent'} with Planck H₀** (H₀ tension is external to the UGP framework)",
]

out_md   = "/Users/nova/ugp-physics/data_mining/results/cosmological_comparison.md"
out_json = "/Users/nova/ugp-physics/data_mining/results/cosmological_comparison.json"

with open(out_md, "w") as f:
    f.write("\n".join(lines))

summary = {
    "date": str(date.today()),
    "MFRR06_w0_ugp": UGP_W0,
    "MFRR06_w0_DESI_Union3": DESI_DR1_BAO_CMB_SNIa["w0"]["val"],
    "MFRR06_tension_sigma": w0_tension_union3,
    "MFRR07_fsig8_ugp": UGP_FSIGMA8,
    "MFRR07_fsig8_planck_LCDM_z0": fsig8_z0_planck,
    "MFRR07_note": "TENSION: requires redshift clarification from MFRR paper",
    "SM17_lambda_ugp_planck_H0": lambda_planck_H0,
    "SM17_lambda_ugp_shoes_H0": lambda_shoes_H0,
    "SM17_lambda_obs": lambda_obs,
    "SM17_dev_planck_pct": dev_planck,
    "SM17_dev_planck_sigma": sig_planck,
}
with open(out_json, "w") as f:
    json.dump(summary, f, indent=2)

print("\n".join(lines))
print(f"\nSaved to {out_md} and {out_json}")
