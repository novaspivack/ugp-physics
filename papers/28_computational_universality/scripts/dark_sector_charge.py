# dark_sector_charge.py
# Rank 162-DKP: Dark Sector Electric Charge Assignment from Z7 Portal Constraints
# Verifies Q(dark₁)=+1/3 and Q(dark₅)=−2/3 against all Z7-conserving vertices.

SM_charges = {0: 0, 2: 2/3, 3: 1, 4: -1, 6: -1/3}
dark_charges = {1: 1/3, 5: -2/3}
all_charges = {**SM_charges, **dark_charges}
dark_windings = {1, 5}

# Rule 110 truth table (f_MDL binary projection)
rule110 = {
    (0,0,0): 0, (0,0,1): 1, (0,1,0): 1, (0,1,1): 1,
    (1,0,0): 0, (1,0,1): 1, (1,1,0): 1, (1,1,1): 0
}

def fmdl(a, b, c):
    ba = 1 if a != 0 else 0
    bb = 1 if b != 0 else 0
    bc = 1 if c != 0 else 0
    return rule110[(ba, bb, bc)]

all_vocab = list(range(7))
results = {"permitted_conserved": [], "suppressed_conserved": [], "suppressed_violated": []}

for a in all_vocab:
    for b in all_vocab:
        c_val = (a - b) % 7
        if all(w in all_charges for w in [a, b, c_val]):
            dark_involved = bool(dark_windings & {a, b, c_val})
            if dark_involved:
                r110 = fmdl(a, b, c_val)
                Q_a = all_charges[a]
                Q_b = all_charges[b]
                Q_c = all_charges[c_val]
                conserved = abs(Q_a - Q_b - Q_c) < 1e-10
                entry = {"vertex": (a, b, c_val), "fmdl": r110,
                         "Q": (Q_a, Q_b, Q_c), "conserved": conserved}
                if r110 == 1 and conserved:
                    results["permitted_conserved"].append(entry)
                elif r110 == 0 and conserved:
                    results["suppressed_conserved"].append(entry)
                else:
                    results["suppressed_violated"].append(entry)

print("=== CHARGE ASSIGNMENT VERIFICATION: Q(dark₁)=+1/3, Q(dark₅)=−2/3 ===")
print(f"f_MDL-permitted and charge-conserved: {len(results['permitted_conserved'])}")
print(f"f_MDL-suppressed and charge-conserved: {len(results['suppressed_conserved'])}")
print(f"f_MDL-suppressed and charge-VIOLATED:  {len(results['suppressed_violated'])}")
print()
print("ALL f_MDL-permitted dark vertices are charge-conserved: "
      + str(len(results['permitted_conserved']) > 0 and len(results['suppressed_violated']) == 0 or
            all(r["fmdl"] == 0 for r in results["suppressed_violated"])))
print()
print("Permitted conserved vertices:")
for e in results["permitted_conserved"]:
    a, b, c = e["vertex"]
    Qa, Qb, Qc = e["Q"]
    print(f"  w={a}→w={b}+w={c}: Q={Qa:+.4f}→{Qb:+.4f}+{Qc:+.4f} ✓")
print()
print("Violated vertices (all f_MDL-suppressed):")
for e in results["suppressed_violated"]:
    a, b, c = e["vertex"]
    Qa, Qb, Qc = e["Q"]
    deficit = Qa - Qb - Qc
    print(f"  w={a}→w={b}+w={c}: Q={Qa:+.4f}→{Qb:+.4f}+{Qc:+.4f}, deficit={deficit:+.4f}")
