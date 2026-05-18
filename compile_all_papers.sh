#!/usr/bin/env bash
# compile_all_papers.sh
#
# Recompile every UGP paper in-place.
# Each paper is built with two pdflatex passes (first builds the .aux / refs,
# second resolves them). If a .bib file is present, bibtex is run between the
# two passes so citations resolve on the second pass.
#
# Usage:
#   bash compile_all_papers.sh              # compile all papers
#   bash compile_all_papers.sh --skip-mfrr  # skip the large MFRR monograph
#   bash compile_all_papers.sh P01 P17      # compile only named papers (prefix match)
#
# After compilation, run collect_paper_pdfs.sh to copy the results to
# specs/paper_pdfs/.

set -uo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
PDFLATEX="pdflatex"
PDFLATEX_FLAGS="-interaction=nonstopmode -halt-on-error"
BIBTEX="bibtex"

SKIP_MFRR=false
FILTER=()
for arg in "$@"; do
  case "$arg" in
    --skip-mfrr) SKIP_MFRR=true ;;
    *)           FILTER+=("$arg") ;;
  esac
done

ok=0; fail=0; skip=0

# ---------------------------------------------------------------------------
# compile_paper DIR TEX_BASENAME LABEL
#   DIR           — directory containing the .tex file
#   TEX_BASENAME  — filename without path, e.g. standard_model_from_ugp.tex
#   LABEL         — short label shown in output, e.g. P01
# ---------------------------------------------------------------------------
compile_paper() {
  local dir="$1"
  local tex="$2"
  local label="$3"

  # honour --skip-mfrr
  if $SKIP_MFRR && [[ "$label" == "P13-monograph" ]]; then
    echo "  SKIP  $label (--skip-mfrr)"
    (( skip++ )) || true
    return
  fi

  # honour selective filter (e.g. P01 P17)
  if [[ ${#FILTER[@]} -gt 0 ]]; then
    local match=false
    for f in "${FILTER[@]}"; do
      [[ "$label" == "$f"* ]] && match=true
    done
    if ! $match; then
      (( skip++ )) || true
      return
    fi
  fi

  local tex_path="$dir/$tex"
  if [[ ! -f "$tex_path" ]]; then
    echo "  MISS  $label — $tex_path not found"
    (( skip++ )) || true
    return
  fi

  local stem="${tex%.tex}"
  local logfile="$dir/${stem}.compile.log"

  printf "  %-42s " "$label ($tex)"

  (
    cd "$dir"
    # Pass 1 — build .aux and initial PDF
    $PDFLATEX $PDFLATEX_FLAGS "$tex" >> "$logfile" 2>&1 || true

    # bibtex if a .bib file lives in the same directory
    if ls *.bib &>/dev/null; then
      $BIBTEX "$stem" >> "$logfile" 2>&1 || true
    fi

    # Pass 2 — resolve cross-references and citations
    $PDFLATEX $PDFLATEX_FLAGS "$tex" >> "$logfile" 2>&1
  )

  local exit_code=$?
  if [[ -f "$dir/${stem}.pdf" ]]; then
    echo "OK"
    (( ok++ )) || true
  else
    echo "FAILED  (log: $logfile)"
    (( fail++ )) || true
  fi
}

# ---------------------------------------------------------------------------
# Paper list  —  DIR (relative to repo root)  |  TEX BASENAME  |  LABEL
# ---------------------------------------------------------------------------

echo "=== UGP Paper Compilation ==="
echo "Repository: $REPO"
echo ""

compile_paper "$REPO/papers/01_SM" \
  "standard_model_from_ugp.tex"                    "P01"

compile_paper "$REPO/papers/01_SM" \
  "supplementary_information.tex"                  "P01-SI"

compile_paper "$REPO/papers/02_GTE_spectrum" \
  "Particle_Spectrum_From_UGP_Paper.tex"            "P02"

compile_paper "$REPO/papers/03_nuclear" \
  "Nuclear_Physics_From_UGP_Paper.tex"              "P03"

compile_paper "$REPO/papers/04_dynamics_universality" \
  "ugp_dynamics_universality.tex"                   "P04"

compile_paper "$REPO/papers/05_uniqueness" \
  "The Uniqueness of the Universal Generative Principle.tex"  "P05"

compile_paper "$REPO/papers/06_math_foundations" \
  "algebraic_geometric_foundations_ugp.tex"         "P06"

compile_paper "$REPO/papers/07_meta_laws" \
  "ugp_meta_laws.tex"                               "P07"

compile_paper "$REPO/papers/08_ugp_foundational_monograph" \
  "Universal_Generative_Principle_UGP_Paper.tex"    "P08"

compile_paper "$REPO/papers/09_architecture" \
  "The Architecture of a Computable Universe.tex"   "P09"

compile_paper "$REPO/papers/10_reflexive_law" \
  "reflexive_reality_self_defining_law.tex"         "P10"

compile_paper "$REPO/papers/11_ontological_dissonance" \
  "Ontological_Dissonance_Minimization_SDS_Validation.tex"  "P11"

compile_paper "$REPO/papers/12_unified_rigidity" \
  "Unified_Rigidity_Capstone.tex"                   "P12"

# P13 — MFRR monograph lives in MFRR/ (not papers/)
compile_paper "$REPO/MFRR" \
  "Mathematical_Foundations_of_Reflexive_Reality.tex"  "P13-monograph"

compile_paper \
  "$REPO/papers/13_MFRR_foundational_monograph/MFRR_explanatory_summaries/MFRR_FOR_PHYSICISTS" \
  "MFRR_FOR_PHYSICISTS_SHORT_OVERVIEW.tex"          "P13-short"

compile_paper \
  "$REPO/papers/13_MFRR_foundational_monograph/MFRR_explanatory_summaries/MFRR_POPULAR_ARTICLE" \
  "MFRR_POPSCI_OVERVIEW.tex"                        "P13-popular"

compile_paper \
  "$REPO/papers/13_MFRR_foundational_monograph/MFRR_explanatory_summaries/SUMMARY_FOR_PHYSICISTS_AND_REFEREES" \
  "MFRR_summary_for_physicists.tex"                 "P13-summary"

compile_paper "$REPO/papers/14_psc_concordance" \
  "PSC_Concordance.tex"                             "P14"

compile_paper "$REPO/papers/15_information_profit" \
  "Information_Profit_Principle.tex"                "P15"

compile_paper "$REPO/papers/16_bh_unitarity" \
  "BH_Reflexive_Unitarity.tex"                      "P16"

compile_paper "$REPO/papers/17_braid_atlas" \
  "Braid_Atlas_v2_First_Principles.tex"             "P17"

compile_paper "$REPO/papers/18_koide_cyclotomic" \
  "koide_cyclotomic_closed_form.tex"                "P18"

compile_paper "$REPO/papers/19_cyclotomic_mass_structure" \
  "cyclotomic_12_mass_structure.tex"                "P19"

compile_paper "$REPO/papers/19_cyclotomic_mass_structure" \
  "supplementary_information.tex"                   "P19-SI"

# P20 (research monograph) moved to research-sandbox — not compiled here

compile_paper "$REPO/papers/20_mfrr_physics_survey" \
  "MFRR_Physics_Survey.tex"                         "P20"

compile_paper "$REPO/papers/21_neutrino_masses" \
  "neutrino_masses_from_braid_atlas.tex"            "P21"

compile_paper "$REPO/papers/22_ugp_dynamics" \
  "ugp_dynamics_paper.tex"                          "P22"

compile_paper "$REPO/papers/23_closure_structure" \
  "closure_structure_ugp.tex"                       "P23"

compile_paper "$REPO/papers/24_deeper_theory" \
  "ugp_deeper_theory.tex"                           "P24"

compile_paper "$REPO/papers/25_genetic_code" \
  "genetic_code_ugp_paper.tex"                      "P25"

compile_paper "$REPO/papers/26_general_selection" \
  "general_selection_theory.tex"                    "P26"

# ---------------------------------------------------------------------------
echo ""
echo "=== Results: $ok OK | $fail failed | $skip skipped ==="
echo ""
echo "To collect all PDFs into specs/paper_pdfs/ run:"
echo "  bash $REPO/collect_paper_pdfs.sh"
