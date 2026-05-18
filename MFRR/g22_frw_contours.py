#!/usr/bin/env python3
import numpy as np, os
import matplotlib.pyplot as plt

def main():
    outdir="g22_frw_contours"; os.makedirs(outdir, exist_ok=True)
    w0s = np.linspace(-1.1, -0.9, 31)
    was = np.linspace(-0.1, +0.1, 41)
    W0, WA = np.meshgrid(w0s, was, indexing='ij')
    mask = (np.abs(WA)<=0.05)  # your "viable" band from theory
    plt.figure(figsize=(6,4))
    plt.contourf(W0, WA, mask.astype(float), levels=[-0.1,0.5,1.1], colors=['white','#8fd3ff'])
    plt.xlabel(r'$w_0$'); plt.ylabel(r'$w_a$')
    plt.title(r'Viable region (Reflexive: $|w_a| \leq 0.05$)')
    plt.tight_layout()
    plt.savefig(os.path.join(outdir,"w0wa_viable.png"), dpi=160); plt.close()
    print("G22: wrote g22_frw_contours/w0wa_viable.png")

if __name__=="__main__":
    main()

