# Genetic Code Sieve — Code

Supporting code for:
*"The Standard Genetic Code as the Unique Survivor of a Two-Stage
Admissibility--Viability Sieve"* (Nova Spivack, 2026)

## Requirements

```bash
pip install numpy scipy
```

## Scripts (run in order)

| Script | Phase | Result |
|--------|-------|--------|
| `codon_sieve.py` | 1 | Wobble admissibility; error score |
| `codon_sieve_phase2.py` | 2 | Prebiotic accessibility |
| `codon_sieve_phase3.py` | 3 | Stop robustness; chemical clustering |
| `codon_sieve_phase4.py` | 4 | Completeness; GTE/DSAC relaxation |
| `codon_sieve_phase5.py` | 5 | Max polar-requirement jump |
| `codon_sieve_phase6.py` | 6 | Uniqueness (evolvability + reachability + stops) |
| `prebiotic_gen_drain.py` | Supp. | Gen/Drain model with published rate constants |
| `per_aa_gen_drain.py` | Supp. | Per-amino-acid competitive fitness model |

## Key Result

```bash
python3 codon_sieve_phase6.py
```

Output: 0/99,998 evolvable complete wobble-admissible codes outperform
the standard genetic code under all eight criteria simultaneously.

The standard genetic code is the unique survivor of:
- Stage 1: Wobble admissibility ($10^{50}$× reduction)
- Stages 2A-2F: Five classical criteria (z = +3.22σ, top 0.009%)
- Stage 2G: Evolvability (max_jump ≥ 6.0)
- Stage 2H: Historical reachability (first-wave AAs in four-fold boxes ≥ 56%)
- Stage 2I: Complete stop coverage (all 3 stop codon identities used)
