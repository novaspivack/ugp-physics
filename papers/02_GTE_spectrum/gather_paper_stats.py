#!/usr/bin/env python3
"""
GTE Particle Spectrum Paper - Statistics Gathering Script

This script collects all the statistics needed for updating the paper with new discovery and analytics data.
It analyzes the latest discovery run and analytics outputs to provide comprehensive statistics for paper updates.

Usage:
    python gather_paper_stats.py

Output:
    - Comprehensive statistics summary for paper updates
    - Particle breakdown by type and classification
    - Analytics results summary
    - Validation checks for data quality
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

# ugp-physics repository root (parent of discovery_engine/). Walk upward from this file
# until we see requirements.txt + discovery_engine/ (works from discovery_engine/ or papers/02_GTE_spectrum/;
# avoids mis-detecting when a duplicate candidates.csv sits beside this script).
def _find_repo_root() -> Path:
    p = Path(__file__).resolve().parent
    for _ in range(10):
        if (p / "requirements.txt").is_file() and (p / "discovery_engine").is_dir():
            return p
        p = p.parent
    raise RuntimeError("ugp-physics repo root not found (expected requirements.txt + discovery_engine/)")

_REPO_ROOT = _find_repo_root()


def _load_json_file(fp: Path) -> Optional[Any]:
    """Load JSON if present and materialized (not a Git LFS pointer stub)."""
    if not fp.is_file():
        return None
    raw = fp.read_text(encoding="utf-8").strip()
    if raw.startswith("version https://git-lfs.github.com"):
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def load_discovery_data() -> Tuple[Optional[pd.DataFrame], Optional[Dict[str, Any]]]:
    """Load frozen discovery data shipped with ugp-physics (`discovery_engine/candidates.csv`)."""

    candidates_file = _REPO_ROOT / "discovery_engine" / "candidates.csv"
    if not candidates_file.is_file():
        print(f"❌ Bundled candidates not found: {candidates_file}")
        return None, None

    print(f"📁 Using bundled candidates: {candidates_file}")
    candidates_df = pd.read_csv(candidates_file, low_memory=False)
    print(f"📊 Loaded {len(candidates_df):,} candidates")

    report_data: Dict[str, Any] = {}
    manifest = _REPO_ROOT / "papers" / "02_GTE_spectrum" / "manifest.json"
    mdata = _load_json_file(manifest)
    if mdata is not None:
        report_data["manifest"] = mdata
    elif manifest.is_file():
        report_data["manifest_note"] = "manifest.json missing or Git LFS pointer only; run `git lfs pull`."

    return candidates_df, report_data


def load_analytics_data() -> Dict[str, Any]:
    """Load frozen analytics JSON from `papers/02_GTE_spectrum/` (same artifacts as the paper)."""

    spectrum = _REPO_ROOT / "papers" / "02_GTE_spectrum"
    analytics_data: Dict[str, Any] = {}
    if not spectrum.is_dir():
        print(f"❌ Paper spectrum directory not found: {spectrum}")
        return {}

    for key, name in (
        ("law_family", "law_family.json"),
        ("oscillation", "oscillation_fdr_mass.json"),
        ("curves", "curves.json"),
    ):
        fp = spectrum / name
        payload = _load_json_file(fp)
        if payload is not None:
            analytics_data[key] = payload
            print(f"📁 Loaded analytics artifact: {name}")
        else:
            print(f"⚠️  Skipping {name} (missing or Git LFS pointer — run `git lfs pull`).")

    overlay = spectrum / "top_curves_overlay.md"
    if overlay.is_file():
        raw_md = overlay.read_text(encoding="utf-8").strip()
        if not raw_md.startswith("version https://git-lfs.github.com"):
            analytics_data["report"] = raw_md

    return analytics_data

def analyze_particle_breakdown(candidates_df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze particle breakdown by type and classification."""
    
    stats = {}
    
    # Basic counts
    stats['total_candidates'] = len(candidates_df)
    stats['unique_particles'] = len(candidates_df.drop_duplicates(subset=['id']))
    
    # Particle type breakdown
    if 'particle_type' in candidates_df.columns:
        type_counts = candidates_df['particle_type'].value_counts()
        stats['particle_types'] = type_counts.to_dict()
    
    # Classification breakdown
    if 'classification_color' in candidates_df.columns:
        color_counts = candidates_df['classification_color'].value_counts()
        stats['classifications'] = color_counts.to_dict()
    
    # Mass range analysis
    if 'mass_mev_calibrated' in candidates_df.columns:
        mass_col = 'mass_mev_calibrated'
    elif 'mass_mev' in candidates_df.columns:
        mass_col = 'mass_mev'
    else:
        mass_col = None
    
    if mass_col:
        masses = candidates_df[mass_col].dropna()
        stats['mass_stats'] = {
            'min_mass_mev': float(masses.min()),
            'max_mass_mev': float(masses.max()),
            'mean_mass_mev': float(masses.mean()),
            'median_mass_mev': float(masses.median())
        }
        
        # Mass range breakdown
        stats['mass_ranges'] = {
            'sub_ev': len(masses[masses < 0.001]),
            'ev_scale': len(masses[(masses >= 0.001) & (masses < 1)]),
            'kev_scale': len(masses[(masses >= 1) & (masses < 1000)]),
            'mev_scale': len(masses[(masses >= 1000) & (masses < 1e6)]),
            'gev_scale': len(masses[masses >= 1e6])
        }
    
    # GTE compliance analysis
    if 'gte_score' in candidates_df.columns:
        gte_scores = candidates_df['gte_score'].dropna()
        stats['gte_stats'] = {
            'mean_gte': float(gte_scores.mean()),
            'median_gte': float(gte_scores.median()),
            'perfect_gte': len(gte_scores[gte_scores >= 0.999]),
            'high_gte': len(gte_scores[gte_scores >= 0.9]),
            'medium_gte': len(gte_scores[(gte_scores >= 0.7) & (gte_scores < 0.9)]),
            'low_gte': len(gte_scores[gte_scores < 0.7])
        }
    
    return stats

def analyze_analytics_results(analytics_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze analytics results for paper statistics."""
    
    stats = {}
    
    # Law family parameters
    if 'law_family' in analytics_data:
        law_family = analytics_data['law_family']
        stats['law_family'] = {
            'B_parameter': law_family.get('B', 'N/A'),
            'D_parameter': law_family.get('D', 'N/A'),
            'inliers': law_family.get('inliers', 'N/A'),
            'total_points': law_family.get('total_points', 'N/A')
        }
    
    # Oscillation analysis
    if 'oscillation' in analytics_data:
        oscillation = analytics_data['oscillation']
        # Handle different oscillation data formats
        if isinstance(oscillation, dict):
            stats['oscillation'] = {
                'peak_period': oscillation.get('peak_period', 'N/A'),
                'z_score': oscillation.get('z_score', 'N/A'),
                'significance': oscillation.get('significance', 'N/A')
            }
        elif isinstance(oscillation, list) and len(oscillation) > 0:
            # If it's a list, take the first item
            first_osc = oscillation[0] if isinstance(oscillation[0], dict) else {}
            stats['oscillation'] = {
                'peak_period': first_osc.get('peak_period', 'N/A'),
                'z_score': first_osc.get('z_score', 'N/A'),
                'significance': first_osc.get('significance', 'N/A')
            }
        else:
            stats['oscillation'] = {
                'peak_period': 'N/A',
                'z_score': 'N/A',
                'significance': 'N/A'
            }
    
    # Curve analysis
    if 'curves' in analytics_data:
        curves = analytics_data['curves']
        if isinstance(curves, list):
            stats['curves'] = {
                'total_curves': len(curves),
                'top_curves': len([c for c in curves if isinstance(c, dict) and c.get('score', 0) > 0.8]),
            }
        elif isinstance(curves, dict):
            stats['curves'] = {
                'total_curves': len(curves),
                'top_curves': 0,
                'note': 'curves payload is a dict (frozen export); list metrics skipped',
            }
        else:
            stats['curves'] = {'total_curves': 0, 'top_curves': 0}
    
    return stats

def validate_data_quality(candidates_df: pd.DataFrame) -> Dict[str, Any]:
    """Validate data quality and identify potential issues."""
    
    issues = []
    warnings = []
    
    # Check for missing data
    missing_mass = candidates_df['mass_mev_calibrated'].isna().sum() if 'mass_mev_calibrated' in candidates_df.columns else 0
    if missing_mass > 0:
        warnings.append(f"Missing mass data for {missing_mass} particles")
    
    # Check for extreme mass values
    if 'mass_mev_calibrated' in candidates_df.columns:
        masses = candidates_df['mass_mev_calibrated'].dropna()
        extreme_high = len(masses[masses > 1e12])  # > 1 TeV
        extreme_low = len(masses[masses < 1e-6])   # < 1 neV
        
        if extreme_high > 0:
            warnings.append(f"Found {extreme_high} particles with extremely high masses (> 1 TeV)")
        if extreme_low > 0:
            warnings.append(f"Found {extreme_low} particles with extremely low masses (< 1 neV)")
    
    # Check GTE compliance distribution
    if 'gte_score' in candidates_df.columns:
        gte_scores = candidates_df['gte_score'].dropna()
        low_compliance = len(gte_scores[gte_scores < 0.5])
        if low_compliance > len(gte_scores) * 0.1:  # More than 10% low compliance
            warnings.append(f"High number of low GTE compliance particles: {low_compliance}")
    
    # Check for duplicate particles
    duplicates = len(candidates_df) - len(candidates_df.drop_duplicates(subset=['id']))
    if duplicates > 0:
        issues.append(f"Found {duplicates} duplicate particle IDs")
    
    return {
        'issues': issues,
        'warnings': warnings,
        'data_quality': 'GOOD' if len(issues) == 0 else 'ISSUES_FOUND'
    }

def generate_paper_stats() -> Dict[str, Any]:
    """Generate comprehensive statistics for paper updates."""
    
    print("🔍 Gathering paper statistics...")
    
    # Load data
    candidates_df, discovery_report = load_discovery_data()
    if candidates_df is None:
        return {'error': 'Could not load discovery data'}
    
    analytics_data = load_analytics_data()
    
    # Analyze data
    particle_stats = analyze_particle_breakdown(candidates_df)
    analytics_stats = analyze_analytics_results(analytics_data)
    quality_check = validate_data_quality(candidates_df)
    
    # Combine all statistics
    paper_stats = {
        'discovery_run': discovery_report,
        'particle_breakdown': particle_stats,
        'analytics_results': analytics_stats,
        'data_quality': quality_check,
        'summary': {
            'total_particles': particle_stats.get('total_candidates', 0),
            'unique_particles': particle_stats.get('unique_particles', 0),
            'mass_range_mev': f"{particle_stats.get('mass_stats', {}).get('min_mass_mev', 'N/A'):.1f} - {particle_stats.get('mass_stats', {}).get('max_mass_mev', 'N/A'):.1f}",
            'mean_gte_score': particle_stats.get('gte_stats', {}).get('mean_gte', 'N/A'),
            'data_quality': quality_check['data_quality']
        }
    }
    
    return paper_stats

def print_statistics_summary(stats: Dict[str, Any]):
    """Print a formatted statistics summary."""
    
    print("\n" + "="*80)
    print("📊 GTE PARTICLE SPECTRUM PAPER - STATISTICS SUMMARY")
    print("="*80)
    
    # Discovery run info
    if 'discovery_run' in stats:
        print(f"\n🔬 DISCOVERY RUN:")
        print(f"   Protocol: {stats['discovery_run'].get('protocol', 'N/A')}")
        total_analyzed = stats['discovery_run'].get('total_analyzed', 'N/A')
        high_confidence = stats['discovery_run'].get('high_confidence', 'N/A')
        print(f"   Total Analyzed: {total_analyzed:,}" if isinstance(total_analyzed, int) else f"   Total Analyzed: {total_analyzed}")
        print(f"   High Confidence: {high_confidence:,}" if isinstance(high_confidence, int) else f"   High Confidence: {high_confidence}")
    
    # Particle breakdown
    if 'particle_breakdown' in stats:
        pb = stats['particle_breakdown']
        print(f"\n📈 PARTICLE BREAKDOWN:")
        print(f"   Total Candidates: {pb.get('total_candidates', 0):,}")
        print(f"   Unique Particles: {pb.get('unique_particles', 0):,}")
        
        if 'mass_stats' in pb:
            ms = pb['mass_stats']
            print(f"   Mass Range: {ms.get('min_mass_mev', 0):.1f} - {ms.get('max_mass_mev', 0):.1f} MeV")
            print(f"   Mean Mass: {ms.get('mean_mass_mev', 0):.1f} MeV")
        
        if 'mass_ranges' in pb:
            mr = pb['mass_ranges']
            print(f"   Mass Distribution:")
            print(f"     Sub-eV: {mr.get('sub_ev', 0)}")
            print(f"     eV-scale: {mr.get('ev_scale', 0)}")
            print(f"     keV-scale: {mr.get('kev_scale', 0)}")
            print(f"     MeV-scale: {mr.get('mev_scale', 0)}")
            print(f"     GeV-scale: {mr.get('gev_scale', 0)}")
        
        if 'gte_stats' in pb:
            gs = pb['gte_stats']
            print(f"   GTE Compliance:")
            print(f"     Mean Score: {gs.get('mean_gte', 0):.3f}")
            print(f"     Perfect (≥0.999): {gs.get('perfect_gte', 0)}")
            print(f"     High (≥0.9): {gs.get('high_gte', 0)}")
    
    # Analytics results
    if 'analytics_results' in stats:
        ar = stats['analytics_results']
        print(f"\n📊 ANALYTICS RESULTS:")
        
        if 'law_family' in ar:
            lf = ar['law_family']
            print(f"   Law Family Parameters:")
            print(f"     B = {lf.get('B_parameter', 'N/A')}")
            print(f"     D = {lf.get('D_parameter', 'N/A')}")
            print(f"     Inliers: {lf.get('inliers', 'N/A')}")
        
        if 'oscillation' in ar:
            osc = ar['oscillation']
            print(f"   Oscillation Analysis:")
            print(f"     Peak Period: {osc.get('peak_period', 'N/A')}")
            print(f"     Z-Score: {osc.get('z_score', 'N/A')}")
    
    # Data quality
    if 'data_quality' in stats:
        dq = stats['data_quality']
        print(f"\n🔍 DATA QUALITY: {dq.get('data_quality', 'UNKNOWN')}")
        
        if dq.get('issues'):
            print(f"   Issues:")
            for issue in dq['issues']:
                print(f"     ❌ {issue}")
        
        if dq.get('warnings'):
            print(f"   Warnings:")
            for warning in dq['warnings']:
                print(f"     ⚠️  {warning}")
    
    print("\n" + "="*80)
    print("✅ Statistics gathering complete!")
    print("="*80)

def main():
    """Main function to run the statistics gathering."""
    
    try:
        # Generate statistics
        stats = generate_paper_stats()
        
        if 'error' in stats:
            print(f"❌ Error: {stats['error']}")
            return
        
        # Print summary
        print_statistics_summary(stats)
        
        # Save next to this script (works regardless of CWD)
        output_file = Path(__file__).resolve().parent / "paper_statistics_summary.json"
        with open(output_file, 'w') as f:
            json.dump(stats, f, indent=2, default=str)
        
        print(f"\n💾 Statistics saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error during statistics gathering: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
