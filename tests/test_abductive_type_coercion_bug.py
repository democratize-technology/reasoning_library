"""
Test file specifically for the type coercion vulnerability in rank_hypotheses function.
This test demonstrates the bug where non-numeric confidence values cause issues.
"""

import pytest
from reasoning_library.abductive import rank_hypotheses
from reasoning_library.core import ReasoningChain
from reasoning_library.exceptions import ValidationError


class TestTypeCoercionBug:
    """Test cases for type coercion vulnerability in confidence calculations."""

    def test_string_confidence_value_should_fail_gracefully(self):
        """Test that string confidence values are handled properly."""
        # Create hypotheses with string confidence (the bug)
        hypotheses = [
            {
                "hypothesis": "The server is overloaded",
                "confidence": "high"  # String instead of number
            }
        ]
        new_evidence = ["Server CPU at 95%"]
        reasoning_chain = ReasoningChain()

        # This should raise a ValidationError with improved error handling
        with pytest.raises(ValidationError):
            rank_hypotheses(hypotheses, new_evidence, reasoning_chain)

    def test_none_confidence_value_should_fail_gracefully(self):
        """Test that None confidence values are handled properly."""
        hypotheses = [
            {
                "hypothesis": "Database connection failed",
                "confidence": None  # None instead of number
            }
        ]
        new_evidence = ["Database connection timeout"]
        reasoning_chain = ReasoningChain()

        # This should raise a ValidationError with improved error handling
        with pytest.raises(ValidationError):
            rank_hypotheses(hypotheses, new_evidence, reasoning_chain)

    def test_dict_confidence_value_should_fail_gracefully(self):
        """Test that dict confidence values are handled properly."""
        hypotheses = [
            {
                "hypothesis": "Network issue detected",
                "confidence": {"level": "medium"}  # Dict instead of number
            }
        ]
        new_evidence = ["Network latency increased"]
        reasoning_chain = ReasoningChain()

        # This should raise a ValidationError with improved error handling
        with pytest.raises(ValidationError):
            rank_hypotheses(hypotheses, new_evidence, reasoning_chain)

    def test_list_confidence_value_should_fail_gracefully(self):
        """Test that list confidence values are handled properly."""
        hypotheses = [
            {
                "hypothesis": "Memory leak detected",
                "confidence": [0.5, 0.7]  # List instead of number
            }
        ]
        new_evidence = ["Memory usage steadily increasing"]
        reasoning_chain = ReasoningChain()

        # This should raise a ValidationError with improved error handling
        with pytest.raises(ValidationError):
            rank_hypotheses(hypotheses, new_evidence, reasoning_chain)

    def test_negative_confidence_should_be_handled(self):
        """Test that negative confidence values are handled properly."""
        hypotheses = [
            {
                "hypothesis": "Disk space full",
                "confidence": -0.5  # Negative confidence
            }
        ]
        new_evidence = ["Disk usage at 100%"]
        reasoning_chain = ReasoningChain()

        # Should either raise ValueError or handle gracefully by clamping/normalizing
        # Currently this may produce unexpected results
        result = rank_hypotheses(hypotheses, new_evidence, reasoning_chain)

        # If it doesn't raise an error, the result should be reasonable
        assert len(result) == 1
        assert result[0]["confidence"] >= 0.0  # Confidence should be non-negative

    def test_confidence_greater_than_one_should_be_handled(self):
        """Test that confidence > 1.0 values are handled properly."""
        hypotheses = [
            {
                "hypothesis": "Security breach detected",
                "confidence": 2.5  # Confidence > 1.0
            }
        ]
        new_evidence = ["Unauthorized access attempts logged"]
        reasoning_chain = ReasoningChain()

        # Should either raise ValueError or handle gracefully by clamping
        result = rank_hypotheses(hypotheses, new_evidence, reasoning_chain)

        # If it doesn't raise an error, the result should be clamped to 1.0
        assert len(result) == 1
        assert result[0]["confidence"] <= 1.0  # Confidence should not exceed 1.0

    def test_mixed_valid_and_invalid_confidence_types(self):
        """Test handling of mixed valid and invalid confidence types."""
        hypotheses = [
            {
                "hypothesis": "Valid hypothesis",
                "confidence": 0.7  # Valid numeric confidence
            },
            {
                "hypothesis": "Invalid hypothesis",
                "confidence": "invalid"  # Invalid string confidence
            },
            {
                "hypothesis": "Another valid hypothesis",
                "confidence": 0.3  # Valid numeric confidence
            }
        ]
        new_evidence = ["Mixed evidence provided"]
        reasoning_chain = ReasoningChain()

        # Should either fail completely or skip invalid hypotheses
        # New validation properly rejects invalid types
        with pytest.raises(ValidationError):
            rank_hypotheses(hypotheses, new_evidence, reasoning_chain)

    def test_existing_functionality_should_still_work(self):
        """Test that existing valid functionality still works correctly."""
        hypotheses = [
            {
                "hypothesis": "Server overload",
                "confidence": 0.6
            },
            {
                "hypothesis": "Network issue",
                "confidence": 0.4
            }
        ]
        new_evidence = ["High CPU usage", "Slow network response"]
        reasoning_chain = ReasoningChain()

        # This should work fine
        result = rank_hypotheses(hypotheses, new_evidence, reasoning_chain)

        # Verify structure and basic functionality
        assert len(result) == 2
        for hypothesis in result:
            assert "hypothesis" in hypothesis
            assert "confidence" in hypothesis
            assert isinstance(hypothesis["confidence"], (int, float))
            assert 0.0 <= hypothesis["confidence"] <= 1.0
            assert "supporting_evidence" in hypothesis