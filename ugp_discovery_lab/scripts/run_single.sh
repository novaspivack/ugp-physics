#!/usr/bin/env bash
set -euo pipefail

# UGP Discovery Lab - Run Single Experiment Script
# Usage: ./scripts/run_single.sh [experiment_config] [workers]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default values
EXPERIMENT_CONFIG="${1:-configs/experiments/gte_lucas.yaml}"
WORKERS="${2:-}"

echo "🧪 UGP Discovery Lab - Running Single Experiment"
echo "================================================"
echo "Experiment config: $EXPERIMENT_CONFIG"
echo "Workers: ${WORKERS:-auto}"
echo "Project root: $PROJECT_ROOT"
echo

# Change to project root
cd "$PROJECT_ROOT"

# Run the experiment
if [ -n "$WORKERS" ]; then
    ugp run-experiment -c "$EXPERIMENT_CONFIG" --workers "$WORKERS"
else
    ugp run-experiment -c "$EXPERIMENT_CONFIG"
fi

echo
echo "✅ Experiment completed successfully!"
