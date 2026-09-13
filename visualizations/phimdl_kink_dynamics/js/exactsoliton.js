// Exact N-soliton solutions of the pure-phi Z7 sector, via the Hirota
// tau-function of the standard sine-Gordon equation carried to Phi = psi/7
// by the exact psi = 7*Phi rescaling. Direct port of a reference Python
// implementation of the same formula, checked there against an
// EOM-residual validation (max residual 5.3e-14 through N=8, dynamical
// PDE match 7.4e-4 at N=6) and re-verified independently here (see
// verify_exact_soliton.mjs). The formula:
//
//   tau(x,t) = sum_{mu in {0,1}^N} prod_j (i*eps_j*e^{eta_j})^{mu_j}
//                                  * exp( sum_{i<j} mu_i*mu_j*A_ij )
//   eta_j = cosh(theta_j)*(x - x0_j) - sinh(theta_j)*t
//   A_ij  = 2*ln|tanh((theta_i - theta_j)/2)|
//   psi(x,t) = 4*arg(tau)   (continuous via phase unwrapping in x)
//   Phi = psi/7                          (GTE normalization; unit kink
//                                          amplitude 2*pi/7, energies /49)
//
// with rapidity theta_j = atanh(v_j) and topological charge eps_j = +-1
// (kink/antikink). This module evaluates Phi(x,t) directly (no numerical
// differentiation needed for the app's overlay + residual use case).
//
// Performance: the subset sum has 2^N terms, evaluated in full for every
// sample point. This is the exact same algorithm as the Python reference
// (itertools.product enumeration) with bitmask enumeration in place of
// itertools. See MAX_EXACT_SOLITONS below for the real-time cap this
// implies.
//
// Branch/vacuum-anchor note: the Hirota tau construction fixes psi = 4*arg
// tau only up to an overall additive integer multiple of the fundamental
// sine-Gordon period 2*pi (one elementary GTE vacuum step, STEP = 2*pi/7,
// after the psi = 7*Phi rescaling) -- this is a genuine branch-choice
// feature of the bilinear method (which coefficient phase i^n the leftmost
// asymptotic vacuum happens to land on depends on the sign/velocity
// pattern of the solitons), not a numerical bug. Verified directly:
// verify_exact_soliton.mjs checks 1-1 that phiOnGrid()'s N=1 case matches
// the closed-form boosted BPS profile to machine precision with NO
// correction needed, while the N=2 closed-form checks require exactly this
// one-period anchor correction to match -- confirming the ambiguity is
// exactly an integer number of steps, as the theory predicts, not an
// arbitrary error. phiOnGrid() below anchors every evaluation so that the
// leftmost sample equals the given anchor vacuum value (the field's actual
// left boundary condition, Field1D.bcl) to fix this ambiguity uniquely.

// 2^10 = 1024 subset terms; at N_EXACT_SAMPLES ~1000 points this stays
// comfortably inside one animation frame (~10-20ms) on ordinary hardware.
// Configurations with more active kinks than this are analytically valid
// but not evaluated live -- see validateKinkSpecs().
export const MAX_EXACT_SOLITONS = 10;

const STEP = (2 * Math.PI) / 7;

// Rapidities within this separation are treated as degenerate (the Hirota
// tau function has a genuine mathematical singularity there: A_ij -> -inf
// as theta_i -> theta_j, i.e. tanh(0) = 0 inside a log). Two kinks placed
// with (numerically) identical velocity have no well-defined N-soliton
// decomposition, so this is a real limitation of the formula, not just a
// numerical-precision guard.
export const MIN_RAPIDITY_SEPARATION = 1e-4;

// Below this position separation, two kinks are too close together for the
// well-separated dominance-ordering assumption behind the scattering-shift
// correction (see the constructor note below) to hold -- the app's own
// addKink() initial condition is itself only physically meaningful for
// kinks placed with at least a few kink-widths of separation, so this is a
// real limitation of the well-separated construction, not just a guard.
export const MIN_POSITION_SEPARATION = 3;

const clampV = (v) => Math.max(-0.999999, Math.min(0.999999, v));

export class NSoliton {
  // kinks: [{ x0, v, sign }], sign = +1 kink / -1 antikink, matching the
  // arguments passed to Field1D.addKink(): x0 is the PHYSICAL position
  // where that kink's own profile is centered at t = 0, exactly as
  // addKink(xc, v, sign) places it.
  //
  // Scattering-shift correction (this is what makes the constructor's
  // output match Field1D's actual initial condition, not just an
  // approximation of it): the raw Hirota tau parameter delta_j = -k_j*x0_j
  // does NOT place soliton j's own transition at x0_j once other solitons
  // are also present -- the pairwise term A_ij is a fixed function of the
  // rapidities alone (it does not decay with separation), so it shifts
  // where each soliton's transition actually falls relative to its bare
  // x0 parameter by a fixed amount that depends on which other solitons
  // are already "included" at that point in the left-to-right dominance
  // sweep. For a well-separated configuration that has not yet collided
  // (the case whenever the app places kinks via addKink()), that
  // dominance order is simply the sort order of the intended physical
  // positions, and the required correction for the soliton at sorted
  // index m is exactly (1/k_m) * sum_{l<m} A[l][m] added to its physical
  // x0 (derived by equating the dominant-subset boundary condition E_mu =
  // E_{mu with bit m added} at x = X_m; verified in verify_exact_soliton.mjs
  // to reduce the tau solution's deviation from the naive well-separated
  // sum-of-boosted-profiles ansatz from O(1) to machine precision for both
  // same-sign and opposite-sign well-separated pairs). This is exactly the
  // same physical effect as the textbook soliton "scattering phase shift"
  // (e.g. delta = ln(1/v)/gamma for the symmetric head-on case) generalized
  // to an arbitrary well-ordered N-soliton configuration.
  constructor(kinks) {
    const N = kinks.length;
    this.N = N;
    const theta = kinks.map((k) => Math.atanh(clampV(k.v)));
    const eps = kinks.map((k) => k.sign);
    const kk = theta.map((th) => Math.cosh(th));
    const ww = theta.map((th) => Math.sinh(th));

    // Pairwise interaction exponent A_ij = 2*ln|tanh((th_i - th_j)/2)|.
    const A = [];
    for (let i = 0; i < N; i++) {
      A.push(new Float64Array(N));
      for (let j = 0; j < N; j++) {
        if (i === j) continue;
        A[i][j] = 2 * Math.log(Math.abs(Math.tanh(0.5 * (theta[i] - theta[j]))));
      }
    }

    // Scattering-shift correction: order = indices sorted by intended
    // physical position, ascending.
    const order = kinks.map((_, i) => i).sort((a, b) => kinks[a].x0 - kinks[b].x0);
    const x0Corrected = new Float64Array(N);
    for (let m = 0; m < order.length; m++) {
      const j = order[m];
      let shift = 0;
      for (let l = 0; l < m; l++) shift += A[order[l]][j];
      x0Corrected[j] = kinks[j].x0 + shift / kk[j];
    }
    const delta = kk.map((ki, i) => -ki * x0Corrected[i]);

    const M = N === 0 ? 1 : (1 << N);
    this.M = M;
    this.Kmu = new Float64Array(M);
    this.Wmu = new Float64Array(M);
    this.Dmu = new Float64Array(M);
    this.coeffRe = new Float64Array(M);
    this.coeffIm = new Float64Array(M);

    for (let mu = 0; mu < M; mu++) {
      let Kmu = 0, Wmu = 0, Dmu = 0, Amu = 0, nAct = 0, epsProd = 1;
      for (let i = 0; i < N; i++) {
        if (!(mu & (1 << i))) continue;
        Kmu += kk[i]; Wmu += ww[i]; Dmu += delta[i]; nAct++; epsProd *= eps[i];
        for (let j = i + 1; j < N; j++) {
          if (mu & (1 << j)) Amu += A[i][j];
        }
      }
      this.Kmu[mu] = Kmu; this.Wmu[mu] = Wmu; this.Dmu[mu] = Dmu + Amu;
      // coeff = i^nAct * epsProd  (i^n cycles through 1, i, -1, -i)
      const r = ((nAct % 4) + 4) % 4;
      const cr = r === 0 ? 1 : (r === 2 ? -1 : 0);
      const ci = r === 1 ? 1 : (r === 3 ? -1 : 0);
      this.coeffRe[mu] = cr * epsProd;
      this.coeffIm[mu] = ci * epsProd;
    }
  }

  // Continuous Phi(x) at fixed t across a sorted (ascending) x array, via
  // phase unwrapping of arg(tau) -- direct port of phi_on_grid() in the
  // Python reference, plus the one-period branch anchor described above
  // (xs[0] should sit deep enough in the asymptotic vacuum for the anchor
  // to be unambiguous -- true whenever the leftmost sample is well outside
  // every kink's core). Returns a new Float64Array of the same length as
  // xs. `anchor` is the known left-boundary vacuum value (Field1D.bcl).
  phiOnGrid(xs, t, anchor = 0) {
    const M = this.M, n = xs.length;
    const out = new Float64Array(n);
    const E = new Float64Array(M);
    let prevAngle = 0, unwrapped = 0, first = true;
    for (let ix = 0; ix < n; ix++) {
      const x = xs[ix];
      let Emax = -Infinity;
      for (let mu = 0; mu < M; mu++) {
        const e = this.Kmu[mu] * x - this.Wmu[mu] * t + this.Dmu[mu];
        E[mu] = e;
        if (e > Emax) Emax = e;
      }
      let tauRe = 0, tauIm = 0;
      for (let mu = 0; mu < M; mu++) {
        const ex = Math.exp(E[mu] - Emax);
        tauRe += this.coeffRe[mu] * ex;
        tauIm += this.coeffIm[mu] * ex;
      }
      const angle = Math.atan2(tauIm, tauRe);
      if (first) {
        unwrapped = angle;
        first = false;
      } else {
        let d = angle - prevAngle;
        while (d > Math.PI) d -= 2 * Math.PI;
        while (d < -Math.PI) d += 2 * Math.PI;
        unwrapped += d;
      }
      prevAngle = angle;
      out[ix] = (4 * unwrapped) / 7;
    }
    if (n > 0) {
      const correction = Math.round((anchor - out[0]) / STEP) * STEP;
      if (correction !== 0) for (let ix = 0; ix < n; ix++) out[ix] += correction;
    }
    return out;
  }
}

// Validate that a kink-spec list ({x0, v, sign} per active kink, matching
// Field1D.kinkSpecs) is a clean, analytically tractable N-soliton
// configuration. Returns { ok: true } or { ok: false, reason }.
export function validateKinkSpecs(kinkSpecs) {
  const N = kinkSpecs.length;
  if (N === 0) return { ok: true };
  if (N > MAX_EXACT_SOLITONS) {
    return {
      ok: false,
      reason: `exact overlay is limited to ${MAX_EXACT_SOLITONS} active kinks for real-time ` +
              `evaluation (currently ${N}) -- reduce the kink count to enable it`,
    };
  }
  const theta = kinkSpecs.map((k) => Math.atanh(clampV(k.v)));
  for (let i = 0; i < N; i++) {
    for (let j = i + 1; j < N; j++) {
      if (Math.abs(theta[i] - theta[j]) < MIN_RAPIDITY_SEPARATION) {
        return {
          ok: false,
          reason: 'exact solution undefined for this configuration -- two kinks share ' +
                  'the same velocity (the Hirota tau function is singular for equal ' +
                  'rapidities); nudge one velocity to enable the overlay',
        };
      }
      if (Math.abs(kinkSpecs[i].x0 - kinkSpecs[j].x0) < MIN_POSITION_SEPARATION) {
        return {
          ok: false,
          reason: 'exact solution undefined for this configuration -- two kinks were ' +
                  'placed too close together for the well-separated N-soliton ' +
                  'construction used here; place kinks further apart to enable the overlay',
        };
      }
    }
  }
  return { ok: true };
}
