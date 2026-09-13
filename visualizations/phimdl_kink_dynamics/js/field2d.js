// 2D mode: the same scalar EOM on a periodic 2D grid,
//   Phi_tt = lap(Phi) - (1/7) sin(7 Phi) - eta (2/7) sin(14 Phi),
// integrated by leapfrog on the GPU (WebGL2 fragment shader, ping-pong
// RG32F textures storing (Phi_n, v_{n+1/2})). One pass per step computes the
// exact leapfrog update: Phi_{n+1} = Phi_n + dt v; v' = v + dt (lap Phi_{n+1}
// - V'(Phi_{n+1})), with the neighbor Phi_{n+1} reconstructed in-shader.
// In 2D a single scalar's topological objects are domain WALLS.

import { VACUUM_COLORS } from './palette.js?v=7';
import { STEP, M_PHI_MEV } from './constants.js?v=7';

// Wheel/slider zoom bounds: view half-width in uv units of the periodic
// domain. 0.5 shows the whole tile (fully zoomed out); 0.02 is maximum
// magnification.
export const ZOOM_OUT_UV = 0.5;
export const ZOOM_IN_UV = 0.02;

const STEP_VS = `#version 300 es
in vec2 aPos;
void main() { gl_Position = vec4(aPos, 0.0, 1.0); }
`;

const STEP_FS = `#version 300 es
precision highp float;
uniform sampler2D uState;   // rg = (phi_n, v_{n+1/2})
uniform float uDt;
uniform float uInvDx2;
uniform float uEta;
out vec4 frag;

float phi1(ivec2 p, ivec2 sz) {
  vec2 s = texelFetch(uState, (p + sz) % sz, 0).rg;
  return s.r + uDt * s.g;
}

void main() {
  ivec2 p = ivec2(gl_FragCoord.xy);
  ivec2 sz = textureSize(uState, 0);
  vec2 c = texelFetch(uState, p, 0).rg;
  float pc = c.r + uDt * c.g;
  float lap = (phi1(p + ivec2(1,0), sz) + phi1(p - ivec2(1,0), sz)
             + phi1(p + ivec2(0,1), sz) + phi1(p - ivec2(0,1), sz)
             - 4.0 * pc) * uInvDx2;
  float vp = lap - sin(7.0 * pc) / 7.0 - uEta * (2.0 / 7.0) * sin(14.0 * pc);
  float vNew = c.g + uDt * vp;
  frag = vec4(pc, vNew, 0.0, 0.0);
}
`;

const PAINT_FS = `#version 300 es
precision highp float;
uniform sampler2D uState;
uniform vec2 uCenter;      // brush center, uv, wrapped to [0,1)
uniform float uRadius;     // brush radius, uv units
uniform float uTargetPhi;
out vec4 frag;

void main() {
  ivec2 p = ivec2(gl_FragCoord.xy);
  ivec2 sz = textureSize(uState, 0);
  vec2 uv = (vec2(p) + 0.5) / vec2(sz);
  vec2 d = uv - uCenter;
  d -= floor(d + 0.5);   // shortest periodic (toroidal) offset
  float t = smoothstep(uRadius, uRadius * 0.3, length(d));
  vec2 c = texelFetch(uState, p, 0).rg;
  float newPhi = mix(c.r, uTargetPhi, t);
  float newV = mix(c.g, 0.0, t);
  frag = vec4(newPhi, newV, 0.0, 0.0);
}
`;

const DRAW_FS = `#version 300 es
precision highp float;
uniform sampler2D uState;
uniform vec3 uPalette[7];
uniform vec2 uCenter;    // view center in uv
uniform float uZoom;     // view half-width in uv
uniform vec2 uRes;       // canvas resolution in px
out vec4 frag;

vec2 stateAt(vec2 uv) {
  // manual bilinear (float textures are not filterable at highp)
  vec2 sz = vec2(textureSize(uState, 0));
  vec2 st = uv * sz - 0.5;
  vec2 i = floor(st), f = st - i;
  ivec2 szi = ivec2(sz);
  ivec2 i00 = (ivec2(i) % szi + szi) % szi;
  ivec2 i10 = (i00 + ivec2(1,0)) % szi;
  ivec2 i01 = (i00 + ivec2(0,1)) % szi;
  ivec2 i11 = (i00 + ivec2(1,1)) % szi;
  vec2 a = mix(texelFetch(uState,i00,0).rg, texelFetch(uState,i10,0).rg, f.x);
  vec2 b = mix(texelFetch(uState,i01,0).rg, texelFetch(uState,i11,0).rg, f.x);
  return mix(a, b, f.y);
}

void main() {
  float minDim = min(uRes.x, uRes.y);
  vec2 uv = uCenter + ((gl_FragCoord.xy - 0.5 * uRes) / minDim) * 2.0 * uZoom;
  float phi = stateAt(uv).r;
  float STEPV = 2.0 * 3.14159265358979 / 7.0;
  float kf = phi / STEPV;
  int k = int(mod(round(kf), 7.0) + 7.0) % 7;
  float dev = min(1.0, abs(phi - round(kf) * STEPV) / (STEPV * 0.5));
  vec3 base = uPalette[k] * (0.62 + 0.38 * dev * dev);
  vec3 col = base + vec3(0.85, 0.9, 1.0) * dev * dev * 0.55;   // wall glow
  frag = vec4(col, 1.0);
}
`;

export class Field2D {
  constructor(canvas, readouts) {
    this.canvas = canvas;
    this.readouts = readouts;
    this.n = 512;
    this.dx = 0.12;
    this.dt = 0.5 * this.dx;          // 2D CFL: dt <= dx/sqrt(2); 0.5 dx is safe
    this.eta = 0;
    this.t = 0;
    this.running = true;
    this.speed = 4;                    // natural time units per second
    this.maxStepsPerFrame = 160;
    this.E0 = null;
    this.energyMeV = undefined;
    this.energyDrift = 0;
    this.lastTime = performance.now();
    // view: center in uv (0..1), zoom = half-width in uv (fully zoomed out)
    this.center = [0.5, 0.5];
    this.zoom = ZOOM_OUT_UV;
    this.frame = 0;

    // paint tool
    this.paintMode = false;      // false = drag pans; true = drag paints
    this.paintK = 4;             // vacuum index currently armed for painting
    this.brushRadius = 0.05;     // uv units (fraction of the periodic domain)
    this.stats = null;           // last computed domain statistics
    this.particleCount = 3;      // bubble count for the 'particles' preset

    // Isolated-domain size history: (t, largestNonBackgroundFraction) pairs,
    // sampled at the same cadence as _domainStats (every 120 frames). Used
    // to measure whether a seeded domain (e.g. the single-bubble preset)
    // shrinks over time and at what rate. Capped ring-style array; oldest
    // samples are evicted once the cap is reached.
    this.history = [];
    this.historyCap = 2000;

    this._initGL();
    this._bindEvents();
    this.reseed();
  }

  _initGL() {
    const gl = this.canvas.getContext('webgl2', { antialias: false });
    if (!gl) throw new Error('WebGL2 unavailable');
    if (!gl.getExtension('EXT_color_buffer_float')) {
      throw new Error('EXT_color_buffer_float unavailable');
    }
    this.gl = gl;

    const compile = (type, src) => {
      const s = gl.createShader(type);
      gl.shaderSource(s, src);
      gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
        throw new Error(gl.getShaderInfoLog(s));
      }
      return s;
    };
    const link = (fsSrc) => {
      const p = gl.createProgram();
      gl.attachShader(p, compile(gl.VERTEX_SHADER, STEP_VS));
      gl.attachShader(p, compile(gl.FRAGMENT_SHADER, fsSrc));
      gl.linkProgram(p);
      if (!gl.getProgramParameter(p, gl.LINK_STATUS)) {
        throw new Error(gl.getProgramInfoLog(p));
      }
      return p;
    };
    this.stepProg = link(STEP_FS);
    this.drawProg = link(DRAW_FS);
    this.paintProg = link(PAINT_FS);

    const quad = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, quad);
    gl.bufferData(gl.ARRAY_BUFFER,
      new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    this.quad = quad;

    this.tex = [this._makeTex(), this._makeTex()];
    this.fbo = gl.createFramebuffer();
    this.src = 0;
  }

  _makeTex() {
    const gl = this.gl;
    const t = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, t);
    gl.texStorage2D(gl.TEXTURE_2D, 1, gl.RG32F, this.n, this.n);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.REPEAT);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.REPEAT);
    return t;
  }

  _bindEvents() {
    const c = this.canvas;
    // screen -> uv offset, consistent with the shader's minDim mapping
    const frac = (e) => {
      const r = c.getBoundingClientRect();
      const m = Math.min(r.width, r.height);
      return [((e.clientX - r.left) - 0.5 * r.width) / m,
              (0.5 * r.height - (e.clientY - r.top)) / m];
    };
    c.addEventListener('wheel', (e) => {
      e.preventDefault();
      const [fx, fy] = frac(e);
      const uvx = this.center[0] + fx * 2 * this.zoom;
      const uvy = this.center[1] + fy * 2 * this.zoom;
      const f = Math.exp(e.deltaY * 0.0015);
      this.zoom = Math.min(ZOOM_OUT_UV, Math.max(ZOOM_IN_UV, this.zoom * f));
      this.center[0] = uvx - fx * 2 * this.zoom;
      this.center[1] = uvy - fy * 2 * this.zoom;
      if (this.onZoomChanged) this.onZoomChanged();
    }, { passive: false });
    const uvAt = (e) => {
      const [fx, fy] = frac(e);
      let ux = this.center[0] + fx * 2 * this.zoom;
      let uy = this.center[1] + fy * 2 * this.zoom;
      ux -= Math.floor(ux); uy -= Math.floor(uy);
      return [ux, uy];
    };
    let pan = null;
    let painting = false;
    c.addEventListener('pointerdown', (e) => {
      try { c.setPointerCapture(e.pointerId); } catch (_) { /* capture unsupported for this pointer */ }
      const wantsPan = e.button === 1 || e.button === 2 || e.altKey || !this.paintMode;
      if (wantsPan) {
        pan = { f: frac(e), c: [...this.center] };
      } else {
        painting = true;
        this._paintAt(uvAt(e));
      }
    });
    c.addEventListener('pointermove', (e) => {
      if (pan) {
        const [fx, fy] = frac(e);
        this.center[0] = pan.c[0] - (fx - pan.f[0]) * 2 * this.zoom;
        this.center[1] = pan.c[1] - (fy - pan.f[1]) * 2 * this.zoom;
      } else if (painting) {
        this._paintAt(uvAt(e));
      }
    });
    c.addEventListener('pointerup', () => { pan = null; painting = false; });
    c.addEventListener('pointercancel', () => { pan = null; painting = false; });
  }

  setEta(eta) { this.eta = eta; }

  // Zoom expressed as a 0..1 fraction of the wheel-zoom bounds (0 = whole
  // periodic tile in view, 1 = maximum magnification), log-parametrized
  // like the wheel. Slider-driven zoom keeps the current view center.
  getZoomFrac() {
    const f = Math.log(this.zoom / ZOOM_OUT_UV) / Math.log(ZOOM_IN_UV / ZOOM_OUT_UV);
    return Math.max(0, Math.min(1, f));
  }
  setZoomFrac(f) {
    const ff = Math.max(0, Math.min(1, f));
    this.zoom = ZOOM_OUT_UV * Math.pow(ZOOM_IN_UV / ZOOM_OUT_UV, ff);
  }
  // Magnification factor relative to fully zoomed out, for the readout.
  getZoomFactor() { return ZOOM_OUT_UV / this.zoom; }

  // Stamp a filled circle of vacuum `this.paintK` at brush center `uv`
  // (uv wrapped to [0,1)) with radius `this.brushRadius` (periodic-aware).
  _paintAt(uv) {
    const gl = this.gl;
    const targetPhi = STEP * this.paintK;
    gl.useProgram(this.paintProg);
    gl.viewport(0, 0, this.n, this.n);
    gl.bindBuffer(gl.ARRAY_BUFFER, this.quad);
    const loc = gl.getAttribLocation(this.paintProg, 'aPos');
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    gl.uniform2f(gl.getUniformLocation(this.paintProg, 'uCenter'), uv[0], uv[1]);
    gl.uniform1f(gl.getUniformLocation(this.paintProg, 'uRadius'), this.brushRadius);
    gl.uniform1f(gl.getUniformLocation(this.paintProg, 'uTargetPhi'), targetPhi);
    gl.bindFramebuffer(gl.FRAMEBUFFER, this.fbo);
    const dst = 1 - this.src;
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0,
      gl.TEXTURE_2D, this.tex[dst], 0);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, this.tex[this.src]);
    gl.uniform1i(gl.getUniformLocation(this.paintProg, 'uState'), 0);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    this.src = dst;
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    this.E0 = null; // painting changes the energy baseline; rebaseline next readback
  }

  // Presets for the initial condition. 'random' is the original long-
  // wavelength Fourier seed; the others are deterministic, sharp-edged
  // constructions that let dynamics build a specific wall/junction scenario
  // to order, rather than waiting for one to appear by chance.
  reseed(preset = 'random') {
    const n = this.n;
    const data = new Float32Array(n * n * 2);
    const set = (i, j, phi) => { data[(j * n + i) * 2] = phi; data[(j * n + i) * 2 + 1] = 0; };
    // V(Phi) has period STEP (one vacuum spacing): any integer multiple of
    // STEP congruent to k mod 7 is physically the same vacuum k. When one
    // preset region borders another, pick the congruent integer closest to
    // the neighbor's raw value, so the box-blur smoothing (which operates
    // on the raw real-valued Phi, not mod-7 labels) bridges them by the
    // genuinely shortest elementary-kink path instead of spuriously
    // wandering through every intermediate vacuum the "long way around".
    const phiNear = (k, neighborPhi) => {
      const neighborK = neighborPhi / STEP;
      let d = ((k - neighborK) % 7 + 7) % 7;
      if (d > 3) d -= 7;
      return neighborPhi + d * STEP;
    };

    if (preset === 'random') {
      const NM = 14;
      const modes = [];
      for (let m = 0; m < NM; m++) {
        const kmag = 1 + Math.floor(Math.random() * 5);
        const ang = Math.random() * Math.PI * 2;
        modes.push({
          kx: (2 * Math.PI * Math.round(kmag * Math.cos(ang))) / n,
          ky: (2 * Math.PI * Math.round(kmag * Math.sin(ang))) / n,
          ph: Math.random() * Math.PI * 2,
          a: (0.8 + 0.6 * Math.random()) / Math.sqrt(NM),
        });
      }
      const amp = 3.2 * STEP;
      for (let j = 0; j < n; j++) {
        for (let i = 0; i < n; i++) {
          let v = 0;
          for (const md of modes) v += md.a * Math.cos(md.kx * i + md.ky * j + md.ph);
          set(i, j, amp * v);
        }
      }
    } else if (preset === 'vacuum') {
      // blank canvas: pure vacuum, for painting your own configuration
      for (let j = 0; j < n; j++) for (let i = 0; i < n; i++) set(i, j, 0);
    } else if (preset === 'bubble') {
      const R = n * 0.16, cx = n / 2, cy = n / 2;
      const inPhi = phiNear(4, 0);
      for (let j = 0; j < n; j++) for (let i = 0; i < n; i++) {
        const inside = Math.hypot(i - cx, j - cy) < R;
        set(i, j, inside ? inPhi : 0);
      }
    } else if (preset === 'particles') {
      // N non-overlapping bubbles, each a random SM sector color
      // {2,3,4,6}: up-quark, W+/positron, charged lepton, down-quark.
      const N = this.particleCount || 3;
      const R = n * (0.14 / Math.sqrt(N + 1));
      const minSep = 2.3 * R;
      const SM_SECTORS = [2, 3, 4, 6];
      const bubbles = [];
      for (let b = 0; b < N; b++) {
        let best = null, bestMinD = -1;
        for (let attempt = 0; attempt < 60; attempt++) {
          const x = n * (0.12 + 0.76 * Math.random());
          const y = n * (0.12 + 0.76 * Math.random());
          let minD = Infinity;
          for (const other of bubbles) minD = Math.min(minD, Math.hypot(x - other.x, y - other.y));
          if (bubbles.length === 0 || minD >= minSep) { best = { x, y }; break; }
          if (minD > bestMinD) { bestMinD = minD; best = { x, y }; }
        }
        const k = SM_SECTORS[Math.floor(Math.random() * SM_SECTORS.length)];
        bubbles.push({ x: best.x, y: best.y, phi: phiNear(k, 0) });
      }
      for (let j = 0; j < n; j++) for (let i = 0; i < n; i++) {
        let phi = 0;
        for (const bub of bubbles) {
          if (Math.hypot(i - bub.x, j - bub.y) < R) { phi = bub.phi; break; }
        }
        set(i, j, phi);
      }
    } else if (preset === 'proton' || preset === 'neutron') {
      // Illustrative arrangement only -- NOT a derived bound state. Places
      // the three quark sectors close together with charge-correct windings
      // (uud: 2,2,6 -> +2/3+2/3-1/3 = +1; udd: 2,6,6 -> +2/3-1/3-1/3 = 0),
      // but this pure-phi field has no color/gauge sector, so nothing here
      // actually confines them: the real dynamics will show whether they
      // stay clustered or drift apart under the phi-only forces alone.
      const R = n * 0.055, sep = 2.5 * R, cx = n / 2, cy = n / 2;
      const ks = preset === 'proton' ? [2, 2, 6] : [2, 6, 6];
      for (let q = 0; q < 3; q++) {
        const ang = (Math.PI / 2) + q * (2 * Math.PI / 3);
        ks[q] = { x: cx + sep * Math.cos(ang), y: cy + sep * Math.sin(ang), phi: phiNear(ks[q], 0) };
      }
      for (let j = 0; j < n; j++) for (let i = 0; i < n; i++) {
        let phi = 0;
        for (const qk of ks) {
          if (Math.hypot(i - qk.x, j - qk.y) < R) { phi = qk.phi; break; }
        }
        set(i, j, phi);
      }
    } else if (preset === 'stripes') {
      const band = n / 7;
      for (let j = 0; j < n; j++) {
        const k = Math.floor(j / band) % 7;
        for (let i = 0; i < n; i++) set(i, j, STEP * k);
      }
    } else if (preset === 'checker') {
      const cell = n / 10, altPhi = phiNear(4, 0);
      for (let j = 0; j < n; j++) for (let i = 0; i < n; i++) {
        const onAlt = (Math.floor(i / cell) + Math.floor(j / cell)) % 2 !== 0;
        set(i, j, onAlt ? altPhi : 0);
      }
    } else if (preset === 'junction') {
      // Three domains meeting at a single point -- the 2D analog of the
      // 3+1D (w,w,w) triple-winding localization question. Confined to a
      // disk with a uniform background outside it (a different vacuum),
      // so the construction is periodic-safe: a bare radial 3-fold sector
      // pattern is NOT periodic (3-fold symmetry doesn't match a straight
      // line's 180-degree antipodal wrap), so extending it to the domain
      // edge creates spurious extra walls at the periodic seam.
      const cx = n / 2, cy = n / 2, R = n * 0.22;
      const bgPhi = STEP * 6;
      const innerPhi = [2, 3, 4].map((k) => phiNear(k, bgPhi));
      for (let j = 0; j < n; j++) for (let i = 0; i < n; i++) {
        const r = Math.hypot(i - cx, j - cy);
        if (r >= R) { set(i, j, bgPhi); continue; }
        const ang = Math.atan2(j - cy, i - cx);
        const sector = Math.floor(((ang + Math.PI) / (2 * Math.PI)) * 3) % 3;
        // adjacent vacua 2,3,4: two of the three internal walls are single
        // elementary kinks (2-3 and 3-4), the third (4-2) is an unavoidable
        // composite 2-step wall -- a genuine consequence of the Z7 vacuum
        // ring having no triangles, not an artifact of this construction.
        set(i, j, innerPhi[sector]);
      }
    }

    // Sharp step edges dump a lot of energy into high-frequency ringing on
    // the first few steps; pre-smooth so the initial condition starts near
    // a relaxed profile (kink width ~1 natural unit ~ 8 grid cells at this
    // dx, so a handful of small-radius periodic box-blur passes is enough).
    if (preset !== 'random') this._smoothPhi(data, n, 10, 2);

    const gl = this.gl;
    for (const t of this.tex) {
      gl.bindTexture(gl.TEXTURE_2D, t);
      gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, n, n, gl.RG, gl.FLOAT, data);
    }
    this.t = 0;
    this.E0 = null;
    this.frame = 0;
    this.stats = null;
    this.history = [];
  }

  // Periodic separable box blur applied to the phi channel only, to soften
  // sharp preset edges before handing them to the leapfrog integrator.
  _smoothPhi(data, n, iterations, radius) {
    const tmp = new Float32Array(n * n);
    const inv = 1 / (2 * radius + 1);
    for (let it = 0; it < iterations; it++) {
      for (let j = 0; j < n; j++) {
        const row = j * n;
        for (let i = 0; i < n; i++) {
          let sum = 0;
          for (let di = -radius; di <= radius; di++) {
            sum += data[(row + ((i + di + n) % n)) * 2];
          }
          tmp[row + i] = sum * inv;
        }
      }
      for (let i = 0; i < n; i++) {
        for (let j = 0; j < n; j++) {
          let sum = 0;
          for (let dj = -radius; dj <= radius; dj++) {
            sum += tmp[((j + dj + n) % n) * n + i];
          }
          data[(j * n + i) * 2] = sum * inv;
        }
      }
    }
  }

  _steps(count) {
    const gl = this.gl;
    gl.useProgram(this.stepProg);
    gl.viewport(0, 0, this.n, this.n);
    gl.bindBuffer(gl.ARRAY_BUFFER, this.quad);
    const loc = gl.getAttribLocation(this.stepProg, 'aPos');
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    gl.uniform1f(gl.getUniformLocation(this.stepProg, 'uDt'), this.dt);
    gl.uniform1f(gl.getUniformLocation(this.stepProg, 'uInvDx2'), 1 / (this.dx * this.dx));
    gl.uniform1f(gl.getUniformLocation(this.stepProg, 'uEta'), this.eta);
    gl.bindFramebuffer(gl.FRAMEBUFFER, this.fbo);
    for (let s = 0; s < count; s++) {
      const dst = 1 - this.src;
      gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0,
        gl.TEXTURE_2D, this.tex[dst], 0);
      gl.activeTexture(gl.TEXTURE0);
      gl.bindTexture(gl.TEXTURE_2D, this.tex[this.src]);
      gl.uniform1i(gl.getUniformLocation(this.stepProg, 'uState'), 0);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
      this.src = dst;
      this.t += this.dt;
    }
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
  }

  _energy() {
    // CPU readback (velocity is staggered by dt/2; the O(dt) offset is far
    // below the badge threshold). Total energy in natural units * dx^2.
    // The same readback buffer is reused for domain statistics (_domainStats)
    // to avoid a second GPU->CPU round trip.
    const gl = this.gl, n = this.n;
    gl.bindFramebuffer(gl.FRAMEBUFFER, this.fbo);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0,
      gl.TEXTURE_2D, this.tex[this.src], 0);
    const buf = new Float32Array(n * n * 4);
    gl.readPixels(0, 0, n, n, gl.RGBA, gl.FLOAT, buf);
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    const idx = (i, j) => ((((j + n) % n) * n + ((i + n) % n)) * 4);
    let E = 0;
    const inv2dx = 1 / (2 * this.dx);
    for (let j = 0; j < n; j++) {
      for (let i = 0; i < n; i++) {
        const p = buf[idx(i, j)], v = buf[idx(i, j) + 1];
        const px = (buf[idx(i + 1, j)] - buf[idx(i - 1, j)]) * inv2dx;
        const py = (buf[idx(i, j + 1)] - buf[idx(i, j - 1)]) * inv2dx;
        const V = ((1 - Math.cos(7 * p)) + this.eta * (1 - Math.cos(14 * p))) / 49;
        E += 0.5 * v * v + 0.5 * (px * px + py * py) + V;
      }
    }
    this.stats = this._domainStats(buf, idx);
    this._recordHistory();
    return E * this.dx * this.dx;
  }

  // Domain count, largest-domain area fraction, largest-non-background
  // fraction, and wall-cell fraction, via a flood fill on a downsampled
  // (every 4th cell) periodic grid classified by vacuum index. Cheap:
  // 128x128 = 16384 cells, run only every 120 frames (same cadence as the
  // energy readback, on the buffer it already fetched).
  //
  // "Background" is not identified by vacuum index (a preset's surrounding
  // vacuum is not fixed a priori) but structurally: it is simply the single
  // largest connected component. For a single isolated bubble this is
  // exactly right (the bubble is the only other component, so "largest
  // non-background" is unambiguously the bubble itself, and it SHRINKS as
  // the background grows). For multi-bubble presets it is the largest of
  // the remaining bubbles, which can jump between individual bubbles as
  // they evolve at different rates -- see the isolated-domain measurement
  // panel's note on why a single isolated bubble is the clean test case.
  _domainStats(buf, idx) {
    const n = this.n, step = 4, m = n / step;
    const k = new Int8Array(m * m);
    for (let jj = 0; jj < m; jj++) {
      for (let ii = 0; ii < m; ii++) {
        const p = buf[idx(ii * step, jj * step)];
        let kk = Math.round((7 * p) / (2 * Math.PI)) % 7;
        if (kk < 0) kk += 7;
        k[jj * m + ii] = kk;
      }
    }
    const seen = new Uint8Array(m * m);
    const stack = new Int32Array(m * m);
    const sizes = [];
    let domainCount = 0, wallCells = 0;
    for (let s = 0; s < m * m; s++) {
      const si = s % m, sj = (s - si) / m;
      const kN = k[((sj + 1) % m) * m + si], kS = k[((sj - 1 + m) % m) * m + si];
      const kE = k[sj * m + ((si + 1) % m)], kW = k[sj * m + ((si - 1 + m) % m)];
      if (kN !== k[s] || kS !== k[s] || kE !== k[s] || kW !== k[s]) wallCells++;
      if (seen[s]) continue;
      let top = 0, size = 0;
      stack[top++] = s; seen[s] = 1;
      const kv = k[s];
      while (top > 0) {
        const cur = stack[--top];
        size++;
        const ci = cur % m, cj = (cur - ci) / m;
        const nb = [
          cj * m + ((ci + 1) % m), cj * m + ((ci - 1 + m) % m),
          ((cj + 1) % m) * m + ci, ((cj - 1 + m) % m) * m + ci,
        ];
        for (const nn of nb) {
          if (!seen[nn] && k[nn] === kv) { seen[nn] = 1; stack[top++] = nn; }
        }
      }
      domainCount++;
      sizes.push(size);
    }
    sizes.sort((a, b) => b - a);
    const largest = sizes[0] || 0;
    const secondLargest = sizes[1] || 0;
    return {
      domainCount,
      largestFraction: largest / (m * m),
      largestNonBackgroundFraction: secondLargest / (m * m),
      wallFraction: wallCells / (m * m),
    };
  }

  // Append the current largest-non-background fraction to the history
  // buffer used by the isolated-domain decay measurement panel.
  _recordHistory() {
    if (!this.stats) return;
    this.history.push([this.t, this.stats.largestNonBackgroundFraction]);
    if (this.history.length > this.historyCap) this.history.shift();
  }

  // Clear the measurement history and start timing fresh from now, without
  // touching the field itself. Lets the user seed a configuration once and
  // then re-time a clean observation window as many times as they like.
  resetMeasurement() {
    this.history = [];
  }

  tick(now) {
    const dtWall = Math.min(0.1, (now - this.lastTime) / 1000);
    this.lastTime = now;
    if (this.running) {
      const steps = Math.min(this.maxStepsPerFrame,
        Math.round((this.speed * dtWall) / this.dt));
      if (steps > 0) this._steps(steps);
    }
    this.frame++;
    if (this.frame % 120 === 1) {
      const E = this._energy();
      if (this.E0 === null) this.E0 = E;
      this.energyMeV = E * M_PHI_MEV;
      this.energyDrift = Math.abs(E - this.E0) / this.E0;
    }
    this._draw();
    this._updateReadouts();
  }

  _draw() {
    const gl = this.gl, c = this.canvas;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const r = c.getBoundingClientRect();
    const w = Math.round(r.width * dpr), h = Math.round(r.height * dpr);
    if (c.width !== w || c.height !== h) { c.width = w; c.height = h; }
    gl.viewport(0, 0, w, h);
    gl.useProgram(this.drawProg);
    gl.bindBuffer(gl.ARRAY_BUFFER, this.quad);
    const loc = gl.getAttribLocation(this.drawProg, 'aPos');
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, this.tex[this.src]);
    gl.uniform1i(gl.getUniformLocation(this.drawProg, 'uState'), 0);
    const pal = new Float32Array(21);
    for (let k = 0; k < 7; k++) {
      pal[k * 3] = VACUUM_COLORS[k][0] / 255;
      pal[k * 3 + 1] = VACUUM_COLORS[k][1] / 255;
      pal[k * 3 + 2] = VACUUM_COLORS[k][2] / 255;
    }
    gl.uniform3fv(gl.getUniformLocation(this.drawProg, 'uPalette'), pal);
    gl.uniform2f(gl.getUniformLocation(this.drawProg, 'uCenter'),
      this.center[0], this.center[1]);
    gl.uniform1f(gl.getUniformLocation(this.drawProg, 'uZoom'), this.zoom);
    gl.uniform2f(gl.getUniformLocation(this.drawProg, 'uRes'), w, h);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
  }

  _updateReadouts() {
    const r = this.readouts;
    const TIME_UNIT = 197.3269804 / M_PHI_MEV;
    r.time.textContent = (this.t * TIME_UNIT).toFixed(2) + ' fm/c';
    r.energy.textContent = this.energyMeV !== undefined
      ? this.energyMeV.toFixed(0) + ' MeV·(m dz)' : '—';
    r.drift.textContent = this.E0 !== null ? this.energyDrift.toExponential(1) : '—';
    r.drift.className = this.energyDrift < 1e-3 ? 'ok' : 'warn';
    r.kinks.textContent = '— (walls)';
    r.winding.textContent = '0 (periodic)';
  }
}
