"""
triple_exchange_s3_equivariance.py

Tests whether the S3 triality action on generation kink sector labels is equivariant
with the triple-exchange phase structure from gte_triple_kink_exchange_statistics (CatAL).

Configuration space: generation kinks with quantum numbers from PhiMDLKinkQuantumNumbers.lean
  gen1: (Q_phi=4, Q_chi=1)
  gen2: (Q_phi=4, Q_chi=2)
  gen3: (Q_phi=3, Q_chi=1)

Exchange phase (certified, uniform-triple case):
  BraidAtlasPhase(w) = -1 if w in {2,4,6} (SM fermions)
                     = +1 if w in {0,3} (SM bosons)

S3 action (from KinkSectorTrialityAction.lean, CatAL):
  rho: gen1->gen2->gen3->gen1 (cyclic)
  sigma: gen1->gen1, gen2->gen3, gen3->gen2 (spinor swap)

Main finding: The S3 triality action on {gen1,gen2,gen3} is NOT equivariant
with the certified exchange-statistics structure. sigma maps gen2 (Q_phi=4,
fermionic, phase -1) to gen3 (Q_phi=3, bosonic, phase +1), because 3=-4 mod 7
in Z7. The unique equivariant subgroup is Z2={e,sigma*rho^2}, which exchanges
gen1<->gen2 (both Q_phi=4).

Level framing:
  - Breaking datum: Level 0-1 (Q_phi values from CatAL Lean modules;
    BraidAtlasPhase assignment from CatAL Lean modules)
  - This constitutes a Level 0-1 obstruction to using the triple-exchange
    mechanism as a Level 3 carrier for the S3 action

Wall-clock timeout: 120 seconds.
"""

import json
import os
import signal
import sys
import time

TIMEOUT_SECONDS = 120
t_start = time.time()

def _timeout_handler(signum, frame):
    print(f"\nTIMEOUT after {TIMEOUT_SECONDS}s")
    sys.exit(1)

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm(TIMEOUT_SECONDS)

# ============================================================
# TASK 1: Configuration space description
# ============================================================

# Generation kink quantum numbers (from PhiMDLKinkQuantumNumbers.lean, CatAL)
GEN_QN = {
    'gen1': {'Q_phi': 4, 'Q_chi': 1},
    'gen2': {'Q_phi': 4, 'Q_chi': 2},
    'gen3': {'Q_phi': 3, 'Q_chi': 1},
}
GENS = ['gen1', 'gen2', 'gen3']

# Braid Atlas phase (from FermionicStatistics.lean BraidAtlasPhase, CatAL)
FERMION_SECTORS = {2, 4, 6}   # u quark, e-, d quark
BOSON_SECTORS   = {0, 3}       # vacuum/nu/gamma, W+

def braid_atlas_phase(w):
    """Phase for uniform triple (w,w,w) from gte_triple_kink_exchange_statistics."""
    if w in FERMION_SECTORS:
        return -1
    elif w in BOSON_SECTORS:
        return +1
    else:
        raise ValueError(f"w={w} not in PSC-admissible set {{0,2,3,4,6}}")

# ============================================================
# TASK 1a: Uniform-triple exchange phases for each generation
# ============================================================
print("=" * 70)
print("TASK 1: CONFIGURATION SPACE — Uniform Triple Exchange Phases")
print("=" * 70)
print()
print("Exchange phase P(g,g,g) = BraidAtlasPhase(Q_phi(g)) from CatAL theorem:")
print()
uniform_phases = {}
for g in GENS:
    w = GEN_QN[g]['Q_phi']
    phase = braid_atlas_phase(w)
    uniform_phases[g] = phase
    stats = "FERMIONIC" if phase == -1 else "BOSONIC"
    print(f"  P({g},{g},{g}) = BraidAtlasPhase({w}) = {phase:+d}  [{stats}]")

print()
print("Q_phi winding values of generation kinks:")
for g in GENS:
    print(f"  {g}: Q_phi={GEN_QN[g]['Q_phi']}, Q_chi={GEN_QN[g]['Q_chi']}")

assert uniform_phases['gen1'] == -1, "gen1 should be fermionic"
assert uniform_phases['gen2'] == -1, "gen2 should be fermionic"
assert uniform_phases['gen3'] == +1, "gen3 should be bosonic"
print()
print("CRITICAL ASYMMETRY: gen1,gen2 are fermionic (Q_phi=4); gen3 is BOSONIC (Q_phi=3)")

# Z7 additive inverse check: 3 = -4 mod 7
print(f"\nZ7 inverse check: Q_phi(gen3) = {GEN_QN['gen3']['Q_phi']} = -{GEN_QN['gen1']['Q_phi']} mod 7 = {(-4) % 7}")
assert GEN_QN['gen3']['Q_phi'] == (-4) % 7, "gen3 Q_phi should be -gen1 Q_phi in Z7"
print("CONFIRMED: gen3(Q_phi=3) is the Z7 additive inverse of gen1/gen2(Q_phi=4)")

# ============================================================
# TASK 2a: S3 action on sector labels
# ============================================================
print()
print("=" * 70)
print("TASK 2a: S3 ACTION ON SECTOR LABELS (from KinkSectorTrialityAction.lean, CatAL)")
print("=" * 70)
print()

gen_idx = {g: i for i, g in enumerate(GENS)}
idx_gen = {i: g for i, g in enumerate(GENS)}

def apply_perm(perm, gen_label):
    """Apply a permutation (list of 3 indices) to a generation label."""
    return idx_gen[perm[gen_idx[gen_label]]]

rho = [1, 2, 0]
rho2 = [2, 0, 1]
sigma = [0, 2, 1]
sigma_rho = [2, 1, 0]
sigma_rho2 = [1, 0, 2]
identity = [0, 1, 2]

s3_elements = [
    (identity, "e"),
    (rho, "rho"),
    (rho2, "rho^2"),
    (sigma, "sigma"),
    (sigma_rho, "sigma*rho"),
    (sigma_rho2, "sigma*rho^2"),
]

def compose(p, q):
    return [p[q[i]] for i in range(3)]

def perm_pow(p, n):
    r = [0,1,2]
    for _ in range(n):
        r = compose(p, r)
    return r

assert perm_pow(rho, 3) == identity, "rho^3 = id"
assert perm_pow(sigma, 2) == identity, "sigma^2 = id"
assert compose(sigma, compose(rho, sigma)) == compose(rho2, identity), "sigma*rho*sigma = rho^-1"
print("S3 relations verified: rho^3=id, sigma^2=id, sigma*rho*sigma=rho^-1")
print()

print("S3 element actions on {gen1,gen2,gen3}:")
for perm, name in s3_elements:
    g0 = apply_perm(perm, 'gen1')
    g1 = apply_perm(perm, 'gen2')
    g2 = apply_perm(perm, 'gen3')
    print(f"  {name:12s}  gen1->{g0:<8}  gen2->{g1:<8}  gen3->{g2:<8}")

# ============================================================
# TASK 2b: Equivariance check
# ============================================================
print()
print("=" * 70)
print("TASK 2b: EQUIVARIANCE CHECK")
print("=" * 70)
print()

violations = []
for perm, name in s3_elements:
    for g in GENS:
        pg = apply_perm(perm, g)
        before = uniform_phases[g]
        after = uniform_phases[pg]
        if before != after:
            violations.append((name, g, pg, before, after))

equivariant_uniform = (len(violations) == 0)

if violations:
    print("VIOLATIONS:")
    for name, g, pg, before, after in violations:
        print(f"  {name}: P({g})={before:+d}  ->  P({pg})={after:+d}  [BREAKS equivariance]")
else:
    print("  All equivariant")

print()
if equivariant_uniform:
    print("VERDICT: Uniform triple phases are S3-EQUIVARIANT")
else:
    print("VERDICT: Uniform triple phases are NOT S3-equivariant")
    print()
    print("THE BREAKING DATUM:")
    print("  sigma: gen2(Q_phi=4, phase=-1) <-> gen3(Q_phi=3, phase=+1)")
    print("  sigma acts as Z7 charge conjugation: Q_phi: 4 <-> 3 = -4 mod 7")
    print("  BraidAtlasPhase is NOT symmetric under Z7 charge conjugation")

# ============================================================
# TASK 2b (extra): Equivariant subgroup analysis
# ============================================================
print()
print("=" * 70)
print("TASK 2b: EQUIVARIANT SUBGROUP ANALYSIS")
print("=" * 70)
print()

def check_equivariance(subgroup_elems, subgroup_name):
    violations_sub = []
    for perm, name in subgroup_elems:
        for g in GENS:
            pg = apply_perm(perm, g)
            if uniform_phases[g] != uniform_phases[pg]:
                violations_sub.append((name, g, pg, uniform_phases[g], uniform_phases[pg]))
    if violations_sub:
        viol_str = "; ".join(f"{n}: {g}->{pg}, {pb}->{pa}"
                             for n, g, pg, pb, pa in violations_sub)
        print(f"  {subgroup_name}: NOT equivariant — {viol_str}")
    else:
        print(f"  {subgroup_name}: EQUIVARIANT")
    return len(violations_sub) == 0

equivariant_subgroups = []
for subgroup, name in [
    ([(identity, "e")],                         "trivial {e}"),
    ([(identity, "e"), (sigma, "sigma")],         "Z2 = {e, sigma}"),
    ([(identity, "e"), (sigma_rho, "sigma*rho")], "Z2 = {e, sigma*rho}"),
    ([(identity, "e"), (sigma_rho2, "sigma*rho^2")], "Z2 = {e, sigma*rho^2}"),
    ([(identity, "e"), (rho, "rho"), (rho2, "rho^2")], "Z3 = {e, rho, rho^2}"),
    (s3_elements,                                  "full S3"),
]:
    if check_equivariance(subgroup, name):
        equivariant_subgroups.append(name)

print()
print("Equivariant subgroups:", equivariant_subgroups)
print()
print("POSITIVE FINDING: Z2 = {e, sigma*rho^2} exchanges gen1<->gen2 (both Q_phi=4)")
print("while fixing gen3 (Q_phi=3). This is the generation-pair symmetry of the")
print("(gen1,gen2) doublet with identical exchange statistics.")

# Assertions
assert not equivariant_uniform, "S3 should NOT be equivariant"
assert check_equivariance([(identity, "e"), (sigma_rho2, "sigma*rho^2")], "Z2={e,sigma*rho^2} (assertion)"), \
    "Z2={e,sigma*rho^2} should be equivariant"

signal.alarm(0)

# ============================================================
# JSON ARTIFACT
# ============================================================
artifact_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
artifact_path = os.path.join(artifact_dir, 'triple_exchange_s3_equivariance_results.json')

results = {
    "script": "triple_exchange_s3_equivariance.py",
    "paper": "P55 — The Octonionic Shadow of GF(7)",
    "question": "Does triple-exchange carry a natural S3 structure realizing triality at Level 3?",
    "answer": "NO",
    "task1_config_space": {
        "certified_domain": "uniform triples (w,w,w) with w in PSC-admissible {0,2,3,4,6}",
        "generation_kink_QNs": GEN_QN,
        "Q_phi_values": [GEN_QN[g]['Q_phi'] for g in GENS],
        "note": "Generation kink triple (gen1,gen2,gen3) has Q_phi=(4,4,3) -- NOT uniform",
        "z7_additive_inverse": "Q_phi(gen3)=3 = -Q_phi(gen1)=4 mod 7"
    },
    "task2_equivariance": {
        "uniform_triple_phases": {g: uniform_phases[g] for g in GENS},
        "equivariant": False,
        "breaking_datum": "sigma: gen2(Q_phi=4, phase=-1) <-> gen3(Q_phi=3, phase=+1); 3 = -4 mod 7",
        "equivariant_subgroup": "Z2={e,sigma*rho^2} (gen1<->gen2 exchange, both Q_phi=4)",
        "non_equivariant": ["Z3={e,rho,rho^2}", "Z2={e,sigma}", "Z2={e,sigma*rho}", "full S3"]
    },
    "level_framing": {
        "breaking_datum_level": "Level 0-1 (Q_phi from CatAL; BraidAtlasPhase from CatAL)",
        "implication": "Level 0-1 obstruction to using triple-exchange as Level 3 S3 carrier",
        "c3pp_status": "OPEN -- triple-exchange route blocked; appropriate carrier requires Q_chi-dependent phase"
    },
    "robustness": "ROBUST — finite arithmetic on certified Q_phi values; exact computation"
}

with open(artifact_path, 'w') as f:
    json.dump(results, f, indent=2)

print()
print(f"JSON artifact saved: {artifact_path}")
print()
print("All assertions passed.")
