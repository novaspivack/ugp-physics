#!/usr/bin/env bash
# Run all BH computational tests

set -euo pipefail

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║    Black Holes in Reflexive Reality — Test Suite             ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

mkdir -p csv figs

echo "Running QNM shift calculation..."
python3 qnm_rr_shift.py

echo ""
echo "Running TOV+Ψ shell analysis..."
python3 tov_psi.py

echo ""
echo "Running JT island Page-time shift..."
python3 jt_rr_page.py

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ All tests complete. See ./csv and ./figs."
echo "═══════════════════════════════════════════════════════════════"

