#!/usr/bin/env python3
"""
Comprehensive Diagnostics Analyzer for UUF Theoretical Upgrades

This script provides deep analysis of why µ-τ anchor works better than 13-torque
by logging comprehensive diagnostics throughout the UUF flow process.
"""

import sys
import os
import time
import json
import yaml
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ugp_discovery_lab.experiments.ugp_single_law_uuf_flow_theoretical_upgrades import UGPSingleLawUUFFlowTheoreticalUpgrades  # type: ignore


class ComprehensiveDiagnosticsAnalyzer:
    """Comprehensive diagnostics analyzer for UUF theoretical upgrades."""
    
    def __init__(self, config_path: str):
        """Initialize the diagnostics analyzer."""
        self.config_path = config_path
        try:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            print(f"❌ Failed to load configuration: {e}")
            self.config = None
        self.diagnostics_data = {}
        
    def analyze_e_orientation_methods(self) -> Dict[str, Any]:
        """
        Analyze different E-orientation methods in detail.
        
        Returns:
            Dict containing detailed analysis of each method
        """
        print("🔬 ANALYZING E-ORIENTATION METHODS")
        print("=" * 50)
        
        methods = ['13_torque', 'mu_tau_anchor']
        analysis = {}
        
        for method in methods:
            print(f"\n📊 Analyzing method: {method}")
            
            # Update config
            self.config['e_orientation_method'] = method
            
            # Create experiment instance
            experiment = UGPSingleLawUUFFlowTheoreticalUpgrades(self.config, project_root)
            
            # Run with diagnostics
            result = self._run_with_diagnostics(experiment, method)
            analysis[method] = result
            
            print(f"✅ {method} analysis completed")
        
        return analysis
    
    def _run_with_diagnostics(self, experiment: UGPSingleLawUUFFlowTheoreticalUpgrades, method_name: str) -> Dict[str, Any]:
        """
        Run experiment with comprehensive diagnostics logging.
        
        Args:
            experiment: The UUF experiment instance
            method_name: Name of the method being analyzed
            
        Returns:
            Dict containing detailed diagnostics
        """
        diagnostics = {
            'method_name': method_name,
            'timestamp': datetime.now().isoformat(),
            'steps': {}
        }
        
        try:
            # Update experiment config for this method
            if 'options' not in experiment.cfg:
                experiment.cfg['options'] = {}
            if 'theoretical_upgrades' not in experiment.cfg['options']:
                experiment.cfg['options']['theoretical_upgrades'] = {}
            
            experiment.cfg['options']['theoretical_upgrades']['e_orientation_method'] = method_name
            
            # Run the experiment using the proper interface
            print(f"  🚀 Running experiment with {method_name}...")
            result = experiment.run_task('single_law_uuf_flow')
            
            if result:
                diagnostics['steps']['experiment_run'] = {
                    'success': True,
                    'result_keys': list(result.keys()) if result else [],
                    'has_ckm_errors': 'ckm_errors' in result,
                    'has_pmns_errors': 'pmns_errors' in result
                }
                
                # Analyze errors if present
                if 'validation' in result:
                    validation = result['validation']
                    ckm_validation = validation.get('ckm_validation', {})
                    pmns_validation = validation.get('pmns_validation', {})
                    
                    ckm_errors = ckm_validation.get('errors', {})
                    pmns_errors = pmns_validation.get('errors', {})
                    
                    if ckm_errors and pmns_errors:
                        diagnostics['steps']['error_analysis'] = {
                            'success': True,
                            'ckm_errors': ckm_errors,
                            'pmns_errors': pmns_errors,
                            'ckm_average': sum(ckm_errors.values()) / len(ckm_errors) if ckm_errors else float('inf'),
                            'pmns_average': sum(pmns_errors.values()) / len(pmns_errors) if pmns_errors else float('inf')
                        }
                    else:
                        diagnostics['steps']['error_analysis'] = {
                            'success': False,
                            'error': 'Missing error data in validation'
                        }
                else:
                    diagnostics['steps']['error_analysis'] = {
                        'success': False,
                        'error': 'Missing validation data in result'
                    }
            else:
                diagnostics['steps']['experiment_run'] = {
                    'success': False,
                    'error': 'No result returned from run_task'
                }
            
            # Overall success
            diagnostics['overall_success'] = diagnostics['steps']['experiment_run'].get('success', False)
            
        except Exception as e:
            print(f"  ❌ Error in diagnostics: {e}")
            diagnostics['error'] = str(e)
            diagnostics['overall_success'] = False
        
        return diagnostics
    
    def _calculate_generator_norms(self, generators: Dict[str, Any]) -> Dict[str, float]:
        """Calculate norms of generator matrices."""
        norms = {}
        
        for sector, sector_gens in generators.items():
            if isinstance(sector_gens, dict):
                for gen_type, gen_matrix in sector_gens.items():
                    if isinstance(gen_matrix, np.ndarray):
                        norms[f"{sector}_{gen_type}"] = float(np.linalg.norm(gen_matrix))
        
        return norms
    
    def _analyze_sector_results(self, flow_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze UUF flow results for each sector."""
        analysis = {}
        
        for sector, sector_data in flow_results.items():
            if isinstance(sector_data, dict):
                sector_analysis = {
                    'data_keys': list(sector_data.keys()),
                    'has_mass_matrix': 'mass_matrix' in sector_data,
                    'has_flow_info': 'flow_info' in sector_data
                }
                
                # Analyze mass matrix if present
                if 'mass_matrix' in sector_data:
                    mass_matrix = sector_data['mass_matrix']
                    if isinstance(mass_matrix, np.ndarray):
                        sector_analysis['mass_matrix_analysis'] = {
                            'shape': mass_matrix.shape,
                            'norm': float(np.linalg.norm(mass_matrix)),
                            'eigenvalues': np.linalg.eigvals(mass_matrix).tolist(),
                            'is_hermitian': np.allclose(mass_matrix, mass_matrix.conj().T),
                            'is_symmetric': np.allclose(mass_matrix, mass_matrix.T)
                        }
                
                analysis[sector] = sector_analysis
        
        return analysis
    
    def _analyze_mixing_matrices(self, mixing_matrices: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze mixing matrices."""
        analysis = {}
        
        for matrix_type, matrix_data in mixing_matrices.items():
            if isinstance(matrix_data, dict):
                matrix_analysis = {
                    'data_keys': list(matrix_data.keys()),
                    'has_matrix': 'matrix' in matrix_data,
                    'has_angles': 'angles' in matrix_data
                }
                
                # Analyze matrix if present
                if 'matrix' in matrix_data:
                    matrix = matrix_data['matrix']
                    if isinstance(matrix, np.ndarray):
                        matrix_analysis['matrix_analysis'] = {
                            'shape': matrix.shape,
                            'norm': float(np.linalg.norm(matrix)),
                            'is_unitary': np.allclose(matrix @ matrix.conj().T, np.eye(matrix.shape[0])),
                            'determinant': float(np.linalg.det(matrix)),
                            'trace': float(np.trace(matrix))
                        }
                
                analysis[matrix_type] = matrix_analysis
        
        return analysis
    
    def _analyze_errors(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze validation errors."""
        error_analysis = {
            'has_ckm_errors': 'ckm_errors' in validation_results,
            'has_pmns_errors': 'pmns_errors' in validation_results,
            'error_summary': {}
        }
        
        if 'ckm_errors' in validation_results:
            ckm_errors = validation_results['ckm_errors']
            error_analysis['error_summary']['ckm'] = {
                'theta_12': ckm_errors.get('theta12_error', 0),
                'theta_13': ckm_errors.get('theta13_error', 0),
                'theta_23': ckm_errors.get('theta23_error', 0),
                'average': sum(ckm_errors.values()) / len(ckm_errors) if ckm_errors else 0
            }
        
        if 'pmns_errors' in validation_results:
            pmns_errors = validation_results['pmns_errors']
            error_analysis['error_summary']['pmns'] = {
                'theta_12': pmns_errors.get('theta12_error', 0),
                'theta_13': pmns_errors.get('theta13_error', 0),
                'theta_23': pmns_errors.get('theta23_error', 0),
                'average': sum(pmns_errors.values()) / len(pmns_errors) if pmns_errors else 0
            }
        
        return error_analysis
    
    def compare_methods(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare different E-orientation methods.
        
        Args:
            analysis: Analysis results from analyze_e_orientation_methods
            
        Returns:
            Dict containing comparison analysis
        """
        print("\n🔍 COMPARING E-ORIENTATION METHODS")
        print("=" * 50)
        
        comparison = {
            'timestamp': datetime.now().isoformat(),
            'methods_compared': list(analysis.keys()),
            'comparisons': {}
        }
        
        # Compare overall success
        comparison['overall_success'] = {
            method: data.get('overall_success', False)
            for method, data in analysis.items()
        }
        
        # Compare error performance
        if all('steps' in data and 'error_analysis' in data['steps'] for data in analysis.values()):
            error_comparison = {}
            
            for method, data in analysis.items():
                error_step = data['steps'].get('error_analysis', {})
                
                # Convert decimal averages to percentages
                ckm_avg_decimal = error_step.get('ckm_average', float('inf'))
                pmns_avg_decimal = error_step.get('pmns_average', float('inf'))
                
                error_comparison[method] = {
                    'ckm_average': ckm_avg_decimal * 100 if ckm_avg_decimal != float('inf') else float('inf'),
                    'pmns_average': pmns_avg_decimal * 100 if pmns_avg_decimal != float('inf') else float('inf'),
                    'overall_average': 0
                }
                
                # Calculate overall average in percentage
                ckm_avg = error_comparison[method]['ckm_average']
                pmns_avg = error_comparison[method]['pmns_average']
                if ckm_avg != float('inf') and pmns_avg != float('inf'):
                    error_comparison[method]['overall_average'] = (ckm_avg + pmns_avg) / 2
            
            comparison['error_performance'] = error_comparison
            
            # Find best method
            best_method = min(error_comparison.keys(), 
                            key=lambda x: error_comparison[x]['overall_average'])
            comparison['best_method'] = best_method
            comparison['best_performance'] = error_comparison[best_method]
        
        # Compare generator characteristics
        if all('steps' in data and 'generator_building' in data['steps'] for data in analysis.values()):
            generator_comparison = {}
            
            for method, data in analysis.items():
                gen_step = data['steps'].get('generator_building', {})
                gen_norms = gen_step.get('generator_norms', {})
                
                generator_comparison[method] = {
                    'total_norm': sum(gen_norms.values()) if gen_norms else 0,
                    'norm_distribution': gen_norms
                }
            
            comparison['generator_characteristics'] = generator_comparison
        
        # Compare sector analysis
        if all('steps' in data and 'uuf_flow' in data['steps'] for data in analysis.values()):
            sector_comparison = {}
            
            for method, data in analysis.items():
                flow_step = data['steps'].get('uuf_flow', {})
                sector_analysis = flow_step.get('sector_analysis', {})
                
                sector_comparison[method] = {
                    'sectors_analyzed': list(sector_analysis.keys()),
                    'sector_count': len(sector_analysis)
                }
            
            comparison['sector_analysis'] = sector_comparison
        
        return comparison
    
    def generate_report(self, analysis: Dict[str, Any], comparison: Dict[str, Any]) -> str:
        """
        Generate a comprehensive diagnostic report.
        
        Args:
            analysis: Analysis results from analyze_e_orientation_methods
            comparison: Comparison results from compare_methods
            
        Returns:
            String containing the diagnostic report
        """
        report = []
        report.append("🔬 COMPREHENSIVE DIAGNOSTICS REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary
        report.append("📊 EXECUTIVE SUMMARY")
        report.append("-" * 30)
        if 'best_method' in comparison:
            report.append(f"Best Method: {comparison['best_method']}")
            report.append(f"Best Performance: {comparison['best_performance']['overall_average']:.2f}% overall error")
        report.append("")
        
        # Method-by-method analysis
        report.append("🔍 DETAILED METHOD ANALYSIS")
        report.append("-" * 30)
        
        for method, data in analysis.items():
            report.append(f"\n📋 Method: {method}")
            report.append(f"Overall Success: {data.get('overall_success', False)}")
            
            # Step-by-step analysis
            for step_name, step_data in data.get('steps', {}).items():
                report.append(f"  {step_name}: {'✅' if step_data.get('success', False) else '❌'}")
                
                # Add specific analysis for key steps
                if step_name == 'error_analysis' and step_data.get('success', False):
                    ckm_errors = step_data.get('ckm_errors', {})
                    pmns_errors = step_data.get('pmns_errors', {})
                    ckm_avg = step_data.get('ckm_average', 0)
                    pmns_avg = step_data.get('pmns_average', 0)
                    
                    if ckm_errors:
                        report.append(f"    CKM Errors: θ₁₂={ckm_errors.get('theta12_error', 0)*100:.2f}%, θ₁₃={ckm_errors.get('theta13_error', 0)*100:.2f}%, θ₂₃={ckm_errors.get('theta23_error', 0)*100:.2f}%")
                        report.append(f"    CKM Average: {ckm_avg*100:.2f}%")
                    if pmns_errors:
                        report.append(f"    PMNS Errors: θ₁₂={pmns_errors.get('theta12_error', 0)*100:.2f}%, θ₁₃={pmns_errors.get('theta13_error', 0)*100:.2f}%, θ₂₃={pmns_errors.get('theta23_error', 0)*100:.2f}%")
                        report.append(f"    PMNS Average: {pmns_avg*100:.2f}%")
        
        # Comparison analysis
        report.append("\n🔍 COMPARISON ANALYSIS")
        report.append("-" * 30)
        
        if 'error_performance' in comparison:
            report.append("\n📊 Error Performance Comparison:")
            for method, perf in comparison['error_performance'].items():
                report.append(f"  {method}:")
                report.append(f"    CKM Average: {perf['ckm_average']:.2f}%")
                report.append(f"    PMNS Average: {perf['pmns_average']:.2f}%")
                report.append(f"    Overall Average: {perf['overall_average']:.2f}%")
        
        if 'generator_characteristics' in comparison:
            report.append("\n🔧 Generator Characteristics:")
            for method, chars in comparison['generator_characteristics'].items():
                report.append(f"  {method}: Total Norm = {chars['total_norm']:.2f}")
        
        # Key insights
        report.append("\n💡 KEY INSIGHTS")
        report.append("-" * 30)
        
        if 'best_method' in comparison:
            best_method = comparison['best_method']
            report.append(f"• {best_method} performs best overall")
            
            # Analyze why it's better
            if 'error_performance' in comparison:
                error_perf = comparison['error_performance']
                best_perf = error_perf[best_method]
                
                if best_perf['ckm_average'] < best_perf['pmns_average']:
                    report.append(f"• {best_method} excels at CKM preservation")
                else:
                    report.append(f"• {best_method} excels at PMNS accuracy")
        
        # Recommendations
        report.append("\n🎯 RECOMMENDATIONS")
        report.append("-" * 30)
        report.append("• Continue using the best-performing method for production")
        report.append("• Investigate why the best method works better")
        report.append("• Consider hybrid approaches combining best aspects")
        report.append("• Explore further theoretical improvements")
        
        return "\n".join(report)
    
    def save_results(self, analysis: Dict[str, Any], comparison: Dict[str, Any], report: str):
        """Save all results to files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed analysis
        analysis_file = f"comprehensive_diagnostics_analysis_{timestamp}.json"
        with open(analysis_file, 'w') as f:
            json.dump({
                'analysis': analysis,
                'comparison': comparison,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)
        print(f"💾 Detailed analysis saved to: {analysis_file}")
        
        # Save report
        report_file = f"comprehensive_diagnostics_report_{timestamp}.md"
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"📄 Diagnostic report saved to: {report_file}")


def main():
    """Main function to run comprehensive diagnostics analysis."""
    print("🔬 STARTING COMPREHENSIVE DIAGNOSTICS ANALYSIS")
    print("=" * 70)
    
    # Initialize analyzer
    config_path = project_root / "configs" / "experiments" / "ugp_single_law_uuf_flow_theoretical_upgrades.yaml"
    analyzer = ComprehensiveDiagnosticsAnalyzer(str(config_path))
    
    # Run analysis
    print("🚀 Running E-orientation method analysis...")
    analysis = analyzer.analyze_e_orientation_methods()
    
    # Compare methods
    print("🔍 Comparing methods...")
    comparison = analyzer.compare_methods(analysis)
    
    # Generate report
    print("📄 Generating diagnostic report...")
    report = analyzer.generate_report(analysis, comparison)
    
    # Save results
    analyzer.save_results(analysis, comparison, report)
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 DIAGNOSTICS ANALYSIS COMPLETE")
    print("=" * 70)
    
    if 'best_method' in comparison:
        print(f"🏆 Best Method: {comparison['best_method']}")
        print(f"📈 Best Performance: {comparison['best_performance']['overall_average']:.2f}% overall error")
    
    print("💾 All results saved to files")
    print("📄 Check the generated report for detailed analysis")


if __name__ == "__main__":
    main()
