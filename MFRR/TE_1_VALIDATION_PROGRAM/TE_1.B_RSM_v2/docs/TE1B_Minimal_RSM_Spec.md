# TE₁.B_v2 Minimal Reflexive Statistical Mechanics Specification

## 1. Objectives

- Construct a tractable reflexive dynamical model that satisfies Jarzynski, Crooks, and Green–Kubo/Fluctuation–Dissipation when regulated by a reflexive controller (TE₁.B.1).
- Demonstrate that the full PR-0 substrate is consistent with the minimal model’s fluctuation structure at selected operating points (TE₁.B.2).

## 2. TE₁.B.1 Minimal Reflexive Testbed

### 2.1 Model Structure
- Finite Markov chain with 6–8 states \(s_i\); each state carries a coherence variable \(c_i\).
- CP-style transitions \(s_i \to s_j\) possess base rates \(k_{ij}\) and entropy increments \(\Delta S_{\text{ref}} = \Delta S_{\text{logical}} + \Delta S_{\text{coh}}\) consistent with the MFRR decomposition.
- Global drive parameter \(\mu\) modulates a subset of transitions to induce forward/reverse asymmetry.

### 2.2 Reflexive Controller
- Observes running windows of:
  - Jarzynski residual \(R_J = \log \langle e^{-\Delta S_{\text{ref}}} \rangle\).
  - Crooks slope deviation \(R_C = \hat{m} - 1\), where \(\hat{m}\) is the logistic slope estimated from forward/reverse samples.
  - Observable \(O\) (e.g., occupancy of a reaction state) for GK/FDT assessment.
- Control knobs: intensity scale \(\alpha\) and reverse bias \(\beta\).
- Adaptation loop: proportional updates drive \(|R_J| < \epsilon_J\) and \(|R_C| < \epsilon_C\) for \(N_{\text{steady}}\) consecutive windows, then freeze \(\alpha^*, \beta^*\).

### 2.3 Validation Protocol
1. **Calibration**: run controller until frozen parameters obtained.
2. **Production**: with \(\alpha^*, \beta^*\) fixed, generate large ensembles for \(+\mu\) and \(-\mu\).
3. **Jarzynski**: require \(\langle e^{-\Delta S_{\text{ref}}} \rangle\) 95% CI within [0.98, 1.02].
4. **Crooks**: logistic slope \(1.00 \pm 0.05\) plus supporting histograms and diagnostic plots.
5. **Green–Kubo / FDT**: autocorrelation integral of \(O\) vs. finite-difference response \(\partial \langle O \rangle / \partial \mu\) to agree within 10% relative error.
6. Document analytic derivations, controller trajectories, and statistical summaries.

## 3. TE₁.B.2 PR-0 Consistency Check

- Select one or two PR-0 parameter points with stable dynamics.
- Use static settings analogous to \(\alpha^*, \beta^*\); no adaptive controller.
- Perform forward/reverse protocol; expect Jarzynski within [0.95, 1.05] and Crooks slope \(1.0 \pm 0.1\).
- Compare work/entropy histograms qualitatively with the minimal model.

## 4. Implementation Roadmap

1. Analytical groundwork: derive entropy increments and expected fluctuation behaviour.
2. Simulation engine (`src/minimal_rsm.py`): states, transitions, entropy collection, observables.
3. Controller module (`src/controller.py`): proportional adaptation, steady-state detection.
4. Simulation coordinator (`src/simulator.py`): forward/reverse ensemble execution with optional multiprocessing.
5. Analysis utilities: bootstrapping, logistic regression, GK integrals, FDT comparison.
6. CLI runner (`src/run_minimal.py`): convenience entry point for calibration + production runs.
7. PR-0 scripts (`src/pr0_check/`): simplified workflows leveraging existing PR-0 APIs.
8. Documentation: update README, produce result summaries, cross-link TE₁ notes.

## 5. Conventions

- Every Python module includes a header referencing this specification.
- Simulation outputs stored under `results/TE1B1_*` or `results/TE1B2_*` with timestamps.
- Markdown reports follow lab notebook standards and cross-link related documents.
