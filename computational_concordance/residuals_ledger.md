# Residuals ledger (computational + theorem boundary)

This memo supports the Unified Rigidity capstone paper: it separates
**theorem-extracted** facts, **computationally verified** facts, **open**
conjectures, and **controlled tensions** (predictive forks).

## 1. Theorem-grade facts

| Fact | Source | Lean / formal |
|------|--------|-----------------|
| RSUC: unified-admissible triples have MDL canonical representative `LeptonSeed` | Paper 25 / `ugp-lean` | `UgpLean.rsuc_canon`, `rsuc_theorem` |
| Lepton Seed values `(1, 73, 823)` | `ugp-lean` | `LeptonSeed_values` |
| Quarter-Lock law (existential, elegant kernel) | `ugp-lean` | `quarterLockLaw` |
| Canonical 3-step orbit numerics | `ugp-lean` | `canonical_orbit_three_steps` |
| Gauge signature rigidity **given RCC** | NEMS `NemS.Physics.Rigidity` | `gauge_signature_rigidity` |
| Unified Rigidity packaging: admissible seed + basin flag | `unified-rigidity-lean` | `unified_rigidity_theorem` |

## 2. Computationally verified facts (finite range)

| Fact | Provenance | Range / caveat |
|------|------------|----------------|
| `n = 10`, `b₁ = 73` minimal robust candidate in sieve | `papers/05_uniqueness/`, `uniqueness/` tooling | Certified at **n = 10** in `ugp-lean` classification; global **all-n** closed form is separate |
| Basin labels **A/B/C** partition the four-seed deep grid | `exp_20260413_deep_trajectories` → `canonical_seed_basin_report.json` | **24** tasks; `(1,73,*)`→**A**, `(2,89,1597)`→**C**, `(3,97,2203)`→**B**; SHA-256 of JSON inputs in report |
| RG fixed-point `α` dispersion by seed | `exp_20260412_rg_sweep_full` → `generated/run_manifest.json` | **224** tasks; statistics pooled per seed tuple |
| `q_early_mean_abs` proxy from GTE traces | Same deep export | Steps **1…5000** mean `\|q\|`; align with paper **Q₄** notation before publication |
| MFRR advanced PSC / SRRG attraction statements | `MFRR/` experiment bundles | **Supporting** evidence; trust boundary marked in MFRR text |

## 3. Open conjectures

| Conjecture | Evidence | What would close it |
|------------|----------|----------------------|
| **RCC** (`ResidualClassificationConjecture`) in NEMS | Gauge rigidity theorem is **conditional** on RCC | Analytic + computational collapse of residual set to SM signature |
| **All-n** closed-form uniqueness beyond certified levels | Monotone strengthening lemmas in `ugp-lean` | Full arithmetic classification in Lean |

## 4. Controlled tensions / predictive forks

| Topic | Status | Notes |
|-------|--------|-------|
| **Neutrino sector** | Predictive fork | Mass/mixing pattern: explicit tension / prediction — not closed as theorem |
| **Dynamical layer** | Computational axioms in `unified-rigidity-lean` | Basin and `Q₄` claims are **computational axioms** until fully derived from analytic dynamics |
| **PSC Layer I vs II** | Bridge axioms in `PSCBridge` | MFRR narrative split not yet mirrored as separate proved predicates in this bridge |
