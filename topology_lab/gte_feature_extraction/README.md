# Pillar 2a: The GTE Rosetta Stone

This directory contains the implementation of Project 2a from the UGP Research Program, which seeks to discover the mathematical formulas that map GTE triples to particle quantum numbers.

## Overview

The GTE Rosetta Stone project implements a data-driven discovery protocol to find the mapping between:
- **Input**: GTE triples (a, b, c) - the "genetic code" of particles
- **Output**: Quantum numbers (charge, spin, family, generation) - observable properties

## Repository Structure

```
UGP_topology_lab/
├── UPG_last_mile_research_program          # Main research program specification
└── pillar2a_rosetta_stone/                 # Pillar 2a implementation directory
    ├── GTE_Feature_Extractor.py           # Core feature extraction module
    ├── Rosetta_Stone_Lab.py               # Main experimental harness
    ├── requirements.txt                    # Python dependencies
    ├── README.md                          # This documentation file
    ├── Rosetta_Stone_Report.md            # Comprehensive analysis report
    ├── feature_matrix.csv                 # Complete feature matrix (39×12)
    ├── feature_matrix_unified.csv         # Unified dataset with targets
    └── __pycache__/                       # Python cache directory
```

## Files

### Core Implementation
- **`GTE_Feature_Extractor.py`**: Extracts 39 number-theoretic features from GTE triples
- **`Rosetta_Stone_Lab.py`**: Main experimental harness for discovery protocol
- **`requirements.txt`**: Python dependencies

### Generated Data
- **`feature_matrix.csv`**: Complete feature matrix (39 features × 12 particles)
- **`feature_matrix_unified.csv`**: Unified dataset with features and targets
- **`Rosetta_Stone_Report.md`**: Comprehensive analysis report

## Usage

### Installation
```bash
pip install -r requirements.txt
```

### Running the Discovery Protocol
```bash
python Rosetta_Stone_Lab.py
```

This will:
1. Load canonical GTE triples and particle properties
2. Extract number-theoretic features
3. Run multiple discovery methods (decision trees, lasso regression, symbolic regression)
4. Generate results and save data files

### Testing the Feature Extractor
```bash
python GTE_Feature_Extractor.py
```

## Key Results

### Electric Charge Mapping
- **Accuracy**: 67.7% (Lasso regression)
- **Key Features**: Modular arithmetic (mod 5), Möbius function
- **Formula**: `div(X17, X23)` (symbolic regression)

### Family Classification
- **Accuracy**: 91.7% (Logistic regression)
- **Key Features**: Radical values, sigma functions
- **Distinguishes**: Leptons vs Quarks

### Generation Mapping
- **Accuracy**: 91.7% (Decision tree)
- **Key Features**: Sum of triple components, modular arithmetic

### Spin Mapping
- **Result**: Constant 0.5 for all fundamental fermions
- **Interpretation**: Fundamental property, not derived from GTE triples

## Scientific Significance

The discovery of these mappings provides:
1. **Evidence** for the UGP hypothesis that physics emerges from arithmetic
2. **Targets** for Pillar 3's topological fitness search
3. **Insights** into the modular arithmetic structure of the universe

## Next Steps

This project provides the "meet-in-the-middle" targets for Pillar 3, where we will search for the Logos Operator that generates braids with these specific topological fingerprints.

## Dependencies

- numpy >= 1.21.0
- pandas >= 1.3.0
- scikit-learn >= 1.0.0
- sympy >= 1.9.0
- gplearn >= 0.4.0 (optional, for symbolic regression)
- matplotlib >= 3.5.0
- seaborn >= 0.11.0
- gmpy2 >= 2.1.0

## Project Status

✅ **Phase 2a Complete**: GTE Rosetta Stone discovered  
🔄 **Next Phase**: Integration with Pillar 3 - Topological Fitness Search  
📋 **Deliverable**: Canonical Braid Atlas (target topological fingerprints)

## Related Documentation

- **Main Research Program**: [UPG_last_mile_research_program](../UPG_last_mile_research_program) - Complete UGP research program specification
- **Results Data**: [feature_matrix.csv](feature_matrix.csv) - Complete feature matrix
- **Analysis Report**: [Rosetta_Stone_Report.md](Rosetta_Stone_Report.md) - Detailed findings and scientific implications
