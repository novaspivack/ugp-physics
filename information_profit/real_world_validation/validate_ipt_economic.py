"""
Economic validation of the Information Profit Threshold (IPT ≈ 1.1309)
using the UCI Polish Companies Bankruptcy Dataset.

Dataset: Zieba et al. (2016), Expert Systems with Applications.
Source: https://archive.ics.uci.edu/dataset/365/polish+companies+bankruptcy+data

The Gen/Drain ratio is constructed from Attr58:
    Attr58 = total costs / total sales
    Gen/Drain = 1 / Attr58 = total sales / total costs

IPT hypothesis: companies with sustained Gen/Drain < IPT ≈ 1.1309 have
significantly higher probability of bankruptcy than those above this threshold.

The test distinguishes IPT = 1.1309 from the trivial threshold IPT = 1.0
(profitable/unprofitable) by comparing ROC-AUC and classification accuracy.
"""

import math
import json
import os
import warnings
import numpy as np
import pandas as pd
from scipy.io import arff
from scipy.stats import mannwhitneyu, pointbiserialr
from sklearn.metrics import roc_auc_score, roc_curve, classification_report
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

warnings.filterwarnings('ignore')

# ── Constants ──────────────────────────────────────────────────────────────────
PHI = (1 + math.sqrt(5)) / 2
LAMBDA_CONST = math.log(PHI) / math.log(2 * math.pi)
IPT = 1 + LAMBDA_CONST / 2          # ≈ 1.1309
TRIVIAL_THRESHOLD = 1.0              # profitable/unprofitable cutoff
ATTR58_COL = 'Attr58'                # total costs / total sales
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)

print(f"φ = {PHI:.6f}")
print(f"Λ = ln(φ)/ln(2π) = {LAMBDA_CONST:.6f}")
print(f"IPT = 1 + Λ/2 = {IPT:.6f} ≈ {IPT:.4f}")
print(f"Trivial threshold = {TRIVIAL_THRESHOLD:.4f}")
print()


# ── Data loading ───────────────────────────────────────────────────────────────
def load_year(year: int) -> pd.DataFrame:
    path = os.path.join(DATA_DIR, f'{year}year.arff')
    data, _ = arff.loadarff(path)
    df = pd.DataFrame(data)
    df['class'] = (df['class'] == b'1').astype(int)   # 1=bankrupt, 0=solvent
    df['year'] = year
    for col in df.columns:
        if col not in ('class', 'year'):
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df


print("Loading dataset (years 1–5)...")
frames = [load_year(y) for y in range(1, 6)]
df_all = pd.concat(frames, ignore_index=True)
print(f"Total instances: {len(df_all):,}   Bankrupt: {df_all['class'].sum():,}   "
      f"Solvent: {(df_all['class']==0).sum():,}")
print()


# ── Compute Gen/Drain ratio ────────────────────────────────────────────────────
# Gen/Drain = 1 / Attr58  (total sales / total costs)
# Exclude non-positive Attr58 (undefined or zero-sales companies)
valid = df_all[ATTR58_COL].notna() & (df_all[ATTR58_COL] > 0)
df = df_all[valid].copy()
df['gen_drain'] = 1.0 / df[ATTR58_COL]

# Remove extreme outliers (Gen/Drain > 50x is almost certainly a data error)
df = df[df['gen_drain'] < 50].copy()
print(f"Valid instances after cleaning: {len(df):,}")
print(f"Gen/Drain  mean={df['gen_drain'].mean():.4f}  "
      f"median={df['gen_drain'].median():.4f}  "
      f"std={df['gen_drain'].std():.4f}")
print()

# By class
bankrupt = df[df['class'] == 1]['gen_drain']
solvent  = df[df['class'] == 0]['gen_drain']
print(f"Bankrupt companies   Gen/Drain: mean={bankrupt.mean():.4f}  "
      f"median={bankrupt.median():.4f}  n={len(bankrupt)}")
print(f"Solvent  companies   Gen/Drain: mean={solvent.mean():.4f}  "
      f"median={solvent.median():.4f}  n={len(solvent)}")
print()


# ── Statistical tests ──────────────────────────────────────────────────────────
# Mann-Whitney U: are the distributions different?
mw_stat, mw_p = mannwhitneyu(solvent, bankrupt, alternative='greater')
print(f"Mann-Whitney U (solvent > bankrupt): stat={mw_stat:.0f}  p={mw_p:.2e}")

# Point-biserial correlation: Gen/Drain vs bankruptcy label
corr, corr_p = pointbiserialr(df['class'], df['gen_drain'])
print(f"Point-biserial r (bankruptcy ~ Gen/Drain): r={corr:.4f}  p={corr_p:.2e}")
print()


# ── Classification: IPT vs trivial threshold ───────────────────────────────────
def threshold_metrics(threshold, label):
    pred = (df['gen_drain'] < threshold).astype(int)
    y    = df['class'].values
    tp = ((pred==1) & (y==1)).sum()
    tn = ((pred==0) & (y==0)).sum()
    fp = ((pred==1) & (y==0)).sum()
    fn = ((pred==0) & (y==1)).sum()
    accuracy  = (tp + tn) / len(y)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1        = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    auroc     = roc_auc_score(y, df['gen_drain'].apply(lambda x: -x))  # lower → more bankrupt
    print(f"Threshold {label} = {threshold:.4f}:")
    print(f"  Accuracy={accuracy:.4f}  Precision={precision:.4f}  "
          f"Recall={recall:.4f}  F1={f1:.4f}  AUROC={auroc:.4f}")
    return dict(threshold=threshold, label=label, accuracy=accuracy,
                precision=precision, recall=recall, f1=f1, auroc=auroc)


metrics_ipt     = threshold_metrics(IPT,              'IPT (1.1309)')
metrics_trivial = threshold_metrics(TRIVIAL_THRESHOLD, 'trivial (1.0)')
print()

# Fraction below each threshold by class
below_ipt_bankrupt = (bankrupt < IPT).mean()
below_ipt_solvent  = (solvent  < IPT).mean()
below_1_bankrupt   = (bankrupt < 1.0).mean()
below_1_solvent    = (solvent  < 1.0).mean()
print(f"Below IPT  (1.1309): bankrupt={below_ipt_bankrupt:.3f}  solvent={below_ipt_solvent:.3f}  "
      f"lift={below_ipt_bankrupt/below_ipt_solvent:.2f}x")
print(f"Below 1.00          : bankrupt={below_1_bankrupt:.3f}   solvent={below_1_solvent:.3f}   "
      f"lift={below_1_bankrupt/below_1_solvent:.2f}x")
print()


# ── Threshold sweep: find the empirically optimal threshold ───────────────────
thresholds = np.linspace(0.8, 2.0, 241)
aurocs, f1s, precisions, recalls = [], [], [], []

y = df['class'].values
gd = df['gen_drain'].values

for t in thresholds:
    pred  = (gd < t).astype(int)
    tp = ((pred==1) & (y==1)).sum()
    tn = ((pred==0) & (y==0)).sum()
    fp = ((pred==1) & (y==0)).sum()
    fn = ((pred==0) & (y==1)).sum()
    prec   = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1val  = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
    auroc  = roc_auc_score(y, -gd)
    f1s.append(f1val)
    precisions.append(prec)
    recalls.append(rec)
    aurocs.append(auroc)  # constant (threshold-independent for ROC-AUC)

best_f1_idx = np.argmax(f1s)
best_f1_threshold = thresholds[best_f1_idx]
best_f1_value     = f1s[best_f1_idx]
print(f"Empirically optimal F1 threshold: {best_f1_threshold:.4f}  "
      f"(F1={best_f1_value:.4f})")
print(f"IPT = {IPT:.4f}  |  empirical optimum = {best_f1_threshold:.4f}  "
      f"|  difference = {abs(IPT - best_f1_threshold):.4f}")
print()


# ── Per-year analysis ──────────────────────────────────────────────────────────
print("Per-year: mean Gen/Drain by class")
for yr in range(1, 6):
    sub = df[df['year'] == yr]
    b = sub[sub['class']==1]['gen_drain']
    s = sub[sub['class']==0]['gen_drain']
    below_ipt_b = (b < IPT).mean() if len(b) > 0 else float('nan')
    below_ipt_s = (s < IPT).mean() if len(s) > 0 else float('nan')
    print(f"  Year {yr}: bankrupt mean={b.mean():.4f} (below IPT: {below_ipt_b:.3f})  "
          f"solvent mean={s.mean():.4f} (below IPT: {below_ipt_s:.3f})  "
          f"n_bankrupt={len(b)}  n_solvent={len(s)}")
print()


# ── ROC curve figure ──────────────────────────────────────────────────────────
fpr, tpr, roc_thresholds = roc_curve(y, -gd)
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Panel 1: ROC curve
axes[0].plot(fpr, tpr, 'b-', linewidth=2, label=f'Gen/Drain (AUROC={aurocs[0]:.4f})')
axes[0].plot([0,1],[0,1],'k--', alpha=0.5, label='Random')
axes[0].set_xlabel('False Positive Rate')
axes[0].set_ylabel('True Positive Rate')
axes[0].set_title('ROC Curve: Gen/Drain as Bankruptcy Predictor')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Panel 2: Gen/Drain distributions with threshold lines
bins = np.linspace(0.5, 3.0, 80)
axes[1].hist(solvent.clip(0.5, 3.0),  bins=bins, alpha=0.5, color='steelblue', label='Solvent',  density=True)
axes[1].hist(bankrupt.clip(0.5, 3.0), bins=bins, alpha=0.5, color='crimson',   label='Bankrupt', density=True)
axes[1].axvline(IPT, color='darkgreen', linewidth=2, linestyle='-',
                label=f'IPT = {IPT:.4f}')
axes[1].axvline(TRIVIAL_THRESHOLD, color='orange', linewidth=2, linestyle='--',
                label='Trivial threshold = 1.0')
axes[1].axvline(best_f1_threshold, color='purple', linewidth=1.5, linestyle=':',
                label=f'Empirical F1-opt = {best_f1_threshold:.4f}')
axes[1].set_xlabel('Gen/Drain ratio (= 1 / Attr58)')
axes[1].set_ylabel('Density')
axes[1].set_title('Gen/Drain Distributions: Bankrupt vs Solvent')
axes[1].legend(fontsize=8)
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
fig_path = os.path.join(RESULTS_DIR, 'ipt_economic_validation.png')
plt.savefig(fig_path, dpi=150, bbox_inches='tight')
print(f"Figure saved: {fig_path}")


# ── Save results JSON ─────────────────────────────────────────────────────────
results = {
    "dataset": "UCI Polish Companies Bankruptcy Dataset (Zieba et al. 2016)",
    "ipt_value": IPT,
    "lambda_constant": LAMBDA_CONST,
    "phi": PHI,
    "n_total": int(len(df)),
    "n_bankrupt": int(df['class'].sum()),
    "n_solvent": int((df['class']==0).sum()),
    "gen_drain_mean_bankrupt": float(bankrupt.mean()),
    "gen_drain_median_bankrupt": float(bankrupt.median()),
    "gen_drain_mean_solvent": float(solvent.mean()),
    "gen_drain_median_solvent": float(solvent.median()),
    "mann_whitney_p": float(mw_p),
    "point_biserial_r": float(corr),
    "point_biserial_p": float(corr_p),
    "fraction_below_ipt_bankrupt": float(below_ipt_bankrupt),
    "fraction_below_ipt_solvent": float(below_ipt_solvent),
    "lift_at_ipt": float(below_ipt_bankrupt / below_ipt_solvent),
    "fraction_below_1_bankrupt": float(below_1_bankrupt),
    "fraction_below_1_solvent": float(below_1_solvent),
    "lift_at_1": float(below_1_bankrupt / below_1_solvent),
    "metrics_ipt": metrics_ipt,
    "metrics_trivial": metrics_trivial,
    "empirical_f1_optimal_threshold": float(best_f1_threshold),
    "empirical_f1_optimal_value": float(best_f1_value),
    "ipt_vs_empirical_delta": float(abs(IPT - best_f1_threshold)),
    "auroc": float(aurocs[0])
}

results_path = os.path.join(RESULTS_DIR, 'ipt_economic_validation.json')
with open(results_path, 'w') as f:
    json.dump(results, f, indent=2)
print(f"Results saved: {results_path}")
print()
print("=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"IPT = {IPT:.4f}")
print(f"AUROC = {results['auroc']:.4f}")
print(f"Lift at IPT threshold: {results['lift_at_ipt']:.2f}x")
print(f"Lift at trivial (1.0): {results['lift_at_1']:.2f}x")
print(f"Empirical F1-optimal threshold: {best_f1_threshold:.4f}  (Δ from IPT: {results['ipt_vs_empirical_delta']:.4f})")
print(f"Mann-Whitney p (solvent > bankrupt): {mw_p:.2e}")
