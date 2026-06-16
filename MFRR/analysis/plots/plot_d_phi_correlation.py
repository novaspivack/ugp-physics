import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def main():
    os.makedirs("../../figures", exist_ok=True)
    df = pd.read_csv("../../data/d_phi_series.csv")
    x = df["D"].to_numpy()
    y = df["Phi"].to_numpy()
    A = np.vstack([x, np.ones_like(x)]).T
    a, b = np.linalg.lstsq(A, y, rcond=None)[0]
    yfit = a*x + b
    r = np.corrcoef(x, y)[0,1]
    plt.figure(figsize=(6.2,4.8))
    plt.scatter(x, y, s=10, alpha=0.7)
    plt.plot(x, yfit, linewidth=2, color='red', label=f'Linear fit (r={r:.4f})')
    plt.xlabel("D")
    plt.ylabel("Φ")
    plt.title(f"corr(D, Φ) = {r:.4f}")
    plt.legend()
    plt.tight_layout()
    plt.savefig("../../figures/d_phi_correlation.png", dpi=200)
    plt.savefig("../../figures/d_phi_correlation.pdf")
    print(f"✓ Generated d_phi_correlation.pdf (r={r:.4f})")

if __name__ == "__main__":
    main()

