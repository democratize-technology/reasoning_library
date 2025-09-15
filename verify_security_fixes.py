"""
Simple security verification script to test ReDoS fixes.
Tests the regex patterns and optimization improvements.
"""
import time
import sys
from reasoning_library.core import (
    FACTOR_PATTERN,
    COMBINATION_PATTERN,
    _detect_mathematical_reasoning,
    tool_spec
)


def test_redos_immunity():
    """Test that regex patterns are immune to ReDoS attacks."""
    print("🔒 Testing ReDoS immunity...")

    # Test FACTOR_PATTERN
    malicious_input = "a" * 1000 + "data_sufficiency_factor" + "b" * 1000
    start_time = time.time()
    result = FACTOR_PATTERN.findall(malicious_input)
    execution_time = time.time() - start_time

    print(f"  FACTOR_PATTERN: {execution_time:.3f}s ({'✅ SAFE' if execution_time < 0.1 else '❌ VULNERABLE'})")
    assert execution_time < 0.1, f"FACTOR_PATTERN vulnerable: {execution_time:.3f}s"
    assert len(result) == 1 and "data_sufficiency_factor" in result[0]

    # Test COMBINATION_PATTERN
    malicious_input2 = "data_factor" + " " * 1000 + "*" + " " * 1000 + "pattern_factor"
    start_time = time.time()
    result2 = COMBINATION_PATTERN.findall(malicious_input2)
    execution_time = time.time() - start_time

    print(f"  COMBINATION_PATTERN: {execution_time:.3f}s ({'✅ SAFE' if execution_time < 0.1 else '❌ VULNERABLE'})")
    assert execution_time < 0.1, f"COMBINATION_PATTERN vulnerable: {execution_time:.3f}s"
    assert len(result2) == 1 and result2[0] == ("data_factor", "pattern_factor")


def test_regex_functionality():
    """Test that regex patterns still work correctly."""
    print("🧪 Testing regex functionality...")

    # Test FACTOR_PATTERN normal operation
    test_cases = [
        ("data_sufficiency_factor * 0.8", ["data_sufficiency_factor"]),
        ("pattern_quality_factor,", ["pattern_quality_factor"]),
        ("complexity_factor +", ["complexity_factor"]),
        ("no_match_here", []),
    ]

    for input_text, expected in test_cases:
        result = FACTOR_PATTERN.findall(input_text)
        assert result == expected, f"FACTOR_PATTERN failed for: {input_text}"

    print("  ✅ FACTOR_PATTERN functionality working")

    # Test COMBINATION_PATTERN normal operation
    test_cases2 = [
        ("data_factor * pattern_factor", [("data_factor", "pattern_factor")]),
        ("quality_factor*complexity_factor", [("quality_factor", "complexity_factor")]),
        ("not_a_factor * something", []),
    ]

    for input_text, expected in test_cases2:
        result = COMBINATION_PATTERN.findall(input_text)
        assert result == expected, f"COMBINATION_PATTERN failed for: {input_text}"

    print("  ✅ COMBINATION_PATTERN functionality working")


def test_source_code_optimization():
    """Test that source code extraction optimization works."""
    print("⚡ Testing source code optimization...")

    # Create a function with no mathematical indicators
    def simple_function():
        """Just a simple function with no math."""
        return "hello"

    # Should return False quickly without extracting source
    start_time = time.time()
    is_math, conf_doc, math_basis = _detect_mathematical_reasoning(simple_function)
    execution_time = time.time() - start_time

    print(f"  Non-math function: {execution_time:.3f}s ({'✅ FAST' if execution_time < 0.001 else '⚠️ SLOW'})")
    assert not is_math, "Should not detect simple function as mathematical"

    # Create a function with mathematical indicators
    def math_function():
        """Function for confidence calculation and statistical analysis."""
        return 0.95

    # Should detect as mathematical and extract patterns
    start_time = time.time()
    is_math2, conf_doc2, math_basis2 = _detect_mathematical_reasoning(math_function)
    execution_time2 = time.time() - start_time

    print(f"  Math function: {execution_time2:.3f}s ({'✅ DETECTED' if is_math2 else '❌ MISSED'})")
    assert is_math2, "Should detect function with mathematical keywords"


def test_hybrid_explicit_declaration():
    """Test that explicit declarations work correctly."""
    print("🔧 Testing hybrid explicit declaration...")

    @tool_spec(
        mathematical_basis="Test explicit declaration",
        confidence_factors=["test_factor1", "test_factor2"]
    )
    def explicit_function():
        """Test function with explicit metadata."""
        return 42

    # Should use explicit metadata, not heuristic detection
    assert hasattr(explicit_function, 'tool_spec')
    spec = explicit_function.tool_spec

    # Check that the function description contains explicit metadata
    description = spec['function']['description']
    assert "Mathematical Basis: Test explicit declaration" in description
    assert "test_factor1, test_factor2" in description

    print("  ✅ Explicit declarations working")


def run_all_tests():
    """Run all security and functionality tests."""
    print("🚀 Running Security Verification Tests\n")

    try:
        test_redos_immunity()
        print()

        test_regex_functionality()
        print()

        test_source_code_optimization()
        print()

        test_hybrid_explicit_declaration()
        print()

        print("✅ ALL TESTS PASSED - Security fixes verified!")
        return True

    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)