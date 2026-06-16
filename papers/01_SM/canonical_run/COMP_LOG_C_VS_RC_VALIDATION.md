# VALIDATION REPORT — `log10(|c|)` vs reflexive closure

**Date:** 2026-05-02  
**Handoff specification:** unpack `closure_handoff.zip` → `HANDOFF_SPEC.md` (§3–§4, §10).

**Tracked artifacts:**

- [`comp_ep18_log_c_vs_rc_validation.py`](comp_ep18_log_c_vs_rc_validation.py)
- [`comp_ep18_validation.json`](comp_ep18_validation.json)
- [`ep18_particle_closure_dataset.py`](ep18_particle_closure_dataset.py) — P01-aligned triple / PDG table mirror

---

## 1. Headline statistics (H1)

**Definition:** Pearson correlation between `log10(|c|)` from the P01-aligned canonical triple (Table 12, via [`ep18_particle_closure_dataset.py`](ep18_particle_closure_dataset.py)) and reflexive closure `RC = (M − Σ constituent rest masses)/M`.

| Cohort | r | p-value | n | 95% CI (Fisher z, approximate) |
|--------|---|---------|---|--------------------------------|
| Full spectrum | −0.8300 | 1.95 × 10⁻¹¹ | 41 | *(see JSON for full cohort)* |
| **Composites only** | **−0.9439** | **6.70 × 10⁻¹⁹** | **38** | **[−0.9707, −0.8939]** |

**Excluded / conventions (§5):**

- **Top:** `c = −1` in P01 Table 12 — excluded from `log_c` pipeline (positive-`c` filter), per handoff convention.
- **W, Z, H:** present in particle table but have no fermion-canonical `(a,b,c)` here — excluded when `compute_log_c_for_composite` returns `None`.
- **Composite triple assignment (Task 3.2):** baseline rule = **heaviest constituent inherits constituent triple’s `c`**. Not a Lean theorem; aligns with exploratory code in the handoff’s `code/ugp_internal_test.py`.

---

## 2. Outcome classification (§4)

**`|r|` (composites) = 0.944 ≥ 0.90 ⇒ Outcome A** — strong numerical confirmation **conditional on** the heuristic composite triple map.

Risk called out upstream: **if** a formally correct composite `(a,b,c)` rule yields `|r| < 0.70`, retract the structural bridge (Outcome C playbook).

---

## 3. H2 — 6D PCA reproducibility (`ugp_internal_test.py` Test 5)

Run from unpacked handoff folder `handoff/code/ugp_internal_test.py` (figure outputs go to `handoff/figures/` after path fix).

| PCs | Variance explained |
|-----|---------------------|
| PC1 alone | **57.2%** (threshold ≥ 50%) |
| PC1+PC2 | **75.8%** (threshold ≥ 70%) |
| PC1+PC2+PC3 | **92.25%** (threshold ≥ 90%) |

**PC1 loadings (rows × PC1 column):**

- `R`: +0.022 (small ✓)
- `A`: −0.194 (moderate — not negligible)
- `RC`: −0.504 (**negative ✓**, matches “RC opposes substrate stack” intuition)
- `log_b`: +0.466 (positive ✓)
- `log_c`: +0.508 (positive ✓)
- `G_topo`: +0.483 (positive ✓)

**Deviation from idealized pattern:** `A` is not as “small” on PC1 as the spec caricature suggests; qualitative story (substrate-heavy PC1 separating lifetime-ish PC2 structure) remains aligned with **`explained_variance_ratio_`** thresholds.

---

## 4. H3 — Rigorous infra upgrade

**Status: not yet differentiated from handoff.**

- **Fundamental fermions:** triples coincide with Lean-backed values cited in Paper 01; formalization lives in `ugp-lean` (see Paper 01 theorem bullets).
- **Composites:** no Category‑A canonical triple derivation is wired in — the mass-side baryon model in P01 §7.1 is **Category B** (15-parameter binding scaffold), not an `(a,b,c)` selector for arbitrary hadrons.

**Recommendation:** Before promoting to a phenomenology manuscript, prototype at least **two** deterministic composite assignments (e.g. heaviest quark vs valence-heavy pooling of `log|c|`) and show stability of `|r|` under physically motivated alternatives.

Additionally reconcile **`UGP_GTE_SM_Verifier.CANONICAL_TRIPLES`** with **P01 Table 12 print** explicitly; the closure-handoff deliberately froze Table‑12-positive convention for reproducibility versus the originating clean-room statistic.

---

## 5. Task 3.5 — Cleaner subsamples (composites only)

From [`comp_ep18_validation.json`](comp_ep18_validation.json) field `subsamples_composites_only`:

| Subsample | n | r | p (two-sided) |
|-----------|---|----|---------------|
| Octet ground baryons (p, n, Λ, Σ±, Ξ⁰, Ξ⁻) | 7 | −0.878 | 9.4 × 10⁻³ |
| Pseudoscalars (π±, π⁰, K, η, η′) | 7 | −0.736 | 5.9 × 10⁻² |
| Light vectors (ρ, ω, φ, K*(892)) | 4 | −0.795 | 0.21 |

**Read:** Strongest clean-line signal remains in octet-like baryons; meson-only slices lose power (small-n, width systematics).

---

## 6. Recommendation (§10)

| Item | Action |
|------|--------|
| **Proceed toward phenomenology note?** | **Yes — cautiously.** Outcome A numerically holds for the documented dataset + heuristic. Frame exactly as HANDOFF_SPEC §11: correlational structural observation, **not** a first-principles derivation of RC. |
| **Verifier integration** | Keep [`comp_ep18_log_c_vs_rc_validation.py`](comp_ep18_log_c_vs_rc_validation.py) as the reproducible spine; regenerate JSON after any particle-table or triple convention change (hash in JSON). |
| **Composite triple research** | **Blocking** if the goal is a Category‑A/D “triples encode closure” theorem; **non-blocking** if the deliverable is an honest A/D phenomenology addition with explicit heuristic scope. |

---

## 7. Engineering note (pre-existing bugfix)

All handoff `code/*.py` scripts that saved figures to an absolute staging directory on the author's machine were **broken on import**. They now write under **`handoff/figures/`** relative to the unpacked handoff package.
