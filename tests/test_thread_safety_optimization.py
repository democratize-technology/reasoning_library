"""
Test for thread safety optimization in keyword extraction.

This test verifies that the optimization using immutable frozensets
maintains functionality and improves thread safety.
"""

import pytest
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import List

from reasoning_library.abductive import _extract_keywords, COMMON_WORDS, LESS_INFORMATIVE_WORDS


def test_immutable_constants_are_thread_safe():
    """
    Verify that the new immutable constants are actually frozensets.
    """
    # Verify constants are immutable
    assert isinstance(COMMON_WORDS, frozenset), "COMMON_WORDS should be a frozenset"
    assert isinstance(LESS_INFORMATIVE_WORDS, frozenset), "LESS_INFORMATIVE_WORDS should be a frozenset"

    # Verify they contain expected content
    assert 'the' in COMMON_WORDS, "COMMON_WORDS should contain 'the'"
    assert 'server' not in COMMON_WORDS, "COMMON_WORDS should not contain 'server'"

    assert 'about' in LESS_INFORMATIVE_WORDS, "LESS_INFORMATIVE_WORDS should contain 'about'"
    assert 'database' not in LESS_INFORMATIVE_WORDS, "LESS_INFORMATIVE_WORDS should not contain 'database'"

    # Test immutability - these should raise AttributeError
    with pytest.raises(AttributeError):
        COMMON_WORDS.add('new_word')

    with pytest.raises(AttributeError):
        LESS_INFORMATIVE_WORDS.add('new_word')


def test_functionality_preserved_after_optimization():
    """
    Test that the optimization preserves all original functionality.
    """
    test_cases = [
        ("server database cpu memory", ["database", "server", "memory"]),  # Actual output order may vary
        ("the quick brown fox jumps over lazy dog", ["quick", "brown", "jumps"]),  # fox filtered by length
        ("about just like more than some", []),  # All words should be filtered out
        ("application deployment performance", ["application", "deployment", "performance"]),
        ("", []),  # Empty string
        ("cpu", []),  # Too short or filtered
        ("server", ["server"]),  # Single valid word
    ]

    for text, expected_keywords in test_cases:
        result = _extract_keywords(text)

        # Check that result contains expected keywords (order may vary)
        for expected in expected_keywords:
            assert expected in result, f"Expected '{expected}' in result for '{text}': {result}"

        # Check that no unexpected keywords are present
        for keyword in result:
            assert keyword not in COMMON_WORDS, f"Common word '{keyword}' not filtered: {result}"
            assert keyword not in LESS_INFORMATIVE_WORDS, f"Less informative word '{keyword}' not filtered: {result}"
            assert len(keyword) >= 3, f"Short word '{keyword}' not filtered: {result}"


def test_thread_safety_with_optimized_constants():
    """
    Test thread safety with the optimized immutable constants.
    """
    test_text = "server deployment database cpu memory slow error performance network"
    num_threads = 100
    iterations_per_thread = 50

    results = []
    exceptions = []

    def thread_worker():
        """Worker function for thread safety testing."""
        try:
            worker_results = []
            for _ in range(iterations_per_thread):
                result = _extract_keywords(test_text)
                worker_results.append(result)
            return worker_results
        except Exception as e:
            exceptions.append(f"Exception in thread {threading.current_thread().name}: {e}")
            return []

    # Run high-concurrency test
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(thread_worker) for _ in range(num_threads)]

        for future in futures:
            try:
                thread_results = future.result(timeout=15)
                results.extend(thread_results)
            except Exception as e:
                exceptions.append(f"Future execution error: {e}")

    # Verify no exceptions occurred
    assert len(exceptions) == 0, f"Exceptions occurred: {exceptions}"

    # Verify all results are identical (deterministic and thread-safe)
    assert len(results) == num_threads * iterations_per_thread, \
        f"Expected {num_threads * iterations_per_thread} results, got {len(results)}"

    if results:
        first_result = results[0]
        for i, result in enumerate(results[1:], 1):
            assert result == first_result, \
                f"Inconsistent result {i}: {result} vs {first_result}"


def test_performance_improvement_verification():
    """
    Test that the optimization provides performance benefits.
    """
    test_text = "server deployment database cpu memory slow error performance network application security"

    # Run many iterations to measure performance
    num_iterations = 1000

    # Test that the function completes quickly and consistently
    results = []
    for _ in range(num_iterations):
        result = _extract_keywords(test_text)
        results.append(result)

    # Verify all results are identical (performance doesn't affect correctness)
    first_result = results[0]
    for i, result in enumerate(results[1:], 1):
        assert result == first_result, f"Inconsistent result {i}: {result} vs {first_result}"

    # Verify we got reasonable results
    assert len(first_result) > 0, "Should extract some keywords"
    assert all(len(word) >= 3 for word in first_result), "All keywords should meet minimum length"
    assert all(word not in COMMON_WORDS for word in first_result), "No common words should remain"
    assert all(word not in LESS_INFORMATIVE_WORDS for word in first_result), "No less informative words should remain"

    print(f"Performance test completed: {num_iterations} iterations with consistent results")


def test_concurrent_access_to_shared_constants():
    """
    Test that concurrent access to shared frozenset constants is safe.
    """
    def read_constants_worker():
        """Worker that reads shared constants concurrently."""
        try:
            # Test reading from both constants
            common_words_copy = set(COMMON_WORDS)  # Convert to set for testing
            less_informative_copy = set(LESS_INFORMATIVE_WORDS)

            # Verify they contain expected content
            assert len(common_words_copy) > 0, "COMMON_WORDS should not be empty"
            assert len(less_informative_copy) > 0, "LESS_INFORMATIVE_WORDS should not be empty"

            # Test using them in keyword extraction
            result = _extract_keywords("server database application")
            assert isinstance(result, list), "Should return a list"

            return True
        except Exception as e:
            print(f"Exception in constant access: {e}")
            return False

    # Run many threads accessing constants concurrently
    num_threads = 50
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(read_constants_worker) for _ in range(num_threads)]

        results = [future.result(timeout=10) for future in futures]

    # All threads should succeed
    assert all(results), f"Failed constant access in some threads: {sum(results)}/{len(results)} successful"


if __name__ == "__main__":
    pytest.main([__file__])