# Three-Tape CMCA — Reproducibility Scripts (P45)

Unified implementation of the three-tape Chiral Minkowski Cellular Automaton
(Rule 110 ⊕ Rule 124 ⊕ inner τ_c, shared outer τ_c)³ with nine canonical verifications.

## Requirements

- Python 3.10+
- `numpy`, `scipy`
- Mathematica ≥ 12.0 or Wolfram Engine (optional cross-check)

## Python

From this directory:

```bash
cd papers/45_three_tape_cmca/scripts
python3 run_all_verifications.py
```

Options:

```bash
python3 run_all_verifications.py --out my_report.json
python3 run_all_verifications.py --quiet
```

Exit code `0` if all nine verifications pass; `1` otherwise.
Report is written atomically to `verification_report.json` (or `--out` path).

### Modules

| File | Role |
|------|------|
| `three_tape_cmca.py` | Core `ThreeTapeCMCA` class |
| `initial_conditions.py` | Vacuum, glider, gravity source, soliton ICs |
| `verification_suite.py` | Nine verification functions |
| `run_all_verifications.py` | CLI entry point |

### Use in code

```python
from three_tape_cmca import ThreeTapeCMCA
from initial_conditions import ic_glider_x

cmca = ThreeTapeCMCA(L=400, native_geodesic=True)
ic_glider_x(cmca)
cmca.run(T=500)
print(cmca.inner_tau_c_rate("x"))
```

Tape length `L` is arbitrary; the period-14 ether tile is repeated and truncated to `L`.

## Mathematica / Wolfram Engine

```bash
WOLFRAM="/Applications/Wolfram Engine.app/Contents/MacOS/WolframKernel"
"$WOLFRAM" -script ThreeTapeCMCA.wl
```

On macOS with full Mathematica:

```bash
/Applications/Mathematica.app/Contents/MacOS/WolframKernel -script ThreeTapeCMCA.wl
```

The script runs verifications **1, 3, and 8** inline (SR gate rate, Z₇ vertices, kink mass).
Full nine-verification suite is Python-only (`run_all_verifications.py`), including gravity
probe dynamics (verification 4).

**Wolfram Engine path (this machine):**
`/Applications/Wolfram Engine.app/Contents/MacOS/WolframKernel`

## Verification summary

1. SR time dilation — inner τ_c rate ≈ 0.382
2. V-A chirality — Rule 110 vs 124 opposite drift
3. SM vertices — 33 Z₇ conservation checks
4. Gravity — native geodesic and explicit Poisson modes
5. Gorard vacuum — κ ≈ 0 on ether
6. Bell — CHSH S > 2
7. Baryon number — conserved at vertices
8. Kink mass — (8/49) m_τ ≈ 290.1 MeV
9. Soliton — localized excitation (max active < 30)

## Parameters (defaults)

- `L=400`, `native_geodesic=True`, `alpha=0.1`, `base_rate=0.6`
- Gravity source: σ=5, Poisson reg=1.0
- Probe: `T_probe=300`, `N_avg=8`, impact parameters `{30,40,50,70,100}`
