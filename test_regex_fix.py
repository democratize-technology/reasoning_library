#!/usr/bin/env python3
"""
Test script to debug the current regex patterns and verify the fix.
"""

import re
import inspect
from inductive import _calculate_geometric_confidence, _calculate_arithmetic_confidence

def test_current_regex_patterns():
    """Test what the current regex patterns extract from mathematical functions."""
    print("=" * 80)
    print("TESTING CURRENT REGEX PATTERNS")
    print("=" * 80)

    # Get source code of a mathematical function
    func = _calculate_geometric_confidence
    source_code = inspect.getsource(func) if hasattr(func, '__code__') else ""

    print(f"Function: {func.__name__}")
    print(f"Source code length: {len(source_code)} characters")
    print("\nFirst 500 characters of source:")
    print(source_code[:500] + "..." if len(source_code) > 500 else source_code)

    # Current patterns from core.py
    confidence_patterns = [
        r'confidence.*=.*([^\n]+)',
        r'_calculate.*confidence.*\([^)]+\)',
        r'base_confidence.*\*.*([^\n]+)',
    ]

    print("\n" + "=" * 50)
    print("TESTING CURRENT PATTERNS:")
    print("=" * 50)

    for i, pattern in enumerate(confidence_patterns, 1):
        print(f"\nPattern {i}: {pattern}")
        matches = re.findall(pattern, source_code, re.IGNORECASE | re.MULTILINE)
        print(f"Matches found: {len(matches)}")
        for j, match in enumerate(matches[:3]):  # Limit to first 3 matches
            print(f"  Match {j+1}: '{match}'")

    # Show what the current logic produces
    print("\n" + "=" * 50)
    print("CURRENT LOGIC OUTPUT:")
    print("=" * 50)

    for pattern in confidence_patterns:
        matches = re.findall(pattern, source_code, re.IGNORECASE | re.MULTILINE)
        if matches:
            # Clean up the matches and limit to reasonable length
            clean_matches = [match.strip() for match in matches[:2] if match.strip()]
            if clean_matches:
                confidence_doc = f"Confidence calculation based on: {', '.join(clean_matches)}"
                print(f"Current output: '{confidence_doc}'")
                break
    else:
        print("No matches found with current patterns")

def test_improved_regex_patterns():
    """Test improved regex patterns that should produce better output."""
    print("\n\n" + "=" * 80)
    print("TESTING IMPROVED REGEX PATTERNS")
    print("=" * 80)

    # Get source code of both functions
    funcs = [_calculate_geometric_confidence, _calculate_arithmetic_confidence]

    # Improved patterns focusing on semantic extraction
    improved_patterns = [
        # Pattern 1: Extract confidence factor variable names
        (r'(\w+(?:_\w+)*)\s*(?:\*|,|\+|\-|=)?\s*(?:factor|quality|sufficiency|confidence)',
         "Factor/quality variables"),

        # Pattern 2: Extract descriptive comments
        (r'#.*?(?:confidence|based on|factors?)[\s:]*([^#\n\.]+)',
         "Descriptive comments"),

        # Pattern 3: Extract calculation descriptions from evidence strings
        (r'f?"[^"]*(?:confidence|based on)[\s:]*([^"\.]+)',
         "Evidence descriptions"),

        # Pattern 4: Extract meaningful calculation terms
        (r'(?:based on|considers|calculated from|factors in)[\s:]*([^.\n]+)',
         "Calculation descriptions"),

        # Pattern 5: Extract factor combination patterns
        (r'(\w+_factor)\s*\*\s*(\w+_factor)',
         "Factor combinations"),
    ]

    for func in funcs:
        print(f"\n{'='*20} {func.__name__} {'='*20}")
        source_code = inspect.getsource(func)

        for pattern, description in improved_patterns:
            print(f"\n{description} pattern: {pattern}")
            matches = re.findall(pattern, source_code, re.IGNORECASE | re.MULTILINE)
            print(f"Matches: {matches}")

            if matches:
                # Process matches to create meaningful descriptions
                if isinstance(matches[0], tuple):
                    # For patterns that capture multiple groups
                    processed = [' and '.join(match) if isinstance(match, tuple) else match for match in matches]
                else:
                    processed = [match.strip() for match in matches if match.strip()]

                if processed:
                    print(f"Processed: {processed}")

if __name__ == "__main__":
    test_current_regex_patterns()
    test_improved_regex_patterns()