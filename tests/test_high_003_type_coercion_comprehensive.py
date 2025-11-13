"""
Additional comprehensive tests for HIGH-003 type coercion vulnerability.

These tests ensure comprehensive coverage of edge cases for type coercion
vulnerabilities in abductive.py confidence validation around line 912.
"""

import pytest
import math
from reasoning_library.abductive import rank_hypotheses, _validate_confidence_value
from reasoning_library.core import ReasoningChain
from reasoning_library.exceptions import ValidationError


class TestHigh003TypeCoercionComprehensive:
    """Comprehensive tests for HIGH-003 type coercion vulnerability."""

    def test_edge_case_numeric_types(self):
        """Test edge cases with numeric types that should work."""
        reasoning_chain = ReasoningChain()

        # Test various numeric types that should be valid
        valid_test_cases = [
            (0, "Zero integer"),
            (1, "One integer"),
            (-1, "Negative integer"),
            (0.0, "Zero float"),
            (1.0, "One float"),
            (-1.0, "Negative float"),
            (0.5, "Positive float"),
            (0.999999, "Close to one float"),
            (1e-10, "Very small float"),
            (1e10, "Very large float"),
        ]

        for confidence, description in valid_test_cases:
            hypotheses = [{
                "hypothesis": f"Test hypothesis - {description}",
                "confidence": confidence
            }]

            # This should not raise an error
            result = rank_hypotheses(hypotheses, ["test evidence"], reasoning_chain)

            # Verify the result
            assert len(result) == 1
            assert isinstance(result[0]["confidence"], (int, float))
            assert 0.0 <= result[0]["confidence"] <= 1.0

    def test_problematic_numeric_types(self):
        """Test numeric types that should be handled carefully."""
        reasoning_chain = ReasoningChain()

        problematic_test_cases = [
            (math.nan, "NaN"),
            (float('inf'), "infinite"),
            (float('-inf'), "infinite"),
        ]

        for confidence, description in problematic_test_cases:
            with pytest.raises(ValidationError, match=description):
                _validate_confidence_value(confidence)

    def test_string_like_numeric_types(self):
        """Test string representations of numbers that should fail."""
        reasoning_chain = ReasoningChain()

        string_numeric_cases = [
            "0.5",
            "1",
            "0",
            "0.0",
            "1.0",
            "2.5",
            "-1.0",
            "1e-10",
            "1e10",
            "inf",
            "nan",
        ]

        for confidence_str in string_numeric_cases:
            hypotheses = [{
                "hypothesis": f"Test hypothesis with string confidence '{confidence_str}'",
                "confidence": confidence_str
            }]

            # All string types should raise ValidationError
            with pytest.raises(ValidationError):
                rank_hypotheses(hypotheses, ["test evidence"], reasoning_chain)

    def test_complex_object_types(self):
        """Test complex object types that should fail validation."""
        reasoning_chain = ReasoningChain()

        object_test_cases = [
            ([0.5], "List containing number"),
            ({"confidence": 0.5}, "Dict with confidence key"),
            (set([0.5]), "Set containing number"),
            (lambda x: 0.5, "Lambda function"),
            (type('Custom', (), {'confidence': 0.5}), "Custom class instance"),
        ]

        for confidence, description in object_test_cases:
            hypotheses = [{
                "hypothesis": f"Test hypothesis - {description}",
                "confidence": confidence
            }]

            # All non-numeric types should raise ValidationError
            with pytest.raises(ValidationError):
                rank_hypotheses(hypotheses, ["test evidence"], reasoning_chain)

    def test_boolean_confidence_values(self):
        """Test boolean values which are technically ints in Python."""
        reasoning_chain = ReasoningChain()

        # In Python, bool is a subclass of int
        # True = 1, False = 0
        boolean_test_cases = [
            (True, "True boolean"),
            (False, "False boolean"),
        ]

        for confidence, description in boolean_test_cases:
            hypotheses = [{
                "hypothesis": f"Test hypothesis - {description}",
                "confidence": confidence
            }]

            # Booleans should be accepted as they are numeric
            result = rank_hypotheses(hypotheses, ["test evidence"], reasoning_chain)
            assert len(result) == 1
            assert isinstance(result[0]["confidence"], (int, float))
            assert 0.0 <= result[0]["confidence"] <= 1.0

    def test_mixed_hypotheses_batch_validation(self):
        """Test that batch validation catches any invalid confidence in a batch."""
        reasoning_chain = ReasoningChain()

        # Create a batch with mostly valid but one invalid confidence
        hypotheses = [
            {"hypothesis": "Valid hypothesis 1", "confidence": 0.7},
            {"hypothesis": "Valid hypothesis 2", "confidence": 0.3},
            {"hypothesis": "Invalid hypothesis", "confidence": "invalid_string"},
            {"hypothesis": "Valid hypothesis 3", "confidence": 0.5},
        ]

        # Should fail due to the invalid string confidence
        with pytest.raises(ValidationError, match="invalid_string"):
            rank_hypotheses(hypotheses, ["test evidence"], reasoning_chain)

    def test_arithmetic_operation_safety(self):
        """Test that arithmetic operations on validated confidence are safe."""
        reasoning_chain = ReasoningChain()

        # Test with various evidence patterns to ensure arithmetic is safe
        test_cases = [
            ([], "No evidence"),
            (["matching evidence"], "Matching evidence"),
            (["evidence"] * 10, "Large evidence set"),
            (["non", "matching", "evidence"], "Non-matching evidence"),
        ]

        for evidence_list, description in test_cases:
            hypotheses = [{
                "hypothesis": f"Test hypothesis - {description}",
                "confidence": 0.5
            }]

            # This should not raise any TypeError or other arithmetic errors
            result = rank_hypotheses(hypotheses, evidence_list, reasoning_chain)

            assert len(result) == 1
            assert isinstance(result[0]["confidence"], (int, float))
            assert not math.isnan(result[0]["confidence"])
            assert not math.isinf(result[0]["confidence"])
            assert 0.0 <= result[0]["confidence"] <= 1.0

    def test_confidence_clamping_behavior(self):
        """Test that confidence values are properly clamped to [0.0, 1.0] range."""
        reasoning_chain = ReasoningChain()

        # Test extreme values that should be clamped
        extreme_test_cases = [
            (-1000, "Large negative"),
            (-1e50, "Very large negative float"),
            (1000, "Large positive"),
            (1e50, "Very large positive float"),
        ]

        for confidence, description in extreme_test_cases:
            hypotheses = [{
                "hypothesis": f"Test hypothesis - {description}",
                "confidence": confidence
            }]

            result = rank_hypotheses(hypotheses, ["test evidence"], reasoning_chain)

            # Should be clamped to valid range
            assert len(result) == 1
            assert 0.0 <= result[0]["confidence"] <= 1.0

            # Extreme values should be clamped to bounds
            if confidence < 0:
                assert result[0]["confidence"] == 0.0
            elif confidence > 1:
                assert result[0]["confidence"] == 1.0

    def test_missing_confidence_key(self):
        """Test handling of missing confidence key in hypothesis."""
        reasoning_chain = ReasoningChain()

        # Create hypothesis without confidence key
        hypotheses = [{
            "hypothesis": "Hypothesis without confidence key"
            # Missing "confidence" key
        }]

        # Should handle gracefully (get() returns None, which should raise ValidationError)
        with pytest.raises(ValidationError):
            rank_hypotheses(hypotheses, ["test evidence"], reasoning_chain)