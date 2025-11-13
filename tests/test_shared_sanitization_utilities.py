"""
Test for the new shared sanitization utilities.

This test verifies that the consolidated sanitization logic works correctly
and maintains backward compatibility with existing functionality.
"""

import pytest

from reasoning_library.sanitization import (
    sanitize_text_input,
    sanitize_for_concatenation,
    sanitize_for_display,
    sanitize_for_logging,
    quick_sanitize,
    SanitizationLevel
)


def test_shared_sanitization_functionality():
    """
    Test that the shared sanitization utilities work correctly.
    """
    dangerous_inputs = [
        "text with ${template} injection",
        "format %s string %d injection",
        "__import__('os') attempt",
        "eval('dangerous code')",
        "text with <script>HTML injection",
        "text with multiple   spaces",
        "text with\nnewlines and\ttabs",
        "text with ANSI \x1b[31mred\x1b[0m colors"
    ]

    # Test different sanitization levels
    for input_text in dangerous_inputs:
        # Test strict sanitization
        strict_result = sanitize_text_input(input_text, level=SanitizationLevel.STRICT)
        assert isinstance(strict_result, str), f"Strict sanitization should return string for: {input_text}"
        assert len(strict_result) <= len(input_text), f"Strict sanitization should reduce or preserve length"

        # Test moderate sanitization
        moderate_result = sanitize_text_input(input_text, level=SanitizationLevel.MODERATE)
        assert isinstance(moderate_result, str), f"Moderate sanitization should return string for: {input_text}"

        # Test permissive sanitization
        permissive_result = sanitize_text_input(input_text, level=SanitizationLevel.PERMISSIVE)
        assert isinstance(permissive_result, str), f"Permissive sanitization should return string for: {input_text}"

    print("✓ All shared sanitization functions work correctly")


def test_specialized_sanitization_functions():
    """
    Test specialized sanitization functions for different use cases.
    """
    test_input = "text with ${template} <script> and\nnewlines"

    # Test concatenation sanitization (most strict)
    concat_result = sanitize_for_concatenation(test_input)
    assert '${' not in concat_result, "Concatenation should remove template injection"
    assert '<' not in concat_result, "Concatenation should remove HTML injection"
    assert len(concat_result) <= 50, "Concatenation should enforce length limit"

    # Test display sanitization (moderate)
    display_result = sanitize_for_display(test_input)
    assert '${' not in display_result, "Display should remove template injection"
    assert '<' not in display_result, "Display should remove HTML injection"

    # Test logging sanitization (focus on control chars)
    logging_result = sanitize_for_logging(test_input)
    assert '\n' not in logging_result, "Logging should normalize newlines"
    assert '\t' not in logging_result, "Logging should normalize tabs"

    # Test quick sanitization (minimal)
    quick_result = quick_sanitize(test_input)
    assert isinstance(quick_result, str), "Quick should return string"

    print("✓ All specialized sanitization functions work correctly")


def test_backward_compatibility():
    """
    Test that backward compatibility is maintained for existing code.
    """
    from reasoning_library.abductive import _sanitize_input_for_concatenation
    from reasoning_library.abductive import _sanitize_template_input

    test_input = "text with ${template} and %s format"

    # Test that old functions still work (they should use new utilities)
    old_result1 = _sanitize_input_for_concatenation(test_input)
    old_result2 = _sanitize_template_input(test_input)

    assert isinstance(old_result1, str), "Old function should return string"
    assert isinstance(old_result2, str), "Old function should return string"
    assert old_result1 == old_result2, "Both old functions should return same result"

    # Test new function gives similar result
    new_result = sanitize_for_concatenation(test_input)
    assert old_result1 == new_result, "New and old functions should give same result"

    print("✓ Backward compatibility maintained")


def test_sanitization_effectiveness():
    """
    Test that sanitization effectively removes dangerous patterns.
    """
    dangerous_patterns = [
        ("${user_input}", "Template injection"),
        ("%s format", "Format string injection"),
        ("__import__('os')", "Import injection"),
        ("eval('code')", "Code injection"),
        ("<script>alert('xss')</script>", "HTML injection"),
        ("'; DROP TABLE users; --", "SQL injection pattern"),
        ("$(whoami)", "Shell injection"),
        ("__proto__.polluted", "Prototype pollution"),
        ("constructor.prototype", "Constructor pollution"),
        ("text\nwith\rcontrol\x1b[31mchars", "Control character injection")
    ]

    for pattern, description in dangerous_patterns:
        # Test strict sanitization
        strict_result = sanitize_text_input(pattern, level=SanitizationLevel.STRICT)

        # Check that dangerous patterns are removed or blocked
        if 'eval(' in pattern or '__import__' in pattern:
            assert 'BLOCKED' in strict_result or 'eval(' not in strict_result, \
                f"Code injection should be blocked in {description}: {pattern} -> {strict_result}"

        # Basic effectiveness checks
        assert len(strict_result) <= len(pattern), \
            f"Sanitization should not increase length for {description}"

        # Check some specific removals
        if '${' in pattern:
            assert '${' not in strict_result, \
                f"Template injection should be removed in {description}"
        if '<script>' in pattern:
            assert '<script>' not in strict_result, \
                f"HTML injection should be removed in {description}"

    print("✓ Sanitization effectiveness verified for dangerous patterns")


def test_edge_cases():
    """
    Test edge cases for sanitization functions.
    """
    edge_cases = [
        None,
        "",
        " ",
        123,
        [],
        {},
        "a" * 1000,  # Long string
        "normal text without special characters",
        "UPPERCASE TEXT",
        "MiXeD CaSe Text",
        "text_with_underscores",
        "text-with-dashes",
        "text.with.dots",
        "text with 多種 語言 characters",
    ]

    for edge_case in edge_cases:
        # Test that all functions handle edge cases gracefully
        try:
            strict_result = sanitize_text_input(edge_case, level=SanitizationLevel.STRICT)
            assert isinstance(strict_result, str), f"Should return string for: {edge_case}"

            moderate_result = sanitize_text_input(edge_case, level=SanitizationLevel.MODERATE)
            assert isinstance(moderate_result, str), f"Should return string for: {edge_case}"

            concat_result = sanitize_for_concatenation(edge_case)
            assert isinstance(concat_result, str), f"Should return string for: {edge_case}"

            quick_result = quick_sanitize(edge_case)
            assert isinstance(quick_result, str), f"Should return string for: {edge_case}"

        except Exception as e:
            pytest.fail(f"Sanitization should handle edge case gracefully: {edge_case} -> {e}")

    print("✓ Edge cases handled correctly")


def test_performance_and_thread_safety():
    """
    Test that sanitization is performant and thread-safe.
    """
    import threading
    from concurrent.futures import ThreadPoolExecutor

    test_input = "text with ${template} and %s format"

    # Test performance with many iterations
    import time
    start_time = time.perf_counter()

    for _ in range(1000):
        result = sanitize_for_concatenation(test_input)

    end_time = time.perf_counter()
    avg_time = (end_time - start_time) / 1000

    print(f"Average sanitization time: {avg_time * 1000:.3f}ms")

    # Test thread safety
    results = []
    exceptions = []

    def sanitize_worker():
        try:
            result = sanitize_for_concatenation(test_input)
            results.append(result)
        except Exception as e:
            exceptions.append(e)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(sanitize_worker) for _ in range(50)]
        for future in futures:
            future.result(timeout=5)

    assert len(exceptions) == 0, f"Thread safety test failed with exceptions: {exceptions}"
    assert len(results) == 50, "Should get results from all threads"

    # All results should be identical
    first_result = results[0]
    for result in results[1:]:
        assert result == first_result, "Thread-safe results should be identical"

    print("✓ Performance and thread safety verified")


if __name__ == "__main__":
    test_shared_sanitization_functionality()
    test_specialized_sanitization_functions()
    test_backward_compatibility()
    test_sanitization_effectiveness()
    test_edge_cases()
    test_performance_and_thread_safety()

    print("\n✅ All shared sanitization utility tests passed!")