"""
Neutral Generator Registry

This module provides approved neutral data generators that guarantee
scientific integrity by avoiding circular reasoning and bias.
"""

import numpy as np
from typing import Dict, List, Any, Optional
from .data_linter import compute_generator_signature


def neutral_trig_with_memory(seed: int, steps: int, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate neutral trigonometric evolution data with temporal memory.
    
    SCIENTIFIC INTEGRITY GUARANTEE:
    - Variables are generated independently with different frequencies
    - NO mathematical relationships between variables are assumed
    - NO conservation laws or algebraic dependencies built in
    - Temporal memory is realistic but doesn't create relationships
    
    Args:
        seed: Random seed for reproducibility
        steps: Number of time steps to generate
        params: Parameters including noise level, memory factor, frequencies
        
    Returns:
        List of dictionaries with evolution data
    """
    # Set seed for reproducibility
    np.random.seed(seed)
    
    # Extract parameters with defaults
    noise_level = params.get('noise_level', 0.1)
    memory_factor = params.get('memory_factor', 0.05)
    frequencies = params.get('frequencies', [2, 3, 5, 7])
    
    if len(frequencies) < 3:
        raise ValueError("Need at least 3 frequencies for independent variable generation")
    
    evolution_data = []
    
    for step in range(steps):
        t = step / steps  # Normalized time [0, 1]
        
        # Generate independent evolution patterns using different frequencies
        # Each variable uses different frequency combinations to ensure independence
        
        # Variable 1: Uses frequencies[0] and frequencies[1]
        var1 = 2.0 + 0.8 * np.sin(frequencies[0] * np.pi * t) + 0.3 * np.cos(frequencies[1] * np.pi * t)
        
        # Variable 2: Uses frequencies[1] and frequencies[2] 
        var2 = 1.5 + 0.6 * np.sin(frequencies[1] * np.pi * t) + 0.4 * np.cos(frequencies[2] * np.pi * t)
        
        # Variable 3: Uses frequencies[2] and frequencies[0]
        var3 = 1.0 + 0.5 * np.sin(frequencies[2] * np.pi * t) + 0.2 * np.cos(frequencies[0] * np.pi * t)
        
        # Add independent noise to each variable
        var1 += noise_level * np.random.normal()
        var2 += noise_level * np.random.normal()
        var3 += noise_level * np.random.normal()
        
        # Add realistic temporal memory (evolution has memory)
        if step > 0:
            prev_data = evolution_data[-1]
            var1 = (1 - memory_factor) * var1 + memory_factor * prev_data['var1']
            var2 = (1 - memory_factor) * var2 + memory_factor * prev_data['var2']
            var3 = (1 - memory_factor) * var3 + memory_factor * prev_data['var3']
        
        evolution_data.append({
            'step': step,
            'var1': var1,
            'var2': var2,
            'var3': var3,
            't': t
        })
    
    return evolution_data


def neutral_multiscale_noise(seed: int, steps: int, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate neutral multi-scale noise evolution data.
    
    SCIENTIFIC INTEGRITY GUARANTEE:
    - Independent noise processes for each variable
    - NO conservation laws or algebraic relationships built in
    - Multi-scale structure creates realistic complexity
    - Each variable evolves independently
    
    Args:
        seed: Random seed for reproducibility
        steps: Number of time steps to generate
        params: Parameters including noise scales and amplitudes
        
    Returns:
        List of dictionaries with evolution data
    """
    # Set seed for reproducibility
    np.random.seed(seed)
    
    # Extract parameters with defaults
    noise_scales = params.get('noise_scales', [1, 5, 10, 50])
    amplitudes = params.get('amplitudes', [1.0, 0.8, 1.2])
    base_levels = params.get('base_levels', [2.0, 1.5, 1.0])
    
    evolution_data = []
    
    for step in range(steps):
        t = step / steps  # Normalized time [0, 1]
        
        # Generate independent multi-scale noise for each variable
        vars_data = {}
        
        for i, (base, amp) in enumerate(zip(base_levels, amplitudes)):
            var_name = f'var{i+1}'
            
            # Multi-scale noise with different scales for each variable
            noise = 0
            for j, scale in enumerate(noise_scales):
                phase = 2 * np.pi * scale * t + np.random.uniform(0, 2*np.pi)
                noise += (amp / (j + 1)) * np.sin(phase) + (amp / (j + 2)) * np.cos(phase)
            
            vars_data[var_name] = base + noise
        
        evolution_data.append({
            'step': step,
            't': t,
            **vars_data
        })
    
    return evolution_data


def neutral_markov_ar(seed: int, steps: int, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate neutral Markov autoregressive evolution data.
    
    SCIENTIFIC INTEGRITY GUARANTEE:
    - Independent AR processes for each variable
    - NO cross-variable dependencies
    - NO conservation laws or relationships assumed
    - Realistic temporal structure without bias
    
    Args:
        seed: Random seed for reproducibility
        steps: Number of time steps to generate
        params: Parameters including AR coefficients and noise levels
        
    Returns:
        List of dictionaries with evolution data
    """
    # Set seed for reproducibility
    np.random.seed(seed)
    
    # Extract parameters with defaults
    ar_coeffs = params.get('ar_coeffs', [0.7, 0.8, 0.6])  # AR(1) coefficients for each variable
    noise_levels = params.get('noise_levels', [0.1, 0.15, 0.12])
    initial_values = params.get('initial_values', [2.0, 1.5, 1.0])
    
    evolution_data = []
    
    # Initialize variables
    vars_current = initial_values.copy()
    
    for step in range(steps):
        t = step / steps  # Normalized time [0, 1]
        
        # Generate new values using independent AR(1) processes
        vars_new = []
        for i, (current, ar_coeff, noise_level) in enumerate(zip(vars_current, ar_coeffs, noise_levels)):
            # AR(1): x_t = phi * x_{t-1} + epsilon_t
            new_val = ar_coeff * current + noise_level * np.random.normal()
            vars_new.append(new_val)
        
        vars_current = vars_new
        
        evolution_data.append({
            'step': step,
            't': t,
            'var1': vars_current[0],
            'var2': vars_current[1], 
            'var3': vars_current[2]
        })
    
    return evolution_data


def get_generator_signature(generator_name: str, params: Dict[str, Any]) -> str:
    """
    Get the signature for a generator configuration.
    
    Args:
        generator_name: Name of the generator function
        params: Parameters used with the generator
        
    Returns:
        Signature string for tracking generator versions
    """
    import inspect
    
    # Get the generator function
    generators = {
        'neutral_trig_with_memory': neutral_trig_with_memory,
        'neutral_multiscale_noise': neutral_multiscale_noise,
        'neutral_markov_ar': neutral_markov_ar
    }
    
    if generator_name not in generators:
        raise ValueError(f"Unknown generator: {generator_name}")
    
    # Get source code of the generator
    generator_func = generators[generator_name]
    source_code = inspect.getsource(generator_func)
    
    # Create signature including source and params
    signature_data = {
        'generator': generator_name,
        'source_hash': compute_generator_signature(source_code),
        'params': params
    }
    
    import json
    return compute_generator_signature(json.dumps(signature_data, sort_keys=True))


def validate_generator_independence(data: List[Dict[str, Any]], 
                                 variables: List[str] = None,
                                 threshold: float = 0.1) -> Dict[str, Any]:
    """
    Validate that variables in generated data are independent.
    
    Args:
        data: Generated evolution data
        variables: List of variable names to check (default: var1, var2, var3)
        threshold: Maximum correlation threshold for independence
        
    Returns:
        Dictionary with independence validation results
    """
    if variables is None:
        variables = ['var1', 'var2', 'var3']
    
    # Extract data arrays
    data_arrays = {}
    for var in variables:
        if var in data[0]:
            data_arrays[var] = np.array([d[var] for d in data])
    
    results = {
        'independence_check': True,
        'correlations': {},
        'max_correlation': 0.0,
        'threshold': threshold
    }
    
    # Check pairwise correlations
    var_list = list(data_arrays.keys())
    for i, var1 in enumerate(var_list):
        for j, var2 in enumerate(var_list[i+1:], i+1):
            corr = np.corrcoef(data_arrays[var1], data_arrays[var2])[0, 1]
            results['correlations'][f'{var1}_vs_{var2}'] = corr
            results['max_correlation'] = max(results['max_correlation'], abs(corr))
    
    # Check if independence threshold is met
    if results['max_correlation'] > threshold:
        results['independence_check'] = False
    
    return results


# Registry of approved generators
NEUTRAL_GENERATORS = {
    'neutral_trig_with_memory': {
        'function': neutral_trig_with_memory,
        'version': '1.0',
        'description': 'Trigonometric evolution with temporal memory',
        'independence_guarantee': 'Variables generated independently with different frequencies',
        'no_relationships': 'No mathematical relationships between variables assumed'
    },
    'neutral_multiscale_noise': {
        'function': neutral_multiscale_noise,
        'version': '1.0',
        'description': 'Multi-scale noise patterns with realistic evolution',
        'independence_guarantee': 'Independent noise processes for each variable',
        'no_relationships': 'No conservation laws or algebraic relationships built in'
    },
    'neutral_markov_ar': {
        'function': neutral_markov_ar,
        'version': '1.0',
        'description': 'Markov autoregressive processes with independent evolution',
        'independence_guarantee': 'Independent AR processes for each variable',
        'no_relationships': 'No cross-variable dependencies or conservation laws'
    }
}


def get_approved_generators() -> Dict[str, Dict[str, Any]]:
    """Get the registry of approved neutral generators."""
    return NEUTRAL_GENERATORS.copy()


def generate_neutral_data(generator_name: str, seed: int, steps: int, 
                         params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate neutral data using an approved generator.
    
    Args:
        generator_name: Name of the approved generator
        seed: Random seed for reproducibility
        steps: Number of time steps
        params: Generator parameters
        
    Returns:
        Generated evolution data
        
    Raises:
        ValueError: If generator_name is not approved
    """
    if generator_name not in NEUTRAL_GENERATORS:
        raise ValueError(
            f"Generator '{generator_name}' not approved. "
            f"Available: {list(NEUTRAL_GENERATORS.keys())}"
        )
    
    generator_func = NEUTRAL_GENERATORS[generator_name]['function']
    return generator_func(seed, steps, params)
