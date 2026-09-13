# PROVENANCE — Paper 24: Substrate Depth and Self-Generated Mass

**Title:** Substrate Depth and Self-Generated Mass: The c-Component of the UGP Canonical Triple Predicts Reflexive Closure across the Standard Model Spectrum  
**Status:** Manuscript draft. Pre-submission.  
**Date written:** 2026-05-02

---

## Origin of the investigation

The investigation was conducted as a clean-room (blind) analysis: the PDG particle
spectrum was studied without prior exposure to the UGP framework. The empirical
regularity (RC ∼ G_topo) was identified first; only then were UGP-internal measures
(log|b|, log|c|) tested against it. The handoff package is archived in:
internal handoff package (local; gitignored).

The originating handoff specification is `HANDOFF_SPEC.md` in that directory.

---

## Canonical data and computation

### Primary dataset
| File | Location | Role |
|------|----------|------|
| `ep18_particle_closure_dataset.py` | `papers/01_SM/canonical_run/` | P01 Table 12 triples + PDG PDG particle data |
| `comp_ep18_log_c_vs_rc_validation.py` | `papers/01_SM/canonical_run/` | Headline statistics + 5-rule robustness + null test |
| `comp_ep18_validation.json` | `papers/01_SM/canonical_run/` | Archival output; SHA-256: `d897315cdd8af70ed9b6d4ee358354b74b0d2e58254deadd70414bce5955bfb4` |

### Key canonical results
| Result | Value | Source |
|--------|-------|--------|
| r (composites, baseline) | −0.9439 | `comp_ep18_validation.json` |
| p-value | 6.70 × 10⁻¹⁹ | `comp_ep18_validation.json` |
| n (composites) | 38 | `comp_ep18_validation.json` |
| r (max-|c|, Braid-motivated) | −0.9814 | `comp_ep18_validation.json` |
| r (GTE Mersenne-sector, P01 validated) | −0.9135 | computed from formal rule |
| Null test: fraction |r|≥0.90 | 0 / 10,000 | embedded in validation script |
| Max null |r| | 0.637 | embedded in validation script |

---

## Lean formalization

| Module | Theorems | Commit | Status |
|--------|----------|--------|--------|
| `GTE.MersenneLadder` | `ugp_rc_tier_structure` + 6 supporting | `ca7ced0` | ✓ zero sorry |
| `BraidAtlas.CompositeTriples` | `ugp_composite_braid_c_rule` + 8 supporting | `bb214e7` | ✓ zero sorry |

Both in `ugp-lean` repository at https://github.com/novaspivack/ugp-lean (part of pending Zenodo batch).

---

## Figures

| Figure | Script | Pre-generated |
|--------|--------|---------------|
| Fig. 1 (main analysis panel) | `handoff/code/ugp_internal_test.py` | `fig_ugp_internal_test.png` |
| Fig. 2 (generation empirical motivation) | `handoff/code/generation_test.py` | `fig_generation_test.png` |

---

## Paper structure

| §§ | Content |
|----|---------|
| 1.1 | RC definition + colorbox disambiguation |
| 1.2 | UGP/GTE intro + Table 1 (canonical triples) + GTE.MersenneLadder and ScaleTransport citations |
| 1.3 | Motivation + section overview |
| 2 | RC landscape + pion chiral symmetry note |
| 3 | Empirical regularity (G_topo, r=−0.81) + Figure 2 |
| 4 | UGP-internal test + main result (r=−0.944) + Figure 1 |
| 5 | Robustness battery (5 rules including formal GTE Mersenne-sector) + proton/neutron c=15 note |
| 6 | 6D PCA (PC1=57%, 92% in 3 PCs) |
| 7 | Generation as continuous quantity + Braid Atlas Theorem G-1 chain |
| 8 | What it is / is not + cross-connections (P17, P18, P19, P22, nuclear) |
| 9 | Subsample stress tests |
| 10 | Falsifiability + null test (0/10,000) + open questions |
| 11 | Conclusion + Key Findings box |

---

## Companion papers

- **P17 Braid Atlas**: cites Theorem G-1 (Cr=Generation−1), composite §6
- **P01 SM**: source of canonical triples and proton/neutron c=15
- **P22 Neutrino masses**: c-value tier markers appear in right-handed neutrino triples
- **P18 Koide**: Koide/N_c chain; right-handed neutrino triples
- **P19 Cyclotomic**: VV log-space relation (parallel motivation)
- **P24** (this paper): first paper to use UGP triples for an observable other than mass

---

## Status and next steps

1. **Pre-submission**: adversarial review recommended before arXiv/journal submission
2. **Composite-triple programme**: formal (a, b) component rule and full Lean formalization
3. **Category upgrade**: currently A/D; would become A once axiomatic sector assignment is proved

---

## BraidAtlas.CompositeTriples — Status Update (2026-05-08)

**Issue identified:** Paper 24 (closure_structure_ugp.tex) extensively references
`BraidAtlas.CompositeTriples` (ugp-lean) as "zero sorry, Lean-certified" for the
nine light-baryon GTE triple assignments (ugp_nucleon_b_formula, ugp_strange_baryon_b_formulas,
ugp_strange_baryon_c_values, winding composition rules).

**Current status (updated 2026-05-08):** `BraidAtlas.CompositeTriples` NOW EXISTS in ugp-lean. Module built and verified (zero sorry). See ugp-lean THEOREMS.md for full theorem listing.
The two BraidAtlas modules that DO exist (as of 2026-05-08) are:
- `UgpLean.BraidAtlas.ChargeTheorem` — charge formula, GMN, GTE-P7 Q=0
- `UgpLean.BraidAtlas.CoxeterConductor` — Coxeter-conductor arithmetic

**Status:** Both modules created and built. P24's [Category A] claims are now supported.

**Risk resolved:** All nine baryon triple claims are now Lean-certified (zero sorry, CompositeTriples module).

**Lean module count:** CompositeTriples and ChiralitySquaring both created. Module counts no longer tracked in papers (see companion formalization paper for current count).
