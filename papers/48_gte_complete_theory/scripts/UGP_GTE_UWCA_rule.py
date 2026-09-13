# UWCA reference implementation and verification harness.
#
# Implements the UWCA construction of the UGP monograph and witnesses, end to end:
#
#   Part A — GTE as a UWCA program (macro layer; thm:gte-as-uwca / thm:self-sim):
#            the arithmetic map T and the compiled macro-schedule run side by side
#            with a bit-for-bit agreement check on the canonical n=10 orbit.
#   Part B — The UWCA itself (the UGP-window constraint automaton): a two-layer
#            survivor window with per-coordinate prime alphabets, binary symbols
#            realized as designated residues in F_p^x, the clopen penalty e_i,
#            and the deterministic zero-temperature sweep that enforces e_i = 0.
#            One sweep computes one Rule 110 row (thm:uwca-universal).
#   Part C — The register-rail realization (binary sector): per-site registers
#            C, L, R, five minterm rails M^u, and N, updated by the synchronous
#            passes P1-P4 with the binary-sector invariant checked every round
#            (uwca_sweep_implements_rule110 / uwca_sector_invariant, ugp-lean).
#   Part D — Verification: Parts B and C evolve non-trivial tapes for many steps
#            and are compared cell-exactly, at every cell of every step, against
#            an INDEPENDENT native Rule 110 implementation (Wolfram-number bit
#            extraction — a different formulation of the rule than the minterm
#            tiles used by the UWCA parts).
#   Part E — Artifact: side-by-side spacetime diagram (UWCA-emulated vs native)
#            plus a capped JSON verification summary.
#
# Direction (machine vs trajectory): the UWCA is the general machine; GTE is one
# lawful program on it, and Rule 110 is another program (the universality witness).
# The UWCA does not "follow" GTE; the compiled GTE program (Part A) does.
#
# Canonical n=10 orbit (Lean: gte_update_at_seed, gte_odd_step_c_is_1023, ugp-lean):
#   (1,73,823) --odd--> (9,42,1023) --even--> (5,275,65535)

import json
import os
import signal
import sys
from math import prod

# All artifacts are written next to this script, independent of the caller's CWD.
ARTIFACT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---- sandbox safety: wall-clock timeout and hard size caps ----
TIMEOUT_SECONDS = 600
MAX_WIDTH = 1024
MAX_STEPS = 1024
MAX_JSON_ITEMS = 1000

def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached. Aborting.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

# ════════════════════════════════════════════════════════════════════════
# Part A — GTE as a UWCA program (macro layer)
# ════════════════════════════════════════════════════════════════════════

# ---- CRT helpers for an odd-prime window P (M > all register maxima) ----
P_N10 = [3, 5, 17, 19, 257]             # M = 1,245,165 > 65,535
M     = prod(P_N10)

def crt_pack(res, P=P_N10):
    """res: list of residues mod p_i; returns x in [0,M) consistent with CRT."""
    x = 0
    for i, p in enumerate(P):
        r = res[i]
        k = 0
        while (x + k*prod(P[:i])) % p != r:
            k += 1
        x += k * prod(P[:i])
    return x % M

def crt_unpack(x, P=P_N10):             # residues of x mod p_i
    return [x % p for p in P]

def crt_roundtrip_ok(x):
    """Register-encoding witness: x < M is exactly recoverable from its residues."""
    return 0 <= x < M and crt_pack(crt_unpack(x)) == x

# ---- arithmetic helpers ----
def divrem(c, b):                        # exact integer division
    q = c // b
    m = c - q*b
    return q, m

def fib_fast_doubling(n):
    def fd(k):
        if k == 0: return (0, 1)
        a, b = fd(k >> 1)                # F_t, F_{t+1}
        c = a * (2*b - a)
        d = a*a + b*b
        return (c, d) if k % 2 == 0 else (d, c + d)
    return fd(n)[0]

N_C = 3  # QCD color rank; even-step Mersenne-ladder exponent jump is 2*N_C

# ---- arithmetic T (Definition \ref{def:update}; per-component formulas) ----
def T_step(state, n, phase):
    a, b, c, q_prev = state
    if phase == "odd":
        # Odd step (t=1): DivRem(c,b) -> (q,m); a = m-(n+1); b = b-(m+q); c = 2^n-1
        q, m = divrem(c, b)
        a2 = m - (n + 2 - 1)
        b2 = b - (m + q)
        c2 = 2**n - 1                    # Mersenne ridge capacity (Def. UGP-1 (C))
        q2 = q
        phase2 = "even"
    else:
        # Even step (t=2): genuine division (no hardwired ridge facts);
        # the ridge invariants are ASSERTED below as theorem checks.
        q, m = divrem(c, b)
        kappa = abs(q - q_prev)          # quotient gap; = 13 on the n=10 ridge
        F = fib_fast_doubling(kappa)     # Fibonacci lift; F_13 = 233
        a2 = m - (n + 2 - 2)
        b2 = b + F
        if c == 2**n - 1:                # Mersenne boundary: ladder extension
            c2 = 2**(n + 2*N_C) - 1      # extended ([B-structured]) value
        else:
            c2 = b * q + 15              # information rule off-boundary
        q2 = q
        phase2 = "odd"
    return (a2, b2, c2, q2), phase2

# ---- UWCA-compiled macro: the sweep-schedule form (lst:uwca-macro) ----
# Distinct code path from T_step: registers Reg = {a,b,c,q,m,q_hat,kappa,F} with a
# phase flag, executed as the schedule's ordered register writes. Agreement with
# T_step is the macro-level witness that the compiled program realizes T exactly.
def UWCA_macro(state, n, phase):
    a, b, c, q_hat = state
    Reg = {"a": a, "b": b, "c": c, "q": 0, "m": 0,
           "q_hat": q_hat, "kappa": 0, "F": 0}
    # DIVREM(c, b -> q, m)
    Reg["q"], Reg["m"] = divrem(Reg["c"], Reg["b"])
    if phase == "odd":
        Reg["a"] = Reg["m"] - (n + 1)
        Reg["b"] = Reg["b"] - (Reg["m"] + Reg["q"])
        Reg["c"] = 2**n - 1              # ridge step: Mersenne capacity
    else:
        Reg["a"] = Reg["m"] - n
        Reg["kappa"] = abs(Reg["q"] - Reg["q_hat"])
        Reg["F"] = fib_fast_doubling(Reg["kappa"])
        Reg["b"] = Reg["b"] + Reg["F"]
        if Reg["c"] == 2**n - 1:         # Mersenne boundary test on pre-update c
            Reg["c"] = 2**(n + 2*N_C) - 1
        else:
            Reg["c"] = b * Reg["q"] + 15  # pre-update (latched) b, current quotient
    Reg["q_hat"] = Reg["q"]              # stash quotient for the next even step
    phase2 = "even" if phase == "odd" else "odd"
    return (Reg["a"], Reg["b"], Reg["c"], Reg["q_hat"]), phase2

# ---- ridge-invariant theorem checks (UGP-1 at n=10) ----
def assert_ridge_facts(trace, n=10):
    """Checks the Lean-certified ridge invariants on the computed trace."""
    (a1, b1, c1, q1), (a2, b2, c2, q2) = trace[0], trace[1]
    q_seed, m_seed = divrem(823, 73)
    assert m_seed == 20, "prime-lock remainder m1 = 20 violated"
    assert (a1, b1, c1) == (9, 42, 1023), "odd step must give (9,42,1023)"
    qe, me = divrem(c1, b1)
    assert me == 15, "ridge remainder lock m2 = 15 violated"
    assert abs(qe - q1) == 13, "quotient gap |q2-q1| = 13 violated"
    assert fib_fast_doubling(13) == 233, "Fibonacci lift F_13 = 233 violated"
    assert b1 * qe + 15 == 2**n - 1, "strict capacity identity b2*q2+15 = 2^n-1 violated"
    assert (a2, b2, c2) == (5, 275, 65535), "even step must give (5,275,65535)"

# ---- run both traces and check exact agreement ----
def run_and_check(seed, n=10, steps=2, write_csv=True, csv_path=None):
    if csv_path is None:
        csv_path = os.path.join(ARTIFACT_DIR, "gte_uwca_trace.csv")
    a, b, c = seed
    q_prev = 0
    phase = "odd"
    stA = (a, b, c, q_prev)    # arithmetic
    stU = (a, b, c, q_prev)    # UWCA-compiled
    rows = [("k","phase","aA","bA","cA","qA","aU","bU","cU","qU")]
    states = []
    for k in range(1, steps+1):
        stA, phaseA = T_step(stA, n, phase)
        stU, phaseU = UWCA_macro(stU, n, phase)
        assert phaseA == phaseU
        aA, bA, cA, qA = stA
        aU, bU, cU, qU = stU
        assert (aA, bA, cA, qA) == (aU, bU, cU, qU), f"Mismatch at step {k}"
        for v in (bA, cA, qA):           # CRT window witnesses every register
            assert crt_roundtrip_ok(v), f"CRT round-trip failed for {v} (M={M})"
        states.append(stA[:3] + (qA,))
        rows.append((str(k), str(phase),
                     str(aA), str(bA), str(cA), str(qA),
                     str(aU), str(bU), str(cU), str(qU)))
        phase = phaseA
    if steps >= 2:
        assert_ridge_facts(states, n=n)
    if write_csv:
        with open(csv_path, "w") as f:
            for r in rows:
                f.write(",".join(map(str, r)) + "\n")
    return rows

# ════════════════════════════════════════════════════════════════════════
# Rule 110: tile data and an independent native implementation
# ════════════════════════════════════════════════════════════════════════

# The UWCA tile data: the minterm set S = {110, 101, 011, 010, 001} — the five
# neighborhoods on which the rule outputs 1. This is the construction's defining
# data (one clopen tile per minterm); Parts B and C consume the rule ONLY via S.
MINTERMS = {(1, 1, 0), (1, 0, 1), (0, 1, 1), (0, 1, 0), (0, 0, 1)}

def rule110_from_minterms(l, c, r):
    """The local map as the UWCA defines it: output 1 iff (l,c,r) is in S."""
    return 1 if (l, c, r) in MINTERMS else 0

def rule110_native(l, c, r):
    """INDEPENDENT reference: Wolfram-number bit extraction, 110 = 0b01101110.
    A different formulation of the rule than the minterm tiles above."""
    return (110 >> ((l << 2) | (c << 1) | r)) & 1

def native_step(row):
    """One synchronous native Rule 110 step on a periodic ring."""
    W = len(row)
    return [rule110_native(row[(i - 1) % W], row[i], row[(i + 1) % W])
            for i in range(W)]

# ════════════════════════════════════════════════════════════════════════
# Part B — The UWCA: survivor-residue window, clopen penalty, deterministic sweep
# ════════════════════════════════════════════════════════════════════════
#
# The UGP-window constraint automaton: sites i in a window carry two time layers
# t in {0,1}; each coordinate (i,t) has its own odd prime p_{i,t} and a two-symbol
# alphabet B_{p_{i,t}} = {SYM0, SYM1} of designated residues in F_{p_{i,t}}^x
# (binary states as clopen cylinder choices in the survivor substrate). The clopen
# penalty e_i is 0 iff x_{i,1} equals the rule image of the frozen t=0 triple.
# The update is the deterministic zero-temperature sweep: visit i left to right
# and replace x_{i,1} by the unique symbol of its alphabet with e_i = 0 (local
# determinism). One completed sweep is one Rule 110 row; iterating with rolling
# windows (commit layer 1 -> layer 0) yields any finite number of CA steps.

def first_odd_primes(count):
    """The first `count` odd primes (sieve; alphabets need p >= 3)."""
    primes, cand = [], 3
    while len(primes) < count:
        if all(cand % q for q in primes if q * q <= cand) and cand % 2:
            primes.append(cand)
        cand += 2
    return primes

class SurvivorWindowUWCA:
    """The penalty-sweep UWCA on a periodic window of width W."""

    def __init__(self, width):
        assert 3 <= width <= MAX_WIDTH
        self.W = width
        # Distinct odd primes for every window coordinate (i, t), t in {0,1}.
        # Rolling windows identify the layer-(t+1) coordinates of one window
        # with the layer-t coordinates of the next; the prime labels roll with them.
        ps = first_odd_primes(2 * width)
        self.p = [ps[:width], ps[width:]]      # self.p[t][i]
        # Designated residues realizing the logical symbols in F_p^x:
        # SYM0 = 1 and SYM1 = 2 (both nonzero mod every odd prime).
        self.SYM = (1, 2)

    def encode(self, bit, i, t):
        """Logical bit -> residue symbol in B_{p_{i,t}} (clopen cylinder choice)."""
        return self.SYM[bit] % self.p[t][i]

    def decode(self, sym):
        """Residue symbol -> logical bit (the 'obvious' identification)."""
        return self.SYM.index(sym)

    def penalty(self, layer0, i, candidate_sym):
        """Clopen penalty e_i: 0 iff the candidate layer-1 symbol equals the rule
        image of the frozen layer-0 triple (the rule enters ONLY here, via the
        minterm tile set S)."""
        W = self.W
        l = self.decode(layer0[(i - 1) % W])
        c = self.decode(layer0[i])
        r = self.decode(layer0[(i + 1) % W])
        want_bit = rule110_from_minterms(l, c, r)
        return 0 if candidate_sym == self.encode(want_bit, i, 1) else 1

    def sweep(self, layer0):
        """One deterministic left-to-right sweep: at each site, search the local
        alphabet for the penalty-zero symbol; assert it is unique (local
        determinism lemma). Returns the completed layer-1 symbol row."""
        layer1 = [None] * self.W
        for i in range(self.W):
            zero_pen = [s for s in (self.encode(0, i, 1), self.encode(1, i, 1))
                        if self.penalty(layer0, i, s) == 0]
            assert len(zero_pen) == 1, f"local determinism violated at site {i}"
            layer1[i] = zero_pen[0]
        assert all(self.penalty(layer0, i, layer1[i]) == 0 for i in range(self.W)), \
            "sweep did not reach the global e_i = 0 configuration"
        return layer1

    def run(self, bits, steps):
        """Evolve a logical bit row for `steps` sweeps with rolling windows;
        returns the list of bit rows (including the initial row)."""
        assert steps <= MAX_STEPS
        rows = [list(bits)]
        layer0 = [self.encode(b, i, 0) for i, b in enumerate(bits)]
        for _ in range(steps):
            layer1 = self.sweep(layer0)
            new_bits = [self.decode(s) for s in layer1]
            rows.append(new_bits)
            # Rolling window: the committed layer becomes the next frozen layer.
            layer0 = [self.encode(b, i, 0) for i, b in enumerate(new_bits)]
        return rows

# ════════════════════════════════════════════════════════════════════════
# Part C — The register-rail realization: passes P1-P4 on the binary sector
# ════════════════════════════════════════════════════════════════════════
#
# Per-site registers: C (visible bit), L, R (neighbor rails), M^u for each
# minterm u in S (match flags), N (next-bit accumulator). The binary sector
# requires all auxiliaries to be zero between rounds. One round is:
#   (P1) neighbor distribution   L_i := C_{i-1}; R_i := C_{i+1}
#   (P2) minterm detection       M^u_i := [L_i=l][C_i=c][R_i=r]
#   (P3) OR-accumulation         N_i := OR_u M^u_i
#   (P4) commit and clear        C_i := N_i; auxiliaries := 0
# (uwca_sweep_implements_rule110, uwca_sector_invariant, ugp-lean: zero sorry.)

class RegisterRailUWCA:
    """The P1-P4 register machine on a periodic ring of width W."""

    def __init__(self, width):
        assert 3 <= width <= MAX_WIDTH
        self.W = width

    def _fresh_sites(self, bits):
        return [{"C": b, "L": 0, "R": 0,
                 "M": {u: 0 for u in MINTERMS}, "N": 0} for b in bits]

    def _assert_binary_sector(self, sites):
        for s in sites:
            assert s["L"] == 0 and s["R"] == 0 and s["N"] == 0 \
                and all(v == 0 for v in s["M"].values()), \
                "binary-sector invariant violated"

    def round(self, sites):
        W = self.W
        self._assert_binary_sector(sites)
        # (P1) neighbor distribution (synchronous, radius 1)
        snapshot = [s["C"] for s in sites]
        for i, s in enumerate(sites):
            s["L"] = snapshot[(i - 1) % W]
            s["R"] = snapshot[(i + 1) % W]
        # (P2) minterm detection on five independent rails
        for s in sites:
            for u in MINTERMS:
                l, c, r = u
                s["M"][u] = 1 if (s["L"] == l and s["C"] == c and s["R"] == r) else 0
        # (P3) OR-accumulation into NEXT
        for s in sites:
            s["N"] = 1 if any(s["M"].values()) else 0
        # (P4) commit and clear auxiliaries
        for s in sites:
            s["C"] = s["N"]
            s["L"] = s["R"] = s["N"] = 0
            for u in MINTERMS:
                s["M"][u] = 0
        self._assert_binary_sector(sites)
        return sites

    def run(self, bits, steps):
        assert steps <= MAX_STEPS
        sites = self._fresh_sites(bits)
        rows = [list(bits)]
        for _ in range(steps):
            sites = self.round(sites)
            rows.append([s["C"] for s in sites])
        return rows

# ════════════════════════════════════════════════════════════════════════
# Part D — Verification harness
# ════════════════════════════════════════════════════════════════════════

def verify_configuration(name, bits, steps):
    """Evolve one initial condition under (i) the penalty-sweep UWCA, (ii) the
    register-rail UWCA, and (iii) native Rule 110; require exact agreement at
    every cell of every step. Returns the verified spacetime and a summary."""
    W = len(bits)
    uwca_rows = SurvivorWindowUWCA(W).run(bits, steps)
    rail_rows = RegisterRailUWCA(W).run(bits, steps)
    native_rows = [list(bits)]
    row = list(bits)
    for _ in range(steps):
        row = native_step(row)
        native_rows.append(row)
    mismatches = 0
    for t in range(steps + 1):
        for i in range(W):
            if not (uwca_rows[t][i] == rail_rows[t][i] == native_rows[t][i]):
                mismatches += 1
    cells = (steps + 1) * W
    verdict = "EXACT MATCH" if mismatches == 0 else f"{mismatches} MISMATCHES"
    print(f"[{name}] width={W} steps={steps} cells-checked={cells:,} "
          f"(UWCA sweep vs register rails vs native): {verdict}")
    assert mismatches == 0, f"{name}: UWCA emulation diverged from native Rule 110"
    return uwca_rows, native_rows, {"config": name, "width": W, "steps": steps,
                                    "cells_checked": cells, "mismatches": 0}

def random_tape(width, seed=110):
    """Reproducible random tape (deterministic LCG; no RNG state dependence)."""
    x, out = seed, []
    for _ in range(width):
        x = (1103515245 * x + 12345) % (1 << 31)
        out.append((x >> 16) & 1)
    return out

# ════════════════════════════════════════════════════════════════════════
# Part E — Side-by-side spacetime artifact
# ════════════════════════════════════════════════════════════════════════

def write_sidebyside_png(uwca_rows, native_rows, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    A = np.array(uwca_rows)
    B = np.array(native_rows)
    fig, axes = plt.subplots(1, 2, figsize=(10, 5.4), dpi=200)
    for ax, data, title in ((axes[0], A, "Rule 110 emulated on the UWCA\n"
                             "(penalty sweep on the survivor window)"),
                            (axes[1], B, "Native Rule 110\n"
                             "(independent reference implementation)")):
        ax.imshow(data, cmap="binary", interpolation="nearest", aspect="auto")
        ax.set_title(title, fontsize=9)
        ax.set_xlabel("space $i$", fontsize=8)
        ax.set_ylabel("time $t$", fontsize=8)
        ax.tick_params(labelsize=7)
    diff = int(np.sum(A != B))
    fig.suptitle(f"UWCA-emulated vs native Rule 110 — "
                 f"cellwise differences: {diff}", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(path)
    plt.close(fig)
    return diff

# ════════════════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Part A — GTE macro witness on the canonical n=10 orbit:
    #   (k=1) phase=odd  -> (a,b,c,q) = (9, 42, 1023, 11)
    #   (k=2) phase=even -> (a,b,c,q) = (5, 275, 65535, 24)
    run_and_check(seed=(1, 73, 823), n=10, steps=2, write_csv=True)
    print("[GTE macro] arithmetic and UWCA-compiled traces agree; "
          "ridge invariants verified. Wrote gte_uwca_trace.csv")

    # Parts B-D — Rule 110 genuinely running on the UWCA, verified cell-exactly.
    summaries = []
    # (i) single-seed tape: the classic Rule 110 structure (figure source)
    single = [0] * 121
    single[60] = 1
    uwca_rows, native_rows, s1 = verify_configuration("single-seed", single, 80)
    summaries.append(s1)
    # (ii) reproducible random tape: ether + glider interactions over a long run
    rnd = random_tape(240, seed=110)
    _, _, s2 = verify_configuration("random-tape(seed=110)", rnd, 160)
    summaries.append(s2)

    # Part E — artifacts
    diff = write_sidebyside_png(uwca_rows, native_rows,
                                os.path.join(ARTIFACT_DIR,
                                             "uwca_rule110_sidebyside.png"))
    assert diff == 0
    summary = {"minterm_tile_set": sorted("".join(map(str, u)) for u in MINTERMS),
               "verifications": summaries[:MAX_JSON_ITEMS],
               "sidebyside_cell_differences": diff,
               "artifacts": ["gte_uwca_trace.csv",
                             "uwca_rule110_sidebyside.png",
                             "uwca_rule110_verification.json"]}
    with open(os.path.join(ARTIFACT_DIR, "uwca_rule110_verification.json"),
              "w") as f:
        json.dump(summary, f, indent=2)
    print("[artifacts] wrote uwca_rule110_sidebyside.png "
          "and uwca_rule110_verification.json")
    print("VERDICT: Rule 110 on the UWCA reproduces native Rule 110 exactly "
          "(every cell, every step, both configurations).")
    signal.alarm(0)
