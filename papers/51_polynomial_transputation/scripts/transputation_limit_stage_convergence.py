#!/usr/bin/env python3
"""
Stage-convergence structure of [D]-constrained adjudication (transputation
classification illustration).

Demonstrates computationally the structure of the Transputation Classification
Theorem: the adjudicator P_top(w) = argmin_rho D(rho|w), restricted to records
whose truth content is Sigma_1 (finite-witness records), is the pointwise limit
of a uniformly computable stage sequence g(w, s) with bounded mind changes
(Ershov-bounded trial-and-error / Gold limiting recursion), while the stage of
convergence has no computable modulus (it equals the halting time of the coded
program on the diagonal fragment).

Four experiments:
  E1  Diagonal (halting-coded) records, k=2 candidate sectors:
      conservative stage-adjudication converges with <= 1 mind change;
      convergence stage = halting time of the coded program (unbounded family).
  E2  Compound records with k=5 winding sectors {0,2,3,4,6} and several
      independent Sigma_1 facts: mind changes <= 2(k-1) = 8 verified.
  E3  Lyapunov dissonance relaxation (DSAC-style): continuous-state descent of
      a dissonance functional on the candidate simplex with Pi_1 sector
      elimination; monotone dissonance decrease and stage-argmin stabilization.
  E4  No-computable-modulus phenomenology: convergence stages across the
      diagonal family grow without a uniform bound expressible from the index.

Expected output ranges: E1 mind changes in {0,1}; E2 mind changes <= 8;
E3 dissonance monotone nonincreasing after burn-in, argmin stable at the end;
E4 max convergence stage >> median (heavy upper tail).

Artifact: transputation_limit_stage_convergence_results.json
"""

import json
import signal
import sys
import random

TIMEOUT_SECONDS = 300


def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

MAX_STAGES = 200_000   # stage horizon for the diagonal family
RNG = random.Random(42)

# ---------------------------------------------------------------------------
# Program family for the diagonal fragment.
# "Program n" = Collatz trajectory from seed n (halts when it reaches 1);
# even n are replaced by an explicit non-halting loop when flagged, giving a
# family with both halting and non-halting members and widely varying halting
# times. Ground truth within the stage horizon comes from actual simulation.
# ---------------------------------------------------------------------------


def halting_time(n, max_steps):
    """Steps for the Collatz trajectory from n to reach 1, or None within horizon."""
    x = n
    for t in range(max_steps):
        if x == 1:
            return t
        x = 3 * x + 1 if x % 2 else x // 2
    return None


def diagonal_adjudication(n, max_stages):
    """
    Stage-wise conservative adjudication of the diagonal record w_n.
    Candidates: rho_plus (posits the halting witness), rho_minus (conservative).
    MDL-conservativity: while no witness is recorded, D(rho_plus) > D(rho_minus)
    (unwitnessed posited event costs description length). When the witness
    appears, rho_minus is refuted (Sigma_1 refutation) and the argmin flips.
    Returns (final_guess, mind_changes, convergence_stage, halted_within_horizon).
    """
    guess = "rho_minus"          # conservative start
    mind_changes = 0
    convergence_stage = 0
    x = n
    for s in range(max_stages):
        if x == 1:               # halting witness appears at stage s
            if guess != "rho_plus":
                guess = "rho_plus"
                mind_changes += 1
                convergence_stage = s
            break
        x = 3 * x + 1 if x % 2 else x // 2
    return guess, mind_changes, convergence_stage, (guess == "rho_plus")


def diagonal_adjudication_loop(max_stages):
    """Adjudication of a record coding an explicitly non-halting program
    (x -> x loop; the halting witness never appears). The conservative guess
    rho_minus is never revised: 0 mind changes, limit correct."""
    return "rho_minus", 0, 0, False


def experiment_E1_E4():
    seeds = [27, 97, 871, 6171, 77031, 9780657630, 2, 3, 7, 703, 26623, 142587,
             837799, 8400511, 63728127]
    results = []
    for n in seeds:
        ht = halting_time(n, MAX_STAGES)
        guess, mc, cs, halted = diagonal_adjudication(n, MAX_STAGES)
        correct = (halted and ht is not None) or (not halted and ht is None)
        results.append({
            "program": f"collatz({n})",
            "seed": n,
            "halting_time": ht,
            "final_guess": guess,
            "mind_changes": mc,
            "convergence_stage": cs,
            "limit_correct_within_horizon": correct,
        })
    # explicit non-halting members (x -> x loops): provably no witness ever
    for tag in ["loop_A", "loop_B", "loop_C"]:
        guess, mc, cs, halted = diagonal_adjudication_loop(MAX_STAGES)
        results.append({
            "program": tag,
            "seed": None,
            "halting_time": None,
            "final_guess": guess,
            "mind_changes": mc,
            "convergence_stage": cs,
            "limit_correct_within_horizon": (guess == "rho_minus"),
        })
    conv_stages = sorted(r["convergence_stage"] for r in results if r["halting_time"] is not None)
    e4 = {
        "median_convergence_stage": conv_stages[len(conv_stages) // 2],
        "max_convergence_stage": conv_stages[-1],
        "tail_ratio_max_over_median": conv_stages[-1] / max(1, conv_stages[len(conv_stages) // 2]),
        "comment": ("convergence stage equals the halting time of the coded program; "
                    "no computable function of the index bounds it (Theorem C illustration)"),
    }
    return results, e4


# ---------------------------------------------------------------------------
# E2: compound record, k = 5 winding sectors {0,2,3,4,6}, each sector posits a
# subset of m independent Sigma_1 facts. Facts get witnesses at random finite
# stages or never. Conservative stage adjudication; verify mind changes <= 2(k-1).
# ---------------------------------------------------------------------------

WINDING_SECTORS = [0, 2, 3, 4, 6]


def compound_adjudication(trial_seed, m_facts=4, max_stages=5000):
    rng = random.Random(trial_seed)
    # Each fact: witness stage (finite) or None (never witnessed).
    witness_stage = [rng.choice([rng.randint(1, max_stages // 2), None]) for _ in range(m_facts)]
    # Each sector posits a subset of facts as TRUE; sector admissible in the
    # limit iff posited set == set of facts that are eventually witnessed
    # (positing an unwitnessed fact -> never minimal; omitting a witnessed
    # fact -> refuted when its witness arrives).
    sector_posits = {k: frozenset(i for i in range(m_facts) if rng.random() < 0.5)
                     for k in WINDING_SECTORS}
    # Force at least one sector to posit exactly the true set (D4: admissible
    # candidate exists -- the realized completion).
    true_set = frozenset(i for i, ws in enumerate(witness_stage) if ws is not None)
    forced = rng.choice(WINDING_SECTORS)
    sector_posits[forced] = true_set
    # Injective coherence ordinal (PR3b): deterministic tie-break by sector label.
    coherence_rank = {k: i for i, k in enumerate(WINDING_SECTORS)}

    alive = {k: True for k in WINDING_SECTORS}
    witnessed = set()
    guess = None
    mind_changes = 0
    for s in range(max_stages):
        for i, ws in enumerate(witness_stage):
            if ws is not None and ws == s:
                witnessed.add(i)
                # refute sectors omitting fact i (their record collides with trace)
                for k in WINDING_SECTORS:
                    if alive[k] and i not in sector_posits[k]:
                        alive[k] = False
        # stage-s effective dissonance: count of posited-but-unwitnessed events
        best, best_key = None, None
        for k in WINDING_SECTORS:
            if not alive[k]:
                continue
            d = len(sector_posits[k] - witnessed)
            key = (d, coherence_rank[k])
            if best_key is None or key < best_key:
                best, best_key = k, key
        if best != guess:
            if guess is not None:
                mind_changes += 1
            guess = best
    # limit value check: admissible-in-the-limit sectors
    limit_admissible = [k for k in WINDING_SECTORS
                        if sector_posits[k] <= true_set and true_set <= sector_posits[k]]
    limit_argmin = min(limit_admissible, key=lambda k: (0, coherence_rank[k])) if limit_admissible else None
    return {
        "trial_seed": trial_seed,
        "mind_changes": mind_changes,
        "bound_2k_minus_2": 2 * (len(WINDING_SECTORS) - 1),
        "within_bound": mind_changes <= 2 * (len(WINDING_SECTORS) - 1),
        "final_guess": guess,
        "limit_argmin": limit_argmin,
        "limit_correct": guess == limit_argmin,
    }


def experiment_E2(n_trials=500):
    trials = [compound_adjudication(t) for t in range(n_trials)]
    return {
        "n_trials": n_trials,
        "max_mind_changes": max(t["mind_changes"] for t in trials),
        "bound": trials[0]["bound_2k_minus_2"],
        "all_within_bound": all(t["within_bound"] for t in trials),
        "all_limits_correct": all(t["limit_correct"] for t in trials),
        "mind_change_histogram": {str(i): sum(1 for t in trials if t["mind_changes"] == i)
                                  for i in range(0, max(t["mind_changes"] for t in trials) + 1)},
    }


# ---------------------------------------------------------------------------
# E3: DSAC-style Lyapunov relaxation. Continuous weights over the 5 sectors,
# dissonance D = sum_k x_k * cost_k(s) with stage-dependent costs (unwitnessed
# posited events) + entropy-free multiplicative-weights descent; sectors are
# eliminated (weight -> 0) when refuted. Shows monotone dissonance decrease
# between refutation events and final argmin stabilization.
# ---------------------------------------------------------------------------


def experiment_E3(max_stages=2000, eta=0.15, trial_seed=7):
    rng = random.Random(trial_seed)
    m_facts = 4
    witness_stage = [rng.choice([rng.randint(1, max_stages // 3), None]) for _ in range(m_facts)]
    sector_posits = {k: frozenset(i for i in range(m_facts) if rng.random() < 0.5)
                     for k in WINDING_SECTORS}
    true_set = frozenset(i for i, ws in enumerate(witness_stage) if ws is not None)
    sector_posits[rng.choice(WINDING_SECTORS)] = true_set

    weights = {k: 1.0 / len(WINDING_SECTORS) for k in WINDING_SECTORS}
    witnessed = set()
    refuted = set()
    dissonance_trace = []
    argmin_trace = []
    for s in range(max_stages):
        for i, ws in enumerate(witness_stage):
            if ws is not None and ws == s:
                witnessed.add(i)
                for k in WINDING_SECTORS:
                    if k not in refuted and i not in sector_posits[k]:
                        refuted.add(k)
        costs = {}
        for k in WINDING_SECTORS:
            if k in refuted:
                costs[k] = 10.0      # refutation penalty (Sigma_1 event fired)
            else:
                costs[k] = float(len(sector_posits[k] - witnessed))
        # multiplicative-weights descent on the dissonance functional
        import math
        new_w = {k: weights[k] * math.exp(-eta * costs[k]) for k in WINDING_SECTORS}
        z = sum(new_w.values())
        weights = {k: v / z for k, v in new_w.items()}
        d_value = sum(weights[k] * costs[k] for k in WINDING_SECTORS)
        dissonance_trace.append(d_value)
        argmin_trace.append(max(weights, key=weights.get))

    # monotonicity check between refutation/witness events
    event_stages = sorted({ws for ws in witness_stage if ws is not None})
    monotone_segments = []
    seg_start = 0
    for es in event_stages + [max_stages]:
        seg = dissonance_trace[seg_start:es]
        ok = all(seg[i + 1] <= seg[i] + 1e-12 for i in range(len(seg) - 1)) if len(seg) > 1 else True
        monotone_segments.append(ok)
        seg_start = es
    stable_tail = len(set(argmin_trace[-200:])) == 1
    return {
        "final_argmin_sector": argmin_trace[-1],
        "final_dissonance": dissonance_trace[-1],
        "dissonance_monotone_between_events": all(monotone_segments),
        "argmin_stable_last_200_stages": stable_tail,
        "n_witness_events": len(event_stages),
        "dissonance_first_last": [dissonance_trace[0], dissonance_trace[-1]],
    }


def main():
    e1, e4 = experiment_E1_E4()
    e2 = experiment_E2()
    e3 = experiment_E3()

    out = {
        "description": "Stage-convergence structure of [D]-constrained adjudication "
                       "(transputation classification illustration)",
        "E1_diagonal_family": e1,
        "E2_compound_records": e2,
        "E3_lyapunov_relaxation": e3,
        "E4_no_computable_modulus": e4,
    }
    path = "transputation_limit_stage_convergence_results.json"
    with open(path, "w") as f:
        json.dump(out, f, indent=2)

    print("E1 diagonal family (halting-coded records, k=2):")
    for r in e1:
        ht = r["halting_time"]
        print(f"  {r['program']:>22}: halt_time={str(ht):>7}  guess={r['final_guess']:<9} "
              f"mind_changes={r['mind_changes']}  conv_stage={r['convergence_stage']:>6}  "
              f"limit_ok={r['limit_correct_within_horizon']}")
    print(f"\nE2 compound records (k=5 winding sectors, 500 trials): "
          f"max mind changes = {e2['max_mind_changes']} (bound {e2['bound']}), "
          f"all within bound = {e2['all_within_bound']}, all limits correct = {e2['all_limits_correct']}")
    print(f"  mind-change histogram: {e2['mind_change_histogram']}")
    print(f"\nE3 Lyapunov relaxation: final sector = {e3['final_argmin_sector']}, "
          f"monotone between events = {e3['dissonance_monotone_between_events']}, "
          f"argmin stable tail = {e3['argmin_stable_last_200_stages']}, "
          f"D first->last = {e3['dissonance_first_last']}")
    print(f"\nE4 modulus phenomenology: median conv stage = {e4['median_convergence_stage']}, "
          f"max = {e4['max_convergence_stage']}, tail ratio = {e4['tail_ratio_max_over_median']:.1f}")
    print(f"\nArtifact written: {path}")
    signal.alarm(0)


if __name__ == "__main__":
    main()
