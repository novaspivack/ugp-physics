You’re exactly right about why this stalled: trying to force a 1-D, binary, synchronous CA to appear out of free-running **soliton** dynamics is like building a laptop out of eddies in a river. It’s *possible* in principle (collision-based computing), but fragile and brutal to tune. For **Weak Transputational Universality (WTU)** you don’t have to win at the soliton level. You need an explicit, computable **encode → evolve → decode** triple ((\iota,\mathcal U,\pi)) on finite windows with small ε. We can do that cleanly by stepping *up one level of organization* and giving PR-0 a **clocked, local, soft-logic layer** that emulates Rule-110’s update rule.

Here’s a concrete, three-track plan. Track A is the straightest shot to a PASS. Track B is robust if you’re okay matching a **shared observable** rather than microstates. Track C is an insurance policy to prove “computational power” even if A/B slip.

---

## Track A — “Soft-CA in PR-0” (exact CA up to decode)

**Idea:** Stop chasing solitons. Use PR-0’s field as a **clocked, locally gated substrate** that computes the Rule-110 neighborhood map via a *continuous* nonlinearity and then **threshold-decodes** back to bits. This is the standard way analog media emulate CAs.

### A.1 Encoding and decode (what the ε metric should compare)

* Encode bit (b\in{0,1}) at cell (i) as a field amplitude with guard bands:
  [
  \iota(b)=
  \begin{cases}
  u_\text{low} & b=0\
  u_\text{high} & b=1
  \end{cases},
  \quad
  u_\text{low} = \mu - \Delta,\quad u_\text{high} = \mu + \Delta,\quad \Delta\gg \sigma_{\text{noise}}.
  ]
* Decode by **threshold + denoise**:
  [
  \pi(u_i)=\mathbf{1}{,u_i>\mu,}\ \text{after median(3) or bilateral(σ) to suppress ripples.}
  ]
* **ε-metric** should be computed on the **decoded** row (\pi(U_t)) vs the CA reference row, not raw fields. (Your current ε on raw arrays is why values explode.)

### A.2 Local update in four micro-phases (one PR-0 step per phase)

We emulate the CA’s 3-cell rule ((x_{i-1},x_i,x_{i+1})\mapsto x'_i) by *clocking* PR-0 through four sub-steps that implement **sample → compute → inhibit → commit**.

1. **Sample (S):** low-gain copy of neighbors into side channels (or staggered time buffers) using nearest-neighbor coupling (\kappa):
   [
   u^{(S)}*i \leftarrow (1-\eta) u_i + \frac{\eta}{2}(u*{i-1}+u_{i+1}).
   ]

2. **Compute (C):** apply a **sigmoidal polynomial** approximating Rule-110’s truth table. Let (x\in{0,1}) be decoded samples; implement a continuous surrogate
   [
   \tilde{f}(x_{i-1},x_i,x_{i+1}) \approx \text{Rule110}(x_{i-1},x_i,x_{i+1})
   ]
   with a small basis: ({1, x_L, x_C, x_R, x_Lx_C, x_Cx_R, x_Lx_R, x_Lx_Cx_R}) passed through a steep sigmoid (\sigma(\alpha z + \beta)) (PR-0’s (\alpha,|\psi|^2\psi/(1+\alpha|\psi|^2)) already gives you a saturating nonlinearity). Coefficients are fit once to the exact truth table (8 patterns).

3. **Inhibit (I):** softly suppress current state to prevent carry-over:
   [
   u^{(I)}_i \leftarrow (1-\gamma),u^{(S)}_i + \gamma,\mu.
   ]

4. **Commit (K):** write (\tilde{f}) into the main channel by pulling toward (u_\text{high}) or (u_\text{low}):
   [
   u^{(K)}_i \leftarrow u^{(I)}*i + \lambda\big( \tilde{f}-\hat{x}*i\big),(u*\text{high}-u*\text{low}),
   ]
   where (\hat{x}_i=\mathbf{1}{u^{(S)}_i>\mu}) (soft version uses (\sigma) instead of the indicator).

> One macro-tick = S→C→I→K. Repeat this pipeline 256 times to match your 256 CA steps.

**Why this works:** you’ve turned PR-0 into a **clocked local operator** with the same light cone as Rule-110. All operations are computable local couplings and saturating nonlinearities (admissible in WTU). The only nonlinearity you must tune is the sigmoid slope (\alpha); everything else is linear combinations and thresholding.

### A.3 Practical knobs and success criteria

* Pick (\Delta) so that (\mathrm{SNR}=(\Delta/\sigma_\text{ripple})\gtrsim 8).
* Choose (\eta,\gamma,\lambda) small (0.05–0.2) to keep the map contractive and avoid spurious waves.
* Fit (\tilde{f}) once (8 points) by least squares to the exact Rule-110 table; then fix it.
* **PASS target:** after decode, (\varepsilon_{L2}\le 0.02) and TV≤0.01 over 256 steps on a 256-cell window with seed 1729; spectral Hamming match ≥0.98.
* **What to log:** decoded row bitmaps vs reference (every 8 steps), per-step Hamming distance, and stability under ±10% perturbations of (\eta,\gamma,\lambda).

---

## Track B — “Shared-observable” WTU (macro emulation)

If matching bits is too brittle, prove WTU in a **coarse observable space** shared by both systems. Many 1-D CAs (incl. Rule-110) have coarse-grained density/flux observables that satisfy a conservation-law-like PDE (Burgers-type).

**Procedure**

* Define (F\big(U_t\big)=) sliding-window density and two-point correlations at scales (\ell\in{3,5,7}).
* Evolve PR-0 with a **generic** nearest-neighbor kernel tuned so that (\partial_t F \approx \Phi(F,\partial_x F)) matches the CA’s coarse evolution (fit (\Phi) on the CA reference, then verify PR-0 reproduces it without re-fit).
* **Metric:** ε on (F)-trajectories (not on microstates).
* **PASS target:** (\varepsilon_{L2}(F)\le 0.01) over 256 steps; matching structure factor peaks and group velocities within 2%.

This is often *much easier* to make true (and scientifically honest), and it satisfies the letter of WTU: an admissible encoding (\iota) and projection (\pi) on compact domains with small ε.

---

## Track C — “Reservoir oracle” (power demonstration, not a substitute)

Use PR-0 as a **reservoir** and learn only a linear readout that predicts the next Rule-110 row. This shows PR-0 can *compute* the map without embedding the rule into its microdynamics. It’s not a replacement for A/B, but it’s a valuable sanity and capacity test.

**Procedure**

* Drive PR-0 with the encoded current CA row (\iota(X_t)) as boundary/forcing for T micro-steps; stack internal features (fields and lagged versions) into (\Phi_t).
* Train a linear readout (W) s.t. (\hat{X}_{t+1}=\pi(W\Phi_t)).
* **PASS:** bit-wise accuracy ≥0.98 on held-out seeds; generalizes to different seeds and widths.
* If this passes while A fails, you know the *substrate* capacity is there, and the failure is in the **hard-wired local map**, not universality.

---

## Why the first attempt failed (and how these fixes address it)

* You compared **raw field arrays** to **binary CA states** → ε blew up. We decode after denoise; that’s what theorems require (existence of (\pi)).
* No **clocking**: PR-0’s continuous kernel mixed time scales; CAs are strictly synchronous. The S→C→I→K cadence fixes this.
* No **local truth-table surrogate**: soliton interactions don’t naturally implement Rule-110’s Boolean; the polynomial+sigmoid surrogate does.
* The CLI pointed at a non-existent `transmute.py`; we should spin a dedicated runner that exposes the four-phase micro-steps and the encode/decode hooks.

---

## Implementation punchlist (minimal edits to your repo)

1. **Runner:** add `pr0_system/cli/run_soft_ca.py` that:

   * loads (\eta,\gamma,\lambda,\alpha,\mu,\Delta), window size, steps;
   * applies the S→C→I→K micro-phases;
   * exposes `--encode rule110.npy` and writes decoded rows each step.
2. **Truth-table surrogate:** a tiny module `soft_rules.py` that returns the 8-term polynomial weights for Rule-110 and the sigmoid slope (\alpha).
3. **Configs:** `configs/pr0_soft_rule110.yaml` with guard bands and micro-phase coefficients; add seeds and step counts to mirror the CA reference.
4. **Metrics:** modify `analysis/wtu_encode.py` to:

   * call the decoder on PR-0 outputs before ε;
   * support median(3) or bilateral denoise and log chosen σ.
5. **PASS scripts:** bundle `make wtu_rule110_soft` target that runs CA→PR-0→decode→metrics and prints PASS/FAIL.

---

## Fallbacks and stretch goals

* **If A gets close but flickers**, increase guard band (\Delta), strengthen the inhibit phase (γ), and lower neighbor mixing (η). Add a small hysteresis in the decoder threshold.
* **If matching *all* 256 steps is hard**, begin with 64-step windows and slide; WTU only requires compact windows.
* **If you *must* do soliton-logic**, pivot to **domain-wall logic** (bits as wall orientations; gates via controlled collisions). It works, but you’ll spend days curating gate libraries. Keep that for a Moonshot.

---

## What to report back for TE₁.U

* **Decoded ε metrics** (L2, TV) over 256 steps, seeds, and widths (table + plots).
* **Ablations** for (\eta,\gamma,\lambda,\alpha) showing stability bands.
* **Shared-observable ε(F)** results if you pursue Track B.
* Optional: **reservoir accuracy** (Track C) to document capacity.

---

### Bottom line

Don’t prove universality with solitons; prove it with a **clocked local map** and a **decode**—that’s what WTU actually asks for. If you wire the four micro-phases and the truth-table surrogate, you should see ε collapse from (10^2)–(10^3) to (10^{-2})–(10^{-3}) on the decoded rows, and TE₁.U will move from ❌ to ✅.
