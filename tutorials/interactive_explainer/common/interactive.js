/* ═══════════════════════════════════════════════════════════════════════════
   UGP Physics — Interactive Explainer
   interactive.js — Component library
   ═══════════════════════════════════════════════════════════════════════════ */

'use strict';

// ─── Step-through panels ────────────────────────────────────────────────────

function initSteps(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const pills   = container.querySelectorAll('.step-pill');
  const panels  = container.querySelectorAll('.step-panel');
  const prevBtn = container.querySelector('[data-action="prev"]');
  const nextBtn = container.querySelector('[data-action="next"]');
  const counter = container.querySelector('.steps-counter');
  const total   = panels.length;
  let current   = 0;

  function goTo(idx) {
    idx = Math.max(0, Math.min(total - 1, idx));
    current = idx;
    pills.forEach((p, i)  => p.classList.toggle('active', i === idx));
    panels.forEach((p, i) => p.classList.toggle('active', i === idx));
    if (prevBtn) prevBtn.disabled = idx === 0;
    if (nextBtn) nextBtn.disabled = idx === total - 1;
    if (counter) counter.textContent = `Step ${idx + 1} of ${total}`;
  }

  pills.forEach((pill, i) => pill.addEventListener('click', () => goTo(i)));
  if (prevBtn) prevBtn.addEventListener('click', () => goTo(current - 1));
  if (nextBtn) nextBtn.addEventListener('click', () => goTo(current + 1));
  goTo(0);
}

// ─── Tab switcher ────────────────────────────────────────────────────────────

function tabSwitch(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const btns   = container.querySelectorAll('.tab-btn');
  const panels = container.querySelectorAll('.tab-panel');

  function activate(idx) {
    btns.forEach((b, i)   => b.classList.toggle('active', i === idx));
    panels.forEach((p, i) => p.classList.toggle('active', i === idx));
  }

  btns.forEach((btn, i) => btn.addEventListener('click', () => activate(i)));
  activate(0);
}

// ─── Collapsible ─────────────────────────────────────────────────────────────

function collapsible(triggerId, contentId) {
  const trigger = document.getElementById(triggerId);
  const content = document.getElementById(contentId);
  if (!trigger || !content) return;

  trigger.addEventListener('click', () => {
    const open = content.classList.toggle('open');
    trigger.classList.toggle('open', open);
  });
}

// ─── CSS variable helpers ─────────────────────────────────────────────────────

function cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

// ─── SVG helper ───────────────────────────────────────────────────────────────

const SVG_NS = 'http://www.w3.org/2000/svg';

function svgEl(tag, attrs) {
  const el = document.createElementNS(SVG_NS, tag);
  Object.entries(attrs || {}).forEach(([k, v]) => el.setAttribute(k, v));
  return el;
}

function svgText(content, attrs) {
  const el = svgEl('text', { 'font-family': 'inherit', ...attrs });
  el.textContent = content;
  return el;
}

// ─── Prime Ring ───────────────────────────────────────────────────────────────
// Usage: <svg class="prime-ring" data-prime="7" data-highlight="0,1"></svg>

function renderPrimeRing(el) {
  if (!el) return;
  const prime = parseInt(el.dataset.prime || '7', 10);
  const hl    = (el.dataset.highlight || '').split(',').map(Number).filter(n => !isNaN(n));
  const size  = 140;
  const cx    = size / 2;
  const cy    = size / 2;
  const r     = 50;

  const accent  = cssVar('--accent') || '#3B82F6';
  const bgElev  = cssVar('--bg-elevated') || '#1F1F23';
  const text1   = cssVar('--text-primary') || '#F4F4F5';
  const text3   = cssVar('--text-tertiary') || '#71717A';
  const stroke  = cssVar('--stroke-primary') || 'rgba(255,255,255,0.12)';

  el.setAttribute('viewBox', `0 0 ${size} ${size}`);
  el.setAttribute('aria-label', `Prime ring for p=${prime}`);

  // Background ring
  el.appendChild(svgEl('circle', { cx, cy, r, fill: 'none', stroke, 'stroke-width': '1.5' }));

  // Residue nodes
  for (let n = 0; n < prime; n++) {
    const angle = (2 * Math.PI * n / prime) - Math.PI / 2;
    const x = (cx + r * Math.cos(angle)).toFixed(2);
    const y = (cy + r * Math.sin(angle)).toFixed(2);
    const isHL = hl.includes(n);

    el.appendChild(svgEl('circle', {
      cx: x, cy: y, r: 14,
      fill:         isHL ? accent : bgElev,
      stroke:       isHL ? accent : stroke,
      'stroke-width': '1.5',
    }));

    el.appendChild(svgText(n, {
      x, y,
      'text-anchor':      'middle',
      'dominant-baseline': 'central',
      'font-size':         '12',
      'font-weight':       isHL ? '700' : '400',
      fill: isHL ? '#fff' : text1,
    }));
  }

  // Center label
  el.appendChild(svgText(`p=${prime}`, {
    x: cx, y: cy,
    'text-anchor':      'middle',
    'dominant-baseline': 'central',
    'font-size':         '12',
    'font-weight':       '600',
    fill: text3,
  }));
}

// Auto-render all .prime-ring elements
function renderAllPrimeRings() {
  document.querySelectorAll('.prime-ring').forEach(renderPrimeRing);
}

// ─── Draw Tape ────────────────────────────────────────────────────────────────
// drawTape(svgEl, [0,1,3,2,0], { highlight: [2], showIndex: true, label: 't=0' })

function drawTape(el, states, opts) {
  if (!el) return;
  opts = opts || {};
  const hl        = opts.highlight || [];
  const showIndex = opts.showIndex !== false;
  const cw        = 52;
  const ch        = 50;
  const gap       = 4;
  const n         = states.length;
  const width     = n * (cw + gap) - gap + 20;
  const height    = showIndex ? ch + 26 : ch + 10;

  const accent  = cssVar('--accent') || '#3B82F6';
  const bgElev  = cssVar('--bg-elevated') || '#1F1F23';
  const text1   = cssVar('--text-primary') || '#F4F4F5';
  const text3   = cssVar('--text-tertiary') || '#71717A';
  const stroke  = cssVar('--stroke-primary') || 'rgba(255,255,255,0.12)';

  el.setAttribute('viewBox', `0 0 ${width} ${height}`);
  el.setAttribute('aria-label', `CA tape: [${states.join(', ')}]`);

  states.forEach((val, i) => {
    const x   = 10 + i * (cw + gap);
    const y   = 5;
    const isHL = hl.includes(i);

    el.appendChild(svgEl('rect', {
      x, y, width: cw, height: ch, rx: 6,
      fill:           isHL ? accent : (val > 0 ? 'rgba(59,130,246,0.12)' : bgElev),
      stroke:         isHL ? accent : stroke,
      'stroke-width': isHL ? '2' : '1',
    }));

    el.appendChild(svgText(val, {
      x: x + cw / 2, y: y + ch / 2,
      'text-anchor':      'middle',
      'dominant-baseline': 'central',
      'font-size': '18', 'font-weight': '700',
      fill: isHL ? '#fff' : text1,
    }));

    if (showIndex) {
      el.appendChild(svgText(i, {
        x: x + cw / 2, y: y + ch + 14,
        'text-anchor': 'middle',
        'font-size':   '11',
        fill: text3,
      }));
    }
  });
}

// ─── Triangle Diagram ─────────────────────────────────────────────────────────

function drawTriangle(el) {
  if (!el) return;
  const accent  = cssVar('--accent') || '#3B82F6';
  const bgElev  = cssVar('--bg-elevated') || '#1F1F23';
  const text1   = cssVar('--text-primary') || '#F4F4F5';
  const text3   = cssVar('--text-tertiary') || '#71717A';
  const stroke  = cssVar('--stroke-primary') || 'rgba(255,255,255,0.12)';

  el.setAttribute('viewBox', '0 0 300 185');
  el.setAttribute('aria-label', 'UGP triangle: three nodes and their relationships');

  // Arrow marker
  const defs   = svgEl('defs');
  const marker = svgEl('marker', { id: 'tri-arrow', markerWidth: '7', markerHeight: '6', refX: '6', refY: '3', orient: 'auto' });
  const mpath  = svgEl('path', { d: 'M0,0 L7,3 L0,6 Z', fill: stroke });
  marker.appendChild(mpath);
  defs.appendChild(marker);
  el.appendChild(defs);

  // Nodes
  const nodes = [
    { label: 'UGP arithmetic', sub: 'prime residues + invariants', x: 100, y: 4,   w: 100, h: 38, ac: true },
    { label: 'GTE orbit',      sub: 'spectrum + masses',           x: 5,   y: 135, w: 100, h: 38, ac: false },
    { label: 'Polynomial p',   sub: 'C+R\u2212CR\u2212LCR',       x: 195, y: 135, w: 100, h: 38, ac: false },
  ];

  nodes.forEach(({ label, sub, x, y, w, h, ac }) => {
    el.appendChild(svgEl('rect', { x, y, width: w, height: h, rx: 5, fill: bgElev, stroke: ac ? accent : stroke, 'stroke-width': ac ? '1.5' : '1' }));
    el.appendChild(svgText(label, { x: x + w/2, y: y + h/2 - 6, 'text-anchor': 'middle', 'font-size': '10', 'font-weight': '600', fill: text1, 'font-family': 'inherit' }));
    el.appendChild(svgText(sub,   { x: x + w/2, y: y + h/2 + 8, 'text-anchor': 'middle', 'font-size': '8',  fill: text3, 'font-family': 'inherit' }));
  });

  // Arrows
  [
    { x1: 130, y1: 42, x2: 74,  y2: 133, lbl: 'T map',             lx: 93,  ly: 93  },
    { x1: 170, y1: 42, x2: 226, y2: 133, lbl: 'UWCA',              lx: 208, ly: 93  },
    { x1: 108, y1: 154, x2: 193, y2: 154, lbl: 'orbit parity + MDL', lx: 150, ly: 168 },
  ].forEach(({ x1, y1, x2, y2, lbl, lx, ly }) => {
    el.appendChild(svgEl('line', { x1, y1, x2, y2, stroke, 'stroke-width': '1.5', 'marker-end': 'url(#tri-arrow)' }));
    el.appendChild(svgText(lbl, { x: lx, y: ly, 'text-anchor': 'middle', 'font-size': '7.5', fill: text3, 'font-family': 'inherit' }));
  });
}

// ─── Survivor Grid ────────────────────────────────────────────────────────────

function drawSurvivorGrid(el, survivorSet) {
  if (!el) return;
  const cols   = 16;
  const rows   = 5;
  const accent = cssVar('--accent') || '#3B82F6';
  const bgElev = cssVar('--bg-elevated') || '#1F1F23';
  const stroke = cssVar('--stroke-secondary') || 'rgba(255,255,255,0.07)';

  el.setAttribute('viewBox', `0 0 ${cols * 20 + 8} ${rows * 20 + 8}`);
  el.setAttribute('aria-label', 'Survivor space: dots representing valid UGP states');

  for (let row = 0; row < rows; row++) {
    for (let col = 0; col < cols; col++) {
      const isSurvivor = survivorSet.has(`${row},${col}`);
      el.appendChild(svgEl('circle', {
        cx:           col * 20 + 12,
        cy:           row * 20 + 12,
        r:            6,
        fill:         isSurvivor ? accent : bgElev,
        stroke:       isSurvivor ? accent : stroke,
        'stroke-width': '1',
        opacity:      isSurvivor ? '1' : '0.38',
      }));
    }
  }
}

// ─── Polynomial Truth Table ───────────────────────────────────────────────────
// Writes rows into <tbody id="tbodyId">

function renderPolynomialTruthTable(tbodyId) {
  const tbody = document.getElementById(tbodyId);
  if (!tbody) return;

  const cases  = [[1,1,1],[1,1,0],[1,0,1],[1,0,0],[0,1,1],[0,1,0],[0,0,1],[0,0,0]];
  const r110   = [0,1,1,0,1,1,1,0];
  const green  = cssVar('--cert-lean') || '#22C55E';
  const red    = '#EF4444';

  cases.forEach(([L,C,R], i) => {
    const pval  = C + R - C*R - L*C*R;   // always in {0,1} for binary input
    const rule  = r110[i];
    const match = pval === rule;
    const tr    = document.createElement('tr');
    tr.innerHTML =
      `<td>${L}</td><td>${C}</td><td>${R}</td>` +
      `<td><strong>${pval}</strong></td>` +
      `<td><strong>${rule}</strong></td>` +
      `<td style="color:${match ? green : red};font-weight:700">${match ? '=' : '≠'}</td>`;
    tbody.appendChild(tr);
  });
}

// ─── Lean Badge ───────────────────────────────────────────────────────────────
// Place <span data-lean="theorem_name"></span> anywhere in the page;
// call autoRenderLeanBadges(LEAN_REFS) after DOM is ready.

function autoRenderLeanBadges(leanRefs) {
  document.querySelectorAll('[data-lean]').forEach(el => {
    const name = el.dataset.lean;
    const ref  = leanRefs && leanRefs[name];
    el.className = 'cert cert--lean';
    if (ref) {
      el.innerHTML = `Cat<sub style="font-size:0.65em">AL</sub> · <a href="${ref.url}" class="cert-source" target="_blank" rel="noopener">view proof ↗</a>`;
    } else {
      el.innerHTML = `Cat<sub style="font-size:0.65em">AL</sub>`;
    }
  });
}

// ─── Auto-init on DOM ready ───────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  renderAllPrimeRings();

  // Triangle
  const tri = document.getElementById('triangle-diagram');
  if (tri) drawTriangle(tri);

  // Tape diagrams
  document.querySelectorAll('[data-tape]').forEach(el => {
    try {
      const states = JSON.parse(el.dataset.tape);
      const hl     = el.dataset.highlight ? JSON.parse(el.dataset.highlight) : [];
      drawTape(el, states, { highlight: hl });
    } catch(e) {}
  });

  // Survivor grid
  const sg = document.getElementById('survivor-grid');
  if (sg) {
    const survivors = new Set([
      '0,1','0,5','0,9','0,13',
      '1,3','1,7','1,11','1,15',
      '2,0','2,4','2,8','2,12',
      '3,2','3,6','3,10','3,14',
      '4,1','4,5','4,9','4,13',
    ]);
    drawSurvivorGrid(sg, survivors);
  }

  // Truth table
  renderPolynomialTruthTable('truth-table-body');
});
