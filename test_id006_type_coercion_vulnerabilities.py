"""
Test file specifically for ID-006 Type Coercion Issues in Metrics Evaluation.

This test demonstrates potential type coercion vulnerabilities in metrics evaluation
functions and ensures strict equality checks are properly implemented.
"""

import pytest
import numpy as np
from reasoning_library.validation import (
    validate_numeric_value,
    validate_confidence_range,
    validate_positive_numeric,
    safe_divide
)
from reasoning_library.exceptions import ValidationError


class TestTypeCoercionVulnerabilities:
    """Test cases for type coercion vulnerabilities in metrics evaluation."""

    def test_string_zero_vs_numeric_zero_comparison(self):
        """Test that string '0' is not treated as numeric 0."""
        # This should fail with strict type checking
        with pytest.raises(ValidationError):
            validate_numeric_value("0", "test_value")

    def test_string_one_vs_numeric_one_comparison(self):
        """Test that string '1' is not treated as numeric 1."""
        # This should fail with strict type checking
        with pytest.raises(ValidationError):
            validate_confidence_range("1", "test_confidence")

    def test_boolean_true_vs_numeric_one_comparison(self):
        """Test that boolean True is not treated as numeric 1."""
        # This should fail with strict type checking - booleans should not be accepted as numbers
        with pytest.raises(ValidationError):
            validate_confidence_range(True, "test_confidence")

    def test_boolean_false_vs_numeric_zero_comparison(self):
        """Test that boolean False is not treated as numeric 0."""
        # This should fail with strict type checking - booleans should not be accepted as numbers
        with pytest.raises(ValidationError):
            validate_positive_numeric(False, "test_value")

    def test_none_vs_zero_comparison(self):
        """Test that None is not treated as 0 in numeric contexts."""
        # This should fail with strict type checking
        with pytest.raises(ValidationError):
            validate_positive_numeric(None, "test_value")

    def test_string_inf_vs_numeric_infinity_comparison(self):
        """Test that string 'inf' is not treated as infinity."""
        with pytest.raises(ValidationError):
            validate_numeric_value("inf", "test_value")

    def test_list_with_zero_vs_numeric_zero(self):
        """Test that list with 0 is not treated as numeric 0."""
        with pytest.raises(ValidationError):
            validate_numeric_value([0], "test_value")

    def test_numpy_array_vs_scalar_comparison(self):
        """Test that numpy arrays are not coerced to scalars."""
        with pytest.raises(ValidationError):
            validate_confidence_range(np.array([0.5]), "test_confidence")

    def test_complex_number_vs_real_number(self):
        """Test that complex numbers are not accepted as real numbers."""
        with pytest.raises(ValidationError):
            validate_numeric_value(1+2j, "test_value")

    def test_bytes_string_vs_regular_string(self):
        """Test that bytes are not treated as strings."""
        with pytest.raises(ValidationError):
            validate_numeric_value(b"0.5", "test_value")


class TestStrictEqualityInMetrics:
    """Test strict equality checks in metrics evaluation."""

    def test_safe_divide_type_coercion_protection(self):
        """Test that safe_divide protects against type coercion in numerator/denominator."""
        # Test with string that looks like a number
        with pytest.raises(ValidationError):
            safe_divide("10", "2", "test_division")

        # Test with boolean values
        with pytest.raises(ValidationError):
            safe_divide(True, False, "test_division")

        # Test with None values
        with pytest.raises(ValidationError):
            safe_divide(None, None, "test_division")

    def test_numeric_validation_edge_cases(self):
        """Test edge cases that could cause type coercion issues."""
        # Test with decimal string that could be coerced
        with pytest.raises(ValidationError):
            validate_numeric_value("3.14159", "test_value")

        # Test with scientific notation string
        with pytest.raises(ValidationError):
            validate_numeric_value("1e-10", "test_value")

        # Test with hexadecimal string
        with pytest.raises(ValidationError):
            validate_numeric_value("0xFF", "test_value")

        # Test with octal string
        with pytest.raises(ValidationError):
            validate_numeric_value("0755", "test_value")


class TestMetricsEvaluationTypeSafety:
    """Test type safety in metrics evaluation functions."""

    def test_array_vs_scalar_confusion(self):
        """Test that arrays are not confused with scalars in metrics."""
        # These should all fail with proper type checking
        invalid_values = [
            np.array([1]),           # Array with single element
            [1.0],                    # List with single element
            "1.0",                    # String representation
            "True",                   # String boolean
            b"1.0",                   # Bytes representation
            {1: "numeric"},           # Dict with numeric key
            (1.0,),                   # Tuple with single element
        ]

        for invalid_value in invalid_values:
            with pytest.raises(ValidationError):
                validate_confidence_range(invalid_value, f"test_confidence_{type(invalid_value).__name__}")

    def test_float_precision_equality_issues(self):
        """Test that floating point precision doesn't cause unexpected equality issues."""
        # These should pass as they are valid floats within range
        valid_values = [
            0.0,
            1.0,
            0.5,
            0.1,
            0.9,
            1e-10,  # Very small positive number
            1.0 - 1e-10,  # Just under 1.0
        ]

        for valid_value in valid_values:
            try:
                result = validate_confidence_range(valid_value, f"test_confidence_{valid_value}")
                assert isinstance(result, float)
                assert 0.0 <= result <= 1.0
            except ValidationError:
                # This should not happen for valid float values
                pytest.fail(f"Valid float value {valid_value} was rejected")

    def test_nan_and_infinity_handling(self):
        """Test that NaN and infinity are properly handled."""
        invalid_values = [
            float('nan'),
            float('inf'),
            float('-inf'),
            np.nan,
            np.inf,
            -np.inf,
        ]

        for invalid_value in invalid_values:
            with pytest.raises(ValidationError):
                validate_numeric_value(invalid_value, f"test_value_{type(invalid_value).__name__}")


class TestStrictEqualityInBooleanContexts:
    """Test strict equality checks in boolean contexts."""

    def test_string_boolean_vs_actual_boolean(self):
        """Test that string booleans are not treated as actual booleans."""
        # These should fail strict boolean checks
        string_booleans = ["True", "False", "true", "false", "1", "0"]

        for string_bool in string_booleans:
            # These should be rejected as boolean values
            if string_bool in ["1", "0"]:
                # Test as potential numeric values
                with pytest.raises(ValidationError):
                    validate_numeric_value(string_bool, f"test_string_bool_{string_bool}")

    def test_empty_string_vs_false(self):
        """Test that empty string is not treated as False."""
        with pytest.raises(ValidationError):
            validate_numeric_value("", "test_empty_string")

    def test_empty_list_vs_false(self):
        """Test that empty list is not treated as False."""
        with pytest.raises(ValidationError):
            validate_numeric_value([], "test_empty_list")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])