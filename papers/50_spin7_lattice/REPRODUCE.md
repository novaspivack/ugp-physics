# REPRODUCE — Paper 50: The Spin-7 Lattice Model

## Requirements

```bash
pip install numpy scipy matplotlib
```

No GPU required (all simulations run on CPU in reasonable time).

## Scripts

All scripts are in `scripts/`. The polynomial is always `(C + R - C*R - L*C*R) % 7`.

### Transfer Matrix Spectral Data (Section 3, Table 1)

```bash
python3 scripts/spin7_transfer_matrix.py
```

Computes the $7 \times 7$ transfer matrix $T[b,c] = \sum_a e^{-\beta p(a,b,c)}$ at
several values of $\beta$ and outputs eigenvalues, spectral gap, correlation length,
and CMCA entropy rate. Expected output: eigenvalues $(10.42, 6.73, 0, 0, 0, 0, -0.67)$
at $\beta = 1$.

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

Verifies the CMCA transfer matrix identity $Z = \mathrm{Tr}(\mathbf{T}^{L_y})$,
the $\mathbb{Z}_3$ symmetry of ground states, and that the global ground states
are exactly $\{0, 1, 5\}$. Also available: `spin7_2d_refined.py` for a refined
2D Monte Carlo scan with hysteresis analysis at additional $\beta$ values.

## Lean Certification

The result $|V(p)(\GF{7})| = 43$ is machine-certified in Lean 4 (zero sorry):

```
Theorem: poly_p_zero_variety_count_gf7
Module:  UgpLean/Universality/Z7InvariantSubsets.lean
Repo:    ugp-lean (https://github.com/novaspivack/ugp-lean)
```

The Lean target `poly_p_uniform_gs_roots` (proving $p(x,x,x) = -x(x-1)(x-5)$ and
GS = $\{0,1,5\}$) is planned for CatAL certification.

## Verification Checklist

- [ ] Transfer matrix eigenvalues at $\beta=1$ match Table 1
- [ ] $\beta_c \approx 0.35$ from $C_V$ peak in FSS scan
- [ ] Hysteresis onset at $\beta_{c,2} \approx 1.7$ for $L=8$
- [ ] Ground states exactly $\{0,1,5\}$ (exhaustive check)
- [ ] $|V(p)| = 43$ (exhaustive count)
