#!/usr/bin/env python3
"""
Test deductive reasoning confidence scoring only.
"""

from reasoning_library.core import ReasoningChain
from reasoning_library.deductive import (
    apply_modus_ponens,
    implies_with_confidence,
    logical_and_with_confidence,
    logical_or_with_confidence,
)


def test_deductive_confidence():
    """Test deductive reasoning confidence scoring."""

    print("Testing deductive reasoning confidence scoring...")

    # Test logical operations have confidence 1.0
    result, confidence = logical_and_with_confidence(True, True)
    assert result is True
    assert confidence == 1.0, f"Expected confidence 1.0, got {confidence}"
    print(f"✅ logical_and(True, True) -> {result}, confidence: {confidence}")

    result, confidence = logical_or_with_confidence(False, True)
    assert result is True
    assert confidence == 1.0, f"Expected confidence 1.0, got {confidence}"
    print(f"✅ logical_or(False, True) -> {result}, confidence: {confidence}")

    result, confidence = implies_with_confidence(True, False)
    assert result is False
    assert confidence == 1.0, f"Expected confidence 1.0, got {confidence}"
    print(f"✅ implies(True, False) -> {result}, confidence: {confidence}")

    # Test Modus Ponens confidence
    chain = ReasoningChain()
    result = apply_modus_ponens(True, True, reasoning_chain=chain)
    assert result is True
    assert (
        chain.steps[0].confidence == 1.0
    ), "Valid Modus Ponens should have confidence 1.0"
    print(
        f"✅ apply_modus_ponens(True, True) -> {result}, confidence: {chain.steps[0].confidence}"
    )

    # Test invalid Modus Ponens
    chain_invalid = ReasoningChain()
    result = apply_modus_ponens(False, True, reasoning_chain=chain_invalid)
    assert result is None
    assert (
        chain_invalid.steps[0].confidence == 0.0
    ), "Invalid Modus Ponens should have confidence 0.0"
    print(
        f"✅ apply_modus_ponens(False, True) -> {result}, confidence: {chain_invalid.steps[0].confidence}"
    )

    print("🎉 All deductive confidence tests passed!")


if __name__ == "__main__":
    test_deductive_confidence()
