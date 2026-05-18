#!/usr/bin/env python3
"""
generate_consolidated_abstracts.py

Extract the abstract from each UGP paper and write a single
consolidated_abstracts.txt to specs/consolidated_papers_file/.

Each abstract is wrapped with a clear banner so it is agent-searchable.
"""
import os
import re
from datetime import datetime, timezone

REPO = os.path.dirname(os.path.abspath(__file__))
DEST = os.path.join(REPO, "specs", "consolidated_papers_file", "consolidated_abstracts.txt")

# Paper list: (label, tex_path_relative_to_repo, title)
# Add new papers here; the script will pick up and extract their abstracts automatically.
PAPERS = [
    ("P00",     "papers/00_survey_guide/ugp_survey_readers_guide.tex",
                "Survey and Reader's Guide to UGP Physics"),
    ("P01",     "papers/01_SM/standard_model_from_ugp.tex",
                "Standard Model from UGP (Flagship)"),
    ("P02",     "papers/02_GTE_spectrum/Particle_Spectrum_From_UGP_Paper.tex",
                "GTE Particle Spectrum at n=10"),
    ("P03",     "papers/03_nuclear/Nuclear_Physics_From_UGP_Paper.tex",
                "Nuclear Descriptors from GTE Coordinates"),
    ("P04",     "papers/04_dynamics_universality/ugp_dynamics_universality.tex",
                "UGP Dynamics: Attractors, Holography, Thermodynamics"),
    ("P05",     "papers/05_uniqueness/The Uniqueness of the Universal Generative Principle.tex",
                "Uniqueness of UGP: Two-Stage Proof"),
    ("P06",     "papers/06_math_foundations/algebraic_geometric_foundations_ugp.tex",
                "Algebraic and Geometric Foundations: SM Gauge Group"),
    ("P07",     "papers/07_meta_laws/ugp_meta_laws.tex",
                "UGP/GTE: Organizing Principle for Nine Meta-Laws"),
    ("P08",     "papers/08_ugp_foundational_monograph/Universal_Generative_Principle_UGP_Paper.tex",
                "UGP Foundational Monograph"),
    ("P09",     "papers/09_architecture/The Architecture of a Computable Universe.tex",
                "Architecture of a Computable Universe: Five Meta-Laws"),
    ("P10",     "papers/10_reflexive_law/reflexive_reality_self_defining_law.tex",
                "Reflexive Reality and Self-Defining Physical Law"),
    ("P11",     "papers/11_ontological_dissonance/Ontological_Dissonance_Minimization_SDS_Validation.tex",
                "Ontological Dissonance Minimization"),
    ("P12",     "papers/12_unified_rigidity/Unified_Rigidity_Theorem.tex",
                "Unified Rigidity Theorem for PSC/UGP Universes"),
    ("P13",     "papers/13_MFRR_foundational_monograph/Mathematical_Foundations_of_Reflexive_Reality.tex",
                "Mathematical Foundations of Reflexive Reality (Monograph)"),
    ("P14",     "papers/14_psc_concordance/PSC_Concordance.tex",
                "Formal and Computational Concordance on PSC"),
    ("P15",     "papers/15_information_profit/Information_Profit_Principle.tex",
                "Information Profit Principle"),
    ("P16",     "papers/16_bh_unitarity/BH_Reflexive_Unitarity.tex",
                "Black Hole Unitarity via Reflexive Unitarity"),
    ("P17",     "papers/17_braid_atlas/Braid_Atlas_v2_First_Principles.tex",
                "Braid Atlas v2: SM Topology from First Principles"),
    ("P18",     "papers/18_koide_cyclotomic/koide_cyclotomic_closed_form.tex",
                "Koide Relation as Cyclotomic-12 Closed Form"),
    ("P19",     "papers/19_cyclotomic_mass_structure/cyclotomic_12_mass_structure.tex",
                "Cyclotomic-12 Structure in Charged-Fermion Mass Spectrum"),
    ("P20",     "papers/20_mfrr_physics_survey/MFRR_Physics_Survey.tex",
                "MFRR Physics Survey (Journal Version)"),
    ("P21",     "papers/21_neutrino_masses/neutrino_masses_from_braid_atlas.tex",
                "Neutrino Mass-Squared Ratio from Braid Atlas"),
    ("P22",     "papers/22_ugp_dynamics/ugp_dynamics_paper.tex",
                "UGP Interaction Skeleton Theorem"),
    ("P23",     "papers/23_closure_structure/closure_structure_ugp.tex",
                "Substrate Depth and Self-Generated Mass"),
    ("P24",     "papers/24_deeper_theory/ugp_deeper_theory.tex",
                "Arithmetic Uniqueness of the Standard Model"),
    ("P25",     "papers/25_genetic_code/genetic_code_ugp_paper.tex",
                "Structural Admissibility Selects the Standard Genetic Code"),
    ("P26",     "papers/26_general_selection/general_selection_theory.tex",
                "A General Theory of Selection (in progress)"),
    ("P27",     "papers/27_SRRG/srrg_paper.tex",
                "Self-Referential Reality Generation (SRRG)"),
]


def extract_abstract(tex_path: str) -> str:
    """Extract the content between \\begin{abstract} and \\end{abstract}."""
    try:
        with open(tex_path, encoding="utf-8", errors="replace") as f:
            src = f.read()
    except FileNotFoundError:
        return "[FILE NOT FOUND]"

    # Find the abstract environment
    m = re.search(
        r"\\begin\{abstract\}(.*?)\\end\{abstract\}",
        src,
        re.DOTALL,
    )
    if not m:
        # Try tcolorbox-wrapped abstract for papers that use that style
        m = re.search(
            r"\\begin\{tcolorbox\}.*?Abstract.*?\](.*?)\\end\{tcolorbox\}",
            src,
            re.DOTALL | re.IGNORECASE,
        )
    if not m:
        return "[ABSTRACT NOT FOUND IN SOURCE]"

    text = m.group(1).strip()

    # Remove LaTeX commands for readability while keeping math inline
    # Strip comments
    text = re.sub(r"%.*$", "", text, flags=re.MULTILINE)
    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Trim trailing whitespace per line
    text = "\n".join(line.rstrip() for line in text.splitlines())
    return text.strip()


def build():
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "#" * 80,
        "# UGP PHYSICS — CONSOLIDATED ABSTRACTS",
        f"# Generated: {now}",
        f"# Repository: {REPO}",
        f"# Papers included: {len(PAPERS)} (P00 = survey guide; P01-P27 = main corpus)",
        "#",
        "# Run to regenerate: python3 generate_consolidated_abstracts.py",
        "# Add new papers to the PAPERS list at the top of that script.",
        "#",
        "# QUICK NAVIGATION — search for these exact strings:",
    ]
    for label, _, title in PAPERS:
        lines.append(f"#   ABSTRACT {label:<8}  {title}")
    lines += [
        "#" * 80,
        "",
    ]

    for label, rel_path, title in PAPERS:
        tex_path = os.path.join(REPO, rel_path)
        abstract = extract_abstract(tex_path)

        banner = "=" * 80
        lines += [
            banner,
            f"ABSTRACT {label}   {title}",
            f"Source: {rel_path}",
            banner,
            "",
            abstract,
            "",
        ]

    content = "\n".join(lines)
    os.makedirs(os.path.dirname(DEST), exist_ok=True)
    with open(DEST, "w", encoding="utf-8") as f:
        f.write(content)

    word_count = len(content.split())
    line_count = content.count("\n")
    print(f"Written: {DEST}")
    print(f"Size:    {len(content):,} bytes  ({line_count:,} lines,  {word_count:,} words)")
    print(f"Papers:  {len(PAPERS)}")


if __name__ == "__main__":
    build()
