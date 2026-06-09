# Reproduction Instructions — P49: MDL Selects the Wolfram Rule

This document describes how to reproduce every figure, computation, and
Lean-certification result in the paper.

---

## 1. Overview

The paper studies the GTE polynomial p(L,C,R) = C+R−CR−LCR (mod 7) as a
standalone k=7 Wolfram cellular automaton. The scripts in `scripts/` generate
all figures and verify key numerical claims. The Lean modules in `ugp-lean`
certify the central algebraic theorems.

---

## Code Navigation

### Which file to use

**Use the Python scripts for:** all figure generation, spacetime diagrams, invariant subset classification, polynomial analysis, and large-scale glider/orbit scans. No Wolfram Engine required for Python scripts.

**Use `wolfram_model_causal_graph.wl` for:** the §5 WolframModel causal graph figure and §7 orbit ring diagram (alternative to `gen_orbit_ring_visualization.py`).

**Use `three_tape_wolframmodel_v2.wl` for:** the three-tape DPP causal structure demonstration (§8 figures); DPP synchronization via GlobalSpacelike.

**Do not use `three_tape_wolfram_model.wl` for new work** — it is a historical first attempt with an integer node aliasing bug; superseded by v2.

### Script roles (P49)

| Script | Role |
|--------|------|
| `wolfram_model_causal_graph.wl` | Single-tape GEN orbit causal graph (§5) + orbit ring diagram (§7) |
| `three_tape_wolframmodel_v2.wl` | Three-tape orbit causal graph with DPP synchronization (§8) |
| `three_tape_wolfram_model.wl` | Historical v1 (superseded; integer node aliasing bug) |
| `invariant_subset_classifier.py` | Exhaustive invariant subset classification (Theorem 4.2) |
| `spacetime_diagram_generator.py` | Z₇ spacetime diagrams with perturbation (Fig 1) |
| `ppoly_fmdl_contrast.py` | f_MDL vs p_poly contrast figures (Fig 2) |
| `gen_orbit_ring_visualization.py` | Orbit ring diagram via matplotlib (Fig 3; no Wolfram needed) |
| `three_tape_dpp_visualization.py` | Three-tape DPP architecture figures (Fig 5) |
| `bulk_causal_graph.py` | Bulk causal graph with cross-tape edges (Fig 6) |
| `z7_sector_dynamics.py` | Z₇ sector color comparison and scattering (Fig 7) |
| `glider_search_taichi.py` | Large-scale glider search (requires Taichi 1.7.3) |
| `orbit_visitation_rate.py` | SM orbit visitation rate (requires Taichi 1.7.3) |

### Related code in other papers

| File | Paper | Description |
|------|-------|-------------|
| `papers/45_three_tape_cmca/scripts/ThreeTapeCMCA.wl` | P45 | Full three-layer CMCA cell-level simulator; single-bit inner clock; SR dilation and 9 verifications |
| `papers/45_three_tape_cmca/scripts/three_tape_cmca.py` | P45 | Python three-tape CMCA (gravity, Bell, soliton); cell-level dynamics |
| `papers/41_three_layer_chiral_minkowski_ca/scripts/cmca_full_reproducibility_wolfram_version.wl` | P41 | Single-tape CMCA with M=7 inner clock; complete P41 9-claim reproducibility suite |

---

## 2. Dependencies

### 2.1 Python 3.10+

```bash
pip install numpy matplotlib networkx scipy
```

All Python scripts are self-contained and write figures to `scripts/figures/`
relative to their own location.

### 2.2 Taichi 1.7.3 (for glider search and orbit visitation scripts only)

```bash
pip install "taichi==1.7.3"
```

Taichi provides parallelised CA kernels (CPU or GPU backend). Tested on
Taichi 1.7.3 with the CPU and Metal (macOS arm64) backends. The two scripts
that require Taichi are `glider_search_taichi.py` and `orbit_visitation_rate.py`.
All other scripts work without Taichi.

**Critical constraint:** Do NOT add `from __future__ import annotations` to any
file that imports Taichi. That import defers type-annotation evaluation, which
breaks Taichi's kernel argument type inspection at import time.

Expected runtimes with Taichi (CPU backend):
- `glider_search_taichi.py` small run (L=200, T=100): ~30 s
- `glider_search_taichi.py` large run (L=10 000, T=2 000): 5–10 min
- `orbit_visitation_rate.py` (L=10 000, T=2 000): ~5 min

Both scripts include a 300-second wall-clock timeout (`TIMEOUT_SECONDS`).

### 2.3 Wolfram Engine 14.3.0 (for `.wl` scripts only)

Free download: https://www.wolfram.com/engine/

Install the SetReplace paclet (required by both `.wl` scripts):

```bash
wolframscript -code 'PacletInstall["SetReplace"]'
```

Tested versions: Wolfram Engine 14.3.0, SetReplace v0.3.196. Load via
`Needs["SetReplace\`"]` (local paclet), NOT `ResourceFunction["WolframModel"]`.

### 2.4 Lean 4 (for certification verification only)

```bash
elan install leanprover/lean4:stable
```

See §5 for module paths and build commands.

---

## 3. Script Inventory

All scripts write output to `scripts/figures/` relative to their own location.
Run from the `scripts/` directory:

```bash
cd papers/49_gte_polynomial_wolfram/scripts
```

| Script | What it produces | Paper section | Requires Taichi? |
|--------|-----------------|---------------|-----------------|
| `invariant_subset_classifier.py` | Printed table: all 127 non-empty subsets of Z₇, invariant subset classification | §4 (Theorem 4.2) | No |
| `spacetime_diagram_generator.py` | `p49_gte_spacetime_perturbed_v2.png`, `p49_gte_ether_only_v2.png` | §6 | No |
| `ppoly_fmdl_contrast.py` | `p49_gen1_fmdl_vs_ppoly.png`, `p49_ether_fmdl_vs_ppoly.png`, `p49_fmdl_vs_ppoly_table.png` | §2, §8 | No |
| `gen_orbit_ring_visualization.py` | `p49_gte_orbit_rings_v2.png` | §7 | No |
| `wolfram_model_causal_graph.wl` | `p49_gte_causal_g10.png`, `p49_gte_final_state_g10.png`, `p49_gte_orbit_rings_v2.png` (alt) | §5, §7 | No (Wolfram) |
| `z7_sector_dynamics.py` | `p49_z7_color_comparison.png`, plus glider search and scattering spacetime diagrams | §6 | No |
| `three_tape_dpp_visualization.py` | `p49_three_tape_dpp_v3.png`, `p49_three_tape_orbit_3d.png`, `p49_dpp_clock_diagram.png`, `p49_three_tape_causal_layered.png`, `p49_paper_fig2_combined.png` | §8 | No |
| `bulk_causal_graph.py` | `p49_bulk_causal_3d.png`, `p49_causal_comparison.png`, `p49_bulk_causal_cross_tape.png`, `p49_bulk_causal_slices.png` | §8 | No |
| `glider_search_taichi.py` | `p49_z7_excitation_panel.png`, `p49_z7_cone_fill.png`, per-sector excitation PNGs, `p49_z7_cone_fill_large.png` | §6 supplemental | **Yes** |
| `orbit_visitation_rate.py` | `p49_orbit_visitation_rates.png` | §6 supplemental | **Yes** |
| `three_tape_wolfram_model.wl` | Causal graph PNGs for three-tape encoding | §8 supplemental | No (Wolfram) |

---

## 4. Reproducing Each Figure

### Theorem 4.2 verification — exhaustive invariant subset classification

Verifies computationally that exactly three non-empty subsets of Z₇ are closed
under p: the vacuum singleton {0}, the binary sublayer {0,1} (= Rule 110), and
the full space Z₇.

```bash
python3 invariant_subset_classifier.py
```

Expected output: `PASS: Exactly 3 invariant subsets confirmed: {0}, {0,1}, Z₇`.
Runtime: < 1 ms. No figure produced — pure printed verification.

---

### Figure 1 — Z₇ spacetime diagrams (§6)

56-cell ether tape with a single Z₇=3 injection at center (Fig 1a) and the
unperturbed ether baseline (Fig 1b).

```bash
python3 spacetime_diagram_generator.py
```

Produces:
- `figures/p49_gte_spacetime_perturbed_v2.png` — causal cone diagram
- `figures/p49_gte_ether_only_v2.png` — unperturbed ether baseline

Runtime: ~2 s.

---

### Figure 2 — f_MDL vs p_poly contrast (§2)

Three panels: GEN₁ ring evolution under the two rules, ether + injection
response comparison, and lookup table sparsity (343-cell grid).

```bash
python3 ppoly_fmdl_contrast.py
```

Produces:
- `figures/p49_gen1_fmdl_vs_ppoly.png`
- `figures/p49_ether_fmdl_vs_ppoly.png`
- `figures/p49_fmdl_vs_ppoly_table.png`

Runtime: ~5 s.

---

### Figure 3 — GEN orbit ring diagram (§7)

Four-state orbit ring: GEN₁=[1,5,2,2,1] → GEN₂=[2,5,2,0,2] → GEN₃=[5,6,5,3,5]
→ VAC=[0,0,0,0,0] under f_MDL on a 5-cell periodic ring.

**Python version (no Wolfram Engine required):**
```bash
python3 gen_orbit_ring_visualization.py
```
Produces `figures/p49_gte_orbit_rings_v2.png`. Runtime: ~2 s.

**Wolfram version (requires Wolfram Engine + SetReplace):**
```bash
wolframscript -file wolfram_model_causal_graph.wl
```
Also produces `figures/p49_gte_orbit_rings_v2.png` (overwritten if Python
version was run first).

---

### Figure 4 — WolframModel causal graph (§5.3)

Causal graph of the ruleGTE WolframModel at 10 generations (1023 events, binary tree).
There are two independent ways to produce this figure:

**Method A — Canonical WolframScript (requires Wolfram Engine + SetReplace):**
```bash
wolframscript -file gte_rulegte_causal_graph.wl
```
Produces:
- `figures/p49_gte_causal_g10.png` — tree-layout causal graph
- `figures/p49_gte_causal_g10_wolfram_radial.png` — radial embedding
- `figures/p49_gte_rulegte_final_state.png` — final hypergraph state (2048 hyperedges)

**Method B — Python fallback (no Wolfram Engine required):**
```bash
python3 gte_wolframmodel_causal_graph.py
```
Produces:
- `figures/p49_gte_causal_g10_python.png` — Python-generated causal graph
- `figures/p49_gte_causal_g10.png` — canonical figure (same data)

**Topology analysis (§5.3 GEN₂/GEN₃ degeneracy):**
```bash
python3 gte_causal_graph_corrected.py
```
Produces:
- `figures/p49_gte_causal_topology_analysis.png` — GEN₂/GEN₃ topology diagram
- `figures/p49_gte_causal_graph_comparison.png` — deterministic vs. multiway comparison
- `figures/p49_gte_causal_g10_deterministic.png` — deterministic (linear) causal chain

**Legacy script (do not use for new figures):**
`wolfram_model_causal_graph.wl` — uses single-brace orbit rules (produces 0 events
with WolframModel v0.3 syntax; shown as deterministic linear chain only).

---

### Figure 5 — Three-tape DPP visualization suite (§8)

Five panels covering the three-tape DPP architecture: 3D orbit ring, clock
coupling diagram, causal layered graph, and combined headline figure.

```bash
python3 three_tape_dpp_visualization.py
```

Produces:
- `figures/p49_three_tape_dpp_v3.png`
- `figures/p49_three_tape_orbit_3d.png`
- `figures/p49_dpp_clock_diagram.png`
- `figures/p49_three_tape_causal_layered.png`
- `figures/p49_paper_fig2_combined.png`

Runtime: ~10 s.

---

### Figures 6a, 6b — Bulk causal graph (§8)

Combined three-tape DPP bulk causal graph with 135 within-tape and 90
cross-tape (gravitational) edges; side-by-side comparison of the coupled
bulk versus three independent causal trees.

```bash
python3 bulk_causal_graph.py
```

Produces:
- `figures/p49_bulk_causal_3d.png` — full 3D causal graph
- `figures/p49_causal_comparison.png` — coupled vs. independent comparison
- `figures/p49_bulk_causal_cross_tape.png` — cross-tape edges only
- `figures/p49_bulk_causal_slices.png` — time-slice causal structure

Runtime: ~20 s.

---

### Figures — Botanical L-system comparison (§5.4)

L-system renderings comparing the GTE causal graph structure to Apiaceae compound
umbel models. Requires only Python (no Wolfram Engine).

```bash
python3 botanical_causal_graph_analysis.py
```

Produces:
- `figures/botanical_lsystem_comparison.png` — GTE L-system vs four Apiaceae models side-by-side
- `figures/botanical_best_match.png` — side-by-side GTE vs Daucus carota best match
- `figures/botanical_metrics_comparison.png` — metric comparison table visualization

Runtime: ~5 s.

---

### Figure 7 — Z₇ sector color comparison (§6)

Five-sector side-by-side spacetime comparison (injection values Z₇=2 through 6)
into the ether background. Also runs the glider search (Experiment A) and
two-particle Z₇ winding scattering experiments (Experiment B).

```bash
python3 z7_sector_dynamics.py
```

Produces:
- `figures/p49_z7_color_comparison.png`
- Scattering spacetime diagrams (`p49_z7_scattering_*.png`)
- Glider search spacetime diagrams (`p49_z7_glider_search_v*.png`)

Runtime: ~60 s (glider search at L=200, T=500).

---

### Supplemental — Ether-excluded glider search (§6, requires Taichi)

Large-scale parallel glider search using excitation fields to eliminate ether
autocorrelation. Tests sector-dependence by pairwise Hamming fractions.

```bash
pip install "taichi==1.7.3"
python3 glider_search_taichi.py
```

Produces:
- `figures/p49_z7_excitation_panel.png` — side-by-side excitation spacetimes
- `figures/p49_z7_cone_fill.png` — cone fill fraction (small run)
- `figures/p49_z7_cone_fill_large.png` — cone fill fraction (large run, L=10 000)
- `figures/p49_z7_excitation_w*.png` — per-window excitation diagrams

Runtime: 30 s – 10 min depending on run size and backend.

---

### Supplemental — SM orbit visitation rate (§6, requires Taichi)

Measures what fraction of triples encountered during chaotic Z₇ evolution
match the 10 SM orbit neighborhoods of f_MDL.

```bash
python3 orbit_visitation_rate.py
```

Produces `figures/p49_orbit_visitation_rates.png`. Runtime: ~5 min (CPU).

---

### Supplemental — Three-tape WolframModel encoding (requires Wolfram Engine)

Encodes the three-tape GEN orbit product as a SetReplace hyperedge rewriting
system and generates the WolframModel causal graph.

```bash
wolframscript -file three_tape_wolfram_model.wl
```

---

## 5. Lean Verification

The central algebraic claims are machine-certified in `ugp-lean` (zero sorry).

Clone the repo and build individual modules:

```bash
git clone https://github.com/novaspivack/ugp-lean.git
cd ugp-lean
lake build UgpLean.Universality.Z7InvariantSubsets
lake build UgpLean.Universality.CUP3DUniqueness
lake build UgpLean.Universality.MDLDerivabilityCriterion
lake build UgpLean.Universality.PhiMDLUniversality
lake build UgpLean.Gravity.RelationalTime
```

A clean build exits 0 with zero `sorry` on all cited theorems.

Key theorems:
- `rule110_z7_poly_rep` (PhiMDLUniversality): p mod 7 restricted to {0,1}³ = Rule 110
- `p_poly_invariant_subsets_classification` (Z7InvariantSubsets): exactly 3 invariant subsets
- `nfam_qnr_explains_binary_floor` (Z7InvariantSubsets): QNR Binary Floor theorem
- `fmdl_z7_three_generation_orbit` (CUP3DUniqueness): GEN₁→GEN₂→GEN₃→VAC orbit
- `t96_02_mdl_selection_theorem` (MDLDerivabilityCriterion): MDL + PSC uniqueness of p
- `dimensional_protocol_principle_master` (RelationalTime): DPP theorem (shared clock → 3+1D)

---

## 6. Paper Compilation

```bash
cd papers/49_gte_polynomial_wolfram/
pdflatex gte_polynomial_wolfram.tex
bibtex gte_polynomial_wolfram
pdflatex gte_polynomial_wolfram.tex
pdflatex gte_polynomial_wolfram.tex
```

Figures are loaded from `scripts/figures/`. Ensure the Python scripts (§4)
have been run first to generate all required PNGs.
