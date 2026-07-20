# Installation and Usage Guide

## Quick Install

### 1. Extract the Package
```bash
unzip goldstone_profit_package.zip
cd goldstone_profit_package
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install numpy matplotlib
```

### 3. Run Quick Start
```bash
python3 code/quick_start.py
```

This will display the two key predictions and their experimental confirmations.

---

## Detailed Usage

### Running All Tests

#### Initial Discovery Test
```bash
python3 code/test_goldstone_profit.py
```

**Output:** Compares pion and Higgs mass ratios to Λ and Λ/2

#### Comprehensive Test Suite
```bash
python3 code/comprehensive_profit_test.py
```

**Output:** Tests across QCD, electroweak, BCS, cosmology (9 systems)

#### Generate Visualizations
```bash
python3 code/create_visualization.py
```

**Output:** Two PNG files in results/ directory

---

## Understanding the Results

### Reading the Test Output

Example output:
```
QCD π±: (m_π/Λ_QCD)² = 0.121749
Expected Λ/2 = 0.130915
Error: 7.00% ⭐⭐
```

**Stars indicate accuracy:**
- ⭐⭐⭐ Excellent (< 5% error)
- ⭐⭐ Good (5-10% error)
- ⭐ Acceptable (10-20% error)
- (no stars) Boundary condition or failure

### Key Files to Read

**For executives/overview:**
1. `README.md` (start here)
2. `results/profit_principle_confirmed_cases.png` (visual summary)
3. `docs/Goldstone_Profit_Isomorphism_FINAL_REPORT.md` (sections 1-3)

**For researchers:**
1. `DERIVATIONS.md` (complete mathematical framework)
2. `docs/Goldstone_Profit_Isomorphism_FINAL_REPORT.md` (full report)
3. `derivations/goldstone_profit_derivation.md` (initial reasoning)

**For experimentalists:**
1. Section 4 of final report (predictions for future tests)
2. `comprehensive_profit_test.py` (see test methodology)
3. Appendix B in DERIVATIONS.md (error analysis)

---

## Customizing Tests

### Test Your Own System

Edit `quick_start.py` or create a new script:

```python
import numpy as np

# Norfleet's constant
phi = (1 + np.sqrt(5)) / 2
Lambda = np.log(phi) / np.log(2*np.pi)

# Your data
m_particle = 500  # MeV (example)
Lambda_breaking = 1000  # MeV (example)

# Test for pseudo-Goldstone
ratio = (m_particle / Lambda_breaking)**2
expected = Lambda / 2
error = abs(ratio - expected) / expected * 100

print(f"Ratio: {ratio:.6f}")
print(f"Expected: {expected:.6f}")
print(f"Error: {error:.2f}%")

if error < 10:
    print("Match confirmed!")
else:
    print("Boundary condition or different mechanism")
```

### Adding New Tests to Comprehensive Suite

In `comprehensive_profit_test.py`, add to the test section:

```python
# Your new test
r_new = test_ratio("Your System", "(m/Λ)²",
                   observed_value, expected_value, "Lambda/2")
print(f"Test: {r_new}")
```

---

## Troubleshooting

### Common Issues

**Issue:** "ModuleNotFoundError: No module named 'numpy'"
**Solution:** Install dependencies: `pip install numpy matplotlib`

**Issue:** "Permission denied" when running scripts
**Solution:** Make executable: `chmod +x code/*.py`

**Issue:** Figures not generating
**Solution:** Check matplotlib backend. Try: `export MPLBACKEND=Agg`

**Issue:** Different numerical results
**Solution:** Check Python version (need 3.7+) and numpy version (need 1.20+)

### Getting Help

1. Read the README.md thoroughly
2. Check DERIVATIONS.md for mathematical details
3. Review the code comments in the scripts
4. Consult the final report for physical interpretation

### Known Limitations

- **Lattice QCD scale ambiguity**: Λ_QCD depends on scheme (MS-bar vs rough)
- **Heavy quark corrections**: Kaons/eta have strong explicit breaking
- **Finite volume effects**: Some lattice QCD systematics
- **Running couplings**: All values quoted at specific scales

---

## Advanced Usage

### Batch Testing

To test multiple systems:

```bash
for file in code/*.py; do
    echo "Running $file..."
    python3 "$file"
done
```

### Generating Publication Figures

The visualizations are publication-quality (300 DPI):

```bash
python3 code/create_visualization.py
ls -lh results/*.png
```

Output files:
- `profit_principle_symmetry_breaking.png` (comprehensive, 6 panels)
- `profit_principle_confirmed_cases.png` (focused, 2 panels)

### Custom Analysis

To compute Λ for different constants:

```python
import numpy as np

def compute_lambda(a, b):
    """Compute Λ = ln(a)/ln(b)"""
    return np.log(a) / np.log(b)

# Standard
Lambda = compute_lambda(phi, 2*np.pi)  # 0.2618

# Alternative ratios (for research)
alt1 = compute_lambda(np.e, 2*np.pi)   # e instead of φ
alt2 = compute_lambda(phi, np.pi)      # π instead of 2π
```

---

## File Structure Reference

```
goldstone_profit_package/
│
├── README.md                   ← Start here
├── CHANGELOG.md                ← Version history
├── INSTALL.md                  ← This file
├── requirements.txt            ← Python dependencies
├── DERIVATIONS.md              ← Complete math (80+ pages)
│
├── code/
│   ├── quick_start.py         ← Run this first
│   ├── test_goldstone_profit.py      ← Initial discovery
│   ├── comprehensive_profit_test.py  ← Full test suite
│   └── create_visualization.py       ← Generate figures
│
├── derivations/
│   ├── goldstone_profit_derivation.md   ← Initial reasoning
│   └── goldstone_profit_CONFIRMED.md    ← Confirmed results
│
├── docs/
│   └── Goldstone_Profit_Isomorphism_FINAL_REPORT.md  ← Full report
│
└── results/
    ├── profit_principle_symmetry_breaking.png     ← 6-panel figure
    └── profit_principle_confirmed_cases.png       ← 2-panel summary
```

---

## System Requirements

### Minimum
- Python 3.7+
- numpy 1.20+
- 100 MB disk space
- Any OS (Linux, macOS, Windows)

### Recommended
- Python 3.9+
- numpy 1.24+
- matplotlib 3.5+
- 500 MB disk space (for additional analysis)

### For Development
- pytest (testing)
- jupyter (notebooks)
- scipy (extended analysis)

---

## Performance

All scripts run in < 5 seconds on modern hardware:
- `quick_start.py`: < 1 second
- `test_goldstone_profit.py`: < 1 second
- `comprehensive_profit_test.py`: < 1 second
- `create_visualization.py`: ~2-3 seconds (figure generation)

No GPU or special hardware required.

---

## Contributing

This is a research package documenting a scientific discovery. If you find:

- **Errors in calculations**: Check DERIVATIONS.md section 6
- **Updated experimental data**: Update values in test scripts
- **New systems to test**: Follow the pattern in comprehensive_profit_test.py

---

## Citation

If you use this work in research, please cite:

**BibTeX:**
```bibtex
@article{Spivack2025GoldstoneProfit,
  title={The Goldstone-Profit Isomorphism: Spontaneous Symmetry Breaking 
         as Information-Theoretic Transputation},
  author={Spivack, Nova},
  journal={Mathematical Foundations of Reflexive Reality},
  year={2025},
  note={Confirmed with 1.4\% and 7\% experimental accuracy}
}
```

**Text:**
Spivack, N. (2025). "The Goldstone-Profit Isomorphism." *Mathematical Foundations of Reflexive Reality*. Confirmed with 1.4% and 7% experimental accuracy.

---

## Next Steps

After installation:

1. **Quick start**: Run `python3 code/quick_start.py`
2. **Read overview**: Open `README.md`
3. **See figures**: View `results/*.png`
4. **Full report**: Read `docs/Goldstone_Profit_Isomorphism_FINAL_REPORT.md`
5. **Deep dive**: Study `DERIVATIONS.md`

**For questions or feedback:** This is a research discovery package documenting experimental confirmation of a theoretical prediction.

---

**Happy exploring!** 🎉

You now have all the tools to verify, extend, and apply the Goldstone-Profit isomorphism discovery.

---

**END OF INSTALLATION GUIDE**
