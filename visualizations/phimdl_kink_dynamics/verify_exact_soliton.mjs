// Standalone verification of js/exactsoliton.js against the closed-form
// analytic solutions and the Phi_MDL pure-phi field equation, mirroring the
// checks performed against the reference Python implementation of the same
// N-soliton and two-soliton closed-form formulas. Run with:
//
//   node verify_exact_soliton.mjs
//
// This is a development/verification script, not part of the running app.

import { NSoliton } from './js/exactsoliton.js';

// Test 2/3 below construct NSoliton with the tau function's OWN bare
// x0-parameter convention directly (x0=0,0, a head-on collision AT x=0),
// so they must bypass NSoliton's public constructor (which expects
// already-physical, well-separated x0 and applies the scattering-shift
// correction described in exactsoliton.js -- inapplicable to a literal
// head-on placement). rawTau() builds the same bitmask tau machinery with
// NO correction, exactly mirroring the Python reference's NSoliton class,
// to check the closed forms directly against the bare formula.
function rawTau(thetas, epss, x0s) {
  const N = thetas.length;
  const kk = thetas.map(Math.cosh);
  const ww = thetas.map(Math.sinh);
  const delta = kk.map((k, i) => -k * x0s[i]);
  const A = [];
  for (let i = 0; i < N; i++) {
    A.push(new Float64Array(N));
    for (let j = 0; j < N; j++) {
      if (i !== j) A[i][j] = 2 * Math.log(Math.abs(Math.tanh(0.5 * (thetas[i] - thetas[j]))));
    }
  }
  const M = 1 << N;
  const Kmu = new Float64Array(M), Wmu = new Float64Array(M), Dmu = new Float64Array(M);
  const coeffRe = new Float64Array(M), coeffIm = new Float64Array(M);
  for (let mu = 0; mu < M; mu++) {
    let K = 0, W = 0, D = 0, Amu = 0, nAct = 0, epsProd = 1;
    for (let i = 0; i < N; i++) {
      if (!(mu & (1 << i))) continue;
      K += kk[i]; W += ww[i]; D += delta[i]; nAct++; epsProd *= epss[i];
      for (let j = i + 1; j < N; j++) if (mu & (1 << j)) Amu += A[i][j];
    }
    Kmu[mu] = K; Wmu[mu] = W; Dmu[mu] = D + Amu;
    const r = ((nAct % 4) + 4) % 4;
    coeffRe[mu] = (r === 0 ? 1 : r === 2 ? -1 : 0) * epsProd;
    coeffIm[mu] = (r === 1 ? 1 : r === 3 ? -1 : 0) * epsProd;
  }
  return {
    phiOnGrid(xs, t, anchor = 0) {
      const n = xs.length, out = new Float64Array(n), E = new Float64Array(M);
      let prevAngle = 0, unwrapped = 0, first = true;
      for (let ix = 0; ix < n; ix++) {
        const x = xs[ix];
        let Emax = -Infinity;
        for (let mu = 0; mu < M; mu++) { const e = Kmu[mu] * x - Wmu[mu] * t + Dmu[mu]; E[mu] = e; if (e > Emax) Emax = e; }
        let re = 0, im = 0;
        for (let mu = 0; mu < M; mu++) { const ex = Math.exp(E[mu] - Emax); re += coeffRe[mu] * ex; im += coeffIm[mu] * ex; }
        const angle = Math.atan2(im, re);
        if (first) { unwrapped = angle; first = false; }
        else { let d = angle - prevAngle; while (d > Math.PI) d -= 2 * Math.PI; while (d < -Math.PI) d += 2 * Math.PI; unwrapped += d; }
        prevAngle = angle;
        out[ix] = (4 * unwrapped) / 7;
      }
      if (n > 0) {
        const c = Math.round((anchor - out[0]) / ((2 * Math.PI) / 7)) * ((2 * Math.PI) / 7);
        if (c !== 0) for (let ix = 0; ix < n; ix++) out[ix] += c;
      }
      return out;
    },
  };
}

let failures = 0;
function check(name, cond, detail) {
  const ok = !!cond;
  if (!ok) failures++;
  console.log(`[${ok ? 'PASS' : 'FAIL'}] ${name}${detail !== undefined ? '  ' + detail : ''}`);
}

// ---------------------------------------------------------------------------
// 1. N=1: boosted BPS kink, direct closed-form comparison (no shift issues).
// ---------------------------------------------------------------------------
console.log('='.repeat(72));
console.log('1. N=1 BOOSTED KINK vs CLOSED FORM');
console.log('='.repeat(72));
{
  const v = 0.37, x0 = 3.1, sign = 1;
  const gamma = 1 / Math.sqrt(1 - v * v);
  const sol = new NSoliton([{ x0, v, sign }]);
  const xs = [];
  for (let i = 0; i <= 400; i++) xs.push(-40 + (80 * i) / 400);
  let maxErr = 0;
  for (const t of [-5, 0, 5, 15]) {
    const phi = sol.phiOnGrid(xs, t);
    for (let i = 0; i < xs.length; i++) {
      const exact = (4 / 7) * Math.atan(Math.exp(gamma * (xs[i] - x0 - v * t)));
      maxErr = Math.max(maxErr, Math.abs(phi[i] - exact));
    }
  }
  check('N=1 max|Phi_tau - Phi_closed| over t in {-5,0,5,15}', maxErr < 1e-10, `max err = ${maxErr.toExponential(3)}`);
}

// ---------------------------------------------------------------------------
// 2. N=2 kink-kink: closed form (Python-verified) vs tau form, after the
//    symmetric phase-shift offset ln(1/v)/gamma used in the reference script
//    (the tau form's x0=0,0 convention and the closed form's origin-centered
//    convention differ by this offset for a symmetric equal-and-opposite
//    rapidity pair).
// ---------------------------------------------------------------------------
console.log('\n' + '='.repeat(72));
console.log('2. N=2 KINK-KINK vs CLOSED FORM (symmetric shift ln(1/v)/gamma)');
console.log('='.repeat(72));
{
  const v = 0.4;
  const th = Math.atanh(v);
  const g = Math.cosh(th);
  const shift = Math.log(1 / v) / g;
  const sol = rawTau([th, -th], [1, 1], [0, 0]);
  const xs = [];
  for (let i = 0; i <= 500; i++) xs.push(-30 + (60 * i) / 500);
  const xsShifted = xs.map((x) => x + shift);
  // Closed-form leftmost asymptote is -2*pi/7 (one full sine-Gordon period
  // below the tau construction's own 0 branch); anchor there so both sides
  // are compared on the same branch (see exactsoliton.js branch-anchor note).
  const closedLeftAnchor = -(2 * Math.PI) / 7;
  let maxErr = 0;
  for (const t of [-8, -2, 0, 2, 8]) {
    const phiTau = sol.phiOnGrid(xsShifted, t, closedLeftAnchor);
    for (let i = 0; i < xs.length; i++) {
      const num = v * Math.sinh(g * xs[i]) / Math.cosh(g * v * t);
      const psiClosed = 4 * Math.atan(num);
      const phiClosed = psiClosed / 7;
      maxErr = Math.max(maxErr, Math.abs(phiTau[i] - phiClosed));
    }
  }
  check('N=2 KK max|Phi_tau - Phi_closed| over t in {-8,-2,0,2,8}', maxErr < 1e-9, `max err = ${maxErr.toExponential(3)}`);
}

// ---------------------------------------------------------------------------
// 3. N=2 kink-antikink: same closed-form cross-check.
// ---------------------------------------------------------------------------
console.log('\n' + '='.repeat(72));
console.log('3. N=2 KINK-ANTIKINK vs CLOSED FORM');
console.log('='.repeat(72));
{
  const v = 0.4;
  const th = Math.atanh(v);
  const g = Math.cosh(th);
  const shift = Math.log(1 / v) / g;
  // Note the eps assignment [-1, +1] (not the naively-expected [+1, -1]):
  // this specific closed form's own labeling convention assigns "kink"
  // to the LEFT-incoming (negative-rapidity) soliton -- confirmed
  // empirically not to affect the app's actual usage, where each
  // individual kink's local rising/falling identity (matched to
  // Field1D.addKink's sign convention) is checked directly by the
  // far-separation test below instead of against this specific labeling.
  const sol = rawTau([th, -th], [-1, 1], [0, 0]);
  const xs = [];
  for (let i = 0; i <= 500; i++) xs.push(-30 + (60 * i) / 500);
  const xsShifted = xs.map((x) => x + shift);
  let maxErr = 0;
  for (const t of [-8, -2, 0, 2, 8]) {
    const phiTau = sol.phiOnGrid(xsShifted, t);
    for (let i = 0; i < xs.length; i++) {
      const num = Math.sinh(g * v * t) / (v * Math.cosh(g * xs[i]));
      const psiClosed = 4 * Math.atan(num);
      const phiClosed = psiClosed / 7;
      maxErr = Math.max(maxErr, Math.abs(phiTau[i] - phiClosed));
    }
  }
  check('N=2 KA max|Phi_tau - Phi_closed| over t in {-8,-2,0,2,8}', maxErr < 1e-9, `max err = ${maxErr.toExponential(3)}`);
}

// ---------------------------------------------------------------------------
// 4. Scattering-shift correction check: this is the actual guarantee the
//    live app relies on. Field1D.addKink() places each kink's OWN profile
//    centered EXACTLY at the given x0 (a naive per-kink superposition, by
//    construction of field1d.js). The bare Hirota tau parameterization does
//    NOT reproduce that placement once other solitons are present (the
//    pairwise interaction term does not decay with separation -- see the
//    long comment in exactsoliton.js), so NSoliton's constructor applies a
//    scattering-shift correction to its internal tau parameters so that,
//    for a well-separated (not-yet-collided) configuration, each kink's
//    OWN transition really does land at its given x0 at t=0. This checks
//    exactly that guarantee for a same-sign and a mixed-sign pair, at two
//    different separations, confirming the correction is a genuine fix
//    (removing an O(1) discrepancy), not a coincidence at one separation.
// ---------------------------------------------------------------------------
console.log('\n' + '='.repeat(72));
console.log('4. SCATTERING-SHIFT CORRECTION (this is what the live overlay relies on)');
console.log('='.repeat(72));
{
  const bpsAt = (x, x0, v, sign) => {
    const g = 1 / Math.sqrt(1 - v * v);
    return sign * (4 / 7) * Math.atan(Math.exp(g * (x - x0)));
  };
  const cases = [
    { name: 'same-sign, d=50', kinks: [{ x0: -25, v: 0.3, sign: 1 }, { x0: 25, v: 0.1, sign: 1 }], tol: 1e-9 },
    { name: 'mixed-sign, d=50', kinks: [{ x0: -25, v: 0.3, sign: 1 }, { x0: 25, v: -0.2, sign: -1 }], tol: 1e-9 },
    // At d=15 (the app's randomGas() minimum separation) the correction is
    // still an excellent approximation, but a small higher-order residual
    // remains: the correction formula equates the crossing point of the
    // two DOMINANT exponential terms with the true transition location,
    // which is exact only in the well-separated limit where the other two
    // (of four total) terms are fully negligible there. This residual
    // shrinks with separation (it is the reason this case's tolerance is
    // looser than the d=50 cases', not a bug) and is far smaller than the
    // O(1) discrepancy the correction eliminates.
    { name: 'mixed-sign, d=15 (near addKink min-separation)', kinks: [{ x0: -7.5, v: 0.25, sign: -1 }, { x0: 7.5, v: -0.35, sign: 1 }], tol: 1e-5 },
  ];
  for (const { name, kinks, tol } of cases) {
    const sol = new NSoliton(kinks);
    const xs = [];
    for (let i = 0; i <= 3000; i++) xs.push(-60 + (120 * i) / 3000);
    const phiTau = sol.phiOnGrid(xs, 0);
    let maxErr = 0;
    for (let i = 0; i < xs.length; i++) {
      const sumAnsatz = kinks.reduce((s, k) => s + bpsAt(xs[i], k.x0, k.v, k.sign), 0);
      maxErr = Math.max(maxErr, Math.abs(phiTau[i] - sumAnsatz));
    }
    check(`${name}: max|Phi_tau - Phi_sum_ansatz| at t=0`, maxErr < tol, `max err = ${maxErr.toExponential(3)}`);
  }
}

// ---------------------------------------------------------------------------
// 5. Field-equation residual via central finite differences, for a genuine
//    N=4 mixed kink/antikink configuration through a collision window --
//    confirms the tau solution actually solves
//      Phi_tt - Phi_xx + (1/7) sin(7 Phi) = 0
//    independent of any closed-form comparison.
// ---------------------------------------------------------------------------
console.log('\n' + '='.repeat(72));
console.log('5. N=4 MIXED CONFIGURATION: FIELD-EQUATION RESIDUAL (finite differences)');
console.log('='.repeat(72));
{
  const kinks = [
    { x0: -20, v: 0.5, sign: 1 },
    { x0: -6, v: 0.1, sign: -1 },
    { x0: 6, v: -0.15, sign: 1 },
    { x0: 20, v: -0.45, sign: 1 },
  ];
  const sol = new NSoliton(kinks);
  const h = 1e-3;
  const phiAt = (x, t) => sol.phiOnGrid([x], t)[0];
  const residualAt = (x, t) => {
    const p0 = phiAt(x, t);
    const ptt = (phiAt(x, t + h) - 2 * p0 + phiAt(x, t - h)) / (h * h);
    const pxx = (phiAt(x + h, t) - 2 * p0 + phiAt(x - h, t)) / (h * h);
    return ptt - pxx + Math.sin(7 * p0) / 7;
  };
  let maxRes = 0;
  const rng = (() => { let s = 12345; return () => { s = (s * 1103515245 + 12345) & 0x7fffffff; return s / 0x7fffffff; }; })();
  for (let n = 0; n < 60; n++) {
    const x = -25 + rng() * 50;
    const t = -30 + rng() * 60;
    maxRes = Math.max(maxRes, Math.abs(residualAt(x, t)));
  }
  // Finite-difference truncation error at h=1e-3 for this smooth solution is
  // expected to be small but not machine-precision; this checks the PDE is
  // satisfied, not exact-arithmetic equality.
  check('N=4 max|Phi_tt - Phi_xx + sin(7 Phi)/7| over 60 random spacetime points',
    maxRes < 1e-4, `max residual = ${maxRes.toExponential(3)}`);
}

console.log('\n' + '='.repeat(72));
if (failures === 0) {
  console.log('ALL CHECKS PASSED.');
} else {
  console.log(`${failures} CHECK(S) FAILED.`);
  process.exit(1);
}
