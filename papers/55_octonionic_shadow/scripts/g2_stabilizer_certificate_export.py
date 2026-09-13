#!/usr/bin/env python3
"""
g2_stabilizer_certificate_export.py

Exports exact-integer certificates for the QR(7) octonion G2 derivation system.
Computes the exact rational nullspace of the 512×64 derivation system and its
apex-stabilizer restriction, then exports an integer-coefficient certificate
suitable for machine-verification in Lean.

The certificate includes:
  - integer basis for der(O) (14 vectors, each 64 integers)
  - integer basis for Stab(e_apex) in der(O) (8 vectors)
  - independence-certifying minors (nonzero determinants)
  - rank witnesses for the full system and the apex-restricted system
  - bracket closure coefficients (confirming Lie algebra structure)

All computations use exact rational arithmetic (via sympy). The output JSON
is readable by the Lean G2StabilizerCertificate module for decide-class
verification of the Lie-algebra claims in g2_stabilizer_derivation.py.

Output: ../data/g2_stabilizer_certificate.json
"""

import json
import math
import os
import signal
import sys
from fractions import Fraction
from itertools import combinations

import sympy as sp

TIMEOUT_SECONDS = 600


def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT: wall-clock limit {TIMEOUT_SECONDS}s reached.")
    sys.exit(1)


signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

MUL = {}
for t in range(7):
    a, b, c = t % 7, (t + 1) % 7, (t + 3) % 7
    for x, y, z in [(a, b, c), (b, c, a), (c, a, b)]:
        MUL[(x, y)] = (z, 1)
        MUL[(y, x)] = (z, -1)


def basis_mul(a, b):
    v = [0] * 8
    if a == 7 and b == 7:
        v[7] = 1
    elif a == 7:
        v[b] = 1
    elif b == 7:
        v[a] = 1
    elif a == b:
        v[7] = -1
    else:
        k, s = MUL[(a, b)]
        v[k] = s
    return v


def build_system():
    RIGHT = {b: [basis_mul(a, b) for a in range(8)] for b in range(8)}
    LEFT = {a: [basis_mul(a, b) for b in range(8)] for a in range(8)}
    rows = []
    for a in range(8):
        for b in range(8):
            ab = basis_mul(a, b)
            block = [[0] * 64 for _ in range(8)]
            for c in range(8):
                if ab[c]:
                    for m in range(8):
                        block[m][m * 8 + c] += ab[c]
            for m in range(8):
                for r in range(8):
                    block[r][m * 8 + a] -= RIGHT[b][m][r]
                    block[r][m * 8 + b] -= LEFT[a][m][r]
            rows.extend(block)
    return rows, LEFT, RIGHT


def vec_to_mat(v):
    return [v[i * 8 : (i + 1) * 8] for i in range(8)]


def mat_flat(M):
    return [x for row in M for x in row]


def mat_mul_int(A, B):
    n, m, p = len(A), len(A[0]), len(B[0])
    return [[sum(A[i][k] * B[k][j] for k in range(m)) for j in range(p)] for i in range(n)]


def commutator(A, B):
    AB = mat_mul_int(A, B)
    BA = mat_mul_int(B, A)
    return [[AB[i][j] - BA[i][j] for j in range(8)] for i in range(8)]


def scale_to_integer_basis(basis_frac):
    out = []
    for v in basis_frac:
        fracs = [Fraction(x) for x in v]
        denoms = [x.denominator for x in fracs if x != 0]
        lcm = 1
        for d in denoms:
            lcm = lcm * d // math.gcd(lcm, d)
        out.append([int(x * lcm) for x in fracs])
    return out


def nullspace_int(A_rows):
    M = sp.Matrix(A_rows)
    ns = M.nullspace()
    rank = M.rank()
    basis = [[int(x) for x in v] for v in ns]
    return scale_to_integer_basis(basis), rank


def check_derivation(D_flat, LEFT, RIGHT):
    D = vec_to_mat(D_flat)
    for a in range(8):
        for b in range(8):
            ab = basis_mul(a, b)
            lhs = [sum(ab[c] * D[m][c] for c in range(8)) for m in range(8)]
            rhs = [
                sum(RIGHT[b][m][r] * D[m][a] for m in range(8))
                + sum(LEFT[a][m][r] * D[m][b] for m in range(8))
                for r in range(8)
            ]
            if lhs != rhs:
                return False
    return True


def rank_minor(A_rows, target_rank):
    import numpy as np

    A = np.array(A_rows, dtype=float)
    nrows, ncols = A.shape
    sel_rows = []
    for i in range(nrows):
        trial = sel_rows + [i]
        if np.linalg.matrix_rank(A[trial, :]) > len(sel_rows):
            sel_rows.append(i)
        if len(sel_rows) == target_rank:
            break
    sel_cols = []
    for j in range(ncols):
        trial = sel_cols + [j]
        if np.linalg.matrix_rank(A[:, trial]) > len(sel_cols):
            sel_cols.append(j)
        if len(sel_cols) == target_rank:
            break
    sub = [[int(A_rows[r][c]) for c in sel_cols] for r in sel_rows]
    d = int(sp.Matrix(sub).det())
    assert d != 0
    return sel_rows, sel_cols, d


def find_independence_cols(B, k):
    import numpy as np

    A = np.array(B.tolist(), dtype=float)
    sel_cols = []
    for j in range(A.shape[1]):
        trial = sel_cols + [j]
        if np.linalg.matrix_rank(A[:, trial]) > len(sel_cols):
            sel_cols.append(j)
        if len(sel_cols) == k:
            break
    d = int(sp.Matrix([[int(A[i][j]) for j in sel_cols] for i in range(k)]).det())
    assert d != 0
    return sel_cols, d


def bracket_closure_coeffs(basis):
    d = len(basis)
    mats = [vec_to_mat(v) for v in basis]
    B = sp.Matrix(basis).T
    out = []
    for i in range(d):
        for j in range(i + 1, d):
            C = mat_flat(commutator(mats[i], mats[j]))
            coef = [int(x) for x in B.gauss_jordan_solve(sp.Matrix(C))[0]]
            out.append({"i": i, "j": j, "coeffs": coef})
    return out


def main():
    A_rows, LEFT, RIGHT = build_system()
    print(f"System size: {len(A_rows)} x {len(A_rows[0])}")

    int_basis, rank = nullspace_int(A_rows)
    print(f"Rank: {rank}, nullity: {len(int_basis)}")
    assert rank == 50 and len(int_basis) == 14
    for i, v in enumerate(int_basis):
        assert check_derivation(v, LEFT, RIGHT)

    apex_rows = A_rows + [[1 if j == m * 8 else 0 for j in range(64)] for m in range(8)]
    int_apex, rank2 = nullspace_int(apex_rows)
    print(f"Apex rank: {rank2}, nullity: {len(int_apex)}")
    assert rank2 == 56 and len(int_apex) == 8
    for i, v in enumerate(int_apex):
        assert check_derivation(v, LEFT, RIGHT)
        assert all(v[m * 8] == 0 for m in range(8))

    rank50_rows, rank50_cols, det50 = rank_minor(A_rows, 50)
    rank56_rows, rank56_cols, det56 = rank_minor(apex_rows, 56)

    B14 = sp.Matrix(int_basis)
    indep14_cols, det14 = find_independence_cols(B14, 14)
    B8 = sp.Matrix(int_apex)
    indep8_cols, det8 = find_independence_cols(B8, 8)

    print(f"det14={det14}, det8={det8}, det50={det50}, det56={det56}")

    bracket14 = bracket_closure_coeffs(int_basis)
    bracket8 = bracket_closure_coeffs(int_apex)

    cert = {
        "derivation_basis_14": int_basis,
        "apex_stabilizer_basis_8": int_apex,
        "independence_14_minor_cols": indep14_cols,
        "independence_14_det": det14,
        "independence_8_minor_cols": indep8_cols,
        "independence_8_det": det8,
        "rank50_row_indices": rank50_rows,
        "rank50_col_indices": rank50_cols,
        "rank50_det": det50,
        "rank56_row_indices": rank56_rows,
        "rank56_col_indices": rank56_cols,
        "rank56_det": det56,
        "system_rank": rank,
        "apex_system_rank": rank2,
        "bracket_closure_14": bracket14,
        "bracket_closure_8": bracket8,
    }

    _data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../data")
    os.makedirs(_data_dir, exist_ok=True)
    out_path = os.path.join(_data_dir, "g2_stabilizer_certificate.json")
    with open(out_path, "w") as f:
        json.dump(cert, f)

    print(f"Wrote {out_path}")
    signal.alarm(0)


if __name__ == "__main__":
    main()
