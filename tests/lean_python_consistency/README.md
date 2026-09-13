# Lean ↔ Python Consistency Test Suite

Prevents silent drift between Lean-certified structural quantities and their Python
implementations — the type of bug that caused the EPIC 24 chimera
(a 0.062% false residual propagating through P25 + P26 before being caught).

## Quick start

```bash
cd <repo root>
python3 -m pytest tests/lean_python_consistency/ -v
# Expected: all 28+ tests pass in < 1 second
```

## What is tested

| Test file | What it covers |
|-----------|----------------|
| `test_ugp_core.py` | `C_ALGEBRAIC`, `PHI`, `K_GEN2`, `K_L2`, integer primitives, `B1_REQUIRED` |
| `test_gauge_couplings.py` | `G1_SQ`, `G2_SQ`, `G3_SQ` as exact `Fraction`s matching Lean theorem literals |
| `test_canonical_run_bulk.py` | Bulk importability of primary result scripts; chimera probe |

## Adding a new Lean-certified invariant

1. Add the new Lean theorem literal to `ugp_lean_canon/canonical_values.py`
   under `PRIMITIVES` (for exact rationals) or `DERIVED` (for algebraics).
2. Write a test in the appropriate test file (or add a new file).
3. Run the suite — it should pass.

## Pre-commit hook

The `.pre-commit-config.yaml` at the repo root runs the suite automatically
when `ugp_core.py`, `ugp_lean_canon/`, or `comp_p25_*.py` files are staged.

To install:
```bash
pip install pre-commit
pre-commit install
```

## Acceptance criteria (SPEC_028_LXC)

- **A1** — Form B chimera injection (revert `ugp_core.py` to old formula) causes
  `test_C_algebraic_matches_lean` to fail with a diagnostic message.  ✓ verified.
- **A2** — Current `ugp_core.py` (Form A, post-fix) passes all 28 tests.  ✓ verified.
- **A3** — Any new script hard-coding a Lean-derived value can be caught by
  adding a spot-check to `test_canonical_run_bulk.py`.
- **A4** — Full suite runs in < 1 second.  ✓ verified (0.06 s).
