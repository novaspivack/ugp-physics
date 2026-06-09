#!/usr/bin/env python3
import argparse, math, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def divisors(n):
    ds, r = set(), int(math.isqrt(n))
    for d in range(1, r+1):
        if n % d == 0:
            ds.add(d); ds.add(n//d)
    return sorted(ds)

def is_probable_prime(n):
    if n < 2: return False
    small = [2,3,5,7,11,13,17,19,23,29,31]
    for p in small:
        if n == p: return True
        if n % p == 0: return False
    d, s = n-1, 0
    while d % 2 == 0:
        d //= 2; s += 1
    for a in [2,3,5,7,11,13,17]:
        if a % n == 0: continue
        x = pow(a, d, n)
        if x in (1, n-1): continue
        for _ in range(s-1):
            x = (x * x) % n
            if x == n-1: break
        else:
            return False
    return True

def ridge(n):          # R_n = 2^n - 16
    return (1 << n) - 16

def q2_from(b2, Rn):   # q2 = floor(R_n / b2)
    return Rn // b2

def q1_from(q2):       # UGP‑1 fixed gap
    return q2 - 13

def b1_from(b2, q2):   # b1 = b2 + q2 + 7
    return b2 + q2 + 7

def c1_from(b1, q1):   # c1 = b1*q1 + 20
    return b1 * q1 + 20

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", type=str, default="./ugp_v2_out/atlas")
    ap.add_argument("--n", type=int, default=10)
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    Rn = ridge(args.n)
    b2s = [d for d in divisors(Rn) if d > 15]
    b2s.sort()

    ids = []
    for b2 in b2s:
        q2 = q2_from(b2, Rn)
        q1 = q1_from(q2)
        b1 = b1_from(b2, q2)
        c1 = c1_from(b1, q1)
        survivor = is_probable_prime(c1)
        basin_id = 1 if survivor else 2
        ids.append((b2, basin_id))

    xs = list(range(len(b2s)))
    ys = [t[1] for t in ids]

    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.scatter(xs, ys, s=12)
    ax.set_xlabel("seed index (sorted by $b_2$)")
    ax.set_ylabel("basin id")
    ax.set_yticks([0,1,2])
    ax.set_yticklabels([f"$c=2^{args.n}-1$", "$c=2^{16}-1$", "other"])
    ax.grid(True, linestyle=":", linewidth=0.6)

    # optional highlight: n=10, mirror survivors at b2 in {24,42}
    if args.n == 10:
        for i, b2 in enumerate(b2s):
            if b2 in (24, 42):
                ax.scatter([i], [ys[i]], marker="*", s=80)

    out = os.path.join(args.outdir, "basin_plot.pdf")
    fig.tight_layout(); fig.savefig(out); plt.close(fig)
    print("Wrote", out)

if __name__ == "__main__":
    main()