#!/usr/bin/env bash
# collect_paper_pdfs.sh
# Compile all UGP papers with latexmk and collect PDFs into specs/paper_pdfs/
#
# Usage: bash collect_paper_pdfs.sh [--skip-mfrr] [--public]
#   --skip-mfrr  skip the large MFRR monograph (takes several minutes alone)
#   --public     omit the internal-only Paper 20 (UGP Research Monograph)
#                from the bundle. Use this for any externally published deposit.

set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
DEST="$REPO/specs/paper_pdfs"
LATEXMK="latexmk"
LATEXMK_FLAGS="-pdf -interaction=nonstopmode -halt-on-error -quiet"

SKIP_MFRR=false
PUBLIC=false  # When true, omit P20 (internal-only research monograph) from the bundle.
for arg in "$@"; do
  case "$arg" in
    --skip-mfrr) SKIP_MFRR=true ;;
    --public)    PUBLIC=true ;;
  esac
done

mkdir -p "$DEST"

ok=0; fail=0; skip=0

compile_and_collect() {
  local src_dir="$1"
  local tex_file="$2"   # basename only, e.g. standard_model_from_ugp.tex
  local dest_name="$3"  # e.g. P01_standard_model_from_ugp.pdf

  local tex_path="$src_dir/$tex_file"
  local pdf_src="$src_dir/${tex_file%.tex}.pdf"

  if [[ ! -f "$tex_path" ]]; then
    echo "  SKIP  (tex not found): $tex_path"
    (( skip++ )) || true
    return
  fi

  echo -n "  Compiling $dest_name ... "
  if (cd "$src_dir" && $LATEXMK $LATEXMK_FLAGS "$tex_file" > /tmp/latexmk_$$.log 2>&1); then
    cp "$pdf_src" "$DEST/$dest_name"
    echo "OK"
    (( ok++ )) || true
  else
    echo "FAILED  (see /tmp/latexmk_$$.log)"
    (( fail++ )) || true
  fi
}

echo "=== UGP Paper PDF Build & Collect ==="
echo "Destination: $DEST"
echo ""

echo "[Paper 01 — Standard Model from UGP]"
compile_and_collect "$REPO/papers/01_SM" \
  "standard_model_from_ugp.tex" \
  "P01_standard_model_from_ugp.pdf"

echo "[Paper 01 SI — Supplementary Information]"
compile_and_collect "$REPO/papers/01_SM" \
  "supplementary_information.tex" \
  "P01_SI_supplementary_information.pdf"

echo "[Paper 02 — GTE Particle Spectrum]"
compile_and_collect "$REPO/papers/02_GTE_spectrum" \
  "Particle_Spectrum_From_UGP_Paper.tex" \
  "P02_GTE_particle_spectrum.pdf"

echo "[Paper 03 — Nuclear Binding Energy]"
compile_and_collect "$REPO/papers/03_nuclear" \
  "Nuclear_Physics_From_UGP_Paper.tex" \
  "P03_nuclear_binding_energy.pdf"

echo "[Paper 04 — GTE Dynamics Universality]"
compile_and_collect "$REPO/papers/04_dynamics_universality" \
  "ugp_dynamics_universality.tex" \
  "P04_gte_dynamics_universality.pdf"

echo "[Paper 05 — Uniqueness of UGP]"
compile_and_collect "$REPO/papers/05_uniqueness" \
  "The Uniqueness of the Universal Generative Principle.tex" \
  "P05_uniqueness_ugp.pdf"

echo "[Paper 06 — Mathematical Foundations]"
compile_and_collect "$REPO/papers/06_math_foundations" \
  "algebraic_geometric_foundations_ugp.tex" \
  "P06_math_foundations.pdf"

echo "[Paper 07 — Meta-Laws]"
compile_and_collect "$REPO/papers/07_meta_laws" \
  "ugp_meta_laws.tex" \
  "P07_meta_laws.pdf"

echo "[Paper 08 — UGP Foundational Monograph]"
compile_and_collect "$REPO/papers/08_ugp_foundational_monograph" \
  "Universal_Generative_Principle_UGP_Paper.tex" \
  "P08_ugp_foundational_monograph.pdf"

echo "[Paper 09 — Architecture of a Computable Universe]"
compile_and_collect "$REPO/papers/09_architecture" \
  "The Architecture of a Computable Universe.tex" \
  "P09_architecture_computable_universe.pdf"

echo "[Paper 10 — Reflexive Reality Self-Defining Law]"
compile_and_collect "$REPO/papers/10_reflexive_law" \
  "reflexive_reality_self_defining_law.tex" \
  "P10_reflexive_law.pdf"

echo "[Paper 11 — Ontological Dissonance Minimization]"
compile_and_collect "$REPO/papers/11_ontological_dissonance" \
  "Ontological_Dissonance_Minimization_SDS_Validation.tex" \
  "P11_ontological_dissonance.pdf"

echo "[Paper 12 — Unified Rigidity Capstone]"
compile_and_collect "$REPO/papers/12_unified_rigidity" \
  "Unified_Rigidity_Capstone.tex" \
  "P12_unified_rigidity.pdf"

if $SKIP_MFRR; then
  echo "[Paper 13 — MFRR Monograph] SKIPPED (--skip-mfrr)"
  (( skip++ )) || true
else
  echo "[Paper 13 — MFRR Monograph (large, may take several minutes)]"
  compile_and_collect "$REPO/MFRR" \
    "Mathematical_Foundations_of_Reflexive_Reality.tex" \
    "P13_MFRR_monograph.pdf"
fi

echo "[Paper 13 — MFRR For Physicists Short]"
compile_and_collect \
  "$REPO/papers/13_MFRR_foundational_monograph/MFRR_explanatory_summaries/MFRR_FOR_PHYSICISTS" \
  "MFRR_FOR_PHYSICISTS_SHORT_OVERVIEW.tex" \
  "P13_MFRR_for_physicists_short.pdf"

echo "[Paper 13 — MFRR Popular Overview]"
compile_and_collect \
  "$REPO/papers/13_MFRR_foundational_monograph/MFRR_explanatory_summaries/MFRR_POPULAR_ARTICLE" \
  "MFRR_POPSCI_OVERVIEW.tex" \
  "P13_MFRR_popular_overview.pdf"

echo "[Paper 13 — MFRR Summary for Physicists and Referees]"
compile_and_collect \
  "$REPO/papers/13_MFRR_foundational_monograph/MFRR_explanatory_summaries/SUMMARY_FOR_PHYSICISTS_AND_REFEREES" \
  "MFRR_summary_for_physicists.tex" \
  "P13_MFRR_summary_for_physicists.pdf"

echo "[Paper 14 — PSC Concordance]"
compile_and_collect "$REPO/papers/14_psc_concordance" \
  "PSC_Concordance.tex" \
  "P14_psc_concordance.pdf"

echo "[Paper 15 — Information Profit Principle]"
compile_and_collect "$REPO/papers/15_information_profit" \
  "Information_Profit_Principle.tex" \
  "P15_information_profit.pdf"

echo "[Paper 16 — BH Reflexive Unitarity]"
compile_and_collect "$REPO/papers/16_bh_unitarity" \
  "BH_Reflexive_Unitarity.tex" \
  "P16_bh_reflexive_unitarity.pdf"

echo "[Paper 17 — Braid Atlas v2]"
compile_and_collect "$REPO/papers/17_braid_atlas" \
  "Braid_Atlas_v2_First_Principles.tex" \
  "P17_braid_atlas.pdf"

echo "[Paper 18 — Koide Cyclotomic Closed Form]"
compile_and_collect "$REPO/papers/18_koide_cyclotomic" \
  "koide_cyclotomic_closed_form.tex" \
  "P18_koide_cyclotomic.pdf"

echo "[Paper 19 — Cyclotomic Mass Structure]"
compile_and_collect "$REPO/papers/19_cyclotomic_mass_structure" \
  "cyclotomic_12_mass_structure.tex" \
  "P19_cyclotomic_mass_structure.pdf"

echo "[Paper 19 SI — Supplementary Information]"
compile_and_collect "$REPO/papers/19_cyclotomic_mass_structure" \
  "supplementary_information.tex" \
  "P19_SI_supplementary_information.pdf"

# P20 (research monograph) moved to research-sandbox/research_monograph_private — skipped always
echo "[Paper 20 (was P20) — Research Monograph] SKIPPED (moved to research-sandbox)"
(( skip++ )) || true

echo "[Paper 20 — MFRR Physics Survey]"
compile_and_collect "$REPO/papers/20_mfrr_physics_survey" \
  "MFRR_Physics_Survey.tex" \
  "P20_mfrr_physics_survey.pdf"

echo "[Paper 21 — Neutrino Masses from Braid Atlas]"
compile_and_collect "$REPO/papers/21_neutrino_masses" \
  "neutrino_masses_from_braid_atlas.tex" \
  "P21_neutrino_masses_from_braid_atlas.pdf"

echo "[Paper 22 — UGP Interaction Skeleton Theorem]"
compile_and_collect "$REPO/papers/22_ugp_dynamics" \
  "ugp_dynamics_paper.tex" \
  "P22_ugp_interaction_skeleton_theorem.pdf"

echo "[Paper 23 — Substrate Depth and Self-Generated Mass]"
compile_and_collect "$REPO/papers/23_closure_structure" \
  "closure_structure_ugp.tex" \
  "P23_closure_structure.pdf"

echo "[Paper 24 — Arithmetic Uniqueness of the Standard Model]"
compile_and_collect "$REPO/papers/24_deeper_theory" \
  "ugp_deeper_theory.tex" \
  "P24_arithmetic_uniqueness_SM.pdf"

echo "[Paper 25 — Genetic Code Two-Stage Sieve]"
compile_and_collect "$REPO/papers/25_genetic_code" \
  "genetic_code_ugp_paper.tex" \
  "P25_genetic_code_two_stage_sieve.pdf"

echo "[Paper 26 — General Selection Theory]"
compile_and_collect "$REPO/papers/26_general_selection" \
  "general_selection_theory.tex" \
  "P26_general_selection_theory.pdf"

echo "[Paper 27 — Self-Referential Reality Generation]"
compile_and_collect "$REPO/papers/27_SRRG" \
  "srrg_paper.tex" \
  "P27_srrg.pdf"

echo "[Paper 28 — Computational Universality and the Standard Model]"
compile_and_collect "$REPO/papers/28_computational_universality" \
  "computational_universality_ugp.tex" \
  "P28_computational_universality.pdf"

echo "[Paper 29 — Mirror Branch Braid Atlas (Dark Sector)]"
compile_and_collect "$REPO/papers/29_dark_sector_braid_atlas" \
  "Dark_Sector_Braid_Atlas_Paper.tex" \
  "P29_dark_sector_braid_atlas.pdf"

echo "[Paper 30 — Machine-Certified Cook's Theorem]"
compile_and_collect "$REPO/papers/30_cook_theorem" \
  "cook_theorem_paper.tex" \
  "P30_cook_theorem.pdf"

echo "[Paper 31 — Electroweak Mixing Angle]"
compile_and_collect "$REPO/papers/31_weinberg_angle" \
  "weinberg_angle_paper.tex" \
  "P31_weinberg_angle.pdf"

echo "[Paper 32 — CKM Wolfenstein Parameters]"
compile_and_collect "$REPO/papers/32_ckm_matrix" \
  "ckm_matrix_paper.tex" \
  "P32_ckm_matrix.pdf"

echo "[Paper 33 — Deeper Consequences of Arithmetic Universality]"
compile_and_collect "$REPO/papers/33_deeper_consequences" \
  "deeper_consequences_paper.tex" \
  "P33_deeper_consequences.pdf"

echo "[Paper 34 — GTE-Mobius Substrate]"
compile_and_collect "$REPO/papers/34_gte_mobius_substrate" \
  "gte_mobius_substrate_paper.tex" \
  "P34_gte_mobius_substrate.pdf"

echo "[Paper 35 — GTE Unification]"
compile_and_collect "$REPO/papers/35_gte_unification" \
  "gte_unification_paper.tex" \
  "P35_gte_unification.pdf"

echo "[Paper 36 — Emergent Gravity from Rule 110 CA]"
compile_and_collect "$REPO/papers/36_emergent_gravity_cmca" \
  "emergent_gravity_paper.tex" \
  "P36_emergent_gravity_cmca.pdf"

echo "[Paper 37 — Quantum Mechanics from Rule 110]"
compile_and_collect "$REPO/papers/37_quantum_mechanics" \
  "quantum_mechanics_paper.tex" \
  "P37_quantum_mechanics.pdf"

echo "[Paper 38 — Emergent Gravity from the Phi_MDL Field]"
compile_and_collect "$REPO/papers/38_emergent_gravity_phimdl" \
  "emergent_gravity_gte_phimdl.tex" \
  "P38_emergent_gravity_phimdl.pdf"

echo "[Paper 39 — QCD Structure from GTE]"
compile_and_collect "$REPO/papers/39_qcd_from_gte" \
  "gte_qcd_structure_paper.tex" \
  "P39_qcd_from_gte.pdf"

echo "[Paper 40 — Rule 110 over GF(7)]"
compile_and_collect "$REPO/papers/40_gf7_polynomial_universality" \
  "gf7_polynomial_universality.tex" \
  "P40_gf7_polynomial_universality.pdf"

echo "[Paper 41 — Three-Layer Chiral Minkowski CA]"
compile_and_collect "$REPO/papers/41_three_layer_chiral_minkowski_ca" \
  "three_layer_chiral_minkowski_ca_paper.tex" \
  "P41_three_layer_chiral_minkowski_ca.pdf"

echo "[Paper 42 — Phi_MDL Field: Quantum Structure and Born Rule]"
compile_and_collect "$REPO/papers/42_phimdl_field" \
  "phimdl_field_paper.tex" \
  "P42_phimdl_field.pdf"

echo "[Paper 43 — Complete Phi_MDL Framework]"
compile_and_collect "$REPO/papers/43_phimdl_completeness" \
  "phimdl_completeness_paper.tex" \
  "P43_phimdl_completeness.pdf"

echo "[Paper 44 — Quantum Gravity: Functional Completeness]"
compile_and_collect "$REPO/papers/44_quantum_gravity" \
  "quantum_gravity_completeness.tex" \
  "P44_quantum_gravity_completeness.pdf"

echo "[Paper 45 — Three-Tape Chiral Minkowski CA]"
compile_and_collect "$REPO/papers/45_three_tape_cmca" \
  "three_tape_cmca_paper.tex" \
  "P45_three_tape_cmca.pdf"

echo "[Paper 46 — GTE Polynomial as Unified Field Theory]"
compile_and_collect "$REPO/papers/46_gte_polynomial_uft" \
  "gte_polynomial_uft_paper.tex" \
  "P46_gte_polynomial_uft.pdf"

echo "[Paper 47 — Cosmological Predictions of GTE/Phi_MDL]"
compile_and_collect "$REPO/papers/47_gte_cosmology" \
  "gte_cosmology_paper.tex" \
  "P47_gte_cosmology.pdf"

echo ""
echo "=== Results: $ok compiled OK | $fail failed | $skip skipped ==="
echo "PDFs in: $DEST"
