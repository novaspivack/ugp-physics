import os
import pandas as pd

def main():
    os.makedirs("../../figures", exist_ok=True)
    df = pd.read_csv("../../data/landauer_trials.csv")
    df["margin"] = df["delta_E_PT"] - (df["kBTlogn"] + df["lambda1_intPsi2"] + df["lambda2_intGradPsi2"])
    tbl = df.groupby("regime")["margin"].agg(
        Trials="count",
        PassFraction=lambda s: (s>=0).mean(),
        MinMargin="min",
        MedianMargin="median"
    ).reset_index()
    with open("../../figures/landauer_table.tex","w") as f:
        f.write("\\begin{tabular}{@{}lcccc@{}}\\toprule\n")
        f.write("Regime & Trials & Pass fraction & Min($\\Delta$) & Median $\\Delta$ \\\\\\midrule\n")
        for _, r in tbl.iterrows():
            f.write(f"{r['regime']} & {int(r['Trials'])} & {r['PassFraction']:.2f} & {r['MinMargin']:.4g} & {r['MedianMargin']:.4g} \\\\\n")
        f.write("\\bottomrule\\end{tabular}\n")
    print("✓ Generated landauer_table.tex")
    stats = df.groupby("regime")["margin"].agg(["count","mean","median","min","max"])
    stats.to_csv("../../figures/landauer_margins_stats.csv")
    print("✓ Generated landauer_margins_stats.csv")

if __name__ == "__main__":
    main()

