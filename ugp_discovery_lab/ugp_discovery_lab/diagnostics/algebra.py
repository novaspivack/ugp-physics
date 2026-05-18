# ugp_discovery_lab/diagnostics/algebra.py
from __future__ import annotations
from typing import List, Dict, Any
import math
import numpy as np

# Try to import high-precision libraries
try:
    import mpmath as mp
    HAS_MPMATH = True
except ImportError:
    HAS_MPMATH = False
    mp = None

try:
    import sympy as sp
    from sympy import Matrix, nsimplify, symbols, sympify
    HAS_SYMPY = True
except ImportError:
    HAS_SYMPY = False
    sp = None


def set_precision(bits: int = 200):
    """Set mpmath precision (bits)."""
    if not HAS_MPMATH:
        raise ImportError("mpmath not available for high-precision arithmetic")
    mp.mp.dps = int(bits / 3.321928094887362)  # bits -> decimal digits (~)


def simple_pslq(x, maxcoeff=20, tolerance=1e-10):
    """
    Simple PSLQ implementation using numpy for integer relation detection.
    Returns integer coefficients if a relation is found.
    """
    import numpy as np
    
    x = np.array(x, dtype=float)
    n = len(x)
    
    if n < 2:
        return None
    
    # Normalize the vector
    x_norm = np.linalg.norm(x)
    if x_norm < 1e-15:
        return None
    
    x = x / x_norm
    
    # Create augmented matrix [x^T; I]
    A = np.vstack([x.reshape(1, -1), np.eye(n)])
    
    # QR decomposition
    Q, R = np.linalg.qr(A.T)
    
    # Look for small elements in the last row
    last_row = R[-1, :]
    
    # Check if any element is close to zero
    min_abs = np.min(np.abs(last_row))
    if min_abs < tolerance:
        # Find the index of the smallest element
        min_idx = np.argmin(np.abs(last_row))
        
        # Get the corresponding column from Q
        coeffs = Q[:, min_idx]
        
        # Round to integers
        coeffs_int = np.round(coeffs).astype(int)
        
        # Check if coefficients are within bounds
        if np.max(np.abs(coeffs_int)) <= maxcoeff:
            return coeffs_int.tolist()
    
    return None


def eval_basis(basis_exprs: List[str], subs: Dict[str, float | int] | None = None) -> List[float]:
    """
    Evaluate a list of basis expressions (strings) into high-precision values.
    Allowed atoms: pi, cos, sin, log, sqrt; supports simple 'n' variables in subs.
    """
    if subs is None: 
        subs = {}
    
    vals = []
    for expr in basis_exprs:
        e = expr.strip()
        
        if HAS_MPMATH:
            # Use mpmath for high precision
            safe = {"mp": mp}
            # Inject numeric substitutions (e.g. {'n': 37})
            safe.update({k: mp.mpf(v) for k, v in subs.items()})
            # Allowed functions/consts
            safe.update({
                "pi": mp.pi, "sin": mp.sin, "cos": mp.cos, 
                "log": mp.log, "sqrt": mp.sqrt, "exp": mp.exp
            })
            try:
                val = eval(e, {"__builtins__": {}}, safe)
                vals.append(float(val))
            except Exception:
                # Fallback to regular evaluation
                try:
                    val = float(eval(e, {"__builtins__": {}}, {
                        "pi": math.pi, "sin": math.sin, "cos": math.cos,
                        "log": math.log, "sqrt": math.sqrt, "exp": math.exp,
                        **{k: float(v) for k, v in subs.items()}
                    }))
                    vals.append(val)
                except Exception:
                    vals.append(float('nan'))
        else:
            # Fallback to regular math
            try:
                val = float(eval(e, {"__builtins__": {}}, {
                    "pi": math.pi, "sin": math.sin, "cos": math.cos,
                    "log": math.log, "sqrt": math.sqrt, "exp": math.exp,
                    **{k: float(v) for k, v in subs.items()}
                }))
                vals.append(val)
            except Exception:
                vals.append(float('nan'))
    
    return vals


def pslq_fit(value: float | str, basis_exprs: List[str], bits: int = 200, 
             subs: Dict[str, float | int] | None = None, max_coeff: int = 20) -> Dict[str, Any]:
    """
    Try to express 'value' as a linear combination of basis_exprs with integer coefficients via PSLQ.
    Returns coefficients, residual, and a human-readable expression if found.
    """
    try:
        # Set precision if mpmath available
        if HAS_MPMATH:
            set_precision(bits)
        
        if isinstance(value, str):
            v = eval_basis([value], subs=subs)[0]
        else:
            v = float(value)
        
        basis = eval_basis(basis_exprs, subs=subs)
        
        # Form vector (basis..., -v)
        x = basis + [-v]
        
        # Use our simple PSLQ implementation
        coeffs = simple_pslq(x, maxcoeff=max_coeff, tolerance=1e-10)

        if coeffs is None or len(coeffs) != (len(basis) + 1):
            return {"ok": False, "coeffs": None, "residual": None, "expr": None, "error": "PSLQ failed"}

        # Compute residual
        cB = coeffs[:-1]
        cV = coeffs[-1]
        
        # Compute approximation
        approx = sum(b * c for b, c in zip(basis, cB))
        residual = abs(approx + cV)
        
        # Expression string
        expr_terms = [f"{c}*({e})" for c, e in zip(cB, basis_exprs) if c != 0]
        expr = " + ".join(expr_terms)
        if cV != 0:
            expr = f"{expr} + ({cV}) ≈ 0"
        else:
            expr = f"{expr} ≈ 0"
        
        return {
            "ok": True, 
            "coeffs": coeffs, 
            "residual": residual, 
            "expr": expr,
            "error": None
        }
    
    except Exception as e:
        return {"ok": False, "coeffs": None, "residual": None, "expr": None, "error": str(e)}


def test_dihedral_consistency(alpha_observed: float, n: int, precision_bits: int = 200) -> Dict[str, Any]:
    """
    Test if observed alpha is consistent with dihedral group theory.
    Tests against basis: {1, sin(π/n), cos(π/n), 1/(2cos(π/n))}
    """
    basis = [
        "1",
        "sin(pi/n)", 
        "cos(pi/n)",
        "1/(2*cos(pi/n))"
    ]
    
    subs = {"n": float(n)}
    
    result = pslq_fit(alpha_observed, basis, bits=precision_bits, subs=subs, max_coeff=20)
    
    if result["ok"]:
        # Check if the result is meaningful (not just constant term)
        coeffs = result["coeffs"]
        non_constant_terms = [c for i, c in enumerate(coeffs[:-1]) if c != 0 and i > 0]
        
        result["has_non_constant"] = len(non_constant_terms) > 0
        result["dihedral_order"] = n
        result["theoretical_value"] = {
            "sin_pi_n": math.sin(math.pi / n),
            "cos_pi_n": math.cos(math.pi / n), 
            "inv_2cos_pi_n": 1 / (2 * math.cos(math.pi / n))
        }
    
    return result


def bootstrap_confidence_interval(values: List[float], confidence: float = 0.95, 
                                 n_bootstrap: int = 1000) -> List[float]:
    """Compute bootstrap confidence interval for a list of values."""
    if len(values) < 2:
        return [values[0] if values else 0, values[0] if values else 0]
    
    np.random.seed(42)  # For reproducibility
    bootstrapped_means = []
    
    for _ in range(n_bootstrap):
        sample = np.random.choice(values, size=len(values), replace=True)
        bootstrapped_means.append(np.mean(sample))
    
    bootstrapped_means = np.sort(bootstrapped_means)
    
    alpha = 1 - confidence
    lower_idx = int(alpha/2 * len(bootstrapped_means))
    upper_idx = int((1 - alpha/2) * len(bootstrapped_means))
    
    return [float(bootstrapped_means[lower_idx]), float(bootstrapped_means[upper_idx])]
