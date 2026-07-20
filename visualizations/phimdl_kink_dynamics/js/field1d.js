// 1+1D leapfrog (Stormer-Verlet) integrator for the Z7 scalar field
//   Phi_tt = Phi_xx - (1/7) sin(7 Phi) - eta (2/7) sin(14 Phi)
// in natural units m = 1. Same stencil, time staggering, and boundary
// treatment as the verified reference integrator (order 2.0, elastic to 3e-8):
// fixed (Dirichlet) boundaries, lap = 0 at the two edge nodes, dt = 0.5 dx
// (stability requires dt <= 0.9 dx).

import { STEP } from './constants.js?v=5';

export class Field1D {
  constructor({ N = 16384, dx = 0.05 } = {}) {
    this.N = N;
    this.dx = dx;
    this.dt = 0.5 * dx;
    this.L = (N - 1) * dx;
    this.x0 = -this.L / 2;
    this.eta = 0;

    this.phi = new Float64Array(N);
    this.vel = new Float64Array(N);   // staggered: v(t + dt/2)
    this.f = new Float64Array(N);     // scratch force
    this.tmp = new Float64Array(N);
    this.t = 0;
    this.bcl = 0;
    this.bcr = 0;
    this.staggered = false;           // whether vel is at t + dt/2
    this.kinkTemplate = null;         // relaxed static profile for eta > 0
    this.E0 = 0;

    // Baseline snapshot of the current configuration (vacuum / random gas /
    // manually-placed kinks), captured every time that configuration is
    // established or extended. Reset replays THIS, not a blank vacuum.
    this._basePhi = null;
    this._baseVel = null;
    this._baseBcl = 0;
    this._baseBcr = 0;

    // Record of the (x0, v, sign) triples passed to addKink() since the
    // last clearToVacuum(), in insertion order -- i.e. exactly the
    // parameters needed to reconstruct "the current configuration" as an
    // exact N-soliton state (js/exactsoliton.js) for the pure-sector exact-
    // overlay feature. Stays in lockstep with the baseline above (both are
    // only mutated by clearToVacuum()/addKink()), so it remains valid
    // across reset()/resetToBaseline() without separate save/restore.
    this.kinkSpecs = [];
  }

  // Record the field as it stands right now as "the current configuration",
  // so a later resetToBaseline() replays it from t=0 instead of wiping it.
  saveBaseline() {
    this._basePhi = this.phi.slice();
    this._baseVel = this.vel.slice();
    this._baseBcl = this.bcl;
    this._baseBcr = this.bcr;
  }

  // Replay the last-saved configuration from t=0. Falls back to plain
  // vacuum only if no configuration has ever been established (should not
  // happen in practice: the constructor always establishes one).
  resetToBaseline() {
    if (!this._basePhi) { this.clearToVacuum(0); return; }
    this.phi.set(this._basePhi);
    this.vel.set(this._baseVel);
    this.bcl = this._baseBcl;
    this.bcr = this._baseBcr;
    this.t = 0;
    this.staggered = false;
    this.E0 = this.energy();
  }

  xAt(i) { return this.x0 + i * this.dx; }
  idxAt(x) { return (x - this.x0) / this.dx; }

  // Linear-interpolated field value at an arbitrary domain position x
  // (clamped to the grid), decoupled from any view/pixel transform --
  // used by the exact-solution residual readout to sample the simulated
  // field at the same domain-fixed positions as the analytic overlay.
  sampleAt(x) {
    const s = Math.max(0, Math.min(this.N - 1.0000001, this.idxAt(x)));
    const i = Math.floor(s), f = s - i;
    return this.phi[i] * (1 - f) + this.phi[i + 1] * f;
  }

  // force = laplacian - V'(phi); V' = (1/7) sin 7p + eta (2/7) sin 14p
  computeForce(p, out) {
    const { N, dx, eta } = this;
    const inv = 1 / (dx * dx);
    out[0] = 0; out[N - 1] = 0;
    if (eta === 0) {
      for (let i = 1; i < N - 1; i++) {
        out[i] = (p[i + 1] - 2 * p[i] + p[i - 1]) * inv - Math.sin(7 * p[i]) / 7;
      }
    } else {
      const c = (2 * eta) / 7;
      for (let i = 1; i < N - 1; i++) {
        out[i] = (p[i + 1] - 2 * p[i] + p[i - 1]) * inv
               - Math.sin(7 * p[i]) / 7 - c * Math.sin(14 * p[i]);
      }
    }
  }

  // Move vel from synchronized (t) to staggered (t + dt/2), or back.
  _stagger() {
    if (this.staggered) return;
    this.computeForce(this.phi, this.f);
    for (let i = 0; i < this.N; i++) this.vel[i] += 0.5 * this.dt * this.f[i];
    this.staggered = true;
  }

  _sync() {
    if (!this.staggered) return;
    this.computeForce(this.phi, this.f);
    for (let i = 0; i < this.N; i++) this.vel[i] -= 0.5 * this.dt * this.f[i];
    this.staggered = false;
  }

  stepN(n) {
    this._stagger();
    const { phi, vel, f, N, dt } = this;
    for (let s = 0; s < n; s++) {
      for (let i = 0; i < N; i++) phi[i] += dt * vel[i];
      phi[0] = this.bcl; phi[N - 1] = this.bcr;
      this.computeForce(phi, f);
      for (let i = 0; i < N; i++) vel[i] += dt * f[i];
      this.t += dt;
    }
  }

  potential(p) {
    const e = this.eta;
    return ((1 - Math.cos(7 * p)) + e * (1 - Math.cos(14 * p))) / 49;
  }

  // Total energy with synchronized velocity (does not disturb evolution).
  energy() {
    const { phi, N, dx } = this;
    let vsync = this.vel;
    if (this.staggered) {
      this.computeForce(phi, this.f);
      const t = this.tmp;
      for (let i = 0; i < N; i++) t[i] = this.vel[i] - 0.5 * this.dt * this.f[i];
      vsync = t;
    }
    let E = 0;
    for (let i = 0; i < N; i++) {
      const ip = i < N - 1 ? i + 1 : i, im = i > 0 ? i - 1 : i;
      const dpx = (phi[ip] - phi[im]) / ((ip - im) * dx);
      E += 0.5 * vsync[i] * vsync[i] + 0.5 * dpx * dpx + this.potential(phi[i]);
    }
    return E * dx;
  }

  // Net topological winding from the boundary plateau difference.
  winding() {
    return (this.phi[this.N - 1] - this.phi[0]) / STEP;
  }

  // All half-plateau level crossings: kink centers. Returns [{x, sign}].
  crossings() {
    const { phi, N } = this;
    let mn = Infinity, mx = -Infinity;
    for (let i = 0; i < N; i++) { const v = phi[i]; if (v < mn) mn = v; if (v > mx) mx = v; }
    const lo = Math.floor(mn / STEP - 0.5), hi = Math.ceil(mx / STEP + 0.5);
    const out = [];
    for (let k = lo; k <= hi; k++) {
      const level = STEP * (k + 0.5);
      let dPrev = phi[0] - level;
      for (let i = 1; i < N; i++) {
        const d = phi[i] - level;
        if ((dPrev < 0 && d >= 0) || (dPrev >= 0 && d < 0)) {
          const frac = dPrev / (dPrev - d);
          out.push({ x: this.xAt(i - 1) + frac * this.dx, sign: d > dPrev ? 1 : -1 });
        }
        dPrev = d;
      }
    }
    out.sort((a, b) => a.x - b.x);
    return out;
  }

  clearToVacuum(k = 0) {
    const v = STEP * k;
    this.phi.fill(v);
    this.vel.fill(0);
    this.bcl = v; this.bcr = v;
    this.t = 0;
    this.staggered = false;
    this.E0 = this.energy();
    this.kinkSpecs = [];
    this.saveBaseline();
  }

  // Relax the static kink profile of the perturbed potential by gradient flow
  // (needed because for eta > 0 the BPS arctan profile is not a static solution).
  // Returns { xs0, dxT, table } sampled on a local window.
  relaxKinkTemplate() {
    const dxT = this.dx, half = 25;
    const n = Math.round(2 * half / dxT) + 1;
    const p = new Float64Array(n);
    for (let i = 0; i < n; i++) {
      p[i] = (4 / 7) * Math.atan(Math.exp(-half + i * dxT));
    }
    const eta = this.eta, dtau = 0.4 * dxT * dxT, inv = 1 / (dxT * dxT);
    const c = (2 * eta) / 7;
    const g = new Float64Array(n);
    for (let it = 0; it < 20000; it++) {
      for (let i = 1; i < n - 1; i++) {
        g[i] = (p[i + 1] - 2 * p[i] + p[i - 1]) * inv
             - Math.sin(7 * p[i]) / 7 - c * Math.sin(14 * p[i]);
      }
      for (let i = 1; i < n - 1; i++) p[i] += dtau * g[i];
    }
    return { half, dxT, table: p };
  }

  _profileAt(u) {
    // Static kink profile Phi(u), u in units of 1/m, rising 0 -> 2pi/7.
    if (this.eta === 0 || !this.kinkTemplate) {
      return (4 / 7) * Math.atan(Math.exp(u));
    }
    const { half, dxT, table } = this.kinkTemplate;
    if (u <= -half) return 0;
    if (u >= half) return STEP;
    const s = (u + half) / dxT, i = Math.floor(s), f = s - i;
    return table[i] * (1 - f) + table[Math.min(i + 1, table.length - 1)] * f;
  }

  setEta(eta) {
    this.eta = eta;
    this.kinkTemplate = eta > 0 ? this.relaxKinkTemplate() : null;
  }

  // Superpose a Lorentz-boosted (anti)kink moving at velocity v, |v| < 1.
  // sign = +1 kink (winding step up), -1 antikink.
  addKink(xc, v, sign) {
    this._sync();
    const g = 1 / Math.sqrt(1 - v * v);
    const { phi, vel, N, dx } = this;
    const eps = 0.5 * dx;
    for (let i = 0; i < N; i++) {
      const u = g * (this.xAt(i) - xc);
      const prof = this._profileAt(u);
      // centered analytic-boost time derivative: Phi_t = -v * dPhi/dx
      const dprof = (this._profileAt(u + g * eps) - this._profileAt(u - g * eps)) / (2 * eps);
      phi[i] += sign * prof;
      vel[i] += -v * sign * dprof;
    }
    this.bcr += sign * STEP;   // profile -> 2pi/7 at +infinity
    phi[0] = this.bcl; phi[N - 1] = this.bcr;
    this.E0 = this.energy();
    this.kinkSpecs.push({ x0: xc, v, sign });
    this.saveBaseline();
  }

  // Random gas of n elementary (anti)kinks with minimum separation,
  // mirroring the reference construction (min sep 15/m, |v| <= vMax).
  randomGas(n, vMax = 0.35, margin = 60) {
    this.clearToVacuum(0);
    const span = this.L - 2 * margin;
    const pos = [];
    for (let i = 0; i < n; i++) pos.push(this.x0 + margin + Math.random() * span);
    pos.sort((a, b) => a - b);
    for (let i = 1; i < n; i++) pos[i] = Math.max(pos[i], pos[i - 1] + 15);
    const mean = pos.reduce((a, b) => a + b, 0) / n;
    const kinks = [];
    for (let i = 0; i < n; i++) {
      const x = pos[i] - mean;
      if (x < this.x0 + margin / 2 || x > -this.x0 - margin / 2) continue;
      const s = Math.random() < 0.5 ? 1 : -1;
      const v = (2 * Math.random() - 1) * vMax;
      this.addKink(x, v, s);
      kinks.push({ x, v, s });
    }
    this.t = 0;
    this.E0 = this.energy();
    return kinks;
  }
}
