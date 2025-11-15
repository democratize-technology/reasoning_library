"""
Comprehensive thread safety tests for keyword extraction and abductive reasoning.

This test module performs stress testing with high concurrency to ensure
the implementation is truly thread-safe and performs well under load.
"""

import pytest
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
import random
import string

from reasoning_library.abductive import (
    _extract_keywords,
    _extract_keywords_with_context,
    generate_hypotheses
)


def generate_random_text(length: int = 100) -> str:
    """Generate random text for testing."""
    words = ['server', 'database', 'network', 'cpu', 'memory', 'slow', 'error',
             'performance', 'deployment', 'application', 'security', 'user',
             'connection', 'timeout', 'latency', 'load', 'cache', 'api']
    return ' '.join(random.choices(words, k=length))


def test_high_concurrency_keyword_extraction():
    """
    Stress test keyword extraction with very high concurrency.

    This test simulates extreme load conditions to verify thread safety
    and performance characteristics under stress.
    """
    # Test parameters
    num_threads = 200  # Very high concurrency
    iterations_per_thread = 50
    total_operations = num_threads * iterations_per_thread

    # Generate varied test inputs
    test_inputs = [generate_random_text(random.randint(20, 100)) for _ in range(100)]

    results = []
    errors = []

    def worker_function(thread_id: int):
        """Worker function that performs keyword extraction."""
        thread_results = []
        thread_errors = []

        for i in range(iterations_per_thread):
            try:
                # Use varied inputs to test different code paths
                text = test_inputs[i % len(test_inputs)]
                result = _extract_keywords(text)

                # Validate result
                assert isinstance(result, list), f"Expected list, got {type(result)}"
                assert len(result) <= 3, f"Too many keywords returned: {len(result)}"

                # All keywords should be strings
                for keyword in result:
                    assert isinstance(keyword, str), f"Keyword not string: {type(keyword)}"
                    assert len(keyword) > 0, "Empty keyword returned"

                thread_results.append((text, result))

            except Exception as e:
                thread_errors.append(f"Thread {thread_id}, iteration {i}: {e}")

        return thread_results, thread_errors

    # Execute with high concurrency
    start_time = time.perf_counter()

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker_function, i) for i in range(num_threads)]

        for future in as_completed(futures, timeout=60):
            try:
                thread_results, thread_errors = future.result()
                results.extend(thread_results)
                errors.extend(thread_errors)
            except Exception as e:
                errors.append(f"Future execution error: {e}")

    end_time = time.perf_counter()
    total_time = end_time - start_time

    # Verify no errors occurred
    assert len(errors) == 0, f"Errors occurred during high concurrency test: {errors}"

    # Verify all operations completed
    assert len(results) == total_operations, \
        f"Expected {total_operations} results, got {len(results)}"

    # Performance check - should complete in reasonable time
    operations_per_second = total_operations / total_time
    print(f"High concurrency performance: {operations_per_second:.0f} operations/second")
    print(f"Total time for {total_operations} operations: {total_time:.2f}s")

    # Should maintain good performance even under high load
    assert operations_per_second > 1000, "Performance degraded too much under load"


def test_concurrent_hypothesis_generation():
    """
    Test concurrent hypothesis generation with various inputs.

    This verifies that the full hypothesis generation pipeline is thread-safe.
    """
    test_cases = [
        {
            "observations": [
                "Server CPU usage is high",
                "Database response times are slow",
                "Network latency increased"
            ],
            "context": "Performance degradation after deployment"
        },
        {
            "observations": [
                "User authentication failing",
                "Access denied errors",
                "Security alerts triggered"
            ],
            "context": "Security issue investigation"
        },
        {
            "observations": [
                "Memory utilization at 90%",
                "Swap usage increasing",
                "Application crashes"
            ],
            "context": "Memory leak investigation"
        }
    ]

    num_threads = 50
    iterations_per_thread = 10

    results = []
    errors = []

    def hypothesis_worker():
        """Worker for concurrent hypothesis generation."""
        worker_results = []
        worker_errors = []

        for i in range(iterations_per_thread):
            try:
                test_case = test_cases[i % len(test_cases)]

                # Test without reasoning chain
                hypotheses = generate_hypotheses(
                    test_case["observations"],
                    reasoning_chain=None,
                    context=test_case["context"],
                    max_hypotheses=3
                )

                # Validate result
                assert isinstance(hypotheses, list), f"Expected list, got {type(hypotheses)}"
                assert len(hypotheses) <= 3, f"Too many hypotheses: {len(hypotheses)}"

                for hypothesis in hypotheses:
                    assert isinstance(hypothesis, dict), f"Hypothesis not dict: {type(hypothesis)}"
                    assert "hypothesis" in hypothesis, "Missing hypothesis text"
                    assert "confidence" in hypothesis, "Missing confidence score"
                    assert 0.0 <= hypothesis["confidence"] <= 1.0, "Invalid confidence range"

                worker_results.append(hypotheses)

            except Exception as e:
                worker_errors.append(f"Hypothesis generation error: {e}")

        return worker_results, worker_errors

    # Run concurrent hypothesis generation
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(hypothesis_worker) for _ in range(num_threads)]

        for future in as_completed(futures, timeout=30):
            try:
                worker_results, worker_errors = future.result()
                results.extend(worker_results)
                errors.extend(worker_errors)
            except Exception as e:
                errors.append(f"Future error: {e}")

    # Verify results
    assert len(errors) == 0, f"Errors in hypothesis generation: {errors}"
    assert len(results) == num_threads * iterations_per_thread, \
        f"Expected {num_threads * iterations_per_thread} results, got {len(results)}"


def test_thread_safety_with_shared_state_validation():
    """
    Test that validates no shared state corruption occurs.

    This test uses deterministic inputs and validates that results
    are always consistent across threads.
    """
    deterministic_inputs = [
        "server database cpu memory slow error performance network",
        "application deployment update restart change database memory",
        "security authentication authorization user role permission access",
        "monitoring metrics alerts cpu threshold disk memory usage",
        "network latency connection timeout load api response"
    ]

    # First, get baseline results sequentially
    baseline_results = {}
    for text in deterministic_inputs:
        baseline_results[text] = _extract_keywords(text)

    # Now test concurrent execution
    num_threads = 100
    concurrent_results = {}

    def concurrent_worker():
        """Worker that extracts keywords from all inputs."""
        worker_results = {}
        for text in deterministic_inputs:
            result = _extract_keywords(text)
            worker_results[text] = result
        return worker_results

    # Run all threads concurrently
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(concurrent_worker) for _ in range(num_threads)]

        for future in as_completed(futures, timeout=15):
            try:
                worker_results = future.result()

                # Merge results
                for text, results_list in worker_results.items():
                    if text not in concurrent_results:
                        concurrent_results[text] = []
                    concurrent_results[text].append(results_list)

            except Exception as e:
                pytest.fail(f"Concurrent worker failed: {e}")

    # Validate all results match baseline
    for text, expected in baseline_results.items():
        actual_results = concurrent_results[text]

        for actual in actual_results:
            assert actual == expected, \
                f"Results differ for '{text}': expected {expected}, got {actual}"

    print(f"Thread safety validation passed: {len(concurrent_results)} inputs, "
          f"{len(actual_results)} concurrent checks per input")


def test_memory_safety_under_concurrent_load():
    """
    Test that memory usage remains stable under concurrent load.

    This test ensures there are no memory leaks or excessive memory usage
    when running many concurrent operations.
    """
    import gc
    import psutil
    import os

    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    num_threads = 100
    iterations_per_thread = 100

    def memory_stress_worker():
        """Worker that performs many operations to stress test memory."""
        for _ in range(iterations_per_thread):
            # Generate and process varied inputs
            text = generate_random_text(50)
            result = _extract_keywords(text)

            # Also test context extraction
            with_context = _extract_keywords_with_context(
                [text, "secondary observation"],
                "test context"
            )

            # Validate results to ensure they're not None
            assert result is not None
            assert with_context is not None

    # Run memory stress test
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(memory_stress_worker) for _ in range(num_threads)]

        # Wait for completion
        for future in as_completed(futures, timeout=60):
            future.result()

    # Force garbage collection
    gc.collect()

    # Check memory usage
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory

    print(f"Memory usage: {initial_memory:.1f}MB -> {final_memory:.1f}MB "
          f"(+{memory_increase:.1f}MB)")

    # Memory increase should be reasonable (less than 100MB for this test)
    assert memory_increase < 100, f"Memory increased too much: {memory_increase:.1f}MB"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])