# UGP→GTE Build Instructions

This document provides build instructions for generating the UGP→GTE artifacts needed by the LaTeX document.

## Quick Start

### Option 1: Makefile (Recommended)
```bash
# Build both artifacts for n=10 (default)
make

# Build for specific level n
make N=12

# Clean output directory
make clean
```

### Option 2: Bash Script
```bash
# Build both artifacts for n=10 (default)
bash scripts/ugp_build_all.sh

# Build for specific level n
bash scripts/ugp_build_all.sh ./ugp_v2_out/atlas 12
```

### Option 3: Direct Python Calls
```bash
# Generate Fibonacci histogram
python3 scripts/ugp_make_fib_hist.py --outdir ./ugp_v2_out/atlas --n 10

# Generate basin plot
python3 scripts/ugp_make_basin_plot.py --outdir ./ugp_v2_out/atlas --n 10
```

## Build Artifacts

The build process generates two key artifacts in `./ugp_v2_out/atlas/`:

1. **`fib_index_hist.csv`** - Fibonacci index histogram data
   - Columns: `k,count`
   - Used by Figure L42 in the LaTeX document

2. **`basin_plot.pdf`** - Basin plot visualization
   - Used by Figure L41 in the LaTeX document

## LaTeX Compilation

After building the artifacts, compile the LaTeX document with:

```bash
pdflatex "\def\DataDir{./ugp_v2_out/atlas}\input{main.tex}"
```

This ensures the LaTeX document can find and load the generated data files.

## File Structure

```
UGP Paper/
├── main.tex                           # Main LaTeX document
├── scripts/
│   ├── ugp_make_fib_hist.py         # Fibonacci histogram generator
│   ├── ugp_make_basin_plot.py       # Basin plot generator
│   └── ugp_build_all.sh             # Consolidated build script
├── ugp_v2_out/atlas/                # Output directory (created by build)
│   ├── fib_index_hist.csv           # Generated Fibonacci data
│   └── basin_plot.pdf               # Generated basin plot
└── UGP_BUILD_INSTRUCTIONS.md        # This file
```

## Makefile

```makefile
# Build both UGP→GTE artifacts into ./ugp_v2_out/atlas
OUTDIR=./ugp_v2_out/atlas
N?=10

.PHONY: all atlas fib basin clean

all: atlas

atlas: fib basin
	@echo "Artifacts ready in $(OUTDIR)"
	@echo "Compile LaTeX with:"
	@echo '  pdflatex "\def\DataDir{$(OUTDIR)}\input{main.tex}"'

fib:
	@mkdir -p $(OUTDIR)
	@python3 scripts/ugp_make_fib_hist.py --outdir $(OUTDIR) --n $(N)

basin:
	@mkdir -p $(OUTDIR)
	@python3 scripts/ugp_make_basin_plot.py --outdir $(OUTDIR) --n $(N)

clean:
	@rm -rf $(OUTDIR)
```

## Bash Script

```bash
#!/usr/bin/env bash
set -euo pipefail
OUTDIR="${1:-./ugp_v2_out/atlas}"
N="${2:-10}"
mkdir -p "$OUTDIR"
python3 scripts/ugp_make_fib_hist.py  --outdir "$OUTDIR" --n "$N"
python3 scripts/ugp_make_basin_plot.py --outdir "$OUTDIR" --n "$N"
echo "Artifacts ready in $OUTDIR"
echo "Compile LaTeX with:"
echo "  pdflatex \"\\def\\DataDir{$OUTDIR}\\input{main.tex}\""
```

## Usage Examples

### Standard Build (n=10)
```bash
make
# or
bash scripts/ugp_build_all.sh
```

### Custom Level
```bash
make N=12
# or
bash scripts/ugp_build_all.sh ./ugp_v2_out/atlas 12
```

### Individual Components
```bash
# Generate only Fibonacci histogram
make fib

# Generate only basin plot
make basin

# Clean output
make clean
```

## Notes

- **Redundancy**: These helpers are redundant with your consolidated generator (`Paper_2_updates_2_final_additions.py`) but provide:
  - Independent regeneration of individual assets
  - Easy CI/CD integration
  - Quick level n adjustments without modifying the master script
- **Output Directory**: All artifacts are placed in `./ugp_v2_out/atlas/`
- **Data Integration**: The LaTeX document automatically loads these files when available, falling back to schematic representations when missing
- **Dependencies**: Requires Python 3 and the specified Python scripts in the `scripts/` directory

## Troubleshooting

### Common Issues

1. **Scripts not found**: Ensure the `scripts/` directory exists and contains the required Python files
2. **Permission denied**: Make the bash script executable with `chmod +x scripts/ugp_build_all.sh`
3. **Python errors**: Check that required Python packages are installed
4. **Output directory issues**: The build process automatically creates the output directory

### Verification

After building, verify the artifacts exist:
```bash
ls -la ./ugp_v2_out/atlas/
# Should show:
# fib_index_hist.csv
# basin_plot.pdf
```

Then compile the LaTeX document to confirm successful integration.
