"""
Rank 128-QUARKMASS: Quark-sector generation mass ratio from GTE cascade.

Uses the canonical InformationMassTransformer (IMT) from the GTE verifier to
compute all fundamental-fermion masses and derive the down-type generation ratio
m_s/m_d (and m_s/m_u), independent of the lepton sector.

Context (Rank 124-MIXANGLE):
  The meson mixing angle θ_P ≈ −10.7° requires r_quark = m_s/m_u ≈ 6.34
  (additive) or ≈ 26 (GOR quadratic) in effective constituent mass conventions.
  GTE IMT gives CURRENT quark masses; this script establishes which regime GTE
  occupies and what additional physics is needed to bridge to the meson sector.

Canonical triples (from CANONICAL_TRIPLES in UGP_GTE_SM_Verifier.py):
  Leptons:
    electron: (a=1, b=73,  c=823,   gen=1, type=lepton)
    muon:     (a=9, b=42,  c=1023,  gen=2, type=lepton)
    tau:      (a=5, b=275, c=-65535,gen=3, type=lepton)
  Up-type quarks:
    up:    (a=5,  b=9,      c=275,  gen=1, type=up_type)
    charm: (a=5,  b=275,    c=65535,gen=2, type=up_type)
    top:   (a=76, b=337920, c=-1,   gen=3, type=up_type)
  Down-type quarks:
    down:    (a=9, b=5,    c=42,   gen=1, type=down_type)
    strange: (a=9, b=186,  c=1023, gen=2, type=down_type)
    bottom:  (a=5, b=8191, c=65535,gen=3, type=down_type)
"""

import sys
import os
import json
import math
import time

TIMEOUT_SECONDS = 120
t_start = time.time()

# ---------------------------------------------------------------------------
# Import the canonical GTE verifier
# ---------------------------------------------------------------------------
VERIFIER_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "papers", "01_SM", "canonical_run"
)
if VERIFIER_PATH not in sys.path:
    sys.path.insert(0, VERIFIER_PATH)

import UGP_GTE_SM_Verifier as M

# Null logger — suppress all internal output
_L = type("_L", (), {
    "info":    lambda *a, **k: None,
    "error":   lambda *a, **k: None,
    "debug":   lambda *a, **k: None,
    "warning": lambda *a, **k: None,
})()

# ---------------------------------------------------------------------------
# PDG reference masses (MeV, 2024 PDG)
# ---------------------------------------------------------------------------
PDG_CURRENT = {
    "electron": 0.51099895,
    "muon":     105.6583755,
    "tau":      1776.86,
    "up":       2.3,
    "down":     4.8,
    "strange":  95.0,
    "charm":    1270.0,
    "bottom":   4180.0,
    "top":      172760.0,
}
PDG_CONSTITUENT = {
    "up":      336.0,
    "down":    340.0,
    "strange": 486.0,
    "charm":   1550.0,
}

# ---------------------------------------------------------------------------
# Canonical particle table: (name, a, b, c, gen, ptype)
# ---------------------------------------------------------------------------
PARTICLES = [
    ("electron", 1,    73,       823,     1, "lepton"),
    ("muon",     9,    42,      1023,     2, "lepton"),
    ("tau",      5,   275,    -65535,     3, "lepton"),
    ("up",       5,     9,       275,     1, "up_type"),
    ("charm",    5,   275,     65535,     2, "up_type"),
    ("top",     76, 337920,        -1,    3, "up_type"),
    ("down",     9,     5,        42,     1, "down_type"),
    ("strange",  9,   186,      1023,     2, "down_type"),
    ("bottom",   5,  8191,     65535,     3, "down_type"),
]

def sanity_check_imt():
    """Reproduce one known result before using IMT for new predictions."""
    imt = M.InformationMassTransformer(_L)
    res = imt.information_to_mass(73, 1, "lepton", "electron", a=1, c=823)
    m_e = float(res.mass_mev)
    expected = 0.5110
    tol = 0.001
    assert abs(m_e - expected) < tol, (
        f"Sanity check FAILED: electron mass = {m_e:.4f} MeV, expected {expected} MeV. "
        "IMT state has changed — do not proceed."
    )
    return m_e

def compute_all_masses():
    """Compute GTE IMT masses for all 9 fundamental fermions."""
    imt = M.InformationMassTransformer(_L)
    results = {}
    for name, a, b, c, gen, ptype in PARTICLES:
        if time.time() - t_start > TIMEOUT_SECONDS:
            raise RuntimeError(f"Timeout after {TIMEOUT_SECONDS}s in compute_all_masses")
        res = imt.information_to_mass(abs(b), gen, ptype, name, a=a, c=c)
        results[name] = {
            "mass_mev":   float(res.mass_mev),
            "a": a, "b": b, "c": c,
            "gen": gen, "ptype": ptype,
        }
    return results

def compute_generation_ratios(masses):
    """Compute generation mass ratios for each sector."""
    m_e  = masses["electron"]["mass_mev"]
    m_mu = masses["muon"]["mass_mev"]
    m_tau= masses["tau"]["mass_mev"]
    m_u  = masses["up"]["mass_mev"]
    m_c  = masses["charm"]["mass_mev"]
    m_t  = masses["top"]["mass_mev"]
    m_d  = masses["down"]["mass_mev"]
    m_s  = masses["strange"]["mass_mev"]
    m_b  = masses["bottom"]["mass_mev"]

    return {
        "r_lepton_gen2_gen1":   m_mu  / m_e,
        "r_lepton_gen3_gen2":   m_tau / m_mu,
        "r_up_gen2_gen1":       m_c   / m_u,
        "r_up_gen3_gen2":       m_t   / m_c,
        "r_down_gen2_gen1":     m_s   / m_d,
        "r_down_gen3_gen2":     m_b   / m_s,
        "r_quark_su_GTE":       m_s   / m_u,   # m_s/m_u — the θ_P-relevant ratio
        "r_quark_su_PDG_curr":  PDG_CURRENT["strange"] / PDG_CURRENT["up"],
    }

def pdg_comparison(masses):
    """Compare GTE IMT predictions to PDG current and constituent masses."""
    rows = []
    for name, _, _, _, _, _ in PARTICLES:
        m_gte = masses[name]["mass_mev"]
        m_pdg = PDG_CURRENT.get(name)
        if m_pdg is not None:
            err_pct = 100.0 * (m_gte - m_pdg) / m_pdg
        else:
            err_pct = None
        m_cons = PDG_CONSTITUENT.get(name)
        rows.append({
            "name":          name,
            "m_GTE_MeV":     m_gte,
            "m_PDG_curr_MeV":m_pdg,
            "err_curr_pct":  err_pct,
            "m_PDG_cons_MeV":m_cons,
        })
    return rows

def mixing_angle_analysis(masses):
    """
    Assess how r_quark from GTE relates to the mixing angle context.
    Uses the GOR and additive formulas from Rank 124-MIXANGLE.
    """
    m_u = masses["up"]["mass_mev"]
    m_d = masses["down"]["mass_mev"]
    m_s = masses["strange"]["mass_mev"]

    # Rank 124: PDG meson masses
    m_pi   = 134.9768   # MeV  π⁰
    m_K    = 495.6477   # MeV  K⁰ (average K⁰/K⁺)
    m_eta  = 547.862    # MeV  η
    m_etap = 957.78     # MeV  η'(958)

    # Standard θ_P from tan² formula (uses only PDG meson masses — Rank 124)
    m_eta8_sq  = (4*m_K**2 - m_pi**2) / 3.0
    tan2_theta = (m_eta8_sq - m_eta**2) / (m_etap**2 - m_eta8_sq)
    tan_theta  = -math.sqrt(max(tan2_theta, 0.0))
    theta_P_deg = math.degrees(math.atan(tan_theta))

    # GOR relation: self-consistent r from meson masses
    r_GOR = 2*(m_K/m_pi)**2 - 1.0   # ≈ 25.97

    # Additive (naive constituent): m_pi = 2m_u, m_K = m_u + m_s
    m_u_eff_add = m_pi / 2.0
    m_s_eff_add = m_K - m_u_eff_add
    r_add       = m_s_eff_add / m_u_eff_add

    # GTE-derived current mass ratios
    r_su_GTE = m_s / m_u
    r_du_GTE = m_s / m_d

    # ΛQCD scale — current→constituent shift
    lambda_QCD = 250.0   # MeV (approximate)
    m_u_cons_est = m_u + lambda_QCD
    m_d_cons_est = m_d + lambda_QCD
    m_s_cons_est = m_s + lambda_QCD
    r_su_cons_GTE = m_s_cons_est / m_u_cons_est

    return {
        "theta_P_deg":        theta_P_deg,
        "m_eta8_MeV":         math.sqrt(m_eta8_sq),
        "r_GOR":              r_GOR,
        "r_add":              r_add,
        "r_su_GTE_current":   r_su_GTE,
        "r_du_GTE_current":   r_du_GTE,
        "r_su_GTE_constituent_estimate": r_su_cons_GTE,
        "lambda_QCD_assumed": lambda_QCD,
        "r_su_PDG_current":   PDG_CURRENT["strange"] / PDG_CURRENT["up"],
        "r_su_PDG_constituent": PDG_CONSTITUENT["strange"] / PDG_CONSTITUENT["up"],
    }

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 72)
    print("Rank 128-QUARKMASS: GTE quark-sector generation mass ratio")
    print("=" * 72)

    # Sanity check
    print("\n[0] Sanity check (reproduce electron mass before new predictions)...")
    m_e_check = sanity_check_imt()
    print(f"    electron: {m_e_check:.4f} MeV (expected 0.5110 MeV) — PASS")

    # Compute all masses
    print("\n[1] GTE IMT masses for all 9 fundamental fermions:")
    masses = compute_all_masses()

    print(f"\n  {'Particle':<10} {'gen':>4} {'ptype':>12} {'b':>8}  "
          f"{'GTE (MeV)':>12} {'PDG curr (MeV)':>16} {'err%':>8}")
    print("  " + "-" * 72)
    for name, a, b, c, gen, ptype in PARTICLES:
        m_gte = masses[name]["mass_mev"]
        m_pdg = PDG_CURRENT.get(name, float("nan"))
        err   = 100*(m_gte - m_pdg)/m_pdg if m_pdg > 0 else float("nan")
        print(f"  {name:<10} {gen:>4} {ptype:>12} {abs(b):>8}  "
              f"{m_gte:>12.4f} {m_pdg:>16.4f} {err:>8.2f}%")

    # Generation ratios
    print("\n[2] Generation mass ratios by sector:")
    ratios = compute_generation_ratios(masses)
    print(f"\n  Lepton sector  (k=1 cascade):")
    print(f"    r_lepton  = m_μ/m_e    = {ratios['r_lepton_gen2_gen1']:>10.4f}  (PDG: 206.77)")
    print(f"    r_lepton  = m_τ/m_μ    = {ratios['r_lepton_gen3_gen2']:>10.4f}  (PDG: 16.82)")
    print(f"\n  Up-type sector (k=4 cascade):")
    print(f"    r_up      = m_c/m_u    = {ratios['r_up_gen2_gen1']:>10.4f}  (PDG curr: {PDG_CURRENT['charm']/PDG_CURRENT['up']:.1f})")
    print(f"    r_up      = m_t/m_c    = {ratios['r_up_gen3_gen2']:>10.4f}  (PDG curr: {PDG_CURRENT['top']/PDG_CURRENT['charm']:.1f})")
    print(f"\n  Down-type sector (k=5 cascade):")
    print(f"    r_down    = m_s/m_d    = {ratios['r_down_gen2_gen1']:>10.4f}  (PDG curr: {PDG_CURRENT['strange']/PDG_CURRENT['down']:.1f})")
    print(f"    r_down    = m_b/m_s    = {ratios['r_down_gen3_gen2']:>10.4f}  (PDG curr: {PDG_CURRENT['bottom']/PDG_CURRENT['strange']:.1f})")
    print(f"\n  Cross-flavor ratio (for θ_P analysis):")
    print(f"    r_s/u     = m_s/m_u    = {ratios['r_quark_su_GTE']:>10.4f}  (PDG curr: {ratios['r_quark_su_PDG_curr']:.1f})")

    # PDG comparison table
    print("\n[3] PDG constituent mass comparison:")
    comp = pdg_comparison(masses)
    print(f"\n  {'Particle':<10} {'GTE':>10} {'PDG_curr':>10} {'PDG_cons':>10}  Mass type verdict")
    for row in comp:
        if row["m_PDG_cons_MeV"] is not None:
            err_cons = 100*(row["m_GTE_MeV"] - row["m_PDG_cons_MeV"]) / row["m_PDG_cons_MeV"]
            verdict  = "CURRENT (match PDG current)" if abs(row["err_curr_pct"] or 99) < abs(err_cons) else "CONSTITUENT (match PDG constituent)"
            print(f"  {row['name']:<10} {row['m_GTE_MeV']:>10.2f} "
                  f"{row['m_PDG_curr_MeV']:>10.2f} {row['m_PDG_cons_MeV']:>10.2f}  {verdict}")

    # Mixing angle analysis
    print("\n[4] θ_P mixing angle and quark ratio analysis:")
    mix = mixing_angle_analysis(masses)
    print(f"\n  Standard θ_P (PDG meson masses, tan² GMO):  {mix['theta_P_deg']:.2f}°  (PDG: −11.3° to −14.3°)")
    print(f"  r_GOR (GOR quadratic, from π/K masses):    {mix['r_GOR']:.2f}")
    print(f"  r_add (naive additive, constituent):       {mix['r_add']:.2f}")
    print(f"")
    print(f"  GTE IMT gives CURRENT quark masses:")
    print(f"    r_s/u  (GTE current) = {mix['r_su_GTE_current']:.2f}  vs PDG current {mix['r_su_PDG_current']:.1f}")
    print(f"    r_s/d  (GTE current) = {mix['r_du_GTE_current']:.2f}  vs PDG current {PDG_CURRENT['strange']/PDG_CURRENT['down']:.1f}")
    print(f"")
    print(f"  Estimate with ΛQCD ~ {mix['lambda_QCD_assumed']:.0f} MeV chiral shift (current→constituent):")
    print(f"    r_s/u (GTE constituent estimate) = {mix['r_su_GTE_constituent_estimate']:.2f}")
    print(f"    PDG constituent m_s/m_u = {mix['r_su_PDG_constituent']:.2f}")
    print(f"")
    print(f"  Summary: GTE r_down = m_s/m_d = {ratios['r_down_gen2_gen1']:.1f} (down-type generation ratio).")
    print(f"  This is the k=5 sector cascade ratio, distinct from the lepton r = 206.8.")
    print(f"  Ratio r_lepton/r_down = {ratios['r_lepton_gen2_gen1']/ratios['r_down_gen2_gen1']:.1f}x (cf. target ~33x from Rank 124).")
    print(f"")
    print(f"  *** θ_P closure: the meson mixing angle uses EFFECTIVE CONSTITUENT masses ***")
    print(f"  GTE IMT predicts current quark masses. The θ_P-relevant ratio")
    print(f"  (r ≈ 6.34 additive or r ≈ 26 GOR) uses PION/KAON masses which encode")
    print(f"  both current quark masses AND the chiral condensate ~ΛQCD.")
    print(f"  GTE first-principles θ_P requires closing:")
    print(f"    (a) GTE chiral condensate → ΛQCD shift (current→constituent)")
    print(f"    (b) GTE Witten-Veneziano χ_top → η' anomaly mass")
    print(f"  Without (a)+(b), the full θ_P prediction is open.")

    # Build output artifact
    results = {
        "rank": "128-QUARKMASS",
        "date": "2026-05-23",
        "status": "CatA",
        "gte_masses_MeV": {name: masses[name]["mass_mev"] for name, *_ in PARTICLES},
        "pdg_current_MeV": PDG_CURRENT,
        "pdg_constituent_MeV": PDG_CONSTITUENT,
        "generation_ratios": ratios,
        "mixing_angle_analysis": mix,
        "b_values": {
            "lepton": {"electron": 73, "muon": 42, "tau": 275},
            "up_type": {"up": 9, "charm": 275, "top": 337920},
            "down_type": {"down": 5, "strange": 186, "bottom": 8191},
        },
        "key_findings": {
            "r_lepton_gen2_gen1": ratios["r_lepton_gen2_gen1"],
            "r_up_gen2_gen1":     ratios["r_up_gen2_gen1"],
            "r_down_gen2_gen1":   ratios["r_down_gen2_gen1"],
            "r_su_GTE_current":   ratios["r_quark_su_GTE"],
            "r_su_PDG_current":   ratios["r_quark_su_PDG_curr"],
            "gte_gives_current_quark_masses": True,
            "theta_P_from_PDG_meson_masses_deg": mix["theta_P_deg"],
            "gte_theta_P_requires": [
                "GTE chiral condensate (current->constituent mass shift)",
                "GTE Witten-Veneziano chi_top derivation"
            ],
        },
    }

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "rank128_quarkmass_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n[5] Artifact written: {out_path}")
    print(f"\nElapsed: {time.time()-t_start:.1f}s")
    print("=" * 72)

    return results


if __name__ == "__main__":
    main()
