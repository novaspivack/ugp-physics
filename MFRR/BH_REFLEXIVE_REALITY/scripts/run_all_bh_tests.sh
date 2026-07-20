#!/bin/bash
#
# Master runner for BH1-BH4 Validation Tests
#
# Date: November 4, 2025
# Reference: MFRR Section 9, Appendix D

echo "╔═══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                               ║"
echo "║         BH1-BH4: BLACK-HOLE REFLEXIVE REALITY VALIDATION SUITE                ║"
echo "║                                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Change to scripts directory
cd "$(dirname "$0")"

# Run each test
echo "Running BH1: Horizon Adjudication..."
python3 bh1_horizon_adjudication.py
BH1_STATUS=$?

echo ""
echo "Running BH2: CP-Fusion Merger..."
python3 bh2_cp_fusion_merger.py
BH2_STATUS=$?

echo ""
echo "Running BH3: Reverse Adjudication (Wormhole)..."
python3 bh3_reverse_adjudication.py
BH3_STATUS=$?

echo ""
echo "Running BH4: Cosmic Global CP..."
python3 bh4_global_cp_cosmo.py
BH4_STATUS=$?

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════════════╗"
echo "║                          VALIDATION SUMMARY                                   ║"
echo "╚═══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check status codes
if [ $BH1_STATUS -eq 0 ]; then
    echo "BH1: ✅ PASS"
else
    echo "BH1: ❌ FAIL"
fi

if [ $BH2_STATUS -eq 0 ]; then
    echo "BH2: ✅ PASS"
else
    echo "BH2: ❌ FAIL"
fi

if [ $BH3_STATUS -eq 0 ]; then
    echo "BH3: ✅ PASS"
else
    echo "BH3: ❌ FAIL"
fi

if [ $BH4_STATUS -eq 0 ]; then
    echo "BH4: ✅ PASS"
else
    echo "BH4: ❌ FAIL"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""

# Extract results
echo "Detailed Results:"
echo ""

if [ -f "../outputs/bh1_outputs/bh1_horizon_results.json" ]; then
    python3 -c "import json; r=json.load(open('../outputs/bh1_outputs/bh1_horizon_results.json')); print(f\"BH1: E_PT/E_bound = {r['reflexive_energy']['ratio_at_horizon']:.4f} (target: 1.00 ± 0.02)\")"
fi

if [ -f "../outputs/bh2_outputs/bh2_merger_results.json" ]; then
    python3 -c "import json; r=json.load(open('../outputs/bh2_outputs/bh2_merger_results.json')); print(f\"BH2: ΔS/S = {r['entropy']['Delta_S_over_S_percent']:.1f}% (target: > 0%)\")"
fi

if [ -f "../outputs/bh3_outputs/bh3_wormhole_results.json" ]; then
    python3 -c "import json; r=json.load(open('../outputs/bh3_outputs/bh3_wormhole_results.json')); print(f\"BH3: Sign reversal = {r['reverse_adjudication']['sign_reversal']} (target: True)\")"
fi

if [ -f "../outputs/bh4_outputs/bh4_cosmic_results.json" ]; then
    python3 -c "import json; r=json.load(open('../outputs/bh4_outputs/bh4_cosmic_results.json')); print(f\"BH4: w_Ψ = {r['equation_of_state']['w_Psi_mean']:.3f} ± {r['equation_of_state']['w_Psi_std']:.3f} (target: -1.00 ± 0.05)\")"
fi

echo ""
echo "All figures saved in ../outputs/bh{1,2,3,4}_outputs/"
echo ""
echo "╔═══════════════════════════════════════════════════════════════════════════════╗"
echo "║                 ✅ BH VALIDATION SUITE COMPLETE ✅                            ║"
echo "╚═══════════════════════════════════════════════════════════════════════════════╝"

