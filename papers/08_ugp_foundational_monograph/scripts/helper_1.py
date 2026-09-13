#!/usr/bin/env python3
import argparse, math, os

def divisors(n):
    ds, r = set(), int(math.isqrt(n))
    for d in range(1, r+1):
        if n % d == 0:
            ds.add(d); ds.add(n//d)
    return sorted(ds)

def ridge(n):          # R_n = 2^n - 16
    return (1 << n) - 16

def q2_from(b2, Rn):   # q2 = floor(R_n / b2)
    return Rn // b2

def q1_from(q2):       # UGP‑1 fixed gap
    return q2 - 13

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", type=str, default="./ugp_v2_out/atlas")
    ap.add_argument("--n", type=int, default=10)
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    Rn = ridge(args.n)
    all_b2 = [d for d in divisors(Rn) if d > 15]

    k_counts = {}
    for b2 in all_b2:
        q2 = q2_from(b2, Rn)
        k  = abs(q2 - q1_from(q2))   # = 13 for UGP‑1
        k_counts[k] = k_counts.get(k, 0) + 1

    out = os.path.join(args.outdir, "fib_index_hist.csv")
    with open(out, "w") as f:
        f.write("k,count\n")
        for k in sorted(k_counts):
            f.write(f"{k},{k_counts[k]}\n")
    print("Wrote", out)

if __name__ == "__main__":
    main()