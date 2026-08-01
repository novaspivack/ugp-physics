# PROVENANCE — P39 — QCD Structure from the GTE Substrate

**Paper:** P39 — "QCD Structure from the Generative Triple Evolution Substrate:
Asymptotic Freedom, Confinement, and Hadron Spectroscopy from F₂₁ ⊂ SU(3)"

**Author:** Nova Spivack

**Series position:** Paper 39 in the UGP Physics Programme

**Date created:** 2026-05-24

---

## Scope

Standalone QCD/hadronic physics paper that assembles the complete QCD consequences
of the F₂₁ = Z₇ ⋊ Z₃ substrate identification from the Generative Triple
Evolution programme. Companion to P35 (electroweak capstone). Covers:

- F₂₁ = Σ(21) ⊂ SU(3) substrate identification (forced, zero parameters)
- All QCD colour factors (C_F = 4/3, C_A = 3, T_F = 1/2), exact
- β-function coefficients b₀ = 7, b₁ = 26 (machine-certified)
- Strong CP resolution: θ_QCD = 0 by three independent proofs (machine-certified)
- QFT mass gap: unconditional positive gap from orbit arithmetic (machine-certified)
- Confinement and Fradkin–Shenker resolution
- Three-field gauge architecture (A_μ, A′_μ, A_μ^EM) with e′ = e
- Non-abelian SU(3) Berry holonomy from kink substrate
- Hadron spectroscopy: meson nonet, baryon octet/decuplet, vector nonet
- Zero-PDG-input predictions: f_π, θ_P, χ_top, B₀, σ₄D

---

## What this paper establishes

| Result | Certification level |
|---|---|
| F₂₁ ≅ Σ(21) ⊂ SU(3); C_F = 4/3, C_A = 3, T_F = 1/2 | Machine-certified (Lean 4, zero sorry) |
| b₀ = 7, b₁ = 26 | Machine-certified (zero sorry, zero axioms) |
| θ_QCD = 0 (three independent proofs) | Machine-certified (zero sorry) ROBUST |
| Unconditional QFT mass gap | Machine-certified (zero sorry, zero axioms) |
| e′ = e (second Cartan coupling) | Machine-certified (zero sorry) |
| Non-abelian Berry holonomy | Computationally verified 5/5 tests; algebraic certified |
| f_π = 91.35 MeV (−0.81% vs PDG) | Computationally verified |
| θ_P = −13.08° ± 3.74° (within PDG range) | Computationally verified |
| χ_top^(1/4) = 166.5 MeV (−6.4% vs PDG) | Computationally verified |
| Fradkin–Shenker resolution | Machine-certified (zero sorry) |
| J^P = 1/2+ baryon ground state | Machine-certified (seven theorems) |

---

## Primary Lean modules

| Module | Content | Status |
|---|---|---|
| `UgpLean/Universality/SylowIndexCouplingHierarchy.lean` §5i–§7, §5j, §5m, §5n | F₂₁, Casimir, β, strong CP, A′, Berry, FS | CatAL zero sorry |
| `UgpLean/QFT/GaugedMassGap.lean` | Conditional + unconditional QFT mass gap | CatAL zero sorry |
| `UgpLean/Spacetime/ColorConfinement.lean` | Colour-singlet restriction | CatAL zero sorry |
| `UgpLean/Spacetime/MassGap.lean` | Beable-level mass gap | CatAL zero sorry |

---

## Computational scripts

| Script | Result | Location |
|--------|--------|----------|
| `fradkin_shenker_confinement.py` | Fradkin–Shenker phase diagram | `scripts/` (graduated from `rank107_higgten_fradkin_shenker.py`) |
| `aprime_lagrangian_extension.py` | A′_μ coupling prediction, e′ = e | `scripts/` (graduated from `rank118_aprime_lagrangian.py`) |
| `rank129_thetap_chain.py` | θ_P mixing angle from GOR chain | `scripts/` (graduated 2026-05-31 from `rank129_thetap_v2.py`) |
| `mphi_scc_derivation.py` | m_φ first-principles via SCC | `scripts/` (graduated 2026-05-24) |
| `g10_gs_derivation.py` | Strong coupling g_s at hadronic scale | `scripts/` |
| `f21_su3_continuum_limit.py` | F₂₁ → SU(3) continuum limit | `scripts/` |
| `g13_creutz_ratio_vectorized.py` | Creutz ratio lattice confinement | `scripts/` |
| `lambda_gte_band_threshold_derivation.py` | Λ_GTE = 7·M_kink derivation (tree/pole/envelope, nulls) | `scripts/` (graduated 2026-06-10) |
| `lambda_gte_band_route_battery.py` | Boundary route battery; RG-invisibility (running-intersection route closed negative) | `scripts/` (graduated 2026-06-10) |
| `lambda_gte_band_sigma_verdict.py` | e² = 7/2 σ-verdict at the derived Λ_GTE band | `scripts/` (graduated 2026-06-10) |

---

## Source papers and dependencies

| Topic | Primary source paper |
|---|---|
| Discrete substrate, Rule 110, lifting theorems | P28 (SpivackCompUniversality) |
| GTE-Möbius substrate arithmetic foundation | P34 (SpivackGTEMobius) |
| Electroweak capstone | P35 (SpivackGTEUnification) |
| Emergent spacetime / causal structure | P36 (SpivackEmergentGravity) |
| CKM / Wolfenstein parameters | P32 (SpivackCKM) |
| Deeper consequences / CP observables | P33 (SpivackDeeperConsequences) |

---

## Confidence summary

| Result class | Level |
|---|---|
| F₂₁ identification, b₀, b₁, θ_QCD=0, mass gap, e′=e, FS, JP | CatAL / ROBUST |
| Berry holonomy → SU(3) | PROVISIONAL-STRONG (algebraic certified, physical identification PROVISIONAL) |
| Hadron multiplets (f_π, θ_P, χ_top) | CatA / PROVISIONAL |
| Λ_GTE = 7·M_kink ≈ 2.0 GeV (tree (8/7)m_τ = 2030.70 ± 0.14 MeV; pole 1.970 ± 0.146 GeV; envelope 1.96 ± 0.15 GeV) | Tree identity CatAD; pole CatA; arithmetic core machine-certified (`lambda_gte_threshold_identity`) |
| UV completion above Λ_GTE | Conjectural |
| Wightman / continuum mass gap | Open |

---

*Provenance document — P39 — UGP Physics — 2026-05-24*

- **2026-06-02 (083C quality audit — commit bba2d17e):** No new results added (P39 update was structural consistency pass). Overfull fixes applied in longtable.
- **2026-06-10 (Λ_GTE derivation update):** The calibration-based Λ_GTE = 2.01 +0.24/−0.44 GeV (Route A′/C′ spread) replaced by the first-principles seven-kink full-winding threshold Λ_GTE = 7·M_kink (tree (8/7)m_τ = 2030.70 ± 0.14 MeV CatAD; pole 7M^Q = 1.970 ± 0.146 GeV CatA with M^Q = 281 ± 21 MeV from P42; envelope 1.96 ± 0.15 GeV). Pair-creation threshold prose corrected to the seven-kink mechanism; Route C′ mislabel on the 290.10 MeV SCC mass fixed; RG-invisibility remark added (b₀ = 7 on both sides of the boundary); α_s anchor-chain footnote added. Scripts `lambda_gte_band_*` graduated to `scripts/` with the corrected pole-mass input.
