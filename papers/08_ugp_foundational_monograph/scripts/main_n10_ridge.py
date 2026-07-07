#!/usr/bin/env python3
# main_n10_ridge.py — minimal n=10 ridge survivors check

def divisors(n):
    small, large = [], []
    i = 1
    while i*i <= n:
        if n % i == 0:
            small.append(i)
            if i*i != n:
                large.append(n//i)
        i += 1
    return small + large[::-1]

def mr64(n: int) -> bool:
    if n < 2: return False
    for p in [2,3,5,7,11,13,17]:
        if n == p: return True
        if n % p == 0 and n != p: return False
    d = n-1; s = 0
    while d % 2 == 0:
        d//=2; s+=1
    def chk(a):
        x = pow(a,d,n)
        if x in (1, n-1): return True
        for _ in range(s-1):
            x = (x*x) % n
            if x == n-1: return True
        return False
    for a in [2,3,5,7,11,13,17]:
        if a % n == 0: continue
        if not chk(a): return False
    return True

def ridge_scan(n: int):
    R = (1<<n) - 16
    for b2 in divisors(R):
        if b2 <= 15: 
            continue
        q2 = R // b2
        b1 = b2 + q2 + 7
        q1 = q2 - 13
        c1 = b1*q1 + 20
        if mr64(c1):
            yield (b2, q2, b1, q1, c1)

def mirror_dual_survivors(n: int):
    """Mirror-dual survivors: (b2,q2) where both (b2,q2) and (q2,b2) pass prime-lock.
    Excludes (72,14) because its mirror (14,72) fails b2 > 15."""
    base = {(b2,q2) for (b2,q2,_,_,_) in ridge_scan(n)}
    return {(b2,q2) for (b2,q2) in base if (q2,b2) in base}

if __name__ == "__main__":
    surv = mirror_dual_survivors(10)
    assert surv == {(24,42), (42,24)}, f"Unexpected mirror-dual survivors at n=10: {surv}"
    print("OK: mirror-dual survivors at n=10 are exactly {(24,42),(42,24)}")
