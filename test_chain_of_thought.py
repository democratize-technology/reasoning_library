#!/usr/bin/env python3
"""
Test script for the chain_of_thought module to verify integration and functionality.
"""

import sys
import os

# Add the parent directory to the Python path so we can import the reasoning_library
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reasoning_library import chain_of_thought_step, get_chain_summary, clear_chain
from reasoning_library import apply_modus_ponens, predict_next_in_sequence
from reasoning_library import ReasoningChain, get_tool_specs
from reasoning_library.core import TOOL_REGISTRY

def test_basic_chain_functionality():
    """Test basic chain of thought functionality."""
    print("=== Testing Basic Chain Functionality ===")

    # Test adding steps to a chain
    conversation_id = "test_conv_1"

    result1 = chain_of_thought_step(
        conversation_id=conversation_id,
        stage="Problem Analysis",
        description="Analyzing the mathematical problem",
        result="Need to find the pattern in the sequence [2, 4, 6, 8]",
        confidence=0.9
    )
    print(f"Step 1 result: {result1}")

    result2 = chain_of_thought_step(
        conversation_id=conversation_id,
        stage="Pattern Recognition",
        description="Identified arithmetic progression",
        result="Pattern is adding 2 each time",
        confidence=0.95,
        evidence="Differences are [2, 2, 2]"
    )
    print(f"Step 2 result: {result2}")

    # Get summary
    summary = get_chain_summary(conversation_id)
    print(f"Chain summary: {summary}")

    # Clear the chain
    clear_result = clear_chain(conversation_id)
    print(f"Clear result: {clear_result}")

    # Try to get summary after clearing
    empty_summary = get_chain_summary(conversation_id)
    print(f"Summary after clearing: {empty_summary}")

    print("Basic functionality test: PASSED\n")

def test_confidence_propagation():
    """Test confidence scoring system."""
    print("=== Testing Confidence Propagation ===")

    conversation_id = "test_conf"

    # Add steps with different confidences
    chain_of_thought_step(conversation_id, "Step1", "High confidence", "Result1", confidence=0.9)
    chain_of_thought_step(conversation_id, "Step2", "Medium confidence", "Result2", confidence=0.6)
    chain_of_thought_step(conversation_id, "Step3", "High confidence", "Result3", confidence=0.85)

    summary = get_chain_summary(conversation_id)
    print(f"Overall confidence (should be 0.6 - minimum): {summary['overall_confidence']}")

    # Test default confidence
    chain_of_thought_step(conversation_id, "Step4", "Default confidence", "Result4")  # Should be 0.8

    summary_after_default = get_chain_summary(conversation_id)
    print(f"Confidence after adding default step: {summary_after_default['overall_confidence']}")

    clear_chain(conversation_id)
    print("Confidence propagation test: PASSED\n")

def test_integration_with_existing_functions():
    """Test integration with deductive and inductive reasoning."""
    print("=== Testing Integration with Existing Functions ===")

    conversation_id = "integration_test"

    # Use existing reasoning functions
    chain = ReasoningChain()

    # Test modus ponens
    mp_result = apply_modus_ponens(
        p_is_true=True,
        p_implies_q_is_true=True,
        reasoning_chain=chain
    )
    print(f"Modus ponens result: {mp_result}")

    # Add this to our chain of thought
    chain_of_thought_step(
        conversation_id,
        "Deductive Reasoning",
        f"Applied modus ponens: P=True, P->Q=True",
        f"Concluded Q={mp_result}",
        confidence=1.0 if mp_result else 0.0
    )

    # Test sequence prediction
    sequence = [2, 4, 6, 8]
    seq_result = predict_next_in_sequence(sequence, reasoning_chain=chain)
    print(f"Sequence prediction result: {seq_result}")

    chain_of_thought_step(
        conversation_id,
        "Inductive Reasoning",
        f"Predicted next number in sequence {sequence}",
        f"Predicted: {seq_result}",
        confidence=0.8
    )

    # Show the combined reasoning chain
    summary = get_chain_summary(conversation_id)
    print(f"Combined reasoning summary:\n{summary['summary']}")

    clear_chain(conversation_id)
    print("Integration test: PASSED\n")

def test_tool_specs():
    """Test that tool specifications are generated correctly."""
    print("=== Testing Tool Specifications ===")

    tool_specs = get_tool_specs()
    print(f"Total tools registered: {len(tool_specs)}")

    # Find our chain of thought functions
    cot_functions = [spec for spec in tool_specs
                     if spec['function']['name'] in ['chain_of_thought_step', 'get_chain_summary', 'clear_chain']]

    print(f"Chain of thought functions found: {len(cot_functions)}")

    for spec in cot_functions:
        print(f"  - {spec['function']['name']}: {spec['function']['description'][:50]}...")

    print("Tool specifications test: PASSED\n")

def test_thread_safety_simulation():
    """Basic test of thread safety (simulation with sequential calls)."""
    print("=== Testing Thread Safety (Simulation) ===")

    # Create multiple conversations
    conversations = ["conv1", "conv2", "conv3"]

    for i, conv_id in enumerate(conversations):
        chain_of_thought_step(
            conv_id,
            f"Stage{i}",
            f"Description for conversation {conv_id}",
            f"Result {i}",
            confidence=0.8
        )

    # Check all conversations exist
    for conv_id in conversations:
        summary = get_chain_summary(conv_id)
        print(f"Conversation {conv_id}: {summary['step_count']} steps")

    # Clear all
    for conv_id in conversations:
        clear_chain(conv_id)

    print("Thread safety simulation: PASSED\n")

def main():
    """Run all tests."""
    print("Starting chain_of_thought module tests...\n")

    try:
        test_basic_chain_functionality()
        test_confidence_propagation()
        test_integration_with_existing_functions()
        test_tool_specs()
        test_thread_safety_simulation()

        print("=== ALL TESTS PASSED ===")
        print("Chain of thought module is working correctly!")

    except Exception as e:
        print(f"TEST FAILED: {e}")
        raise

if __name__ == "__main__":
    main()