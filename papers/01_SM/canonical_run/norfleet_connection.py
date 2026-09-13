"""
norfleet_connection.py

Investigate the structural relationship between Norfleet's universal balance
constant Λ_N = ln(φ)/ln(2π) and the UGP generation-count N_gen_eff = ln(φ)/(π-ln(2π²)).

Norfleet (independent, empirical): Λ_N ≈ 0.2618, validated in MLB batting averages
and Go rating systems as a balance constant between discrete (φ) and continuous (2π)
dynamics.

UGP: N_gen_eff ≈ 3.0268, the effective generation count from HMC L2 PSC-entropy
balance.  Both share the numerator ln(φ); their denominators differ.

KEY FINDING:
    D1 + D2 = π - ln(π)   [EXACT algebraic identity]
    where D1 = ln(2π), D2 = π - ln(2π²)

Equivalently:
    1/Λ_N + 1/N_gen_eff = (π - ln π) / ln φ   [exact]

And N_gen_eff is determined by Λ_N via:
    N_gen_eff = Λ_N · ln(φ) / [Λ_N(π - ln π) - ln φ]

The two formulas are NOT independent — they are the two natural solutions to a
system whose "sum of reciprocals" is fixed by π - ln(π), itself near-2 (deviation
~0.00314).

NOTE: 3 × Λ_N ≈ π/4 is a NEAR-MISS, not an exact identity (difference ~9.3e-5,
relative error ~1.2e-4).
"""

from mpmath import mp, mpf, log, pi, sqrt, nstr

mp.dps = 60  # 60 significant figures throughout

phi = (1 + sqrt(5)) / 2

# ── the two formulas ────────────────────────────────────────────────────────
Lambda_N   = log(phi) / log(2 * pi)                # Norfleet's constant
N_gen_eff  = log(phi) / (pi - log(2 * pi**2))      # UGP generation count
eps        = N_gen_eff - 3

D1 = log(2 * pi)           # Norfleet's denominator
D2 = pi - log(2 * pi**2)   # UGP denominator

print("=" * 65)
print("Norfleet Connection — 60-decimal-place analysis")
print("=" * 65)

print(f"\nφ          = {nstr(phi, 50)}")
print(f"Λ_Norfleet = ln(φ)/ln(2π)      = {nstr(Lambda_N, 50)}")
print(f"N_gen_eff  = ln(φ)/(π-ln(2π²)) = {nstr(N_gen_eff, 50)}")
print(f"ε = N_gen_eff - 3              = {nstr(eps, 50)}")

# ── KEY CHECK 1: 3 × Λ_N vs π/4 ────────────────────────────────────────────
print("\n" + "=" * 65)
print("CHECK 1: Is 3 × Λ_Norfleet = π/4 exactly?")
print("=" * 65)
three_L = 3 * Lambda_N
diff_pi4 = three_L - pi / 4
print(f"  3 × Λ_N      = {nstr(three_L, 50)}")
print(f"  π/4          = {nstr(pi / 4, 50)}")
print(f"  Difference   = {nstr(diff_pi4, 15)}")
print(f"  Relative err = {nstr(abs(diff_pi4) / (pi/4), 6)}")
print(f"  → NEAR-MISS, NOT exact  (diff ~ 9.26e-5)")

# ── KEY CHECK 2: D1 + D2 = π - ln(π) ───────────────────────────────────────
print("\n" + "=" * 65)
print("CHECK 2: D1 + D2 = π - ln(π)  [exact algebraic identity]")
print("=" * 65)
print(f"  D1 = ln(2π)        = {nstr(D1, 40)}")
print(f"  D2 = π - ln(2π²)   = {nstr(D2, 40)}")
print(f"  D1 + D2            = {nstr(D1 + D2, 40)}")
print(f"  π - ln(π)          = {nstr(pi - log(pi), 40)}")
print(f"  Equal (to 55 s.f.)? {abs(D1 + D2 - (pi - log(pi))) < 1e-55}")
print()
print("  Algebraic proof:")
print("    D1 + D2 = (ln2 + lnπ) + (π - ln2 - 2lnπ)")
print("            = π - lnπ  ✓")

# ── KEY CHECK 3: reciprocal sum identity ────────────────────────────────────
print("\n" + "=" * 65)
print("CHECK 3: 1/Λ_N + 1/N_gen_eff = (π - ln π)/ln φ  [exact]")
print("=" * 65)
recip_sum  = 1 / Lambda_N + 1 / N_gen_eff
rhs        = (pi - log(pi)) / log(phi)
print(f"  1/Λ_N + 1/N_gen  = {nstr(recip_sum, 40)}")
print(f"  (π-lnπ)/ln(φ)    = {nstr(rhs, 40)}")
print(f"  Equal?            {abs(recip_sum - rhs) < 1e-55}")

# ── KEY CHECK 4: express N_gen_eff via Λ_N ──────────────────────────────────
print("\n" + "=" * 65)
print("CHECK 4: N_gen_eff expressed through Λ_N")
print("=" * 65)
# From D1 + D2 = π - lnπ:  D2 = π - lnπ - D1 = π - lnπ - ln(φ)/Λ_N
# So N_gen_eff = ln(φ)/D2 = ln(φ) / (π - lnπ - ln(φ)/Λ_N)
expr = log(phi) / (pi - log(pi) - log(phi) / Lambda_N)
print(f"  ln(φ) / (π - lnπ - ln(φ)/Λ_N) = {nstr(expr, 30)}")
print(f"  N_gen_eff                       = {nstr(N_gen_eff, 30)}")
print(f"  Equal? {abs(expr - N_gen_eff) < 1e-55}")
print()
print("  Also: N_gen_eff = Λ_N · ln(φ) / [Λ_N(π - lnπ) - ln φ]")
expr2 = Lambda_N * log(phi) / (Lambda_N * (pi - log(pi)) - log(phi))
print(f"  = {nstr(expr2, 30)}")
print(f"  Equal? {abs(expr2 - N_gen_eff) < 1e-55}")

# ── master formula scan ──────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("Master formula family: denom(n) = ln2 + n·lnπ")
print("(n=1 gives Norfleet; n=2 gives ln(2π²), one step from our D2)")
print("=" * 65)
for n in range(1, 6):
    dn = log(2) + n * log(pi)
    r  = log(phi) / dn
    mark = "← Norfleet Λ_N" if n == 1 else ("← ln(2π²): our D2 = π - this" if n == 2 else "")
    print(f"  n={n}: denom={nstr(dn, 16)}, ratio={nstr(r, 16)}  {mark}")

print("\n  Our D2 = π - denom(2) — so N_gen_eff = ln(φ)/(π - denom(2))")

# ── summary ──────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("SUMMARY")
print("=" * 65)
print("""
  1. 3 × Λ_N = π/4 is APPROXIMATE, not exact. (diff ~9.3e-5)

  2. EXACT IDENTITY (algebraic, no approximation):
       ln(2π) + (π − ln(2π²)) = π − ln(π)
       i.e. D_Norfleet + D_UGP = π − ln π

  3. EQUIVALENT EXACT IDENTITY:
       1/Λ_N + 1/N_gen_eff = (π − ln π) / ln φ

  4. N_gen_eff is algebraically determined by Λ_N:
       N_gen_eff = Λ_N · ln φ / [Λ_N(π − ln π) − ln φ]

  5. Master formula denom(n) = ln2 + n·lnπ:
       n=1  → Norfleet Λ_N = ln φ / ln(2π)
       n=2  → ln φ / ln(2π²), and our D2 = π − ln(2π²)
     So N_gen_eff = ln φ / (π − denom(2)).

  6. The shared scaffold is:
       numerator = ln φ   (Fibonacci/golden ratio — discrete novelty)
       π and ln π appear in the denominators, encoding the
       "circular / continuous" sector Norfleet identified.

  7. Physical interpretation (tentative):
       Λ_N measures novelty-to-opportunity at the full circle (2π).
       N_gen_eff measures the same ratio at the CRITICAL LEVEL where
       π (half-period) minus the circle's logarithm ln(2π²) sets
       the PSC-entropy balance.  The two are complementary projections
       of the same ln(φ)/[π, lnπ] algebra, unified by the exact identity.
""")
