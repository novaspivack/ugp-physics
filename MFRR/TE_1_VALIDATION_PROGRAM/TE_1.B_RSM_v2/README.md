# TE₁.B_v2 Reflexive Statistical Mechanics Redesign

This directory hosts the reconceptualized TE₁.B programme (version 2). The prior PR-0-heavy implementation was removed; the new plan focuses on:

1. **TE₁.B.1 — Minimal Reflexive Fluctuation Testbed**: a tractable reflexive Markov system that demonstrates Jarzynski, Crooks, and Green–Kubo with a reflexive controller.
2. **TE₁.B.2 — PR-0 Consistency Check**: a lightweight validation showing the full PR-0 substrate is compatible with the minimal model’s fluctuation structure.

Consult `docs/TE1B_Minimal_RSM_Spec.md` for detailed objectives, architecture, and implementation milestones. All new code resides in `src/` and must reference that specification in its header comments.

To run the minimal experiment end-to-end from this directory:

```bash
python -m src.run_minimal --help
```
