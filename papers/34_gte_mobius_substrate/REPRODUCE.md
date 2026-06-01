# REPRODUCE — P34 GTE-Möbius Architecture

**Paper:** The GTE-Möbius Architecture: Arithmetic Unification of Computation and Transputation in the Universal Generative Principle  
**Status:** Draft — reproducibility paths below match the current PDF (~28 pages)

---

## Compiling the PDF

```bash
cd papers/34_gte_mobius_substrate
pdflatex gte_mobius_substrate_paper.tex
bibtex gte_mobius_substrate_paper
pdflatex gte_mobius_substrate_paper.tex
pdflatex gte_mobius_substrate_paper.tex
```

Bibliography: `../bib/Spivack_Papers_Bibliography.bib`.

---

## Lean 4 certification

**Current location:** `ugp-lean` (graduate to `ugp-lean` before public Zenodo).

```bash
cd /path/to/ugp-lean
lake build UgpLean.Framework.GTEFrameworkInstance
lake build UgpLean.Universality.GUTStructure
lake build UgpLean.Universality.LawvereZone
lake build UgpLean.Universality.GTEComputability
```

| Module | Commit (when pinned) | Key theorems |
|--------|----------------------|--------------|
| `GTEFrameworkInstance.lean` | `41a1461` | `gte_tpc_from_nems_classification`, `gte_tpc_real`, bridge axiom `gte_partrec_eval_iff_fmdl_phi` |
| `GUTStructure.lean` §62 | — | TPC power class (13 theorems) |
| `GUTStructure.lean` §67 | — | `C3TPCCompleteness` |
| `LawvereZone.lean` | — | C4 Lawvere–physical correspondence |
| `GUTStructure.lean` §64–§65 | — | D-uniqueness / optimality |
| `GTEFinalCoalgebra.lean` | `5f5df60` | C1 Theorem: `c1_final_coalgebra_derived`, `c1_lambek_isomorphism` (zero sorry, zero axiom) |
| `GTEOptimalityInstance.lean` | `5f5df60` | `GTECompatibleSpace.orbit_admissible`, `GTEPSCSubstrate.oa_proof` (zero sorry) |
| `LiftingTheorem.lean` | `89cbef3` | `algebraic_lifting_theorem`, physical-scale corollaries (zero sorry) |
| `SpatiallyExtendedLifting.lean` | `9078a1b` | `spatially_extended_composite_lifting`, `meson_bound_state_exists`, `causal_path_exists` (theorem, forward-causal pairs) |
| `AlgebraicDescentTheorem.lean` | — | `algebraic_descent_theorem`, `casimirs_m_independent` (zero sorry) |
| `GeodesicTheorem.lean` | `544df1b` | `gte_equivalence_principle`; `d2_orbit_closed_iter`; `causal_sequence_exists`; `geodesic_preferred_direction` (CatAL) |
| `CentroidMeasure.lean` | `544df1b` | `beableCentroid`; `centroid_well_defined`; `beableCentroid_point` (point-localization model) |
| `QECStabilizer.lean` | `1594970` | `qec_gte_is_stabilizer_code` (four-part bundle, zero sorry); `qec_orbit_closure`; `qec_dweight_projector`; `qec_error_detected`; `qec_mass_gap_error_energy` |

**Planned:** `ugp-lean/UgpLean/GTE_Substrate.lean` — not yet in repo.

---

## Python scripts (cross-reference)

| Script | Location | What it reproduces |
|--------|----------|-------------------|
| `particle_size_bounds.py` | `papers/36_emergent_gravity/scripts/` | Planck-scale compositeness bounds (§Particle Compositeness) |
| `mdl_uniqueness_score.py` | `papers/34_gte_mobius_substrate/scripts/` | MDL three-layer uniqueness score (96-MDLUNIQ) |
| `mdl_l1_potential_closure.py` | `papers/34_gte_mobius_substrate/scripts/` | L1 potential MDL closure |
| `z7_fca_phase_check.py` | `papers/34_gte_mobius_substrate/scripts/` | Z₇-consistent FCA phase structure |
| `fmdl_wolfram_category.py` | `papers/28_computational_universality/scripts/` | f_MDL Category IV classification (shared with P28/P35) |

### Running P34 numerical scripts

```bash
cd papers/34_gte_mobius_substrate/scripts
python3 mdl_uniqueness_score.py          # MDL score; Z₇ vs competitors
python3 mdl_l1_potential_closure.py      # L1 potential form closure
python3 z7_fca_phase_check.py            # M=5 binary does not realize Z₇
```

Expected: f_MDL selected as MDL-minimal Category IV Z₇ CA; Z₇ phase consistency confirmed.

Pass criteria: MDL score minimal for f_MDL among admitted competitors; phase-check nulls pass as documented in lab notes.

Frozen JSON: co-located in `scripts/` (`rank96_mdl_score_results.json`, etc.).

---

## C1 Final Coalgebra — Lean 4 Certification

**Repo:** https://github.com/novaspivack/ugp-lean (`ugp-lean` branch, graduate to `ugp-lean`)
**File:** `UgpLean/Framework/GTEFinalCoalgebra.lean`
**Commit:** `5f5df60`
**Status:** Zero sorry, zero axiom (CatAL)
**Key theorems:** `psc_optimal_zero_on_free`, `GTEReflexiveSpace`, `optimal_unique_up_to_iso`,
`c1_final_coalgebra_derived`, `c1_final_coalgebra`, `c1_lambek_isomorphism`

**Supporting modules (same commit):**
- `UgpLean/Framework/GTEOptimalityInstance.lean` — `GTECompatibleSpace.orbit_admissible`, `GTEPSCSubstrate.oa_proof`
- `NemS.Category.PSCSys` (commit `a3c80f3`, `nems-lean`) — orbit-admissible field + `oa_proof`
- `NemS.Category.FPSC` (commit `a3c80f3`) — F_PSC = identity on PSCSys

To verify:
```bash
git clone https://github.com/novaspivack/ugp-lean
cd ugp-lean
git checkout 5f5df60
lake build UgpLean.Framework.GTEFinalCoalgebra
```

**External:** NEMS `transputation_classification` via `nems-lean`; Cook conditional via `rule110-lean` (see P30 REPRODUCE).

---

## Python / JSON artifacts

No canonical numerical scripts are required for the current PDF. When epic_071 SRRG checks land, graduate scripts to `papers/34_gte_mobius_substrate/scripts/` and record SHA-256 here.

---

## QEC Stabilizer Code (38-QEC)

**Module:** `UgpLean/Spacetime/QECStabilizer.lean`  
**Commit:** `1594970`  
**Theorem:** `qec_gte_is_stabilizer_code` (CatAL, zero sorry)  
**Supporting:** `qec_orbit_closure`, `qec_dweight_projector`, `qec_error_detected`,
`qec_generation_mass_advance`, `qec_mass_gap_error_energy` — all CatAL.

No computational scripts — pure Lean formalization of the `DWeight` function as a
quantum error correcting code projector.

To verify (after graduation to `ugp-lean`):
```bash
cd /path/to/ugp-lean
lake build UgpLean.Spacetime.QECStabilizer
```

---

## Graduation checklist (full reproducibility)

| Item | Status | Target |
|------|--------|--------|
| `GTEFrameworkInstance.lean` | ⏳ `ugp-lean` | `ugp-lean` + formalization paper Round 4b |
| `GUTStructure` §62, §64–§67 | ⏳ exp | `ugp-lean` |
| `LawvereZone.lean` | ⏳ exp | `ugp-lean` |
| `GTEFinalCoalgebra.lean` | ✅ `ugp-lean` commit `5f5df60` | Graduate to `ugp-lean` |
| `LiftingTheorem.lean` | ✅ commit `89cbef3` | `ugp-lean/UgpLean/Spacetime/` |
| `SpatiallyExtendedLifting.lean` | ✅ commit `a38d804` | `ugp-lean/UgpLean/Spacetime/` |
| `AlgebraicDescentTheorem.lean` | ✅ | `ugp-lean/UgpLean/Universality/` |
| `GeodesicTheorem.lean` | ✅ commit `544df1b` | `ugp-lean/UgpLean/Spacetime/` (pending graduation from dev branch) |
| `CentroidMeasure.lean` | ✅ commit `544df1b` | `ugp-lean/UgpLean/Spacetime/` (pending graduation from dev branch) |
| `QECStabilizer.lean` | ✅ commit `1594970` | `ugp-lean/UgpLean/Spacetime/` (pending graduation from dev branch) |
| `OrbitMassHierarchy.lean` §7 | ✅ commit `d7e1b87` | SCC: `mphi_equals_tau_mass_scc`, `mkink_from_scc`, `fpi_from_scc`, `leptonic_sector_heaviest_gen3` — zero sorry, zero custom axioms |
| `DWeightSRFormula.lean` | ✅ commits `74f2294`, `28dce40f` (ugp-lean-exp) | [D]-weighted SR formula: `dmdl_qec_sr_bundle`, `dmdl_dweight_sr_formula`, `dmdl_proper_time_ratio`, `dmdl_dweight_positive` — zero sorry, standard axioms only |
| `GTE_Substrate.lean` | ⏳ Planned | `ugp-lean/GTE/` |
| Lean cert table `gte_tpc_real` row | ⏳ PLANNED | R236-FLP.5 |
| REPRODUCE / PROVENANCE | ✅ This file | — |
| `.tex` repo paths unified | ⏳ | All `ugp-lean` after graduation |
| Zenodo | ⏳ | After P00 cross-ref + Nova approval |

Handoff 8 § P34; `SPEC_236_GTF_GTE_NEMS_FRAMEWORK_INSTANCE.md`.

---

*REPRODUCE.md — P34 — 2026-05-20*

---

## Paper pass update — 2026-05-24

- Macro definitions changed: `\catAL` etc. now render as abbreviated scientific notation.
- Motivation paragraphs added for Φ_MDL realization and Algebraic Lifting Theorem sections.
- Claim-strength taxonomy box added.

---

## EPIC_073 scripts (graduated 2026-05-25)

```bash
cd papers/34_gte_mobius_substrate/scripts
python3 epic073_rank281_3dh_3d_hamiltonian_spec.py    # 281-3DH: H_3D spec, Approach A partial
python3 epic073_rank281_3dh_b_so3_emergence.py        # 281-3DH-B: lattice SO(3) no-go + continuum emergence
```

| Script | Rank | Expected headline |
|--------|------|-------------------|
| `epic073_rank281_3dh_3d_hamiltonian_spec.py` | 281-3DH | L=2: 32 cycles; axis gen1→gen2 PASS; cubic rotation equivariance PASS |
| `epic073_rank281_3dh_b_so3_emergence.py` | 281-3DH-B | Power-law n=2.0001 anisotropy; unified Wilson π²/(3M²) |

**Lean (zero sorry):** `Substrate/PSCPILorentzMain.lean`, `Substrate/NoetherAngularMomentum.lean`.

*REPRODUCE.md — P34 — EPIC_073 pass 2026-05-25*
