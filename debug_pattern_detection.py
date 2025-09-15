#!/usr/bin/env python3
"""
Debug script to investigate pattern detection issues.
"""

import numpy as np
from inductive import predict_next_in_sequence, find_pattern_description
from core import ReasoningChain

def debug_noisy_arithmetic():
    """Debug why noisy arithmetic sequence fails detection."""
    print("🔍 DEBUGGING NOISY ARITHMETIC SEQUENCE")
    print("=" * 50)

    sequence = [1, 2.1, 2.9, 4.1, 4.9]
    print(f"Sequence: {sequence}")

    # Calculate differences manually
    diffs = np.diff(sequence)
    print(f"Differences: {diffs}")
    print(f"Expected difference: ~1.0")

    # Test numpy.allclose behavior
    expected_diff = diffs[0]  # 1.1
    print(f"First difference: {expected_diff}")

    # Test if np.allclose considers these "close"
    is_close = np.allclose(diffs, expected_diff)
    print(f"np.allclose(diffs, {expected_diff}): {is_close}")

    # Test with different tolerance
    is_close_looser = np.allclose(diffs, expected_diff, rtol=0.1, atol=0.1)
    print(f"np.allclose with rtol=0.1, atol=0.1: {is_close_looser}")

    # Calculate variance to understand pattern quality
    variance = np.var(diffs)
    mean_abs_diff = np.mean(np.abs(diffs))
    variance_penalty = variance / (mean_abs_diff + 1e-10)
    pattern_quality = max(0.1, 1.0 - variance_penalty)

    print(f"Variance: {variance:.6f}")
    print(f"Mean absolute difference: {mean_abs_diff:.6f}")
    print(f"Variance penalty: {variance_penalty:.6f}")
    print(f"Pattern quality: {pattern_quality:.6f}")

    # Test the actual function
    chain = ReasoningChain()
    result = predict_next_in_sequence(sequence, chain)

    # Call result if it's a function (curry issue)
    if callable(result):
        print("Result is callable - curry decorator issue detected")
        result = result()

    print(f"Function result: {result}")

    if len(chain.steps) > 0:
        print(f"Confidence: {chain.steps[-1].confidence}")
        print(f"Description: {chain.steps[-1].description}")
    else:
        print("No reasoning steps recorded")

def debug_curry_decorator():
    """Debug the curry decorator issue."""
    print("\n🔍 DEBUGGING CURRY DECORATOR")
    print("=" * 50)

    # Test simple case
    simple_sequence = [1, 2, 3]
    result = predict_next_in_sequence(simple_sequence)

    print(f"predict_next_in_sequence([1,2,3]) returns: {type(result)}")
    print(f"Is callable: {callable(result)}")

    if callable(result):
        print("Curry decorator returning lambda - this is the API issue")
        # This means we need to pass ALL required arguments
        chain = ReasoningChain()
        actual_result = predict_next_in_sequence(simple_sequence, chain)
        print(f"With reasoning chain: {actual_result}")
        print(f"Type with reasoning chain: {type(actual_result)}")

def debug_geometric_confidence():
    """Debug geometric sequence confidence calculation."""
    print("\n🔍 DEBUGGING GEOMETRIC CONFIDENCE")
    print("=" * 50)

    sequence = [2, 4, 8, 16, 32]
    print(f"Sequence: {sequence}")

    # Calculate ratios manually
    ratios = [sequence[i] / sequence[i-1] for i in range(1, len(sequence))]
    print(f"Ratios: {ratios}")

    # Test if all ratios are close
    is_close = np.allclose(ratios, ratios[0])
    print(f"np.allclose(ratios, {ratios[0]}): {is_close}")

    # Test the function
    chain = ReasoningChain()
    result = predict_next_in_sequence(sequence, chain)

    if len(chain.steps) > 0:
        confidence = chain.steps[-1].confidence
        print(f"Actual confidence: {confidence:.6f}")
        print(f"Expected range: 0.85 - 0.95")
        print(f"Within range: {0.85 <= confidence <= 0.95}")

if __name__ == "__main__":
    debug_curry_decorator()
    debug_noisy_arithmetic()
    debug_geometric_confidence()