import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def compute_margin(df):
    bound = df["kBTlogn"] + df["lambda1_intPsi2"] + df["lambda2_intGradPsi2"]
    return df["delta_E_PT"] - bound

def main():
    os.makedirs("../../figures", exist_ok=True)
    df = pd.read_csv("../../data/landauer_trials.csv")
    df["margin"] = compute_margin(df)
    plt.figure(figsize=(7.5,4.5))
    for k, grp in df.groupby("regime"):
        x = np.full(len(grp), hash(k)%97)
        plt.scatter(x, grp["margin"], label=k, s=18)
    plt.axhline(0.0, linestyle="--", color="black", linewidth=0.8)
    plt.ylabel("Δ = ΔE_PT − (k_BT log n + λ₁∫Ψ² + λ₂∫‖∇Ψ‖²)")
    plt.xticks([])
    plt.legend()
    plt.tight_layout()
    plt.savefig("../../figures/landauer_margins_scatter.png", dpi=200)
    plt.savefig("../../figures/landauer_margins_scatter.pdf")
    print("✓ Generated landauer_margins_scatter.pdf")
    stats = df.groupby("regime")["margin"].agg(["count","mean","median","min","max"])
    stats.to_csv("../../figures/landauer_margins_stats.csv")
    print("✓ Generated landauer_margins_stats.csv")

if __name__ == "__main__":
    main()

