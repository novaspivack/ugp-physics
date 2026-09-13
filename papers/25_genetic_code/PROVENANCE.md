# Provenance: Genetic Code Paper

**Paper:** *The Standard Genetic Code as the Unique Survivor of a Two-Stage Admissibility--Viability Sieve*  
**Version:** v1.0 (2026-05-08)  
**Status:** First draft complete — in review before submission

---

## Overview

This paper develops the UGP two-stage sieve framework for the genetic code
and demonstrates that the standard genetic code is the unique survivor (at
sampling depth $n = 10^5$) of eight simultaneous biological viability criteria
applied to the wobble-admissible codon space.

---

## Phase-by-Phase Results Log

| Phase | Script | Key Result | z-score |
|-------|--------|-----------|---------|
| 1 (wobble admissibility) | `codon_sieve.py` | 23^{27} admissible codes (10^{50}× reduction) | — |
| 2 (error + accessibility) | `codon_sieve_phase2.py` | z = +2.22σ; 0.198% beat standard | +2.22σ |
| 3 (+stop, +clustering) | `codon_sieve_phase3.py` | z = +2.43σ; 0.024% beat standard | +2.43σ |
| 4 (+completeness, DSAC) | `codon_sieve_phase4.py` | z = +3.59σ; ~0% beat standard | +3.59σ |
| 5 (+max-jump bound) | `codon_sieve_phase5.py` | z = +3.76σ; 0/50k beat standard | +3.76σ |
| 5 (re-run, paper metric) | `codon_sieve_phase6.py` | z = +3.22σ; 9/100k beat standard | +3.22σ |
| 6 (+evolvability +reachability +stops) | `codon_sieve_phase6.py` | 0/99,998 beat standard | +∞ (unique) |

Note: The Phase-5 z-scores from `codon_sieve_phase5.py` (z=+3.76σ) and the
Phase-6 paper metric (z=+3.22σ) differ slightly because the scoring formula was
refined for Phase 6. Both confirm the standard code is in the top 0.1%.

---

## CP-SAT Global Search

| Script | Objective | Best code found | Standard code |
|--------|-----------|-----------------|---------------|
| `codon_ortools_4crit.py` | 4-criterion | score = −0.051 | score = −0.338 |
| `codon_ortools_exact.py` | 5-criterion | score = −0.097 | score = −0.400 |

All CP-SAT codes scoring better than standard have max_jump ≤ 5.
These are eliminated by Stage 2G (evolvability criterion) in Phase 6.

---

## Uniqueness Result Details

From `codon_sieve_phase6.py` (seed=42, n=100,000):

| Filter level | Competitors vs. standard |
|-------------|--------------------------|
| 5-criterion metric | 9/100,000 (0.009%) |
| + Stage 2G (max_jump ≥ 6.0) | 9/99,998 (0.009%) |
| + Stage 2H (hist. reachability ≥ 0.56) | 1/~93,000 (<0.002%) |
| + Stage 2I (all 3 stops) | **0** |

The single competitor at the Stage-2H level:
- max_jump = 7.70, hist = 0.571
- Missing stop codon: Stop2 (UAG) absent → eliminated by Stage 2I

---

## Code Files

| File | Location | Purpose |
|------|----------|---------|
| `codon_sieve.py` | `code/` | Phase 1: wobble admissibility, error score |
| `codon_sieve_phase2.py` | `code/` | Phase 2: prebiotic accessibility |
| `codon_sieve_phase3.py` | `code/` | Phase 3: stop robustness, clustering |
| `codon_sieve_phase4.py` | `code/` | Phase 4: completeness, DSAC relaxation |
| `codon_sieve_phase5.py` | `code/` | Phase 5: max-jump constraint |
| `codon_sieve_phase6.py` | `code/` | Phase 6: evolvability + reachability + stops → uniqueness |

Note: CP-SAT scripts (`codon_ortools_*.py`) remain in the sandbox
`research-sandbox/01_genetic_code/code/` as they require the OR-Tools package
which some users may not have installed. Results are summarized in PROVENANCE.md.

---

## Requirements

- Python 3.9+
- `numpy` (any recent)
- `scipy` (for z-score utilities)
- No GPU, no external data downloads needed
- OR-Tools (`pip install ortools`) for CP-SAT scripts only (optional; results documented above)

---

## Standard Code Reference Values

| Criterion | Standard code value | z-score |
|-----------|---------------------|---------|
| Error minimization | 1.684 | $-2.04\sigma$ |
| Prebiotic accessibility | 0.697 | $+1.28\sigma$ |
| Chemical clustering | 0.714 | $+1.56\sigma$ |
| Max-jump | 7.40 | $-4.49\sigma$ (conservative) |
| Historical reachability | 0.714 | — |
| All 3 stops used | Yes | pass |

---

## Variant Code Confirmations

All 17 known variant genetic codes confirmed as local minima of the Phase-5
viability metric. Tested: vertebrate mitochondrial, invertebrate mitochondrial
(multiple lineages), yeast mitochondrial, mold/protozoan, ciliate (Tetrahymena
and Paramecium), Mycoplasma/Spiroplasma, flatworm, Acetabularia (one reassignment
each).

---

## v2.0 Changes (2026-05-08)

### New: Prebiotic Gen/Drain analysis added to §Limitations

**Result:** Minimum prebiotic chemistry enhancement for viability = IPT = 1.1309×

**Code:** `code/prebiotic_gen_drain.py` (new public file)
Rate constants from: Rode 1999 (peptide formation), Orgel 1992 (template ligation)
**Claim grade:** [B] Toy model with real rate constants.
**Citations added:** SpivackIPT, Rode1999, Orgel1992

This result supports the genetic code Stage 2 viability criterion:
the prebiotic network needs IPT enhancement to sustain itself,
and the 20-AA set maximizes Gen/Drain for the first-wave autocatalytic network.
