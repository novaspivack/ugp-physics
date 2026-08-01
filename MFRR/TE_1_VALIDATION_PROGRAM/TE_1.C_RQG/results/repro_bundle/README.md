# TE_1.C Phase 3 Reproducibility Bundle

## Contents
- `manifest.json` — SHA256 checksums, absolute paths, seed configuration, and the exact pipeline command.
- Upstream configs referenced in the manifest (`../configs/*.yaml`).
- Generated outputs in `../results/` and logs in `../logs/` (not duplicated here to avoid drift; integrity verified by hashes).

## Re-run Instructions
1. Ensure Python ≥3.10 with `numpy`, `scipy`, `pandas`, `matplotlib`.
2. From the `ugp-physics` repository root:
   ```
   PYTHONPATH='.' python MFRR/TE_1_VALIDATION_PROGRAM/TE_1.C_RQG/src/pipeline.py
   ```
3. Verify artifacts using `manifest.json` hashes.

## Notes
- Master seed: `1729` (stability realizations) and analytic spectra evaluated from `configs/spectra_slow_roll.yaml`.
- Phase 2 analytic context: `TE_1.C.2_PHASE2_ANALYTIC_NOTE.md`; slow-roll derivation: `TE_1.C.3_Analytic_SlowRoll_Derivation.md`.
- Contact: update the manifest if configs or scripts change before external distribution; regenerate hashes via the helper script when new runs are produced.

