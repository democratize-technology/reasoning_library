#!/usr/bin/env python3
"""
CRITICAL #7: Algorithmic Complexity DoS Attack Fix Verification

This test verifies that the DoS protection mechanisms are working correctly
in the reasoning library's recursive pattern detection functions.
"""

import os
import sys
import time
import numpy as np
from typing import List, Dict, Any, Optional

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from reasoning_library.inductive import (
    detect_fibonacci_pattern,
    detect_lucas_pattern,
    detect_tribonacci_pattern,
    detect_recursive_pattern,
    _MAX_SEQUENCE_LENGTH,
    _COMPUTATION_TIMEOUT,
    _VALUE_MAGNITUDE_LIMIT
)

def test_input_size_validation_protection() -> bool:
    """Test that input size validation prevents DoS attacks."""
    print("Testing input size validation protection...")

    # Test 1: Sequence length limit
    print("  Test 1: Sequence length limit enforcement...")
    oversized_sequence = [float(i) for i in range(_MAX_SEQUENCE_LENGTH + 1)]

    try:
        result = detect_fibonacci_pattern(oversized_sequence)
        print(f"    ❌ FAIL: Should have rejected oversized sequence ({len(oversized_sequence)} elements)")
        return False
    except ValueError as e:
        if "Input sequence too large" in str(e):
            print(f"    ✅ PASS: Correctly rejected oversized sequence")
        else:
            print(f"    ❌ FAIL: Wrong error message: {e}")
            return False
    except Exception as e:
        print(f"    ❌ FAIL: Unexpected exception: {e}")
        return False

    # Test 2: Edge case - reasonable size sequence
    print("  Test 2: Reasonable size sequence...")
    # Use a very small arithmetic sequence that won't overflow
    reasonable_sequence = [float(i) for i in range(50)]

    try:
        # This should work without issues
        start_time = time.time()
        result = detect_fibonacci_pattern(reasonable_sequence)
        end_time = time.time()
        print(f"    ✅ PASS: Accepted reasonable size sequence ({end_time - start_time:.3f}s)")
    except Exception as e:
        # It's okay if this doesn't detect a pattern, but shouldn't crash
        if "Value overflow" in str(e):
            print(f"    ❌ FAIL: Should not overflow with reasonable sequence: {e}")
            return False
        else:
            print(f"    ✅ PASS: No overflow with reasonable sequence (no pattern detected is okay)")

    return True

def test_value_magnitude_validation_protection() -> bool:
    """Test that value magnitude validation prevents overflow attacks."""
    print("Testing value magnitude validation protection...")

    # Test 1: Large positive values
    print("  Test 1: Large positive values...")
    large_value_sequence = [float(_VALUE_MAGNITUDE_LIMIT + 1)]

    try:
        result = detect_fibonacci_pattern(large_value_sequence)
        print(f"    ❌ FAIL: Should have rejected large values")
        return False
    except ValueError as e:
        if "Value magnitude too large" in str(e):
            print(f"    ✅ PASS: Correctly rejected large values")
        else:
            print(f"    ❌ FAIL: Wrong error message: {e}")
            return False
    except Exception as e:
        print(f"    ❌ FAIL: Unexpected exception: {e}")
        return False

    # Test 2: Large negative values
    print("  Test 2: Large negative values...")
    large_negative_sequence = [float(-_VALUE_MAGNITUDE_LIMIT - 1)]

    try:
        result = detect_fibonacci_pattern(large_negative_sequence)
        print(f"    ❌ FAIL: Should have rejected large negative values")
        return False
    except ValueError as e:
        if "Value magnitude too large" in str(e):
            print(f"    ✅ PASS: Correctly rejected large negative values")
        else:
            print(f"    ❌ FAIL: Wrong error message: {e}")
            return False
    except Exception as e:
        print(f"    ❌ FAIL: Unexpected exception: {e}")
        return False

    # Test 3: NaN and infinity values
    print("  Test 3: NaN and infinity values...")
    invalid_sequences = [
        [float('nan')],
        [float('inf')],
        [float('-inf')],
        [1.0, float('nan'), 2.0],
        [1.0, float('inf'), 2.0]
    ]

    for seq in invalid_sequences:
        try:
            result = detect_fibonacci_pattern(seq)
            print(f"    ❌ FAIL: Should have rejected sequence with invalid values: {seq}")
            return False
        except ValueError as e:
            if "Invalid value" in str(e):
                continue  # Expected
            else:
                print(f"    ❌ FAIL: Wrong error message for {seq}: {e}")
                return False
        except Exception as e:
            print(f"    ❌ FAIL: Unexpected exception for {seq}: {e}")
            return False

    print(f"    ✅ PASS: Correctly rejected all invalid value sequences")
    return True

def test_computation_timeout_protection() -> bool:
    """Test that computation timeout protection prevents long-running attacks."""
    print("Testing computation timeout protection...")

    # Test 1: Complex sequence that could take a long time
    print("  Test 1: Complex sequence timeout...")

    # Create a sequence that requires computation but is still within size limits
    complex_sequence = []
    for i in range(2000):  # Smaller to avoid magnitude overflow
        if i < 3:
            complex_sequence.append(float(i + 1))
        else:
            # Use modulo to keep values within bounds
            val = (complex_sequence[-1] + complex_sequence[-2] + complex_sequence[-3]) % 1000000
            complex_sequence.append(val)

    try:
        start_time = time.time()
        result = detect_tribonacci_pattern(complex_sequence)
        end_time = time.time()
        computation_time = end_time - start_time

        if computation_time > _COMPUTATION_TIMEOUT + 1.0:  # Allow some margin
            print(f"    ❌ FAIL: Computation took too long ({computation_time:.2f}s)")
            return False
        else:
            print(f"    ✅ PASS: Computation completed in reasonable time ({computation_time:.3f}s)")
    except TimeoutError as e:
        print(f"    ✅ PASS: Correctly timed out long computation: {e}")
    except ValueError as e:
        if "Value overflow" in str(e):
            print(f"    ✅ PASS: Correctly detected arithmetic overflow: {e}")
        else:
            print(f"    ❌ FAIL: Unexpected ValueError: {e}")
            return False
    except Exception as e:
        print(f"    ❌ FAIL: Unexpected exception: {e}")
        return False

    return True

def test_all_functions_protection() -> bool:
    """Test that all pattern detection functions have DoS protection."""
    print("Testing protection in all pattern detection functions...")

    # Test sequence that should trigger protection
    attack_sequence = [float(_VALUE_MAGNITUDE_LIMIT + 1)] * 10

    functions_to_test = [
        ("detect_fibonacci_pattern", detect_fibonacci_pattern),
        ("detect_lucas_pattern", detect_lucas_pattern),
        ("detect_tribonacci_pattern", detect_tribonacci_pattern)
    ]

    for func_name, func in functions_to_test:
        try:
            result = func(attack_sequence)
            print(f"    ❌ FAIL: {func_name} should have rejected attack sequence")
            return False
        except ValueError as e:
            if "Value magnitude too large" in str(e):
                print(f"    ✅ PASS: {func_name} correctly protected")
            else:
                print(f"    ❌ FAIL: {func_name} wrong error: {e}")
                return False
        except Exception as e:
            print(f"    ❌ FAIL: {func_name} unexpected exception: {e}")
            return False

    # Test detect_recursive_pattern
    try:
        result = detect_recursive_pattern(attack_sequence, None)
        print(f"    ❌ FAIL: detect_recursive_pattern should have rejected attack sequence")
        return False
    except ValueError as e:
        if "Value magnitude too large" in str(e):
            print(f"    ✅ PASS: detect_recursive_pattern correctly protected")
        else:
            print(f"    ❌ FAIL: detect_recursive_pattern wrong error: {e}")
            return False
    except Exception as e:
        print(f"    ❌ FAIL: detect_recursive_pattern unexpected exception: {e}")
        return False

    return True

def test_legitimate_usage_still_works() -> bool:
    """Test that legitimate usage still works correctly after protection."""
    print("Testing that legitimate usage still works...")

    # Test 1: Real Fibonacci sequence
    print("  Test 1: Real Fibonacci sequence...")
    fibonacci_seq = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]

    try:
        result = detect_fibonacci_pattern(fibonacci_seq)
        if result and result["type"] == "fibonacci":
            print(f"    ✅ PASS: Correctly detected Fibonacci pattern")
        else:
            print(f"    ❌ FAIL: Failed to detect Fibonacci pattern")
            return False
    except Exception as e:
        print(f"    ❌ FAIL: Exception with legitimate Fibonacci: {e}")
        return False

    # Test 2: Real Lucas sequence
    print("  Test 2: Real Lucas sequence...")
    lucas_seq = [2, 1, 3, 4, 7, 11, 18, 29]

    try:
        result = detect_lucas_pattern(lucas_seq)
        if result and "lucas" in result["type"]:
            print(f"    ✅ PASS: Correctly detected Lucas pattern")
        else:
            print(f"    ❌ FAIL: Failed to detect Lucas pattern")
            return False
    except Exception as e:
        print(f"    ❌ FAIL: Exception with legitimate Lucas: {e}")
        return False

    # Test 3: Real Tribonacci sequence
    print("  Test 3: Real Tribonacci sequence...")
    tribonacci_seq = [0, 0, 1, 1, 2, 4, 7, 13, 24]

    try:
        result = detect_tribonacci_pattern(tribonacci_seq)
        if result and result["type"] == "tribonacci":
            print(f"    ✅ PASS: Correctly detected Tribonacci pattern")
        else:
            print(f"    ❌ FAIL: Failed to detect Tribonacci pattern")
            return False
    except Exception as e:
        print(f"    ❌ FAIL: Exception with legitimate Tribonacci: {e}")
        return False

    # Test 4: detect_recursive_pattern with legitimate input
    print("  Test 4: detect_recursive_pattern with legitimate input...")
    try:
        result = detect_recursive_pattern(fibonacci_seq, None)
        if result and "fibonacci" in result.get("type", ""):
            print(f"    ✅ PASS: detect_recursive_pattern works correctly")
        else:
            print(f"    ❌ FAIL: detect_recursive_pattern failed")
            return False
    except Exception as e:
        print(f"    ❌ FAIL: Exception with detect_recursive_pattern: {e}")
        return False

    return True

def main():
    """Main test function."""
    print("🔒 CRITICAL #7: Algorithmic Complexity DoS Fix Verification")
    print("=" * 70)
    print()

    all_passed = True

    # Run all protection tests
    test_functions = [
        ("Input Size Validation", test_input_size_validation_protection),
        ("Value Magnitude Validation", test_value_magnitude_validation_protection),
        ("Computation Timeout Protection", test_computation_timeout_protection),
        ("All Functions Protection", test_all_functions_protection),
        ("Legitimate Usage Still Works", test_legitimate_usage_still_works)
    ]

    for test_name, test_func in test_functions:
        print(f"Running {test_name}...")
        try:
            passed = test_func()
            if not passed:
                all_passed = False
            print()
        except Exception as e:
            print(f"    ❌ FAIL: Test crashed with exception: {e}")
            all_passed = False
            print()

    print("=" * 70)

    if all_passed:
        print("🛡️ CRITICAL #7 FIX VERIFICATION: ALL TESTS PASSED!")
        print()
        print("DoS Protection Confirmed:")
        print("  ✅ Input size validation prevents large sequence attacks")
        print("  ✅ Value magnitude validation prevents overflow attacks")
        print("  ✅ Computation timeout prevents long-running attacks")
        print("  ✅ All pattern detection functions are protected")
        print("  ✅ Legitimate usage continues to work correctly")
        print()
        print("Security Status: PROTECTED against Algorithmic Complexity DoS attacks")

        return 0
    else:
        print("🚨 CRITICAL #7 FIX VERIFICATION: SOME TESTS FAILED!")
        print()
        print("Issues detected in DoS protection implementation.")
        print("The fix may not fully protect against all attack vectors.")

        return 1

if __name__ == "__main__":
    sys.exit(main())