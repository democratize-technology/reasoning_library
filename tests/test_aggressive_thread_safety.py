"""
Aggressive thread safety tests for keyword extraction.

This test tries to find edge cases and race conditions that might
only appear under specific conditions or timing.
"""

import pytest
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from reasoning_library.abductive import _extract_keywords


def test_stress_test_with_edge_cases():
    """
    Stress test with edge case inputs that might expose race conditions.
    """
    # Edge case inputs that could cause issues
    edge_cases = [
        "",  # Empty string
        "a",  # Very short
        "a" * 100,  # Very long single character
        "normal text with normal words",
        "UPPERCASE lowercase MiXeD CaSe",
        "123 456 789 numbers everywhere",
        "!@# $%^ &*() special characters",
        "中文 characters unicode test",
        "multiple\nlines\nof\ntext",
        "tabs\tand\tspaces  mixed",
        "repeated repeated repeated repeated repeated words",
        "server server server server cpu cpu cpu cpu"
    ]

    num_threads = 20
    iterations_per_thread = 50

    results = {}
    exceptions = []

    def test_worker():
        """Worker that tests all edge cases."""
        for iteration in range(iterations_per_thread):
            for i, text in enumerate(edge_cases):
                try:
                    # Add some timing variability
                    time.sleep(0.0001 * (iteration % 5))

                    result = _extract_keywords(text)

                    # Store result for this edge case
                    if i not in results:
                        results[i] = []
                    results[i].append(result)

                except Exception as e:
                    exceptions.append(f"Exception on edge case {i} ('{text[:20]}...'): {e}")

    # Run with high concurrency
    threads = []
    for _ in range(num_threads):
        thread = threading.Thread(target=test_worker)
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join(timeout=30)
        if thread.is_alive():
            pytest.fail("Thread did not complete within timeout")

    # Check for exceptions
    assert len(exceptions) == 0, f"Exceptions occurred: {exceptions}"

    # Verify consistency of results for each edge case
    for case_index, case_results in results.items():
        if not case_results:
            continue

        # All results for the same input should be identical
        first_result = case_results[0]
        for i, result in enumerate(case_results[1:], 1):
            if result != first_result:
                pytest.fail(
                    f"Inconsistent results for edge case {case_index}: "
                    f"iteration {i} got {result}, expected {first_result}"
                )


def test_concurrent_shared_regex_access():
    """
    Test concurrent access to the shared regex pattern.

    This specifically tests the KEYWORD_EXTRACTION_PATTERN which is
    a module-level shared resource.
    """
    # Texts that will heavily exercise the regex
    regex_heavy_texts = [
        "words" * 1000,  # Many repeated words
        "a" * 5000,  # At the length limit
        "mixed123content456with789numbers0",
        "special!@#$%^&*()characters" * 100,
        "UPPER lower MiXeD case text" * 50
    ]

    num_threads = 50
    iterations_per_thread = 20

    results = []
    regex_exceptions = []

    def regex_worker():
        """Worker that heavily exercises regex operations."""
        for iteration in range(iterations_per_thread):
            for text in regex_heavy_texts:
                try:
                    result = _extract_keywords(text)
                    results.append(result)
                except Exception as e:
                    # Look specifically for regex-related errors
                    error_str = str(e).lower()
                    if any(keyword in error_str for keyword in ['regex', 'pattern', 'compile', 'match']):
                        regex_exceptions.append(f"Regex error: {e}")
                    else:
                        regex_exceptions.append(f"Other error: {e}")

    # Run concurrent regex stress test
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(regex_worker) for _ in range(num_threads)]

        for future in as_completed(futures):
            try:
                future.result(timeout=15)
            except Exception as e:
                regex_exceptions.append(f"Thread execution error: {e}")

    # Check for regex-specific exceptions
    assert len(regex_exceptions) == 0, f"Regex exceptions occurred: {regex_exceptions}"

    # Verify we got the expected number of results
    expected_results = num_threads * iterations_per_thread * len(regex_heavy_texts)
    assert len(results) == expected_results, \
        f"Expected {expected_results} results, got {len(results)}"


def test_memory_safety_under_load():
    """
    Test memory usage and potential memory leaks under concurrent load.
    """
    import gc
    import psutil
    import os

    # Get initial memory usage
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    # Large texts that could cause memory pressure
    large_texts = [
        "word " * 1000,  # 1000 words
        "text with server database cpu memory performance " * 200,
        "deployment error network latency application " * 300,
    ]

    num_threads = 30
    iterations_per_thread = 10

    def memory_worker():
        """Worker that processes large texts."""
        for _ in range(iterations_per_thread):
            for text in large_texts:
                result = _extract_keywords(text)
                # Force some garbage collection
                del result

    # Run memory stress test
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(memory_worker) for _ in range(num_threads)]

        for future in as_completed(futures):
            future.result(timeout=20)

    # Force garbage collection
    gc.collect()

    # Check final memory usage
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory

    print(f"Memory usage: {initial_memory:.1f}MB -> {final_memory:.1f}MB (increase: {memory_increase:.1f}MB)")

    # Memory increase should be reasonable (less than 100MB)
    assert memory_increase < 100, f"Excessive memory increase: {memory_increase:.1f}MB"


def test_deterministic_sorting_under_concurrency():
    """
    Test that the sorting in keyword extraction is deterministic.

    This specifically tests line 235: unique_keywords.sort(key=lambda w: (-len(w), keywords.index(w)))
    """
    test_text = "longword server mediumword performance short cpu memory database"

    # Extract many times concurrently to see if sorting is always consistent
    num_threads = 40
    results = []

    def sorting_worker():
        result = _extract_keywords(test_text)
        return result

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(sorting_worker) for _ in range(num_threads)]

        for future in as_completed(futures):
            try:
                result = future.result(timeout=10)
                results.append(result)
            except Exception as e:
                pytest.fail(f"Exception in sorting test: {e}")

    # All results should be identical (same order)
    if results:
        first_result = results[0]
        for i, result in enumerate(results[1:], 1):
            if result != first_result:
                pytest.fail(
                    f"Sorting inconsistency: result {i} = {result}, expected {first_result}"
                )


if __name__ == "__main__":
    pytest.main([__file__])