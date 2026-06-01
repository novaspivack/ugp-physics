# REPRODUCE — UGP Survey / Reader's Guide (P00)

**Paper:** `ugp_survey_readers_guide.tex`
**Status:** Survey document — no original code or data.  All claims cite the
primary papers P01–P27, each of which has its own `REPRODUCE.md`.

---

## What this paper contains

P00 is a pure survey and reader's guide.  It introduces no new theorems,
derivations, or datasets.  Every quantitative claim, prediction, and
evidence grade cited here is sourced from a primary UGP paper; see the
corresponding `REPRODUCE.md` in that paper's directory.

---

## Reproducing the compiled PDF

### Prerequisites

- TeX Live 2023+ (or equivalent) with `pdflatex`, `microtype`, `tcolorbox`,
  `tikz`, `longtable`, `booktabs`, `cleveref`, `lmodern`, `hyperref`.
- The shared bibliography: `../bib/Spivack_Papers_Bibliography.bib`

### Build

```bash
cd papers/00_survey_guide
pdflatex -interaction=nonstopmode ugp_survey_readers_guide.tex
bibtex ugp_survey_readers_guide
pdflatex -interaction=nonstopmode ugp_survey_readers_guide.tex
pdflatex -interaction=nonstopmode ugp_survey_readers_guide.tex
```

The final PDF is `ugp_survey_readers_guide.pdf`.

---

## Reproducing individual claims

To reproduce any specific claim cited in P00, consult the `REPRODUCE.md` in
the corresponding primary paper directory:

| Claim area                    | Primary paper | Directory                        |
|-------------------------------|---------------|----------------------------------|
| SM constants, α_s, m_W        | P01           | `papers/01_SM/`                  |
| GTE particle spectrum         | P02           | `papers/02_GTE_spectrum/`        |
| Nuclear binding energies      | P03           | `papers/03_nuclear/`             |
| UGP uniqueness (n=10, b₁=73) | P05           | `papers/05_uniqueness/`          |
| Information Profit Threshold  | P15           | `papers/15_information_profit/`  |
| Koide closed form             | P18           | `papers/18_koide/`               |
| Neutrino mass-squared ratio   | P21           | `papers/21_neutrino/`            |
| General Selection Theory      | P26           | `papers/26_general_selection/`   |
| SRRG / IPT fixed-point proof  | P27           | `papers/27_SRRG/`                |

For Lean machine-checked results, see:
- `ugp-lean` repository: <https://github.com/novaspivack/ugp-lean>
- `srrg-lean` repository: cited in P27
