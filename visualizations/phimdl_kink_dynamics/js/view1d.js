// 1D mode: live field strip colored by vacuum index, Phi(x) curve overlay,
// and a scrolling spacetime history panel. Interactions: wheel zoom, pan,
// click-drag kink placement with velocity, random gas.

import { Field1D } from './field1d.js?v=7';
import { VACUUM_COLORS, VACUUM_CSS, vacuumIndex } from './palette.js?v=7';
import { STEP, TIME_UNIT_FM_C, M_PHI_MEV, lengthUnitFmFor } from './constants.js?v=7';
import { NSoliton, validateKinkSpecs } from './exactsoliton.js?v=7';

const TWO_PI = 2 * Math.PI;

// Domain-fixed sample count for the exact-solution overlay + residual
// (Feature 1, "Advanced / Verification" panel). Fixed, not tied to the
// current zoom/pixel width, so the residual reflects the whole domain
// rather than whatever is currently in view; see the MAX_EXACT_SOLITONS
// cap in exactsoliton.js for the real-time-performance reasoning that also
// bounds this choice (cost scales as N_EXACT_SAMPLES * 2^kinkCount).
const N_EXACT_SAMPLES = 1000;

export class View1D {
  constructor(root, readouts) {
    this.root = root;
    this.readouts = readouts;

    this.fieldCanvas = root.querySelector('#field-canvas');
    this.historyCanvas = root.querySelector('#history-canvas');
    this.fctx = this.fieldCanvas.getContext('2d');
    this.hctx = this.historyCanvas.getContext('2d');

    this.sim = new Field1D({ N: 18432, dx: 0.05 });
    this.sim.clearToVacuum(0);

    // view transform: x_px = (x - centerX) * scale + width/2
    this.centerX = 0;
    this.scale = 1;           // px per natural length unit; set on resize
    this.running = true;
    this.speed = 30;          // natural time units per wall-clock second
    this.maxStepsPerFrame = 240;   // ~0.1 ms/step at N=18432: keeps 60 fps at max speed

    this.drag = null;         // kink placement drag state
    this.pan = null;
    this.energyDrift = 0;
    this.kinkCount = 0;
    this.frame = 0;
    this.lastTime = performance.now();

    // replay state (null = live simulation)
    this.replay = null;
    this.replayIndex = 0;

    // Feature 1 (Advanced panel): exact analytic N-soliton overlay + live
    // residual, pure sector only. OFF by default -- see _updateExactOverlay().
    this.showExact = false;
    this._exactXs = null;         // domain-fixed sample positions (built once)
    this._exactCache = null;      // last-computed exact Phi(x) at those positions
    this._exactValid = { ok: true };
    this._exactResidual = 0;
    this._exactKinksRef = null;   // identity+length cache key for this.sim.kinkSpecs
    this._exactKinksLen = -1;
    this._exactSol = null;

    // Feature 2 (Advanced panel): hypothetical departure from the SCC value
    // m_phi = m_tau = M_PHI_MEV. OFF by default -- defaults to the real,
    // derived SCC value, which is what every readout/scale-bar conversion
    // below uses unless main.js's SCC-explore toggle calls setEffectiveMPhi().
    this.effectiveMPhi = M_PHI_MEV;

    this._bindEvents();
  }

  setShowExact(v) { this.showExact = !!v; }
  setEffectiveMPhi(mPhiMeV) { this.effectiveMPhi = mPhiMeV; }

  // Status object for the Advanced panel: { ok, reason } (reason present
  // only when !ok) plus the current residual when ok and enabled.
  getExactStatus() { return this._exactValid; }
  getExactResidual() { return this._exactResidual; }

  resize() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    for (const c of [this.fieldCanvas, this.historyCanvas]) {
      const r = c.getBoundingClientRect();
      if (r.width === 0) continue;
      const w = Math.round(r.width * dpr), h = Math.round(r.height * dpr);
      if (c.width !== w || c.height !== h) {
        if (c === this.historyCanvas && c.width > 0) {
          // preserve history across resize
          const tmp = document.createElement('canvas');
          tmp.width = c.width; tmp.height = c.height;
          tmp.getContext('2d').drawImage(c, 0, 0);
          c.width = w; c.height = h;
          this.hctx.drawImage(tmp, 0, 0, w, h);
        } else {
          c.width = w; c.height = h;
        }
      }
    }
    if (this.scale === 1) {
      // initial fit: full domain
      this.scale = this.fieldCanvas.width / this.sim.L;
    }
  }

  _bindEvents() {
    const fc = this.fieldCanvas;
    const px2x = (px) => this.centerX + (px - fc.width / 2) / this.scale;
    const evPx = (e) => {
      const r = fc.getBoundingClientRect();
      return ((e.clientX - r.left) / r.width) * fc.width;
    };

    fc.addEventListener('wheel', (e) => {
      e.preventDefault();
      const px = evPx(e);
      const xAt = px2x(px);
      const f = Math.exp(-e.deltaY * 0.0015);
      const [minScale, maxScale] = this._zoomBounds();
      this.scale = Math.min(maxScale, Math.max(minScale, this.scale * f));
      this.centerX = xAt - (px - fc.width / 2) / this.scale;
      this._clampCenter();
      if (this.onZoomChanged) this.onZoomChanged();
    }, { passive: false });

    fc.addEventListener('pointerdown', (e) => {
      try { fc.setPointerCapture(e.pointerId); } catch (_) { /* capture unsupported for this pointer */ }
      const px = evPx(e);
      if (e.button === 1 || e.button === 2 || e.altKey) {
        this.pan = { startPx: px, startCenter: this.centerX };
      } else if (!this.replay) {
        this.drag = { x: px2x(px), startPx: px, curPx: px, anti: e.shiftKey };
      }
    });
    fc.addEventListener('pointermove', (e) => {
      const px = evPx(e);
      if (this.pan) {
        this.centerX = this.pan.startCenter - (px - this.pan.startPx) / this.scale;
        this._clampCenter();
      } else if (this.drag) {
        this.drag.curPx = px;
        this.drag.anti = e.shiftKey;
      }
    });
    const finish = (e) => {
      if (this.pan) { this.pan = null; return; }
      if (this.drag) {
        const d = this.drag;
        this.drag = null;
        const v = Math.max(-0.95, Math.min(0.95, (d.curPx - d.startPx) / 250));
        const margin = 12; // keep away from fixed boundaries
        if (d.x > this.sim.x0 + margin && d.x < -this.sim.x0 - margin) {
          this.sim.addKink(d.x, v, d.anti ? -1 : 1);
          // refresh markers/count immediately so the click feels instant,
          // instead of waiting up to 12 frames for the periodic refresh
          this._lastCrossings = this.sim.crossings();
          this.kinkCount = this._lastCrossings.length;
          this.flashX = d.x;
          this.flashUntil = performance.now() + 450;
        }
      }
    };
    fc.addEventListener('pointerup', finish);
    fc.addEventListener('pointercancel', () => { this.drag = null; this.pan = null; });
    fc.addEventListener('contextmenu', (e) => e.preventDefault());
  }

  _clampCenter() {
    const halfView = this.fieldCanvas.width / (2 * this.scale);
    const lim = this.sim.L / 2;
    this.centerX = Math.max(-lim + halfView, Math.min(lim - halfView, this.centerX));
    if (this.fieldCanvas.width / this.scale >= this.sim.L) this.centerX = 0;
  }

  // Zoom expressed as a 0..1 fraction of the wheel-zoom bounds (0 = whole
  // domain in view, 1 = maximum magnification), log-parametrized like the
  // wheel. Shared with the zoom slider so neither control can exceed the
  // other's range.
  _zoomBounds() {
    const w = this.fieldCanvas.width || 1;
    return [w / this.sim.L, w / 4];
  }
  getZoomFrac() {
    const [mn, mx] = this._zoomBounds();
    const f = Math.log(this.scale / mn) / Math.log(mx / mn);
    return Math.max(0, Math.min(1, f));
  }
  setZoomFrac(f) {
    const [mn, mx] = this._zoomBounds();
    this.scale = mn * Math.pow(mx / mn, Math.max(0, Math.min(1, f)));
    this._clampCenter();
  }
  // Magnification factor relative to fully zoomed out, for the readout.
  getZoomFactor() {
    const [mn] = this._zoomBounds();
    return this.scale / mn;
  }

  setEta(eta) { this.sim.setEta(eta); }

  // ---- Feature 1: exact analytic overlay + residual (pure sector only) ----

  _buildExactSampleXs() {
    const n = N_EXACT_SAMPLES;
    const xs = new Float64Array(n);
    const lo = this.sim.x0, hi = -this.sim.x0;
    for (let i = 0; i < n; i++) xs[i] = lo + ((hi - lo) * i) / (n - 1);
    this._exactXs = xs;
  }

  // Rebuilds the cached NSoliton instance only when the active kink
  // configuration has actually changed (kinkSpecs is only ever cleared or
  // appended to -- see field1d.js -- so reference+length is a cheap and
  // correct change detector).
  _ensureExactSolution() {
    const specs = this.sim.kinkSpecs;
    if (specs === this._exactKinksRef && specs.length === this._exactKinksLen) return;
    this._exactKinksRef = specs;
    this._exactKinksLen = specs.length;
    this._exactValid = validateKinkSpecs(specs);
    this._exactSol = this._exactValid.ok && specs.length > 0 ? new NSoliton(specs) : null;
  }

  // Recomputes the overlay curve + residual for the current sim state.
  // Called every live-simulation frame while the toggle is on; cheap for
  // the configurations it supports (see MAX_EXACT_SOLITONS).
  _updateExactOverlay() {
    if (!this.showExact) { this._exactCache = null; return; }
    if (this.replay) {
      this._exactValid = { ok: false, reason: 'not available during replay playback' };
      this._exactCache = null;
      return;
    }
    if (this.sim.eta !== 0) {
      this._exactValid = { ok: false, reason: 'no closed-form solution exists in Perturbed mode (pure sector only)' };
      this._exactCache = null;
      return;
    }
    this._ensureExactSolution();
    if (!this._exactValid.ok) { this._exactCache = null; return; }
    if (!this._exactXs) this._buildExactSampleXs();
    const xs = this._exactXs;
    this._exactCache = this._exactSol
      ? this._exactSol.phiOnGrid(xs, this.sim.t, this.sim.bcl)
      : new Float64Array(xs.length).fill(this.sim.bcl);
    let maxRes = 0;
    for (let i = 0; i < xs.length; i++) {
      const d = Math.abs(this.sim.sampleAt(xs[i]) - this._exactCache[i]);
      if (d > maxRes) maxRes = d;
    }
    this._exactResidual = maxRes;
  }

  // Replay the current configuration (random gas / manually-placed kinks /
  // whatever was last established) from t=0 -- NOT a blank vacuum. The
  // vacuum-only case is simply what resetToBaseline() replays when the
  // current configuration IS plain vacuum.
  reset() {
    this.replay = null;
    this.sim.resetToBaseline();
    this.energyDrift = 0;
    this.frame = 0;
    this._lastCrossings = this.sim.crossings();
    this.kinkCount = this._lastCrossings.length;
    this.energyMeV = this.sim.E0 * this.effectiveMPhi;
    this.hctx.fillStyle = '#0b0e14';
    this.hctx.fillRect(0, 0, this.historyCanvas.width, this.historyCanvas.height);
  }

  randomGas(n) {
    this.replay = null;
    this.sim.randomGas(n);
    this.hctx.fillStyle = '#0b0e14';
    this.hctx.fillRect(0, 0, this.historyCanvas.width, this.historyCanvas.height);
  }

  singleStep() {
    this.sim.stepN(1);
    this._recordHistoryRow();
  }

  loadReplay(rep) {
    // rep: { name, x (Float32Array), t (Float32Array), field (Float32Array Nt*Nx),
    //        nx, nt, pure (bool) }
    this.replay = rep;
    this.replayIndex = 0;
    this.hctx.fillStyle = '#0b0e14';
    this.hctx.fillRect(0, 0, this.historyCanvas.width, this.historyCanvas.height);
    // fit view to replay domain
    const L = rep.x[rep.nx - 1] - rep.x[0];
    this.centerX = (rep.x[rep.nx - 1] + rep.x[0]) / 2;
    this.scale = this.fieldCanvas.width / L;
    if (this.onZoomChanged) this.onZoomChanged();
  }

  // ---- per-frame update ----------------------------------------------------

  tick(now) {
    const dtWall = Math.min(0.1, (now - this.lastTime) / 1000);
    this.lastTime = now;

    if (this.replay) {
      if (this.running) {
        // replay cadence: snapshots are 0.5 time units apart
        this.replayIndex += (this.speed * dtWall) / 0.5;
        if (this.replayIndex >= this.replay.nt) this.replayIndex = 0;
      }
      this._updateExactOverlay();
      this._drawReplayFrame();
      return;
    }

    if (this.running) {
      const steps = Math.min(this.maxStepsPerFrame,
        Math.round((this.speed * dtWall) / this.sim.dt));
      if (steps > 0) {
        this.sim.stepN(steps);
        this._recordHistoryRow();
      }
    }

    this.frame++;
    if (this.frame % 12 === 0 || this.frame === 1) {
      const E = this.sim.energy();
      this.energyMeV = E * this.effectiveMPhi;
      this.energyDrift = this.sim.E0 > 1e-12 ? Math.abs(E - this.sim.E0) / this.sim.E0 : 0;
      this.kinkCount = this.sim.crossings().length;
    }
    this._updateExactOverlay();
    this._drawFieldFrame();
    this._updateReadouts();
  }

  _updateReadouts() {
    const r = this.readouts;
    const lengthUnitFm = lengthUnitFmFor(this.effectiveMPhi);
    r.time.textContent = (this.sim.t * lengthUnitFm).toFixed(2) + ' fm/c';
    r.energy.textContent = this.energyMeV !== undefined
      ? this.energyMeV.toFixed(1) + ' MeV' : '—';
    r.drift.textContent = this.energyDrift.toExponential(1);
    r.drift.className = this.energyDrift < 1e-3 ? 'ok' : 'warn';
    r.kinks.textContent = String(this.kinkCount);
    const w = Math.round(this.sim.winding());
    r.winding.textContent = (w >= 0 ? '+' : '') + w;
    if (r.exactStatus) this._updateExactReadouts(r);
  }

  _updateExactReadouts(r) {
    if (!this.showExact) {
      r.exactStatus.textContent = '';
      r.exactResidualRow.style.display = 'none';
      return;
    }
    if (!this._exactValid.ok) {
      r.exactStatus.textContent = this._exactValid.reason;
      r.exactStatus.className = 'hint warn-text';
      r.exactResidualRow.style.display = 'none';
      return;
    }
    r.exactStatus.textContent = this.sim.kinkSpecs.length === 0
      ? 'vacuum only -- exact solution is trivially the vacuum'
      : `exact overlay active (${this.sim.kinkSpecs.length} soliton${this.sim.kinkSpecs.length === 1 ? '' : 's'})`;
    r.exactStatus.className = 'hint';
    r.exactResidualRow.style.display = '';
    r.exactResidual.textContent = this._exactResidual.toExponential(2);
  }

  // ---- rendering -----------------------------------------------------------

  _sampleColumn(px, W) {
    // field value at pixel column px (linear interpolation)
    const x = this.centerX + (px - W / 2) / this.scale;
    const s = this.sim.idxAt(x);
    const i = Math.max(0, Math.min(this.sim.N - 2, Math.floor(s)));
    const f = Math.max(0, Math.min(1, s - i));
    return this.sim.phi[i] * (1 - f) + this.sim.phi[i + 1] * f;
  }

  _drawFieldFrame() {
    const ctx = this.fctx, W = this.fieldCanvas.width, H = this.fieldCanvas.height;
    ctx.fillStyle = '#0b0e14';
    ctx.fillRect(0, 0, W, H);

    const stripTop = Math.round(H * 0.10), stripBot = Math.round(H * 0.52);
    const curveTop = stripBot + 8, curveBot = H - 30;

    // vacuum strip
    const img = ctx.createImageData(W, 1);
    const d = img.data;
    const vals = new Float64Array(W);
    for (let px = 0; px < W; px++) {
      const v = this._sampleColumn(px, W);
      vals[px] = v;
      const k = vacuumIndex(v);
      // blend toward white near a wall (large |dPhi/dx| proxy: distance from vacuum)
      const dev = Math.min(1, Math.abs(v - Math.round(v / STEP) * STEP) / (STEP / 2));
      const c = VACUUM_COLORS[k];
      const glow = dev * dev * 150;
      d[px * 4] = Math.min(255, c[0] + glow);
      d[px * 4 + 1] = Math.min(255, c[1] + glow);
      d[px * 4 + 2] = Math.min(255, c[2] + glow);
      d[px * 4 + 3] = 255;
    }
    // stretch the 1-px row over the strip
    const off = new OffscreenCanvas(W, 1);
    off.getContext('2d').putImageData(img, 0, 0);
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(off, 0, 0, W, 1, 0, stripTop, W, stripBot - stripTop);

    // Phi(x) curve: y spans the value range in view (min 1.2 plateau steps)
    let mn = Infinity, mx = -Infinity;
    for (let px = 0; px < W; px++) { if (vals[px] < mn) mn = vals[px]; if (vals[px] > mx) mx = vals[px]; }
    const pad = 0.35 * STEP;
    mn = Math.floor(mn / STEP) * STEP - pad;
    mx = Math.ceil(mx / STEP) * STEP + pad;
    const y = (v) => curveBot - ((v - mn) / (mx - mn)) * (curveBot - curveTop);

    // vacuum grid lines
    ctx.lineWidth = 1;
    for (let k = Math.ceil(mn / STEP); k <= Math.floor(mx / STEP); k++) {
      const kk = ((k % 7) + 7) % 7;
      ctx.strokeStyle = VACUUM_CSS[kk];
      ctx.globalAlpha = 0.35;
      ctx.beginPath();
      ctx.moveTo(0, y(k * STEP));
      ctx.lineTo(W, y(k * STEP));
      ctx.stroke();
      ctx.globalAlpha = 0.9;
      ctx.fillStyle = VACUUM_CSS[kk];
      ctx.font = `${Math.round(10 * (this.fieldCanvas.width / this.fieldCanvas.getBoundingClientRect().width))}px system-ui`;
      ctx.fillText(`k=${kk}`, 6, y(k * STEP) - 3);
    }
    ctx.globalAlpha = 1;

    // the curve
    ctx.strokeStyle = '#e8ecf4';
    ctx.lineWidth = Math.max(1.5, W / 900);
    ctx.beginPath();
    for (let px = 0; px < W; px++) {
      const yy = y(vals[px]);
      if (px === 0) ctx.moveTo(px, yy); else ctx.lineTo(px, yy);
    }
    ctx.stroke();

    // exact analytic overlay (Feature 1), dashed and color-contrasted so it
    // never masks the default white curve: rendered from the domain-fixed
    // sample array (_exactCache), mapped through the same x->px transform
    // used for the sim curve above.
    if (this.showExact && this._exactCache && this._exactXs) {
      ctx.save();
      ctx.strokeStyle = '#ffd166';
      ctx.lineWidth = Math.max(1.5, W / 900);
      ctx.setLineDash([7, 6]);
      ctx.beginPath();
      let started = false;
      for (let i = 0; i < this._exactXs.length; i++) {
        const px = (this._exactXs[i] - this.centerX) * this.scale + W / 2;
        if (px < -10 || px > W + 10) { started = false; continue; }
        const yy = y(this._exactCache[i]);
        if (!started) { ctx.moveTo(px, yy); started = true; } else { ctx.lineTo(px, yy); }
      }
      ctx.stroke();
      ctx.restore();
    }

    // kink markers on the strip
    if (this.frame % 12 === 1 || !this._lastCrossings) this._lastCrossings = this.sim.crossings();
    for (const c of this._lastCrossings) {
      const px = (c.x - this.centerX) * this.scale + W / 2;
      if (px < 0 || px > W) continue;
      ctx.fillStyle = c.sign > 0 ? '#ff6b6b' : '#5ba8ff';
      const yTip = stripTop - 4;
      ctx.beginPath();
      ctx.moveTo(px, yTip);
      ctx.lineTo(px - 5, yTip - 8);
      ctx.lineTo(px + 5, yTip - 8);
      ctx.closePath();
      ctx.fill();
    }

    // brief highlight ring where a kink was just placed
    if (this.flashUntil && performance.now() < this.flashUntil) {
      const frac = 1 - (this.flashUntil - performance.now()) / 450;
      const px = (this.flashX - this.centerX) * this.scale + W / 2;
      const yMid = (stripTop + stripBot) / 2;
      ctx.strokeStyle = `rgba(232,236,244,${1 - frac})`;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(px, yMid, 6 + frac * 26, 0, 2 * Math.PI);
      ctx.stroke();
    }

    // drag preview: arrow showing placement velocity
    if (this.drag) {
      const d = this.drag;
      const v = Math.max(-0.95, Math.min(0.95, (d.curPx - d.startPx) / 250));
      const yMid = (stripTop + stripBot) / 2;
      ctx.strokeStyle = d.anti ? '#5ba8ff' : '#ff6b6b';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(d.startPx, yMid);
      ctx.lineTo(d.curPx, yMid);
      ctx.stroke();
      ctx.font = '24px system-ui';
      ctx.fillStyle = ctx.strokeStyle;
      ctx.fillText(`${d.anti ? 'antikink' : 'kink'}  v = ${v.toFixed(2)}c`, d.startPx + 8, yMid - 14);
    }

    this._drawScaleBar(ctx, W, H);
  }

  _drawScaleBar(ctx, W, H) {
    // pick a nice round fm length ~ 1/5 of the view -- uses effectiveMPhi so
    // the SCC-explore slider (Feature 2) visibly rescales physical length
    // even though the underlying natural-unit grid/dynamics never change.
    const lengthUnitFm = lengthUnitFmFor(this.effectiveMPhi);
    const viewFm = (W / this.scale) * lengthUnitFm;
    const target = viewFm / 5;
    const pow = Math.pow(10, Math.floor(Math.log10(target)));
    let nice = pow;
    for (const m of [1, 2, 5, 10]) if (m * pow <= target) nice = m * pow;
    const barPx = (nice / lengthUnitFm) * this.scale;
    const y0 = H - 12, x0 = W - barPx - 20;
    ctx.strokeStyle = '#aab4c8';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(x0, y0); ctx.lineTo(x0 + barPx, y0);
    ctx.moveTo(x0, y0 - 5); ctx.lineTo(x0, y0 + 5);
    ctx.moveTo(x0 + barPx, y0 - 5); ctx.lineTo(x0 + barPx, y0 + 5);
    ctx.stroke();
    ctx.fillStyle = '#aab4c8';
    ctx.font = `${Math.round(12 * (W / this.fieldCanvas.getBoundingClientRect().width))}px system-ui`;
    ctx.textAlign = 'center';
    ctx.fillText(nice >= 1 ? `${nice} fm` : `${(nice * 1000).toFixed(0)} am`, x0 + barPx / 2, y0 - 8);
    ctx.textAlign = 'left';
  }

  _recordHistoryRow() {
    const hc = this.historyCanvas, ctx = this.hctx;
    const W = hc.width, H = hc.height;
    if (W === 0) return;
    // scroll up one row
    ctx.drawImage(hc, 0, 1, W, H - 1, 0, 0, W, H - 1);
    const img = ctx.createImageData(W, 1);
    const d = img.data;
    for (let px = 0; px < W; px++) {
      const v = this._sampleColumn(px, W);
      const k = vacuumIndex(v);
      const dev = Math.min(1, Math.abs(v - Math.round(v / STEP) * STEP) / (STEP / 2));
      const c = VACUUM_COLORS[k];
      const dark = 0.55 + 0.45 * dev * dev;   // walls bright, plateaus dimmer
      const glow = dev * dev * 130;
      d[px * 4] = Math.min(255, c[0] * dark + glow);
      d[px * 4 + 1] = Math.min(255, c[1] * dark + glow);
      d[px * 4 + 2] = Math.min(255, c[2] * dark + glow);
      d[px * 4 + 3] = 255;
    }
    ctx.putImageData(img, 0, H - 1);
  }

  // ---- replay --------------------------------------------------------------

  _drawReplayFrame() {
    const rep = this.replay;
    const idx = Math.min(rep.nt - 1, Math.floor(this.replayIndex));
    const row = rep.field.subarray(idx * rep.nx, (idx + 1) * rep.nx);
    // temporarily adapt _sampleColumn to replay data
    const W = this.fieldCanvas.width;
    const savedSample = this._sampleColumn;
    const x0 = rep.x[0], dxr = rep.x[1] - rep.x[0], nx = rep.nx;
    this._sampleColumn = (px, Wp) => {
      const x = this.centerX + (px - Wp / 2) / this.scale;
      const s = (x - x0) / dxr;
      const i = Math.max(0, Math.min(nx - 2, Math.floor(s)));
      const f = Math.max(0, Math.min(1, s - i));
      return row[i] * (1 - f) + row[i + 1] * f;
    };
    // kink census from replay row
    if (this.frame % 6 === 0 || !this._lastCrossings) {
      this._lastCrossings = replayCrossings(row, x0, dxr);
      this.kinkCount = this._lastCrossings.length;
    }
    this.frame++;
    this._drawFieldFrame();
    if (this.running) this._recordHistoryRow();
    this._sampleColumn = savedSample;

    const r = this.readouts;
    r.time.textContent = (rep.t[idx] * TIME_UNIT_FM_C).toFixed(2) + ' fm/c (replay)';
    r.energy.textContent = '— (replay)';
    r.drift.textContent = '—';
    r.drift.className = '';
    r.kinks.textContent = String(this.kinkCount);
    const w = Math.round((row[nx - 1] - row[0]) / STEP);
    r.winding.textContent = (w >= 0 ? '+' : '') + w;
  }
}

function replayCrossings(row, x0, dxr) {
  let mn = Infinity, mx = -Infinity;
  for (let i = 0; i < row.length; i++) { const v = row[i]; if (v < mn) mn = v; if (v > mx) mx = v; }
  const lo = Math.floor(mn / STEP - 0.5), hi = Math.ceil(mx / STEP + 0.5);
  const out = [];
  for (let k = lo; k <= hi; k++) {
    const level = STEP * (k + 0.5);
    let dPrev = row[0] - level;
    for (let i = 1; i < row.length; i++) {
      const d = row[i] - level;
      if ((dPrev < 0 && d >= 0) || (dPrev >= 0 && d < 0)) {
        const f = dPrev / (dPrev - d);
        out.push({ x: x0 + (i - 1 + f) * dxr, sign: d > dPrev ? 1 : -1 });
      }
      dPrev = d;
    }
  }
  out.sort((a, b) => a.x - b.x);
  return out;
}
