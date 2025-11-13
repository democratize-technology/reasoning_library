#!/usr/bin/env python3
"""
Verification test for CRIT-002 Algorithmic DoS fix.

This test verifies that the DoS vulnerabilities have been properly fixed.
All tests should PASS after the fix is implemented.
"""

import pytest
import time
from reasoning_library.inductive import (
    predict_next_in_sequence,
    detect_fibonacci_pattern,
    detect_lucas_pattern,
    detect_tribonacci_pattern,
    MAX_SEQUENCE_LENGTH,
    _VALUE_MAGNITUDE_LIMIT,
    TIMEOUT_CHECK_INTERVAL
)
from reasoning_library.exceptions import ValidationError, TimeoutError


class TestCRIT002AlgorithmicDoSFixVerification:
    """Verify that CRIT-002 Algorithmic DoS vulnerabilities have been fixed."""

    def test_sequence_length_limit_enforced(self):
        """Verify that sequence length limit is properly enforced."""
        # Try to create a sequence longer than the new limit
        too_long_sequence = list(range(MAX_SEQUENCE_LENGTH + 1))

        # This should now be rejected
        with pytest.raises(ValidationError) as exc_info:
            predict_next_in_sequence(too_long_sequence, reasoning_chain=None)

        error_msg = str(exc_info.value)
        assert "Input sequence too large" in error_msg
        assert f"{MAX_SEQUENCE_LENGTH} elements" in error_msg
        assert "prevents DoS attacks" in error_msg

    def test_sequence_length_limit_acceptable(self):
        """Verify that sequences at the limit are still accepted."""
        # This should work fine
        acceptable_sequence = list(range(MAX_SEQUENCE_LENGTH))
        result = predict_next_in_sequence(acceptable_sequence, reasoning_chain=None)

        # Should return a result without errors (arithmetic progression)
        assert result is not None
        assert result == MAX_SEQUENCE_LENGTH

    def test_exponential_growth_detection(self):
        """Verify that exponential growth sequences are detected and rejected."""
        # Create an exponential growth sequence
        exponential_sequence = [1, 2]
        for i in range(8):
            exponential_sequence.append(exponential_sequence[-1] * 3)  # 3x growth

        # This should be rejected due to exponential growth detection
        with pytest.raises(ValidationError) as exc_info:
            detect_fibonacci_pattern(exponential_sequence, tolerance=0.1)

        error_msg = str(exc_info.value)
        assert "Exponential growth detected" in error_msg
        assert "potential DoS attack" in error_msg
        assert "growth factor" in error_msg

    def test_normal_sequences_still_work(self):
        """Verify that normal sequences still work after the fix."""
        # Test Fibonacci
        fib_sequence = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
        result = detect_fibonacci_pattern(fib_sequence)
        assert result is not None
        assert result["type"] == "fibonacci"

        # Test Lucas
        lucas_sequence = [2, 1, 3, 4, 7, 11, 18, 29, 47, 76]
        result = detect_lucas_pattern(lucas_sequence)
        assert result is not None
        assert result["type"] == "lucas"

        # Test arithmetic progression
        arith_sequence = [2, 4, 6, 8, 10, 12]
        result = predict_next_in_sequence(arith_sequence, reasoning_chain=None)
        assert result is not None
        assert result == 14

    def test_timeout_check_interval_reduced(self):
        """Verify that timeout check interval has been reduced."""
        # The constant should be set to 100 (reduced from 1000)
        assert TIMEOUT_CHECK_INTERVAL == 100

    def test_timeout_checks_more_frequent(self):
        """Verify that timeout checks are now more frequent."""
        # Create a long sequence that would trigger timeout checks
        # This sequence is long but not too long to be rejected outright
        long_sequence = [1.001, 1.002] + [1.003] * (TIMEOUT_CHECK_INTERVAL * 2)

        start_time = time.time()

        try:
            # This should either complete or timeout, but not take too long
            result = detect_fibonacci_pattern(long_sequence, tolerance=0.1)
            elapsed = time.time() - start_time

            # If it completes, it should do so reasonably quickly
            assert elapsed < 5.0, f"Operation took too long: {elapsed}s"

        except (ValidationError, TimeoutError, ValueError):
            # These are expected and acceptable
            elapsed = time.time() - start_time
            assert elapsed < 5.0, f"Error handling took too long: {elapsed}s"

    def test_value_magnitude_limit_still_enforced(self):
        """Verify that value magnitude limits are still enforced."""
        # Create sequence with values that exceed the magnitude limit
        large_value_sequence = [_VALUE_MAGNITUDE_LIMIT * 2, 1, 2, 3]

        with pytest.raises(ValidationError) as exc_info:
            detect_fibonacci_pattern(large_value_sequence)

        error_msg = str(exc_info.value)
        assert "Value magnitude too large" in error_msg
        assert "Maximum allowed magnitude" in error_msg

    def test_geometric_growth_not_flagged_as_exponential(self):
        """Verify that reasonable geometric growth is not flagged as exponential."""
        # This is a geometric progression (2x growth) - should be allowed up to a point
        geometric_sequence = [1, 2, 4, 8, 16, 32, 64, 128]  # 8 terms of 2x growth

        try:
            result = detect_fibonacci_pattern(geometric_sequence, tolerance=0.5)
            # Should not raise ValidationError for exponential growth
            # The function may or may not find a pattern, but shouldn't error out
        except ValidationError as e:
            # If it does error, it shouldn't be about exponential growth
            assert "Exponential growth detected" not in str(e)

    def test_tribonacci_exponential_protection(self):
        """Verify that Tribonacci pattern detection also has exponential protection."""
        # Create an exponential sequence
        exponential_sequence = [1, 1, 2]
        for i in range(7):
            exponential_sequence.append(exponential_sequence[-1] * 4)  # 4x growth

        with pytest.raises(ValidationError) as exc_info:
            detect_tribonacci_pattern(exponential_sequence, tolerance=0.1)

        error_msg = str(exc_info.value)
        assert "Exponential growth detected" in error_msg

    def test_performance_after_fix(self):
        """Verify that the fix doesn't significantly impact normal performance."""
        # Test with a reasonably sized sequence
        test_sequence = list(range(100))  # 100 elements

        start_time = time.time()
        result = predict_next_in_sequence(test_sequence)
        elapsed = time.time() - start_time

        # Should complete quickly
        assert elapsed < 0.1, f"Performance degraded: {elapsed}s for 100 elements"
        assert result is not None

    def test_backward_compatibility_maintained(self):
        """Verify that the fix maintains backward compatibility."""
        # Test all the main functions still work with normal inputs

        # Fibonacci
        fib_result = detect_fibonacci_pattern([1, 1, 2, 3, 5, 8, 13])
        assert fib_result["type"] == "fibonacci"

        # Lucas
        lucas_result = detect_lucas_pattern([2, 1, 3, 4, 7, 11, 18])
        assert lucas_result["type"] == "lucas"

        # Tribonacci
        trib_result = detect_tribonacci_pattern([0, 0, 1, 1, 2, 4, 7, 13])
        assert trib_result["type"] == "tribonacci"

        # General prediction
        pred_result = predict_next_in_sequence([1, 3, 5, 7, 9], reasoning_chain=None)
        assert pred_result == 11


if __name__ == "__main__":
    # Run the verification tests
    print("Verifying CRIT-002 Algorithmic DoS Fix")
    print("=" * 50)

    test_suite = TestCRIT002AlgorithmicDoSFixVerification()

    tests = [
        ("Sequence length limit enforcement", test_suite.test_sequence_length_limit_enforced),
        ("Sequence length limit acceptable", test_suite.test_sequence_length_limit_acceptable),
        ("Exponential growth detection", test_suite.test_exponential_growth_detection),
        ("Normal sequences still work", test_suite.test_normal_sequences_still_work),
        ("Timeout check interval reduced", test_suite.test_timeout_check_interval_reduced),
        ("Timeout checks more frequent", test_suite.test_timeout_checks_more_frequent),
        ("Value magnitude limit still enforced", test_suite.test_value_magnitude_limit_still_enforced),
        ("Geometric growth not flagged", test_suite.test_geometric_growth_not_flagged_as_exponential),
        ("Tribonacci exponential protection", test_suite.test_tribonacci_exponential_protection),
        ("Performance after fix", test_suite.test_performance_after_fix),
        ("Backward compatibility maintained", test_suite.test_backward_compatibility_maintained),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            test_func()
            print(f"✅ {test_name}")
            passed += 1
        except Exception as e:
            print(f"❌ {test_name}: {e}")
            failed += 1

    print("\n" + "=" * 50)
    print(f"Verification complete: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All CRIT-002 fixes verified successfully!")
    else:
        print("⚠️  Some fixes need attention")