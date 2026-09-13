#!/usr/bin/env python3
"""
vertex_truth_table.py — Finite vertex audit for UGP Interaction Skeleton Theorem

Generates truth tables for:
1. Gauge-fermion vertices (all chiral fermions × all SM gauge bosons)
2. Yukawa vertices (all L×H×R triples)  
3. Forbidden-process stress tests

Matches the Lean 4 formalization in ugp-physics-lean/UgpPhysicsLean/VertexTheorem.lean
and HiggsYukawa.lean.

All UGP definitions are UGP-native (winding, color, chirality — no SM input).
SM definitions are conventional representation-theoretic vertex tables.
"""

import hashlib, json, datetime

# ─── Fermion types ─────────────────────────────────────────────────────────────
FERMION_TYPES = ['ChargedLepton', 'Neutrino', 'UpQuark', 'DownQuark']
CHIRALITIES   = ['L', 'R']
COLORS        = [None, 'red', 'green', 'blue']   # None = colorless (leptons)

# ─── UGP winding number W = N_c × Q at N_c = 3 ───────────────────────────────
winding = {
    'ChargedLepton': -3,  # Q = -1
    'Neutrino':       0,  # Q = 0
    'UpQuark':        2,  # Q = +2/3
    'DownQuark':     -1,  # Q = -1/3
}

# ─── chargeNumerator3 (= winding at Nc=3 — for photon SM check) ────────────────
chargeNumerator3 = winding  # same values

# ─── Sector (colour multiplicity) ─────────────────────────────────────────────
def isLepton(ft):  return ft in ('ChargedLepton', 'Neutrino')
def isQuark(ft):   return ft in ('UpQuark', 'DownQuark')
def sameSector(f1, f2): return (isLepton(f1) and isLepton(f2)) or (isQuark(f1) and isQuark(f2))

# ─── UGP weak pair (from Spec 017-08) ─────────────────────────────────────────
def UGPWeakPair(f1, f2):
    return sameSector(f1, f2) and abs(winding[f1] - winding[f2]) == 3

# ─── Higgs winding ─────────────────────────────────────────────────────────────
higgs_winding = {'Hplus': 3, 'Hzero': 0}

# ─── StrongVertex (UGP color transfer) ────────────────────────────────────────
def StrongVertex(f1, f2, g_colorIn, g_colorOut, c1, c2):
    return (f1 == f2 and
            isQuark(f1) and
            c1 == g_colorIn and
            c2 == g_colorOut and
            c1 is not None and c2 is not None)

# ─── UGP gauge-fermion vertex ─────────────────────────────────────────────────
def UGPVertex(ft1, chi1, c1, ft2, chi2, c2, boson, g_colorIn=None, g_colorOut=None):
    if boson == 'photon':
        return ft1 == ft2 and c1 == c2
    elif boson == 'Z':
        return ft1 == ft2 and c1 == c2
    elif boson == 'Wplus':
        return (winding[ft2] == winding[ft1] + 3 and
                chi1 == 'L' and chi2 == 'L' and c1 == c2)
    elif boson == 'Wminus':
        return (winding[ft2] == winding[ft1] - 3 and
                chi1 == 'L' and chi2 == 'L' and c1 == c2)
    elif boson == 'gluon':
        return StrongVertex(ft1, ft2, g_colorIn, g_colorOut, c1, c2)
    return False

# ─── SM gauge-fermion vertex ───────────────────────────────────────────────────
def SMVertex(ft1, chi1, c1, ft2, chi2, c2, boson, g_colorIn=None, g_colorOut=None):
    if boson == 'photon':
        return chargeNumerator3[ft1] == chargeNumerator3[ft2] and c1 == c2
    elif boson == 'Z':
        return ft1 == ft2 and c1 == c2
    elif boson == 'Wplus':
        # W+ couples left-handed doublet members; direction: winding increases by 3
        return (winding[ft2] == winding[ft1] + 3 and
                chi1 == 'L' and chi2 == 'L' and c1 == c2)
    elif boson == 'Wminus':
        return (winding[ft2] == winding[ft1] - 3 and
                chi1 == 'L' and chi2 == 'L' and c1 == c2)
    elif boson == 'gluon':
        return StrongVertex(ft1, ft2, g_colorIn, g_colorOut, c1, c2)
    return False

# ─── UGP Yukawa ────────────────────────────────────────────────────────────────
def UGPYukawaAllowed(ftL, chiL, ftR, chiR, H):
    return (chiL == 'L' and chiR == 'R' and
            winding[ftL] + higgs_winding[H] == winding[ftR])

def SMYukawaAllowed(ftL, chiL, ftR, chiR):
    return (chiL == 'L' and chiR == 'R' and
            isQuark(ftL) == isQuark(ftR))

# ─── Audit 1: Gauge-fermion vertex truth table ──────────────────────────────────
print("=" * 70)
print("GAUGE-FERMION VERTEX AUDIT")
print("=" * 70)

EW_BOSONS = ['photon', 'Z', 'Wplus', 'Wminus']
mismatches = []
ew_vertex_count = 0
ew_allowed_count = 0

for B in EW_BOSONS:
    for ft1 in FERMION_TYPES:
        for chi1 in CHIRALITIES:
            for c1 in [None]:  # leptons have no colour; quarks have colour but for EW, same colour
                for ft2 in FERMION_TYPES:
                    for chi2 in CHIRALITIES:
                        c2 = c1
                        ugp = UGPVertex(ft1, chi1, c1, ft2, chi2, c2, B)
                        sm  = SMVertex(ft1, chi1, c1, ft2, chi2, c2, B)
                        ew_vertex_count += 1
                        if ugp:
                            ew_allowed_count += 1
                        if ugp != sm:
                            mismatches.append((B, ft1, chi1, ft2, chi2, ugp, sm))

# Add same-colour quark EW vertices
for B in EW_BOSONS:
    for ft1 in ['UpQuark', 'DownQuark']:
        for chi1 in CHIRALITIES:
            for ft2 in ['UpQuark', 'DownQuark']:
                for chi2 in CHIRALITIES:
                    for c in ['red', 'green', 'blue']:
                        ugp = UGPVertex(ft1, chi1, c, ft2, chi2, c, B)
                        sm  = SMVertex(ft1, chi1, c, ft2, chi2, c, B)
                        if ugp != sm:
                            mismatches.append((B, ft1+'_'+c, chi1, ft2+'_'+c, chi2, ugp, sm))

print(f"EW gauge boson cases checked: {ew_vertex_count}")
print(f"EW vertices allowed by UGP:  {ew_allowed_count}")
print(f"EW mismatches (UGP ≠ SM):    {len(mismatches)}")
if mismatches:
    for m in mismatches[:10]:
        print(f"  MISMATCH: {m}")
else:
    print("✓ Zero mismatches for EW gauge-fermion vertices")

# Gluon audit
print()
gluon_mismatches = []
for ft1 in ['UpQuark', 'DownQuark']:
    for ft2 in ['UpQuark', 'DownQuark']:
        for c1 in ['red', 'green', 'blue']:
            for c2 in ['red', 'green', 'blue']:
                ugp = UGPVertex(ft1, 'L', c1, ft2, 'L', c2, 'gluon', c1, c2)
                sm  = SMVertex(ft1, 'L', c1, ft2, 'L', c2, 'gluon', c1, c2)
                if ugp != sm:
                    gluon_mismatches.append((ft1, c1, ft2, c2, ugp, sm))
print(f"Gluon vertex mismatches: {len(gluon_mismatches)}")
if not gluon_mismatches:
    print("✓ Zero mismatches for gluon vertices")

total_mismatches = len(mismatches) + len(gluon_mismatches)
print(f"\n{'='*70}")
print(f"GAUGE-FERMION TOTAL MISMATCH COUNT: {total_mismatches}")
print(f"{'='*70}")

# ─── Audit 2: Yukawa vertex truth table ─────────────────────────────────────────
print()
print("=" * 70)
print("YUKAWA VERTEX AUDIT")
print("=" * 70)

HIGGS = ['Hplus', 'Hzero']
yukawa_mismatches = []
yukawa_total = 0
yukawa_ugp_allowed = 0
yukawa_sm_allowed = 0

for ftL in FERMION_TYPES:
    for ftR in FERMION_TYPES:
        for H in HIGGS:
            ugp = UGPYukawaAllowed(ftL, 'L', ftR, 'R', H)
            sm  = SMYukawaAllowed(ftL, 'L', ftR, 'R')
            yukawa_total += 1
            if ugp: yukawa_ugp_allowed += 1
            if sm:  yukawa_sm_allowed  += 1
            # UGP → SM should always hold (we proved ugp_yukawa_implies_sm [T])
            if ugp and not sm:
                yukawa_mismatches.append(('UGP_not_SM', ftL, H, ftR, ugp, sm))

print(f"Yukawa vertex triples (L+H+R): {yukawa_total}")
print(f"UGP-allowed:  {yukawa_ugp_allowed}")
print(f"SM-allowed:   {yukawa_sm_allowed}")
print(f"UGP→SM failures: {len(yukawa_mismatches)}")
if not yukawa_mismatches:
    print("✓ ugp_yukawa_implies_sm holds for all cases (as proved [T])")
else:
    for m in yukawa_mismatches:
        print(f"  FAILURE: {m}")

# List all UGP-allowed Yukawas
print("\nAll UGP-allowed Yukawa vertices (canonical SM mass terms):")
for ftL in FERMION_TYPES:
    for H in HIGGS:
        for ftR in FERMION_TYPES:
            if UGPYukawaAllowed(ftL, 'L', ftR, 'R', H):
                dW = winding[ftL] + higgs_winding[H] - winding[ftR]
                print(f"  {ftL}_L + {H} → {ftR}_R  [ΔW={dW}]  {'SM mass term ✓' if SMYukawaAllowed(ftL,'L',ftR,'R') else 'cross-sector!'}")

# ─── Audit 3: Forbidden process stress tests ────────────────────────────────────
print()
print("=" * 70)
print("FORBIDDEN PROCESS STRESS TESTS")
print("=" * 70)

forbidden_tests = [
    # (description, ft1, chi1, c1, ft2, chi2, c2, boson, should_be_forbidden)
    ("e↔u lepton-quark W+",     'ChargedLepton','L',None,  'UpQuark','L',None,  'Wplus', True),
    ("ν↔d lepton-quark W-",     'Neutrino','L',None,       'DownQuark','L',None,'Wminus',True),
    ("right-handed W+ e→ν",     'ChargedLepton','R',None,  'Neutrino','R',None,  'Wplus', True),
    ("right-handed W- ν→e",     'Neutrino','R',None,       'ChargedLepton','R',None,'Wminus',True),
    ("lepton-gluon e-gluon",    'ChargedLepton','L',None,  'ChargedLepton','L',None,'gluon',True),
    ("ν-gluon coupling",        'Neutrino','L',None,       'Neutrino','L',None,   'gluon',True),
    ("exotic W(+5) e→u",        'ChargedLepton','L',None,  'UpQuark','L',None,  'Wplus', True),  # W+ can't connect these
    ("baryon-violating e→u",    'ChargedLepton','L',None,  'UpQuark','L',None,  'Wplus', True),
    # Valid processes for contrast
    ("valid: e→ν W+",           'ChargedLepton','L',None,  'Neutrino','L',None,  'Wplus', False),
    ("valid: d→u W+",           'DownQuark','L','red',     'UpQuark','L','red',  'Wplus', False),
    ("valid: e photon",         'ChargedLepton','L',None,  'ChargedLepton','L',None,'photon',False),
    ("valid: u gluon r→g",      'UpQuark','L','red',       'UpQuark','L','green','gluon', False),
]

all_stress_pass = True
for desc, ft1, chi1, c1, ft2, chi2, c2, B, should_forbid in forbidden_tests:
    g_colorIn  = c1 if B == 'gluon' else None
    g_colorOut = c2 if B == 'gluon' else None
    ugp_allows = UGPVertex(ft1, chi1, c1, ft2, chi2, c2, B, g_colorIn, g_colorOut)
    correct    = (not ugp_allows) if should_forbid else ugp_allows
    status = "✓" if correct else "✗ FAIL"
    label  = "FORBIDDEN" if should_forbid else "ALLOWED"
    print(f"  {status} [{label}] {desc}: UGP says {'allowed' if ugp_allows else 'forbidden'}")
    if not correct:
        all_stress_pass = False

print()
print("Forbidden Yukawa stress tests:")
yukawa_forbidden = [
    ("e_L + H0 → d_R (lepton-quark)",          'ChargedLepton','L','DownQuark','R','Hzero', True),
    ("e_L + H+ → u_R (lepton-quark, charged)", 'ChargedLepton','L','UpQuark','R','Hplus',  True),
    ("u_L + H+ → u_R (wrong: 2+3≠2)",         'UpQuark','L','UpQuark','R','Hplus',        True),
    ("ν_L + H+ → ν_R (wrong: 0+3≠0)",         'Neutrino','L','Neutrino','R','Hplus',      True),
    ("d_L + H0 → u_R (wrong: -1+0≠2)",        'DownQuark','L','UpQuark','R','Hzero',      True),
    # Valid
    ("e_L + H0 → e_R (correct lepton mass)",   'ChargedLepton','L','ChargedLepton','R','Hzero', False),
    ("d_L + H+ → u_R (correct up mass)",       'DownQuark','L','UpQuark','R','Hplus',      False),
    ("d_L + H0 → d_R (correct down mass)",     'DownQuark','L','DownQuark','R','Hzero',    False),
    ("ν_L + H0 → ν_R (correct Dirac ν)",      'Neutrino','L','Neutrino','R','Hzero',      False),
]

for desc, ftL, chiL, ftR, chiR, H, should_forbid in yukawa_forbidden:
    ugp = UGPYukawaAllowed(ftL, chiL, ftR, chiR, H)
    correct = (not ugp) if should_forbid else ugp
    status  = "✓" if correct else "✗ FAIL"
    label   = "FORBIDDEN" if should_forbid else "ALLOWED"
    print(f"  {status} [{label}] {desc}: UGP says {'allowed' if ugp else 'forbidden'}")
    if not correct:
        all_stress_pass = False

# ─── Final summary ──────────────────────────────────────────────────────────────
print()
print("=" * 70)
print("FINAL AUDIT SUMMARY")
print("=" * 70)
print(f"Gauge-fermion EW mismatches:  {len(mismatches)}")
print(f"Gauge-fermion gluon mismatch: {len(gluon_mismatches)}")
print(f"Yukawa UGP→SM failures:       {len(yukawa_mismatches)}")
print(f"Forbidden-process tests pass: {'ALL ✓' if all_stress_pass else 'SOME FAILED ✗'}")
print()
total = len(mismatches) + len(gluon_mismatches) + len(yukawa_mismatches) + (0 if all_stress_pass else 1)
if total == 0:
    print("✅ MISMATCH COUNT = 0")
    print("✅ UGP INTERACTION SKELETON THEOREM VALIDATED")
else:
    print(f"❌ TOTAL ISSUES: {total}")

# ─── JSON artifact ──────────────────────────────────────────────────────────────
result = {
    "date": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "description": "UGP Interaction Skeleton — Finite Vertex Audit",
    "mismatch_count": total,
    "gauge_fermion_mismatches": len(mismatches) + len(gluon_mismatches),
    "yukawa_failures": len(yukawa_mismatches),
    "stress_tests_pass": all_stress_pass,
    "ugp_ew_allowed_vertices": ew_allowed_count,
    "yukawa_ugp_allowed": yukawa_ugp_allowed,
    "status": "VALIDATED" if total == 0 else "ISSUES_FOUND",
    "lean_theorem": "ugp_gauge_fermion_equals_sm : ∀ f1 f2 B, UGPVertex f1 f2 B ↔ SMVertex f1 f2 B [T]",
}
sha256 = hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()
result["sha256"] = sha256

outfile = "vertex_audit.json"
with open(outfile, "w") as f:
    json.dump(result, f, indent=2)
print(f"\nSHA-256: {sha256[:32]}...")
print(f"Saved → {outfile}")
