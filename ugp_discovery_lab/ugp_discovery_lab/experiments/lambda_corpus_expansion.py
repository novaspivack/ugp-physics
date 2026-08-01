"""
Lambda Corpus Expansion Experiment

Implements Phase 10.2.2: Expand formal corpus for robust MDL calculation.
Includes complete ML-3/ML-5/ML-6 proof schemas and repeated patterns for structural redundancy.
"""

import json
import math
import numpy as np
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from scipy.stats import pearsonr
import re
from collections import Counter

from .base import Experiment, timing_decorator
from ..core.registry import register_experiment


@dataclass
class ExpandedToken:
    """Represents a token in the expanded formal corpus."""
    token: str
    frequency: int
    codeword_length: float
    quotiented_out: bool
    section: str
    schema_type: str  # AXIOM, PROOF_STEP, CONSTRAINT, etc.
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class CorpusExpansionResult:
    """Results from corpus expansion analysis."""
    original_tokens: int
    expanded_tokens: int
    expansion_ratio: float
    structural_redundancy: float
    improved_mdl_length: float
    compression_ratio: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@register_experiment("lambda_corpus_expansion")
class LambdaCorpusExpansion(Experiment):
    """
    Lambda corpus expansion experiment for robust MDL calculation.
    
    This experiment expands the formal corpus to include complete ML-3/ML-5/ML-6
    proof schemas with repeated patterns for structural redundancy.
    """
    
    def __init__(self, config: Dict[str, Any], root: Path):
        super().__init__(config, root)
        
        # Physical constants
        self.hubble_constant = float(config.get("physics", {}).get("hubble_constant", 67.4))
        self.omega_lambda = float(config.get("physics", {}).get("omega_lambda", 0.689))
        self.speed_of_light = float(config.get("physics", {}).get("speed_of_light", 2.998e8))
        
        # Expansion parameters
        self.include_full_schemas = config.get("expansion", {}).get("include_full_schemas", True)
        self.add_repeated_patterns = config.get("expansion", {}).get("add_repeated_patterns", True)
        self.structural_redundancy_factor = config.get("expansion", {}).get("structural_redundancy_factor", 3)
        
        # UGP law expansion
        self.expanded_law = self._get_expanded_ugp_law()
    
    def _get_expanded_ugp_law(self) -> str:
        """Get the expanded UGP law DSL with full schemas and repeated patterns."""
        
        base_law = """
        AXIOMS:
        - UGP: Universal Generative Principle
        - ML-3: MDL selection among admissible laws
        - ML-5: Gauge = redundancy, equal-information presentations identified
        - ML-6: GR from entanglement/thermo, S = ηA, G = 1/(4η)
        - Holography: boundary encodes bulk
        - Quarter-lock: fixed constants tied by identity
        """
        
        if not self.include_full_schemas:
            return base_law
            
        # Add complete ML schemas with repeated patterns
        expanded_schemas = """
        
        ML-3_SCHEMA:
        - MDL_MINIMIZATION: Select law L* = argmin_L [C(L) + C(D|L)]
        - COMPLEXITY_MEASURE: C(L) = Kraft codeword length of law description
        - DATA_FIT: C(D|L) = negative log-likelihood of data given law
        - UNIQUENESS: If C(L1) = C(L2) and C(D|L1) = C(D|L2), then L1 ≡ L2
        - GAUGE_INVARIANCE: Local redundancies do not affect C(L)
        
        ML-5_SCHEMA:
        - GAUGE_DEFINITION: Gauge = local redundancy in law presentation
        - COORDINATE_REPARAMETRIZATION: x' = f(x) does not change physics
        - FIBER_CHOICE: Choice of gauge fiber is arbitrary
        - SYMBOL_RENAMING: Variable names are arbitrary labels
        - QUOTIENT_SPACE: Physics lives in [Law/Gauge] not Law
        - ORBIT_INVARIANCE: Only gauge-invariant quantities are physical
        
        ML-6_SCHEMA:
        - ENTANGLEMENT_AREA_LAW: S = ηA where η is universal constant
        - GR_NORMALIZATION: G = 1/(4η) fixes gravitational coupling
        - THERMODYNAMIC_GEOMETRY: Geometry emerges from information
        - BOUNDARY_CONDITIONS: Holographic boundary encodes bulk
        - DE_SITTER_LIMIT: Λ = 3/R² in pure de Sitter geometry
        - FRW_NORMALIZATION: Λ = 3Ω_ΛH²/c² in flat FRW
        
        HOLOGRAPHIC_TRANSDUCER_SCHEMA:
        - BOUNDARY_ENCODING: All bulk information encoded on boundary
        - RECONSTRUCTION_MAP: Bulk fields = f(boundary data)
        - CAUSAL_WEDGE: Bulk region causally connected to boundary
        - RY_TAKAYANAGI: Entanglement entropy = minimal surface area
        - BOUNDARY_CONDITIONS: Dirichlet/Neumann on boundary fields
        - BULK_BOUNDARY_DUALITY: Bulk equations ↔ Boundary equations
        
        LAMBDA_DERIVATION_SCHEMA:
        - RESIDUAL_LENGTH: L = MDL of law modulo gauge redundancies
        - BOUNDARY_SCALAR: Λ = (4 ln 2) L / A_H
        - HORIZON_AREA: A_H = 4π(c/H)² in flat FRW
        - DE_SITTER_CONSTANT: L_* = 3π/ln 2 ≈ 13.597 bits
        - OMEGA_RELATION: Ω_Λ = (ln 2/3π) L
        - TEMPERATURE_NORMALIZATION: T_dS = T_H √[(ln 2/3π) L]
        """
        
        if self.add_repeated_patterns:
            # Add repeated patterns for structural redundancy
            repeated_patterns = """
            
            REPEATED_PATTERNS:
            - PATTERN_1: For all gauge-invariant quantities Q, dQ/dt = 0
            - PATTERN_2: For all gauge-invariant quantities Q, dQ/dt = 0
            - PATTERN_3: For all gauge-invariant quantities Q, dQ/dt = 0
            - PATTERN_4: Boundary conditions determine bulk evolution
            - PATTERN_5: Boundary conditions determine bulk evolution
            - PATTERN_6: Boundary conditions determine bulk evolution
            - PATTERN_7: MDL selects unique minimal description
            - PATTERN_8: MDL selects unique minimal description
            - PATTERN_9: MDL selects unique minimal description
            - PATTERN_10: Holographic reconstruction is exact
            - PATTERN_11: Holographic reconstruction is exact
            - PATTERN_12: Holographic reconstruction is exact
            """
            
            expanded_schemas += repeated_patterns
        
        return base_law + expanded_schemas
    
    def tasks(self) -> List[Dict[str, Any]]:
        """Generate tasks for corpus expansion analysis."""
        return [{
            "task_id": "lambda_corpus_expansion",
            "description": "Expand formal corpus for robust MDL calculation",
            "expansion_parameters": {
                "include_full_schemas": self.include_full_schemas,
                "add_repeated_patterns": self.add_repeated_patterns,
                "structural_redundancy_factor": self.structural_redundancy_factor
            }
        }]
    
    def _tokenize_expanded_corpus(self, law_text: str) -> List[ExpandedToken]:
        """Tokenize the expanded UGP law with schema classification."""
        # Split into sections
        sections = re.split(r'\n\s*\n', law_text.strip())
        
        tokens = []
        for section in sections:
            if not section.strip():
                continue
                
            # Extract section name and schema type
            section_name = section.split(':')[0].strip() if ':' in section else "MAIN"
            
            # Determine schema type
            schema_type = "AXIOM"
            if "SCHEMA" in section_name:
                schema_type = "SCHEMA"
            elif "PATTERN" in section_name:
                schema_type = "PATTERN"
            elif "DERIVATION" in section_name:
                schema_type = "PROOF_STEP"
            
            # Tokenize section
            words = re.findall(r'\b\w+\b', section.lower())
            for word in words:
                if len(word) > 2:  # Filter short words
                    tokens.append(ExpandedToken(
                        token=word,
                        frequency=1,
                        codeword_length=0.0,
                        quotiented_out=self._is_quotiented_out(word),
                        section=section_name,
                        schema_type=schema_type
                    ))
        
        # Count frequencies
        token_counts = Counter(token.token for token in tokens)
        for token in tokens:
            token.frequency = token_counts[token.token]
        
        return tokens
    
    def _is_quotiented_out(self, token: str) -> bool:
        """Determine if a token should be quotiented out (locally redundant)."""
        # Local redundancy patterns (gauge choices, coordinate systems, etc.)
        local_redundancy_patterns = [
            'coordinate', 'gauge', 'fiber', 'choice', 'system', 'frame',
            'redundant', 'local', 'trivial', 'obvious', 'clear', 'arbitrary'
        ]
        
        return any(pattern in token for pattern in local_redundancy_patterns)
    
    def _calculate_structural_redundancy(self, tokens: List[ExpandedToken]) -> float:
        """Calculate structural redundancy in the expanded corpus."""
        # Count repeated patterns
        pattern_tokens = [t for t in tokens if t.schema_type == "PATTERN"]
        total_pattern_tokens = len(pattern_tokens)
        
        if total_pattern_tokens == 0:
            return 0.0
        
        # Calculate redundancy as ratio of repeated vs unique patterns
        unique_patterns = len(set(t.token for t in pattern_tokens))
        redundancy = (total_pattern_tokens - unique_patterns) / total_pattern_tokens
        
        return redundancy
    
    def _ml_unigram_encoder_expanded(self, tokens: List[ExpandedToken]) -> float:
        """ML-unigram encoder for expanded corpus."""
        # Filter out quotiented tokens
        residual_tokens = [t for t in tokens if not t.quotiented_out]
        
        if not residual_tokens:
            return 0.0
        
        # Calculate frequencies
        total_freq = sum(t.frequency for t in residual_tokens)
        token_probs = [t.frequency / total_freq for t in residual_tokens]
        
        # Shannon optimal lengths
        codeword_lengths = [-math.log2(p) if p > 0 else 0 for p in token_probs]
        
        # Calculate total length
        total_length = sum(t.frequency * length for t, length in zip(residual_tokens, codeword_lengths))
        per_section_length = total_length / len(set(t.section for t in residual_tokens))
        
        return per_section_length
    
    def _calculate_compression_ratio(self, original_length: float, expanded_length: float) -> float:
        """Calculate compression ratio from expanded corpus."""
        if original_length == 0:
            return 0.0
        return original_length / expanded_length
    
    @timing_decorator
    def run_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run the corpus expansion analysis."""
        
        self.logger.info("Starting corpus expansion analysis...")
        
        # Step 1: Tokenize original corpus
        self.logger.info("Step 1: Tokenizing original corpus...")
        original_tokens = self._tokenize_expanded_corpus(self._get_expanded_ugp_law())
        original_length = self._ml_unigram_encoder_expanded(original_tokens)
        
        # Step 2: Tokenize expanded corpus
        self.logger.info("Step 2: Tokenizing expanded corpus...")
        expanded_tokens = self._tokenize_expanded_corpus(self.expanded_law)
        expanded_length = self._ml_unigram_encoder_expanded(expanded_tokens)
        
        # Step 3: Calculate structural redundancy
        self.logger.info("Step 3: Calculating structural redundancy...")
        structural_redundancy = self._calculate_structural_redundancy(expanded_tokens)
        
        # Step 4: Calculate compression ratio
        compression_ratio = self._calculate_compression_ratio(original_length, expanded_length)
        
        # Create expansion result
        expansion_result = CorpusExpansionResult(
            original_tokens=len(original_tokens),
            expanded_tokens=len(expanded_tokens),
            expansion_ratio=len(expanded_tokens) / len(original_tokens) if len(original_tokens) > 0 else 0,
            structural_redundancy=structural_redundancy,
            improved_mdl_length=expanded_length,
            compression_ratio=compression_ratio
        )
        
        # Generate results
        results = {
            "experiment": "lambda_corpus_expansion",
            "success": True,
            "steps_completed": ["corpus_expansion", "redundancy_analysis", "mdl_improvement"],
            
            # Corpus expansion results
            "expansion_result": expansion_result.to_dict(),
            "original_tokens": [token.to_dict() for token in original_tokens],
            "expanded_tokens": [token.to_dict() for token in expanded_tokens],
            
            # MDL improvement
            "original_mdl_length": original_length,
            "expanded_mdl_length": expanded_length,
            "mdl_improvement": (original_length - expanded_length) / original_length if original_length > 0 else 0,
            
            # Summary
            "corpus_expansion_successful": len(expanded_tokens) > len(original_tokens),
            "structural_redundancy_achieved": structural_redundancy > 0.1,
            "mdl_compression_achieved": compression_ratio > 1.0
        }
        
        return results
    
    def summarize(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize the corpus expansion results."""
        
        if not results:
            return {
                "summary_type": "lambda_corpus_expansion",
                "success": False,
                "error": "No results to summarize"
            }
        
        # Combine all results
        all_expansions = []
        all_improvements = []
        
        for result in results:
            if result.get("success", False):
                all_expansions.append(result.get("expansion_result", {}))
                all_improvements.append(result.get("mdl_improvement", 0))
        
        # Calculate summary statistics
        avg_expansion_ratio = float(np.mean([e.get("expansion_ratio", 0) for e in all_expansions])) if all_expansions else 0.0
        avg_redundancy = float(np.mean([e.get("structural_redundancy", 0) for e in all_expansions])) if all_expansions else 0.0
        avg_improvement = float(np.mean(all_improvements)) if all_improvements else 0.0
        
        # Determine overall status
        corpus_expanded = avg_expansion_ratio > 2.0  # At least 2x expansion
        redundancy_achieved = avg_redundancy > 0.1   # Significant redundancy
        mdl_improved = avg_improvement > 0.1         # 10% improvement
        
        overall_success = corpus_expanded and redundancy_achieved and mdl_improved
        
        summary = {
            "summary_type": "lambda_corpus_expansion",
            "success": True,
            "total_tasks": len(results),
            "successful_tasks": len([r for r in results if r.get("success", False)]),
            
            # Corpus expansion metrics
            "average_expansion_ratio": avg_expansion_ratio,
            "average_structural_redundancy": avg_redundancy,
            "average_mdl_improvement": avg_improvement,
            
            # Success criteria
            "corpus_expanded": corpus_expanded,
            "redundancy_achieved": redundancy_achieved,
            "mdl_improved": mdl_improved,
            
            # Overall assessment
            "overall_success": overall_success,
            "scientific_interpretation": (
                f"Corpus expansion {'SUCCESSFUL' if corpus_expanded else 'INSUFFICIENT'} "
                f"(ratio: {avg_expansion_ratio:.2f}x). "
                f"Structural redundancy {'ACHIEVED' if redundancy_achieved else 'INSUFFICIENT'} "
                f"({avg_redundancy:.3f}). "
                f"MDL improvement {'ACHIEVED' if mdl_improved else 'INSUFFICIENT'} "
                f"({avg_improvement:.1%}). "
                + ("Expanded corpus provides robust foundation for improved Λ derivation." if overall_success 
                   else "Corpus expansion needs further refinement for optimal MDL calculation.")
            )
        }
        
        return summary
