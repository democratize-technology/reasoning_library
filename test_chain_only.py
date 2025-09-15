#!/usr/bin/env python3
"""
Test chain-of-thought confidence scoring only.
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_chain_of_thought_confidence():
    """Test chain-of-thought confidence scoring."""
    from chain_of_thought import (
        chain_of_thought_step,
        get_chain_summary,
        clear_chain
    )

    print("Testing chain-of-thought confidence scoring...")

    conversation_id = "test_chain"
    clear_chain(conversation_id)

    # Test minimum confidence aggregation
    confidences = [0.9, 0.6, 0.8, 0.7]  # Minimum should be 0.6

    for i, conf in enumerate(confidences):
        result = chain_of_thought_step(
            conversation_id=conversation_id,
            stage=f"Step_{i+1}",
            description=f"Test step {i+1}",
            result=f"Result {i+1}",
            confidence=conf
        )
        assert result["success"] is True, f"Step {i+1} should succeed"
        print(f"✅ Added step {i+1} with confidence: {conf}")

    # Verify minimum aggregation
    summary = get_chain_summary(conversation_id)
    assert summary["success"] is True
    assert summary["step_count"] == 4
    expected_minimum = min(confidences)
    assert summary["overall_confidence"] == expected_minimum
    print(f"✅ Overall confidence (minimum): {summary['overall_confidence']} (expected: {expected_minimum})")

    # Test confidence bounds
    clear_chain(conversation_id)

    # Test clamping
    result = chain_of_thought_step(conversation_id, "Test", "Bounds test", "Result", confidence=-0.5)
    summary = get_chain_summary(conversation_id)
    assert summary["overall_confidence"] == 0.0, "Negative confidence should be clamped to 0.0"
    print(f"✅ Negative confidence clamped: {result['confidence']} -> 0.0")

    clear_chain(conversation_id)
    result = chain_of_thought_step(conversation_id, "Test", "Bounds test", "Result", confidence=1.5)
    summary = get_chain_summary(conversation_id)
    assert summary["overall_confidence"] == 1.0, "Confidence > 1.0 should be clamped to 1.0"
    print(f"✅ High confidence clamped: 1.5 -> {result['confidence']}")

    # Test default confidence
    clear_chain(conversation_id)
    result = chain_of_thought_step(conversation_id, "Default", "Default test", "Result")  # No confidence
    assert result["confidence"] == 0.8, "Missing confidence should default to 0.8"
    print(f"✅ Default confidence applied: {result['confidence']}")

    clear_chain(conversation_id)
    print("🎉 All chain-of-thought confidence tests passed!")

if __name__ == "__main__":
    test_chain_of_thought_confidence()