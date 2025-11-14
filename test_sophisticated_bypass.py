#!/usr/bin/env python3
"""
Advanced test script to find sophisticated template injection bypass vulnerabilities.

This script tests more advanced bypass techniques that target the manual string
replacement approach in _safe_hypothesis_template.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from reasoning_library.abductive import _safe_hypothesis_template

def test_sophisticated_bypasses():
    """Test sophisticated bypass techniques that target manual replacement logic."""

    print("🔬 TESTING SOPHISTICATED BYPASS TECHNIQUES")
    print("=" * 60)

    template = "The {action} on {component} causes {issue}"

    sophisticated_attacks = [
        # Double replacement bypass - the second replacement might create new patterns
        {
            "name": "Double Replacement Bypass",
            "action": "test",
            "component": "system{action}",  # {action} gets replaced, then might create new exploit
            "issue": "failure",
            "exploit": "systemtest"  # What {action} becomes after replacement
        },

        # Partial replacement to create new patterns
        {
            "name": "Partial Pattern Creation",
            "action": "test{",  # Creates partial opening brace
            "component": "action}",
            "issue": "failure",
            "exploit": "Forms {action} after replacement"
        },

        # Replacement order manipulation
        {
            "name": "Replacement Order Attack",
            "action": "{component}",  # Will be replaced with component value
            "component": "__import__('os')",
            "issue": "failure",
            "exploit": "Action gets replaced with dangerous content"
        },

        # Nested replacement that survives sanitization
        {
            "name": "Nested After Sanitization",
            "action": "{issue}",
            "component": "component",
            "issue": "{__import__('os')}",
            "exploit": "Replacement creates new template after sanitization"
        },

        # Overlapping replacement patterns
        {
            "name": "Overlapping Pattern Attack",
            "action": "act{action}on",
            "component": "component",
            "issue": "failure",
            "exploit": "Creates {action}{action} pattern"
        },

        # Replacement chain attack
        {
            "name": "Replacement Chain Attack",
            "action": "{component}",
            "component": "{issue}",
            "issue": "__import__('os')",
            "exploit": "Chain of replacements leads to dangerous content"
        },

        # Case sensitivity bypass
        {
            "name": "Case Sensitivity Bypass",
            "action": "test",
            "component": "system{ACTION}",  # Uppercase might bypass pattern matching
            "issue": "failure",
            "exploit": "Case-sensitive replacement might miss patterns"
        },

        # Whitespace manipulation
        {
            "name": "Whitespace Manipulation",
            "action": "test",
            "component": "system{ action }",  # Spaces around braces
            "issue": "failure",
            "exploit": "Whitespace might bypass pattern matching"
        },

        # Replacement in dangerous patterns list
        {
            "name": "Dangerous Pattern Bypass",
            "action": "test",
            "component": "sys{tem}",  # Splits dangerous keyword
            "issue": "failure",
            "exploit": "Replacement reconstructs dangerous patterns"
        },

        # Template parameter confusion
        {
            "name": "Parameter Confusion",
            "action": "{component} causes {issue}",
            "component": "The action",
            "issue": "system failure",
            "exploit": "Action contains template syntax itself"
        },

        # Sanitization bypass through reconstruction
        {
            "name": "Reconstruction Attack",
            "action": "import os",
            "component": "sys{action}",  # Reconstructs import os
            "issue": "failure",
            "exploit": "Reconstruction bypasses sanitization"
        },

        # Multi-byte character bypass
        {
            "name": "Multi-byte Character Attack",
            "action": "test",
            "component": "system\xc2\xa7import__('os')",  # Using multi-byte chars
            "issue": "failure",
            "exploit": "Multi-byte chars might bypass pattern matching"
        }
    ]

    vulnerabilities_found = 0
    total_tests = len(sophisticated_attacks)

    for i, attack in enumerate(sophisticated_attacks, 1):
        print(f"\n🎯 Test {i}/{total_tests}: {attack['name']}")
        print(f"   Strategy: {attack['exploit']}")
        print(f"   Action: '{attack['action']}'")
        print(f"   Component: '{attack['component']}'")
        print(f"   Issue: '{attack['issue']}'")

        try:
            result = _safe_hypothesis_template(
                attack['action'],
                attack['component'],
                attack['issue'],
                template
            )

            print(f"   Result: '{result}'")

            # Check for dangerous patterns that indicate successful bypass
            critical_patterns = [
                '__import__',
                'system(',
                'exec(',
                'eval(',
                'subprocess',
                'popen',
                'import os',
                'import sys',
                'os.system',
                'sys.exec',
                '${',
                '%(',
                'getattr',
                'setattr',
                'delattr',
                '__class__',
                '__base__',
                '__subclasses__'
            ]

            template_patterns = [
                '{action}',
                '{component}',
                '{issue}',
                '{{',
                '}}'
            ]

            has_critical = any(pattern in result for pattern in critical_patterns)
            has_template = any(pattern in result for pattern in template_patterns)

            if has_critical:
                print("   🚨 CRITICAL: Dangerous code execution pattern found!")
                vulnerabilities_found += 1
            elif has_template:
                print("   ⚠️  WARNING: Template patterns still present - potential bypass")
                vulnerabilities_found += 1
            else:
                print("   ✅ No obvious bypass detected")

        except Exception as e:
            print(f"   💥 Exception: {type(e).__name__}: {e}")
            # Analyze if exception indicates successful attack or failed defense
            if "import" in str(e) or "exec" in str(e) or "eval" in str(e):
                print("   🚨 CRITICAL: Exception contains dangerous keywords - possible RCE!")
                vulnerabilities_found += 1
            else:
                print("   ✅ Exception appears to be defensive (good)")

    print("\n" + "=" * 60)
    print("🔍 SOPHISTICATED BYPASS ASSESSMENT")
    print("=" * 60)
    print(f"Total sophisticated tests: {total_tests}")
    print(f"Vulnerabilities found: {vulnerabilities_found}")
    print(f"Security score: {((total_tests - vulnerabilities_found) / total_tests) * 100:.1f}%")

    return vulnerabilities_found == 0

def test_template_manipulation():
    """Test manipulation of the template pattern itself."""

    print("\n🎭 TESTING TEMPLATE PATTERN MANIPULATION")
    print("=" * 50)

    # Test with malicious template patterns
    malicious_templates = [
        "Normal template with {action}",
        "{action} {component} {issue}",  # Multiple placeholders
        "The {action} on {action} causes {issue}",  # Duplicate placeholders
        "Template with {{literal}} braces and {action}",  # Literal braces
        "Template with ${{action}} and {component}",  # Mixed syntax
        "No placeholders here",  # No placeholders
        "{action} on system{component}",  # Component in suspicious context
        "The {action} causes {__import__('os')}",  # Direct injection in template
        "Template with {action} and {nonexistent}",  # Non-existent placeholder
    ]

    for i, template in enumerate(malicious_templates, 1):
        print(f"\nTemplate {i}: '{template}'")

        try:
            result = _safe_hypothesis_template(
                "test_action",
                "test_component",
                "test_issue",
                template
            )

            print(f"Result: '{result}'")

            # Check for issues
            if '{__import__' in result:
                print("🚨 Template injection successful!")
            elif '{action}' in result or '{component}' in result or '{issue}' in result:
                print("⚠️  Unexpanded placeholders remain")
            elif '${' in result or '%(' in result:
                print("⚠️  Other template syntax present")
            else:
                print("✅ Template processed safely")

        except Exception as e:
            print(f"Exception: {type(e).__name__}: {e}")

def test_sanitization_bypass():
    """Test if the sanitization can be bypassed through encoding tricks."""

    print("\n🛡️ TESTING SANITIZATION BYPASS TECHNIQUES")
    print("=" * 50)

    encoding_attacks = [
        # Various encoding of dangerous content
        {
            "name": "Hex Encoding",
            "input": "\\x69\\x6d\\x70\\x6f\\x72\\x74\\x20\\x6f\\x73",  # "import os" in hex
            "expected": "should be blocked"
        },
        {
            "name": "Octal Encoding",
            "input": "\\151\\155\\160\\157\\162\\164\\040\\157\\163",  # "import os" in octal
            "expected": "should be blocked"
        },
        {
            "name": "Unicode Escape",
            "input": "\\u0069\\u006d\\u0070\\u006f\\u0072\\u0074\\u0020\\u006f\\u0073",  # "import os" in unicode
            "expected": "should be blocked"
        },
        {
            "name": "Mixed Encodings",
            "input": "\\x69mport \\u006f\\x73",
            "expected": "should be blocked"
        },
        {
            "name": "Partial Encoding",
            "input": "im\\x70ort o\\163",
            "expected": "should be blocked"
        },
        {
            "name": "String Concatenation",
            "input": "'im' + 'port' + ' ' + 'os'",
            "expected": "might bypass pattern matching"
        }
    ]

    for attack in encoding_attacks:
        print(f"\nTesting {attack['name']}: '{attack['input']}'")
        print(f"Expected: {attack['expected']}")

        try:
            # Test the encoding in different positions
            positions = ['action', 'component', 'issue']

            for pos in positions:
                result = _safe_hypothesis_template(
                    attack['input'] if pos == 'action' else 'test',
                    attack['input'] if pos == 'component' else 'test',
                    attack['input'] if pos == 'issue' else 'test',
                    "The {action} on {component} causes {issue}"
                )

                # Check if the dangerous content survived
                if 'import os' in result or 'import' in result or 'os' in result:
                    print(f"   🚨 {pos.upper()}: Encoding bypass successful!")
                elif '\\x' in result or '\\u' in result or '+' in result:
                    print(f"   ⚠️  {pos.upper()}: Encoded content present but not executed")
                else:
                    print(f"   ✅ {pos.upper()}: Blocked successfully")

        except Exception as e:
            print(f"   Exception during encoding test: {e}")

if __name__ == "__main__":
    print("Advanced Template Injection Bypass Test")
    print("This script tests sophisticated bypass techniques")
    print()

    # Test sophisticated bypasses
    is_secure = test_sophisticated_bypasses()

    # Test template manipulation
    test_template_manipulation()

    # Test sanitization bypass
    test_sanitization_bypass()

    print("\n" + "=" * 60)
    if is_secure:
        print("✅ No sophisticated bypasses detected")
        print("   (Still recommend implementing proper secure templating)")
        sys.exit(0)
    else:
        print("🚨 SOPHISTICATED BYPASSES DETECTED!")
        print("   Manual string replacement approach has vulnerabilities")
        sys.exit(1)