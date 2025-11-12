"""
Test to demonstrate the specific type coercion bug in rank_hypotheses function.
This test shows the vulnerability at line 547 in abductive.py.
"""

import pytest
from src.reasoning_library.abductive import rank_hypotheses
from src.reasoning_library.core import ReasoningChain


def test_type_coercion_bug_demonstration():
    """
    This test demonstrates the type coercion vulnerability in confidence calculations.

    At line 547 in abductive.py:
    updated_hypothesis["confidence"] = min(1.0,
                                           hypothesis["confidence"] * confidence_multiplier)

    If hypothesis["confidence"] is not numeric, this will cause a TypeError.
    """
    # Test case 1: String confidence causes TypeError
    hypotheses = [
        {
            "hypothesis": "Test hypothesis",
            "confidence": "high"  # This will cause TypeError when multiplied
        }
    ]
    new_evidence = ["Some evidence"]
    reasoning_chain = ReasoningChain()

    # This should fail with TypeError due to string * float operation
    with pytest.raises(TypeError):
        rank_hypotheses(hypotheses, new_evidence, reasoning_chain)


def test_none_confidence_bug_demonstration():
    """
    Test case 2: None confidence causes TypeError
    """
    hypotheses = [
        {
            "hypothesis": "Test hypothesis",
            "confidence": None  # This will cause TypeError when multiplied
        }
    ]
    new_evidence = ["Some evidence"]
    reasoning_chain = ReasoningChain()

    # This should fail with TypeError due to None * float operation
    with pytest.raises(TypeError):
        rank_hypotheses(hypotheses, new_evidence, reasoning_chain)


def test_valid_confidence_still_works():
    """
    Test case 3: Verify that valid numeric confidence still works
    """
    hypotheses = [
        {
            "hypothesis": "Test hypothesis",
            "confidence": 0.5  # Valid numeric confidence
        }
    ]
    new_evidence = ["Some evidence"]
    reasoning_chain = ReasoningChain()

    # This should work fine
    result = rank_hypotheses(hypotheses, new_evidence, reasoning_chain)

    # Verify results
    assert len(result) == 1
    assert isinstance(result[0]["confidence"], (int, float))
    assert 0.0 <= result[0]["confidence"] <= 1.0