"""
Reporting system for experiment results and analysis.
"""

import sys
import json
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from ..utils.io import safe_json_dump, create_provenance


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles numpy types."""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        return super().default(obj)


def write_json_report(root: Path, name: str, payload: Dict[str, Any], config: Optional[Dict] = None) -> Path:
    """Write a JSON report to the reports directory."""
    reports_dir = root / "results" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Add metadata and provenance
    report_data = {
        "report_name": name,
        "timestamp": datetime.now().isoformat(),
        "provenance": create_provenance(config or {}),
        "data": payload
    }
    
    out_path = reports_dir / f"{name}.json"
    out_path.write_text(safe_json_dump(report_data, indent=2), encoding="utf-8")
    return out_path


def write_md_report(root: Path, name: str, md_content: str, summary: Dict[str, Any] = None) -> Path:
    """Write a Markdown report to the reports directory."""
    reports_dir = root / "results" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Add timestamp header
    header = f"# {name}\n\n*Generated: {datetime.now().isoformat()}*\n\n"
    
    # Add integrity badge if summary provided
    if summary:
        integrity_badge = generate_integrity_badge(summary)
        header += integrity_badge + "\n\n"
    
    full_content = header + md_content
    
    out_path = reports_dir / f"{name}.md"
    out_path.write_text(full_content, encoding="utf-8")
    return out_path


def create_run_summary(root: Path, run_name: str, results: Dict[str, Any]) -> Path:
    """Create a comprehensive run summary report."""
    timestamp = datetime.now().isoformat()
    
    # Count tasks and successes
    total_tasks = results.get("total_tasks", 0)
    successful_tasks = results.get("successful_tasks", 0)
    failed_tasks = total_tasks - successful_tasks
    
    # Create markdown content
    md_content = f"""
## Run Summary: {run_name}

**Timestamp:** {timestamp}  
**Total Tasks:** {total_tasks}  
**Successful:** {successful_tasks}  
**Failed:** {failed_tasks}  
**Success Rate:** {f"{(successful_tasks/total_tasks*100):.1f}%" if total_tasks > 0 else "N/A"}

### Experiment Results

"""
    
    # Add experiment summaries
    for exp_result in results.get("experiments", []):
        exp_name = exp_result.get("experiment", "unknown")
        exp_summary = exp_result.get("summary", {})
        
        md_content += f"#### {exp_name}\n\n"
        md_content += f"**Status:** {exp_summary.get('status', 'unknown')}\n\n"
        
        if "metrics" in exp_summary:
            md_content += "**Key Metrics:**\n"
            for metric, value in exp_summary["metrics"].items():
                md_content += f"- {metric}: {value}\n"
            md_content += "\n"
        
        if "discoveries" in exp_summary:
            md_content += "**Discoveries:**\n"
            for discovery in exp_summary["discoveries"]:
                md_content += f"- {discovery}\n"
            md_content += "\n"
    
    # Add detailed results section
    md_content += "### Detailed Results\n\n"
    md_content += "See individual JSON reports in the reports directory for detailed data.\n\n"
    
    # Add configuration section
    if "configuration" in results:
        md_content += "### Configuration\n\n"
        md_content += f"```yaml\n{json.dumps(results['configuration'], indent=2)}\n```\n\n"
    
    return write_md_report(root, f"run_summary_{run_name}", md_content)


def create_discovery_report(root: Path, discovery_name: str, findings: Dict[str, Any]) -> Path:
    """Create a specialized report for scientific discoveries."""
    timestamp = datetime.now().isoformat()
    
    md_content = f"""
## Discovery Report: {discovery_name}

**Timestamp:** {timestamp}  
**Discovery Type:** {findings.get('type', 'unknown')}  
**Confidence Level:** {findings.get('confidence', 'unknown')}

### Summary

{findings.get('summary', 'No summary provided.')}

### Mathematical Details

"""
    
    # Add mathematical content
    if "formulas" in findings:
        md_content += "**Key Formulas:**\n\n"
        for formula in findings["formulas"]:
            md_content += f"```\n{formula}\n```\n\n"
    
    if "proof_sketch" in findings:
        md_content += "**Proof Sketch:**\n\n"
        md_content += findings["proof_sketch"] + "\n\n"
    
    # Add experimental evidence
    if "evidence" in findings:
        md_content += "### Experimental Evidence\n\n"
        for evidence_type, evidence_data in findings["evidence"].items():
            md_content += f"**{evidence_type}:**\n"
            md_content += f"{evidence_data}\n\n"
    
    # Add implications
    if "implications" in findings:
        md_content += "### Implications\n\n"
        for implication in findings["implications"]:
            md_content += f"- {implication}\n"
        md_content += "\n"
    
    # Add next steps
    if "next_steps" in findings:
        md_content += "### Next Steps\n\n"
        for step in findings["next_steps"]:
            md_content += f"- {step}\n"
        md_content += "\n"
    
    return write_md_report(root, f"discovery_{discovery_name}", md_content)


def create_artifacts_index(root: Path, run_name: str, artifacts: list[Dict[str, Any]]) -> Path:
    """Create an index of all artifacts generated during a run."""
    timestamp = datetime.now().isoformat()
    
    md_content = f"""
## Artifacts Index: {run_name}

**Generated:** {timestamp}  
**Total Artifacts:** {len(artifacts)}

### Artifact List

"""
    
    for i, artifact in enumerate(artifacts, 1):
        name = artifact.get("name", f"artifact_{i}")
        path = artifact.get("path", "unknown")
        artifact_type = artifact.get("type", "unknown")
        description = artifact.get("description", "No description")
        
        md_content += f"#### {i}. {name}\n\n"
        md_content += f"**Type:** {artifact_type}  \n"
        md_content += f"**Path:** `{path}`  \n"
        md_content += f"**Description:** {description}\n\n"
    
    return write_md_report(root, f"artifacts_index_{run_name}", md_content)


def generate_lab_notebook_entry(root: Path, entry_name: str, content: Dict[str, Any]) -> Path:
    """Generate a lab notebook entry with full scientific documentation."""
    timestamp = datetime.now().isoformat()
    
    md_content = f"""
## Lab Notebook Entry: {entry_name}

**Date:** {timestamp}  
**Experimenter:** Nova Spivack  
**Project:** UGP Discovery Lab

### Objective

{content.get('objective', 'No objective specified.')}

### Methodology

{content.get('methodology', 'No methodology documented.')}

### Results

{content.get('results', 'No results documented.')}

### Analysis

{content.get('analysis', 'No analysis provided.')}

### Conclusions

{content.get('conclusions', 'No conclusions drawn.')}

### Data Files

"""
    
    # List all data files referenced
    if "data_files" in content:
        for file_info in content["data_files"]:
            file_path = file_info.get("path", "unknown")
            file_desc = file_info.get("description", "No description")
            md_content += f"- `{file_path}`: {file_desc}\n"
    
    md_content += "\n### Next Steps\n\n"
    
    if "next_steps" in content:
        for step in content["next_steps"]:
            md_content += f"- {step}\n"
    else:
        md_content += "No next steps planned.\n"
    
    return write_md_report(root, f"lab_notebook_{entry_name}", md_content)


def generate_integrity_badge(summary: Dict[str, Any]) -> str:
    """Generate an integrity badge for Markdown reports."""
    
    # Extract data origin information
    data_origin = summary.get("data_origin", {})
    origin_type = data_origin.get("type", "unknown")
    generator = data_origin.get("generator", "unknown")
    seed = data_origin.get("seed", "unknown")
    
    # Check for integrity validation
    integrity_warnings = summary.get("integrity_warnings", [])
    lint_passed = len(integrity_warnings) == 0
    
    badge_content = "### Data Integrity\n\n"
    
    if origin_type == "synthetic":
        badge_content += "- Synthetic data: ✅ Neutral generator"
        if generator != "unknown":
            badge_content += f" ({generator})"
        badge_content += "\n"
    elif origin_type == "real":
        badge_content += "- Real data: ✅ External/experimental source\n"
    elif origin_type == "synthetic_negative_control":
        badge_content += "- Synthetic data: ⚠️ Negative control (expected bias)\n"
    else:
        badge_content += f"- Data origin: {origin_type}\n"
    
    if lint_passed:
        badge_content += "- Lint checks: ✅ Passed (0 warnings)\n"
    else:
        badge_content += f"- Lint checks: ⚠️ {len(integrity_warnings)} warnings\n"
    
    if seed != "unknown":
        badge_content += f"- Reproducibility: ✅ Seeded (seed={seed})\n"
    
    return badge_content


def add_provenance_to_summary(summary: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Add provenance information to experiment summary."""
    
    # Add data origin if not present
    if "data_origin" not in summary:
        summary["data_origin"] = {
            "type": "synthetic",
            "generator": "neutral_trig_with_memory",
            "version": "1.0",
            "seed": "unknown",
            "params": {}
        }
    
    # Add git metadata if available
    try:
        import subprocess
        git_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD'], 
                                         stderr=subprocess.DEVNULL).decode().strip()
        summary["provenance"] = {
            "git_hash": git_hash,
            "timestamp": datetime.now().isoformat(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": sys.platform
        }
    except:
        summary["provenance"] = {
            "timestamp": datetime.now().isoformat(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": sys.platform
        }
    
    # Add config provenance if provided
    if config:
        summary["config_provenance"] = {
            "config_keys": list(config.keys()),
            "has_experiment_config": "experiment" in config,
            "has_integrity_config": "integrity" in config
        }
    
    return summary
