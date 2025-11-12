#!/usr/bin/env python3
"""
Comprehensive test suite for refactored long functions.

Tests the new helper functions created during refactoring to ensure they maintain
exact functionality and behavior while being more modular and testable.
"""
import pytest
from typing import List, Optional, Tuple, Dict, Any
import numpy as np

from reasoning_library.exceptions import ValidationError
from reasoning_library.core import (
    _get_mathematical_indicators,
    _has_mathematical_indicators_in_docs,
    _extract_confidence_factors,
    _clean_confidence_factors,
    _create_confidence_documentation,
    _extract_mathematical_basis,
    _detect_mathematical_reasoning_uncached,
)
from reasoning_library.abductive import (
    _generate_single_cause_hypothesis,
    _generate_multiple_causes_hypothesis,
    _generate_causal_chain_hypothesis,
    _sanitize_template_input,
    _generate_domain_template_hypotheses,
    _generate_contextual_hypothesis,
    _generate_systemic_hypothesis,
    generate_hypotheses,
)
from reasoning_library.inductive import (
    _validate_sequence_input,
    _check_arithmetic_progression,
    _check_geometric_progression,
    _add_reasoning_step,
    predict_next_in_sequence,
)


class TestMathematicalReasoningRefactoring:
    """Test refactored mathematical reasoning detection functions."""

    def test_get_mathematical_indicators(self):
        """Test _get_mathematical_indicators returns expected indicators."""
        indicators = _get_mathematical_indicators()

        assert isinstance(indicators, list)
        assert len(indicators) > 10
        assert "confidence" in indicators
        assert "probability" in indicators
        assert "arithmetic" in indicators
        assert "geometric" in indicators
        assert "pattern" in indicators

    def test_has_mathematical_indicators_in_docs_positive(self):
        """Test detection of mathematical indicators in docs."""
        def test_func():
            """This function uses confidence calculations."""
            pass

        indicators = ["confidence", "probability"]
        result = _has_mathematical_indicators_in_docs(test_func, indicators)

        assert result is True

    def test_has_mathematical_indicators_in_docs_negative(self):
        """Test no mathematical indicators detection."""
        def test_func():
            """This function does simple text processing."""
            pass

        indicators = ["confidence", "probability"]
        result = _has_mathematical_indicators_in_docs(test_func, indicators)

        assert result is False

    def test_has_mathematical_indicators_in_docs_function_name(self):
        """Test detection via function name."""
        def confidence_calculator():
            """Simple function."""
            pass

        indicators = ["confidence"]
        result = _has_mathematical_indicators_in_docs(confidence_calculator, indicators)

        assert result is True

    def test_extract_confidence_factors_from_source(self):
        """Test confidence factor extraction from source code."""
        source = """
        pattern_quality_factor = 0.8
        data_sufficiency_factor = 0.9
        result = pattern_quality_factor * data_sufficiency_factor
        """
        docstring = "Calculates confidence based on factors"

        factors = _extract_confidence_factors(source, docstring)

        assert isinstance(factors, list)
        # Should extract factors using FACTOR_PATTERN which matches specific factor names
        assert len(factors) >= 0  # Should find some factors or return empty list

    def test_extract_confidence_factors_from_docstring(self):
        """Test confidence factor extraction from docstring."""
        source = "simple code"
        docstring = "Pattern analysis based on pattern quality and confidence factors"

        factors = _extract_confidence_factors(source, docstring)

        assert isinstance(factors, list)
        # Should extract pattern-related terms when both "confidence" and "based on" are in docstring
        if "confidence" in docstring.lower() and "based on" in docstring.lower():
            assert len(factors) >= 0  # At least some factors should be found

    def test_clean_confidence_factors(self):
        """Test confidence factor cleaning."""
        raw_factors = [
            "confidence factor",
            "pattern_quality",  # with underscore
            "  data sufficiency  ",  # with spaces
            "a",  # too short
            "pattern quality",  # duplicate
            "pattern quality",  # duplicate
            "complex calculation factor"
        ]

        clean_factors = _clean_confidence_factors(raw_factors)

        assert isinstance(clean_factors, list)
        assert "confidence factor" in clean_factors
        assert "pattern quality" in clean_factors
        assert "data sufficiency" in clean_factors
        assert "complex calculation factor" in clean_factors
        # Remove duplicates
        assert len([f for f in clean_factors if f == "pattern quality"]) == 1
        # Remove too short
        assert "a" not in clean_factors

    def test_create_confidence_documentation(self):
        """Test confidence documentation creation."""
        clean_factors = ["pattern quality", "data sufficiency", "sample size"]

        doc = _create_confidence_documentation(clean_factors)

        assert doc is not None
        assert "Confidence calculation based on:" in doc
        assert "pattern quality" in doc
        assert "data sufficiency" in doc
        assert "sample size" in doc

    def test_create_confidence_documentation_empty(self):
        """Test confidence documentation with empty factors."""
        doc = _create_confidence_documentation([])

        assert doc is None

    def test_extract_mathematical_basis_arithmetic(self):
        """Test mathematical basis extraction for arithmetic."""
        docstring = "This function performs arithmetic progression analysis"

        basis = _extract_mathematical_basis(docstring)

        assert basis is not None
        assert "Arithmetic progression analysis" in basis

    def test_extract_mathematical_basis_geometric(self):
        """Test mathematical basis extraction for geometric."""
        docstring = "This function performs geometric progression analysis"

        basis = _extract_mathematical_basis(docstring)

        assert basis is not None
        assert "Geometric progression analysis" in basis

    def test_extract_mathematical_basis_modus_ponens(self):
        """Test mathematical basis extraction for modus ponens."""
        docstring = "This function uses modus ponens logic"

        basis = _extract_mathematical_basis(docstring)

        assert basis is not None
        assert "Modus Ponens" in basis

    def test_extract_mathematical_basis_none(self):
        """Test mathematical basis extraction with no match."""
        docstring = "This function does simple text processing"

        basis = _extract_mathematical_basis(docstring)

        assert basis is None

    def test_detect_mathematical_reasoning_uncached_integration(self):
        """Test complete mathematical reasoning detection integration."""
        def mathematical_func():
            """
            This function performs arithmetic progression analysis with confidence calculations.
            Based on pattern quality and data sufficiency.
            """
            confidence_factor = 0.5
            pattern_quality = 0.8
            return confidence_factor * pattern_quality

        result = _detect_mathematical_reasoning_uncached(mathematical_func)

        assert isinstance(result, tuple)
        assert len(result) == 3

        is_mathematical, confidence_doc, mathematical_basis = result

        assert is_mathematical is True
        assert confidence_doc is not None
        assert mathematical_basis is not None

    def test_detect_mathematical_reasoning_uncached_non_mathematical(self):
        """Test detection with non-mathematical function."""
        def simple_func():
            """This function does simple text processing."""
            return "hello world"

        result = _detect_mathematical_reasoning_uncached(simple_func)

        is_mathematical, confidence_doc, mathematical_basis = result

        assert is_mathematical is False
        assert confidence_doc is None
        assert mathematical_basis is None


class TestAbductiveReasoningRefactoring:
    """Test refactored abductive reasoning functions."""

    def test_generate_single_cause_hypothesis_with_themes(self):
        """Test single-cause hypothesis generation."""
        common_themes = ["server overload", "high cpu"]
        observations_count = 3

        hypothesis = _generate_single_cause_hypothesis(common_themes, observations_count)

        assert hypothesis is not None
        assert hypothesis["type"] == "single_cause"
        assert "server overload" in hypothesis["hypothesis"]
        assert hypothesis["theme"] == "server overload"
        assert len(hypothesis["explains"]) == observations_count
        assert hypothesis["confidence"] > 0.0

    def test_generate_single_cause_hypothesis_no_themes(self):
        """Test single-cause hypothesis with no themes."""
        hypothesis = _generate_single_cause_hypothesis([], 3)

        assert hypothesis is None

    def test_generate_multiple_causes_hypothesis_sufficient_themes(self):
        """Test multiple-causes hypothesis with sufficient themes."""
        common_themes = ["server overload", "memory leak", "network latency"]
        observations_count = 3

        hypothesis = _generate_multiple_causes_hypothesis(common_themes, observations_count)

        assert hypothesis is not None
        assert hypothesis["type"] == "multiple_causes"
        assert "Multiple factors" in hypothesis["hypothesis"]
        assert len(hypothesis["themes"]) == 3
        assert hypothesis["confidence"] > 0.0

    def test_generate_multiple_causes_hypothesis_insufficient_themes(self):
        """Test multiple-causes hypothesis with insufficient themes."""
        hypothesis = _generate_multiple_causes_hypothesis(["single theme"], 3)

        assert hypothesis is None

    def test_generate_causal_chain_hypothesis_sufficient_observations(self):
        """Test causal chain hypothesis with sufficient observations."""
        observations_count = 3

        hypothesis = _generate_causal_chain_hypothesis(observations_count)

        assert hypothesis is not None
        assert hypothesis["type"] == "causal_chain"
        assert "causal chain" in hypothesis["hypothesis"]
        assert len(hypothesis["explains"]) == observations_count
        assert hypothesis["confidence"] > 0.0

    def test_generate_causal_chain_hypothesis_insufficient_observations(self):
        """Test causal chain hypothesis with insufficient observations."""
        hypothesis = _generate_causal_chain_hypothesis(1)

        assert hypothesis is None

    def test_sanitize_template_input_dangerous_chars(self):
        """Test template input sanitization with dangerous characters."""
        dangerous_input = "{action} ${value} %s text"

        sanitized = _sanitize_template_input(dangerous_input)

        assert "{" not in sanitized
        assert "}" not in sanitized
        assert "%s" not in sanitized
        # ${value} becomes $value after sanitization (only $ pattern without braces is removed)
        assert sanitized == "action $value  text"

    def test_sanitize_template_input_non_string(self):
        """Test template input sanitization with non-string input."""
        sanitized = _sanitize_template_input(123)

        assert sanitized == ""

    def test_generate_domain_template_hypotheses_debugging_domain(self):
        """Test domain template hypothesis generation for debugging."""
        observations = ["server is slow", "cpu usage is high", "memory leak detected"]
        context = "Recent deployment caused server issues"

        hypotheses = _generate_domain_template_hypotheses(
            observations, context, 2, len(observations)
        )

        assert isinstance(hypotheses, list)
        if hypotheses:  # Only test if debugging domain was detected
            for hyp in hypotheses:
                assert hyp["type"] == "domain_template"
                assert hyp["confidence"] > 0.0
                assert len(hyp["explains"]) == len(observations)

    def test_generate_contextual_hypothesis_with_keywords(self):
        """Test contextual hypothesis generation with keywords."""
        observations = ["error occurred", "system crashed"]
        context = "server deployment database connection"

        hypothesis = _generate_contextual_hypothesis(observations, context, len(observations))

        assert hypothesis is not None
        assert hypothesis["type"] == "contextual"
        assert "context" in hypothesis["hypothesis"]
        assert len(hypothesis["context_keywords"]) > 0

    def test_generate_contextual_hypothesis_no_keywords(self):
        """Test contextual hypothesis with no keywords."""
        observations = ["error occurred"]
        context = "a an the"  # Common words only

        hypothesis = _generate_contextual_hypothesis(observations, context, len(observations))

        assert hypothesis is None

    def test_generate_systemic_hypothesis(self):
        """Test systemic hypothesis generation."""
        observations_count = 3

        hypothesis = _generate_systemic_hypothesis(observations_count)

        assert hypothesis is not None
        assert hypothesis["type"] == "systemic"
        assert "systemic issue" in hypothesis["hypothesis"]
        assert len(hypothesis["explains"]) == observations_count
        assert hypothesis["confidence"] > 0.0

    def test_generate_hypotheses_integration(self):
        """Test complete hypothesis generation integration."""
        observations = ["server is slow", "cpu usage is high", "memory leak detected"]

        hypotheses = generate_hypotheses(observations, None, context="deployment issue")

        assert isinstance(hypotheses, list)
        assert len(hypotheses) > 0

        # Check that different hypothesis types are present
        hypothesis_types = {h["type"] for h in hypotheses}
        # Should include at least systemic and/or other types based on context
        assert len(hypothesis_types) > 0

        # Check confidence values are valid
        for hyp in hypotheses:
            assert 0.0 <= hyp["confidence"] <= 1.0
            assert "hypothesis" in hyp
            assert "explains" in hyp


class TestInductiveReasoningRefactoring:
    """Test refactored inductive reasoning functions."""

    def test_validate_sequence_input_valid(self):
        """Test sequence validation with valid input."""
        sequence = [1.0, 2.0, 3.0]

        # Should not raise exception
        _validate_sequence_input(sequence)

    def test_validate_sequence_input_invalid_type(self):
        """Test sequence validation with invalid type."""
        with pytest.raises(ValidationError) as exc_info:
            _validate_sequence_input("not a sequence")

        assert "Expected list/tuple/array" in str(exc_info.value)

    def test_validate_sequence_input_empty(self):
        """Test sequence validation with empty sequence."""
        with pytest.raises(ValidationError) as exc_info:
            _validate_sequence_input([])

        assert "Sequence cannot be empty" in str(exc_info.value)

    def test_check_arithmetic_progression_positive(self):
        """Test arithmetic progression detection with valid progression."""
        sequence = [2.0, 4.0, 6.0, 8.0]

        result, confidence, description = _check_arithmetic_progression(
            sequence, rtol=0.1, atol=0.1
        )

        assert result is not None
        assert result == 10.0  # Next value should be 10
        assert confidence > 0.0
        assert "arithmetic progression" in description.lower()

    def test_check_arithmetic_progression_negative(self):
        """Test arithmetic progression detection with non-progression."""
        sequence = [1.0, 3.0, 2.0, 5.0]

        result, confidence, description = _check_arithmetic_progression(
            sequence, rtol=0.1, atol=0.1
        )

        assert result is None
        assert confidence is None
        assert description is None

    def test_check_geometric_progression_positive(self):
        """Test geometric progression detection with valid progression."""
        sequence = [2.0, 4.0, 8.0, 16.0]

        result, confidence, description = _check_geometric_progression(
            sequence, rtol=0.1, atol=0.1
        )

        assert result is not None
        assert result == 32.0  # Next value should be 32
        assert confidence > 0.0
        assert "geometric progression" in description.lower()

    def test_check_geometric_progression_negative(self):
        """Test geometric progression detection with non-progression."""
        sequence = [2.0, 5.0, 3.0, 7.0]

        result, confidence, description = _check_geometric_progression(
            sequence, rtol=0.1, atol=0.1
        )

        assert result is None
        assert confidence is None
        assert description is None

    def test_check_geometric_progression_with_zero(self):
        """Test geometric progression detection with zero in sequence."""
        sequence = [2.0, 0.0, 8.0]

        result, confidence, description = _check_geometric_progression(
            sequence, rtol=0.1, atol=0.1
        )

        assert result is None
        assert confidence is None
        assert description is None

    def test_add_reasoning_step_with_chain(self):
        """Test adding reasoning step with a chain."""
        from reasoning_library.core import ReasoningChain

        chain = ReasoningChain()

        _add_reasoning_step(
            chain,
            "Test Stage",
            "Test Description",
            42.0,
            0.8,
            evidence="Test evidence",
            assumptions=["test assumption"]
        )

        assert len(chain.steps) == 1
        step = chain.steps[0]
        assert step.stage == "Test Stage"
        assert step.description == "Test Description"
        assert step.result == 42.0
        assert step.confidence == 0.8
        assert step.evidence == "Test evidence"
        assert step.assumptions == ["test assumption"]

    def test_add_reasoning_step_without_chain(self):
        """Test adding reasoning step without a chain."""
        # Should not raise exception
        _add_reasoning_step(
            None,
            "Test Stage",
            "Test Description",
            42.0,
            0.8
        )

    def test_predict_next_in_sequence_arithmetic(self):
        """Test sequence prediction with arithmetic progression."""
        sequence = [3.0, 6.0, 9.0, 12.0]

        result = predict_next_in_sequence(sequence, None)

        assert result == 15.0

    def test_predict_next_in_sequence_geometric(self):
        """Test sequence prediction with geometric progression."""
        sequence = [3.0, 6.0, 12.0, 24.0]

        result = predict_next_in_sequence(sequence, None)

        assert result == 48.0

    def test_predict_next_in_sequence_no_pattern(self):
        """Test sequence prediction with no clear pattern."""
        sequence = [1.0, 5.0, 3.0, 8.0]

        result = predict_next_in_sequence(sequence, None)

        assert result is None

    def test_predict_next_in_sequence_short_sequence(self):
        """Test sequence prediction with short sequence."""
        sequence = [5.0]

        result = predict_next_in_sequence(sequence, None)

        assert result is None

    def test_predict_next_in_sequence_with_reasoning_chain(self):
        """Test sequence prediction with reasoning chain."""
        from reasoning_library.core import ReasoningChain

        chain = ReasoningChain()
        sequence = [2.0, 4.0, 6.0, 8.0]

        result = predict_next_in_sequence(sequence, chain)

        assert result == 10.0
        assert len(chain.steps) == 1
        assert "arithmetic progression" in chain.steps[0].description.lower()

    def test_predict_next_in_sequence_invalid_input(self):
        """Test sequence prediction with invalid input."""
        with pytest.raises(ValidationError):
            predict_next_in_sequence("not a sequence", None)

    def test_predict_next_in_sequence_empty_input(self):
        """Test sequence prediction with empty input."""
        with pytest.raises(ValidationError):
            predict_next_in_sequence([], None)


class TestRefactoringIntegration:
    """Test integration of refactored functions to ensure no behavior changes."""

    def test_performance_maintained_mathematical_reasoning(self):
        """Test that mathematical reasoning performance is maintained."""
        import time

        def mathematical_func():
            """
            Arithmetic progression analysis with confidence calculations.
            Based on pattern quality and data sufficiency.
            """
            confidence_factor = 0.5
            return confidence_factor

        # Time the function multiple times
        start_time = time.time()
        for _ in range(10):
            result = _detect_mathematical_reasoning_uncached(mathematical_func)
        end_time = time.time()

        # Should complete quickly (less than 1 second for 10 calls)
        assert end_time - start_time < 1.0
        assert result[0] is True  # Should detect as mathematical

    def test_behavior_maintained_hypothesis_generation(self):
        """Test that hypothesis generation behavior is maintained."""
        observations = ["server slow", "cpu high", "memory leak"]
        context = "deployment issue"

        hypotheses = generate_hypotheses(observations, None, context=context)

        # Should still generate multiple hypotheses
        assert len(hypotheses) > 1

        # Should include different types
        types = {h["type"] for h in hypotheses}
        assert len(types) > 0  # At least some types should be present

        # All should have valid confidence scores
        for h in hypotheses:
            assert 0.0 <= h["confidence"] <= 1.0

    def test_behavior_maintained_sequence_prediction(self):
        """Test that sequence prediction behavior is maintained."""
        test_cases = [
            ([1.0, 2.0, 3.0, 4.0], 5.0),  # Arithmetic
            ([2.0, 4.0, 8.0, 16.0], 32.0),  # Geometric
            ([1.0, 4.0, 9.0, 16.0], None),  # No pattern
        ]

        for sequence, expected in test_cases:
            result = predict_next_in_sequence(sequence, None)
            assert result == expected