"""
te2_4_page_curve_thermal.py — COMP-P16-D
Purified Thermal BH Page Curve (Canonical Script)

Physically correct setup for a thermal black hole:
- Purify the thermal BH state using a reference system R (BH interior)
- Total pure initial state: |Φ+⟩_BH,R ⊗ |0⟩^n_rad
  (maximally entangled BH–R = purification of maximally mixed = thermal BH)
- BH evaporates into radiation via partial-SWAP unitaries on (BH qubit k, rad qubit k)
- R is untouched throughout (= island formula setup)

Expected results (Page 1993):
- S_BH starts at log(d_BH) = thermal entropy
- S_BH decreases monotonically; S_rad increases; Page crossing at n/2 modes
- S_BH = 0 after full evaporation (all entropy in radiation)
- PT^{-1} = U†_evap restores BH–R entanglement to F = 1.000000

Run:
    python3 te2_4_page_curve_thermal.py
Output:
    ../results/page_curve_thermal/results_3modes_thermal.json (canonical)
    ../results/page_curve_thermal/results_4modes_thermal.json (extended)
"""
import numpy as np
import json
import hashlib
import time
from pathlib import Path


def von_neumann_entropy(rho):
    ev = np.linalg.eigvalsh(rho + 1e-14 * np.eye(rho.shape[0]))
    ev = ev[ev > 1e-13]
    return float(-np.sum(ev * np.log(ev)))


def partial_trace(rho, keep_dims, all_dims):
    """
    Partial trace: keep subsystems in keep_dims, trace over the rest.
    all_dims: list of integer dimensions for each subsystem.
    """
    n = len(all_dims)
    trace_dims = [i for i in range(n) if i not in keep_dims]
    d_keep = int(np.prod([all_dims[i] for i in keep_dims]))
    d_trace = int(np.prod([all_dims[i] for i in trace_dims]))
    # Permute: kept dims first (bra and ket), traced dims last
    perm = list(keep_dims) + list(trace_dims)
    full_perm = perm + [p + n for p in perm]
    rho_r = np.transpose(rho.reshape(list(all_dims) * 2), full_perm)
    rho_p = rho_r.reshape(d_keep, d_trace, d_keep, d_trace)
    return np.einsum('iaja->ij', rho_p)


def build_swap_unitary(nq, bq, rq_rad, theta, db, dR, dr):
    """
    Partial-SWAP unitary acting on BH qubit bq and rad qubit rq_rad.
    Space: H_BH ⊗ H_R ⊗ H_rad.  R is untouched.

    U: |0,0⟩ → |0,0⟩;  |1,1⟩ → |1,1⟩
       |0,1⟩ → cos(θ)|0,1⟩ − i sin(θ)|1,0⟩
       |1,0⟩ → cos(θ)|1,0⟩ − i sin(θ)|0,1⟩
    """
    c, s = np.cos(theta), np.sin(theta)
    dt = db * dR * dr

    bh_all   = np.arange(db)
    R_all    = np.arange(dR)
    rad_all  = np.arange(dr)
    bh_g, R_g, rad_g = np.meshgrid(bh_all, R_all, rad_all, indexing='ij')
    flat_idx = bh_g * dR * dr + R_g * dr + rad_g

    bh_bit  = (bh_g  >> (nq - 1 - bq))     & 1
    rad_bit = (rad_g >> (nq - 1 - rq_rad)) & 1

    U = np.zeros((dt, dt), dtype=np.complex128)

    same = bh_bit == rad_bit
    idx_same = flat_idx[same].ravel()
    U[idx_same, idx_same] += 1.0

    m01 = (bh_bit == 0) & (rad_bit == 1)
    idx_01 = flat_idx[m01].ravel()
    bh_f = bh_g[m01] ^ (1 << (nq - 1 - bq))
    rad_f = rad_g[m01] ^ (1 << (nq - 1 - rq_rad))
    idx_flipped_01 = (bh_f * dR * dr + R_g[m01] * dr + rad_f).ravel()
    U[idx_01, idx_01] += c
    U[idx_flipped_01, idx_01] += -1j * s

    m10 = (bh_bit == 1) & (rad_bit == 0)
    idx_10 = flat_idx[m10].ravel()
    bh_f = bh_g[m10] ^ (1 << (nq - 1 - bq))
    rad_f = rad_g[m10] ^ (1 << (nq - 1 - rq_rad))
    idx_flipped_10 = (bh_f * dR * dr + R_g[m10] * dr + rad_f).ravel()
    U[idx_10, idx_10] += c
    U[idx_flipped_10, idx_10] += -1j * s

    return U


def run_thermal_page_curve(nq: int = 3, n_steps: int = 20) -> dict:
    """
    Run the purified thermal BH Page curve for nq modes.
    """
    db = dR = dr = 2 ** nq
    theta = (np.pi / 2) / n_steps
    all_dims = [db, dR, dr]

    # Initial state: |Φ+⟩_BH,R ⊗ |0⟩^n_rad
    psi = np.zeros(db * dR * dr, dtype=np.complex128)
    for i in range(db):
        psi[i * dR * dr + i * dr + 0] = 1.0 / np.sqrt(db)
    rho = np.outer(psi, psi.conj())

    S_bh  = [von_neumann_entropy(partial_trace(rho, [0], all_dims))]
    S_rad = [von_neumann_entropy(partial_trace(rho, [2], all_dims))]
    S_R   = [von_neumann_entropy(partial_trace(rho, [1], all_dims))]
    pur   = [float(np.real(np.trace(rho @ rho)))]
    ts    = [0.0]
    U_acc = np.eye(db * dR * dr, dtype=np.complex128)

    print(f"nq={nq}: S_BH_initial={S_bh[0]:.4f}, S_R={S_R[0]:.4f}, S_rad={S_rad[0]:.4f}")

    t0 = time.time()
    for mode in range(nq):
        for step in range(n_steps):
            Uf = build_swap_unitary(nq, mode, mode, theta, db, dR, dr)
            rho = Uf @ rho @ Uf.conj().T
            rho = (rho + rho.conj().T) / 2
            U_acc = Uf @ U_acc
            ts.append(float(len(ts)))
            S_bh.append(von_neumann_entropy(partial_trace(rho, [0], all_dims)))
            S_rad.append(von_neumann_entropy(partial_trace(rho, [2], all_dims)))
            S_R.append(von_neumann_entropy(partial_trace(rho, [1], all_dims)))
            pur.append(float(np.real(np.trace(rho @ rho))))
        print(f"  Mode {mode+1}/{nq} ({time.time()-t0:.1f}s): "
              f"S_BH={S_bh[-1]:.4f}, S_R={S_R[-1]:.4f}, S_rad={S_rad[-1]:.4f}, purity={pur[-1]:.6f}")

    S_arr = np.array(S_bh)
    t_page_idx = int(np.argmax(S_arr))

    # PT^{-1}: apply U_acc† to restore BH–R entanglement
    rho_rec = U_acc.conj().T @ rho @ U_acc
    rho_rec = (rho_rec + rho_rec.conj().T) / 2
    rho_bhr_rec = partial_trace(rho_rec, [0, 1], all_dims)
    psi_bhr = np.zeros(db * dR, dtype=np.complex128)
    for i in range(db):
        psi_bhr[i * dR + i] = 1.0 / np.sqrt(db)
    F_bhr = float(np.real(psi_bhr.conj() @ rho_bhr_rec @ psi_bhr))
    rho_bh_rec = partial_trace(rho_rec, [0], all_dims)

    print(f"\n  t_page={ts[t_page_idx]:.1f}, S_BH_peak={S_arr[t_page_idx]:.4f}")
    print(f"  S_BH_final={S_bh[-1]:.6f}, entropy_turns_over={float(S_bh[-1]) < float(S_arr[t_page_idx])*0.5}")
    print(f"  PT^{{-1}}: F(BH-R restored)={F_bhr:.8f}, S_BH_rec={von_neumann_entropy(rho_bh_rec):.6f}")

    return {
        "config": {
            "nq": nq, "n_steps": n_steps, "theta": float(theta),
            "dim_total": db * dR * dr,
            "initial_state": "|Phi+>_BH,R x |0>_rad (purified thermal BH)",
            "physical_interpretation": (
                "Thermal BH purified by reference R (= BH interior). "
                "Evaporation U_evap on BH+rad; R untouched. "
                "Island formula setup."
            ),
        },
        "page_curve": {
            "times": [float(x) for x in ts],
            "S_bh":  [float(x) for x in S_bh],
            "S_rad": [float(x) for x in S_rad],
            "S_R":   [float(x) for x in S_R],
            "purity": [float(x) for x in pur],
            "t_page": float(ts[t_page_idx]),
            "S_bh_peak": float(S_arr[t_page_idx]),
            "S_bh_initial": float(S_bh[0]),
            "S_bh_final": float(S_bh[-1]),
            "S_rad_final": float(S_rad[-1]),
            "S_R_final": float(S_R[-1]),
            "entropy_turns_over": bool(float(S_bh[-1]) < float(S_arr[t_page_idx]) * 0.5),
        },
        "pt_inverse": {
            "F_BHR_restored": float(F_bhr),
            "S_BH_recovered": float(von_neumann_entropy(rho_bh_rec)),
        },
    }


if __name__ == "__main__":
    out_dir = Path("../results/page_curve_thermal")
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("COMP-P16-D: Purified Thermal BH Page Curve")
    print("=" * 60)

    # Canonical run: nq=3 (512-dim total space, fast)
    print("\n[1/2] Canonical run: nq=3")
    t0 = time.time()
    res3 = run_thermal_page_curve(nq=3, n_steps=20)
    elapsed3 = time.time() - t0
    sha3 = hashlib.sha256(json.dumps(res3, sort_keys=True, default=float).encode()).hexdigest()
    res3["sha256"] = sha3
    with open(out_dir / "results_3modes_thermal.json", "w") as f:
        json.dump(res3, f, indent=2)
    print(f"  Saved results_3modes_thermal.json ({elapsed3:.1f}s) | SHA: {sha3[:20]}...")

    # Extended run: nq=4 (4096-dim, ~few minutes)
    print("\n[2/2] Extended run: nq=4")
    t0 = time.time()
    res4 = run_thermal_page_curve(nq=4, n_steps=20)
    elapsed4 = time.time() - t0
    sha4 = hashlib.sha256(json.dumps(res4, sort_keys=True, default=float).encode()).hexdigest()
    res4["sha256"] = sha4
    with open(out_dir / "results_4modes_thermal.json", "w") as f:
        json.dump(res4, f, indent=2)
    print(f"  Saved results_4modes_thermal.json ({elapsed4:.1f}s) | SHA: {sha4[:20]}...")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for label, res in [("nq=3", res3), ("nq=4", res4)]:
        pc = res["page_curve"]; pt = res["pt_inverse"]
        print(f"  {label}: S_BH_initial={pc['S_bh_initial']:.4f}, "
              f"S_BH_final={pc['S_bh_final']:.6f}, "
              f"turns_over={pc['entropy_turns_over']}, "
              f"F_BHR={pt['F_BHR_restored']:.8f}")
