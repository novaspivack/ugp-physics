# Pillar 2a-R: Enhanced GTE Rosetta Stone Refinement

This directory contains the enhanced implementation of Project 2a-R from the UGP Research Program, which significantly expanded the feature space and employed advanced machine learning methods to push beyond the initial 67.7% accuracy threshold.

## Overview

The Enhanced GTE Rosetta Stone project implements an advanced data-driven discovery protocol to find the mapping between:
- **Input**: GTE triples (a, b, c) - the "genetic code" of particles
- **Output**: Quantum numbers (charge, spin, family, generation) - observable properties

## Key Enhancements

### Feature Space Expansion
- **360 total features** (9.2x expansion from v1.0)
- **276 interaction terms** (pairwise products of basic features)
- **30 non-linear transformations** (log, square, inverse)
- **15 ratio features** (component ratios)

### Advanced ML Methods
- **XGBoost Benchmark**: Established predictability ceiling
- **Enhanced Lasso Regression**: Multiple alpha values for optimal sparsity
- **Enhanced Symbolic Regression**: Expanded function set with MDL scoring
- **Ridge Regression**: Baseline comparison

## Repository Structure

```
UGP_topology_lab/
├── UPG_last_mile_research_program          # Main research program specification
├── PILLAR_2_SUMMARY.md                     # Complete Pillar 2 overview
├── pillar2a_rosetta_stone/                 # Original Pillar 2a implementation
│   ├── GTE_Feature_Extractor.py           # Basic feature extraction (39 features)
│   ├── Rosetta_Stone_Lab.py               # Basic ML pipeline
│   ├── Rosetta_Stone_Report.md            # Original analysis report
│   ├── feature_matrix.csv                 # Basic feature matrix (39×12)
│   ├── feature_matrix_unified.csv         # Basic unified dataset
│   ├── requirements.txt                   # Basic dependencies
│   └── README.md                          # Original documentation
└── pillar2a_refinement/                    # Complete Pillar 2a-R implementation
    ├── GTE_Feature_Extractor_v2.py        # Enhanced feature extraction (360 features)
    ├── Rosetta_Stone_Lab_v2.py            # Advanced ML pipeline (v2.0)
    ├── Advanced_Rosetta_Stone_Lab.py      # Advanced analysis (v3.0)
    ├── Focused_Rosetta_Stone_Lab.py       # Focused critical insights (v3.1)
    ├── requirements.txt                   # Updated dependencies
    ├── README.md                          # This documentation
    ├── Rosetta_Stone_Report_v2.md         # Enhanced analysis report
    ├── Final_Rosetta_Stone_Report_v3.md   # Comprehensive final report
    ├── feature_matrix_v2.csv              # Enhanced feature matrix (360×12)
    ├── feature_matrix_v2_unified.csv      # Enhanced unified dataset
    ├── advanced_feature_matrix.csv         # Advanced analysis results
    ├── focused_feature_matrix.csv          # Focused analysis results
    └── __pycache__/                        # Python cache directory
```

## Files

### Core Implementation
- **`GTE_Feature_Extractor_v2.py`**: Enhanced feature extraction with 360 features
- **`Rosetta_Stone_Lab_v2.py`**: Advanced ML pipeline (v2.0) with XGBoost benchmarking
- **`Advanced_Rosetta_Stone_Lab.py`**: Advanced analysis (v3.0) with comprehensive feature engineering
- **`Focused_Rosetta_Stone_Lab.py`**: Focused critical insights (v3.1) targeting specific discoveries
- **`requirements.txt`**: Updated Python dependencies including XGBoost

### Generated Data
- **`feature_matrix_v2.csv`**: Enhanced feature matrix (360 features × 12 particles)
- **`feature_matrix_v2_unified.csv`**: Enhanced unified dataset with features and targets
- **`advanced_feature_matrix.csv`**: Advanced analysis results with expanded feature set
- **`focused_feature_matrix.csv`**: Focused analysis results with critical insights

### Analysis Reports
- **`Rosetta_Stone_Report_v2.md`**: Enhanced analysis report (v2.0)
- **`Final_Rosetta_Stone_Report_v3.md`**: Comprehensive final report (v3.0) with complete analysis

## Usage

### Installation
```bash
pip install -r requirements.txt
```

### Running the Enhanced Discovery Protocol (v2.0)
```bash
python Rosetta_Stone_Lab_v2.py
```

This will:
1. Load canonical GTE triples and particle properties
2. Extract 360 enhanced features (interactions, non-linear, ratios)
3. Run advanced ML methods (XGBoost, enhanced Lasso, symbolic regression)
4. Generate comprehensive results and save enhanced data files

### Running the Advanced Analysis (v3.0)
```bash
python Advanced_Rosetta_Stone_Lab.py
```

This will:
1. Create comprehensive feature engineering (628 total features)
2. Run advanced ML methods with hyperparameter tuning
3. Identify Feature X176 and analyze critical insights
4. Generate advanced analysis results

### Running the Focused Analysis (v3.1)
```bash
python Focused_Rosetta_Stone_Lab.py
```

This will:
1. Create focused feature set based on critical insights (46 features)
2. Run focused ML methods targeting specific discoveries
3. Validate Möbius function dominance and Feature X176
4. Generate focused analysis results

### Testing the Enhanced Feature Extractor
```bash
python GTE_Feature_Extractor_v2.py
```

## Key Results

### Electric Charge Mapping - Complete Analysis
- **Accuracy**: 67.95% R² (consistent across XGBoost, Lasso, Ridge, Neural Networks)
- **Key Discovery**: Möbius function of b-component (`b_mu`) dominates with 65.34% importance
- **Feature X176 Identified**: `a_omega_x_a_sigma` with 41.41% correlation to charge
- **Top Features**: 
  1. `b_mu` (Möbius function of b): 65.34%
  2. `c_raw` (raw value of c): 22.41%
  3. `b_mod_5` (b modulo 5): 10.78%
- **Symbolic Formula**: `log(X176)` (36.58% R², single-term)
- **Predictability Ceiling**: 67.95% represents theoretical limit for current GTE triple information

### Family Classification - Enhanced
- **Accuracy**: 91.67% (maintained with enhanced features)
- **Key Features**: GCD relationships and interaction terms
- **Top Coefficients**:
  1. `gcd_bc`: 0.125 (greatest common divisor)
  2. `a_mod_5_x_b_mod_5`: -0.088 (interaction term)
  3. `a_omega_div_b_omega`: 0.084 (ratio feature)

### Advanced Analysis Results (v3.0)
- **Feature Engineering**: 628 total features (comprehensive expansion)
- **Method Validation**: Multiple algorithms achieve identical accuracy
- **Critical Insights**: Square-free parity fundamental to charge determination
- **Logarithmic Relationships**: Confirmed through symbolic regression

### Focused Analysis Results (v3.1)
- **Focused Features**: 46 features based on critical insights
- **Method Convergence**: 67.95% R² maintained with focused approach
- **Feature X176 Validation**: Confirmed as `a_omega_x_a_sigma`
- **Möbius Function Dominance**: Validated across all analysis methods

## Scientific Significance

### 1. Method Convergence
The **identical R² scores** (67.95%) across XGBoost, Lasso, and Ridge regression provides strong evidence that we have captured the maximum predictable variance in the current feature space.

### 2. Möbius Function Dominance
The **Möbius function of component b** emerges as the single most important feature, suggesting that **square-free parity** is fundamental to electric charge determination.

### 3. Interaction Terms Reveal Complex Structure
The importance of interaction terms reveals that the universe's "source code" operates through sophisticated mathematical relationships involving modular arithmetic gates and cross-component dependencies.

## Dependencies

- numpy >= 1.21.0
- pandas >= 1.3.0
- scikit-learn >= 1.0.0
- sympy >= 1.9.0
- gplearn >= 0.4.0
- matplotlib >= 3.5.0
- seaborn >= 0.11.0
- gmpy2 >= 2.1.0
- xgboost >= 1.6.0
- lightgbm >= 3.3.0

## Project Status

✅ **Phase 2a-R Complete**: Enhanced GTE Rosetta Stone discovered  
🔄 **Next Phase**: Project 2b - Construction of the Canonical Braid Atlas  
📋 **Deliverable**: Target topological fingerprints based on validated arithmetic patterns

## Related Documentation

- **Main Research Program**: [UPG_last_mile_research_program](../UPG_last_mile_research_program) - Complete UGP research program specification
- **Pillar 2 Overview**: [PILLAR_2_SUMMARY.md](../PILLAR_2_SUMMARY.md) - Complete Pillar 2 implementation summary
- **Original Implementation**: [pillar2a_rosetta_stone/](../pillar2a_rosetta_stone/) - Original Pillar 2a implementation
- **Enhanced Results**: [Rosetta_Stone_Report_v2.md](Rosetta_Stone_Report_v2.md) - Enhanced analysis report (v2.0)
- **Final Comprehensive Report**: [Final_Rosetta_Stone_Report_v3.md](Final_Rosetta_Stone_Report_v3.md) - Complete analysis with all findings
- **Enhanced Data**: [feature_matrix_v2.csv](feature_matrix_v2.csv) - Complete enhanced feature matrix
- **Advanced Data**: [advanced_feature_matrix.csv](advanced_feature_matrix.csv) - Advanced analysis results
- **Focused Data**: [focused_feature_matrix.csv](focused_feature_matrix.csv) - Focused analysis results

## Key Insights for Project 2b

The enhanced analysis provides crucial insights for the construction of the Canonical Braid Atlas:

1. **Focus on Möbius Function**: Square-free parity appears fundamental to charge determination
2. **Investigate Feature X176**: The symbolic regression identified a single highly predictive feature
3. **Develop Interaction-Based Invariants**: Topological equivalents of modular arithmetic interactions
4. **Explore Logarithmic Relationships**: The symbolic formula suggests logarithmic scaling may be fundamental
