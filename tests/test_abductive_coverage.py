#!/usr/bin/env python3
"""
Coverage-focused test suite for abductive.py module.

Targets specific missing lines to achieve 100% test coverage.
Tests error handling, edge cases, and validation paths.
"""
from unittest.mock import patch, MagicMock

import pytest

from reasoning_library.core import ReasoningChain
from reasoning_library.exceptions import ValidationError
from reasoning_library.abductive import (
    _validate_and_sanitize_input_size,
    _validate_confidence_value,
    generate_hypotheses,
    rank_hypotheses,
    evaluate_best_explanation,
    # Add other functions as needed from abductive.py
)


class TestMissingAbductiveCoverage:
    """Test cases specifically targeting missing coverage lines in abductive.py."""

    def test_validate_and_sanitize_non_string_observations(self):
        """Test lines 90-91: non-string observation conversion."""
        # Test with non-string observations
        observations = [123, None, True]
        sanitized, context = _validate_and_sanitize_input_size(observations)
        assert all(isinstance(obs, str) for obs in sanitized)

    def test_validate_and_sanitize_observation_truncation(self):
        """Test lines 93-94: observation length truncation."""
        # Create very long observation
        long_obs = "x" * 15000  # Longer than MAX_OBSERVATION_LENGTH (10000)
        observations = [long_obs]
        sanitized, context = _validate_and_sanitize_input_size(observations)
        assert len(sanitized[0]) <= 10000  # Should be truncated to MAX_OBSERVATION_LENGTH

    def test_validate_and_sanitize_non_string_context(self):
        """Test lines 98-99: non-string context conversion."""
        observations = ["test obs"]
        context = 123  # Non-string context
        sanitized, result_context = _validate_and_sanitize_input_size(observations, context)
        assert isinstance(result_context, str)

    def test_validate_and_sanitize_context_truncation(self):
        """Test lines 100-101: context length truncation."""
        observations = ["test obs"]
        long_context = "x" * 8000  # Longer than MAX_CONTEXT_LENGTH (5000)
        sanitized, result_context = _validate_and_sanitize_input_size(observations, long_context)
        assert len(result_context) <= 5000  # Should be truncated to MAX_CONTEXT_LENGTH

    def test_validate_confidence_value_non_numeric(self):
        """Test lines 123-126: non-numeric confidence validation."""
        with pytest.raises(ValidationError, match="Confidence value '.*' must be numeric"):
            _validate_confidence_value("invalid_confidence")

    def test_validate_confidence_value_with_index(self):
        """Test line 121: hypothesis index in error message."""
        with pytest.raises(ValidationError, match=r"\(hypothesis #2\)"):
            _validate_confidence_value("invalid", hypothesis_index=2)

    def test_validate_confidence_float_nan(self):
        """Test lines 129-130: NaN confidence validation."""
        with pytest.raises(ValidationError, match="Confidence cannot be NaN"):
            _validate_confidence_value(float('nan'))

    def test_validate_confidence_float_infinite(self):
        """Test lines 131-132: infinite confidence validation."""
        with pytest.raises(ValidationError, match="Confidence cannot be infinite"):
            _validate_confidence_value(float('inf'))

        with pytest.raises(ValidationError, match="Confidence cannot be infinite"):
            _validate_confidence_value(float('-inf'))

    def test_validate_confidence_conversion_error(self):
        """Test line 139: confidence conversion error handling."""
        # Test with a string that can't be converted to float properly
        with pytest.raises(ValidationError, match="must be numeric"):
            _validate_confidence_value("invalid_confidence_string")

    def test_generate_hypotheses_empty_observations(self):
        """Test edge case: empty observations list raises validation error."""
        with pytest.raises(ValidationError, match="observations cannot be empty"):
            generate_hypotheses([], None)

    def test_generate_hypotheses_very_long_observations(self):
        """Test edge case: very long observations."""
        long_obs = "x" * 1000
        result = generate_hypotheses([long_obs], None)
        assert isinstance(result, list)

    def test_rank_hypotheses_empty_list(self):
        """Test edge case: empty hypotheses list raises validation error."""
        with pytest.raises(ValidationError, match="hypotheses cannot be empty"):
            rank_hypotheses([], [], None)

    def test_rank_hypotheses_invalid_confidence_types(self):
        """Test edge case: invalid confidence values in hypotheses."""
        invalid_hypotheses = [
            {"hypothesis": "test1", "confidence": "invalid"},
            {"hypothesis": "test2", "confidence": 0.8}
        ]
        # Should handle gracefully or raise appropriate error
        with pytest.raises((TypeError, ValidationError)):
            rank_hypotheses(invalid_hypotheses, [], None)

    def test_evaluate_best_explanation_empty_list(self):
        """Test edge case: empty hypotheses list for evaluation raises validation error."""
        with pytest.raises(ValidationError, match="hypotheses cannot be empty"):
            evaluate_best_explanation([], None)

    def test_abductive_input_validation_special_characters(self):
        """Test edge case: observations with special characters."""
        special_obs = ["test\n\r\t\x00\u202e", "more\u200bspecial\u200bchars"]
        result = generate_hypotheses(special_obs, None)
        assert isinstance(result, list)

    def test_abductive_confidence_boundary_values(self):
        """Test edge case: confidence at boundary values."""
        # Test with confidence exactly at boundaries - valid values only
        boundary_hypotheses = [
            {"hypothesis": "test1", "confidence": 0.0},
            {"hypothesis": "test2", "confidence": 1.0},
        ]
        result = rank_hypotheses(boundary_hypotheses, [], None)
        assert isinstance(result, list)

        # Test values outside range - they get clamped, not rejected
        clamped_hypotheses = [
            {"hypothesis": "test3", "confidence": -0.1},  # Will be clamped to 0.0
            {"hypothesis": "test4", "confidence": 1.1}    # Will be clamped to 1.0
        ]
        # Should not raise error - values get clamped to valid range
        result = rank_hypotheses(clamped_hypotheses, [], None)
        assert isinstance(result, list)

        # Verify confidence values were clamped
        for hyp in result:
            assert 0.0 <= hyp["confidence"] <= 1.0

    def test_abductive_large_dataset_performance(self):
        """Test edge case: large number of observations."""
        many_obs = [f"observation_{i}" for i in range(100)]
        result = generate_hypotheses(many_obs, None)
        assert isinstance(result, list)

    def test_abductive_unicode_handling(self):
        """Test edge case: Unicode characters in observations."""
        unicode_obs = ["test with émojis 🚀 and 中文 characters"]
        result = generate_hypotheses(unicode_obs, None)
        assert isinstance(result, list)

    def test_abductive_context_edge_cases(self):
        """Test edge cases for context parameter."""
        obs = ["test observation"]

        # Test with None context
        result1 = generate_hypotheses(obs, None, context=None)

        # Test with empty string context
        result2 = generate_hypotheses(obs, None, context="")

        # Test with very long context (will be truncated)
        long_context = "x" * 8000
        result3 = generate_hypotheses(obs, None, context=long_context)

        for result in [result1, result2, result3]:
            assert isinstance(result, list)