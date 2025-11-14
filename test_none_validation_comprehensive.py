#!/usr/bin/env python3
"""
Comprehensive validation test for None crash fixes.

This test validates that the specific functions mentioned in the requirements
are properly handling None inputs by raising ValidationError instead of crashing.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from reasoning_library.validation import ValidationError
from reasoning_library.deductive import apply_modus_ponens
from reasoning_library.abductive import generate_hypotheses, rank_hypotheses
from reasoning_library.core import ReasoningChain


def test_validate_hypothesis_dict_none_fix():
    """Test that validate_hypothesis_dict raises ValidationError for None input."""
    from reasoning_library.validation import validate_hypothesis_dict

    try:
        result = validate_hypothesis_dict(None, "test_field")
        return False, f"ERROR: Expected ValidationError but got result: {result}"
    except ValidationError as e:
        return True, f"✅ SUCCESS: validate_hypothesis_dict correctly raised ValidationError: {str(e)}"
    except Exception as e:
        return False, f"ERROR: Expected ValidationError but got {type(e).__name__}: {str(e)}"


def test_generate_hypotheses_none_fix():
    """Test that generate_hypotheses raises ValidationError for None observations."""
    try:
        result = generate_hypotheses(None, None)
        return False, f"ERROR: Expected ValidationError but got result: {result}"
    except ValidationError as e:
        return True, f"✅ SUCCESS: generate_hypotheses correctly raised ValidationError: {str(e)}"
    except Exception as e:
        return False, f"ERROR: Expected ValidationError but got {type(e).__name__}: {str(e)}"


def test_rank_hypotheses_none_fix():
    """Test that rank_hypotheses raises ValidationError for None hypotheses."""
    try:
        result = rank_hypotheses(None, [], None)
        return False, f"ERROR: Expected ValidationError but got result: {result}"
    except ValidationError as e:
        return True, f"✅ SUCCESS: rank_hypotheses correctly raised ValidationError: {str(e)}"
    except Exception as e:
        return False, f"ERROR: Expected ValidationError but got {type(e).__name__}: {str(e)}"


def test_apply_modus_ponens_none_fix():
    """Test that apply_modus_ponens raises ValidationError for None inputs."""
    try:
        result = apply_modus_ponens(None, None, None)
        return False, f"ERROR: Expected ValidationError but got result: {result}"
    except ValidationError as e:
        return True, f"✅ SUCCESS: apply_modus_ponens correctly raised ValidationError: {str(e)}"
    except Exception as e:
        return False, f"ERROR: Expected ValidationError but got {type(e).__name__}: {str(e)}"


def test_valid_inputs_still_work():
    """Test that valid inputs still work correctly (regression test)."""

    # Test apply_modus_ponens with valid inputs
    try:
        chain = ReasoningChain()
        result = apply_modus_ponens(True, True, chain)
        # Should return True for valid modus ponens
        if result is True:
            return True, "✅ SUCCESS: apply_modus_ponens works with valid inputs"
        else:
            return False, f"ERROR: Expected True for valid modus ponens, got {result}"
    except Exception as e:
        return False, f"ERROR: Valid inputs failed in apply_modus_ponens: {type(e).__name__}: {str(e)}"


def main():
    """Run all validation tests."""
    print("=" * 70)
    print("COMPREHENSIVE VALIDATION TEST FOR None CRASH FIXES")
    print("=" * 70)

    tests = [
        ("validate_hypothesis_dict None fix", test_validate_hypothesis_dict_none_fix),
        ("generate_hypotheses None fix", test_generate_hypotheses_none_fix),
        ("rank_hypotheses None fix", test_rank_hypotheses_none_fix),
        ("apply_modus_ponens None fix", test_apply_modus_ponens_none_fix),
        ("Valid inputs still work", test_valid_inputs_still_work),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\nTesting: {test_name}")
        success, message = test_func()
        results.append(success)
        print(f"  {message}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"🎉 ALL {total} TESTS PASSED!")
        print("✅ None crash vulnerabilities have been successfully fixed")
        print("✅ All specified functions now raise ValidationError for None inputs")
        print("✅ Valid inputs continue to work correctly")
        return True
    else:
        print(f"❌ {total - passed} OF {total} TESTS FAILED")
        print("⚠️ Some None crash fixes may not be working correctly")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)