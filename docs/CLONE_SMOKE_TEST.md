# Clone smoke test (repeatable)

Use this checklist after a **fresh clone** (or before a public release) to confirm the tree installs cleanly and the main entry points run. It mirrors the smoke test used for release readiness: **venv → pip → `ugp` CLI → UGP_GTE_SM_Verifier fullstack → discovery engine quick run → cleanup**.

---

## Prerequisites

- **Git** and **Git LFS** (`git lfs install` once per machine; `git lfs pull` after clone if you need LFS-tracked assets — see root `README.md` and `.gitattributes`).
- **Python 3.10 or newer** for `ugp_discovery_lab` (`pyproject.toml`). On macOS, **`python3` is often still 3.9.x** — use `python3.12 -m venv`, conda, Homebrew, or pyenv; do not rely on `/usr/bin/python3` alone.
- Optional: a full TeX stack only if you repeat the **paper PDF rebuild** section.

---

## 1. Fresh clone

```bash
# Example; use your fork or upstream URL.
git clone <repository-url> ugp-physics
cd ugp-physics
git lfs pull    # if you need CSV/parquet/LFS blobs for downstream steps
```

---

## 2. Create a disposable venv

Use an explicit 3.10+ interpreter (adjust the path to your install):

```bash
python3.12 -m venv /tmp/ugp_physics_smoke_venv
# e.g. conda: conda create -n ugp-smoke python=3.12 -y && conda activate ugp-smoke

source /tmp/ugp_physics_smoke_venv/bin/activate   # Windows: \path\to\venv\Scripts\activate
python --version   # expect 3.10.x or newer
```

---

## 3. Install dependencies

From the **repository root**:

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -e "ugp_discovery_lab/[plots]"
```

Sanity import:

```bash
python -c "import ugp_discovery_lab; print('ok')"
```

---

## 4. UGP Discovery Lab CLI

Still at repo root, with the venv activated:

```bash
ugp list-experiments
```

**Expected:** process exits `0` and lists experiment names. Avoid piping to `head` when checking logs (a closed pipe can trigger harmless `BrokenPipeError` noise from the logger).

---

## 5. Monolith (GTE verifier v8), fullstack mode

This exercises the default **fullstack** path (cascade checks, phase‑1 suite, test batteries, echoes, UCL artifacts, report). From **repository root**:

```bash
cd UGP_GTE_SM_Verifier
python UGP_GTE_SM_Verifier.py --mode fullstack --quiet
cd ..
```

**Expected:** exit code `0`. Runtime is typically on the order of **tens of seconds** on a modern machine (not the multi-hour discovery runs).

**Lighter alternative** (if you only need a fast import/exec check):

```bash
cd UGP_GTE_SM_Verifier
python UGP_GTE_SM_Verifier.py --mode phys --quiet
cd ..
```

---

## 6. Discovery engine (short discover run)

Exercises the **discovery** CLI and UGP_GTE_SM_Verifier import used by the engine. From **repository root**:

```bash
cd discovery_engine
python Verifier_discovery_engine_v4.py run \
  --mode discover_new \
  --preset fermion_only_quick \
  --max-new-particles 1000
cd ..
```

**Expected:** exit code `0` within a few seconds to a few minutes depending on hardware.

---

## 7. Clean up local run outputs (recommended)

Smoke tests write **untracked** artifacts under `UGP_GTE_SM_Verifier/` and `discovery_engine/`. Remove them so `git status` stays clean (paths are safe to delete; they are regenerated on the next run):

```bash
rm -rf UGP_GTE_SM_Verifier/Verifier_reports
rm -rf discovery_engine/discovery_runs
rm -f UGP_GTE_SM_Verifier/ucl_coeff_palette_deltas.csv \
      UGP_GTE_SM_Verifier/ucl_geometry_certificate.json \
      UGP_GTE_SM_Verifier/ucl_geometry_certificate.md \
      UGP_GTE_SM_Verifier/ucl_iso_sigma_solutions.json \
      UGP_GTE_SM_Verifier/ucl_lock_certificate.json \
      UGP_GTE_SM_Verifier/ucl_lock_certificate.md \
      UGP_GTE_SM_Verifier/ucl_pslq_best.json \
      UGP_GTE_SM_Verifier/ucl_pslq_catalog.json \
      UGP_GTE_SM_Verifier/universal_calibration_law.json \
      UGP_GTE_SM_Verifier/universal_calibration_law.md
```

---

## 8. Remove the disposable venv (save disk space)

```bash
deactivate 2>/dev/null || true
rm -rf /tmp/ugp_physics_smoke_venv
```

---

## Optional — rebuild key paper PDFs

Not required for the Python smoke test. If you need PDFs aligned with the current TeX and bibliography, from a **TeX Live** install:

```bash
# Dynamics
cd papers/04_dynamics
latexmk -pdf -interaction=nonstopmode -halt-on-error ugp_dynamics_universality.tex
cd ../..

# Meta-laws
cd papers/07_meta_laws
latexmk -pdf -interaction=nonstopmode -halt-on-error ugp_meta_laws.tex
cd ../..

# Standard Model (e.g. after correspondence email changes)
cd papers/01_SM
latexmk -pdf -interaction=nonstopmode -halt-on-error standard_model_from_ugp.tex
cd ../..

# GTE spectrum paper (biblatex + biber — use pdflatex/biber if latexmk lacks biber integration)
cd papers/02_GTE_spectrum
pdflatex -interaction=nonstopmode -halt-on-error Particle_Spectrum_From_UGP_Paper.tex
biber Particle_Spectrum_From_UGP_Paper
pdflatex -interaction=nonstopmode -halt-on-error Particle_Spectrum_From_UGP_Paper.tex
pdflatex -interaction=nonstopmode -halt-on-error Particle_Spectrum_From_UGP_Paper.tex
cd ../..
```

Paper-specific details live in each folder’s `REPRODUCE.md`.

---

## Pass criteria

- **Steps 3–6** complete with **exit code 0** and no unexpected tracebacks.
- `git status` is **clean** after step 7 (or only shows intended PDF changes if you ran the optional section and choose to commit them).

---

## Changelog

- **2026-04-16** — Initial version (clone + venv + pip + `ugp` + UGP_GTE_SM_Verifier fullstack + discovery quick run + cleanup + optional LaTeX).
