// Lightweight Canvas2D line/area chart for a scalar time series. No
// framework dependency, reusable by any live-history readout panel.
//
// history: array of [x, y] pairs, already in the caller's display units,
// sorted by x (ascending).

export function drawHistoryChart(canvas, history, opts = {}) {
  const ctx = canvas.getContext('2d');
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const rect = canvas.getBoundingClientRect();
  const w = Math.max(1, Math.round(rect.width * dpr));
  const h = Math.max(1, Math.round(rect.height * dpr));
  if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }

  const bg = opts.bg || '#171c29';
  const grid = opts.grid || '#232a3b';
  const line = opts.line || '#5ba8ff';
  const fill = opts.fill || 'rgba(91,168,255,0.16)';
  const label = opts.labelColor || '#8b95ab';
  const padL = 2 * dpr, padR = 2 * dpr, padT = 4 * dpr, padB = 2 * dpr;

  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, w, h);

  if (!history || history.length < 2) {
    ctx.fillStyle = label;
    ctx.font = `${11 * dpr}px -apple-system, sans-serif`;
    ctx.textBaseline = 'middle';
    ctx.fillText(opts.emptyText || 'collecting samples\u2026', padL + 4 * dpr, h / 2);
    return;
  }

  const xs = history.map((p) => p[0]);
  const ys = history.map((p) => p[1]);
  const x0 = xs[0], x1 = xs[xs.length - 1];
  const yDataMax = Math.max(...ys);
  const yMax = Math.max(opts.yMinTop || 0, yDataMax * 1.12, 1e-9);
  const yMin = 0;

  const plotW = w - padL - padR, plotH = h - padT - padB;
  const xAt = (x) => padL + ((x - x0) / Math.max(1e-9, x1 - x0)) * plotW;
  const yAt = (y) => padT + (1 - (y - yMin) / (yMax - yMin)) * plotH;

  ctx.strokeStyle = grid;
  ctx.lineWidth = Math.max(1, dpr * 0.6);
  for (const f of [0.5]) {
    const gy = padT + f * plotH;
    ctx.beginPath();
    ctx.moveTo(padL, gy);
    ctx.lineTo(w - padR, gy);
    ctx.stroke();
  }

  ctx.beginPath();
  ctx.moveTo(xAt(xs[0]), yAt(ys[0]));
  for (let i = 1; i < xs.length; i++) ctx.lineTo(xAt(xs[i]), yAt(ys[i]));
  ctx.lineTo(xAt(xs[xs.length - 1]), padT + plotH);
  ctx.lineTo(xAt(xs[0]), padT + plotH);
  ctx.closePath();
  ctx.fillStyle = fill;
  ctx.fill();

  ctx.beginPath();
  ctx.moveTo(xAt(xs[0]), yAt(ys[0]));
  for (let i = 1; i < xs.length; i++) ctx.lineTo(xAt(xs[i]), yAt(ys[i]));
  ctx.strokeStyle = line;
  ctx.lineWidth = 1.5 * dpr;
  ctx.stroke();

  ctx.fillStyle = label;
  ctx.font = `${10 * dpr}px -apple-system, sans-serif`;
  ctx.textBaseline = 'top';
  ctx.fillText((opts.yLabelFmt ? opts.yLabelFmt(yMax) : yMax.toFixed(1)), padL + 3 * dpr, padT + 1 * dpr);
}
