#!/bin/bash
# Run all validation tests in sequence

echo "╔═══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                               ║"
echo "║         MFRR Computational Validation Suite - Round 2                         ║"
echo "║                                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════════════════════╝"
echo ""

cd "$(dirname "$0")"

echo "Running V1: PT Regularity Map..."
python3 v1_pt_regularity_map.py
echo ""

echo "Running V2: Energy Condition Validation..."
python3 v2_energy_condition_validation.py
echo ""

echo "Running V3: Ψ-Ω Scaling Regimes..."
python3 v3_psi_omega_scaling_regimes.py
echo ""

echo "Running V4: Generalized Landauer..."
python3 v4_generalized_landauer.py
echo ""

echo "Running V5: SRRG Jacobian Spectrum..."
python3 v5_srrg_jacobian_spectrum.py
echo ""

echo "╔═══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                               ║"
echo "║                  ✅ ALL VALIDATION TESTS COMPLETE ✅                          ║"
echo "║                                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════════════════════╝"

