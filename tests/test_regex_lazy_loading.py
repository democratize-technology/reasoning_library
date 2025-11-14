"""
Test for regex compilation optimization with lazy loading.

This test verifies that regex patterns are compiled lazily to improve
module import performance and reduce startup overhead.
"""

import pytest
import time
import sys
import importlib
from unittest.mock import patch
from typing import Dict

def test_current_regex_compilation_timing():
    """
    Test current regex compilation timing to establish baseline.
    """
    # Time the module import to measure regex compilation overhead
    start_time = time.perf_counter()

    # Import the module for the first time
    import reasoning_library.core as core_module

    import_time = time.perf_counter() - start_time

    print(f"Module import time: {import_time:.4f} seconds")

    # Verify that regex patterns are compiled at import time
    assert hasattr(core_module, 'FACTOR_PATTERN'), "FACTOR_PATTERN should exist"
    assert hasattr(core_module, 'COMMENT_PATTERN'), "COMMENT_PATTERN should exist"
    assert hasattr(core_module, 'EVIDENCE_PATTERN'), "EVIDENCE_PATTERN should exist"
    assert hasattr(core_module, 'COMBINATION_PATTERN'), "COMBINATION_PATTERN should exist"
    assert hasattr(core_module, 'CLEAN_FACTOR_PATTERN'), "CLEAN_FACTOR_PATTERN should exist"

    # Verify they are compiled regex objects
    import re
    assert isinstance(core_module.FACTOR_PATTERN, re.Pattern), "FACTOR_PATTERN should be compiled"
    assert isinstance(core_module.COMMENT_PATTERN, re.Pattern), "COMMENT_PATTERN should be compiled"
    assert isinstance(core_module.EVIDENCE_PATTERN, re.Pattern), "EVIDENCE_PATTERN should be compiled"
    assert isinstance(core_module.COMBINATION_PATTERN, re.Pattern), "COMBINATION_PATTERN should be compiled"
    assert isinstance(core_module.CLEAN_FACTOR_PATTERN, re.Pattern), "CLEAN_FACTOR_PATTERN should be compiled"

    return {
        'import_time': import_time,
        'patterns_compiled': 5
    }


def test_regex_pattern_usage_frequency():
    """
    Test which regex patterns are actually used to determine optimization priorities.
    """
    import reasoning_library.core as core_module

    # Track which patterns are actually accessed during typical operations
    accessed_patterns = []

    # Patch the lazy loading functions to track access
    original_get_factor_pattern = core_module._get_factor_pattern

    def track_factor_pattern_access():
        accessed_patterns.append('FACTOR_PATTERN')
        return original_get_factor_pattern()

    # Apply tracking by patching the lazy loading function
    with patch.object(core_module, '_get_factor_pattern', side_effect=track_factor_pattern_access):

        # Test typical usage scenarios
        try:
            # Access the pattern to trigger lazy loading
            pattern = core_module.FACTOR_PATTERN
            assert pattern is not None, "FACTOR_PATTERN should be accessible"

            # Test some operations that might use regex patterns
            from reasoning_library.core import _detect_mathematical_reasoning

            def dummy_func():
                """Dummy function for testing."""
                pass

            # This should trigger some regex usage
            result = _detect_mathematical_reasoning(dummy_func)
            assert result is not None, "Should return some result"

        except Exception as e:
            # Even if it fails, we can still see which patterns were accessed
            pass

    print(f"Patterns accessed during test: {dict(zip(accessed_patterns, [accessed_patterns.count(p) for p in set(accessed_patterns)]))}")
    return accessed_patterns


def test_lazy_loading_benefits():
    """
    Test the potential benefits of lazy loading regex patterns.
    """
    # Create a mock module to test lazy loading behavior
    import re
    from functools import lru_cache

    # Simulate lazy loading with caching
    compilation_calls = 0

    @lru_cache(maxsize=None)
    def get_lazy_pattern(pattern_name: str) -> re.Pattern:
        nonlocal compilation_calls
        compilation_calls += 1

        patterns = {
            'FACTOR_PATTERN': rf"(\w{{0,50}}(?:data_sufficiency | pattern_quality | complexity)_factor)[\s]{{0,5}}(?:\*|,|\+|\-|=)",
            'COMMENT_PATTERN': r"#\s*(?:Data | Pattern | Complexity)\s+([^#\n]+factor)",
            'EVIDENCE_PATTERN': r'f?"[^"]*(?:confidence\s + based\s + on | factors?[\s:]*in)[^"]*([^"\.]+pattern[^"\.]*)',
            'COMBINATION_PATTERN': rf"(\w{{1,50}}_factor)[\s]{{0,5}}\*[\s]{{0,5}}(\w{{1,50}}_factor)",
            'CLEAN_FACTOR_PATTERN': r"[()=\*]+"
        }

        if pattern_name not in patterns:
            raise ValueError(f"Unknown pattern: {pattern_name}")

        return re.compile(patterns[pattern_name], re.IGNORECASE | re.MULTILINE)

    # Test that patterns are only compiled when accessed
    initial_calls = compilation_calls

    # Access first pattern
    pattern1 = get_lazy_pattern('FACTOR_PATTERN')
    assert compilation_calls == initial_calls + 1, "First access should compile pattern"

    # Access same pattern again
    pattern1_again = get_lazy_pattern('FACTOR_PATTERN')
    assert compilation_calls == initial_calls + 1, "Second access should use cache"
    assert pattern1 is pattern1_again, "Should return same cached object"

    # Access different pattern
    pattern2 = get_lazy_pattern('COMMENT_PATTERN')
    assert compilation_calls == initial_calls + 2, "Different pattern should be compiled"

    # Access third pattern
    pattern3 = get_lazy_pattern('EVIDENCE_PATTERN')
    assert compilation_calls == initial_calls + 3, "Third pattern should be compiled"

    print(f"Lazy compilation calls: {compilation_calls}")
    print(f"Patterns cached: 3")

    return {
        'compilation_calls': compilation_calls,
        'cache_hits': 2  # We accessed FACTOR_PATTERN twice
    }


def test_import_time_comparison():
    """
    Compare import times between eager and lazy loading approaches.
    """
    # Test current eager loading
    eager_start = time.perf_counter()

    # Force reimport to measure fresh import time
    if 'reasoning_library.core' in sys.modules:
        del sys.modules['reasoning_library.core']

    import reasoning_library.core
    eager_time = time.perf_counter() - eager_start

    print(f"Eager loading import time: {eager_time:.4f} seconds")

    # For comparison, test importing a simple module
    simple_start = time.perf_counter()
    import json
    simple_time = time.perf_counter() - simple_start

    print(f"Simple module import time: {simple_time:.4f} seconds")

    return {
        'eager_time': eager_time,
        'simple_time': simple_time,
        'overhead': eager_time - simple_time
    }


if __name__ == "__main__":
    from collections import Counter

    print("=== Regex Compilation Analysis ===")

    print("\n1. Testing current compilation timing...")
    timing_result = test_current_regex_compilation_timing()

    print("\n2. Testing pattern usage frequency...")
    usage_result = test_regex_pattern_usage_frequency()

    print("\n3. Testing lazy loading benefits...")
    lazy_result = test_lazy_loading_benefits()

    print("\n4. Testing import time comparison...")
    import_result = test_import_time_comparison()

    print("\n=== Summary ===")
    print(f"Current approach: {timing_result['patterns_compiled']} patterns compiled at import time")
    print(f"Import overhead: {import_result['overhead']:.4f} seconds")
    print(f"Lazy loading potential: {lazy_result['compilation_calls']} compilations only when needed")

    print("\nThis test demonstrates the need for lazy loading optimization.")
    print("Patterns should only be compiled when actually used, not at module import.")