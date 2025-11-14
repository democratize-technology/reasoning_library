"""
Test to verify that regex lazy loading optimization works correctly.

This test verifies that regex patterns are compiled lazily and that
the functionality is preserved.
"""

import pytest
import time
import sys
import importlib
from unittest.mock import patch
from typing import Dict

from reasoning_library.core import (
    _get_factor_pattern,
    _get_comment_pattern,
    _get_evidence_pattern,
    _get_combination_pattern,
    _get_clean_factor_pattern,
    _extract_confidence_factors
)


def test_lazy_loading_functionality():
    """
    Test that lazy loading functions work correctly.
    """
    import re

    # Test that patterns are compiled on first access
    pattern1 = _get_factor_pattern()
    assert isinstance(pattern1, re.Pattern), "Should return compiled Pattern object"

    # Test that subsequent accesses return the same object (cached)
    pattern1_again = _get_factor_pattern()
    assert pattern1 is pattern1_again, "Should return same cached object"

    # Test that all lazy loading functions work
    patterns = [
        _get_factor_pattern(),
        _get_comment_pattern(),
        _get_evidence_pattern(),
        _get_combination_pattern(),
        _get_clean_factor_pattern()
    ]

    for pattern in patterns:
        assert isinstance(pattern, re.Pattern), f"Should return compiled Pattern object: {pattern}"


def test_lazy_loading_preserves_functionality():
    """
    Test that lazy loading preserves all original functionality.
    """
    # Test with sample source code that should match patterns
    sample_source = '''
    def calculate_confidence(base_confidence, data_sufficiency_factor, pattern_quality_factor):
        # Data quality affects confidence calculation
        confidence = base_confidence * data_sufficiency_factor
        # Pattern complexity influences reliability
        return confidence * pattern_quality_factor
    '''

    sample_docstring = "Confidence calculation based on data sufficiency and pattern quality"

    # Test that confidence factor extraction works with lazy-loaded patterns
    factors = _extract_confidence_factors(sample_source, sample_docstring)

    # Should extract the expected factors
    assert len(factors) > 0, "Should extract some confidence factors"

    # Check that specific factors are found (these depend on the regex patterns)
    factor_text = ' '.join(factors).lower()
    assert 'data sufficiency' in factor_text or 'pattern quality' in factor_text, \
        f"Should find expected factors in: {factor_text}"


def test_lazy_loading_performance_benefit():
    """
    Test that lazy loading provides performance benefits.
    """
    import re
    from functools import lru_cache

    # Clear any existing cache to test from scratch
    _get_factor_pattern.cache_clear()
    _get_comment_pattern.cache_clear()
    _get_evidence_pattern.cache_clear()
    _get_combination_pattern.cache_clear()
    _get_clean_factor_pattern.cache_clear()

    # Test compilation time for first access
    start_time = time.perf_counter()
    pattern1 = _get_factor_pattern()
    first_access_time = time.perf_counter() - start_time

    # Test access time for cached access (should be much faster)
    start_time = time.perf_counter()
    pattern1_cached = _get_factor_pattern()
    cached_access_time = time.perf_counter() - start_time

    # Verify caching works
    assert pattern1 is pattern1_cached, "Should return same cached object"
    assert cached_access_time < first_access_time, "Cached access should be faster"

    print(f"First access: {first_access_time:.6f}s")
    print(f"Cached access: {cached_access_time:.6f}s")
    print(f"Speedup: {first_access_time / cached_access_time:.1f}x")


def test_lazy_loading_thread_safety():
    """
    Test that lazy loading is thread-safe.
    """
    import threading
    from concurrent.futures import ThreadPoolExecutor

    patterns = []
    exceptions = []

    def worker():
        try:
            # Access all patterns from multiple threads
            worker_patterns = [
                _get_factor_pattern(),
                _get_comment_pattern(),
                _get_evidence_pattern(),
                _get_combination_pattern(),
                _get_clean_factor_pattern()
            ]
            patterns.append(worker_patterns)
        except Exception as e:
            exceptions.append(f"Exception in thread {threading.current_thread().name}: {e}")

    # Run multiple threads concurrently
    num_threads = 10
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker) for _ in range(num_threads)]

        for future in futures:
            future.result(timeout=10)

    # Verify no exceptions occurred
    assert len(exceptions) == 0, f"Exceptions occurred: {exceptions}"

    # Verify all threads got patterns
    assert len(patterns) == num_threads, f"Expected {num_threads} results, got {len(patterns)}"

    # Verify all threads got the same pattern objects (shared cache)
    first_thread_patterns = patterns[0]
    for i, thread_patterns in enumerate(patterns[1:], 1):
        for j, pattern in enumerate(thread_patterns):
            assert pattern is first_thread_patterns[j], \
                f"Thread {i} pattern {j} should be same object as thread 0 pattern {j}"


def test_lazy_loading_with_no_source_code():
    """
    Test that lazy loading handles edge cases gracefully.
    """
    # Test with empty source code
    factors = _extract_confidence_factors("", "")
    assert isinstance(factors, list), "Should return list even for empty input"

    # Test with source code that has no matching patterns
    no_match_source = '''
    def simple_function():
        return "hello world"
    '''
    factors = _extract_confidence_factors(no_match_source, "Simple function")
    assert isinstance(factors, list), "Should return list for no-match input"


def test_backward_compatibility():
    """
    Test that the old pattern variables still exist for compatibility.
    """
    import reasoning_library.core as core_module

    # These should exist and be immediately accessible (backward compatibility with __getattr__)
    assert hasattr(core_module, 'FACTOR_PATTERN'), "FACTOR_PATTERN should exist for compatibility"
    assert hasattr(core_module, 'COMMENT_PATTERN'), "COMMENT_PATTERN should exist for compatibility"
    assert hasattr(core_module, 'EVIDENCE_PATTERN'), "EVIDENCE_PATTERN should exist for compatibility"
    assert hasattr(core_module, 'COMBINATION_PATTERN'), "COMBINATION_PATTERN should exist for compatibility"
    assert hasattr(core_module, 'CLEAN_FACTOR_PATTERN'), "CLEAN_FACTOR_PATTERN should exist for compatibility"

    # They should be re.Pattern objects (lazily compiled on first access via __getattr__)
    import re
    assert isinstance(core_module.FACTOR_PATTERN, re.Pattern), "FACTOR_PATTERN should be re.Pattern object"
    assert isinstance(core_module.COMMENT_PATTERN, re.Pattern), "COMMENT_PATTERN should be re.Pattern object"


if __name__ == "__main__":
    pytest.main([__file__])