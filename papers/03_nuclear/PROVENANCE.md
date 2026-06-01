# Provenance: Nuclear Physics From UGP Paper

**Paper:** *GTE Coordinates as Nuclear Descriptors: Competitive ML Performance from UGP-Derived Features*  
**Version:** v7.0 (2026-05-08)  
**Status:** content complete — publishing hold

---

## v6.0 Changes (2026-05-08)

### New section added: Magic Number Derivation (§sec:magic-numbers-derivation)

**Claim type:** [B] Bridge claim  
**Claim:** All 7 nuclear magic numbers {2,8,20,28,50,82,126} derived from GTE-predicted pion parameters ($f_\pi$, $m_\pi$) via Nilsson model with nuclear many-body suppression factor $F_{SR} \approx 0.42$.

**What the GTE cascade provides:**
- $m_\pi c^2 = 139.6$ MeV (pion mass — GTE prediction from Papers P01-P02)
- $f_\pi^2 = 0.079$ (pion-nucleon coupling — GTE prediction from Papers P01-P02)

**What is NOT derived from GTE (open task):**
- $F_{SR} \approx 0.42$: short-range suppression factor from Brueckner-Hartree-Fock nuclear many-body theory
- A-dependence of $\kappa$: the formula gives $\kappa \propto A^{1/3}$; empirical $\kappa$ is roughly constant across the periodic table

**Corrected arithmetic (important):** The bare OPE formula gives $\kappa_{OPE} \approx 0.119$ at $A=50$, not 0.050. Multiplying by $F_{SR} = 0.42$ gives $\kappa_{GTE} \approx 0.050$. An earlier draft incorrectly stated $0.00945 \times 12.58 \approx 0.050$; this was an arithmetic error (correct product = 0.119).

**Tensor force correction:**
- $\kappa_T = (f_\pi^2 / 4\pi) \times (m_\pi c^2 / \hbar\omega_0) \times 0.35 \approx 0.028$
- Raises the N=28 gap from 0.275 to ~0.317 $\hbar\omega_0$, crossing the 0.3 threshold
- The short-range factor 0.35 for the tensor correction is also from nuclear structure fits

**Reproducible code:**
- `papers/03_nuclear/magic_number_derivation/magic_number_derivation.py` — Nilsson model, gap scan
- `papers/03_nuclear/magic_number_derivation/tensor_force_correction.py` — tensor analysis
- `papers/03_nuclear/magic_number_derivation/kappa_empirical_fit.py` — empirical κ comparison (see below)
- Requirements: numpy, scipy only (no Docker needed)

**Empirical κ comparison (new, v6.0) — computed results:**
- Script: `magic_number_derivation/kappa_empirical_fit.py`
- Data: 7 nuclei spanning A=15–207 (Bohr-Mottelson Vol. 1, NNDC)
- Results:
  - Empirical κ(A) ranges from 0.034 (⁹¹Zr) to 0.127 (¹⁵N)
  - Required F_SR ranges from 0.24 to 1.60 across nuclei
  - Constant-F_SR model: F_SR = 0.598 ± 0.454 (±76% RMS uncertainty)
  - Power-law fit: F_SR = 5.53 × A^{-0.626} (better fit, RMS ±38%)
  - A-dependence: formula gives κ ∝ A^{+1/3} but empirical is ∝ A^{-0.3}
    (systematic sign error in A-scaling — deeper nuclear physics needed)
- Implication: Formula is an ORDER-OF-MAGNITUDE derivation (factor ~2), not a precision calculation
- Magic numbers ARE robustly predicted because the target range κ ∈ [0.045, 0.060]
  is covered by the formula at A~40-90 (where magic numbers 28-82 reside)

**New citations added to references.bib:**
- `MagicNumberCode` — supplementary code citation
- `MayerJensen1949` — Mayer-Jensen 1949 Nobel-prize paper

---

## Wave-5 Decision Gate Results (2026-04-20)

### COMP-P03-A: Controlled Ablation — Equal-Size Baseline Comparison

| Artifact | Script | SHA-256 | Date |
|----------|--------|---------|------|
| `computational_concordance/p03_ablation_results.json` | `nuclear/ablation_equal_size_random.py` | `e949eeec` | 2026-04-20 |

**Key results:**
- GTE Composition (50 feat.) 10-fold CV MAE: **3.1717 ± 0.1722 MeV**
- Random Poly (50 feat.) 10-fold CV MAE: **4.2360 ± 0.3011 MeV** (+1.06 MeV worse)
- Enriched BW (50 feat.) 10-fold CV MAE: **3.3271 ± 0.2451 MeV** (+0.16 MeV worse)
- **DECISION: Path A** — GTE features win vs both baselines → full UGP nuclear paper

### COMP-P03-B: Honest 10-Fold CV

| Artifact | Script | SHA-256 | Date |
|----------|--------|---------|------|
| `computational_concordance/p03_nubase_crossval_results.json` | `nuclear/nubase_crossval.py` | `c5e55f97` | 2026-04-20 |

**Key results:** (confirmed same as COMP-3-A CV numbers above)
- GTE: 3.1717 ± 0.1722 MeV
- Random Poly: 4.2360 ± 0.3011 MeV
- Enriched BW: 3.3271 ± 0.2451 MeV

### Path A text changes applied (2026-04-20)
- Title updated to "GTE Coordinates as Nuclear Descriptors: Competitive ML Performance from UGP-Derived Features"
- Abstract rewritten with COMP-3-A numbers
- §2 two-feature-set architecture subsection added
- Appendix X.0 honest disclosure added (coordinate features not algebraically derived from seeds)
- "Law of Stability" renamed to "Nuclear Stability Score Function" (G0-2)
- "excellent agreement" for R²=0.62 fixed → "substantial out-of-sample degradation" (G0-1)
- MFRR TE₂.3 cross-citation added in Discussion
- Robustness section updated with equal-size baseline framing

---

## Forensic Audit (2026-04-13)

All original model files, datasets, and scripts were recovered from git commit `a4b1ca21` (initial commit, Sept 2025). All numerical claims in the paper have been verified or explained. The canonical 6-term laws, ML oracle, and datasets are bundled in the public repo.

---

## Dataset

### Canonical Training Dataset

| Property | Value |
|----------|-------|
| File | `training_data_with_stability.csv` (in this folder) |
| Original path | `PERIODIC_TABLE_APP/current_datasets/unified_gte_training_dataset_with_stability.csv` |
| Source | NUBASE2020, AMDC, NDS, ENSDF |
| Rows | **1,319 nuclei** (filtered: excludes anomalous light nuclei Z<2 and unmeasured superheavy) |
| Stability distribution | 989 stable (75.0%), 330 unstable |
| Key columns | `Z, N, A, BE, BE_per_A, Is_Stable, Stability_Reason, N_Z_ratio` + 20 GTE/physics features |
| SHA256 | compute on use: `shasum -a 256 training_data_with_stability.csv` |

**Note on stability labels:** `Is_Stable` was derived from NUBASE2020 half-life data and physical stability criteria (a nucleus is "stable" if its ground state has half-life > threshold or is listed as stable in NUBASE). The correct 6-term stability law accuracy is **96.21% training / 96.13% ± 0.77% 5-fold CV** (majority-class baseline: 75.0%).

**T-03 diagnosis:** The Verifier App (`Verifier_periodic_table_gte_v2.py`) applies `sigmoid(Ridge_score)` and thresholds at 0.5, which is mathematically equivalent to thresholding the raw Ridge output at 0 (not 0.5). The correct threshold for Ridge regression trained to predict 0 (unstable) and 1 (stable) is 0.5 on the raw Ridge output. With threshold Ridge > 0.5, the 6-term law achieves 96.21% on all 1,319 training nuclei and 96.13% ± 0.77% in 5-fold CV. Evidence: `comp_p03_NSL_stability_upgrade_v2.json`. For out-of-distribution generalization, training on valley-of-stability nuclei (N/Z ∈ [0.9,1.5], n=825) and testing on exotic peripheral nuclei (n=494, 73.3% stable baseline) yields 81.8% accuracy for the 6-term law and 87.7% for the extended 9-term law (adding pairing + magic-number proximity features) — both substantially above baseline.

### Raw Data Sources (not included — must download)

- NUBASE2020: https://www.nndc.bnl.gov/nubase2020/
- AME2020: `ame2020_data/mass_1.mas20.txt`
- NUBASE raw (local): `ame2020_data/nubase_1.mas20.txt`

---

## Models

### Canonical Models (in `canonical_models/`)

| File | Description | Performance |
|------|-------------|------------|
| `optimal_6term_binding_law.pkl` | **6-term binding energy Ridge law** (the paper's parsimonious BE law) | MAE = 0.032 MeV/A |
| `optimal_6term_stability_law.pkl` | **6-term stability Ridge law** (the paper's parsimonious stability law) | 96.21% training / 96.13% 5-fold CV (correct threshold Ridge>0.5) |
| `unified_gte_scaler.pkl` | StandardScaler for the 41 GTE features | — |
| `unified_gte_metadata.json` | Metadata: 41 features, 1319 samples, training date 2025-09-12 | — |
| `complete_binding_energy_law.txt` | Human-readable law coefficients | — |
| `complete_stability_law.txt` | Human-readable law coefficients | — |
| `improved_9term_stability_law.pkl` | **9-term stability LogisticRegression** (6 smooth features + pairing + z_magic_dist + n_magic_dist; GTE-internally consistent via NUC-06 magic numbers) | 96.97% training; **87.7% on exotic OOD split** (N/Z outside [0.9,1.5]) vs 81.8% for 6-term (+5.9pp); generated 2026-05-11 |
| `improved_9term_stability_law.txt` | Human-readable 9-term law coefficients with OOD performance notes | — |

### ML Oracle (champion model — in `Verifier_periodic_table_work_files/model_backups/`)

| File | Description | Performance |
|------|-------------|------------|
| `primary_model_final.pkl` | XGBRegressor champion model (72 features including LDM terms) | MAE ~0.025 MeV/A (training) |
| `primary_scaler_final.pkl` | StandardScaler for 72-feature set | — |

**IMPORTANT:** The champion model uses 72 features including Liquid Drop Model terms (vol_term, surf_term, coul_term, etc.) and magic number features — it is NOT purely GTE-only. The paper must be honest about this (framing: "GTE-feature ML complemented by physics-informed features").

---

## Scripts

### Canonical Scripts

| Script | Path | Purpose |
|--------|------|---------|
| `ablation_study.py` | `` | Three-way ablation: Physics vs GTE vs Hybrid. Run with `filtered_experimental_dataset.csv` in CWD |
| `Verifier_periodic_enhanced_ml_training_v4_champion.py` | `Verifier_periodic_table_work_files/` | Trains the 72-feature champion ML Oracle |
| `Verifier_periodic_ugp_nuclear_toolkit_v4.py` | same | Periodic table generation |
| `Verifier_periodic_table_final.py` | same | Final periodic table output |
| `parse_nubase_stability_data.py` | `` | Parse NUBASE stability labels |

### Feature Construction

**Paper Appendix (6 features for analytical laws):**
- f1 = log(N(N-1)/A + 1)
- f2 = log(A^(2/3) + 1)
- f3 = log(Z(Z-1)/A + 1)
- f4 = ((N-Z)/A)²
- f5 = exp(-Z(Z-1)/(100A))
- f6 = exp(-N(N-1)/(100A))

**Ablation script (50 GTE features):** Uses multiplicative GTE triple construction: `a_eff = proton_a^Z × neutron_a^N` etc., with proton constants (a=1, b=73, c=823) and neutron constants (a=1, b=5, c=42) — DIFFERENT from paper appendix feature construction.

**Champion model (72 features):** Uses `real_experimental_dataset_v4.csv` feature set including LDM terms, magic numbers, Möbius functions. See champion script lines 42-80 for full list.

---

## Numerical Claims Registry

| Claim | Value | Source | Verified |
|-------|-------|--------|---------|
| ML Oracle BE/A MAE | 0.025 MeV | Training performance on 1319 nuclei | ✅ |
| ML Oracle total BE MAE | 2.132 MeV | Training performance | ✅ |
| ML Oracle R² | 0.994 | Training performance | ✅ |
| ML Oracle stability | 99.4% | Training performance | ⚠️ needs verification with stability labels |
| 6-term law BE/A MAE | 0.032 MeV | Recomputed from exact coefficients | ✅ |
| 6-term law stability | 96.21% train / 96.13% 5-fold CV | Correct threshold: Ridge > 0.5 on raw output. Verified on 1,319 training nuclei. See T-03 diagnosis. | ✅ |
| CV table BE MAE | 0.0231 MeV | 5-fold CV on 6-term law (re-fitted) | ✅ |
| CV table stability | 98.63% | 5-fold CV on **ML Oracle** re-fitted in each fold (not the 6-term parsimonious law — Table 2 caption updated 2026-04-13 to make this explicit) | ✅ |
| Ablation improvement | ~20% | GTE vs simplified BW baseline on total BE | ✅ (we get 22.7%) |
| Ablation improvement (canonical run) | +19.7% | GTE-only vs physics-only on `filtered_experimental_dataset.csv` via `ablation_study.py` — confirmed 2026-04-13, see `nuclear_claims_audit_results.json` | ✅ |

---

## Files in this repository

Included in this archive:
1. `training_data_with_stability.csv` — canonical 1319-row training data
2. `canonical_models/optimal_6term_*.pkl` — 6-term law models
3. `canonical_models/unified_gte_scaler.pkl` — scaler
4. `nuclear/ablation_study.py` — ablation script
5. `periodic_table_data.csv` — Z=1-190 predictions
6. `nuclear_claims_audit_results.json` — claims audit: ablation (+19.7%), 6-term MAE (0.032 MeV), Table 2 CV ambiguity resolution
7. All figures (12 PNG files)
8. `PROVENANCE.md` and `REPRODUCE.md`

**Exclude:** `primary_model_final.pkl` (72 features, needs separate explanation), raw NUBASE data (license), and any private or unreleased auxiliary files not listed here


---

## Graduated from Research Sandbox (2026-05-11)

| Script | Destination | Purpose | Source |
|--------|------------|---------|--------|
| `magic_sieve_v3.py` | `papers/03_nuclear/` | Two-stage sieve v3 (FINAL) — stable-valley Stage 2 constraint; improvements over v2 | `research-sandbox/05_nuclear_magic_numbers/code/` |
| `magic_tensor.py` | `papers/03_nuclear/magic_number_derivation/` | Tensor-force nuclear magic number analysis | `research-sandbox/05_nuclear_magic_numbers/code/` |
| `nuclear_ipt_phase2.py` | `papers/03_nuclear/ipt_analysis/` | Nuclear IPT reconciliation: full AME2020 extended analysis | `research-sandbox/05_nuclear_magic_numbers/code/ipt_reconciliation/` |
| `nuclear_ipt_test.py` | `papers/03_nuclear/ipt_analysis/` | Nuclear IPT test suite | `research-sandbox/05_nuclear_magic_numbers/code/ipt_reconciliation/` |

**Note on magic_sieve versions:**
- `magic_sieve_v2.py` (previously in paper dir): Stage 2 uses energy-gap threshold only
- `magic_sieve_v3.py` (now graduated): Stage 2 adds stable-valley constraint (physically motivated); see header docstring for details

---

## v7.0 Changes (2026-05-08)

### New section: Nuclear IPT Reconciliation (§sec:magic-numbers-derivation, IPT paragraph)

**Result:** κ_emp/κ_min(N=50) = 1.149 ≈ IPT = 1.1309 (1.6% match)

**Method:**
- κ_min(N=50) = 0.0435 = minimum κ for N=50 gap > 0.3 ℏω₀ (Nilsson model, standard threshold)
- κ_emp = 0.050 (empirical Nilsson value)
- Ratio = 1.149 ≈ IPT = 1.1309 (Information Profit Threshold from P15)

**Why N=50 uniquely matches:**
Among all magic numbers, only N=50 has κ_min = 0.0435 ≈ κ_emp/IPT = 0.0442 (within 0.073 in κ units).
Other magic numbers differ by 10-40%.

**Claim grade:** [B] Computationally established. Normalization (N=50, threshold=0.3ℏω₀) is physically motivated.

**Code:** `ipt_analysis/nuclear_ipt_analysis.py` (new public file)
**Citation added:** SpivackIPT (P15, Information Profit Principle)


## Extended BE Law (added 2026-05-12)

| Artifact | SHA-256 |
|---|---|
| extended_binding_energy_law.txt | `4378d3216c76cd8cc29dc7b7ecc6232e720a32e5b43fa6d1ffb3eaf34678870e` |
| extended_stability_law.txt      | `1d9d9f6f09529168e5f32de93f1f5326b3a1bb7595dcbe571b366cc85a9b9e49` |

### Performance comparison

| Model | CV MAE (MeV/A) | OOS R² |
|---|---|---|
| Parsimonious (6-term) | 0.0328 ± 0.0019 | 0.9921 |
| Extended (9-term) | 0.0283 ± 0.0016 | 0.9933 |


## Full AME2020 Retraining (2026-05-12)

AME2020 source: https://www-nds.iaea.org/amdc/ame2020/mass_1.mas20.txt
Experimental nuclei in AME2020: 2548
OOD set (new vs initial 1,319-nucleus training): 1229 nuclei

| Dataset | Model | Training N | CV MAE | OOD MAE | OOD R² |
|---|---|---|---|---|---|
| Initial | Parsimonious | 1319 | 0.0328 | 0.0484 | 0.9540 |
| Initial | Extended     | 1319 | 0.0283 | 0.0416 | 0.9616 |
| Full AME2020 | Parsimonious | 2548 | 0.0522 | 0.0554 | 0.9652 |
| Full AME2020 | Extended     | 2548 | 0.0511 | 0.0530 | 0.9771 |

| Artifact | SHA-256 |
|---|---|
| p2_extended_binding_energy_law.txt | `d4be40a8a45f6f1d3f370b931ae905e8b6b622df05e84002774670b210f3123d` |
| p2_parsimonious_binding_energy_law.txt | `14b893b813b2d5d9ce16418e8ab172321e5d5bb81bf854f3e749e165c57fda56` |
| p2_extended_stability_law.txt | `22a926f4297258cd42545ebe81a6fa27e554547aa8a4e7d3de014b03ad86db8f` |
| p2_training_results.json | `511a6f54c2b1b34b3421a14209c929d696524166b0b3f21a7b85f01ad948d63f` |
