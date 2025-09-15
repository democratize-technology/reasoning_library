"""
Comprehensive Test Suite for Deductive Reasoning Confidence Scoring.

This module tests the mathematical correctness of confidence scoring in deductive logic,
ensuring that:
1. Valid logical operations have confidence = 1.0 (deterministic)
2. Invalid logical operations have confidence = 0.0 (failed deduction)
3. Input validation works correctly
4. Edge cases and boundary conditions are handled properly
"""

import pytest
from typing import Any
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from reasoning_library.deductive import (
        logical_not_with_confidence,
        logical_and_with_confidence,
        logical_or_with_confidence,
        implies_with_confidence,
        check_modus_ponens_premises_with_confidence,
        apply_modus_ponens
    )
    from reasoning_library.core import ReasoningChain
except ImportError:
    # Fallback for direct execution
    from deductive import (
        logical_not_with_confidence,
        logical_and_with_confidence,
        logical_or_with_confidence,
        implies_with_confidence,
        check_modus_ponens_premises_with_confidence,
        apply_modus_ponens
    )
    from core import ReasoningChain


class TestLogicalOperationsConfidence:
    """Test confidence scoring for basic logical operations."""

    def test_logical_not_confidence_valid(self):
        """Test logical NOT with valid boolean inputs - should have confidence 1.0."""
        # Test True -> False
        result, confidence = logical_not_with_confidence(True)
        assert result is False
        assert confidence == 1.0, "Logical NOT should have confidence 1.0 for deterministic operation"

        # Test False -> True
        result, confidence = logical_not_with_confidence(False)
        assert result is True
        assert confidence == 1.0, "Logical NOT should have confidence 1.0 for deterministic operation"

    def test_logical_not_invalid_input(self):
        """Test logical NOT with invalid inputs - should raise TypeError."""
        invalid_inputs = [1, 0, "true", "false", None, [], {}]

        for invalid_input in invalid_inputs:
            with pytest.raises(TypeError, match=f"Expected bool for p, got {type(invalid_input).__name__}"):
                logical_not_with_confidence(invalid_input)

    def test_logical_and_confidence_valid(self):
        """Test logical AND with valid boolean inputs - should have confidence 1.0."""
        # Truth table for AND
        test_cases = [
            (True, True, True),    # T ∧ T = T
            (True, False, False),  # T ∧ F = F
            (False, True, False),  # F ∧ T = F
            (False, False, False), # F ∧ F = F
        ]

        for p, q, expected in test_cases:
            result, confidence = logical_and_with_confidence(p, q)
            assert result == expected, f"AND({p}, {q}) should equal {expected}"
            assert confidence == 1.0, "Logical AND should have confidence 1.0 for deterministic operation"

    def test_logical_and_invalid_input(self):
        """Test logical AND with invalid inputs - should raise TypeError."""
        invalid_inputs = [1, 0, "true", "false", None, [], {}]

        # Test invalid first argument
        for invalid_input in invalid_inputs:
            with pytest.raises(TypeError, match=f"Expected bool for p, got {type(invalid_input).__name__}"):
                logical_and_with_confidence(invalid_input, True)

        # Test invalid second argument
        for invalid_input in invalid_inputs:
            with pytest.raises(TypeError, match=f"Expected bool for q, got {type(invalid_input).__name__}"):
                logical_and_with_confidence(True, invalid_input)

    def test_logical_or_confidence_valid(self):
        """Test logical OR with valid boolean inputs - should have confidence 1.0."""
        # Truth table for OR
        test_cases = [
            (True, True, True),    # T ∨ T = T
            (True, False, True),   # T ∨ F = T
            (False, True, True),   # F ∨ T = T
            (False, False, False), # F ∨ F = F
        ]

        for p, q, expected in test_cases:
            result, confidence = logical_or_with_confidence(p, q)
            assert result == expected, f"OR({p}, {q}) should equal {expected}"
            assert confidence == 1.0, "Logical OR should have confidence 1.0 for deterministic operation"

    def test_logical_or_invalid_input(self):
        """Test logical OR with invalid inputs - should raise TypeError."""
        invalid_inputs = [1, 0, "true", "false", None, [], {}]

        # Test invalid first argument
        for invalid_input in invalid_inputs:
            with pytest.raises(TypeError, match=f"Expected bool for p, got {type(invalid_input).__name__}"):
                logical_or_with_confidence(invalid_input, True)

        # Test invalid second argument
        for invalid_input in invalid_inputs:
            with pytest.raises(TypeError, match=f"Expected bool for q, got {type(invalid_input).__name__}"):
                logical_or_with_confidence(True, invalid_input)

    def test_implies_confidence_valid(self):
        """Test logical IMPLIES with valid boolean inputs - should have confidence 1.0."""
        # Truth table for IMPLIES (P -> Q is equivalent to ¬P ∨ Q)
        test_cases = [
            (True, True, True),    # T -> T = T
            (True, False, False),  # T -> F = F
            (False, True, True),   # F -> T = T (vacuously true)
            (False, False, True),  # F -> F = T (vacuously true)
        ]

        for p, q, expected in test_cases:
            result, confidence = implies_with_confidence(p, q)
            assert result == expected, f"IMPLIES({p}, {q}) should equal {expected}"
            assert confidence == 1.0, "Logical IMPLIES should have confidence 1.0 for deterministic operation"

    def test_implies_invalid_input(self):
        """Test logical IMPLIES with invalid inputs - should raise TypeError."""
        invalid_inputs = [1, 0, "true", "false", None, [], {}]

        # Test invalid first argument
        for invalid_input in invalid_inputs:
            with pytest.raises(TypeError, match=f"Expected bool for p, got {type(invalid_input).__name__}"):
                implies_with_confidence(invalid_input, True)

        # Test invalid second argument
        for invalid_input in invalid_inputs:
            with pytest.raises(TypeError, match=f"Expected bool for q, got {type(invalid_input).__name__}"):
                implies_with_confidence(True, invalid_input)


class TestModusPonensConfidence:
    """Test confidence scoring for Modus Ponens reasoning."""

    def test_modus_ponens_premises_confidence_valid(self):
        """Test Modus Ponens premise checking with valid inputs - should have confidence 1.0."""
        # Test cases for premise validation: (P -> Q) ∧ P
        test_cases = [
            (True, True, True),    # (T -> T) ∧ T = T ∧ T = T
            (True, False, False),  # (T -> F) ∧ T = F ∧ T = F
            (False, True, False),  # (F -> T) ∧ F = T ∧ F = F
            (False, False, False), # (F -> F) ∧ F = T ∧ F = F
        ]

        for p, q, expected in test_cases:
            result, confidence = check_modus_ponens_premises_with_confidence(p, q)
            assert result == expected, f"Modus Ponens premises check for P={p}, Q={q} should equal {expected}"
            assert confidence == 1.0, "Modus Ponens premises check should have confidence 1.0 for deterministic operation"

    def test_modus_ponens_premises_invalid_input(self):
        """Test Modus Ponens premises with invalid inputs - should raise TypeError."""
        invalid_inputs = [1, 0, "true", "false", None, [], {}]

        # Test invalid first argument
        for invalid_input in invalid_inputs:
            with pytest.raises(TypeError, match=f"Expected bool for p, got {type(invalid_input).__name__}"):
                check_modus_ponens_premises_with_confidence(invalid_input, True)

        # Test invalid second argument
        for invalid_input in invalid_inputs:
            with pytest.raises(TypeError, match=f"Expected bool for q, got {type(invalid_input).__name__}"):
                check_modus_ponens_premises_with_confidence(True, invalid_input)

    def test_apply_modus_ponens_valid_deduction(self):
        """Test Modus Ponens application with valid deduction - should have confidence 1.0."""
        reasoning_chain = ReasoningChain()

        # Valid Modus Ponens: P is True, (P -> Q) is True, therefore Q is True
        result = apply_modus_ponens(
            p_is_true=True,
            p_implies_q_is_true=True,
            reasoning_chain=reasoning_chain
        )

        assert result is True, "Modus Ponens should deduce True when premises are valid"
        assert len(reasoning_chain.steps) == 1, "Should add exactly one step to reasoning chain"

        step = reasoning_chain.steps[0]
        assert step.confidence == 1.0, "Valid Modus Ponens should have confidence 1.0"
        assert step.result is True, "Step result should be True for valid deduction"
        assert "Concluded Q is True" in step.description, "Description should indicate successful deduction"

    def test_apply_modus_ponens_invalid_deduction_cases(self):
        """Test Modus Ponens application with invalid deductions - should have confidence 0.0."""
        invalid_cases = [
            (False, True),   # P is False, (P -> Q) is True - cannot conclude Q
            (True, False),   # P is True, (P -> Q) is False - contradiction
            (False, False),  # P is False, (P -> Q) is False - cannot conclude Q
        ]

        for p_is_true, p_implies_q_is_true in invalid_cases:
            reasoning_chain = ReasoningChain()

            result = apply_modus_ponens(
                p_is_true=p_is_true,
                p_implies_q_is_true=p_implies_q_is_true,
                reasoning_chain=reasoning_chain
            )

            assert result is None, f"Modus Ponens should return None for invalid premises P={p_is_true}, (P->Q)={p_implies_q_is_true}"
            assert len(reasoning_chain.steps) == 1, "Should add exactly one step to reasoning chain"

            step = reasoning_chain.steps[0]
            assert step.confidence == 0.0, "Invalid Modus Ponens should have confidence 0.0"
            assert step.result is None, "Step result should be None for invalid deduction"
            assert "Cannot conclude Q" in step.description, "Description should indicate failed deduction"

    def test_apply_modus_ponens_without_reasoning_chain(self):
        """Test Modus Ponens application without reasoning chain - should still work correctly."""
        # Valid case
        result = apply_modus_ponens(p_is_true=True, p_implies_q_is_true=True)
        assert result is True, "Modus Ponens should work without reasoning chain"

        # Invalid case
        result = apply_modus_ponens(p_is_true=False, p_implies_q_is_true=True)
        assert result is None, "Modus Ponens should return None for invalid premises without reasoning chain"


class TestConfidenceScoreMathematicalProperties:
    """Test mathematical properties and edge cases of confidence scoring."""

    def test_confidence_bounds(self):
        """Test that all confidence scores are within valid bounds [0.0, 1.0]."""
        # Test all basic logical operations
        logical_ops = [
            (logical_not_with_confidence, [(True,), (False,)]),
            (logical_and_with_confidence, [(True, True), (True, False), (False, True), (False, False)]),
            (logical_or_with_confidence, [(True, True), (True, False), (False, True), (False, False)]),
            (implies_with_confidence, [(True, True), (True, False), (False, True), (False, False)]),
            (check_modus_ponens_premises_with_confidence, [(True, True), (True, False), (False, True), (False, False)]),
        ]

        for op_func, test_inputs in logical_ops:
            for inputs in test_inputs:
                _, confidence = op_func(*inputs)
                assert 0.0 <= confidence <= 1.0, f"Confidence {confidence} from {op_func.__name__}{inputs} is outside valid bounds [0.0, 1.0]"

    def test_deterministic_confidence(self):
        """Test that deterministic logical operations always have confidence 1.0."""
        # All basic logical operations should be deterministic (confidence = 1.0)
        logical_ops = [
            (logical_not_with_confidence, [(True,), (False,)]),
            (logical_and_with_confidence, [(True, True), (True, False), (False, True), (False, False)]),
            (logical_or_with_confidence, [(True, True), (True, False), (False, True), (False, False)]),
            (implies_with_confidence, [(True, True), (True, False), (False, True), (False, False)]),
            (check_modus_ponens_premises_with_confidence, [(True, True), (True, False), (False, True), (False, False)]),
        ]

        for op_func, test_inputs in logical_ops:
            for inputs in test_inputs:
                _, confidence = op_func(*inputs)
                assert confidence == 1.0, f"Deterministic operation {op_func.__name__}{inputs} should have confidence 1.0, got {confidence}"

    def test_modus_ponens_confidence_dichotomy(self):
        """Test that Modus Ponens has confidence 1.0 for valid deductions and 0.0 for invalid ones."""
        reasoning_chain = ReasoningChain()

        # Valid deduction should have confidence 1.0
        apply_modus_ponens(True, True, reasoning_chain)
        assert reasoning_chain.steps[-1].confidence == 1.0, "Valid Modus Ponens should have confidence 1.0"

        # Invalid deductions should have confidence 0.0
        invalid_cases = [(False, True), (True, False), (False, False)]
        for p, p_implies_q in invalid_cases:
            reasoning_chain.clear()
            apply_modus_ponens(p, p_implies_q, reasoning_chain)
            assert reasoning_chain.steps[-1].confidence == 0.0, f"Invalid Modus Ponens P={p}, (P->Q)={p_implies_q} should have confidence 0.0"


class TestEdgeCasesAndBoundaryConditions:
    """Test edge cases and boundary conditions for deductive reasoning."""

    def test_repeated_operations_consistency(self):
        """Test that repeated operations produce consistent results and confidence scores."""
        # Test repeated logical operations for consistency
        for _ in range(100):  # Repeat operations to check consistency
            result1, conf1 = logical_and_with_confidence(True, False)
            result2, conf2 = logical_and_with_confidence(True, False)

            assert result1 == result2, "Repeated logical operations should produce consistent results"
            assert conf1 == conf2, "Repeated logical operations should produce consistent confidence scores"
            assert conf1 == 1.0, "Logical AND should always have confidence 1.0"

    def test_nested_operation_confidence(self):
        """Test confidence propagation in nested logical operations."""
        # Test: (P AND Q) OR (NOT P)
        p, q = True, False

        # Step 1: P AND Q
        and_result, and_conf = logical_and_with_confidence(p, q)
        assert and_conf == 1.0, "Base AND operation should have confidence 1.0"

        # Step 2: NOT P
        not_result, not_conf = logical_not_with_confidence(p)
        assert not_conf == 1.0, "Base NOT operation should have confidence 1.0"

        # Step 3: (P AND Q) OR (NOT P)
        final_result, final_conf = logical_or_with_confidence(and_result, not_result)
        assert final_conf == 1.0, "Composed operation should maintain confidence 1.0"

    def test_reasoning_chain_integration(self):
        """Test integration with ReasoningChain for complex deductive scenarios."""
        chain = ReasoningChain()

        # Build a complex deductive argument
        # Premise 1: If it rains (P), then the ground is wet (Q)
        # Premise 2: It is raining (P is True)
        # Conclusion: The ground is wet (Q is True)

        # Apply Modus Ponens
        result = apply_modus_ponens(
            p_is_true=True,
            p_implies_q_is_true=True,
            reasoning_chain=chain
        )

        # Verify chain properties
        assert len(chain.steps) == 1, "Should have exactly one reasoning step"
        assert chain.last_result is True, "Chain should record correct final result"
        assert chain.steps[0].confidence == 1.0, "Deductive step should have maximum confidence"

        # Test chain summary
        summary = chain.get_summary()
        assert "Modus Ponens" in summary, "Summary should mention the reasoning rule used"
        assert "Confidence: 1.00" in summary, "Summary should show confidence score"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])