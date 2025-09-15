#!/usr/bin/env python3
"""
Debug geometric confidence calculation in detail.
"""

import numpy as np
from inductive import _calculate_geometric_confidence, _assess_data_sufficiency, _calculate_pattern_quality_score

def debug_geometric_calculation():
    """Debug the geometric confidence calculation step by step."""
    print("🔍 DETAILED GEOMETRIC CONFIDENCE CALCULATION")
    print("=" * 60)

    # Test case: [2, 4, 8, 16, 32]
    sequence = [2, 4, 8, 16, 32]
    ratios = [2.0, 2.0, 2.0, 2.0]
    sequence_length = len(sequence)

    print(f"Sequence: {sequence}")
    print(f"Ratios: {ratios}")
    print(f"Sequence length: {sequence_length}")

    # Step 1: Data sufficiency factor
    data_sufficiency = _assess_data_sufficiency(sequence_length, 'geometric')
    print(f"\n1. Data Sufficiency Factor:")
    print(f"   Minimum required for geometric: 4")
    print(f"   Sequence length: {sequence_length}")
    print(f"   Data sufficiency: min(1.0, {sequence_length}/4) = {data_sufficiency}")

    # Step 2: Pattern quality factor
    pattern_quality = _calculate_pattern_quality_score(ratios, 'geometric')
    print(f"\n2. Pattern Quality Factor:")
    print(f"   Mean ratio: {np.mean(ratios)}")
    print(f"   Std ratio: {np.std(ratios)}")
    print(f"   Coefficient of variation: {np.std(ratios) / np.abs(np.mean(ratios))}")
    print(f"   Pattern quality: max(0.1, 1.0 - {np.std(ratios) / np.abs(np.mean(ratios))}) = {pattern_quality}")

    # Step 3: Complexity factor
    complexity_score = 0.2  # From design doc
    complexity_factor = 1.0 / (1.0 + complexity_score)
    print(f"\n3. Complexity Factor:")
    print(f"   Complexity score: {complexity_score}")
    print(f"   Complexity factor: 1.0 / (1.0 + {complexity_score}) = {complexity_factor}")

    # Step 4: Base confidence
    base_confidence = 1.0  # From function default
    print(f"\n4. Base Confidence: {base_confidence}")

    # Step 5: Final calculation
    expected_confidence = base_confidence * data_sufficiency * pattern_quality * complexity_factor
    print(f"\n5. Final Confidence Calculation:")
    print(f"   confidence = {base_confidence} × {data_sufficiency} × {pattern_quality} × {complexity_factor}")
    print(f"   confidence = {expected_confidence}")

    # Test actual function
    actual_confidence = _calculate_geometric_confidence(ratios, sequence_length)
    print(f"\n6. Actual Function Result: {actual_confidence}")

    print(f"\n7. Comparison:")
    print(f"   Expected: {expected_confidence:.6f}")
    print(f"   Actual:   {actual_confidence:.6f}")
    print(f"   Match: {abs(expected_confidence - actual_confidence) < 1e-6}")

    print(f"\n8. Design Specification Check:")
    print(f"   Design expectation: 0.85 - 0.95")
    print(f"   Actual result: {actual_confidence:.6f}")
    print(f"   Issue: Result {actual_confidence:.3f} < 0.85 minimum")

    # Check if base_confidence should be different
    needed_confidence_for_085 = 0.85 / (data_sufficiency * pattern_quality * complexity_factor)
    print(f"\n9. Base Confidence Analysis:")
    print(f"   To achieve 0.85 minimum, base_confidence needs to be: {needed_confidence_for_085:.3f}")
    print(f"   Current base_confidence: {base_confidence}")

if __name__ == "__main__":
    debug_geometric_calculation()