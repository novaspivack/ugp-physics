# REPRODUCE — The Uniqueness of the UGP

**Requires:** Python 3.10+, `ugp_discovery_lab/` at the **clone root** of [`ugp-physics`](https://github.com/novaspivack/ugp-physics) (stdlib only for core sieves).

```bash
cd ugp_discovery_lab
```

## 1) Stage 1: Full arithmetic sieve (n=4–30, ~42 seconds)

```bash
python3.10 ugp_uniqueness_sieve.py
```

**Expected output:** `EXACTLY ONE SOLUTION FOUND` — n=10, b₁=73.  
**Artifact:** `uniqueness_sieve_results.json` — `total_survivors: 1`.

## 2) Stage 2: Physical constraint (instantiation factor, <1 second)

```bash
python3.10 ugp_final_sieve.py
```

**Expected output:** 6 candidates tested; only b₁=73 passes (relative error 2.70×10⁻⁵⁹).  
**Artifact:** `final_sieve_results.json`.

## 3) Cleanroom independent derivation

```bash
pip install -e ".[plots]"  # only needed once
python3.10 test_ugp_t_02_first_principles.py
```

**Expected:** `VALIDATION PASSED: δ matches target within 1e-5`

## 4) Universal instantiation factor

```bash
python3.10 test_ugp_t_03_universal_instantiation.py
```

**Expected:** g₁²=0.1301, g₂²=0.4385, g₃²=1.5103

## 5) Compile paper

```bash
cd ../papers/05_uniqueness
latexmk -pdf -interaction=nonstopmode "The Uniqueness of the Universal Generative Principle.tex"
```

## Notes

- `protocol_victory_lap_final.py` fails at Step 3 (RGE type error in `ugp_renormalization_finalizer_enhanced`). This script is supplementary and not required for the uniqueness theorem. The failure does not affect core results.
- The paper's Table 1 values (b₁, δ_predicted, relative errors) can be reproduced from `final_sieve_results.json`.
