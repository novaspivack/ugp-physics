#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Reference: TE_1.R plan (1_1_TE_1R_PLAN.md)
"""
Probabilistic transputation selector (Definition 4.4) with measurable-selection validation.

Functionality:
- Load branch datasets (Choice Points) describing admissible successor states and MDL losses.
- Apply the PT selection rule: minimize adjudicative cost
      L(S'|S_t) = k_B T log[P(S_t)/P(S')] + lambda_Psi * E_coherence(S')
  subject to microcausality constraints.
- Compare selected frequencies against Born probabilities; compute KL divergence
  and L1 error per branch.
- Export detailed diagnostics to JSON/CSV under results/pt_selector/.

Inputs:
- JSON files conforming to schema:
      {
          "choice_id": str,
          "temperature": float,
          "lambda_psi": float,
          "states": [
              {
                  "state_id": str,
                  "p_born": float,
                  "mdl_loss": float,
                  "coherence_energy": float,
                  "microcausal": bool
              },
              ...
          ]
      }
- Multiple files can be processed in a single run.

Output artifacts (per dataset):
- <choice_id>_summary.json: selected state, selection probabilities, KL & L1 metrics.
- <choice_id>_trials.csv: simulated adjudication trials and empirical frequencies.

Usage:
    python pt_selector.py --input data/pt_cases --n-trials 10000
"""
from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import pandas as pd
except ImportError as exc:  # pragma: no cover
    raise SystemExit("pandas is required for PT selector; install it before running.") from exc

try:
    import numpy as np
except ImportError as exc:  # pragma: no cover
    raise SystemExit("numpy is required for PT selector; install it before running.") from exc

# ---------- Data structures ----------


@dataclass
class BranchState:
    state_id: str
    p_born: float
    mdl_loss: float
    coherence_energy: float
    microcausal: bool


@dataclass
class ChoicePoint:
    choice_id: str
    temperature: float
    lambda_psi: float
    states: List[BranchState]


# ---------- Core PT selector ----------


def load_choice_point(path: Path) -> ChoicePoint:
    data = json.loads(path.read_text())
    states = [
        BranchState(
            state_id=state["state_id"],
            p_born=state["p_born"],
            mdl_loss=state["mdl_loss"],
            coherence_energy=state["coherence_energy"],
            microcausal=state.get("microcausal", True),
        )
        for state in data["states"]
    ]
    return ChoicePoint(
        choice_id=data["choice_id"],
        temperature=data["temperature"],
        lambda_psi=data["lambda_psi"],
        states=states,
    )


def adjudication_cost(state: BranchState, temperature: float, lambda_psi: float) -> float:
    """Compute PT cost (Definition 4.4). P(S_t)/P(S') is encoded via mdl_loss."""
    return k_B * temperature * state.mdl_loss + lambda_psi * state.coherence_energy


k_B = 1.380649e-23  # Boltzmann constant, SI units


def pt_select(choice: ChoicePoint) -> BranchState:
    feasible = [s for s in choice.states if s.microcausal]
    if not feasible:
        raise ValueError(f"No microcausal branches available for {choice.choice_id}")
    costs = [
        (adjudication_cost(s, choice.temperature, choice.lambda_psi), s)
        for s in feasible
    ]
    costs.sort(key=lambda item: item[0])
    return costs[0][1]


def simulate_adjudications(
    choice: ChoicePoint, n_trials: int
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """Simulate stochastic adjudications using PT selector to gather empirical frequencies."""
    selections = []
    for _ in range(n_trials):
        selected = pt_select(choice)
        selections.append(selected.state_id)
    series = pd.Series(selections)
    freq = series.value_counts(normalize=True).to_dict()
    df = pd.DataFrame({"state_id": series})
    return df, freq


def born_distribution(choice: ChoicePoint) -> Dict[str, float]:
    total = sum(s.p_born for s in choice.states if s.microcausal)
    if total <= 0:
        raise ValueError(f"Born probabilities invalid for {choice.choice_id}")
    return {s.state_id: s.p_born / total for s in choice.states if s.microcausal}


def kl_divergence(emp: Dict[str, float], born: Dict[str, float]) -> float:
    eps = 1e-12
    keys = set(emp) | set(born)
    kl = 0.0
    for key in keys:
        p = emp.get(key, eps)
        q = born.get(key, eps)
        kl += p * math.log(p / q)
    return kl


def l1_error(emp: Dict[str, float], born: Dict[str, float]) -> float:
    keys = set(emp) | set(born)
    return sum(abs(emp.get(key, 0.0) - born.get(key, 0.0)) for key in keys) / 2.0


# ---------- CLI ----------


def process_choice(path: Path, output_dir: Path, n_trials: int, seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)

    choice = load_choice_point(path)
    born = born_distribution(choice)
    df_trials, empirical = simulate_adjudications(choice, n_trials)

    selected_state = pt_select(choice)
    summary = {
        "choice_id": choice.choice_id,
        "selected_state": selected_state.state_id,
        "temperature": choice.temperature,
        "lambda_psi": choice.lambda_psi,
        "born_distribution": born,
        "empirical_distribution": empirical,
        "kl_divergence": kl_divergence(empirical, born),
        "l1_error": l1_error(empirical, born),
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / f"{choice.choice_id}_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))

    trials_path = output_dir / f"{choice.choice_id}_trials.csv"
    df_trials.to_csv(trials_path, index=False)

    print(f"[PT] Processed {choice.choice_id}: KL={summary['kl_divergence']:.3e}, L1={summary['l1_error']:.3e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="PT measurable-selection selector.")
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to JSON file or directory containing choice point datasets.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/pt_selector"),
        help="Directory for output summaries/trials (default: results/pt_selector).",
    )
    parser.add_argument(
        "--n-trials",
        type=int,
        default=10000,
        help="Number of simulated adjudication trials per dataset.",
    )
    parser.add_argument("--seed", type=int, default=0, help="Random seed.")
    args = parser.parse_args()

    if args.input.is_file():
        files = [args.input]
    elif args.input.is_dir():
        files = sorted(args.input.glob("*.json"))
    else:
        raise SystemExit(f"Input path {args.input} not found.")

    if not files:
        raise SystemExit("No input datasets found.")

    for file_path in files:
        process_choice(file_path, args.output, args.n_trials, args.seed)


if __name__ == "__main__":
    main()

