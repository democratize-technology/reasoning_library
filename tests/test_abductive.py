"""
Tests for abductive reasoning module.
"""

from reasoning_library.abductive import (
    DOMAIN_TEMPLATES,
    _extract_keywords_with_context,
    _validate_and_sanitize_input_size,
    _validate_confidence_value,
    _calculate_hypothesis_confidence,
    _extract_keywords,
    _find_common_themes,
    _generate_single_cause_hypothesis,
    _generate_multiple_causes_hypothesis,
    _generate_causal_chain_hypothesis,
    _sanitize_template_input,
    _generate_domain_template_hypotheses,
    _generate_contextual_hypothesis,
    _generate_systemic_hypothesis,
    generate_hypotheses,
    rank_hypotheses,
    evaluate_best_explanation,
)


class TestExtractKeywordsWithContext:
    """Test the _extract_keywords_with_context function."""

    def test_basic_functionality(self):
        """Test basic keyword extraction with context."""
        observations = ["server responding slowly", "database CPU at 95%"]
        context = "production web application"

        result = _extract_keywords_with_context(observations, context)

        # Check structure
        assert "actions" in result
        assert "components" in result
        assert "issues" in result

        # Check that we get expected components
        assert "server" in result["components"]
        assert "database" in result["components"]
        assert "application" in result["components"]

    def test_deploy_action_extraction(self):
        """Test that deploy actions are extracted with modifiers."""
        observations = ["recent code deploy", "database CPU high"]
        context = None

        result = _extract_keywords_with_context(observations, context)

        # Should extract "recent code deploy" or similar
        actions = result["actions"]
        assert len(actions) > 0
        assert any("deploy" in action for action in actions)

    def test_cpu_issue_extraction(self):
        """Test that CPU issues are extracted correctly."""
        observations = ["CPU at 95%", "database running slow"]
        context = None

        result = _extract_keywords_with_context(observations, context)

        # Should extract "high CPU usage"
        issues = result["issues"]
        assert any("CPU" in issue and "usage" in issue for issue in issues)

    def test_slow_response_extraction(self):
        """Test that slow response issues are extracted correctly."""
        observations = ["server responding slowly"]
        context = None

        result = _extract_keywords_with_context(observations, context)

        # Should extract "slow response times"
        issues = result["issues"]
        assert any("slow" in issue.lower() for issue in issues)

    def test_defaults_provided(self):
        """Test that sensible defaults are provided when keywords not found."""
        observations = ["some random text"]
        context = "unrelated context"

        result = _extract_keywords_with_context(observations, context)

        # Should provide defaults
        assert "recent change" in result["actions"]
        assert "system" in result["components"]
        assert "performance issue" in result["issues"]

    def test_empty_inputs(self):
        """Test behavior with empty inputs."""
        result = _extract_keywords_with_context([], None)

        # Should still provide defaults
        assert "recent change" in result["actions"]
        assert "system" in result["components"]
        assert "performance issue" in result["issues"]


class TestDomainTemplates:
    """Test the domain template system."""

    def test_domain_templates_structure(self):
        """Test that domain templates have correct structure."""
        assert "debugging" in DOMAIN_TEMPLATES
        assert "system" in DOMAIN_TEMPLATES

        for domain_name, domain_info in DOMAIN_TEMPLATES.items():
            assert "keywords" in domain_info
            assert "templates" in domain_info
            assert len(domain_info["templates"]) > 0

    def test_debugging_domain_keywords(self):
        """Test that debugging domain has expected keywords."""
        debugging = DOMAIN_TEMPLATES["debugging"]
        expected_keywords = ["deploy", "code", "server", "database", "cpu", "memory", "slow", "error"]

        for keyword in expected_keywords:
            assert keyword in debugging["keywords"]

    def test_debugging_domain_templates(self):
        """Test that debugging domain has valid templates."""
        debugging = DOMAIN_TEMPLATES["debugging"]
        templates = debugging["templates"]

        # All templates should have the expected placeholders
        for template in templates:
            assert "{action}" in template
            assert "{component}" in template
            assert "{issue}" in template

    def test_template_formatting(self):
        """Test that templates can be formatted correctly."""
        template = DOMAIN_TEMPLATES["debugging"]["templates"][0]

        # This should not raise an exception
        formatted = template.format(
            action="recent code deploy",
            component="database",
            issue="high CPU usage"
        )

        assert len(formatted) > 0
        assert formatted[0].islower()  # Template should start with lowercase for capitalization later


class TestGenerateHypothesesWithTemplates:
    """Test template-based hypothesis generation."""

    def test_debugging_domain_detection(self):
        """Test that debugging domain is detected correctly."""
        observations = ["server responding slowly", "database CPU at 95%", "recent code deploy"]
        context = "production web application"

        result = generate_hypotheses(
            observations=observations,
            reasoning_chain=None,
            context=context,
            max_hypotheses=3
        )

        # Should generate template-based hypotheses
        assert len(result) >= 3

        # Check that we get domain-specific hypotheses
        template_hyps = [h for h in result if h.get("type") == "domain_template"]
        assert len(template_hyps) > 0

    def test_hypothesis_grammar(self):
        """Test that generated hypotheses have correct grammar."""
        observations = ["server responding slowly", "database CPU at 95%", "recent code deploy"]
        context = "production web application"

        result = generate_hypotheses(
            observations=observations,
            reasoning_chain=None,
            context=context,
            max_hypotheses=3
        )

        # Check first 3 hypotheses (should be template-based)
        for i, h in enumerate(result[:3]):
            hypothesis = h["hypothesis"]

            # Grammar checks
            assert hypothesis[0].isupper(), f"Should start with capital: {hypothesis}"
            assert len(hypothesis.split()) >= 5, f"Too short: {hypothesis}"
            assert not hypothesis.endswith('due to'), f"Incomplete: {hypothesis}"

    def test_system_domain_detection(self):
        """Test that system domain is detected correctly."""
        observations = ["network timeout", "connection refused", "high latency"]
        context = "distributed system"

        result = generate_hypotheses(
            observations=observations,
            reasoning_chain=None,
            context=context,
            max_hypotheses=3
        )

        # Should generate system-domain hypotheses
        system_hyps = [h for h in result if h.get("type") == "domain_template"]
        assert len(system_hyps) > 0

    def test_fallback_to_context_hypothesis(self):
        """Test fallback to context hypothesis when no domain matches."""
        observations = ["random observation", "another random thing"]
        context = "unrelated context"

        result = generate_hypotheses(
            observations=observations,
            reasoning_chain=None,
            context=context,
            max_hypotheses=3
        )

        # Should fall back to context-based hypothesis
        contextual_hyps = [h for h in result if h.get("type") == "contextual"]
        assert len(contextual_hyps) > 0

    def test_backward_compatibility(self):
        """Test that function works without context (backward compatibility)."""
        observations = ["server responding slowly", "database CPU at 95%"]

        result = generate_hypotheses(
            observations=observations,
            reasoning_chain=None,
            context=None,  # No context
            max_hypotheses=3
        )

        # Should still work and generate hypotheses
        assert len(result) > 0

        # Should not generate template-based hypotheses without context
        template_hyps = [h for h in result if h.get("type") == "domain_template"]
        assert len(template_hyps) == 0


class TestInputValidation:
    """Test input validation and security."""

    def test_template_injection_prevention(self):
        """Test that template injection is prevented."""
        observations = ["server {injection}", "database CPU at 95%"]
        context = "test context"

        result = generate_hypotheses(
            observations=observations,
            reasoning_chain=None,
            context=context,
            max_hypotheses=3
        )

        # Should not allow injection through braces
        for h in result:
            hypothesis = h["hypothesis"]
            assert "{injection}" not in hypothesis

    def test_long_input_handling(self):
        """Test handling of very long inputs."""
        long_observation = "slow " * 1000  # Very long observation
        observations = [long_observation, "database CPU high"]

        # Should not crash and should handle gracefully
        result = generate_hypotheses(
            observations=observations,
            reasoning_chain=None,
            context="test",
            max_hypotheses=3
        )

        assert len(result) > 0

    def test_unicode_handling(self):
        """Test handling of unicode characters."""
        observations = ["server responding slowly 🐌", "database CPU at 95%"]
        context = "production application 🏭"

        result = generate_hypotheses(
            observations=observations,
            reasoning_chain=None,
            context=context,
            max_hypotheses=3
        )

        assert len(result) > 0
        # Should handle unicode gracefully (either include or filter out)


class TestDoSProtection:
    """Test Denial of Service (DoS) protection for large inputs."""

    def test_extremely_large_string_dos_attack(self):
        """Test DoS protection against extremely large string inputs (>1MB)."""
        # Create a maliciously large string that could cause memory issues
        large_action = "A" * 1000000  # 1MB string
        large_component = "B" * 1000000  # 1MB string
        large_issue = "C" * 1000000  # 1MB string

        # These should be truncated early in processing, not after
        observations = [f"The {large_component} system has {large_issue} after {large_action}"]
        context = f"Production environment with {large_component} and {large_issue}"

        # This should handle large inputs gracefully without memory issues
        # The current implementation applies length limits AFTER processing
        # which means it still processes the full large strings
        result = generate_hypotheses(
            observations=observations,
            reasoning_chain=None,
            context=context,
            max_hypotheses=1  # Limit to minimize processing time
        )

        # Should return results without using excessive memory
        assert len(result) > 0

        # Check that the generated hypotheses are properly truncated
        for h in result:
            hypothesis = h["hypothesis"]
            # Hypotheses should be reasonably sized, not contain the massive strings
            assert len(hypothesis) < 10000  # Should be much smaller than input

            # Should not contain the maliciously large strings
            assert large_action not in hypothesis
            assert large_component not in hypothesis
            assert large_issue not in hypothesis

    def test_boundary_conditions_size_limits(self):
        """Test boundary conditions around size limits."""
        # Test exactly at the limit
        exactly_50 = "A" * 50
        exactly_100 = "B" * 100

        observations = [f"System {exactly_50} has issue {exactly_100}"]
        result = generate_hypotheses(
            observations=observations,
            reasoning_chain=None,
            context="test",
            max_hypotheses=1
        )

        assert len(result) > 0

        # Test just over the limit
        over_50 = "C" * 51
        over_100 = "D" * 101

        observations = [f"System {over_50} has issue {over_100}"]
        result = generate_hypotheses(
            observations=observations,
            reasoning_chain=None,
            context="test",
            max_hypotheses=1
        )

        assert len(result) > 0
        # Should truncate the over-limit strings
        for h in result:
            hypothesis = h["hypothesis"]
            # Should not contain the full over-limit strings
            assert over_50 not in hypothesis
            assert over_100 not in hypothesis

    def test_early_validation_performance(self):
        """Test that large inputs are validated early to prevent performance issues."""
        import time

        # Create a large input that would be slow to process if not truncated early
        large_input = "X" * 100000  # 100KB string
        observations = [f"System with {large_input} is experiencing issues"]

        start_time = time.time()
        result = generate_hypotheses(
            observations=observations,
            reasoning_chain=None,
            context="test",
            max_hypotheses=1
        )
        end_time = time.time()

        # Should complete quickly (under 1 second) even with large input
        processing_time = end_time - start_time
        assert processing_time < 1.0, f"Processing took {processing_time}s, should be < 1s"
        assert len(result) > 0


class TestAbductiveInternalFunctions:
    """Test internal functions of abductive reasoning module."""

    def test_validate_and_sanitize_input_size(self):
        """Test input validation and sanitization."""
        observations = ["test obs", "another obs"]
        context = "test context"

        sanitized_obs, sanitized_ctx = _validate_and_sanitize_input_size(observations, context)

        # Should return the same values for valid inputs
        assert sanitized_obs == observations
        assert sanitized_ctx == context

    def test_validate_confidence_value(self):
        """Test confidence value validation."""
        # Test valid values
        assert _validate_confidence_value(0.5) == 0.5
        assert _validate_confidence_value(0.0) == 0.0
        assert _validate_confidence_value(1.0) == 1.0
        assert _validate_confidence_value(0.75, hypothesis_index=1) == 0.75

        # Test with hypothesis_index
        assert _validate_confidence_value(0.8, hypothesis_index=2) == 0.8

    def test_calculate_hypothesis_confidence(self):
        """Test hypothesis confidence calculation."""
        hypothesis = {
            "hypothesis": "Test hypothesis",
            "explains": [0, 1],
            "assumptions": ["test assumption"],
            "testable_predictions": ["test prediction"]
        }
        observations_count = 3
        keywords_count = 2
        domain_count = 1

        confidence = _calculate_hypothesis_confidence(
            hypothesis, observations_count, keywords_count, domain_count
        )

        assert 0.0 <= confidence <= 1.0

    def test_extract_keywords(self):
        """Test keyword extraction from text."""
        text = "server CPU high and memory low"
        keywords = _extract_keywords(text)

        assert isinstance(keywords, list)
        assert len(keywords) > 0
        # Should contain relevant keywords
        assert any("server" in kw or "cpu" in kw or "memory" in kw for kw in keywords)

    def test_find_common_themes(self):
        """Test finding common themes in observations."""
        observations = [
            "server CPU is high",
            "database server memory usage",
            "application server response time"
        ]
        themes = _find_common_themes(observations)

        assert isinstance(themes, list)
        # Should find common themes like "server"
        assert any("server" in theme for theme in themes)

    def test_generate_single_cause_hypothesis(self):
        """Test single cause hypothesis generation."""
        common_themes = ["server", "performance"]
        observations_count = 2

        hypothesis = _generate_single_cause_hypothesis(common_themes, observations_count)

        assert hypothesis is not None
        assert "hypothesis" in hypothesis
        assert "confidence" in hypothesis
        assert "explains" in hypothesis
        assert isinstance(hypothesis["confidence"], float)

    def test_generate_multiple_causes_hypothesis(self):
        """Test multiple causes hypothesis generation."""
        common_themes = ["server", "database", "network"]
        observations_count = 3

        hypothesis = _generate_multiple_causes_hypothesis(common_themes, observations_count)

        assert hypothesis is not None
        assert "hypothesis" in hypothesis
        assert "confidence" in hypothesis
        assert "explains" in hypothesis
        assert isinstance(hypothesis["confidence"], float)

    def test_generate_causal_chain_hypothesis(self):
        """Test causal chain hypothesis generation."""
        observations_count = 2

        hypothesis = _generate_causal_chain_hypothesis(observations_count)

        assert hypothesis is not None
        assert "hypothesis" in hypothesis
        assert "confidence" in hypothesis
        assert "explains" in hypothesis
        assert isinstance(hypothesis["confidence"], float)

    def test_sanitize_template_input(self):
        """Test template input sanitization."""
        # Test normal input
        assert _sanitize_template_input("normal text") == "normal text"

        # Test malicious input
        malicious = "{evil} <script>alert('xss')</script>"
        safe = _sanitize_template_input(malicious)
        assert "{" not in safe
        assert "}" not in safe
        assert "<" not in safe
        assert ">" not in safe

    def test_generate_domain_template_hypotheses(self):
        """Test domain template hypothesis generation."""
        observations = ["server slow", "database error"]
        context = "web application"
        max_hypotheses = 3
        observations_count = len(observations)

        hypotheses = _generate_domain_template_hypotheses(observations, context, max_hypotheses, observations_count)

        assert isinstance(hypotheses, list)
        if hypotheses:  # May be empty if no domain matches
            for hyp in hypotheses:
                assert "hypothesis" in hyp
                assert "confidence" in hyp

    def test_generate_contextual_hypothesis(self):
        """Test contextual hypothesis generation."""
        observations = ["system slow"]
        context = "production environment"
        observations_count = 1

        hypothesis = _generate_contextual_hypothesis(observations, context, observations_count)

        # May return None if no keywords found
        if hypothesis is not None:
            assert "hypothesis" in hypothesis
            assert "confidence" in hypothesis

    def test_generate_systemic_hypothesis(self):
        """Test systemic hypothesis generation."""
        observations_count = 3

        hypothesis = _generate_systemic_hypothesis(observations_count)

        assert hypothesis is not None
        assert "hypothesis" in hypothesis
        assert "confidence" in hypothesis
        assert "systemic" in hypothesis["hypothesis"].lower()

    def test_rank_hypotheses(self):
        """Test hypothesis ranking."""
        hypotheses = [
            {"hypothesis": "high confidence", "confidence": 0.9},
            {"hypothesis": "low confidence", "confidence": 0.3},
            {"hypothesis": "medium confidence", "confidence": 0.6}
        ]
        new_evidence = ["supporting evidence"]

        ranked = rank_hypotheses(hypotheses, new_evidence, None)

        assert len(ranked) == 3
        # Should be sorted by confidence descending
        assert ranked[0]["confidence"] >= ranked[1]["confidence"] >= ranked[2]["confidence"]

    def test_evaluate_best_explanation(self):
        """Test best explanation evaluation."""
        hypotheses = [
            {"hypothesis": "best", "confidence": 0.9, "explains": [0, 1]},
            {"hypothesis": "worse", "confidence": 0.5, "explains": [0]}
        ]

        best = evaluate_best_explanation(hypotheses, None)

        # Should return the highest confidence hypothesis with evaluation metadata
        assert best["hypothesis"] == "best"
        assert best["confidence"] == 0.9
        assert "evaluation" in best
        assert best["evaluation"]["selected_as_best"] is True

    def test_evaluate_best_explanation_empty_list(self):
        """Test best explanation evaluation with empty list."""
        from reasoning_library.exceptions import ValidationError
        import pytest

        with pytest.raises(ValidationError):
            evaluate_best_explanation([], None)
