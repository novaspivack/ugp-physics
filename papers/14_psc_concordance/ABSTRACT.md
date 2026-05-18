# Abstract

We present a concordance between two methodologically distinct lines of evidence, both converging on the Standard Model gauge structure SU(3)×SU(2)×U(1) and three-generation chiral fermion content as the preferred PSC-consistent structure—subject to explicitly stated conditions.

The first line is **formal**: a chain of axiomatic closure theorems (Papers 03, 05, 20, and 21 of the NEMS/PSC suite) establishes that PSC implies the exclusion of GUT groups, vector-like fermions, and CP-conserving theories, and that the Two-Layer PSC Theorem selects G_SM and N_gen=3. Key sieve constraints are machine-checked in Lean 4. Full uniqueness (the claim that no other theory passes the sieve) is conditional on the open Residual Classification Conjecture (RCC).

The second line is **computational**: a finite exhaustive enumeration over 20,160 candidate universe descriptions (TE2.2 scan) minimizes a fourteen-term PSC dissonance functional D[Ψ], finding that only 12 universes (0.06%) satisfy the hard PSC filters, all 12 are SM-like, and the Standard Model gauge-structure-and-generation tuple (d, G, N_gen) = (4, G_SM, 3) is the unique co-minimum family at D_min = 1.0667 (Hessian stability λ_min = 2.0 > 0; four co-minimizers in ρ, τ within the SM family).

The computational result is a verified finite certificate over a specific discrete parameterization; extension to the full continuum of theories relies on analytic density and continuity arguments. We carefully characterize the partial dependence of two scan constraints (C_2, C_3) on the SRRG fixed-point, which encodes SM structure, and explain why this does not vitiate the concordance but does affect the interpretation of the independence claim. The two methods share no common proof steps, code, or deductive machinery; their agreement on the same answer constitutes a non-trivial cross-domain concordance that strengthens the case for Standard Model structural necessity.

Residuals characterised include: the RCC (open), the discretization gap, the neutrino sector, and explicit falsifiability conditions.
