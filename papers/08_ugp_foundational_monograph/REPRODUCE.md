# REPRODUCE — Foundational UGP monograph

All commands assume a POSIX shell and paths relative to the **clone root** of [`ugp-physics`](https://github.com/novaspivack/ugp-physics). The monograph sources and `ugp_release/` bundle live under **`papers/08_ugp_foundational_monograph/`**.

## 1. Python environment (figures / atlas tooling)

```bash
cd papers/08_ugp_foundational_monograph/ugp_release
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python3 test_phase3.py
```

**Expected:** Phase 3 test completes and reports matplotlib/numpy versions. This validates plotting and CSV generation paths used by the release bundle.

**Stack:** See `papers/08_ugp_foundational_monograph/ugp_release/requirements.txt` (matplotlib, numpy, pandas; optional seaborn; streamlit optional for the Universe Finder UI).

## 2. Generate atlas-style outputs (Fibonacci histogram, basin plot)

Follow **`UGP_BUILD_INSTRUCTIONS.md`** in `papers/08_ugp_foundational_monograph/`. Typical pattern:

```bash
cd papers/08_ugp_foundational_monograph
# Example: Makefile or scripts under ugp_release/scripts if present in your checkout
# Output directory used by the TeX defaults:
mkdir -p ./ugp_v2_out/atlas
```

Then compile the PDF with `\DataDir` pointing at that folder so `pgfplotstable` and `\TryPathsGraphic` resolve data and images:

```bash
cd papers/08_ugp_foundational_monograph
pdflatex -interaction=nonstopmode '\def\DataDir{./ugp_v2_out/atlas}\input{Universal_Generative_Principle_UGP_Paper.tex}'
bibtex Universal_Generative_Principle_UGP_Paper
pdflatex ...
pdflatex ...
```

Or use `latexmk` with the same `\def\DataDir{...}` prefix as documented in the TeX preamble comments.

## 3. Minimal PDF build (no generated data)

If atlas outputs are missing, the manuscript still compiles; missing graphics show framed placeholders where `\MaybeGraphic` / `\TryPathsGraphic` apply.

```bash
cd papers/08_ugp_foundational_monograph
pdflatex -interaction=nonstopmode Universal_Generative_Principle_UGP_Paper.tex
bibtex Universal_Generative_Principle_UGP_Paper
pdflatex ...
pdflatex ...
```

Ensure `../bib/Spivack_Papers_Bibliography.bib` exists relative to this directory (shared bibliography at `papers/bib/`).

## 4. Optional: Streamlit Universe Finder

```bash
cd papers/08_ugp_foundational_monograph/ugp_release
streamlit run streamlit_universe_finder.py
```

Not required to reproduce static numbers in the PDF; useful for interactive exploration.

## 5. Machine-checked proofs (external)

Clone **`ugp-lean`** from GitHub and run `lake build` per the Zenodo record cited in the bibliography (`ugp-lean` entry in `Spivack_Papers_Bibliography.bib`). This epic does not modify that repository (SD-0).

## 6. Ridge scan helpers (root folder)

`papers/08_ugp_foundational_monograph/scripts/main_n10_ridge.py` is a manuscript-adjacent utility; exact CLI flags may vary. Prefer `papers/08_ugp_foundational_monograph/ugp_release/ugp_cli.py` when a unified entry point is available in your checkout.
