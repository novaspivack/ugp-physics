# UGP Tools Phase 3 - Figure Generation and Build System

## Overview

Phase 3 adds comprehensive figure generation and build automation to the UGP Tools package. This enables automatic generation of all figures and data files needed for the UGP paper.

## New Features

### 1. Plotting Functions

#### `generate_basin_plot(n_min, n_max, output_path)`
- **Purpose**: Creates scatter plot of c-attractors by level n
- **Output**: `basin_plot.png` - Shows how c₁ values cluster by n level
- **Use case**: Visualize the basin structure of the UGP system

#### `generate_fib_index_histogram(n_min, n_max, output_path)`
- **Purpose**: Creates histogram of Fibonacci lift indices |q₂ - q₁|
- **Output**: 
  - `fib_index_hist.png` - Visual histogram
  - `fib_index_hist.csv` - Data for LaTeX integration
- **Use case**: Analyze the distribution of Fibonacci indices across survivors

#### `generate_transition_diagram(n_min, n_max, output_path)`
- **Purpose**: Creates state transition diagram with q-gap coloring
- **Output**: `transition_diagram.png` - Shows state flow with colored arrows
- **Use case**: Visualize the dynamics and transitions between states

### 2. Build Automation

#### `build_all(n_min, n_max, output_dir)`
- **Purpose**: One-command generation of all figures and data files
- **Outputs**:
  - `survivors.csv` - Prime-locked survivors with full coordinates
  - `orders.csv` - Order counts by n (mirror pair counts)
  - `basin_plot.png` - Basin visualization
  - `fib_index_hist.png` - Fibonacci index distribution
  - `transition_diagram.png` - State transition flow
- **Use case**: Complete paper asset generation in one command

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Verify installation:
```bash
python test_phase3.py
```

## Usage Examples

### Basic Usage

```python
from ugp_tools import build_all

# Generate all assets for n=10 to n=18
results = build_all(10, 18, "./paper_assets")
print(f"Generated: {results}")
```

### Individual Plot Generation

```python
from ugp_tools import generate_basin_plot, generate_fib_index_histogram

# Generate specific plots
generate_basin_plot(10, 15, "my_basin.png")
generate_fib_index_histogram(10, 15, "my_fib.png")
```

### Integration with LaTeX

The generated files integrate seamlessly with the LaTeX document:

- **PNG files**: Automatically loaded via `\AutoGraphic{}` macros
- **CSV files**: Auto-loaded via `\AutoCSVTable{}` macros
- **Data consistency**: All figures use the same survivor data

## File Structure

```
ugp_release/
├── ugp_tools.py          # Core functionality + Phase 3 additions
├── test_phase3.py        # Test suite for Phase 3
├── requirements.txt      # Python dependencies
├── PHASE3_README.md     # This file
├── streamlit_universe_finder.py  # Interactive interface
└── [generated outputs]  # Created by build_all()
```

## Testing

Run the comprehensive test suite:

```bash
python test_phase3.py
```

This will:
1. Test individual plotting functions
2. Test the comprehensive `build_all()` function
3. Verify all expected files are created
4. Clean up test artifacts

## Troubleshooting

### Common Issues

1. **Matplotlib backend errors**: Ensure you have a display or use `matplotlib.use('Agg')`
2. **Memory issues with large n ranges**: Use smaller ranges (e.g., 10-15 instead of 10-22)
3. **File permission errors**: Check write permissions in output directory

### Dependencies

- **Required**: matplotlib, numpy, pandas
- **Optional**: seaborn (for enhanced plots), streamlit (for interface)
- **Python**: 3.7+ recommended

## Integration with Paper

The generated figures automatically integrate with the LaTeX document through:

1. **Multi-path resolution**: Figures are found in `ugp_v2_out/atlas/` or `ugp_release/`
2. **Auto-loading macros**: `\AutoGraphic{}`, `\AutoCSVTable{}`, `\AutoListing{}`
3. **Fallback handling**: Placeholder boxes when files are missing

## Performance Notes

- **Small ranges (n=10-15)**: Fast, <5 seconds
- **Medium ranges (n=10-18)**: Moderate, 10-30 seconds  
- **Large ranges (n=10-22)**: Slower, 1-5 minutes
- **Memory usage**: Scales linearly with survivor count

## Future Enhancements

Potential Phase 4 improvements:
- Interactive plot customization
- Batch processing for multiple parameter sets
- Animation generation for dynamic processes
- 3D visualization of higher-dimensional structures
