#!/usr/bin/env bash
# consolidate_papers.sh
#
# Concatenate all UGP paper LaTeX source files into a single consolidated text
# file with prominent agent-searchable banners between each paper.
#
# Usage:
#   bash consolidate_papers.sh [OUTPUT_FILE]
#
# Default output: consolidated_papers.txt at repo root.

set -uo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
OUTPUT="${1:-$REPO/specs/consolidated_papers_file/consolidated_papers_file.txt}"

# ---------------------------------------------------------------------------
# Paper registry: LABEL | TITLE | DIR (relative to repo) | TEX_BASENAME
# ---------------------------------------------------------------------------
declare -a LABELS TITLES DIRS TEXFILES

add_paper() {
  LABELS+=("$1")
  TITLES+=("$2")
  DIRS+=("$3")
  TEXFILES+=("$4")
}

add_paper "P01"           "Standard Model from UGP"                                           "papers/01_SM"                                                                       "standard_model_from_ugp.tex"
add_paper "P01-SI"        "Standard Model from UGP — Supplementary Information"               "papers/01_SM"                                                                       "supplementary_information.tex"
add_paper "P02"           "GTE Particle Spectrum at n=10"                                     "papers/02_GTE_spectrum"                                                             "Particle_Spectrum_From_UGP_Paper.tex"
add_paper "P03"           "Nuclear Binding Energy from UGP"                                   "papers/03_nuclear"                                                                  "Nuclear_Physics_From_UGP_Paper.tex"
add_paper "P04"           "GTE Dynamics Universality"                                         "papers/04_dynamics_universality"                                                    "ugp_dynamics_universality.tex"
add_paper "P05"           "The Uniqueness of the Universal Generative Principle"               "papers/05_uniqueness"                                                               "The Uniqueness of the Universal Generative Principle.tex"
add_paper "P06"           "Algebraic and Geometric Foundations of UGP"                        "papers/06_math_foundations"                                                         "algebraic_geometric_foundations_ugp.tex"
add_paper "P07"           "Meta-Laws of UGP"                                                  "papers/07_meta_laws"                                                                "ugp_meta_laws.tex"
add_paper "P08"           "UGP Foundational Monograph"                                        "papers/08_ugp_foundational_monograph"                                               "Universal_Generative_Principle_UGP_Paper.tex"
add_paper "P09"           "The Architecture of a Computable Universe"                         "papers/09_architecture"                                                             "The Architecture of a Computable Universe.tex"
add_paper "P10"           "Reflexive Reality and Self-Defining Physical Law"                  "papers/10_reflexive_law"                                                            "reflexive_reality_self_defining_law.tex"
add_paper "P11"           "Ontological Dissonance Minimization"                               "papers/11_ontological_dissonance"                                                   "Ontological_Dissonance_Minimization_SDS_Validation.tex"
add_paper "P12"           "Unified Rigidity Capstone"                                         "papers/12_unified_rigidity"                                                         "Unified_Rigidity_Capstone.tex"
add_paper "P13-monograph" "Mathematical Foundations of Reflexive Reality (MFRR Monograph)"   "MFRR"                                                                               "Mathematical_Foundations_of_Reflexive_Reality.tex"
add_paper "P13-short"     "MFRR for Physicists — Short Overview"                              "papers/13_MFRR_foundational_monograph/MFRR_explanatory_summaries/MFRR_FOR_PHYSICISTS"            "MFRR_FOR_PHYSICISTS_SHORT_OVERVIEW.tex"
add_paper "P13-popular"   "MFRR Popular Science Overview"                                     "papers/13_MFRR_foundational_monograph/MFRR_explanatory_summaries/MFRR_POPULAR_ARTICLE"           "MFRR_POPSCI_OVERVIEW.tex"
add_paper "P13-summary"   "MFRR Summary for Physicists and Referees"                          "papers/13_MFRR_foundational_monograph/MFRR_explanatory_summaries/SUMMARY_FOR_PHYSICISTS_AND_REFEREES" "MFRR_summary_for_physicists.tex"
add_paper "P14"           "PSC Concordance"                                                   "papers/14_psc_concordance"                                                          "PSC_Concordance.tex"
add_paper "P15"           "Information Profit Principle"                                      "papers/15_information_profit"                                                       "Information_Profit_Principle.tex"
add_paper "P16"           "BH Reflexive Unitarity"                                            "papers/16_bh_unitarity"                                                             "BH_Reflexive_Unitarity.tex"
add_paper "P17"           "Canonical Braid Atlas v2.0 — First Principles"                    "papers/17_braid_atlas"                                                              "Braid_Atlas_v2_First_Principles.tex"
add_paper "P18"           "Koide Cyclotomic Closed Form"                                      "papers/18_koide_cyclotomic"                                                         "koide_cyclotomic_closed_form.tex"
add_paper "P19"           "Cyclotomic Mass Structure"                                         "papers/19_cyclotomic_mass_structure"                                                "cyclotomic_12_mass_structure.tex"
add_paper "P19-SI"        "Cyclotomic Mass Structure — Supplementary Information"             "papers/19_cyclotomic_mass_structure"                                                "supplementary_information.tex"
# P20 (research monograph) moved to research-sandbox/research_monograph_private — excluded from public consolidation
add_paper "P20"           "MFRR Physics Survey"                                               "papers/20_mfrr_physics_survey"                                                      "MFRR_Physics_Survey.tex"
add_paper "P21"           "Neutrino Masses from the Canonical Braid Atlas"                    "papers/21_neutrino_masses"                                                          "neutrino_masses_from_braid_atlas.tex"
add_paper "P22"           "UGP Interaction Skeleton Theorem"                                  "papers/22_ugp_dynamics"                                                             "ugp_dynamics_paper.tex"
add_paper "P23"           "Substrate Depth and Self-Generated Mass"                           "papers/23_closure_structure"                                                        "closure_structure_ugp.tex"
add_paper "P24"           "Standard Model Parameter Spectrum as Unique Arithmetic Intersection" "papers/24_deeper_theory"                                                          "ugp_deeper_theory.tex"
add_paper "P25"           "The Standard Genetic Code as the Unique Survivor of a Two-Stage Admissibility-Viability Sieve" "papers/25_genetic_code"                             "genetic_code_ugp_paper.tex"
add_paper "P26"           "A General Theory of Selection: The UGP Framework Across Domains" "papers/26_general_selection"                "general_selection_theory.tex"
add_paper "P26-md"        "A General Theory of Selection (Markdown draft)"                  "papers/26_general_selection"                "general_selection_theory.md"

# ---------------------------------------------------------------------------
# Build the output file
# ---------------------------------------------------------------------------
TOTAL=${#LABELS[@]}
TIMESTAMP="$(date -u '+%Y-%m-%d %H:%M UTC')"
DIVIDER="################################################################################"
THIN_DIV="--------------------------------------------------------------------------------"

{
  echo "$DIVIDER"
  echo "# UGP PHYSICS — CONSOLIDATED PAPER SOURCES"
  echo "# Generated: $TIMESTAMP"
  echo "# Repository: $REPO"
  echo "# Papers included: $TOTAL"
  echo "# Format: LaTeX source (.tex) with agent-searchable section banners"
  echo "#"
  echo "# QUICK NAVIGATION — search for these exact strings:"
  echo "#   BEGIN PAPER P01      Standard Model from UGP"
  echo "#   BEGIN PAPER P01-SI   Supplementary Information"
  echo "#   BEGIN PAPER P02      GTE Particle Spectrum"
  echo "#   BEGIN PAPER P03      Nuclear Binding Energy"
  echo "#   BEGIN PAPER P04      GTE Dynamics Universality"
  echo "#   BEGIN PAPER P05      Uniqueness of UGP"
  echo "#   BEGIN PAPER P06      Mathematical Foundations"
  echo "#   BEGIN PAPER P07      Meta-Laws"
  echo "#   BEGIN PAPER P08      UGP Foundational Monograph"
  echo "#   BEGIN PAPER P09      Architecture of a Computable Universe"
  echo "#   BEGIN PAPER P10      Reflexive Reality"
  echo "#   BEGIN PAPER P11      Ontological Dissonance Minimization"
  echo "#   BEGIN PAPER P12      Unified Rigidity Capstone"
  echo "#   BEGIN PAPER P13-monograph  MFRR Monograph"
  echo "#   BEGIN PAPER P13-short      MFRR For Physicists Short"
  echo "#   BEGIN PAPER P13-popular    MFRR Popular Overview"
  echo "#   BEGIN PAPER P13-summary    MFRR Summary for Referees"
  echo "#   BEGIN PAPER P14      PSC Concordance"
  echo "#   BEGIN PAPER P15      Information Profit Principle"
  echo "#   BEGIN PAPER P16      BH Reflexive Unitarity"
  echo "#   BEGIN PAPER P17      Canonical Braid Atlas v2.0"
  echo "#   BEGIN PAPER P18      Koide Cyclotomic Closed Form"
  echo "#   BEGIN PAPER P19      Cyclotomic Mass Structure"
  echo "#   BEGIN PAPER P19-SI   Cyclotomic Mass Structure SI"
  echo "#   BEGIN PAPER P20      UGP Research Monograph"
  echo "#   BEGIN PAPER P21      MFRR Physics Survey"
  echo "#   BEGIN PAPER P22      Neutrino Masses from Braid Atlas"
  echo "#   BEGIN PAPER P23      UGP Interaction Skeleton Theorem"
  echo "$DIVIDER"
  echo ""

  for i in "${!LABELS[@]}"; do
    label="${LABELS[$i]}"
    title="${TITLES[$i]}"
    dir="${DIRS[$i]}"
    tex="${TEXFILES[$i]}"
    filepath="$REPO/$dir/$tex"
    relpath="$dir/$tex"

    echo ""
    echo "$DIVIDER"
    echo "# BEGIN PAPER $label"
    echo "# TITLE:  $title"
    echo "# FILE:   $relpath"
    echo "# LABEL:  $label"
    echo "$DIVIDER"
    echo ""

    if [[ -f "$filepath" ]]; then
      cat "$filepath"
    else
      echo "[FILE NOT FOUND: $filepath]"
    fi

    echo ""
    echo "$THIN_DIV"
    echo "# END PAPER $label — $title"
    echo "$THIN_DIV"
    echo ""
  done

  echo ""
  echo "$DIVIDER"
  echo "# END OF CONSOLIDATED PAPER SOURCES"
  echo "# Generated: $TIMESTAMP"
  echo "# Total papers: $TOTAL"
  echo "$DIVIDER"

} > "$OUTPUT"

SIZE=$(du -sh "$OUTPUT" | cut -f1)
LINES=$(wc -l < "$OUTPUT")
echo "Written: $OUTPUT"
echo "Size:    $SIZE  ($LINES lines)"
echo "Papers:  $TOTAL"
