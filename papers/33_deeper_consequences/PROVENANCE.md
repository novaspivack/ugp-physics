# PROVENANCE — P33: Deeper Consequences

**Paper:** `papers/33_deeper_consequences/deeper_consequences_paper.tex`  
**Status:** Active development

---

## Pass 1 — Initial publication (2026-05-19)

Paper written and compiled. 31 pages. Covers:
- §2: Electroweak Boson Staircase and Goldstone Mechanism
- §3: MDL Minimality and Matter Dominance
- §4: Causal Orbit Isolation (6-part master theorem, Lean-certified zero sorry)
- §5: The Photon as the Cellular-Automaton Vacuum
- §6: Casimir Structure and Vacuum Sparsity
- §7: Vertex Duality

---

## Pass 2 — Global attractor / single-cycle result (2026-05-19)

**What changed:**

1. **§4 (Causal Orbit Isolation) — global attractor remark added.** New `\begin{remark}[Global attractor, CatA]` inserted after the six-condition master theorem discussion (before §4 Orbit Sum Trajectory Invariance subsection). States: f_MDL on Z₇⁵ has exactly one periodic orbit (vacuum fixed point); every non-vacuum state converges to vacuum in ≤7 steps; tail lengths gen₃=1, gen₂=2, gen₁=3 (GoE), consistent with generation stability hierarchy. CatA, numerical verification over all 16,807 states.

2. **§5 (The Photon as the CA Vacuum) — Physical Interpretation remark extended.** Added sentence at end of remark: global orbit decomposition confirms vacuum is the unique periodic orbit in the f_MDL dynamical system; every other state is a transient converging in ≤7 steps. CatA.

**Compile:** 31 pages, clean (zero overfulls, zero errors).

**Zenodo impact:** No deposit until full paper series ready (P28+P30–P33).

*P33 PROVENANCE.md — 2026-05-19*

---

## Pass 3 — f_MDL perfect code remark (2026-05-19)

**What changed:**

1. **§5 (The Photon as the CA Vacuum) — perfect code remark added.** New `\begin{remark}[$f_{\rm MDL}$ as a perfect code; $\CatAL$]` inserted at the end of §5, after the helicity remark and before §6. States: f_MDL achieves the minimum 14 = 3+10+1 non-zero neighborhoods for orbit admissibility + Turing universality + vacuum transparency; lower bound 14 = 9_orbit + 5_binary from structural disjointness; MDL-minimality forces all free neighborhoods to zero. Cites `fmdl_perfect_code` and `fmdl_nonzero_lower_bound` (GUTStructure §36, CatAL, zero sorry).

**Compile:** Clean (pre-existing \vbox overfull, zero \hbox overfulls, zero errors).

**Zenodo impact:** No deposit until full paper series ready.

*P33 PROVENANCE.md — 2026-05-19*

---

## Pass 4 — Chiral pair Lorentz item in Open Problems (2026-05-19)

**What changed:**

1. **§8 Open Problems — new item 9 added.** Lorentz invariance item: states that the Rule 110 ether has a persistent preferred frame (v_R=2/3, v_L≈1/3), describes the partial resolution via the chiral pair {Rule 110, Rule 124} achieving v_R = |v_L| = 2/3 exactly (CatA; 100% period-3 purity, T=300 steps) at the cost of doubling the CA layers, and notes that a single-rule Lorentz-symmetric realization remains open.

**Compile:** 33 pages, clean (zero hbox overfulls, zero errors).

**Zenodo impact:** No deposit until full paper series ready (P28+P30–P33).

*P33 PROVENANCE.md — 2026-05-19*

---

## Pass 5 — Baryogenesis amplitude structure Lean cert (Rank 209-LCA, 2026-05-20)

**What changed:**

1. **§7.5 (Baryon-to-Photon Ratio)** — amplitude exponent structure upgraded from $\CatD$ to $\CatAL$. CA-to-QFT lift at $f_{\mathrm{MDL}}(2,0,2)=3$: $n_{\rm EW}=1$, $n_{\rm EM}=2$, $\eta_B=|A_B|^2$ with $2n_{\rm EW}=2$, $2n_{\rm EM}=4$. Lean: `eta_B_amplitude_structure`, `baryogenesis_amplitude_counting`, `baryogenesis_amplitude_A_B_structure`, `wplus_vertex_fmdl_emission` (`GUTStructure.lean` §70). $\kappa$ normalization remains $\CatD$.

2. **GoE loop cut** — $N_{\rm fam}-1=4$ upgraded $\CatAD$→$\CatAL$ via `baryogenesis_amplitude_goe_exclusivity`, `baryogenesis_amplitude_goe_loop_count`.

3. **Leptogenesis comparison** — $\eta_B$ line: exponent structure $\CatAL$, $\kappa$ still $\CatD$.

**Compile:** 44 pages, clean.

**Lean:** `ugp-lean/UgpLean/Universality/GUTStructure.lean` §70; zero sorry; one κ axiom.

*P33 PROVENANCE.md — 2026-05-20*

---

## Pass 6–10 — PMNS, §79–§81, script graduation (2026-05-20 audit)

| Pass | Content | Page count |
|------|---------|------------|
| 6 | PMNS block R191–R208 (Z₅ NLO θ₁₂, etc.) | 42+ |
| 7 | §79 orbit-sum winding; §80 orbit-intrinsic 8 neighborhoods | 46 |
| 8 | §81 QCD Vandermonde β₀ = 23/3 | 46 |
| 9 | `scripts/leptoquark_vertex_catalog.py` graduated | 46 |
| 10 | Reproducibility audit: sandbox paths removed from `scripts/` (2026-05-24) | 46 |

### Computational artifacts (graduated 2026-05-20)

| Script | Location |
|--------|----------|
| `leptoquark_su5_windings.py` | `scripts/` ✅ |
| `leptoquark_vertex_catalog.py` | `scripts/` ✅ |
| `casimir_anti_enhancement.py` | `scripts/` ✅ |
| `ca_vertex_table.py` | `scripts/` ✅ |
| `photon_vacuum_casimir_analysis.py` | `scripts/` ✅ |
| `mdl_cp_uniqueness.py` | `scripts/` ✅ |
| `z7_vertex_catalog.py` | `scripts/` ✅ |
| `w_boson_self_energy.py` | `scripts/` ✅ |
| `pmns_cp_phase.py` | `scripts/` ✅ |
| `pmns_z5_correction.py` | `scripts/` ✅ |
| `cp_observables.py` | `scripts/` ✅ |
| `epsilon_k_tension.py` | `scripts/` ✅ |
| `fmdl3d_chirality.py` | `scripts/` ✅ |

### JSON artifacts in `data/`

| File | Source |
|------|--------|
| `casimir_anti_enhancement_results.json` | P28 canonical_run ✅ |
| `photon_vacuum_casimir_results.json` | P28 canonical_run ✅ |
| `w_boson_self_energy_results.json` | sandbox ✅ |
| `fmdl3d_chirality_results.json` | P28 canonical_run ✅ |

**Open quantitative gap (audit):** η_B +7.2% vs Planck — labeled CatD in body; no script change.

**Zenodo:** `ugp-physics-p33-deeper-consequences` — new version after graduation + Nova approval.

*P33 PROVENANCE.md — reproducibility audit 2026-05-20*

---

## Paper Pass — 2026-05-24

**What changed:**

1. **§Tree-Level Lepton Decay Rates** — Added full derivation chain: tree-level vertex catalog → $V\!-\!A$ weak width formula → partial width. Moved the +12.2%/+12.5% numbers after the derivation setup.
2. **§CP observables** — Added Table~\ref{tab:cp_observables} comparing sin(2β), |εK|, and γ to PDG with explicit error bars.
3. **§What this paper does not claim** — Fixed literal "CatA/D" → "analytically derived".
4. **Script renaming** — All rank-prefixed scripts renamed to role-based names: `rank283_cpo_cp_observables.py` → `cp_observables.py`, `rank284_ekt_epsilon_k_tension.py` → `epsilon_k_tension.py`, `rank140_z7_vertex_catalog.py` → `z7_vertex_catalog.py`, `rank157_dyson_self_energy.py` → `w_boson_self_energy.py`, `rank196_leptoquark.py` → `leptoquark_su5_windings.py`, `rank199_leptoquark_vertices.py` → `leptoquark_vertex_catalog.py`, `rank202_cp_phase.py` → `pmns_cp_phase.py`, `rank208_z5_correction.py` → `pmns_z5_correction.py`, `ranks_46_50_casimir_items.py` → `casimir_anti_enhancement.py`.
5. **All script references in body text and appendix** — Updated to role-based names.

*P33 PROVENANCE.md — 2026-05-24*
