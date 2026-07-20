#!/usr/bin/env python3
"""
QA Standardization pass for all UGP Physics tutorials.
Applies: series header, navigation box, Further Reading box,
tocdepth, color fixes.
"""

import re, sys, os

BASE = "/Users/nova/ugp-physics/tutorials"

# ─── Per-tutorial metadata ───────────────────────────────────────────────────

TUTORIALS = {
    "polynomial_cheatsheet": {
        "file": "polynomial_cheatsheet/polynomial_cheatsheet.tex",
        "nav_prereqs": r"None — this is the first tutorial in the series.",
        "nav_next": (
            r"\emph{How the UWCA Works} $\cdot$ "
            r"\emph{Perfect Self-Containment and MDL} $\cdot$ "
            r"\emph{How MDL Selects the 19-Bit Polynomial}"
        ),
        "nav_seealso": (
            r"\emph{From the Arithmetic Substrate to Particle Masses}"
        ),
        "further_reading": r"""The results in this tutorial are derived in the following papers,
all available open-access on Zenodo and at
\href{https://novaspivack.com/research}{novaspivack.com/research}:
\begin{itemize}
  \item \textbf{P48 --- The Complete GTE Framework} (main synthesis monograph):\\
        \href{https://doi.org/10.5281/zenodo.20560550}{doi.org/10.5281/zenodo.20560550}
  \item \textbf{P01 --- Standard Model Parameters from the UGP} (first-principles derivation):\\
        \href{https://doi.org/10.5281/zenodo.20168787}{doi.org/10.5281/zenodo.20168787}
  \item \textbf{P40 --- GF(7) Polynomial Universality} (uniqueness theorem):\\
        \href{https://doi.org/10.5281/zenodo.20417566}{doi.org/10.5281/zenodo.20417566}
\end{itemize}
Lean~4 machine proofs: \href{https://github.com/novaspivack/ugp-lean}{github.com/novaspivack/ugp-lean}""",
    },
    "uwca_tutorial": {
        "file": "uwca_tutorial/uwca_tutorial.tex",
        "nav_prereqs": (
            r"\emph{The GTE Polynomial: A Step-by-Step Cheat Sheet} --- "
            r"introduces $p(L,C,R)$ and Rule~110."
        ),
        "nav_next": (
            r"\emph{The Three-Tape CMCA} (how the CA becomes 3+1D) $\cdot$ "
            r"\emph{The $\Phi_{\rm MDL}$ Field}"
        ),
        "nav_seealso": r"\emph{From the Arithmetic Substrate to Particle Masses}",
        "further_reading": r"""The results in this tutorial are derived in the following papers,
all available open-access on Zenodo and at
\href{https://novaspivack.com/research}{novaspivack.com/research}:
\begin{itemize}
  \item \textbf{P28 --- Computational Universality} (UWCA construction):\\
        \href{https://doi.org/10.5281/zenodo.20259513}{doi.org/10.5281/zenodo.20259513}
  \item \textbf{P48 --- The Complete GTE Framework} (main synthesis monograph):\\
        \href{https://doi.org/10.5281/zenodo.20560550}{doi.org/10.5281/zenodo.20560550}
\end{itemize}
Lean~4 machine proofs: \href{https://github.com/novaspivack/ugp-lean}{github.com/novaspivack/ugp-lean}""",
    },
    "ugp_gte_masses": {
        "file": "ugp_gte_masses/ugp_gte_masses_tutorial.tex",
        "nav_prereqs": (
            r"\emph{The GTE Polynomial: A Step-by-Step Cheat Sheet} $\cdot$ "
            r"\emph{How the UWCA Works}"
        ),
        "nav_next": r"\emph{Perfect Self-Containment and MDL}",
        "nav_seealso": (
            r"\emph{How the Standard Model Quantum Numbers Emerge from $\mathbb{Z}_7\times\mathbb{Z}_3$}"
        ),
        "further_reading": r"""The results in this tutorial are derived in the following papers,
all available open-access on Zenodo and at
\href{https://novaspivack.com/research}{novaspivack.com/research}:
\begin{itemize}
  \item \textbf{P01 --- Standard Model Parameters from the UGP} (charged fermion masses):\\
        \href{https://doi.org/10.5281/zenodo.20168787}{doi.org/10.5281/zenodo.20168787}
  \item \textbf{P48 --- The Complete GTE Framework} (main synthesis monograph):\\
        \href{https://doi.org/10.5281/zenodo.20560550}{doi.org/10.5281/zenodo.20560550}
\end{itemize}
Lean~4 machine proofs: \href{https://github.com/novaspivack/ugp-lean}{github.com/novaspivack/ugp-lean}""",
    },
    "psc_mdl": {
        "file": "psc_mdl/psc_mdl_tutorial.tex",
        "nav_prereqs": (
            r"\emph{The GTE Polynomial: A Step-by-Step Cheat Sheet} $\cdot$ "
            r"\emph{From the Arithmetic Substrate to Particle Masses}"
        ),
        "nav_next": r"\emph{How MDL Selects the 19-Bit Polynomial}",
        "nav_seealso": r"\emph{The $\Phi_{\rm MDL}$ Field}",
        "further_reading": r"""The results in this tutorial are derived in the following papers,
all available open-access on Zenodo and at
\href{https://novaspivack.com/research}{novaspivack.com/research}:
\begin{itemize}
  \item \textbf{P48 --- The Complete GTE Framework} (main synthesis monograph, includes
        full PSC and MDL treatment):\\
        \href{https://doi.org/10.5281/zenodo.20560550}{doi.org/10.5281/zenodo.20560550}
  \item \textbf{P01 --- Standard Model Parameters from the UGP}:\\
        \href{https://doi.org/10.5281/zenodo.20168787}{doi.org/10.5281/zenodo.20168787}
\end{itemize}
Lean~4 machine proofs: \href{https://github.com/novaspivack/ugp-lean}{github.com/novaspivack/ugp-lean}""",
    },
    "mdl_selection": {
        "file": "mdl_selection/mdl_selection_tutorial.tex",
        "nav_prereqs": (
            r"\emph{The GTE Polynomial: A Step-by-Step Cheat Sheet} $\cdot$ "
            r"\emph{Perfect Self-Containment and MDL}"
        ),
        "nav_next": r"\emph{The $\Phi_{\rm MDL}$ Field}",
        "nav_seealso": r"\emph{How the UWCA Works}",
        "further_reading": r"""The results in this tutorial are derived in the following papers,
all available open-access on Zenodo and at
\href{https://novaspivack.com/research}{novaspivack.com/research}:
\begin{itemize}
  \item \textbf{P40 --- GF(7) Polynomial Universality} (MDL uniqueness theorem):\\
        \href{https://doi.org/10.5281/zenodo.20417566}{doi.org/10.5281/zenodo.20417566}
  \item \textbf{P48 --- The Complete GTE Framework} (main synthesis monograph):\\
        \href{https://doi.org/10.5281/zenodo.20560550}{doi.org/10.5281/zenodo.20560550}
\end{itemize}
Lean~4 machine proofs: \href{https://github.com/novaspivack/ugp-lean}{github.com/novaspivack/ugp-lean}""",
    },
    "phimdl_field": {
        "file": "phimdl_field/phimdl_field_tutorial.tex",
        "nav_prereqs": (
            r"\emph{The GTE Polynomial} $\cdot$ "
            r"\emph{How the UWCA Works} $\cdot$ "
            r"\emph{The Three-Tape CMCA}"
        ),
        "nav_next": (
            r"\emph{How the Standard Model Quantum Numbers Emerge} $\cdot$ "
            r"\emph{Gravity from Description-Length Minimization}"
        ),
        "nav_seealso": r"\emph{The Born Rule as a Theorem}",
        "further_reading": r"""The results in this tutorial are derived in the following papers,
all available open-access on Zenodo and at
\href{https://novaspivack.com/research}{novaspivack.com/research}:
\begin{itemize}
  \item \textbf{P42 --- The $\Phi_{\rm MDL}$ Field} (Lagrangian and kink spectrum):\\
        \href{https://doi.org/10.5281/zenodo.20417576}{doi.org/10.5281/zenodo.20417576}
  \item \textbf{P43 --- The Complete $\Phi_{\rm MDL}$ Framework} (no-CA-replica theorem):\\
        \href{https://doi.org/10.5281/zenodo.20417578}{doi.org/10.5281/zenodo.20417578}
  \item \textbf{P45 --- The Three-Tape CMCA} (3+1D architecture):\\
        \href{https://doi.org/10.5281/zenodo.20465805}{doi.org/10.5281/zenodo.20465805}
  \item \textbf{P48 --- The Complete GTE Framework} (main synthesis monograph):\\
        \href{https://doi.org/10.5281/zenodo.20560550}{doi.org/10.5281/zenodo.20560550}
\end{itemize}
Lean~4 machine proofs: \href{https://github.com/novaspivack/ugp-lean}{github.com/novaspivack/ugp-lean}""",
    },
    "quantum_numbers": {
        "file": "quantum_numbers/quantum_numbers_tutorial.tex",
        "nav_prereqs": (
            r"\emph{The GTE Polynomial: A Step-by-Step Cheat Sheet} $\cdot$ "
            r"\emph{The $\Phi_{\rm MDL}$ Field}"
        ),
        "nav_next": (
            r"\emph{Why the Strong CP Problem Is Solved} $\cdot$ "
            r"\emph{The Weinberg Angle} $\cdot$ "
            r"\emph{The Born Rule as a Theorem}"
        ),
        "nav_seealso": None,
        "further_reading": r"""The results in this tutorial are derived in the following papers,
all available open-access on Zenodo and at
\href{https://novaspivack.com/research}{novaspivack.com/research}:
\begin{itemize}
  \item \textbf{P35 --- GTE Unification} (quantum numbers, charge, generations):\\
        \href{https://doi.org/10.5281/zenodo.20319421}{doi.org/10.5281/zenodo.20319421}
  \item \textbf{P48 --- The Complete GTE Framework} (main synthesis monograph):\\
        \href{https://doi.org/10.5281/zenodo.20560550}{doi.org/10.5281/zenodo.20560550}
\end{itemize}
Lean~4 machine proofs: \href{https://github.com/novaspivack/ugp-lean}{github.com/novaspivack/ugp-lean}""",
    },
    "strong_cp": {
        "file": "strong_cp/strong_cp_tutorial.tex",
        "nav_prereqs": (
            r"\emph{How the Standard Model Quantum Numbers Emerge} $\cdot$ "
            r"\emph{The GTE Polynomial: A Step-by-Step Cheat Sheet}"
        ),
        "nav_next": None,
        "nav_seealso": (
            r"\emph{The Weinberg Angle, Fine-Structure Constant, and Gauge Couplings} $\cdot$ "
            r"\emph{How the Standard Model Quantum Numbers Emerge}"
        ),
        "further_reading": r"""The results in this tutorial are derived in the following papers,
all available open-access on Zenodo and at
\href{https://novaspivack.com/research}{novaspivack.com/research}:
\begin{itemize}
  \item \textbf{P35 --- GTE Unification} (contains the $F_{21}$ strong CP proofs):\\
        \href{https://doi.org/10.5281/zenodo.20319421}{doi.org/10.5281/zenodo.20319421}
  \item \textbf{P48 --- The Complete GTE Framework} (main synthesis monograph, Ch.~7):\\
        \href{https://doi.org/10.5281/zenodo.20560550}{doi.org/10.5281/zenodo.20560550}
\end{itemize}
Lean~4 machine proofs (including \texttt{f21\_theta\_term\_vanishes}):
\href{https://github.com/novaspivack/ugp-lean}{github.com/novaspivack/ugp-lean}""",
    },
    "weinberg_angle": {
        "file": "weinberg_angle/weinberg_angle_tutorial.tex",
        "nav_prereqs": (
            r"\emph{How the Standard Model Quantum Numbers Emerge} $\cdot$ "
            r"\emph{The GTE Polynomial: A Step-by-Step Cheat Sheet}"
        ),
        "nav_next": r"\emph{Gravity from Description-Length Minimization}",
        "nav_seealso": r"\emph{Why the Strong CP Problem Is Solved}",
        "further_reading": r"""The results in this tutorial are derived in the following papers,
all available open-access on Zenodo and at
\href{https://novaspivack.com/research}{novaspivack.com/research}:
\begin{itemize}
  \item \textbf{P31 --- Arithmetic Derivation of the Weinberg Angle}:\\
        \href{https://doi.org/10.5281/zenodo.20319413}{doi.org/10.5281/zenodo.20319413}
  \item \textbf{P35 --- GTE Unification} (electroweak sector):\\
        \href{https://doi.org/10.5281/zenodo.20319421}{doi.org/10.5281/zenodo.20319421}
  \item \textbf{P48 --- The Complete GTE Framework} (main synthesis monograph):\\
        \href{https://doi.org/10.5281/zenodo.20560550}{doi.org/10.5281/zenodo.20560550}
\end{itemize}
Lean~4 machine proofs: \href{https://github.com/novaspivack/ugp-lean}{github.com/novaspivack/ugp-lean}""",
    },
    "gravity": {
        "file": "gravity/gravity_tutorial.tex",
        "nav_prereqs": (
            r"\emph{The $\Phi_{\rm MDL}$ Field} $\cdot$ "
            r"\emph{The Three-Tape CMCA}"
        ),
        "nav_next": r"\emph{The Cosmological Constant}",
        "nav_seealso": r"\emph{The Born Rule as a Theorem}",
        "further_reading": r"""The results in this tutorial are derived in the following papers,
all available open-access on Zenodo and at
\href{https://novaspivack.com/research}{novaspivack.com/research}:
\begin{itemize}
  \item \textbf{P36 --- Emergent Gravity from Rule~110} (CMCA gravity derivation):\\
        \href{https://doi.org/10.5281/zenodo.20319425}{doi.org/10.5281/zenodo.20319425}
  \item \textbf{P38 --- Emergent Gravity from $\Phi_{\rm MDL}$} (Einstein equations, $G_N$):\\
        \href{https://doi.org/10.5281/zenodo.20417559}{doi.org/10.5281/zenodo.20417559}
  \item \textbf{P45 --- The Three-Tape CMCA} (3+1D architecture and geodesics):\\
        \href{https://doi.org/10.5281/zenodo.20465805}{doi.org/10.5281/zenodo.20465805}
  \item \textbf{P48 --- The Complete GTE Framework} (main synthesis monograph):\\
        \href{https://doi.org/10.5281/zenodo.20560550}{doi.org/10.5281/zenodo.20560550}
\end{itemize}
Lean~4 machine proofs: \href{https://github.com/novaspivack/ugp-lean}{github.com/novaspivack/ugp-lean}""",
    },
    "born_rule": {
        "file": "born_rule/born_rule_tutorial.tex",
        "nav_prereqs": (
            r"\emph{How the Standard Model Quantum Numbers Emerge} $\cdot$ "
            r"\emph{The $\Phi_{\rm MDL}$ Field}"
        ),
        "nav_next": (
            r"\emph{Transputation: Quantum Measurement at Turing Degree $\mathbf{0}'$} $\cdot$ "
            r"\emph{The Cosmological Constant}"
        ),
        "nav_seealso": None,
        "further_reading": r"""The results in this tutorial are derived in the following papers,
all available open-access on Zenodo and at
\href{https://novaspivack.com/research}{novaspivack.com/research}:
\begin{itemize}
  \item \textbf{P37 --- Quantum Mechanics from Rule~110} (Born rule as theorem):\\
        \href{https://doi.org/10.5281/zenodo.20319431}{doi.org/10.5281/zenodo.20319431}
  \item \textbf{P51 --- Transputation Versus Computation} (four derivations, DSAC):\\
        \href{https://doi.org/10.5281/zenodo.20611502}{doi.org/10.5281/zenodo.20611502}
  \item \textbf{P48 --- The Complete GTE Framework} (main synthesis monograph, Ch.~10):\\
        \href{https://doi.org/10.5281/zenodo.20560550}{doi.org/10.5281/zenodo.20560550}
\end{itemize}
Lean~4 machine proofs: \href{https://github.com/novaspivack/ugp-lean}{github.com/novaspivack/ugp-lean}""",
    },
    "cosmological_constant": {
        "file": "cosmological_constant/cc_tutorial.tex",
        "nav_prereqs": (
            r"\emph{Gravity from Description-Length Minimization} $\cdot$ "
            r"\emph{The Born Rule as a Theorem}"
        ),
        "nav_next": r"\emph{$\mathbb{Z}_7$ Defect Cosmology}",
        "nav_seealso": None,
        "further_reading": r"""The results in this tutorial are derived in the following papers,
all available open-access on Zenodo and at
\href{https://novaspivack.com/research}{novaspivack.com/research}:
\begin{itemize}
  \item \textbf{P47 --- GTE Cosmological Predictions} (CC derivation and bracket):\\
        \href{https://doi.org/10.5281/zenodo.20465803}{doi.org/10.5281/zenodo.20465803}
  \item \textbf{P48 --- The Complete GTE Framework} (main synthesis monograph, Ch.~11):\\
        \href{https://doi.org/10.5281/zenodo.20560550}{doi.org/10.5281/zenodo.20560550}
\end{itemize}
Lean~4 machine proofs: \href{https://github.com/novaspivack/ugp-lean}{github.com/novaspivack/ugp-lean}""",
    },
    "defect_cosmology": {
        "file": "defect_cosmology/defect_cosmology_tutorial.tex",
        "nav_prereqs": (
            r"\emph{The Cosmological Constant} $\cdot$ "
            r"\emph{Gravity from Description-Length Minimization}"
        ),
        "nav_next": None,
        "nav_seealso": r"\emph{The $\Phi_{\rm MDL}$ Field}",
        "further_reading": r"""The results in this tutorial are derived in the following papers,
all available open-access on Zenodo and at
\href{https://novaspivack.com/research}{novaspivack.com/research}:
\begin{itemize}
  \item \textbf{P47 --- GTE Cosmological Predictions} (defect cosmology, relic constraints):\\
        \href{https://doi.org/10.5281/zenodo.20465803}{doi.org/10.5281/zenodo.20465803}
  \item \textbf{P42 --- The $\Phi_{\rm MDL}$ Field} (kink/domain-wall spectrum):\\
        \href{https://doi.org/10.5281/zenodo.20417576}{doi.org/10.5281/zenodo.20417576}
  \item \textbf{P48 --- The Complete GTE Framework} (main synthesis monograph):\\
        \href{https://doi.org/10.5281/zenodo.20560550}{doi.org/10.5281/zenodo.20560550}
\end{itemize}
Lean~4 machine proofs: \href{https://github.com/novaspivack/ugp-lean}{github.com/novaspivack/ugp-lean}""",
    },
    "transputation": {
        "file": "transputation/transputation_tutorial.tex",
        "nav_prereqs": (
            r"\emph{The Born Rule as a Theorem} $\cdot$ "
            r"\emph{How the Standard Model Quantum Numbers Emerge}"
        ),
        "nav_next": None,
        "nav_seealso": r"\emph{The Three-Tape CMCA} $\cdot$ \emph{The Born Rule as a Theorem}",
        "further_reading": r"""The results in this tutorial are derived in the following papers,
all available open-access on Zenodo and at
\href{https://novaspivack.com/research}{novaspivack.com/research}:
\begin{itemize}
  \item \textbf{P51 --- Transputation Versus Computation} (three-level MDL unification,
        degree-exact classification):\\
        \href{https://doi.org/10.5281/zenodo.20611502}{doi.org/10.5281/zenodo.20611502}
  \item \textbf{P48 --- The Complete GTE Framework} (main synthesis monograph, Ch.~10):\\
        \href{https://doi.org/10.5281/zenodo.20560550}{doi.org/10.5281/zenodo.20560550}
\end{itemize}
Lean~4 machine proofs: \href{https://github.com/novaspivack/ugp-lean}{github.com/novaspivack/ugp-lean}""",
    },
    "three_tape_cmca": {
        "file": "three_tape_cmca/three_tape_cmca_tutorial.tex",
        "nav_prereqs": (
            r"\emph{The GTE Polynomial: A Step-by-Step Cheat Sheet} $\cdot$ "
            r"\emph{How the UWCA Works}"
        ),
        "nav_next": (
            r"\emph{The $\Phi_{\rm MDL}$ Field} $\cdot$ "
            r"\emph{Gravity from Description-Length Minimization}"
        ),
        "nav_seealso": None,
        "further_reading": r"""The results in this tutorial are derived in the following papers,
all available open-access on Zenodo and at
\href{https://novaspivack.com/research}{novaspivack.com/research}:
\begin{itemize}
  \item \textbf{P41 --- The Three-Layer Chiral Minkowski CA} (single-tape architecture):\\
        \href{https://doi.org/10.5281/zenodo.20417572}{doi.org/10.5281/zenodo.20417572}
  \item \textbf{P45 --- The Three-Tape CMCA} (DPP, 3+1D emergence, all theorems):\\
        \href{https://doi.org/10.5281/zenodo.20465805}{doi.org/10.5281/zenodo.20465805}
  \item \textbf{P48 --- The Complete GTE Framework} (main synthesis monograph):\\
        \href{https://doi.org/10.5281/zenodo.20560550}{doi.org/10.5281/zenodo.20560550}
\end{itemize}
Lean~4 machine proofs: \href{https://github.com/novaspivack/ugp-lean}{github.com/novaspivack/ugp-lean}""",
    },
}

# ─── Standard color definitions ──────────────────────────────────────────────

STANDARD_COLORS = r"""\definecolor{boxblue}{RGB}{220,235,255}
\definecolor{boxorange}{RGB}{255,240,210}
\definecolor{boxgreen}{RGB}{220,245,220}"""

# ─── Builder functions ───────────────────────────────────────────────────────

def build_nav_box(prereqs, next_tuts, seealso):
    lines = [
        r"\begin{tcolorbox}[colback=blue!6,colframe=blue!40!black,",
        r"  title=\textbf{UGP Physics Tutorial Series}]",
    ]
    if prereqs:
        lines.append(r"\textbf{Prerequisites (read first):} " + prereqs + r"\\[4pt]")
    else:
        lines.append(r"\textbf{Prerequisites:} None --- this is the first tutorial.\\[4pt]")
    if next_tuts:
        lines.append(r"\textbf{Next tutorials:} " + next_tuts + r"\\[4pt]")
    if seealso:
        lines.append(r"\textbf{See also:} " + seealso)
    lines.append(r"\end{tcolorbox}")
    lines.append("")
    return "\n".join(lines)


def build_further_reading_box(content):
    return (
        r"\section*{Further Reading}" + "\n"
        r"\begin{tcolorbox}[colback=orange!8,colframe=orange!50!black," + "\n"
        r"  title=\textbf{Primary Sources}]" + "\n"
        + content + "\n"
        r"\end{tcolorbox}" + "\n"
    )


def add_series_subtitle(text):
    """Insert \\[4pt]\\normalsize\\textit{UGP Physics Tutorial Series} into the title."""
    # We look for patterns in \title{...} and insert before the closing }
    # The title ends just before \author or \date on a fresh line.
    # Strategy: find the last }} or } right before \n\author or \n\date
    # and insert the series line.

    # Match the title block
    # Pattern: \title{<content>} where content may span lines
    pattern = re.compile(
        r'(\\title\{)(.*?)(^\})',
        re.DOTALL | re.MULTILINE
    )
    # Already has series?
    if 'UGP Physics Tutorial Series' in text:
        return text, False

    # Find \title{ ... } block
    # The title block ends with a lone } at the start of a line before \author or \date
    title_start = text.find(r'\title{')
    if title_start == -1:
        return text, False

    # Find the matching closing brace
    depth = 0
    i = title_start + len(r'\title{')
    while i < len(text):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            if depth == 0:
                break
            depth -= 1
        i += 1

    # Insert series line before the closing brace
    series_line = r'\\[4pt]\normalsize\textit{UGP Physics Tutorial Series}'
    new_text = text[:i] + series_line + text[i:]
    return new_text, True


def add_tocdepth(text):
    """Add \\setcounter{tocdepth}{2} after \\begin{document} if not present."""
    if r'\setcounter{tocdepth}' in text:
        return text, False
    text = text.replace(
        r'\begin{document}',
        r'\begin{document}' + '\n' + r'\setcounter{tocdepth}{2}',
        1
    )
    return text, True


def add_nav_box(text, prereqs, next_tuts, seealso):
    """Add navigation box after \\tableofcontents\\n\\newpage if not present."""
    # Check if already has UGP Physics Tutorial Series box
    if (r'\textbf{UGP Physics Tutorial Series}' in text and
            r'\textbf{Prerequisites' in text):
        # Already has a nav box — replace it with standard format
        # Find and replace the existing box
        old_box_pattern = re.compile(
            r'\\begin\{tcolorbox\}\[.*?UGP Physics Tutorial Series.*?\].*?\\end\{tcolorbox\}',
            re.DOTALL
        )
        nav_box = build_nav_box(prereqs, next_tuts, seealso)
        new_text, count = old_box_pattern.subn(nav_box.strip(), text, count=1)
        return new_text, count > 0

    # Find \\tableofcontents\n\\newpage and insert after
    toc_patterns = [
        r'\tableofcontents' + '\n' + r'\newpage',
        r'\tableofcontents' + '\n' + '\n' + r'\newpage',
    ]
    nav_box = build_nav_box(prereqs, next_tuts, seealso)

    for pat in toc_patterns:
        if pat in text:
            text = text.replace(pat, pat + '\n\n' + nav_box, 1)
            return text, True

    return text, False


def add_further_reading(text, content):
    """Add/replace Further Reading section before \\end{document}."""
    fr_box = build_further_reading_box(content)

    # Remove existing informal further-reading content if present
    # (patterns like "\noindent\textbf{Further reading" followed by stuff before \end{document})
    existing_fr_patterns = [
        # Pattern: \bigskip\noindent\textbf{Further reading...} ... \end{document}
        re.compile(
            r'\\bigskip\s*\\noindent\\textbf\{Further reading[^\}]*\}.*?(?=\\end\{document\})',
            re.DOTALL | re.IGNORECASE
        ),
        # Pattern: \bigskip\n\noindent\n\textbf{Further reading...}
        re.compile(
            r'\n\\bigskip\n\\noindent\\textbf\{(?:For )?[Ff]urther [Rr]eading.*?(?=\\end\{document\})',
            re.DOTALL
        ),
    ]

    if r'\section*{Further Reading}' in text:
        # Already has standardized FR — replace it
        fr_section_pattern = re.compile(
            r'\\section\*\{Further Reading\}.*?(?=\\end\{document\})',
            re.DOTALL
        )
        new_text, count = fr_section_pattern.subn('\n' + fr_box + '\n', text, count=1)
        return new_text, count > 0

    # Try to remove existing informal FR
    for pat in existing_fr_patterns:
        m = pat.search(text)
        if m:
            text = text[:m.start()] + '\n' + text[m.end():]
            break

    # Insert before \end{document}
    if r'\end{document}' in text:
        text = text.replace(
            r'\end{document}',
            '\n' + fr_box + '\n' + r'\end{document}',
            1
        )
        return text, True

    return text, False


def fix_colors(text, key):
    """Add missing standard color definitions."""
    changes = []
    colors_needed = {
        'boxblue': r'\definecolor{boxblue}{RGB}{220,235,255}',
        'boxorange': r'\definecolor{boxorange}{RGB}{255,240,210}',
        'boxgreen': r'\definecolor{boxgreen}{RGB}{220,245,220}',
    }
    # Fix any wrong RGB values
    for color, correct_def in colors_needed.items():
        # Replace any existing definition with correct one
        pat = re.compile(r'\\definecolor\{' + color + r'\}\{RGB\}\{[^\}]+\}')
        if pat.search(text):
            new_text = pat.sub(lambda m: correct_def, text)
            if new_text != text:
                changes.append(f"  Fixed {color} RGB")
                text = new_text

    # Add missing colors
    missing = []
    for color, defn in colors_needed.items():
        if r'\definecolor{' + color + '}' not in text:
            missing.append(defn)

    if missing:
        # Find a good insertion point — after last \definecolor or before \newcommand
        insert_after = None
        for pat in [r'\definecolor{', r'\newcommand{', r'\begin{document}']:
            pos = text.rfind(pat)
            if pos != -1:
                # Find end of that line
                eol = text.find('\n', pos)
                if eol != -1:
                    insert_after = eol
                    break

        if insert_after is not None:
            insertion = '\n'.join(missing)
            text = text[:insert_after+1] + insertion + '\n' + text[insert_after+1:]
            changes.append(f"  Added missing colors: {[c.split('{')[1].split('}')[0] for c in missing]}")

    return text, changes


def process_tutorial(key, meta):
    filepath = os.path.join(BASE, meta['file'])
    if not os.path.exists(filepath):
        print(f"  [SKIP] {key}: file not found at {filepath}")
        return

    with open(filepath, 'r') as f:
        text = f.read()

    original = text
    changes = []

    # 1. Add series subtitle
    text, changed = add_series_subtitle(text)
    if changed:
        changes.append("  [+] Series subtitle added to title")

    # 2. Add tocdepth
    text, changed = add_tocdepth(text)
    if changed:
        changes.append("  [+] \\setcounter{tocdepth}{2} added")

    # 3. Add nav box
    text, changed = add_nav_box(
        text,
        meta['nav_prereqs'],
        meta.get('nav_next'),
        meta.get('nav_seealso'),
    )
    if changed:
        changes.append("  [+] Navigation box added/updated")

    # 4. Add Further Reading box
    text, changed = add_further_reading(text, meta['further_reading'])
    if changed:
        changes.append("  [+] Further Reading box added/updated")

    # 5. Fix colors
    text, color_changes = fix_colors(text, key)
    changes.extend(color_changes)

    if text != original:
        with open(filepath, 'w') as f:
            f.write(text)
        print(f"=== {key} ===")
        for c in changes:
            print(c)
    else:
        print(f"=== {key} === (no changes needed)")


def main():
    for key, meta in TUTORIALS.items():
        process_tutorial(key, meta)
    print("\nAll tutorials processed.")


if __name__ == '__main__':
    main()
