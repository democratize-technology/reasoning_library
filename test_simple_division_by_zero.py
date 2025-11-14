#!/usr/bin/env python3
"""
Simple test to directly demonstrate division by zero vulnerabilities.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np
from reasoning_library.inductive import (
    _check_geometric_progression,
    _check_arithmetic_progression,
    detect_fibonacci_pattern,
    detect_polynomial_pattern,
    detect_exponential_pattern
)


def test_direct_division_by_zero_vulnerabilities():
    """Test that directly exposes division by zero vulnerabilities."""

    print("Testing division by zero vulnerabilities...")

    # Test 1: Geometric progression with zero in sequence
    print("\n1. Testing geometric progression with zero...")
    try:
        vulnerable_sequence = [1, 0, 0, 0]
        result = _check_geometric_progression(vulnerable_sequence, rtol=1e-5, atol=1e-8)
        print(f"   ❌ NO ERROR - This should have failed with ZeroDivisionError")
        print(f"   Result: {result}")
    except ZeroDivisionError as e:
        print(f"   ✅ ZeroDivisionError caught: {e}")
    except Exception as e:
        print(f"   ⚠️  Other error: {type(e).__name__}: {e}")

    # Test 2: Geometric progression with leading zero
    print("\n2. Testing geometric progression with leading zero...")
    try:
        vulnerable_sequence = [0, 1, 1, 1]
        result = _check_geometric_progression(vulnerable_sequence, rtol=1e-5, atol=1e-8)
        print(f"   ❌ NO ERROR - This should have failed with ZeroDivisionError")
        print(f"   Result: {result}")
    except ZeroDivisionError as e:
        print(f"   ✅ ZeroDivisionError caught: {e}")
    except Exception as e:
        print(f"   ⚠️  Other error: {type(e).__name__}: {e}")

    # Test 3: Test arithmetic progression with all zeros
    print("\n3. Testing arithmetic progression with all zeros...")
    try:
        vulnerable_sequence = [0, 0, 0, 0]
        result = _check_arithmetic_progression(vulnerable_sequence, rtol=1e-5, atol=1e-8)
        print(f"   Result: {result}")
        # Check for invalid values
        if result and result[0] is not None:
            if np.isinf(result[0]) or np.isnan(result[0]):
                print(f"   ⚠️  Invalid mathematical value detected: {result[0]}")
            else:
                print(f"   ✅ Valid result: {result[0]}")
    except Exception as e:
        print(f"   ⚠️  Error: {type(e).__name__}: {e}")

    # Test 4: Test polynomial pattern with extreme values
    print("\n4. Testing polynomial pattern with all zeros...")
    try:
        vulnerable_sequence = [0, 0, 0, 0, 0]
        result = detect_polynomial_pattern(vulnerable_sequence)
        print(f"   Result: {result}")
    except Exception as e:
        print(f"   ⚠️  Error: {type(e).__name__}: {e}")

    # Test 5: Test exponential pattern with zeros
    print("\n5. Testing exponential pattern with zeros...")
    try:
        vulnerable_sequence = [0, 0, 0, 0]
        result = detect_exponential_pattern(vulnerable_sequence)
        print(f"   Result: {result}")
    except Exception as e:
        print(f"   ⚠️  Error: {type(e).__name__}: {e}")

    print("\nVulnerability testing complete!")


if __name__ == "__main__":
    test_direct_division_by_zero_vulnerabilities()