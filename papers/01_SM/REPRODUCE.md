# Reproducing All Results in "A Deterministic Number-Theoretic Framework for the Standard Model Parameter Spectrum"

## ugp-physics (standalone clone)

Assume a clone of [`ugp-physics`](https://github.com/novaspivack/ugp-physics), `pip install -r requirements.txt` at the repo root, and a shell whose working directory you change as below. The Standard Model verifier script lives under **`UGP_GTE_SM_Verifier/`** (not the repo root).

## Prerequisites

- Python 3.9 or later
- `numpy` (any recent version)
- Optional: `matplotlib` (figures), `scipy` (PSLQ searches only)

No GPU, no external optimization, no random seeds.

```bash
pip install numpy matplotlib scipy
```

## Single command: reproduce all SM paper results

```bash
cd UGP_GTE_SM_Verifier
python3 UGP_GTE_SM_Verifier.py \
  --preset-fullstack --n 10 --full-derivation 1
```

All outputs are written to a timestamped directory under `UGP_GTE_SM_Verifier/Verifier_reports/`, e.g.:
`UGP_GTE_SM_Verifier/Verifier_reports/Verifier_V8_run_mode-fullstack_n10_fd1_YYYYMMDD-HHMMSS/`

**Expected runtime:** 3–8 minutes on a modern laptop.

**Expected key outputs:**
- Primary σ (empirical): 4.364 × 10⁻⁵ %
- Primary σ (theoretical): 0.293 %
- W-ρ: 1.04900 (PASS)
- Baryon RMS (theoretical): 0.01 %
- Fine-structure constant: +2.39 ppm vs CODATA

## UCL coefficient audit (dual-path + Elegant Kernel)

After the 2026-04-23 `k_gen` correction (`φ cos(π/10)`, not `π/2` in `calculate_theoretical_coefficients()`), regenerate the frozen comparison bundle:

```bash
cd papers/01_SM/canonical_run
python3 comp_p01_ucl_coeff_audit.py
```

This writes updated `dual_path_comparison.{json,md}`, `theoretical_coefficients.json`, and `fully_theoretical_*` into `canonical_run/` and a timestamped directory under `Verifier_reports/ucl_coeff_audit_*`.

**Expected (2026-05-30 audit):** empirical primary σ ≈ **0.003%**; dual-path “theoretical” σ ≈ **0.295%** (URC + empirical UCL, theoretical `renorm_K`); `k_gen` in `theoretical_coefficients.json` ≈ **1.53884**.

### Verifier modes (see also P01 Appendix D, `UGP_GTE_SM_Verifier/README.md`)

| Mode | Command sketch | What it demonstrates |
|------|----------------|----------------------|
| **Dual-path headline** | `--run-dual-path` + `--coeffs-source empirical` | UCL2.3 both arms; theoretical arm: derived `renorm_K` + URC → ~0.29% σ |
| **Bare Elegant Kernel** | `--coeffs-source limit --run-fully-theoretical` | Full `THEORETICAL_COEFF_VECTOR` in mass pipeline → ~1.1% σ |
| **CMCA mixer audit** | `--imt-mixer-mode cmca` | Structural IMT mixer (≈ v12 for masses today) |

`--run-dual-path` does **not** substitute kernel coefficients into masses; see `dual_path_comparison.json` for coeff **targets** only.

```bash
cd papers/01_SM/canonical_run
python3 UGP_GTE_SM_Verifier.py --n 10 --mode phys --quiet \
  --coeffs-source empirical --imt-mixer-mode v12 --run-dual-path
python3 UGP_GTE_SM_Verifier.py --n 10 --mode phys --quiet \
  --coeffs-source limit --run-fully-theoretical
```

```bash
cd UGP_GTE_SM_Verifier
python3 UGP_GTE_SM_Verifier.py --write-help-md   # fast; writes HELP.md
python3 UGP_GTE_SM_Verifier.py --help            # flags + mode epilog
```

The primary repo copy `UGP_GTE_SM_Verifier/UGP_GTE_SM_Verifier.py` is kept in sync with `canonical_run/UGP_GTE_SM_Verifier.py`.

## Hash verification

```bash
cd UGP_GTE_SM_Verifier
python3 UGP_GTE_SM_Verifier.py \
  --verify-reference --n 10
```

This replays the locked reference run and diffs every output against stored SHA-256 hashes, confirming byte-level reproducibility.

## Derived CKM matrix (Appendix, §8.1)

```bash
cd UGP_GTE_SM_Verifier
python3 -c "
import importlib.util, pathlib, sys, json
p = pathlib.Path(
  'UGP_GTE_SM_Verifier.py')
s = importlib.util.spec_from_file_location('v8', p)
m = importlib.util.module_from_spec(s)
sys.modules['v8'] = m; s.loader.exec_module(m)
r = m.ckm_from_ugp_derived()
print(json.dumps(r, indent=2, default=str))
"
```

## PMNS QLC/TM2 derivation (§8.2)

```bash
cd UGP_GTE_SM_Verifier
python3 -c "
import importlib.util, pathlib, sys, json
p = pathlib.Path(
  'UGP_GTE_SM_Verifier.py')
s = importlib.util.spec_from_file_location('v8', p)
m = importlib.util.module_from_spec(s)
sys.modules['v8'] = m; s.loader.exec_module(m)
r = m.pmns_from_ugp_derived()
print(json.dumps(r, indent=2, default=str))
"
```

## Cosmological constant trace (§9.1)

```bash
python3 -c "
import math
L = math.log2((2**4 * 5**3) / 3)
H0 = 70e3 / 3.0856775814913673e22
c = 299792458.0
Lambda = (math.log(2)/math.pi) * L * H0**2/c**2
print(f'L_model = {L} bits')
print(f'Lambda  = {Lambda} m^-2')
"
```

Expected: `L_model = 9.38082...` bits, `Lambda ≈ 1.185 × 10⁻⁵² m⁻²`.

## Higgs mass self-consistent VEV (§subsec:higgs, OP(iv))

The self-consistent VEV result reduces the bare $9.1\sigma$ Higgs tension to $-2.08\sigma$:

```bash
cd papers/01_SM/canonical_run
python3 comp_p01_HMC_higgs_mass_closure.py
```

Outputs: `comp_p01_HMC_higgs_mass_closure.json` — self-consistent VEV $v_{\rm self} = 246.27$~GeV,
$m_H^{\rm self} = 124.971$~GeV at $-2.08\sigma$ (PDG 2024 $125.20 \pm 0.11$~GeV).
Tension reduced from $9.1\sigma$ (bare) to $-2.08\sigma$ via two-loop $g_2$ running (Grade~C; $M_W$ external anchor).

## EW VEV structural derivation (§subsec:higgs; grade [A−]; P27/VEVProof)

The following scripts (graduated from research sandbox 2026-05-15) produce the structural
EW VEV result $v_{\rm PSC} = 246.16$~GeV ($-0.024\%$ from $v_{\rm PDG}$), Lean-formalized in
`SrrgLean.VEVProof.*` (zero sorry; conditional on one named axiom: `psc_ew_entropy_maximization`).

| Script/File | Description | Key result |
|------------|-------------|-----------|
| `null_discipline_vev_formula.py` | Null-discipline enumeration over 288 structural VEV candidates | Saturation 0.35% — structural, not coincidental |
| `null_discipline_vev_formula.json` | Results: 1 hit within 1% threshold out of 288 candidates | Confirms structural uniqueness |
| `norfleet_connection.py` | Exact identity $D_{\rm Norfleet} + D_{\rm UGP} = \pi - \ln(\pi)$ | Verifies structural connection |
| `two_loop_srrg_correction.py` | $N_{\rm gen,eff} = \ln(\varphi)/(\pi - \ln(2\pi^2))$ structural formula | Two-loop SRRG correction anatomy |
| `two_loop_srrg_correction.json` | $N_{\rm gen,eff} = 3.027$ (0.85% above 3); structural formula exact | Confirms $N_{\rm gen}=3$ base |
| `gap2_genius_team.json` | Gap 2 systematic analysis of $\varphi^{1/3}$ residual | Gap anatomy |
| `genius_team_ngen_eff.json` | $N_{\rm gen,eff}$ anatomy computation | Formula verification |
| `proof_psc_duality_synthesis.md` | Formal synthesis of PSC-duality proof analysis | Proof structure |
| `proof_psc_duality_adam.py` | PSC duality proof attempt (exploratory) | Supporting analysis |
| `proof_psc_duality_jane.py` | PSC duality proof attempt (exploratory) | Supporting analysis |

Run:
```bash
cd papers/01_SM/canonical_run
python3 null_discipline_vev_formula.py
python3 two_loop_srrg_correction.py
python3 norfleet_connection.py
```

The Lean formalization (zero sorry) is in the companion `srrg-lean` repository:
```bash
cd srrg-lean && lake build SrrgLean.VEVProof
```
Modules: `VEVProof.GoldstoneEntropyCorrection`, `VEVProof.PSCEntropyDuality`,
`VEVProof.EWGoldstoneManifold`, `VEVProof.EWVacuumBridge` (all zero sorry).

## Supplementary structural-analysis scripts

The *N_c* structural chain (§3.6 of the main paper), the VV GUT group-theory derivation (§3.1), and the neutrino structural prediction (§6.4) are each verified by standalone Python scripts in `papers/01_SM/canonical_run/`.  Each script is independently reproducible, runs in under a minute, and emits a JSON artifact with a SHA-256 hash.

```bash
cd papers/01_SM/canonical_run

# Lepton-sector anchor and S_3 structural observations
python3 comp_p01_K_charged_lepton_integer_search.py
python3 comp_p01_L_koide_from_s3.py
python3 comp_p01_N_koide_anchored_composite.py
python3 comp_p01_R_koide_S3_quadric.py

# TT/VV mass relations
python3 comp_p01_TT_up_lepton_cyclotomic_identity.py
python3 comp_p01_VV_down_linked_to_up_lepton.py
python3 comp_p01_XX_gut_structure_search.py

# E_base foundations (Casimir, orbit volume, det-ratio, Fibonacci, MFRR, U(1) correction)
python3 comp_p01_EBF_01_casimir_type_modulation.py
python3 comp_p01_EBF_02_orbit_volume_holographic.py
python3 comp_p01_EBF_03_det_ratio_null_and_corrections.py
python3 comp_p01_EBF_04_fibonacci_generation_hierarchy.py
python3 comp_p01_EBF_05_mfrr_reflexive_landauer_bridge.py
python3 comp_p01_EBF_06_type_mod_u1_correction.py

# N_c structural chain → Koide angle from N_c = 3
python3 comp_p01_EBF_09_deep_muon_structure.py
python3 comp_p01_EBF_11_koide_angle_structural_search.py
python3 comp_p01_EBF_12_top_quark_and_s3_angle.py
python3 comp_p01_EBF_13_s3_koide_angle_proof.py

# VV GUT group theory
python3 comp_p01_EBF_14_vv_rg_flow.py
python3 comp_p01_EBF_15_vv_gj_su5_full.py
python3 comp_p01_EBF_16_vv_gut_group_theory.py

# Neutrino sector structural prediction
python3 comp_p01_EBF_17_neutrino_survey.py
python3 comp_p01_EBF_18_neutrino_126_bridge.py
python3 comp_p01_EBF_19_neutrino_29_9_derivation.py
python3 comp_p01_EBF_20_neutrino_absolute_scale.py
python3 comp_p01_EBF_21_neutrino_29_9_structural_decomp.py
python3 comp_p01_EBF_22_neutrino_full_mechanism.py
python3 comp_p01_EBF_23_MGUT_from_UGP_gauge.py
python3 comp_p01_EBF_24_SO10_CG_majorana.py
```

Each script is independent and can be run in any order.  Requirements: Python 3.9+, `numpy`.  A subset (`comp_p01_EBF_15`, `comp_p01_EBF_16`, `comp_p01_EBF_24`) additionally uses `sympy` for exact group-theory computations.  Per-script descriptions and SHA-256 hashes for the committed JSON outputs are in `PROVENANCE.md`.

## Lean 4 formalization (ugp-lean)

The machine-checked proofs are in the companion Lean 4 repository:

```bash
git clone https://github.com/novaspivack/ugp-lean
cd ugp-lean
lake build
```

A successful build with no `sorry` warnings confirms all theorems (zero sorry policy).
See `MANIFEST.md` for the theorem index.

## Artifact manifest

Every run produces `artifact_manifest.{json,csv}` containing SHA-256 hashes of all outputs, enabling bit-exact reproducibility verification across machines and Python versions.

## Key artifacts produced

| File | Contents |
|------|----------|
| `dual_path_comparison.json` | Empirical and theoretical mass predictions |
| `reference_lock.json` | Frozen primary score and key observables |
| `CANONICAL_HASHES.md` | SHA-256 hashes for 2026-05-30 canonical bundle |
| `ckm_report_ugp_derived.json` | Derived CKM (τ(1008)/D₁ formula) |
| `pmns_report_ugp_derived.json` | Derived PMNS (QLC + TM2) |
| `seesaw_from_ugp.json` | Neutrino masses, δ_CP, M_R scales |
| `ewk_couplings_from_gte.json` | Gauge couplings g₁, g₂ |
| `dof_ledger.{json,csv}` | DOF/MDL accounting |
| `nulls_suite.{json,csv}` | Permutation null distributions |
| `ucl_lock_certificate.{json,md}` | Quarter-Lock residual |
| `anomaly_proof.json` | Gauge anomaly cancellation |
| `Verifier_runs/cosmological_lambda_L_model_trace.json` | Λ derivation trace |

---

## Repository layout (this archive)

The following paths are part of the public `ugp-physics` repository:

### Code (required — one file does everything)
| File | Location | Notes |
|------|----------|-------|
| `UGP_GTE_SM_Verifier.py` | `UGP_GTE_SM_Verifier/` | Primary location; run from this directory |
| `UGP_GTE_SM_Verifier.py` | `papers/01_SM/canonical_run/` | Convenience copy; graduated 2026-05-12 |
| `REPRODUCE.md` | `papers/01_SM/` | This file |

> **Note (2026-05-12):** The "Code Availability" section in the paper (§Code Availability) lists
> `papers/01_SM/canonical_run/UGP_GTE_SM_Verifier.py`. The canonical run instructions use
> `cd UGP_GTE_SM_Verifier` (repo root). A convenience copy has been added to `canonical_run/`
> to resolve the discrepancy; both files are kept in sync.
>
> **Note (2026-05-30):** `calculate_theoretical_coefficients()` now uses `k_gen = φ cos(π/10)` per Lean
> `thm_ucl2_fully_unconditional` (commit `3762f9e4` updated the paper/JSON only; Python aligned 2026-05-30).
> Use `comp_p01_ucl_coeff_audit.py` to refresh frozen `dual_path_comparison.json`.

### Companion formalization
| Resource | URL | Notes |
|----------|-----|-------|
| `ugp-lean` | https://github.com/novaspivack/ugp-lean | Lean 4 machine-checked proofs |

### Canonical run artifacts (required — from a verified fullstack run)
These live under `UGP_GTE_SM_Verifier/Verifier_reports/`. A frozen bundle may also be archived under `papers/01_SM/` when published.

| File | Contents |
|------|----------|
| `dual_path_comparison.json` | Empirical + theoretical mass predictions |
| `reference_lock.json` | Frozen primary score + key observables |
| `artifact_manifest.{json,csv}` | SHA-256 hashes of all outputs |
| `ckm_report_ugp_derived.json` | Derived CKM (τ(1008)/D₁) |
| `pmns_report_ugp_derived.json` | Derived PMNS (QLC + TM2) |
| `seesaw_from_ugp.json` | Neutrino masses, δ_CP, M_R |
| `ewk_couplings_from_gte.json` | Gauge couplings g₁, g₂ |
| `dof_ledger.{json,csv}` | DOF/MDL accounting |
| `nulls_suite.{json,csv}` | Permutation null distributions |
| `ucl_lock_certificate.{json,md}` | Quarter-Lock residual |
| `ucl_geometry_certificate.{json,md}` | Fisher metric + curvature |
| `ucl_pslq_catalog.json` | PSLQ algebraic identifications |
| `grand_synthesis_audit.json` | Full particle audit table |
| `anomaly_proof.json` | Gauge anomaly cancellation |
| `preregistration.{md,json}` | Locked prediction capsule |
| `gte_cascade_derivation.json` | N-value cascade verification |

### Companion artifact archive (alongside paper)
| File | Location | Notes |
|------|----------|-------|
| `cosmological_lambda_L_model_trace.json` | `Verifier_runs/` | Λ derivation trace |
| `te1e_frw_validation_run_..._summary.json` | `Verifier_runs/` | FRW dynamical consistency |

### Figures (required)
All `*.png` from the canonical run's output folder.

### What NOT to include
- Raw `.db` database files
- `Backups/` folder (old v4, v7 verifier scripts)
- Private paths or internal development notes (specs, internal docs)
- `/tmp/*.log` files
- Any file referencing absolute local paths

---

## Lean verification: Two-Layer PSC enumeration

The generation-count constraint $N_{\mathrm{gen}} = 3$ from the Layer~I PSC filter is
machine-certified in `ugp-lean/UgpLean/TE22/ScanCertificate.lean`:

```bash
git clone https://github.com/novaspivack/ugp-lean.git
cd ugp-lean
lake build UgpLean.TE22.ScanCertificate
```

| Theorem | Statement |
|---------|-----------|
| `universe_params_card` | `Fintype.card UniverseParams = 34560` |
| `psc_enumeration_forces_ngen_3` | Every PSC-admissible universe has $N_{\mathrm{gen}} = 3$ |
| `psc_12_survivors_have_ngen_3` | 12 Layer~I survivors, all with $N_{\mathrm{gen}} = 3$ |
| `psc_admissible_forces_sm_gauge` | Every PSC-admissible universe is SM gauge in 4D |

All theorems: zero `sorry`, discharged by `native_decide`.

## GTE vs PDG Comparison Verifier

**Script:** `scripts/gte_pdg_verifier.py`  
**Purpose:** Compares all GTE predictions against PDG 2024 (default) and NuFIT 6.0 IC24 NH reference values. Reports σ deviations and improvement/regression vs PDG 2022.  
**Run:** `python3 scripts/gte_pdg_verifier.py` (PDG 2024 default)  
**Compare mode:** `python3 scripts/gte_pdg_verifier.py --mode compare`  
**Note:** This is the PDG comparison tool only. The mass-prediction engine is in `UGP_GTE_SM_Verifier/`.  
**Reference:** PDG 2024 (Navas et al., Phys. Rev. D 110, 030001); NuFIT 6.0 (JHEP 12 (2024) 216).

---

## Citation

If you use this code, please cite:

> N. Spivack, "A Deterministic Number-Theoretic Framework for the Standard Model Parameter Spectrum," 2026.
> Code: https://github.com/novaspivack/ugp-physics (DOI to be assigned upon publication).
