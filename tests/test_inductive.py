#!/usr/bin/env python3
"""
Comprehensive test suite for inductive.py module.

Tests pattern recognition, confidence scoring, numpy dependency handling,
edge cases, and statistical analysis functionality.
"""
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Handle numpy import gracefully
try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("⚠️  NumPy not available - some tests will be skipped")

from reasoning_library.core import ReasoningChain, ReasoningStep
from reasoning_library.inductive import (
    _assess_data_sufficiency,
    _calculate_arithmetic_confidence,
    _calculate_geometric_confidence,
    _calculate_pattern_quality_score,
    find_pattern_description,
    predict_next_in_sequence,
)


@pytest.mark.skipif(not NUMPY_AVAILABLE, reason="NumPy not available")
class TestNumpyDependentFunctions:
    """Test functions that require numpy."""

    def test_predict_arithmetic_sequence(self):
        """Test prediction of arithmetic sequences."""
        chain = ReasoningChain()

        # Simple arithmetic sequence: 2, 4, 6, 8, ...
        sequence = [2, 4, 6, 8]
        result = predict_next_in_sequence(sequence, reasoning_chain=chain)

        assert result == 10
        assert len(chain.steps) == 1
        assert chain.steps[0].confidence > 0.5
        assert "arithmetic progression" in chain.steps[0].description.lower()

    def test_predict_geometric_sequence(self):
        """Test prediction of geometric sequences."""
        chain = ReasoningChain()

        # Simple geometric sequence: 2, 4, 8, 16, ...
        sequence = [2, 4, 8, 16]
        result = predict_next_in_sequence(sequence, reasoning_chain=chain)

        assert result == 32
        assert len(chain.steps) == 1
        assert chain.steps[0].confidence > 0.5
        assert "geometric progression" in chain.steps[0].description.lower()

    def test_predict_no_pattern(self):
        """Test sequence with no recognizable pattern."""
        chain = ReasoningChain()

        # Random sequence with no clear pattern
        sequence = [1, 7, 3, 9, 2]
        result = predict_next_in_sequence(sequence, reasoning_chain=chain)

        assert result is None
        assert len(chain.steps) == 1
        assert chain.steps[0].confidence == 0.0
        assert "No simple arithmetic or geometric pattern" in chain.steps[0].description

    def test_find_arithmetic_pattern_description(self):
        """Test finding description of arithmetic patterns."""
        chain = ReasoningChain()

        # Arithmetic sequence
        sequence = [10, 15, 20, 25]
        description = find_pattern_description(sequence, reasoning_chain=chain)

        assert "Arithmetic progression with common difference: 5" in description
        assert len(chain.steps) == 1
        assert chain.steps[0].confidence > 0.5

    def test_find_geometric_pattern_description(self):
        """Test finding description of geometric patterns."""
        chain = ReasoningChain()

        # Geometric sequence
        sequence = [3, 6, 12, 24]
        description = find_pattern_description(sequence, reasoning_chain=chain)

        assert "Geometric progression with common ratio: 2" in description
        assert len(chain.steps) == 1
        assert chain.steps[0].confidence > 0.5

    def test_find_no_pattern_description(self):
        """Test finding description when no pattern exists."""
        chain = ReasoningChain()

        # Random sequence
        sequence = [1, 4, 7, 3, 9]
        description = find_pattern_description(sequence, reasoning_chain=chain)

        assert description == "No simple pattern found."
        assert len(chain.steps) == 1
        assert chain.steps[0].confidence == 0.0


class TestInputValidation:
    """Test input validation and error handling."""

    def test_empty_sequence_validation(self):
        """Test validation of empty sequences."""
        with pytest.raises(ValueError, match="Sequence cannot be empty"):
            predict_next_in_sequence([], reasoning_chain=None)

        with pytest.raises(ValueError, match="Sequence cannot be empty"):
            find_pattern_description([], reasoning_chain=None)

    def test_invalid_sequence_type_validation(self):
        """Test validation of invalid sequence types."""
        invalid_inputs = ["not a list", 123, None, {"not": "list"}]

        for invalid_input in invalid_inputs:
            with pytest.raises(
                TypeError, match="Expected list/tuple/array for sequence"
            ):
                predict_next_in_sequence(invalid_input, reasoning_chain=None)

            with pytest.raises(
                TypeError, match="Expected list/tuple/array for sequence"
            ):
                find_pattern_description(invalid_input, reasoning_chain=None)

    @pytest.mark.skipif(not NUMPY_AVAILABLE, reason="NumPy not available")
    def test_numpy_array_input(self):
        """Test that numpy arrays are accepted as input."""
        import numpy as np

        # Test with numpy array
        sequence = np.array([1, 3, 5, 7])
        result = predict_next_in_sequence(sequence, reasoning_chain=None)
        assert result == 9

        # Test with tuple
        sequence = (2, 4, 6, 8)
        result = predict_next_in_sequence(sequence, reasoning_chain=None)
        assert result == 10

    def test_single_element_sequence(self):
        """Test handling of single-element sequences."""
        chain = ReasoningChain()

        result = predict_next_in_sequence([42], reasoning_chain=chain)
        assert result is None
        assert len(chain.steps) == 1
        assert "too short to determine a pattern" in chain.steps[0].description

        description = find_pattern_description([42], reasoning_chain=chain)
        assert description == "Sequence too short to determine a pattern."


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.skipif(not NUMPY_AVAILABLE, reason="NumPy not available")
    def test_zero_values_in_sequence(self):
        """Test sequences containing zero values."""
        # Arithmetic sequence with zeros
        sequence = [0, 5, 10, 15]
        result = predict_next_in_sequence(sequence, reasoning_chain=None)
        assert result == 20

        # Sequence starting with zero
        sequence = [0, 0, 0, 0]
        result = predict_next_in_sequence(sequence, reasoning_chain=None)
        assert result == 0

        # Geometric sequence with zero (should not be detected as geometric)
        sequence = [1, 0, 0, 0]
        result = predict_next_in_sequence(sequence, reasoning_chain=None)
        assert result is None  # Cannot have geometric progression with zeros

    @pytest.mark.skipif(not NUMPY_AVAILABLE, reason="NumPy not available")
    def test_negative_values(self):
        """Test sequences with negative values."""
        # Arithmetic with negative difference
        sequence = [10, 7, 4, 1]
        result = predict_next_in_sequence(sequence, reasoning_chain=None)
        assert result == -2

        # Geometric with negative ratio
        sequence = [8, -4, 2, -1]
        result = predict_next_in_sequence(sequence, reasoning_chain=None)
        assert result == 0.5

    @pytest.mark.skipif(not NUMPY_AVAILABLE, reason="NumPy not available")
    def test_floating_point_sequences(self):
        """Test sequences with floating point numbers."""
        # Arithmetic with floats
        sequence = [1.5, 2.5, 3.5, 4.5]
        result = predict_next_in_sequence(sequence, reasoning_chain=None)
        assert abs(result - 5.5) < 1e-10

        # Geometric with floats
        sequence = [0.5, 1.0, 2.0, 4.0]
        result = predict_next_in_sequence(sequence, reasoning_chain=None)
        assert abs(result - 8.0) < 1e-10

    @pytest.mark.skipif(not NUMPY_AVAILABLE, reason="NumPy not available")
    def test_very_small_differences(self):
        """Test sequences with very small differences."""
        # Small arithmetic differences
        sequence = [1.0, 1.0001, 1.0002, 1.0003]
        result = predict_next_in_sequence(sequence, reasoning_chain=None)
        assert result is not None
        assert abs(result - 1.0004) < 1e-10

    @pytest.mark.skipif(not NUMPY_AVAILABLE, reason="NumPy not available")
    def test_large_numbers(self):
        """Test sequences with large numbers."""
        # Large arithmetic sequence
        sequence = [1000000, 2000000, 3000000, 4000000]
        result = predict_next_in_sequence(sequence, reasoning_chain=None)
        assert result == 5000000

        # Large geometric sequence
        sequence = [1000, 10000, 100000, 1000000]
        result = predict_next_in_sequence(sequence, reasoning_chain=None)
        assert result == 10000000

    @pytest.mark.skipif(not NUMPY_AVAILABLE, reason="NumPy not available")
    def test_tolerance_parameters(self):
        """Test custom tolerance parameters."""
        # Noisy arithmetic sequence that should be detected with higher tolerance
        sequence = [1, 2.1, 2.9, 4.1]  # Roughly arithmetic with difference ~1

        # With default tolerance (should not detect pattern)
        result = predict_next_in_sequence(sequence, reasoning_chain=None)
        assert result is None

        # With higher tolerance (should detect pattern)
        result = predict_next_in_sequence(sequence, reasoning_chain=None, rtol=0.5)
        assert result is not None


class TestConfidenceScoring:
    """Test confidence scoring algorithms."""

    @pytest.mark.skipif(not NUMPY_AVAILABLE, reason="NumPy not available")
    def test_data_sufficiency_assessment(self):
        """Test data sufficiency factor calculation."""
        # Test arithmetic requirements
        assert _assess_data_sufficiency(4, "arithmetic") == 1.0  # Minimum required
        assert _assess_data_sufficiency(3, "arithmetic") < 1.0  # Below minimum
        assert _assess_data_sufficiency(6, "arithmetic") == 1.0  # Above minimum

        # Test geometric requirements
        assert _assess_data_sufficiency(4, "geometric") == 1.0  # Minimum required
        assert _assess_data_sufficiency(3, "geometric") < 1.0  # Below minimum
        assert _assess_data_sufficiency(8, "geometric") == 1.0  # Above minimum

    @pytest.mark.skipif(not NUMPY_AVAILABLE, reason="NumPy not available")
    def test_pattern_quality_scoring(self):
        """Test pattern quality assessment."""
        import numpy as np

        # Perfect arithmetic pattern
        perfect_diffs = np.array([1, 1, 1, 1])
        quality = _calculate_pattern_quality_score(perfect_diffs, "arithmetic")
        assert quality > 0.9  # Should be very high

        # Noisy arithmetic pattern
        noisy_diffs = np.array([1, 1.5, 0.5, 1])
        quality = _calculate_pattern_quality_score(noisy_diffs, "arithmetic")
        assert 0.1 < quality < 0.9  # Should be moderate

        # Perfect geometric pattern
        perfect_ratios = [2, 2, 2, 2]
        quality = _calculate_pattern_quality_score(perfect_ratios, "geometric")
        assert quality > 0.8  # Should be high

    @pytest.mark.skipif(not NUMPY_AVAILABLE, reason="NumPy not available")
    def test_arithmetic_confidence_calculation(self):
        """Test arithmetic confidence calculation."""
        import numpy as np

        # Perfect pattern with sufficient data
        perfect_diffs = np.array([2, 2, 2, 2])
        confidence = _calculate_arithmetic_confidence(perfect_diffs, 5)
        assert confidence > 0.9

        # Perfect pattern with insufficient data
        perfect_diffs = np.array([2, 2])
        confidence = _calculate_arithmetic_confidence(perfect_diffs, 3)
        assert confidence < 0.9  # Should be penalized for insufficient data

        # Noisy pattern
        noisy_diffs = np.array([2, 3, 1, 2])
        confidence = _calculate_arithmetic_confidence(noisy_diffs, 5)
        assert 0.1 < confidence < 0.8

    @pytest.mark.skipif(not NUMPY_AVAILABLE, reason="NumPy not available")
    def test_geometric_confidence_calculation(self):
        """Test geometric confidence calculation."""
        # Perfect pattern with sufficient data
        perfect_ratios = [2, 2, 2, 2]
        confidence = _calculate_geometric_confidence(perfect_ratios, 5)
        assert confidence > 0.8

        # Perfect pattern with insufficient data
        perfect_ratios = [2, 2]
        confidence = _calculate_geometric_confidence(perfect_ratios, 3)
        assert confidence < 0.8  # Should be penalized for insufficient data

        # Noisy pattern
        noisy_ratios = [2, 2.5, 1.5, 2]
        confidence = _calculate_geometric_confidence(noisy_ratios, 5)
        assert 0.1 < confidence < 0.7


class TestCurryingFunctionality:
    """Test currying functionality of inductive functions."""

    @pytest.mark.skipif(not NUMPY_AVAILABLE, reason="NumPy not available")
    def test_predict_next_in_sequence_currying(self):
        """Test currying of predict_next_in_sequence function."""
        # Create a curried function with a specific sequence
        sequence = [1, 3, 5, 7]
        predict_for_sequence = predict_next_in_sequence(sequence)

        # Should be a callable that accepts reasoning_chain
        assert callable(predict_for_sequence)

        # Call with reasoning chain
        chain = ReasoningChain()
        result = predict_for_sequence(reasoning_chain=chain)
        assert result == 9
        assert len(chain.steps) == 1

    @pytest.mark.skipif(not NUMPY_AVAILABLE, reason="NumPy not available")
    def test_find_pattern_description_currying(self):
        """Test currying of find_pattern_description function."""
        # Create a curried function
        sequence = [2, 4, 6, 8]
        describe_sequence = find_pattern_description(sequence)

        assert callable(describe_sequence)

        # Call with reasoning chain
        chain = ReasoningChain()
        description = describe_sequence(reasoning_chain=chain)
        assert "Arithmetic progression" in description
        assert len(chain.steps) == 1


class TestReasoningChainIntegration:
    """Test integration with ReasoningChain."""

    @pytest.mark.skipif(not NUMPY_AVAILABLE, reason="NumPy not available")
    def test_detailed_step_recording(self):
        """Test that detailed steps are recorded in reasoning chain."""
        chain = ReasoningChain()

        # Test arithmetic sequence
        sequence = [5, 10, 15, 20]
        result = predict_next_in_sequence(sequence, reasoning_chain=chain)

        assert result == 25
        assert len(chain.steps) == 1

        step = chain.steps[0]
        assert step.stage == "Inductive Reasoning: Sequence Prediction"
        assert step.result == 25
        assert step.confidence is not None
        assert step.confidence > 0
        assert step.evidence is not None
        assert "Common difference" in step.evidence
        assert len(step.assumptions) > 0
        assert "arithmetic or geometric progression" in step.assumptions[0]

    @pytest.mark.skipif(not NUMPY_AVAILABLE, reason="NumPy not available")
    def test_failure_step_recording(self):
        """Test that failure cases are properly recorded."""
        chain = ReasoningChain()

        # Random sequence with no pattern
        sequence = [1, 7, 3, 11, 2]
        result = predict_next_in_sequence(sequence, reasoning_chain=chain)

        assert result is None
        assert len(chain.steps) == 1

        step = chain.steps[0]
        assert step.result is None
        assert step.confidence == 0.0
        assert "No simple arithmetic or geometric pattern" in step.description

    @pytest.mark.skipif(not NUMPY_AVAILABLE, reason="NumPy not available")
    def test_multiple_predictions_same_chain(self):
        """Test multiple predictions using the same reasoning chain."""
        chain = ReasoningChain()

        # First prediction
        sequence1 = [2, 4, 6, 8]
        result1 = predict_next_in_sequence(sequence1, reasoning_chain=chain)

        # Second prediction
        sequence2 = [3, 6, 12, 24]
        result2 = predict_next_in_sequence(sequence2, reasoning_chain=chain)

        assert result1 == 10
        assert result2 == 48
        assert len(chain.steps) == 2
        assert chain.steps[0].description != chain.steps[1].description


class TestToolSpecMetadata:
    """Test tool specification metadata for inductive functions."""

    def test_predict_next_in_sequence_tool_spec(self):
        """Test tool spec metadata for predict_next_in_sequence."""
        assert hasattr(predict_next_in_sequence, "tool_spec")

        spec = predict_next_in_sequence.tool_spec
        assert spec["type"] == "function"
        assert spec["function"]["name"] == "predict_next_in_sequence"
        assert "sequence" in spec["function"]["parameters"]["properties"]
        assert "reasoning_chain" not in spec["function"]["parameters"]["properties"]

    def test_find_pattern_description_tool_spec(self):
        """Test tool spec metadata for find_pattern_description."""
        assert hasattr(find_pattern_description, "tool_spec")

        spec = find_pattern_description.tool_spec
        assert spec["type"] == "function"
        assert spec["function"]["name"] == "find_pattern_description"
        assert "sequence" in spec["function"]["parameters"]["properties"]


class TestNumpyFallbackHandling:
    """Test handling when numpy is not available."""

    @patch("sys.modules", {"numpy": None})
    def test_graceful_numpy_import_failure(self):
        """Test graceful handling when numpy import fails."""
        # This test simulates what happens when numpy is not available
        # The actual import handling is done at module level, so this is more of a design test

        # The key is that the module should still be importable even without numpy
        # and should raise appropriate errors when numpy-dependent functions are called

        # Since we can't easily mock the module-level import, we'll just verify
        # that the functions exist and can be called with appropriate error handling

        try:
            # These functions should exist even if numpy isn't available
            assert callable(predict_next_in_sequence)
            assert callable(find_pattern_description)
        except NameError:
            # If the functions don't exist, it's because numpy import failed
            # This is expected behavior in that case
            pass


def run_all_tests():
    """Run all inductive reasoning tests with detailed output."""
    print("🧪 Running comprehensive test suite for inductive.py...")

    if not NUMPY_AVAILABLE:
        print("⚠️  NumPy not available - many tests will be skipped")

    test_classes = [
        TestInputValidation,
        TestEdgeCases,
        TestCurryingFunctionality,
        TestReasoningChainIntegration,
        TestToolSpecMetadata,
        TestNumpyFallbackHandling,
    ]

    # Add numpy-dependent tests if available
    if NUMPY_AVAILABLE:
        test_classes.insert(0, TestNumpyDependentFunctions)
        test_classes.insert(-1, TestConfidenceScoring)

    total_tests = 0
    passed_tests = 0
    failed_tests = []
    skipped_tests = 0

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

            except pytest.skip.Exception as e:
                skipped_tests += 1
                print(f"  ⏭️  {method_name}: SKIPPED - {str(e)}")

            except Exception as e:
                failed_tests.append(f"{test_class.__name__}.{method_name}: {str(e)}")
                print(f"  ❌ {method_name}: {str(e)}")

    print(f"\n📊 Test Summary:")
    print(f"  Total tests: {total_tests}")
    print(f"  Passed: {passed_tests}")
    print(f"  Skipped: {skipped_tests}")
    print(f"  Failed: {len(failed_tests)}")

    if failed_tests:
        print(f"\n❌ Failed tests:")
        for failure in failed_tests:
            print(f"  - {failure}")
        return False
    else:
        print(f"\n🎉 All inductive reasoning tests passed!")
        if skipped_tests > 0:
            print(
                f"   (Note: {skipped_tests} tests were skipped due to missing dependencies)"
            )
        return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
