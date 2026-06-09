"""
run_all.py
----------
Run all UGP investigation tests sequentially.
Results are printed to stdout and saved to results/ directory.
"""

import os
import sys
import time

os.makedirs('results', exist_ok=True)

scripts = [
    ('01_asymptotic_sieve.py',    'Asymptotic Sparsity Sieve'),
    ('02_diophantine_analysis.py','Diophantine System Analysis'),
    ('03_t6_root_hypothesis.py',  'T6: Positive Root Hypothesis'),
    ('04_galois_orbits.py',       'Galois Orbit Analysis'),
    ('05_wzw_structure.py',       'WZW Structure Summary'),
    ('06_synthesis.py',           'Final Synthesis'),
    ('07_e8_cyclotomic.py',       'T14: E8 Cyclotomic Universality'),
]

print("="*72)
print("UGP DEEPER THEORY INVESTIGATION - FULL RUN")
print("="*72)
print()

total_start = time.time()

for script, description in scripts:
    print(f"\n{'='*72}")
    print(f"Running: {description}")
    print(f"Script:  {script}")
    print(f"{'='*72}\n")

    start = time.time()

    # Import and run
    module_name = script.replace('.py', '')
    import importlib.util
    spec = importlib.util.spec_from_file_location(module_name, script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.run()

    elapsed = time.time() - start
    print(f"\n[Completed in {elapsed:.1f}s]")

total_elapsed = time.time() - total_start

print(f"\n{'='*72}")
print(f"ALL TESTS COMPLETE  ({total_elapsed:.1f}s total)")
print(f"{'='*72}")
print()
print("Results saved to:")
for f in sorted(os.listdir('results')):
    print(f"  results/{f}")
