#!/bin/bash
# TE_2.4 Environment Setup Script
# Sets up Python environment with all required dependencies

set -e  # Exit on error

echo "============================================================"
echo "TE_2.4: Black-Hole Unitarity - Environment Setup"
echo "============================================================"

# Check Python version
echo ""
echo "Checking Python version..."
python3 --version

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Error: Python $REQUIRED_VERSION or higher required (found $PYTHON_VERSION)"
    exit 1
fi

echo "✓ Python $PYTHON_VERSION detected"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo ""
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo ""
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# Verify critical packages
echo ""
echo "Verifying critical packages..."

python3 << EOF
import sys

packages = {
    'numpy': 'NumPy',
    'scipy': 'SciPy',
    'matplotlib': 'Matplotlib',
    'qutip': 'QuTiP',
}

missing = []
for module, name in packages.items():
    try:
        __import__(module)
        print(f"✓ {name} installed")
    except ImportError:
        print(f"❌ {name} NOT installed")
        missing.append(name)

if missing:
    print(f"\n❌ Missing packages: {', '.join(missing)}")
    sys.exit(1)
else:
    print("\n✓ All critical packages verified")
EOF

# Check for optional packages
echo ""
echo "Checking optional packages..."

python3 << EOF
optional = {
    'jax': 'JAX (for Hessians)',
    'pandas': 'Pandas (for data analysis)',
    'seaborn': 'Seaborn (for plotting)',
}

for module, name in optional.items():
    try:
        __import__(module)
        print(f"✓ {name} installed")
    except ImportError:
        print(f"⚠️  {name} not installed (optional)")
EOF

# Set up PYTHONPATH for TE_1 modules
echo ""
echo "Setting up PYTHONPATH for TE_1 modules..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
TE1_PATH="$REPO_ROOT/MFRR/TE_1_VALIDATION_PROGRAM"

if [ -d "$TE1_PATH" ]; then
    export PYTHONPATH="${PYTHONPATH}:${TE1_PATH}"
    echo "✓ TE_1 modules path added to PYTHONPATH"
    echo "  Path: $TE1_PATH"
else
    echo "⚠️  TE_1 modules path not found (you may need to set this manually)"
    echo "  Expected: $TE1_PATH"
fi

# Create results directories
echo ""
echo "Creating results directories..."
mkdir -p results/jt_toy_model/plots
mkdir -p results/gksl
mkdir -p results/stinespring
mkdir -p results/page_curve/plots
echo "✓ Results directories created"

# Summary
echo ""
echo "============================================================"
echo "✓ Environment setup complete!"
echo "============================================================"
echo ""
echo "To activate the environment in the future, run:"
echo "  source venv/bin/activate"
echo ""
echo "To run the Phase 1 test:"
echo "  cd src"
echo "  python te2_4_jt_toy_model.py"
echo ""
echo "To deactivate the environment:"
echo "  deactivate"
echo ""
echo "============================================================"

