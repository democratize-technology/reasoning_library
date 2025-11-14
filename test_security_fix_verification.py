#!/usr/bin/env python3
"""
Verification test to confirm the template injection security fix works correctly.

This test verifies that the new implementation completely eliminates cross-contamination
and template injection vulnerabilities.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from reasoning_library.abductive import _safe_hypothesis_template

def test_security_fix():
    """Test that the security fix completely blocks cross-contamination."""

    print("🔒 TESTING SECURITY FIX VERIFICATION")
    print("=" * 50)

    print("""
SECURITY FIX ANALYSIS:
The new implementation uses:
1. NO template processing or string replacement
2. Direct string concatenation only
3. Predefined sentence structure: "The {action} on {component} causes {issue}"
4. All user inputs treated as literal text
5. Strict sanitization of all inputs
6. NO possibility of cross-contamination
""")

    # Test cases that previously caused cross-contamination
    test_cases = [
        {
            "name": "Basic Cross-Contamination (Previously Vulnerable)",
            "action": "test",
            "component": "component",
            "issue": "{action}",  # This should remain as literal "action"
            "template": "Any template",  # Template is ignored now
            "expected_contains": ["The test on component causes action"],
            "should_not_contain": ["The test on component causes test"]  # This was the vulnerability
        },
        {
            "name": "Multiple Placeholders in Input",
            "action": "{component}",
            "component": "{issue}",
            "issue": "{action}",
            "template": "Any template",
            "expected_contains": ["The component on issue causes action"],
            "should_not_contain": ["cross-contamination"]
        },
        {
            "name": "Dangerous Input with Placeholders",
            "action": "legitimate_action",
            "component": "__import__('os')",
            "issue": "{action}",
            "template": "Any template",
            "expected_contains": ["The legitimate_action on BLOCKED causes action"],
            "should_not_contain": ["__import__"]
        },
        {
            "name": "Nested Placeholders",
            "action": "test",
            "component": "system{action}",
            "issue": "failure",
            "template": "Any template",
            "expected_contains": ["The test on action causes failure"],
            "should_not_contain": ["cross-contamination"]
        },
        {
            "name": "Different Template Syntax",
            "action": "test",
            "component": "component",
            "issue": "${__import__('os')}",
            "template": "Any template",
            "expected_contains": ["The test on component causes unknown issue"],
            "should_not_contain": ["${", "__import__"]
        },
        {
            "name": "Empty Inputs",
            "action": "",
            "component": "",
            "issue": "",
            "template": "Any template",
            "expected_contains": ["The unknown action on system causes unknown issue"],
            "should_not_contain": ["{action}", "{component}", "{issue}"]
        },
        {
            "name": "Long Dangerous Inputs",
            "action": "a" * 1000,
            "component": "__import__('os')" * 100,
            "issue": "{action}" * 50,
            "template": "Any template",
            "expected_contains": ["The aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"],  # Truncated
            "should_not_contain": ["__import__", "{action}"]
        }
    ]

    vulnerabilities_found = 0
    tests_passed = 0

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}/{len(test_cases)}: {test_case['name']}")
        print(f"   Action: '{test_case['action'][:50]}{'...' if len(test_case['action']) > 50 else ''}'")
        print(f"   Component: '{test_case['component'][:50]}{'...' if len(test_case['component']) > 50 else ''}'")
        print(f"   Issue: '{test_case['issue'][:50]}{'...' if len(test_case['issue']) > 50 else ''}'")

        try:
            result = _safe_hypothesis_template(
                test_case['action'],
                test_case['component'],
                test_case['issue'],
                test_case['template']
            )

            print(f"   Result: '{result}'")

            # Check that expected patterns are present
            expected_found = all(expected in result for expected in test_case['expected_contains'])

            # Check that dangerous patterns are NOT present
            dangerous_found = any(dangerous in result for dangerous in test_case['should_not_contain'])

            if expected_found and not dangerous_found:
                print("   ✅ SECURITY FIX CONFIRMED: No cross-contamination detected")
                tests_passed += 1
            else:
                print("   ❌ SECURITY ISSUE DETECTED:")
                if not expected_found:
                    missing = [exp for exp in test_case['expected_contains'] if exp not in result]
                    print(f"      Missing expected patterns: {missing}")
                if dangerous_found:
                    present = [dan for dan in test_case['should_not_contain'] if dan in result]
                    print(f"      Dangerous patterns present: {present}")
                vulnerabilities_found += 1

        except Exception as e:
            print(f"   💥 Exception: {type(e).__name__}: {e}")
            vulnerabilities_found += 1

    print(f"\n📊 SECURITY FIX VERIFICATION RESULTS")
    print("=" * 45)
    print(f"Tests: {len(test_cases)}")
    print(f"Passed: {tests_passed}")
    print(f"Failed: {vulnerabilities_found}")
    print(f"Success rate: {(tests_passed / len(test_cases)) * 100:.1f}%")

    return vulnerabilities_found == 0

def test_invariant_behavior():
    """Test that legitimate inputs still work correctly."""

    print("\n🔧 TESTING INVARIANT BEHAVIOR")
    print("=" * 35)

    legitimate_cases = [
        {
            "name": "Normal Legitimate Input",
            "action": "authentication",
            "component": "login system",
            "issue": "credentials timeout",
            "expected": "The authentication on login system causes credentials timeout"
        },
        {
            "name": "Input with Special Characters",
            "action": "data-processing",
            "component": "API endpoint",
            "issue": "rate limiting exceeded",
            "expected": "The data processing on API endpoint causes rate limiting exceeded"
        },
        {
            "name": "Single Word Inputs",
            "action": "error",
            "component": "database",
            "issue": "connection",
            "expected": "The error on database causes connection"
        }
    ]

    invariants_preserved = 0

    for case in legitimate_cases:
        print(f"\nTesting: {case['name']}")

        try:
            result = _safe_hypothesis_template(
                case['action'],
                case['component'],
                case['issue'],
                "any template"
            )

            print(f"Expected: '{case['expected']}'")
            print(f"Actual:   '{result}'")

            if result == case['expected']:
                print("✅ Invariant preserved")
                invariants_preserved += 1
            else:
                print("⚠️  Behavior changed - may need adjustment")

        except Exception as e:
            print(f"💥 Exception: {e}")

    print(f"\nInvariants preserved: {invariants_preserved}/{len(legitimate_cases)}")
    return invariants_preserved == len(legitimate_cases)

def demonstrate_security_improvement():
    """Show before/after comparison of the security fix."""

    print("\n📈 SECURITY IMPROVEMENT DEMONSTRATION")
    print("=" * 45)

    print("""
BEFORE (Vulnerable):
- Used sequential string replacement: replace("{action}", action)
- User input with "{action}" got processed as template
- Cross-contamination between inputs possible
- Template injection vulnerabilities existed

AFTER (Secure):
- Uses direct string concatenation only
- User input always treated as literal text
- No template processing or replacement
- Zero possibility of cross-contamination
- All dangerous patterns blocked by sanitization
""")

    # Demonstrate with the classic vulnerability case
    print("\n🧪 VULNERABILITY CASE DEMONSTRATION:")
    print("-" * 40)

    action = "test"
    component = "component"
    issue = "{action}"  # This was the vulnerability vector
    template = "System {action} fails on {component} with {issue}"

    print(f"Inputs:")
    print(f"  action: '{action}'")
    print(f"  component: '{component}'")
    print(f"  issue: '{issue}' ← Contains placeholder pattern")
    print(f"  template: '{template}'")

    result = _safe_hypothesis_template(action, component, issue, template)
    print(f"\nSecure result: '{result}'")

    # Verify security
    if "test" in result and result.count("test") == 1:
        print("✅ SECURITY CONFIRMED: 'test' appears only once (from action field)")
        print("✅ The literal '{action}' in issue field was treated as literal text 'action'")
        return True
    else:
        print("❌ Security issue detected")
        return False

if __name__ == "__main__":
    print("Template Injection Security Fix Verification")
    print("Verifying that the cross-contamination vulnerability is eliminated")
    print()

    # Test the security fix
    is_secure = test_security_fix()

    # Test invariant behavior
    invariants_preserved = test_invariant_behavior()

    # Demonstrate improvement
    improvement_confirmed = demonstrate_security_improvement()

    print("\n" + "=" * 65)
    print("🎯 FINAL SECURITY ASSESSMENT")
    print("=" * 65)

    if is_secure and invariants_preserved and improvement_confirmed:
        print("✅ TEMPLATE INJECTION VULNERABILITY ELIMINATED!")
        print("   - Cross-contamination completely blocked")
        print("   - All attack vectors neutralized")
        print("   - Legitimate functionality preserved")
        print("   - Security fix successfully implemented")
        sys.exit(0)
    else:
        print("❌ SECURITY ISSUES REMAIN:")
        if not is_secure:
            print("   - Vulnerabilities still detected")
        if not invariants_preserved:
            print("   - Legitimate functionality broken")
        if not improvement_confirmed:
            print("   - Security improvement not confirmed")
        sys.exit(1)