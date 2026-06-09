#!/usr/bin/env python3
"""
UGP→GTE artifact generator
--------------------------
Produces the two data/figure assets used by the LaTeX hooks:
  1) fib_index_hist.csv
  2) basin_plot.pdf

Defaults:
  outdir = ./ugp_v2_out/atlas
  level n = 10  (ridge R = 2^n - 16, c2 = 2^n - 1)

Usage:
  python ugp_make_artifacts.py
  python ugp_make_artifacts.py --outdir ./ugp_v2_out/atlas --n 10
"""

import argparse
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt

# -------------------------------
# Utilities
# -------------------------------
def divisors(n):
    """All positive divisors of n (unordered)."""
    ds = set()
    r = int(math.isqrt(n))
    for d in range(1, r + 1):
        if n % d == 0:
            ds.add(d)
            ds.add(n // d)
    return sorted(ds)

def is_probable_prime(n):
    """Deterministic Miller–Rabin for 64-bit; fine for our sizes here."""
    if n < 2:
        return False
    small_primes = [2,3,5,7,11,13,17,19,23,29,31]
    for p in small_primes:
        if n == p:
            return True
        if n % p == 0:
            return False
    # write n-1 as d*2^s
    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1
    # Deterministic bases for 64-bit
    for a in [2, 3, 5, 7, 11, 13, 17]:
        if a % n == 0:
            continue
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        skip_to_next_a = False
        for _ in range(s - 1):
            x = (x * x) % n
            if x == n - 1:
                skip_to_next_a = True
                break
        if skip_to_next_a:
            continue
        return False
    return True

def fib(k):
    """Fibonacci with F1=F2=1."""
    if k <= 0:
        return 0
    if k in (1,2):
        return 1
    a,b = 1,1
    for _ in range(3,k+1):
        a,b = b,a+b
    return b

# -------------------------------
# Core UGP-1 / GTE helpers
# -------------------------------
def ridge(n):
    """R_n = 2^n - 16"""
    return (1 << n) - 16

def c2_at_level(n):
    """c2 = 2^n - 1"""
    return (1 << n) - 1

def q2_from(b2, Rn):
    return Rn // b2

def q1_from(q2):
    # UGP-1 fixed gap
    return q2 - 13

def b1_from(b2, q2):
    return b2 + q2 + 7

def c1_from(b1, q1):
    return b1 * q1 + 20

def m_mod(c, b):
    return c % b

# -------------------------------
# Artifact builders
# -------------------------------
def build_fib_index_hist(outdir, n):
    """
    Produce 'fib_index_hist.csv' with columns: k,count
    For UGP-1 (fixed gap 13 at level n), this is a spike at k=13
    across all admissible divisors b2>15.
    """
    Rn = ridge(n)
    all_b2 = [d for d in divisors(Rn) if d > 15]
    # Every divisor defines q2, hence q1, hence k = |q2 - q1| = 13 (fixed).
    k_counts = {}
    for b2 in all_b2:
        q2 = q2_from(b2, Rn)
        k = abs(q2 - q1_from(q2))
        k_counts[k] = k_counts.get(k, 0) + 1

    # Write CSV
    csv_path = os.path.join(outdir, "fib_index_hist.csv")
    with open(csv_path, "w") as f:
        f.write("k,count\n")
        for k in sorted(k_counts):
            f.write(f"{k},{k_counts[k]}\n")
    return csv_path

def build_basin_plot(outdir, n):
    """
    Produce 'basin_plot.pdf' showing a simple schematic of basin IDs
    for seeds ordered by b2. Convention:
      id=0 → basin c=2^n-1 (Mersenne at step 2)
      id=1 → basin c=2^16-1 (observed step 3 for n=10 survivors)
      id=2 → other / non-admissible (prime-lock fails)
    Rule of thumb for this plot:
      - If c1 is prime (survivor), label id=1 (reaches 2^n-1 then 2^16-1).
      - Else id=2.
    (All admissible b2 have c2 = 2^n - 1 by construction; survivors are those with prime-lock c1.)
    """
    Rn = ridge(n)
    C2 = c2_at_level(n)

    b2s = [d for d in divisors(Rn) if d > 15]
    b2s.sort()

    ids = []
    for b2 in b2s:
        q2 = q2_from(b2, Rn)
        q1 = q1_from(q2)
        b1 = b1_from(b2, q2)
        c1 = c1_from(b1, q1)
        survivor = is_probable_prime(c1)
        if survivor:
            # survivor trajectory (observed): c2=Mersenne; next step hits larger Mersenne (n=16 for main example)
            basin_id = 1
        else:
            basin_id = 2
        ids.append((b2, basin_id, b1, q1, c1, q2))

    # Plot
    fig, ax = plt.subplots(figsize=(8, 4.2))
    xs = list(range(len(b2s)))
    ys = [t[1] for t in ids]
    ax.scatter(xs, ys, s=12)
    ax.set_xlabel("seed index (sorted by $b_2$)")
    ax.set_ylabel("basin id")
    ax.set_yticks([0,1,2])
    ax.set_yticklabels([f"$c=2^{n}-1$", "$c=2^{16}-1$", "other"])
    ax.grid(True, linestyle=":", linewidth=0.6)

    # Highlight the mirror pair survivors at n=10: b2 in {24,42}
    if n == 10:
        highlights = {24, 42}
        for i, b2 in enumerate(b2s):
            if b2 in highlights:
                ax.scatter([i], [ys[i]], marker="*", s=80)

    pdf_path = os.path.join(outdir, "basin_plot.pdf")
    fig.tight_layout()
    fig.savefig(pdf_path)
    plt.close(fig)
    return pdf_path

# -------------------------------
# Main
# -------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", type=str, default="./ugp_v2_out/atlas")
    ap.add_argument("--n", type=int, default=10)
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    csv_path = build_fib_index_hist(args.outdir, args.n)
    pdf_path = build_basin_plot(args.outdir, args.n)

    print("Artifacts written:")
    print("  -", csv_path)
    print("  -", pdf_path)
    print()
    print("Compilation tip:")
    print(r'  pdflatex "\def\DataDir{' + args.outdir + r'}\input{main.tex}"')

if __name__ == "__main__":
    sys.exit(main())