"""
Tests for the constants module.

This test suite verifies that all constants have appropriate values,
are well-documented, and maintain backward compatibility.
"""

import pytest
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from reasoning_library.constants import *


class TestSecurityConstants:
    """Test security-related constants."""

    def test_max_sequence_length(self):
        """Test MAX_SEQUENCE_LENGTH constant."""
        assert isinstance(MAX_SEQUENCE_LENGTH, int)
        assert MAX_SEQUENCE_LENGTH > 0
        assert MAX_SEQUENCE_LENGTH == 10000  # Verify expected value

    def test_computation_timeout(self):
        """Test COMPUTATION_TIMEOUT constant."""
        assert isinstance(COMPUTATION_TIMEOUT, (int, float))
        assert COMPUTATION_TIMEOUT > 0
        assert COMPUTATION_TIMEOUT == 5.0

    def test_max_memory_elements(self):
        """Test MAX_MEMORY_ELEMENTS constant."""
        assert isinstance(MAX_MEMORY_ELEMENTS, int)
        assert MAX_MEMORY_ELEMENTS > 0
        assert MAX_MEMORY_ELEMENTS == 5000

    def test_value_magnitude_limit(self):
        """Test VALUE_MAGNITUDE_LIMIT constant."""
        assert isinstance(VALUE_MAGNITUDE_LIMIT, (int, float))
        assert VALUE_MGITUDE_LIMIT > 0
        assert VALUE_MAGNITUDE_LIMIT == 1e15


class TestPerformanceConstants:
    """Test performance optimization constants."""

    def test_large_sequence_threshold(self):
        """Test LARGE_SEQUENCE_THRESHOLD constant."""
        assert isinstance(LARGE_SEQUENCE_THRESHOLD, int)
        assert LARGE_SEQUENCE_THRESHOLD > 0
        assert LARGE_SEQUENCE_THRESHOLD == 100

    def test_early_exit_tolerance(self):
        """Test EARLY_EXIT_TOLERANCE constant."""
        assert isinstance(EARLY_EXIT_TOLERANCE, (int, float))
        assert EARLY_EXIT_TOLERANCE > 0
        assert EARLY_EXIT_TOLERANCE == 1e-12

    def test_max_cache_size(self):
        """Test MAX_CACHE_SIZE constant."""
        assert isinstance(MAX_CACHE_SIZE, int)
        assert MAX_CACHE_SIZE > 0
        assert MAX_CACHE_SIZE == 1000

    def test_max_registry_size(self):
        """Test MAX_REGISTRY_SIZE constant."""
        assert isinstance(MAX_REGISTRY_SIZE, int)
        assert MAX_REGISTRY_SIZE > 0
        assert MAX_REGISTRY_SIZE == 500


class TestConfidenceConstants:
    """Test confidence calculation constants."""

    def test_base_confidence_values(self):
        """Test all base confidence constants are in valid range."""
        confidence_constants = [
            BASE_CONFIDENCE_ARITHMETIC,
            BASE_CONFIDENCE_GEOMETRIC,
            BASE_CONFIDENCE_ABDUCTIVE,
            BASE_CONFIDENCE_CHAIN_OF_THOUGHT,
            BASE_CONFIDENCE_DEDUCTIVE,
            BASE_CONFIDENCE_TEMPLATE_HYPOTHESIS,
            BASE_CONFIDENCE_RECURSIVE,
            BASE_CONFIDENCE_POLYNOMIAL,
            BASE_CONFIDENCE_EXPONENTIAL,
            BASE_CONFIDENCE_PATTERN_DESCRIPTION,
        ]

        for confidence in confidence_constants:
            assert isinstance(confidence, (int, float))
            assert CONFIDENCE_MIN <= confidence <= CONFIDENCE_MAX
            assert confidence >= 0.0
            assert confidence <= 1.0

    def test_confidence_boundaries(self):
        """Test confidence boundary constants."""
        assert CONFIDENCE_MIN == 0.0
        assert CONFIDENCE_MAX == 1.0
        assert CONFIDENCE_MIN < CONFIDENCE_MAX

    def test_complexity_scores(self):
        """Test complexity score constants."""
        assert isinstance(COMPLEXITY_SCORE_ARITHMETIC, (int, float))
        assert isinstance(COMPLEXITY_SCORE_GEOMETRIC, (int, float))
        assert isinstance(COMPLEXITY_SCORE_RECURSIVE, (int, float))

        # Arithmetic should be simplest (lowest complexity)
        assert COMPLEXITY_SCORE_ARITHMETIC < COMPLEXITY_SCORE_GEOMETRIC
        assert COMPLEXITY_SCORE_GEOMETRIC < COMPLEXITY_SCORE_RECURSIVE


class TestToleranceConstants:
    """Test tolerance and threshold constants."""

    def test_pattern_detection_tolerances(self):
        """Test pattern detection tolerance constants."""
        assert isinstance(RELATIVE_TOLERANCE_DEFAULT, (int, float))
        assert isinstance(ABSOLUTE_TOLERANCE_DEFAULT, (int, float))
        assert isinstance(ABSOLUTE_TOLERANCE_PATTERN, (int, float))
        assert isinstance(NUMERICAL_STABILITY_THRESHOLD, (int, float))

        # All tolerances should be positive
        assert RELATIVE_TOLERANCE_DEFAULT > 0
        assert ABSOLUTE_TOLERANCE_DEFAULT > 0
        assert ABSOLUTE_TOLERANCE_PATTERN > 0
        assert NUMERICAL_STABILITY_THRESHOLD > 0

    def test_evidence_support_thresholds(self):
        """Test evidence support threshold constants."""
        assert isinstance(EVIDENCE_SUPPORT_HIGH_THRESHOLD, (int, float))
        assert isinstance(EVIDENCE_SUPPORT_MODERATE_THRESHOLD, (int, float))

        # High threshold should be higher than moderate
        assert EVIDENCE_SUPPORT_HIGH_THRESHOLD > EVIDENCE_SUPPORT_MODERATE_THRESHOLD

        # Both should be in valid range
        assert 0.0 <= EVIDENCE_SUPPORT_MODERATE_THRESHOLD <= 1.0
        assert 0.0 <= EVIDENCE_SUPPORT_HIGH_THRESHOLD <= 1.0


class TestTextProcessingConstants:
    """Test text processing limit constants."""

    def test_text_length_limits(self):
        """Test text length limit constants."""
        length_limits = [
            MAX_OBSERVATION_LENGTH,
            MAX_CONTEXT_LENGTH,
            KEYWORD_EXTRACTION_OBSERVATION_LIMIT,
            KEYWORD_EXTRACTION_CONTEXT_LIMIT,
            DOMAIN_DETECTION_LIMIT,
            KEYWORD_LENGTH_LIMIT,
            COMPONENT_LENGTH_LIMIT,
            ISSUE_LENGTH_LIMIT,
            HYPOTHESIS_TEXT_HARD_LIMIT,
        ]

        for limit in length_limits:
            assert isinstance(limit, int)
            assert limit > 0

    def test_keyword_length_relationships(self):
        """Test relationships between keyword length constants."""
        # Component should be longer than keyword
        assert COMPONENT_LENGTH_LIMIT >= KEYWORD_LENGTH_LIMIT

        # Issue should be longer than component
        assert ISSUE_LENGTH_LIMIT >= COMPONENT_LENGTH_LIMIT

        # Hypothesis limit should be much longer than individual components
        assert HYPOTHESIS_TEXT_HARD_LIMIT > ISSUE_LENGTH_LIMIT


class TestDataSufficiencyConstants:
    """Test data sufficiency threshold constants."""

    def test_minimum_requirements(self):
        """Test minimum data point requirements."""
        minimums = [
            DATA_SUFFICIENCY_MINIMUM_ARITHMETIC,
            DATA_SUFFICIENCY_MINIMUM_GEOMETRIC,
            DATA_SUFFICIENCY_MINIMUM_DEFAULT,
            DATA_SUFFICIENCY_MINIMUM_RECURSIVE,
            DATA_SUFFICIENCY_MINIMUM_FIBONACCI,
            DATA_SUFFICIENCY_MINIMUM_LUCAS,
            DATA_SUFFICIENCY_MINIMUM_TRIBONACCI,
            DATA_SUFFICIENCY_MINIMUM_POLYNOMIAL,
        ]

        for minimum in minimums:
            assert isinstance(minimum, int)
            assert minimum > 0

    def test_recursive_requirements(self):
        """Test recursive pattern requirements."""
        # Recursive patterns should require more data than simple patterns
        assert DATA_SUFFICIENCY_MINIMUM_RECURSIVE > DATA_SUFFICIENCY_MINIMUM_ARITHMETIC
        assert DATA_SUFFICIENCY_MINIMUM_RECURSIVE > DATA_SUFFICIENCY_MINIMUM_GEOMETRIC

        # Tribonacci should require more than Fibonacci
        assert DATA_SUFFICIENCY_MINIMUM_TRIBONACCI > DATA_SUFFICIENCY_MINIMUM_FIBONACCI


class TestPatternQualityConstants:
    """Test pattern quality factor constants."""

    def test_quality_factors(self):
        """Test pattern quality factor constants."""
        factors = [
            PATTERN_QUALITY_MINIMAL_DATA,
            PATTERN_QUALITY_GEOMETRIC_MINIMUM,
            PATTERN_QUALITY_DEFAULT_UNKNOWN,
        ]

        for factor in factors:
            assert isinstance(factor, (int, float))
            assert 0.0 <= factor <= 1.0

        # Minimal data should be better than geometric minimum
        assert PATTERN_QUALITY_MINIMAL_DATA > PATTERN_QUALITY_GEOMETRIC_MINIMUM


class TestCacheManagementConstants:
    """Test cache management constants."""

    def test_eviction_fractions(self):
        """Test cache eviction fraction constants."""
        assert isinstance(CACHE_EVICTION_FRACTION, (int, float))
        assert isinstance(REGISTRY_EVICTION_FRACTION, (int, float))

        # Fractions should be between 0 and 1
        assert 0.0 < CACHE_EVICTION_FRACTION <= 1.0
        assert 0.0 < REGISTRY_EVICTION_FRACTION <= 1.0

        # Should be reasonable fractions
        assert 0.1 <= CACHE_EVICTION_FRACTION <= 0.5
        assert 0.1 <= REGISTRY_EVICTION_FRACTION <= 0.5


class TestHypothesisGenerationConstants:
    """Test hypothesis generation constants."""

    def test_generation_limits(self):
        """Test hypothesis generation limit constants."""
        assert isinstance(MAX_HYPOTHESES_DEFAULT, int)
        assert isinstance(MAX_THEMES_RETURNED, int)
        assert isinstance(THEME_FREQUENCY_THRESHOLD, int)
        assert isinstance(MAX_TEMPLATE_KEYWORDS, int)

        # All should be positive
        assert MAX_HYPOTHESES_DEFAULT > 0
        assert MAX_THEMES_RETURNED > 0
        assert THEME_FREQUENCY_THRESHOLD > 0
        assert MAX_TEMPLATE_KEYWORDS > 0

    def test_keyword_length(self):
        """Test minimum keyword length constant."""
        assert isinstance(MIN_KEYWORD_LENGTH, int)
        assert MIN_KEYWORD_LENGTH > 0
        assert MIN_KEYWORD_LENGTH == 3


class TestPolynomialConstants:
    """Test polynomial fitting constants."""

    def test_polynomial_parameters(self):
        """Test polynomial fitting parameters."""
        assert isinstance(MAX_POLYNOMIAL_DEGREE_DEFAULT, int)
        assert isinstance(POLYNOMIAL_R_SQUARED_THRESHOLD, (int, float))
        assert isinstance(POLYNOMIAL_COEFFICIENT_TOLERANCE, (int, float))
        assert isinstance(COEFFICIENT_OF_VARIATION_DECAY_FACTOR, (int, float))

        # Reasonable values
        assert MAX_POLYNOMIAL_DEGREE_DEFAULT > 0
        assert 0.0 <= POLYNOMIAL_R_SQUARED_THRESHOLD <= 1.0
        assert POLYNOMIAL_COEFFICIENT_TOLERANCE > 0
        assert COEFFICIENT_OF_VARIATION_DECAY_FACTOR > 0


class TestRegexConstants:
    """Test regular expression constants."""

    def test_regex_limits(self):
        """Test regex pattern limits."""
        assert isinstance(REGEX_WORD_CHAR_MAX, int)
        assert isinstance(REGEX_SPACING_MAX, int)

        # Should be reasonable limits
        assert REGEX_WORD_CHAR_MAX > 0
        assert REGEX_SPACING_MAX > 0
        assert REGEX_WORD_CHAR_MAX <= 100  # Reasonable upper bound
        assert REGEX_SPACING_MAX <= 50     # Reasonable upper bound


class TestConstantDocumentation:
    """Test that constants have proper documentation."""

    def test_constants_have_docstrings(self):
        """Test that the constants module has a docstring."""
        import reasoning_library.constants as constants_module
        assert constants_module.__doc__ is not None
        assert len(constants_module.__doc__.strip()) > 0
        assert "constants" in constants_module.__doc__.lower()


class TestBackwardCompatibility:
    """Test backward compatibility of constants."""

    def test_expected_values(self):
        """Test that constants maintain expected values for backward compatibility."""
        # Security constants
        assert MAX_SEQUENCE_LENGTH == 10000
        assert COMPUTATION_TIMEOUT == 5.0
        assert MAX_MEMORY_ELEMENTS == 5000
        assert VALUE_MAGNITUDE_LIMIT == 1e15

        # Performance constants
        assert LARGE_SEQUENCE_THRESHOLD == 100
        assert EARLY_EXIT_TOLERANCE == 1e-12
        assert MAX_CACHE_SIZE == 1000
        assert MAX_REGISTRY_SIZE == 500
        assert MAX_CONVERSATIONS == 1000

        # Base confidence values
        assert BASE_CONFIDENCE_ARITHMETIC == 0.95
        assert BASE_CONFIDENCE_GEOMETRIC == 0.95
        assert BASE_CONFIDENCE_ABDUCTIVE == 0.7
        assert BASE_CONFIDENCE_CHAIN_OF_THOUGHT == 0.8
        assert BASE_CONFIDENCE_DEDUCTIVE == 1.0
        assert BASE_CONFIDENCE_TEMPLATE_HYPOTHESIS == 0.6
        assert BASE_CONFIDENCE_RECURSIVE == 0.9
        assert BASE_CONFIDENCE_POLYNOMIAL == 0.85
        assert BASE_CONFIDENCE_EXPONENTIAL == 0.9
        assert BASE_CONFIDENCE_PATTERN_DESCRIPTION == 0.9

        # Complexity scores
        assert COMPLEXITY_SCORE_ARITHMETIC == 0.0
        assert COMPLEXITY_SCORE_GEOMETRIC == 0.1
        assert COMPLEXITY_SCORE_RECURSIVE == 0.3
        assert COMPLEXITY_SCORE_POLYNOMIAL_DEGREE_FACTOR == 0.1

        # Tolerances
        assert RELATIVE_TOLERANCE_DEFAULT == 0.2
        assert ABSOLUTE_TOLERANCE_DEFAULT == 1e-8
        assert ABSOLUTE_TOLERANCE_PATTERN == 1e-10
        assert NUMERICAL_STABILITY_THRESHOLD == 1e-10

        # Confidence boundaries
        assert CONFIDENCE_MIN == 0.0
        assert CONFIDENCE_MAX == 1.0

        # Evidence support thresholds
        assert EVIDENCE_SUPPORT_HIGH_THRESHOLD == 0.7
        assert EVIDENCE_SUPPORT_MODERATE_THRESHOLD == 0.3

        # Text processing limits
        assert MAX_OBSERVATION_LENGTH == 10000
        assert MAX_CONTEXT_LENGTH == 5000
        assert KEYWORD_EXTRACTION_OBSERVATION_LIMIT == 1000
        assert KEYWORD_EXTRACTION_CONTEXT_LIMIT == 500
        assert DOMAIN_DETECTION_LIMIT == 50000
        assert KEYWORD_LENGTH_LIMIT == 50
        assert COMPONENT_LENGTH_LIMIT == 50
        assert ISSUE_LENGTH_LIMIT == 100
        assert HYPOTHESIS_TEXT_HARD_LIMIT == 500

        # Hypothesis generation
        assert MAX_HYPOTHESES_DEFAULT == 5
        assert MAX_THEMES_RETURNED == 10
        assert THEME_FREQUENCY_THRESHOLD == 2
        assert MAX_TEMPLATE_KEYWORDS == 3

        # Data sufficiency
        assert DATA_SUFFICIENCY_MINIMUM_ARITHMETIC == 4
        assert DATA_SUFFICIENCY_MINIMUM_GEOMETRIC == 4
        assert DATA_SUFFICIENCY_MINIMUM_DEFAULT == 3
        assert DATA_SUFFICIENCY_MINIMUM_RECURSIVE == 5
        assert DATA_SUFFICIENCY_MINIMUM_FIBONACCI == 5
        assert DATA_SUFFICIENCY_MINIMUM_LUCAS == 5
        assert DATA_SUFFICIENCY_MINIMUM_TRIBONACCI == 6
        assert DATA_SUFFICIENCY_MINIMUM_POLYNOMIAL == 2

        # Pattern quality
        assert PATTERN_QUALITY_MINIMAL_DATA == 0.7
        assert PATTERN_QUALITY_GEOMETRIC_MINIMUM == 0.1
        assert PATTERN_QUALITY_DEFAULT_UNKNOWN == 0.5

        # Statistical factors
        assert COEFFICIENT_OF_VARIATION_DECAY_FACTOR == 2.0

        # Cache management
        assert CACHE_EVICTION_FRACTION == 0.25
        assert REGISTRY_EVICTION_FRACTION == 0.25

        # Regex limits
        assert REGEX_WORD_CHAR_MAX == 30
        assert REGEX_SPACING_MAX == 10

        # Input validation
        assert MIN_KEYWORD_LENGTH == 3

        # Polynomial fitting
        assert MAX_POLYNOMIAL_DEGREE_DEFAULT == 3
        assert POLYNOMIAL_R_SQUARED_THRESHOLD == 0.95
        assert POLYNOMIAL_COEFFICIENT_TOLERANCE == 1e-6

        # Alternating patterns
        assert ALTERNATING_PATTERN_MIN_DIFFS == 4
        assert ALTERNATING_TOLERANCE == 0.1
        assert ALTERNATING_CONFIDENCE == 0.8
        assert PERIODIC_PATTERN_CONFIDENCE == 0.85

        # Domain detection
        assert MIN_OBSERVATIONS_FOR_DOMAIN_DETECTION == 6
        assert MAX_PATTERN_PERIOD == 5


class TestConstantTypes:
    """Test that constants have appropriate types."""

    def test_integer_constants(self):
        """Test that integer constants are actually integers."""
        integer_constants = [
            MAX_SEQUENCE_LENGTH,
            MAX_MEMORY_ELEMENTS,
            LARGE_SEQUENCE_THRESHOLD,
            MAX_CACHE_SIZE,
            MAX_REGISTRY_SIZE,
            MAX_CONVERSATIONS,
            KEYWORD_LENGTH_LIMIT,
            COMPONENT_LENGTH_LIMIT,
            ISSUE_LENGTH_LIMIT,
            HYPOTHESIS_TEXT_HARD_LIMIT,
            MAX_HYPOTHESES_DEFAULT,
            MAX_THEMES_RETURNED,
            THEME_FREQUENCY_THRESHOLD,
            MAX_TEMPLATE_KEYWORDS,
            DATA_SUFFICIENCY_MINIMUM_ARITHMETIC,
            DATA_SUFFICIENCY_MINIMUM_GEOMETRIC,
            DATA_SUFFICIENCY_MINIMUM_DEFAULT,
            DATA_SUFFICIENCY_MINIMUM_RECURSIVE,
            DATA_SUFFICIENCY_MINIMUM_FIBONACCI,
            DATA_SUFFICIENCY_MINIMUM_LUCAS,
            DATA_SUFFICIENCY_MINIMUM_TRIBONACCI,
            DATA_SUFFICIENCY_MINIMUM_POLYNOMIAL,
            MIN_KEYWORD_LENGTH,
            REGEX_WORD_CHAR_MAX,
            REGEX_SPACING_MAX,
            MAX_POLYNOMIAL_DEGREE_DEFAULT,
            ALTERNATING_PATTERN_MIN_DIFFS,
            MIN_OBSERVATIONS_FOR_DOMAIN_DETECTION,
            MAX_PATTERN_PERIOD,
        ]

        for constant in integer_constants:
            assert isinstance(constant, int), f"{constant} should be an integer"

    def test_float_constants(self):
        """Test that float constants are actually floats."""
        float_constants = [
            COMPUTATION_TIMEOUT,
            VALUE_MAGNITUDE_LIMIT,
            EARLY_EXIT_TOLERANCE,
            RELATIVE_TOLERANCE_DEFAULT,
            ABSOLUTE_TOLERANCE_DEFAULT,
            ABSOLUTE_TOLERANCE_PATTERN,
            NUMERICAL_STABILITY_THRESHOLD,
            EVIDENCE_SUPPORT_HIGH_THRESHOLD,
            EVIDENCE_SUPPORT_MODERATE_THRESHOLD,
            POLYNOMIAL_COEFFICIENT_TOLERANCE,
            COEFFICIENT_OF_VARIATION_DECAY_FACTOR,
            ALTERNATING_TOLERANCE,
        ]

        for constant in float_constants:
            assert isinstance(constant, (int, float)), f"{constant} should be a number"
            # Convert to float for comparison
            assert float(constant) >= 0.0, f"{constant} should be non-negative"


if __name__ == "__main__":
    pytest.main([__file__])