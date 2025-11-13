"""
Template for performance testing in the reasoning library.

This template provides standardized patterns for testing performance
characteristics including memory usage, execution time, and scalability.
"""

import time
import gc
import pytest
from typing import Any, Callable, List, Optional, Dict, Tuple
from dataclasses import dataclass


@dataclass
class PerformanceMetrics:
    """Container for performance test metrics."""
    execution_time: float
    memory_usage: int
    input_size: int
    operations_per_second: float
    memory_per_operation: float


class PerformanceTestTemplate:
    """
    Template class for performance testing.

    Provides standardized methods for testing execution time,
    memory usage, and scalability patterns.
    """

    # Performance thresholds (adjustable per test)
    MAX_EXECUTION_TIME = 1.0  # 1 second
    MAX_MEMORY_USAGE = 10 * 1024 * 1024  # 10MB
    MIN_OPERATIONS_PER_SECOND = 1000

    @pytest.mark.performance
    def test_execution_time_scalability(
        self,
        func: Callable,
        input_sizes: List[int],
        input_generator: Callable[[int], Any],
        max_complexity: str = "linear"  # "linear", "quadratic", "logarithmic"
    ) -> None:
        """
        Test that execution time scales appropriately with input size.

        Args:
            func: Function to test
            input_sizes: List of input sizes to test
            input_generator: Function that generates input of given size
            max_complexity: Expected time complexity
        """
        metrics = []

        for size in input_sizes:
            test_input = input_generator(size)

            # Warm up
            func(test_input)
            gc.collect()

            # Measure execution time
            start_time = time.time()
            try:
                result = func(test_input)
                execution_time = time.time() - start_time

                metrics.append({
                    'size': size,
                    'time': execution_time,
                    'result_size': len(result) if hasattr(result, '__len__') else 1
                })

                # Individual performance check
                assert execution_time <= self.MAX_EXECUTION_TIME, \
                    f"Execution time exceeded: {execution_time:.4f}s for size {size}"

            except Exception as e:
                execution_time = time.time() - start_time
                # Exceptions should also be fast
                assert execution_time <= self.MAX_EXECUTION_TIME, \
                    f"Exception handling too slow: {execution_time:.4f}s for size {size}"

        # Check scalability pattern
        if len(metrics) >= 3:
            self._validate_complexity(metrics, max_complexity)

    @pytest.mark.performance
    def test_memory_usage_efficiency(
        self,
        func: Callable,
        input_sizes: List[int],
        input_generator: Callable[[int], Any],
        allow_memory_growth: bool = True
    ) -> None:
        """
        Test that memory usage is efficient and doesn't leak.

        Args:
            func: Function to test
            input_sizes: List of input sizes to test
            input_generator: Function that generates input of given size
            allow_memory_growth: Whether memory usage is allowed to grow with input size
        """
        try:
            import psutil
            import os

            process = psutil.Process(os.getpid())
            memory_metrics = []

            for size in input_sizes:
                test_input = input_generator(size)

                # Force garbage collection before measurement
                gc.collect()
                initial_memory = process.memory_info().rss

                try:
                    result = func(test_input)

                    # Measure memory after function call
                    current_memory = process.memory_info().rss
                    memory_increase = current_memory - initial_memory

                    memory_metrics.append({
                        'size': size,
                        'memory_increase': memory_increase,
                        'result_size': len(result) if hasattr(result, '__len__') else 1
                    })

                    assert memory_increase <= self.MAX_MEMORY_USAGE, \
                        f"Excessive memory usage: {memory_increase} bytes for size {size}"

                except Exception as e:
                    # Exceptions shouldn't cause memory leaks
                    current_memory = process.memory_info().rss
                    memory_increase = current_memory - initial_memory
                    assert memory_increase <= self.MAX_MEMORY_USAGE, \
                        f"Memory leak in exception: {memory_increase} bytes for size {size}"

            # Check memory growth pattern
            if len(memory_metrics) >= 3 and allow_memory_growth:
                self._validate_memory_growth(memory_metrics)

        except ImportError:
            pytest.skip("psutil not available for memory testing")

    @pytest.mark.performance
    def test_throughput_under_load(
        self,
        func: Callable,
        test_input: Any,
        duration: float = 1.0,
        min_operations_per_second: Optional[int] = None
    ) -> None:
        """
        Test function throughput under sustained load.

        Args:
            func: Function to test
            test_input: Input to use for testing
            duration: Test duration in seconds
            min_operations_per_second: Minimum operations per second required
        """
        min_ops = min_operations_per_second or self.MIN_OPERATIONS_PER_SECOND

        start_time = time.time()
        operation_count = 0

        while time.time() - start_time < duration:
            try:
                func(test_input)
                operation_count += 1
            except Exception:
                operation_count += 1  # Count exceptions as operations

        actual_duration = time.time() - start_time
        ops_per_second = operation_count / actual_duration

        assert ops_per_second >= min_ops, \
            f"Throughput too low: {ops_per_second:.2f} ops/sec < {min_ops} ops/sec"

    @pytest.mark.performance
    def test_concurrent_performance(
        self,
        func: Callable,
        test_input: Any,
        num_threads: int = 4,
        operations_per_thread: int = 100
    ) -> None:
        """
        Test performance under concurrent load.

        Args:
            func: Function to test
            test_input: Input to use for testing
            num_threads: Number of concurrent threads
            operations_per_thread: Operations per thread
        """
        import threading
        import queue

        results = queue.Queue()
        exceptions = queue.Queue()

        def worker():
            try:
                start_time = time.time()
                for _ in range(operations_per_thread):
                    func(test_input)
                end_time = time.time()
                results.put(end_time - start_time)
            except Exception as e:
                exceptions.put(e)

        # Start concurrent workers
        threads = []
        start_time = time.time()

        for _ in range(num_threads):
            thread = threading.Thread(target=worker)
            thread.start()
            threads.append(thread)

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        total_time = time.time() - start_time

        # Check for exceptions
        exception_count = 0
        while not exceptions.empty():
            exception_count += 1
            exceptions.get()

        # Collect performance metrics
        execution_times = []
        while not results.empty():
            execution_times.append(results.get())

        # Performance assertions
        assert len(execution_times) == num_threads, \
            f"Not all threads completed: {len(execution_times)}/{num_threads}"

        if execution_times:
            avg_thread_time = sum(execution_times) / len(execution_times)
            max_thread_time = max(execution_times)

            # Concurrent execution should be faster than sequential
            sequential_time = avg_thread_time * num_threads
            concurrency_improvement = sequential_time / total_time

            assert concurrency_improvement > 1.5, \
                f"Poor concurrent performance: improvement factor {concurrency_improvement:.2f}"

            # No single thread should take too long
            assert max_thread_time <= self.MAX_EXECUTION_TIME * 2, \
                f"Thread took too long: {max_thread_time:.4f}s"

    def _validate_complexity(
        self,
        metrics: List[Dict[str, float]],
        expected_complexity: str
    ) -> None:
        """
        Validate that execution time follows expected complexity pattern.

        Args:
            metrics: List of performance metrics
            expected_complexity: Expected time complexity
        """
        if len(metrics) < 3:
            return

        # Calculate complexity from metrics
        sizes = [m['size'] for m in metrics]
        times = [m['time'] for m in metrics]

        # Simple complexity check using last two points
        if len(sizes) >= 2:
            size_ratio = sizes[-1] / sizes[-2]
            time_ratio = times[-1] / times[-2] if times[-2] > 0 else float('inf')

            if expected_complexity == "linear":
                assert time_ratio <= size_ratio * 1.5, \
                    f"Complexity worse than linear: time ratio {time_ratio:.2f} > size ratio {size_ratio:.2f}"
            elif expected_complexity == "logarithmic":
                expected_time_ratio = (size_ratio if size_ratio > 1 else 1) ** 0.5
                assert time_ratio <= expected_time_ratio * 2, \
                    f"Complexity worse than logarithmic: {time_ratio:.2f} vs expected {expected_time_ratio:.2f}"

    def _validate_memory_growth(
        self,
        memory_metrics: List[Dict[str, int]]
    ) -> None:
        """
        Validate that memory growth is reasonable.

        Args:
            memory_metrics: List of memory usage metrics
        """
        if len(memory_metrics) < 3:
            return

        # Check for memory leaks by looking at growth pattern
        sizes = [m['size'] for m in memory_metrics]
        memory_usage = [m['memory_increase'] for m in memory_metrics]

        # Memory growth should be proportional to input size
        size_growth = sizes[-1] / sizes[0] if sizes[0] > 0 else 1
        memory_growth = memory_usage[-1] / memory_usage[0] if memory_usage[0] > 0 else 1

        # Allow some overhead but not excessive memory growth
        assert memory_growth <= size_growth * 3, \
            f"Excessive memory growth: {memory_growth:.2f}x vs size growth {size_growth:.2f}x"


class PerformanceTestMixin:
    """
    Mixin class to provide performance test methods for existing test classes.
    """

    def measure_performance(
        self,
        func: Callable,
        test_input: Any,
        iterations: int = 100
    ) -> PerformanceMetrics:
        """
        Measure performance metrics for a function.

        Args:
            func: Function to measure
            test_input: Input to use
            iterations: Number of iterations to run

        Returns:
            PerformanceMetrics object with measurements
        """
        # Warm up
        for _ in range(10):
            func(test_input)

        # Measure
        start_time = time.time()
        for _ in range(iterations):
            func(test_input)
        total_time = time.time() - start_time

        operations_per_second = iterations / total_time
        input_size = len(test_input) if hasattr(test_input, '__len__') else 1

        return PerformanceMetrics(
            execution_time=total_time,
            memory_usage=0,  # Would need psutil for accurate measurement
            input_size=input_size,
            operations_per_second=operations_per_second,
            memory_per_operation=0
        )

    def assert_performance_within_bounds(
        self,
        metrics: PerformanceMetrics,
        max_time: Optional[float] = None,
        min_ops_per_second: Optional[int] = None
    ) -> None:
        """
        Assert that performance metrics are within acceptable bounds.

        Args:
            metrics: Performance metrics to validate
            max_time: Maximum allowed execution time
            min_ops_per_second: Minimum required operations per second
        """
        if max_time:
            assert metrics.execution_time <= max_time, \
                f"Execution time exceeded: {metrics.execution_time:.4f}s > {max_time}s"

        if min_ops_per_second:
            assert metrics.operations_per_second >= min_ops_per_second, \
                f"Operations per second too low: {metrics.operations_per_second:.2f} < {min_ops_per_second}"