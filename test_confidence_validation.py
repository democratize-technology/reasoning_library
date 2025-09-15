#!/usr/bin/env python3
"""
Architectural validation script for inductive confidence scoring.
Tests mathematical correctness against design specifications.
"""

import sys
import numpy as np
from typing import List, Optional

# Import the implementation
from inductive import (
    predict_next_in_sequence,
    find_pattern_description,
    _calculate_arithmetic_confidence,
    _calculate_geometric_confidence,
    _assess_data_sufficiency,
    _calculate_pattern_quality_score
)
from core import ReasoningChain

def test_design_compliance():
    """Test implementation against design document specifications."""
    print("🏗️  ARCHITECTURAL COMPLIANCE VALIDATION")
    print("=" * 50)

    results = {
        'design_compliance': True,
        'mathematical_correctness': True,
        'api_compatibility': True,
        'test_cases_passed': 0,
        'test_cases_total': 5,
        'issues': []
    }

    # Test cases from design document
    test_cases = [
        {
            'sequence': [1, 2, 3, 4, 5],
            'description': "Perfect Arithmetic Sequence",
            'expected_confidence_range': (0.90, 1.0),
            'pattern_type': 'arithmetic'
        },
        {
            'sequence': [2, 4, 8, 16, 32],
            'description': "Perfect Geometric Sequence",
            'expected_confidence_range': (0.85, 0.95),
            'pattern_type': 'geometric'
        },
        {
            'sequence': [1, 2],
            'description': "Insufficient Data",
            'expected_confidence_range': (0.30, 0.50),
            'pattern_type': 'arithmetic'
        },
        {
            'sequence': [1, 7, 3, 12, 9],
            'description': "No Pattern",
            'expected_confidence_range': (0.0, 0.1),
            'pattern_type': None
        },
        {
            'sequence': [1, 2.1, 2.9, 4.1, 4.9],
            'description': "Noisy Arithmetic",
            'expected_confidence_range': (0.50, 0.80),
            'pattern_type': 'arithmetic'
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test_case['description']}")
        print(f"   Sequence: {test_case['sequence']}")

        # Test with reasoning chain
        chain = ReasoningChain()
        result = predict_next_in_sequence(test_case['sequence'], chain, rtol=0.3, atol=1e-8)

        if len(chain.steps) > 0:
            actual_confidence = chain.steps[-1].confidence
            expected_min, expected_max = test_case['expected_confidence_range']

            print(f"   Expected confidence: {expected_min:.2f} - {expected_max:.2f}")
            print(f"   Actual confidence: {actual_confidence:.3f}")
            print(f"   Prediction: {result}")

            # Validate confidence range
            if expected_min <= actual_confidence <= expected_max:
                print(f"   Status: ✅ PASS")
                results['test_cases_passed'] += 1
            else:
                print(f"   Status: ❌ FAIL - Confidence outside expected range")
                results['issues'].append(f"Test {i}: Confidence {actual_confidence:.3f} not in range [{expected_min}, {expected_max}]")
        else:
            print(f"   Status: ❌ FAIL - No reasoning steps recorded")
            results['issues'].append(f"Test {i}: No reasoning steps generated")

    return results

def test_mathematical_formulas():
    """Test the mathematical correctness of confidence calculation components."""
    print("\n🧮 MATHEMATICAL FORMULA VALIDATION")
    print("=" * 50)

    # Test data sufficiency factor
    print("\n📊 Data Sufficiency Factor Tests:")

    # Arithmetic progression thresholds
    arith_2_points = _assess_data_sufficiency(2, 'arithmetic')  # Should be 2/3 ≈ 0.67
    arith_3_points = _assess_data_sufficiency(3, 'arithmetic')  # Should be 1.0
    arith_5_points = _assess_data_sufficiency(5, 'arithmetic')  # Should be 1.0

    print(f"   Arithmetic 2 points: {arith_2_points:.3f} (expected ≈ 0.67)")
    print(f"   Arithmetic 3 points: {arith_3_points:.3f} (expected = 1.00)")
    print(f"   Arithmetic 5 points: {arith_5_points:.3f} (expected = 1.00)")

    # Geometric progression thresholds
    geom_3_points = _assess_data_sufficiency(3, 'geometric')  # Should be 3/4 = 0.75
    geom_4_points = _assess_data_sufficiency(4, 'geometric')  # Should be 1.0
    geom_6_points = _assess_data_sufficiency(6, 'geometric')  # Should be 1.0

    print(f"   Geometric 3 points: {geom_3_points:.3f} (expected = 0.75)")
    print(f"   Geometric 4 points: {geom_4_points:.3f} (expected = 1.00)")
    print(f"   Geometric 6 points: {geom_6_points:.3f} (expected = 1.00)")

    # Test pattern quality scoring
    print("\n📈 Pattern Quality Factor Tests:")

    # Perfect arithmetic differences
    perfect_diffs = np.array([1.0, 1.0, 1.0, 1.0])
    perfect_quality = _calculate_pattern_quality_score(perfect_diffs, 'arithmetic')
    print(f"   Perfect arithmetic: {perfect_quality:.3f} (expected ≈ 1.00)")

    # Noisy arithmetic differences
    noisy_diffs = np.array([1.0, 1.1, 0.9, 1.05])
    noisy_quality = _calculate_pattern_quality_score(noisy_diffs, 'arithmetic')
    print(f"   Noisy arithmetic: {noisy_quality:.3f} (expected < 1.00)")

    # Perfect geometric ratios
    perfect_ratios = [2.0, 2.0, 2.0, 2.0]
    perfect_geom_quality = _calculate_pattern_quality_score(perfect_ratios, 'geometric')
    print(f"   Perfect geometric: {perfect_geom_quality:.3f} (expected ≈ 1.00)")

    return {
        'data_sufficiency_correct': all([
            abs(arith_2_points - 0.667) < 0.01,
            arith_3_points == 1.0,
            abs(geom_3_points - 0.75) < 0.01,
            geom_4_points == 1.0
        ]),
        'pattern_quality_correct': perfect_quality > 0.95 and noisy_quality < perfect_quality
    }

def test_api_compatibility():
    """Test that API remains backward compatible."""
    print("\n🔌 API COMPATIBILITY VALIDATION")
    print("=" * 50)

    # Test function signatures haven't changed
    try:
        # These should work exactly as before
        result1 = predict_next_in_sequence([1, 2, 3])
        result2 = find_pattern_description([2, 4, 8])

        # Test with reasoning chain (optional parameter)
        chain = ReasoningChain()
        result3 = predict_next_in_sequence([1, 3, 5], chain, rtol=0.3, atol=1e-8)
        result4 = find_pattern_description([1, 4, 9], chain, rtol=0.3, atol=1e-8)

        print("✅ All function signatures compatible")
        print(f"   predict_next_in_sequence([1,2,3]) = {result1}")
        print(f"   find_pattern_description([2,4,8]) = '{result2}'")
        print(f"   With reasoning chain: steps recorded = {len(chain.steps)}")

        return True

    except Exception as e:
        print(f"❌ API compatibility issue: {e}")
        return False

def main():
    """Run comprehensive architectural validation."""
    print("🏛️  INDUCTIVE REASONING ARCHITECTURAL REVIEW")
    print("=" * 60)
    print("Validating implementation against design specifications")
    print("=" * 60)

    # Run all validation tests
    design_results = test_design_compliance()
    math_results = test_mathematical_formulas()
    api_compatible = test_api_compatibility()

    # Summary
    print("\n📋 VALIDATION SUMMARY")
    print("=" * 50)

    overall_score = 0
    max_score = 100

    # Design compliance scoring
    compliance_score = (design_results['test_cases_passed'] / design_results['test_cases_total']) * 40
    overall_score += compliance_score
    print(f"Design Compliance: {compliance_score:.1f}/40 ({design_results['test_cases_passed']}/{design_results['test_cases_total']} tests passed)")

    # Mathematical correctness scoring
    math_score = 0
    if math_results['data_sufficiency_correct']:
        math_score += 20
    if math_results['pattern_quality_correct']:
        math_score += 20
    overall_score += math_score
    print(f"Mathematical Correctness: {math_score:.1f}/40")

    # API compatibility scoring
    api_score = 20 if api_compatible else 0
    overall_score += api_score
    print(f"API Compatibility: {api_score:.1f}/20")

    print(f"\n🎯 OVERALL SCORE: {overall_score:.1f}/100")

    if design_results['issues']:
        print(f"\n⚠️  ISSUES FOUND:")
        for issue in design_results['issues']:
            print(f"   • {issue}")

    # Determine approval status
    if overall_score >= 90:
        status = "APPROVED"
        print(f"\n✅ ARCHITECTURAL REVIEW: {status}")
    elif overall_score >= 70:
        status = "PENDING"
        print(f"\n⚠️  ARCHITECTURAL REVIEW: {status} (improvements needed)")
    else:
        status = "REJECTED"
        print(f"\n❌ ARCHITECTURAL REVIEW: {status} (major issues)")

    return {
        'status': status,
        'overall_score': overall_score,
        'design_compliance': compliance_score,
        'mathematical_correctness': math_score,
        'api_compatibility': api_score,
        'issues': design_results['issues']
    }

if __name__ == "__main__":
    results = main()