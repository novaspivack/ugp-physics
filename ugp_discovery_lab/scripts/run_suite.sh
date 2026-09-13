#!/usr/bin/env bash
set -euo pipefail

# UGP Discovery Lab - Run Test Suite Script
# Usage: ./scripts/run_suite.sh [suite_config] [workers]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default values
SUITE_CONFIG="${1:-configs/suites/starter_suite.yaml}"
WORKERS="${2:-}"

echo "🧪 UGP Discovery Lab - Running Test Suite"
echo "=========================================="
echo "Suite config: $SUITE_CONFIG"
echo "Workers: ${WORKERS:-auto}"
echo "Project root: $PROJECT_ROOT"
echo

# Change to project root
cd "$PROJECT_ROOT"

# Run the suite
if [ -n "$WORKERS" ]; then
    ugp run-suite -c "$SUITE_CONFIG" --workers "$WORKERS"
else
    ugp run-suite -c "$SUITE_CONFIG"
fi

echo
echo "✅ Suite completed successfully!"
