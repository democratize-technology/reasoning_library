#!/usr/bin/env python3
"""
Comprehensive test suite for chain_of_thought.py module.

Tests thread-safe conversation management, confidence scoring,
validation, and concurrent access patterns.
"""
import os
import sys
import threading
import time
from unittest.mock import patch

import pytest

from reasoning_library.chain_of_thought import (
    _MAX_CONVERSATIONS,
    _conversations,
    _conversations_lock,
    _evict_oldest_conversations_if_needed,
    _get_or_create_conversation,
    _validate_conversation_id,
    chain_of_thought_step,
    clear_chain,
    get_active_conversations,
    get_chain_summary,
    get_conversation_stats,
)
from reasoning_library.core import ReasoningChain, ReasoningStep


class TestConversationIdValidation:
    """Test conversation ID validation and security."""

    def test_valid_conversation_ids(self):
        """Test valid conversation ID formats."""
        valid_ids = [
            "conv1",
            "conversation_123",
            "user-session-456",
            "a",
            "A1b2C3d4",
            "test_conv_2024",
            "session-uuid-1234567890123456789012345678901234567890123456789012"[:64],
        ]

        for conv_id in valid_ids:
            try:
                result = _validate_conversation_id(conv_id)
                assert result == conv_id
            except ValueError as e:
                pytest.fail(f"Valid conversation ID '{conv_id}' was rejected: {e}")

    def test_invalid_conversation_ids(self):
        """Test invalid conversation ID formats are rejected."""
        invalid_ids = [
            "",  # Empty string
            "conv with spaces",  # Spaces
            "conv@mail.com",  # Special characters
            "conv/path",  # Slash
            "conv\\backslash",  # Backslash
            "conv;semicolon",  # Semicolon
            "conv<script>",  # HTML tags
            "a" * 65,  # Too long (over 64 chars)
            123,  # Not a string
            None,  # None
            "conv\n",  # Newline
            "conv\t",  # Tab
            "conv.dot",  # Dot
            "conv#hash",  # Hash
        ]

        for conv_id in invalid_ids:
            with pytest.raises(
                ValueError,
                match="Invalid conversation_id format|conversation_id must be a string",
            ):
                _validate_conversation_id(conv_id)

    def test_conversation_id_injection_protection(self):
        """Test protection against injection attacks."""
        malicious_ids = [
            "../../../etc/passwd",
            "$(rm -rf /)",
            "<script>alert('xss')</script>",
            "'; DROP TABLE conversations; --",
            "conv && rm -rf /",
            "conv | cat /etc/passwd",
            "conv`whoami`",
        ]

        for malicious_id in malicious_ids:
            with pytest.raises(ValueError):
                _validate_conversation_id(malicious_id)


class TestChainOfThoughtStep:
    """Test chain_of_thought_step function."""

    def setup_method(self):
        """Clear conversations before each test."""
        with _conversations_lock:
            _conversations.clear()

    def test_basic_step_creation(self):
        """Test basic step creation."""
        result = chain_of_thought_step(
            conversation_id="test_conv",
            stage="Analysis",
            description="Initial analysis",
            result="analysis complete",
        )

        assert result["success"] == True
        assert result["step_number"] == 1
        assert result["conversation_id"] == "test_conv"
        assert result["confidence"] == 0.8  # Default confidence

        # Check that conversation was created
        with _conversations_lock:
            assert "test_conv" in _conversations
            chain = _conversations["test_conv"]
            assert len(chain.steps) == 1
            assert chain.steps[0].stage == "Analysis"
            assert chain.steps[0].description == "Initial analysis"
            assert chain.steps[0].result == "analysis complete"

    def test_step_with_custom_confidence(self):
        """Test step creation with custom confidence."""
        result = chain_of_thought_step(
            conversation_id="test_conv",
            stage="Analysis",
            description="High confidence analysis",
            result="confident result",
            confidence=0.95,
        )

        assert result["success"] == True
        assert result["confidence"] == 0.95

        with _conversations_lock:
            chain = _conversations["test_conv"]
            assert chain.steps[0].confidence == 0.95

    def test_step_with_all_optional_fields(self):
        """Test step creation with all optional fields."""
        assumptions = ["assumption1", "assumption2"]
        metadata = {"source": "test", "version": 1}

        result = chain_of_thought_step(
            conversation_id="test_conv",
            stage="Synthesis",
            description="Complex step",
            result={"complex": "result"},
            confidence=0.75,
            evidence="Strong supporting evidence",
            assumptions=assumptions,
            metadata=metadata,
        )

        assert result["success"] == True

        with _conversations_lock:
            chain = _conversations["test_conv"]
            step = chain.steps[0]
            assert step.confidence == 0.75
            assert step.evidence == "Strong supporting evidence"
            assert step.assumptions == assumptions
            assert step.metadata == metadata

    def test_confidence_clamping(self):
        """Test that confidence values are clamped to [0.0, 1.0]."""
        # Test above 1.0
        result = chain_of_thought_step(
            conversation_id="test_conv",
            stage="Analysis",
            description="Over-confident step",
            result="result",
            confidence=1.5,
        )

        assert result["confidence"] == 1.0

        # Test below 0.0
        result = chain_of_thought_step(
            conversation_id="test_conv_2",
            stage="Analysis",
            description="Under-confident step",
            result="result",
            confidence=-0.5,
        )

        assert result["confidence"] == 0.0

    def test_multiple_steps_same_conversation(self):
        """Test adding multiple steps to the same conversation."""
        conv_id = "multi_step_conv"

        # Add first step
        result1 = chain_of_thought_step(
            conversation_id=conv_id,
            stage="Analysis",
            description="Step 1",
            result="result1",
        )

        # Add second step
        result2 = chain_of_thought_step(
            conversation_id=conv_id,
            stage="Synthesis",
            description="Step 2",
            result="result2",
        )

        assert result1["step_number"] == 1
        assert result2["step_number"] == 2

        with _conversations_lock:
            chain = _conversations[conv_id]
            assert len(chain.steps) == 2
            assert chain.steps[0].description == "Step 1"
            assert chain.steps[1].description == "Step 2"

    def test_invalid_conversation_id_handling(self):
        """Test handling of invalid conversation IDs."""
        result = chain_of_thought_step(
            conversation_id="invalid id with spaces",
            stage="Analysis",
            description="This should fail",
            result="should not work",
        )

        assert result["success"] == False
        assert result["step_number"] == -1
        assert "error" in result
        assert "Invalid conversation_id format" in result["error"]


class TestGetChainSummary:
    """Test get_chain_summary function."""

    def setup_method(self):
        """Clear conversations before each test."""
        with _conversations_lock:
            _conversations.clear()

    def test_summary_of_existing_conversation(self):
        """Test getting summary of existing conversation."""
        conv_id = "summary_test"

        # Add some steps
        chain_of_thought_step(conv_id, "Analysis", "Step 1", "result1", confidence=0.9)
        chain_of_thought_step(conv_id, "Synthesis", "Step 2", "result2", confidence=0.8)
        chain_of_thought_step(
            conv_id, "Conclusion", "Step 3", "result3", confidence=0.95
        )

        result = get_chain_summary(conv_id)

        assert result["success"] == True
        assert result["conversation_id"] == conv_id
        assert result["step_count"] == 3
        assert result["overall_confidence"] == 0.8  # Minimum of all confidences

        summary = result["summary"]
        assert "Reasoning Chain Summary:" in summary
        assert "Step 1 (Analysis): Step 1" in summary
        assert "Step 2 (Synthesis): Step 2" in summary
        assert "Step 3 (Conclusion): Step 3" in summary

    def test_summary_nonexistent_conversation(self):
        """Test getting summary of non-existent conversation."""
        result = get_chain_summary("nonexistent_conv")

        assert result["success"] == False
        assert result["step_count"] == 0
        assert result["overall_confidence"] == 0.0
        assert "No reasoning chain found" in result["summary"]

    def test_summary_empty_conversation(self):
        """Test getting summary of conversation with no steps."""
        conv_id = "empty_conv"

        # Create conversation but don't add steps
        with _conversations_lock:
            _conversations[conv_id] = ReasoningChain()

        result = get_chain_summary(conv_id)

        assert result["success"] == True
        assert result["step_count"] == 0
        assert result["overall_confidence"] == 0.0  # No steps means no confidence

    def test_overall_confidence_calculation(self):
        """Test overall confidence calculation methods."""
        conv_id = "confidence_test"

        # Test with different confidence values
        chain_of_thought_step(conv_id, "Stage1", "Step 1", "result1", confidence=0.9)
        chain_of_thought_step(conv_id, "Stage2", "Step 2", "result2", confidence=0.7)
        chain_of_thought_step(conv_id, "Stage3", "Step 3", "result3", confidence=0.85)

        result = get_chain_summary(conv_id)
        assert result["overall_confidence"] == 0.7  # Minimum (conservative approach)

    def test_confidence_with_none_values(self):
        """Test confidence calculation when some steps have None confidence."""
        conv_id = "mixed_confidence_test"

        # Add steps with mixed confidence values
        chain_of_thought_step(conv_id, "Stage1", "Step 1", "result1", confidence=0.9)
        chain_of_thought_step(conv_id, "Stage2", "Step 2", "result2", confidence=None)
        chain_of_thought_step(conv_id, "Stage3", "Step 3", "result3", confidence=0.8)

        result = get_chain_summary(conv_id)

        # Should only consider non-None confidences
        assert result["overall_confidence"] == 0.8  # Min of 0.9 and 0.8

    def test_invalid_conversation_id_in_summary(self):
        """Test summary with invalid conversation ID."""
        result = get_chain_summary("invalid id with spaces")

        assert result["success"] == False
        assert "Invalid conversation ID" in result["summary"]
        assert "error" in result


class TestClearChain:
    """Test clear_chain function."""

    def setup_method(self):
        """Clear conversations before each test."""
        with _conversations_lock:
            _conversations.clear()

    def test_clear_existing_conversation(self):
        """Test clearing an existing conversation."""
        conv_id = "clear_test"

        # Add some steps
        chain_of_thought_step(conv_id, "Analysis", "Step 1", "result1")
        chain_of_thought_step(conv_id, "Synthesis", "Step 2", "result2")

        # Verify conversation exists
        with _conversations_lock:
            assert conv_id in _conversations
            assert len(_conversations[conv_id].steps) == 2

        # Clear the conversation
        result = clear_chain(conv_id)

        assert result["success"] == True
        assert result["conversation_id"] == conv_id
        assert result["steps_removed"] == 2
        assert "Cleared reasoning chain" in result["message"]

        # Verify conversation is removed
        with _conversations_lock:
            assert conv_id not in _conversations

    def test_clear_nonexistent_conversation(self):
        """Test clearing a non-existent conversation."""
        result = clear_chain("nonexistent_conv")

        assert result["success"] == False
        assert result["steps_removed"] == 0
        assert "No reasoning chain found" in result["message"]

    def test_clear_with_invalid_conversation_id(self):
        """Test clearing with invalid conversation ID."""
        result = clear_chain("invalid id with spaces")

        assert result["success"] == False
        assert result["steps_removed"] == 0
        assert "Invalid conversation ID" in result["message"]
        assert "error" in result


class TestThreadSafety:
    """Test thread safety of conversation management."""

    def setup_method(self):
        """Clear conversations before each test."""
        with _conversations_lock:
            _conversations.clear()

    def test_concurrent_step_addition(self):
        """Test concurrent addition of steps to different conversations."""
        num_threads = 10
        steps_per_thread = 20
        results = []
        errors = []

        def add_steps(thread_id):
            conv_id = f"thread_{thread_id}"
            try:
                for i in range(steps_per_thread):
                    result = chain_of_thought_step(
                        conversation_id=conv_id,
                        stage=f"Stage_{i}",
                        description=f"Step {i} from thread {thread_id}",
                        result=f"result_{thread_id}_{i}",
                    )
                    results.append(result)
                    time.sleep(0.001)  # Small delay to encourage race conditions
            except Exception as e:
                errors.append(e)

        # Start threads
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=add_steps, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == num_threads * steps_per_thread

        # Check that all conversations were created correctly
        with _conversations_lock:
            assert len(_conversations) == num_threads
            for i in range(num_threads):
                conv_id = f"thread_{i}"
                assert conv_id in _conversations
                assert len(_conversations[conv_id].steps) == steps_per_thread

    def test_concurrent_same_conversation_access(self):
        """Test concurrent access to the same conversation."""
        conv_id = "shared_conversation"
        num_threads = 5
        steps_per_thread = 10
        results = []
        errors = []

        def add_steps(thread_id):
            try:
                for i in range(steps_per_thread):
                    result = chain_of_thought_step(
                        conversation_id=conv_id,
                        stage=f"Thread{thread_id}",
                        description=f"Step {i} from thread {thread_id}",
                        result=f"result_{thread_id}_{i}",
                    )
                    results.append(result["step_number"])
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)

        # Start threads
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=add_steps, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == num_threads * steps_per_thread

        # Check that all step numbers are unique and sequential
        assert len(set(results)) == len(results), "Step numbers should be unique"
        assert min(results) == 1
        assert max(results) == num_threads * steps_per_thread

        # Check conversation state
        with _conversations_lock:
            assert len(_conversations[conv_id].steps) == num_threads * steps_per_thread

    def test_concurrent_clear_and_add(self):
        """Test concurrent clear and add operations."""
        conv_id = "concurrent_test"
        errors = []

        def add_steps():
            try:
                for i in range(10):
                    chain_of_thought_step(
                        conversation_id=conv_id,
                        stage="Addition",
                        description=f"Adding step {i}",
                        result=f"result_{i}",
                    )
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)

        def clear_conversation():
            try:
                time.sleep(0.005)  # Wait a bit before clearing
                clear_chain(conv_id)
            except Exception as e:
                errors.append(e)

        # Start threads
        add_thread = threading.Thread(target=add_steps)
        clear_thread = threading.Thread(target=clear_conversation)

        add_thread.start()
        clear_thread.start()

        add_thread.join()
        clear_thread.join()

        # Should not have any errors (operations should be thread-safe)
        assert len(errors) == 0, f"Errors occurred: {errors}"


class TestMemoryManagement:
    """Test memory management and conversation limits."""

    def setup_method(self):
        """Clear conversations before each test."""
        with _conversations_lock:
            _conversations.clear()

    def test_conversation_eviction_when_limit_reached(self):
        """Test that old conversations are evicted when limit is reached."""
        # Mock the limit to a small number for testing
        import reasoning_library.chain_of_thought as cot_module

        original_limit = cot_module._MAX_CONVERSATIONS

        try:
            # Temporarily set a small limit
            cot_module._MAX_CONVERSATIONS = 3

            # Add conversations up to the limit
            for i in range(3):
                chain_of_thought_step(
                    f"conv_{i}", "Stage", "Description", f"result_{i}"
                )

            with _conversations_lock:
                assert len(_conversations) == 3
                assert "conv_0" in _conversations
                assert "conv_1" in _conversations
                assert "conv_2" in _conversations

            # Add one more conversation (should evict the oldest)
            chain_of_thought_step("conv_3", "Stage", "Description", "result_3")

            with _conversations_lock:
                assert len(_conversations) == 3
                assert "conv_0" not in _conversations  # Oldest should be evicted
                assert "conv_1" in _conversations
                assert "conv_2" in _conversations
                assert "conv_3" in _conversations

        finally:
            # Restore original limit
            cot_module._MAX_CONVERSATIONS = original_limit

    def test_lru_behavior(self):
        """Test LRU (Least Recently Used) behavior."""
        # Add multiple conversations
        chain_of_thought_step("conv_1", "Stage", "Description", "result_1")
        chain_of_thought_step("conv_2", "Stage", "Description", "result_2")
        chain_of_thought_step("conv_3", "Stage", "Description", "result_3")

        # Access conv_1 to make it recently used
        get_chain_summary("conv_1")

        # Add another step to conv_2
        chain_of_thought_step("conv_2", "Stage", "Description", "result_2_2")

        with _conversations_lock:
            # Check that conversations are ordered by recent access
            conversation_keys = list(_conversations.keys())
            # Most recently accessed should be at the end
            assert conversation_keys[-1] == "conv_2"  # Most recent (step added)


class TestUtilityFunctions:
    """Test utility functions for monitoring and debugging."""

    def setup_method(self):
        """Clear conversations before each test."""
        with _conversations_lock:
            _conversations.clear()

    def test_get_active_conversations(self):
        """Test get_active_conversations utility function."""
        # Initially should be empty
        assert get_active_conversations() == []

        # Add some conversations
        chain_of_thought_step("conv_1", "Stage", "Description", "result_1")
        chain_of_thought_step("conv_2", "Stage", "Description", "result_2")

        active_convs = get_active_conversations()
        assert len(active_convs) == 2
        assert "conv_1" in active_convs
        assert "conv_2" in active_convs

    def test_get_conversation_stats(self):
        """Test get_conversation_stats utility function."""
        # Add conversations with different characteristics
        chain_of_thought_step("conv_1", "Stage", "Step 1", "result_1", confidence=0.9)
        chain_of_thought_step("conv_1", "Stage", "Step 2", "result_2", confidence=0.8)

        chain_of_thought_step(
            "conv_2", "Stage", "Single step", "result", confidence=0.95
        )

        stats = get_conversation_stats()

        assert stats["total_conversations"] == 2
        assert "conv_1" in stats["conversation_details"]
        assert "conv_2" in stats["conversation_details"]

        conv_1_stats = stats["conversation_details"]["conv_1"]
        assert conv_1_stats["step_count"] == 2
        assert conv_1_stats["overall_confidence"] == 0.8  # Minimum
        assert conv_1_stats["last_result"] == "result_2"

        conv_2_stats = stats["conversation_details"]["conv_2"]
        assert conv_2_stats["step_count"] == 1
        assert conv_2_stats["overall_confidence"] == 0.95
        assert conv_2_stats["last_result"] == "result"


def run_all_tests():
    """Run all chain of thought tests with detailed output."""
    print("🧪 Running comprehensive test suite for chain_of_thought.py...")

    test_classes = [
        TestConversationIdValidation,
        TestChainOfThoughtStep,
        TestGetChainSummary,
        TestClearChain,
        TestThreadSafety,
        TestMemoryManagement,
        TestUtilityFunctions,
    ]

    total_tests = 0
    passed_tests = 0
    failed_tests = []

    for test_class in test_classes:
        print(f"\n📝 Testing {test_class.__name__}...")

        test_methods = [
            method for method in dir(test_class) if method.startswith("test_")
        ]

        for method_name in test_methods:
            total_tests += 1
            try:
                instance = test_class()
                if hasattr(instance, "setup_method"):
                    instance.setup_method()

                method = getattr(instance, method_name)
                method()

                passed_tests += 1
                print(f"  ✅ {method_name}")

            except Exception as e:
                failed_tests.append(f"{test_class.__name__}.{method_name}: {str(e)}")
                print(f"  ❌ {method_name}: {str(e)}")

    print(f"\n📊 Test Summary:")
    print(f"  Total tests: {total_tests}")
    print(f"  Passed: {passed_tests}")
    print(f"  Failed: {len(failed_tests)}")

    if failed_tests:
        print(f"\n❌ Failed tests:")
        for failure in failed_tests:
            print(f"  - {failure}")
        return False
    else:
        print(f"\n🎉 All chain of thought tests passed!")
        return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
