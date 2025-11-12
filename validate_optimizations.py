#!/usr/bin/env python3
"""
Optimization validation benchmark for reasoning library.

This script validates the performance improvements from the implemented optimizations:
1. NINJA: Function source code caching and mathematical detection memoization
2. SAMURAI: Optimized NumPy pattern detection with early exit and streaming

Measures concrete performance gains and validates correctness.

Run with: uv run python validate_optimizations.py
"""

import os
import statistics

# Import the library functions
import sys
import time
from typing import Callable, Dict

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from reasoning_library.core import (
    _detect_mathematical_reasoning,
    _detect_mathematical_reasoning_uncached,
    clear_performance_caches,
)
from reasoning_library.inductive import (
    _calculate_pattern_quality_score_optimized,
    _calculate_pattern_quality_score_original,
)


class OptimizationValidator:
    """Validates optimization performance gains with statistical significance."""

    def __init__(self):
        self.results = {}

    def benchmark_function(
        self,
        func: Callable,
        *args,
        name: str,
        iterations: int = 100,
        **kwargs
    ) -> Dict[str, float]:
        """Benchmark a function with statistical analysis."""
        times = []

        for _ in range(iterations):
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                print(f"Error in {name}: {e}")
                continue
            end = time.perf_counter()
            times.append((end - start) * 1000)  # Convert to milliseconds

        if not times:
            return {"error": f"All iterations failed for {name}"}

        return {
            "name": name,
            "mean_ms": statistics.mean(times),
            "median_ms": statistics.median(times),
            "std_ms": statistics.stdev(times) if len(times) > 1 else 0,
            "min_ms": min(times),
            "max_ms": max(times),
            "p95_ms": sorted(times)[int(0.95 * len(times))],
            "iterations": len(times)
        }

    def validate_regex_optimization(self):
        """Validate the NINJA-level regex caching optimization."""
        print("🥷 NINJA OPTIMIZATION VALIDATION")
        print("================================")

        # Create test functions with varying complexity
        def simple_math_function():
            """Simple confidence calculation."""
            return sum([1, 2, 3])

        def complex_math_function():
            """
            Complex mathematical reasoning with confidence calculation.
            Uses data_sufficiency_factor and pattern_quality_factor.
            Includes arithmetic progression analysis with variance.
            Geometric progression with coefficient_of_variation.
            Deductive logic with modus_ponens inference.
            Chain of thought reasoning with sequential steps.
            """
            data_sufficiency_factor = 0.8
            pattern_quality_factor = 0.9
            complexity_factor = 0.7
            return data_sufficiency_factor * pattern_quality_factor * complexity_factor

        # Clear caches to ensure fair comparison
        clear_performance_caches()

        # Benchmark uncached version (original)
        uncached_simple = self.benchmark_function(
            _detect_mathematical_reasoning_uncached,
            simple_math_function,
            name="Uncached Simple",
            iterations=200
        )

        uncached_complex = self.benchmark_function(
            _detect_mathematical_reasoning_uncached,
            complex_math_function,
            name="Uncached Complex",
            iterations=200
        )

        # Clear caches again
        clear_performance_caches()

        # Benchmark cached version - first run (cache miss)
        cached_simple_cold = self.benchmark_function(
            _detect_mathematical_reasoning,
            simple_math_function,
            name="Cached Simple (Cold)",
            iterations=10  # Just a few to populate cache
        )

        cached_complex_cold = self.benchmark_function(
            _detect_mathematical_reasoning,
            complex_math_function,
            name="Cached Complex (Cold)",
            iterations=10
        )

        # Benchmark cached version - subsequent runs (cache hit)
        cached_simple_hot = self.benchmark_function(
            _detect_mathematical_reasoning,
            simple_math_function,
            name="Cached Simple (Hot)",
            iterations=200
        )

        cached_complex_hot = self.benchmark_function(
            _detect_mathematical_reasoning,
            complex_math_function,
            name="Cached Complex (Hot)",
            iterations=200
        )

        # Calculate improvements
        simple_improvement = (uncached_simple["mean_ms"] - cached_simple_hot["mean_ms"]) / uncached_simple["mean_ms"] * 100
        complex_improvement = (uncached_complex["mean_ms"] - cached_complex_hot["mean_ms"]) / uncached_complex["mean_ms"] * 100

        print("📊 REGEX OPTIMIZATION RESULTS:")
        print("├── Simple Function:")
        print(f"│   ├── Uncached: {uncached_simple['mean_ms']:.2f}ms ± {uncached_simple['std_ms']:.2f}ms")
        print(f"│   ├── Cached (Hot): {cached_simple_hot['mean_ms']:.2f}ms ± {cached_simple_hot['std_ms']:.2f}ms")
        print(f"│   └── Improvement: {simple_improvement:.1f}% faster")
        print("│")
        print("├── Complex Function:")
        print(f"│   ├── Uncached: {uncached_complex['mean_ms']:.2f}ms ± {uncached_complex['std_ms']:.2f}ms")
        print(f"│   ├── Cached (Hot): {cached_complex_hot['mean_ms']:.2f}ms ± {cached_complex_hot['std_ms']:.2f}ms")
        print(f"│   └── Improvement: {complex_improvement:.1f}% faster")

        # Target validation
        target_met = complex_improvement >= 80  # Target was 80% improvement
        status = "✅ TARGET MET" if target_met else "❌ TARGET MISSED"
        print("│")
        print(f"└── {status} (Target: 80% improvement)")

        self.results['regex_optimization'] = {
            'uncached_complex': uncached_complex,
            'cached_hot_complex': cached_complex_hot,
            'improvement_percent': complex_improvement,
            'target_met': target_met
        }

    def validate_numpy_optimization(self):
        """Validate the SAMURAI-level NumPy optimization."""
        print("\n⚔️ SAMURAI OPTIMIZATION VALIDATION")
        print("==================================")

        # Test with various sequence sizes
        sequence_sizes = [50, 100, 200, 500, 1000]

        for size in sequence_sizes:
            print(f"\n📊 Sequence Size: {size}")

            # Perfect arithmetic sequence (early exit optimization test)
            perfect_arithmetic = list(range(size))
            perfect_diffs = np.diff(perfect_arithmetic)

            # Noisy arithmetic sequence
            noisy_arithmetic = [i + np.random.normal(0, 0.1) for i in range(size)]
            noisy_diffs = np.diff(noisy_arithmetic)

            # Benchmark original vs optimized for perfect pattern
            original_perfect = self.benchmark_function(
                _calculate_pattern_quality_score_original,
                perfect_diffs,
                "arithmetic",
                name=f"Original Perfect {size}",
                iterations=100
            )

            optimized_perfect = self.benchmark_function(
                _calculate_pattern_quality_score_optimized,
                perfect_diffs,
                "arithmetic",
                name=f"Optimized Perfect {size}",
                iterations=100
            )

            # Benchmark original vs optimized for noisy pattern
            original_noisy = self.benchmark_function(
                _calculate_pattern_quality_score_original,
                noisy_diffs,
                "arithmetic",
                name=f"Original Noisy {size}",
                iterations=100
            )

            optimized_noisy = self.benchmark_function(
                _calculate_pattern_quality_score_optimized,
                noisy_diffs,
                "arithmetic",
                name=f"Optimized Noisy {size}",
                iterations=100
            )

            # Calculate improvements
            perfect_improvement = (original_perfect["mean_ms"] - optimized_perfect["mean_ms"]) / original_perfect["mean_ms"] * 100
            noisy_improvement = (original_noisy["mean_ms"] - optimized_noisy["mean_ms"]) / original_noisy["mean_ms"] * 100

            print("├── Perfect Pattern:")
            print(f"│   ├── Original: {original_perfect['mean_ms']:.3f}ms")
            print(f"│   ├── Optimized: {optimized_perfect['mean_ms']:.3f}ms")
            print(f"│   └── Improvement: {perfect_improvement:.1f}%")
            print("├── Noisy Pattern:")
            print(f"│   ├── Original: {original_noisy['mean_ms']:.3f}ms")
            print(f"│   ├── Optimized: {optimized_noisy['mean_ms']:.3f}ms")
            print(f"│   └── Improvement: {noisy_improvement:.1f}%")

            # Store results for large sequences
            if size >= 500:
                self.results[f'numpy_optimization_{size}'] = {
                    'perfect_improvement': perfect_improvement,
                    'noisy_improvement': noisy_improvement,
                    'original_perfect': original_perfect,
                    'optimized_perfect': optimized_perfect
                }

    def validate_correctness(self):
        """Ensure optimizations don't change mathematical results."""
        print("\n🔍 CORRECTNESS VALIDATION")
        print("=========================")

        correctness_passed = True
        test_cases = []

        # Test mathematical reasoning detection consistency
        def test_math_function():
            """Test function with mathematical indicators."""
            confidence = 0.8 * 0.9  # data_sufficiency_factor * pattern_quality_factor
            return confidence

        clear_performance_caches()
        uncached_result = _detect_mathematical_reasoning_uncached(test_math_function)
        cached_result = _detect_mathematical_reasoning(test_math_function)

        if uncached_result != cached_result:
            print("❌ Math detection results differ between cached and uncached!")
            correctness_passed = False
        else:
            print("✅ Math detection results consistent")
            test_cases.append("Math detection consistency")

        # Test pattern quality consistency for various sequences
        test_sequences = [
            [1, 2, 3, 4, 5],  # Perfect arithmetic
            [2, 4, 8, 16, 32],  # Perfect geometric
            [1, 2.1, 2.9, 4.1, 4.9],  # Noisy arithmetic
            [1, 1, 1, 1, 1],  # Constant sequence
            list(range(100)),  # Large arithmetic
            [2**i for i in range(50)]  # Large geometric
        ]

        for i, seq in enumerate(test_sequences):
            diffs = np.diff(seq)
            original_score = _calculate_pattern_quality_score_original(diffs, "arithmetic")
            optimized_score = _calculate_pattern_quality_score_optimized(diffs, "arithmetic")

            # Allow small numerical differences due to floating point precision
            if abs(original_score - optimized_score) > 1e-10:
                print(f"❌ Pattern quality differs for sequence {i}: {original_score:.6f} vs {optimized_score:.6f}")
                correctness_passed = False
            else:
                test_cases.append(f"Sequence {i} consistency")

        if correctness_passed:
            print(f"✅ All {len(test_cases)} correctness tests passed")
        else:
            print("❌ Some correctness tests failed!")

        self.results['correctness'] = {
            'passed': correctness_passed,
            'test_cases': len(test_cases)
        }

    def generate_final_report(self):
        """Generate comprehensive optimization validation report."""
        print("\n" + "="*70)
        print("🎯 OPTIMIZATION VALIDATION REPORT")
        print("="*70)

        # Overall performance summary
        regex_results = self.results.get('regex_optimization', {})
        regex_improvement = regex_results.get('improvement_percent', 0)
        regex_target_met = regex_results.get('target_met', False)

        print("\n🥷 NINJA LEVEL RESULTS:")
        print(f"├── Regex Optimization: {regex_improvement:.1f}% improvement")
        print(f"├── Target (80%): {'✅ MET' if regex_target_met else '❌ MISSED'}")
        if regex_target_met:
            print("├── Status: Massive success! Function detection significantly faster")
            original_time = regex_results.get('uncached_complex', {}).get('mean_ms', 0)
            optimized_time = regex_results.get('cached_hot_complex', {}).get('mean_ms', 0)
            print(f"└── Concrete gain: {original_time:.2f}ms → {optimized_time:.2f}ms per function")
        else:
            print("└── Status: Partial success, but room for improvement")

        # NumPy optimization summary
        large_seq_results = self.results.get('numpy_optimization_1000', {})
        if large_seq_results:
            perfect_improvement = large_seq_results.get('perfect_improvement', 0)
            print("\n⚔️ SAMURAI LEVEL RESULTS:")
            print(f"├── NumPy Optimization: {perfect_improvement:.1f}% improvement for perfect patterns")
            print(f"├── Early Exit Working: {'✅ YES' if perfect_improvement > 30 else '❌ NO'}")
            print("└── Large Sequence Handling: Optimized for sequences >100 elements")

        # Correctness validation
        correctness = self.results.get('correctness', {})
        correctness_passed = correctness.get('passed', False)
        test_count = correctness.get('test_cases', 0)

        print("\n🔍 CORRECTNESS VALIDATION:")
        print(f"├── All Tests Passed: {'✅ YES' if correctness_passed else '❌ NO'}")
        print(f"├── Test Cases: {test_count}")
        print(f"└── Mathematical Accuracy: {'✅ PRESERVED' if correctness_passed else '❌ COMPROMISED'}")

        # Overall assessment
        overall_success = regex_target_met and correctness_passed
        print("\n🏆 OVERALL ASSESSMENT:")
        if overall_success:
            print("├── Status: ✅ OPTIMIZATION SUCCESS")
            print("├── Performance: Significant improvements achieved")
            print("├── Correctness: Mathematical accuracy preserved")
            print("└── Recommendation: Deploy to production")
        else:
            print("├── Status: ⚠️ PARTIAL SUCCESS")
            print(f"├── Issues: {'Correctness' if not correctness_passed else 'Performance targets'}")
            print(f"└── Recommendation: {'Fix correctness issues' if not correctness_passed else 'Further optimization needed'}")

        print("\n📋 NEXT STEPS:")
        print("├── Add to CI/CD pipeline for regression testing")
        print("├── Monitor production performance metrics")
        print("├── Consider GODZILLA-level optimizations for 10x gains")
        print("└── Implement async conversion for I/O-bound operations")


def main():
    """Run comprehensive optimization validation."""
    print("🔬 REASONING LIBRARY OPTIMIZATION VALIDATOR")
    print("==========================================")
    print("Validating NINJA and SAMURAI level optimizations...")

    validator = OptimizationValidator()

    try:
        # Validate each optimization level
        validator.validate_regex_optimization()
        validator.validate_numpy_optimization()
        validator.validate_correctness()

        # Generate comprehensive report
        validator.generate_final_report()

    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
