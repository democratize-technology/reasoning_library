"""
Test for thread safety in keyword extraction function.

This test verifies that concurrent access to keyword extraction
does not cause race conditions or data corruption.
"""

import pytest
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict

from reasoning_library.abductive import _extract_keywords, _extract_keywords_with_context


def test_concurrent_keyword_extraction_safety():
    """
    Test that keyword extraction is thread-safe under concurrent load.

    This test simulates multiple threads calling _extract_keywords
    simultaneously to detect race conditions.
    """
    # Test data that would exercise the keyword extraction logic
    test_texts = [
        "server deployment update restart change database cpu memory slow error",
        "application performance network latency load api connection timeout slow response",
        "database cache memory disk network application deployment code new change",
        "monitoring metrics alerts cpu threshold disk memory usage application server",
        "security authentication authorization user role permission access control system"
    ]

    # Run extraction multiple times in parallel threads
    num_threads = 10
    iterations_per_thread = 20

    results = []
    exceptions = []

    def extract_worker(text: str, iterations: int) -> List[str]:
        """Worker function for concurrent keyword extraction."""
        worker_results = []
        for i in range(iterations):
            try:
                result = _extract_keywords(text)
                worker_results.append(result)
            except Exception as e:
                exceptions.append(f"Thread {threading.current_thread().name}: {e}")
                break
        return worker_results

    # Create threads for concurrent execution
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []

        for i in range(num_threads):
            text = test_texts[i % len(test_texts)]
            future = executor.submit(extract_worker, text, iterations_per_thread)
            futures.append(future)

        # Collect results
        for future in as_completed(futures):
            try:
                thread_results = future.result(timeout=10)
                results.extend(thread_results)
            except Exception as e:
                exceptions.append(f"Future execution error: {e}")

    # Verify no exceptions occurred
    assert len(exceptions) == 0, f"Exceptions occurred during concurrent execution: {exceptions}"

    # Verify all results are valid (non-empty lists of strings)
    assert len(results) == num_threads * iterations_per_thread, \
        f"Expected {num_threads * iterations_per_thread} results, got {len(results)}"

    for i, result in enumerate(results):
        assert isinstance(result, list), f"Result {i} is not a list: {type(result)}"
        # Empty results are acceptable for some inputs, but when not empty, should be strings
        if result:
            for word in result:
                assert isinstance(word, str), f"Result {i} contains non-string: {type(word)}"


def test_concurrent_keywords_with_context_safety():
    """
    Test that keyword extraction with context is thread-safe.
    """
    observations = [
        "Server CPU usage is high",
        "Database response times are slow",
        "Network latency increased",
        "Memory utilization at 90%"
    ]
    context = "System performance degradation after recent deployment"

    num_threads = 8
    results = []
    exceptions = []

    def extract_with_context_worker():
        """Worker function for concurrent keyword extraction with context."""
        try:
            result = _extract_keywords_with_context(observations, context)
            return result
        except Exception as e:
            exceptions.append(f"Thread {threading.current_thread().name}: {e}")
            return None

    # Run concurrent extractions
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(extract_with_context_worker) for _ in range(num_threads)]

        for future in as_completed(futures):
            try:
                result = future.result(timeout=10)
                if result is not None:
                    results.append(result)
            except Exception as e:
                exceptions.append(f"Future execution error: {e}")

    # Verify no exceptions occurred
    assert len(exceptions) == 0, f"Exceptions occurred: {exceptions}"

    # Verify all results are consistent and valid
    assert len(results) == num_threads, f"Expected {num_threads} results, got {len(results)}"

    # All results should be identical since input is the same
    first_result = results[0]
    for i, result in enumerate(results[1:], 1):
        assert result == first_result, f"Result {i} differs from first result: {result} vs {first_result}"

    # Verify result structure
    assert isinstance(first_result, dict), "Result should be a dictionary"
    expected_keys = {"actions", "components", "issues"}
    assert set(first_result.keys()) == expected_keys, f"Missing keys: {expected_keys - set(first_result.keys())}"


def test_keyword_extraction_determinism_under_load():
    """
    Test that keyword extraction produces deterministic results under concurrent load.
    """
    test_text = "deployment server database cpu memory slow error performance network api connection timeout"

    # Extract keywords sequentially first to get baseline
    baseline_results = []
    for _ in range(10):
        result = _extract_keywords(test_text)
        baseline_results.append(result)

    # All sequential results should be identical
    assert all(result == baseline_results[0] for result in baseline_results), \
        "Sequential results are not deterministic"

    # Now extract concurrently
    concurrent_results = []

    def concurrent_worker():
        return _extract_keywords(test_text)

    num_concurrent = 20
    with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
        futures = [executor.submit(concurrent_worker) for _ in range(num_concurrent)]

        for future in as_completed(futures):
            try:
                result = future.result(timeout=5)
                concurrent_results.append(result)
            except Exception as e:
                pytest.fail(f"Exception in concurrent execution: {e}")

    # All concurrent results should match baseline
    baseline = baseline_results[0]
    assert len(concurrent_results) == num_concurrent, \
        f"Expected {num_concurrent} concurrent results, got {len(concurrent_results)}"

    for i, result in enumerate(concurrent_results):
        assert result == baseline, \
            f"Concurrent result {i} differs from baseline: {result} vs {baseline}"


def test_keyword_extraction_no_shared_state_corruption():
    """
    Test that concurrent extraction doesn't corrupt shared state.

    This test runs extractions with different inputs concurrently
    and verifies each result is correct for its input.
    """
    # Different test texts that should produce different keyword sets
    test_cases = [
        ("server cpu memory slow performance", ["server", "memory", "slow", "performance"]),  # cpu might be filtered out
        ("database network latency connection", ["database", "network", "latency", "connection"]),
        ("application deployment error processing", ["application", "deployment", "error", "processing"]),
        ("security authentication user access", ["security", "authentication", "user", "access"]),
        ("performance metrics monitoring analysis", ["performance", "metrics", "monitoring", "analysis"])
    ]

    num_iterations = 10
    results = {}

    def extract_worker(test_input: str, expected_keywords: List[str]):
        """Worker that extracts keywords and verifies correctness."""
        for iteration in range(num_iterations):
            result = _extract_keywords(test_input)

            # Result should contain expected keywords (order may vary)
            for expected in expected_keywords:
                if expected not in result:
                    pytest.fail(f"Expected keyword '{expected}' not found in result: {result}")

            # Store result for this input
            if test_input not in results:
                results[test_input] = []
            results[test_input].append(result)

    # Run all test cases concurrently
    with ThreadPoolExecutor(max_workers=len(test_cases)) as executor:
        futures = []

        for test_input, expected_keywords in test_cases:
            future = executor.submit(extract_worker, test_input, expected_keywords)
            futures.append(future)

        # Wait for all to complete
        for future in as_completed(futures):
            future.result(timeout=10)

    # Verify all test cases produced results
    assert len(results) == len(test_cases), "Not all test cases produced results"

    # Verify results are consistent within each test case
    for test_input, input_results in results.items():
        assert len(input_results) == num_iterations, \
            f"Expected {num_iterations} results for input '{test_input}', got {len(input_results)}"

        # All results for the same input should be identical
        first_result = input_results[0]
        for i, result in enumerate(input_results[1:], 1):
            assert result == first_result, \
                f"Inconsistent results for input '{test_input}': {result} vs {first_result}"


if __name__ == "__main__":
    pytest.main([__file__])