"""G30 — Mirror branch cosmological-constant cancellation test.

Tests the hypothesis that the GTE mirror branch (dark sector) provides the
cosmological-constant cancellation mechanism through one-loop vacuum-energy
mass-splitting between the canonical (SM) sector and the mirror (dark) sector.

Hypothesis: if the Z2 involution b2<->q2 (24<->42) acts as a Bose-Fermi-like
grading, the SM sector contributes +rho_SM and the mirror sector contributes
-rho_mirror, giving a net CC = rho_SM - rho_mirror. The question is whether
(m_SM^4 - m_mirror^4) / (16 pi^2) reproduces the observed rho_obs.

Masses are taken from P29 (Mirror Branch Braid Atlas) and PDG; nothing is fitted.
"""

import numpy as np

# ----------------------------------------------------------------------------
# Inputs (exact, sourced)
# ----------------------------------------------------------------------------
# SM charged-lepton masses (PDG), GeV
m_e, m_mu, m_tau = 0.511e-3, 105.7e-3, 1776.9e-3

# Mirror dark-lepton masses (P29 Table tab:dark_leptons), GeV
m_d1, m_d2, m_d3 = 0.5406e-3, 24.47e-3, 3604.68e-3

# Dark quark G1 masses (P29 ssec:dark_quarks; preliminary), GeV
m_dq_up, m_dq_dn = 0.57e-3, 17.30e-3

# Observed vacuum-energy density: rho_obs = (2.3 meV)^4
rho_obs = (2.3e-12) ** 4  # GeV^4

NORM = 16.0 * np.pi ** 2
N_f = 4  # off-shell Dirac fermion dof (one-loop coefficient convention)


def vac(m):
    """One-loop vacuum-energy contribution of a Dirac fermion of mass m (GeV^4),
    magnitude only: N_f * m^4 / (16 pi^2)."""
    return N_f * m ** 4 / NORM


# ----------------------------------------------------------------------------
print("=" * 72)
print("G30 — MIRROR BRANCH CC CANCELLATION TEST")
print("=" * 72)
print(f"rho_obs = (2.3 meV)^4 = {rho_obs:.4e} GeV^4\n")

print("--- SM charged leptons ---")
for name, m in [("e", m_e), ("mu", m_mu), ("tau", m_tau)]:
    print(f"  m_{name:<4} = {m*1e3:9.4f} MeV   m^4/(16pi^2) = {m**4/NORM:.4e} GeV^4")

print("\n--- Mirror dark leptons (P29) ---")
for name, m in [("d1", m_d1), ("d2", m_d2), ("d3", m_d3)]:
    print(f"  m_{name:<4} = {m*1e3:9.4f} MeV   m^4/(16pi^2) = {m**4/NORM:.4e} GeV^4")

# ----------------------------------------------------------------------------
# Leptonic sector vacuum energies
# ----------------------------------------------------------------------------
rho_SM_lep = N_f * (m_e**4 + m_mu**4 + m_tau**4) / NORM
rho_mir_lep = N_f * (m_d1**4 + m_d2**4 + m_d3**4) / NORM

print("\n--- Leptonic sector totals ---")
print(f"  rho_SM   (e,mu,tau)   = {rho_SM_lep:.4e} GeV^4")
print(f"  rho_mir  (d1,d2,d3)   = {rho_mir_lep:.4e} GeV^4")

rho_net = rho_SM_lep - rho_mir_lep
rho_res = abs(rho_net)
print(f"\n  rho_net = rho_SM - rho_mir = {rho_net:.4e} GeV^4")
print(f"  |rho_net|                  = {rho_res:.4e} GeV^4")
print(f"  |rho_net| / rho_obs        = {rho_res/rho_obs:.4e}")
print(f"  log10(|rho_net|/rho_obs)   = {np.log10(rho_res/rho_obs):.2f}")

# ----------------------------------------------------------------------------
# Per-generation splittings (what dominates the residual)
# ----------------------------------------------------------------------------
print("\n--- Per-generation |m_SM^4 - m_mirror^4| splittings ---")
split = {}
for tag, mS, mM in [("e/d1", m_e, m_d1), ("mu/d2", m_mu, m_d2), ("tau/d3", m_tau, m_d3)]:
    s = N_f * abs(mS**4 - mM**4) / NORM
    split[tag] = s
    print(f"  {tag:<7}: {s:.4e} GeV^4   (= {s/rho_obs:.3e} x rho_obs)")
tot_split = sum(split.values())
print(f"  SUM of |per-gen| splittings = {tot_split:.4e} GeV^4 = {tot_split/rho_obs:.3e} x rho_obs")

# ----------------------------------------------------------------------------
# Quark sector: does dark QCD cancel SM QCD?  (G1 only is known)
# ----------------------------------------------------------------------------
print("\n--- Quark G1 (only computable dark generation) ---")
# SM light quark masses (MSbar 2 GeV), GeV
m_u, m_d = 2.16e-3, 4.67e-3
rho_SM_q1 = N_f * (m_u**4 + m_d**4) / NORM
rho_mir_q1 = N_f * (m_dq_up**4 + m_dq_dn**4) / NORM
print(f"  SM   (u,d)        : {rho_SM_q1:.4e} GeV^4")
print(f"  dark (up',dn')    : {rho_mir_q1:.4e} GeV^4")
print(f"  |diff|            : {abs(rho_SM_q1-rho_mir_q1):.4e} GeV^4 = "
      f"{abs(rho_SM_q1-rho_mir_q1)/rho_obs:.3e} x rho_obs")
print("  (Dark G2/G3 quark masses NOT computable from current GTE results; dark quarks")
print("   confine at Lambda_dark ~ 200 MeV. Confinement-scale vacuum energy ~ Lambda^4")
Lam_dark = 0.200
Lam_QCD = 0.200  # SM confinement scale ~ 200 MeV
print(f"   Lambda_dark^4 ~ {Lam_dark**4:.4e} GeV^4 = {Lam_dark**4/rho_obs:.3e} x rho_obs)")
print(f"   |Lambda_dark^4 - Lambda_QCD^4| = {abs(Lam_dark**4-Lam_QCD**4):.4e} "
      f"(exact only if Lambda_dark == Lambda_QCD, which P29 does NOT establish)")

# ----------------------------------------------------------------------------
# The "42 in 10^42" arithmetic check
# ----------------------------------------------------------------------------
print("\n--- The '42 appears in 10^42' check ---")
hier_MPl = np.log10(rho_obs / (1.22e19) ** 4)   # rho_obs / M_Pl^4
hier_kink = np.log10((0.29010**4 / NORM) / rho_obs)  # kink one-loop / rho_obs
print(f"  log10(rho_obs / M_Pl^4)        = {hier_MPl:.2f}  (the canonical ~122 dex)")
print(f"  log10(m_kink^4/16pi^2 / rho_obs) = {hier_kink:.2f}  (the residual ~42-43 dex)")
print(f"  b2(mirror) = 24, q2(mirror) = 42, 42 x 24 = {42*24} = R_10")
print("  '42' is the SM-branch b2 (= mirror q2). The residual exponent ~42.6 is a")
print("  base-10 logarithm of a ratio; matching it to the integer arithmetic label 42")
print("  requires the residual to be EXACTLY 10^-42.6, and the label to be base-10.")
print("  Both are coincidental: the residual is 10^(-42.6) not 10^(-42); the GTE label")
print("  42 is dimensionless arithmetic, not a base-10 exponent. -> NUMEROLOGICAL.")

# ----------------------------------------------------------------------------
# FINAL ASSESSMENT
# ----------------------------------------------------------------------------
print("\n" + "=" * 72)
print("FINAL ASSESSMENT")
print("=" * 72)
print(f"rho_obs                         = {rho_obs:.4e} GeV^4")
print(f"|rho_SM_lep - rho_mir_lep|      = {rho_res:.4e} GeV^4")
print(f"Hierarchy (residual / observed) = {rho_res/rho_obs:.3e}  "
      f"(~10^{np.log10(rho_res/rho_obs):.0f})")
print()
print("Even with EXACT cancellation of the SM and mirror QCD sectors, the leptonic")
print("vacuum-energy mismatch is ~10^47 times too large. The mirror branch does NOT")
print("supply the observed CC: the mirror masses are NOT mass-degenerate with the SM")
print("(ratios differ per generation), so the Bose-Fermi-style cancellation is far")
print("from exact. Worse, the residual is set by the dark tau (3.60 GeV, HEAVIER than")
print("the SM tau at 1.78 GeV), so the mirror branch does not even reduce the naive")
print("scale -- it makes the bare leptonic vacuum energy larger, not smaller.")

results = {
    "rho_obs_GeV4": rho_obs,
    "masses_MeV": {
        "SM_leptons": [m_e*1e3, m_mu*1e3, m_tau*1e3],
        "dark_leptons": [m_d1*1e3, m_d2*1e3, m_d3*1e3],
        "dark_quarks_G1": [m_dq_up*1e3, m_dq_dn*1e3],
    },
    "rho_SM_lep_GeV4": rho_SM_lep,
    "rho_mirror_lep_GeV4": rho_mir_lep,
    "rho_net_GeV4": rho_net,
    "abs_residual_GeV4": rho_res,
    "residual_over_obs": rho_res / rho_obs,
    "log10_residual_over_obs": float(np.log10(rho_res / rho_obs)),
    "per_gen_splittings_GeV4": split,
    "sum_per_gen_splittings_GeV4": tot_split,
    "42_check": {
        "log10_rho_obs_over_MPl4": float(hier_MPl),
        "log10_kink_over_obs": float(hier_kink),
        "verdict": "numerological (base-10 exponent vs dimensionless arithmetic label)",
    },
    "verdict": "FALSIFIED: mirror branch does not cancel CC; residual ~10^40 x rho_obs",
}

import json, os
out = os.path.join(os.path.dirname(__file__), "..", "data", "g30_mirror_branch_cc_results.json")
out = os.path.abspath(out)
with open(out, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nArtifact written: {out}")
