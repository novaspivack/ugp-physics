# REPRODUCE — Paper 50: The Spin-7 Lattice Model

## Requirements

```bash
pip install numpy scipy matplotlib mpmath sympy
```

No GPU required (all simulations run on CPU in reasonable time; the slowest
script, `spin7_gap_amplitude_selfconsistent.py`, takes about two minutes).

## Scripts

All scripts are in `scripts/`. The polynomial is always `(C + R - C*R - L*C*R) % 7`.

### Transfer Matrix Spectral Data (Section 3, Table 1)

```bash
python3 scripts/spin7_transfer_matrix.py
```

Builds the exact $49 \times 49$ pair-state transfer matrix
$M[(a,b),(b,c)] = e^{-\beta p(a,b,c)}$, verifies $Z_N = \mathrm{Tr}(M^N)$ against
exhaustive enumeration over all $7^N$ ring configurations for $N \le 7$, and
outputs the spectral table (dominant eigenvalues, spectral gap, correlation
length, CMCA entropy rate) at several $\beta$. Expected output at $\beta = 1$:
$\lambda_1 = 1.4846$, $S = \log \lambda_1 = 0.395$ nats/site, $\xi \approx 2.9$
sites; rank $43 = \Phi_6(7)$; zero-energy successor digraph with exactly three
cycles $(0,0)$, $(1,1)$, $(5,5)$. Writes `spin7_transfer_matrix_results.json`.

### 2D Monte Carlo Phase Scan (Section 4, Tables 2-3)

```bash
python3 scripts/spin7_2d_phase.py
```

Runs Metropolis Monte Carlo on $L \times L$ tori for $L \in \{4, 8, 12\}$ at $\beta$
values from $0.20$ to $1.00$. Outputs order parameter $M_{\rm gs}$ and specific heat
$C_V$. Expected: $\beta_c \approx 0.35$, $C_V$ peak $\approx 1.5$--$1.9$.

### Finite-Size Scaling and Hysteresis (Section 4)

```bash
python3 scripts/spin7_2d_fss.py
```

Runs FSS analysis including random-start vs.\ ordered-start hysteresis at high $\beta$.
Expected: hysteresis onset at $\beta_{c,2} \approx 1.7$ for $L = 8$.

### CMCA Connection and Ground-State Algebra (Sections 2, 5)

```bash
python3 scripts/spin7_cmca_connection.py
```

Verifies the exact pair-state transfer matrix identity
$Z = \mathrm{Tr}(\mathbf{M}^N)$ (with enumeration cross-checks), the
$\mathbb{Z}_3$ symmetry of ground states, and that the global ground states
are exactly $\{0, 1, 5\}$. Also available: `spin7_2d_refined.py` for a refined
2D Monte Carlo scan with hysteresis analysis at additional $\beta$ values.

### GTE Constraint Code Parameters (Ground-Space Rigidity)

```bash
python3 scripts/gte_code_parameters.py
```

Treats the cyclic zero-energy strings of the spin-7 chain as a code over
$\mathrm{GF}(7)$ and computes its parameters for ring lengths $n = 3$--$12$:
codeword count $K(n)$ via the pair-state transfer matrix (cross-checked by
exhaustive enumeration for $n \le 8$), effective dimension $k = \log_7 K$,
and exact minimum Hamming distance $d(n)$. Expected output: $|V(p)| = 43$,
$K(n) = 3$ for every $n$ (the three uniform ground states $\{0,1,5\}$),
$d(n) = n$ — i.e.\ the ground space is a ternary repetition code with maximal
relative distance, and the Perron eigenvalue of the pair transfer matrix is
exactly $1$ (no zero-energy entropy). Writes
`scripts/gte_code_parameters_results.json`. Runtime: a few seconds.

## Continuum Limit and the Physical Point (Section 6)

The scripts below require only `numpy` plus `mpmath` (high-precision
eigenvalues) and, for the resolvent scripts, `sympy`/`fractions` (exact
rational algebra). Each writes its JSON artifact next to itself in
`scripts/`.

### Directed Wall Spectroscopy (Section 6.2, Theorem on wall energies)

```bash
python3 scripts/spin7_domain_wall_energy_exact.py
python3 scripts/spin7_wall_translation_classes.py
```

Exact directed interface energies by shortest paths on the 49-node weighted
pair digraph. Expected: `E_w(1->0)=1, E_w(0->1)=2, E_w(5->0)=2, E_w(0->5)=4,
E_w(1->5)=4, E_w(5->1)=4` with the composite identity `E_w(5->1) =
E_w(5->0) + E_w(0->1)`; bump energies `E_loop(0,1,5) = (2,3,4)`; both minimal
walls sharp (one interior pair state, translation freedom only). Note: the
first script's printed "predicted slope" block uses a direction-symmetric
model superseded by the directed (geometric-mean) analysis in the paper; the
integer tables are the result. Writes
`spin7_domain_wall_energy_exact.json`, `spin7_wall_translation_classes.json`.
Runtime: seconds.

### Chiral Gap Law (Section 6.3)

```bash
python3 scripts/spin7_continuum_scaling_law.py        # ~25 s (mpmath dps 50)
python3 scripts/spin7_gap_amplitude_resolvent.py      # ~7 s
python3 scripts/spin7_gap_amplitude_selfconsistent.py # ~105 s
python3 scripts/spin7_gap_amplitude_highbeta_verify.py # ~22 s (mpmath dps 80)
python3 scripts/spin7_spectator_amplitude_resolution.py # ~44 s (mpmath dps 60)
python3 scripts/spin7_subleading_channel_scaling.py   # ~26 s
```

Expected: extrapolated slope `1.4999974` (|dev| 2.6e-06) and amplitude
`0.999986` (scaling law); exact through-walk counts `c10 = c01 = 1`,
`b0 = b1 = 1`, `b5 = 2` and interior nilpotency `N^22 = 0` (resolvent); the
exact correction tower `Delta = e^(-3beta/2)[1 + 1/2 u + 1/8 u^2 + 1/2 u^3 +
63/128 u^4 + 65/4 u^5 + 11971/3072 u^6 + ...]` with residual `7.8e-31` at
beta = 21 (self-consistent); `(lambda_2 - 1)/e^(-4beta) -> 2.0000000`
(high-beta verify); `rho(zero-energy digraph) = 1.000000000000`,
`Delta_3/Delta_2` extrapolated `1.99999932`, ratio-correction coefficient
`0.99999958` (spectator resolution). Note: the printed slope-adjudication
block of `spin7_subleading_channel_scaling.py` uses a simplified
`Delta ~ E*beta` model for soft channels; its raw spectra are correct, and the
correct reading is the cluster analysis of
`spin7_spectator_amplitude_resolution.py`.

### Spectral Insensitivity to the Deterministic Attractor (Section 6.4)

```bash
python3 scripts/spin7_thermal_spectrum_period475.py   # ~6 s
python3 scripts/spin7_spectrum_locked_phases_autopsy.py
```

Pre-registered fingerprint batteries. Expected (all null): 23 tracked
eigenvalue families, 340 lock segments, 0 grid hits (only locked phase is
theta = pi); exact charpoly `lambda^11 * (irreducible deg 38)` at rational
`x in {1/2, 1/3, 1/7}` with lambda-support gcd 1; trivial affine covariance
group. The autopsy script shows wrong-target rules with attractor periods
15/90/385 give the identical spectral pattern, and the kernel accounting
(geometric 6, algebraic 11) is rule-independent.

### Physical Point and Tape Saturation (Sections 6.5–6.7)

```bash
python3 scripts/cmca_physical_point_calibration.py
python3 scripts/mdl_tape_extremization.py
python3 scripts/cmca_spectral_census_physical_point.py
python3 scripts/ldiss_nfam_null_battery.py
python3 scripts/hosting_boundary_csc_free_audit.py      # < 1 s
python3 scripts/spin7_hosting_boundary_digraph_facts.py # < 1 s
```

Expected: `beta* = 1.53459777` with `xi(beta*) = 7.00000000` and
`Delta(beta*) = 1/7` to 1e-8; `S(beta*) = 0.15951931` nats/site; tree spacing
`a = 0.097172 fm`, envelope `0.100677 +/- 0.007705 fm`; `a*m_phi = 0.875`
(= 7/8 exactly); mixed-reading `xi* = 7.23 +/- 0.54` (calibration);
extremization selects the admissible supremum under both pricings at every
kappa, with the campaign-echo rigidity scan giving the unique factorization
`(n, p) = (7, 8)` (extremization); the spectral census at `beta*` returns the
honest negative — no `Delta = 1` structure, `n(Delta <= 1) = 22`, all
pre-registered closed-form candidates fail (census); the dissolution-scale
window census shows 24 rationals in the 1-sigma window (null battery); the
register-window counting gives `kappa = 1` alphabet-independently (Z_N all
1.0), the kappa-family consistency audit shows all six candidates
`{1/3, 2pi/7, 1, pi/2, pi, 2pi}` consistent with every certified constraint
with spread 18.85x (only the `xi_kink = 7/kappa` column discriminates), and
the digraph battery replicates the wall integers, ground sectors `{0,1,5}`,
sharp walls at all beta, and the soft-edge additivity `Delta_3/Delta_2 -> 2`
(audits).

## Lean Certification

The result $|V(p)(\GF{7})| = 43$ is machine-certified in Lean 4 (zero sorry):

```
Theorem: poly_p_zero_variety_count_gf7
Module:  UgpLean/Universality/Z7InvariantSubsets.lean
Repo:    ugp-lean (https://github.com/novaspivack/ugp-lean)
```

The diagonal cubic $p(x,x,x) = -x(x-1)(x-5)$ with roots $\{0,1,5\}$ is
machine-certified (zero sorry):

```
Theorem: poly_p_uniform_gs_roots
Module:  UgpLean/Polynomial/PolyExplorations.lean
Repo:    ugp-lean
```

The ground-space rigidity theorem — for every ring length $n \ge 3$ the
zero-energy configurations are exactly $\{0^n, 1^n, 5^n\}$ — is
machine-certified (zero sorry, zero custom axioms):

```
Theorem: gte_ring_ground_states_uniform_general
Converse: uniform_ground_ring_satisfies_zero_energy
Module:  UgpLean/Polynomial/SpinSevenGroundSpace.lean
Repo:    ugp-lean
```

The directed wall/bump tables and the half-integer gap-exponent arithmetic are
machine-certified (zero sorry):

```
Theorems: spin7_directed_wall_energies, directed_wall_half_integer_gap
Module:   UgpLean/Polynomial/SpinSevenWallSpectroscopy.lean
Repo:     ugp-lean
```

The gap-amplitude counts (with frontier-death totality), the spectator package
(rho = 1, cluster eigensystem, amplitude tie-in), and the Perron–Frobenius
hypothesis package (all real beta) are machine-certified (zero sorry):

```
Theorems: spin7_gap_amplitude_certificate; spin7_spectator_amplitude;
          spin7_transfer_pf_hypotheses
Modules:  UgpLean/Polynomial/SpinSevenGapAmplitude.lean;
          UgpLean/Polynomial/SpinSevenSpectatorAmplitude.lean;
          UgpLean/Polynomial/SpinSevenTransferPrimitivity.lean
Repo:     ugp-lean
```

The physical-point dictionary, the Tape Saturation Theorem (conditional on the
named Compton-Support Criterion), and the Boundary Equivalence Theorem with
the saturation-bijection corollary are machine-certified at their stated
conditional grades (zero sorry; named premise structures
`ComptonSupportCriterion`, `MDLSaturationSpacingHypothesis`,
`RegisterWindowReadability`):

```
Theorems: cmca_physical_point_dictionary, mdl_saturation_tree_reading,
          tape_saturation_theorem, compton_support_derives_mdl_saturation,
          tape_saturation_physical_point_dictionary,
          hosting_boundary_csc_equivalence, saturation_alphabet_bijection
Module:   UgpLean/Physics/CMCAPhysicalPoint.lean
Repo:     ugp-lean
```

## Verification Checklist

- [ ] Pair transfer matrix: $\mathrm{Tr}(M^N)$ = exhaustive $Z_N$ for $N \le 7$
- [ ] Spectral table at $\beta = 0.3$--$3.0$ matches Table 1 ($\lambda_1 = 1.4846$ at $\beta = 1$)
- [ ] $\beta_c \approx 0.35$ from $C_V$ peak in FSS scan
- [ ] Hysteresis onset at $\beta_{c,2} \approx 1.7$ for $L=8$
- [ ] Ground states exactly $\{0,1,5\}$ (exhaustive check)
- [ ] $|V(p)| = 43$ (exhaustive count)
- [ ] Constraint code: $K(n) = 3$, $d(n) = n$ for $n = 3$--$8$; Perron eigenvalue $1$
- [ ] Zero-energy successor digraph: 43 active pairs, only cycles $(0,0)$, $(1,1)$, $(5,5)$
- [ ] Directed wall energies: $E_w(1{\to}0)=1$, $E_w(0{\to}1)=2$, composite $E_w(5{\to}1)=4=2+2$; bumps $(2,3,4)$
- [ ] Gap law: slope $1.4999974$, amplitude $0.999986$; tower residual $7.8\times10^{-31}$ at $\beta=21$
- [ ] $\Delta_3/\Delta_2 \to 2$ (extrapolated $1.99999932$); $\rho(\text{zero-energy digraph}) = 1$
- [ ] Period-475 fingerprint batteries all null (0 grid hits; charpoly $\lambda^{11}\cdot(\deg 38)$, gcd 1; trivial covariance)
- [ ] Physical point: $\beta^* = 1.53459777$, $\xi(\beta^*) = 7$, $S(\beta^*) = 0.1595$ nats/site, $a = 0.0972$ fm (tree)
- [ ] Register-window counting: $\kappa = 1$ for every $\mathbb{Z}_N$; $\kappa$-family spread $18.85\times$, only $\xi_{\rm kink} = 7/\kappa$ discriminates
