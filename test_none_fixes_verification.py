#!/usr/bin/env python3
"""
Verification that None crash fixes are working correctly.

This test ensures our critical None crash vulnerabilities have been fixed.
"""

import pytest
from reasoning_library.validation import ValidationError
from reasoning_library.deductive import chain_deductions
from reasoning_library.abductive import _extract_keywords
from reasoning_library.inductive import predict_next_in_sequence, find_pattern_description
from reasoning_library.core import ReasoningChain


def test_critical_none_fixes():
    """Verify that critical None crash vulnerabilities have been fixed."""

    # Test 1: chain_deductions with None functions
    chain = ReasoningChain()
    with pytest.raises(ValidationError, match="Function at position 0 cannot be None"):
        chain_deductions(chain, None)

    # Test 2: _extract_keywords with None text
    with pytest.raises(ValidationError, match="text cannot be None"):
        _extract_keywords(None)

    # Test 3: predict_next_in_sequence with None sequence
    with pytest.raises(ValidationError, match="Expected list/tuple/array for sequence"):
        predict_next_in_sequence(None, None)

    # Test 4: find_pattern_description with None sequence
    with pytest.raises(ValidationError, match="Expected list/tuple/array for sequence"):
        find_pattern_description(None, None)

    print("✅ All critical None crash vulnerabilities have been fixed!")


if __name__ == "__main__":
    test_critical_none_fixes()
    print("✅ Verification successful: None crash prevention is working!")