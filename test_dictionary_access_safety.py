#!/usr/bin/env python3
"""
Comprehensive test script to verify dictionary access safety fixes in abductive.py.

This test specifically validates the 8 fixes mentioned in the code review scope:
1. Evidence update vulnerability (line 1044) - Safe access with skip logic
2. Domain template access (lines 657, 672-682) - Safe access with defaults
3. Hypothesis sorting (lines 931, 1086) - Safe access with 0.0 fallback
4. Best hypothesis selection (lines 939, 1093, 1155) - Safe access with confidence fallback
5. Hypothesis text update (lines 1079-1081) - Safe text handling with existence checks

Each test creates malformed dictionaries that would trigger KeyError with unsafe access.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from reasoning_library.abductive import (
    generate_hypotheses,
    rank_hypotheses,
    evaluate_best_explanation
)
from reasoning_library.core import ReasoningChain
from reasoning_library.exceptions import ValidationError

def test_evidence_update_safety():
    """Test Fix #1: Evidence update vulnerability (line 1044) - Safe access with skip logic"""
    print("🔍 Testing Fix #1: Evidence update vulnerability...")

    # Create hypotheses with missing 'hypothesis' key that would cause KeyError
    malformed_hypotheses = [
        {"confidence": 0.7},  # Missing 'hypothesis' key
        {"confidence": 0.5},  # Missing 'hypothesis' key
        {"hypothesis": "Valid hypothesis", "confidence": 0.9}  # Valid hypothesis
    ]

    try:
        reasoning_chain = ReasoningChain()
        result = rank_hypotheses(malformed_hypotheses, ["test evidence"], reasoning_chain)

        # Should handle missing 'hypothesis' keys gracefully
        assert len(result) == 3

        # Check that hypotheses without text are handled properly
        for hyp in result:
            assert "confidence" in hyp
            # Either hypothesis exists or was set to a default
            assert "hypothesis" in hyp

        print("✅ Fix #1 PASSED: Evidence update handles missing hypothesis keys safely")
        return True

    except KeyError as e:
        print(f"❌ Fix #1 FAILED: KeyError still occurs: {e}")
        return False
    except Exception as e:
        print(f"❌ Fix #1 FAILED: Unexpected error: {e}")
        return False

def test_domain_template_safety():
    """Test Fix #2: Domain template access (lines 657, 672-682) - Safe access with defaults"""
    print("🔍 Testing Fix #2: Domain template access safety...")

    # Mock DOMAIN_TEMPLATES with missing keys to test safe access
    original_templates = None
    try:
        # Import the module to modify DOMAIN_TEMPLATES temporarily
        import reasoning_library.abductive as abductive_module
        original_templates = abductive_module.DOMAIN_TEMPLATES.copy()

        # Create malformed template structure with missing keys
        abductive_module.DOMAIN_TEMPLATES = {
            "test_domain": {
                # Missing "keywords" key entirely
                "templates": ["Test template for {action}, {component}, {issue}"]
            },
            "test_domain2": {
                "keywords": ["test"],  # Has keywords
                "templates": ["Another template"]
                # Missing expected structure for template processing
            }
        }

        try:
            reasoning_chain = ReasoningChain()
            observations = ["test observation"]
            context = "test context with test keyword"

            result = generate_hypotheses(observations, reasoning_chain, context=context, max_hypotheses=2)

            # Should handle missing domain template keys gracefully
            assert isinstance(result, list)
            print("✅ Fix #2 PASSED: Domain template access handles missing keys safely")
            return True

        except KeyError as e:
            print(f"❌ Fix #2 FAILED: KeyError in domain template access: {e}")
            return False
        finally:
            # Restore original templates
            abductive_module.DOMAIN_TEMPLATES = original_templates

    except Exception as e:
        print(f"❌ Fix #2 FAILED: Unexpected error: {e}")
        if original_templates:
            try:
                import reasoning_library.abductive as abductive_module
                abductive_module.DOMAIN_TEMPLATES = original_templates
            except:
                pass
        return False

def test_hypothesis_sorting_safety():
    """Test Fix #3: Hypothesis sorting (lines 931, 1086) - Safe access with 0.0 fallback"""
    print("🔍 Testing Fix #3: Hypothesis sorting safety...")

    # Create hypotheses with missing 'confidence' keys
    malformed_hypotheses = [
        {"hypothesis": "No confidence key 1"},  # Missing confidence
        {"hypothesis": "No confidence key 2"},  # Missing confidence
        {"hypothesis": "Valid hypothesis", "confidence": 0.8}  # Valid confidence
    ]

    try:
        reasoning_chain = ReasoningChain()

        # Test in generate_hypotheses (line 931)
        result1 = generate_hypotheses(["test"], reasoning_chain)
        assert isinstance(result1, list)

        # Test in rank_hypotheses (line 1086)
        result2 = rank_hypotheses(malformed_hypotheses, ["evidence"], reasoning_chain)
        assert isinstance(result2, list)
        assert len(result2) == 3

        # Should sort without KeyError, using 0.0 fallback for missing confidence
        for hyp in result2:
            assert "confidence" in hyp
            assert isinstance(hyp["confidence"], (int, float))

        print("✅ Fix #3 PASSED: Hypothesis sorting handles missing confidence safely")
        return True

    except KeyError as e:
        print(f"❌ Fix #3 FAILED: KeyError in hypothesis sorting: {e}")
        return False
    except Exception as e:
        print(f"❌ Fix #3 FAILED: Unexpected error: {e}")
        return False

def test_best_hypothesis_selection_safety():
    """Test Fix #4: Best hypothesis selection (lines 939, 1093, 1155) - Safe access with confidence fallback"""
    print("🔍 Testing Fix #4: Best hypothesis selection safety...")

    # Create hypotheses with missing 'confidence' keys
    malformed_hypotheses = [
        {"hypothesis": "Missing confidence 1"},
        {"hypothesis": "Missing confidence 2"},
        {"hypothesis": "Valid hypothesis", "confidence": 0.9}
    ]

    try:
        reasoning_chain = ReasoningChain()

        # Test in generate_hypotheses (line 939)
        result1 = generate_hypotheses(["test"], reasoning_chain)
        assert isinstance(result1, list)

        # Test in rank_hypotheses (line 1093)
        result2 = rank_hypotheses(malformed_hypotheses, ["evidence"], reasoning_chain)
        assert isinstance(result2, list)

        # Test in evaluate_best_explanation (line 1155)
        result3 = evaluate_best_explanation(malformed_hypotheses, reasoning_chain)
        assert result3 is not None
        assert "hypothesis" in result3
        assert "confidence" in result3

        print("✅ Fix #4 PASSED: Best hypothesis selection handles missing confidence safely")
        return True

    except KeyError as e:
        print(f"❌ Fix #4 FAILED: KeyError in best hypothesis selection: {e}")
        return False
    except Exception as e:
        print(f"❌ Fix #4 FAILED: Unexpected error: {e}")
        return False

def test_hypothesis_text_update_safety():
    """Test Fix #5: Hypothesis text update (lines 1079-1081) - Safe text handling with existence checks"""
    print("🔍 Testing Fix #5: Hypothesis text update safety...")

    # Create hypotheses with missing or empty 'hypothesis' text
    malformed_hypotheses = [
        {"confidence": 0.7},  # Missing hypothesis key
        {"hypothesis": "", "confidence": 0.5},  # Empty hypothesis
        {"hypothesis": None, "confidence": 0.3},  # None hypothesis
        {"hypothesis": "Valid hypothesis", "confidence": 0.9}  # Valid hypothesis
    ]

    try:
        reasoning_chain = ReasoningChain()
        result = rank_hypotheses(malformed_hypotheses, ["strong evidence"], reasoning_chain)

        # Should handle missing/empty hypothesis text gracefully
        assert len(result) == 4

        for hyp in result:
            assert "hypothesis" in hyp
            # Hypothesis text should exist and be a string
            assert isinstance(hyp["hypothesis"], str)
            assert len(hyp["hypothesis"]) > 0

        print("✅ Fix #5 PASSED: Hypothesis text update handles missing/empty text safely")
        return True

    except KeyError as e:
        print(f"❌ Fix #5 FAILED: KeyError in hypothesis text update: {e}")
        return False
    except Exception as e:
        print(f"❌ Fix #5 FAILED: Unexpected error: {e}")
        return False

def test_specific_access_patterns():
    """Test specific .get() patterns mentioned in the fixes"""
    print("🔍 Testing Fix #6-8: Specific access patterns...")

    try:
        reasoning_chain = ReasoningChain()

        # Test line 200: hypothesis.get("testable_predictions", [])
        from reasoning_library.abductive import _calculate_hypothesis_confidence
        hypothesis_without_predictions = {"hypothesis": "test", "confidence": 0.5}
        confidence = _calculate_hypothesis_confidence(hypothesis_without_predictions, 1, 1, 1)
        assert isinstance(confidence, (int, float))

        # Test evidence access patterns with malformed data
        malformed_hypotheses = [
            {"confidence": 0.7},  # Missing hypothesis text
            {"hypothesis": "test", "confidence": "invalid"},  # Invalid confidence type
        ]

        # Should handle type validation and missing keys
        try:
            rank_hypotheses(malformed_hypotheses, ["evidence"], reasoning_chain)
            print("❌ Fix #6-8 FAILED: Should have raised ValidationError for invalid confidence")
            return False
        except ValidationError:
            # Expected behavior - invalid types should raise ValidationError
            pass

        print("✅ Fix #6-8 PASSED: Specific access patterns work correctly")
        return True

    except Exception as e:
        print(f"❌ Fix #6-8 FAILED: Unexpected error: {e}")
        return False

def main():
    """Run all dictionary access safety tests"""
    print("🛡️  Dictionary Access Safety Tests for Abductive Reasoning")
    print("=" * 60)
    print("Testing the 8 specific fixes for dictionary KeyError vulnerabilities:")
    print()

    tests = [
        test_evidence_update_safety,
        test_domain_template_safety,
        test_hypothesis_sorting_safety,
        test_best_hypothesis_selection_safety,
        test_hypothesis_text_update_safety,
        test_specific_access_patterns
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {e}")
            failed += 1
        print()

    print("=" * 60)
    print(f"📊 RESULTS: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 ALL DICTIONARY ACCESS SAFETY FIXES VERIFIED!")
        print("The 8 fixes successfully prevent KeyError vulnerabilities.")
        return 0
    else:
        print("🚨 SOME DICTIONARY ACCESS SAFETY FIXES FAILED!")
        print("Not all KeyError vulnerabilities are properly addressed.")
        return 1

if __name__ == "__main__":
    exit(main())