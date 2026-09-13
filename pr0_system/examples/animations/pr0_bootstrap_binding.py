"""
PR-0: Bootstrap to Binding via Multi-Scale Fitness

Revolutionary approach:
- Track MULTIPLE metrics over MULTIPLE timescales
- Reward sustained localization + proximity
- Penalize dissolution OR spreading
- Learn optimal damping through reinforcement

AUTHOR: Nova Spivack
DATE: October 31, 2025
"""

import numpy as np
from scipy.ndimage import distance_transform_edt
from collections import deque


class BootstrapPR0:
    """
    Self-organizing PR-0 with multi-scale reinforcement learning.
    
    Tracks:
    - Localization (are structures staying compact?)
    - Proximity (are they getting closer?)
    - Persistence (are structures surviving?)
    - Stability (is max density reasonable?)
    
    Adapts γ_base, γ_scale to maximize binding fitness.
    """
    
    def __init__(self, L_x, L_y):
        self.L_x = L_x
        self.L_y = L_y
        
        # Fields
        self.psi = np.zeros((L_y, L_x), dtype=np.complex128)
        self.chi = np.zeros((L_y, L_x), dtype=np.float64)
        self.chi_dot = np.zeros((L_y, L_x), dtype=np.float64)
        
        # Damping parameters (START with Goldilocks values!)
        self.gamma_base = 0.01
        self.gamma_scale = 0.5
        
        # Mediator strength
        self.g = 0.2
        
        # History for multi-scale fitness
        self.sep_history = deque(maxlen=100)
        self.dens_history = deque(maxlen=100)
        self.n_loc_history = deque(maxlen=100)
        
        self.timestep = 0
        self.best_fitness = -np.inf
        self.best_gamma_base = self.gamma_base
        self.best_gamma_scale = self.gamma_scale
    
    def step(self, dt=0.01):
        """Evolution with meta-learning."""
        # Compute damping
        gamma = self._compute_damping()
        
        # Evolve
        self._evolve(dt, gamma)
        
        # Track metrics
        self._track_metrics()
        
        # Every 200 steps, adapt
        if self.timestep % 200 == 0 and self.timestep > 0:
            self._meta_learn()
        
        self.timestep += 1
    
    def _compute_damping(self):
        """Separation-aware damping."""
        psi_real = np.real(self.psi)
        pos = (psi_real > 0.5).astype(np.float64)
        neg = (psi_real < -0.5).astype(np.float64)
        
        if np.sum(pos) > 5 and np.sum(neg) > 5:
            dist_from_pos = distance_transform_edt(1 - pos)
            dist_from_neg = distance_transform_edt(1 - neg)
            
            sep_map = np.where(psi_real > 0, dist_from_neg, dist_from_pos)
            
            # Adaptive: strong when close, weak when far
            gamma = np.where(sep_map < 10,
                            self.gamma_scale / (sep_map**2 + 0.5),
                            self.gamma_base * (15.0 / (sep_map + 1.0)))
            
            gamma = np.clip(gamma, self.gamma_base, 0.8)
        else:
            gamma = np.ones((self.L_y, self.L_x)) * self.gamma_base
        
        return gamma
    
    def _evolve(self, dt, gamma):
        """Field evolution."""
        # ψ evolution
        lap = (np.roll(self.psi, 1, axis=0) + np.roll(self.psi, -1, axis=0) +
               np.roll(self.psi, 1, axis=1) + np.roll(self.psi, -1, axis=1) - 4 * self.psi)
        
        psi_mag = np.abs(self.psi)
        psi_safe = np.where(psi_mag > 10, 10 * self.psi / (psi_mag + 1e-10), self.psi)
        nonlin = np.abs(psi_safe)**2 * psi_safe
        
        chi_safe = np.clip(self.chi, -20, 20)
        med_force = -self.g * chi_safe * psi_safe
        
        rhs = 1j * (lap + nonlin) + med_force - gamma * psi_safe
        self.psi += dt * rhs
        
        # Clip
        psi_mag = np.abs(self.psi)
        self.psi = np.where(psi_mag > 20, 20 * self.psi / (psi_mag + 1e-10), self.psi)
        
        # χ evolution
        lap_chi = (np.roll(self.chi, 1, axis=0) + np.roll(self.chi, -1, axis=0) +
                   np.roll(self.chi, 1, axis=1) + np.roll(self.chi, -1, axis=1) - 4 * self.chi)
        
        self.chi_dot += dt * (lap_chi + np.abs(self.psi)**2 - self.chi * 0.01)
        self.chi_dot *= (1.0 - gamma * dt)
        self.chi += dt * self.chi_dot
    
    def _track_metrics(self):
        """Track metrics for fitness."""
        dens = np.abs(self.psi)**2
        n_loc = np.sum(dens > 0.5)
        max_dens = np.max(dens)
        
        # Find separation
        flat = dens.flatten()
        indices = np.argsort(flat)[::-1][:2]
        
        if flat[indices[1]] > 1.0:
            y1, x1 = indices[0] // self.L_x, indices[0] % self.L_x
            y2, x2 = indices[1] // self.L_x, indices[1] % self.L_x
            
            dx, dy = x2 - x1, y2 - y1
            if abs(dx) > self.L_x // 2: dx = dx - np.sign(dx) * self.L_x
            if abs(dy) > self.L_y // 2: dy = dy - np.sign(dy) * self.L_y
            
            sep = np.sqrt(dx**2 + dy**2)
        else:
            sep = 0.0  # Merged or dissolved
        
        self.sep_history.append(sep)
        self.dens_history.append(max_dens)
        self.n_loc_history.append(n_loc)
    
    def _compute_fitness(self):
        """
        Multi-scale fitness for binding.
        
        GOOD:
        - Structures persist (max_dens > 50 consistently)
        - Structures localized (n_loc < 500)
        - Separation decreasing or small (sep < 10)
        
        BAD:
        - Dissolution (max_dens → 0)
        - Spreading (n_loc → 4096)
        - Structures far (sep > 30)
        """
        if len(self.sep_history) < 20:
            return 0.0
        
        seps = np.array(list(self.sep_history))
        dens = np.array(list(self.dens_history))
        locs = np.array(list(self.n_loc_history))
        
        # Persistence: structures exist
        persistence = np.mean(dens > 50)
        
        # Localization: not spreading
        localization = 1.0 / (1.0 + np.mean(locs) / 500.0)
        
        # Proximity: getting close
        recent_sep = np.mean(seps[-10:])
        proximity = 1.0 / (1.0 + recent_sep / 10.0)
        
        # Trend: separation decreasing?
        if len(seps) >= 40:
            trend_early = np.mean(seps[-40:-20])
            trend_late = np.mean(seps[-20:])
            trend = max(0, trend_early - trend_late) / 10.0  # Reward decrease
        else:
            trend = 0.0
        
        # Total fitness
        fitness = persistence * 0.3 + localization * 0.3 + proximity * 0.3 + trend * 0.1
        
        return fitness
    
    def _meta_learn(self):
        """
        Meta-learning: Adjust damping based on fitness.
        
        Strategy:
        - Compute fitness
        - If better than best → save params
        - If worse → try small random perturbation (explore)
        - If much worse → revert to best (exploit)
        """
        fitness = self._compute_fitness()
        
        print(f"    Step {self.timestep:5d}: fitness={fitness:.4f}, γ_b={self.gamma_base:.4f}, γ_s={self.gamma_scale:.4f}, sep={np.mean(list(self.sep_history)[-10:]):.1f}")
        
        # Update best
        if fitness > self.best_fitness:
            self.best_fitness = fitness
            self.best_gamma_base = self.gamma_base
            self.best_gamma_scale = self.gamma_scale
            print(f"      ✅ NEW BEST: fitness={fitness:.4f}")
        
        # SIMULATED ANNEALING: exploration decreases over time
        progress = self.timestep / 40000.0
        temperature = max(0.05, 1.0 - progress)  # 1.0 → 0.05
        
        # Adaptation strategy with temperature-scaled exploration
        if fitness > 0.6:  # Good! Small exploration
            scale = 1.0 + temperature * 0.1  # ±10% early, ±0.5% late
            self.gamma_base *= np.random.uniform(1.0/scale, scale)
            self.gamma_scale *= np.random.uniform(1.0/scale, scale)
        elif fitness > 0.3:  # OK, explore more
            scale = 1.0 + temperature * 0.3  # ±30% early, ±1.5% late
            self.gamma_base *= np.random.uniform(1.0/scale, scale)
            self.gamma_scale *= np.random.uniform(1.0/scale, scale)
        else:  # Bad, revert to best + explore
            scale = 1.0 + temperature * 0.2
            self.gamma_base = self.best_gamma_base * np.random.uniform(1.0/scale, scale)
            self.gamma_scale = self.best_gamma_scale * np.random.uniform(1.0/scale, scale)
        
        # Bounds
        self.gamma_base = np.clip(self.gamma_base, 0.001, 0.1)
        self.gamma_scale = np.clip(self.gamma_scale, 0.1, 2.0)
    
    def set_soliton(self, x0, y0, amplitude, width, velocity_x=0, sign=+1):
        """Initialize soliton."""
        for y in range(self.L_y):
            for x in range(self.L_x):
                dx = x - x0
                r = np.abs(dx)
                
                val = amplitude / np.cosh(r / width)
                phase = velocity_x * dx + (np.pi if sign < 0 else 0)
                
                self.psi[y, x] += val * np.exp(1j * phase)
    
    def density(self):
        return np.abs(self.psi)**2


if __name__ == "__main__":
    print("="*70)
    print("🎯 BOOTSTRAP TO BINDING")
    print("="*70)
    print()
    
    pr0 = BootstrapPR0(L_x=64, L_y=64)
    
    pr0.set_soliton(x0=24, y0=32, amplitude=3.0, width=3.0, velocity_x=0.1, sign=+1)
    pr0.set_soliton(x0=40, y0=32, amplitude=3.0, width=3.0, velocity_x=-0.1, sign=-1)
    
    print("Running 40,000 steps with simulated annealing...")
    print()
    
    for t in range(40000):
        pr0.step(dt=0.01)
    
    print()
    print("="*70)
    print("FINAL RESULTS:")
    print(f"  Best fitness: {pr0.best_fitness:.4f}")
    print(f"  Best γ_base: {pr0.best_gamma_base:.4f}")
    print(f"  Best γ_scale: {pr0.best_gamma_scale:.4f}")
    print("="*70)

