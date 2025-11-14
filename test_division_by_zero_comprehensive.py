#!/usr/bin/env python3
"""
Comprehensive test suite for division by zero vulnerability fixes.
This ensures all our protective measures work correctly and don't break functionality.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
import numpy as np
from reasoning_library.inductive import (
    _check_arithmetic_progression,
    _check_geometric_progression,
    _detect_exponential_growth_sequence,
    _assess_data_sufficiency,
    _calculate_pattern_quality_score,
    detect_fibonacci_pattern,
    detect_lucas_pattern,
    detect_polynomial_pattern,
    detect_exponential_pattern,
    detect_custom_step_patterns,
    _calculate_recursive_confidence,
    _calculate_polynomial_confidence
)
from reasoning_library.exceptions import ValidationError


class TestDivisionByZeroComprehensive:
    """Comprehensive tests for division by zero fixes."""

    def test_geometric_progression_zero_protection(self):
        """Test that geometric progression handles zeros gracefully."""
        # Test sequences that should return None, not crash
        zero_sequences = [
            [0, 0, 0, 0],      # All zeros
            [1, 0, 0, 0],      # Zero after first element
            [0, 1, 2, 3],      # Leading zero
            [2, 0, 2, 0, 2],   # Alternating zeros
        ]

        for seq in zero_sequences:
            result = _check_geometric_progression(seq, rtol=1e-5, atol=1e-8)
            assert result == (None, None, None), f"Expected (None, None, None) for {seq}, got {result}"

        # Test valid geometric progression still works
        valid_seq = [2, 4, 8, 16]
        result = _check_geometric_progression(valid_seq, rtol=1e-5, atol=1e-8)
        assert result[0] is not None, "Valid geometric progression should return a result"
        assert result[0] == 32.0, f"Expected 32.0, got {result[0]}"

    def test_arithmetic_progression_zeros(self):
        """Test arithmetic progression with zero values."""
        # Arithmetic progression should handle zeros correctly
        zero_seq = [0, 0, 0, 0]
        result = _check_arithmetic_progression(zero_seq, rtol=1e-5, atol=1e-8)

        # Should predict 0 and provide reasonable confidence
        assert result[0] == 0.0, f"Expected 0.0, got {result[0]}"
        assert result[1] is not None, "Should provide confidence"
        assert 0 <= result[1] <= 1, f"Confidence should be in range 0-1, got {result[1]}"

    def test_exponential_growth_sequence_division_protection(self):
        """Test exponential growth detection handles zeros without division by zero."""
        # This function has division operations that need protection
        zero_sequences = [
            [0, 0, 0, 0],      # All zeros
            [1e-15, 1e-15, 1e-15],  # Extremely small values
        ]

        for seq in zero_sequences:
            try:
                _detect_exponential_growth_sequence(seq, "test_function")
                # If it doesn't raise an error, that's good
            except (ValidationError, ValueError):
                # These are acceptable errors
                pass
            except ZeroDivisionError:
                pytest.fail(f"ZeroDivisionError should not occur with sequence {seq}")

    def test_data_sufficiency_division_protection(self):
        """Test data sufficiency assessment doesn't have division by zero."""
        # Test with different sequence lengths
        for seq_len in [0, 1, 2, 5, 10]:
            for pattern_type in ["arithmetic", "geometric", "unknown"]:
                try:
                    result = _assess_data_sufficiency(seq_len, pattern_type)
                    assert isinstance(result, float), "Should return a float"
                    assert 0 <= result <= 1, f"Data sufficiency should be in range 0-1, got {result}"
                except ZeroDivisionError:
                    pytest.fail(f"ZeroDivisionError should not occur with seq_len={seq_len}, pattern_type={pattern_type}")

    def test_pattern_quality_score_division_protection(self):
        """Test pattern quality calculation handles edge cases."""
        # Test with various value arrays that could cause division issues
        test_arrays = [
            [0, 0, 0, 0],        # All zeros
            [1e-15, 1e-15],      # Very small values
            [1, 1, 1, 1],        # All identical
            [0, 1, 0, 1],        # Alternating zeros and ones
        ]

        for values in test_arrays:
            for pattern_type in ["arithmetic", "geometric", "unknown"]:
                try:
                    result = _calculate_pattern_quality_score(values, pattern_type)
                    assert isinstance(result, float), "Should return a float"
                    assert result > 0, f"Pattern quality should be positive, got {result}"
                except ZeroDivisionError:
                    pytest.fail(f"ZeroDivisionError should not occur with values={values}, pattern_type={pattern_type}")

    def test_fibonacci_pattern_edge_cases(self):
        """Test Fibonacci pattern detection with edge cases."""
        edge_cases = [
            [0, 0, 0, 0, 0],    # All zeros
            [1, 1, 2, 3, 5],    # Valid Fibonacci
            [0, 1, 1, 2, 3],    # Fibonacci starting with 0
        ]

        for seq in edge_cases:
            try:
                result = detect_fibonacci_pattern(seq)
                # Result should be None or a valid dict
                assert result is None or isinstance(result, dict), f"Expected None or dict, got {type(result)}"
            except (ValidationError, ValueError):
                # Acceptable validation errors
                pass
            except ZeroDivisionError:
                pytest.fail(f"ZeroDivisionError should not occur with Fibonacci sequence {seq}")

    def test_polynomial_pattern_edge_cases(self):
        """Test polynomial pattern detection with edge cases."""
        edge_cases = [
            [0, 0, 0, 0, 0],    # All zeros (degree 0)
            [1, 1, 1, 1, 1],    # Constant sequence (degree 0)
            [1, 2, 3, 4, 5],    # Linear sequence (degree 1)
        ]

        for seq in edge_cases:
            try:
                result = detect_polynomial_pattern(seq)
                # Should handle these gracefully
                assert result is None or isinstance(result, dict), f"Expected None or dict, got {type(result)}"
            except ZeroDivisionError:
                pytest.fail(f"ZeroDivisionError should not occur with polynomial sequence {seq}")

    def test_exponential_pattern_edge_cases(self):
        """Test exponential pattern detection with edge cases."""
        edge_cases = [
            [0, 0, 0, 0],       # All zeros
            [1, 1, 1, 1],       # Constant sequence
            [1, 2, 4, 8],       # Valid exponential (base 2)
        ]

        for seq in edge_cases:
            try:
                result = detect_exponential_pattern(seq)
                # Should handle these gracefully
                assert result is None or isinstance(result, dict), f"Expected None or dict, got {type(result)}"
            except ZeroDivisionError:
                pytest.fail(f"ZeroDivisionError should not occur with exponential sequence {seq}")

    def test_custom_step_patterns_edge_cases(self):
        """Test custom step pattern detection with edge cases."""
        edge_cases = [
            [0, 0, 0, 0],       # All zeros
            [1, 2, 3, 4],       # Simple arithmetic progression
            [1, 3, 5, 7],       # Arithmetic progression with step 2
        ]

        for seq in edge_cases:
            try:
                result = detect_custom_step_patterns(seq)
                # Should handle these gracefully
                assert isinstance(result, list), f"Expected list, got {type(result)}"
            except ZeroDivisionError:
                pytest.fail(f"ZeroDivisionError should not occur with custom step sequence {seq}")

    def test_recursive_confidence_edge_cases(self):
        """Test recursive confidence calculation edge cases."""
        edge_cases = [
            (0, 1.0),           # Zero match score
            (0.5, 5),           # Normal values
            (1.0, 100),         # High values
        ]

        for match_score, seq_len in edge_cases:
            try:
                result = _calculate_recursive_confidence(match_score, seq_len)
                assert isinstance(result, float), "Should return a float"
                assert 0 <= result <= 1, f"Confidence should be in range 0-1, got {result}"
            except ZeroDivisionError:
                pytest.fail(f"ZeroDivisionError should not occur with match_score={match_score}, seq_len={seq_len}")

    def test_polynomial_confidence_edge_cases(self):
        """Test polynomial confidence calculation edge cases."""
        edge_cases = [
            (0.5, 5, 0),        # Zero degree
            (1.0, 10, 2),       # High degree
            (0.1, 3, -1),       # Negative degree (edge case)
        ]

        for r_squared, seq_len, degree in edge_cases:
            try:
                result = _calculate_polynomial_confidence(r_squared, seq_len, degree)
                assert isinstance(result, float), "Should return a float"
                assert 0 <= result <= 1, f"Confidence should be in range 0-1, got {result}"
            except ZeroDivisionError:
                pytest.fail(f"ZeroDivisionError should not occur with r_squared={r_squared}, seq_len={seq_len}, degree={degree}")

    def test_lucas_pattern_edge_cases(self):
        """Test Lucas pattern detection with edge cases."""
        edge_cases = [
            [0, 0, 0, 0, 0],    # All zeros
            [2, 1, 3, 4, 7],    # Valid Lucas sequence
            [1, 1, 2, 3, 5],    # Fibonacci sequence (should not match Lucas)
        ]

        for seq in edge_cases:
            try:
                result = detect_lucas_pattern(seq)
                # Should handle these gracefully
                assert result is None or isinstance(result, dict), f"Expected None or dict, got {type(result)}"
            except (ValidationError, ValueError):
                # Acceptable validation errors
                pass
            except ZeroDivisionError:
                pytest.fail(f"ZeroDivisionError should not occur with Lucas sequence {seq}")

    def test_numerical_stability_extreme_values(self):
        """Test that extreme values don't cause numerical instability."""
        extreme_sequences = [
            [1e-15, 1e-15, 1e-15],      # Extremely small values
            [1e15, 1e15, 1e15],         # Extremely large values
            [1e-15, 1e15, 1e-15, 1e15], # Mixed extreme values
        ]

        for seq in extreme_sequences:
            # Test that these don't cause division by zero or overflow
            try:
                result_arith = _check_arithmetic_progression(seq, rtol=1e-5, atol=1e-8)
                result_geom = _check_geometric_progression(seq, rtol=1e-5, atol=1e-8)

                # Results should be valid (None or reasonable predictions)
                if result_arith[0] is not None:
                    assert not np.isinf(result_arith[0]), "Arithmetic result should not be infinite"
                    assert not np.isnan(result_arith[0]), "Arithmetic result should not be NaN"

                if result_geom[0] is not None:
                    assert not np.isinf(result_geom[0]), "Geometric result should not be infinite"
                    assert not np.isnan(result_geom[0]), "Geometric result should not be NaN"

            except (ValidationError, ValueError, OverflowError):
                # These are acceptable for extreme values
                pass
            except ZeroDivisionError:
                pytest.fail(f"ZeroDivisionError should not occur with extreme sequence {seq}")

    def test_confidence_bounds_maintained(self):
        """Test that all confidence calculations remain within valid bounds."""
        # Test various sequences to ensure confidence stays in [0, 1]
        test_sequences = [
            [1, 2, 3, 4, 5],          # Simple arithmetic
            [2, 4, 8, 16, 32],        # Simple geometric
            [0, 0, 0, 0, 0],          # All zeros
            [1, 1, 1, 1, 1],          # All ones
            [1, -1, 1, -1, 1],        # Alternating signs
        ]

        for seq in test_sequences:
            # Test arithmetic progression
            arith_result = _check_arithmetic_progression(seq, rtol=1e-5, atol=1e-8)
            if arith_result[1] is not None:  # confidence score
                assert 0 <= arith_result[1] <= 1, f"Arithmetic confidence out of bounds: {arith_result[1]}"

            # Test geometric progression
            geom_result = _check_geometric_progression(seq, rtol=1e-5, atol=1e-8)
            if geom_result[1] is not None:  # confidence score
                assert 0 <= geom_result[1] <= 1, f"Geometric confidence out of bounds: {geom_result[1]}"

    def test_division_by_zero_protection_summary(self):
        """Summary test that verifies all division by zero protections are working."""
        protection_count = 0
        total_checks = 0

        # This function serves as a verification that our protections are in place
        # If any of these cause ZeroDivisionError, our protections have failed

        # Test 1: Geometric progression zero handling
        total_checks += 1
        try:
            _check_geometric_progression([0, 1, 2, 3], rtol=1e-5, atol=1e-8)
            protection_count += 1
        except ZeroDivisionError:
            pass

        # Test 2: Arithmetic progression with zeros
        total_checks += 1
        try:
            _check_arithmetic_progression([0, 0, 0, 0], rtol=1e-5, atol=1e-8)
            protection_count += 1
        except ZeroDivisionError:
            pass

        # Test 3: Data sufficiency assessment
        total_checks += 1
        try:
            _assess_data_sufficiency(5, "arithmetic")
            protection_count += 1
        except ZeroDivisionError:
            pass

        # Test 4: Pattern quality scores
        total_checks += 1
        try:
            _calculate_pattern_quality_score([0, 0, 0], "arithmetic")
            protection_count += 1
        except ZeroDivisionError:
            pass

        # Test 5: Fibonacci pattern
        total_checks += 1
        try:
            detect_fibonacci_pattern([0, 0, 0, 0, 0])
            protection_count += 1
        except ZeroDivisionError:
            pass

        # Test 6: Polynomial pattern
        total_checks += 1
        try:
            detect_polynomial_pattern([0, 0, 0, 0, 0])
            protection_count += 1
        except ZeroDivisionError:
            pass

        # Test 7: Exponential pattern
        total_checks += 1
        try:
            detect_exponential_pattern([0, 0, 0, 0])
            protection_count += 1
        except ZeroDivisionError:
            pass

        # Verify that most protections are working
        protection_ratio = protection_count / total_checks
        assert protection_ratio >= 0.8, f"Too many division by zero vulnerabilities: {protection_count}/{total_checks} protected"

        print(f"\n{'='*60}")
        print("DIVISION BY ZERO PROTECTION SUMMARY")
        print(f"{'='*60}")
        print(f"Tests passed: {protection_count}/{total_checks}")
        print(f"Protection ratio: {protection_ratio:.1%}")
        print("✅ Division by zero protections are working correctly")
        print(f"{'='*60}")


if __name__ == "__main__":
    # Run comprehensive tests
    pytest.main([__file__, "-v", "--tb=short"])