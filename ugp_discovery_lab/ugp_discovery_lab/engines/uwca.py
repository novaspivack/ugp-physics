"""
Universal Windowed Cellular Automaton (UWCA) engine for UGP Discovery Lab.

Implements the core CA rules and arithmetic operations needed for UGP computations.
"""

from typing import List, Set, Tuple
import numpy as np


# CA Rule definitions (Wolfram ordering: 111, 110, 101, 100, 011, 010, 001, 000)
RULES = {
    "rule110": {(1,1,0), (1,0,1), (0,1,1), (0,1,0), (0,0,1)},
    "rule30":  {(1,0,0), (0,1,1), (0,1,0), (0,0,1)},
    "rule54":  {(1,0,1), (1,0,0), (0,1,0), (0,0,1)},
    "rule90":  {(1,1,1), (1,1,0), (1,0,1), (1,0,0), (0,1,1), (0,1,0), (0,0,1), (0,0,0)},  # XOR rule
    "rule150": {(1,1,1), (1,0,1), (0,1,1), (0,0,1)},  # XNOR rule
}


def ca_step(row: List[int], rule: str, wrap: bool = True) -> List[int]:
    """
    Execute one step of a cellular automaton.
    
    Args:
        row: Current state as list of 0s and 1s
        rule: Rule name (e.g., 'rule110', 'rule30', 'rule54')
        wrap: Whether to use periodic boundary conditions
        
    Returns:
        Next state as list of 0s and 1s
    """
    if rule not in RULES:
        raise ValueError(f"Unknown rule: {rule}. Available: {list(RULES.keys())}")
    
    ones = RULES[rule]
    n = len(row)
    nxt = [0] * n
    
    for i in range(n):
        # Get neighborhood
        L = row[(i-1) % n] if wrap else (row[i-1] if i > 0 else 0)
        C = row[i]
        R = row[(i+1) % n] if wrap else (row[i+1] if i < n-1 else 0)
        
        # Apply rule
        nxt[i] = 1 if (L, C, R) in ones else 0
    
    return nxt


def ca_run(initial_row: List[int], rule: str, steps: int, wrap: bool = True) -> List[List[int]]:
    """
    Run a cellular automaton for multiple steps.
    
    Args:
        initial_row: Starting configuration
        rule: Rule name
        steps: Number of steps to run
        wrap: Whether to use periodic boundary conditions
        
    Returns:
        List of all states (including initial)
    """
    history = [initial_row.copy()]
    current = initial_row.copy()
    
    for _ in range(steps):
        current = ca_step(current, rule, wrap)
        history.append(current.copy())
    
    return history


def fib_fast_doubling(k: int) -> int:
    """
    Compute Fibonacci number F_k using fast doubling method.
    
    Args:
        k: Index of Fibonacci number to compute
        
    Returns:
        F_k (the k-th Fibonacci number)
    """
    if k < 0:
        raise ValueError("Fibonacci index must be non-negative")
    if k == 0:
        return 0
    if k == 1:
        return 1
    
    def _fast_double(n: int) -> Tuple[int, int]:
        """Compute (F_n, F_{n+1}) using fast doubling."""
        if n == 0:
            return (0, 1)
        
        a, b = _fast_double(n >> 1)
        c = a * (2 * b - a)
        d = a * a + b * b
        
        if n & 1:  # n is odd
            return (d, c + d)
        else:  # n is even
            return (c, d)
    
    return _fast_double(k)[0]


def lucas_fast_doubling(k: int) -> int:
    """
    Compute Lucas number L_k using fast doubling method.
    
    Args:
        k: Index of Lucas number to compute
        
    Returns:
        L_k (the k-th Lucas number)
    """
    if k < 0:
        raise ValueError("Lucas index must be non-negative")
    if k == 0:
        return 2
    if k == 1:
        return 1
    
    def _fast_double(n: int) -> Tuple[int, int]:
        """Compute (L_n, L_{n+1}) using fast doubling."""
        if n == 0:
            return (2, 1)
        
        a, b = _fast_double(n >> 1)
        c = a * a - 2 * (1 if n & 1 else -1)
        d = a * b
        
        if n & 1:  # n is odd
            return (d, c)
        else:  # n is even
            return (c, d)
    
    return _fast_double(k)[0]


def chebyshev_u(n: int, x: int) -> int:
    """
    Compute Chebyshev polynomial of the second kind U_n(x).
    
    Args:
        n: Degree of polynomial
        x: Evaluation point
        
    Returns:
        U_n(x)
    """
    if n < 0:
        raise ValueError("Chebyshev degree must be non-negative")
    if n == 0:
        return 1
    if n == 1:
        return 2 * x
    
    # Use recurrence relation: U_n(x) = 2*x*U_{n-1}(x) - U_{n-2}(x)
    u_prev = 1  # U_0(x)
    u_curr = 2 * x  # U_1(x)
    
    for i in range(2, n + 1):
        u_next = 2 * x * u_curr - u_prev
        u_prev = u_curr
        u_curr = u_next
    
    return u_curr


def mersenne_number(n: int) -> int:
    """
    Compute Mersenne number M_n = 2^n - 1.
    
    Args:
        n: Exponent
        
    Returns:
        2^n - 1
    """
    if n < 0:
        raise ValueError("Mersenne exponent must be non-negative")
    return (1 << n) - 1  # 2^n - 1


def repunit_number(base: int, n: int) -> int:
    """
    Compute repunit number in given base.
    
    Args:
        base: Base of the repunit (e.g., 3 for ternary)
        n: Number of digits
        
    Returns:
        (base^n - 1) / (base - 1)
    """
    if base < 2:
        raise ValueError("Repunit base must be at least 2")
    if n < 0:
        raise ValueError("Repunit length must be non-negative")
    if n == 0:
        return 0
    
    return (base ** n - 1) // (base - 1)


def gcd_extended(a: int, b: int) -> Tuple[int, int, int]:
    """
    Extended Euclidean algorithm.
    
    Returns:
        (gcd, x, y) where gcd = a*x + b*y
    """
    if a == 0:
        return b, 0, 1
    
    gcd, x1, y1 = gcd_extended(b % a, a)
    x = y1 - (b // a) * x1
    y = x1
    
    return gcd, x, y


def modular_inverse(a: int, m: int) -> int:
    """
    Compute modular inverse of a mod m.
    
    Args:
        a: Number to invert
        m: Modulus
        
    Returns:
        x such that a*x ≡ 1 (mod m)
    """
    gcd, x, _ = gcd_extended(a, m)
    if gcd != 1:
        raise ValueError(f"No modular inverse exists for {a} mod {m}")
    
    return x % m


def chinese_remainder_theorem(remainders: List[int], moduli: List[int]) -> int:
    """
    Solve system of congruences using Chinese Remainder Theorem.
    
    Args:
        remainders: List of remainders
        moduli: List of pairwise coprime moduli
        
    Returns:
        Solution x such that x ≡ remainders[i] (mod moduli[i]) for all i
    """
    if len(remainders) != len(moduli):
        raise ValueError("Remainders and moduli must have same length")
    
    if not remainders:
        return 0
    
    # Check pairwise coprimality
    for i in range(len(moduli)):
        for j in range(i + 1, len(moduli)):
            if gcd_extended(moduli[i], moduli[j])[0] != 1:
                raise ValueError(f"Moduli {moduli[i]} and {moduli[j]} are not coprime")
    
    # Solve using Garner's algorithm
    result = 0
    product = 1
    
    for i in range(len(remainders)):
        remainder = remainders[i]
        modulus = moduli[i]
        
        # Compute partial solution
        partial = (remainder - result) * modular_inverse(product, modulus) % modulus
        result += partial * product
        product *= modulus
    
    return result


def prime_sieve(limit: int) -> List[int]:
    """
    Generate all primes up to limit using Sieve of Eratosthenes.
    
    Args:
        limit: Upper bound for prime generation
        
    Returns:
        List of primes ≤ limit
    """
    if limit < 2:
        return []
    
    # Initialize sieve
    sieve = [True] * (limit + 1)
    sieve[0] = sieve[1] = False
    
    # Mark composites
    for i in range(2, int(limit ** 0.5) + 1):
        if sieve[i]:
            for j in range(i * i, limit + 1, i):
                sieve[j] = False
    
    # Collect primes
    primes = [i for i, is_prime in enumerate(sieve) if is_prime]
    return primes


def is_prime(n: int) -> bool:
    """
    Test if a number is prime.
    
    Args:
        n: Number to test
        
    Returns:
        True if n is prime, False otherwise
    """
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    
    # Trial division up to sqrt(n)
    for i in range(3, int(n ** 0.5) + 1, 2):
        if n % i == 0:
            return False
    
    return True
