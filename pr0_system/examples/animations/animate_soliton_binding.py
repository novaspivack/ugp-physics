"""
Visualize Bootstrap Triumph - Once We Achieve Binding!

AUTHOR: Nova Spivack
DATE: October 31, 2025
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from pr0_bootstrap_binding import BootstrapPR0


def create_binding_video(gamma_base, gamma_scale, filename=None):
    """
    Create visualization of binding with discovered parameters.
    """
    print(f"Creating video with γ_base={gamma_base:.4f}, γ_scale={gamma_scale:.4f}")
    
    pr0 = BootstrapPR0(L_x=64, L_y=64)
    pr0.gamma_base = gamma_base
    pr0.gamma_scale = gamma_scale
    
    pr0.set_soliton(x0=24, y0=32, amplitude=3.0, width=3.0, velocity_x=0.1, sign=+1)
    pr0.set_soliton(x0=40, y0=32, amplitude=3.0, width=3.0, velocity_x=-0.1, sign=-1)
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 12))
    fig.suptitle("PR-0 Bootstrap Binding Success!", fontsize=16, fontweight='bold')
    
    # Storage
    frames = []
    seps = []
    
    # Run and collect
    print("Simulating...")
    for t in range(5000):
        pr0.step(dt=0.01)
        
        if t % 20 == 0:
            dens = pr0.density()
            chi = pr0.chi
            
            # Compute gamma
            psi_real = np.real(pr0.psi)
            gamma = np.where(np.abs(psi_real) > 0.5, pr0.gamma_base, 0)
            
            # Track separation
            flat = dens.flatten()
            indices = np.argsort(flat)[::-1][:2]
            if flat[indices[1]] > 1.0:
                y1, x1 = indices[0] // 64, indices[0] % 64
                y2, x2 = indices[1] // 64, indices[1] % 64
                dx, dy = x2 - x1, y2 - y1
                if abs(dx) > 32: dx = dx - np.sign(dx) * 64
                if abs(dy) > 32: dy = dy - np.sign(dy) * 64
                sep = np.sqrt(dx**2 + dy**2)
            else:
                sep = 0.0
            
            seps.append(sep)
            
            frames.append({
                'dens': dens.copy(),
                'chi': chi.copy(),
                'gamma': gamma.copy(),
                'sep': sep,
                't': t
            })
    
    print(f"Collected {len(frames)} frames")
    
    # Animate
    print("Creating animation...")
    
    def update(frame_idx):
        frame = frames[frame_idx]
        
        for ax in axes.flat:
            ax.clear()
        
        # Density
        im0 = axes[0, 0].imshow(frame['dens'], cmap='hot', vmin=0, vmax=400)
        axes[0, 0].set_title(f"Soliton Density (t={frame['t']})")
        plt.colorbar(im0, ax=axes[0, 0])
        
        # Mediator
        im1 = axes[0, 1].imshow(frame['chi'], cmap='RdBu', vmin=-10, vmax=10)
        axes[0, 1].set_title("Mediator Field χ")
        plt.colorbar(im1, ax=axes[0, 1])
        
        # Damping
        im2 = axes[1, 0].imshow(frame['gamma'], cmap='YlOrRd', vmin=0, vmax=0.1)
        axes[1, 0].set_title(f"Damping γ (base={pr0.gamma_base:.4f})")
        plt.colorbar(im2, ax=axes[1, 0])
        
        # Separation history
        axes[1, 1].plot(seps[:frame_idx+1], 'b-', linewidth=2)
        axes[1, 1].axhline(y=8, color='g', linestyle='--', label='Binding threshold')
        axes[1, 1].set_ylim(0, 40)
        axes[1, 1].set_xlabel("Frame")
        axes[1, 1].set_ylabel("Separation (cells)")
        axes[1, 1].set_title(f"Separation: {frame['sep']:.1f} cells")
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)
        
        return [axes[0, 0], axes[0, 1], axes[1, 0], axes[1, 1]]
    
    anim = FuncAnimation(fig, update, frames=len(frames), interval=50, blit=False)
    anim.save(filename, writer='ffmpeg', fps=20, dpi=100)
    plt.close()
    
    print(f"✅ Saved to {filename}")
    print(f"   Average separation: {np.mean(seps):.2f} cells")
    print(f"   Final separation: {np.mean(seps[-10:]):.2f} cells")
    print(f"   Minimum: {np.min(seps):.2f} cells")


if __name__ == "__main__":
    print("="*70)
    print("VISUALIZE BOOTSTRAP TRIUMPH")
    print("="*70)
    print()
    
    # Use discovered best parameters (update after bootstrap run!)
    gamma_base = 0.0087  # From best run
    gamma_scale = 0.5546
    
    create_binding_video(gamma_base, gamma_scale)
    
    print("="*70)

