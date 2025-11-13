"""
Comprehensive security tests for the type coercion vulnerability fix in validate_confidence_value().

This test suite validates that the type coercion vulnerability has been properly addressed
and that dangerous string inputs are securely rejected.
"""

import pytest
from reasoning_library.validation import validate_confidence_value
from reasoning_library.exceptions import ValidationError


class TestConfidenceSecurityFix:
    """Test the security fix for type coercion vulnerability."""

    def test_dangerous_string_inputs_rejected(self):
        """Test that dangerous string inputs are properly rejected."""

        dangerous_inputs = [
            "nan",           # NaN string
            "NaN",           # NaN uppercase
            "NAN",           # NaN all caps
            "inf",           # Infinity string
            "-inf",          # Negative infinity
            "infinity",      # Infinity word
            "1e10",          # Scientific notation large
            "1e-10",         # Scientific notation small
            "-1e-10",        # Scientific notation negative
            "0x1",           # Hexadecimal
            "0b1",           # Binary
            "0o1",           # Octal
            "",              # Empty string
            "   ",           # Whitespace only
            "null",          # Null string
            "undefined",     # Undefined string
            "true",          # Boolean true
            "false",         # Boolean false
            "123abc",        # Mixed alphanumeric
            "abc123",        # Mixed alphanumeric
            "1+1",           # Expression
            "1/0",           # Division by zero expression
            "--1",           # Double negative
            "++1",           # Double positive
            "1.2.3",         # Multiple decimal points
            "1..2",          # Double decimal point
            ".",             # Just decimal point
            "-.5.",          # Invalid decimal format
            "1.0e10",        # Mixed decimal and scientific
        ]

        for dangerous_input in dangerous_inputs:
            with pytest.raises(ValidationError, match="Confidence value.*"):
                validate_confidence_value(dangerous_input)

    def test_valid_string_inputs_accepted(self):
        """Test that valid string inputs are properly accepted and processed."""

        valid_inputs = [
            ("0.5", 0.5),
            ("0.75", 0.75),
            ("1.0", 1.0),
            ("0.0", 0.0),
            ("1", 1.0),
            ("0", 0.0),
            ("  0.75  ", 0.75),  # Whitespace trimmed
            ("+0.5", 0.5),       # Positive sign
            ("-0.5", 0.0),       # Negative value gets clamped
            ("1.5", 1.0),        # Value gets clamped to 1.0
            ("0.0000000001", 0.0000000001),  # Very small decimal
            ("1.0000000001", 1.0),  # Just over 1.0, gets clamped
            ("-0.0000000001", 0.0),  # Just under 0.0, gets clamped
            (".5", 0.5),          # Leading decimal point
            ("0.", 0.0),          # Trailing decimal point
            ("0.999", 0.999),     # High precision
            ("0.001", 0.001),     # Low precision
        ]

        for input_str, expected in valid_inputs:
            result = validate_confidence_value(input_str)
            assert abs(result - expected) < 1e-10, f"Failed for input '{input_str}': expected {expected}, got {result}"

    def test_numeric_inputs_still_work(self):
        """Test that the original numeric input functionality is preserved."""

        numeric_inputs = [
            (0.5, 0.5),
            (1, 1.0),
            (0.0, 0.0),
            (-0.5, 0.0),    # Gets clamped
            (1.5, 1.0),     # Gets clamped
        ]

        for input_val, expected in numeric_inputs:
            result = validate_confidence_value(input_val)
            assert abs(result - expected) < 1e-10

    def test_none_input_rejected(self):
        """Test that None input is properly rejected."""
        with pytest.raises(ValidationError, match="Confidence value cannot be None"):
            validate_confidence_value(None)

    def test_nan_infinity_floats_rejected(self):
        """Test that NaN and infinity floats are still rejected."""

        with pytest.raises(ValidationError, match="Confidence cannot be NaN"):
            validate_confidence_value(float('nan'))

        with pytest.raises(ValidationError, match="Confidence cannot be infinite"):
            validate_confidence_value(float('inf'))

        with pytest.raises(ValidationError, match="Confidence cannot be infinite"):
            validate_confidence_value(float('-inf'))

    def test_error_messages_are_specific(self):
        """Test that error messages provide specific, helpful information."""

        # Test empty string error
        with pytest.raises(ValidationError) as exc_info:
            validate_confidence_value("")
        assert "cannot be empty" in str(exc_info.value).lower()

        # Test invalid characters error
        with pytest.raises(ValidationError) as exc_info:
            validate_confidence_value("abc")
        assert "invalid characters" in str(exc_info.value).lower()

        # Test dangerous format error
        with pytest.raises(ValidationError) as exc_info:
            validate_confidence_value("1e10")
        assert "invalid format" in str(exc_info.value).lower() or "dangerous" in str(exc_info.value).lower()

    def test_bounds_enforcement(self):
        """Test that confidence values are properly clamped to [0.0, 1.0] range."""

        # Test clamping from above
        result = validate_confidence_value("1.5")
        assert result == 1.0

        result = validate_confidence_value("10.0")
        assert result == 1.0

        # Test clamping from below
        result = validate_confidence_value("-0.5")
        assert result == 0.0

        result = validate_confidence_value("-10.0")
        assert result == 0.0

        # Test exact boundaries
        result = validate_confidence_value("0.0")
        assert result == 0.0

        result = validate_confidence_value("1.0")
        assert result == 1.0

    def test_precision_preservation(self):
        """Test that precision is preserved for valid decimal inputs."""

        precision_tests = [
            ("0.123456789", 0.123456789),
            ("0.987654321", 0.987654321),
            ("0.001", 0.001),
            ("0.999", 0.999),
        ]

        for input_str, expected in precision_tests:
            result = validate_confidence_value(input_str)
            assert abs(result - expected) < 1e-15


if __name__ == "__main__":
    pytest.main([__file__])