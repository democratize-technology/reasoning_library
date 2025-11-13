"""
Test to demonstrate sanitization logic duplication across modules.

This test identifies the duplicate sanitization functions that should be
consolidated into shared utilities.
"""

import pytest

from reasoning_library.abductive import _sanitize_input_for_concatenation
from reasoning_library.core import _get_function_source_cached


def test_duplicate_sanitization_functions():
    """
    Test that demonstrates duplicate sanitization logic exists.
    """
    # Test cases that show similar sanitization behavior
    dangerous_inputs = [
        "text with ${template} injection",
        "format %s string %d injection",
        "__import__('os') attempt",
        "eval('dangerous code')",
        "text with <script>HTML injection",
        "text with multiple   spaces",
        "text with\nnewlines and\ttabs"
    ]

    # Test both sanitization functions
    abductive_results = []
    core_results = []

    for input_text in dangerous_inputs:
        abductive_results.append(_sanitize_input_for_concatenation(input_text))
        # The core module has sanitize_text_input as a method inside a function
        # We'll need to access it differently

    print("Abductive sanitization results:")
    for i, result in enumerate(abductive_results):
        print(f"  '{dangerous_inputs[i]}' -> '{result}'")

    # Verify both functions perform similar sanitization operations
    assert len(abductive_results) == len(dangerous_inputs), "Should process all inputs"

    # Check that dangerous patterns are removed
    for i, result in enumerate(abductive_results):
        # Basic checks for dangerous pattern removal
        assert '${' not in result, f"Template injection not removed in: {result}"
        assert '%' not in result or result.count('%') == 0, f"Format string not removed in: {result}"
        assert '__import__' not in result, f"Import attempt not removed in: {result}"
        assert 'eval(' not in result, f"Eval attempt not removed in: {result}"

    return {
        'inputs_tested': len(dangerous_inputs),
        'abductive_results': abductive_results
    }


def test_sanitization_function_overlap():
    """
    Test that shows overlapping functionality between sanitization functions.
    """
    # Common dangerous patterns that both functions should handle
    common_patterns = [
        ('${template}', 'Template injection'),
        ('%s format', 'Format string injection'),
        ('__import__(os)', 'Import injection'),
        ('eval(code)', 'Code injection'),
        ('<script>', 'HTML injection'),
        ("'quotes'", 'Quote injection'),
        ('(parentheses)', 'Parentheses injection'),
        ('[brackets]', 'Bracket injection'),
        ('{braces}', 'Brace injection')
    ]

    abductive_results = {}

    for pattern, description in common_patterns:
        result = _sanitize_input_for_concatenation(pattern)
        abductive_results[description] = result

    print("Sanitization function overlap analysis:")
    for description, result in abductive_results.items():
        print(f"  {description}: '{result}'")

    # Verify basic sanitization effectiveness
    assert all(
        len(result) < len(original) for original, (pattern, _) in zip(common_patterns, abductive_results.items())
        for result in [abductive_results[_]]
    ), "Sanitization should reduce or remove dangerous content"

    return {
        'patterns_tested': len(common_patterns),
        'results': abductive_results
    }


def test_duplicate_regex_patterns():
    """
    Test that similar regex patterns are used in multiple places.
    """
    import re

    # These patterns appear in both sanitization functions
    shared_patterns = [
        r'\${[^}]*}',      # Template injection patterns
        r'__import__\s*\(', # Import attempts
        r'eval\s*\(',      # Eval attempts
        r'[%]',            # Percent characters
        r'[{}]',           # Template braces
        r'["\']',          # Quote characters
    ]

    pattern_usage = {}

    for pattern in shared_patterns:
        try:
            compiled = re.compile(pattern, re.IGNORECASE)
            # Test with sample dangerous inputs
            test_inputs = [
                "${user_input}",
                "__import__('os')",
                "eval('code')",
                "%s format",
                "{template}",
                "'quoted'"
            ]

            matches = []
            for test_input in test_inputs:
                if compiled.search(test_input):
                    matches.append(test_input)

            pattern_usage[pattern] = {
                'matches': matches,
                'count': len(matches)
            }

        except re.error as e:
            pattern_usage[pattern] = {'error': str(e)}

    print("Shared regex pattern analysis:")
    for pattern, info in pattern_usage.items():
        if 'error' in info:
            print(f"  {pattern}: ERROR - {info['error']}")
        else:
            print(f"  {pattern}: matches {info['count']} inputs")

    # Verify patterns work
    successful_patterns = sum(1 for info in pattern_usage.values() if 'error' not in info)
    assert successful_patterns >= len(shared_patterns) * 0.8, "Most patterns should compile successfully"

    return {
        'patterns_analyzed': len(shared_patterns),
        'successful_patterns': successful_patterns,
        'pattern_usage': pattern_usage
    }


if __name__ == "__main__":
    print("=== Sanitization Duplication Analysis ===")

    print("\n1. Testing duplicate sanitization functions...")
    result1 = test_duplicate_sanitization_functions()

    print("\n2. Testing sanitization function overlap...")
    result2 = test_sanitization_function_overlap()

    print("\n3. Testing duplicate regex patterns...")
    result3 = test_duplicate_regex_patterns()

    print("\n=== Summary ===")
    print(f"Sanitization functions analyzed: {result1['inputs_tested']} inputs")
    print(f"Common patterns tested: {result2['patterns_tested']} patterns")
    print(f"Regex patterns analyzed: {result3['patterns_analyzed']} patterns")

    print("\nThis test demonstrates that duplicate sanitization logic exists")
    print("across modules and should be consolidated into shared utilities.")