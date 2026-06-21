#!/usr/bin/env python3
"""
DynamicBraidAnalyzer.py - Advanced capsule for analyzing dynamic braid properties

This capsule analyzes the time-series evolution of braids to extract dynamic invariants
that may explain the 32% information gap in electric charge prediction.

Part of Project 2c: Foundational Fortification of the Braid Atlas
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from scipy import signal, fft
from scipy.stats import entropy
import matplotlib.pyplot as plt
from pathlib import Path

@dataclass
class BraidTimeseries:
    """Container for braid evolution data"""
    braid_id: str
    timesteps: np.ndarray
    strand_positions: np.ndarray  # Shape: (timesteps, strands, dimensions)
    field_values: np.ndarray      # Shape: (timesteps, fields)
    stability_metrics: Dict[str, float]
    metadata: Dict[str, any]

@dataclass
class DynamicInvariants:
    """Container for computed dynamic invariants"""
    braid_id: str
    oscillation_frequencies: List[float]
    dominant_frequency: float
    frequency_entropy: float
    mean_lifetime: float
    stability_index: float
    computational_irreducibility: float
    dynamic_complexity: float
    field_correlation_matrix: np.ndarray
    temporal_variance: float
    cross_strand_interactions: List[float]

class DynamicBraidAnalyzer:
    """
    Advanced analyzer for extracting dynamic invariants from braid evolution data.
    
    This analyzer addresses the 32% information gap in electric charge prediction
    by examining the dynamic properties of braid evolution.
    """
    
    def __init__(self, sampling_rate: float = 1.0, min_frequency: float = 0.01):
        """
        Initialize the dynamic braid analyzer.
        
        Args:
            sampling_rate: Temporal sampling rate for frequency analysis
            min_frequency: Minimum frequency threshold for analysis
        """
        self.sampling_rate = sampling_rate
        self.min_frequency = min_frequency
        self.frequency_resolution = 0.001
        
    def analyze_oscillation_frequencies(self, braid_timeseries: BraidTimeseries) -> Dict[str, float]:
        """
        Extract dominant oscillation frequencies from braid evolution.
        
        Args:
            braid_timeseries: Time-series data of braid evolution
            
        Returns:
            Dictionary containing frequency analysis results
        """
        timesteps = braid_timeseries.timesteps
        strand_positions = braid_timeseries.strand_positions
        
        # Compute frequency spectrum for each strand
        frequencies = []
        dominant_frequencies = []
        
        for strand_idx in range(strand_positions.shape[1]):
            # Extract position data for this strand
            strand_data = strand_positions[:, strand_idx, :]
            
            # Compute power spectral density
            for dim in range(strand_data.shape[1]):
                signal_data = strand_data[:, dim]
                
                # Apply FFT to get frequency spectrum
                freqs = fft.fftfreq(len(signal_data), d=1.0/self.sampling_rate)
                fft_values = fft.fft(signal_data)
                power_spectrum = np.abs(fft_values) ** 2
                
                # Find dominant frequencies above threshold
                valid_freqs = freqs[freqs >= self.min_frequency]
                valid_power = power_spectrum[freqs >= self.min_frequency]
                
                if len(valid_freqs) > 0:
                    # Find peaks in power spectrum
                    peaks, _ = signal.find_peaks(valid_power, height=np.max(valid_power) * 0.1)
                    
                    if len(peaks) > 0:
                        dominant_freq = valid_freqs[peaks[np.argmax(valid_power[peaks])]]
                        dominant_frequencies.append(dominant_freq)
                        frequencies.extend(valid_freqs[peaks])
        
        # Compute frequency statistics
        if frequencies:
            freq_entropy = entropy(np.histogram(frequencies, bins=50)[0] + 1e-10)
            dominant_freq = np.mean(dominant_frequencies) if dominant_frequencies else 0.0
        else:
            freq_entropy = 0.0
            dominant_freq = 0.0
        
        return {
            'dominant_frequency': dominant_freq,
            'frequency_entropy': freq_entropy,
            'num_frequencies': len(frequencies),
            'frequency_variance': np.var(frequencies) if frequencies else 0.0
        }
    
    def compute_lifetime_metrics(self, braid_timeseries: BraidTimeseries) -> Dict[str, float]:
        """
        Calculate stability and decay characteristics of the braid.
        
        Args:
            braid_timeseries: Time-series data of braid evolution
            
        Returns:
            Dictionary containing lifetime analysis results
        """
        timesteps = braid_timeseries.timesteps
        strand_positions = braid_timeseries.strand_positions
        
        # Compute stability metrics
        position_variance = np.var(strand_positions, axis=0)
        mean_variance = np.mean(position_variance)
        
        # Compute temporal correlation
        temporal_corr = np.corrcoef(timesteps, np.mean(strand_positions, axis=(1,2)))[0,1]
        
        # Estimate lifetime from stability metrics
        stability_index = 1.0 / (1.0 + mean_variance)
        mean_lifetime = len(timesteps) * stability_index
        
        # Compute decay rate
        if len(timesteps) > 1:
            position_energy = np.sum(strand_positions ** 2, axis=(1,2))
            decay_rate = np.polyfit(timesteps, position_energy, 1)[0]
        else:
            decay_rate = 0.0
        
        return {
            'mean_lifetime': mean_lifetime,
            'stability_index': stability_index,
            'decay_rate': abs(decay_rate),
            'temporal_correlation': abs(temporal_corr),
            'position_variance': mean_variance
        }
    
    def measure_computational_irreducibility(self, braid_timeseries: BraidTimeseries) -> Dict[str, float]:
        """
        Quantify the dynamic complexity and computational irreducibility of the braid.
        
        Args:
            braid_timeseries: Time-series data of braid evolution
            
        Returns:
            Dictionary containing complexity metrics
        """
        timesteps = braid_timeseries.timesteps
        strand_positions = braid_timeseries.strand_positions
        field_values = braid_timeseries.field_values
        
        # Compute information-theoretic complexity
        position_entropy = entropy(np.histogram(strand_positions.flatten(), bins=100)[0] + 1e-10)
        
        # Compute mutual information between strands
        mutual_information = 0.0
        if strand_positions.shape[1] > 1:
            for i in range(strand_positions.shape[1]):
                for j in range(i+1, strand_positions.shape[1]):
                    strand_i = strand_positions[:, i, :].flatten()
                    strand_j = strand_positions[:, j, :].flatten()
                    
                    # Compute mutual information
                    joint_hist, _, _ = np.histogram2d(strand_i, strand_j, bins=50)
                    joint_prob = joint_hist / np.sum(joint_hist)
                    
                    if np.sum(joint_prob) > 0:
                        mi = entropy(joint_prob.flatten() + 1e-10)
                        mutual_information += mi
        
        # Compute field complexity
        field_entropy = entropy(np.histogram(field_values.flatten(), bins=100)[0] + 1e-10)
        
        # Compute overall dynamic complexity
        dynamic_complexity = position_entropy + field_entropy + mutual_information
        
        # Compute computational irreducibility index
        irreducibility_index = dynamic_complexity / len(timesteps)
        
        return {
            'computational_irreducibility': irreducibility_index,
            'dynamic_complexity': dynamic_complexity,
            'position_entropy': position_entropy,
            'field_entropy': field_entropy,
            'mutual_information': mutual_information
        }
    
    def extract_dynamic_invariants(self, braid_timeseries: BraidTimeseries) -> DynamicInvariants:
        """
        Generate comprehensive dynamic feature vector for the braid.
        
        Args:
            braid_timeseries: Time-series data of braid evolution
            
        Returns:
            Complete set of dynamic invariants
        """
        # Analyze oscillation frequencies
        freq_analysis = self.analyze_oscillation_frequencies(braid_timeseries)
        
        # Compute lifetime metrics
        lifetime_metrics = self.compute_lifetime_metrics(braid_timeseries)
        
        # Measure computational irreducibility
        complexity_metrics = self.measure_computational_irreducibility(braid_timeseries)
        
        # Compute field correlation matrix
        field_values = braid_timeseries.field_values
        if field_values.shape[1] > 1:
            field_correlation_matrix = np.corrcoef(field_values.T)
        else:
            field_correlation_matrix = np.array([[1.0]])
        
        # Compute temporal variance
        temporal_variance = np.var(braid_timeseries.strand_positions, axis=0).mean()
        
        # Compute cross-strand interactions
        strand_positions = braid_timeseries.strand_positions
        cross_strand_interactions = []
        if strand_positions.shape[1] > 1:
            for i in range(strand_positions.shape[1]):
                for j in range(i+1, strand_positions.shape[1]):
                    interaction = np.mean(np.abs(strand_positions[:, i, :] - strand_positions[:, j, :]))
                    cross_strand_interactions.append(interaction)
        
        return DynamicInvariants(
            braid_id=braid_timeseries.braid_id,
            oscillation_frequencies=[freq_analysis['dominant_frequency']],
            dominant_frequency=freq_analysis['dominant_frequency'],
            frequency_entropy=freq_analysis['frequency_entropy'],
            mean_lifetime=lifetime_metrics['mean_lifetime'],
            stability_index=lifetime_metrics['stability_index'],
            computational_irreducibility=complexity_metrics['computational_irreducibility'],
            dynamic_complexity=complexity_metrics['dynamic_complexity'],
            field_correlation_matrix=field_correlation_matrix,
            temporal_variance=temporal_variance,
            cross_strand_interactions=cross_strand_interactions
        )
    
    def analyze_multiple_braids(self, braid_timeseries_list: List[BraidTimeseries]) -> pd.DataFrame:
        """
        Analyze multiple braids and return feature matrix.
        
        Args:
            braid_timeseries_list: List of braid time-series data
            
        Returns:
            DataFrame with dynamic features for all braids
        """
        results = []
        
        for braid_ts in braid_timeseries_list:
            invariants = self.extract_dynamic_invariants(braid_ts)
            
            # Convert to feature vector
            feature_vector = {
                'braid_id': invariants.braid_id,
                'dominant_frequency': invariants.dominant_frequency,
                'frequency_entropy': invariants.frequency_entropy,
                'mean_lifetime': invariants.mean_lifetime,
                'stability_index': invariants.stability_index,
                'computational_irreducibility': invariants.computational_irreducibility,
                'dynamic_complexity': invariants.dynamic_complexity,
                'temporal_variance': invariants.temporal_variance,
                'num_cross_strand_interactions': len(invariants.cross_strand_interactions),
                'mean_cross_strand_interaction': np.mean(invariants.cross_strand_interactions) if invariants.cross_strand_interactions else 0.0,
                'field_correlation_mean': np.mean(invariants.field_correlation_matrix),
                'field_correlation_std': np.std(invariants.field_correlation_matrix)
            }
            
            results.append(feature_vector)
        
        return pd.DataFrame(results)
    
    def visualize_dynamic_analysis(self, braid_timeseries: BraidTimeseries, 
                                 output_path: Optional[Path] = None) -> None:
        """
        Create visualization of dynamic analysis results.
        
        Args:
            braid_timeseries: Time-series data to visualize
            output_path: Optional path to save visualization
        """
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # Plot strand positions over time
        strand_positions = braid_timeseries.strand_positions
        timesteps = braid_timeseries.timesteps
        
        for strand_idx in range(min(3, strand_positions.shape[1])):
            axes[0, 0].plot(timesteps, strand_positions[:, strand_idx, 0], 
                          label=f'Strand {strand_idx}', alpha=0.7)
        axes[0, 0].set_title('Strand Positions Over Time')
        axes[0, 0].set_xlabel('Time')
        axes[0, 0].set_ylabel('Position')
        axes[0, 0].legend()
        
        # Plot field values
        field_values = braid_timeseries.field_values
        for field_idx in range(min(3, field_values.shape[1])):
            axes[0, 1].plot(timesteps, field_values[:, field_idx], 
                          label=f'Field {field_idx}', alpha=0.7)
        axes[0, 1].set_title('Field Values Over Time')
        axes[0, 1].set_xlabel('Time')
        axes[0, 1].set_ylabel('Field Value')
        axes[0, 1].legend()
        
        # Plot frequency spectrum
        invariants = self.extract_dynamic_invariants(braid_timeseries)
        axes[1, 0].bar(['Dominant Freq', 'Freq Entropy'], 
                      [invariants.dominant_frequency, invariants.frequency_entropy])
        axes[1, 0].set_title('Frequency Analysis')
        axes[1, 0].set_ylabel('Value')
        
        # Plot complexity metrics
        complexity_metrics = ['Stability', 'Lifetime', 'Irreducibility', 'Complexity']
        complexity_values = [invariants.stability_index, invariants.mean_lifetime,
                           invariants.computational_irreducibility, invariants.dynamic_complexity]
        axes[1, 1].bar(complexity_metrics, complexity_values)
        axes[1, 1].set_title('Complexity Metrics')
        axes[1, 1].set_ylabel('Value')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.show()

def create_sample_braid_timeseries(braid_id: str, duration: int = 1000) -> BraidTimeseries:
    """
    Create sample braid time-series data for testing.
    
    Args:
        braid_id: Identifier for the braid
        duration: Number of timesteps
        
    Returns:
        Sample BraidTimeseries object
    """
    timesteps = np.arange(duration)
    
    # Create sample strand positions (3 strands, 3D)
    strand_positions = np.zeros((duration, 3, 3))
    for strand in range(3):
        for dim in range(3):
            # Add oscillation with different frequencies
            freq = 0.1 + strand * 0.05 + dim * 0.02
            strand_positions[:, strand, dim] = np.sin(2 * np.pi * freq * timesteps) + np.random.normal(0, 0.1, duration)
    
    # Create sample field values (2 fields)
    field_values = np.zeros((duration, 2))
    field_values[:, 0] = np.sin(2 * np.pi * 0.05 * timesteps) + np.random.normal(0, 0.1, duration)
    field_values[:, 1] = np.cos(2 * np.pi * 0.03 * timesteps) + np.random.normal(0, 0.1, duration)
    
    # Create stability metrics
    stability_metrics = {
        'mean_energy': np.mean(np.sum(strand_positions ** 2, axis=(1,2))),
        'energy_variance': np.var(np.sum(strand_positions ** 2, axis=(1,2))),
        'strand_separation': np.mean(np.linalg.norm(strand_positions[:, 0, :] - strand_positions[:, 1, :], axis=1))
    }
    
    metadata = {
        'num_strands': 3,
        'dimensions': 3,
        'num_fields': 2,
        'sampling_rate': 1.0
    }
    
    return BraidTimeseries(
        braid_id=braid_id,
        timesteps=timesteps,
        strand_positions=strand_positions,
        field_values=field_values,
        stability_metrics=stability_metrics,
        metadata=metadata
    )

def main():
    """Test the DynamicBraidAnalyzer with sample data."""
    print("🧪 Testing DynamicBraidAnalyzer...")
    
    # Create sample braid data
    sample_braid = create_sample_braid_timeseries("test_braid_001")
    
    # Initialize analyzer
    analyzer = DynamicBraidAnalyzer()
    
    # Extract dynamic invariants
    invariants = analyzer.extract_dynamic_invariants(sample_braid)
    
    print(f"✅ Analysis complete for braid: {invariants.braid_id}")
    print(f"   Dominant Frequency: {invariants.dominant_frequency:.4f}")
    print(f"   Frequency Entropy: {invariants.frequency_entropy:.4f}")
    print(f"   Mean Lifetime: {invariants.mean_lifetime:.4f}")
    print(f"   Stability Index: {invariants.stability_index:.4f}")
    print(f"   Computational Irreducibility: {invariants.computational_irreducibility:.4f}")
    print(f"   Dynamic Complexity: {invariants.dynamic_complexity:.4f}")
    
    # Test with multiple braids
    sample_braids = [
        create_sample_braid_timeseries(f"test_braid_{i:03d}") 
        for i in range(5)
    ]
    
    feature_matrix = analyzer.analyze_multiple_braids(sample_braids)
    print(f"\n✅ Feature matrix created with {len(feature_matrix)} braids")
    print(f"   Features: {list(feature_matrix.columns)}")
    
    print("\n🎯 DynamicBraidAnalyzer ready for Project 2c implementation!")

if __name__ == "__main__":
    main()
