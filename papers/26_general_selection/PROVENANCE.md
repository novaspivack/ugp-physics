# PROVENANCE — Paper 26: A General Theory of Selection

**Title:** A General Theory of Selection: Two-Stage Sieves, the Information Profit Threshold, and Cyclotomic Algebraic Substrates  
**Author:** Nova Spivack  
**Status:** PRE-SUBMISSION (upgraded 2026-05-10)  
**Classification:** PUBLIC  
**Canonical source:** `papers/26_general_selection/general_selection_theory.tex`

---

## What this paper claims

A meta-theoretical synthesis demonstrating that the two-stage sieve mechanism
(admissibility filter ∩ IPT viability filter → asymptotic sparsity) recurs across
structurally unrelated domains. Two independent quantitative signatures are identified:
the dynamical threshold IPT ≈ 1.131 and the algebraic field Q(ζ₁₂₀).

### Evidence domains

| Domain | Evidence | Grade |
|--------|----------|-------|
| Ecology and economics | IPT confirmed in 5 real-world datasets | [T]/[C] |
| Nuclear magic numbers | κ_emp/κ_min(N=50) ≈ 1.149 ≈ IPT (1.6%) | [B] |
| Prebiotic amino acids | Standard-20 pass IPT threshold; 10 non-standard excluded | [B] |
| Genetic code | Unique two-stage sieve survivor (CP-SAT; P25) | [C] |
| **Microbial metabolic selection** | **E. coli iJO1366 FBA: Pearson r(G/D, μ)=0.971, p<0.001; IPT separates selected substrates from formate (G/D=0.384); anaerobic glucose at G/D=1.154** | **[B]** |
| **Organizational selection** | **13.37× protection factor; AUC=0.781; activist AUC=0.698; entropy ρ=0.339; inception-cohort HR=5.01×; variance phase transition BC=0.907, Levene p=0.046; 7 independent tests** | **[B⁻]** |
| E8 QFT mass spectrum | All 8 masses in Q(ζ₁₂₀) — Lean-certified | [T] |
| E7 QFT falsifier | All masses NOT in Q(ζ₁₂₀) — Lean-certified | [T] |
| ADE Toda field theories | Coxeter-conductor theorem: h\|120 ↔ Q(ζ₁₂₀) | [T]+[C] |
| WZW quantum dimensions | (k+2)\|120 ↔ Q(ζ₁₂₀) (PSLQ confirmed) | [C] |
| Cognitive systems | IPT as proposed consciousness threshold | [I] |

## Claim grades

- General Selection Principle (GSP): **[Conj]** — well-motivated conjecture
- **Theorem 1.1 (Asymptotic Sparsity):** **[B]** — zero-sorry Lean formalization in `ugp-physics-lean/UgpPhysicsLean/GXT/AsymptoticSparsity.lean` (2026-05-12); full [A_Lean] pending Mathlib Hoeffding infrastructure
- IPT threshold confirmation: [T] for P15 derivation; [C] for empirical fits; [B] for nuclear/prebiotic
- Q(ζ₁₂₀) confirmations: [T] for Lean-certified; [C] for PSLQ
- Consciousness bridge: [I] — theoretical interpretation only

## Files

| File | Purpose |
|------|---------|
| `general_selection_theory.tex` | Main paper (LaTeX, canonical source) |
| `general_selection_theory.md` | Original draft (superseded by .tex) |
| `nuclear_magic_binding.py` | Python script: nuclear S₂ₙ figure + κ/κ_min analysis |
| `prebiotic_fitness_model.py` | Python script: SIPF fitness model for amino acids |
| `prebiotic_gen_drain.py` | Python script: Gen/Drain calculator using real prebiotic chemistry (Phase 2) |
| `autocatalytic_ipt.py` | Python script: autocatalytic network Gen/Drain toy model (Phase 1) |
| `scripts/microbial_ipt_test.py` | Python script: E. coli FBA G/D analysis (COBRApy + iJO1366) |
| `figures/microbial_ipt.png` / `.pdf` | Figure: 3-panel microbial IPT result (O₂ sweep, carbon-source survey, G/D vs μ) |
| `data/microbial_ipt_results.json` | Data: full numerical FBA results for 8 carbon-source conditions + O₂ sweep |
| `nuclear_magic_s2n.pdf` | Figure: two-neutron separation energy vs N |
| `nuclear_magic_ipt_ratio.pdf` | Figure: κ/κ_min at each magic number |
| `nuclear_magic_summary.csv` | Data table: nuclear magic number summary |
| `prebiotic_fitness_ipt.pdf` | Figure: prebiotic fitness with IPT threshold |
| `prebiotic_fitness_table.csv` | Data table: fitness scores for 30 amino acids |
| `LAB_NOTES_P26_UPGRADE.md` | Lab notes for the 2026-05-10 upgrade |
| `data/` | Machine-readable JSON results for all five GXT organizational tests (graduated 2026-05-12) |
| `data/MANIFEST.md` | Full artifact manifest with descriptions, sample sizes, and key metrics |
| `figures/survival_roc_ipt.png` | ROC curve for Test C survival analysis (cited as Fig. \ref{fig:ipt_survival_roc}) |
| `figures/` | All eight GXT empirical figures (graduated 2026-05-12) |

## Computational Artifacts

| Script | Purpose | Source | Status |
|--------|---------|--------|--------|
| `nuclear_magic_binding.py` | Nuclear S₂ₙ figure and κ/κ_min analysis | `papers/26_general_selection/` (previously graduated) | Active |
| `prebiotic_fitness_model.py` | SIPF fitness model for amino acids | `papers/26_general_selection/` (previously graduated) | Active |
| `prebiotic_gen_drain.py` | Gen/Drain calculator with real prebiotic chemistry (real-chemistry parametrization) | `papers/26_general_selection/` (previously graduated) | Active |
| `autocatalytic_ipt.py` | Autocatalytic network Gen/Drain toy model (initial framework) | `papers/26_general_selection/` (previously graduated) | Active |
| `data/*.json` | GXT organizational test canonical results (7 tests incl. VPT SPEC_056) | VYRA production pipeline | Graduated 2026-05-12 |
| `figures/*.png` | GXT organizational test publication figures (9 figures incl. fig10 variance) | VYRA production pipeline | Graduated 2026-05-12 |

All scripts are deterministic and produce identical output on re-run.

## Lean certification

| Module | Key theorems | Grade |
|--------|-------------|-------|
| `ugp-physics-lean/UgpPhysicsLean/GXT/AsymptoticSparsity.lean` | `hoeffding_exponent_pos`, `hoeffding_bound_le_one`, `exp_decay_tendsto_zero` (all zero sorry); `asymptotic_sparsity_ipt`, `asymptotic_sparsity_tendsto_zero` (zero sorry, under `h_hoeffding_bound`) | Core: [A_Lean]; Full sparsity: [B] |

`h_hoeffding_bound` requires Mathlib's concentration inequality infrastructure (tracked open gap).
Full [A_Lean] for Theorem 1.1 requires closing this gap.

## Upgrade history

## Upgrade history

- **2026-05-12 (microbial metabolic selection):** SPEC_055_MMS — E. coli iJO1366 FBA G/D analysis (COBRApy 0.31, 2583 reactions). Pearson r(G/D, μ)=0.971, p<0.001 across 8 carbon-source conditions. IPT cleanly separates selected substrates (G/D ≥ 1.131) from formate (G/D=0.384). Anaerobic glucose sits 2.1% above IPT (G/D=1.154). New §7 added; P26 domain count 7→8; abstract updated. Grade [B].
- **2026-05-12 (variance phase transition — SPEC_056_VPT):** Test V added to §6. N=12,741 company-years. V1 Levene: std(Watch)=2.33 vs std(Safe)=1.30, p=0.046 ✓; V2 bimodality: BC(Watch)=0.907>>0.555, Hartigan dip p≈0 ✓; V5 escape symmetry: P(W→S)=0.12, P(W→D)=0.14 ✓. Grade [B-] confirmed from two independent directions: first-moment (HR=5.01×, ΔBIC=−92.19) and second-moment (BC=0.907, Levene p=0.046). Organizational domain grade: [B-] (seven independent tests). Result files: `data/variance_phase_transition_spec056_results.json`, `data/v9_variance_phase_transition_results.json`. Figure: `figures/fig10_variance_watch_zone_returns.png`.
- **2026-05-12 (three-regime organizational cascade):** Three-regime conditional survival model (Destruction/Watch/Safe, G/D < 0.4/0.4–1.13/> 1.13) confirmed with failure rates 6.81%→1.11%→0.22% (cascade). ΔBIC=−92 relative to two-regime baseline — strong structural evidence that IPT is a genuine second boundary. Odds ratio 5.15× (Safe vs. Watch zone). All result files in `data/`; ROC figures in `figures/`.
- **2026-05-12:** GXT organizational physics bundle artifacts archived. JSON result files (`data/`) and figures (`figures/`) from production pipeline. Survival AUC=0.781 (N=590); activist targeting AUC=0.698 (N=2,006); entropy ρ=0.339.
- **2026-05-12:** Organizational selection section added (§6). Conclusion upgraded to seven evidence domains. Grade [C+] → [B-] (inception-cohort) → [B-] confirmed (variance phase transition).
- **2026-05-12:** Lean formalization of Theorem 1.1 (Asymptotic Sparsity) in `ugp-physics-lean`; grade [Conj] → [B].
- **2026-05-08:** Graduated to papers/26.
- **2026-05-10:** Major upgrade: claim taxonomy, proof sketch for Theorem 1.1, nuclear magic numbers S₂ₙ figure, prebiotic chemistry data table, §5 (Cognitive Systems), Appendices.

## Remaining open questions

1. IPT band: is IPT exactly 1.1309 or does it represent a criticality band [1.05, 1.15]?
2. Consciousness section: needs empirical test (G/D ratio measurement in conscious/non-conscious systems)
3. 3D Ising bootstrap: conjecture that critical exponents lie in Q(ζ_N) awaits higher-precision data
4. Lean certification of Coxeter-conductor field-theoretic interpretation (currently [C]+[I])
5. ~~Organizational [B-] path~~ — **RESOLVED 2026-05-12**: inception-cohort HR=5.01× + variance phase transition BC=0.907 together confirm [B-] from two directions.
6. Organizational [B] path: international replication (MSCI World ex-US) + H6 attractor p<0.05 with N>200 (est. 2027–2028).
