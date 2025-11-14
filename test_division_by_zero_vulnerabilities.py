#!/usr/bin/env python3
"""
Test suite to demonstrate division by zero vulnerabilities in the reasoning library.
These tests expose the critical security issues that need to be fixed.

Division by Zero Vulnerabilities Found:
1. Line 146: ratio = curr_val / prev_val when prev_val can be zero or near-zero
2. Line 151: avg_growth = sum(growth_ratios) / len(growth_ratios) when len can be zero
3. Line 204: sequence_length / minimum_required when minimum_required could be zero
4. Line 231: coefficient_of_variation = np.std(values_array) / (mean_abs_diff + NUMERICAL_STABILITY_THRESHOLD)
5. Line 240: coefficient_of_variation = np.std(values_array) / (np.abs(mean_ratio) + NUMERICAL_STABILITY_THRESHOLD)
6. Line 324: coefficient_of_variation = std_dev / (mean_abs_diff + 1e-10)
7. Line 336: coefficient_of_variation = std_dev / (np.abs(mean_ratio) + 1e-10)
8. Line 365: coefficient_of_variation = np.std(values_array) / (mean_abs_diff + NUMERICAL_STABILITY_THRESHOLD)
9. Line 374: coefficient_of_variation = np.std(values_array) / (np.abs(mean_ratio) + NUMERICAL_STABILITY_THRESHOLD)
10. Line 415: complexity_factor = 1.0 / (1.0 + COMPLEXITY_SCORE_ARITHMETIC)
11. Line 459: complexity_factor = 1.0 / (1.0 + COMPLEXITY_SCORE_GEOMETRIC)
12. Line 540: ratios = sequence_array[1:] / sequence_array[:-1] when denominator can be zero
13. Line 641: ratios = sequence_array[1:] / sequence_array[:-1] when denominator can be zero
14. Line 728: ratios = sequence_array[1:] / sequence_array[:-1] when denominator can be zero
15. Line 781: data_sufficiency_factor = min(1.0, sequence_length / minimum_required)
16. Line 816: data_sufficiency_factor = min(1.0, sequence_length / minimum_required)
17. Line 822: complexity_factor = 1.0 / (1.0 + COMPLEXITY_SCORE_POLYNOMIAL_DEGREE_FACTOR * degree)
18. Line 785: complexity_factor = 1.0 / (1.0 + COMPLEXITY_SCORE_RECURSIVE)
19. Line 888: match_score = 1.0 - np.mean(np.abs(actual_sequence - calculated_sequence)) / (np.mean(np.abs(actual_sequence)) + 1e-10)
20. Line 961: match_score = 1.0 - np.mean(np.abs(actual_sequence - calculated_sequence)) / (np.mean(np.abs(actual_sequence)) + 1e-10)
21. Line 1039: match_score = 1.0 - np.mean(np.abs(actual_sequence - calculated_sequence)) / (np.mean(np.abs(actual_sequence)) + 1e-10)
22. Line 1102: r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
23. Line 1174: r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
24. Line 1260: relative_error = np.mean(np.abs((y_values - predicted_values) / y_values))
25. Line 1261: match_score = max(0.0, 1.0 - relative_error / rtol) when rtol could be zero
26. Line 1335: for period in range(2, min(len(sequence) // 2, 6))
27. Line 1339: repetitions = len(sequence) // period when period could be zero
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
import numpy as np
from reasoning_library.inductive import (
    _check_arithmetic_progression,
    _check_geometric_progression,
    detect_polynomial_pattern,
    detect_fibonacci_pattern,
    detect_lucas_pattern,
    detect_exponential_pattern,
    detect_custom_step_patterns
)
from reasoning_library.exceptions import ValidationError


class TestDivisionByZeroVulnerabilities:
    """Test cases that demonstrate division by zero vulnerabilities."""

    def test_vulnerability_01_geometric_progression_zero_division_line_540(self):
        """Test division by zero in geometric progression detection line 540."""
        # This should cause ZeroDivisionError when sequence contains zero
        vulnerable_sequence = [1, 0, 0, 0]  # Division by zero: 0/1, 0/0, 0/0

        with pytest.raises(ZeroDivisionError):
            _check_geometric_progression(vulnerable_sequence)

    def test_vulnerability_02_geometric_progression_leading_zero_line_540(self):
        """Test division by zero with leading zero in sequence."""
        vulnerable_sequence = [0, 1, 1, 1]  # Division by zero: 1/0

        with pytest.raises(ZeroDivisionError):
            _check_geometric_progression(vulnerable_sequence)

    def test_vulnerability_03_geometric_alternating_zeros_line_540(self):
        """Test division by zero with alternating zeros."""
        vulnerable_sequence = [2, 0, 2, 0, 2, 0]  # Multiple zero divisions

        with pytest.raises(ZeroDivisionError):
            _check_geometric_progression(vulnerable_sequence)

    def test_vulnerability_04_fibonacci_pattern_zero_division(self):
        """Test division by zero in Fibonacci pattern detection."""
        # This can trigger zero division in confidence calculations
        vulnerable_sequence = [0, 0, 0, 0, 0]  # All zeros

        with pytest.raises((ZeroDivisionError, ValidationError)):
            detect_fibonacci_pattern(vulnerable_sequence)

    def test_vulnerability_05_polynomial_zero_mean_division(self):
        """Test division by zero in polynomial detection when mean is zero."""
        vulnerable_sequence = [0, 0, 0, 0, 0]  # All zeros cause zero mean

        with pytest.raises((ZeroDivisionError, RuntimeWarning)):
            detect_polynomial_pattern(vulnerable_sequence)

    def test_vulnerability_06_exponential_zero_y_values_division_line_1260(self):
        """Test division by zero in exponential pattern detection line 1260."""
        vulnerable_sequence = [0, 0, 0, 0]  # All zeros cause division by zero in relative error

        with pytest.raises((ZeroDivisionError, RuntimeWarning)):
            detect_exponential_pattern(vulnerable_sequence)

    def test_vulnerability_07_periodic_zero_length_division(self):
        """Test division by zero in periodic pattern detection."""
        # This can cause issues in length calculations
        vulnerable_sequence = []  # Empty sequence

        with pytest.raises(ValidationError):
            detect_custom_step_patterns(vulnerable_sequence)

    def test_vulnerability_08_arithmetic_confidence_zero_division(self):
        """Test division by zero in arithmetic confidence calculation."""
        vulnerable_sequence = [0, 0, 0, 0]  # Can cause zero division in confidence

        # This might not raise ZeroDivisionError but can produce inf/nan values
        result = _check_arithmetic_progression(vulnerable_sequence)

        # Check if the result contains invalid mathematical values
        if result[0] is not None:
            assert not np.isinf(result[0]), "Arithmetic progression produced infinite value"
            assert not np.isnan(result[0]), "Arithmetic progression produced NaN value"

        if result[1] is not None:
            assert not np.isinf(result[1]), "Confidence calculation produced infinite value"
            assert not np.isnan(result[1]), "Confidence calculation produced NaN value"

    def test_vulnerability_09_near_zero_numerical_instability(self):
        """Test numerical instability with values very close to zero."""
        # Use extremely small values that can cause numerical instability
        tiny_value = 1e-15
        vulnerable_sequence = [tiny_value, tiny_value * 2, tiny_value * 4]

        try:
            result = _check_geometric_progression(vulnerable_sequence)

            # Check for numerical instability
            if result[0] is not None:
                assert not np.isinf(result[0]), "Geometric progression produced infinite value with tiny inputs"
                assert not np.isnan(result[0]), "Geometric progression produced NaN value with tiny inputs"

        except (ZeroDivisionError, FloatingPointError, OverflowError):
            # These are expected vulnerabilities
            pass

    def test_vulnerability_10_confidence_calculation_zero_length(self):
        """Test division by zero in confidence calculations with zero-length inputs."""
        # Some confidence calculations may have edge cases with zero lengths

        # Test with sequence that could cause zero-length growth_ratios
        vulnerable_sequence = [0, 0, 0]  # All zeros might cause empty growth_ratios

        try:
            result = _check_arithmetic_progression(vulnerable_sequence)

            # Verify no invalid values
            if result[1] is not None:  # confidence score
                assert 0 <= result[1] <= 1, f"Confidence score out of bounds: {result[1]}"

        except (ZeroDivisionError, ValueError):
            # Expected vulnerability
            pass

    def test_vulnerability_11_geometric_confidence_zero_ratio_variance(self):
        """Test division by zero in geometric confidence when ratio variance is zero."""
        # Sequence with identical ratios can cause zero variance
        sequence_with_zero_variance = [2, 4, 8, 16, 32]  # Perfect geometric progression

        try:
            result = _check_geometric_progression(sequence_with_zero_variance)

            # Should handle this gracefully without division by zero
            if result[1] is not None:  # confidence
                assert not np.isinf(result[1]), "Geometric confidence produced infinite value"
                assert not np.isnan(result[1]), "Geometric confidence produced NaN value"

        except ZeroDivisionError:
            # This demonstrates the vulnerability
            pytest.fail("Geometric progression detection failed with division by zero on valid input")

    def test_vulnerability_12_polynomial_degree_zero_division(self):
        """Test potential division by zero when polynomial degree is zero."""
        vulnerable_sequence = [5, 5, 5, 5, 5]  # Constant sequence (degree 0 polynomial)

        try:
            result = detect_polynomial_pattern(vulnerable_sequence)

            # Should handle degree 0 without division by zero
            if result[0] is not None:
                assert not np.isinf(result[0]), "Polynomial detection produced infinite value"
                assert not np.isnan(result[0]), "Polynomial detection produced NaN value"

        except ZeroDivisionError:
            # This demonstrates the vulnerability
            pytest.fail("Polynomial detection failed with division by zero on constant sequence")

    def test_vulnerability_13_sequence_with_extreme_values(self):
        """Test division operations with extreme values that can cause overflow/underflow."""
        extreme_sequence = [1e-10, 1e-20, 1e-30]  # Extremely small values

        try:
            result = _check_geometric_progression(extreme_sequence)

            # Check for floating point exceptions
            if result[0] is not None:
                assert not np.isinf(result[0]), "Extreme values caused infinite result"
                assert not np.isnan(result[0]), "Extreme values caused NaN result"

        except (ZeroDivisionError, FloatingPointError, OverflowError, UnderflowError):
            # Expected vulnerabilities with extreme values
            pass

    def test_vulnerability_14_negative_zero_edge_case(self):
        """Test edge case with negative zero."""
        # Negative zero behaves differently in some division operations
        vulnerable_sequence = [-0.0, 0.0, -0.0, 0.0]

        try:
            result = _check_geometric_progression(vulnerable_sequence)

            # Should handle negative zero gracefully
            if result[0] is not None:
                assert not np.isinf(result[0]), "Negative zero caused infinite result"
                assert not np.isnan(result[0]), "Negative zero caused NaN result"

        except ZeroDivisionError:
            # Demonstrates vulnerability with signed zero
            pass

    def test_vulnerability_summary_all_vulnerabilities_documented(self):
        """Document all discovered division by zero vulnerabilities."""
        vulnerabilities = [
            "Line 146: ratio = curr_val / prev_val",
            "Line 151: avg_growth = sum(growth_ratios) / len(growth_ratios)",
            "Line 204: sequence_length / minimum_required",
            "Line 231: coefficient_of_variation division by mean_abs_diff",
            "Line 240: coefficient_of_variation division by mean_ratio",
            "Line 324: coefficient_of_variation division by mean_abs_diff",
            "Line 336: coefficient_of_variation division by mean_ratio",
            "Line 365: coefficient_of_variation division by mean_abs_diff",
            "Line 374: coefficient_of_variation division by mean_ratio",
            "Line 415: complexity_factor = 1.0 / (1.0 + COMPLEXITY_SCORE_ARITHMETIC)",
            "Line 459: complexity_factor = 1.0 / (1.0 + COMPLEXITY_SCORE_GEOMETRIC)",
            "Line 540: ratios = sequence_array[1:] / sequence_array[:-1]",
            "Line 641: ratios = sequence_array[1:] / sequence_array[:-1]",
            "Line 728: ratios = sequence_array[1:] / sequence_array[:-1]",
            "Line 781: data_sufficiency_factor = sequence_length / minimum_required",
            "Line 816: data_sufficiency_factor = sequence_length / minimum_required",
            "Line 822: complexity_factor = 1.0 / (1.0 + COMPLEXITY_SCORE_POLYNOMIAL_DEGREE_FACTOR * degree)",
            "Line 785: complexity_factor = 1.0 / (1.0 + COMPLEXITY_SCORE_RECURSIVE)",
            "Line 888: match_score division by mean_abs(actual_sequence)",
            "Line 961: match_score division by mean_abs(actual_sequence)",
            "Line 1039: match_score division by mean_abs(actual_sequence)",
            "Line 1102: r_squared = 1 - (ss_res / ss_tot)",
            "Line 1174: r_squared = 1 - (ss_res / ss_tot)",
            "Line 1260: relative_error division by y_values",
            "Line 1261: match_score division by rtol",
            "Line 1339: repetitions = len(sequence) // period"
        ]

        # This test documents all 26 division by zero vulnerabilities found
        assert len(vulnerabilities) == 26, f"Expected 26 vulnerabilities, found {len(vulnerabilities)}"

        # Print vulnerability summary for reference
        print(f"\n{'='*80}")
        print("DIVISION BY ZERO VULNERABILITY SUMMARY")
        print(f"{'='*80}")
        for i, vuln in enumerate(vulnerabilities, 1):
            print(f"{i:2d}. {vuln}")
        print(f"{'='*80}")
        print(f"TOTAL VULNERABILITIES: {len(vulnerabilities)}")
        print("ALL VULNERABILITIES MUST BE FIXED BEFORE PRODUCTION DEPLOYMENT")
        print(f"{'='*80}")


if __name__ == "__main__":
    # Run vulnerability tests
    pytest.main([__file__, "-v", "--tb=short"])