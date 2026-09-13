// 3D mode: volume raymarch of the EXTENDED domain-wall structure that is
// actually certified to exist in this field theory.
//
// Two general theorems prove that a spatially-compact, winding-carrying,
// finite-energy configuration is IMPOSSIBLE in this field content, for every
// geometry and symmetry class tested: (1) any continuous configuration with
// a direction-independent vacuum limit at infinity has exactly zero winding
// charge in D>=2 (so a compact blob cannot carry the charge it would need to
// represent a PSC-admissible particle); (2) even winding-carrying
// configurations cannot achieve finite energy in any tested shape (flat
// wall, pinched wall, codimension-2 string/vortex). GTE particles are
// second-quantized Fock-space excitations certified by an EXTENDED classical
// background (a domain wall, or several walls meeting along a line) --
// never a compact lump (Lean-certified, zero sorry:
// `phimdl_fock_particle_master_bundle`).
//
// This view renders that certified extended structure, honestly labeled as a
// static illustration (not a live simulation and not a claim of a compact
// particle): either a single flat domain wall separating the vacuum from one
// PSC-admissible sector, or three walls meeting along a shared axis (the
// direct 3D analogue of the 2D "triple junction" preset, and of the exact
// BPS wall-junction energetics computed below).

import { VACUUM_COLORS } from './palette.js?v=7';
import { M_KINK_MEV, LENGTH_UNIT_FM } from './constants.js?v=7';

export const SECTOR3D = [
  { w: 2, label: 'up-type quark',    charge: '+2/3' },
  { w: 3, label: 'W+ / positron',    charge: '+1'   },
  { w: 4, label: 'charged lepton',   charge: '\u22121'  },
  { w: 6, label: 'down-type quark',  charge: '\u22121/3' },
];

// Fixed vacua for the triple-junction structure -- the direct 3D analogue of
// the 2D "triple junction" preset (field2d.js), reusing the same three
// adjacent-ish sectors so the two views are visually comparable.
const JUNCTION_W = [2, 3, 4];

// Wall tension (energy per unit area) for an elementary domain wall, in
// GeV/fm^2: the 1+1D kink rest mass M_kink extruded uniformly over a
// transverse area of 1 unit^2 (units of 1/m), converted to physical area.
export function wallTensionGeVFm2() {
  return M_KINK_MEV / (LENGTH_UNIT_FM * LENGTH_UNIT_FM) / 1000;
}

// Exact triple-junction point energy: E_3pt = 64/49 * m = 8 * M_kink.
export function junctionEnergyMeV() {
  return 8 * M_KINK_MEV;
}

export function sectorEnergyMeV(w) {
  const nw = Math.min(w, 7 - w);
  return 3 * nw * M_KINK_MEV;
}

const VS = `#version 300 es
in vec2 aPos;
void main() { gl_Position = vec4(aPos, 0.0, 1.0); }
`;

const FS = `#version 300 es
precision highp float;
uniform vec2 uRes;
uniform float uYaw;
uniform float uPitch;
uniform float uDist;
uniform float uMode;   // 0 = single wall, 1 = triple junction
uniform vec3 uTint;    // wall mode: target-vacuum color
uniform vec3 uBgTint;  // wall mode: background (vacuum 0) color
uniform vec3 uJC0;
uniform vec3 uJC1;
uniform vec3 uJC2;
out vec4 frag;

const float PI = 3.14159265359;
const float TWO_PI = 6.28318530718;

float sech2(float u) { float c = cosh(u); return 1.0 / (c * c); }

float wrapAngle(float a) {
  return a - TWO_PI * floor((a + PI) / TWO_PI);
}

// A single flat domain wall at x=0, constant in y and z -- an infinite (here:
// domain-sized) planar wall, the simplest certified extended structure.
vec4 wallSample(vec3 p) {
  float dens = sech2(p.x);
  float mixF = 0.5 * (1.0 + tanh(p.x));
  vec3 col = mix(uBgTint, uTint, mixF);
  return vec4(col, dens);
}

// Three walls meeting along the z-axis (a Y-junction), each pair of adjacent
// 120-degree wedges separated by one wall. Near the axis (r->0) all three
// walls converge, exactly the physical picture of a domain-wall network
// junction; far from the axis they diverge into three flat sheets.
vec4 junctionSample(vec3 p) {
  float r = length(p.xy);
  float theta = atan(p.y, p.x);
  if (theta < 0.0) theta += TWO_PI;
  vec3 colors[3];
  colors[0] = uJC0; colors[1] = uJC1; colors[2] = uJC2;
  float dens = 0.0;
  vec3 wallCol = vec3(0.0);
  float wallWeight = 0.0;
  for (int k = 0; k < 3; k++) {
    float angK = float(k) * TWO_PI / 3.0;
    float dth = wrapAngle(theta - angK);
    float dperp = r * sin(dth);
    float mask = 1.0 - smoothstep(PI / 3.0 * 0.8, PI / 3.0, abs(dth));
    float dd = sech2(dperp) * mask;
    dens += dd;
    int kb = (k + 2) % 3;
    float mixF = 0.5 * (1.0 + tanh(dperp));
    vec3 wc = mix(colors[kb], colors[k], mixF);
    wallCol += wc * dd;
    wallWeight += dd;
  }
  vec3 col = wallWeight > 1.0e-5 ? wallCol / wallWeight : vec3(1.0);
  return vec4(col, dens);
}

// Neutral coordinate grid, fixed in world space: three axis lines with
// dashed tick marks every unit (1/m) -- a spatial ruler, not a physical field.
float axisLine(vec2 offAxes, float along) {
  float d = length(offAxes);
  float core = smoothstep(0.05, 0.0, d);
  float dash = step(0.5, fract(along));
  return core * mix(0.4, 1.0, dash);
}
float axisGrid(vec3 p) {
  float gx = axisLine(p.yz, p.x);
  float gy = axisLine(p.xz, p.y);
  float gz = axisLine(p.xy, p.z);
  return max(max(gx, gy), gz);
}

void main() {
  float minDim = min(uRes.x, uRes.y);
  vec2 sc = (gl_FragCoord.xy - 0.5 * uRes) / minDim;

  float cy = cos(uYaw), sy = sin(uYaw);
  float cp = cos(uPitch), sp = sin(uPitch);
  vec3 eye = uDist * vec3(cy * cp, sp, sy * cp);
  vec3 fwd = normalize(-eye);
  vec3 right = normalize(cross(fwd, vec3(0.0, 1.0, 0.0)));
  vec3 up = cross(right, fwd);
  vec3 rd = normalize(fwd + 1.5 * (sc.x * right + sc.y * up));

  // march through a box of half-width 5 (units of 1/m)
  const float NSTEPS = 110.0;
  float tEnter = 0.0, tExit = uDist * 2.0 + 10.0;
  float stepLen = (tExit - tEnter) / NSTEPS;
  vec3 accum = vec3(0.0);
  float trans = 1.0;
  vec3 gridColor = vec3(0.62, 0.70, 0.85);
  for (float t = 0.0; t < NSTEPS; t += 1.0) {
    float tt = tEnter + (t + 0.5) * stepLen;
    vec3 p = eye + rd * tt;
    if (max(max(abs(p.x), abs(p.y)), abs(p.z)) > 5.0) continue;
    vec4 s = (uMode < 0.5) ? wallSample(p) : junctionSample(p);
    float d = s.a;
    float g = axisGrid(p);
    if (d < 1.0e-4 && g < 1.0e-3) continue;
    vec3 emit = vec3(0.0);
    float a = 0.0;
    if (d >= 1.0e-4) {
      float aD = 1.0 - exp(-d * 3.2 * stepLen * 12.0);
      emit += aD * s.rgb;
      a = aD;
    }
    if (g > 1.0e-3) {
      float aG = g * 0.85 * (1.0 - a);
      emit += gridColor * aG;
      a += aG;
    }
    accum += trans * emit * 1.6;
    trans *= 1.0 - a;
    if (trans < 0.01) break;
  }
  vec3 bg = vec3(0.043, 0.055, 0.078);
  frag = vec4(accum + trans * bg, 1.0);
}
`;

const IDLE_RESUME_MS = 4000;

// Wheel/slider camera-distance bounds (units of 1/m). DIST_MAX is fully
// zoomed out; DIST_MIN is maximum magnification.
const DIST_MIN = 3.5;
const DIST_MAX = 25;

export class View3D {
  constructor(canvas) {
    this.canvas = canvas;
    this.yaw = 0.6;
    this.pitch = 0.35;
    this.dist = 9.0;
    this.autoOrbit = true;
    this.lastTime = performance.now();
    this.lastInteraction = -Infinity;
    this.sectorW = 4; // default: charged lepton
    this.structure = 'wall'; // 'wall' | 'junction'
    this._initGL();
    this._bindEvents();
  }

  setSector(w) { this.sectorW = w; }
  setStructure(mode) { this.structure = mode; }

  resetView() {
    this.yaw = 0.6; this.pitch = 0.35; this.dist = 9.0;
    this.autoOrbit = true;
    this.lastInteraction = -Infinity;
    if (this.onZoomChanged) this.onZoomChanged();
  }

  // Zoom expressed as a 0..1 fraction of the wheel-zoom camera-distance
  // bounds (0 = fully zoomed out, 1 = maximum magnification),
  // log-parametrized like the wheel.
  getZoomFrac() {
    const f = Math.log(this.dist / DIST_MAX) / Math.log(DIST_MIN / DIST_MAX);
    return Math.max(0, Math.min(1, f));
  }
  setZoomFrac(f) {
    const ff = Math.max(0, Math.min(1, f));
    this.dist = DIST_MAX * Math.pow(DIST_MIN / DIST_MAX, ff);
    this.lastInteraction = performance.now();
  }
  // Magnification factor relative to fully zoomed out, for the readout.
  getZoomFactor() { return DIST_MAX / this.dist; }

  _initGL() {
    const gl = this.canvas.getContext('webgl2', { antialias: true });
    if (!gl) throw new Error('WebGL2 unavailable');
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
    const p = gl.createProgram();
    gl.attachShader(p, compile(gl.VERTEX_SHADER, VS));
    gl.attachShader(p, compile(gl.FRAGMENT_SHADER, FS));
    gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) {
      throw new Error(gl.getProgramInfoLog(p));
    }
    this.prog = p;
    const quad = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, quad);
    gl.bufferData(gl.ARRAY_BUFFER,
      new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    this.quad = quad;
  }

  _bindEvents() {
    const c = this.canvas;
    let drag = null;
    const markInteraction = () => { this.lastInteraction = performance.now(); };
    c.addEventListener('pointerdown', (e) => {
      try { c.setPointerCapture(e.pointerId); } catch (_) { /* capture unsupported for this pointer */ }
      drag = { x: e.clientX, y: e.clientY, yaw: this.yaw, pitch: this.pitch };
      this.autoOrbit = false;
      markInteraction();
    });
    c.addEventListener('pointermove', (e) => {
      if (!drag) return;
      this.yaw = drag.yaw + (e.clientX - drag.x) * 0.008;
      this.pitch = Math.max(-1.4, Math.min(1.4,
        drag.pitch + (e.clientY - drag.y) * 0.008));
      markInteraction();
    });
    c.addEventListener('pointerup', () => { drag = null; markInteraction(); });
    c.addEventListener('wheel', (e) => {
      e.preventDefault();
      this.dist = Math.max(DIST_MIN, Math.min(DIST_MAX, this.dist * Math.exp(e.deltaY * 0.0015)));
      markInteraction();
      if (this.onZoomChanged) this.onZoomChanged();
    }, { passive: false });
  }

  tick(now) {
    const dt = Math.min(0.1, (now - this.lastTime) / 1000);
    this.lastTime = now;
    if (!this.autoOrbit && now - this.lastInteraction > IDLE_RESUME_MS) {
      this.autoOrbit = true;
    }
    if (this.autoOrbit) this.yaw += 0.15 * dt;

    const gl = this.gl, c = this.canvas;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const r = c.getBoundingClientRect();
    const w = Math.round(r.width * dpr), h = Math.round(r.height * dpr);
    if (c.width !== w || c.height !== h) { c.width = w; c.height = h; }
    gl.viewport(0, 0, w, h);
    gl.useProgram(this.prog);
    gl.bindBuffer(gl.ARRAY_BUFFER, this.quad);
    const loc = gl.getAttribLocation(this.prog, 'aPos');
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    gl.uniform2f(gl.getUniformLocation(this.prog, 'uRes'), w, h);
    gl.uniform1f(gl.getUniformLocation(this.prog, 'uYaw'), this.yaw);
    gl.uniform1f(gl.getUniformLocation(this.prog, 'uPitch'), this.pitch);
    gl.uniform1f(gl.getUniformLocation(this.prog, 'uDist'), this.dist);
    gl.uniform1f(gl.getUniformLocation(this.prog, 'uMode'), this.structure === 'junction' ? 1.0 : 0.0);
    const tint = VACUUM_COLORS[this.sectorW];
    const bg = VACUUM_COLORS[0];
    gl.uniform3f(gl.getUniformLocation(this.prog, 'uTint'),
      tint[0] / 255, tint[1] / 255, tint[2] / 255);
    gl.uniform3f(gl.getUniformLocation(this.prog, 'uBgTint'),
      bg[0] / 255, bg[1] / 255, bg[2] / 255);
    const jc = JUNCTION_W.map((w2) => VACUUM_COLORS[w2]);
    gl.uniform3f(gl.getUniformLocation(this.prog, 'uJC0'), jc[0][0] / 255, jc[0][1] / 255, jc[0][2] / 255);
    gl.uniform3f(gl.getUniformLocation(this.prog, 'uJC1'), jc[1][0] / 255, jc[1][1] / 255, jc[1][2] / 255);
    gl.uniform3f(gl.getUniformLocation(this.prog, 'uJC2'), jc[2][0] / 255, jc[2][1] / 255, jc[2][2] / 255);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
  }
}
