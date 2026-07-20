// Trend analysis for a scalar time series: ordinary-least-squares linear
// fit, plus an exponential fit when the data support one, with a
// residual-based significance threshold to decide whether any trend is
// measurable at all within the observed window. Pure math, no DOM/canvas
// dependency, so it is reusable by any live readout that needs a
// quantitative "is this actually changing?" answer rather than an eyeballed
// chart.
//
// Units are whatever the caller passes in (the caller is responsible for
// converting to physical units before calling, so the fitted rate comes
// out already in the caller's units).

// Significance threshold rationale: a slope is only reported as a
// measured trend when it exceeds SIGNIFICANCE_MULTIPLE times its own
// ordinary-least-squares standard error -- the standard single-parameter
// ~95%-confidence bar (t ~ 2 for the sample sizes this panel accumulates,
// typically tens to hundreds of points). Below that bar the slope is not
// distinguishable from zero given the sample's own scatter, so the series
// is reported as flat over the observed window rather than assigning it a
// spurious rate.
const SIGNIFICANCE_MULTIPLE = 2;

function linearRegression(xs, ys) {
  const n = xs.length;
  let sx = 0, sy = 0;
  for (let i = 0; i < n; i++) { sx += xs[i]; sy += ys[i]; }
  const mx = sx / n, my = sy / n;
  let sxx = 0, sxy = 0;
  for (let i = 0; i < n; i++) {
    const dx = xs[i] - mx;
    sxx += dx * dx;
    sxy += dx * (ys[i] - my);
  }
  const b = sxx > 0 ? sxy / sxx : 0;
  const a = my - b * mx;
  let ssr = 0;
  for (let i = 0; i < n; i++) {
    const r = ys[i] - (a + b * xs[i]);
    ssr += r * r;
  }
  const dof = Math.max(1, n - 2);
  const seB = sxx > 0 ? Math.sqrt((ssr / dof) / sxx) : Infinity;
  return { a, b, ssr, seB };
}

// history: array of [x, y] pairs, already in the caller's physical units
// (e.g. x = time in fm/c, y = area fraction in percent), sorted by x.
export function analyzeTrend(history, opts = {}) {
  const minPoints = opts.minPoints || 5;
  const n = history ? history.length : 0;
  if (n < minPoints) return { status: 'insufficient', nPoints: n };

  const xs = history.map((p) => p[0]);
  const ys = history.map((p) => p[1]);
  const rangeX = xs[n - 1] - xs[0];
  if (!(rangeX > 0)) return { status: 'insufficient', nPoints: n };

  const meanY = ys.reduce((s, v) => s + v, 0) / n;
  const lin = linearRegression(xs, ys);
  const significant = meanY > 0 && Math.abs(lin.b) > SIGNIFICANCE_MULTIPLE * lin.seB;

  if (!significant) {
    let maxDev = 0;
    for (const y of ys) maxDev = Math.max(maxDev, Math.abs(y - meanY));
    return {
      status: 'flat',
      nPoints: n,
      rangeX,
      meanY,
      stabilityFrac: meanY > 0 ? maxDev / meanY : 0,
      linB: lin.b,
      linSeB: lin.seB,
    };
  }

  // Exponential candidate: y = A exp(k x), fit by linear regression on
  // (x, ln y). Only defined if every sample is strictly positive.
  let exp = null;
  if (ys.every((y) => y > 0)) {
    const logFit = linearRegression(xs, ys.map(Math.log));
    const A = Math.exp(logFit.a);
    let ssrExp = 0;
    for (let i = 0; i < n; i++) {
      const r = ys[i] - A * Math.exp(logFit.b * xs[i]);
      ssrExp += r * r;
    }
    exp = { A, k: logFit.b, ssr: ssrExp };
  }

  const useExp = exp !== null && exp.ssr < lin.ssr;
  return {
    status: useExp ? 'exponential' : 'linear',
    nPoints: n,
    rangeX,
    meanY,
    linB: lin.b,
    linA: lin.a,
    linSsr: lin.ssr,
    expA: exp ? exp.A : null,
    expK: exp ? exp.k : null,
    expSsr: exp ? exp.ssr : null,
  };
}
