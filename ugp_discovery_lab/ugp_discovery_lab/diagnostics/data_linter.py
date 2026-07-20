"""
Data Integrity Linter

This module provides integrity checks to prevent biased data generation
and ensure scientific validity in UGP Discovery Lab experiments.
"""

import re
import ast
import hashlib
from typing import Dict, List, Any, Optional, Union


class DataIntegrityError(Exception):
    """Raised when data integrity checks fail."""
    pass


class DataIntegrityWarning(Exception):
    """Raised when data integrity warnings are detected."""
    pass


def lint_generator(cfg: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
    """
    Lint a data generator configuration for integrity issues.
    
    Args:
        cfg: Configuration dictionary containing generator settings
        context: Context dictionary with seeds and other metadata
        
    Returns:
        List of warning messages. Empty list means no issues detected.
    """
    warnings = []
    
    # 1) Check for forbidden imports in generator code
    warnings.extend(_check_forbidden_imports(cfg))
    
    # 2) Check for suspicious fields in data sections
    warnings.extend(_check_suspicious_fields(cfg))
    
    # 3) Audit seed usage
    warnings.extend(_audit_seeds(context))
    
    # 4) Check for variable dependencies
    warnings.extend(_check_variable_dependencies(cfg))
    
    # 5) Check for hardcoded relationships
    warnings.extend(_check_hardcoded_relationships(cfg))
    
    return warnings


def _check_forbidden_imports(cfg: Dict[str, Any]) -> List[str]:
    """Check for forbidden imports that could introduce bias."""
    warnings = []
    
    forbidden_imports = {
        'from .fit_', 'from .model_', 'from .regression_',
        'from sklearn.linear_model', 'from scipy.optimize',
        'from .coefficient_', 'from .alpha_', 'from .lambda_'
    }
    
    # Check generator code sections
    generator_sections = ['generator', 'data', 'neutral', 'synthesis']
    
    for section in generator_sections:
        section_data = cfg.get(section, {})
        if isinstance(section_data, dict):
            code = section_data.get('code', '')
            if isinstance(code, str):
                for forbidden in forbidden_imports:
                    if forbidden in code:
                        warnings.append(
                            f"Forbidden import '{forbidden}' found in {section} section"
                        )
    
    return warnings


def _check_suspicious_fields(cfg: Dict[str, Any]) -> List[str]:
    """Check for suspicious fields that might indicate bias."""
    warnings = []
    
    suspicious_fields = {
        'alpha', 'lambda', 'lambda_n', 'alpha_n', 'plane', 'lock', 
        'fit', 'model_coeffs', 'coefficient', 'target', 'expected',
        'theoretical', 'formula', 'cos', 'sin_formula'
    }
    
    # Check data-related sections
    data_sections = ['data', 'generator', 'neutral', 'synthesis', 'test_data']
    
    for section in data_sections:
        section_data = cfg.get(section, {})
        if isinstance(section_data, dict):
            found_suspicious = suspicious_fields.intersection(section_data.keys())
            if found_suspicious:
                warnings.append(
                    f"Suspicious fields in {section}: {list(found_suspicious)}"
                )
    
    return warnings


def _audit_seeds(context: Dict[str, Any]) -> List[str]:
    """Audit seed usage for proper randomness control."""
    warnings = []
    
    seeds = context.get('seeds', [])
    if not isinstance(seeds, (list, tuple)):
        warnings.append("Seeds must be list or tuple")
        return warnings
    
    if not seeds:
        warnings.append("No seeds provided - reproducibility not guaranteed")
    
    # Check for suspicious seed computation
    seed_computation = context.get('seed_computation', '')
    if isinstance(seed_computation, str):
        suspicious_patterns = [
            r'seed.*fit', r'seed.*alpha', r'seed.*lambda',
            r'seed.*coefficient', r'seed.*model'
        ]
        for pattern in suspicious_patterns:
            if re.search(pattern, seed_computation, re.IGNORECASE):
                warnings.append(f"Suspicious seed computation: {pattern}")
    
    return warnings


def _check_variable_dependencies(cfg: Dict[str, Any]) -> List[str]:
    """Check for variable dependencies that could introduce bias."""
    warnings = []
    
    # Patterns that indicate dependency creation
    dependency_patterns = [
        r'k_M\s*=\s*k_G\s*\+',  # k_M = k_G + ...
        r'kM\s*=\s*kG\s*\+',    # kM = kG + ...
        r'M\s*=\s*G\s*\+',      # M = G + ...
        r'k_M.*k_G.*k_L',       # k_M involving k_G and k_L
        r'alpha.*k_L',           # alpha * k_L
        r'lambda.*k_L'           # lambda * k_L
    ]
    
    # Check all string fields in config
    for key, value in cfg.items():
        if isinstance(value, str):
            for pattern in dependency_patterns:
                if re.search(pattern, value, re.IGNORECASE):
                    warnings.append(
                        f"Variable dependency pattern '{pattern}' found in {key}"
                    )
        elif isinstance(value, dict):
            # Recursively check nested dictionaries
            for subkey, subvalue in value.items():
                if isinstance(subvalue, str):
                    for pattern in dependency_patterns:
                        if re.search(pattern, subvalue, re.IGNORECASE):
                            warnings.append(
                                f"Variable dependency pattern '{pattern}' found in {key}.{subkey}"
                            )
    
    return warnings


def _check_hardcoded_relationships(cfg: Dict[str, Any]) -> List[str]:
    """Check for hardcoded mathematical relationships."""
    warnings = []
    
    # Mathematical relationship patterns
    relationship_patterns = [
        r'0\.25',  # Quarter-lock
        r'1/4',    # Quarter-lock fraction
        r'2\s*\*\s*cos\s*\(',  # 2*cos(...)
        r'1\s*/\s*\(\s*2\s*\*\s*cos',  # 1/(2*cos(...))
        r'cos\s*\(\s*pi\s*/\s*n\s*\)',  # cos(pi/n)
        r'cos\s*\(\s*π\s*/\s*n\s*\)'    # cos(π/n)
    ]
    
    # Check for hardcoded constants in data generation
    data_sections = ['generator', 'data', 'neutral', 'synthesis']
    
    for section in data_sections:
        section_data = cfg.get(section, {})
        if isinstance(section_data, dict):
            for key, value in section_data.items():
                if isinstance(value, (str, int, float)):
                    value_str = str(value)
                    for pattern in relationship_patterns:
                        if re.search(pattern, value_str, re.IGNORECASE):
                            warnings.append(
                                f"Hardcoded relationship pattern '{pattern}' found in {section}.{key}"
                            )
    
    return warnings


def validate_data_integrity(cfg: Dict[str, Any], context: Dict[str, Any], 
                          fail_on_warning: bool = True) -> None:
    """
    Validate data integrity and raise exceptions if issues are found.
    
    Args:
        cfg: Configuration dictionary
        context: Context dictionary
        fail_on_warning: If True, raise exception on warnings. If False, only log.
        
    Raises:
        DataIntegrityError: If critical integrity issues are found
        DataIntegrityWarning: If warnings are found and fail_on_warning=True
    """
    warnings = lint_generator(cfg, context)
    
    if warnings:
        if fail_on_warning:
            raise DataIntegrityError(
                f"Data integrity issues detected:\n" + "\n".join(f"- {w}" for w in warnings)
            )
        else:
            # Log warnings but don't fail
            import logging
            logger = logging.getLogger(__name__)
            for warning in warnings:
                logger.warning(f"Data integrity warning: {warning}")


def compute_generator_signature(generator_code: str) -> str:
    """
    Compute a signature for generator code to track versions.
    
    Args:
        generator_code: The generator code as a string
        
    Returns:
        SHA256 hash of the generator code
    """
    return hashlib.sha256(generator_code.encode('utf-8')).hexdigest()[:16]


def get_neutral_generator_info() -> Dict[str, Any]:
    """
    Get information about approved neutral generators.
    
    Returns:
        Dictionary with generator information
    """
    return {
        "neutral_trig_with_memory": {
            "version": "1.0",
            "description": "Trigonometric evolution with temporal memory",
            "independence_guarantee": "Variables generated independently with different frequencies",
            "no_relationships": "No mathematical relationships between variables assumed"
        },
        "neutral_multiscale_noise": {
            "version": "1.0", 
            "description": "Multi-scale noise patterns with realistic evolution",
            "independence_guarantee": "Independent noise processes for each variable",
            "no_relationships": "No conservation laws or algebraic relationships built in"
        }
    }


# CLI integration function
def cli_integrity_check(config_path: str, context: Optional[Dict] = None) -> bool:
    """
    CLI function to check data integrity of a configuration file.
    
    Args:
        config_path: Path to configuration file
        context: Optional context dictionary
        
    Returns:
        True if integrity checks pass, False otherwise
    """
    import yaml
    
    try:
        with open(config_path, 'r') as f:
            cfg = yaml.safe_load(f)
        
        if context is None:
            context = {}
        
        warnings = lint_generator(cfg, context)
        
        if warnings:
            print("Data integrity issues detected:")
            for warning in warnings:
                print(f"  ⚠️  {warning}")
            return False
        else:
            print("✅ Data integrity checks passed")
            return True
            
    except Exception as e:
        print(f"❌ Error checking data integrity: {e}")
        return False


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
        success = cli_integrity_check(config_path)
        sys.exit(0 if success else 1)
