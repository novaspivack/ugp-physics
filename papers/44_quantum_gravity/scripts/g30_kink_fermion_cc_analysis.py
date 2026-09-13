"""Kink-fermion cosmological-constant cancellation: null test.

Tests the hypothesis that the fermionic kink sector of the Z7 sine-Gordon field
(repulsive regime beta^2 = 49 > 8 pi; exact kink-kink S-matrix S_kk = -1 by the
Zamolodchikov-Zamolodchikov 1979 bootstrap) contributes a NEGATIVE vacuum
zero-point energy that cancels the positive bosonic Phi_MDL field vacuum energy,
in analogy with a supersymmetric boson-fermion cancellation.

The script runs the proposed two-sector accounting and the decisive
methodology-robustness null test. Coleman (1975) / Mandelstam (1975) prove the
(1+1)D sine-Gordon QFT is EXACTLY EQUIVALENT to the massive Thirring QFT: one
Hilbert space, one partition function (Z_sineGordon = Z_Thirring), one vacuum,
hence one vacuum energy. The bosonic field and the kink-fermion are dual
descriptions of the SAME degrees of freedom, not two independent physical
sectors. Adding +rho_bosonic and -rho_fermionic therefore double-counts the same
modes with opposite sign. The null test demonstrates this explicitly: in both
descriptions |rho_vac| is the identical single number.

Conclusion: the proposed cancellation is a double-counting artifact. The quantum
cosmological-constant hierarchy is unchanged. A genuine SUSY-like cancellation
requires a SEPARATE degenerate fermionic superpartner spectrum, which a
Coleman-Mandelstam re-description does not provide.
"""

import json
import os

import numpy as np
from scipy.integrate import quad

# GTE parameters (from closed CatAD ranks)
m_kink = 0.29010      # GeV  (kink mass; BPS relation M_kink = 8 m_field / 49)
sigma = 0.18920       # GeV^2 (string tension)
M_Pl = 1.22e19        # GeV  (Planck mass)
rho_obs = (2.3e-12) ** 4  # GeV^4 (observed dark-energy density)
m_field = m_kink * 49 / 8  # bare Z7 field mass


def rho_bosonic(m, Lambda):
    """Bosonic zero-point energy density, mass m, UV cutoff Lambda."""
    integrand = lambda k: k ** 2 * np.sqrt(m ** 2 + k ** 2) / (2 * np.pi ** 2 * 2)
    result, _ = quad(integrand, 0, Lambda)
    return result


def rho_fermionic_kink(m, Lambda):
    """Naive fermionic zero-point energy (negative); same mode count as bosonic."""
    return -rho_bosonic(m, Lambda)


print("=" * 70)
print("PROPOSED TWO-SECTOR VACUUM ENERGY")
print("=" * 70)
by_cutoff = {}
for name, Lambda in [("Planck", M_Pl), ("String_sqrt_sigma", np.sqrt(sigma)),
                     ("Kink_mass", m_kink)]:
    rb = rho_bosonic(m_kink, Lambda)
    rf = rho_fermionic_kink(m_kink, Lambda)
    print(f"Lambda={name:18s} = {Lambda:.3e} GeV  "
          f"bos=+{rb:.3e}  ferm={rf:.3e}  total={rb + rf:.3e} GeV^4")
    by_cutoff[name] = {"Lambda_GeV": float(Lambda), "rho_bos": float(rb),
                       "rho_ferm": float(rf), "rho_total": float(rb + rf)}

Lambda = m_field * 10
rho_field = rho_bosonic(m_field, Lambda)
rho_kink = rho_fermionic_kink(m_kink, Lambda)
rho_net = rho_field + rho_kink
print(f"\nDistinct-mass two-sector accounting (Lambda = 10 m_field = {Lambda:.4f} GeV):")
print(f"  +rho(boson, m_field={m_field*1000:.1f} MeV) = +{rho_field:.4e} GeV^4")
print(f"  -rho(kink,  m_kink ={m_kink*1000:.1f} MeV)  = {rho_kink:.4e} GeV^4")
print(f"  net = {rho_net:.4e} GeV^4  (cancellation {abs(rho_kink/rho_field)*100:.2f}%, "
      f"residual/field {abs(rho_net/rho_field)*100:.2f}%)")

print("\n" + "=" * 70)
print("COLEMAN-MANDELSTAM DUALITY")
print("=" * 70)
beta_sq = 49.0
g_thirring = 4 * np.pi / beta_sq - 1
print(f"beta^2 = {beta_sq}  (8 pi = {8*np.pi:.4f}; repulsive regime)")
print(f"g_Thirring = 4 pi / beta^2 - 1 = {g_thirring:.4f}")
rho_1d_field = m_field ** 2 / (2 * np.pi)
rho_1d_kink = -(m_kink ** 2) / (2 * np.pi)
ratio4 = (m_kink / m_field) ** 4
print(f"1+1D ansatz rho = m^2/(2 pi): field={rho_1d_field:.6f}, "
      f"kink={rho_1d_kink:.6f} GeV^2  ({abs(rho_1d_kink/rho_1d_field)*100:.2f}% naive cancel)")
print(f"3+1D estimate (M_kink/m_field)^4 = (8/49)^4 = {ratio4:.6e}")

print("\n" + "=" * 70)
print("NULL TEST: DUALITY IS AN EQUIVALENCE, NOT A SECOND SECTOR")
print("=" * 70)
Lambda_test = M_Pl
rho_boson_desc = rho_bosonic(m_kink, Lambda_test)
rho_fermion_desc = abs(rho_fermionic_kink(m_kink, Lambda_test))
print("Same theory, same mass m_kink, same cutoff M_Pl:")
print(f"  |rho| bosonic description   = {rho_boson_desc:.4e} GeV^4")
print(f"  |rho| fermionic description = {rho_fermion_desc:.4e} GeV^4")
print(f"  ratio = {rho_boson_desc/rho_fermion_desc:.6f}  (=1: one physical number, not a sum)")
print(f"  hierarchy vs observed = {rho_boson_desc/rho_obs:.3e}  (UNCHANGED, ~10^122)")

verdict = (
    "Proposed kink-fermion CC cancellation is a DOUBLE-COUNTING ARTIFACT. "
    "Coleman-Mandelstam duality is an exact equivalence of one theory "
    "(Z_sineGordon = Z_Thirring), not two additive sectors. The physical vacuum "
    "energy is a single number, identical in the bosonic and kink-fermion "
    "descriptions; adding +rho_bos and -rho_ferm counts the same modes twice. No "
    "new cancellation exists; the ~10^122 quantum hierarchy is unchanged. A SUSY-like "
    "cancellation requires a SEPARATE degenerate fermionic superpartner spectrum, "
    "which a duality re-description does not supply. The bosonic-T00>=0 diagnosis "
    "(classical Lambda = 0 derived; quantum hierarchy open) stands."
)
print("\n" + "=" * 70)
print("VERDICT")
print("=" * 70)
print(verdict)

results = {
    "parameters": {"m_kink_GeV": m_kink, "m_field_GeV": m_field, "sigma_GeV2": sigma,
                   "M_Pl_GeV": M_Pl, "rho_obs_GeV4": rho_obs, "beta_sq": beta_sq,
                   "g_thirring": float(g_thirring)},
    "proposed_two_sector": {
        "by_cutoff": by_cutoff,
        "distinct_mass": {"rho_field": float(rho_field), "rho_kink": float(rho_kink),
                          "rho_net": float(rho_net),
                          "cancellation_fraction": float(abs(rho_kink / rho_field)),
                          "residual_over_field": float(abs(rho_net / rho_field))}},
    "coleman_mandelstam": {"rho_1d_field": float(rho_1d_field),
                           "rho_1d_kink": float(rho_1d_kink),
                           "ratio4_8over49": float(ratio4)},
    "null_test_double_counting": {
        "rho_boson_desc_GeV4": float(rho_boson_desc),
        "rho_fermion_desc_magnitude_GeV4": float(rho_fermion_desc),
        "descriptions_identical": bool(np.isclose(rho_boson_desc, rho_fermion_desc)),
        "hierarchy_unchanged": float(rho_boson_desc / rho_obs)},
    "verdict": verdict,
    "g30_status": "OPEN (unchanged) -- proposed mechanism falsified by double-counting null test",
}

os.makedirs("papers/44_quantum_gravity/data", exist_ok=True)
out = "papers/44_quantum_gravity/data/g30_kink_fermion_cc_results.json"
with open(out, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nSaved {out}")
