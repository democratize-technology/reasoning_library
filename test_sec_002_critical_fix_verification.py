#!/usr/bin/env python3
"""
SEC-002-CRITICALFIX: Comprehensive Security Fix Verification

This script tests the critical implementation vulnerabilities that were defeating
the entire security architecture:

1. Post-Decoding Bypass Vulnerability (CRITICAL)
   - Incomplete dangerous_patterns list in _decode_encoded_characters()
   - Missing standalone dangerous keywords like eval, exec, import
   - Attack: \\x65\\x76\\x61\\x6c → eval → NOT BLOCKED (before fix)

2. SEC-001 Integration Inconsistency (CRITICAL)
   - sanitize_for_concatenation() doesn't use _enhanced_preprocessing_for_bypass_prevention()
   - Vulnerable to pass%77ord=secret bypass
   - Creates inconsistent security posture across library

CRITICAL BYPASS VECTORS TO TEST:
- "\\x65\\x76\\x61\\x6c"        # hex 'eval'
- "\\x69\\x6d\\x70\\x6f\\x72\\x74" # hex 'import'
- "\\145\\166\\141\\154"        # octal 'eval'
- "\\151\\155\\160\\157\\162\\164" # octal 'import'
- "pass%77ord=secret123"      # URL encoding bypass
- "passwor&#100;=secret"      # HTML entity bypass
"""

import sys
import os

# Add the src directory to the path so we can import the library
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from reasoning_library.sanitization import (
    sanitize_for_concatenation,
    sanitize_for_logging,
    _decode_encoded_characters,
    _enhanced_preprocessing_for_bypass_prevention
)

def test_post_decoding_bypass_vectors():
    """Test that post-decoding bypass vectors are properly blocked."""
    print("="*80)
    print("TESTING: Post-Decoding Bypass Vectors")
    print("="*80)

    # Critical bypass vectors that should be BLOCKED
    bypass_vectors = [
        (r"\\x65\\x76\\x61\\x6c", "hex 'eval'"),
        (r"\\x69\\x6d\\x70\\x6f\\x72\\x74", "hex 'import'"),
        (r"\\145\\166\\141\\154", "octal 'eval'"),
        (r"\\151\\155\\160\\157\\162\\164", "octal 'import'"),
        (r"\\x63\\x6f\\x6d\\x70\\x69\\x6c\\x65", "hex 'compile'"),
        (r"\\143\\157\\155\\160\\151\\154\\145", "octal 'compile'"),
        (r"\\x5f\\x5f\\x69\\x6d\\x70\\x6f\\x72\\x74\\x5f\\x5f", "hex '__import__'"),
        (r"\\137\\137\\151\\155\\160\\157\\162\\164\\137\\137", "octal '__import__'"),
    ]

    print("\n1. Testing _decode_encoded_characters() function directly:")
    print("-" * 60)

    failed_direct_tests = 0
    for encoded_text, description in bypass_vectors:
        # Convert raw string to actual encoded string
        actual_encoded = encoded_text.encode('utf-8').decode('unicode_escape')

        result = _decode_encoded_characters(actual_encoded)

        if result == "[ENCODED_INJECTION_BLOCKED]":
            status = "✅ BLOCKED"
        else:
            status = f"❌ VULNERABLE - returned: '{result}'"
            failed_direct_tests += 1

        print(f"  {description:25} -> {status}")
        print(f"    Input: {repr(actual_encoded)}")
        print(f"    Output: {repr(result)}")
        print()

    print(f"\nDirect decoding test results: {len(bypass_vectors) - failed_direct_tests}/{len(bypass_vectors)} blocked")

    print("\n2. Testing through sanitize_for_concatenation():")
    print("-" * 60)

    failed_concat_tests = 0
    for encoded_text, description in bypass_vectors:
        # Convert raw string to actual encoded string
        actual_encoded = encoded_text.encode('utf-8').decode('unicode_escape')

        result = sanitize_for_concatenation(actual_encoded)

        if result == "":
            status = "✅ BLOCKED"
        else:
            status = f"❌ VULNERABLE - returned: '{result}'"
            failed_concat_tests += 1

        print(f"  {description:25} -> {status}")
        print(f"    Input: {repr(actual_encoded)}")
        print(f"    Output: {repr(result)}")
        print()

    print(f"\nConcatenation test results: {len(bypass_vectors) - failed_concat_tests}/{len(bypass_vectors)} blocked")

    return failed_direct_tests == 0 and failed_concat_tests == 0

def test_sec_001_integration_bypass_vectors():
    """Test that SEC-001 integration bypass vectors are properly blocked."""
    print("\n" + "="*80)
    print("TESTING: SEC-001 Integration Bypass Vectors")
    print("="*80)

    # SEC-001 bypass vectors that should be MASKED in logs but BLOCKED in concatenation
    bypass_vectors = [
        ("pass%77ord=secret123", "URL encoding bypass"),
        ("api_%6bey=token456", "URL encoding bypass (api_key)"),
        ("passwor&#100;=secret", "HTML entity bypass"),
        ("secre&#116;=value", "HTML entity bypass (secret)"),
        ("token&#61;abc123", "HTML entity bypass (token)"),
        ("credential&#115;=data", "HTML entity bypass (credentials)"),
        ("password=%73ecret", "Mixed URL encoding"),
        ("api_key=t&#111ken", "Mixed HTML entity"),
    ]

    print("\n1. Testing sanitize_for_concatenation() should BLOCK these:")
    print("-" * 60)

    failed_concat_tests = 0
    for test_input, description in bypass_vectors:
        result = sanitize_for_concatenation(test_input)

        if result == "":
            status = "✅ BLOCKED"
        else:
            status = f"❌ VULNERABLE - returned: '{result}'"
            failed_concat_tests += 1

        print(f"  {description:35} -> {status}")
        print(f"    Input: {repr(test_input)}")
        print(f"    Output: {repr(result)}")
        print()

    print(f"\nConcatenation blocking test results: {len(bypass_vectors) - failed_concat_tests}/{len(bypass_vectors)} blocked")

    print("\n2. Testing sanitize_for_logging() should MASK these:")
    print("-" * 60)

    failed_logging_tests = 0
    for test_input, description in bypass_vectors:
        result = sanitize_for_logging(test_input)

        if "[REDACTED]" in result:
            status = "✅ MASKED"
        else:
            status = f"❌ NOT MASKED - returned: '{result}'"
            failed_logging_tests += 1

        print(f"  {description:35} -> {status}")
        print(f"    Input: {repr(test_input)}")
        print(f"    Output: {repr(result)}")
        print()

    print(f"\nLogging masking test results: {len(bypass_vectors) - failed_logging_tests}/{len(bypass_vectors)} masked")

    return failed_concat_tests == 0 and failed_logging_tests == 0

def test_complex_bypass_vectors():
    """Test sophisticated multi-layer bypass attempts."""
    print("\n" + "="*80)
    print("TESTING: Complex Multi-Layer Bypass Vectors")
    print("="*80)

    complex_vectors = [
        # Multi-layer encoding
        ("\\x65\\x76\\x61\\x6c('malicious')", "Hex encoded function call"),
        ("\\145\\166\\141\\154('harmful')", "Octal encoded function call"),
        ("\\x69\\x6d\\x70\\x6f\\x72\\x74 os", "Hex encoded import"),
        ("__import__('os').system", "Direct dangerous call"),
        # Concatenation bypass attempts
        ("'ev' + 'al' + '(code)'", "String concatenation bypass"),
        ("'ex' + 'ec' + '(command)'", "String concatenation bypass"),
        # Mixed encoding
        ("\\x65v\\x61l", "Mixed direct and encoded"),
        ("e\\x76a\\x6c", "Mixed encoding patterns"),
    ]

    print("\nTesting sanitize_for_concatenation() against complex attacks:")
    print("-" * 60)

    failed_complex_tests = 0
    for test_input, description in complex_vectors:
        # Convert escape sequences
        actual_input = test_input.encode('utf-8').decode('unicode_escape')

        result = sanitize_for_concatenation(actual_input)

        if result == "":
            status = "✅ BLOCKED"
        else:
            status = f"❌ VULNERABLE - returned: '{result}'"
            failed_complex_tests += 1

        print(f"  {description:35} -> {status}")
        print(f"    Input: {repr(actual_input)}")
        print(f"    Output: {repr(result)}")
        print()

    print(f"\nComplex bypass test results: {len(complex_vectors) - failed_complex_tests}/{len(complex_vectors)} blocked")

    return failed_complex_tests == 0

def main():
    """Main test function."""
    print("SEC-002-CRITICALFIX: Security Fix Verification")
    print("=" * 80)
    print("Testing critical implementation vulnerabilities that defeat security architecture")
    print()

    # Run all test suites
    post_decoding_passed = test_post_decoding_bypass_vectors()
    sec_001_passed = test_sec_001_integration_bypass_vectors()
    complex_passed = test_complex_bypass_vectors()

    # Final results
    print("\n" + "="*80)
    print("FINAL RESULTS")
    print("="*80)

    all_tests_passed = post_decoding_passed and sec_001_passed and complex_passed

    print(f"Post-Decoding Bypass Protection:     {'✅ PASS' if post_decoding_passed else '❌ FAIL'}")
    print(f"SEC-001 Integration Consistency:    {'✅ PASS' if sec_001_passed else '❌ FAIL'}")
    print(f"Complex Bypass Protection:          {'✅ PASS' if complex_passed else '❌ FAIL'}")
    print()

    if all_tests_passed:
        print("🎉 ALL CRITICAL SECURITY FIXES VERIFIED! 🎉")
        print("The implementation vulnerabilities have been successfully fixed.")
        return 0
    else:
        print("🚨 CRITICAL VULNERABILITIES STILL EXIST! 🚨")
        print("The security architecture is still vulnerable to bypass attacks.")
        return 1

if __name__ == "__main__":
    sys.exit(main())