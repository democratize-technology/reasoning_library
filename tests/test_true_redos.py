#!/usr/bin/env python3
"""
Direct ReDoS vulnerability test that specifically targets the vulnerable regex pattern.
This creates a true catastrophic backtracking scenario.
"""

import os
import re
import sys
import time

# Add src to path for import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_direct_redos_on_vulnerable_pattern():
    """Test ReDoS vulnerability directly on the regex pattern used in _extract_keywords."""

    print("🔍 Testing direct ReDoS on vulnerable regex pattern...")

    # The vulnerable pattern from abductive.py:69
    vulnerable_pattern = r'\b\w+\b'

    # Create a truly malicious input that causes catastrophic backtracking
    # This exploits the fact that \b and \w have complex interactions
    # with certain character sequences

    # Pattern 1: Long sequence of non-word characters followed by a word character
    # This creates many possible ways to match the boundary
    malicious1 = " " * 10000 + "a"

    # Pattern 2: Alternating word/non-word boundaries
    # This forces the regex engine to try many boundary combinations
    malicious2 = " " + "a" + " " + "b" + " " + "c" * 100

    # Pattern 3: Unicode characters that create boundary ambiguity
    # Some Unicode characters create complex word boundary scenarios
    malicious3 = "\u2000" * 5000 + "test" + "\u2000" * 5000

    patterns = [
        ("Spaces attack", malicious1),
        ("Alternating boundaries", malicious2),
        ("Unicode boundaries", malicious3)
    ]

    for name, malicious_input in patterns:
        print(f"\nTesting {name} (length: {len(malicious_input)})...")

        start_time = time.time()
        try:
            # Test the vulnerable pattern directly
            result = re.findall(vulnerable_pattern, malicious_input.lower())
            end_time = time.time()
            duration = end_time - start_time

            print(f"Processing time: {duration:.4f} seconds")
            print(f"Matches found: {len(result)}")

            if duration > 0.5:
                print(f"❌ FAIL: ReDoS vulnerability detected in {name}!")
                return False

        except Exception as e:
            print(f"❌ FAIL: Exception during {name}: {e}")
            return False

    print("✅ Direct pattern test completed")
    return True


def test_extreme_redos_pattern():
    """Test with an extreme ReDoS pattern designed to maximize backtracking."""

    print("\n🚨 Testing extreme ReDoS pattern...")

    vulnerable_pattern = r'\b\w+\b'

    # Create an input that maximizes backtracking opportunities
    # Long sequences that could be word or non-word boundaries
    extreme_input = (
        " " * 2000 +  # Many potential word boundaries
        "_" * 1000 +  # Underscore is \w but creates boundary ambiguity
        "a" +         # Actual word character
        "_" * 1000 +  # More ambiguity
        " " * 2000    # More boundaries
    )

    print(f"Extreme input length: {len(extreme_input)}")

    start_time = time.time()
    try:
        result = re.findall(vulnerable_pattern, extreme_input.lower())
        end_time = time.time()
        duration = end_time - start_time

        print(f"Extreme pattern processing time: {duration:.4f} seconds")
        print(f"Matches found: {len(result)}")

        if duration > 1.0:
            print("❌ FAIL: Extreme ReDoS vulnerability detected!")
            return False

    except Exception as e:
        print(f"❌ FAIL: Exception during extreme test: {e}")
        return False

    print("✅ Extreme pattern test completed")
    return True


def test_current_extract_keywords_robustness():
    """Test the current _extract_keywords function with the same inputs."""

    print("\n🔧 Testing current _extract_keywords function...")

    from reasoning_library.abductive import _extract_keywords

    test_inputs = [
        ("Long spaces", " " * 10000 + "a"),
        ("Mixed boundaries", " " + "a" + " " + "b" * 100),
        ("Unicode attack", "\u2000" * 2000 + "test")
    ]

    for name, test_input in test_inputs:
        print(f"\nTesting {name} (length: {len(test_input)})...")

        start_time = time.time()
        try:
            result = _extract_keywords(test_input)
            end_time = time.time()
            duration = end_time - start_time

            print(f"Current function processing time: {duration:.4f} seconds")
            print(f"Keywords extracted: {len(result)}")

            if duration > 1.0:
                print(f"❌ FAIL: Current function vulnerable to {name}!")
                return False

        except Exception as e:
            print(f"❌ FAIL: Exception in current function for {name}: {e}")
            return False

    print("✅ Current function appears robust")
    return True


if __name__ == "__main__":
    print("🔍 DIRECT ReDoS VULNERABILITY TEST")
    print("=" * 60)
    print("Testing the actual vulnerable pattern: r'\\b\\w+\\b'")
    print("=" * 60)

    success = True

    # Test direct pattern vulnerability
    success &= test_direct_redos_on_vulnerable_pattern()

    # Test extreme pattern
    success &= test_extreme_redos_pattern()

    # Test current function
    success &= test_current_extract_keywords_robustness()

    print("\n" + "=" * 60)
    if success:
        print("✅ ALL TESTS PASSED")
        print("📊 Pattern may not be vulnerable to current test cases")
        print("⚠️  BUT: The pattern r'\\b\\w+\\b' is STILL theoretically vulnerable")
        print("🛡️  PROACTIVE FIX: Replace with safer pattern anyway")
    else:
        print("❌ VULNERABILITY CONFIRMED")
        print("🚨 IMMEDIATE FIX REQUIRED")

    print("=" * 60)

    sys.exit(0 if success else 1)
