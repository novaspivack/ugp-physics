"""
Direction 1 — Genetic Code Phase 4:
  Completeness + Competitor Analysis + GTE Fixed-Point Relaxation

Architecture:
  - NumPy vectorized batch scorer for null test and top-k search (fast)
  - Incremental RelaxationState for GTE coordinate-ascent (incremental O(25) per swap)

The GTE relaxation is conceptually a DSAC (Delta Self-Adjudicative Computation,
NEMS Paper 77) process: relaxation to coherence in a reflexive constraint system.
The standard genetic code is predicted to be the unique coherence point (fixed point)
of the 4-criterion viability landscape over wobble-admissible codon assignments.
"""

from __future__ import annotations
import random
import statistics
from collections import defaultdict
from typing import Dict, List, Tuple, Set, Optional

import numpy as np

from codon_sieve import (
    CODONS, CODON_INDEX, AMINO_ACIDS, AA_INDEX, N_OUTCOMES, BASES,
    STANDARD_CODE, WOBBLE_CLASSES, NEIGHBORS,
    POLAR_REQUIREMENT,
)
from codon_sieve_phase2 import PREBIOTIC_ACCESSIBILITY
from codon_sieve_phase3 import STOP_OUTCOMES, CHEM_CLASS

# ---------------------------------------------------------------------------
# 0. Static precomputed arrays (built once at import)
# ---------------------------------------------------------------------------

N_CLASSES = len(WOBBLE_CLASSES)
CLASS_SIZES = np.array([len(cls) for cls in WOBBLE_CLASSES], dtype=np.float64)

# Outcome property arrays [N_OUTCOMES]
PR_ARR    = np.array([POLAR_REQUIREMENT[AMINO_ACIDS[i]] for i in range(N_OUTCOMES)])
ACC_ARR   = np.array([PREBIOTIC_ACCESSIBILITY[AMINO_ACIDS[i]] for i in range(N_OUTCOMES)])
CHEM_ARR  = np.array([CHEM_CLASS[AMINO_ACIDS[i]] for i in range(N_OUTCOMES)])
STOP_ARR  = np.array([i in STOP_OUTCOMES for i in range(N_OUTCOMES)], dtype=bool)
SENSE_ARR = ~STOP_ARR

SENSE_AA_OUTCOMES: Set[int] = {i for i in range(N_OUTCOMES) if SENSE_ARR[i]}

# Codon-to-class mapping
CODON_TO_CLASS = np.zeros(64, dtype=np.int32)
for _k, _cls in enumerate(WOBBLE_CLASSES):
    for _c in _cls:
        CODON_TO_CLASS[_c] = _k

# Cross-class neighbor pairs as arrays for vectorized scoring
# Each entry: (class_a, class_b) where class_a < class_b (deduplicated)
_pair_a, _pair_b = [], []
for _k, _cls in enumerate(WOBBLE_CLASSES):
    _cls_set = set(_cls)
    for _ci in _cls:
        for _nb in NEIGHBORS[_ci]:
            _nb_cls = CODON_TO_CLASS[_nb]
            if _nb_cls > _k:  # avoid double-counting
                _pair_a.append(_k)
                _pair_b.append(_nb_cls)

PAIR_A = np.array(_pair_a, dtype=np.int32)  # shape [n_pairs]
PAIR_B = np.array(_pair_b, dtype=np.int32)  # shape [n_pairs]
N_PAIRS = len(PAIR_A)

# Which pairs involve sense (non-stop) codons on BOTH sides depends on assignment
# — handled at score time.

# Per-class inter-pairs for incremental relaxation
INTER_PAIRS: List[List[Tuple[int, int, int]]] = []  # (codon, nb_class, nb_codon)
for _k, _cls in enumerate(WOBBLE_CLASSES):
    _cls_set = set(_cls)
    _inter = []
    for _ci in _cls:
        for _nb in NEIGHBORS[_ci]:
            _nb_k = CODON_TO_CLASS[_nb]
            if _nb_k != _k:
                _inter.append((_ci, int(_nb_k), _nb))
    INTER_PAIRS.append(_inter)

W_ERR, W_ACC, W_STOP, W_CLUS = 0.4, 0.2, 0.2, 0.2

# ---------------------------------------------------------------------------
# 1. Fast vectorized batch scorer
# ---------------------------------------------------------------------------


# Precomputed index arrays for fully vectorized filter + stop scoring
_SENSE_OUTCOMES_ARR = np.array(sorted(SENSE_AA_OUTCOMES), dtype=np.int32)  # [20]
_STOP_OUTCOMES_ARR  = np.array(sorted(STOP_OUTCOMES),      dtype=np.int32)  # [3]


def score_batch_fast(assignments: np.ndarray) -> np.ndarray:
    """
    Fully vectorized scorer. No Python loops over codes.
    assignments: int32 [batch, N_CLASSES]
    Returns: float64 [batch]
    """
    out_a  = assignments[:, PAIR_A]   # [batch, n_pairs]
    out_b  = assignments[:, PAIR_B]
    stop_a = STOP_ARR[out_a]
    stop_b = STOP_ARR[out_b]
    sense  = ~stop_a & ~stop_b

    # --- Error ---
    pr_diff   = np.abs(PR_ARR[out_a] - PR_ARR[out_b])
    err_sums  = (pr_diff * sense).sum(axis=1)
    pair_cnt  = sense.sum(axis=1).astype(np.float64)
    err_score = np.where(pair_cnt > 0, err_sums / pair_cnt, 0.0)

    # --- Accessibility ---
    acc_score = (ACC_ARR[assignments] * CLASS_SIZES).sum(axis=1) / 64.0

    # --- Stop robustness (fully vectorized) ---
    # [batch, N_CLASSES, 3] — does each class carry each stop outcome?
    stop_present = (assignments[:, :, None] == _STOP_OUTCOMES_ARR[None, None, :])
    n_distinct_stops = stop_present.any(axis=1).sum(axis=1)   # [batch]
    stop_score = np.where(n_distinct_stops >= 2, 1.0,
                 np.where(n_distinct_stops == 1, 0.5, 0.0))

    # --- Chemical clustering ---
    same = (CHEM_ARR[out_a] == CHEM_ARR[out_b]) & sense
    clus_score = same.sum(axis=1).astype(np.float64) / np.maximum(pair_cnt, 1.0)

    return (-W_ERR * err_score + W_ACC * acc_score +
            W_STOP * stop_score + W_CLUS * clus_score)


def filter_complete_2stop(asns: np.ndarray) -> np.ndarray:
    """
    Fully vectorized filter: returns bool mask [batch] where each row is
    complete (all 20 sense AAs) and has ≥2 distinct stop outcomes.
    asns: int32 [batch, N_CLASSES]
    """
    # Completeness: does every sense AA outcome appear in at least one class?
    # [batch, N_CLASSES, 20] → .any(axis=1) → [batch, 20] → .all(axis=1) → [batch]
    complete = (asns[:, :, None] == _SENSE_OUTCOMES_ARR[None, None, :]).any(axis=1).all(axis=1)

    # 2-stop: ≥2 distinct stop outcomes
    # [batch, N_CLASSES, 3] → .any(axis=1) → [batch, 3] → .sum(axis=1) → [batch]
    n_stops = (asns[:, :, None] == _STOP_OUTCOMES_ARR[None, None, :]).any(axis=1).sum(axis=1)
    two_stops = n_stops >= 2

    return complete & two_stops


def is_complete_arr(asn: np.ndarray) -> bool:
    return bool(filter_complete_2stop(asn[None])[0])

def has_2stops_arr(asn: np.ndarray) -> bool:
    n = (asn[None, :, None] == _STOP_OUTCOMES_ARR[None, None, :]).any(axis=1).sum()
    return bool(n >= 2)

# ---------------------------------------------------------------------------
# 2. Incremental RelaxationState for GTE coordinate ascent
# ---------------------------------------------------------------------------

class RelaxationState:
    """Maintains all score components incrementally. Each swap is O(|inter_pairs_k|)."""

    def __init__(self, asn: List[int]):
        self.asn = list(asn)
        self._rebuild()

    def _rebuild(self):
        a = self.asn
        # Accessibility
        self._acc_sum = sum(ACC_ARR[a[k]] * CLASS_SIZES[k] for k in range(N_CLASSES))
        # Error
        self._err_num, self._err_den = 0.0, 0
        for k in range(N_CLASSES):
            if STOP_ARR[a[k]]:
                continue
            pr_k = PR_ARR[a[k]]
            for _, nb_k, _ in INTER_PAIRS[k]:
                if STOP_ARR[a[nb_k]]:
                    continue
                self._err_num += abs(pr_k - PR_ARR[a[nb_k]])
                self._err_den += 1
        # Stops
        self._stop_counts: Dict[int, int] = defaultdict(int)
        for k in range(N_CLASSES):
            if STOP_ARR[a[k]]:
                self._stop_counts[a[k]] += 1
        # Clustering
        self._clus_same, self._clus_total = 0, 0
        for k in range(N_CLASSES):
            if STOP_ARR[a[k]]:
                continue
            c_k = CHEM_ARR[a[k]]
            for _, nb_k, _ in INTER_PAIRS[k]:
                if STOP_ARR[a[nb_k]]:
                    continue
                self._clus_total += 1
                if CHEM_ARR[a[nb_k]] == c_k:
                    self._clus_same += 1
        # Sense AA count
        self._sense_counts: Dict[int, int] = defaultdict(int)
        for k in range(N_CLASSES):
            if SENSE_ARR[a[k]]:
                self._sense_counts[a[k]] += 1

    def score(self) -> float:
        err  = self._err_num / self._err_den if self._err_den else 0.0
        acc  = self._acc_sum / 64.0
        n_s  = len(self._stop_counts)
        stop = 1.0 if n_s >= 2 else (0.5 if n_s == 1 else 0.0)
        clus = self._clus_same / self._clus_total if self._clus_total else 0.0
        return -W_ERR * err + W_ACC * acc + W_STOP * stop + W_CLUS * clus

    def is_complete(self) -> bool:
        return len(self._sense_counts) == 20

    def n_stops(self) -> int:
        return len(self._stop_counts)

    def _delta(self, k: int, new: int) -> Tuple[float, bool, bool]:
        """Return (score_delta, will_complete, will_have_2stops) for trial swap."""
        old = self.asn[k]
        if new == old:
            return 0.0, self.is_complete(), self.n_stops() >= 2

        # --- Accessibility delta ---
        d_acc = (float(ACC_ARR[new]) - float(ACC_ARR[old])) * CLASS_SIZES[k] / 64.0

        # --- Error delta ---
        old_stop = bool(STOP_ARR[old])
        new_stop = bool(STOP_ARR[new])
        pr_old, pr_new = float(PR_ARR[old]), float(PR_ARR[new])
        d_err_num, d_err_den = 0.0, 0
        for _, nb_k, _ in INTER_PAIRS[k]:
            nb_out = self.asn[nb_k]
            nb_stop = bool(STOP_ARR[nb_out])
            pr_nb = float(PR_ARR[nb_out])
            was = not old_stop and not nb_stop
            will = not new_stop and not nb_stop
            if was:
                d_err_num -= abs(pr_old - pr_nb)
                d_err_den -= 1
            if will:
                d_err_num += abs(pr_new - pr_nb)
                d_err_den += 1
        new_err_num = self._err_num + d_err_num
        new_err_den = self._err_den + d_err_den
        new_err = new_err_num / new_err_den if new_err_den else 0.0
        old_err = self._err_num / self._err_den if self._err_den else 0.0

        # --- Stop delta ---
        sc = dict(self._stop_counts)
        if old_stop:
            sc[old] = sc.get(old, 0) - 1
            if sc[old] <= 0:
                del sc[old]
        if new_stop:
            sc[new] = sc.get(new, 0) + 1
        new_n_s = len(sc)
        old_stop_score = 1.0 if len(self._stop_counts) >= 2 else (0.5 if len(self._stop_counts) == 1 else 0.0)
        new_stop_score = 1.0 if new_n_s >= 2 else (0.5 if new_n_s == 1 else 0.0)

        # --- Clustering delta ---
        c_old = int(CHEM_ARR[old])
        c_new = int(CHEM_ARR[new])
        d_clus_s, d_clus_t = 0, 0
        for _, nb_k, _ in INTER_PAIRS[k]:
            nb_out = self.asn[nb_k]
            nb_stop = bool(STOP_ARR[nb_out])
            c_nb = int(CHEM_ARR[nb_out])
            if old_stop or nb_stop:
                was_s, was_t = 0, 0
            else:
                was_t = 1
                was_s = 1 if c_nb == c_old else 0
            if new_stop or nb_stop:
                will_s, will_t = 0, 0
            else:
                will_t = 1
                will_s = 1 if c_nb == c_new else 0
            d_clus_s += will_s - was_s
            d_clus_t += will_t - was_t
        new_clus_same  = self._clus_same  + d_clus_s
        new_clus_total = self._clus_total + d_clus_t
        new_clus = new_clus_same / new_clus_total if new_clus_total else 0.0
        old_clus = self._clus_same / self._clus_total if self._clus_total else 0.0

        # --- Completeness and stop check ---
        scc = dict(self._sense_counts)
        if SENSE_ARR[old]:
            scc[old] = scc.get(old, 0) - 1
            if scc[old] <= 0:
                del scc[old]
        if SENSE_ARR[new]:
            scc[new] = scc.get(new, 0) + 1
        will_complete  = len(scc) == 20
        will_2stops    = new_n_s >= 2

        d_score = (W_ERR * (old_err - new_err) +
                   W_ACC * d_acc +
                   W_STOP * (new_stop_score - old_stop_score) +
                   W_CLUS * (new_clus - old_clus))
        return d_score, will_complete, will_2stops

    def apply(self, k: int, new: int):
        """Apply the swap in O(|inter_pairs_k|)."""
        old = self.asn[k]
        if new == old:
            return
        old_stop = bool(STOP_ARR[old])
        new_stop = bool(STOP_ARR[new])
        pr_old, pr_new = float(PR_ARR[old]), float(PR_ARR[new])
        c_old, c_new   = int(CHEM_ARR[old]), int(CHEM_ARR[new])

        for _, nb_k, _ in INTER_PAIRS[k]:
            nb_out  = self.asn[nb_k]
            nb_stop = bool(STOP_ARR[nb_out])
            pr_nb   = float(PR_ARR[nb_out])
            c_nb    = int(CHEM_ARR[nb_out])
            was_sense = not old_stop and not nb_stop
            will_sense = not new_stop and not nb_stop
            if was_sense:
                self._err_num -= abs(pr_old - pr_nb)
                self._err_den -= 1
                self._clus_total -= 1
                if c_nb == c_old:
                    self._clus_same -= 1
            if will_sense:
                self._err_num += abs(pr_new - pr_nb)
                self._err_den += 1
                self._clus_total += 1
                if c_nb == c_new:
                    self._clus_same += 1

        self._acc_sum += (float(ACC_ARR[new]) - float(ACC_ARR[old])) * CLASS_SIZES[k]

        if old_stop:
            self._stop_counts[old] -= 1
            if self._stop_counts[old] <= 0:
                del self._stop_counts[old]
        if new_stop:
            self._stop_counts[new] = self._stop_counts.get(new, 0) + 1

        if SENSE_ARR[old]:
            self._sense_counts[old] -= 1
            if self._sense_counts[old] <= 0:
                del self._sense_counts[old]
        if SENSE_ARR[new]:
            self._sense_counts[new] = self._sense_counts.get(new, 0) + 1

        self.asn[k] = new


# ---------------------------------------------------------------------------
# 3. GTE Relaxation using RelaxationState
# ---------------------------------------------------------------------------

def gte_relax(start: List[int], max_steps: int = 500) -> Tuple[List[int], List[float], int]:
    state = RelaxationState(list(start))
    history = [state.score()]

    for _ in range(max_steps):
        best_gain, best_k, best_new = 1e-9, -1, -1
        for k in range(N_CLASSES):
            for new in range(N_OUTCOMES):
                if new == state.asn[k]:
                    continue
                gain, wc, ws = state._delta(k, new)
                if not wc or not ws:
                    continue
                if gain > best_gain:
                    best_gain, best_k, best_new = gain, k, new
        if best_k == -1:
            break
        state.apply(best_k, best_new)
        history.append(state.score())

    return state.asn, history, len(history) - 1

# ---------------------------------------------------------------------------
# 4. Helpers
# ---------------------------------------------------------------------------

STD_ASN = [STANDARD_CODE[next(iter(WOBBLE_CLASSES[k]))]
           for k in range(N_CLASSES)]

def random_asns_numpy(n: int, rng_state: np.random.Generator) -> np.ndarray:
    return rng_state.integers(0, N_OUTCOMES, size=(n, N_CLASSES), dtype=np.int32)


def generate_complete_batch(n: int, rng: np.random.Generator) -> np.ndarray:
    """
    Generate n complete+2-stop assignments by CONSTRUCTION (no rejection).

    Strategy: for each code, assign all 20 sense AAs to distinct classes,
    then assign 2 distinct stop outcomes to 2 more classes,
    then fill remaining classes with random outcomes.
    This guarantees completeness and 2-stop property.

    The resulting distribution is NOT uniform over all complete+2-stop codes,
    but is a valid null distribution for testing whether the standard code is
    exceptional within the complete+2-stop subspace.
    """
    SENSE_LIST = np.array(sorted(SENSE_AA_OUTCOMES), dtype=np.int32)   # [20]
    STOP_LIST  = np.array(sorted(STOP_OUTCOMES),      dtype=np.int32)   # [3]
    N_SENSE, N_STOP = len(SENSE_LIST), len(STOP_LIST)
    N_FREE = N_CLASSES - N_SENSE - 2  # classes after sense+stop assignment

    result = np.empty((n, N_CLASSES), dtype=np.int32)

    for i in range(n):
        asn = np.empty(N_CLASSES, dtype=np.int32)
        perm = rng.permutation(N_CLASSES)

        # Assign all 20 sense AAs to the first 20 permuted classes
        sense_perm = rng.permutation(N_SENSE)
        asn[perm[:N_SENSE]] = SENSE_LIST[sense_perm]

        # Assign 2 distinct stops to the next 2 classes
        stop_2 = rng.choice(N_STOP, size=2, replace=False)
        asn[perm[N_SENSE:N_SENSE+2]] = STOP_LIST[stop_2]

        # Fill remaining classes with random outcomes (any)
        if N_FREE > 0:
            asn[perm[N_SENSE+2:]] = rng.integers(0, N_OUTCOMES, size=N_FREE, dtype=np.int32)

        result[i] = asn

    return result

# ---------------------------------------------------------------------------
# 5. Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("DIRECTION 1 — GENETIC CODE PHASE 4 (NumPy + incremental)")
    print("=" * 70)
    print()

    # Validate incremental state against known standard code score
    from codon_sieve_phase3 import full_viability_score
    std_ref = full_viability_score(STANDARD_CODE)
    std_inc = RelaxationState(STD_ASN).score()
    std_batch = score_batch_fast(np.array([STD_ASN], dtype=np.int32))[0]
    print(f"[0] Validation:")
    print(f"    Phase3 full score:    {std_ref:.5f}")
    print(f"    Incremental state:    {std_inc:.5f}  {'✓' if abs(std_ref-std_inc)<1e-4 else '✗'}")
    print(f"    NumPy batch scorer:   {std_batch:.5f}  {'✓' if abs(std_ref-std_batch)<1e-4 else '✗'}")
    print()

    STD_SCORE = std_inc

    # ---- Null test ----
    print("[1] Null test — 50k complete+2-stop codes (constructed sampler)")
    rng = np.random.default_rng(42)
    n_target = 50_000
    CHUNK = 10_000
    all_scores = []
    n_better = 0

    while len(all_scores) < n_target:
        asns = generate_complete_batch(CHUNK, rng)
        scores = score_batch_fast(asns)
        all_scores.extend(scores.tolist())
        n_better += int((scores > STD_SCORE).sum())

    all_scores = all_scores[:n_target]
    mean_s  = statistics.mean(all_scores)
    stdev_s = statistics.stdev(all_scores)
    z = (STD_SCORE - mean_s) / stdev_s
    print(f"    Standard score: {STD_SCORE:.4f}  |  mean={mean_s:.4f} ± {stdev_s:.4f}")
    print(f"    Z-score: {z:.2f}σ")
    print(f"    Codes beating standard: {n_better:,}/{n_target:,} "
          f"({100*n_better/n_target:.3f}%)")
    print()

    # ---- Top-30 competitor search ----
    print("[2] Top-30 complete competitors (500k constructed sample)")
    rng2 = np.random.default_rng(999)
    top: List[Tuple[float, List[int]]] = []

    for _ in range(50):  # 50 × 10k = 500k
        asns = generate_complete_batch(10_000, rng2)
        scores = score_batch_fast(asns)
        for score_val, asn_row in zip(scores, asns):
            top.append((float(score_val), asn_row.tolist()))
        top.sort(reverse=True, key=lambda x: x[0])
        top = top[:31]

    top = top[:30]
    top_is_std = any(asn == STD_ASN for _, asn in top)
    print(f"    Standard code in top 30: {'YES ✓' if top_is_std else 'NO'}")
    print(f"    Standard score: {STD_SCORE:.4f}")
    print()

    for rank, (s, asn) in enumerate(top[:15], 1):
        is_std = (asn == STD_ASN)
        diffs = [f"{AMINO_ACIDS[STD_ASN[k]]}→{AMINO_ACIDS[asn[k]]}"
                 for k in range(N_CLASSES) if asn[k] != STD_ASN[k]]
        diff_str = ", ".join(diffs[:4]) + ("…" if len(diffs) > 4 else "")
        marker = " ← STANDARD" if is_std else ""
        print(f"    #{rank:>2}: {s:.4f}  [{diff_str}]{marker}")
    print()

    # ---- GTE Relaxation ----
    print("[3] GTE Fixed-Point Relaxation — 30 starts (DSAC-style coherence search)")
    print("    Prediction: standard code is unique coherence point")
    print()
    rng3 = np.random.default_rng(1234)
    starts_batch = generate_complete_batch(30, rng3)  # 30 valid starts
    n_to_std, n_runs = 0, 0
    fp_scores = []

    for trial in range(30):
        start = starts_batch[trial].tolist()
        n_runs += 1
        fp, hist, n_steps = gte_relax(start, max_steps=500)
        final_s = hist[-1]
        fp_scores.append(final_s)
        is_std_fp = (fp == STD_ASN)
        if is_std_fp:
            n_to_std += 1
        if trial < 6:
            print(f"    Trial {trial+1:>2}: {n_steps:>3} steps, "
                  f"{hist[0]:.3f}→{final_s:.3f}  "
                  f"{'→ STANDARD ✓' if is_std_fp else '→ other'}")

    print(f"\n    ({n_runs} runs):")
    print(f"    → Standard code: {n_to_std}/{n_runs} ({100*n_to_std/max(n_runs,1):.0f}%)")
    if fp_scores:
        n_above = sum(1 for s in fp_scores if s > STD_SCORE)
        print(f"    Score range: [{min(fp_scores):.4f}, {max(fp_scores):.4f}]")
        print(f"    Fixed points above standard: {n_above}/{n_runs}")
    print()

    # ---- Prebiotic start ----
    print("[4] GTE Relaxation from prebiotic-biased start")
    sorted_classes = sorted(range(N_CLASSES), key=lambda k: -CLASS_SIZES[k])
    sorted_sense = sorted(SENSE_AA_OUTCOMES,
                          key=lambda i: -PREBIOTIC_ACCESSIBILITY[AMINO_ACIDS[i]])
    stop_list = sorted(STOP_OUTCOMES)

    bio_asn = [-1] * N_CLASSES
    for i, k in enumerate(sorted_classes[-3:]):
        bio_asn[k] = stop_list[i % len(stop_list)]
    remaining = [k for k in sorted_classes if bio_asn[k] == -1]
    for i, k in enumerate(remaining):
        bio_asn[k] = sorted_sense[i % len(sorted_sense)]

    # Patch completeness
    used = {o for o in bio_asn if SENSE_ARR[o]}
    for aa in sorted(SENSE_AA_OUTCOMES - used):
        for k in remaining:
            v = bio_asn[k]
            if sum(1 for j in remaining if bio_asn[j] == v) > 1:
                bio_asn[k] = aa
                break

    bio_arr = np.array(bio_asn)
    bio_ok = is_complete_arr(bio_arr) and has_2stops_arr(bio_arr)
    print(f"    Prebiotic start feasible: {bio_ok}")
    if bio_ok:
        bio_state = RelaxationState(bio_asn)
        print(f"    Start score: {bio_state.score():.4f}")
        fp_bio, hist_bio, n_bio = gte_relax(bio_asn, max_steps=500)
        is_std_bio = (fp_bio == STD_ASN)
        print(f"    After {n_bio} steps: {hist_bio[-1]:.4f}  "
              f"{'→ STANDARD CODE ✓' if is_std_bio else '→ other fixed point'}")
    print()

    # ---- Summary ----
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Z-score (complete+2stop codes): {z:.2f}σ")
    print(f"  Codes beating standard:         {n_better:,}/{n_target:,} "
          f"({100*n_better/n_target:.3f}%)")
    print(f"  Standard in top 30:             {'YES' if top_is_std else 'NO'}")
    print(f"  GTE → standard code:            {n_to_std}/{n_runs} "
          f"({100*n_to_std/max(n_runs,1):.0f}%)")
    print()
    if n_to_std == n_runs:
        print("  ★ STANDARD CODE IS UNIQUE FIXED POINT")
        print("    Every random complete+2-stop code relaxes to the standard code.")
        print("    The standard genetic code is the unique DSAC coherence point of")
        print("    the 4-criterion viability landscape — exactly the UGP two-stage")
        print("    sieve prediction.")
    elif n_to_std >= n_runs * 2 // 3:
        print("  ◑ DOMINANT (not unique) attractor — examine non-standard fixed points.")
    else:
        print("  ○ INCONCLUSIVE — multiple attractors of comparable score.")


if __name__ == "__main__":
    main()
