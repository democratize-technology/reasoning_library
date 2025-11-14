#!/usr/bin/env python3
"""
Test script to demonstrate template injection bypass vulnerabilities in _safe_hypothesis_template.

This script tests various attack vectors that can bypass the current manual string replacement
approach, demonstrating why a more secure solution is needed.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from reasoning_library.abductive import _safe_hypothesis_template

def test_vulnerability_scenarios():
    """Test various template injection bypass attack vectors."""

    print("🔍 TESTING TEMPLATE INJECTION BYPASS VULNERABILITIES")
    print("=" * 60)

    # Base template
    template = "The {action} on {component} causes {issue}"

    # Test cases organized by attack vector type
    attack_vectors = [
        # Basic template injection (should be caught by current implementation)
        {
            "name": "Basic Template Injection",
            "action": "test",
            "component": "system{__import__('os').system('echo pwned')}",
            "issue": "failure",
            "expected_danger": True
        },

        # Unicode encoding bypasses
        {
            "name": "Unicode Brace Bypass",
            "action": "test",
            "component": "system\u007b__import__('os').system('echo pwned')\u007d",
            "issue": "failure",
            "expected_danger": True
        },
        {
            "name": "Unicode Template Bypass",
            "action": "test",
            "component": "system",
            "issue": "failure\u0024\u007b__import__('os').system('echo pwned')\u007d",
            "expected_danger": True
        },

        # Hexadecimal encoding bypasses
        {
            "name": "Hex Brace Bypass",
            "action": "test",
            "component": "system\\x7b__import__('os').system('echo pwned')\\x7d",
            "issue": "failure",
            "expected_danger": True
        },

        # Nested template patterns
        {
            "name": "Nested Template Pattern",
            "action": "test",
            "component": "system{action}",
            "issue": "failure{component}",
            "expected_danger": False  # This might not be dangerous but shows pattern issues
        },

        # Format string bypasses
        {
            "name": "Format String Bypass",
            "action": "test%s",
            "component": "system",
            "issue": "failure",
            "expected_danger": False  # Format strings aren't directly dangerous here
        },

        # String concatenation bypass attempts
        {
            "name": "Concatenation Bypass Attempt",
            "action": "test" + "{__import__('os')}",
            "component": "system",
            "issue": "failure",
            "expected_danger": True
        },

        # Mixed encoding attacks
        {
            "name": "Mixed Unicode/Hex Attack",
            "action": "test",
            "component": "system\\u007b__import__('os').system('echo pwned')\\u007d",
            "issue": "failure",
            "expected_danger": True
        },

        # Attribute access bypasses
        {
            "name": "Attribute Access Bypass",
            "action": "test",
            "component": "system.__class__.__base__",
            "issue": "failure",
            "expected_danger": False  # Attribute access itself isn't dangerous
        },

        # URL encoded attacks (if the system decodes URLs)
        {
            "name": "URL Encoded Attack",
            "action": "test",
            "component": "system%7B__import__('os').system('echo pwned')%7D",
            "issue": "failure",
            "expected_danger": True  # Dangerous if URL decoding occurs
        },

        # Base64 encoded attacks (if the system decodes base64)
        {
            "name": "Base64 Encoded Attack",
            "action": "test",
            "component": "system",
            "issue": "failure{{'__import__'.decode('base64')}}",
            "expected_danger": False  # Base64 decode would need to be implemented
        },

        # Multiple placeholder abuse
        {
            "name": "Multiple Placeholder Abuse",
            "action": "{action}",
            "component": "{component}",
            "issue": "{issue}",
            "expected_danger": False  # Should just result in literal text
        }
    ]

    vulnerabilities_found = 0
    total_tests = len(attack_vectors)

    for i, test_case in enumerate(attack_vectors, 1):
        print(f"\n📋 Test {i}/{total_tests}: {test_case['name']}")
        print(f"   Action: '{test_case['action']}'")
        print(f"   Component: '{test_case['component']}'")
        print(f"   Issue: '{test_case['issue']}'")

        try:
            result = _safe_hypothesis_template(
                test_case['action'],
                test_case['component'],
                test_case['issue'],
                template
            )

            print(f"   Result: '{result}'")

            # Check for dangerous patterns that might indicate successful bypass
            dangerous_indicators = [
                '__import__',
                'system(',
                'exec(',
                'eval(',
                'subprocess',
                'popen',
                '${',
                '%(',
                '{__',
                '{action',
                '{component',
                '{issue',
                'system.',
                '__class__',
                '__base__'
            ]

            has_danger = any(indicator in result for indicator in dangerous_indicators)

            if has_danger:
                print("   ❌ VULNERABILITY DETECTED: Dangerous patterns found in output!")
                vulnerabilities_found += 1
            elif test_case['expected_danger'] and not has_danger:
                print("   ✅ Attack blocked (as expected)")
            elif not test_case['expected_danger'] and not has_danger:
                print("   ✅ No dangerous patterns detected (as expected)")
            else:
                print("   ⚠️  Unexpected result")

        except Exception as e:
            print(f"   💥 EXCEPTION: {type(e).__name__}: {e}")
            # Exceptions might indicate that the attack was blocked or broke the system
            if test_case['expected_danger']:
                print("   ✅ Attack caused exception (potentially good)")
            else:
                print("   ❌ Unexpected exception for non-dangerous input")
                vulnerabilities_found += 1

    print("\n" + "=" * 60)
    print("📊 VULNERABILITY ASSESSMENT SUMMARY")
    print("=" * 60)
    print(f"Total tests: {total_tests}")
    print(f"Vulnerabilities found: {vulnerabilities_found}")
    print(f"Security score: {((total_tests - vulnerabilities_found) / total_tests) * 100:.1f}%")

    if vulnerabilities_found > 0:
        print("\n🚨 CRITICAL: Template injection bypass vulnerabilities detected!")
        print("   The current manual string replacement approach can be bypassed.")
        print("   Immediate security fix required.")
        return False
    else:
        print("\n✅ No obvious bypass vulnerabilities detected.")
        print("   Current implementation appears to block tested attack vectors.")
        return True

def test_edge_cases():
    """Test edge cases that might break the security implementation."""

    print("\n🧪 TESTING EDGE CASES")
    print("=" * 40)

    template = "The {action} on {component} causes {issue}"

    edge_cases = [
        {
            "name": "Empty inputs",
            "action": "",
            "component": "",
            "issue": ""
        },
        {
            "name": "Very long inputs",
            "action": "a" * 1000,
            "component": "b" * 1000,
            "issue": "c" * 1000
        },
        {
            "name": "Only dangerous characters",
            "action": "{}{}{}{}",
            "component": "$$$",
            "issue": "{{{{}}}}"
        },
        {
            "name": "Mixed valid/dangerous content",
            "action": "legitimate action {dangerous}",
            "component": "normal.component",
            "issue": "issue with ${template}"
        },
        {
            "name": "Template without placeholders",
            "action": "test",
            "component": "system",
            "issue": "failure"
        }
    ]

    for test_case in edge_cases:
        print(f"\nTesting: {test_case['name']}")
        try:
            # Test with normal template
            result1 = _safe_hypothesis_template(
                test_case['action'],
                test_case['component'],
                test_case['issue'],
                template
            )

            # Test with template without placeholders
            result2 = _safe_hypothesis_template(
                test_case['action'],
                test_case['component'],
                test_case['issue'],
                "Fixed template without placeholders"
            )

            print(f"  With placeholders: '{result1[:50]}{'...' if len(result1) > 50 else ''}'")
            print(f"  Without placeholders: '{result2[:50]}{'...' if len(result2) > 50 else ''}'")

        except Exception as e:
            print(f"  Exception: {type(e).__name__}: {e}")

if __name__ == "__main__":
    print("Template Injection Bypass Vulnerability Test")
    print("This script tests the security of _safe_hypothesis_template function")
    print()

    # Run comprehensive vulnerability tests
    is_secure = test_vulnerability_scenarios()

    # Run edge case tests
    test_edge_cases()

    print("\n" + "=" * 60)
    if not is_secure:
        print("🚨 SECURITY ISSUE CONFIRMED: Template injection bypass vulnerabilities exist!")
        print("   Immediate action required to fix the _safe_hypothesis_template function.")
        sys.exit(1)
    else:
        print("✅ No obvious security issues detected with current implementation.")
        print("   (This doesn't guarantee security - more sophisticated attacks may exist)")
        sys.exit(0)