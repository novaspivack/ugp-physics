
# Reflexive Reality — Computational Templates

This folder provides three executable Python templates you can adapt directly in your UGP/MFRR Discovery Lab:

1. `constraint_solver_palette.py`  
   - Verifies and evaluates the FPSM Elegant-Kernel palette on canonical triples.  
   - Enforces the Quarter-Lock law `k_M = k_gen2 + 1/4 k_L2` and fixed algebraic constants  
     `k_L2 = 7/512`, `k_gen2 = -phi/2`, `k_gen = pi/2`, `(k_a,k_b,k_c)=(1/8,-3/2,4/3)`.  
   - Computes derived linear terms per FPSM (reparam.)  
     `k_L = -2 k_L2 (-3/2 log phi)`, `k_const = -1/(2*pi) + k_L2 (-3/2 log phi)^2`.  
   - Evaluates `Cf` for canonical leptonic triples (electron, muon, tau) with and without the URC delta(log Cf).  
   - Prints the orthogonality `n·k` with `n = (-1/4, -1, +1)` to confirm QL plane preservation.

2. `pt_normal_step_integrator.py`  
   - Integrates the PT-induced normal step in invariant space (MFRR sec. 9.4):  
     `dk/d ln mu = beta(k) - 2 rho_PT lambda(Epsi) (n·k) n` with QL normal `n = grad(k_M - k_gen2 - 1/4 k_L2)`.  
   - Plug in your own `beta(k)`, `rho_PT(mu)`, and `lambda(Epsi)` models.  
   - Diagnostics print `final n·k` and `J_PT · tau_plane` for a user-supplied in-plane tangent `tau` (should be ~ 0).  
   - Writes the trajectory to `pt_traj.json` for downstream plotting/analysis.

3. `frw_psi_solver.py`  
   - Minimal flat FRW + Psi(t) solver (canonical scalar with effective potential `V_eff`).  
   - Equations follow MFRR sec. 7.7 and 7.19; default units set `8*pi*G = 1`.  
   - Choose potential parameters `(m, beta, <omega>, V0)` and a dynamical cosmological term via `Lambda_eff`.  
   - Produces `frw_psi_series.json` with time series `{t, a, H, psi, psidot, rhoPsi, rho_m, rho_L}`.

## Quick start
```bash
python3 constraint_solver_palette.py
python3 pt_normal_step_integrator.py
python3 frw_psi_solver.py
```

## Integration Notes
- The palette formulas and Quarter-Lock law are taken from *First_Principles_Standard_Model.pdf* (FPSM) sec. 4.7 eqs. (10)-(13).  
- The PT normal source and bundle FRW+Psi equations follow *Mathematical_Foundations_of_Reflexive_Reality.pdf* (MFRR) sec. 7.7, 9.1-9.4, 7.19.
