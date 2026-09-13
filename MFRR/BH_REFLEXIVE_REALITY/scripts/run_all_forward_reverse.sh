#!/usr/bin/env bash
#
# Orchestrator for Forward-Reverse Adjudication Experiments (E1-E4)
#
# Reference: MFRR Appendix E
# Date: November 4, 2025

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
SCRIPTS="${ROOT}"

echo "╔═══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                               ║"
echo "║        FORWARD-REVERSE ADJUDICATION EXPERIMENTS (E1-E4)                       ║"
echo "║                                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# E1: PT ↔ PT^{-1} Cycle
echo "=== Running E1: PT↔PT^{-1} cycle test ==="
python3 "${SCRIPTS}/cycles/pt_cycle.py"
E1_STATUS=$?
echo ""

# E2: Hawking vs Reflexive Landauer balance
echo "=== Running E2: Hawking vs Reflexive Landauer balance test ==="
python3 "${SCRIPTS}/entropy_flow/hawking_landauer_balance.py"
E2_STATUS=$?
echo ""

# E3: Analog white-hole (planned)
if [ -f "${SCRIPTS}/analogs/bec_whitehole_signflip.py" ]; then
  echo "=== Running E3: analog white-hole sign-flip test ==="
  python3 "${SCRIPTS}/analogs/bec_whitehole_signflip.py"
  E3_STATUS=$?
else
  echo "=== E3: Analog white-hole test (planned, script not yet implemented) ==="
  E3_STATUS=0
fi
echo ""

# E4: Cosmological PT^{-1} dark-energy link (planned)
if [ -f "${SCRIPTS}/cosmo/de_as_PTinv.py" ]; then
  echo "=== Running E4: cosmological PT^{-1} dark-energy link test ==="
  python3 "${SCRIPTS}/cosmo/de_as_PTinv.py"
  E4_STATUS=$?
else
  echo "=== E4: Cosmological PT^{-1} dark-energy link (planned, script not yet implemented) ==="
  E4_STATUS=0
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════════════╗"
echo "║                          EXPERIMENT SUMMARY                                   ║"
echo "╚═══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check status codes
if [ $E1_STATUS -eq 0 ]; then
    echo "E1: ✅ COMPLETE"
else
    echo "E1: ❌ FAIL"
fi

if [ $E2_STATUS -eq 0 ]; then
    echo "E2: ✅ COMPLETE"
else
    echo "E2: ❌ FAIL"
fi

echo "E3: (planned)"
echo "E4: (planned)"

echo ""
echo "═══════════════════════════════════════════════════════════════════════════════"
echo "Artifacts:"
echo "  - results/*.json"
echo "  - figures/*.png"
echo "═══════════════════════════════════════════════════════════════════════════════"

