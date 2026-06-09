# PROVENANCE — P37 — Quantum Mechanics from Rule 110

**Paper:** P37 — "Quantum Mechanics from Rule 110: Hilbert Space, Hamiltonian,
and Born Rule"  
**Date:** 2026-05-20  
**Author:** Nova Spivack  
**Series:** UGP Physics, Paper 37

---

## Derivation Record

### Result 1: f_MDL Hilbert Space — 1-dimensional, E=0 (CatA)

**Source:** Lab notes 77, 80, 82, 85, 158 (2026-05-19/20), Rank 95  
**Script:** `canonical_run/fmdl_hamiltonian_spectrum.py`  
**Method:** Exhaustive forward-orbit decomposition over all 7⁵ = 16,807 states
using the canonical 14-entry Z₇³ f_MDL lookup table.

**Key values (exact):**
- Distinct cycles: 1 (vacuum fixed point)
- Hamiltonian eigenvalues: {E=0} only
- Physical Hilbert space dimension: 1
- SM generation tail lengths: gen₁=3, gen₂=2, gen₃=1
- gen₁ predecessors: 0 (Garden-of-Eden)
- Vacuum predecessors: 14,147

**Dark sector (CatAL):** Z₇⁴ has 3 cycles, dim(H_dark)=5, E=π doublets.  
**Lean file:** `ugp-lean/UgpLean/Universality/GUTStructure.lean §35`  
**Lean theorems (zero sorry):**
- `dark_sector_orbit_structure`
- `dark_sector_period2_exhaustive`
- `dark_sector_vacuum_fixed_point`
- `dark_sector_cycles_are_period2`
- `dark_states_z7_winding_3`

### Result 2: Eigenvalue-Mass Falsification and Two-Role Theorem (CatA, CatAD)

**Source:** Lab notes 159 (2026-05-20), Rank 94  
**Script:** `canonical_run/eigenvalue_mass_correspondence.py`

**Falsification (CatA):**
- T=3 ratio spread: 69.3%
- T=4 ratio spread: 63.0%
- m_μ/m_e discrepancy: 10,238%
- m_τ/m_e discrepancy: 115,807%
- All alternative hypotheses (orbit depth, degeneracy, predecessor count): FAIL

**Positive result (CatA):** Tail-length ordering 3>2>1 matches stability
hierarchy gen₁>gen₂>gen₃.

**Two-Role Theorem (CatAD):** Cogwheel = QM structure; GTE N_eff cascade =
mass content. Derived from Rank 130 (beable superposition formalism).

### Result 3: Z₇ Winding-Class Gauge Derivation (CatAD, CatAL components)

**Source:** Lab notes 161 (2026-05-20), Rank 96  
**Method:** Purely theoretical (no new script); builds on CatAL results from
Rank 99 (`GUTStructure.lean §33`).

**Winding class structure (CatAD):**
- 7 classes of 2,401 states each (exact by Z₇-homomorphism argument)
- SM classes {0,2,3,4,6} = 5 = dim(SU(5) 5̄)
- Missing classes {1,5} = SU(5) X,Y leptoquark mediators

**Gauge derivation (CatAD, CatAL components):**
- U(1)_EM: winding-sector phase freedom; Z₇→Q map CatAL
  (`winding_class_sm_assignment`, GUTStructure.lean §31)
- SU(3)_c: Z₃={1,2,4}⊂Z₇* acting on winding-2 sector; Z₃ arithmetic CatAL
  (`z7_color_subgroup_*`, GUTStructure.lean §33)
- SU(2)_L: {w=3,w=4} doublet; doublet arithmetic CatAL
  (`su2l_charge_assignment_z7_discriminator`, GUTStructure.lean §33)
- U(1)_Y: hypercharge Y=2(Q-T₃) consistent for all SM doublet members CatAL
  (`quark_doublet_hypercharge`, `lepton_doublet_hypercharge`, GUTStructure §49);
  Weinberg angle sin²θ_W = 3/13 certified CatAL
  (`HyperchargeConsistency`, GUTStructure §73, zero sorry)

**Residual gap (CatAD→CatAL):** Lean cert of 't Hooft §9.3 identification
(Rank 201-IGF, future work).

### Result 4: Born Rule (CatAD)

**Source:** 't Hooft (2016) Chapters 4, 7 applied to f_MDL; lab notes 158, 161  
**Method:** Structural — follows from the information-loss regime established
in Result 1.

---

## Citation Chain

This paper (P37) builds on:
- **P28** (`SpivackCompUniversality`): MDL uniqueness of Rule 110; f_MDL
  construction; N_gen=3; Z₅/Z₇ orbit structure
- **P01** (`ugp-p01`): Z₇ winding-number SM charge assignment;
  N_fam=5 identification
- **P36** (`SpivackEmergentGravity`): emergent D=4 from f_MDL; CA-gravity context
- **P31** (`SpivackWeinbergAngle`): sin²θ_W = N_gen/c_H = 3/13 (CatA)
- **P32** (`SpivackCKM`): CKM from GTE orbit arithmetic
- **'t Hooft (2016)** (`tHooft2016CA`): cellular automaton interpretation of QM;
  cogwheel construction; information-loss Born rule; §9.3 gauge conjecture

---

## Confidence Levels

| Result | Confidence | Evidence |
|--------|------------|----------|
| f_MDL Hilbert space: dim=1, E=0 | **CatA** | Exhaustive orbit decomposition |
| SM tail-length stability hierarchy | **CatA** | Exhaustive orbit decomposition |
| Eigenvalue-mass falsification | **CatA** | Quantitative tests, all routes fail |
| Dark sector: dim=5, E=π doublets | **CatAL** | Lean 4, zero sorry |
| Z₇ winding: 7 classes × 2401 states | **CatAD** | Z₇-homomorphism (analytic) |
| Two-Role Theorem | **CatAD** | Structural (Rank 130 beable formalism) |
| U(1)_EM from winding phase | **CatAD** | 't Hooft §9.3; charge map CatAL |
| SU(3)_c from Z₃={1,2,4}⊂Z₇* | **CatAD** | Gauge id; Z₃ arithmetic CatAL |
| SU(2)_L from {w=3,4} doublet | **CatAD** | Gauge id; doublet arithmetic CatAL |
| U(1)_Y hypercharge consistency | **CatAL** | Lean 4, §49+§73, zero sorry |
| Weinberg angle sin²θ_W=3/13 | **CatAL** | HyperchargeConsistency §73 |
| Born rule from information loss | **CatAD** | Structural (follows from CatA orbit) |
| Continuum limit | **CatD** | Open problem |
| Multi-particle Hilbert space | **CatD** | Open problem |

---

## Graduation checklist (2026-05-20 audit)

| Item | Status |
|------|--------|
| `canonical_run/` (3 scripts) | ✅ Graduated |
| `GUTStructure` §§31,33,35,55,73,76 | ⏳ `ugp-lean` → `ugp-lean` |
| REPRODUCE §73/§76 theorem list | ✅ Updated 2026-05-20 |
| Optional JSON outputs from canonical_run | ⏳ At Zenodo |

`REPRODUCE.md`; Handoff 8 § P37.

---

*Provenance document — P37 — UGP Physics — 2026-05-20*

---

## Paper Pass — 2026-05-24

**What changed:**

1. **Abstract** — Added sentence summarizing Lorentz-invariant causal structure results (AFCA causal invariance, Minkowski cone embedding, coordinate surjection).
2. **§AFCA causal invariance** — Added motivating paragraph explaining why causal invariance implies Lorentz-frame independence (derived property, not postulate).
3. **§Special-relativistic time dilation** — Fixed literal "CatAL" text → "full Lean~4 closure of SR awaits".
4. **§Quantitative mass hierarchy** — Fixed literal "CatD" in text → "open problem".
5. **Table (orbit decomposition)** — Renamed column header "Cat." → "Cert."
6. **`canonical_run/`** — Renamed `rank94_eigenvalue_mass.py` → `eigenvalue_mass_correspondence.py` (role-based name).
7. **REPRODUCE.md** — Updated script name reference.

*P37 PROVENANCE.md — 2026-05-24*

---

## Paper Pass — 2026-05-25 (EPIC_073 graduation)

**Ranks:** 070-131, 070-139, 070-140, 070-97, 070-97B, 070-94, 070-95, 76-BORN, 77-2QUANT, 75-DSLIT

| Result | Rank | Script / Lean | Status |
|--------|------|---------------|--------|
| (g−2)_μ one-loop GTE falsification | 070-131 | `g_minus_2_muon_gte_correction.py`; GUTStructure §42 | CatA — not falsified |
| (g−2)_μ two-loop + Fermilab | 070-139 | `g_minus_2_two_loop_gte.py` | CatD neutral |
| Hadronic HVP dispersion | 070-140 | `gte_hvp_dispersion_estimate.py` | CatD neutral |
| Born rule equivalence ('t Hooft vs NEMS P13) | 070-97 | analysis only | CatAD |
| EffectMeasure B1 bridge | 070-97B | `epic073_rank070_97b_thooft_effectmeasure_bridge.py`; `ThooftEffectMeasureBridge.lean` | CatA partial B1 |
| Two-Role Structural Principle | 070-94 | `TwoRoleTheorem.lean` | CatAD (+CatAL partial) |
| f_MDL Hamiltonian spectrum | 070-95 | `canonical_run/fmdl_hamiltonian_spectrum.py`; GUTStructure §35 | CatAL |
| MDL Born rule structural layer | 76-BORN | `BornRuleMDL.lean` | CatAL conditional |
| Fock space kink quantization | 77-2QUANT | `FockSpaceKink.lean` | CatAL |
| Double-slit Born ensemble | 75-DSLIT | `dslit_gte_interference.py` | CatA |

**Graduated:** five scripts → `papers/37_quantum_mechanics/scripts/` (2026-05-25).
