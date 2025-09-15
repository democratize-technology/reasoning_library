#!/usr/bin/env python3
"""
Test script to verify the confidence documentation extraction fix works correctly.
"""

from core import _detect_mathematical_reasoning
from inductive import _calculate_geometric_confidence, _calculate_arithmetic_confidence, predict_next_in_sequence

def test_confidence_extraction_fix():
    """Test that the improved regex patterns produce clean, readable output."""
    print("=" * 80)
    print("TESTING CONFIDENCE EXTRACTION FIX")
    print("=" * 80)

    # Test functions
    test_functions = [
        _calculate_geometric_confidence,
        _calculate_arithmetic_confidence,
        predict_next_in_sequence
    ]

    for func in test_functions:
        print(f"\nTesting: {func.__name__}")
        print("-" * 50)

        is_mathematical, confidence_doc, mathematical_basis = _detect_mathematical_reasoning(func)

        print(f"Is mathematical: {is_mathematical}")
        print(f"Confidence documentation: {confidence_doc}")
        print(f"Mathematical basis: {mathematical_basis}")

        # Check if we avoided the malformed output
        if confidence_doc:
            malformed_indicators = ['0, )', ':, r', ', ,', '=,', '*,']
            is_malformed = any(indicator in confidence_doc for indicator in malformed_indicators)
            print(f"Is malformed: {is_malformed}")

            if is_malformed:
                print("❌ STILL MALFORMED!")
            else:
                print("✅ Clean output!")
        else:
            print("⚠️  No confidence documentation extracted")

def test_specific_expected_outputs():
    """Test that we get the expected clean outputs."""
    print("\n\n" + "=" * 80)
    print("TESTING EXPECTED OUTPUTS")
    print("=" * 80)

    expected_patterns = [
        'data sufficiency',
        'pattern quality',
        'complexity',
    ]

    func = _calculate_geometric_confidence
    is_mathematical, confidence_doc, mathematical_basis = _detect_mathematical_reasoning(func)

    print(f"Function: {func.__name__}")
    print(f"Confidence doc: {confidence_doc}")

    if confidence_doc:
        found_patterns = [pattern for pattern in expected_patterns if pattern in confidence_doc.lower()]
        print(f"Expected patterns found: {found_patterns}")

        if len(found_patterns) >= 2:
            print("✅ Contains expected confidence calculation factors!")
        else:
            print("⚠️  Missing some expected patterns")
    else:
        print("❌ No confidence documentation generated")

if __name__ == "__main__":
    test_confidence_extraction_fix()
    test_specific_expected_outputs()