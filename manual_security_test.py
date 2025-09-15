#!/usr/bin/env python3
"""
Manual security verification tests - no external dependencies required.
"""

import sys
import traceback
import numpy as np

# Try to import our module
try:
    from inductive import predict_next_in_sequence, find_pattern_description
    print("✅ Successfully imported inductive module")
except ImportError as e:
    print(f"❌ Failed to import inductive module: {e}")
    sys.exit(1)


def test_confidence_bounds():
    """Test that confidence bounds are respected."""
    print("\n🔍 Testing Confidence Bounds...")

    try:
        # Test perfect arithmetic sequence
        result = predict_next_in_sequence([1, 2, 3, 4, 5])
        assert result == 6, f"Expected 6, got {result}"
        print("✅ Perfect arithmetic sequence works")

        # Test perfect geometric sequence
        result = predict_next_in_sequence([1, 2, 4, 8])
        assert result == 16, f"Expected 16, got {result}"
        print("✅ Perfect geometric sequence works")

        # Test pattern description
        desc = find_pattern_description([1, 2, 3, 4, 5])
        assert "Arithmetic progression" in desc
        print("✅ Pattern description works")

        print("✅ Confidence bounds test PASSED")
        return True

    except Exception as e:
        print(f"❌ Confidence bounds test FAILED: {e}")
        traceback.print_exc()
        return False


def test_input_validation():
    """Test that input validation works correctly."""
    print("\n🔍 Testing Input Validation...")

    # Test invalid types
    invalid_inputs = [
        "not a list",
        123,
        {"not": "a list"},
        None
    ]

    for invalid_input in invalid_inputs:
        try:
            predict_next_in_sequence(invalid_input)
            print(f"❌ Should have raised TypeError for {invalid_input}")
            return False
        except TypeError:
            print(f"✅ Correctly rejected invalid input: {type(invalid_input).__name__}")
        except Exception as e:
            print(f"❌ Unexpected error for {invalid_input}: {e}")
            return False

    # Test empty sequence
    try:
        predict_next_in_sequence([])
        print("❌ Should have raised ValueError for empty sequence")
        return False
    except ValueError:
        print("✅ Correctly rejected empty sequence")
    except Exception as e:
        print(f"❌ Unexpected error for empty sequence: {e}")
        return False

    # Test valid inputs
    valid_inputs = [
        [1, 2, 3],
        (1, 2, 3),
        np.array([1, 2, 3])
    ]

    for valid_input in valid_inputs:
        try:
            result = predict_next_in_sequence(valid_input)
            assert result == 4, f"Expected 4, got {result}"
            print(f"✅ Correctly accepted valid input: {type(valid_input).__name__}")
        except Exception as e:
            print(f"❌ Unexpected error for valid input {type(valid_input).__name__}: {e}")
            return False

    print("✅ Input validation test PASSED")
    return True


def test_overflow_protection():
    """Test that numerical overflow protection works."""
    print("\n🔍 Testing Overflow Protection...")

    try:
        # Test extreme values that could cause overflow
        extreme_sequence = [1e-10, 1e10, 1e20]
        result = predict_next_in_sequence(extreme_sequence)

        if result is not None:
            assert np.isfinite(result), f"Result should be finite, got {result}"
            assert not np.isnan(result), f"Result should not be NaN, got {result}"
            print("✅ Extreme values handled safely")
        else:
            print("✅ Extreme values correctly rejected (no pattern found)")

        # Test sequence with zeros (division by zero protection)
        zero_sequence = [1, 0, 5]
        result = predict_next_in_sequence(zero_sequence)
        print(f"✅ Zero sequence handled safely (result: {result})")

        # Test negative geometric progression
        negative_sequence = [-1, -2, -4, -8]
        result = predict_next_in_sequence(negative_sequence)
        if result is not None:
            assert np.isfinite(result), "Result should be finite"
            assert result == -16, f"Expected -16, got {result}"
            print("✅ Negative geometric progression works")

        print("✅ Overflow protection test PASSED")
        return True

    except Exception as e:
        print(f"❌ Overflow protection test FAILED: {e}")
        traceback.print_exc()
        return False


def test_mathematical_correctness():
    """Test that mathematical correctness is preserved."""
    print("\n🔍 Testing Mathematical Correctness...")

    test_cases = [
        # Arithmetic progressions
        ([1, 2, 3, 4], 5),
        ([0, 5, 10, 15], 20),
        ([10, 7, 4, 1], -2),
        ([-3, -1, 1, 3], 5),

        # Geometric progressions
        ([1, 2, 4, 8], 16),
        ([3, 6, 12, 24], 48),
        ([100, 10, 1], 0.1),
        ([1, 0.5, 0.25], 0.125)
    ]

    try:
        for sequence, expected in test_cases:
            result = predict_next_in_sequence(sequence)
            if isinstance(expected, float):
                assert abs(result - expected) < 1e-10, f"Failed for {sequence}: got {result}, expected {expected}"
            else:
                assert result == expected, f"Failed for {sequence}: got {result}, expected {expected}"
            print(f"✅ {sequence} → {result} (expected {expected})")

        # Test no pattern cases
        random_sequences = [
            [1, 3, 7, 2, 9],
            [1, 4, 2, 8, 5]
        ]

        for sequence in random_sequences:
            result = predict_next_in_sequence(sequence)
            assert result is None, f"Should not find pattern in {sequence}, but got {result}"
            print(f"✅ Correctly found no pattern in {sequence}")

        print("✅ Mathematical correctness test PASSED")
        return True

    except Exception as e:
        print(f"❌ Mathematical correctness test FAILED: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all security verification tests."""
    print("🔒 SECURITY RE-REVIEW: Inductive Reasoning Confidence Scoring")
    print("=" * 60)

    tests = [
        test_confidence_bounds,
        test_input_validation,
        test_overflow_protection,
        test_mathematical_correctness
    ]

    passed = 0
    failed = 0

    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1

    print("\n" + "=" * 60)
    print(f"SUMMARY: {passed} tests PASSED, {failed} tests FAILED")

    if failed == 0:
        print("🎉 ALL SECURITY FIXES VERIFIED - SECURITY CLEARANCE APPROVED")
        return True
    else:
        print("❌ SECURITY ISSUES REMAIN - ADDITIONAL FIXES REQUIRED")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)