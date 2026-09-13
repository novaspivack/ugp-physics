import os
import numpy as np
import matplotlib.pyplot as plt

def imshow_pair(a, b, title_a, title_b, fname_base, cmap="viridis"):
    plt.figure(figsize=(8,3.8))
    plt.subplot(1,2,1)
    plt.imshow(a, cmap=cmap, origin="lower")
    plt.title(title_a)
    plt.axis("off")
    plt.colorbar(shrink=0.8)
    plt.subplot(1,2,2)
    plt.imshow(b, cmap=cmap, origin="lower")
    plt.title(title_b)
    plt.axis("off")
    plt.colorbar(shrink=0.8)
    plt.tight_layout()
    plt.savefig(f"../../figures/{fname_base}.png", dpi=200)
    plt.savefig(f"../../figures/{fname_base}.pdf")
    print(f"✓ Generated {fname_base}.pdf")

def main():
    os.makedirs("../../figures", exist_ok=True)
    data = np.load("../../data/psi_fields.npz")
    psi_t0 = data["psi_t0"]
    psi_t1 = data["psi_t1"]
    if "grad_psi_t0" in data and "grad_psi_t1" in data:
        g0 = data["grad_psi_t0"]
        g1 = data["grad_psi_t1"]
    else:
        g0 = np.zeros_like(psi_t0)
        g1 = np.zeros_like(psi_t1)
    imshow_pair(psi_t0, psi_t1, "Ψ start", "Ψ end", "psi_maps")
    imshow_pair(g0, g1, "‖∇Ψ‖ start", "‖∇Ψ‖ end", "psi_grad_maps", cmap="magma")

if __name__ == "__main__":
    main()

