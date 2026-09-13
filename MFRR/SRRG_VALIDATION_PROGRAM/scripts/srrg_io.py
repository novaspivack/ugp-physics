"""
SRRG I/O Utilities
Reference: SRRG_VALIDATION_PROGRAM/1_2_DATA_ARTIFACT_CATALOG.md

Data loading, validation, saving with checksums and manifest management.

Author: AI Assistant
Date: 2025-01-27
Cross-Reference: SRRG_VALIDATION_PROGRAM/1_2_DATA_ARTIFACT_CATALOG.md
"""

import json
import hashlib
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime

from srrg_core import GTETriple, triple_from_dict

# =============================================================================
# Section A: Data Loading
# =============================================================================

def load_canonical_sm_triples(path: Path) -> List[Dict]:
    """
    Load canonical SM triples from JSON.
    
    Args:
        path: Path to canonical_sm_triples.json
    
    Returns:
        List of particle dictionaries with triples and PDG data
    """
    with open(path, 'r') as f:
        data = json.load(f)
    
    return data["particles"]


def load_pdg_reference(path: Path) -> pd.DataFrame:
    """
    Load PDG reference masses from CSV.
    
    Args:
        path: Path to pdg_2024_masses.csv
    
    Returns:
        DataFrame with particle data
    """
    return pd.read_csv(path)


def load_ame_data(path: Path) -> pd.DataFrame:
    """
    Load preprocessed AME nuclear data.
    
    Args:
        path: Path to ame_2020_processed.csv
    
    Returns:
        DataFrame with nuclear binding energies
    """
    return pd.read_csv(path)


def load_json_data(path: Path) -> Dict:
    """
    Load arbitrary JSON file with error handling.
    
    Args:
        path: Path to JSON file
    
    Returns:
        Parsed JSON as dictionary
    """
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}")
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {path}")


# =============================================================================
# Section B: Data Validation
# =============================================================================

def validate_triple_data(particles: List[Dict]) -> bool:
    """
    Validate canonical SM triples data structure.
    
    Checks:
    - Required fields present
    - Triple components are integers
    - PDG masses are positive (or zero for massless)
    - Generation is valid (0, 1, 2, 3)
    
    Args:
        particles: List of particle dictionaries
    
    Returns:
        True if valid, raises ValueError otherwise
    """
    required_fields = ["name", "pdg_id", "triple", "sector", "generation", "mass_pdg_mev"]
    
    for i, p in enumerate(particles):
        # Check required fields
        for field in required_fields:
            if field not in p:
                raise ValueError(f"Particle {i} missing required field: {field}")
        
        # Check triple structure
        triple = p["triple"]
        if not all(k in triple for k in ["a", "b", "c", "g"]):
            raise ValueError(f"Particle {p['name']} has incomplete triple")
        
        # Check types
        if not all(isinstance(triple[k], int) for k in ["a", "b", "c", "g"]):
            raise ValueError(f"Particle {p['name']} triple components must be integers")
        
        # Check generation
        if p["generation"] not in {0, 1, 2, 3}:
            raise ValueError(f"Particle {p['name']} has invalid generation: {p['generation']}")
        
        # Check mass
        if p["mass_pdg_mev"] < 0:
            raise ValueError(f"Particle {p['name']} has negative mass")
    
    return True


def compute_sha256(file_path: Path) -> str:
    """
    Compute SHA256 checksum of file.
    
    Args:
        file_path: Path to file
    
    Returns:
        Hex digest of SHA256 hash
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


# =============================================================================
# Section C: Data Saving with Manifest
# =============================================================================

def save_json_with_checksum(data: Dict, 
                           path: Path,
                           pretty: bool = True) -> str:
    """
    Save JSON data with optional pretty printing.
    
    Args:
        data: Dictionary to save
        path: Output path
        pretty: Use indentation (default True)
    
    Returns:
        SHA256 checksum of saved file
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        if pretty:
            json.dump(data, f, indent=2)
        else:
            json.dump(data, f)
    
    return compute_sha256(path)


def update_data_manifest(manifest_path: Path,
                        file_info: Dict):
    """
    Update or create data manifest with file metadata.
    
    Args:
        manifest_path: Path to DATA_MANIFEST.json
        file_info: Dictionary with file metadata
    """
    # Load existing manifest or create new
    if manifest_path.exists():
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
    else:
        manifest = {
            "manifest_version": "1.0",
            "created": datetime.now().isoformat(),
            "files": []
        }
    
    # Update or append file info
    file_name = file_info["name"]
    found = False
    for i, f in enumerate(manifest["files"]):
        if f["name"] == file_name:
            manifest["files"][i] = file_info
            found = True
            break
    
    if not found:
        manifest["files"].append(file_info)
    
    # Save manifest
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)


def save_results_with_manifest(data: Dict,
                               path: Path,
                               manifest_path: Path,
                               description: str = ""):
    """
    Save results JSON and update manifest automatically.
    
    Args:
        data: Results dictionary
        path: Output JSON path
        manifest_path: Path to DATA_MANIFEST.json
        description: Description of the data
    """
    # Save data
    checksum = save_json_with_checksum(data, path)
    
    # Create file info
    file_size = path.stat().st_size
    
    file_info = {
        "name": path.name,
        "path": str(path.relative_to(manifest_path.parent.parent)),
        "description": description,
        "format": "JSON",
        "sha256": checksum,
        "size_bytes": file_size,
        "created": datetime.now().isoformat(),
        "status": "complete"
    }
    
    # Update manifest
    update_data_manifest(manifest_path, file_info)


# =============================================================================
# Section D: CSV Utilities
# =============================================================================

def save_csv(data: List[Dict], 
            path: Path,
            fieldnames: Optional[List[str]] = None):
    """
    Save list of dictionaries to CSV.
    
    Args:
        data: List of dictionaries
        path: Output CSV path
        fieldnames: Optional field order (default: keys from first dict)
    """
    if not data:
        raise ValueError("Cannot save empty data to CSV")
    
    if fieldnames is None:
        fieldnames = list(data[0].keys())
    
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


# =============================================================================
# Section E: Conversion Utilities
# =============================================================================

def particles_to_triples(particles: List[Dict]) -> List[GTETriple]:
    """
    Convert particle dictionaries to GTETriple objects.
    
    Args:
        particles: List of particle dicts from canonical_sm_triples.json
    
    Returns:
        List of GTETriple objects
    """
    triples = []
    for p in particles:
        t_dict = p["triple"]
        triple = GTETriple(
            a=t_dict["a"],
            b=t_dict["b"],
            c=t_dict["c"],
            g=t_dict["g"],
            name=p["name"]
        )
        triples.append(triple)
    
    return triples


def triples_to_particle_dicts(triples: List[GTETriple],
                              pdg_masses: Optional[Dict[str, float]] = None) -> List[Dict]:
    """
    Convert GTETriple objects back to particle dictionaries.
    
    Args:
        triples: List of GTETriple objects
        pdg_masses: Optional dict mapping names to PDG masses
    
    Returns:
        List of particle dictionaries
    """
    particles = []
    for triple in triples:
        p_dict = {
            "name": triple.name,
            "triple": {
                "a": triple.a,
                "b": triple.b,
                "c": triple.c,
                "g": triple.g
            },
            "generation": triple.g
        }
        
        if pdg_masses and triple.name in pdg_masses:
            p_dict["mass_pdg_mev"] = pdg_masses[triple.name]
        
        particles.append(p_dict)
    
    return particles


if __name__ == "__main__":
    # Unit tests
    print("SRRG I/O Module — Unit Tests")
    print("=" * 60)
    
    # Test 1: Load canonical SM triples
    data_dir = Path(__file__).parent.parent / "data"
    triples_path = data_dir / "canonical_sm_triples.json"
    
    if triples_path.exists():
        particles = load_canonical_sm_triples(triples_path)
        print(f"\n1. Loaded {len(particles)} SM particles from {triples_path.name}")
        
        # Test 2: Validate
        try:
            validate_triple_data(particles)
            print("2. Validation: PASS")
        except ValueError as e:
            print(f"2. Validation: FAIL ({e})")
        
        # Test 3: Convert to triples
        triples = particles_to_triples(particles)
        print(f"3. Converted to {len(triples)} GTETriple objects")
        print(f"   First: {triples[0]}")
        
        # Test 4: Compute checksum
        checksum = compute_sha256(triples_path)
        print(f"4. File checksum: {checksum[:16]}...")
    else:
        print(f"\n⚠️  {triples_path} not found")
        print("   Run from SRRG_VALIDATION_PROGRAM directory")
    
    print("\n" + "=" * 60)
    print("✅ I/O module tests complete")

