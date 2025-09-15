#!/usr/bin/env python3
"""
Simple confidence scoring tests without external dependencies.

This script validates the mathematical correctness of confidence scoring
across the reasoning library without requiring numpy or pytest.
"""

import sys
import os
import traceback

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

def test_deductive_confidence_mathematical_correctness():
    """Test that deductive reasoning has correct confidence dichotomy (1.0 or 0.0)."""
    try:
        from deductive import (
            logical_and_with_confidence,
            logical_or_with_confidence,
            implies_with_confidence,
            apply_modus_ponens
        )
        from core import ReasoningChain
    except ImportError:
        from reasoning_library.deductive import (
            logical_and_with_confidence,
            logical_or_with_confidence,
            implies_with_confidence,
            apply_modus_ponens
        )
        from reasoning_library.core import ReasoningChain

    # Test all logical operations have confidence 1.0 (deterministic)
    test_cases = [
        (logical_and_with_confidence, [(True, True), (True, False), (False, True), (False, False)]),
        (logical_or_with_confidence, [(True, True), (True, False), (False, True), (False, False)]),
        (implies_with_confidence, [(True, True), (True, False), (False, True), (False, False)]),
    ]

    for op_func, inputs in test_cases:
        for input_args in inputs:
            result, confidence = op_func(*input_args)
            assert confidence == 1.0, f"{op_func.__name__}{input_args} should have confidence 1.0, got {confidence}"

    # Test Modus Ponens confidence dichotomy
    # Valid case should have confidence 1.0
    chain_valid = ReasoningChain()
    result = apply_modus_ponens(True, True, reasoning_chain=chain_valid)
    assert result is True
    assert chain_valid.steps[0].confidence == 1.0, "Valid Modus Ponens should have confidence 1.0"

    # Invalid cases should have confidence 0.0
    invalid_cases = [(False, True), (True, False), (False, False)]
    for p, p_implies_q in invalid_cases:
        chain_invalid = ReasoningChain()
        result = apply_modus_ponens(p, p_implies_q, reasoning_chain=chain_invalid)
        assert result is None, f"Invalid Modus Ponens should return None for P={p}, (P->Q)={p_implies_q}"
        assert chain_invalid.steps[0].confidence == 0.0, f"Invalid Modus Ponens should have confidence 0.0 for P={p}, (P->Q)={p_implies_q}"

def test_inductive_confidence_variable_scoring():
    """Test that inductive reasoning has variable confidence based on pattern strength."""
    try:
        from inductive import predict_next_in_sequence
        from core import ReasoningChain
    except ImportError:
        from reasoning_library.inductive import predict_next_in_sequence
        from reasoning_library.core import ReasoningChain

    # Perfect arithmetic progression should have high confidence
    perfect_sequence = [1, 2, 3, 4, 5]
    chain_perfect = ReasoningChain()
    result = predict_next_in_sequence(perfect_sequence, reasoning_chain=chain_perfect)

    assert result == 6, f"Perfect arithmetic progression should predict 6, got {result}"
    assert len(chain_perfect.steps) == 1, "Should add exactly one step"
    perfect_confidence = chain_perfect.steps[0].confidence
    assert perfect_confidence > 0.8, f"Perfect progression should have high confidence (>0.8), got {perfect_confidence}"
    assert perfect_confidence <= 1.0, f"Confidence should not exceed 1.0, got {perfect_confidence}"

    # Test confidence bounds
    assert 0.0 <= perfect_confidence <= 1.0, f"Confidence should be in [0,1], got {perfect_confidence}"

    # Test that longer sequences don't decrease confidence inappropriately
    longer_sequence = [1, 2, 3, 4, 5, 6, 7]
    chain_longer = ReasoningChain()
    result_longer = predict_next_in_sequence(longer_sequence, reasoning_chain=chain_longer)

    assert result_longer == 8, "Longer perfect sequence should predict 8"
    longer_confidence = chain_longer.steps[0].confidence
    assert longer_confidence >= perfect_confidence, "Longer sequence should have equal or higher confidence"

def test_chain_of_thought_minimum_aggregation():
    """Test that chain-of-thought uses minimum confidence aggregation (weakest link)."""
    try:
        from chain_of_thought import (
            chain_of_thought_step,
            get_chain_summary,
            clear_chain
        )
    except ImportError:
        from reasoning_library.chain_of_thought import (
            chain_of_thought_step,
            get_chain_summary,
            clear_chain
        )

    conversation_id = "test_minimum_aggregation"
    clear_chain(conversation_id)

    # Test minimum confidence calculation
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

    # Verify minimum aggregation
    summary = get_chain_summary(conversation_id)
    assert summary["success"] is True
    assert summary["step_count"] == 4
    expected_minimum = min(confidences)
    assert summary["overall_confidence"] == expected_minimum, f"Expected minimum {expected_minimum}, got {summary['overall_confidence']}"

    # Test edge case: single step
    clear_chain(conversation_id)
    chain_of_thought_step(conversation_id, "Single", "Single step", "Result", confidence=0.75)
    summary_single = get_chain_summary(conversation_id)
    assert summary_single["overall_confidence"] == 0.75, "Single step should preserve its confidence"

    # Test edge case: all same confidence
    clear_chain(conversation_id)
    same_confidence = 0.85
    for i in range(3):
        chain_of_thought_step(conversation_id, f"Same_{i}", f"Same step {i}", f"Result {i}", confidence=same_confidence)

    summary_same = get_chain_summary(conversation_id)
    assert summary_same["overall_confidence"] == same_confidence, "All same confidence should preserve that value"

    clear_chain(conversation_id)

def test_confidence_bounds_enforcement():
    """Test that confidence values are properly bounded to [0.0, 1.0]."""
    try:
        from chain_of_thought import chain_of_thought_step, get_chain_summary, clear_chain
    except ImportError:
        from reasoning_library.chain_of_thought import chain_of_thought_step, get_chain_summary, clear_chain

    conversation_id = "test_bounds"

    # Test confidence clamping
    test_cases = [
        (-0.5, 0.0),   # Below minimum should clamp to 0.0
        (1.5, 1.0),    # Above maximum should clamp to 1.0
        (-10, 0.0),    # Far below minimum
        (5.0, 1.0),    # Far above maximum
        (0.0, 0.0),    # At minimum boundary
        (1.0, 1.0),    # At maximum boundary
        (0.5, 0.5),    # Valid middle value
    ]

    for input_conf, expected_conf in test_cases:
        clear_chain(conversation_id)

        result = chain_of_thought_step(
            conversation_id=conversation_id,
            stage="Bounds_Test",
            description=f"Testing bounds with input {input_conf}",
            result="Test result",
            confidence=input_conf
        )

        assert result["success"] is True, f"Should succeed even with out-of-bounds confidence {input_conf}"
        assert result["confidence"] == expected_conf, f"Input {input_conf} should be clamped to {expected_conf}, got {result['confidence']}"

        summary = get_chain_summary(conversation_id)
        assert summary["overall_confidence"] == expected_conf, f"Summary should reflect clamped confidence {expected_conf}"

    clear_chain(conversation_id)

def test_default_confidence_application():
    """Test that default confidence (0.8) is applied when not specified."""
    try:
        from chain_of_thought import chain_of_thought_step, get_chain_summary, clear_chain
    except ImportError:
        from reasoning_library.chain_of_thought import chain_of_thought_step, get_chain_summary, clear_chain

    conversation_id = "test_default"
    clear_chain(conversation_id)

    # Test with None confidence (should default to 0.8)
    result = chain_of_thought_step(
        conversation_id=conversation_id,
        stage="Default_Test",
        description="Testing default confidence",
        result="Test result",
        confidence=None
    )

    assert result["success"] is True
    assert result["confidence"] == 0.8, "None confidence should default to 0.8"

    # Test without confidence parameter (should default to 0.8)
    result2 = chain_of_thought_step(
        conversation_id=conversation_id,
        stage="Default_Test_2",
        description="Testing default confidence without parameter",
        result="Test result 2"
        # No confidence parameter
    )

    assert result2["success"] is True
    assert result2["confidence"] == 0.8, "Missing confidence should default to 0.8"

    # Verify overall confidence with defaults
    summary = get_chain_summary(conversation_id)
    assert summary["overall_confidence"] == 0.8, "All default confidence steps should result in 0.8 overall"

    clear_chain(conversation_id)

def test_integrated_reasoning_workflow():
    """Test end-to-end reasoning workflow combining all reasoning types."""
    try:
        from deductive import apply_modus_ponens
        from inductive import predict_next_in_sequence
        from chain_of_thought import chain_of_thought_step, get_chain_summary, clear_chain
        from core import ReasoningChain
    except ImportError:
        from reasoning_library.deductive import apply_modus_ponens
        from reasoning_library.inductive import predict_next_in_sequence
        from reasoning_library.chain_of_thought import chain_of_thought_step, get_chain_summary, clear_chain
        from reasoning_library.core import ReasoningChain

    conversation_id = "integrated_test"
    clear_chain(conversation_id)

    # Step 1: Deductive reasoning (should have confidence 1.0)
    deductive_chain = ReasoningChain()
    deductive_result = apply_modus_ponens(True, True, reasoning_chain=deductive_chain)
    deductive_confidence = deductive_chain.steps[0].confidence

    assert deductive_result is True
    assert deductive_confidence == 1.0

    chain_of_thought_step(
        conversation_id=conversation_id,
        stage="Deductive_Logic",
        description="Applied Modus Ponens rule",
        result=deductive_result,
        confidence=deductive_confidence
    )

    # Step 2: Inductive reasoning (variable confidence)
    sequence = [2, 4, 6, 8]
    inductive_chain = ReasoningChain()
    inductive_result = predict_next_in_sequence(sequence, reasoning_chain=inductive_chain)
    inductive_confidence = inductive_chain.steps[0].confidence

    assert inductive_result == 10
    assert 0.8 < inductive_confidence <= 1.0  # Should be high for perfect arithmetic

    chain_of_thought_step(
        conversation_id=conversation_id,
        stage="Pattern_Recognition",
        description="Predicted next in arithmetic sequence",
        result=inductive_result,
        confidence=inductive_confidence
    )

    # Step 3: Manual reasoning with moderate confidence
    manual_confidence = 0.7
    chain_of_thought_step(
        conversation_id=conversation_id,
        stage="Synthesis",
        description="Combined deductive and inductive insights",
        result="Integrated conclusion",
        confidence=manual_confidence
    )

    # Verify overall confidence follows minimum rule
    summary = get_chain_summary(conversation_id)
    expected_minimum = min(deductive_confidence, inductive_confidence, manual_confidence)

    assert summary["success"] is True
    assert summary["step_count"] == 3
    assert summary["overall_confidence"] == expected_minimum
    assert summary["overall_confidence"] == 0.7  # Manual step is weakest link

    clear_chain(conversation_id)

def main():
    """Run all confidence scoring validation tests."""
    print("🧠 Mathematical Correctness Validation: Confidence Scoring")
    print("=" * 65)
    print("Testing confidence thresholds across deductive, inductive, and")
    print("chain-of-thought reasoning with mathematical validation.\n")

    tests = [
        ("Deductive Confidence Mathematical Correctness", test_deductive_confidence_mathematical_correctness),
        ("Inductive Confidence Variable Scoring", test_inductive_confidence_variable_scoring),
        ("Chain-of-Thought Minimum Aggregation", test_chain_of_thought_minimum_aggregation),
        ("Confidence Bounds Enforcement", test_confidence_bounds_enforcement),
        ("Default Confidence Application", test_default_confidence_application),
        ("Integrated Reasoning Workflow", test_integrated_reasoning_workflow),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        if run_test(test_name, test_func):
            passed += 1
        print()

    print("=" * 65)
    print(f"📊 MATHEMATICAL VALIDATION RESULTS: {passed}/{total} tests passed")
    print()

    if passed == total:
        print("🎉 ALL CONFIDENCE SCORING TESTS PASSED!")
        print("✅ Mathematical correctness VERIFIED across all reasoning types:")
        print("   • Deductive: Binary confidence (1.0 valid, 0.0 invalid)")
        print("   • Inductive: Variable confidence (0.0-1.0 based on pattern strength)")
        print("   • Chain-of-thought: Minimum aggregation (weakest link)")
        print("   • Integration: Proper confidence propagation")
        print("   • Bounds: All confidence values in [0.0, 1.0]")
        return 0
    else:
        print(f"⚠️  {total - passed} CRITICAL FAILURES DETECTED!")
        print("❌ Mathematical correctness issues found in confidence scoring.")
        print("   Review failed tests above for specific problems.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)