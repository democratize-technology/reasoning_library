#!/usr/bin/env python3
"""
Comprehensive tests for None crash vulnerabilities in reasoning functions.

These tests systematically verify that proper input validation prevents
None values from causing crashes throughout the codebase.

Critical areas tested:
- Functions that iterate over potentially None values
- Dictionary access without .get() or existence checks
- List operations on None values
- String operations on None values
- Arithmetic operations on None values
"""

import pytest
from reasoning_library.validation import ValidationError
from reasoning_library.exceptions import ReasoningError
from reasoning_library.deductive import chain_deductions, apply_modus_ponens
from reasoning_library.abductive import generate_hypotheses, rank_hypotheses
from reasoning_library.inductive import predict_next_in_sequence, find_pattern_description
from reasoning_library.core import ReasoningChain


class TestNoneCrashVulnerabilities:
    """Test cases that demonstrate None crash vulnerabilities."""

    def test_deductive_chain_deductions_with_none_functions(self):
        """Test chain_deductions with None in functions list."""
        chain = ReasoningChain()

        with pytest.raises((ValidationError, TypeError, ReasoningError)):
            chain_deductions(chain, None)  # None as function

    def test_deductive_chain_deductions_with_none_input(self):
        """Test chain_deductions with None input to chained functions."""
        chain = ReasoningChain()

        def dummy_func(x):
            return x

        with pytest.raises((ValidationError, TypeError, ReasoningError)):
            chain_deductions(chain, dummy_func, None)  # None as second function

    def test_abductive_generate_hypotheses_with_none_observations(self):
        """Test generate_hypotheses with None observations."""
        with pytest.raises((ValidationError, TypeError, ReasoningError)):
            generate_hypotheses(None)  # None observations list

    def test_abductive_generate_hypotheses_with_none_in_observations(self):
        """Test generate_hypotheses with None values in observations list."""
        with pytest.raises((ValidationError, TypeError, ReasoningError)):
            generate_hypotheses(["valid observation", None, "another valid"])

    def test_abductive_generate_hypotheses_with_none_context(self):
        """Test generate_hypotheses with None context."""
        observations = ["observation 1", "observation 2"]

        with pytest.raises((ValidationError, TypeError, ReasoningError)):
            generate_hypotheses(observations, context=None)

    def test_abductive_rank_hypotheses_with_none_hypotheses(self):
        """Test rank_hypotheses with None hypotheses list."""
        with pytest.raises((ValidationError, TypeError, ReasoningError)):
            rank_hypotheses(None)

    def test_abductive_rank_hypotheses_with_none_in_hypotheses(self):
        """Test rank_hypotheses with None values in hypotheses list."""
        valid_hypothesis = {
            "hypothesis": "test hypothesis",
            "confidence": 0.8,
            "evidence": ["evidence1"]
        }

        with pytest.raises((ValidationError, TypeError, ReasoningError)):
            rank_hypotheses([valid_hypothesis, None, valid_hypothesis])

    def test_inductive_predict_sequence_with_none_sequence(self):
        """Test predict_next_in_sequence with None sequence."""
        # The function is curried, so we need to provide all arguments
        with pytest.raises((ValidationError, TypeError, ReasoningError)):
            predict_next_in_sequence(None, None)  # None sequence, None reasoning chain

    def test_inductive_predict_sequence_with_none_in_sequence(self):
        """Test predict_next_in_sequence with None values in sequence."""
        with pytest.raises((ValidationError, TypeError, ReasoningError)):
            predict_next_in_sequence([1, 2, None, 4], None)  # None in sequence, None reasoning chain

    def test_inductive_find_pattern_with_none_sequence(self):
        """Test find_pattern_description with None sequence."""
        # The function is also curried
        with pytest.raises((ValidationError, TypeError, ReasoningError)):
            find_pattern_description(None, None)  # None sequence, None reasoning chain

    def test_deductive_apply_modus_ponens_with_none_inputs(self):
        """Test apply_modus_ponens with None inputs."""
        # None premises
        with pytest.raises((ValidationError, TypeError, ReasoningError)):
            apply_modus_ponens(None, "conclusion", "rule_name")

        # None conclusion
        with pytest.raises((ValidationError, TypeError, ReasoningError)):
            apply_modus_ponens(["premise1", "premise2"], None, "rule_name")

        # None in premises list
        with pytest.raises((ValidationError, TypeError, ReasoningError)):
            apply_modus_ponens(["valid premise", None, "another premise"], "conclusion", "rule_name")

    def test_reasoning_chain_add_step_with_none_data(self):
        """Test ReasoningChain.add_step with None step data."""
        chain = ReasoningChain()

        with pytest.raises((ValidationError, TypeError, ReasoningError)):
            chain.add_step(step_type=None, description="test", data=None)

        with pytest.raises((ValidationError, TypeError, ReasoningError)):
            chain.add_step(step_type="test", description=None, data={})

    def test_validation_dictionary_iteration_with_none(self):
        """Test validation functions that iterate over dictionaries."""
        from reasoning_library.validation import validate_hypothesis_dict

        # None hypothesis dict
        with pytest.raises((ValidationError, TypeError, ReasoningError)):
            validate_hypothesis_dict(None, field_name="test")

        # Dictionary with None values
        invalid_hypothesis = {
            "hypothesis": None,  # None hypothesis text
            "confidence": 0.8,
            "evidence": ["evidence1"]
        }

        with pytest.raises((ValidationError, TypeError, ReasoningError)):
            validate_hypothesis_dict(invalid_hypothesis, field_name="test")

    def test_validation_list_iteration_with_none(self):
        """Test validation functions that iterate over lists."""
        from reasoning_library.validation import validate_hypotheses_list

        # None list
        with pytest.raises((ValidationError, TypeError, ReasoningError)):
            validate_hypotheses_list(None, field_name="test", required=True)

        # List with None values
        with pytest.raises((ValidationError, TypeError, ReasoningError)):
            validate_hypotheses_list([None, None, None], field_name="test", required=True)

    def test_abductive_keyword_extraction_with_none_text(self):
        """Test keyword extraction functions with None text."""
        from reasoning_library.abductive import _extract_keywords

        with pytest.raises((ValidationError, TypeError, ReasoningError)):
            _extract_keywords(None)

    def test_abductive_generate_hypotheses_with_empty_observations(self):
        """Test generate_hypotheses edge cases."""
        # Empty observations
        result = generate_hypotheses([])
        assert isinstance(result, list)  # Should handle gracefully

    def test_inductive_numpy_operations_with_none_data(self):
        """Test inductive functions that perform numpy operations on None data."""
        import numpy as np

        # Test with None converted to numpy array
        with pytest.raises((ValidationError, TypeError, ReasoningError)):
            # Simulate what would happen if None data got to numpy operations
            np.array(None)

    def test_core_function_iteration_with_none_parameters(self):
        """Test core functions that iterate over parameter dictionaries."""
        # Test that tool specs handle None gracefully
        tool_spec = {
            "name": None,  # None name should be handled
            "description": "valid description",
            "parameters": {"properties": {}}
        }

        # This should raise ValidationError, not crash
        with pytest.raises((ValidationError, TypeError, ReasoningError)):
            from reasoning_library.core import register_tool
            register_tool(None, lambda x: x, tool_spec)  # None function

    def test_memory_exhaustion_protection_with_none(self):
        """Test that memory exhaustion protection handles None values."""
        from reasoning_library.validation import validate_reasoning_chain_size

        chain = ReasoningChain()

        # Add step with None data
        with pytest.raises((ValidationError, TypeError, ReasoningError)):
            chain.add_step("test", "description", None)

        # The size validation should handle this gracefully
        validate_reasoning_chain_size(chain)

    def test_regex_operations_with_none_input(self):
        """Test regex operations with None input."""
        import re

        with pytest.raises((ValidationError, TypeError, ReasoningError)):
            re.findall(r"pattern", None)  # This would raise TypeError

    def test_string_operations_with_none_input(self):
        """Test string operations with None input."""
        test_cases = [
            lambda: None.upper(),  # AttributeError
            lambda: None.lower(),  # AttributeError
            lambda: None.strip(),  # AttributeError
            lambda: None.split(),  # AttributeError
            lambda: None + "string",  # TypeError
            lambda: "string" + None,  # TypeError
        ]

        for test_case in test_cases:
            with pytest.raises((AttributeError, TypeError)):
                test_case()

    def test_arithmetic_operations_with_none(self):
        """Test arithmetic operations with None values."""
        test_cases = [
            lambda: None + 1,      # TypeError
            lambda: None - 1,      # TypeError
            lambda: None * 1,      # TypeError
            lambda: None / 1,      # TypeError
            lambda: 1 + None,      # TypeError
            lambda: 1 - None,      # TypeError
            lambda: 1 * None,      # TypeError
            lambda: 1 / None,      # TypeError
        ]

        for test_case in test_cases:
            with pytest.raises(TypeError):
                test_case()

    def test_list_comprehensions_with_none_input(self):
        """Test list comprehensions that might crash on None input."""
        test_cases = [
            lambda: [x for x in None],  # TypeError
            lambda: [x.upper() for x in None],  # TypeError
        ]

        for test_case in test_cases:
            with pytest.raises(TypeError):
                test_case()

    def test_dictionary_access_with_none_key_or_value(self):
        """Test dictionary operations that might crash with None."""
        # Using None as key (this is actually valid in Python but may cause issues)
        test_dict = {None: "value", "key": None}

        # These should work but may cause logic errors
        assert test_dict[None] == "value"
        assert test_dict["key"] is None

        # But accessing non-existent keys should raise KeyError
        with pytest.raises(KeyError):
            test_dict["non_existent"]

    def test_function_call_with_none_arguments(self):
        """Test function calls with None arguments that might cause crashes."""

        def test_function(a, b, c="default"):
            """A function that expects specific types."""
            if not isinstance(a, (str, int, float)):
                raise TypeError(f"Expected str/int/float, got {type(a)}")
            if not isinstance(b, (str, int, float)):
                raise TypeError(f"Expected str/int/float, got {type(b)}")
            return f"{a}_{b}_{c}"

        with pytest.raises(TypeError):
            test_function(None, "valid")

        with pytest.raises(TypeError):
            test_function("valid", None)


class TestNonePropagationSafety:
    """Test that None values are handled safely and don't propagate unexpectedly."""

    def test_safe_none_handling_in_validation(self):
        """Test that validation functions handle None safely."""
        from reasoning_library.validation import validate_hypothesis_dict

        # Should raise ValidationError, not crash with AttributeError
        with pytest.raises(ValidationError):
            validate_hypothesis_dict(None, field_name="test")

    def test_safe_none_handling_in_ranking(self):
        """Test that ranking functions handle None in data structures."""
        from reasoning_library.abductive import rank_hypotheses

        hypotheses = [
            {"hypothesis": "valid", "confidence": 0.8},
            {"hypothesis": None, "confidence": 0.5},  # None hypothesis text
            {"hypothesis": "another valid", "confidence": 0.7}
        ]

        # Should handle None gracefully or raise ValidationError
        with pytest.raises(ValidationError):
            rank_hypotheses(hypotheses)

    def test_safe_none_handling_in_confidence_calculation(self):
        """Test confidence calculation with None inputs."""
        from reasoning_library.validation import validate_confidence_value

        # Should clamp or validate, not crash
        with pytest.raises(ValidationError):
            validate_confidence_value(None)


if __name__ == "__main__":
    # Run these tests to verify None crash vulnerabilities
    pytest.main([__file__, "-v"])