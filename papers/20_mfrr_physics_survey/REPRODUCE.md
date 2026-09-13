# REPRODUCE — Paper 20: Mathematical Foundations of Reflexive Reality: A Survey

**Paper:** `MFRR_Physics_Survey.tex`
**Last verified:** 2026-05-09

---

## Nature of This Paper

This is a **survey paper** summarizing the formal and computational results of
the MFRR programme. It does not introduce new computations or experiments of
its own. All results it reports are derived and verified in companion papers
and codebases.

---

## Review Methodology

The survey collates results from:

1. **Lean 4 formalization** (`ugp-lean`, `nems-lean`): zero sorry, zero custom axioms.
2. **Computational experiments** (297 Python modules, ~210,000 lines, 57,337+ runs).
3. **Companion papers**: P01 (SM derivation), P02 (GTE spectrum),
   P18 (Koide cyclotomic-12 closed form), P19 (cyclotomic-12 mass structure),
   P21 (neutrino masses), P22 (UGP dynamics), and others.

Each claim in the survey is tagged with an epistemic label:
- **[T]** Machine-checked theorem (Lean 4, zero sorry)
- **[B]** Bridge claim (conditional on stated premises)
- **[C]** Computationally certified (SHA-256 provenance)
- **[I]** Interpretive framework

---

## 1. Verify Lean theorems cited in Appendix A

```bash
# ugp-lean (primary Lean library)
git clone https://github.com/novaspivack/ugp-lean
cd ugp-lean
lake exe cache get
lake build
# Expected: Build completed successfully. 0 errors. 0 sorry.

# nems-lean (NEMS theorem library — available via Zenodo DOI in paper)
# Contact repository owner for access.
```

Key theorems to verify:
- `closed_choice_forces_transputation` (Forced Adjudication, NEMS 08)
- `NemS.born_rule_unique` (Born Rule Uniqueness, NEMS 13+14)
- `ArrowOfTime.closure_arrow_theorem` (Arrow of Time, NEMS 36+78)
- `SM_gauge_uniquely_selected` (SM gauge uniqueness, NEMS 05)
- `IPT_theorem` (Information Profit Threshold)
- See Appendix A of the paper for the full inventory.

---

## 2. Verify computational results

The computational claims reference experiments in the MFRR monograph and
companion papers. Key reproducible artifacts:

```bash
# SM universe scan (34,560 universes) — SM ranks #1 among all candidates
cd papers/01_SM/canonical_run
python3 comp_p23_SP1_rcc_extended_scan.py      # extended scan (34,560 universes)
python3 te22_rcc_certificate.py                # canonical 20,160-universe certificate

# SRRG flow-basin analysis (TS1: 8,704 random starts) — see P27 for full derivation
cd papers/27_SRRG/scripts
python3 beta_eta_flow.py

# Information Profit Threshold (E32) — IPT = 1.1300 ± 0.0001
cd papers/15_information_profit/information_profit
python verify_ipt_derivation.py
```

All scripts emit JSON artifacts with SHA-256 hashes.
Full provenance records are in `papers/01_SM/PROVENANCE.md` and
`papers/20_mfrr_physics_survey/PROVENANCE.md`.

---

## 3. Build the PDF

```bash
cd papers/20_mfrr_physics_survey
pdflatex MFRR_Physics_Survey.tex
bibtex MFRR_Physics_Survey
pdflatex MFRR_Physics_Survey.tex
pdflatex MFRR_Physics_Survey.tex
```

Expected: ~14 pages, 0 undefined citations.

---

## Dependencies

- TeX Live 2025 (pdflatex + bibtex)
- Python 3.9+ (for verifying referenced computational experiments)
- Lean 4.29.0-rc6, Mathlib 4.29.0-rc6 (for Lean verification)
