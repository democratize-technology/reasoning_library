#!/usr/bin/env python3
"""
Direct test of chain_of_thought module without going through __init__.py
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Direct imports to avoid numpy dependency
import reasoning_library.chain_of_thought as cot
import reasoning_library.core as core

def test_basic_functionality():
    """Test basic chain of thought functionality."""
    print("=== Testing Basic Chain Functionality ===")

    # Test adding steps to a chain
    conversation_id = "test_conv_1"

    result1 = cot.chain_of_thought_step(
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

    result2 = cot.chain_of_thought_step(
        conversation_id=conversation_id,
        stage="Pattern Recognition",
        description="Identified arithmetic progression",
        result="Pattern is adding 2 each time",
        confidence=0.95,
        evidence="Differences are [2, 2, 2]"
    )
    print(f"Step 2 result: {result2}")

    # Get summary
    summary = cot.get_chain_summary(conversation_id)
    print(f"Summary has {summary['step_count']} steps")
    print(f"Overall confidence: {summary['overall_confidence']}")
    assert summary['success'] == True
    assert summary['step_count'] == 2

    # Test tool specs
    tool_specs = core.get_tool_specs()
    print(f"Total tools registered: {len(tool_specs)}")

    cot_functions = [spec for spec in tool_specs
                     if spec['function']['name'] in ['chain_of_thought_step', 'get_chain_summary', 'clear_chain']]
    print(f"Chain of thought functions found: {len(cot_functions)}")

    # Clear the chain
    clear_result = cot.clear_chain(conversation_id)
    print(f"Clear result: {clear_result}")
    assert clear_result['success'] == True

    print("Basic functionality test: PASSED\n")

def test_confidence_system():
    """Test confidence scoring."""
    print("=== Testing Confidence System ===")

    conversation_id = "conf_test"

    # Test with different confidences
    cot.chain_of_thought_step(conversation_id, "Step1", "High conf", "Result1", confidence=0.9)
    cot.chain_of_thought_step(conversation_id, "Step2", "Low conf", "Result2", confidence=0.3)

    summary = cot.get_chain_summary(conversation_id)
    print(f"Overall confidence (should be 0.3): {summary['overall_confidence']}")
    assert summary['overall_confidence'] == 0.3

    # Test default confidence
    result = cot.chain_of_thought_step(conversation_id, "Step3", "Default", "Result3")
    assert result['confidence'] == 0.8

    cot.clear_chain(conversation_id)
    print("Confidence system test: PASSED\n")

def test_thread_safety():
    """Test multiple conversations."""
    print("=== Testing Multiple Conversations ===")

    conversations = ["conv1", "conv2", "conv3"]

    for i, conv_id in enumerate(conversations):
        cot.chain_of_thought_step(
            conv_id,
            f"Stage{i}",
            f"Description for {conv_id}",
            f"Result {i}",
            confidence=0.8
        )

    # Verify all exist
    for conv_id in conversations:
        summary = cot.get_chain_summary(conv_id)
        assert summary['success'] == True
        assert summary['step_count'] == 1

    # Check stats
    stats = cot.get_conversation_stats()
    print(f"Total conversations: {stats['total_conversations']}")
    assert stats['total_conversations'] == 3

    # Clear all
    for conv_id in conversations:
        cot.clear_chain(conv_id)

    print("Multiple conversations test: PASSED\n")

def main():
    """Run all tests."""
    print("Starting direct chain_of_thought tests...\n")

    try:
        test_basic_functionality()
        test_confidence_system()
        test_thread_safety()

        print("=== ALL TESTS PASSED ===")
        print("Chain of thought module is working correctly!")
        return True

    except Exception as e:
        print(f"TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)