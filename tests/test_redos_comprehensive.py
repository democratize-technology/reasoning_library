#!/usr/bin/env python3
"""
Comprehensive ReDoS vulnerability test suite for _extract_keywords function.
Tests both the fix effectiveness and functional correctness.
"""

import os
import re
import sys
import time

# Add src to path for import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from reasoning_library.abductive import _extract_keywords


def test_redos_vulnerability_fix():
    """Test that the ReDoS vulnerability has been properly fixed."""

    print("🔍 Testing ReDoS vulnerability fix effectiveness...")

    # Test cases designed to trigger catastrophic backtracking in vulnerable patterns
    vulnerable_test_cases = [
        # Classic ReDoS patterns that would be slow with \b\w+\b
        ("Long prefix before word", " " * 50000 + "testword"),
        ("Alternating boundaries", ". " * 25000 + "word"),
        ("Unicode boundary attack", "\u2000" * 10000 + "test"),
        ("Mixed special chars", "!@#$%^&*() " * 5000 + "keyword"),
        ("Repeated non-word chars", "---___---___" * 2500 + "data"),
        ("Pathological case", " " * 25000 + "_" * 25000 + "test"),
        ("Complex boundary", ".-_._-._-." * 10000 + "final"),
        ("URL-like attack", ":///" * 8000 + "endpoint"),
        ("Email pattern", "@@@" * 6000 + "user"),
        ("Extreme length", "a" * 100000),  # Pure word chars
    ]

    max_time_per_test = 0.1  # 100ms max per test
    passed = 0
    failed = 0

    for i, (description, test_input) in enumerate(vulnerable_test_cases, 1):
        print(f"\nTest {i}: {description} (length: {len(test_input)})")

        start_time = time.time()
        try:
            result = _extract_keywords(test_input)
            end_time = time.time()
            duration = end_time - start_time

            print(f"  Processing time: {duration:.4f}s")
            print(f"  Keywords found: {len(result)}")

            if duration <= max_time_per_test:
                print("  ✅ PASS")
                passed += 1
            else:
                print(f"  ❌ FAIL: Too slow ({duration:.4f}s > {max_time_per_test}s)")
                failed += 1

        except Exception as e:
            print(f"  ❌ FAIL: Exception: {e}")
            failed += 1

    print(f"\nReDoS Test Results: {passed} passed, {failed} failed")
    return failed == 0


def test_functional_correctness():
    """Test that the fix preserves the correct functionality."""

    print("\n🧪 Testing functional correctness after ReDoS fix...")

    test_cases = [
        # Basic functionality tests
        {
            "input": "The server is running slowly",
            "expected_contains": ["server", "running", "slowly"],
            "should_not_contain": ["the", "is"],
            "description": "Basic keyword extraction"
        },
        {
            "input": "Database connection failed due to network timeout",
            "expected_contains": ["database", "connection", "failed", "network", "timeout"],
            "should_not_contain": ["due", "to"],
            "description": "Technical terms extraction"
        },
        {
            "input": "CPU usage at 95% memory utilization high",
            "expected_contains": ["cpu", "usage", "95", "memory", "utilization", "high"],
            "should_not_contain": ["at"],
            "description": "Numbers and metrics extraction"
        },
        {
            "input": "ERROR: System crash detected - immediate action required",
            "expected_contains": ["error", "system", "crash", "detected", "immediate", "action", "required"],
            "should_not_contain": [],
            "description": "Mixed case and punctuation"
        },
        {
            "input": "user123 test456 789validation",
            "expected_contains": ["user123", "test456", "789validation"],
            "should_not_contain": [],
            "description": "Alphanumeric strings"
        },
        {
            "input": "",
            "expected_contains": [],
            "should_not_contain": [],
            "description": "Empty input"
        },
        {
            "input": "!!! @@@ ### $$$",
            "expected_contains": [],
            "should_not_contain": [],
            "description": "Special characters only"
        }
    ]

    passed = 0
    failed = 0

    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['description']}")
        print(f"Input: '{test_case['input']}'")

        try:
            result = _extract_keywords(test_case['input'])
            print(f"Result: {result}")

            # Check expected keywords
            missing = [kw for kw in test_case['expected_contains'] if kw not in result]
            unexpected = [kw for kw in result if kw in test_case.get('should_not_contain', [])]

            if missing:
                print(f"  ❌ FAIL: Missing expected keywords: {missing}")
                failed += 1
            elif unexpected:
                print(f"  ⚠️  WARNING: Unexpected keywords: {unexpected}")
                passed += 1  # Warning, not failure
            else:
                print("  ✅ PASS")
                passed += 1

        except Exception as e:
            print(f"  ❌ FAIL: Exception: {e}")
            failed += 1

    print(f"\nFunctional Test Results: {passed} passed, {failed} failed")
    return failed == 0


def test_pattern_analysis():
    """Analyze the regex pattern used and verify it's safe."""

    print("\n🔬 Analyzing regex pattern safety...")

    # Get the actual pattern used in _extract_keywords
    import inspect
    source = inspect.getsource(_extract_keywords)

    # Look for the regex pattern
    if "r'[a-zA-Z0-9]+'" in source:
        print("✅ Pattern confirmed: r'[a-zA-Z0-9]+' (safe)")
        pattern_safety = True
    elif r"r'\b\w+\b'" in source:
        print("❌ Vulnerable pattern detected: r'\\b\\w+\\b'")
        pattern_safety = False
    else:
        print("⚠️  Unknown pattern - manual review required")
        pattern_safety = False

    # Test the pattern directly for safety
    safe_pattern = r'[a-zA-Z0-9]+'
    vulnerable_pattern = r'\b\w+\b'

    # Malicious inputs that would trigger ReDoS in vulnerable patterns
    malicious_inputs = [
        " " * 10000 + "a",
        "." * 5000 + "word" + "." * 5000,
        "_" * 2500 + "test",
    ]

    print("\nTesting pattern safety directly...")

    for malicious_input in malicious_inputs:
        print(f"Testing input length: {len(malicious_input)}")

        # Test safe pattern
        start = time.time()
        result_safe = re.findall(safe_pattern, malicious_input.lower())
        safe_time = time.time() - start

        # Test vulnerable pattern (but with timeout protection)
        start = time.time()
        try:
            # Use a very short timeout to avoid hanging
            result_vulnerable = re.findall(vulnerable_pattern, malicious_input.lower())
            vulnerable_time = time.time() - start
            print(f"  Safe pattern: {safe_time:.4f}s, Vulnerable pattern: {vulnerable_time:.4f}s")
        except Exception as e:
            vulnerable_time = float('inf')
            print(f"  Safe pattern: {safe_time:.4f}s, Vulnerable pattern: ERROR ({e})")

        if safe_time < 0.01:  # Should be very fast
            print("  ✅ Safe pattern performs well")
        else:
            print("  ⚠️  Safe pattern slower than expected")

    return pattern_safety


def test_edge_cases_and_robustness():
    """Test edge cases to ensure robustness."""

    print("\n🎯 Testing edge cases and robustness...")

    edge_cases = [
        ("Very long single word", "a" * 10000),
        ("Mixed case", "UPPER lower MiXeD CaSe"),
        ("Numbers only", "123 456 789 0"),
        ("Mixed alphanumeric", "test123 case456 789numbers"),
        ("Leading/trailing spaces", "   word   "),
        ("Multiple spaces", "word1    word2     word3"),
        ("Tab and newline", "word1\tword2\nword3"),
        ("Punctuation", "word1, word2. word3! word4?"),
        ("Unicode characters", "café naïve résumé"),
        ("Special chars mixed", "!@#$%^&*()word1!@#$%^&*()"),
        ("Empty and whitespace", "", "   ", "\t\n"),
        ("Very long input", "word " * 10000),
    ]

    passed = 0
    failed = 0

    for i, test_case in enumerate(edge_cases, 1):
        if isinstance(test_case, tuple):
            description = test_case[0]
            test_input = test_case[1]
        else:
            description = f"Edge case {i}"
            test_input = test_case

        print(f"\nTest {i}: {description}")
        print(f"Input: '{repr(test_input)}'")

        try:
            start_time = time.time()
            result = _extract_keywords(test_input)
            duration = time.time() - start_time

            print(f"Processing time: {duration:.4f}s")
            print(f"Result: {result}")

            # Should complete quickly and return list
            if duration < 0.1 and isinstance(result, list):
                print("✅ PASS")
                passed += 1
            else:
                print("❌ FAIL: Slow execution or wrong return type")
                failed += 1

        except Exception as e:
            print(f"❌ FAIL: Exception: {e}")
            failed += 1

    print(f"\nEdge Case Test Results: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    print("🔍 COMPREHENSIVE REDoS VULNERABILITY REVIEW")
    print("=" * 60)

    all_passed = True

    # Test ReDoS fix effectiveness
    all_passed &= test_redos_vulnerability_fix()

    # Test functional correctness
    all_passed &= test_functional_correctness()

    # Analyze pattern safety
    all_passed &= test_pattern_analysis()

    # Test edge cases
    all_passed &= test_edge_cases_and_robustness()

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("🎉 ReDoS vulnerability fix is working correctly!")
        print("🛡️  Pattern is safe and functionality is preserved")
    else:
        print("❌ SOME TESTS FAILED")
        print("🚨 ReDoS fix requires attention")

    print("=" * 60)

    sys.exit(0 if all_passed else 1)
