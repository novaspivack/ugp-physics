# PROVENANCE — The Architecture of a Computable Universe

**Paper:** `The Architecture of a Computable Universe.tex`  
**Status:** Conceptual synthesis — no novel code; all numerical results from companion papers  
**Last updated:** 2026-04-13

---

## Overlap with meta-laws paper (2026-04-13)

This paper's "five meta-laws" and the meta-laws paper's "nine ML-x" are **compatible and complementary** — not conflicting:

| Paper 12 meta-law | Meta-laws paper relationship | Citation |
|---|---|---|
| Meta-Law I: Constrained Contingency (unique program) | Uniqueness paper (sieve result) | `\cite{SpivackUGPUniqueness}` already in paper |
| Meta-Law II: Ontological Scaffolding (Loop Kernel) | Not in ML-1–ML-9; new content | No ML-x overlap |
| Meta-Law III: Reflexive Computation (Turing universal) | Dynamics paper (CA universality), ugp-lean T1/T2 | `\cite{SpivackUGPFormalization,ugp-lean}` already |
| Meta-Law IV: Constants as Compression Ratios | SM constants paper + gauge couplings paper (Paper 02) | `\cite{Spivack2025Algebraic}` already |
| Meta-Law V: Necessary Observers | Not in ML-1–ML-9; in Reflexive Reality paper | `\cite{Spivack2025TAD}` already |

**Paper 12 already cites the Meta-Laws paper** via `\cite{Spivack2025OrganizingPrinciple}` in the introduction.  
**Meta-laws paper** (`ugp_meta_laws.tex`) already references the organizing principle framing.  
No additional bidirectional citation changes needed.

---

## Code availability

This paper is a conceptual synthesis with **no novel computational artifacts**. The numerical results cited are produced by companion papers; reproduction is via those papers' `REPRODUCE.md` files:

| Claim | Companion | Experiment |
|-------|-----------|-----------|
| ML-I uniqueness (n=10, b₁=73) | Uniqueness paper | `ugp_uniqueness_sieve.py` |
| ML-III Turing universality | `ugp-lean` | `Universality.TuringUniversal` |
| ML-III reversibility | `ugp-lean` | `UWCAHistoryReversible` |
| ML-IV gauge couplings (g₁²,g₂²,g₃²) | Math Foundations paper | `gauge_couplings_unified.py` |
| ML-IV SU(2)/SU(3) rigidity | Math Foundations paper | `su2_rigidity_proof.py`, `su3_rigidity_proof.py` |

---

## Changes made (2026-04-13)

1. Added `\section*{Code and Data Availability}` before bibliography
2. Removed spurious `%` comment from section title  
3. Remaining 0.67pt overfull in section title heading — cosmetic only, not addressed
