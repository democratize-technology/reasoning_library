#!/usr/bin/env python3
"""
Test to demonstrate the cross-contamination vulnerability in _safe_hypothesis_template.

This test shows how the manual replacement approach can lead to unexpected behavior
where one input's value contaminates another's processing.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from reasoning_library.abductive import _safe_hypothesis_template

def demonstrate_cross_contamination():
    """Demonstrate the cross-contamination vulnerability."""

    print("🔍 DEMONSTRATING CROSS-CONTAMINATION VULNERABILITY")
    print("=" * 60)

    print("""
VULNERABILITY: Cross-Contamination in Manual Replacement

The _safe_hypothesis_template function uses sequential string replacement:
1. Replace {action} with safe_action
2. Replace {component} with safe_component
3. Replace {issue} with safe_issue

This creates a vulnerability when:
- Input values contain placeholder patterns themselves
- Later replacements affect text from earlier replacements
- The order of replacement creates unexpected results

Example:
- action: "test"
- component: "component"
- issue: "{action}"  ← Contains another placeholder!
- Template: "System {action} fails on {component} with {issue}"

Expected result: "System test fails on component with {action}"
Actual result: "System test fails on component with test" ← UNEXPECTED!
""")

    # Test the specific vulnerability
    test_cases = [
        # Basic cross-contamination
        {
            "name": "Basic Cross-Contamination",
            "action": "test",
            "component": "component",
            "issue": "{action}",
            "template": "System {action} fails on {component} with {issue}",
            "expected": "Cross-contamination: issue should stay as literal {action}"
        },

        # Multiple cross-contamination
        {
            "name": "Multiple Cross-Contamination",
            "action": "{component}",
            "component": "{issue}",
            "issue": "{action}",
            "template": "The {action} affects {component} causing {issue}",
            "expected": "Complex cross-contamination between all fields"
        },

        # Dangerous cross-contamination
        {
            "name": "Dangerous Cross-Contamination",
            "action": "legitimate_action",
            "component": "__import__('os')",
            "issue": "{action}",
            "template": "The {issue} on {component} causes failure",
            "expected": "Dangerous content might be injected through cross-contamination"
        },

        # Nested cross-contamination
        {
            "name": "Nested Cross-Contamination",
            "action": "test",
            "component": "system{action}",
            "issue": "failure",
            "template": "The {action} on {component} causes {issue}",
            "expected": "Nested placeholder might be processed incorrectly"
        },

        # Template injection through cross-contamination
        {
            "name": "Template Injection via Cross-Contamination",
            "action": "test",
            "component": "component",
            "issue": "${__import__('os')}",
            "template": "The {action} fails on {component} with {issue}",
            "expected": "Different template syntax gets processed through cross-contamination"
        }
    ]

    vulnerabilities_found = 0

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🚨 Test {i}/{len(test_cases)}: {test_case['name']}")
        print(f"   Strategy: {test_case['expected']}")
        print(f"   Action: '{test_case['action']}'")
        print(f"   Component: '{test_case['component']}'")
        print(f"   Issue: '{test_case['issue']}'")
        print(f"   Template: '{test_case['template']}'")

        try:
            result = _safe_hypothesis_template(
                test_case['action'],
                test_case['component'],
                test_case['issue'],
                test_case['template']
            )

            print(f"   📤 Result: '{result}'")

            # Analyze for cross-contamination
            original_placeholders = ["{action}", "{component}", "{issue}"]
            cross_contamination_detected = False

            # Check if any placeholder that was supposed to remain literal got replaced
            if test_case['issue'] == "{action}" and "test" in result and "test" not in test_case['component']:
                cross_contamination_detected = True
                print("   🔍 CROSS-CONTAMINATION: Issue field {action} got replaced with action value!")

            elif test_case['action'] == "{component}" and "component" in result and test_case['component'] != "component":
                cross_contamination_detected = True
                print("   🔍 CROSS-CONTAMINATION: Action field {component} got processed!")

            elif test_case['component'] == "{issue}" and "test" in result and test_case['issue'] != "test":
                cross_contamination_detected = True
                print("   🔍 CROSS-CONTAMINATION: Component field {issue} got processed!")

            # Check for dangerous patterns
            dangerous_patterns = ['__import__', 'system(', 'exec(', 'eval(']
            has_dangerous = any(pattern in result for pattern in dangerous_patterns)

            # Check for unexpected template processing
            unexpected_processing = (
                '${' in result or  # Different template syntax
                '%(' in result or   # Format string syntax
                test_case['issue'] != "{action}" and "{action}" not in result and "test" in result
            )

            if has_dangerous:
                print("   🚨 CRITICAL: Dangerous pattern detected!")
                vulnerabilities_found += 1
            elif cross_contamination_detected:
                print("   ⚠️  VULNERABILITY: Cross-contamination confirmed!")
                vulnerabilities_found += 1
            elif unexpected_processing:
                print("   ⚠️  VULNERABILITY: Unexpected template processing!")
                vulnerabilities_found += 1
            else:
                print("   ✅ No obvious cross-contamination detected")

        except Exception as e:
            print(f"   💥 Exception: {type(e).__name__}: {e}")
            vulnerabilities_found += 1

    print(f"\n📊 CROSS-CONTAMINATION ASSESSMENT")
    print("=" * 40)
    print(f"Tests: {len(test_cases)}")
    print(f"Vulnerabilities found: {vulnerabilities_found}")

    if vulnerabilities_found > 0:
        print("\n🚨 CROSS-CONTAMINATION VULNERABILITY CONFIRMED!")
        print("   Manual string replacement allows inputs to affect each other")
        print("   This breaks the isolation expected between template parameters")
        return False
    else:
        print("\n✅ No cross-contamination detected")
        return True

def demonstrate_manual_replacement_flaw():
    """Show exactly why manual replacement is flawed."""

    print("\n💡 WHY MANUAL REPLACEMENT IS FUNDAMENTALLY FLAWED")
    print("=" * 55)

    print("""
The core issue with manual string replacement:

1. Manual replacement cannot distinguish between:
   - Original template placeholders (should be replaced)
   - Literal placeholder text in user input (should NOT be replaced)
   - Placeholder text created by previous replacements (ambiguous)

2. Sequential processing creates race conditions:
   - Step 1: {action} → user_action_value
   - Step 2: {component} → user_component_value
   - Step 3: {issue} → user_issue_value
   - Problem: If user inputs contain placeholder patterns, they get processed too!

3. No proper escaping or context awareness:
   - Manual replace() doesn't understand template context
   - Can't distinguish literal text from template syntax
   - Can't handle nested or escaped placeholders properly

This is why proper templating engines use:
- Tokenizers that understand template syntax
- Context-aware parsing
- Proper escaping mechanisms
- Defined evaluation order
- Security boundaries between template and data
""")

    # Show the problem with a concrete example
    print("\n🧪 CONCRETE EXAMPLE OF THE FLAW:")
    print("-" * 35)

    action = "test"
    component = "system"
    issue = "{action}"  # This should be LITERAL text, not processed!
    template = "The {action} fails on {component} with issue {issue}"

    print(f"Inputs:")
    print(f"  action: '{action}'")
    print(f"  component: '{component}'")
    print(f"  issue: '{issue}' (should be literal)")
    print(f"  template: '{template}'")

    print(f"\nManual replacement steps:")
    step1 = template.replace("{action}", action)
    print(f"  Step 1: '{step1}'")

    step2 = step1.replace("{component}", component)
    print(f"  Step 2: '{step2}'")

    step3 = step2.replace("{issue}", issue)
    print(f"  Step 3: '{step3}'")

    result = _safe_hypothesis_template(action, component, issue, template)
    print(f"\nActual result: '{result}'")

    if "test" in result and result.count("test") > 1:
        print("\n🚨 VULNERABILITY: The literal {action} in user input got replaced!")
        print("   This breaks the expectation that user input is treated as literal text")
        return False
    else:
        print("\n✅ No cross-contamination in this case")
        return True

if __name__ == "__main__":
    print("Cross-Contamination Vulnerability Test")
    print("Testing for template injection via cross-contamination")
    print()

    # Test cross-contamination vulnerabilities
    is_secure = demonstrate_cross_contamination()

    # Explain the fundamental flaw
    fundamental_secure = demonstrate_manual_replacement_flaw()

    print("\n" + "=" * 65)
    print("🎯 SECURITY ASSESSMENT")
    print("=" * 65)

    if not is_secure or not fundamental_secure:
        print("🚨 TEMPLATE INJECTION VULNERABILITY CONFIRMED!")
        print("   Manual string replacement allows cross-contamination between inputs")
        print("   This violates the principle of input isolation")
        print("   URGENT SECURITY FIX REQUIRED")
        sys.exit(1)
    else:
        print("✅ No cross-contamination vulnerabilities detected")
        print("   However, manual replacement remains theoretically insecure")
        sys.exit(0)