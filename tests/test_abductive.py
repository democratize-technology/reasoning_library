"""
Tests for abductive reasoning module.
"""

from src.reasoning_library.abductive import (
    DOMAIN_TEMPLATES,
    _extract_keywords_with_context,
    generate_hypotheses,
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
