#!/usr/bin/env python3
"""
SEC-001-ARCHFIX Verification Test

This test verifies that all critical architectural flaws in the sanitization system
have been properly fixed and bypass vectors are now blocked.

ARCHITECTURAL FLAWS FIXED:
1. URL Encoding Bypass Vulnerability - pass%77ord=secret now masked
2. HTML Entity Bypass Vulnerability - passwor&#100;=secret now masked
3. Regex Greediness Boundary Issue - compound strings now fully masked
4. False Positive Over-Masking - password_reset_page no longer over-masked
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from reasoning_library.sanitization import sanitize_for_logging


def test_critical_bypass_vectors():
    """Test that all critical bypass vectors are now blocked."""

    print("🔒 TESTING CRITICAL BYPASS VECTORS")
    print("=" * 60)

    # These were the specific bypass vectors mentioned in the task
    critical_bypass_tests = [
        # URL encoding bypasses (should now be blocked)
        {
            "name": "URL Encoding Bypass 1",
            "input": "pass%77ord=secret123",
            "expected": "password=[REDACTED]",
            "description": "URL encoded 'password' field name"
        },
        {
            "name": "URL Encoding Bypass 2",
            "input": "api_%6bey=token456",
            "expected": "api_key=[REDACTED]",
            "description": "URL encoded 'api_key' field name"
        },

        # HTML entity bypasses (should now be blocked)
        {
            "name": "HTML Entity Bypass",
            "input": "passwor&#100;=secret",
            "expected": "password=[REDACTED]",
            "description": "HTML entity encoded field name"
        },

        # Compound string bypasses (should now be fully masked)
        {
            "name": "Compound String Bypass",
            "input": "password=secret123&api_key=token456",
            "expected": "password=[REDACTED]&api_key=[REDACTED]",
            "description": "Multiple credentials in one string"
        },
    ]

    all_passed = True
    for test in critical_bypass_tests:
        result = sanitize_for_logging(test["input"])
        passed = result == test["expected"]

        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test['name']}")
        print(f"   Input:    {test['input']}")
        print(f"   Expected: {test['expected']}")
        print(f"   Got:      {result}")
        print(f"   Note:     {test['description']}")

        if not passed:
            all_passed = False
            print("   🚨 CRITICAL: Bypass vector still works!")
        print()

    return all_passed


def test_false_positive_prevention():
    """Test that false positive over-masking is prevented."""

    print("🛡️ TESTING FALSE POSITIVE PREVENTION")
    print("=" * 50)

    # These should NOT be masked (false positives)
    false_positive_tests = [
        {
            "name": "Password Reset Page",
            "input": "password_reset_page",
            "expected": "password_reset_page",
            "description": "Contains 'password' but is not a credential"
        },
        {
            "name": "Secretary of State",
            "input": "secretary_of_state",
            "expected": "secretary_of_state",
            "description": "Contains 'secret' but is not a credential"
        },
        {
            "name": "Tokenization Required",
            "input": "tokenization_required",
            "expected": "tokenization_required",
            "description": "Contains 'token' but is not a credential"
        },
        {
            "name": "Password123",
            "input": "password123",
            "expected": "password123",
            "description": "No separator character, should not be masked"
        },
        {
            "name": "API Key Data",
            "input": "my_api_key_data",
            "expected": "my_api_key_data",
            "description": "Embedded in longer word, should not be masked"
        }
    ]

    all_passed = True
    for test in false_positive_tests:
        result = sanitize_for_logging(test["input"])
        passed = result == test["expected"]

        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test['name']}")
        print(f"   Input:    {test['input']}")
        print(f"   Expected: {test['expected']}")
        print(f"   Got:      {result}")
        print(f"   Note:     {test['description']}")

        if not passed:
            all_passed = False
            print("   🚨 CRITICAL: False positive over-masking detected!")
        print()

    return all_passed


def test_advanced_bypass_vectors():
    """Test advanced bypass vectors to ensure comprehensive protection."""

    print("🔬 TESTING ADVANCED BYPASS VECTORS")
    print("=" * 50)

    advanced_tests = [
        # Multiple encodings
        ("pass%77%6F%72%64=secret", "password=[REDACTED]"),
        ("api_%6b%65%79=token", "api_key=[REDACTED]"),

        # Case variations with encoding
        ("PASSWOR&#68;=secret", "PASSWORD=[REDACTED]"),

        # Different separators
        ("Password = secret123", "Password=[REDACTED]"),
        ("api_key:token456", "api_key=[REDACTED]"),

        # Quote variations
        ('password="secret"', 'password=[REDACTED]'),
        ("api_key='token'", 'api_key=[REDACTED]'),

        # Complex compound strings
        ("user=admin&password=secret&role=user", "user=admin&password=[REDACTED]&role=user"),
        ("token=abc123, api_key=def456", "token=[REDACTED], api_key=[REDACTED]"),
        ("secret=xyz; credential=pass", "secret=[REDACTED]; credential=[REDACTED]"),
    ]

    all_passed = True
    for i, (input_val, expected) in enumerate(advanced_tests, 1):
        result = sanitize_for_logging(input_val)
        passed = result == expected

        status = f"✅ PASS {i:2d}" if passed else f"❌ FAIL {i:2d}"
        print(f"{status}: {input_val}")
        print(f"         → {result}")

        if not passed:
            all_passed = False
            print(f"         Expected: {expected}")
            print("         🚨 Advanced bypass vector detected!")

    return all_passed


def test_original_functionality_preserved():
    """Test that original documented functionality still works."""

    print("🔧 TESTING ORIGINAL FUNCTIONALITY")
    print("=" * 50)

    original_tests = [
        # Original documented examples
        ("Error\n[INFO] Fake admin logged in", "[LOG_INJECTION_BLOCKED]"),
        ("Critical issue\x1b[31mRED TEXT\x1b[0m", "[ANSI_BLOCKED]"),
        ("password='secret123'", "[REDACTED]"),
    ]

    all_passed = True
    for i, (input_val, expected_contains) in enumerate(original_tests, 1):
        result = sanitize_for_logging(input_val)
        passed = expected_contains in result

        status = f"✅ PASS {i}" if passed else f"❌ FAIL {i}"
        print(f"{status}: {repr(input_val)}")
        print(f"         → {repr(result)}")

        if not passed:
            all_passed = False
            print(f"         Expected to contain: {expected_contains}")
            print("         🚨 Original functionality broken!")

    return all_passed


def main():
    """Run all architectural fix verification tests."""

    print("SEC-001-ARCHFIX: Architectural Flaw Verification")
    print("=" * 70)
    print("Testing fixes for critical architectural vulnerabilities")
    print()

    # Run all test suites
    bypass_results = test_critical_bypass_vectors()
    false_positive_results = test_false_positive_prevention()
    advanced_results = test_advanced_bypass_vectors()
    original_results = test_original_functionality_preserved()

    # Summary
    print("=" * 70)
    print("🏁 ARCHITECTURAL FIX VERIFICATION SUMMARY")
    print("=" * 70)

    test_results = [
        ("Critical Bypass Vectors", bypass_results),
        ("False Positive Prevention", false_positive_results),
        ("Advanced Bypass Vectors", advanced_results),
        ("Original Functionality", original_results)
    ]

    all_tests_passed = True
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not result:
            all_tests_passed = False

    print()
    if all_tests_passed:
        print("🎉 ALL ARCHITECTAL FIXES VERIFIED!")
        print("   ✅ All bypass vectors blocked")
        print("   ✅ No false positive over-masking")
        print("   ✅ Advanced bypass protection working")
        print("   ✅ Original functionality preserved")
        print()
        print("🛡️  SANITIZATION SYSTEM IS SECURE")
        print("   Critical architectural flaws successfully fixed!")
        return 0
    else:
        print("🚨 CRITICAL ISSUES DETECTED!")
        print("   Some architectural fixes are not working properly")
        print("   Immediate attention required!")
        return 1


if __name__ == "__main__":
    sys.exit(main())