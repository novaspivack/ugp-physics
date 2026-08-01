# REPRODUCE — P30 Cook Theorem Formalization

**Status:** Partial certification — Lean library builds; L=6 list compose certificate + Python cross-check available.

## Lean 4 proof artifact

**Repository:** `rule110-lean`  
**Local path:** `/Users/nova/rule110-lean`  
**Toolchain:** Lean 4.29.x, Mathlib `v4.29.1` (see `lakefile.lean`)

### Steps

```bash
cd /Users/nova/rule110-lean
lake exe cache get    # first run only
lake build
```

### Expected result (2026-05-20)

- `lake build` succeeds (3365 jobs).
- `Rule110.len6Evolved390_correct` — hard-coded L=6 evolved list proved by `native_decide`.
- `Rule110.len6_evolved_inf30_eq_list420_at_slot` — **theorem** (not axiom), proved via literal + 30-step bridge.
- `Rule110.cook_cts_tail_origin_len6_M390_M30` — **zero sorry**, fully discharged.
- `cook_operational_stage3_tm_microstep_readback` is a theorem (contingent on 5 named Cook bridge axioms — see `#print axioms`). It is a conditional operational certification (CTS decode plus origin readback for an already-supplied `TMCTSCompilation` witness), not a Turing-universality theorem.

### Axiom check

```bash
lake env lean axiom_check.lean
# axiom_check.lean:
#   import Rule110.CookUniversalityTop
#   open Rule110
#   #print axioms cook_operational_stage3_tm_microstep_readback
```

Expected Cook bridge axioms (5):
- `cook_cts_data_cones_origin_one_step_ax`
- `cook_cts_eval_sim_at_data_cones_origin_step_degenerate`
- `cook_cts_phased_post_decode_ax`
- `cook_cts_tail_origin_ax`
- `cook_cts_tail_origin_final_ax`

These are mathematical facts from Cook (2004) §4, not yet formalized in full generality.
The `native_decide` axioms in the list are not Cook bridge axioms.


### Spot checks (Lean REPL or `#check`)

```lean
#import Rule110.CookLen6FastInfCert
#import Rule110.CookLen6TailOrigin
#check Rule110.len6_fast_compose420_origin_ok
#check Rule110.cook_cts_tail_origin_len6_M390_M30
#print axioms Rule110.cook_cts_tail_origin_len6_M390_M30
#print axioms Rule110.len6_evolved_inf30_eq_list420_at_slot
```

## L=6 evolved-origin list certificate (Python cross-check)

From `papers/30_cook_theorem/`:

```bash
# Export init tape from Lean (once, or when encode changes)
cd /Users/nova/rule110-lean
lake env lean --run scripts/export_len6_phased_init.lean
cp len6_true_phased_support_init.json ../ugp-physics/papers/30_cook_theorem/data/

# Verify compose certificate
python3 scripts/len6_evolved_origin_cert.py
```

**Expected:** `Certificate: PASS` for all six slot origins; writes `data/len6_evolved_origin_cert.json` with SHA-256 of the init tape and result payload.

Constants mirrored from Lean: `c2SimBound = 2500`, `M₁ = 390`, `M₂ = 30`, `c2SimOrigin slot = 1000 + 42·slot`.

## Paper PDF (optional)

From `papers/30_cook_theorem/`:

```bash
pdflatex cook_theorem_paper.tex
bibtex cook_theorem_paper
pdflatex cook_theorem_paper.tex
pdflatex cook_theorem_paper.tex
```

## Cross-repo scripts (rule110-lean)

`scripts/cook_m_values.py` and `scripts/gen_cook_block_data.py` referenced in the paper's proof pipeline (§Reproducibility) live in the `rule110-lean` companion repo at `rule110-lean/scripts/`. Clone that repo and run from its `scripts/` directory:

```bash
cd /path/to/rule110-lean/scripts
python3 gen_cook_block_data.py   # generates cook_blocks.json → CookBlockData.lean input
python3 cook_m_values.py         # verified by lean{cook_m_values_python_parity}
```

## Remaining axioms

Five Cook bridge axioms remain; see `CLOSING_COOK_REMAINING_WORK.md` in the epic for the close path for each.

## When complete

Update this file with:

1. Pinned `rule110-lean` commit hash after InfTape bridge discharge
2. Confirmation that `#print axioms` on the top universality theorem shows no Cook bridge axioms
3. Job count and wall time for `lake build` on reference hardware
