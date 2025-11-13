#!/usr/bin/env python3
"""
Test suite for HIGH-001 ReDoS vulnerability fix in keyword extraction.

This test verifies that the regular expression DoS vulnerability has been
fixed with proper input validation, length limits, and safe patterns.
"""

import pytest
import time
import sys
import os

# Add src to path for importing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from reasoning_library.abductive import _extract_keywords


class TestReDoSFixHigh001:
    """Test cases for HIGH-001 ReDoS vulnerability fix."""

    def test_input_validation_prevents_crashes(self):
        """Test that input validation prevents crashes on invalid inputs."""
        # Test with None input
        result = _extract_keywords(None)
        assert isinstance(result, list)
        assert len(result) == 0

        # Test with non-string input
        result = _extract_keywords(123)
        assert isinstance(result, list)
        assert len(result) == 0

        result = _extract_keywords([])
        assert isinstance(result, list)
        assert len(result) == 0

    def test_long_input_truncation(self):
        """Test that very long inputs are safely truncated."""
        # Create a very long string that would normally cause performance issues
        very_long_input = "a" * 10000 + " word " * 1000

        start_time = time.time()
        result = _extract_keywords(very_long_input)
        elapsed_time = time.time() - start_time

        # Should complete quickly (under 0.1 seconds)
        assert elapsed_time < 0.1, f"Processing took too long: {elapsed_time:.3f}s"

        # Should return reasonable number of keywords (limited by safety checks)
        assert len(result) <= 50, f"Too many keywords returned: {len(result)}"

        # Should not contain the extremely long word (truncated by length limits)
        long_words = [word for word in result if len(word) > 50]
        assert len(long_words) == 0, "Found words longer than 50 characters"

    def test_keyword_extraction_limits(self):
        """Test that keyword extraction respects safety limits."""
        # Create input with many repeated words to test keyword explosion prevention
        many_words_input = "word " * 1000 + " " + "different " * 500

        start_time = time.time()
        result = _extract_keywords(many_words_input)
        elapsed_time = time.time() - start_time

        # Should complete quickly
        assert elapsed_time < 0.05, f"Processing took too long: {elapsed_time:.3f}s"

        # Should respect keyword limits
        assert len(result) <= 50, f"Keyword limit exceeded: {len(result)}"

    def test_regex_pattern_safety(self):
        """Test that the regex pattern handles edge cases safely."""
        # Test with characters that could cause backtracking issues
        edge_case_inputs = [
            "a" * 100 + "!",  # Long word with non-alphanumeric
            "a" * 50 + " " + "b" * 50 + " " + "c" * 50,  # Multiple long words
            "!!!!!!!!!!",  # Only special characters
            "a1b2c3d4e5f6g7h8i9j0" * 10,  # Long alphanumeric pattern
            "",  # Empty string
        ]

        for test_input in edge_case_inputs:
            start_time = time.time()
            result = _extract_keywords(test_input)
            elapsed_time = time.time() - start_time

            # Each should complete very quickly
            assert elapsed_time < 0.01, f"Input '{test_input[:20]}...' took too long: {elapsed_time:.3f}s"

            # Results should be reasonable
            assert isinstance(result, list)
            assert all(isinstance(word, str) for word in result)
            assert all(len(word) <= 50 for word in result)

    def test_performance_under_attack(self):
        """Test performance under simulated ReDoS attack conditions."""
        # Simulate various attack patterns that could cause ReDoS
        attack_patterns = [
            "a" * 1000,  # Very long single word
            "a " * 2000,  # Many short words
            "a" * 100 + "b" * 100 + "c" * 100 + "d" * 100,  # Long repeated patterns
            "abcdefghijklmnopqrstuvwxyz" * 100,  # Repeated alphabet
        ]

        for pattern in attack_patterns:
            start_time = time.time()
            result = _extract_keywords(pattern)
            elapsed_time = time.time() - start_time

            # Should resist ReDoS attacks - complete quickly
            assert elapsed_time < 0.05, f"ReDoS resistance failed for pattern: {elapsed_time:.3f}s"

    def test_functional_correctness_maintained(self):
        """Test that the fix doesn't break normal keyword extraction functionality."""
        # Test normal inputs still work correctly
        normal_inputs = [
            "The system is experiencing performance issues",
            "Database connection failed due to timeout",
            "Memory usage increased after recent deployment",
            "Server crashed with segmentation fault",
        ]

        for text in normal_inputs:
            result = _extract_keywords(text)

            # Should extract meaningful keywords
            assert len(result) > 0, f"No keywords extracted from: {text}"

            # Should not include common words
            common_words = {'the', 'is', 'with', 'due', 'to', 'after'}
            for word in result:
                assert word not in common_words, f"Common word '{word}' not filtered out"

            # Should include relevant terms
            relevant_terms = {'system', 'performance', 'database', 'connection', 'timeout',
                            'memory', 'usage', 'deployment', 'server', 'crashed'}
            found_relevant = any(word.lower() in relevant_terms for word in result)
            assert found_relevant, f"No relevant terms found in: {result}"

    def test_critical_redos_vulnerability_fixed(self):
        """CRITICAL TEST: Verify the ReDoS vulnerability is actually fixed."""
        # This test verifies the specific vulnerability mentioned in HIGH-001

        # Before fix: re.findall(r'[a-zA-Z0-9]+') could be vulnerable
        # After fix: should use pre-compiled pattern with length limits

        # Test the original vulnerable pattern conditions
        vulnerable_inputs = [
            # These could potentially cause issues with naive regex implementations
            "a" * 1000 + "!",
            "a" * 5000,  # Very long input
            "word" * 2000,  # Many repeated patterns
        ]

        for test_input in vulnerable_inputs:
            start_time = time.time()
            result = _extract_keywords(test_input)
            elapsed_time = time.time() - start_time

            # CRITICAL: Must complete quickly to prove ReDoS is fixed
            assert elapsed_time < 0.1, f"CRITICAL: ReDoS vulnerability still present! Took {elapsed_time:.3f}s"

            # CRITICAL: Must not return excessive keywords
            assert len(result) <= 50, f"CRITICAL: Keyword explosion not prevented! Returned {len(result)} keywords"

            # CRITICAL: Must respect length limits
            for word in result:
                assert len(word) <= 50, f"CRITICAL: Word length limit not enforced! Found: '{word}' (len={len(word)})"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])