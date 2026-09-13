#!/usr/bin/env python3
"""
generate_consolidated_papers_file.py

Concatenate all UGP paper LaTeX sources into a single searchable text file
at specs/consolidated_papers_file/consolidated_papers_file.txt.

Each paper is wrapped with agent-searchable banners:
    # BEGIN PAPER P01      Standard Model from UGP
    ...source...
    # END PAPER P01
"""
import os
from datetime import datetime, timezone

REPO = os.path.dirname(os.path.abspath(__file__))
DEST = os.path.join(REPO, "specs", "consolidated_papers_file", "consolidated_papers_file.txt")

# Paper list: (label, tex_path_relative_to_repo, title)
PAPERS = [
    ("P01",           "papers/01_SM/standard_model_from_ugp.tex",
                      "Standard Model from UGP"),
    ("P01-SI",        "papers/01_SM/supplementary_information.tex",
                      "Supplementary Information"),
    ("P02",           "papers/02_GTE_spectrum/Particle_Spectrum_From_UGP_Paper.tex",
                      "GTE Particle Spectrum"),
    ("P03",           "papers/03_nuclear/Nuclear_Physics_From_UGP_Paper.tex",
                      "Nuclear Binding Energy"),
    ("P04",           "papers/04_dynamics_universality/ugp_dynamics_universality.tex",
                      "GTE Dynamics Universality"),
    ("P05",           "papers/05_uniqueness/The Uniqueness of the Universal Generative Principle.tex",
                      "Uniqueness of UGP"),
    ("P06",           "papers/06_math_foundations/algebraic_geometric_foundations_ugp.tex",
                      "Mathematical Foundations"),
    ("P07",           "papers/07_meta_laws/ugp_meta_laws.tex",
                      "Meta-Laws"),
    ("P08",           "papers/08_ugp_foundational_monograph/Universal_Generative_Principle_UGP_Paper.tex",
                      "UGP Foundational Monograph"),
    ("P09",           "papers/09_architecture/The Architecture of a Computable Universe.tex",
                      "Architecture of a Computable Universe"),
    ("P10",           "papers/10_reflexive_law/reflexive_reality_self_defining_law.tex",
                      "Reflexive Reality Self-Defining Law"),
    ("P11",           "papers/11_ontological_dissonance/Ontological_Dissonance_Minimization_SDS_Validation.tex",
                      "Ontological Dissonance Minimization"),
    ("P12",           "papers/12_unified_rigidity/Unified_Rigidity_Theorem.tex",
                      "Unified Rigidity Theorem"),
    ("P13",           "papers/13_MFRR_foundational_monograph/Mathematical_Foundations_of_Reflexive_Reality.tex",
                      "Mathematical Foundations of Reflexive Reality (Monograph)"),
    ("P13-monograph", "papers/13_MFRR_foundational_monograph/MFRR_explanatory_summaries/MFRR_FOR_PHYSICISTS/MFRR_FOR_PHYSICISTS_SHORT_OVERVIEW.tex",
                      "MFRR For Physicists"),
    ("P13-popular",   "papers/13_MFRR_foundational_monograph/MFRR_explanatory_summaries/MFRR_POPULAR_ARTICLE/MFRR_POPSCI_OVERVIEW.tex",
                      "MFRR Popular Overview"),
    ("P13-summary",   "papers/13_MFRR_foundational_monograph/MFRR_explanatory_summaries/SUMMARY_FOR_PHYSICISTS_AND_REFEREES/MFRR_summary_for_physicists.tex",
                      "MFRR Summary for Referees"),
    ("P14",           "papers/14_psc_concordance/PSC_Concordance.tex",
                      "PSC Concordance"),
    ("P15",           "papers/15_information_profit/Information_Profit_Principle.tex",
                      "Information Profit Principle"),
    ("P16",           "papers/16_bh_unitarity/BH_Reflexive_Unitarity.tex",
                      "BH Reflexive Unitarity"),
    ("P17",           "papers/17_braid_atlas/Braid_Atlas_v2_First_Principles.tex",
                      "Canonical Braid Atlas v2.0"),
    ("P18",           "papers/18_koide_cyclotomic/koide_cyclotomic_closed_form.tex",
                      "Koide Cyclotomic Closed Form"),
    ("P19",           "papers/19_cyclotomic_mass_structure/cyclotomic_12_mass_structure.tex",
                      "Cyclotomic Mass Structure"),
    ("P20",           "papers/20_mfrr_physics_survey/MFRR_Physics_Survey.tex",
                      "MFRR Physics Survey"),
    ("P21",           "papers/21_neutrino_masses/neutrino_masses_from_braid_atlas.tex",
                      "Neutrino Masses from Braid Atlas"),
    ("P22",           "papers/22_ugp_dynamics/ugp_dynamics_paper.tex",
                      "UGP Interaction Skeleton Theorem"),
    ("P23",           "papers/23_closure_structure/closure_structure_ugp.tex",
                      "Closure Structure"),
    ("P24",           "papers/24_deeper_theory/ugp_deeper_theory.tex",
                      "Arithmetic Uniqueness of the Standard Model"),
    ("P25",           "papers/25_genetic_code/genetic_code_ugp_paper.tex",
                      "Structural Admissibility Selects the Standard Genetic Code"),
    ("P26",           "papers/26_general_selection/general_selection_theory.tex",
                      "A General Theory of Selection"),
    ("P27",           "papers/27_SRRG/srrg_paper.tex",
                      "Self-Referential Reality Generation (SRRG)"),
    ("P28",           "papers/28_computational_universality/computational_universality_ugp.tex",
                      "Computational Universality and the Standard Model"),
    ("P29",           "papers/29_dark_sector_braid_atlas/Dark_Sector_Braid_Atlas_Paper.tex",
                      "The Mirror Branch Braid Atlas (Dark Sector)"),
    ("P30",           "papers/30_cook_theorem/cook_theorem_paper.tex",
                      "Machine-Certified Formalization of Cook's Theorem"),
    ("P31",           "papers/31_weinberg_angle/weinberg_angle_paper.tex",
                      "Arithmetic Derivation of the Electroweak Mixing Angle"),
    ("P32",           "papers/32_ckm_matrix/ckm_matrix_paper.tex",
                      "The CKM Wolfenstein Parameters from GTE"),
    ("P33",           "papers/33_deeper_consequences/deeper_consequences_paper.tex",
                      "Deeper Consequences of Arithmetic Universality"),
    ("P34",           "papers/34_gte_mobius_substrate/gte_mobius_substrate_paper.tex",
                      "The GTE-Mobius Substrate"),
    ("P35",           "papers/35_gte_unification/gte_unification_paper.tex",
                      "GTE Unification"),
    ("P36",           "papers/36_emergent_gravity_cmca/emergent_gravity_paper.tex",
                      "Emergent Gravity from Rule 110 Cellular Automaton"),
    ("P37",           "papers/37_quantum_mechanics/quantum_mechanics_paper.tex",
                      "Quantum Mechanics from Rule 110"),
    ("P38",           "papers/38_emergent_gravity_phimdl/emergent_gravity_gte_phimdl.tex",
                      "Emergent Gravity from the Phi_MDL Field"),
    ("P39",           "papers/39_qcd_from_gte/gte_qcd_structure_paper.tex",
                      "QCD Structure from the GTE Substrate"),
    ("P40",           "papers/40_gf7_polynomial_universality/gf7_polynomial_universality.tex",
                      "Algebraic Characterization of Rule 110 over GF(7)"),
    ("P41",           "papers/41_three_layer_chiral_minkowski_ca/three_layer_chiral_minkowski_ca_paper.tex",
                      "The Three-Layer Chiral Minkowski Cellular Automaton"),
    ("P42",           "papers/42_phimdl_field/phimdl_field_paper.tex",
                      "The Phi_MDL Field: Quantum Structure and Born Rule"),
    ("P43",           "papers/43_phimdl_completeness/phimdl_completeness_paper.tex",
                      "The Complete Phi_MDL Framework"),
    ("P44",           "papers/44_quantum_gravity/quantum_gravity_completeness.tex",
                      "Quantum Gravity in the GTE/Phi_MDL Framework: Functional Completeness"),
    ("P45",           "papers/45_three_tape_cmca/three_tape_cmca_paper.tex",
                      "The Three-Tape Chiral Minkowski Cellular Automaton"),
    ("P46",           "papers/46_gte_polynomial_uft/gte_polynomial_uft_paper.tex",
                      "The GTE Polynomial as Unified Field Theory"),
    ("P47",           "papers/47_gte_cosmology/gte_cosmology_paper.tex",
                      "Cosmological Predictions of the GTE/Phi_MDL Framework"),
]


def main() -> None:
    os.makedirs(os.path.dirname(DEST), exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines_out: list[str] = []
    header = [
        "#" * 80,
        "# UGP PHYSICS — CONSOLIDATED PAPER SOURCES",
        f"# Generated: {now}",
        f"# Repository: {REPO}",
        f"# Papers included: {len(PAPERS)}",
        "# Format: LaTeX source (.tex) with agent-searchable section banners",
        "#",
        "# QUICK NAVIGATION — search for these exact strings:",
    ]
    for label, _, title in PAPERS:
        header.append(f"#   BEGIN PAPER {label:<12} {title}")
    header.append("#" * 80)
    lines_out.extend(header)
    lines_out.append("")

    included = 0
    skipped = []
    for label, rel_path, title in PAPERS:
        tex_path = os.path.join(REPO, rel_path)
        banner = f"# BEGIN PAPER {label}"
        end_banner = f"# END PAPER {label}"
        sep = "#" * 80
        if not os.path.exists(tex_path):
            lines_out.append(sep)
            lines_out.append(banner)
            lines_out.append(f"# Title: {title}")
            lines_out.append(f"# FILE NOT FOUND: {rel_path}")
            lines_out.append(end_banner)
            lines_out.append("")
            skipped.append(label)
            continue
        with open(tex_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        lines_out.append(sep)
        lines_out.append(banner)
        lines_out.append(f"# Title: {title}")
        lines_out.append(f"# Source: {rel_path}")
        lines_out.append(sep)
        lines_out.append(content)
        lines_out.append("")
        lines_out.append(end_banner)
        lines_out.append("")
        included += 1

    with open(DEST, "w", encoding="utf-8") as f:
        f.write("\n".join(lines_out))

    size_kb = os.path.getsize(DEST) // 1024
    total_lines = len(lines_out)
    print(f"Written: {DEST}")
    print(f"Size:    {size_kb:,} KB  ({total_lines:,} lines)")
    print(f"Papers:  {included} included, {len(skipped)} skipped")
    if skipped:
        print(f"Skipped: {', '.join(skipped)}")


if __name__ == "__main__":
    main()
