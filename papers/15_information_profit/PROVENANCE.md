# Provenance — The Information Profit Principle

This file records the origin, integrity, and caveats for all data sources and
computational results cited in the paper.

---

## Primary Data Sources

### 1. TE1.H Coherence History CSV Files

**Location:** `MFRR/TE_1_VALIDATION_PROGRAM/TE_1.H_LEVIN/results/csv/`

**Scripts used:**
- `MFRR/TE_1_VALIDATION_PROGRAM/TE_1.H_LEVIN/information_profit_simulation.py`
- `MFRR/TE_1_VALIDATION_PROGRAM/TE_1.H_LEVIN/run_te1h.py`
- `MFRR/TE_1_VALIDATION_PROGRAM/TE_1.H_LEVIN/te1b_pipeline_levin.py`

**Date of run:** 2025-11-08

**Files and SHA-256 checksums:**

| File | SHA-256 |
|------|---------|
| `profitable:_gen_drain_≈_1.4_(>_1.13)_coherence_history.csv` | `b63b40598999dc2283215d18a0e96d482092f5468462e416672777979abb7ad4` |
| `unprofitable:_gen_drain_≈_0.8_(<_1.13)_coherence_history.csv` | `ae2d9e96f52a8ce1c398a1c5e1065fe0e184705635873a715f3aa29e1a48fab2` |
| `profitable_gen_+_high_noise:_gen_drain_<_1.0_coherence_history.csv` | `1cc3cb6dccdf5c43e8479236b19ed1f4fc99f87f7dbb004bcfb56b97ae5794cd` |

**Three scenarios run (single seed each, 400 steps, 64x64 grid):**
- Unprofitable: A_gen=0.07, r_drain=0.08, A_noise=0.03 → rho ≈ 0.80
- Profitable: A_gen=0.14, r_drain=0.08, A_noise=0.02 → rho ≈ 1.40
- High Noise: A_gen=0.14, r_drain=0.08, A_noise=0.12 → rho < 1.00

---

### 2. TE2.1 Evolutionary Genesis JSON Files

**Location:** `MFRR/TE_2_Advanced_Explorations/TE_2_1_Recursive_Fidelity_Experiments/results/`

**Scripts used:**
- `MFRR/TE_2_Advanced_Explorations/TE_2_1_Recursive_Fidelity_Experiments/MFRR_Evolutionary_Genesis.py`
- `MFRR/TE_2_Advanced_Explorations/TE_2_1_Recursive_Fidelity_Experiments/MFRR_Evolutionary_Sweep.py`

**Date of runs:** 2025-11-19 to 2025-11-20

**Files:** Multiple `MFRR_Evolutionary_Genesis_v2_YYYYMMDD_HHMMSS.json` and
`MFRR_Evolutionary_Sweep_YYYYMMDD_HHMMSS.json` files in `results/`.

**Aggregate statistics used in paper:**

| Statistic | Value |
|-----------|-------|
| Total genesis runs | 124 |
| Runs with rho > IPT (1.1309) | 15 |
| Supercritical range | [1.137, 1.567] |
| Supercritical mean | 1.234 |
| Overall mean rho | 0.821 |
| Sweep runs total | 72 |
| Sweep runs above IPT | 14 (19.4%) |

---

### 3. E4 Reflexive Landauer Results JSON

**Location:** `MFRR/E4_reflexive_landauer_results.json`

**Script used:** `MFRR/E4_reflexive_landauer_check.py`

**Date of run:** 2026-04-13

**SHA-256:** `13cf53baaa10f02b9e5cda2b88fafaeff717fafa7057d1da4fcb4f3c938f4071`

**Aggregate statistics used in paper:**

| Statistic | Value |
|-----------|-------|
| Total trials | 50 |
| Pass rate | 100% |
| Min margin | 0.0182 |
| Max margin | 4.0798 |
| Mean margin | 0.9481 |

---

## Verified Claims Table

| Claim | Value | Source |
|-------|-------|--------|
| IPT | 1.130915... | Analytical derivation (verified by `verify_ipt_derivation.py`) |
| Lambda | 0.261830... | Analytical derivation |
| phi | 1.618034... | Analytical (golden ratio) |
| TE1.H: 3 scenarios run | Unprofitable, Profitable, High Noise | TE1.H CSV files |
| TE1.H: Supercritical only scenario with positive coherence slope | rho ≈ 1.40, Delta-C/step = +1.00e-4 | profitable CSV |
| TE1.H: Unprofitable decay rate | Delta-C/step = -1.94e-5 | unprofitable CSV |
| TE1.H: High-noise decay rate | Delta-C/step = -3.51e-5 | high-noise CSV |
| TE2.1: 15/124 above IPT | 15 supercritical runs out of 124 genesis runs | TE2.1 JSON files |
| TE2.1: Supercritical mean | rho_mean = 1.234 | TE2.1 JSON files |
| E4: 50/50 pass rate | All PT costs exceed Reflexive Landauer bound | E4 JSON |
| E4: Min margin | 0.0182 | E4 JSON |
| E4: Mean margin | 0.9481 | E4 JSON |

---

## Lean Machine-Checked Certification (updated 2026-05-12)

### ugp-physics-lean (H9, A1, A2 GXT/IPT modules)

Repository: https://github.com/novaspivack/ugp-physics-lean  
Zenodo DOI: pending deposit

| Theorem | Lean name | Module | Sorry? |
|---------|-----------|--------|--------|
| H9: IPT self-consistency | `ipt_self_consistent` | `GXT.H9SelfConsistency` | Zero |
| A1: 1/φ unique positive FP | `golden_ratio_fixed_point_unique` | `GXT.GoldenRatioFixedPoint` | Zero |
| A1: 1/φ satisfies the equation | `golden_ratio_is_fixed_point` | `GXT.GoldenRatioFixedPoint` | Zero |
| A2: entropy formula H(U(1))=ln(2π) | `entropy_formula_U1` | `IPT.InformationProfitThreshold` | Zero |
| A2: H_adj = ln(2π) > 0 | `A2_adjudication_entropy` | `IPT.InformationProfitThreshold` | Zero |
| A2: Circle ≅ ℝ/(2πℤ) | `circle_iso_addCircle_2pi` | `GXT.U1DirectProof` | Zero |
| A2: Circle.exp surjective | `circle_exp_surjective_MAIN` | `GXT.LieExpSurjective` | Zero |
| A2: abstract minimality | `u1_minimality_reduced` | `GXT.U1DirectProof` | **1 sorry** (Mathlib gap) |
| A3: 1/2 PSC split | `A3_forward_backward_split` | `IPT.InformationProfitThreshold` | Zero |
| IPT theorem | `IPT_theorem` | `IPT.InformationProfitThreshold` | Zero |

Remaining sorry count: **2** (both in abstract Lie group minimality, both awaiting
`LieGroup.exp` addition to Mathlib; neither affects the Circle-specific results needed
for the UGP/IPT application).

### ugp-lean (A1 canonical home, IPT re-export)

Repository: https://github.com/novaspivack/ugp-lean  
Zenodo: https://doi.org/10.5281/zenodo.19433538

| Theorem | Lean name | Module |
|---------|-----------|--------|
| A1: \|ψ\|=1/φ | `abs_psi_eq_inv_phi` (re-exposed as `A1_psc_contraction_rate_is_inv_phi`) | `UgpLean.GTE.LinearResponse`; `UgpLean.IPT.InformationProfitThreshold` |
| A2: H(U(1))=ln(2π) | `A2_adjudication_entropy` + `entropy_formula_U1` | `UgpLean.IPT.InformationProfitThreshold` |
| A3: 1/2 PSC split | `A3_forward_backward_split` | same |
| IPT theorem | `IPT_theorem` | same |

All zero sorry in ugp-lean.

**Claim type:** [B] bridge (conditional on A1–A3) → **[T] machine-checked** (all premises zero-sorry in ugp-lean; H9 and A1 uniqueness additionally zero-sorry in ugp-physics-lean).

---

## Caveats and Limitations

### No biological or economic experimental data

The paper discusses connections between IPT and biological metabolism and economic
sustainability as interpretive conjectures only. No biological measurements, metabolic
data, or economic time series were collected, analyzed, or used in any calculation.
These connections are not supported by data in this paper.

### Toy model limitations

TE1.H uses a 64x64 grid, three parameter regimes, single run per regime, and a
gzip-compression-ratio coherence proxy. This is a qualitative consistency check,
not a rigorous statistical test. The simulator does not incorporate the full MFRR
dynamics and is intentionally simple.

TE2.1 uses simplified neural controllers and a discrete resource grid. The mapping
from agent dynamics to the MFRR constructs (PSC, PT adjudication, Psi-field) is
heuristic. The 15/124 count will vary under different random seeds; the pre-computed
result files fix the reported values.

E4's 100% pass rate is structurally expected from the model construction (the PT
cost includes a difficulty factor epsilon >= 0 by design). The informative output
is the margin distribution, not the pass rate itself.

### MFRR model assumptions

All results are conditional on the MFRR framework assumptions: the PSC requirement,
the Reflexive Landauer Bound with coherence coupling constant lambda_Psi, and the
two-step predict-correct structure of the PSC update operator. The value of
lambda_Psi is a free parameter in the current formulation. The IPT value would
change if the PSC update structure or phase-space geometry assumption were relaxed.

### Single-seed TE1.H runs

Each TE1.H scenario uses a single random seed. Stochastic variation across seeds
has not been quantified for this experiment.

## Real-world validation data (added 2026-04-14)

### Population dynamics (§4.4)
- **Source:** World Bank Open Data API
- **Indicators:** SP.DYN.CBRT.IN (birth rate), SP.DYN.CDRT.IN (death rate)
- **Coverage:** 261 countries, 2010–2022 annual averages
- **Key result:** Buffer zone [1.0, 1.13) mean growth = +0.04%/yr; above-IPT mean = +1.46%/yr; p < 1e-4
- **Result file:** `information_profit/results/ipt_population_validation.json`

### Business formation (§4.5)
- **Source:** U.S. Bureau of Labor Statistics Business Employment Dynamics (BED)
- **Data:** Annual private-sector establishment births/deaths, 1994–2022
- **Key result:** Gen/Drain range 0.845–1.153; IPT = 1.1309 is historical ceiling of expansion
- **Result file:** `information_profit/results/ipt_business_validation.json`
