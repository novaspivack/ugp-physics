# Uniqueness Sieve — UGP-T-04

Computational proof of the uniqueness of the UGP canonical solution `(n=10, b₁=73)` within its universality class.

The sieve systematically searches the space of possible UGP-like structures (`n = 4 … 30`) and applies a cascade of arithmetic and physical constraints. Only one candidate survives all four filters: the canonical seed.

---

## What this proves

For the UGP framework (R_n = 2ⁿ − 16), the following four constraints jointly select a **unique solution**:

1. **Divisor structure & mirror duality** — pairs (b₂, q₂) with b₂ × q₂ = R_n, both > 15, and mirror (q₂, b₂) also valid.
2. **Prime-lock constraint** — c₁ = b₁ × q₁ + 20 must be prime for both mirror pairs.
3. **Full mirror-dual prime-lock** — both pairs must survive the prime-lock simultaneously.
4. **Instantiation factor constraint** — δ_predicted must match the experimental target δ_UGP = 0.01659915… (80-digit precision, tolerance 10⁻⁵).

Result: out of 27 values of n, **only n=10 produces any survivor**, and that survivor is **b₁=73** with a relative error of ~2.7×10⁻⁵⁹.

---

## Files

| File | Purpose |
|---|---|
| `ugp_uniqueness_sieve.py` | `UGPUniquenessSieve` — runs the full 4-stage sieve over n=4…30, saves `uniqueness_sieve_results.json` |
| `ugp_final_sieve.py` | `UGPFinalSieve` — applies the instantiation-factor constraint to externally provided survivors from `survivors.csv` |
| `test_ugp_t_02_first_principles.py` | First-principles derivation tests (UGP-T-02) |
| `test_ugp_t_03_universal_instantiation.py` | Universal instantiation tests (UGP-T-03) |
| `uniqueness_sieve_summary.md` | Human-readable summary of all sieve results |

---

## Requirements

```bash
pip install numpy   # optional — only stdlib used in the sieve scripts themselves
```

The sieve scripts use only Python stdlib: `json`, `math`, `decimal`, `csv`, `pathlib`. No third-party dependencies are required.

---

## Running

### Full sieve (n=4 to n=30)

```bash
cd uniqueness
python ugp_uniqueness_sieve.py
```

Writes `uniqueness_sieve_results.json` in the same directory.
Expected runtime: < 1 minute.

### Final instantiation-factor sieve

Requires `survivors.csv` (produced by UGP_GTE_SM_Verifier or the full sieve) to be present in the same directory.

```bash
cd uniqueness
python ugp_final_sieve.py
```

Writes `final_sieve_results.json`.

### Tests

```bash
cd uniqueness
python test_ugp_t_02_first_principles.py
python test_ugp_t_03_universal_instantiation.py
```

---

## Key constants (80-digit precision)

| Constant | Value |
|---|---|
| k_L² | 7/512 (exact rational) |
| φ | (1+√5)/2 (golden ratio) |
| k_gen2 | −φ/2 |
| k_M | k_gen2 + (1/4)k_L² |
| δ_target | 0.016599156624119311813092002999496908875… |

---

## Result summary

| n | R_n | Initial pairs | Survived mirror | Survived prime-lock | Final survivors |
|---|-----|--------------|-----------------|---------------------|-----------------|
| 4–9 | — | 0–2 | 0–2 | 0 | **0** |
| **10** | **1008** | **10** | **10** | **2** | **1 (b₁=73)** |
| 11–30 | — | 2–452 | 2–452 | 0–6 | **0** |

The full proof is documented in `uniqueness_sieve_summary.md`. The machine-checked Lean 4 formalization of the uniqueness theorem is in the companion repository [novaspivack/ugp-lean](https://github.com/novaspivack/ugp-lean).

---

## Related

- `papers/05_uniqueness/REPRODUCE.md` — paper replication instructions
- `UGP_GTE_SM_Verifier/` — the GTE verifier that produces inputs consumed by the final sieve
- [ugp-lean](https://github.com/novaspivack/ugp-lean) — Lean 4 machine-checked proof (`rsuc_theorem`, `ridgeSurvivors_10`)
