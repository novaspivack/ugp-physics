# GTE Novel-Particle Search Results — Combined Laboratory Dark Photon Limits
Date: 2026-05-11
Source: cajohare/AxionLimits, DP_Combined_Laboratory.txt
(Envelope of all published laboratory dark photon / hidden photon exclusion limits)

## Critical Context

The GTE framework predicts particle MASSES and STABILITY but does not yet specify
a production coupling. The exclusion limits below apply to kinetically mixed dark
photons (coupling via ε to the SM photon). If GTE particles are:
  • Kinetically mixed at ε² > limit → EXCLUDED
  • Purely gravitationally coupled (no kinetic mixing) → OPEN (invisible to current searches)
  • GTE-P7 is Lean-certified Q=0, colour-singlet → if electrically neutral, couples only
    gravitationally or via exotic portals → likely OPEN at current sensitivity

## Exclusion Limits at GTE Predicted Masses

| GTE ID | Mass (MeV) | ε² exclusion (90% CL) | ε exclusion | Status | Note |
|--------|-----------|----------------------|------------|--------|------|
| GTE-P1 | 2.97 | ε² < 2.568e-07 | ε < 5.067e-04 | OPEN (if only grav. coupled) | Isolated; highest stability score |
| GTE-P5 | 21.0 | ε² < 2.568e-07 | ε < 5.067e-04 | OPEN (if only grav. coupled) | Electron trajectory multiplicity |
| GTE-P6 | 30.9 | ε² < 2.568e-07 | ε < 5.067e-04 | OPEN (if only grav. coupled) | 3-member band (29-33 MeV) |
| GTE-P2 | 107.4 | ε² < 2.568e-07 | ε < 5.067e-04 | OPEN (if only grav. coupled) | Isolated |
| GTE-P4 | 137.0 | ε² < 2.568e-07 | ε < 5.067e-04 | OPEN (if only grav. coupled) | Muon trajectory multiplicity |
| GTE-P7 | 212.0 | ε² < 2.568e-07 | ε < 5.067e-04 | OPEN (if only grav. coupled) | ★ HIGHEST PRIORITY — SM-D1 cross-paper;  |
| GTE-P8 | 298.0 | ε² < 2.568e-07 | ε < 5.067e-04 | OPEN (if only grav. coupled) | 2-member cluster |
| GTE-P9 | 561.0 | ε² < 2.568e-07 | ε < 5.067e-04 | OPEN (if only grav. coupled) | Charm/tau trajectory multiplicity |
| GTE-P3 | 801.3 | ε² < 2.568e-07 | ε < 5.067e-04 | OPEN (if only grav. coupled) | 4-member band (796-850 MeV) |
| GTE-P10 | 1100.2 | ε² < 3.641e-05 | ε < 6.034e-03 | OPEN (if only grav. coupled) | ★ XP-02: cross-paper charm-adjacent |
| GTE-P11 | 1600.0 | ε² < 3.459e-05 | ε < 5.881e-03 | OPEN (if only grav. coupled) | ★ XP-03: cross-paper tau-adjacent |

## Interpretation

**For masses 3 MeV – 1 GeV (GTE-P1 through GTE-P9):**
  Combined laboratory limit: ε² < 2.568×10⁻⁷ (ε < 5.07×10⁻⁴)
  Source: NA48/2, NA64, BaBar, Belle, KLOE-2, LHCb combined envelope
  → IF GTE particles couple via kinetic mixing at EM strength (ε ~ 10⁻³), they are EXCLUDED
  → IF they have no kinetic mixing (ε = 0), they are OPEN — no current search can see them

**For masses 1100-1900 MeV (GTE-P10, GTE-P11):**
  Combined laboratory limit: ε² < ~3.4-3.6×10⁻⁵ (ε < ~5.9×10⁻³)
  Weaker exclusion due to fewer experiments in this mass range
  Same open/excluded interpretation applies

**GTE-P7 (212 MeV) — Special Case:**
  This is the highest-priority prediction (two independent UGP pathways agree).
  Lean-certified: Q=0, colour-singlet (gte_p7_quantum_numbers_neutral).
  A Q=0 colour-singlet couples to SM only via gravity or exotic portals, NOT kinetic mixing.
  → For GTE-P7 specifically: existing dark photon searches are NOT sensitive.
  → The appropriate search is MISSING ENERGY at e+e- colliders (BaBar, Belle II).
  → Belle II with 50 ab⁻¹ plans a dedicated single-photon search at this mass.
  → Current BaBar single-photon limit (arXiv:1702.03327): covers 200 MeV range
     but is interpreted for kinetically mixed dark photon, not gravitational coupling.

## Key Question for P02 Paper Authors

The GTE novel-particle search strategy REQUIRES specifying the production mechanism.
Specifically: what portal couples GTE stable particles to SM matter in a collider?
If the coupling is purely gravitational (Planck-suppressed), current colliders cannot
produce or detect them regardless of mass. The exclusion limits above are irrelevant
in that case. This is the critical open question for the particle search program.

## Data Source
  Repository: https://github.com/cajohare/AxionLimits
  File: limit_data/DarkPhoton/DP_Combined_Laboratory.txt
  Reference: C. O'Hare, AxionLimits (2020-2026)