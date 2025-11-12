"""
Test to verify the confidence validation fix works correctly.
This test shows that the type coercion vulnerability has been fixed.
"""

import pytest
from src.reasoning_library.abductive import rank_hypotheses
from src.reasoning_library.core import ReasoningChain


def test_string_confidence_now_raises_typeerror():
    """
    Test that string confidence values now raise a clear TypeError
    instead of causing cryptic multiplication errors.
    """
    hypotheses = [
        {
            "hypothesis": "Test hypothesis",
            "confidence": "high"  # String should raise TypeError
        }
    ]
    new_evidence = ["Some evidence"]
    reasoning_chain = ReasoningChain()

    # Should raise a clear TypeError with helpful message
    with pytest.raises(TypeError) as exc_info:
        rank_hypotheses(hypotheses, new_evidence, reasoning_chain)

    # Verify the error message is helpful
    error_msg = str(exc_info.value)
    assert "Confidence value must be numeric" in error_msg
    assert "hypothesis #0" in error_msg
    assert "str" in error_msg


def test_none_confidence_now_raises_typeerror():
    """
    Test that None confidence values now raise a clear TypeError.
    """
    hypotheses = [
        {
            "hypothesis": "Test hypothesis",
            "confidence": None  # None should raise TypeError
        }
    ]
    new_evidence = ["Some evidence"]
    reasoning_chain = ReasoningChain()

    # Should raise a clear TypeError
    with pytest.raises(TypeError) as exc_info:
        rank_hypotheses(hypotheses, new_evidence, reasoning_chain)

    error_msg = str(exc_info.value)
    assert "Confidence value must be numeric" in error_msg
    assert "NoneType" in error_msg


def test_negative_confidence_is_clamped_to_zero():
    """
    Test that negative confidence values are clamped to 0.0.
    """
    hypotheses = [
        {
            "hypothesis": "Test hypothesis",
            "confidence": -0.5  # Negative should be clamped to 0.0
        }
    ]
    new_evidence = ["Some evidence"]
    reasoning_chain = ReasoningChain()

    # Should work without error and clamp to 0.0
    result = rank_hypotheses(hypotheses, new_evidence, reasoning_chain)

    assert len(result) == 1
    assert result[0]["confidence"] >= 0.0  # Should be non-negative


def test_confidence_greater_than_one_is_clamped():
    """
    Test that confidence > 1.0 values are clamped to 1.0.
    """
    hypotheses = [
        {
            "hypothesis": "Test hypothesis",
            "confidence": 2.5  # > 1.0 should be clamped
        }
    ]
    new_evidence = ["Some evidence"]
    reasoning_chain = ReasoningChain()

    result = rank_hypotheses(hypotheses, new_evidence, reasoning_chain)

    assert len(result) == 1
    # The confidence should be clamped to 1.0 by both validation and min(1.0, ...)
    assert result[0]["confidence"] <= 1.0


def test_edge_case_confidence_values():
    """
    Test edge cases like very small numbers, zero, etc.
    """
    test_cases = [
        0.0,      # Zero
        0.000001, # Very small positive
        1.0,      # Maximum valid
        -0.0,     # Negative zero (should become 0.0)
    ]

    for confidence_value in test_cases:
        hypotheses = [
            {
                "hypothesis": f"Test hypothesis with confidence {confidence_value}",
                "confidence": confidence_value
            }
        ]
        new_evidence = ["Some evidence"]
        reasoning_chain = ReasoningChain()

        result = rank_hypotheses(hypotheses, new_evidence, reasoning_chain)

        assert len(result) == 1
        assert isinstance(result[0]["confidence"], (int, float))
        assert 0.0 <= result[0]["confidence"] <= 1.0


def test_multiple_hypotheses_with_mixed_valid_confidence():
    """
    Test that multiple hypotheses with valid confidence values work correctly.
    """
    hypotheses = [
        {
            "hypothesis": "First hypothesis",
            "confidence": 0.3
        },
        {
            "hypothesis": "Second hypothesis",
            "confidence": 0.7
        },
        {
            "hypothesis": "Third hypothesis",
            "confidence": 0.5
        }
    ]
    new_evidence = ["Evidence supporting all hypotheses"]
    reasoning_chain = ReasoningChain()

    result = rank_hypotheses(hypotheses, new_evidence, reasoning_chain)

    assert len(result) == 3
    for hypothesis in result:
        assert isinstance(hypothesis["confidence"], (int, float))
        assert 0.0 <= hypothesis["confidence"] <= 1.0

    # Should be sorted by confidence (highest first)
    confidences = [h["confidence"] for h in result]
    assert confidences == sorted(confidences, reverse=True)