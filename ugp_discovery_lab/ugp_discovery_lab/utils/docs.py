"""
Documentation generation utilities for UGP Discovery Lab.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List
from ..core.registry import list_experiments


def generate_experiment_docs(output_dir: Path) -> Path:
    """
    Generate experiment documentation index.
    
    Args:
        output_dir: Output directory for documentation
    
    Returns:
        Path to generated documentation file
    """
    # Get list of available experiments
    experiments = list_experiments()
    
    # Find config files for each experiment
    config_dir = Path("configs/experiments")
    experiment_configs = {}
    
    if config_dir.exists():
        for config_file in config_dir.glob("*.yaml"):
            try:
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
                    exp_name = config.get("experiment", {}).get("name")
                    if exp_name:
                        experiment_configs[exp_name] = {
                            "config_file": str(config_file),
                            "config": config
                        }
            except Exception:
                continue
    
    # Generate markdown content
    md_content = """# UGP Discovery Lab - Experiment Index

This document provides an overview of all available experiments in the UGP Discovery Lab.

## Available Experiments

"""
    
    for exp_name in sorted(experiments):
        md_content += f"### {exp_name}\n\n"
        
        if exp_name in experiment_configs:
            config_info = experiment_configs[exp_name]
            config = config_info["config"]
            exp_config = config.get("experiment", {})
            
            # Add description
            description = exp_config.get("description", "No description available")
            md_content += f"**Description:** {description}\n\n"
            
            # Add configuration file
            md_content += f"**Configuration:** `{config_info['config_file']}`\n\n"
            
            # Add YAML schema
            md_content += "**YAML Schema:**\n```yaml\n"
            md_content += yaml.dump(config, default_flow_style=False, indent=2)
            md_content += "```\n\n"
            
            # Add usage example
            md_content += "**Usage:**\n```bash\n"
            md_content += f"ugp run-experiment -c {config_info['config_file']}\n"
            md_content += "```\n\n"
        else:
            md_content += "**Description:** No configuration file found\n\n"
        
        md_content += "---\n\n"
    
    # Add general usage information
    md_content += """## General Usage

### Running Experiments

```bash
# Run a single experiment
ugp run-experiment -c configs/experiments/experiment_name.yaml

# Run with plots (requires matplotlib)
ugp run-experiment -c configs/experiments/experiment_name.yaml --plots

# Run with multiple workers
ugp run-experiment -c configs/experiments/experiment_name.yaml --workers 4
```

### Running Test Suites

```bash
# Run smoke tests (fast)
ugp run-suite -c configs/suites/smoke.yaml

# Run CI golden path
ugp run-suite -c configs/suites/ci_golden.yaml

# Run full validation suite
ugp run-suite -c configs/suites/validation_suite.yaml
```

### Other Commands

```bash
# List available experiments
ugp list-experiments

# List available suites
ugp list-suites

# Clean up old artifacts
ugp clean --all

# Generate this documentation
ugp docs --output docs/
```

## Configuration Schema

All experiment configurations follow this general structure:

```yaml
experiment:
  name: "experiment_name"
  description: "Brief description of the experiment"
  
  # Experiment-specific parameters
  param1: value1
  param2: value2
  
  run:
    # Runtime parameters
    steps: 1000
    workers: 2
    
  fit:
    # Fitting parameters
    model: "model_specification"
    tolerance: 1e-6
    
  report:
    # Reporting options
    export_md: true
    export_json: true
```

## Experiment Types

### Core Experiments
- **ca_universality**: Test computational universality of cellular automata
- **lawful_evolution**: Explore UGP-lawful evolution patterns
- **reversible_core**: Test reversible computation extensions

### Discovery Experiments
- **dihedral_lock**: Search for dihedral symmetry constraints
- **kernel_fit**: Fit algebraic relationships in kernel space
- **index_lock**: Detect fixed index patterns
- **rg_flow**: Analyze renormalization group dynamics

### Validation Experiments
- **quarterlock_anchor**: Validate Quarter-Lock coefficient
- **dihedral_consistency**: Test dihedral constant hypotheses
- **lock_stability**: Stress test across parameter space

### Advanced Experiments
- **noether_current_scan**: Search for conserved currents
- **rg_cycle_detector**: Detect limit cycles in RG flow
- **holographic_transducer**: Test holographic reconstruction

## Scientific Methodology

All experiments follow rigorous scientific methodology:

1. **Empirical Validation**: Constants derived from data, not assumptions
2. **Error Analysis**: Confidence intervals and tolerance specifications
3. **Reproducibility**: Hash-based run equivalence detection
4. **Provenance Tracking**: Complete metadata and system information

## Contributing

To add a new experiment:

1. Create the experiment class in `ugp_discovery_lab/experiments/`
2. Add configuration file in `configs/experiments/`
3. Register the experiment using `@register_experiment`
4. Update this documentation with `ugp docs`

---
*Generated by UGP Discovery Lab Documentation System*
"""
    
    # Write to file
    docs_file = output_dir / "experiments.md"
    docs_file.write_text(md_content, encoding="utf-8")
    
    return docs_file


def generate_suite_docs(output_dir: Path) -> Path:
    """Generate test suite documentation."""
    # Find suite files
    suite_dir = Path("configs/suites")
    suites = []
    
    if suite_dir.exists():
        for suite_file in suite_dir.glob("*.yaml"):
            try:
                with open(suite_file, 'r') as f:
                    config = yaml.safe_load(f)
                    suites.append({
                        "file": str(suite_file),
                        "config": config
                    })
            except Exception:
                continue
    
    # Generate markdown content
    md_content = """# UGP Discovery Lab - Test Suite Index

This document provides an overview of all available test suites.

## Available Suites

"""
    
    for suite_info in suites:
        suite_config = suite_info["config"]
        suite_name = suite_config.get("suite", {}).get("name", "Unknown")
        description = suite_config.get("suite", {}).get("description", "No description")
        
        md_content += f"### {suite_name}\n\n"
        md_content += f"**Description:** {description}\n\n"
        md_content += f"**File:** `{suite_info['file']}`\n\n"
        
        # Add experiments in suite
        experiments = suite_config.get("experiments", [])
        if experiments:
            md_content += "**Experiments:**\n"
            for exp in experiments:
                exp_name = exp.get("name", "Unknown")
                exp_desc = exp.get("description", "No description")
                md_content += f"- {exp_name}: {exp_desc}\n"
            md_content += "\n"
        
        # Add usage
        md_content += "**Usage:**\n```bash\n"
        md_content += f"ugp run-suite -c {suite_info['file']}\n"
        md_content += "```\n\n"
        md_content += "---\n\n"
    
    # Write to file
    docs_file = output_dir / "suites.md"
    docs_file.write_text(md_content, encoding="utf-8")
    
    return docs_file
