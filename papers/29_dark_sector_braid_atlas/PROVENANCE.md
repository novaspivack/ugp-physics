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

### Python artifacts (graduated)

| Script | Output |
|--------|--------|
| `artifacts/mdb_cascade.py` | Dark + SM lepton masses |
| `artifacts/fimp_yield_analytic.py` | FIMP factor ~4.84×10⁶ |
| `artifacts/relic_density.py` | Parametric relic hierarchy |
| `artifacts/predictions_table.json` | Frozen prediction table |
| `artifacts/lean_certificates.json` | Lean module manifest |

GTB η uses MDL-minimal c₁ = 823, 9007, 46681 (`GTBGenerationPrimes.lean`); see `REPRODUCE.md` (corrected 2026-05-20).

**Graduated 2026-05-24:** `rank247_dsr_dark_confinement.py` → `artifacts/` (dark SU(3) running coupling and Λ_dark self-consistent determination). This script is not on the ranked board; it is exploratory supporting computation for the Λ_dark range [210 MeV, 1.7 GeV] quoted in §3.4 and §4. It is not Lean-certified. The paper's Λ_dark values derive from one-loop RG running with α_s,dark = α_s,SM (Lean-certified via `g3Sq_bare_eq`); the script provides numerical verification of the analytic RG estimate.

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

- **2026-06-02 (083C quality audit — commit bba2d17e):** Added D_top topological dilution: Ω_DM h²=0.11994 (−0.044% Planck 2018) via D_top=exp(−1/N_c). Identity q_dark/(|Z₇|−1)=1/N_c certified CatAL. Lean cert: `z7_dark_baryon_correction_identity`. Scripts graduated: `h0_z7_topological_dilution.py`, `h0_dark_matter_relic_density_v2.py`.

- **2026-06-02:** D_top derivation upgraded to machine-certified (Lean 4, zero sorry). Z₇ group transitivity closes the equal-sector-distribution argument; Rajaraman §4.4 analogy superseded. New certs: `z7_star_transitivity_under_addition`, `z7_symmetry_forces_equal_sector_action`, `d_top_derivation_chain_catal` (all zero sorry).
