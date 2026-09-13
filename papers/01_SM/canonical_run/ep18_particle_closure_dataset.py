"""
Reference particle data table used in the closure analysis.

**Tracked mirror** of the closure-handoff package `handoff/data/particle_data.py` for
repository reproducibility (`specs/` is git‑ignored upstream). Sync from the
unpack of `closure_handoff.zip` when the handoff particle table updates.

Canonical triples align with Paper 01 Appendix A Table 12 (see paper tex).


This file is a self-contained extract of the data used. The receiving agent
should compare against ugp-physics's canonical particle data and verify
consistency.

For each particle:
  - canonical triple (a, b, c; g) from P01 Table 12 / Appendix A
  - constituent quark/lepton list (for composite RC computation)
  - mass (GeV) — PDG central value
  - width (GeV) or lifetime (s) — PDG dominant decay
  - dominant decay class — strong, EM, EM_strong, weak, EW
  - decay-product structure — for RC and self-adjudication

Format:
  PARTICLE = {
    "name": {
      "triple": (a, b, c, g) or None,
      "constituents": ["quark1", "quark2", ...] or ["self"] for elementary,
      "mass_GeV": M,
      "width_GeV": Gamma or None,
      "lifetime_s": tau or None,
      "decay_class": "strong"/"EM"/"EM_strong"/"weak"/"EW",
      "products_rest_mass_GeV": Σm_products in dominant channel,
      "dominant_BR": branching fraction,
    }
  }
"""

# Canonical triples for fundamental fermions (P01 Table 12)
TRIPLES = {
    "e":      (1,    73,    823,    1),
    "mu":     (9,    42,    1023,   2),
    "tau":    (5,    275,   65535,  3),
    "u":      (5,    9,     275,    1),
    "c":      (5,    275,   65535,  2),
    "t":      (76,   337920, -1,    3),  # Note: c = -1 needs special handling
    "d":      (9,    5,     42,     1),
    "s":      (9,    186,   1023,   2),
    "b":      (5,    8191,  65535,  3),
    "nu_e":   (1,    1,     823,    1),
    "nu_mu":  (9,    1,     1023,   2),
    "nu_tau": (5,    1,     65535,  3),
    # Right-handed neutrinos (Type-I seesaw construction):
    "nu_e_R":   (2,  5,  5,   1),
    "nu_mu_R":  (7,  11, 13,  2),
    "nu_tau_R": (17, 19, 23,  3),
}

# Quark current masses (PDG MS-bar at 2 GeV)
QUARK_MASS_GeV = {
    "u": 0.00216, "d": 0.00467, "s": 0.0934,
    "c": 1.275,   "b": 4.18,    "t": 172.69,
}

# Lepton physical masses
LEPTON_MASS_GeV = {
    "e": 0.000510999,
    "mu": 0.105658,
    "tau": 1.77686,
}

# Particle data: composites and elementary
# Format: name -> dict with mass_GeV, width_GeV (or lifetime_s), decay_class,
# constituents, products_rest_mass_GeV (for dominant channel), BR
PARTICLE_DATA = {
    # Elementary - leptons
    "e":   {"M": 0.000511, "constituents": ["e"],   "decay_class": "stable"},
    "mu":  {"M": 0.10566,  "constituents": ["mu"],  "lifetime_s": 2.1969e-6,
            "decay_class": "weak", "products_M": 0.000511, "BR": 1.0},
    "tau": {"M": 1.77686,  "constituents": ["tau"], "lifetime_s": 2.903e-13,
            "decay_class": "weak", "products_M": 0.10566, "BR": 0.1739},

    # Elementary - quarks
    "t":   {"M": 172.69, "constituents": ["t"], "width_GeV": 1.42,
            "decay_class": "weak", "products_M": 80.377+4.18, "BR": 1.0},

    # Light pseudoscalar mesons
    "pi+": {"M": 0.13957, "constituents": ["u","d_bar"], "lifetime_s": 2.6033e-8,
            "decay_class": "weak", "products_M": 0.10566, "BR": 0.99988},
    "pi0": {"M": 0.13498, "constituents": ["u","u_bar"], "lifetime_s": 8.43e-17,
            "decay_class": "EM", "products_M": 0.0, "BR": 0.98823},
    "K+":  {"M": 0.49368, "constituents": ["u","s_bar"], "lifetime_s": 1.2380e-8,
            "decay_class": "weak", "products_M": 0.10566, "BR": 0.6356},
    "K0_S":{"M": 0.49761, "constituents": ["d","s_bar"], "lifetime_s": 8.954e-11,
            "decay_class": "weak", "products_M": 0.27914, "BR": 0.6920},
    "K0_L":{"M": 0.49761, "constituents": ["d","s_bar"], "lifetime_s": 5.116e-8,
            "decay_class": "weak", "products_M": 0.41412, "BR": 0.4055},
    "eta": {"M": 0.54786, "constituents": ["u","u_bar"], "width_GeV": 1.31e-6,
            "decay_class": "EM", "products_M": 0.0, "BR": 0.3941},
    "eta_prime":{"M": 0.95778,"constituents":["u","u_bar"],"width_GeV": 1.96e-4,
            "decay_class": "EM_strong", "products_M": 0.41412, "BR": 0.292},

    # Light vector mesons
    "rho":      {"M": 0.77526, "constituents": ["u","d_bar"], "width_GeV": 0.1474,
                 "decay_class": "strong", "products_M": 0.27914, "BR": 1.0},
    "omega":    {"M": 0.78266, "constituents": ["u","u_bar"], "width_GeV": 0.00868,
                 "decay_class": "strong", "products_M": 0.41412, "BR": 0.892},
    "phi":      {"M": 1.01946, "constituents": ["s","s_bar"], "width_GeV": 0.00425,
                 "decay_class": "strong", "products_M": 0.98736, "BR": 0.492},
    "K*(892)":  {"M": 0.89167, "constituents": ["u","s_bar"], "width_GeV": 0.0514,
                 "decay_class": "strong", "products_M": 0.63325, "BR": 1.0},
    "f0(500)":  {"M": 0.475,   "constituents": ["u","u_bar"], "width_GeV": 0.55,
                 "decay_class": "strong", "products_M": 0.27914, "BR": 1.0},
    "a1(1260)": {"M": 1.230,   "constituents": ["u","d_bar"], "width_GeV": 0.42,
                 "decay_class": "strong", "products_M": 0.91483, "BR": 0.604},
    "f2(1270)": {"M": 1.275,   "constituents": ["u","u_bar"], "width_GeV": 0.187,
                 "decay_class": "strong", "products_M": 0.27914, "BR": 0.842},

    # Heavy mesons
    "D0":   {"M": 1.86484, "constituents": ["c","u_bar"], "lifetime_s": 4.10e-13,
             "decay_class": "weak", "products_M": 0.63325, "BR": 0.0395},
    "D+":   {"M": 1.86966, "constituents": ["c","d_bar"], "lifetime_s": 1.040e-12,
             "decay_class": "weak", "products_M": 0.63718, "BR": 0.0938},
    "Ds+":  {"M": 1.96835, "constituents": ["c","s_bar"], "lifetime_s": 5.04e-13,
             "decay_class": "weak", "products_M": 0.41412, "BR": 0.0537},
    "B0":   {"M": 5.27966, "constituents": ["b","d_bar"], "lifetime_s": 1.519e-12,
             "decay_class": "weak", "products_M": 2.00441, "BR": 0.1041},
    "B+":   {"M": 5.27934, "constituents": ["b","u_bar"], "lifetime_s": 1.638e-12,
             "decay_class": "weak", "products_M": 1.86966, "BR": 0.1099},
    "Bs0":  {"M": 5.36692, "constituents": ["b","s_bar"], "lifetime_s": 1.521e-12,
             "decay_class": "weak", "products_M": 2.10792, "BR": 0.0962},

    # Charmonium/bottomonium
    "J/psi":   {"M": 3.0969,  "constituents": ["c","c_bar"], "width_GeV": 9.29e-5,
                "decay_class": "EM_strong", "products_M": 0.41871, "BR": 0.0593},
    "psi(2S)": {"M": 3.6861,  "constituents": ["c","c_bar"], "width_GeV": 2.94e-4,
                "decay_class": "strong", "products_M": 3.37604, "BR": 0.341},
    "Y(1S)":   {"M": 9.4603,  "constituents": ["b","b_bar"], "width_GeV": 5.402e-5,
                "decay_class": "EM_strong", "products_M": 0.0, "BR": 0.0248},
    "Y(2S)":   {"M": 10.0233, "constituents": ["b","b_bar"], "width_GeV": 3.198e-5,
                "decay_class": "strong", "products_M": 9.73944, "BR": 0.180},
    "Y(3S)":   {"M": 10.3552, "constituents": ["b","b_bar"], "width_GeV": 2.032e-5,
                "decay_class": "strong", "products_M": 10.30244, "BR": 0.0626},

    # Light baryons
    "p":      {"M": 0.93827, "constituents": ["u","u","d"], "decay_class": "stable"},
    "n":      {"M": 0.93957, "constituents": ["u","d","d"], "lifetime_s": 879.4,
               "decay_class": "weak", "products_M": 0.93878, "BR": 1.0},
    "Lambda": {"M": 1.11568, "constituents": ["u","d","s"], "lifetime_s": 2.632e-10,
               "decay_class": "weak", "products_M": 1.07784, "BR": 0.639},
    "Sigma+": {"M": 1.18937, "constituents": ["u","u","s"], "lifetime_s": 8.018e-11,
               "decay_class": "weak", "products_M": 1.07325, "BR": 0.516},
    "Sigma-": {"M": 1.19745, "constituents": ["d","d","s"], "lifetime_s": 1.479e-10,
               "decay_class": "weak", "products_M": 1.07914, "BR": 0.999},
    "Xi0":    {"M": 1.31486, "constituents": ["u","s","s"], "lifetime_s": 2.90e-10,
               "decay_class": "weak", "products_M": 1.25066, "BR": 0.9952},
    "Xi-":    {"M": 1.32171, "constituents": ["d","s","s"], "lifetime_s": 1.639e-10,
               "decay_class": "weak", "products_M": 1.25525, "BR": 0.9989},
    "Omega-": {"M": 1.67245, "constituents": ["s","s","s"], "lifetime_s": 8.21e-11,
               "decay_class": "weak", "products_M": 1.60936, "BR": 0.678},
    "Lambda_c":{"M": 2.28646, "constituents": ["u","d","c"], "lifetime_s": 2.024e-13,
                "decay_class": "weak", "products_M": 1.57152, "BR": 0.0628},

    # Excited baryons
    "Delta":   {"M": 1.232, "constituents": ["u","u","u"], "width_GeV": 0.117,
                "decay_class": "strong", "products_M": 1.07784, "BR": 1.0},
    "N(1440)": {"M": 1.44,  "constituents": ["u","u","d"], "width_GeV": 0.35,
                "decay_class": "strong", "products_M": 1.07784, "BR": 0.65},
    "Sig(1385)":{"M": 1.385,"constituents": ["u","d","s"], "width_GeV": 0.036,
                 "decay_class": "strong", "products_M": 1.25525, "BR": 0.870},
    "Lam(1405)":{"M": 1.405,"constituents": ["u","d","s"], "width_GeV": 0.0505,
                 "decay_class": "strong", "products_M": 1.25525, "BR": 1.0},

    # Electroweak bosons
    "W": {"M": 80.377, "constituents": ["W"], "width_GeV": 2.085,
          "decay_class": "weak", "products_M": 0.10566, "BR": 0.1063},
    "Z": {"M": 91.1876, "constituents": ["Z"], "width_GeV": 2.4952,
          "decay_class": "weak", "products_M": 0.21132, "BR": 0.03366},
    "H": {"M": 125.25, "constituents": ["H"], "width_GeV": 0.0041,
          "decay_class": "EW", "products_M": 8.36, "BR": 0.582},
}


# Constants
HBAR_eVs = 6.582119569e-16  # eV·s


def compute_RC(name):
    """Reflexive closure: (M - Σ constituent rest masses) / M.

    For elementary particles, RC = 0 (they are their own constituent).
    For composites, RC measures the fraction of mass that is internally
    generated by binding/dynamics rather than imposed by constituent
    rest masses.
    """
    if name not in PARTICLE_DATA:
        return None
    p = PARTICLE_DATA[name]
    M = p["M"]
    consts = p["constituents"]
    if len(consts) == 1 and consts[0] == name:
        return 0.0  # elementary
    sum_M = 0.0
    for c in consts:
        # Get mass of constituent
        c_clean = c.replace("_bar", "")
        if c_clean in QUARK_MASS_GeV:
            sum_M += QUARK_MASS_GeV[c_clean]
        elif c_clean in LEPTON_MASS_GeV:
            sum_M += LEPTON_MASS_GeV[c_clean]
        elif c in PARTICLE_DATA:
            sum_M += PARTICLE_DATA[c]["M"]
        # else: 0 (e.g., bosons)
    return max(0.0, (M - sum_M) / M)


def compute_log_c_for_composite(name, rule="heaviest_constituent"):
    """Composite-triple assignment for c-component.

    Default rule: take the c-value of the heaviest constituent.
    Alternative rules to consider:
      - product of constituent c-values
      - sum of constituent c-values
      - some braid-cobordism-derived rule from P23
    """
    if name in TRIPLES:
        a, b, c, g = TRIPLES[name]
        return c if c > 0 else None  # handle top's c = -1 separately
    if name not in PARTICLE_DATA:
        return None
    consts = PARTICLE_DATA[name]["constituents"]
    if rule == "heaviest_constituent":
        masses = []
        for c in consts:
            c_clean = c.replace("_bar", "")
            m = QUARK_MASS_GeV.get(c_clean) or LEPTON_MASS_GeV.get(c_clean) or 0
            masses.append((c_clean, m))
        if not masses:
            return None
        heaviest = max(masses, key=lambda x: x[1])[0]
        if heaviest in TRIPLES:
            _, _, c_val, _ = TRIPLES[heaviest]
            return c_val if c_val > 0 else None
    return None


if __name__ == "__main__":
    # Sanity check
    print("Particles in PARTICLE_DATA:", len(PARTICLE_DATA))
    print("Particles in TRIPLES:", len(TRIPLES))
    print()
    print("RC values for selected particles:")
    for name in ["p", "n", "pi+", "K+", "B0", "J/psi", "Y(1S)", "mu", "tau",
                 "Lambda", "Omega-"]:
        rc = compute_RC(name)
        c = compute_log_c_for_composite(name)
        print(f"  {name:10s}  RC = {rc:.3f}  c = {c}")
