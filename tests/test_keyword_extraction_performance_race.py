"""
Test to demonstrate performance issue that could be perceived as thread safety problems.

While _extract_keywords is technically thread-safe, recreating sets on every call
causes performance issues under high concurrency that could be mistaken for race conditions.
"""

import pytest
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from reasoning_library.abductive import _extract_keywords


def test_performance_issue_under_high_concurrency():
    """
    Test that demonstrates the performance issue with set recreation.

    Under high concurrency, the overhead of recreating sets on every call
    can cause significant performance degradation that might be perceived as thread safety issues.
    """
    test_text = "server deployment database cpu memory slow error performance network application"

    # Test with increasing concurrency levels
    concurrency_levels = [1, 5, 10, 20, 50]
    performance_results = {}

    for concurrency in concurrency_levels:
        start_time = time.perf_counter()

        # Run multiple iterations per thread to get measurable times
        iterations_per_thread = 100
        total_iterations = concurrency * iterations_per_thread

        def performance_worker():
            for _ in range(iterations_per_thread):
                result = _extract_keywords(test_text)
                # Verify result is reasonable
                assert isinstance(result, list), f"Expected list, got {type(result)}"

        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(performance_worker) for _ in range(concurrency)]

            # Wait for completion
            for future in futures:
                future.result(timeout=30)

        end_time = time.perf_counter()
        total_time = end_time - start_time
        avg_time_per_call = (total_time / total_iterations) * 1000  # ms

        performance_results[concurrency] = avg_time_per_call
        print(f"Concurrency {concurrency:2d}: {avg_time_per_call:.3f}ms per call")

    # The performance degradation should be significant with higher concurrency
    # This demonstrates the inefficiency that needs to be fixed

    # Calculate performance degradation
    baseline = performance_results[1]
    worst_case = performance_results[50]
    degradation_factor = worst_case / baseline

    print(f"Performance degradation: {degradation_factor:.1f}x slower at 50x concurrency")

    # This test documents the performance issue that needs fixing
    # The function is thread-safe but inefficient under high concurrency
    assert degradation_factor > 1.0, "Expected some performance degradation"

    # Document the performance characteristics
    return {
        'performance_results': performance_results,
        'degradation_factor': degradation_factor
    }


def test_set_creation_overhead():
    """
    Directly measure the overhead of set creation in _extract_keywords.
    """
    test_text = "server database cpu memory performance"

    # Count how many sets are created by patching the set constructor
    original_set = set
    set_creation_count = 0

    def counting_set(*args, **kwargs):
        nonlocal set_creation_count
        set_creation_count += 1
        return original_set(*args, **kwargs)

    with patch('builtins.set', side_effect=counting_set):
        # Call the function multiple times
        for _ in range(10):
            result = _extract_keywords(test_text)
            assert isinstance(result, list)

    # Each call to _extract_keywords should create 2 sets (common_words, less_informative)
    # Plus any sets used internally for deduplication
    expected_minimum_sets = 10 * 2  # At least 2 sets per call
    assert set_creation_count >= expected_minimum_sets, \
        f"Expected at least {expected_minimum_sets} set creations, got {set_creation_count}"

    print(f"Set creation overhead: {set_creation_count} sets created for 10 function calls")
    print("This demonstrates the inefficiency that needs optimization")


def test_thread_safety_with_optimized_constants():
    """
    Test that shows the current function is thread-safe but could be improved.

    This test will be used to verify that our optimization maintains thread safety.
    """
    test_text = "server deployment database cpu memory slow error performance"

    # Test high concurrency for determinism
    num_threads = 100
    iterations_per_thread = 50

    results = []

    def thread_worker():
        worker_results = []
        for _ in range(iterations_per_thread):
            result = _extract_keywords(test_text)
            worker_results.append(result)
        return worker_results

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(thread_worker) for _ in range(num_threads)]

        for future in futures:
            try:
                thread_results = future.result(timeout=15)
                results.extend(thread_results)
            except Exception as e:
                pytest.fail(f"Exception in thread safety test: {e}")

    # Verify all results are identical (thread-safe)
    if results:
        first_result = results[0]
        for i, result in enumerate(results[1:], 1):
            if result != first_result:
                pytest.fail(
                    f"Thread safety issue: result {i} = {result}, expected {first_result}"
                )

    # Document that current implementation is thread-safe but inefficient
    print(f"Thread safety confirmed: {len(results)} consistent results under high concurrency")


if __name__ == "__main__":
    # Run the performance test
    print("=== Performance Issue Demonstration ===")
    test_performance_issue_under_high_concurrency()

    print("\n=== Set Creation Overhead Test ===")
    test_set_creation_overhead()

    print("\n=== Thread Safety Verification ===")
    test_thread_safety_with_optimized_constants()

    print("\n=== Conclusion ===")
    print("The function IS thread-safe but inefficient due to set recreation.")
    print("Optimization needed: move common_words and less_informative to module level.")