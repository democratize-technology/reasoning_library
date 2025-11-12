"""
Test for the CRITICAL DoS vulnerability fix in contextual hypotheses.

This test validates the fix for a critical security issue where contextual hypotheses
could still contain extremely long strings (5000+ characters) even after input validation,
due to keyword extraction from truncated but repetitive context strings.

The vulnerability was identified and fixed during code review on 2025-01-20.
"""

import pytest
from reasoning_library.abductive import generate_hypotheses


class TestContextualDoSVulnerabilityFix:
    """Test the fix for the critical contextual hypothesis DoS vulnerability."""

    def test_contextual_hypothesis_dos_attack_prevention(self):
        """Test that contextual hypotheses cannot contain extremely long repetitive strings."""
        # Create a malicious context that would trigger the vulnerability
        malicious_context = "A" * 5000  # 5KB repetitive string (after truncation)
        observations = ["System experiencing issues"]

        result = generate_hypotheses(
            observations=observations,
            reasoning_chain=None,
            context=malicious_context,
            max_hypotheses=1
        )

        # Should still return results
        assert len(result) > 0

        # Find contextual hypothesis (if it exists)
        contextual_hypotheses = [h for h in result if h.get("type") == "contextual"]

        for hypothesis in contextual_hypotheses:
            hypothesis_text = hypothesis["hypothesis"]

            # CRITICAL: Hypothesis must not be extremely long
            assert len(hypothesis_text) < 1000, f"Contextual hypothesis too long: {len(hypothesis_text)} chars"

            # Must not contain large blocks of repetitive characters
            assert "A" * 100 not in hypothesis_text, "Contains large repetitive character block"

            # Should be reasonable English text
            assert len(hypothesis_text.split()) >= 3, "Too short to be meaningful"

    def test_contextual_hypothesis_keyword_truncation(self):
        """Test that keywords in contextual hypotheses are properly truncated."""
        # Create context with long keywords
        long_keyword1 = "B" * 1000
        long_keyword2 = "C" * 800
        context = f"System with {long_keyword1} and {long_keyword2} issues"
        observations = ["System problem detected"]

        result = generate_hypotheses(
            observations=observations,
            reasoning_chain=None,
            context=context,
            max_hypotheses=1
        )

        contextual_hypotheses = [h for h in result if h.get("type") == "contextual"]

        for hypothesis in contextual_hypotheses:
            hypothesis_text = hypothesis["hypothesis"]

            # Should not contain extremely long keywords
            assert long_keyword1 not in hypothesis_text, "Long keyword not truncated"
            assert long_keyword2 not in hypothesis_text, "Long keyword not truncated"

            # Keywords should be truncated to reasonable length
            if "context:" in hypothesis_text:
                # Extract the part after "context:" to check keyword length
                keyword_part = hypothesis_text.split("context:")[1].strip()
                if keyword_part:
                    individual_keywords = [kw.strip() for kw in keyword_part.split(',')]
                    for kw in individual_keywords:
                        assert len(kw) <= 50, f"Keyword too long: {len(kw)} chars: {kw}"

    def test_contextual_hypothesis_hard_length_limit(self):
        """Test that contextual hypotheses have a hard length limit."""
        # Create context that would normally create a very long hypothesis
        many_keywords = ["X" * 60 for _ in range(10)]  # 10 long keywords
        context = " ".join(many_keywords)
        observations = ["Multiple issues detected"]

        result = generate_hypotheses(
            observations=observations,
            reasoning_chain=None,
            context=context,
            max_hypotheses=1
        )

        contextual_hypotheses = [h for h in result if h.get("type") == "contextual"]

        for hypothesis in contextual_hypotheses:
            hypothesis_text = hypothesis["hypothesis"]

            # Must have hard length limit of 500 chars
            assert len(hypothesis_text) <= 500, f"Hard length limit violated: {len(hypothesis_text)} chars"

    def test_contextual_hypothesis_fallback_behavior(self):
        """Test that contextual hypotheses still work correctly with normal inputs."""
        # Test with normal, reasonable context that doesn't match any domain
        normal_context = "Educational research about student learning patterns"
        observations = ["Students showing improved engagement", "Test scores increasing"]

        result = generate_hypotheses(
            observations=observations,
            reasoning_chain=None,
            context=normal_context,
            max_hypotheses=5
        )

        # Should generate contextual hypothesis when no domain matches
        contextual_hypotheses = [h for h in result if h.get("type") == "contextual"]
        assert len(contextual_hypotheses) > 0, "Should generate contextual hypothesis for non-domain input"

        hypothesis = contextual_hypotheses[0]
        hypothesis_text = hypothesis["hypothesis"]

        # Should contain relevant keywords from the context
        assert "research" in hypothesis_text.lower() or "student" in hypothesis_text.lower()
        assert "context" in hypothesis_text.lower()

        # Should be reasonable length
        assert 50 <= len(hypothesis_text) <= 500

        # Should have proper structure
        assert hypothesis["type"] == "contextual"
        assert "context_keywords" in hypothesis
        assert len(hypothesis["context_keywords"]) <= 3

    def test_edge_case_empty_keywords_after_truncation(self):
        """Test behavior when all keywords become empty after truncation."""
        # Create context with only whitespace and special characters
        problematic_context = "     \t\n   \r\n   \t      "  # Only whitespace
        observations = ["System issue"]

        result = generate_hypotheses(
            observations=observations,
            reasoning_chain=None,
            context=problematic_context,
            max_hypotheses=1
        )

        # Should still work and not crash
        assert len(result) > 0

        # Should handle empty keywords gracefully
        for hypothesis in result:
            if hypothesis.get("type") == "contextual":
                hypothesis_text = hypothesis["hypothesis"]
                # Should have fallback text when no keywords
                assert len(hypothesis_text) > 0
                assert "context" in hypothesis_text.lower()

    def test_mixed_contextual_and_template_hypotheses(self):
        """Test that the fix doesn't interfere with template-based hypotheses."""
        # Create input that should trigger both contextual and template hypotheses
        observations = ["Recent code deploy caused server issues"]
        context = "Production environment with database" * 100  # Long but normal context

        result = generate_hypotheses(
            observations=observations,
            reasoning_chain=None,
            context=context,
            max_hypotheses=5
        )

        # Should generate multiple types of hypotheses
        assert len(result) >= 2, "Should generate multiple hypothesis types"

        # Check that all hypotheses are reasonable length
        for hypothesis in result:
            assert len(hypothesis["hypothesis"]) <= 1000, f"Hypothesis too long: {len(hypothesis['hypothesis'])} chars"

            # Should not contain large repetitive blocks
            assert "Production environment" * 10 not in hypothesis["hypothesis"]