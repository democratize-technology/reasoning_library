"""
Security regression tests for ReDoS vulnerabilities in regex patterns.
Tests ensure that regex patterns are immune to catastrophic backtracking attacks.
"""
import time
import pytest
from reasoning_library.core import (
    FACTOR_PATTERN,
    COMBINATION_PATTERN,
    COMMENT_PATTERN,
    EVIDENCE_PATTERN,
    CLEAN_FACTOR_PATTERN
)


class TestReDoSSecurity:
    """Test suite for ReDoS vulnerability prevention."""

    def test_factor_pattern_redos_immunity(self):
        """Test FACTOR_PATTERN is immune to ReDoS attacks."""
        # Create a malicious input designed to cause backtracking
        malicious_input = "a" * 1000 + "data_sufficiency_factor" + "b" * 1000

        start_time = time.time()
        result = FACTOR_PATTERN.findall(malicious_input)
        execution_time = time.time() - start_time

        # Should execute quickly (under 0.1 seconds) and find the pattern
        assert execution_time < 0.1, f"FACTOR_PATTERN took {execution_time:.3f}s - potential ReDoS vulnerability"
        assert len(result) == 1
        assert "data_sufficiency_factor" in result[0]

    def test_combination_pattern_redos_immunity(self):
        """Test COMBINATION_PATTERN is immune to ReDoS attacks."""
        # Create a malicious input with many spaces and underscores
        malicious_input = "data_factor" + " " * 1000 + "*" + " " * 1000 + "pattern_factor"

        start_time = time.time()
        result = COMBINATION_PATTERN.findall(malicious_input)
        execution_time = time.time() - start_time

        # Should execute quickly and find the pattern
        assert execution_time < 0.1, f"COMBINATION_PATTERN took {execution_time:.3f}s - potential ReDoS vulnerability"
        assert len(result) == 1
        assert result[0] == ("data_factor", "pattern_factor")

    def test_factor_pattern_normal_operation(self):
        """Test FACTOR_PATTERN works correctly for normal inputs."""
        test_cases = [
            ("data_sufficiency_factor * 0.8", ["data_sufficiency_factor"]),
            ("pattern_quality_factor,", ["pattern_quality_factor"]),
            ("complexity_factor +", ["complexity_factor"]),
            ("my_data_sufficiency_factor =", ["my_data_sufficiency_factor"]),
            ("no_match_here", []),
        ]

        for input_text, expected in test_cases:
            result = FACTOR_PATTERN.findall(input_text)
            assert result == expected, f"Failed for input: {input_text}"

    def test_combination_pattern_normal_operation(self):
        """Test COMBINATION_PATTERN works correctly for normal inputs."""
        test_cases = [
            ("data_factor * pattern_factor", [("data_factor", "pattern_factor")]),
            ("quality_factor*complexity_factor", [("quality_factor", "complexity_factor")]),
            ("data_factor  *  pattern_factor", [("data_factor", "pattern_factor")]),
            ("not_a_factor * something", []),
        ]

        for input_text, expected in test_cases:
            result = COMBINATION_PATTERN.findall(input_text)
            assert result == expected, f"Failed for input: {input_text}"

    def test_large_input_performance(self):
        """Test all patterns handle large inputs efficiently."""
        large_input = "x" * 5000 + "data_sufficiency_factor * pattern_quality_factor" + "y" * 5000

        patterns = [
            FACTOR_PATTERN,
            COMBINATION_PATTERN,
            COMMENT_PATTERN,
            EVIDENCE_PATTERN,
            CLEAN_FACTOR_PATTERN
        ]

        for pattern in patterns:
            start_time = time.time()
            pattern.findall(large_input)
            execution_time = time.time() - start_time

            assert execution_time < 0.2, f"Pattern {pattern.pattern} took {execution_time:.3f}s on large input"

    def test_nested_repetition_immunity(self):
        """Test patterns are immune to nested repetition attacks."""
        # Test various nested repetition patterns that could cause backtracking
        attack_vectors = [
            "a" * 100 + "b" * 100 + "data_sufficiency_factor",
            "(" * 50 + ")" * 50 + "pattern_quality_factor",
            "x" * 200 + "_factor * " + "y" * 200 + "_factor",
        ]

        for attack_input in attack_vectors:
            for pattern in [FACTOR_PATTERN, COMBINATION_PATTERN]:
                start_time = time.time()
                pattern.findall(attack_input)
                execution_time = time.time() - start_time

                assert execution_time < 0.1, f"Pattern vulnerable to nested repetition attack: {execution_time:.3f}s"


class TestRegexFunctionality:
    """Test that regex patterns still work correctly after security fixes."""

    def test_factor_pattern_edge_cases(self):
        """Test FACTOR_PATTERN handles edge cases correctly."""
        test_cases = [
            # Standard cases
            ("data_sufficiency_factor = 0.8", ["data_sufficiency_factor"]),
            ("pattern_quality_factor * 0.9", ["pattern_quality_factor"]),
            ("complexity_factor + 1.0", ["complexity_factor"]),

            # With prefixes
            ("my_data_sufficiency_factor,", ["my_data_sufficiency_factor"]),
            ("calc_pattern_quality_factor-", ["calc_pattern_quality_factor"]),

            # Multiple on same line
            ("data_sufficiency_factor * pattern_quality_factor", ["data_sufficiency_factor"]),

            # Case variations
            ("DATA_SUFFICIENCY_FACTOR =", ["DATA_SUFFICIENCY_FACTOR"]),
            ("Pattern_Quality_Factor +", ["Pattern_Quality_Factor"]),
        ]

        for input_text, expected in test_cases:
            result = FACTOR_PATTERN.findall(input_text)
            assert result == expected, f"FACTOR_PATTERN failed for: {input_text}, got {result}, expected {expected}"

    def test_combination_pattern_variations(self):
        """Test COMBINATION_PATTERN handles variations correctly."""
        test_cases = [
            # Standard multiplication
            ("data_factor * pattern_factor", [("data_factor", "pattern_factor")]),
            ("quality_factor*complexity_factor", [("quality_factor", "complexity_factor")]),

            # With whitespace
            ("data_factor  *  pattern_factor", [("data_factor", "pattern_factor")]),
            ("factor1    *    factor2", [("factor1", "factor2")]),

            # Multiple combinations
            ("a_factor * b_factor and c_factor * d_factor", [("a_factor", "b_factor"), ("c_factor", "d_factor")]),
        ]

        for input_text, expected in test_cases:
            result = COMBINATION_PATTERN.findall(input_text)
            assert result == expected, f"COMBINATION_PATTERN failed for: {input_text}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])