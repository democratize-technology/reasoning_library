#!/usr/bin/env python3
"""
Performance profiling script for reasoning library bottlenecks.

This script measures the exact performance bottlenecks identified:
1. Regex-heavy mathematical reasoning detection
2. Thread lock contention in conversation management
3. NumPy-intensive pattern detection and confidence calculation

Run with: python profile_bottlenecks.py
"""

import os
import statistics

# Import the actual library functions
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from reasoning_library.chain_of_thought import chain_of_thought_step
from reasoning_library.core import _detect_mathematical_reasoning
from reasoning_library.inductive import (
    _calculate_pattern_quality_score,
    predict_next_in_sequence,
)


class PerformanceProfiler:
    """Systematic performance profiler for bottleneck analysis."""

    def __init__(self):
        self.results = {}

    def time_function(self, func: Callable, *args, iterations: int = 1000, **kwargs) -> dict:
        """Time a function execution with statistical analysis."""
        times = []

        for _ in range(iterations):
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                print(f"Error in {func.__name__}: {e}")
                continue
            end = time.perf_counter()
            times.append((end - start) * 1000)  # Convert to milliseconds

        if not times:
            return {"error": "All iterations failed"}

        return {
            "mean_ms": statistics.mean(times),
            "median_ms": statistics.median(times),
            "std_ms": statistics.stdev(times) if len(times) > 1 else 0,
            "min_ms": min(times),
            "max_ms": max(times),
            "p95_ms": sorted(times)[int(0.95 * len(times))],
            "total_time_ms": sum(times),
            "iterations": len(times)
        }

    def profile_regex_bottleneck(self):
        """Profile the regex-heavy mathematical reasoning detection."""
        print("🔍 Profiling Regex Bottleneck...")

        # Create test functions with varying complexity
        def simple_math_function():
            """Simple confidence calculation based on pattern quality."""
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
            # Simulate complex mathematical operations
            data_sufficiency_factor = 0.8
            pattern_quality_factor = 0.9
            complexity_factor = 0.7
            return data_sufficiency_factor * pattern_quality_factor * complexity_factor

        # Profile different function complexities
        simple_result = self.time_function(_detect_mathematical_reasoning, simple_math_function, iterations=500)
        complex_result = self.time_function(_detect_mathematical_reasoning, complex_math_function, iterations=500)

        print(f"  Simple function detection: {simple_result['mean_ms']:.2f}ms ± {simple_result['std_ms']:.2f}ms")
        print(f"  Complex function detection: {complex_result['mean_ms']:.2f}ms ± {complex_result['std_ms']:.2f}ms")
        print(f"  Complexity overhead: {complex_result['mean_ms'] - simple_result['mean_ms']:.2f}ms")

        self.results['regex_bottleneck'] = {
            'simple': simple_result,
            'complex': complex_result,
            'overhead_ms': complex_result['mean_ms'] - simple_result['mean_ms']
        }

    def profile_threading_bottleneck(self):
        """Profile thread lock contention in conversation management."""
        print("🔒 Profiling Threading Bottleneck...")

        # Single-threaded baseline
        single_result = self.time_function(
            chain_of_thought_step,
            "test_conversation",
            "Simple reasoning step",
            iterations=1000
        )

        # Multi-threaded contention test
        def concurrent_conversation_access():
            """Simulate concurrent conversation access."""
            def worker(thread_id):
                for i in range(50):
                    chain_of_thought_step(
                        f"conv_{thread_id}",
                        f"Step {i} from thread {thread_id}"
                    )

            start = time.perf_counter()
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = [executor.submit(worker, i) for i in range(8)]
                for future in futures:
                    future.result()
            end = time.perf_counter()
            return (end - start) * 1000

        # Run contention test multiple times
        contention_times = [concurrent_conversation_access() for _ in range(10)]
        contention_result = {
            "mean_ms": statistics.mean(contention_times),
            "std_ms": statistics.stdev(contention_times),
            "min_ms": min(contention_times),
            "max_ms": max(contention_times)
        }

        print(f"  Single-threaded: {single_result['mean_ms']:.2f}ms ± {single_result['std_ms']:.2f}ms")
        print(f"  8-thread contention: {contention_result['mean_ms']:.2f}ms ± {contention_result['std_ms']:.2f}ms")
        print(f"  Contention overhead: {contention_result['mean_ms'] / (8 * 50) - single_result['mean_ms']:.2f}ms per operation")

        self.results['threading_bottleneck'] = {
            'single': single_result,
            'contention': contention_result
        }

    def profile_numpy_bottleneck(self):
        """Profile NumPy-intensive pattern detection."""
        print("📊 Profiling NumPy Bottleneck...")

        # Test different sequence sizes
        sequence_sizes = [10, 50, 100, 500, 1000]

        for size in sequence_sizes:
            # Arithmetic sequence
            arithmetic_seq = list(range(size))

            # Geometric sequence
            geometric_seq = [2 ** i for i in range(size)]

            # Random sequence (worst case - no pattern)
            random_seq = np.random.rand(size).tolist()

            # Profile pattern detection
            arith_result = self.time_function(predict_next_in_sequence, arithmetic_seq, None, iterations=100)
            geom_result = self.time_function(predict_next_in_sequence, geometric_seq, None, iterations=100)
            random_result = self.time_function(predict_next_in_sequence, random_seq, None, iterations=100)

            # Profile confidence calculation directly
            diffs = np.diff(arithmetic_seq)
            conf_result = self.time_function(_calculate_pattern_quality_score, diffs, "arithmetic", iterations=500)

            print(f"  Size {size:4d}: Arith={arith_result['mean_ms']:.2f}ms, Geom={geom_result['mean_ms']:.2f}ms, Random={random_result['mean_ms']:.2f}ms, Conf={conf_result['mean_ms']:.2f}ms")

            self.results[f'numpy_size_{size}'] = {
                'arithmetic': arith_result,
                'geometric': geom_result,
                'random': random_result,
                'confidence': conf_result
            }

    def profile_memory_usage(self):
        """Profile memory usage patterns."""
        print("💾 Profiling Memory Usage...")

        import tracemalloc

        # Start memory tracking
        tracemalloc.start()

        # Baseline measurement
        baseline = tracemalloc.take_snapshot()

        # Create many conversations (memory stress test)
        for i in range(1000):
            chain_of_thought_step(f"conv_{i}", f"Step for conversation {i}")

        conversations_snapshot = tracemalloc.take_snapshot()

        # Create large sequences for pattern detection
        large_sequences = []
        for i in range(100):
            seq = list(range(1000))
            predict_next_in_sequence(seq, None)
            large_sequences.append(seq)

        patterns_snapshot = tracemalloc.take_snapshot()

        # Calculate memory differences
        conv_stats = conversations_snapshot.compare_to(baseline, 'lineno')
        pattern_stats = patterns_snapshot.compare_to(conversations_snapshot, 'lineno')

        total_conv_mb = sum(stat.size_diff for stat in conv_stats) / (1024 * 1024)
        total_pattern_mb = sum(stat.size_diff for stat in pattern_stats) / (1024 * 1024)

        print(f"  Conversations memory: {total_conv_mb:.2f} MB")
        print(f"  Pattern detection memory: {total_pattern_mb:.2f} MB")

        tracemalloc.stop()

        self.results['memory_usage'] = {
            'conversations_mb': total_conv_mb,
            'patterns_mb': total_pattern_mb
        }

    def generate_optimization_report(self):
        """Generate detailed optimization recommendations."""
        print("\n" + "="*60)
        print("🎯 OPTIMIZATION REPORT - GODZILLA MODE 🦖")
        print("="*60)

        # Analyze results and provide specific recommendations
        regex_overhead = self.results.get('regex_bottleneck', {}).get('overhead_ms', 0)

        print("\n🥷 NINJA LEVEL OPTIMIZATIONS (Quick Wins):")
        print(f"├── Regex Bottleneck: {regex_overhead:.2f}ms overhead per complex function")
        if regex_overhead > 1.0:
            print("│   ✅ IMPLEMENT: Function source code caching with weak references")
            print("│   ✅ IMPLEMENT: Pre-compiled regex pattern memoization")
            print("│   📈 ESTIMATED GAIN: 80% reduction in detection time")

        # Threading analysis
        if 'threading_bottleneck' in self.results:
            contention = self.results['threading_bottleneck']['contention']['mean_ms']
            single = self.results['threading_bottleneck']['single']['mean_ms']
            overhead_per_op = contention / (8 * 50) - single

            print(f"├── Threading Bottleneck: {overhead_per_op:.2f}ms contention overhead per operation")
            if overhead_per_op > 0.1:
                print("│   ✅ IMPLEMENT: Replace RLock with asyncio.Lock")
                print("│   ✅ IMPLEMENT: Lock-free data structures where possible")
                print("│   📈 ESTIMATED GAIN: 60% reduction in contention")

        print("\n⚔️ SAMURAI LEVEL OPTIMIZATIONS (Disciplined Refactoring):")
        print("├── Async Conversion")
        print("│   ✅ IMPLEMENT: Convert chain_of_thought to async/await patterns")
        print("│   ✅ IMPLEMENT: Async conversation management with asyncio.Lock")
        print("│   📈 ESTIMATED GAIN: 3x improvement in I/O-bound operations")

        # NumPy analysis
        numpy_results = [v for k, v in self.results.items() if k.startswith('numpy_size_')]
        if numpy_results:
            print("├── NumPy Vectorization")
            print("│   ✅ IMPLEMENT: Streaming confidence calculation with generators")
            print("│   ✅ IMPLEMENT: Early termination for obvious non-patterns")
            print("│   ✅ IMPLEMENT: Parallel pattern detection with concurrent.futures")
            print("│   📈 ESTIMATED GAIN: 40% improvement for large sequences")

        print("\n🦖 GODZILLA LEVEL OPTIMIZATIONS (Destroy and Rebuild):")
        print("├── Architecture Changes")
        print("│   ✅ CONSIDER: Replace in-memory storage with Redis/SQLite")
        print("│   ✅ CONSIDER: GPU acceleration with CuPy for large pattern detection")
        print("│   ✅ CONSIDER: Complete async rewrite of core reasoning chains")
        print("│   📈 ESTIMATED GAIN: 10x improvement for high-throughput scenarios")

        # Memory recommendations
        if 'memory_usage' in self.results:
            conv_mb = self.results['memory_usage']['conversations_mb']
            pattern_mb = self.results['memory_usage']['patterns_mb']
            print("├── Memory Optimization")
            print(f"│   📊 Current usage: {conv_mb:.1f}MB conversations, {pattern_mb:.1f}MB patterns")
            if conv_mb > 50:
                print("│   ✅ IMPLEMENT: Persistent conversation storage")
            if pattern_mb > 100:
                print("│   ✅ IMPLEMENT: Pattern result caching")

        print("\n📊 PERFORMANCE BASELINE ESTABLISHED")
        print("├── Run this script before/after optimizations to measure gains")
        print("├── Add to CI/CD for performance regression detection")
        print("└── Target: <1ms regex detection, <0.1ms threading overhead, <10ms pattern detection")


def main():
    """Run complete performance profiling analysis."""
    print("🔬 REASONING LIBRARY PERFORMANCE PROFILER")
    print("=========================================")
    print("Analyzing the three major bottlenecks identified...")

    profiler = PerformanceProfiler()

    try:
        # Profile each bottleneck systematically
        profiler.profile_regex_bottleneck()
        profiler.profile_threading_bottleneck()
        profiler.profile_numpy_bottleneck()
        profiler.profile_memory_usage()

        # Generate actionable optimization report
        profiler.generate_optimization_report()

    except Exception as e:
        print(f"❌ Profiling failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
