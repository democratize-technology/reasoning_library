"""
Comprehensive Test Suite for Inductive Reasoning Confidence Scoring.

This module tests the mathematical correctness of confidence scoring in inductive reasoning,
ensuring that:
1. Confidence varies 0.0-1.0 based on pattern strength and data sufficiency
2. Perfect patterns have high confidence (approaching 1.0)
3. Noisy patterns have lower confidence
4. Insufficient data reduces confidence appropriately
5. Statistical validation of confidence calculation formulas
"""

import pytest
import numpy as np
from typing import List, Any
import sys
import os
import math

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from reasoning_library.inductive import (
        predict_next_in_sequence,
        find_pattern_description,
        _calculate_arithmetic_confidence,
        _calculate_geometric_confidence,
        _assess_data_sufficiency,
        _calculate_pattern_quality_score
    )
    from reasoning_library.core import ReasoningChain
except ImportError:
    # Fallback for direct execution
    from inductive import (
        predict_next_in_sequence,
        find_pattern_description,
        _calculate_arithmetic_confidence,
        _calculate_geometric_confidence,
        _assess_data_sufficiency,
        _calculate_pattern_quality_score
    )
    from core import ReasoningChain


class TestArithmeticProgressionConfidence:
    """Test confidence scoring for arithmetic progression detection."""

    def test_perfect_arithmetic_progression_high_confidence(self):
        """Test that perfect arithmetic progressions have high confidence (>0.9)."""
        # Perfect arithmetic progressions with different common differences
        perfect_sequences = [
            [1, 2, 3, 4, 5],           # Common difference: 1
            [0, 5, 10, 15, 20],        # Common difference: 5
            [10, 7, 4, 1, -2],         # Common difference: -3
            [1.5, 2.5, 3.5, 4.5],     # Common difference: 1.0 (floats)
            [-10, -5, 0, 5, 10, 15],   # Common difference: 5 (longer sequence)
        ]

        for sequence in perfect_sequences:
            chain = ReasoningChain()
            result = predict_next_in_sequence(sequence, reasoning_chain=chain)

            assert result is not None, f"Should predict next value for perfect sequence: {sequence}"
            assert len(chain.steps) == 1, "Should add exactly one step to reasoning chain"

            confidence = chain.steps[0].confidence
            assert confidence > 0.9, f"Perfect arithmetic progression {sequence} should have high confidence (>0.9), got {confidence}"
            assert confidence <= 1.0, f"Confidence should not exceed 1.0, got {confidence}"

    def test_noisy_arithmetic_progression_lower_confidence(self):
        """Test that noisy arithmetic progressions have lower confidence."""
        # Noisy arithmetic progressions (should still be detected but with lower confidence)
        noisy_sequences = [
            [1, 2.1, 2.9, 4.1, 4.9],      # Small noise around arithmetic progression
            [0, 4.8, 10.2, 14.9, 20.1],   # Moderate noise
            [10, 6.5, 4.2, 0.8, -2.3],    # Negative progression with noise
        ]

        for sequence in noisy_sequences:
            chain = ReasoningChain()
            result = predict_next_in_sequence(sequence, reasoning_chain=chain, rtol=0.3)

            # Should still detect pattern but with lower confidence
            if result is not None:  # Pattern detected
                confidence = chain.steps[0].confidence
                assert 0.1 <= confidence < 0.9, f"Noisy arithmetic progression {sequence} should have moderate confidence (0.1-0.9), got {confidence}"

    def test_data_sufficiency_impact_on_confidence(self):
        """Test that data sufficiency affects confidence appropriately."""
        # Test sequences of different lengths with same pattern
        base_sequence = [2, 4, 6]  # Common difference: 2

        # Short sequence (minimal data)
        chain_short = ReasoningChain()
        predict_next_in_sequence(base_sequence, reasoning_chain=chain_short)
        conf_short = chain_short.steps[0].confidence

        # Longer sequence (more data)
        extended_sequence = base_sequence + [8, 10, 12, 14]
        chain_long = ReasoningChain()
        predict_next_in_sequence(extended_sequence, reasoning_chain=chain_long)
        conf_long = chain_long.steps[0].confidence

        assert conf_long >= conf_short, f"Longer sequence should have equal or higher confidence: {conf_short} vs {conf_long}"

    def test_arithmetic_confidence_calculation_internal(self):
        """Test internal arithmetic confidence calculation function."""
        # Perfect arithmetic progression differences
        perfect_diffs = np.array([2, 2, 2, 2])
        confidence = _calculate_arithmetic_confidence(perfect_diffs, len(perfect_diffs) + 1)

        assert 0.8 <= confidence <= 1.0, f"Perfect arithmetic differences should have high confidence, got {confidence}"

        # Noisy arithmetic progression differences
        noisy_diffs = np.array([2.1, 1.9, 2.05, 1.95])
        confidence_noisy = _calculate_arithmetic_confidence(noisy_diffs, len(noisy_diffs) + 1)

        assert confidence_noisy < confidence, "Noisy differences should have lower confidence than perfect differences"
        assert confidence_noisy > 0.0, "Should still have some confidence for reasonable noise"

    def test_edge_case_constant_sequence(self):
        """Test arithmetic progression with zero common difference (constant sequence)."""
        constant_sequences = [
            [5, 5, 5, 5],
            [0, 0, 0, 0, 0],
            [-3, -3, -3]
        ]

        for sequence in constant_sequences:
            chain = ReasoningChain()
            result = predict_next_in_sequence(sequence, reasoning_chain=chain)

            assert result == sequence[0], f"Constant sequence {sequence} should predict same value"
            confidence = chain.steps[0].confidence
            assert confidence > 0.9, f"Constant sequence should have high confidence, got {confidence}"


class TestGeometricProgressionConfidence:
    """Test confidence scoring for geometric progression detection."""

    def test_perfect_geometric_progression_high_confidence(self):
        """Test that perfect geometric progressions have high confidence (>0.8)."""
        # Perfect geometric progressions with different common ratios
        perfect_sequences = [
            [1, 2, 4, 8, 16],          # Common ratio: 2
            [3, 6, 12, 24, 48],        # Common ratio: 2 (different start)
            [100, 50, 25, 12.5],       # Common ratio: 0.5
            [2, 6, 18, 54, 162],       # Common ratio: 3
            [1, -2, 4, -8, 16],        # Common ratio: -2 (alternating signs)
        ]

        for sequence in perfect_sequences:
            chain = ReasoningChain()
            result = predict_next_in_sequence(sequence, reasoning_chain=chain)

            assert result is not None, f"Should predict next value for perfect geometric sequence: {sequence}"
            assert len(chain.steps) == 1, "Should add exactly one step to reasoning chain"

            confidence = chain.steps[0].confidence
            assert confidence > 0.8, f"Perfect geometric progression {sequence} should have high confidence (>0.8), got {confidence}"
            assert confidence <= 1.0, f"Confidence should not exceed 1.0, got {confidence}"

    def test_noisy_geometric_progression_lower_confidence(self):
        """Test that noisy geometric progressions have lower confidence."""
        # Noisy geometric progressions
        noisy_sequences = [
            [1, 2.1, 3.9, 8.2, 15.8],     # Approximate doubling with noise
            [3, 5.8, 12.3, 23.7, 48.9],   # Approximate doubling with noise
            [100, 49, 26, 12.2],          # Approximate halving with noise
        ]

        for sequence in noisy_sequences:
            chain = ReasoningChain()
            result = predict_next_in_sequence(sequence, reasoning_chain=chain, rtol=0.3)

            if result is not None:  # Pattern detected
                confidence = chain.steps[0].confidence
                assert 0.1 <= confidence < 0.9, f"Noisy geometric progression {sequence} should have moderate confidence (0.1-0.9), got {confidence}"

    def test_geometric_confidence_calculation_internal(self):
        """Test internal geometric confidence calculation function."""
        # Perfect geometric progression ratios
        perfect_ratios = [2.0, 2.0, 2.0, 2.0]
        confidence = _calculate_geometric_confidence(perfect_ratios, len(perfect_ratios) + 1)

        assert 0.7 <= confidence <= 1.0, f"Perfect geometric ratios should have high confidence, got {confidence}"

        # Noisy geometric progression ratios
        noisy_ratios = [2.1, 1.9, 2.05, 1.95]
        confidence_noisy = _calculate_geometric_confidence(noisy_ratios, len(noisy_ratios) + 1)

        assert confidence_noisy < confidence, "Noisy ratios should have lower confidence than perfect ratios"
        assert confidence_noisy > 0.0, "Should still have some confidence for reasonable noise"

    def test_geometric_edge_case_zero_elements(self):
        """Test geometric progression detection when sequence contains zeros."""
        sequences_with_zeros = [
            [0, 0, 0, 0],              # All zeros
            [1, 0, 2, 4],              # Zero in middle (should not detect geometric)
            [0, 1, 2, 4],              # Zero at start (should not detect geometric)
        ]

        for sequence in sequences_with_zeros:
            chain = ReasoningChain()
            result = predict_next_in_sequence(sequence, reasoning_chain=chain)

            # Should either not detect geometric pattern or handle gracefully
            if result is not None and len(chain.steps) > 0:
                # If pattern detected, it should be arithmetic, not geometric
                description = chain.steps[0].description
                assert "arithmetic" in description.lower() or "no simple pattern" in description.lower()


class TestDataSufficiencyAndPatternQuality:
    """Test internal functions for data sufficiency and pattern quality assessment."""

    def test_data_sufficiency_assessment(self):
        """Test data sufficiency factor calculation."""
        # Test arithmetic progression data sufficiency
        assert _assess_data_sufficiency(3, 'arithmetic') == 1.0, "3 points should be sufficient for arithmetic"
        assert _assess_data_sufficiency(2, 'arithmetic') < 1.0, "2 points should be insufficient for arithmetic"
        assert _assess_data_sufficiency(6, 'arithmetic') == 1.0, "6 points should be more than sufficient for arithmetic"

        # Test geometric progression data sufficiency
        assert _assess_data_sufficiency(4, 'geometric') == 1.0, "4 points should be sufficient for geometric"
        assert _assess_data_sufficiency(3, 'geometric') < 1.0, "3 points should be insufficient for geometric"
        assert _assess_data_sufficiency(8, 'geometric') == 1.0, "8 points should be more than sufficient for geometric"

    def test_pattern_quality_score_arithmetic(self):
        """Test pattern quality scoring for arithmetic progressions."""
        # Perfect arithmetic differences
        perfect_diffs = [2, 2, 2, 2]
        quality = _calculate_pattern_quality_score(perfect_diffs, 'arithmetic')
        assert quality > 0.9, f"Perfect arithmetic pattern should have high quality score, got {quality}"

        # Noisy arithmetic differences
        noisy_diffs = [2.1, 1.9, 2.05, 1.95]
        quality_noisy = _calculate_pattern_quality_score(noisy_diffs, 'arithmetic')
        assert quality_noisy < quality, "Noisy pattern should have lower quality score"
        assert quality_noisy > 0.1, "Should still have reasonable quality for moderate noise"

        # Very noisy differences
        very_noisy_diffs = [1, 5, 0.5, 10]
        quality_very_noisy = _calculate_pattern_quality_score(very_noisy_diffs, 'arithmetic')
        assert quality_very_noisy < quality_noisy, "Very noisy pattern should have lowest quality score"

    def test_pattern_quality_score_geometric(self):
        """Test pattern quality scoring for geometric progressions."""
        # Perfect geometric ratios
        perfect_ratios = [2.0, 2.0, 2.0, 2.0]
        quality = _calculate_pattern_quality_score(perfect_ratios, 'geometric')
        assert quality > 0.9, f"Perfect geometric pattern should have high quality score, got {quality}"

        # Noisy geometric ratios
        noisy_ratios = [2.1, 1.9, 2.05, 1.95]
        quality_noisy = _calculate_pattern_quality_score(noisy_ratios, 'geometric')
        assert quality_noisy < quality, "Noisy pattern should have lower quality score"
        assert quality_noisy > 0.1, "Should still have reasonable quality for moderate noise"

    def test_pattern_quality_edge_cases(self):
        """Test pattern quality assessment edge cases."""
        # Single value
        single_value = [5]
        quality_single = _calculate_pattern_quality_score(single_value, 'arithmetic')
        assert 0.1 <= quality_single <= 1.0, "Single value should have conservative quality score"

        # Empty array
        empty_array = []
        quality_empty = _calculate_pattern_quality_score(empty_array, 'arithmetic')
        assert 0.1 <= quality_empty <= 1.0, "Empty array should have conservative quality score"

        # Zero differences (constant sequence)
        zero_diffs = [0, 0, 0, 0]
        quality_zeros = _calculate_pattern_quality_score(zero_diffs, 'arithmetic')
        assert quality_zeros == 1.0, "Zero differences (constant sequence) should have perfect quality"


class TestPatternDescriptionConfidence:
    """Test confidence scoring for pattern description functionality."""

    def test_pattern_description_confidence_higher_than_prediction(self):
        """Test that pattern description has higher confidence than prediction (more conservative)."""
        test_sequences = [
            [1, 2, 3, 4, 5],           # Perfect arithmetic
            [2, 6, 18, 54],            # Perfect geometric
            [1.1, 2.0, 2.9, 4.1],     # Noisy arithmetic
        ]

        for sequence in test_sequences:
            pred_chain = ReasoningChain()
            desc_chain = ReasoningChain()

            # Get prediction confidence
            predict_next_in_sequence(sequence, reasoning_chain=pred_chain)

            # Get description confidence
            find_pattern_description(sequence, reasoning_chain=desc_chain)

            if len(pred_chain.steps) > 0 and len(desc_chain.steps) > 0:
                pred_confidence = pred_chain.steps[0].confidence
                desc_confidence = desc_chain.steps[0].confidence

                # Description should have equal or higher confidence (it's easier to describe than predict)
                assert desc_confidence >= pred_confidence, f"Description confidence {desc_confidence} should be >= prediction confidence {pred_confidence} for sequence {sequence}"


class TestConfidenceScoreMathematicalProperties:
    """Test mathematical properties of confidence scoring system."""

    def test_confidence_bounds_all_operations(self):
        """Test that all confidence scores are within valid bounds [0.0, 1.0]."""
        test_sequences = [
            [1, 2, 3, 4],                    # Perfect arithmetic
            [2, 4, 8, 16],                   # Perfect geometric
            [1.1, 2.1, 2.9, 4.2],          # Noisy arithmetic
            [1, 3, 7, 15, 31],              # No simple pattern
            [1],                             # Too short
            [],                              # Empty (should raise error)
        ]

        for sequence in test_sequences:
            if len(sequence) == 0:  # Skip empty sequence for this test
                continue

            chain = ReasoningChain()
            try:
                predict_next_in_sequence(sequence, reasoning_chain=chain)
                if len(chain.steps) > 0:
                    confidence = chain.steps[0].confidence
                    assert 0.0 <= confidence <= 1.0, f"Confidence {confidence} for sequence {sequence} is outside valid bounds [0.0, 1.0]"
            except (ValueError, TypeError):
                pass  # Expected for invalid inputs

    def test_confidence_monotonicity_with_pattern_strength(self):
        """Test that confidence increases with pattern strength."""
        # Create sequences with increasing pattern strength
        base_sequence = [1, 2, 3, 4]

        # Add noise with decreasing levels
        noise_levels = [0.5, 0.3, 0.1, 0.0]
        confidences = []

        for noise_level in noise_levels:
            # Add noise to the base sequence
            noisy_sequence = [val + np.random.uniform(-noise_level, noise_level) for val in base_sequence]

            chain = ReasoningChain()
            predict_next_in_sequence(noisy_sequence, reasoning_chain=chain, rtol=0.5)

            if len(chain.steps) > 0:
                confidences.append(chain.steps[0].confidence)

        # Confidence should generally increase as noise decreases (pattern becomes clearer)
        # Allow for some variance due to randomness, but overall trend should be increasing
        if len(confidences) >= 2:
            # Check that at least the cleanest pattern has higher confidence than the noisiest
            assert confidences[-1] >= confidences[0], "Clearest pattern should have higher confidence than noisiest"

    def test_confidence_formula_consistency(self):
        """Test that confidence calculation formulas are mathematically consistent."""
        # Test arithmetic progression confidence components
        sequence_length = 5
        perfect_diffs = np.array([2, 2, 2, 2])

        # Individual components
        data_sufficiency = _assess_data_sufficiency(sequence_length, 'arithmetic')
        pattern_quality = _calculate_pattern_quality_score(perfect_diffs, 'arithmetic')

        # Combined confidence
        confidence = _calculate_arithmetic_confidence(perfect_diffs, sequence_length)

        # Verify the formula: confidence = base_confidence * data_sufficiency * pattern_quality * complexity_factor
        base_confidence = 0.95
        complexity_factor = 1.0  # For arithmetic progression
        expected_confidence = min(1.0, max(0.0, base_confidence * data_sufficiency * pattern_quality * complexity_factor))

        assert abs(confidence - expected_confidence) < 0.01, f"Confidence calculation should match formula: expected {expected_confidence}, got {confidence}"

    def test_input_validation_confidence_impact(self):
        """Test that input validation errors don't affect confidence calculation integrity."""
        invalid_inputs = [
            "not a list",
            123,
            None,
            [None, 1, 2],
            ["a", "b", "c"],
        ]

        for invalid_input in invalid_inputs:
            with pytest.raises((TypeError, ValueError)):
                chain = ReasoningChain()
                predict_next_in_sequence(invalid_input, reasoning_chain=chain)


class TestEdgeCasesAndBoundaryConditions:
    """Test edge cases and boundary conditions for inductive reasoning confidence."""

    def test_extreme_values_sequences(self):
        """Test confidence scoring with extreme numerical values."""
        extreme_sequences = [
            [1e10, 2e10, 3e10, 4e10],       # Very large numbers
            [1e-10, 2e-10, 3e-10, 4e-10],   # Very small numbers
            [-1e6, -2e6, -3e6, -4e6],       # Large negative numbers
            [float('inf')],                  # Infinity (should be handled gracefully)
        ]

        for sequence in extreme_sequences:
            chain = ReasoningChain()
            try:
                result = predict_next_in_sequence(sequence, reasoning_chain=chain)
                if len(chain.steps) > 0:
                    confidence = chain.steps[0].confidence
                    assert 0.0 <= confidence <= 1.0, f"Confidence for extreme sequence {sequence} should be in valid bounds"
                    assert not math.isnan(confidence), f"Confidence should not be NaN for sequence {sequence}"
                    assert not math.isinf(confidence), f"Confidence should not be infinite for sequence {sequence}"
            except (ValueError, TypeError, OverflowError):
                pass  # Expected for some extreme cases

    def test_very_long_sequences_performance(self):
        """Test that confidence calculation works efficiently for long sequences."""
        # Create a long arithmetic sequence
        long_sequence = list(range(1000))  # 1000 elements

        chain = ReasoningChain()
        result = predict_next_in_sequence(long_sequence, reasoning_chain=chain)

        assert result is not None, "Should handle long sequences"
        assert len(chain.steps) == 1, "Should add exactly one step"
        confidence = chain.steps[0].confidence
        assert 0.95 <= confidence <= 1.0, f"Long perfect sequence should have very high confidence, got {confidence}"

    def test_floating_point_precision_edge_cases(self):
        """Test confidence scoring with floating point precision edge cases."""
        # Sequences that might cause floating point precision issues
        precision_sequences = [
            [0.1, 0.2, 0.3, 0.4],                          # Standard decimal fractions
            [1/3, 2/3, 1, 4/3],                            # Repeating decimals
            [math.sqrt(2), 2*math.sqrt(2), 3*math.sqrt(2)], # Irrational numbers
            [1.0000000001, 2.0000000001, 3.0000000001],    # Very close to integers
        ]

        for sequence in precision_sequences:
            chain = ReasoningChain()
            result = predict_next_in_sequence(sequence, reasoning_chain=chain)

            if result is not None and len(chain.steps) > 0:
                confidence = chain.steps[0].confidence
                assert 0.0 <= confidence <= 1.0, f"Confidence for precision sequence {sequence} should be in valid bounds"
                assert not math.isnan(confidence), f"Confidence should not be NaN for precision sequence {sequence}"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])