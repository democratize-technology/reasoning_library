#!/usr/bin/env python3
"""
Comprehensive test suite for deductive.py module.

Expands beyond the basic test_deductive_only.py to cover all logical operations,
edge cases, error conditions, currying functionality, and confidence scoring.
"""
import os
import sys
from unittest.mock import MagicMock

import pytest

from reasoning_library.core import ReasoningChain, ReasoningStep
from reasoning_library.deductive import (
    apply_modus_ponens,
    chain_deductions,
    check_modus_ponens_premises,
    check_modus_ponens_premises_with_confidence,
    implies,
    implies_with_confidence,
    logical_and,
    logical_and_with_confidence,
    logical_not,
    logical_not_with_confidence,
    logical_or,
    logical_or_with_confidence,
)


class TestLogicalPrimitives:
    """Test basic logical operations and their confidence scoring."""

    def test_logical_not_basic(self):
        """Test basic logical NOT operation."""
        assert logical_not(True) == False
        assert logical_not(False) == True

    def test_logical_not_with_confidence_basic(self):
        """Test logical NOT with confidence scoring."""
        result, confidence = logical_not_with_confidence(True)
        assert result == False
        assert confidence == 1.0

        result, confidence = logical_not_with_confidence(False)
        assert result == True
        assert confidence == 1.0

    def test_logical_not_with_confidence_type_validation(self):
        """Test logical NOT with invalid input types."""
        with pytest.raises(TypeError, match="Expected bool for p, got"):
            logical_not_with_confidence("not a bool")

        with pytest.raises(TypeError, match="Expected bool for p, got"):
            logical_not_with_confidence(1)

        with pytest.raises(TypeError, match="Expected bool for p, got"):
            logical_not_with_confidence(None)

    def test_logical_and_basic(self):
        """Test basic logical AND operation."""
        assert logical_and(True, True) == True
        assert logical_and(True, False) == False
        assert logical_and(False, True) == False
        assert logical_and(False, False) == False

    def test_logical_and_with_confidence_all_combinations(self):
        """Test logical AND with confidence for all truth combinations."""
        test_cases = [
            (True, True, True, 1.0),
            (True, False, False, 1.0),
            (False, True, False, 1.0),
            (False, False, False, 1.0),
        ]

        for p, q, expected_result, expected_confidence in test_cases:
            result, confidence = logical_and_with_confidence(p, q)
            assert result == expected_result
            assert confidence == expected_confidence

    def test_logical_and_with_confidence_type_validation(self):
        """Test logical AND with invalid input types."""
        with pytest.raises(TypeError, match="Expected bool for p, got"):
            logical_and_with_confidence("not a bool", True)

        with pytest.raises(TypeError, match="Expected bool for q, got"):
            logical_and_with_confidence(True, "not a bool")

        with pytest.raises(TypeError, match="Expected bool for p, got"):
            logical_and_with_confidence(1, True)

        with pytest.raises(TypeError, match="Expected bool for q, got"):
            logical_and_with_confidence(True, 1)

    def test_logical_or_basic(self):
        """Test basic logical OR operation."""
        assert logical_or(True, True) == True
        assert logical_or(True, False) == True
        assert logical_or(False, True) == True
        assert logical_or(False, False) == False

    def test_logical_or_with_confidence_all_combinations(self):
        """Test logical OR with confidence for all truth combinations."""
        test_cases = [
            (True, True, True, 1.0),
            (True, False, True, 1.0),
            (False, True, True, 1.0),
            (False, False, False, 1.0),
        ]

        for p, q, expected_result, expected_confidence in test_cases:
            result, confidence = logical_or_with_confidence(p, q)
            assert result == expected_result
            assert confidence == expected_confidence

    def test_logical_or_with_confidence_type_validation(self):
        """Test logical OR with invalid input types."""
        with pytest.raises(TypeError, match="Expected bool for p, got"):
            logical_or_with_confidence("not a bool", True)

        with pytest.raises(TypeError, match="Expected bool for q, got"):
            logical_or_with_confidence(True, "not a bool")

    def test_implies_basic(self):
        """Test basic logical IMPLICATION operation."""
        # P -> Q is equivalent to (NOT P) OR Q
        assert implies(True, True) == True  # True -> True = True
        assert implies(True, False) == False  # True -> False = False
        assert implies(False, True) == True  # False -> True = True
        assert implies(False, False) == True  # False -> False = True

    def test_implies_with_confidence_all_combinations(self):
        """Test logical IMPLICATION with confidence for all truth combinations."""
        test_cases = [
            (True, True, True, 1.0),  # True -> True = True
            (True, False, False, 1.0),  # True -> False = False
            (False, True, True, 1.0),  # False -> True = True
            (False, False, True, 1.0),  # False -> False = True
        ]

        for p, q, expected_result, expected_confidence in test_cases:
            result, confidence = implies_with_confidence(p, q)
            assert result == expected_result
            assert confidence == expected_confidence

    def test_implies_with_confidence_type_validation(self):
        """Test logical IMPLICATION with invalid input types."""
        with pytest.raises(TypeError, match="Expected bool for p, got"):
            implies_with_confidence("not a bool", True)

        with pytest.raises(TypeError, match="Expected bool for q, got"):
            implies_with_confidence(True, "not a bool")


class TestCurryingFunctionality:
    """Test currying functionality of logical operations."""

    def test_logical_and_currying(self):
        """Test currying of logical_and function."""
        # Partial application
        and_with_true = logical_and(True)
        assert callable(and_with_true)
        assert and_with_true(True) == True
        assert and_with_true(False) == False

        and_with_false = logical_and(False)
        assert callable(and_with_false)
        assert and_with_false(True) == False
        assert and_with_false(False) == False

    def test_logical_or_currying(self):
        """Test currying of logical_or function."""
        # Partial application
        or_with_true = logical_or(True)
        assert callable(or_with_true)
        assert or_with_true(True) == True
        assert or_with_true(False) == True

        or_with_false = logical_or(False)
        assert callable(or_with_false)
        assert or_with_false(True) == True
        assert or_with_false(False) == False

    def test_implies_currying(self):
        """Test currying of implies function."""
        # Partial application
        implies_from_true = implies(True)
        assert callable(implies_from_true)
        assert implies_from_true(True) == True
        assert implies_from_true(False) == False

        implies_from_false = implies(False)
        assert callable(implies_from_false)
        assert implies_from_false(True) == True
        assert implies_from_false(False) == True


class TestModusPonens:
    """Test Modus Ponens inference rule implementation."""

    def test_check_modus_ponens_premises_basic(self):
        """Test basic Modus Ponens premise checking."""
        # Valid premises: P is True, P -> Q is True
        assert check_modus_ponens_premises(True, True) == True

        # Invalid premises
        assert check_modus_ponens_premises(False, True) == False
        assert check_modus_ponens_premises(True, False) == False
        assert check_modus_ponens_premises(False, False) == False

    def test_check_modus_ponens_premises_with_confidence_basic(self):
        """Test Modus Ponens premise checking with confidence."""
        result, confidence = check_modus_ponens_premises_with_confidence(True, True)
        assert result == True
        assert confidence == 1.0

        result, confidence = check_modus_ponens_premises_with_confidence(False, True)
        assert result == False
        assert confidence == 1.0

    def test_check_modus_ponens_premises_with_confidence_type_validation(self):
        """Test Modus Ponens premise checking with invalid input types."""
        with pytest.raises(TypeError, match="Expected bool for p, got"):
            check_modus_ponens_premises_with_confidence("not a bool", True)

        with pytest.raises(TypeError, match="Expected bool for q, got"):
            check_modus_ponens_premises_with_confidence(True, "not a bool")

    def test_apply_modus_ponens_valid_inference(self):
        """Test valid Modus Ponens inference."""
        chain = ReasoningChain()

        # Valid case: P is True, P -> Q is True, so Q should be True
        result = apply_modus_ponens(True, True, reasoning_chain=chain)

        assert result == True
        assert len(chain.steps) == 1

        step = chain.steps[0]
        assert step.stage == "Deductive Reasoning: Modus Ponens"
        assert step.result == True
        assert step.confidence == 1.0
        assert "Concluded Q is True" in step.description
        assert "Premise P is True" in step.evidence
        assert "Premise (P -> Q) is True" in step.evidence

    def test_apply_modus_ponens_invalid_inference_false_p(self):
        """Test invalid Modus Ponens with false P."""
        chain = ReasoningChain()

        # Invalid case: P is False, P -> Q is True, cannot conclude Q
        result = apply_modus_ponens(False, True, reasoning_chain=chain)

        assert result is None
        assert len(chain.steps) == 1

        step = chain.steps[0]
        assert step.result is None
        assert step.confidence == 0.0
        assert "Cannot conclude Q" in step.description

    def test_apply_modus_ponens_invalid_inference_false_implication(self):
        """Test invalid Modus Ponens with false implication."""
        chain = ReasoningChain()

        # Invalid case: P is True, P -> Q is False, cannot conclude Q
        result = apply_modus_ponens(True, False, reasoning_chain=chain)

        assert result is None
        assert len(chain.steps) == 1

        step = chain.steps[0]
        assert step.result is None
        assert step.confidence == 0.0
        assert "Cannot conclude Q" in step.description

    def test_apply_modus_ponens_without_reasoning_chain(self):
        """Test Modus Ponens without providing reasoning chain."""
        # Should work without reasoning chain
        result = apply_modus_ponens(True, True)
        assert result == True

        result = apply_modus_ponens(False, True)
        assert result is None

    def test_apply_modus_ponens_evidence_and_assumptions(self):
        """Test that Modus Ponens records proper evidence and assumptions."""
        chain = ReasoningChain()

        apply_modus_ponens(True, True, reasoning_chain=chain)

        step = chain.steps[0]
        assert "Premise P is True" in step.evidence
        assert "Premise (P -> Q) is True" in step.evidence
        assert len(step.assumptions) > 0
        assert "Propositions P and (P -> Q) are true" in step.assumptions


class TestChainDeductions:
    """Test higher-order function for chaining deductions."""

    def test_chain_deductions_simple_chain(self):
        """Test simple deduction chain."""
        chain = ReasoningChain()

        # Create simple functions for chaining
        def add_one(x):
            if isinstance(x, (int, float)):
                return x + 1
            return None

        def multiply_two(x):
            if isinstance(x, (int, float)):
                return x * 2
            return None

        # Chain the functions
        chained_func = chain_deductions(chain, add_one, multiply_two)

        result = chained_func(5)
        assert result == 12  # (5 + 1) * 2 = 12

    def test_chain_deductions_with_failure(self):
        """Test deduction chain that fails at some step."""
        chain = ReasoningChain()

        def always_succeed(x):
            return x

        def always_fail(x):
            return None

        def never_reached(x):
            return x * 100

        # Chain with a failing function
        chained_func = chain_deductions(
            chain, always_succeed, always_fail, never_reached
        )

        result = chained_func(5)
        assert result is None  # Should fail at always_fail

    def test_chain_deductions_empty_chain(self):
        """Test deduction chain with no functions."""
        chain = ReasoningChain()

        chained_func = chain_deductions(chain)
        result = chained_func(42)
        assert result == 42  # Should return input unchanged

    def test_chain_deductions_single_function(self):
        """Test deduction chain with single function."""
        chain = ReasoningChain()

        def double(x):
            return x * 2

        chained_func = chain_deductions(chain, double)
        result = chained_func(5)
        assert result == 10


class TestConfidenceScoring:
    """Test confidence scoring edge cases and boundary conditions."""

    def test_confidence_always_one_for_logical_operations(self):
        """Test that logical operations always return confidence 1.0."""
        operations = [
            (
                logical_and_with_confidence,
                [(True, True), (True, False), (False, False)],
            ),
            (logical_or_with_confidence, [(True, True), (True, False), (False, False)]),
            (implies_with_confidence, [(True, True), (True, False), (False, False)]),
            (logical_not_with_confidence, [(True,), (False,)]),
        ]

        for operation, test_cases in operations:
            for args in test_cases:
                if len(args) == 1:
                    result, confidence = operation(args[0])
                else:
                    result, confidence = operation(args[0], args[1])
                assert (
                    confidence == 1.0
                ), f"Expected confidence 1.0 for {operation.__name__} with args {args}"

    def test_modus_ponens_confidence_extremes(self):
        """Test Modus Ponens confidence in extreme cases."""
        chain = ReasoningChain()

        # Valid inference should have confidence 1.0
        apply_modus_ponens(True, True, reasoning_chain=chain)
        assert chain.steps[0].confidence == 1.0

        # Invalid inference should have confidence 0.0
        chain.clear()
        apply_modus_ponens(False, True, reasoning_chain=chain)
        assert chain.steps[0].confidence == 0.0

        chain.clear()
        apply_modus_ponens(True, False, reasoning_chain=chain)
        assert chain.steps[0].confidence == 0.0

        chain.clear()
        apply_modus_ponens(False, False, reasoning_chain=chain)
        assert chain.steps[0].confidence == 0.0


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling scenarios."""

    def test_tool_spec_metadata(self):
        """Test that apply_modus_ponens has proper tool spec metadata."""
        # Check that the function has tool spec attached
        assert hasattr(apply_modus_ponens, "tool_spec")

        spec = apply_modus_ponens.tool_spec
        assert spec["type"] == "function"
        assert spec["function"]["name"] == "apply_modus_ponens"
        assert "Modus Ponens" in spec["function"]["description"]

        # Check parameters
        params = spec["function"]["parameters"]
        assert "p_is_true" in params["properties"]
        assert "p_implies_q_is_true" in params["properties"]
        assert "reasoning_chain" not in params["properties"]  # Should be excluded

    def test_reasoning_chain_integration(self):
        """Test integration with ReasoningChain for step tracking."""
        chain = ReasoningChain()

        # Test multiple operations add steps correctly
        logical_and_with_confidence(True, False)  # No chain provided, should work
        apply_modus_ponens(True, True, reasoning_chain=chain)
        apply_modus_ponens(False, True, reasoning_chain=chain)

        assert len(chain.steps) == 2
        assert chain.steps[0].confidence == 1.0
        assert chain.steps[1].confidence == 0.0

    def test_boolean_coercion_resistance(self):
        """Test that functions resist implicit boolean coercion."""
        # These should raise TypeError, not silently convert to bool
        with pytest.raises(TypeError):
            logical_and_with_confidence(1, 0)  # Truthy/falsy but not bool

        with pytest.raises(TypeError):
            logical_or_with_confidence([], [1])  # Empty list is falsy

        with pytest.raises(TypeError):
            implies_with_confidence("true", "false")  # Strings

    def test_currying_with_reasoning_chain_parameter(self):
        """Test that currying works properly even with optional reasoning_chain parameter."""
        # This tests the curry decorator interaction with the reasoning_chain parameter
        curried_apply = apply_modus_ponens(True)
        assert callable(curried_apply)

        chain = ReasoningChain()
        result = curried_apply(True, reasoning_chain=chain)
        assert result == True
        assert len(chain.steps) == 1

    def test_function_composition_with_logical_operations(self):
        """Test composing logical operations."""
        # Test that curried functions can be composed
        and_true = logical_and(True)
        or_false = logical_or(False)

        # These should be composable
        result1 = and_true(True)  # True AND True = True
        result2 = or_false(result1)  # False OR True = True

        assert result1 == True
        assert result2 == True

        # Test with False values
        result3 = and_true(False)  # True AND False = False
        result4 = or_false(result3)  # False OR False = False

        assert result3 == False
        assert result4 == False


def run_all_tests():
    """Run all deductive reasoning tests with detailed output."""
    print("🧪 Running comprehensive test suite for deductive.py...")

    test_classes = [
        TestLogicalPrimitives,
        TestCurryingFunctionality,
        TestModusPonens,
        TestChainDeductions,
        TestConfidenceScoring,
        TestEdgeCasesAndErrorHandling,
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
        print(f"\n🎉 All deductive reasoning tests passed!")
        return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
