# su3_rigidity_proof_summary

*Generated: 2026-04-13T10:27:03.598343*

# SU(3) Rigidity Proof — Summary

- **Proof Status**: PASSED
- **Total Lemmas**: 5
- **Passed Lemmas**: 5
- **Vandermonde Discriminant**: 41075281/1327104

## Rigidity Lemmas

- **Dl1 Symmetry**: ✅ PASSED
  - Δ² invariant under all permutations of (a,b,c)
- **Dl2 Degree6 Homogeneity**: ✅ PASSED
  - Δ²(λk) = λ⁶Δ²(k) for all λ>0
- **Dl3 Pair Collision Order2**: ✅ PASSED
  - Δ²/(k_a - k_b)² = (k_a - k_c)²(k_b - k_c)²
- **Dl4 Multiplicativity**: ✅ PASSED
  - Δ² = h(k_a - k_b) × h(k_b - k_c) × h(k_c - k_a) where h(x) = x²
- **Dl5 Minimality**: ✅ PASSED
  - Any symmetric degree-6 polynomial vanishing to order ≥2 on each diagonal must be c × Δ²

## Algebraic Proof

- **Step 1**: Condition 3 requires F to be divisible by (k_i - k_j)² for each pair
- **Step 2**: S3 invariance forbids any odd 'alternating' factor
- **Step 3**: Any additional symmetric polynomial factor Q would raise total degree beyond 6
- **Step 4**: Degree-6 minimality forces F = C × Δ²
- **Step 5**: Multiplicativity over pairs requires even quadratic factor h(x) = x²
- **Conclusion**: Therefore F must be a constant multiple of Δ²

## Conclusion

The squared Vandermonde discriminant is **uniquely determined** as the only function satisfying:
- S3 invariance under permutations of (a,b,c)
- Degree-6 homogeneity in (k_a,k_b,k_c)
- Pair-collision zeros (vanishes quadratically when any pair coincides)
- Multiplicativity over pairs (three independent commutators multiply)

**Proof Status**: ✅ COMPLETE