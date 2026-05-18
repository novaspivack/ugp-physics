# PROVENANCE — Paper P29: The Mirror Branch Braid Atlas

**Paper:** The Mirror Branch Braid Atlas: A Parameter-Free Dark Sector from the Universal Generative Principle  
**Author:** Nova Spivack  
**Created:** 2026-05-17  
**Status:** Draft — DOI pending Zenodo deposit

---

## Data and Computation Provenance

### Dark Singlet Lepton Masses

| Particle | Mass | Source |
|----------|------|--------|
| G1 (χ₁) | 0.5406 MeV | `InformationMassTransformer` (type="lepton") applied to mirror branch inputs |
| G2 (χ₂) | 24.47 MeV  | Same |
| G3 (χ₃) | 3604.68 MeV | Same |

**Script:** `papers/29_dark_sector_braid_atlas/artifacts/mdb_cascade.py`  
**Sanity check:** SM masses reproduce PDG 2022 to <0.01% (e=0.511, μ=105.66, τ=1776.76 MeV).

### Dark Quark G1 Masses

| Particle | Mass | Source |
|----------|------|--------|
| Dark up quark G1 | 0.57 MeV | Mirror-branch Permutation Principle; preliminary |
| Dark down quark G1 | 17.30 MeV | Same |

**Status:** Preliminary (pending verification from locked GTE map).

### Dark Coupling and Confinement Scale

| Quantity | Value | Source |
|----------|-------|--------|
| α_s,dark,bare | 0.11822 | P01 Gauge Coupling Master Formula (g3Sq_bare_eq) applied to SU(3)_dark |
| Λ_dark (N_f=6) | ~210 MeV | One-loop RG running from α_s,dark |
| Λ_dark (N_f=2) | ~1.7 GeV | Same |

### GTE Topological Baryogenesis

| Quantity | Value | Source |
|----------|-------|--------|
| η_{B+L,pre} (naive 1/ln) | 3.95×10⁻⁶ | η = N_f × ∏ P_gen,i where P_gen,i = 1/ln(c₁,i) |
| η_χ = (2/7)η_{B+L,pre} | 1.13×10⁻⁶ | Z₇ dark baryon charge (§4 of paper) |
| FIMP overproduction factor | 4.84×10⁶× | Corrected semi-analytic freeze-in formula |

**GTB calculations:** Semi-analytic GTE topological baryogenesis estimate; see §Asymmetric Dark Matter in the paper.

### Relic Density

The FIMP overproduction factor 4.84×10⁶ is from a corrected semi-analytic Boltzmann
equation estimate. A full numerical Boltzmann integration is required for the definitive
result but is not expected to change the overproduction by orders of magnitude.

### Neutrino Mass Ratio

| Quantity | Value | Source |
|----------|-------|--------|
| R_dark | 0.2080 | GTE mass formula applied to mirror b-values {5,29,37} |
| R_SM | 0.02936 | P21 (Lean-certified); matches NuFIT 6.0 at 0.16σ |

**Condition:** R_dark is conditional on b₃'=37 structural derivation (gap theorem).

---

## Lean Certificate Provenance

All Lean files reside in `ugp-lean/UgpLean/` (the canonical Lean 4 library):

| File | Location | Date |
|------|----------|------|
| `MirrorWindingNumber.lean` | `BraidAtlas/` | 2026-05-17 |
| `DarkQuarkCharge.lean` | `BraidAtlas/` | 2026-05-17 |
| `DarkBraidAtlas.lean` | `BraidAtlas/` | 2026-05-17 |
| `EWBosonRHNConnection.lean` | `BraidAtlas/` | 2026-05-17 |
| `RHNGapTheorem.lean` | `GTE/` | 2026-05-17 |
| `GTBGenerationPrimes.lean` | `GTE/` | 2026-05-17 |

All six files compile with zero sorry in `ugp-lean` (verified: `lake build` 2026-05-17).

---

## Citation Verification

| Citation | Key | Verified |
|----------|-----|---------|
| McDonald 2002 | McDonald2002 | ✓ hep-ph/0106249 confirmed via arXiv |
| Hall et al. 2010 | HallFIMP2010 | ✓ arXiv:0911.1120 confirmed via arXiv |
| Planck 2018 | Planck2018 | ✓ arXiv:1807.06209 confirmed |
| NuFIT 6.0 | NuFIT60 | ✓ arXiv:2410.05380, JHEP 12 (2024) 216 |
| PDG 2022 | ParticleDataGroup2022 | ✓ in main bib file |
| Foot, Lew, Volkas 1991 | FootLewVolkas1991 | ✓ Phys. Lett. B 272 (1991) 67 |
| Sakharov 1967 | Sakharov1967 | ✓ JETP Lett. 5 (1967) 24 |
