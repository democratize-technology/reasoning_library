#!/usr/bin/env python3
"""
Simple test script for the chain_of_thought module without numpy dependencies.
"""

import sys
import os

# Add the parent directory to the Python path so we can import the reasoning_library
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Only import what we need to avoid numpy dependency
from reasoning_library.chain_of_thought import chain_of_thought_step, get_chain_summary, clear_chain
from reasoning_library.core import get_tool_specs, ReasoningChain

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
    assert result1['success'] == True
    assert result1['step_number'] == 1
    assert result1['confidence'] == 0.9

    result2 = chain_of_thought_step(
        conversation_id=conversation_id,
        stage="Pattern Recognition",
        description="Identified arithmetic progression",
        result="Pattern is adding 2 each time",
        confidence=0.95,
        evidence="Differences are [2, 2, 2]"
    )
    print(f"Step 2 result: {result2}")
    assert result2['step_number'] == 2
    assert result2['confidence'] == 0.95

    # Get summary
    summary = get_chain_summary(conversation_id)
    print(f"Chain summary step count: {summary['step_count']}")
    print(f"Overall confidence: {summary['overall_confidence']}")
    assert summary['success'] == True
    assert summary['step_count'] == 2
    assert summary['overall_confidence'] == 0.9  # Should be minimum of 0.9 and 0.95

    # Clear the chain
    clear_result = clear_chain(conversation_id)
    print(f"Clear result: {clear_result}")
    assert clear_result['success'] == True
    assert clear_result['steps_removed'] == 2

    # Try to get summary after clearing
    empty_summary = get_chain_summary(conversation_id)
    print(f"Summary after clearing success: {empty_summary['success']}")
    assert empty_summary['success'] == False
    assert empty_summary['step_count'] == 0

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
    assert summary['overall_confidence'] == 0.6  # Should be minimum

    # Test default confidence
    result = chain_of_thought_step(conversation_id, "Step4", "Default confidence", "Result4")  # Should be 0.8
    assert result['confidence'] == 0.8

    summary_after_default = get_chain_summary(conversation_id)
    print(f"Confidence after adding default step: {summary_after_default['overall_confidence']}")
    assert summary_after_default['overall_confidence'] == 0.6  # Still minimum

    clear_chain(conversation_id)
    print("Confidence propagation test: PASSED\n")

def test_tool_specs():
    """Test that tool specifications are generated correctly."""
    print("=== Testing Tool Specifications ===")

    tool_specs = get_tool_specs()
    print(f"Total tools registered: {len(tool_specs)}")

    # Find our chain of thought functions
    cot_functions = [spec for spec in tool_specs
                     if spec['function']['name'] in ['chain_of_thought_step', 'get_chain_summary', 'clear_chain']]

    print(f"Chain of thought functions found: {len(cot_functions)}")
    assert len(cot_functions) == 3

    for spec in cot_functions:
        print(f"  - {spec['function']['name']}: {len(spec['function']['parameters']['properties'])} parameters")
        assert 'conversation_id' in spec['function']['parameters']['properties']

    print("Tool specifications test: PASSED\n")

def test_edge_cases():
    """Test edge cases and error conditions."""
    print("=== Testing Edge Cases ===")

    # Test invalid confidence values
    result = chain_of_thought_step(
        "edge_test", "Test", "Testing bounds", "Result", confidence=1.5  # Should be clamped to 1.0
    )
    assert result['confidence'] == 1.0

    result2 = chain_of_thought_step(
        "edge_test", "Test2", "Testing negative", "Result2", confidence=-0.5  # Should be clamped to 0.0
    )
    assert result2['confidence'] == 0.0

    # Test clearing non-existent conversation
    clear_result = clear_chain("non_existent_conversation")
    assert clear_result['success'] == False
    assert clear_result['steps_removed'] == 0

    clear_chain("edge_test")
    print("Edge cases test: PASSED\n")

def main():
    """Run all tests."""
    print("Starting chain_of_thought module tests (simple version)...\n")

    try:
        test_basic_chain_functionality()
        test_confidence_propagation()
        test_tool_specs()
        test_edge_cases()

        print("=== ALL TESTS PASSED ===")
        print("Chain of thought module is working correctly!")
        return True

    except Exception as e:
        print(f"TEST FAILED: {e}")
        raise

if __name__ == "__main__":
    main()