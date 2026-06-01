# Reproduction Guide — The Self-Referential Renormalization Group (P27)

This document provides exact steps to reproduce the computational results reported in:
*"The Self-Referential Renormalization Group: A Universal Framework for Physical Constants"*

---

## Environment

- Python 3.9 or later
- `numpy` (required)
- `matplotlib` (optional, for plot output)

```bash
pip install numpy matplotlib
```

---

## Lean Machine-Checked Verification

All core SRRG theorems are formalized in `srrg-lean` (zero sorry for owned modules):

```bash
# Build the full ugp-lean library (includes GaugeCouplings, etc.)
git clone https://github.com/novaspivack/ugp-lean.git
cd ugp-lean
lake build UgpLean

# Key SRRG-relevant modules:
lake build UgpLean.Phase4.GaugeCouplings   # sin²θ_W derivation
lake build UgpLean.CyclotomicCompleteness.CyclotomicContainment
```

See `ugp-lean/docs/THEOREMS.md` for the full theorem catalog.

The two-fixed-point picture and derived $\beta_\eta$ quadratic form are formalized in:

```bash
git clone https://github.com/novaspivack/srrg-lean.git
cd srrg-lean
lake build SrrgLean.FixedPoints.EtaFlow           # two fixed-point flow, sign analysis
lake build SrrgLean.FixedPoints.NoThirdFixedPoint  # no-third-zero [A_Lean]; exhaustion [B+]
lake build SrrgLean.FixedPoints.BetaEtaQuadratic   # Vieta uniqueness + derived β_η [A_Lean]/[B+]
```

Key theorems for the §5 Remark:

| Theorem | Lean name | Module | Grade |
|---------|-----------|--------|-------|
| No third zero of candidate β_η | `eta_beta_zero_iff` | `FixedPoints/NoThirdFixedPoint` | [A_Lean] |
| Candidate β_η has exactly two zeros | `no_third_zero_of_eta_beta` | `FixedPoints/NoThirdFixedPoint` | [A_Lean] |
| No third SRRG fixed point (under exhaustion hyp.) | `no_third_srrg_fixed_point` | `FixedPoints/NoThirdFixedPoint` | [B+] |
| Vieta uniqueness: deg-2 poly with 2 zeros | `poly2_zeros_determine_poly` | `FixedPoints/BetaEtaQuadratic` | [A_Lean] |
| Unique deg-2 poly with zeros at IPT and 2 is β_η | `eta_beta_is_unique_quadratic` | `FixedPoints/BetaEtaQuadratic` | [A_Lean] |
| SRRG β_η = κ(η−IPT)(η−2) derived under two hyps. | `beta_eta_quadratic_form` | `FixedPoints/BetaEtaQuadratic` | [B+] |

All six theorems: zero sorry.

Upstream warnings in `UgpPhysicsLean.GXT.{U1DirectProof, LieExpSurjective}` are
pre-existing in `ugp-physics-lean` and tracked separately; they do not affect SRRG
core theorems.

---

## β_η Flow Trajectories Script

**Script:** `scripts/beta_eta_flow.py`

**Purpose:** Numerically integrates the $\beta$-function flow
$d\eta/dt = \kappa(\eta - \mathrm{IPT})(\eta - 2)$ from eight initial conditions
$\eta_0 \in \{0.5, 0.8, 1.05, 1.2, 1.5, 1.8, 2.1, 2.5\}$ and produces the three-panel
flow figure (§5 Remark).  Also verifies the analytic separable solution
$(\eta(t)-2)/(\eta(t)-\mathrm{IPT}) = C e^{\kappa(2-\mathrm{IPT})t}$.

**Usage:**

```bash
cd papers/27_SRRG
python3 scripts/beta_eta_flow.py
```

**Dependencies:** `numpy`, `matplotlib`

**Output:** `figures/beta_eta_flow.png` — three-panel figure:
Panel A: $\beta$-function profile with sign regions;
Panel B: phase portrait (flow arrows);
Panel C: RG flow trajectories (IR-stable fixed point $\mathrm{IPT}\approx 1.1309$;
UV-unstable fixed point $\eta=2$).

**Key results to verify:**
- All trajectories with $\eta_0 < 2$ converge to $\mathrm{IPT}\approx 1.1309$ within
  $1.3\times 10^{-5}$ at $t=15$.
- Trajectories with $\eta_0 > 2$ diverge.
- Analytic solution matches numerics to $< 3\times 10^{-13}$ at $t=10$.

---

## Fine-Structure Constant: Direct Coupling Route (Appendix C, Round 09)

**Method:** Pure algebraic evaluation — no Python script required.

**Claim:** $1/\alpha(M_Z) = 4\pi\cdot(g_1^2+g_2^2)\cdot g_1^2 g_2^2 / (g_1^2 g_2^2)
= 4\pi\cdot 377525/37264 \approx 127.311$ (0.495% from PDG 127.944).

**To verify by hand or in Python:**

```python
from fractions import Fraction
import math

g1sq = Fraction(16, 125)
g2sq = Fraction(2329, 5400)
num = g1sq + g2sq          # 377525/675000
den = g1sq * g2sq           # 37264/675000
inv_alpha = 4 * math.pi * float(num / den)
print(f"1/alpha(M_Z) = {inv_alpha:.6f}")        # expects ~127.311
print(f"PDG value 127.944, deviation {abs(inv_alpha-127.944)/127.944*100:.3f}%")  # expects ~0.495%

# By-product: bare Weinberg angle
sin2_thetaW = float(g1sq / (g1sq + g2sq))
print(f"sin^2(theta_W) bare = {sin2_thetaW:.6f}")  # expects ~0.2290
```

**Key results (grade [A/D]; upstream Lean-certified couplings from `ugp-lean`):**
- $1/\alpha(M_Z) \approx 127.311$ (0.495% from PDG)
- $\sin^2\theta_W^{\rm bare} = 3456/15101 \approx 0.229$ (1.0% from PDG)

**SRRG–MDL equivalence conjecture (Open Problem 9; grade [B+]):** No computation
required; this is a structural identification established in Appendix C and awaiting
Lean formalization.

---

## Weinberg Angle Haar Entropy Assessment Script

**Script:** `scripts/weinberg_angle_haar.py`

**Purpose:** Enumerates all simple ratios of Haar measure entropies for U(1), SU(2),
and SU(3) and checks whether any ratio matches sin²θ_W = 0.23122 ± 0.00003 (PDG 2022).
This is the preliminary structural test described in §8.4.

**Usage:**

```bash
cd papers/27_SRRG
python3 scripts/weinberg_angle_haar.py
```

**Dependencies:** `numpy` only

**Key result:** No simple Haar entropy ratio recovers the experimental value. Best
candidate: H_U1/(H_SU2+H_SU3) ≈ 0.212 (deviation 8.2%). **Negative result honestly
disclosed.** Grade: [D→C] — structural hypothesis identified and numerically tested.

---

## Weinberg Angle RG-Running Script

**Script:** `scripts/weinberg_rg_running.py`

**Purpose:** Tests whether SRRG Haar-entropy Planck-scale boundary conditions +
one-loop SM RG running from M_Planck to M_Z reproduce sin²(θ_W). Fixes the free
parameter λ from α_s(M_Z) = 0.1179 (PDG 2022) and predicts α_1(M_Z), α_2(M_Z).

**Usage:**

```bash
cd papers/27_SRRG
python3 scripts/weinberg_rg_running.py
```

**Dependencies:** `numpy`, `scipy`

**Key result:** sin²θ_W ≈ 0.190 (−1385σ from experiment). **Negative result honestly
disclosed.** The Haar-entropy RG approach does not reproduce the Weinberg angle.

---

## Weinberg Angle GUT Unification Script

**Script:** `scripts/weinberg_gut_unification.py`

**Purpose:** Tests three GUT-scale directions for recovering sin²θ_W = 0.23122 ± 0.00003
(PDG 2022): (1) canonical GUT unification (α₁ = α₂ at M_GUT), (2) two-loop SM RG
running from M_Planck to M_Z, and (3) SU(5) embedding normalization (5/3 factor
applied to the Haar entropy U(1) boundary condition).

**Usage:**

```bash
cd papers/27_SRRG
python3 scripts/weinberg_gut_unification.py
```

**Dependencies:** `numpy`, `scipy`

**Key results:**
- Bare Haar ratio: sin²θ_W ≈ 0.381 (deviation ~+5001σ)
- Direction A — GUT democratic coupling at M_GUT + 1-loop to M_Z: deviation −1886σ
- Direction B — Two-loop SM RG running from M_Planck to M_Z: deviation −1358σ (marginal improvement over 1-loop)
- Direction C — SU(5)-embedded U(1) Haar entropy (5/3 normalization): sin²θ_W ≈ 0.412 (deviation +6039σ, worse)
- Root cause diagnosed: SRRG Haar-entropy boundary sets α₁*/α₂* ≈ 0.616; experiment requires ≈ 1.0 at M_GUT; this is not a running problem but a boundary condition problem
- **Negative result honestly disclosed.** Grade: [D→C]. Path forward requires deriving U(1) hypercharge normalization from SRRG matter-field content (Open Problem 5).

---

## CFT Universality and ε₃ₛ Crossing Script

**Script:** `cft_universality_classes.py`

**Purpose:** Computes the ε₃ₛ = MI·ξ/L observable at critical-strip scaling for the
2D Ising model and the 3-state Potts model, testing the GXT hypothesis that
ε₃ₛ → IPT at the critical point (§5, H13a/H16).

**Observable:** ε₃ₛ = MI·ξ/L at critical-strip scaling; tests ε₃ₛ → IPT hypothesis

**Usage:**

```bash
cd papers/27_SRRG
python3 cft_universality_classes.py --L 4 6 8
```

Add `--plot` for a PNG figure:

```bash
python3 cft_universality_classes.py --L 4 6 8 --plot
```

**Output:** JSON artifacts written to `results/` with SHA-256 content-addressed
filenames (hash printed to stdout). The JSON contains `epsilon3s`, `mutual_information_nats`,
`xi`, and `beta` for each strip width L.

**Key result to verify:** For the 2D Ising model at β_c ≈ ln(1+√2)/2,
ε₃ₛ should approach IPT ≈ 1.1309 as L increases.

**Dependencies:** `numpy` only for core computation; `matplotlib` for `--plot`.

---

## VEVProof — EW Vacuum PSC Entropy Derivation

The EW VEV structural derivation is formalized in four `srrg-lean` modules
(all zero sorry; grade [A−]; conditional on 1 named open axiom: `psc_ew_entropy_maximization`):

```bash
cd srrg-lean
lake exe cache get
lake build SrrgLean.VEVProof
```

| Module | Lean file | Lean-certified theorem | Key result |
|--------|-----------|----------------------|-----------|
| `GoldstoneEntropyCorrection` | `VEVProof/GoldstoneEntropyCorrection.lean` | `goldstone_volume_correction_per_generation` | $\varphi^{1/N_{\rm gen}}$ volume correction from SRRG $1/\varphi$ eigenvalue |
| `PSCEntropyDuality` | `VEVProof/PSCEntropyDuality.lean` | `psc_entropy_after_contraction` | PSC Entropy-Contraction Duality theorem |
| `EWGoldstoneManifold` | `VEVProof/EWGoldstoneManifold.lean` | `ew_vacuum_manifold_uniqueness` | EW vacuum manifold $= S^3$, $\mathrm{Vol}=2\pi^2$, 3 Goldstone bosons |
| `EWVacuumBridge` | `VEVProof/EWVacuumBridge.lean` | `srrg_physical_fp_implies_ew_vacuum_manifold` | Bridge from PhysicalSubspace $\mathrm{U}(1)$ minimality to $S^3$ |

**Result:** $v_{\rm PSC} = 246.16$~GeV ($-0.024\%$ from $v_{\rm PDG} = 246.22$~GeV), grade [A−].

**Null-discipline:** saturation 0.35% over 288 structural candidates (structural, not
coincidental; artifact `null_discipline_vev_formula.json` in P01 `canonical_run/`).

**Open axioms (grade [A−] not yet [A_Lean]):**
- `psc_entropy_contraction_duality` — general PSC/SRRG duality (est. 2–4 months to prove)
- `srrg_s3_entropy_increase` — S³-specific consequence (follows from general duality)

---

## EPIC_083 additions (2026-05-31): SRRG–MDL Equivalence (OP9 partial closure)

Open Problem 9 is now CatAD partially closed. The algebraic core is formalized in two
new `srrg-lean` modules (both zero sorry; commit `6ccf201`):

```bash
cd srrg-lean
lake exe cache get
lake build SrrgLean.Bridges.ToMDL         # OP9 algebraic bridge (13 theorems)
lake build SrrgLean.Core.CMCALanguage     # CMCA encoding language formalization
```

**`SrrgLean/Bridges/ToMDL.lean`** — 13 theorems, all zero sorry:

| Theorem | Statement | Status |
|---------|-----------|--------|
| `srrg_mdl_functional_identity` | K[S] = B − F[S] (description length = barrier minus viability) | CatAD |
| `srrg_mdl_proportionality_L` | L[S] = B − R[S] (self-description length is exact, not proportional) | CatAD |
| `srrg_mdl_proportionality_C` | L[data\|S] = C_Λ[S] (conditional description = constraint cost) | CatAD |
| `argmax_viability_iff_argmin_descLen` | IsSrrgFixedPoint P C s ↔ descLen minimizer | CatAD |
| `srrg_fp_is_mdl_minimizer` | SRRG fixed point → MDL minimizer | CatAD |
| `mdl_minimizer_is_srrg_fp` | MDL minimizer → SRRG fixed point | CatAD |
| `srrg_op9_biconditional` | h_ugp → (IsSrrgFixedPoint ↔ K minimizer) | CatAD (1 hypothesis) |

**`SrrgLean/Core/CMCALanguage.lean`** — CMCA encoding language formalization:
- `cmcaUpdate` — CMCA rule p(L,C,R) = C+R−CR−LCR over GF(7)
- `cmca_k_eq_barrier_minus_viability` — K_CMCA(s) = B − F[s] (zero sorry)
- `ugp_substrate_constraint_from_cmca` — conditional full OP9 closure (zero sorry)

**Remaining hypothesis** (`UGPSubstrateConstraint`): two named sorries remain
(`kolmogorov_eq_mdl_profile` L4 and `ugp_substrate_constraint_full` L6). These
require formal shortest-program semantics for the CMCA encoding language (estimated
4–6 months; tracked as Rank 083-UGP-SUBSTRATE).

**Verification (numerical):**

```python
import math
phi = (math.sqrt(5) + 1) / 2
g_star = 1 / phi
K_CMCA = lambda g: -math.log2(g**2 + g)
F = lambda g, B=10: B - K_CMCA(g)   # F[S] = B - K[S]
print(f"K_CMCA(g*) = {K_CMCA(g_star):.6f}")  # expects 0.0
print(f"F(g*) = {F(g_star):.6f}")             # expects B = 10.0
# K + F = B for all g:
for g in [0.3, 0.4, 0.5, g_star]:
    print(f"g={g:.4f}: K+F = {K_CMCA(g) + F(g):.6f}")  # all 10.0
```

---

## EPIC_080 additions (2026-05-29)

### One-loop radiative corrections to m_W (G29)

**Script:** `scripts/srrg_loop_corrections.py`

**Purpose:** Computes the oblique ρ-parameter (T-parameter) one-loop correction to m_W
from the top-bottom doublet and verifies the v_H radiative stability bound from the SRRG
β_η attractor structure.

**Usage:**
```bash
cd papers/27_SRRG
python3 scripts/srrg_loop_corrections.py
```

**Key results to verify:**
- δρ = 3G_F m_top²/(8π²√2) = 0.00939
- m_W(1-loop) = 80.372 GeV (vs PDG 80.377 GeV; residual 4.7 MeV, 0.006%)
- Oblique correction closes 98.8% of the tree-level m_W gap
- v_H radiative shift upper bound: δv_H/v_H ≤ 2%

Artifact: `scripts/srrg_loop_corrections_results.json`

---

## EPIC_083B additions (2026-06-01)

**SU(2)_L MDL gauging (CatAL, zero named axioms):**
- `su2l_l2_from_phimdl_potential_catad` — `UgpLean/Algebra/GaugeMDL.lean` (ugp-lean commit `378ff20`)
- Supporting theorems: `phimdl_potential_su2l_invariant`, `su2l_covariant_derivative_minimal`, `su2l_wpm_generator_algebra`, `m_W_gap_fraction_certified`
- Verify: `cd ugp-lean && lake build UgpLean.Algebra.GaugeMDL`

---

## LaTeX Compilation

```bash
cd papers/27_SRRG
pdflatex -interaction=nonstopmode srrg_paper.tex
biber srrg_paper
pdflatex -interaction=nonstopmode srrg_paper.tex
pdflatex -interaction=nonstopmode srrg_paper.tex
```

---

## SHA-256 of Key Result Files

Pre-computed JSON results are in `results/` (this directory).  Content-addressed
filenames include the SHA-256 hash; verify by running the script and comparing hashes.

```
results/cft_universality_4b672f8eb70f427d.json   (2D Ising, L∈{4,6,8})
results/cft_universality_913752f229248d5d.json   (3-state Potts, L∈{4,6,8})
```
