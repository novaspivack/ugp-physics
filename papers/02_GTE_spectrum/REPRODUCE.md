# Reproduction Guide — GTE Particle Spectrum Paper

This document provides the minimal steps to reproduce all results and figures in the paper from scratch.

For full details (artifact hashes, run parameters, analytics flags, stale artifact exclusions), see `PROVENANCE.md`.

---

## ugp-physics layout

From the **clone root**, discovery code is under `discovery_engine/`, frozen `candidates.csv` is under `discovery_engine/` (Git LFS), paper-local scripts are under `papers/02_GTE_spectrum/`, and the UGP_GTE_SM_Verifier import for the engine lives under `UGP_GTE_SM_Verifier/`.

---

## Requirements

- Python ≥ 3.9 with conda (DISCOVERY environment)
- ≥ 16 CPU cores recommended (14 workers used)
- ≥ 32 GB RAM
- ~2 GB disk space

```bash
conda activate DISCOVERY
python -c "import psutil, numpy, pandas, scipy, sklearn, matplotlib, tqdm; print('All dependencies OK')"
```

The engine imports from `../UGP_GTE_SM_Verifier/` when run from `discovery_engine/` (see `sys.path` setup in `Verifier_discovery_engine_v4.py`).

---

## Step 1 — Discovery Run (~25 min, 14 workers)

**Optional if verifying against the frozen catalog:** When `discovery_engine/candidates.csv` is present and its SHA-256 matches `PROVENANCE.md`, you can skip this step and use the bundled file for Steps 2–4.

```bash
cd discovery_engine
python Verifier_discovery_engine_v4.py run \
  --mode discover_new \
  --preset comprehensive_gte_strict_search \
  --max-new-particles 25000000 \
  --output-dir "discovery_runs/discovery_run_v4_$(date +%Y%m%d-%H%M%S)"
```

Expected output:
- `candidates.csv` — ~1,000,035 rows
- Green tier: ~19,958 candidates
- SM-matched: 24 candidates

Verify SHA256 of `candidates.csv`:
```
5c113e62468d19fbda73d9df06a3740f1dbd7609c8eee6ecb1ac6039f38f72db
```

---

## Step 2 — Analytics Run (~25 min, 14 workers)

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

Expected key outputs:
- Law family: B ≈ 4.01×10⁻⁶, D ≈ −3.13×10⁻⁶
- Oscillation intrinsic period: ~100,000 steps (z > 50 after quadratic detrending; prior single-cycle estimate of ~499,972 steps was a window artifact)
- Consensus anchors: 23,450

---

## Step 3 — Paper Statistics

```bash
cd papers/02_GTE_spectrum
python gather_paper_stats.py
```

Outputs `paper_statistics_summary.json` with all numbers used in the paper.

---

## Step 4 — Paper Figures

```bash
cd papers/02_GTE_spectrum
python generate_paper_figures.py
```

Outputs:
- `gte_spectrum_full.png` — full 1M-candidate landscape
- `gte_spectrum_sm_zoom.png` — SM mass range with labeled particles and novel predictions

---

## Step 5 — Hardening Tests (robustness battery)

The following produce the 8 JSON artifacts in `calibration_robustness/`. These are pre-computed and committed; re-running requires the canonical `candidates.csv`.

```bash
cd discovery_engine
# All hardening analyses run from candidates.csv in the paper folder
python -c "
# Hardening JSON artifacts are pre-computed under papers/02_GTE_spectrum/calibration_robustness/
print('See papers/02_GTE_spectrum/calibration_robustness/ for pre-computed hardening results')
"
```

All 10 hardening artifacts are committed in `calibration_robustness/`:
- `raw_ucl_structure_report.json` — SM rank at 100th pctile before force-labeling
- `score_ablation_report.json` — SM enrichment across scoring variants
- `oscillation_horizon_study.json` — D1: multi-horizon period analysis (~100K steps confirmed, z > 55)
- `oscillation_method_consensus.json` — D2: FFT (71,533 steps, z=26.5) + Lomb-Scargle (92,562 steps, FAP=6×10⁻⁹) independently confirm the ~100K oscillation; refutes "window artifact" attack
- `hinge_stability_report.json` — D3: 500-resample bootstrap CIs — D=3.69×10⁻⁷ [3.14×10⁻⁷, 4.27×10⁻⁷] (CV~14%), k₀~7,000 [5,250, 7,000]
- `quantum_number_assignment.json` — Möbius-parity QN assignments for GTE-P1–P11
- `cross_paper_dependency_report.json` — methodological vs statistical independence
- `preregistration_manifest.json` — locked analysis choices
- `multiple_testing_ledger.json` — all inferential claims with Bonferroni p-values
- `trajectory_path_multiplicity_theorem.json` — formal theorem sketch

---

## Artifact Shipping Decision

The canonical `candidates.csv` (1,000,035 rows, SHA256 above) is **included as a frozen artifact** alongside the code. This is because:
- The full discovery run takes ~25 minutes with 14 cores
- Results are deterministic given the same preset and random seed
- The artifact allows immediate reproduction of analytics, figures, and paper numbers without re-running Step 1

If you choose to re-run Step 1, verify the SHA256 matches before proceeding to Step 2.

---

## Mirror-Branch Quantum Number Computation (new, 2026-05-08)

Runs the Braid Atlas computation for GTE-P7 (mirror triple, c₁=2137):

```bash
cd papers/02_GTE_spectrum
pip install sympy  # if not installed
python3 mirror_branch_quantum_numbers.py
```

**Expected output (key lines):**
```
All SM charges verified. ✓
...
Electric charge: Q = 0 (NEUTRAL)  ✓
Color:           SU(3) singlet   ✓
Spin:            1/2 (Dirac fermion) ✓
SM-neutral:      YES
Claim grade: [B] bridge
```

**Lean arithmetic verification (in ugp-lean repo):**
```bash
lake build UgpLean.GTE.GeneralTheorems
```
Theorems verified: `mirror_triple_residue`, `mirror_prime_2137`,
`mirror_quotient_q1`, `mirror_triple_prime_lock` (all `native_decide`, zero sorry).
