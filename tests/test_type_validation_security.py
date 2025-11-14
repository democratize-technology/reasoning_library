"""
Comprehensive test coverage for type validation security improvements.

This test file verifies that all arithmetic operations are protected against
type validation vulnerabilities while maintaining backward compatibility.
"""

import pytest
import numpy as np
from reasoning_library.exceptions import ValidationError
from reasoning_library.validation import (
    validate_numeric_sequence,
    validate_numeric_value,
    validate_positive_numeric,
    validate_confidence_range,
    validate_sequence_length,
    safe_divide,
    safe_array_operation,
    validate_arithmetic_inputs,
    validate_arithmetic_operation
)
from reasoning_library.inductive import (
    _calculate_arithmetic_confidence,
    _calculate_geometric_confidence,
    _calculate_pattern_quality_score_optimized,
    _check_arithmetic_progression,
    _check_geometric_progression,
    detect_fibonacci_pattern,
    detect_polynomial_pattern,
    detect_exponential_pattern
)
from reasoning_library.abductive import (
    _calculate_hypothesis_confidence
)


class TestNumericValidationUtilities:
    """Test the numeric validation utilities."""

    def test_validate_numeric_sequence_valid_inputs(self):
        """Test validation with valid numeric sequences."""
        valid_inputs = [
            [1.0, 2.0, 3.0, 4.0],
            [1, 2, 3, 4],
            np.array([1.0, 2.0, 3.0]),
            (1.0, 2.0, 3.0),
        ]

        for valid_input in valid_inputs:
            result = validate_numeric_sequence(valid_input)
            assert isinstance(result, np.ndarray)
            assert len(result) > 0
            assert not np.any(np.isnan(result))
            assert not np.any(np.isinf(result))

    def test_validate_numeric_sequence_invalid_inputs(self):
        """Test validation with invalid numeric sequences."""
        invalid_inputs = [
            None,
            "not_a_sequence",
            [1, 2, "three", 4],
            [1, 2, None, 4],
            [1, 2, {"key": "value"}, 4],
            [],  # empty
            [np.nan, 1, 2],  # contains NaN
            [np.inf, 1, 2],  # contains infinity
        ]

        for invalid_input in invalid_inputs:
            with pytest.raises(ValidationError):
                validate_numeric_sequence(invalid_input)

    def test_validate_numeric_value_valid_inputs(self):
        """Test numeric value validation with valid inputs."""
        valid_inputs = [
            (1.0, True, True),
            (1, True, True),
            (0.5, True, True),
            (-3.14, True, True),
        ]

        for value, allow_float, allow_int in valid_inputs:
            result = validate_numeric_value(value, "test", allow_float, allow_int)
            assert isinstance(result, float)
            assert not np.isnan(result)
            assert not np.isinf(result)

    def test_validate_numeric_value_invalid_inputs(self):
        """Test numeric value validation with invalid inputs."""
        invalid_inputs = [
            None,
            "not_a_number",
            {"key": "value"},
            [1, 2, 3],
            np.nan,
            np.inf,
            -np.inf,
        ]

        for invalid_input in invalid_inputs:
            with pytest.raises(ValidationError):
                validate_numeric_value(invalid_input)

    def test_validate_positive_numeric(self):
        """Test positive numeric validation."""
        valid_inputs = [1.0, 1, 0.1, 100, np.array([1.0])[0]]
        invalid_inputs = [0, -1, -0.1, None, "not_a_number"]

        for valid_input in valid_inputs:
            result = validate_positive_numeric(valid_input)
            assert result > 0

        for invalid_input in invalid_inputs:
            with pytest.raises(ValidationError):
                validate_positive_numeric(invalid_input)

    def test_validate_confidence_range(self):
        """Test confidence range validation."""
        valid_inputs = [0.0, 0.5, 1.0, 0.25, 0.75]
        invalid_inputs = [-0.1, 1.1, None, "not_a_number", 2.0, -1.0]

        for valid_input in valid_inputs:
            result = validate_confidence_range(valid_input)
            assert 0.0 <= result <= 1.0

        for invalid_input in invalid_inputs:
            with pytest.raises(ValidationError):
                validate_confidence_range(invalid_input)

    def test_validate_sequence_length(self):
        """Test sequence length validation."""
        valid_inputs = [1, 10, 100, 1000]
        invalid_inputs = [0, -1, None, "not_a_number", 1.5, 1000001]

        for valid_input in valid_inputs:
            result = validate_sequence_length(valid_input)
            assert isinstance(result, int)
            assert result > 0

        for invalid_input in invalid_inputs:
            with pytest.raises(ValidationError):
                validate_sequence_length(invalid_input)


class TestSafeArithmeticOperations:
    """Test safe arithmetic operations."""

    def test_safe_divide_valid_operations(self):
        """Test safe division with valid inputs."""
        test_cases = [
            (10, 2, 5.0),
            (5, 2, 2.5),
            (10, 4, 2.5),
            (-10, 2, -5.0),
        ]

        for num, den, expected in test_cases:
            result = safe_divide(num, den)
            assert result == expected

    def test_safe_divide_zero_denominator(self):
        """Test safe division with zero denominator."""
        result = safe_divide(10, 0, default_value=99.0)
        assert result == 99.0

        result = safe_divide(10, 0.00000000001)  # Near zero - gets treated as zero (1e-11 < 1e-10)
        assert result == 0.0  # Default value

    def test_safe_divide_invalid_inputs(self):
        """Test safe division with invalid inputs."""
        # ID-006: After fixing type coercion, safe_divide should raise ValidationError for invalid inputs
        test_cases = [
            (None, 2),
            ("not_a_number", 2),
            (10, None),
            (10, "not_a_number"),
            (True, False),  # Boolean values should not be accepted as numbers
        ]

        for num, den in test_cases:
            with pytest.raises(ValidationError):
                safe_divide(num, den, default_value=88.0)

    def test_safe_array_operation_valid(self):
        """Test safe array operations with valid inputs."""
        valid_array = [1.0, 2.0, 3.0, 4.0]

        # Test std operation
        result = safe_array_operation(np.std, valid_array)
        assert isinstance(result, (float, np.floating))
        assert not np.isnan(result)

        # Test mean operation
        result = safe_array_operation(np.mean, valid_array)
        assert isinstance(result, (float, np.floating))
        assert not np.isnan(result)

    def test_safe_array_operation_invalid_inputs(self):
        """Test safe array operations with invalid inputs."""
        invalid_arrays = [
            None,
            "not_an_array",
            [1, 2, "three", 4],
            [np.nan, 1, 2],
            [np.inf, 1, 2],
        ]

        for invalid_array in invalid_arrays:
            with pytest.raises(ValidationError):
                safe_array_operation(np.std, invalid_array)

    def test_validate_arithmetic_inputs(self):
        """Test multiple input validation."""
        valid_array1 = [1.0, 2.0, 3.0]
        valid_array2 = [4.0, 5.0, 6.0]

        # Should not raise exception
        validate_arithmetic_inputs(valid_array1, valid_array2, scalar1=1.0, scalar2=2)

        # Test with invalid inputs
        with pytest.raises(ValidationError):
            validate_arithmetic_inputs(None, valid_array1)

        with pytest.raises(ValidationError):
            validate_arithmetic_inputs(valid_array1, valid_array2, scalar1="not_a_number")


class TestArithmeticFunctionValidation:
    """Test validation in arithmetic functions."""

    def test_calculate_arithmetic_confidence_with_validation(self):
        """Test arithmetic confidence calculation with type validation."""
        valid_array = np.array([1.0, 1.0, 1.0, 1.0])

        # Valid input should work
        result = _calculate_arithmetic_confidence(valid_array, 4, 0.8)
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0

        # Invalid inputs should raise ValidationError
        invalid_test_cases = [
            (None, 4, 0.8),
            ("not_an_array", 4, 0.8),
            (np.array([1, "string", 3]), 4, 0.8),
            (valid_array, None, 0.8),
            (valid_array, "not_a_number", 0.8),
            (valid_array, 4, None),
            (valid_array, 4, "not_a_number"),
            (valid_array, 4, 2.0),  # Confidence out of range
            (valid_array, 4, -0.1),  # Confidence out of range
        ]

        for diffs, seq_len, base_conf in invalid_test_cases:
            with pytest.raises(ValidationError):
                _calculate_arithmetic_confidence(diffs, seq_len, base_conf)

    def test_calculate_geometric_confidence_with_validation(self):
        """Test geometric confidence calculation with type validation."""
        valid_ratios = [1.0, 1.0, 1.0]

        # Valid input should work
        result = _calculate_geometric_confidence(valid_ratios, 4, 0.7)
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0

        # Invalid inputs should raise ValidationError
        invalid_test_cases = [
            (None, 4, 0.7),
            (["not", "numeric", "ratios"], 4, 0.7),
            ([1, 2, None, 4], 4, 0.7),
            (valid_ratios, None, 0.7),
            (valid_ratios, "not_a_number", 0.7),
            (valid_ratios, 4, None),
            (valid_ratios, 4, 1.5),  # Confidence out of range
        ]

        for ratios, seq_len, base_conf in invalid_test_cases:
            with pytest.raises(ValidationError):
                _calculate_geometric_confidence(ratios, seq_len, base_conf)

    def test_pattern_quality_score_with_validation(self):
        """Test pattern quality score calculation with type validation."""
        valid_values = [1.0, 1.0, 1.0]

        # Valid input should work
        result = _calculate_pattern_quality_score_optimized(valid_values, "arithmetic")
        assert isinstance(result, float)
        assert result > 0

        # Invalid inputs should raise ValidationError
        invalid_inputs = [
            None,
            "not_a_sequence",
            [1, 2, "three", 4],
            [1, 2, None, 4],
            [np.nan, 1, 2],
            [np.inf, 1, 2],
            [],  # empty
        ]

        for invalid_input in invalid_inputs:
            with pytest.raises(ValidationError):
                _calculate_pattern_quality_score_optimized(invalid_input, "arithmetic")

    def test_check_arithmetic_progression_with_validation(self):
        """Test arithmetic progression check with type validation."""
        valid_sequence = [1.0, 2.0, 3.0, 4.0]

        # Valid input should work
        result = _check_arithmetic_progression(valid_sequence, 0.1, 1e-8)
        assert result is None or isinstance(result, tuple)

        # Invalid inputs should raise ValidationError
        invalid_test_cases = [
            (None, 0.1, 1e-8),
            (["not", "numeric"], 0.1, 1e-8),
            ([], 0.1, 1e-8),  # empty
            (valid_sequence, "not_a_number", 1e-8),
            (valid_sequence, 0.1, "not_a_number"),
        ]

        for seq, rtol, atol in invalid_test_cases:
            with pytest.raises(ValidationError):
                _check_arithmetic_progression(seq, rtol, atol)

    def test_check_geometric_progression_with_validation(self):
        """Test geometric progression check with type validation."""
        valid_sequence = [1.0, 2.0, 4.0, 8.0]

        # Valid input should work
        result = _check_geometric_progression(valid_sequence, 0.1, 1e-8)
        assert result is None or isinstance(result, tuple)

        # Invalid inputs should raise ValidationError
        invalid_test_cases = [
            (None, 0.1, 1e-8),
            (["not", "numeric"], 0.1, 1e-8),
            ([], 0.1, 1e-8),  # empty
            (valid_sequence, "not_a_number", 1e-8),
            (valid_sequence, 0.1, "not_a_number"),
        ]

        for seq, rtol, atol in invalid_test_cases:
            with pytest.raises(ValidationError):
                _check_geometric_progression(seq, rtol, atol)


class TestAbductiveValidation:
    """Test type validation in abductive reasoning."""

    def test_calculate_hypothesis_confidence_with_validation(self):
        """Test hypothesis confidence calculation with type validation."""
        valid_hypothesis = {
            "description": "Test hypothesis",
            "testable_predictions": ["prediction1", "prediction2"]
        }

        # Valid input should work
        result = _calculate_hypothesis_confidence(valid_hypothesis, 10, 5, 2, 0.7)
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0

        # Invalid inputs should raise ValidationError
        invalid_test_cases = [
            (valid_hypothesis, None, 5, 2, 0.7),  # Invalid total_observations
            (valid_hypothesis, 10, "not_a_number", 2, 0.7),  # Invalid explained_observations
            (valid_hypothesis, 10, None, 2, 0.7),  # Invalid explained_observations
            (valid_hypothesis, 10, 5, None, 0.7),  # Invalid assumption_count
            (valid_hypothesis, 10, 5, 2, None),  # Invalid base_confidence
            (valid_hypothesis, 10, 5, 2, 1.5),  # Confidence out of range
            (valid_hypothesis, 10, 5, 2, -0.1),  # Confidence out of range
            (valid_hypothesis, 10, 5, -1, 0.7),  # Negative assumption count
        ]

        for hyp, total_obs, explained_obs, assumption_count, base_conf in invalid_test_cases:
            with pytest.raises(ValidationError):
                _calculate_hypothesis_confidence(hyp, total_obs, explained_obs, assumption_count, base_conf)


class TestDecoratorValidation:
    """Test the validation decorator."""

    def test_validate_arithmetic_operation_decorator(self):
        """Test the arithmetic operation validation decorator."""

        @validate_arithmetic_operation('array1', 'array2', factor='confidence')
        def test_function(array1, array2, factor=0.5):
            return np.mean(array1) + np.mean(array2) * factor

        # Valid inputs should work
        result = test_function([1, 2, 3], [4, 5, 6], factor=0.8)
        assert isinstance(result, (float, np.floating))

        # Invalid inputs should raise ValidationError
        with pytest.raises(ValidationError):
            test_function(None, [1, 2, 3])

        with pytest.raises(ValidationError):
            test_function([1, 2, 3], "not_an_array")

        with pytest.raises(ValidationError):
            test_function([1, 2, 3], [4, 5, 6], factor="not_a_number")

        with pytest.raises(ValidationError):
            test_function([1, 2, 3], [4, 5, 6], factor=2.0)  # Out of range


class TestBackwardCompatibility:
    """Test that type validation maintains backward compatibility."""

    def test_backward_compatibility_valid_inputs(self):
        """Test that all valid inputs still work as before."""
        test_cases = [
            # Arithmetic confidence
            (_calculate_arithmetic_confidence, [np.array([1.0, 1.0, 1.0]), 3, 0.8]),

            # Geometric confidence
            (_calculate_geometric_confidence, [[1.0, 1.0, 1.0], 3, 0.7]),

            # Pattern quality
            (_calculate_pattern_quality_score_optimized, [[1.0, 1.0, 1.0], "arithmetic"]),

            # Arithmetic progression check
            (_check_arithmetic_progression, [[1.0, 2.0, 3.0, 4.0], 0.1, 1e-8]),

            # Geometric progression check
            (_check_geometric_progression, [[1.0, 2.0, 4.0, 8.0], 0.1, 1e-8]),
        ]

        for func, args in test_cases:
            try:
                result = func(*args)
                # Function should succeed without errors
                assert result is not None or isinstance(result, tuple)
            except Exception as e:
                pytest.fail(f"Backward compatibility broken for {func.__name__}: {e}")

    def test_mixed_numpy_list_compatibility(self):
        """Test that functions accept both numpy arrays and Python lists."""
        list_input = [1.0, 2.0, 3.0, 4.0]
        numpy_input = np.array([1.0, 2.0, 3.0, 4.0])

        # Both should work
        result1 = _calculate_pattern_quality_score_optimized(list_input, "arithmetic")
        result2 = _calculate_pattern_quality_score_optimized(numpy_input, "arithmetic")

        assert isinstance(result1, float)
        assert isinstance(result2, float)
        # Results should be very close
        assert abs(result1 - result2) < 1e-10

    def test_edge_case_valid_inputs(self):
        """Test edge cases that should still be valid."""
        edge_cases = [
            # Single element arrays
            ([1.0], "single_element"),

            # Very small differences
            ([1.0, 1.0000001, 1.0000002], "small_differences"),

            # Very large numbers (but not too large)
            ([1e6, 1e6 + 1, 1e6 + 2], "large_numbers"),

            # Very small numbers (but not too small)
            ([1e-6, 2e-6, 3e-6], "small_numbers"),
        ]

        for array, description in edge_cases:
            try:
                result = _calculate_pattern_quality_score_optimized(array, "arithmetic")
                assert isinstance(result, float)
                assert 0.1 <= result <= 1.0  # Valid range for pattern quality
            except Exception as e:
                pytest.fail(f"Edge case {description} failed: {e}")


class TestPerformanceImpact:
    """Test that type validation doesn't significantly impact performance."""

    def test_validation_performance_overhead(self):
        """Test that validation doesn't add excessive overhead."""
        import time

        # Test with a reasonably sized array
        large_array = list(range(1000))  # 1000 elements

        # Time with validation (should be our implementation)
        start_time = time.time()
        for _ in range(100):  # 100 iterations
            _calculate_pattern_quality_score_optimized(large_array, "arithmetic")
        validation_time = time.time() - start_time

        # The validation should not add excessive overhead
        # This is a rough check - adjust threshold as needed
        assert validation_time < 5.0, f"Validation too slow: {validation_time}s for 100 iterations"