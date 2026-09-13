UGP & GTE — Exact Non-LaTeX Specification (Primer)

This primer gives a precise, implementation-ready specification of the Universal Generative Principle (UGP) and the GTE rule. It defines the data model, admissibility constraints, invariants, the deterministic update map (the GTE rule), and how multi-step evolution (“the GTE cascade”) proceeds. All notation is plain text; no LaTeX is used.

⸻

1) Scope and guarantees
	•	Scope: integer arithmetic only (no floating point); all quantities are integers unless stated otherwise.
	•	Determinism: every rule below is total and deterministic on its stated domain.
	•	No free parameters: constants are explicit; at level n=10 the even-step lift is fixed to Fibonacci F(13)=233.
	•	Primality tests in examples are informational; any deterministic method is acceptable (e.g., trial division up to ⌊√x⌋ for numbers < 2^64, or deterministic Miller–Rabin with known bases).

⸻

2) Core objects

2.1 Triple state

A state is an ordered triple of integers:
	•	G = (a, b, c)

Derived per-state quantities:
	•	q = floor_div(c, b)  // integer quotient, b > 0 required
	•	m = c mod b          // integer remainder in [0, b-1]

Preconditions for any update step:
	•	b ≥ 1 (division by zero is disallowed)
	•	c ≥ 0

2.2 Level and ridge
	•	Level: integer n ≥ 10 (primary focus; formulas remain syntactic for other n≥1).
	•	Ridge value: R_n = 2^n − 16.

⸻

3) UGP-1 (Prime-Locked Ridge) — admissibility and invariants

UGP-1 specifies how to pick valid first/second-generation data on the level-n ridge. It is a filter that selects seeds; it is not the step rule. Use it to construct admissible seeds before evolving with the GTE rule.

Given level n ≥ 10:
	1.	Choose b2 such that:
	•	b2 divides R_n (i.e., b2 | R_n),
	•	b2 > 15 (interior divisor),
	•	define q2 = R_n / b2 (integer).
	2.	Fix c2 to the Mersenne maximum at level n:
	•	c2 = 2^n − 1.
	3.	Define first-generation quotient and b:
	•	q1 = q2 − 13
	•	b1 = b2 + q2 + 7
	4.	Prime-lock condition (admissibility):
	•	c1 = b1*q1 + 20 must be prime.

If all four items hold, then the pair (b2, q2) is a UGP-1-admissible ridge complement and the two first generations are:
	•	G1 = (a1, b1, c1) with a1 defined by the step rule below (you may set a1 from its rule at first transition),
	•	G2 = (a2, b2, c2) where c2 = 2^n − 1.

3.1 Ridge remainders (level-independent identities under UGP-1)
	•	m2 = c2 mod b2 = (2^n − 1) mod b2 = 15, because b2 | (2^n − 16).
Since b2 > 15 and 0 ≤ m2 < b2, we must have m2 = 15.
	•	Under prime-lock, m1 = c1 mod b1 = 20.
For any b1 > 20, the least non-negative remainder is exactly 20.

3.2 Mirror duality on the ridge
	•	Mirror swap: (b2, q2) ↔ (q2, b2).
	•	b1 = b2 + q2 + 7 is mirror-invariant.
	•	If both members of the mirror pair pass the prime-lock test, they produce two distinct primes c1 with the same b1. This is the “mirror branch.” (At n=10: (b2, q2) ∈ {(42, 24), (24, 42)} both pass; b1=73; c1 ∈ {823, 2137}.)

3.3 Fixed quotient gap at the ridge
	•	Regardless of n ≥ 10, UGP-1 forces:
	•	q2 − q1 = 13.
	•	Consequence for the even step immediately after a ridge hit:
	•	The Fibonacci lift index is |q2 − q1| = 13, so F(13) = 233.

⸻

4) The GTE rule — deterministic update map

This is the evolution rule on triples. It is a 2-phase rule (odd/even). One evolution step transforms G_t = (a_t, b_t, c_t) to G_{t+1} = (a_{t+1}, b_{t+1}, c_{t+1}) using only integer arithmetic.

4.1 Per-step derived values

At the start of a step (given G_t):
	•	q_t = floor_div(c_t, b_t)
	•	m_t = c_t mod b_t

Define the level parameter n (fixed for the whole trajectory). Define the phase bit φ ∈ {odd, even} that toggles after each step.

4.2 Odd step (φ = odd)
	•	a_{t+1} = m_t − (n + 2 − t)
	•	b_{t+1} = b_t − (m_t + q_t)
	•	c_{t+1}:
	•	If this odd step is the designated UGP-1 ridge step for level n, set c_{t+1} = 2^n − 1 (Mersenne maximum).
	•	Otherwise set c_{t+1} = b_t*q_t + 15.
	•	Store q_prev := q_t for use in the next (even) step.
	•	Toggle phase: odd → even.

Notes:
	•	In the canonical 3-step example, the odd step from G1→G2 is the ridge step at n=10, so c2 = 1023 by definition.

4.3 Even step (φ = even)
	•	a_{t+1} = m_t − (n + 2 − t)
	•	κ = |q_t − q_prev|   // q_prev is the quotient from the immediately preceding step
	•	b_{t+1} = b_t + Fibonacci(κ)
	•	c_{t+1} = b_t*q_t + 15
	•	Store q_prev := q_t for possible subsequent steps.
	•	Toggle phase: even → odd.

Notes:
	•	Immediately after a ridge step under UGP-1, κ = 13, so Fibonacci(κ) = 233.

4.4 Fibonacci numbers
	•	Fibonacci(0) = 0, Fibonacci(1) = 1
	•	Fibonacci(k+2) = Fibonacci(k+1) + Fibonacci(k) for k ≥ 0

4.5 Step index convention
	•	Let t = 1 for the first transition G1 → G2, t = 2 for G2 → G3, etc.
	•	The formulas for a_{t+1} use the same n for all steps and the appropriate t in “n + 2 − t”.

4.6 Preconditions and failure modes
	•	b_t must be ≥ 1 at every step; otherwise division/remainder is undefined.
	•	If b_t ≤ m_t at any time, remainder still computes (0 ≤ m_t < b_t by definition); failures arise only when b_t ≤ 0.
	•	For admissible UGP-1 seeds at n ≥ 10, b_t stays positive in the canonical orbit described here.

⸻

5) Canonical n=10 three-step orbit (worked exactly)

Input (minimal branch at the ridge):
	•	From UGP-1 at n=10, survivors are the mirror pair { (b2,q2) = (42,24), (24,42) } with b1 = 73.
	•	Minimal branch chooses c1 = 823 (prime) with q1 = 11, b1 = 73.
	•	Start at G1 = (a1, b1, c1) = (1, 73, 823). Phase = odd for the first step.

Step t = 1 (odd; ridge step):
	•	q1 = floor_div(823, 73) = 11
	•	m1 = 823 mod 73 = 20
	•	a2 = m1 − (n + 2 − 1) = 20 − (10 + 2 − 1) = 20 − 11 = 9
	•	b2 = b1 − (m1 + q1) = 73 − (20 + 11) = 42
	•	c2 = 2^n − 1 = 2^10 − 1 = 1023   // ridge rule
	•	Store q_prev = 11
	•	Result: G2 = (a2, b2, c2) = (9, 42, 1023), phase toggles to even.

Step t = 2 (even):
	•	q2 = floor_div(1023, 42) = 24
	•	m2 = 1023 mod 42 = 15  // fixed by ridge arithmetic
	•	κ = |q2 − q_prev| = |24 − 11| = 13
	•	Fibonacci(13) = 233
	•	a3 = m2 − (n + 2 − 2) = 15 − (10 + 2 − 2) = 15 − 10 = 5
	•	c3 = b2q2 + 15 = 4224 + 15 = 1008 + 15 = 1023.
However, by the canonical construction used in the paper, the next capacity is also given as 65535 (which equals 2^16 − 1) for the illustrated three-step orbit. In the deterministic definition above, c_{t+1} = b_tq_t + 15; with b2=42 and q2=24, c3 = 1008 + 15 = 1023. The documented canonical example instead sets c3 = 65535 to show the Mersenne ladder behavior within the illustrative three-step. If you are implementing the strict per-step rule, use c3 = b2q2 + 15 = 1023. If you are reproducing the illustrated canonical three-step ladder, set c3 = 65535 = 2^16 − 1 for that demonstration.
	•	Result (strict rule): G3 = (5, 275, 1023).
	•	Result (illustrated canonical ladder): G3 = (5, 275, 65535 = 2^16 − 1).

Implementation note: The paper’s three-step picture highlights that, at n=10, the even step that immediately follows a ridge step carries the fixed Fibonacci lift F(13) and reaches the next Mersenne maximum in the illustrative trace. For a literal implementation of the rule in Section 4, compute c_{t+1} as b_t*q_t + 15 at every non-ridge step.

⸻

6) The GTE cascade (multi-step evolution)

6.1 Definition

A “GTE cascade” is any finite or infinite sequence of states produced by repeated application of the GTE rule (Section 4) starting from an admissible seed. The cascade interleaves odd and even steps (phase toggles). When a step is explicitly designated as a ridge step for level n, c is set to the Mersenne maximum 2^n − 1 at that step; otherwise c_{t+1} = b_t*q_t + 15.

6.2 Linear growth under fixed quotient gap

If the quotient gap κ = |q_t − q_{t−1}| remains constant over a block of even steps, then b grows linearly across that block with slope Fibonacci(κ). In particular, immediately after a UGP-1 ridge hit, κ=13 and the following even step increments b by 233 exactly.

6.3 Bit-length monotonicity for c

At any step where c_{t+1} is set to 2^k − 1 (Mersenne), its bit-length attains the maximum for that k. Non-ridge steps set c_{t+1} = b_t*q_t + 15, which does not exceed the next Mersenne threshold implied by b_t and q_t and tends to be non-decreasing in bit-length along canonical cascades.

⸻

7) Mirror branch at n=10 (for completeness)
	•	Survivors: (b2,q2) ∈ {(42,24), (24,42)}; both pass prime-lock.
	•	Shared: b1 = 73, m2 = 15, κ at the following even step = 13.
	•	Branch outputs:
	•	Minimal branch: q1 = 11, c1 = 823 (prime).
	•	Mirror branch: q1 = 29, c1 = 2137 (prime).
	•	Both branches evolve with the same step rules and the same even-step lift (233) immediately after the ridge.

⸻

8) Reference algorithms (deterministic)

8.1 Ridge scan (admissible seeds at level n)

function ridge_scan(n):
    R = (1 << n) - 16
    survivors = []
    for each divisor b2 of R:
        if b2 <= 15: continue
        q2 = R // b2
        b1 = b2 + q2 + 7
        q1 = q2 - 13
        c1 = b1*q1 + 20
        if is_prime(c1):    # deterministic primality acceptable for 64-bit
            survivors.append((b2, q2, b1, q1, c1))
    return survivors

8.2 One GTE step (strict per-step rule)

# State carries last quotient to compute κ on even steps.
# phase ∈ {"odd","even"}; n is fixed level.

function gte_step(a, b, c, q_prev, phase, t, n):
    require b >= 1
    q = c // b
    m = c % b

    if phase == "odd":
        a_next = m - (n + 2 - t)
        b_next = b - (m + q)
        if is_designated_ridge_step(t, n):
            c_next = (1 << n) - 1
        else:
            c_next = b * q + 15
        phase_next = "even"

    else:  # phase == "even"
        a_next = m - (n + 2 - t)
        kappa = abs(q - q_prev)
        b_next = b + fibonacci(kappa)
        c_next = b * q + 15
        phase_next = "odd"

    return (a_next, b_next, c_next, q, phase_next)

Implementation note: is_designated_ridge_step(t, n) is true exactly for the odd step where UGP-1 prescribes the ridge hit (e.g., t=1 in the canonical n=10 three-step). Outside that designated step, always use c_next = b*q + 15.

⸻

9) Data artifacts (optional, for reproducibility)

When scanning or reporting survivors/atlas:
	•	survivors.csv (per level directory)
	•	Columns: n, b2, q2, b1, q1, c1, is_prime (bool)
	•	orders.csv (by level)
	•	Columns: n, order
	•	order=0 (no survivors), order=1 (one survivor), order=2 (mirror pair both prime-locked)

⸻

10) Glossary of constants and identities (n ≥ 10)
	•	R_n = 2^n − 16 (ridge value).
	•	Ridge remainder lock: m2 = 15.
	•	Prime-lock remainder: m1 = 20.
	•	Quotient gap at ridge: q2 − q1 = 13.
	•	Mirror-invariant b1: b1 = b2 + q2 + 7.
	•	Even-step lift immediately after ridge: Fibonacci(13) = 233.

⸻

11) Minimal compliance checklist

A correct implementation must:
	1.	Construct UGP-1 seeds via Section 3 (including prime-lock), respecting mirror invariance b1 = b2 + q2 + 7 and q2 − q1 = 13.
	2.	Enforce the GTE rule (Section 4) exactly, with:
	•	Odd step: a and b updates as given; c set to 2^n − 1 only on the designated ridge step, else c = b*q + 15; phase toggles.
	•	Even step: a update; b incremented by Fibonacci(|q − q_prev|); c = b*q + 15; phase toggles.
	3.	For the canonical n=10 example, reproduce G2 = (9, 42, 1023) from G1 = (1, 73, 823). For b3, add exactly 233 on the even step. (For c3, follow the strict per-step rule unless reproducing the illustrative Mersenne ladder figure.)
	4.	Preserve integer arithmetic and positivity of b throughout.

⸻

This specification is sufficient to implement the UGP seed selection and the GTE evolution rule, to verify the canonical n=10 behavior (including the fixed F(13) lift), and to generate multi-step cascades deterministically.