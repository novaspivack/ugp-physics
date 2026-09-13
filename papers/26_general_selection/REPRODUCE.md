# Reproduction Guide — General Selection Theory Paper (P26)

Reproduces all main results in:
*"A General Theory of Selection: The UGP Framework Across Domains"*

---

## Requirements

```bash
pip install numpy scipy matplotlib
```

---

## P26-local computation scripts

These scripts live directly in `papers/26_general_selection/` and reproduce
the paper's own domain-specific results:

### Nuclear magic numbers (IPT ratio figure)

```bash
cd papers/26_general_selection
python3 nuclear_magic_binding.py
```

Produces: `nuclear_magic_s2n.pdf`, `nuclear_magic_ipt_ratio.pdf`, `nuclear_magic_summary.csv`

### Prebiotic amino acid fitness (SIPF model)

```bash
python3 prebiotic_fitness_model.py
```

Produces: `prebiotic_fitness_ipt.pdf`, `prebiotic_fitness_table.csv`

### Origin-of-life Gen/Drain analysis (real-chemistry parametrization)

```bash
python3 prebiotic_gen_drain.py
```

Computes Gen/Drain ratios for autocatalytic prebiotic networks using published
rate constants (Miller-Urey, Sutherland, Brack, Orgel). Tests whether IPT ≈ 1.13
is the natural viability threshold.

### Autocatalytic network toy model

```bash
python3 autocatalytic_ipt.py
```

Toy model: 2,454 network configurations over subsets of 10 first-wave amino acids.
Establishes the Gen/Drain framework prior to real-chemistry parametrization.

### Microbial metabolic selection — E. coli FBA (§7)

**Requirements:** `pip install cobra` (COBRApy ≥ 0.26) plus iJO1366 GSMM.

```bash
# Download iJO1366 genome-scale metabolic model (once, ~20 MB)
python3 -c "import urllib.request; urllib.request.urlretrieve('http://bigg.ucsd.edu/static/models/iJO1366.json', '/tmp/iJO1366.json')"

# Run full analysis
cd papers/26_general_selection
python3 scripts/microbial_ipt_test.py
```

Produces:
- `figures/microbial_ipt.png` / `.pdf` — 3-panel figure (O₂ sweep, carbon-source survey, G/D vs μ)
- `data/microbial_ipt_results.json` — full numerical results

Key result: Pearson r(G/D, μ) = 0.971, p < 0.001 across 8 carbon-source FBA conditions.  
Grade [B].

---

## Organizational selection results (§6)

The organizational survival analysis (§6: Test C AUC=0.781, 13.37× protection
factor; Test B AUC=0.698 activist targeting; Test D-H3 entropy ρ=0.339) was
computed from SEC EDGAR XBRL financial filings and Compustat fundamental data.

**This analysis is not reproducible with public code** — the computation uses
proprietary data infrastructure for survivorship-bias-corrected XBRL extraction
and ROIC/WACC construction.

**Methodology available upon request.**

Summary: Organizational survival data computed using SEC EDGAR XBRL (full
historical panel including delisted companies) and Compustat/Finnhub ROIC and
WACC at each annual reporting date. Panel covers 1,354 company-year observations
(2013–2023). Temporal leakage prevention: G/D features use prior fiscal
year-end data; all AUC estimates on out-of-time holdout splits.

### Canonical result files

Machine-readable JSON results and figures are archived in:

| File | Domain | Key result |
|------|--------|-----------|
| `data/survival_test_N590_AUC0781_results.json` | Organizational survival | AUC=0.781, OR=13.37× at IPT |
| `data/conditional_survival_3regime_DBIC92_results.json` | Three-regime structure | Three-regime cascade, ΔBIC=−92.19, IPT as second boundary |
| `data/activist_signal_N2006_AUC0698_results.json` | Activist targeting | AUC=0.6977, N=2,006 |
| `data/phase_a_infothermo_results.json` | Information-thermodynamic entropy | ρ=0.339, p=0.005 |
| `data/tsr_prediction_fulluniv_N8546_results.json` | TSR prediction | AUC=0.564 (null, EMH-consistent) |
| `data/variance_phase_transition_spec056_results.json` | Variance phase transition (Test V) | BC(Watch)=0.907, Levene p=0.046, dip p≈0 |
| `data/v9_variance_phase_transition_results.json` | Variance phase transition raw | N=12,741; V1/V2/V5 pass; V3/V4 fail (tail confound) |
| `figures/survival_roc_ipt.png` | Organizational survival | ROC curve figure |
| `figures/fig10_variance_watch_zone_returns.png` | Variance phase transition (Test V) | Return distributions by IPT regime |

See `data/MANIFEST.md` for full descriptions of all artifacts.

### Test V — Variance Phase Transition (SPEC_056_VPT)

The Watch-Zone variance phase transition test was run on N=12,741 company-years (SPEC_056_VPT, 2026-05-12).
This analysis is not reproducible with public code — same data infrastructure constraints as §6 Tests B/C/D.

**Key results:**
- V1 (Levene): std(Watch)=2.33, std(Safe)=1.30, ratio=1.79×, p=0.046
- V2 (Bimodality): BC(Watch)=0.907 >> 0.555; Hartigan dip p≈0
- V5 (Escape symmetry): P(W→S)=0.12, P(W→D)=0.14
- V3/V4: Fail (Safe Zone right-skew outlier confound)

Result files: `data/variance_phase_transition_spec056_results.json`, `data/v9_variance_phase_transition_results.json`

---

## Cross-paper claims — see companion reproduction guides

| Claim domain | Source paper | Reproduction guide |
|---|---|---|
| Particle physics (IPT, Q(ζ₁₂₀)) | P24 (deeper_theory) | `papers/24_deeper_theory/REPRODUCE.md` |
| Nuclear magic numbers (full) | P03 (nuclear) | `papers/03_nuclear/REPRODUCE.md` |
| Genetic code uniqueness | P25 (genetic_code) | `papers/25_genetic_code/REPRODUCE.md` |
| Coxeter-conductor theorem | P17 (braid_atlas) | `papers/17_braid_atlas/REPRODUCE.md` |
| E8 mass ratios | P24 | `papers/24_deeper_theory/pslq_e8_exact.py` |
| WZW quantum dimensions | P24 | `papers/24_deeper_theory/wzw_dimensions.py` |
| Toda mass spectra | P24 | `papers/24_deeper_theory/toda_masses.py` |

## LaTeX compilation

```bash
cd papers/26_general_selection
pdflatex -interaction=nonstopmode general_selection_theory.tex
biber general_selection_theory
pdflatex -interaction=nonstopmode general_selection_theory.tex
```

## Lean formalization

### ugp-physics-lean — Asymptotic Sparsity (Theorem 1.1)

Repository: https://github.com/novaspivack/ugp-physics-lean

```bash
git clone https://github.com/novaspivack/ugp-physics-lean
cd ugp-physics-lean
lake build UgpPhysicsLean.GXT.AsymptoticSparsity
```

Key theorems for P26 Theorem 1.1:

| Theorem | Lean name | Module | Grade |
|---------|-----------|--------|-------|
| Hoeffding exponent positive | `hoeffding_exponent_pos` | `UgpPhysicsLean.GXT.AsymptoticSparsity` | [A_Lean] |
| Exponential bound ≤ 1 | `hoeffding_bound_le_one` | `UgpPhysicsLean.GXT.AsymptoticSparsity` | [A_Lean] |
| Viable fraction has exponential upper bound | `asymptotic_sparsity_ipt` | `UgpPhysicsLean.GXT.AsymptoticSparsity` | [B] (zero sorry, under `h_hoeffding_bound`) |
| C·exp(−δN) → 0 as N → ∞ | `exp_decay_tendsto_zero` | `UgpPhysicsLean.GXT.AsymptoticSparsity` | [A_Lean] |
| Full sparsity convergence | `asymptotic_sparsity_tendsto_zero` | `UgpPhysicsLean.GXT.AsymptoticSparsity` | [B] |

`h_hoeffding_bound` (the Hoeffding concentration inequality hypothesis) is physically
grounded but requires Mathlib's concentration inequality infrastructure for a full
[A_Lean] certificate; tracked as an open gap. The exponential decay conclusion and
Hoeffding exponent estimates are zero sorry.

### ugp-lean — Cyclotomic and IPT theorems

The Lean-certified Q(ζ₁₂₀) theorems cited in §3 are in the `ugp-lean` library:
```bash
cd /path/to/ugp-lean
lake build UgpLean
```

See `ugp-lean/docs/THEOREMS.md` for the full theorem catalog.
