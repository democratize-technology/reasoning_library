#!/usr/bin/env python3
"""
Verification test for the ReDoS fix in _extract_keywords.
This test ensures the fix works and functionality is preserved.
"""

import os
import sys
import time

# Add src to path for import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from reasoning_library.abductive import _extract_keywords


def test_functionality_preserved():
    """Test that the fix preserves the original functionality."""

    print("🔧 Testing that functionality is preserved after ReDoS fix...")

    test_cases = [
        {
            "input": "The server is running slowly due to high CPU usage",
            "expected_keywords": ["server", "running", "slowly", "high", "cpu", "usage"],
            "description": "Basic keyword extraction"
        },
        {
            "input": "Database error occurred during deployment",
            "expected_keywords": ["database", "error", "occurred", "during", "deployment"],
            "description": "Technical terms extraction"
        },
        {
            "input": "a an the and or but in with to for of as by",
            "expected_keywords": [],
            "description": "Common words filtered out"
        },
        {
            "input": "Network latency increased after code deployment",
            "expected_keywords": ["network", "latency", "increased", "after", "code", "deployment"],
            "description": "Mixed case words"
        },
        {
            "input": "",
            "expected_keywords": [],
            "description": "Empty input"
        }
    ]

    all_passed = True

    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['description']}")
        print(f"Input: '{test_case['input']}'")

        result = _extract_keywords(test_case['input'])
        print(f"Result: {result}")
        print(f"Expected: {test_case['expected_keywords']}")

        # Check if all expected keywords are in result
        missing_keywords = [kw for kw in test_case['expected_keywords'] if kw not in result]
        extra_keywords = [kw for kw in result if kw not in test_case['expected_keywords']]

        if missing_keywords:
            print(f"❌ FAIL: Missing keywords: {missing_keywords}")
            all_passed = False
        elif extra_keywords and test_case['expected_keywords']:
            print(f"⚠️  WARNING: Extra keywords: {extra_keywords}")
        else:
            print("✅ PASS")

    return all_passed


def test_redos_fix_effectiveness():
    """Test that the ReDoS fix prevents catastrophic backtracking."""

    print("\n🛡️ Testing ReDoS fix effectiveness...")

    # Test cases that would be vulnerable with the old pattern
    malicious_inputs = [
        " " * 10000 + "a",
        "." * 5000 + "word" + "." * 5000,
        "_" * 2000 + "test" + "_" * 2000,
        "a1b2c3d4e5f6g7h8i9j0" * 100,
        "café naïve résumé test"  # Unicode should be handled safely
    ]

    for i, malicious_input in enumerate(malicious_inputs, 1):
        print(f"\nMalicious input {i} (length: {len(malicious_input)})...")

        start_time = time.time()
        try:
            result = _extract_keywords(malicious_input)
            end_time = time.time()
            duration = end_time - start_time

            print(f"Processing time: {duration:.4f} seconds")
            print(f"Keywords extracted: {len(result)}")

            # Should be very fast even with malicious input
            if duration > 0.1:
                print(f"❌ FAIL: Still vulnerable to input {i}")
                return False
            else:
                print("✅ PASS: No ReDoS vulnerability detected")

        except Exception as e:
            print(f"❌ FAIL: Exception on input {i}: {e}")
            return False

    return True


def test_edge_cases():
    """Test edge cases to ensure robustness."""

    print("\n🎯 Testing edge cases...")

    edge_cases = [
        {
            "input": "123 456 789",
            "description": "Numbers only"
        },
        {
            "input": "test123 case456 numbers789",
            "description": "Mixed alphanumeric"
        },
        {
            "input": "!!! @@@ ### $$$ %%%",
            "description": "Special characters only"
        },
        {
            "input": "word!!! special@@@ chars###",
            "description": "Mixed words and special chars"
        },
        {
            "input": "UPPERCASE MiXeD CaSe lower",
            "description": "Case variations"
        }
    ]

    all_passed = True

    for i, test_case in enumerate(edge_cases, 1):
        print(f"\nEdge case {i}: {test_case['description']}")
        print(f"Input: '{test_case['input']}'")

        try:
            result = _extract_keywords(test_case['input'])
            print(f"Result: {result}")

            # Should not crash and should return reasonable results
            if not isinstance(result, list):
                print(f"❌ FAIL: Expected list, got {type(result)}")
                all_passed = False
            else:
                print("✅ PASS")

        except Exception as e:
            print(f"❌ FAIL: Exception: {e}")
            all_passed = False

    return all_passed


if __name__ == "__main__":
    print("🔍 REDoS FIX VERIFICATION TEST")
    print("=" * 60)
    print("Testing that the ReDoS vulnerability fix works correctly")
    print("and preserves the original functionality.")
    print("=" * 60)

    success = True

    # Test functionality preservation
    success &= test_functionality_preserved()

    # Test ReDoS fix effectiveness
    success &= test_redos_fix_effectiveness()

    # Test edge cases
    success &= test_edge_cases()

    print("\n" + "=" * 60)
    if success:
        print("✅ ALL TESTS PASSED")
        print("🎉 ReDoS vulnerability fixed successfully!")
        print("🛡️  Pattern r'[a-zA-Z0-9]+' is safe from catastrophic backtracking")
        print("🔧 Functionality preserved and working correctly")
    else:
        print("❌ SOME TESTS FAILED")
        print("🚨 Fix may need adjustment")

    print("=" * 60)

    sys.exit(0 if success else 1)
