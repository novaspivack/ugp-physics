# 1_1_TE_1U_TRANSPUTATIONAL_UNIVERSALITY_PLAN

Cross-links: [Kickoff](1_0_TE_1U_TRANSPUTATIONAL_UNIVERSALITY_KICKOFF.md) - [Audit 1_8](../SESSIONS/1_8_NEW_SUB-PROJECTS.md) - [TE1 Summary](../SESSIONS/TE_1_SUMMARY.md) - [Integration TODOs](../SESSIONS/TE_1_FINAL_INTEGRATION_TODO_LIST.md)

## Objectives
1. Prove weak and strong transputational universality for PR-0.
2. Demonstrate epsilon-simulation of benchmark systems using PR-0 encodings.
3. Validate strong universality proxies through entropy complexity analysis.
4. Deliver documentation and datasets suitable for MFRR integration.

## Work Breakdown Structure

### Phase A: Formal Proof Development
- A1. Catalogue admissible transputations and define encoding function iota.
- A2. Prove epsilon-simulation bounds leveraging PR-0 dynamics.
- A3. Formalize strong universality argument using entropy oracle assumptions.
- A4. Draft theorem and remark sections with references to Absolute Gauge results.

### Phase B: Weak Universality Benchmarks
- B1. Select representative systems (Rule 110, logistic map PDE surrogate, RIC kernel).
- B2. Implement encoding scripts using PR-0 CLI (`analysis/wtu_encode.py`).
- B3. Run simulations, compute epsilon metrics (L2, TVD) across finite windows.
- B4. Record results in `results/wtu/` with manifest.

### Phase C: Strong Universality Proxy
- C1. Integrate entropy sources (hardware TRNG or high quality pseudo RNG) into PR-0 runs.
- C2. Collect output sequences; compute compression ratio, approximate Kolmogorov complexity, and entropy rates.
- C3. Compare against finite automaton baselines.
- C4. Store outputs in `results/stu/` with documentation of entropy setup.

### Phase D: Reporting and Integration
- D1. Aggregate findings into tables and plots (epsilon vs time, complexity metrics).
- D2. Draft MFRR section insert referencing TE1.O and TE1.F datasets.
- D3. Update TE1 summary row with milestone status.
- D4. Register artefacts in project manifest with SHA256 hashes.

## Milestones
| Milestone | Target Date | Description | Exit Criteria |
| --------- | ----------- | ----------- | ------------- |
| M1 | 2025-11-16 | Proof draft complete | Theorem text circulation with reviewer comments addressed |
| M2 | 2025-11-19 | Weak universality benchmarks executed | Encoded trajectories logged in `results/wtu/` with epsilon table |
| M3 | 2025-11-22 | Strong universality proxy analysis completed | Complexity report published with figures |
| M4 | 2025-11-23 | Integration package ready | LaTeX insert, figures, tables finalized |

## Validation Checklist
- Epsilon thresholds: <= 1e-3 L2 error for Rule 110 encoding, <= 1e-4 for RIC surrogate.
- Entropy metrics: compression ratio > 0.95 (low compressibility), entropy rate within 1 percent of TRNG baseline.
- All scripts parameterized for reproducibility (seed logging, config snapshots).
- Cross-references verified for Absolute Gauge and RIC datasets.

## Risk Mitigation
- If encodings underperform, iterate on state mapping and timestep alignment; document adjustments.
- For entropy sourcing, validate randomness quality before use; if hardware TRNG unavailable, document substitute.
- Maintain separate branches for experimental modifications to PR-0 CLI to avoid regressions.

## Deliverables
- `proofs/transputational_universality.tex`
- `analysis/wtu_encode.py`, `analysis/stu_entropy.py`, supporting notebooks
- `results/wtu/*.json`, `results/stu/*.json`
- Figures: `figs/wtu_epsilon.png`, `figs/stu_complexity.png`
- Updated TE1 Summary entry and integration notes

## Communication Cadence
- Weekly sync with PR-0 tooling maintainers.
- Post milestone summaries to TE1 summary row.
- Track open issues in integration TODO list.
