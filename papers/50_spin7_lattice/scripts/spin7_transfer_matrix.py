"""
Round 3: p(L,C,R) = C+R-CR-LCR over GF(7) as a spin-7 lattice model.

Interprets each site as carrying a "spin" in Z_7 = {0,1,2,3,4,5,6}.
The update rule p gives a local "coupling" structure.

1. Compute the Z_7 transfer matrix (T_{i,j} = exp(-beta * E(i,j)) where
   E(i,j) = sum of p values in the neighborhood)
2. Compute partition function for chains of length L at several beta
3. Look for signs of phase transitions (non-analyticities in log Z)
4. Check the symmetry group F21 = Z7 ⋊ Z3 in the transfer matrix

For a 1D spin chain with periodic BC:
Z(L) = Tr(T^L) where T is the transfer matrix

Here we use a 2-spin transfer matrix approach:
T[s1,s2,s3] with action based on p.
"""

import signal, sys, json
import numpy as np

TIMEOUT_SECONDS = 120

def _timeout(s, f):
    print("TIMEOUT reached.")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)

# p over GF(7)
def p_gf7(L, C, R):
    return (C + R - C*R - L*C*R) % 7

# Energy function: E(L,C,R) = "cost" of a spin configuration
# Interpretation: distance from target output
# E = p(L,C,R)^2 mod 7 (quadratic "kinetic" energy)
# or: E = p(L,C,R) directly (linear coupling)
# We'll use E = p(L,C,R) as a "spin interaction term"

# Transfer matrix approach: T[a,b] = sum over c of exp(-beta * p(a,b,c))
# This represents the transfer from site (a,b) -> (b,c)
# Size: 7^2 x 7^2

def build_transfer_matrix(beta):
    """Build 49x49 transfer matrix T[(a,b),(b,c)] = exp(-beta * p(a,b,c))"""
    T = np.zeros((7, 7, 7))  # T[a, b, c] = Boltzmann weight
    for a in range(7):
        for b in range(7):
            for c in range(7):
                E = p_gf7(a, b, c)
                T[a, b, c] = np.exp(-beta * E)
    
    # Reshape to transfer matrix: rows = (a,b), cols = (b,c)
    # But we need to marginalize over a (or keep track)
    # Standard 1D transfer matrix: T2[b,c] = sum_a T[a,b,c] * rho[a]
    # For simplicity, use T2[b,c] = sum_a T[a,b,c] (flat measure on a)
    T2 = T.sum(axis=0)  # shape (7, 7)
    return T2

def partition_function(L, beta):
    """Compute Z = Tr(T^L) for periodic chain of length L"""
    T = build_transfer_matrix(beta)
    # Compute T^L using matrix power
    TL = np.linalg.matrix_power(T, L)
    Z = np.trace(TL)
    return Z

def free_energy_per_site(L, beta):
    """F/L = -log(Z)/L/beta"""
    Z = partition_function(L, beta)
    if Z <= 0:
        return float('inf')
    return -np.log(Z) / (L * beta) if beta > 0 else float('inf')

print("=== Spin-7 lattice model: Partition function and free energy ===")
print(f"p(L,C,R) = C+R-CR-LCR over GF(7)")
print(f"Energy E(L,C,R) = p(L,C,R)")
print()

# Transfer matrix at beta=1
T_beta1 = build_transfer_matrix(1.0)
print("Transfer matrix T (beta=1.0, 7x7, T[b,c] = sum_a exp(-p(a,b,c))):")
print(T_beta1.round(3))

# Eigenvalues of transfer matrix
eigenvalues = np.linalg.eigvals(T_beta1)
eigenvalues_real = np.sort(eigenvalues.real)[::-1]
print(f"\nEigenvalues (real parts, sorted descending):")
print(eigenvalues_real.round(6))

# The spectral gap determines correlation length
lambda1 = eigenvalues_real[0]
lambda2 = eigenvalues_real[1]
spectral_gap = lambda1 - lambda2
correlation_length = 1.0 / np.log(lambda1/lambda2) if abs(lambda2) > 0 and lambda1 > lambda2 else float('inf')
print(f"\nLargest eigenvalue: {lambda1:.6f}")
print(f"Second eigenvalue: {lambda2:.6f}")
print(f"Spectral gap: {spectral_gap:.6f}")
print(f"Correlation length xi = 1/log(lambda1/lambda2): {correlation_length:.4f}")

# Scan over beta: look for phase transition indicators
betas = [0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0]
L = 10  # chain length for partition function

print(f"\n=== Partition function Z and free energy at chain length L={L} ===")
print(f"{'beta':>10} {'log(Z)':>12} {'F/L/beta':>12} {'xi':>10}")
for beta in betas:
    T = build_transfer_matrix(beta)
    evals = np.linalg.eigvals(T)
    evals_r = np.sort(evals.real)[::-1]
    lam1 = evals_r[0]
    lam2 = evals_r[1]
    
    # For large L, Z ~ lambda1^L
    Z_approx = lam1**L
    logZ = L * np.log(max(lam1, 1e-10))
    
    # Correlation length
    xi = 1.0/np.log(lam1/max(abs(lam2), 1e-10)) if abs(lam2) > 1e-10 else float('inf')
    
    # Free energy per site
    F_per_site = -np.log(max(lam1, 1e-10)) / beta
    
    print(f"{beta:>10.3f} {logZ:>12.4f} {F_per_site:>12.4f} {xi:>10.4f}")

# Check F21 symmetry: Z7⋊Z3
# F21 acts as: Z7 shifts (x -> x+1 mod 7) and Z3 cube-root rotation (x -> 2x mod 7)
print("\n=== F21 symmetry check on transfer matrix ===")
# Z7 shift: x -> (x+1) mod 7
# Z3 cube: x -> 2x mod 7 (order 3: 1->2->4->1)
def shift_perm(k):
    return [(x + k) % 7 for x in range(7)]

def cube_perm():
    return [(2*x) % 7 for x in range(7)]

def permute_matrix(T, perm):
    """Apply permutation to rows and columns of T"""
    n = len(perm)
    Tp = np.zeros_like(T)
    for i in range(n):
        for j in range(n):
            Tp[i, j] = T[perm[i], perm[j]]
    return Tp

T1 = build_transfer_matrix(1.0)

# Check Z7 shift symmetry
shifts = [shift_perm(k) for k in range(7)]
max_shift_error = 0
for k in range(1, 7):
    T_shifted = permute_matrix(T1, shift_perm(k))
    err = np.max(np.abs(T_shifted - T1))
    max_shift_error = max(max_shift_error, err)
print(f"Z7 shift symmetry violation (max element error): {max_shift_error:.8f}")

# Check Z3 cube symmetry
cp = cube_perm()
print(f"Z3 cube permutation: {cp}")
T_cubed = permute_matrix(T1, cp)
cube_error = np.max(np.abs(T_cubed - T1))
print(f"Z3 cube symmetry violation: {cube_error:.8f}")

# Physical interpretation
print("\n=== Physical interpretation ===")
# Energy values 0-6 in the Boltzmann weight
E_counts = {}
for L in range(7):
    for C in range(7):
        for R in range(7):
            E = p_gf7(L, C, R)
            E_counts[E] = E_counts.get(E, 0) + 1
print("Distribution of energy values over all 343 inputs:")
for E in sorted(E_counts.keys()):
    print(f"  E={E}: {E_counts[E]} states ({100*E_counts[E]/343:.1f}%)")

# Mean field energy
total_E = sum(E * count for E, count in E_counts.items())
mean_E = total_E / 343
print(f"Mean energy per site (at beta->0 / T->inf): {mean_E:.4f}")

# Check for degeneracy at E=0 (ground state)
ground_states = [(L2, C2, R2) for L2 in range(7) for C2 in range(7) for R2 in range(7) 
                  if p_gf7(L2, C2, R2) == 0]
print(f"Ground state degeneracy (E=0): {len(ground_states)} / 343")

signal.alarm(0)

results = {
    "eigenvalues_beta1": eigenvalues_real.tolist(),
    "spectral_gap_beta1": float(spectral_gap),
    "correlation_length_beta1": float(correlation_length) if not np.isinf(correlation_length) else None,
    "energy_distribution": E_counts,
    "mean_energy": float(mean_E),
    "ground_state_degeneracy": len(ground_states),
    "Z7_shift_symmetry_error": float(max_shift_error),
    "Z3_cube_symmetry_error": float(cube_error)
}

with open("spin7_transfer_matrix_results.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nResults saved.")
