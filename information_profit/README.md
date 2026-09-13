# Information Profit Threshold — Code Companion

This directory contains the code companion to the paper:

> **The Information Profit Principle: Derivation and Computational Validation of a Threshold Condition for Self-Maintaining Reflexive Systems**
> Nova Spivack, 2026

The code implements and validates the Information Profit Threshold (IPT) derivation
and its three computational validation experiments.

---

## What This Code Does

A reflexive self-maintaining system must generate information structure faster than
it dissipates it. The Information Profit Threshold (IPT) is a sharp dimensionless
value derived from the structural requirements of self-consistency and thermodynamic
accounting for such systems:

    IPT = 1 + Lambda / 2,    Lambda = ln(phi) / ln(2*pi)  ≈  0.261830

where phi = (1 + sqrt(5)) / 2 is the golden ratio. Numerically, IPT ≈ 1.130915.

A system whose generative-to-drain ratio rho = G/D satisfies rho > IPT has an energy
budget sufficient for sustaining coherent self-referential processing. A system with
rho ≤ IPT cannot.

---

## Three Components

### 1. Analytical Derivation Verification (`verify_ipt_derivation.py`)

A standalone script that computes phi, Lambda, and IPT from closed-form expressions,
prints the values to 10 decimal places, verifies IPT is within tolerance of the
expected value, and saves results to `results/ipt_derivation_verification.json`.

This is fully self-contained and requires only numpy.

### 2. TE1.H-Style 2D Field Simulation

Located in `MFRR/TE_1_VALIDATION_PROGRAM/TE_1.H_LEVIN/`.

Implements a 64x64 2D spatial field simulator that tests three parameter regimes:
- Subcritical (rho ≈ 0.80): coherence decays
- Supercritical (rho ≈ 1.40): coherence grows
- High-noise subcritical (rho < 1.00): coherence decays despite high generation rate

Coherence is measured as 1 minus the gzip compression ratio of the field state.

### 3. TE2.1-Style Evolutionary Agent Experiment

Located in `MFRR/TE_2_Advanced_Explorations/TE_2_1_Recursive_Fidelity_Experiments/`.

Evolves a population of neural agents in a 2D resource environment. Each agent
accumulates a profit ratio over its lifetime. Selection pressure favors agents
maintaining positive information profit. Over 124 genesis runs, 15 produce final
profit ratios exceeding the IPT.

---

## Installation

Python 3.9 or later is required.

```
pip install -r requirements.txt
```

Dependencies: numpy, scipy, matplotlib.

---

## How to Run

### Derivation verification (this directory):

```
python verify_ipt_derivation.py
```

Output is printed to stdout and saved to `results/ipt_derivation_verification.json`.

### TE1.H simulation:

```
cd ../MFRR/TE_1_VALIDATION_PROGRAM/TE_1.H_LEVIN/
python run_te1h.py
```

### TE2.1 evolutionary agents:

```
cd ../MFRR/TE_2_Advanced_Explorations/TE_2_1_Recursive_Fidelity_Experiments/
python MFRR_Evolutionary_Genesis.py
python MFRR_Evolutionary_Sweep.py
```

### E4 energy model consistency check (pre-computed; re-run to regenerate):

```
cd ../MFRR/
python E4_reflexive_landauer_check.py
```

---

## What Outputs Are Produced

| Script | Output |
|--------|--------|
| `verify_ipt_derivation.py` | `results/ipt_derivation_verification.json`, stdout summary |
| TE1.H `run_te1h.py` | `results/csv/*.csv` coherence histories; `figs/` plots |
| TE2.1 `MFRR_Evolutionary_Genesis.py` | `results/MFRR_Evolutionary_Genesis_v2_*.json` |
| TE2.1 `MFRR_Evolutionary_Sweep.py` | `results/MFRR_Evolutionary_Sweep_*.json` |
| E4 `E4_reflexive_landauer_check.py` | `MFRR/E4_reflexive_landauer_results.json` |

---

## Scope and Limitations

All experiments are simulation-only internal consistency tests. They confirm that
the computational implementations behave in accordance with the IPT prediction within
the model framework. They are not independent physical experiments and do not
constitute empirical validation in biological or economic systems.

Interpretive connections to biological metabolism or economic sustainability, discussed
in the companion paper, are conjectural analogies and are not supported by data
produced by this code.
