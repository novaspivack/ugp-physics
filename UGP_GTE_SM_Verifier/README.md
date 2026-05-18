# GTE Verifier Monolith — v8

Single-file, deterministic verifier and report generator for the **S\[I\]-GTE Universal Calibration Law (UCL)**, with an integrated multi-sector physics engine and the full **UGP → GTE derivation stack**.

The script is self-contained and reproducible (NumPy only at minimum; matplotlib and SciPy optional). All results are deterministic at fixed canonical knobs. It emits JSON / CSV / Markdown / TeX artifacts suitable for auditing and peer review.

---

## Files in this directory

| File | Purpose |
|---|---|
| `UGP_GTE_SM_Verifier.py` | The verifier. All physics, derivation, scoring, and reporting. |
| `higgs_canonical.py` | Standalone Higgs-triple constructor (knob-free, UGP + mirror path). |
| `neutrino_canonical.py` | Standalone neutrino-triple constructor and number-theory helpers. |
| `ucl_certificates.py` | Pure UCL certificate utilities: Quarter-Lock residuals, Fisher/Hessian geometry echoes, PSLQ exact-form candidates. |

---

## What UGP_GTE_SM_Verifier does

**Primary verdict** — tests the formal UCL proof path and the parameter-free W-boson ρ-law invariant. These are the two metrics that determine PASS/FAIL.

**Physics engine** (supplementary and auditable) — Yukawa couplings, CKM matrix (two independent paths), PMNS matrix, electroweak echoes, 1-loop RGEs, anomaly cancellation proofs, Higgs sector, neutrino forecasts, hadron echoes, information geometry.

**Anti-overfitting batteries** — permutation nulls, LOOCV ridge probe, MDL/DOF accounting, broad-flat-optimum sweeps, noise-sensitivity, coefficient-jitter robustness.

**Reproducibility** — SHA-256 digests of code, coefficient vector, and canonical triples are embedded in every report. A reference-lock / verify workflow allows exact regression-to-baseline checks.

**V7/V8 additions** — dual-path comparison (empirical vs. theoretically derived UCL coefficients); 3-parameter URC generating function (`α_QCD`, `α_EW`, `α_symmetry`); fully theoretical grand synthesis.

---

## Requirements

```bash
pip install numpy scipy matplotlib sympy mpmath
```

All packages are listed in `requirements.txt` at the repository root. To install everything at once:

```bash
pip install -r requirements.txt
```

**Python 3.10 or later is recommended.**  
NumPy is the only hard dependency. matplotlib adds plots; SciPy enables some auxiliary paths; mpmath is required by `ucl_certificates.py` (PSLQ).

---

## Canonical knobs

| Knob | Canonical value | Flag |
|---|---|---|
| Phase mode | `dimless` | `--phase-mode dimless` |
| Phase scaling k | `2.0` | `--phase-k 2.0` |
| N-renorm K | `1400` | `--renorm-K 1400` |

All presets below use these canonical knobs. The report header badges show the active knob values and SHA-256 digests for every run.

---

## Paper replication runs

### Paper 1 — Standard Model from UGP (`papers/01_SM/`)

**Single command reproducing all SM paper results:**

```bash
cd UGP_GTE_SM_Verifier
python3 UGP_GTE_SM_Verifier.py \
    --preset-fullstack --n 10 --full-derivation 1
```

All outputs go to a timestamped directory: `UGP_GTE_SM_Verifier/Verifier_reports/Verifier_V8_run_mode-fullstack_n10_fd1_YYYYMMDD-HHMMSS/`

**Expected runtime:** 3–8 minutes on a modern laptop.

**Expected key results:**
- Primary σ (empirical): 4.364 × 10⁻⁵ %
- Primary σ (theoretical): 0.293 %
- W-ρ: 1.04900 (PASS)
- Baryon RMS (theoretical): 0.01 %
- Fine-structure constant: +2.39 ppm vs CODATA

**Hash verification (regression check):**

```bash
cd UGP_GTE_SM_Verifier
python3 UGP_GTE_SM_Verifier.py \
    --verify-reference --n 10
```

**Derived CKM matrix (Appendix §8.1):**

```bash
cd UGP_GTE_SM_Verifier
python3 -c "
import importlib.util, pathlib, sys, json
p = pathlib.Path('UGP_GTE_SM_Verifier.py')
s = importlib.util.spec_from_file_location('v8', p)
m = importlib.util.module_from_spec(s)
sys.modules['v8'] = m; s.loader.exec_module(m)
r = m.ckm_from_ugp_derived()
print(json.dumps(r, indent=2, default=str))
"
```

**PMNS QLC/TM2 derivation (§8.2):**

```bash
cd UGP_GTE_SM_Verifier
python3 -c "
import importlib.util, pathlib, sys, json
p = pathlib.Path('UGP_GTE_SM_Verifier.py')
s = importlib.util.spec_from_file_location('v8', p)
m = importlib.util.module_from_spec(s)
sys.modules['v8'] = m; s.loader.exec_module(m)
r = m.pmns_from_ugp_derived()
print(json.dumps(r, indent=2, default=str))
"
```

**Cosmological constant trace (§9.1):**

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

See `papers/01_SM/REPRODUCE.md` for the full artifact manifest and Lean 4 formalization instructions.

---

### Paper 2 — GTE Particle Spectrum (`papers/02_GTE_spectrum/`)

This paper uses the discovery engine (under `discovery_engine/`) rather than UGP_GTE_SM_Verifier directly. UGP_GTE_SM_Verifier is imported as a library by the engine. Requirements: `numpy`, `pandas`, `scipy`, `scikit-learn`, `matplotlib`, `tqdm`; ≥ 16 CPU cores recommended; ≥ 32 GB RAM; ~2 GB disk.

**Step 1 — Discovery run (~25 min, 14 workers):**

```bash
cd discovery_engine
python Verifier_discovery_engine_v4.py run \
    --mode discover_new \
    --preset comprehensive_gte_strict_search \
    --max-new-particles 25000000 \
    --output-dir "discovery_runs/discovery_run_v4_$(date +%Y%m%d-%H%M%S)"
```

Expected: ~1,000,035-row `candidates.csv`; 24 SM-matched candidates.
SHA-256 of canonical `candidates.csv`: `5c113e62468d19fbda73d9df06a3740f1dbd7609c8eee6ecb1ac6039f38f72db`

The frozen `candidates.csv` is bundled in the repository (Git LFS). Steps 2–4 can be run directly against it without re-running Step 1.

**Step 2 — Analytics run (~25 min, 14 workers):**

```bash
cd discovery_engine
python Verifier_discovery_advanced_particle_analysis.py \
    --csv "discovery_runs/<run_id>/candidates.csv" \
    --mass_cutoff 173000.0 \
    --max_curves 8 \
    --trials 5000 \
    --bootstrap_n 200 \
    --nperm 800 \
    --do_lifetime \
    --do_surface \
    --do_consensus \
    --fit_law_family \
    --with_hinge2 \
    --plot_heatmaps \
    --max_workers 14 \
    --out "analytics_$(date +%Y%m%d-%H%M%S)"
```

Expected: law family B ≈ 4.01×10⁻⁶, D ≈ −3.13×10⁻⁶; oscillation period ~100,000 steps (z > 50); consensus anchors: 23,450.

**Step 3 — Paper statistics:**

```bash
cd papers/02_GTE_spectrum
python gather_paper_stats.py
```

**Step 4 — Paper figures:**

```bash
cd papers/02_GTE_spectrum
python generate_paper_figures.py
```

See `papers/02_GTE_spectrum/REPRODUCE.md` for hardening tests, pre-computed robustness artifacts, and the full artifact manifest.

---

### Paper 3 — Nuclear Physics from UGP (`papers/03_nuclear/`)

Requirements: `numpy`, `pandas`, `scikit-learn`, `xgboost`, `matplotlib`, `seaborn`.

**Step 1 — Verify the 6-term analytical laws:**

```bash
cd papers/03_nuclear
python3 - <<'EOF'
import numpy as np, pandas as pd
from sklearn.metrics import mean_absolute_error, accuracy_score

df = pd.read_csv('training_data_with_stability.csv')
Z, N, A = df['Z'].values.astype(float), df['N'].values.astype(float), df['A'].values.astype(float)

f1 = np.log(N*(N-1)/A + 1)
f2 = np.log(A**(2/3) + 1)
f3 = np.log(Z*(Z-1)/A + 1)
f4 = ((N-Z)/A)**2
f5 = np.exp(-Z*(Z-1)/(100*A))
f6 = np.exp(-N*(N-1)/(100*A))
X6 = np.column_stack([f1, f2, f3, f4, f5, f6])

means  = np.array([3.6187, 3.1879, 3.0213, 0.0324, 0.7988, 0.6564])
scales = np.array([0.7545, 0.4417, 0.6442, 0.0250, 0.0904, 0.1602])
X6_sc = (X6 - means) / scales

be_weights = np.array([0.6624, 0.4447, 0.2003, -0.4237, 1.1843, 0.2147])
y_pred_be = 8.026758 + X6_sc @ be_weights
print(f'6-term BE law MAE: {mean_absolute_error(df["BE_per_A"], y_pred_be):.4f} MeV/A  (expected: 0.032)')

stab_weights = np.array([0.3821, 0.1088, 0.3421, -0.0361, 0.5207, 0.5349])
stab_pred = ((0.749810 + X6_sc @ stab_weights) >= 0.0).astype(int)
print(f'6-term stability accuracy: {accuracy_score(df["Is_Stable"].astype(int), stab_pred)*100:.1f}%  (expected: 96.2%)')
EOF
```

Expected: BE law MAE **0.032 MeV/A**; stability training accuracy **~96.2%**.

**Step 2 — Ablation study (GTE vs Physics features):**

```bash
cd nuclear
cp ../papers/03_nuclear/training_data_with_stability.csv filtered_experimental_dataset.csv
python ablation_study.py
```

Expected: GTE-only CV MAE ~3.96 MeV; physics-only ~5.19 MeV; GTE improvement ~20–23%.

**Step 3 — Periodic table generation (Z=1–190):**

```bash
cd nuclear
python Verifier_periodic_table_final.py
```

Generates `periodic_table_data.csv`.

See `papers/03_nuclear/REPRODUCE.md` for the full artifact manifest including bundled ML oracle models.

---

## General-purpose runs

### Reference run (canonical knobs, writes lock)

```bash
cd UGP_GTE_SM_Verifier
python3 UGP_GTE_SM_Verifier.py \
    --preset-reference
```

### Verify against a saved reference lock

```bash
cd UGP_GTE_SM_Verifier
python3 UGP_GTE_SM_Verifier.py \
    --verify-reference --ref-path reference_lock.json
```

### Maximum report (all sections embedded, one command)

```bash
cd UGP_GTE_SM_Verifier
python3 UGP_GTE_SM_Verifier.py \
    --maximum-report
```

### Phase I physics suite

Emits Yukawa couplings, CKM (both paths), electroweak echoes, anomaly proof, and Lagrangian TeX.

```bash
cd UGP_GTE_SM_Verifier
python3 UGP_GTE_SM_Verifier.py \
    --phase1-suite
```

### 1-loop RGE evolution

```bash
cd UGP_GTE_SM_Verifier
python3 UGP_GTE_SM_Verifier.py \
    --rge-to-scale 1e16 --rge-method rk4
```

### PMNS suite (preferred mode: seesaw_structured)

```bash
cd UGP_GTE_SM_Verifier
python3 UGP_GTE_SM_Verifier.py \
    --emit-pmns --pmns-mode seesaw_structured
```

> **Note:** `--pmns-mode unistochastic` and `--pmns-deterministic` are deprecated — they produce an incorrect CP phase (~97° vs the correct ~39°) and are retained only for regression testing.

### V8 fully theoretical grand synthesis

```bash
cd UGP_GTE_SM_Verifier
python3 UGP_GTE_SM_Verifier.py \
    --run-fully-theoretical
```

### Anti-overfitting batteries

```bash
cd UGP_GTE_SM_Verifier
python3 UGP_GTE_SM_Verifier.py \
    --run-nulls --nulls-trials 1000 \
    --run-uncertainty --unc-n-jitter 1.0 --unc-trials 500 \
    --run-dof-ledger \
    --run-bfopt
```

### Atlas sweep across n values

```bash
cd UGP_GTE_SM_Verifier
python3 UGP_GTE_SM_Verifier.py \
    --sweep 8,10,12,16
```

### Extreme mode (everything in one pass)

```bash
cd UGP_GTE_SM_Verifier
python3 UGP_GTE_SM_Verifier.py \
    --extreme
```

---

## Output artifacts

All artifacts are written to a timestamped run directory created automatically alongside the script.

| Artifact | Description |
|---|---|
| `gte_report_*.md` | Main Markdown report with embedded badges, tables, and optional appendices |
| `reference_lock.json` | Frozen Primary σ, W ρ, and key masses for regression checks |
| `freeze_manifest_reference.json` | Full coefficient / triple / code hash manifest |
| `artifact_manifest.{json,csv}` | SHA-256 hashes of all outputs |
| `derived_triples.json` | UGP → GTE derivation provenance (with `--full-derivation`) |
| `dual_path_comparison.json` | Empirical and theoretical mass predictions side by side |
| `yukawas.json` / `yukawas.csv` | Diagonal Yukawa couplings from predicted pole masses |
| `ckm_path_A.json` / `ckm_path_B.json` | CKM matrices (ρ-matrix path and mass-ratio path) |
| `ewk_echoes.json` | sin²θ_W and ρ-echo at M_Z |
| `anomaly_proof.json` | Exact rational anomaly cancellation per generation |
| `lagrangian_sm_from_gte.tex` | LaTeX Lagrangian snippet with numeric Yukawas and couplings |
| `pmns_report.json` | Complex U_PMNS, magnitudes, mixing angles, δ_CP, J_CP |
| `rge_trace.json` | 1-loop RGE coupling evolution trace |
| `dof_ledger.{json,csv}` | DOF/MDL accounting |
| `nulls_suite.{json,csv}` | Permutation null distributions |
| `Verifier_bundle_*.zip` | Zipped report + manifest |

---

## Reproducibility notes

- **No network access.** Everything is self-contained.
- SHA-256 digests of the code file, coefficient vector, and canonical triples are embedded in every report header. Match these to confirm you are running the same version.
- The canonical knobs (`dimless`, k=2.0, K=1400) are the only inputs that affect the Primary verdict. All other flags add supplementary physics without touching the Primary path.
- To reproduce a prior run exactly: match the knobs shown in the report header badges, use `--verify-reference` against the saved `reference_lock.json`.

## Reviewer / replicator quick-start

UGP_GTE_SM_Verifier can emit its own reviewer guide from the live codebase:

```bash
cd UGP_GTE_SM_Verifier
python3 UGP_GTE_SM_Verifier.py --write-help-md
```

For the canonical replication runs, see the `REPRODUCE.md` files in each `papers/` subdirectory.
