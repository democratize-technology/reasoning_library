#!/usr/bin/env python3
"""
Manual test runner for confidence scoring validation.

This script runs key confidence scoring tests to verify mathematical correctness
without requiring pytest installation.
"""

import sys
import os
import traceback
import numpy as np

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_test(test_name, test_function):
    """Run a single test and report results."""
    try:
        test_function()
        print(f"✅ {test_name}: PASSED")
        return True
    except Exception as e:
        print(f"❌ {test_name}: FAILED - {str(e)}")
        traceback.print_exc()
        return False

def test_deductive_confidence_basic():
    """Test basic deductive reasoning confidence scoring."""
    from reasoning_library.deductive import (
        logical_and_with_confidence,
        logical_or_with_confidence,
        apply_modus_ponens
    )
    from reasoning_library.core import ReasoningChain

    # Test logical operations have confidence 1.0
    result, confidence = logical_and_with_confidence(True, True)
    assert result is True
    assert confidence == 1.0, f"Expected confidence 1.0, got {confidence}"

    result, confidence = logical_or_with_confidence(False, True)
    assert result is True
    assert confidence == 1.0, f"Expected confidence 1.0, got {confidence}"

    # Test Modus Ponens confidence
    chain = ReasoningChain()
    result = apply_modus_ponens(True, True, reasoning_chain=chain)
    assert result is True
    assert chain.steps[0].confidence == 1.0, "Valid Modus Ponens should have confidence 1.0"

    # Test invalid Modus Ponens
    chain_invalid = ReasoningChain()
    result = apply_modus_ponens(False, True, reasoning_chain=chain_invalid)
    assert result is None
    assert chain_invalid.steps[0].confidence == 0.0, "Invalid Modus Ponens should have confidence 0.0"

def test_inductive_confidence_basic():
    """Test basic inductive reasoning confidence scoring."""
    from reasoning_library.inductive import predict_next_in_sequence
    from reasoning_library.core import ReasoningChain

    # Test perfect arithmetic progression
    perfect_sequence = [1, 2, 3, 4, 5]
    chain = ReasoningChain()
    result = predict_next_in_sequence(perfect_sequence, reasoning_chain=chain)

    assert result == 6, f"Expected next value 6, got {result}"
    assert len(chain.steps) == 1, "Should add one step"
    confidence = chain.steps[0].confidence
    assert confidence > 0.9, f"Perfect arithmetic progression should have high confidence (>0.9), got {confidence}"
    assert confidence <= 1.0, f"Confidence should not exceed 1.0, got {confidence}"

    # Test noisy sequence
    noisy_sequence = [1.1, 2.0, 2.9, 4.1]
    chain_noisy = ReasoningChain()
    result = predict_next_in_sequence(noisy_sequence, reasoning_chain=chain_noisy, rtol=0.3)

    if len(chain_noisy.steps) > 0:
        confidence_noisy = chain_noisy.steps[0].confidence
        assert 0.0 <= confidence_noisy <= 1.0, f"Confidence should be in [0,1], got {confidence_noisy}"
        assert confidence_noisy < confidence, "Noisy sequence should have lower confidence than perfect"

def test_chain_of_thought_confidence_basic():
    """Test basic chain-of-thought confidence propagation."""
    from reasoning_library.chain_of_thought import (
        chain_of_thought_step,
        get_chain_summary,
        clear_chain
    )

    conversation_id = "test_basic_chain"
    clear_chain(conversation_id)

    # Add steps with different confidence levels
    confidences = [0.9, 0.7, 0.8]

    for i, conf in enumerate(confidences):
        result = chain_of_thought_step(
            conversation_id=conversation_id,
            stage=f"Step_{i+1}",
            description=f"Test step {i+1}",
            result=f"Result {i+1}",
            confidence=conf
        )
        assert result["success"] is True

    # Verify minimum confidence aggregation
    summary = get_chain_summary(conversation_id)
    assert summary["success"] is True
    assert summary["step_count"] == 3
    expected_min = min(confidences)
    assert summary["overall_confidence"] == expected_min, f"Expected minimum confidence {expected_min}, got {summary['overall_confidence']}"

    clear_chain(conversation_id)

def test_confidence_bounds():
    """Test that all confidence values are within valid bounds."""
    from reasoning_library.deductive import logical_and_with_confidence
    from reasoning_library.inductive import predict_next_in_sequence
    from reasoning_library.chain_of_thought import chain_of_thought_step, get_chain_summary, clear_chain
    from reasoning_library.core import ReasoningChain

    # Test deductive bounds
    _, conf_deductive = logical_and_with_confidence(True, False)
    assert 0.0 <= conf_deductive <= 1.0, f"Deductive confidence out of bounds: {conf_deductive}"

    # Test inductive bounds
    chain = ReasoningChain()
    predict_next_in_sequence([1, 2, 3], reasoning_chain=chain)
    if len(chain.steps) > 0:
        conf_inductive = chain.steps[0].confidence
        assert 0.0 <= conf_inductive <= 1.0, f"Inductive confidence out of bounds: {conf_inductive}"

    # Test chain-of-thought bounds with extreme values
    conversation_id = "test_bounds"
    clear_chain(conversation_id)

    # Test confidence clamping
    chain_of_thought_step(conversation_id, "Test", "Bounds test", "Result", confidence=-0.5)
    summary = get_chain_summary(conversation_id)
    assert summary["overall_confidence"] == 0.0, "Negative confidence should be clamped to 0.0"

    clear_chain(conversation_id)
    chain_of_thought_step(conversation_id, "Test", "Bounds test", "Result", confidence=1.5)
    summary = get_chain_summary(conversation_id)
    assert summary["overall_confidence"] == 1.0, "Confidence > 1.0 should be clamped to 1.0"

    clear_chain(conversation_id)

def test_confidence_mathematical_properties():
    """Test mathematical properties of confidence scoring."""
    from reasoning_library.inductive import _calculate_arithmetic_confidence, _assess_data_sufficiency, _calculate_pattern_quality_score

    # Test data sufficiency calculation
    sufficiency_3_arith = _assess_data_sufficiency(3, 'arithmetic')
    sufficiency_2_arith = _assess_data_sufficiency(2, 'arithmetic')
    assert sufficiency_3_arith >= sufficiency_2_arith, "More data should have equal or higher sufficiency"

    sufficiency_4_geom = _assess_data_sufficiency(4, 'geometric')
    sufficiency_3_geom = _assess_data_sufficiency(3, 'geometric')
    assert sufficiency_4_geom >= sufficiency_3_geom, "More data should have equal or higher sufficiency"

    # Test pattern quality calculation
    perfect_diffs = [2, 2, 2, 2]
    noisy_diffs = [2.1, 1.9, 2.05, 1.95]

    quality_perfect = _calculate_pattern_quality_score(perfect_diffs, 'arithmetic')
    quality_noisy = _calculate_pattern_quality_score(noisy_diffs, 'arithmetic')

    assert quality_perfect > quality_noisy, "Perfect pattern should have higher quality than noisy pattern"
    assert 0.0 <= quality_perfect <= 1.0, "Pattern quality should be in [0,1]"
    assert 0.0 <= quality_noisy <= 1.0, "Pattern quality should be in [0,1]"

def test_integration_workflow():
    """Test end-to-end reasoning workflow with confidence tracking."""
    from reasoning_library.deductive import apply_modus_ponens
    from reasoning_library.inductive import predict_next_in_sequence
    from reasoning_library.chain_of_thought import chain_of_thought_step, get_chain_summary, clear_chain
    from reasoning_library.core import ReasoningChain

    conversation_id = "integration_test"
    clear_chain(conversation_id)

    # Step 1: Deductive reasoning
    deductive_chain = ReasoningChain()
    apply_modus_ponens(True, True, reasoning_chain=deductive_chain)
    deductive_conf = deductive_chain.steps[0].confidence

    chain_of_thought_step(
        conversation_id=conversation_id,
        stage="Deductive",
        description="Applied deductive logic",
        result=True,
        confidence=deductive_conf
    )

    # Step 2: Inductive reasoning
    inductive_chain = ReasoningChain()
    predict_next_in_sequence([1, 2, 3, 4], reasoning_chain=inductive_chain)
    inductive_conf = inductive_chain.steps[0].confidence

    chain_of_thought_step(
        conversation_id=conversation_id,
        stage="Inductive",
        description="Applied pattern recognition",
        result=5,
        confidence=inductive_conf
    )

    # Step 3: Manual reasoning
    manual_conf = 0.8
    chain_of_thought_step(
        conversation_id=conversation_id,
        stage="Manual",
        description="Manual analysis",
        result="Conclusion",
        confidence=manual_conf
    )

    # Verify overall confidence follows minimum rule
    summary = get_chain_summary(conversation_id)
    expected_min = min(deductive_conf, inductive_conf, manual_conf)
    assert summary["overall_confidence"] == expected_min, f"Expected minimum {expected_min}, got {summary['overall_confidence']}"

    clear_chain(conversation_id)

def main():
    """Run all confidence scoring tests."""
    print("🧠 Running Comprehensive Confidence Scoring Tests")
    print("=" * 60)

    tests = [
        ("Deductive Confidence Basic", test_deductive_confidence_basic),
        ("Inductive Confidence Basic", test_inductive_confidence_basic),
        ("Chain-of-Thought Confidence Basic", test_chain_of_thought_confidence_basic),
        ("Confidence Bounds Validation", test_confidence_bounds),
        ("Confidence Mathematical Properties", test_confidence_mathematical_properties),
        ("Integration Workflow", test_integration_workflow),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        if run_test(test_name, test_func):
            passed += 1
        print()

    print("=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All confidence scoring tests PASSED! Mathematical correctness verified.")
        return 0
    else:
        print(f"⚠️  {total - passed} tests FAILED. Mathematical correctness issues detected.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)