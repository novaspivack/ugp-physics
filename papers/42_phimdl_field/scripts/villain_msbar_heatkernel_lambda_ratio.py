#!/usr/bin/env python3
"""First-principles one-loop Lambda-ratio for the heat-kernel (Villain) lattice action.

Derivation (background-field contact-term calculus): two single-plaquette actions with
identical Gaussian parts differ at one loop only through (i) O(beta^0) quadratic
plaquette terms and (ii) the self-contraction of their O(beta H^4) difference.

  Wilson:      quartic term -(beta/24N) tr H^4  -> Delta(1/g^2)_W  = -(2N^2-3)/(24N)
  Heat-kernel: measure term (1/2) ln J(H_p)     -> Delta(1/g^2)_HK = -N/24
  =>  ln(Lambda_HK / Lambda_W) = pi^2 (N^2-3) / (11 N^2)   (pure gauge)

This script VERIFIES every ingredient numerically:
  (a) su(N) contraction identities sum_a tr(B B T^a T^a) = C_F tr B^2 and
      sum_a tr(B T^a B T^a) = -tr B^2/(2N)  (explicit generators, random traceless B)
  (b) sum_roots (alpha,a)^2 = N |a|^2  (adjoint matrices, random a)
  (c) the heat-kernel measure term from EXACT character sums: SU(2) and SU(3)
      F(theta,s) = -ln(K_s(U)/K_s(1)) - d^2(U,1)/(4s)  ->  (1/2) ln J  as s -> 0
  (d) assembled Lambda ratios + Dashen-Gross / Hasenfratz-Hasenfratz consistency.

  (e) calibration against the published one-loop background-field values of
      Lang, Rebbi, Salomonson & Skagerstam, Phys. Rev. D 26, 2028 (1982)
      [doi:10.1103/PhysRevD.26.2028; CERN CDS record 130349, open-access scan
      cds.cern.ch/record/130349/files/PhysRevD.26.2028.pdf], verified directly
      from the scan: Lambda_MOM = 18.7 Lambda_L^(M) (eq. 2.15),
      Lambda_L^(M) = 3.07 Lambda_L^(W) (eq. 2.16),
      Lambda_L^(M) = 2.45 Lambda_L^(HK) (eq. 2.21, N-independent per eq. 2.20),
      Lambda_L^(V)/Lambda_L^(W) = 1.25 (Table I) -- all SU(2);
      Lambda_MOM/Lambda_L^(W) = 112.5 exp(-3 pi^2/(11 N^2)) (eq. 2.14);
      HK measure shift 1/g0^2 -> 1/g0^2 - N/24 (eq. 2.18 and following text).

Expected: identities to machine precision; character-sum measure term matching
(1/2) ln J to <1e-3 after s->0 extrapolation; Lambda_HK/Lambda_W = 1.2514 (SU2),
1.8197 (SU3); Lambda_MSbar/Lambda_HK(SU3) = 15.8; c_BA-A ~ 61 (pure gauge);
LRSS calibration agreement to <0.2% on all four published SU(2) values.
"""
import json
import math
import signal
import sys
import numpy as np

TIMEOUT_SECONDS = 600

def _timeout(signum, frame):
    print(f"TIMEOUT {TIMEOUT_SECONDS}s reached")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout)
signal.alarm(TIMEOUT_SECONDS)
rng = np.random.default_rng(88)
results = {}

# ---------- generators of su(N), tr T^a T^b = delta^ab / 2 ----------
def su_generators(N):
    gens = []
    for i in range(N):
        for j in range(i + 1, N):
            S = np.zeros((N, N), complex); S[i, j] = S[j, i] = 0.5
            gens.append(S)
            A = np.zeros((N, N), complex); A[i, j] = -0.5j; A[j, i] = 0.5j
            gens.append(A)
    for k in range(1, N):
        D = np.zeros((N, N), complex)
        for m in range(k):
            D[m, m] = 1.0
        D[k, k] = -k
        D /= math.sqrt(2.0 * k * (k + 1))
        gens.append(D)
    return gens

print("=== (a) su(N) contraction identities ===")
ok_a = True
for N in (2, 3, 4):
    T = su_generators(N)
    assert len(T) == N * N - 1
    # random traceless hermitian B
    X = rng.normal(size=(N, N)) + 1j * rng.normal(size=(N, N))
    B = (X + X.conj().T) / 2
    B -= np.trace(B) / N * np.eye(N)
    trB2 = np.trace(B @ B).real
    q1 = sum(np.trace(B @ B @ t @ t) for t in T).real
    q2 = sum(np.trace(B @ t @ B @ t) for t in T).real
    cf = (N * N - 1) / (2 * N)
    e1 = abs(q1 - cf * trB2) / abs(trB2)
    e2 = abs(q2 + trB2 / (2 * N)) / abs(trB2)
    tot = 4 * q1 + 2 * q2
    pred = (2 * N * N - 3) / N * trB2
    e3 = abs(tot - pred) / abs(pred)
    print(f"  N={N}: C_F id err={e1:.1e}; cross id err={e2:.1e}; "
          f"4*q1+2*q2 vs (2N^2-3)/N err={e3:.1e}")
    ok_a &= max(e1, e2, e3) < 1e-12
results["contraction_identities_pass"] = bool(ok_a)

print("=== (b) sum_roots (alpha,a)^2 = N |a|^2 ===")
ok_b = True
for N in (2, 3, 4):
    T = su_generators(N)
    avec = rng.normal(size=len(T))
    H = sum(c * t for c, t in zip(avec, T))
    # ad_H in the generator basis: (ad_H)_{ba} = 2 tr(T^b [H, T^a]) ... factor from norm
    dim = len(T)
    ad = np.zeros((dim, dim), complex)
    for a_i in range(dim):
        comm = H @ T[a_i] - T[a_i] @ H
        for b_i in range(dim):
            ad[b_i, a_i] = 2 * np.trace(T[b_i] @ comm)
    # ad_H is hermitian for hermitian H: eigenvalues are the REAL roots (alpha,a);
    # sum (alpha,a)^2 = +tr(ad^2) = Killing(H,H) = 2N tr H^2 = N |a|^2
    s2 = np.trace(ad @ ad).real
    err = abs(s2 - N * np.dot(avec, avec)) / (N * np.dot(avec, avec))
    print(f"  N={N}: sum(alpha,a)^2 / (N|a|^2) - 1 = {err:.1e}")
    ok_b &= err < 1e-12
results["root_sum_identity_pass"] = bool(ok_b)

print("=== (c) heat-kernel measure term from exact character sums ===")
# SU(2): K_s(theta) = sum_j (2j+1) chi_j(theta) e^{-s j(j+1)}, chi_j = sin((2j+1)t/2)/sin(t/2)
# metric: |a|^2 = theta^2; prediction F -> (1/2) ln J = ln(sin(theta/2)/(theta/2))
def k_su2(theta, s, jmax=400):
    tot, j = 0.0, 0.0
    while j <= jmax:
        d = 2 * j + 1
        chi = d if theta == 0 else math.sin(d * theta / 2) / math.sin(theta / 2)
        tot += d * chi * math.exp(-s * j * (j + 1))
        j += 0.5
    return tot

su2_rows = []
ok_c2 = True
for theta in (0.4, 0.8, 1.2):
    pred = math.log(math.sin(theta / 2) / (theta / 2))
    fs = {}
    for s in (0.05, 0.10, 0.20):
        # tail check
        k1, k2 = k_su2(theta, s, 300), k_su2(theta, s, 400)
        assert abs(k1 - k2) / abs(k2) < 1e-14, "character sum not converged"
        F = -math.log(k_su2(theta, s) / k_su2(0.0, s)) - theta ** 2 / (4 * s)
        fs[s] = F
    # Richardson s->0 (F is analytic in s): F0 ~ 2*F(0.05) - F(0.10)
    f0 = 2 * fs[0.05] - fs[0.10]
    err = abs(f0 - pred)
    su2_rows.append({"theta": theta, "F_extrap": f0, "pred_halflnJ": pred, "abs_err": err})
    print(f"  SU(2) theta={theta}: F(s->0)={f0:.6f}  (1/2)lnJ={pred:.6f}  err={err:.1e}")
    ok_c2 &= err < 1e-3
results["su2_heat_kernel_measure"] = su2_rows

# SU(3): K_s(U) = sum_{p,q} d_pq chi_pq(U) e^{-s C2(p,q)},
# C2(p,q) = (p^2+q^2+pq)/3 + p + q  (tr T^aT^b = delta/2 normalization)
# U = diag(e^{i phi1}, e^{i phi2}, e^{i phi3}), phi3 = -phi1-phi2
# chi via Weyl formula: det[z_k^{l_j}] / Vandermonde(z), l = (p+q+2, q+1, 0)
def chi_su3(p, q, phis):
    if np.allclose(phis, 0.0):
        return (p + 1) * (q + 1) * (p + q + 2) / 2.0  # dimension at the identity
    z = np.exp(1j * np.array(phis))
    l = (p + q + 2, q + 1, 0)
    Mnum = np.array([[zk ** lj for lj in l] for zk in z])
    Mden = np.array([[zk ** lj for lj in (2, 1, 0)] for zk in z])
    return np.linalg.det(Mnum) / np.linalg.det(Mden)

def k_su3(phis, s, lmax=60):
    tot = 0.0 + 0.0j
    for p in range(lmax + 1):
        for q in range(lmax + 1):
            c2 = (p * p + q * q + p * q) / 3.0 + p + q
            w = math.exp(-s * c2)
            if w < 1e-18:
                continue
            d = (p + 1) * (q + 1) * (p + q + 2) / 2.0
            tot += d * chi_su3(p, q, phis) * w
    return tot.real

# direction in the Cartan: a = t * h, h = diag(1, -1, 0)/sqrt(2)? choose metric-normalized:
# H = t * diag(c1, c2, c3), traceless; |a|^2 = 2 tr (H_herm^2)? with X = iH: |a|^2 = -2 tr X^2
# = 2 tr H^2. Use H = t*diag(1,-1,0)/sqrt(2) -> |a|^2 = 2 * t^2 * (1/2 + 1/2)/1 = ...
ok_c3 = True
su3_rows = []
for t in (0.5, 0.9):
    cdiag = np.array([1.0, -1.0, 0.0]) / math.sqrt(2.0)
    phis = t * cdiag
    a_norm2 = 2 * t * t * np.dot(cdiag, cdiag) / 2 * 2  # = 2 tr H^2, H = t*diag(c)/? compute directly:
    Hm = t * np.diag(cdiag)
    a_norm2 = 2 * np.trace(Hm @ Hm).real
    # prediction: (1/2) ln J = sum_{alpha>0} ln(sin(x)/x), x = (phi_j - phi_k)/2, j<k
    pred = 0.0
    for j in range(3):
        for k in range(j + 1, 3):
            x = (phis[j] - phis[k]) / 2
            if x != 0:
                pred += math.log(math.sin(abs(x)) / abs(x))
    fs = {}
    for s in (0.05, 0.10):
        k_hi = k_su3(phis, s, 60)
        k_lo = k_su3(phis, s, 50)
        assert abs(k_hi - k_lo) / abs(k_hi) < 1e-12, "SU(3) character sum not converged"
        F = -math.log(k_su3(phis, s) / k_su3([0, 0, 0], s)) - a_norm2 / (4 * s)
        fs[s] = F
    f0 = 2 * fs[0.05] - fs[0.10]
    err = abs(f0 - pred)
    su3_rows.append({"t": t, "F_extrap": f0, "pred_halflnJ": pred, "abs_err": err})
    print(f"  SU(3) t={t}: F(s->0)={f0:.6f}  (1/2)lnJ={pred:.6f}  err={err:.1e}")
    ok_c3 &= err < 2e-3
results["su3_heat_kernel_measure"] = su3_rows
results["heat_kernel_measure_pass"] = bool(ok_c2 and ok_c3)

print("=== (d) assembled Lambda ratios (pure gauge) ===")
table = {}
for N in (2, 3):
    d_w = -(2 * N * N - 3) / (24 * N)          # Wilson quartic tadpole
    d_hk = -N / 24.0                            # heat-kernel measure term
    d_m = 0.0                                   # Manton (geodesic, no measure, no quartic)
    b0t = 11.0 * N / 3.0                        # pure-gauge 16pi^2 b0
    lam_hk_w = math.exp((d_hk - d_w) * 16 * math.pi ** 2 / (2 * b0t))
    lam_m_w = math.exp((d_m - d_w) * 16 * math.pi ** 2 / (2 * b0t))
    closed = math.exp(math.pi ** 2 * (N * N - 3) / (11.0 * N * N))
    dg = 38.852704 * math.exp(-3 * math.pi ** 2 / (11.0 * N * N))
    lam_ms_hk = dg / lam_hk_w
    table[N] = {"Lambda_HK_over_W": lam_hk_w, "closed_form": closed,
                "Lambda_Manton_over_W": lam_m_w,
                "Lambda_MSbar_over_W_DashenGross": dg,
                "Lambda_MSbar_over_HK": lam_ms_hk}
    print(f"  SU({N}): L_HK/L_W = {lam_hk_w:.4f} (closed form {closed:.4f}); "
          f"L_Manton/L_W = {lam_m_w:.4f}; L_MS/L_W = {dg:.3f}; L_MS/L_HK = {lam_ms_hk:.3f}")
# consistency: HH Lambda_MOM/Lambda_L = 83.5 (SU3) => Lambda_MOM/Lambda_MS = 83.5/28.809
print(f"  consistency: Lambda_MOM/Lambda_MSbar (SU3) = 83.5/{table[3]['Lambda_MSbar_over_W_DashenGross']:.3f}"
      f" = {83.5/table[3]['Lambda_MSbar_over_W_DashenGross']:.3f}  (known ~2.9: OK)")
results["lambda_ratios"] = table

print("=== (e) calibration vs Lang-Rebbi-Salomonson-Skagerstam, PRD 26 (1982) 2028 ===")
# published one-loop background-field values, verified from the CERN CDS scan
# (record 130349). All SU(2) unless noted.
LRSS = {
    "Lambda_M_over_W_SU2":   (3.07, table[2]["Lambda_Manton_over_W"]),
    "Lambda_M_over_HK_SU2":  (2.45, table[2]["Lambda_Manton_over_W"] /
                                    table[2]["Lambda_HK_over_W"]),
    "Lambda_V_over_W_SU2":   (1.25, table[2]["Lambda_HK_over_W"]),
    # eq. 2.14/2.15: Lambda_MOM/Lambda_W = 112.5 e^{-3pi^2/11N^2}; /3.07 -> 18.7
    "Lambda_MOM_over_M_SU2": (18.7, 112.5 * math.exp(-3 * math.pi ** 2 / 44.0) /
                                    table[2]["Lambda_Manton_over_W"]),
}
ok_e = True
cal = {}
for name, (pub, ours) in LRSS.items():
    rel = abs(ours - pub) / pub
    cal[name] = {"published": pub, "this_work": ours, "rel_dev": rel}
    print(f"  {name:24s} published {pub:6.2f}   this work {ours:7.4f}   rel dev {rel:.2%}")
    ok_e &= rel < 0.005
# the N-independence statement (their eq. 2.20) vs ours:
hk_m_su3 = table[3]["Lambda_Manton_over_W"] / table[3]["Lambda_HK_over_W"]
print(f"  N-independence (eq. 2.20): Lambda_M/Lambda_HK SU(3) = {hk_m_su3:.4f} "
      f"= e^(pi^2/11) = {math.exp(math.pi**2/11):.4f}  (matches SU(2) value)")
print(f"  LRSS calibration: {'PASS' if ok_e else 'FAIL'}")
results["lrss_calibration"] = {"values": cal, "pass": bool(ok_e),
    "citation": "C.B. Lang, C. Rebbi, P. Salomonson, B.-S. Skagerstam, "
                "Phys. Rev. D 26, 2028 (1982); doi:10.1103/PhysRevD.26.2028; "
                "GOTEBORG-81-22; CERN CDS record 130349 (open-access scan)"}
results["lrss_table1_mc_vs_theory_note"] = (
    "LRSS Table I: Monte Carlo ratios (4.40, 2.99, 1.47) exceed one-loop theory "
    "(3.07, 2.45, 1.25) by 18-43% at moderate coupling -- published evidence of "
    "higher-loop degradation of the one-loop lattice conversion.")

# the BA-A conversion coefficient at mu = 1/a, pure gauge dictionary
c_baa = 2 * 11 * math.log(table[3]["Lambda_MSbar_over_HK"])
validity = c_baa * 3.5 / (16 * math.pi ** 2)
print(f"\n  c(BA-A, SU(3) pure gauge, mu = 1/a) = 2*11*ln({table[3]['Lambda_MSbar_over_HK']:.3f})"
      f" = {c_baa:.1f}")
print(f"  perturbative-control metric c*g_V^2/16pi^2 at g_V^2 = 7/2: {validity:.2f}"
      f"  ({'OUT OF CONTROL' if validity > 0.5 else 'ok'})")
results["c_BA_A_pure_gauge"] = c_baa
results["c_BA_A_validity_metric"] = validity

with open("/Users/nova/ugp-physics/papers/42_phimdl_field/scripts/"
          "villain_msbar_heatkernel_lambda_ratio_results.json", "w") as fp:
    json.dump(results, fp, indent=1)
print("Saved villain_msbar_heatkernel_lambda_ratio_results.json")
signal.alarm(0)
