# P46 — REPRODUCE

## Compilation

```bash
cd papers/46_gte_polynomial_uft
pdflatex gte_polynomial_uft_paper.tex
bibtex gte_polynomial_uft_paper
pdflatex gte_polynomial_uft_paper.tex
pdflatex gte_polynomial_uft_paper.tex
```

Expected output: `gte_polynomial_uft_paper.pdf`, ~40–50 pages, no errors.

## Lean verification

Key theorems are in the `ugp-lean` repository.

```bash
cd /path/to/ugp-lean
lake build
# Expected: zero sorry in the modules listed in Appendix A
```

Key modules:
- `UgpLean/Gravity/PMDLGravityTheorems.lean` — MDL uniqueness, vacuum fixed-point, mass hierarchy (CatAL)
- `UgpLean/Gravity/PMDLVariational.lean` — PMDL variational theorems (CatAL)
- `UgpLean/Gravity/PSCEpochSelection.lean` — PSP axiom L1/L2/T-PSP, Ω_Λ numerical (CatAL)
- `UgpLean/Algebra/ChargeFromPolynomial.lean` — 3Q(w)=p(0,w,0)=w, gravity/EM degree split, tape role asymmetry: p(w,0,0)=0 (l_tape_zero_source), p(0,w,0)=w (tape_role_asymmetry), gravity requires cross-tape coordination (gravity_requires_cross_tape_coordination), non-separability witness (CatAL, commit 243764d)
- `UgpLean/Algebra/SU3GluonCount.lean` — 8 gluon generators (CatAL)
- `UgpLean/Algebra/ColorConfinementMDL.lean` — ΔK=log₂(9) (CatAL)
- `UgpLean/Algebra/BaryonNumber.lean` — B=(1/3)Σχ_q topological charge (CatAL)
- `UgpLean/Algebra/SRRGCABridge.lean` — 1/φ = CA self-similar fixed point (CatAL)
- `UgpLean/Algebra/GaugeMDL.lean` — SU(2)_L from PMDL gauging (zero named axioms) (CatAL)
- `UgpLean/Framework/MDLTower.lean` — three nested MDL roles unified (CatAL)
- `UgpLean/Universality/FiveRolesPolynomial.lean` — five physical roles, K_extra=0 (CatAL)
- `UgpLean/Gravity/PSCEpochSelection.lean` — `incompleteness_implies_nonzero_omega_lambda` (CatAL)
- `UgpLean/BraidAtlas/WindingToBraidRep.lean` — fermionic sector = non-primitive roots Z₇* (CatAL)

## Python scripts (CatA numerics)

The Python scripts in `scripts/` are adapted from the canonical P45 three-tape CMCA implementation. To reproduce the CatA numerical results cited in this paper, run each script from within the `scripts/` directory with Python 3.9+ and NumPy/SciPy installed.

```bash
cd papers/46_gte_polynomial_uft/scripts
python3 coulomb_regime_gravity.py
python3 bell_inequality_test.py
python3 entanglement_analysis.py
python3 baryon_number_l2_correspondence.py
```

| Script | Key result |
|---|---|
| `coulomb_regime_gravity.py` | Force law \(F \propto b^{-2.23}\) (Coulomb regime) |
| `bell_inequality_test.py` | CHSH \(S \approx 2.44\) at \(G_{\rm eff}=0.5\) |
| `entanglement_analysis.py` | Tape-tape entanglement negativity scan |
| `baryon_number_l2_correspondence.py` | L1↔L2 baryon number coincidence: B_L2 = B_L1 via (7/6π)(2π/7) = 1/3; ∂_μJ^μ_B = 0 topological (CatAD) |

Artifact: `scripts/baryon_number_l2_correspondence_results.json`

Lean: `baryon_number_l1_l2_correspondence_certified` (zero sorry, `UgpLean/Algebra/BaryonNumber.lean`)

## Additional Lean certificates

| Theorem | Module | Commit | Statement |
|---|---|---|---|
| `gte_polynomial_five_roles_k_extra_zero` | `UgpLean/Universality/FiveRolesPolynomial.lean` | `f3d5334` | Single-Source Principle: five physical roles with K_extra=0 |
| `su2l_l2_from_phimdl_potential_catad` | `UgpLean/Algebra/GaugeMDL.lean` | `378ff20` | SU(2)_L gauging from PMDL; zero named axioms (CatAL) |
| `phimdl_potential_su2l_invariant` | `UgpLean/Algebra/GaugeMDL.lean` | `378ff20` | L2 norm preserved under SU(2) |
| `su2l_covariant_derivative_minimal` | `UgpLean/Algebra/GaugeMDL.lean` | `378ff20` | Covariant derivative MDL-minimal |
| `su2l_wpm_generator_algebra` | `UgpLean/Algebra/GaugeMDL.lean` | `378ff20` | W± satisfy SU(2) Lie algebra |
| `incompleteness_implies_nonzero_omega_lambda` | `UgpLean/Gravity/PSCEpochSelection.lean` | `63c015b` | PSC incompleteness → D_res>0 → Ω_Λ>0 |
| `mdl_tower_bundle` | `UgpLean/Framework/MDLTower.lean` | `63c015b` | Three nested MDL roles unified |

Verify with `lake build` from the `ugp-lean` repository root.

## Key numerical results

| Quantity | Value | Error | Source |
|---|---|---|---|
| Ω_Λ | 0.6899 | 0.70σ from Planck | PSCEpochSelection.lean |
| ΔK (color confinement) | log₂(9) = 3.170 bits | exact | ColorConfinementMDL.lean |
| Gravity force law | b^{-2.23} | <12% from b^{-2} | coulomb_regime_gravity.py |
| Bell violation | S=2.44 | 87% Tsirelson | bell_inequality_test.py |
| Quantum entanglement | Negativity=0.38 | — | entanglement_analysis.py |
| SRRG-CA bridge | 1/φ = 0.6180 | exact algebraic | SRRGCABridge.lean |
| m_W (1-loop) | 80.37 GeV | 0.008% from PDG 80.377 | W propagator (g×v_PSC/2) |

## Generating functional

Z[J] = ∫Dφ exp(−½φ(−Δ)φ − p(w_x,w_y,w_z)φ + Jφ)

Sources:
- Gravity: p(w_x,w_y,w_z) [degree-3 diagonal]
- EM: p(0,w,0) = w [degree-1 linear, Q = p(0,w,0)/3]
- All massless propagators: (−Δ)^{-1} = 1/(4πr) [source-independent]
- W/Z propagators: (−Δ+m²)^{-1} = e^{-mr}/(4πr) [Yukawa]
