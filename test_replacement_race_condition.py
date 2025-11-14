#!/usr/bin/env python3
"""
Test for replacement race condition and order-dependent vulnerabilities in manual string replacement.

This test targets the fundamental issue with manual string replacement: the order of operations
and potential for incomplete replacements that can leave dangerous partial patterns.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from reasoning_library.abductive import _safe_hypothesis_template

def test_replacement_order_vulnerabilities():
    """Test vulnerabilities in the replacement order logic."""

    print("🔄 TESTING REPLACEMENT ORDER VULNERABILITIES")
    print("=" * 60)

    # The current implementation does:
    # 1. Replace {action} with safe_action
    # 2. Replace {component} with safe_component
    # 3. Replace {issue} with safe_issue

    # This creates vulnerabilities when:
    # - Replacement strings contain placeholder patterns
    # - Multiple passes through replacements are needed
    # - Partial replacements create new dangerous patterns

    test_cases = [
        # Case 1: Replacement strings contain other placeholder patterns
        {
            "name": "Cross-Contamination Attack",
            "action": "{component}",
            "component": "__import__('os')",
            "issue": "failure",
            "template": "The {action} on {component} causes {issue}",
            "vulnerability": "action gets replaced with component's dangerous content"
        },

        # Case 2: Replacement creates nested patterns
        {
            "name": "Nested Pattern Creation",
            "action": "test",
            "component": "system{__import__('os')}",
            "issue": "failure",
            "template": "The {action} on {component} causes {issue}",
            "vulnerability": "component replacement leaves inner pattern"
        },

        # Case 3: Multiple identical placeholders
        {
            "name": "Multiple Placeholder Race Condition",
            "action": "{component}",
            "component": "test_component",
            "issue": "{action}",
            "template": "The {action} on {component} and {issue}",
            "vulnerability": "Order-dependent replacement creates inconsistent results"
        },

        # Case 4: Replacement sanitization bypass
        {
            "name": "Post-Reconstruction Attack",
            "action": "test",
            "component": "im{action}rt",  # Attempts to reconstruct "import" after replacement
            "issue": "failure",
            "template": "The {action} on {component} causes {issue}",
            "vulnerability": "Replacement reconstructs dangerous keywords"
        },

        # Case 5: Bracket manipulation during replacement
        {
            "name": "Bracket Reassembly Attack",
            "action": "{",
            "component": "}",
            "issue": "__import__('os')",
            "template": "The {action}action{component} causes {issue}",
            "vulnerability": "Brackets get reassembled around dangerous content"
        },

        # Case 6: Template injection through replacement
        {
            "name": "Template Injection via Replacement",
            "action": "test",
            "component": "${__import__('os')}",  # Different template syntax
            "issue": "failure",
            "template": "The {action} on {component} causes {issue}",
            "vulnerability": "Different template syntax survives replacement"
        },

        # Case 7: Escaping the replacement logic
        {
            "name": "Replacement Logic Escape",
            "action": "test",
            "component": "system\\{action\\}",  # Escaped braces that might be interpreted later
            "issue": "failure",
            "template": "The {action} on {component} causes {issue}",
            "vulnerability": "Escaped brackets might be processed by other systems"
        },

        # Case 8: Multi-stage replacement attack
        {
            "name": "Multi-Stage Replacement",
            "action": "act{component}on",
            "component": "{issue}",
            "issue": "__import__('os')",
            "template": "The {action} on system causes {issue}",
            "vulnerability": "Nested replacements propagate dangerous content"
        }
    ]

    vulnerabilities_found = 0

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🎯 Test {i}/{len(test_cases)}: {test_case['name']}")
        print(f"   Strategy: {test_case['vulnerability']}")
        print(f"   Template: '{test_case['template']}'")
        print(f"   Action: '{test_case['action']}'")
        print(f"   Component: '{test_case['component']}'")
        print(f"   Issue: '{test_case['issue']}'")

        try:
            # Step-by-step analysis of what happens during replacement
            print("   📝 Manual replacement analysis:")

            # Show what each replacement step does
            step1 = test_case['template'].replace("{action}", "[ACTION_PLACEHOLDER]")
            print(f"      Step 1 (action removal): '{step1}'")

            step2 = step1.replace("{component}", "[COMPONENT_PLACEHOLDER]")
            print(f"      Step 2 (component removal): '{step2}'")

            step3 = step2.replace("{issue}", "[ISSUE_PLACEHOLDER]")
            print(f"      Step 3 (issue removal): '{step3}'")

            # Now test with actual function
            result = _safe_hypothesis_template(
                test_case['action'],
                test_case['component'],
                test_case['issue'],
                test_case['template']
            )

            print(f"   📤 Actual result: '{result}'")

            # Check for dangerous patterns that might indicate successful bypass
            dangerous_patterns = [
                '__import__',
                'system(',
                'exec(',
                'eval(',
                'subprocess',
                'popen',
                'import os',
                'import sys',
                'os.system',
                'getattr',
                'setattr',
                '__class__',
                '__base__',
                '${',
                '%('
            ]

            residual_patterns = [
                '{action}',
                '{component}',
                '{issue}',
                '{{',
                '}}'
            ]

            has_dangerous = any(pattern in result for pattern in dangerous_patterns)
            has_residual = any(pattern in result for pattern in residual_patterns)

            # Check for partial dangerous patterns
            partial_dangerous = [
                'import',
                'system',
                'exec',
                'eval',
                'getattr',
                '__class',
                '__base'
            ]

            has_partial = any(pattern in result for pattern in partial_dangerous)

            if has_dangerous:
                print("   🚨 VULNERABILITY: Dangerous code execution pattern found!")
                vulnerabilities_found += 1
            elif has_residual:
                print("   ⚠️  VULNERABILITY: Unexpanded template patterns remain!")
                vulnerabilities_found += 1
            elif has_partial:
                print("   ⚠️  WARNING: Partial dangerous patterns detected - potential bypass")
                # Count partial as potential vulnerability
                if any(p in result for p in ['import', 'system']) and 'action' in result:
                    vulnerabilities_found += 1
            else:
                print("   ✅ No obvious vulnerability detected")

        except Exception as e:
            print(f"   💥 Exception: {type(e).__name__}: {e}")
            # Check if exception indicates successful attack
            if any(keyword in str(e).lower() for keyword in ['import', 'exec', 'eval', 'system']):
                print("   🚨 VULNERABILITY: Exception contains dangerous keywords!")
                vulnerabilities_found += 1

    print("\n" + "=" * 60)
    print("📊 REPLACEMENT VULNERABILITY ASSESSMENT")
    print("=" * 60)
    print(f"Total tests: {len(test_cases)}")
    print(f"Vulnerabilities found: {vulnerabilities_found}")
    print(f"Security score: {((len(test_cases) - vulnerabilities_found) / len(test_cases)) * 100:.1f}%")

    return vulnerabilities_found == 0

def demonstrate_manual_replacement_flaw():
    """Demonstrate the fundamental flaw with manual string replacement."""

    print("\n💡 DEMONSTRATING MANUAL REPLACEMENT FUNDAMENTAL FLAW")
    print("=" * 65)

    print("""
The fundamental issue with manual string replacement is that it creates
a race condition where:

1. Input sanitization happens FIRST
2. String replacement happens SECOND
3. Final pattern checking happens THIRD

This allows attackers to manipulate the order of operations to bypass security.

Example attack:
- Input: "im{action}rt os"
- After sanitization: "im[SAFE_ACTION]rt os"
- After replacement: "import os"  ← DANGEROUS CONTENT RECONSTRUCTED!
""")

    # Demonstrate the attack
    print("🧪 Live demonstration of the attack:")

    malicious_action = "im{action}rt os"
    malicious_component = "test_system"
    malicious_issue = "failure"
    template = "The {action} on {component} causes {issue}"

    print(f"   Malicious action: '{malicious_action}'")
    print(f"   Template: '{template}'")

    try:
        result = _safe_hypothesis_template(
            malicious_action,
            malicious_component,
            malicious_issue,
            template
        )

        print(f"   Result: '{result}'")

        if "import" in result:
            print("   🚨 SUCCESS: Demonstrated dangerous keyword reconstruction!")
            return False
        else:
            print("   ✅ Attack blocked - reconstruction failed")
            return True

    except Exception as e:
        print(f"   Exception: {e}")
        return True

if __name__ == "__main__":
    print("Manual String Replacement Vulnerability Test")
    print("This demonstrates the fundamental flaws in manual replacement approach")
    print()

    # Test replacement order vulnerabilities
    is_secure = test_replacement_order_vulnerabilities()

    # Demonstrate the fundamental flaw
    fundamental_secure = demonstrate_manual_replacement_flaw()

    print("\n" + "=" * 65)
    print("🎯 FINAL ASSESSMENT")
    print("=" * 65)

    if not is_secure or not fundamental_secure:
        print("🚨 CRITICAL VULNERABILITIES DETECTED!")
        print("   Manual string replacement approach has fundamental security flaws")
        print("   URGENT: Replace with proper secure templating system")
        sys.exit(1)
    else:
        print("✅ No vulnerabilities detected in current tests")
        print("   (However, manual replacement is inherently risky - recommend fix)")
        sys.exit(0)