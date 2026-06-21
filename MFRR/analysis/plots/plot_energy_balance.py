import os
import pandas as pd
import matplotlib.pyplot as plt

def main():
    df = pd.read_csv("../../data/energy_timeseries.csv")
    os.makedirs("../../figures", exist_ok=True)
    plt.figure(figsize=(8,4.5))
    plt.plot(df["t"], df["E_tot"], label="E_tot")
    plt.plot(df["t"], df["D_psi"], label="D_psi")
    plt.plot(df["t"], df["D_chi"], label="D_chi")
    plt.plot(df["t"], df["W_ext"], label="W_ext")
    plt.xlabel("t")
    plt.ylabel("Energy / Rate")
    plt.legend()
    plt.tight_layout()
    plt.savefig("../../figures/pt_energy_balance.png", dpi=200)
    plt.savefig("../../figures/pt_energy_balance.pdf")
    print("✓ Generated pt_energy_balance.pdf")

if __name__ == "__main__":
    main()

