// App shell: mode switching, control wiring, render loop.

import { View1D } from './view1d.js?v=7';
import { Field2D } from './field2d.js?v=7';
import { View3D, SECTOR3D, wallTensionGeVFm2, junctionEnergyMeV } from './view3d.js?v=7';
import { VACUUM_CSS } from './palette.js?v=7';
import { SECTORS, TIME_UNIT_FM_C, M_PHI_MEV, lengthUnitFmFor, kinkMassMevFor } from './constants.js?v=7';
import { analyzeTrend } from './trend.js?v=7';
import { drawHistoryChart } from './historychart.js?v=7';

const $ = (id) => document.getElementById(id);

const readouts = {
  time: $('ro-time'),
  energy: $('ro-energy'),
  drift: $('ro-drift'),
  kinks: $('ro-kinks'),
  winding: $('ro-winding'),
  exactStatus: $('exact-status'),
  exactResidualRow: $('exact-residual-row'),
  exactResidual: $('exact-residual-out'),
};

// ---- legend ----------------------------------------------------------------

const legendBox = $('legend-vacua');
for (let k = 0; k < 7; k++) {
  const sw = document.createElement('div');
  sw.className = 'sw';
  sw.style.background = VACUUM_CSS[k];
  sw.textContent = String(k);
  sw.title = `vacuum k=${k}, \u03A6 = 2\u03C0\u00B7${k}/7`;
  legendBox.appendChild(sw);
}
const secRows = $('sector-rows');
for (const s of SECTORS) {
  const tr = document.createElement('tr');
  const dark = s.note === 'PSC-forbidden';
  tr.innerHTML = `<td${dark ? ' class="dark"' : ''}>${s.w}</td>` +
    `<td${dark ? ' class="dark"' : ''}>${s.name}${s.note ? ` <small>(${s.note})</small>` : ''}</td>` +
    `<td${dark ? ' class="dark"' : ''}>${s.charge}</td>`;
  secRows.appendChild(tr);
}

// ---- 3D sector selector -------------------------------------------------

const sector3dSelect = $('sector3d-select');
for (const s of SECTOR3D) {
  const opt = document.createElement('option');
  opt.value = String(s.w);
  opt.textContent = `${s.label} (w=${s.w}, Q=${s.charge})`;
  sector3dSelect.appendChild(opt);
}
sector3dSelect.value = '4'; // default: charged lepton

// ---- 2D paint palette -----------------------------------------------------

const paint2dPalette = $('paint2d-palette');
const paint2dSwatches = [];
const SECTOR_BY_W = new Map(SECTORS.map((s) => [s.w, s]));
for (let k = 0; k < 7; k++) {
  const sw = document.createElement('div');
  sw.className = 'sw';
  sw.style.background = VACUUM_CSS[k];
  sw.style.cursor = 'pointer';
  sw.textContent = String(k);
  const sec = SECTOR_BY_W.get(k);
  sw.title = sec && !sec.note
    ? `k=${k}: ${sec.name} (Q=${sec.charge})`
    : sec ? `k=${k}: ${sec.name} (${sec.note})` : `k=${k}`;
  sw.addEventListener('click', () => {
    for (const s of paint2dSwatches) s.style.outline = 'none';
    sw.style.outline = '2px solid #fff';
    if (field2d) field2d.paintK = k;
  });
  paint2dPalette.appendChild(sw);
  paint2dSwatches.push(sw);
}
paint2dSwatches[4].style.outline = '2px solid #fff'; // default paint color: k=4

// ---- views (2D/3D lazily created) -------------------------------------------

const view1d = new View1D($('view-1d'), readouts);
let field2d = null;
let view3d = null;
let mode = '1d';

function activate(next) {
  mode = next;
  for (const m of ['1d', '2d', '3d']) {
    $(`view-${m}`).classList.toggle('active', m === next);
    $(`tab-${m}`).classList.toggle('active', m === next);
  }
  if (next === '2d' && !field2d) {
    try {
      field2d = new Field2D($('canvas-2d'), readouts);
      field2d.setEta(currentEta());
      field2d.running = running;
      field2d.onZoomChanged = syncZoomSlider;
    } catch (err) {
      alert('2D mode requires WebGL2 with float render targets: ' + err.message);
    }
  }
  if (next === '3d' && !view3d) {
    try {
      view3d = new View3D($('canvas-3d'));
      view3d.setSector(parseInt(sector3dSelect.value, 10));
      view3d.setStructure(structure3d);
      view3d.onZoomChanged = syncZoomSlider;
    } catch (err) { alert('3D mode requires WebGL2: ' + err.message); }
  }
  // per-mode control visibility
  $('gas-row').style.display = next === '1d' ? '' : 'none';
  $('btn-gas').style.display = next === '1d' ? '' : 'none';
  $('preset2d-row').style.display = next === '2d' ? '' : 'none';
  $('particlecount2d-row').style.display =
    (next === '2d' && $('preset2d-select').value === 'particles') ? '' : 'none';
  $('reseed2d-row').style.display = next === '2d' ? '' : 'none';
  $('stats-card-2d').style.display = next === '2d' ? '' : 'none';
  $('history-card-2d').style.display = next === '2d' ? '' : 'none';
  $('replay-row').style.display = next === '1d' ? '' : 'none';
  $('hint-card-1d').style.display = next === '1d' ? '' : 'none';
  $('hint-card-2d').style.display = next === '2d' ? '' : 'none';
  $('hint-card-3d').style.display = next === '3d' ? '' : 'none';
  $('nogo-card-3d').style.display = next === '3d' ? '' : 'none';
  // the pure/perturbed dynamics toggle only applies to the two live-field
  // modes; the 3D view is a static illustration of a certified extended
  // structure, not a live simulation
  $('dynamics-card').style.display = next === '3d' ? 'none' : '';
  updateSpeedLabel();
  syncZoomSlider();
  if (next === '1d') view1d.resize();
  if (next === '3d') {
    readouts.time.textContent = 'static';
    readouts.drift.textContent = '\u2014';
    readouts.drift.className = '';
    update3dReadouts();
  }
}

// ---- 3D structure toggle (single wall vs. triple junction) ----------------

let structure3d = 'wall';

function update3dReadouts() {
  if (structure3d === 'wall') {
    const w = parseInt(sector3dSelect.value, 10);
    readouts.kinks.textContent = 'wall (extended)';
    readouts.winding.textContent = '0\u2192+' + w;
    readouts.energy.textContent = 'diverges \u221d area';
  } else {
    readouts.kinks.textContent = 'triple junction';
    readouts.winding.textContent = '+2,+3,+4';
    readouts.energy.textContent = junctionEnergyMeV().toFixed(1) + ' MeV (junction point)';
  }
  updateNogoText();
}

function updateNogoText() {
  const nogo = $('nogo-text');
  if (!nogo) return;
  const sigma = wallTensionGeVFm2();
  if (structure3d === 'wall') {
    const w = parseInt(sector3dSelect.value, 10);
    nogo.innerHTML =
      `This translucent sheet is a single elementary domain wall separating ` +
      `vacuum 0 from vacuum ${w} &mdash; the smallest certified extended ` +
      `structure. Its tension is &sigma; \u2248 ${sigma.toFixed(1)} GeV/fm&sup2; ` +
      `(= M<sub>kink</sub> per unit transverse area); a patch of area A costs ` +
      `energy \u2248 &sigma;&middot;A, which <b>diverges</b> as the wall is ` +
      `extended. That unavoidable divergence &mdash; confirmed for every wall ` +
      `shape tested, pinched or not &mdash; is exactly why no ` +
      `finite-energy compact 3D particle exists here. GTE particles are ` +
      `Fock-space excitations certified by this kind of extended background, ` +
      `not the wall itself viewed as \u201cthe particle.\u201d`;
  } else {
    nogo.innerHTML =
      `Three elementary domain walls (vacua 2, 3, 4) meet along the vertical ` +
      `axis &mdash; the 3D analogue of the 2D \u201ctriple junction\u201d ` +
      `preset, and the geometry behind the exact BPS wall-junction ` +
      `energy calculation. The junction point itself carries a real, ` +
      `computed excess energy E<sub>3</sub> = 8&middot;M<sub>kink</sub> = ` +
      `${junctionEnergyMeV().toFixed(1)} MeV &mdash; but this does <b>not</b> ` +
      `rescue a finite-energy particle: the three wall sheets radiating out ` +
      `from the junction still diverge as their area grows (\u221d L&sup2;, ` +
      `same &sigma; \u2248 ${sigma.toFixed(1)} GeV/fm&sup2; as the single-wall ` +
      `case). No shape tested &mdash; flat, pinched, or codimension-2 &mdash; ` +
      `gives both finite energy and topological protection.`;
  }
}

function setStructure3d(mode) {
  structure3d = mode;
  $('btn-wall3d').classList.toggle('active', mode === 'wall');
  $('btn-junction3d').classList.toggle('active', mode === 'junction');
  $('sector3d-row').style.display = mode === 'wall' ? '' : 'none';
  if (view3d) view3d.setStructure(mode);
  update3dReadouts();
}
$('btn-wall3d').addEventListener('click', () => setStructure3d('wall'));
$('btn-junction3d').addEventListener('click', () => setStructure3d('junction'));

sector3dSelect.addEventListener('change', () => {
  const w = parseInt(sector3dSelect.value, 10);
  if (view3d) view3d.setSector(w);
  update3dReadouts();
});
$('btn-reset3d').addEventListener('click', () => { if (view3d) view3d.resetView(); });

// ---- 2D pan/paint mode and brush ------------------------------------------

$('btn-pan2d').addEventListener('click', () => {
  $('btn-pan2d').classList.add('active');
  $('btn-paint2d').classList.remove('active');
  $('paint2d-controls').style.display = 'none';
  if (field2d) field2d.paintMode = false;
});
$('btn-paint2d').addEventListener('click', () => {
  $('btn-paint2d').classList.add('active');
  $('btn-pan2d').classList.remove('active');
  $('paint2d-controls').style.display = '';
  if (field2d) field2d.paintMode = true;
});
$('brush2d-slider').addEventListener('input', () => {
  const pct = parseInt($('brush2d-slider').value, 10);
  $('brush2d-out').textContent = pct + '%';
  if (field2d) field2d.brushRadius = pct / 100;
});
$('tab-1d').addEventListener('click', () => activate('1d'));
$('tab-2d').addEventListener('click', () => activate('2d'));
$('tab-3d').addEventListener('click', () => activate('3d'));

// ---- dynamics mode: pure / perturbed ----------------------------------------

let perturbed = false;
function currentEta() {
  return perturbed ? parseFloat($('eta-slider').value) : 0;
}
function applyDynamics() {
  const eta = currentEta();
  $('eta-row').style.display = perturbed ? '' : 'none';
  $('btn-pure').classList.toggle('active', !perturbed);
  $('btn-pert').classList.toggle('active', perturbed);
  const badge = $('mode-badge');
  if (perturbed) {
    badge.className = 'mode-badge pert';
    badge.innerHTML =
      'Perturbed mode — integrability-breaking perturbation (proxy), ' +
      '<b>PROVISIONAL</b>. Slow kink\u2013antikink pairs capture into bions ' +
      'and decay by radiation: genuine annihilation.';
  } else {
    badge.className = 'mode-badge pure';
    badge.innerHTML =
      'Pure sector: exactly integrable. Kinks always pass through each other ' +
      '(phase shift only); kink\u2013antikink pairs never annihilate; no radiation.';
  }
  view1d.setEta(eta);
  if (field2d) field2d.setEta(eta);
  updateExactAvailability();
}
$('btn-pure').addEventListener('click', () => { perturbed = false; applyDynamics(); });
$('btn-pert').addEventListener('click', () => { perturbed = true; applyDynamics(); });
$('eta-slider').addEventListener('input', () => {
  $('eta-out').textContent = parseFloat($('eta-slider').value).toFixed(3);
  applyDynamics();
});

// ---- Advanced / Verification panel ------------------------------------------

$('btn-advanced-toggle').addEventListener('click', () => {
  const body = $('advanced-body');
  const open = body.style.display === 'none';
  body.style.display = open ? '' : 'none';
  $('btn-advanced-toggle').setAttribute('aria-expanded', String(open));
  $('advanced-toggle-arrow').innerHTML = open ? '&#9662;' : '&#9656;';
});

// Feature 1: exact analytic overlay (pure sector only, 1D mode only) -------

const chkExact = $('chk-exact');
function updateExactAvailability() {
  const available = !perturbed;
  chkExact.disabled = !available;
  $('chk-exact-label').setAttribute('aria-disabled', String(!available));
  $('chk-exact-label').title = available
    ? ''
    : 'no closed-form solution exists in Perturbed mode -- switch to Pure to enable';
  if (!available && chkExact.checked) {
    chkExact.checked = false;
    view1d.setShowExact(false);
  }
}
chkExact.addEventListener('change', () => {
  view1d.setShowExact(chkExact.checked);
  if (!chkExact.checked) {
    $('exact-status').textContent = '';
    $('exact-residual-row').style.display = 'none';
  }
});
updateExactAvailability();

// Feature 2: SCC-deviation exploration (1D mode only) -----------------------

const sccSlider = $('scc-slider');
const SCC_REAL_MEV = M_PHI_MEV; // the actual, derived SCC value (1776.86 MeV)

function positionSccTick() {
  const min = parseFloat(sccSlider.min), max = parseFloat(sccSlider.max);
  const frac = (SCC_REAL_MEV - min) / (max - min);
  $('scc-tick').style.left = `calc(${(frac * 100).toFixed(3)}% - 1px)`;
}

function updateSccDisplay() {
  const mPhi = parseFloat(sccSlider.value);
  $('scc-out').textContent = mPhi.toFixed(2);
  view1d.setEffectiveMPhi(mPhi);

  const lenFm = lengthUnitFmFor(mPhi), realLenFm = lengthUnitFmFor(SCC_REAL_MEV);
  const mKink = kinkMassMevFor(mPhi), realMKink = kinkMassMevFor(SCC_REAL_MEV);
  const rows = [
    ['kink mass M_kink = (8/49)&middot;m<sub>&phi;</sub>', `${mKink.toFixed(2)} MeV`, `${realMKink.toFixed(2)} MeV`],
    ['kink width = &#295;c/m<sub>&phi;</sub>', `${lenFm.toFixed(4)} fm`, `${realLenFm.toFixed(4)} fm`],
    ['m<sub>&phi;</sub>', `${mPhi.toFixed(2)} MeV`, `${SCC_REAL_MEV.toFixed(2)} MeV`],
  ];
  $('scc-rows').innerHTML = rows.map(([label, a, b]) =>
    `<tr><td>${label}</td><td>${a}</td><td>${b}</td></tr>`).join('');

  const deviationPct = 100 * Math.abs(mPhi - SCC_REAL_MEV) / SCC_REAL_MEV;
  const verdict = $('scc-verdict');
  if (deviationPct < 1e-6) {
    verdict.innerHTML = 'This is exactly the derived SCC value &mdash; nothing is excluded here.';
  } else {
    verdict.innerHTML =
      `At m<sub>&phi;</sub> = ${mPhi.toFixed(2)} MeV, the derived kink mass would be ` +
      `<b>${mKink.toFixed(2)} MeV</b> &mdash; but the Self-Consistency Condition fixes ` +
      `m<sub>&phi;</sub> = m<sub>&tau;</sub> = <b>${SCC_REAL_MEV.toFixed(2)} MeV</b> exactly, ` +
      `which is what gives the actual GTE kink mass, <b>${realMKink.toFixed(2)} MeV</b>. ` +
      `This slider value departs from the SCC by ${deviationPct.toFixed(2)}% and is therefore ` +
      `<b>excluded</b> &mdash; m<sub>&phi;</sub> is not a free parameter.`;
  }
}

$('chk-scc').addEventListener('change', () => {
  const on = $('chk-scc').checked;
  $('scc-body').style.display = on ? '' : 'none';
  $('scc-off-hint').style.display = on ? 'none' : '';
  if (on) {
    sccSlider.value = String(SCC_REAL_MEV);
    updateSccDisplay();
  } else {
    view1d.setEffectiveMPhi(SCC_REAL_MEV);
  }
});
sccSlider.addEventListener('input', updateSccDisplay);
$('btn-scc-reset').addEventListener('click', () => {
  sccSlider.value = String(SCC_REAL_MEV);
  updateSccDisplay();
});
positionSccTick();
updateSccDisplay();

// ---- simulation controls ----------------------------------------------------

let running = true;
$('btn-pause').addEventListener('click', () => {
  running = !running;
  $('btn-pause').textContent = running ? 'Pause' : 'Run';
  view1d.running = running;
  if (field2d) field2d.running = running;
});
$('btn-step').addEventListener('click', () => {
  if (mode === '1d' && !view1d.replay) view1d.singleStep();
  if (mode === '2d' && field2d) field2d._steps(1);
});
// presets localized near the domain center benefit from a tighter default
// framing than the full periodic tile; other presets fill the whole domain
const PRESET_ZOOM = { junction: 0.28, bubble: 0.22, particles: 0.48, proton: 0.24, neutron: 0.24 };
$('preset2d-select').addEventListener('change', () => {
  $('particlecount2d-row').style.display =
    $('preset2d-select').value === 'particles' ? '' : 'none';
});
$('particlecount2d-slider').addEventListener('input', () => {
  const n = parseInt($('particlecount2d-slider').value, 10);
  $('particlecount2d-out').textContent = String(n);
  if (field2d) field2d.particleCount = n;
});
function applyPreset2d() {
  const preset = $('preset2d-select').value;
  if (!field2d) return;
  if (preset === 'particles') {
    field2d.particleCount = parseInt($('particlecount2d-slider').value, 10);
  }
  field2d.reseed(preset);
  field2d.center = [0.5, 0.5];
  field2d.zoom = PRESET_ZOOM[preset] || 0.5;
  syncZoomSlider();
}
$('btn-reset').addEventListener('click', () => {
  if (mode === '1d') { $('replay-select').value = ''; view1d.reset(); }
  if (mode === '2d') applyPreset2d();
});
$('btn-gas').addEventListener('click', () => {
  $('replay-select').value = '';
  view1d.randomGas(parseInt($('gas-slider').value, 10));
});
$('btn-reseed').addEventListener('click', applyPreset2d);
$('gas-slider').addEventListener('input', () => {
  $('gas-out').textContent = $('gas-slider').value;
});

// speed: log slider 0..100 -> time units per second
function speedFromSlider() {
  const s = parseInt($('speed-slider').value, 10) / 100;
  const range = mode === '2d' ? [0.2, 40] : [0.5, 200];
  return range[0] * Math.pow(range[1] / range[0], s);
}
function updateSpeedLabel() {
  const v = speedFromSlider();
  $('speed-out').textContent = v >= 10 ? v.toFixed(0) : v.toFixed(1);
  if (mode === '2d' && field2d) field2d.speed = v;
  else view1d.speed = v;
}
$('speed-slider').addEventListener('input', updateSpeedLabel);

// zoom: slider 0..100 <-> the same log-parametrized bounds as each mode's
// wheel zoom (0 = fully zoomed out, 100 = maximum magnification), kept in
// bidirectional sync: wheel-zooming moves the slider, dragging the slider
// zooms the active view about its current center.
function activeZoomTarget() {
  if (mode === '2d') return field2d;
  if (mode === '3d') return view3d;
  return view1d;
}
function syncZoomSlider() {
  const t = activeZoomTarget();
  if (!t) return;
  $('zoom-slider').value = String(Math.round(t.getZoomFrac() * 100));
  updateZoomLabel();
}
function updateZoomLabel() {
  const t = activeZoomTarget();
  if (!t) return;
  const v = t.getZoomFactor();
  $('zoom-out').textContent = (v >= 10 ? v.toFixed(0) : v.toFixed(1)) + '\u00d7';
}
$('zoom-slider').addEventListener('input', () => {
  const t = activeZoomTarget();
  if (!t) return;
  t.setZoomFrac(parseInt($('zoom-slider').value, 10) / 100);
  updateZoomLabel();
});
view1d.onZoomChanged = syncZoomSlider;

// ---- isolated-domain decay measurement (2D) --------------------------------

let lastHistoryLen = -1;
const domainChartCanvas = $('chart-domain-history');
const domainTrendReadout = $('domain-trend-readout');

function formatTrendReadout(trend) {
  if (trend.status === 'insufficient') {
    return `collecting samples\u2026 (${trend.nPoints} so far, need \u2265 5)`;
  }
  if (trend.status === 'flat') {
    return `stable to within \u00b1${trend.stabilityFrac.toFixed(1)}% of its mean ` +
      `over ${trend.rangeX.toFixed(1)} fm/c observed \u2014 no slope exceeding ` +
      `2\u00d7 its own statistical uncertainty (no measurable decay yet).`;
  }
  if (trend.status === 'linear') {
    const sign = trend.linB >= 0 ? '+' : '\u2212';
    return `domain area: ${sign}${Math.abs(trend.linB).toFixed(3)}%/fm\u00b7c ` +
      `(linear fit \u2014 constant-rate loss, the generic curvature-flow ` +
      `signature) over ${trend.rangeX.toFixed(1)} fm/c observed.`;
  }
  // exponential
  const efold = trend.expK !== 0 ? Math.abs(1 / trend.expK) : Infinity;
  const sign = trend.expK < 0 ? 'shrinking' : 'growing';
  return `domain area ${sign} with e-folding time ${efold.toFixed(1)} fm/c ` +
    `(exponential fit fits better than linear) over ${trend.rangeX.toFixed(1)} fm/c observed.`;
}

function updateDomainHistoryUI() {
  const history = (field2d && field2d.history) || [];
  // Convert to display units: fm/c on x, percent area fraction on y.
  const disp = history.map(([t, frac]) => [t * TIME_UNIT_FM_C, frac * 100]);
  drawHistoryChart(domainChartCanvas, disp, {
    yLabelFmt: (v) => v.toFixed(1) + '%',
    emptyText: 'seed a domain and let it run\u2026',
  });
  const trend = analyzeTrend(disp, { minPoints: 5 });
  domainTrendReadout.textContent = formatTrendReadout(trend);
  domainTrendReadout.className = trend.status === 'flat' ? 'flat'
    : (trend.status === 'linear' || trend.status === 'exponential') ? 'trend' : '';
}
$('btn-reset-measurement').addEventListener('click', () => {
  if (field2d) field2d.resetMeasurement();
  lastHistoryLen = -1; // force an immediate chart/readout refresh
  updateDomainHistoryUI();
});

// ---- replay loading -----------------------------------------------------------

async function loadReplay(name) {
  const meta = await (await fetch(`replay/${name}.meta.json`)).json();
  const buf = await (await fetch(`replay/${name}.field.f32`)).arrayBuffer();
  const field = new Float32Array(buf);
  if (field.length !== meta.nt * meta.nx) {
    throw new Error(`replay ${name}: field size mismatch`);
  }
  const x = new Float32Array(meta.nx);
  for (let i = 0; i < meta.nx; i++) x[i] = meta.x0 + i * meta.dx;
  const t = new Float32Array(meta.nt);
  for (let i = 0; i < meta.nt; i++) t[i] = meta.t0 + i * meta.dt;
  return { name, x, t, field, nx: meta.nx, nt: meta.nt, pure: meta.pure };
}

$('replay-select').addEventListener('change', async () => {
  const v = $('replay-select').value;
  if (!v) { view1d.reset(); return; }
  try {
    view1d.loadReplay(await loadReplay(v));
  } catch (err) {
    alert('Replay data not found. Generate it with export_replay_json.py ' +
      'in the viz directory.\n\n' + err.message);
    $('replay-select').value = '';
  }
});

// ---- boot ---------------------------------------------------------------------

applyDynamics();
updateSpeedLabel();
$('eta-out').textContent = parseFloat($('eta-slider').value).toFixed(3);
view1d.resize();
syncZoomSlider();
// default demo scene: a moving multi-kink gas, never a blank vacuum
view1d.randomGas(12);
window.addEventListener('resize', () => view1d.resize());

function loop(now) {
  if (mode === '1d') view1d.tick(now);
  else if (mode === '2d' && field2d) {
    field2d.tick(now);
    if (field2d.stats) {
      $('stat-domains').textContent = String(field2d.stats.domainCount);
      $('stat-largest').textContent = (field2d.stats.largestFraction * 100).toFixed(1) + '%';
      $('stat-wall').textContent = (field2d.stats.wallFraction * 100).toFixed(1) + '%';
      if (field2d.history.length !== lastHistoryLen) {
        lastHistoryLen = field2d.history.length;
        updateDomainHistoryUI();
      }
    }
  }
  else if (mode === '3d' && view3d) view3d.tick(now);
  requestAnimationFrame(loop);
}
requestAnimationFrame(loop);

// console access for scripted checks (e.g. integrator validation)
window.kinkViz = { view1d, get field2d() { return field2d; }, get view3d() { return view3d; } };
