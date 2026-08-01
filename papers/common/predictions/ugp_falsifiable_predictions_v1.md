# UGP Physics Corpus — Falsifiable Predictions Registry

**Version:** v1 (immutable)
**Registry date:** 2026-07-04
**Author:** Nova Spivack
**Repository:** ugp-physics (github.com/novaspivack/ugp-physics)

---

## Purpose

This file is a pre-registered, SHA-256-committed record of falsifiable predictions from
the Universal Generative Principle (UGP) / Generative Triple Evolution (GTE) physics
corpus. Every entry describes a quantity that was not yet measured or definitively
decided at the registry date. Retrodictions of already-measured values are excluded.

The SHA-256 hash of this file (UTF-8, LF line endings, no trailing whitespace) is
recorded in the companion file `ugp_falsifiable_predictions_v1.sha256`. The hash
cannot live inside the hashed artifact; it lives in the separate companion file.

---

## Versioning Policy

v1 is committed once and never modified. If a correction or addition is required, a
new file `ugp_falsifiable_predictions_v2.md` is created following the same commitment
procedure. v1 is never deleted. This policy follows the same immutability convention
as database migration files: once committed, the version is fixed.

---

## Verification

To verify the integrity of this file:

```
python3 papers/common/predictions/verify_predictions_hash.py
```

The script recomputes the SHA-256 of this file and compares it to the hash stored in
`ugp_falsifiable_predictions_v1.sha256`. Exit code 0 = verified; exit code 1 = mismatch.

---

## Claim-Strength Taxonomy

| Label  | Meaning |
|--------|---------|
| CatAL  | Machine-verified in Lean 4, zero sorry (strongest) |
| CatA   | Analytically derived; no Lean certificate |
| CatAD  | Derived, conditional on an open structural axiom |

Only CatAL and CatA entries appear in the physics-sector predictions (entries 1–6).
CatAD entries (novel particle masses) are included with the open axiom stated.

---

## Prediction Entries

### Physics-sector predictions

| # | Quantity | Predicted value | Derivation source | Deciding experiment | Falsification condition | Cat |
|---|----------|----------------|-------------------|---------------------|------------------------|-----|
| 1 | Neutrino mass ordering | Normal Ordering (NO): m_v1 < m_v2 < m_v3 | P55 §7, P21; `seesaw_normal_ordering_from_seed_ordering` in SeesawTrialityPinning.lean; b_R1=5 < b_R2=11 < b_R3=19, strict monotonicity of x^(29/9) | JUNO (~2027); T2K/NOvA atmospheric | Inverted Ordering (IO) confirmed at >3σ by any experiment | CatAL |
| 2 | Neutrino mass sum Σm_v | 59.4 meV | P21, P47; GTE seesaw m_{v,k} = C · b_{R,k}^(29/9), M_R = 1.11×10^13 GeV; SeesawNumericalCerts.lean; script neutrino_mass_prediction.py | CMB-S4 + Euclid (forecast σ(Σm_v) ~ 20 meV) | Σm_v < 30 meV or Σm_v > 100 meV at 3σ | CatA |
| 3 | Individual neutrino masses {m_v1, m_v2, m_v3} | {0.679, 8.61, 50.1} meV | P21 (eq. dark_ring_masses), P55 §7; same seesaw formula; SeesawNumericalCerts.lean | PTOLEMY (direct m_v1); CMB-S4/Euclid (Σm_v indirect) | m_v1 > 5 meV at 3σ, or Σm_v inconsistent with 59.4 meV at >3σ | CatA |
| 4 | PMNS Dirac CP phase δ_CP | 205.71° = (4/7) × 360° | P45 §CP violation; three-tape clock ratio τ_inner/τ_outer = 3/7; NuFIT 6.0 IC24 NH: 212° (+26°/-41°), placing prediction at −0.15σ | DUNE, T2K-II, Hyper-Kamiokande | |δ_CP − 205.71°| > 75° at >3σ | CatA |
| 5 | Tensor-to-scalar ratio r | 0 (exactly) | P44, P45; non-inflationary bounce cosmology with MDL initial state; corrections exponentially suppressed by blue-tilted kination spectrum | LiteBIRD (σ_r ≈ 0.001) | r > 0.003 at 3σ | CatAL |
| 6 | Proton stability (dimension-4 BNV) | No dimension-4 baryon-number-violating operator; proton absolutely stable against all dim-4 BNV processes | P22 §winding topology; `proton_decay_dim4_forbidden` in ForbiddenProcesses.lean; ℤ_7 winding conservation forbids all dim-4 BNV vertices | Super-Kamiokande, DUNE, Hyper-K proton searches; collider searches | Any confirmed baryon-number-violating process mediated by a dimension-4 operator | CatAL |

### Beyond-SM particle predictions — GTE visible sector (P02)

Masses are PCHIP-calibrated UCL values (calibration uncertainty ±1–25% as noted).
The prediction register is defined in P02 (paper code: SpivackGTESpectrum). The open
axiom for CatAD mass predictions is the identification of the UCL evolution as the
physical mass formula; Q=0 for GTE-P7 is independently CatAL from P29 topology.

| # | Label | Calibrated mass | Uncertainty | Deciding experiment | Falsification condition | Cat |
|---|-------|----------------|-------------|---------------------|------------------------|-----|
| 7  | GTE-P7 | 211.9 MeV, Q=0, spin-1/2, color singlet | ±14% | Belle II ≤500 fb⁻¹ monophoton; BaBar/LHCb archival dimuon | No neutral state in [182, 243] MeV in monophoton at Belle II | CatAD (mass), CatAL (Q=0) |
| 8  | GTE-P1 | 2.97 MeV, lepton-like | ±1.4% | DAFNE or dedicated MeV-scale search | No anomalous production at 2.97 MeV | CatAD |
| 9  | GTE-P2 | 107.4 MeV | ±14% | NA62, DarkLight (JLab) | No long-lived charged state at ~107 MeV | CatAD |
| 10 | GTE-P3 | ~800 MeV, baryon-like | ±25% | Belle II, LHCb Run 3 | No stable state in 600–1000 MeV outside SM | CatAD |
| 11 | GTE-P6 | 30.9 MeV | ±14% | Future MeV-scale experiments | No state at ~31 MeV beyond SM | CatAD |
| 12 | GTE-P8 | 298.0 MeV, quark-like | ±14% | BESIII existing data | No second peak in ππη/2γ near 298 MeV | CatAD |
| 13 | GTE-P9 | 561.0 MeV | ±20% | BESIII, LHCb Run 3 | No stable state in 550–575 MeV window | CatAD |
| 14 | GTE-P10 | ~1,100 MeV, baryon-like | ±20% | LHCb Run 3, BESIII | No new stable states in 1100–1350 MeV | CatAD |
| 15 | GTE-P11 | ~1,600 MeV, baryon-like | ±25% | LHCb Run 3, BESIII | No new stable states in 1600–1900 MeV | CatAD |

### Beyond-SM particle predictions — GTE mirror dark sector (P29)

Mirror-branch dark sector particles (ℤ_2 involution). Q=0 for all is Lean-certified
via MirrorWindingNumber.lean and DarkBraidAtlas.lean (P29, CatAL). Masses from GTE
arithmetic (CatA). All three dark singlet leptons have suppressed Higgs-portal coupling
(λ_s ~ 10^−6) and are below current experimental sensitivity; listed for completeness.

| # | Label | Mass | Q_EM | Deciding experiment | Falsification condition | Cat (mass / Q) |
|---|-------|------|------|---------------------|------------------------|----------------|
| 16 | χ_1 (dark singlet lepton G1) | 0.5406 MeV | 0 | Future CMB spectral distortion; dedicated sub-MeV search | Detection of charged dark state at this mass | CatA / CatAL |
| 17 | χ_2 (dark singlet lepton G2) | 24.47 MeV | 0 | Future MeV-scale dark matter searches | Detection of charged dark state at ~24 MeV | CatA / CatAL |
| 18 | χ_3 (dark singlet lepton G3) | 3604.68 MeV | 0 | LHC Higgs invisible width; mono-jet searches | Detection of charged dark state at ~3.6 GeV, or ε > 10^−4 kinetic mixing | CatA / CatAL |

---

## Dropped Candidates

The following entries from the draft candidate list were excluded because they are
retrodictions of already-measured quantities at the registry date:

| Dropped entry | Reason | Current experimental value |
|---------------|--------|---------------------------|
| Δm²_21 = 7.37×10^−5 eV² | Solar + reactor neutrino experiments (KamLAND, SNO, SK) have measured this to ~0.5% precision; GTE agreement is a consistency check, not a prediction | NuFIT 6.0 IC24 NH: 7.41×10^−5 eV² |
| Δm²_31 = 2.511×10^−3 eV² | Atmospheric + accelerator experiments (T2K, NOvA, MINOS+) have measured this to ~0.5% precision; GTE agreement is a consistency check | NuFIT 6.0 IC24 NH: 2.515×10^−3 eV² |

---

## Integrity and Commitment Scheme

**SHA-256 commitment:** The SHA-256 hash of this file (canonical UTF-8, LF line
endings, no trailing whitespace) is stored in `ugp_falsifiable_predictions_v1.sha256`.
This file was frozen before any hash was embedded anywhere in the corpus. The hash
is embedded downstream (in `papers/55_octonionic_shadow/PROVENANCE.md`, in P55 §7
as a footnote, and in `papers/common/ugp_master_index.tex`) but never inside this file.

**Git history:** Every commit to this repository is timestamped and signed by GitHub.
The commit that first adds this file provides a cryptographically verifiable lower
bound on the registry date.

**Zenodo deposit:** A dedicated Zenodo deposit of this file and its `.sha256`
companion is recommended to establish a DOI-linked, independent timestamp. This
deposit is pending and is described in the publishing-team handoff. The deposit type
should be "dataset" or "other" with its own concept DOI; `publication_date` must be
set to the actual deposit date at time of upload.

**OpenTimestamps:** If `ots` is installed, the companion file
`ugp_falsifiable_predictions_v1.md.ots` provides blockchain-anchored timestamping
via the Bitcoin blockchain. Generation of the .ots file is a publishing-team step.

---

## Embedded JSON

The following fenced JSON block mirrors the prediction table above for machine
readability. This block is part of this file and therefore covered by the SHA-256
commitment.

```json
{
  "registry_version": "v1",
  "registry_date": "2026-07-04",
  "corpus": "UGP Physics (github.com/novaspivack/ugp-physics)",
  "author": "Nova Spivack",
  "scope": "Pre-registered falsifiable predictions; no retrodictions",
  "predictions": [
    {
      "id": 1,
      "quantity": "Neutrino mass ordering",
      "predicted_value": "Normal Ordering (NO): m_v1 < m_v2 < m_v3",
      "precision": "categorical",
      "derivation_source": "P55 §7, P21; seesaw_normal_ordering_from_seed_ordering (SeesawTrialityPinning.lean); b_R1=5 < b_R2=11 < b_R3=19",
      "deciding_experiment": "JUNO (~2027); T2K/NOvA atmospheric",
      "falsification_condition": "Inverted Ordering (IO) confirmed at >3sigma by any experiment",
      "cat_level": "CatAL"
    },
    {
      "id": 2,
      "quantity": "Neutrino mass sum",
      "symbol": "Sigma_m_v",
      "predicted_value_meV": 59.4,
      "derivation_source": "P21, P47; GTE seesaw m_{v,k} = C * b_{R,k}^(29/9); M_R = 1.11e13 GeV; SeesawNumericalCerts.lean",
      "deciding_experiment": "CMB-S4 + Euclid (forecast sigma(Sigma_m_v) ~ 20 meV)",
      "falsification_condition": "Sigma_m_v < 30 meV or Sigma_m_v > 100 meV at 3sigma",
      "cat_level": "CatA"
    },
    {
      "id": 3,
      "quantity": "Individual neutrino masses",
      "predicted_values_meV": {"m_v1": 0.679, "m_v2": 8.61, "m_v3": 50.1},
      "derivation_source": "P21 (eq. dark_ring_masses), P55 §7; SeesawNumericalCerts.lean",
      "deciding_experiment": "PTOLEMY (m_v1 direct); CMB-S4/Euclid (Sigma_m_v)",
      "falsification_condition": "m_v1 > 5 meV at 3sigma, or Sigma_m_v inconsistent with 59.4 meV at >3sigma",
      "cat_level": "CatA"
    },
    {
      "id": 4,
      "quantity": "PMNS Dirac CP phase",
      "symbol": "delta_CP",
      "predicted_value_deg": 205.71,
      "formula": "(4/7) * 360 degrees",
      "derivation_source": "P45 §CP violation; three-tape clock ratio tau_inner/tau_outer = 3/7; NuFIT 6.0 IC24 NH comparison: 212 deg, -0.15sigma",
      "deciding_experiment": "DUNE, T2K-II, Hyper-Kamiokande",
      "falsification_condition": "|delta_CP - 205.71 deg| > 75 deg at >3sigma",
      "cat_level": "CatA"
    },
    {
      "id": 5,
      "quantity": "Tensor-to-scalar ratio",
      "symbol": "r",
      "predicted_value": 0,
      "derivation_source": "P44, P45; non-inflationary bounce cosmology with MDL initial state; corrections exponentially suppressed",
      "deciding_experiment": "LiteBIRD (sigma_r approx 0.001)",
      "falsification_condition": "r > 0.003 at 3sigma",
      "cat_level": "CatAL"
    },
    {
      "id": 6,
      "quantity": "Proton stability — dimension-4 BNV",
      "predicted_value": "No dimension-4 baryon-number-violating operator; absolute stability at dim-4",
      "derivation_source": "P22; proton_decay_dim4_forbidden in ForbiddenProcesses.lean; Z7 winding conservation",
      "deciding_experiment": "Super-Kamiokande, DUNE, Hyper-K; collider B-violation searches",
      "falsification_condition": "Any confirmed B-violating process mediated by a dimension-4 operator",
      "cat_level": "CatAL"
    },
    {
      "id": 7,
      "quantity": "GTE-P7 dark sector state",
      "predicted_value": {"mass_MeV": 211.9, "Q_EM": 0, "spin": "1/2", "color": "singlet"},
      "mass_uncertainty_pct": 14,
      "derivation_source": "P02 (mass, CatAD); P29 MirrorWindingNumber.lean + DarkBraidAtlas.lean (Q=0, CatAL)",
      "deciding_experiment": "Belle II <= 500 fb^-1 monophoton; BaBar/LHCb archival dimuon",
      "falsification_condition": "No neutral state in [182, 243] MeV in monophoton at Belle II",
      "cat_level": "CatAD (mass), CatAL (Q=0)"
    },
    {
      "id": 8,
      "quantity": "GTE-P1",
      "predicted_value": {"mass_MeV": 2.97, "sector": "lepton-like"},
      "mass_uncertainty_pct": 1.4,
      "derivation_source": "P02 (GTE arithmetic)",
      "deciding_experiment": "DAFNE or dedicated MeV-scale search",
      "falsification_condition": "No anomalous production at 2.97 MeV",
      "cat_level": "CatAD"
    },
    {
      "id": 9,
      "quantity": "GTE-P2",
      "predicted_value": {"mass_MeV": 107.4},
      "mass_uncertainty_pct": 14,
      "derivation_source": "P02 (GTE arithmetic)",
      "deciding_experiment": "NA62, DarkLight (JLab)",
      "falsification_condition": "No long-lived charged state at ~107 MeV",
      "cat_level": "CatAD"
    },
    {
      "id": 10,
      "quantity": "GTE-P3",
      "predicted_value": {"mass_MeV_approx": 800, "sector": "baryon-like"},
      "mass_uncertainty_pct": 25,
      "derivation_source": "P02 (GTE arithmetic)",
      "deciding_experiment": "Belle II, LHCb Run 3",
      "falsification_condition": "No stable state in 600–1000 MeV outside SM",
      "cat_level": "CatAD"
    },
    {
      "id": 11,
      "quantity": "GTE-P6",
      "predicted_value": {"mass_MeV": 30.9},
      "mass_uncertainty_pct": 14,
      "derivation_source": "P02 (GTE arithmetic)",
      "deciding_experiment": "Future MeV-scale experiments",
      "falsification_condition": "No state at ~31 MeV beyond SM",
      "cat_level": "CatAD"
    },
    {
      "id": 12,
      "quantity": "GTE-P8",
      "predicted_value": {"mass_MeV": 298.0, "sector": "quark-like"},
      "mass_uncertainty_pct": 14,
      "derivation_source": "P02 (GTE arithmetic)",
      "deciding_experiment": "BESIII existing data",
      "falsification_condition": "No second peak in pi-pi-eta or 2-gamma near 298 MeV",
      "cat_level": "CatAD"
    },
    {
      "id": 13,
      "quantity": "GTE-P9",
      "predicted_value": {"mass_MeV": 561.0},
      "mass_uncertainty_pct": 20,
      "derivation_source": "P02 (GTE arithmetic, trajectory-reinterpreted)",
      "deciding_experiment": "BESIII, LHCb Run 3",
      "falsification_condition": "No stable state in 550–575 MeV window",
      "cat_level": "CatAD"
    },
    {
      "id": 14,
      "quantity": "GTE-P10",
      "predicted_value": {"mass_MeV_approx": 1100, "sector": "baryon-like"},
      "mass_uncertainty_pct": 20,
      "derivation_source": "P02 (GTE arithmetic)",
      "deciding_experiment": "LHCb Run 3, BESIII",
      "falsification_condition": "No new stable states in 1100–1350 MeV",
      "cat_level": "CatAD"
    },
    {
      "id": 15,
      "quantity": "GTE-P11",
      "predicted_value": {"mass_MeV_approx": 1600, "sector": "baryon-like"},
      "mass_uncertainty_pct": 25,
      "derivation_source": "P02 (GTE arithmetic)",
      "deciding_experiment": "LHCb Run 3, BESIII",
      "falsification_condition": "No new stable states in 1600–1900 MeV",
      "cat_level": "CatAD"
    },
    {
      "id": 16,
      "quantity": "Mirror dark singlet lepton G1",
      "symbol": "chi_1",
      "predicted_value": {"mass_MeV": 0.5406, "Q_EM": 0},
      "derivation_source": "P29; GTE mirror-branch seesaw; DarkBraidAtlas.lean (Q=0, CatAL)",
      "deciding_experiment": "CMB spectral distortion; future sub-MeV dedicated search",
      "falsification_condition": "Detection of a charged dark state at this mass, or Q_EM != 0 for this sector",
      "cat_level": "CatA (mass), CatAL (Q=0)"
    },
    {
      "id": 17,
      "quantity": "Mirror dark singlet lepton G2",
      "symbol": "chi_2",
      "predicted_value": {"mass_MeV": 24.47, "Q_EM": 0},
      "derivation_source": "P29; GTE mirror-branch seesaw; DarkBraidAtlas.lean (Q=0, CatAL)",
      "deciding_experiment": "Future MeV-scale dark matter searches",
      "falsification_condition": "Detection of a charged dark state at ~24 MeV",
      "cat_level": "CatA (mass), CatAL (Q=0)"
    },
    {
      "id": 18,
      "quantity": "Mirror dark singlet lepton G3",
      "symbol": "chi_3",
      "predicted_value": {"mass_MeV": 3604.68, "Q_EM": 0},
      "derivation_source": "P29; GTE mirror-branch seesaw; DarkBraidAtlas.lean (Q=0, CatAL)",
      "deciding_experiment": "LHC Higgs invisible width; mono-jet searches",
      "falsification_condition": "Detection of a charged dark state at ~3.6 GeV, or epsilon > 10^-4 kinetic mixing",
      "cat_level": "CatA (mass), CatAL (Q=0)"
    }
  ],
  "dropped_candidates": [
    {
      "quantity": "Delta_m_sq_21",
      "value": "7.37e-5 eV^2",
      "reason": "Already measured (KamLAND + solar; NuFIT 6.0 IC24 NH: 7.41e-5 eV^2); GTE agreement is a consistency check, not a prediction"
    },
    {
      "quantity": "Delta_m_sq_31",
      "value": "2.511e-3 eV^2",
      "reason": "Already measured (T2K/NOvA/atmospheric; NuFIT 6.0 IC24 NH: 2.515e-3 eV^2); GTE agreement is a consistency check"
    }
  ]
}
```
