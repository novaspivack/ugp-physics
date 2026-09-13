#!/usr/bin/env python3
import numpy as np
import csv, os

G = 6.67430e-11
c = 299792458.0

def coherence_energy(alpha1, alpha2, Psi0, V, ell, Cshape=1.0):
    return alpha1*Psi0**2 * V + Cshape*alpha2*Psi0**2 * V/(ell**2)

def scenario(name, alpha1, alpha2, Psi0, V, R, ell, Cshape=1.0):
    Epsi = coherence_energy(alpha1, alpha2, Psi0, V, ell, Cshape)
    Meff = Epsi / c**2
    gsurf = G*Meff/(R**2)
    return dict(name=name, Epsi=Epsi, Meff=Meff, g=gsurf, g_over_g0=gsurf/9.80665)

def main():
    outdir = "e16_detect_outputs"
    os.makedirs(outdir, exist_ok=True)

    # Example calibrations (SI):
    # alpha1 [J/m^3], alpha2 [J/m]
    # Choose conservative small values representing extremely weak coupling energy scale.
    alpha1 = 1e-6     # J/m^3
    alpha2 = 1e-6     # J/m
    Psi0_lab = 1e-2
    ell_lab = 0.1     # m

    cases = []
    # Lab cube 1 m^3, R ~ 0.62 m (equiv sphere radius for same volume)
    V1 = 1.0
    R1 = (3.0*V1/(4.0*np.pi))**(1/3)
    cases.append(scenario("Lab_1m3", alpha1, alpha2, Psi0_lab, V1, R1, ell_lab))

    # Data hall 100m x 100m x 30m
    Vdc = 100*100*30
    Rdc = (3.0*Vdc/(4.0*np.pi))**(1/3)
    cases.append(scenario("DataHall_3e5m3", alpha1, alpha2, Psi0_lab, Vdc, Rdc, ell_lab))

    # Large campus 1km x 1km x 30m
    Vbig = 1000*1000*30
    Rbig = (3.0*Vbig/(4.0*np.pi))**(1/3)
    cases.append(scenario("Campus_3e7m3", alpha1, alpha2, Psi0_lab, Vbig, Rbig, ell_lab))

    with open(os.path.join(outdir,"scenarios.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name","Epsi[J]","Meff[kg]","g[m/s^2]","g/g0"])
        for c in cases:
            w.writerow([c["name"], c["Epsi"], c["Meff"], c["g"], c["g_over_g0"]])

    print("Wrote e16_detect_outputs/scenarios.csv")

if __name__ == "__main__":
    main()
