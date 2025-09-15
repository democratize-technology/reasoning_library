"""
Comprehensive Test Suite for Chain-of-Thought Confidence Propagation.

This module tests the mathematical correctness of confidence scoring in chain-of-thought reasoning,
ensuring that:
1. Overall confidence = min(all_step_confidences) (conservative approach)
2. Thread safety for concurrent conversation management
3. Proper confidence bounds and validation
4. Memory management and conversation isolation
5. Edge cases in confidence aggregation
"""

import pytest
import threading
import time
import concurrent.futures
from typing import List, Dict, Any
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from reasoning_library.chain_of_thought import (
        chain_of_thought_step,
        get_chain_summary,
        clear_chain,
        get_active_conversations,
        get_conversation_stats,
        _validate_conversation_id,
        _get_or_create_conversation,
        _conversations,
        _conversations_lock
    )
    from reasoning_library.core import ReasoningChain
except ImportError:
    # Fallback for direct execution
    from chain_of_thought import (
        chain_of_thought_step,
        get_chain_summary,
        clear_chain,
        get_active_conversations,
        get_conversation_stats,
        _validate_conversation_id,
        _get_or_create_conversation,
        _conversations,
        _conversations_lock
    )
    from core import ReasoningChain


class TestChainOfThoughtConfidencePropagation:
    """Test confidence propagation in chain-of-thought reasoning."""

    def setup_method(self):
        """Clean up conversations before each test."""
        with _conversations_lock:
            _conversations.clear()

    def teardown_method(self):
        """Clean up conversations after each test."""
        with _conversations_lock:
            _conversations.clear()

    def test_single_step_confidence(self):
        """Test confidence scoring for a single reasoning step."""
        conversation_id = "test_single_step"

        # Add a single step with specific confidence
        result = chain_of_thought_step(
            conversation_id=conversation_id,
            stage="Analysis",
            description="Test single step reasoning",
            result="Test result",
            confidence=0.8
        )

        assert result["success"] is True
        assert result["confidence"] == 0.8
        assert result["step_number"] == 1

        # Get chain summary and verify overall confidence
        summary_result = get_chain_summary(conversation_id)
        assert summary_result["success"] is True
        assert summary_result["overall_confidence"] == 0.8
        assert summary_result["step_count"] == 1

    def test_minimum_confidence_aggregation(self):
        """Test that overall confidence equals minimum of all step confidences."""
        conversation_id = "test_min_confidence"

        # Add multiple steps with different confidence levels
        confidence_values = [0.9, 0.7, 0.85, 0.6, 0.95]

        for i, confidence in enumerate(confidence_values):
            chain_of_thought_step(
                conversation_id=conversation_id,
                stage=f"Step_{i+1}",
                description=f"Test step {i+1}",
                result=f"Result {i+1}",
                confidence=confidence
            )

        # Overall confidence should equal the minimum
        summary_result = get_chain_summary(conversation_id)
        expected_min_confidence = min(confidence_values)

        assert summary_result["success"] is True
        assert summary_result["overall_confidence"] == expected_min_confidence
        assert summary_result["step_count"] == len(confidence_values)

    def test_default_confidence_application(self):
        """Test that default confidence (0.8) is applied when not specified."""
        conversation_id = "test_default_confidence"

        # Add step without specifying confidence
        result = chain_of_thought_step(
            conversation_id=conversation_id,
            stage="Analysis",
            description="Test step without explicit confidence",
            result="Test result"
        )

        assert result["success"] is True
        assert result["confidence"] == 0.8  # Default confidence

        summary_result = get_chain_summary(conversation_id)
        assert summary_result["overall_confidence"] == 0.8

    def test_confidence_bounds_enforcement(self):
        """Test that confidence values are clamped to valid bounds [0.0, 1.0]."""
        conversation_id = "test_confidence_bounds"

        # Test values outside bounds
        test_cases = [
            (-0.5, 0.0),   # Below minimum
            (1.5, 1.0),    # Above maximum
            (-10, 0.0),    # Far below minimum
            (5.0, 1.0),    # Far above maximum
            (0.0, 0.0),    # At minimum boundary
            (1.0, 1.0),    # At maximum boundary
        ]

        for input_confidence, expected_confidence in test_cases:
            clear_chain(conversation_id)  # Clear previous steps

            result = chain_of_thought_step(
                conversation_id=conversation_id,
                stage="Bounds_Test",
                description=f"Testing confidence bounds with input {input_confidence}",
                result="Test result",
                confidence=input_confidence
            )

            assert result["success"] is True
            assert result["confidence"] == expected_confidence

            summary_result = get_chain_summary(conversation_id)
            assert summary_result["overall_confidence"] == expected_confidence

    def test_mixed_confidence_scenarios(self):
        """Test various combinations of confidence values."""
        test_scenarios = [
            {
                "name": "all_high_confidence",
                "confidences": [0.9, 0.95, 0.85, 0.92],
                "expected_min": 0.85
            },
            {
                "name": "all_low_confidence",
                "confidences": [0.3, 0.25, 0.4, 0.35],
                "expected_min": 0.25
            },
            {
                "name": "mixed_with_zero",
                "confidences": [0.8, 0.0, 0.9, 0.7],
                "expected_min": 0.0
            },
            {
                "name": "mixed_with_perfect",
                "confidences": [0.8, 1.0, 0.6, 0.9],
                "expected_min": 0.6
            },
            {
                "name": "decreasing_confidence",
                "confidences": [1.0, 0.8, 0.6, 0.4, 0.2],
                "expected_min": 0.2
            }
        ]

        for scenario in test_scenarios:
            conversation_id = f"test_{scenario['name']}"

            # Add steps with specified confidence values
            for i, confidence in enumerate(scenario["confidences"]):
                chain_of_thought_step(
                    conversation_id=conversation_id,
                    stage=f"Step_{i+1}",
                    description=f"Step {i+1} for {scenario['name']}",
                    result=f"Result {i+1}",
                    confidence=confidence
                )

            # Verify minimum confidence calculation
            summary_result = get_chain_summary(conversation_id)
            assert summary_result["success"] is True
            assert summary_result["overall_confidence"] == scenario["expected_min"]

    def test_empty_chain_confidence(self):
        """Test confidence behavior for empty reasoning chains."""
        conversation_id = "test_empty_chain"

        # Try to get summary of non-existent conversation
        summary_result = get_chain_summary(conversation_id)
        assert summary_result["success"] is False
        assert summary_result["overall_confidence"] == 0.0
        assert summary_result["step_count"] == 0

    def test_confidence_with_none_values(self):
        """Test behavior when some steps have None confidence."""
        conversation_id = "test_none_confidence"

        # Add steps with mix of explicit and None confidence values
        steps = [
            {"confidence": 0.8, "description": "Step with explicit confidence"},
            {"confidence": None, "description": "Step with None confidence"},
            {"confidence": 0.6, "description": "Another step with explicit confidence"},
        ]

        for i, step_data in enumerate(steps):
            chain_of_thought_step(
                conversation_id=conversation_id,
                stage=f"Step_{i+1}",
                description=step_data["description"],
                result=f"Result {i+1}",
                confidence=step_data["confidence"]
            )

        # When None confidence is passed, it should default to 0.8
        summary_result = get_chain_summary(conversation_id)
        assert summary_result["success"] is True
        # Minimum of [0.8, 0.8, 0.6] should be 0.6
        assert summary_result["overall_confidence"] == 0.6


class TestThreadSafetyAndConcurrency:
    """Test thread safety and concurrent access to chain-of-thought functionality."""

    def setup_method(self):
        """Clean up conversations before each test."""
        with _conversations_lock:
            _conversations.clear()

    def teardown_method(self):
        """Clean up conversations after each test."""
        with _conversations_lock:
            _conversations.clear()

    def test_concurrent_conversation_access(self):
        """Test concurrent access to different conversations."""
        num_conversations = 10
        steps_per_conversation = 5

        def create_conversation_steps(conv_id: int) -> List[float]:
            """Create steps for a single conversation and return confidence values."""
            conversation_id = f"concurrent_test_{conv_id}"
            confidence_values = []

            for step_num in range(steps_per_conversation):
                confidence = 0.5 + (step_num * 0.1)  # Varying confidence: 0.5, 0.6, 0.7, 0.8, 0.9
                confidence_values.append(confidence)

                result = chain_of_thought_step(
                    conversation_id=conversation_id,
                    stage=f"Step_{step_num+1}",
                    description=f"Concurrent step {step_num+1} for conversation {conv_id}",
                    result=f"Result {step_num+1}",
                    confidence=confidence
                )

                assert result["success"] is True

                # Small delay to encourage race conditions
                time.sleep(0.001)

            return confidence_values

        # Execute concurrent conversations
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_conversations) as executor:
            futures = [executor.submit(create_conversation_steps, i) for i in range(num_conversations)]
            confidence_results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # Verify all conversations were created correctly
        assert len(confidence_results) == num_conversations

        # Verify each conversation has correct confidence aggregation
        for conv_id in range(num_conversations):
            conversation_id = f"concurrent_test_{conv_id}"
            summary_result = get_chain_summary(conversation_id)

            assert summary_result["success"] is True
            assert summary_result["step_count"] == steps_per_conversation

            # Expected minimum confidence for this conversation
            expected_min = 0.5  # First step has confidence 0.5
            assert summary_result["overall_confidence"] == expected_min

    def test_concurrent_same_conversation_access(self):
        """Test concurrent access to the same conversation (stress test)."""
        conversation_id = "stress_test_conversation"
        num_threads = 20
        steps_per_thread = 5

        def add_steps_to_conversation(thread_id: int) -> List[Dict[str, Any]]:
            """Add steps to the same conversation from multiple threads."""
            results = []

            for step_num in range(steps_per_thread):
                confidence = 0.3 + (thread_id * 0.01) + (step_num * 0.01)  # Unique confidence per thread/step

                result = chain_of_thought_step(
                    conversation_id=conversation_id,
                    stage=f"Thread_{thread_id}_Step_{step_num+1}",
                    description=f"Step {step_num+1} from thread {thread_id}",
                    result=f"Thread {thread_id} Result {step_num+1}",
                    confidence=confidence
                )

                results.append(result)

                # Small delay to encourage race conditions
                time.sleep(0.001)

            return results

        # Execute concurrent access to same conversation
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(add_steps_to_conversation, i) for i in range(num_threads)]
            thread_results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # Verify all operations succeeded
        total_expected_steps = num_threads * steps_per_thread
        successful_operations = sum(len(results) for results in thread_results)
        assert successful_operations == total_expected_steps

        # Verify conversation state
        summary_result = get_chain_summary(conversation_id)
        assert summary_result["success"] is True
        assert summary_result["step_count"] == total_expected_steps

        # Overall confidence should be the minimum of all added steps
        assert 0.0 <= summary_result["overall_confidence"] <= 1.0

    def test_conversation_isolation(self):
        """Test that conversations are properly isolated from each other."""
        conversations = {
            "conversation_A": [0.9, 0.8, 0.7],
            "conversation_B": [0.6, 0.5, 0.4],
            "conversation_C": [1.0, 0.95, 0.85]
        }

        # Create conversations with different confidence patterns
        for conv_id, confidences in conversations.items():
            for i, confidence in enumerate(confidences):
                chain_of_thought_step(
                    conversation_id=conv_id,
                    stage=f"Step_{i+1}",
                    description=f"Step {i+1} for {conv_id}",
                    result=f"Result {i+1}",
                    confidence=confidence
                )

        # Verify each conversation maintains its own confidence calculation
        for conv_id, confidences in conversations.items():
            summary_result = get_chain_summary(conv_id)
            expected_min = min(confidences)

            assert summary_result["success"] is True
            assert summary_result["overall_confidence"] == expected_min
            assert summary_result["step_count"] == len(confidences)

        # Verify conversations don't interfere with each other
        assert len(get_active_conversations()) == len(conversations)


class TestMemoryManagementAndEdgeCases:
    """Test memory management and edge cases in chain-of-thought reasoning."""

    def setup_method(self):
        """Clean up conversations before each test."""
        with _conversations_lock:
            _conversations.clear()

    def teardown_method(self):
        """Clean up conversations after each test."""
        with _conversations_lock:
            _conversations.clear()

    def test_conversation_id_validation(self):
        """Test conversation ID validation for security."""
        invalid_ids = [
            "",                           # Empty string
            "a" * 65,                    # Too long (>64 characters)
            "test@conversation",         # Invalid character @
            "test conversation",         # Space not allowed
            "test.conversation",         # Dot not allowed
            "test/conversation",         # Slash not allowed
            "../conversation",           # Path traversal attempt
            "test\nconversation",        # Newline not allowed
            123,                         # Not a string
            None,                        # None value
        ]

        for invalid_id in invalid_ids:
            result = chain_of_thought_step(
                conversation_id=invalid_id,
                stage="Test",
                description="Test invalid ID",
                result="Test result",
                confidence=0.8
            )

            assert result["success"] is False
            assert "error" in result
            assert result["step_number"] == -1

    def test_conversation_memory_bounds(self):
        """Test conversation memory management and bounds checking."""
        # This test verifies that the system handles memory limits appropriately
        # Note: The actual limit is 1000 conversations as defined in the module

        # Create many conversations to test memory management
        base_conversation_count = 50  # Reasonable number for testing

        for i in range(base_conversation_count):
            conversation_id = f"memory_test_{i:04d}"
            chain_of_thought_step(
                conversation_id=conversation_id,
                stage="Memory_Test",
                description=f"Memory test step for conversation {i}",
                result=f"Result {i}",
                confidence=0.8
            )

        # Verify conversations were created
        active_conversations = get_active_conversations()
        assert len(active_conversations) == base_conversation_count

        # Test that conversation stats work correctly
        stats = get_conversation_stats()
        assert stats["total_conversations"] == base_conversation_count
        assert len(stats["conversation_details"]) == base_conversation_count

    def test_clear_chain_functionality(self):
        """Test chain clearing functionality and its impact on confidence."""
        conversation_id = "test_clear_chain"

        # Add some steps
        confidences = [0.9, 0.7, 0.8]
        for i, confidence in enumerate(confidences):
            chain_of_thought_step(
                conversation_id=conversation_id,
                stage=f"Step_{i+1}",
                description=f"Step {i+1} before clearing",
                result=f"Result {i+1}",
                confidence=confidence
            )

        # Verify chain exists
        summary_before = get_chain_summary(conversation_id)
        assert summary_before["success"] is True
        assert summary_before["step_count"] == len(confidences)

        # Clear the chain
        clear_result = clear_chain(conversation_id)
        assert clear_result["success"] is True
        assert clear_result["steps_removed"] == len(confidences)

        # Verify chain is cleared
        summary_after = get_chain_summary(conversation_id)
        assert summary_after["success"] is False
        assert summary_after["step_count"] == 0
        assert summary_after["overall_confidence"] == 0.0

    def test_edge_case_confidence_calculations(self):
        """Test edge cases in confidence calculations."""
        conversation_id = "test_edge_cases"

        # Test with very small confidence differences
        tiny_differences = [0.7000001, 0.7000002, 0.7000000]
        for i, confidence in enumerate(tiny_differences):
            chain_of_thought_step(
                conversation_id=conversation_id,
                stage=f"Tiny_Diff_{i+1}",
                description=f"Step with tiny confidence difference {i+1}",
                result=f"Result {i+1}",
                confidence=confidence
            )

        summary_result = get_chain_summary(conversation_id)
        expected_min = min(tiny_differences)
        assert abs(summary_result["overall_confidence"] - expected_min) < 1e-10

    def test_conversation_reuse_after_clear(self):
        """Test that conversations can be reused after clearing."""
        conversation_id = "test_reuse_conversation"

        # First use of conversation
        first_confidences = [0.8, 0.6, 0.9]
        for i, confidence in enumerate(first_confidences):
            chain_of_thought_step(
                conversation_id=conversation_id,
                stage=f"First_Use_Step_{i+1}",
                description=f"First use step {i+1}",
                result=f"First result {i+1}",
                confidence=confidence
            )

        first_summary = get_chain_summary(conversation_id)
        assert first_summary["overall_confidence"] == min(first_confidences)

        # Clear conversation
        clear_chain(conversation_id)

        # Second use of conversation with different confidence pattern
        second_confidences = [0.95, 0.85, 0.75]
        for i, confidence in enumerate(second_confidences):
            chain_of_thought_step(
                conversation_id=conversation_id,
                stage=f"Second_Use_Step_{i+1}",
                description=f"Second use step {i+1}",
                result=f"Second result {i+1}",
                confidence=confidence
            )

        second_summary = get_chain_summary(conversation_id)
        assert second_summary["overall_confidence"] == min(second_confidences)
        assert second_summary["step_count"] == len(second_confidences)

        # Verify no interference between uses
        assert first_summary["overall_confidence"] != second_summary["overall_confidence"]


class TestConfidenceAggregationMathematicalProperties:
    """Test mathematical properties of confidence aggregation in chain-of-thought reasoning."""

    def setup_method(self):
        """Clean up conversations before each test."""
        with _conversations_lock:
            _conversations.clear()

    def teardown_method(self):
        """Clean up conversations after each test."""
        with _conversations_lock:
            _conversations.clear()

    def test_minimum_function_properties(self):
        """Test mathematical properties of the minimum function used for confidence aggregation."""
        conversation_id = "test_min_properties"

        # Test cases for minimum function properties
        test_cases = [
            {
                "name": "idempotency",
                "confidences": [0.7, 0.7, 0.7, 0.7],
                "expected": 0.7
            },
            {
                "name": "commutativity",
                "confidences": [0.8, 0.6, 0.9, 0.7],  # Order shouldn't matter
                "expected": 0.6
            },
            {
                "name": "monotonicity",
                "confidences": [0.5, 0.6, 0.7, 0.8, 0.9],
                "expected": 0.5
            },
            {
                "name": "boundary_minimum",
                "confidences": [0.0, 0.8, 0.9, 1.0],
                "expected": 0.0
            },
            {
                "name": "boundary_maximum",
                "confidences": [1.0, 1.0, 1.0],
                "expected": 1.0
            }
        ]

        for test_case in test_cases:
            # Clear conversation for each test case
            clear_chain(conversation_id)

            for i, confidence in enumerate(test_case["confidences"]):
                chain_of_thought_step(
                    conversation_id=conversation_id,
                    stage=f"{test_case['name']}_Step_{i+1}",
                    description=f"Testing {test_case['name']} property",
                    result=f"Result {i+1}",
                    confidence=confidence
                )

            summary_result = get_chain_summary(conversation_id)
            assert summary_result["overall_confidence"] == test_case["expected"]

    def test_confidence_aggregation_with_dynamic_updates(self):
        """Test confidence aggregation as chain grows dynamically."""
        conversation_id = "test_dynamic_updates"

        confidences = [0.9, 0.8, 0.7, 0.6, 0.5]
        expected_minimums = [0.9, 0.8, 0.7, 0.6, 0.5]  # Running minimums

        for i, confidence in enumerate(confidences):
            chain_of_thought_step(
                conversation_id=conversation_id,
                stage=f"Dynamic_Step_{i+1}",
                description=f"Dynamic update step {i+1}",
                result=f"Result {i+1}",
                confidence=confidence
            )

            # Check that overall confidence equals running minimum
            summary_result = get_chain_summary(conversation_id)
            assert summary_result["overall_confidence"] == expected_minimums[i]
            assert summary_result["step_count"] == i + 1

    def test_confidence_precision_and_accuracy(self):
        """Test precision and accuracy of confidence calculations."""
        conversation_id = "test_precision"

        # Test with high precision floating point values
        high_precision_confidences = [
            0.123456789012345,
            0.987654321098765,
            0.555555555555555,
            0.333333333333333
        ]

        for i, confidence in enumerate(high_precision_confidences):
            chain_of_thought_step(
                conversation_id=conversation_id,
                stage=f"Precision_Step_{i+1}",
                description=f"High precision step {i+1}",
                result=f"Result {i+1}",
                confidence=confidence
            )

        summary_result = get_chain_summary(conversation_id)
        expected_min = min(high_precision_confidences)

        # Verify precision is maintained
        assert abs(summary_result["overall_confidence"] - expected_min) < 1e-15

    def test_weakest_link_principle_validation(self):
        """Test that the weakest link principle is correctly implemented."""
        conversation_id = "test_weakest_link"

        # Create a chain where one step has very low confidence
        confidences = [0.99, 0.95, 0.01, 0.98, 0.97]  # One very weak link

        for i, confidence in enumerate(confidences):
            chain_of_thought_step(
                conversation_id=conversation_id,
                stage=f"Link_Step_{i+1}",
                description=f"Chain link {i+1}",
                result=f"Result {i+1}",
                confidence=confidence
            )

        summary_result = get_chain_summary(conversation_id)

        # The overall confidence should be dominated by the weakest link
        assert summary_result["overall_confidence"] == 0.01

        # Verify this makes mathematical sense for chain reliability
        # In a chain, the reliability is determined by the weakest component
        assert summary_result["overall_confidence"] < min(confidences[:-1])  # Less than all but the weakest


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])