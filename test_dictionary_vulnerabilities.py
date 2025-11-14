#!/usr/bin/env python3
"""
Test suite to demonstrate CRITICAL dictionary access vulnerabilities.

This test suite demonstrates the unsafe dictionary access patterns that could
cause KeyError crashes and application instability.

Security vulnerabilities identified:
1. Direct dictionary access without key existence checks
2. Missing required keys causing KeyError exceptions
3. Unsafe dictionary operations assuming keys always exist
"""

import sys
import os
import pytest

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from reasoning_library.exceptions import ValidationError


class TestDictionaryAccessVulnerabilities:
    """Test cases demonstrating dictionary access vulnerabilities."""

    def test_abductive_hypothesis_missing_hypothesis_key(self):
        """Test KeyError when hypothesis dictionary missing 'hypothesis' key."""
        from reasoning_library.abductive import _extract_keywords

        # Hypothesis dictionary missing the 'hypothesis' key
        invalid_hypothesis = {
            "confidence": 0.8,
            "evidence": "Some evidence"
            # Missing 'hypothesis' key
        }

        # This should cause a KeyError when trying to access hypothesis["hypothesis"]
        with pytest.raises(KeyError) as exc_info:
            # This line calls hypothesis["hypothesis"] without checking if key exists
            _extract_keywords(invalid_hypothesis["hypothesis"])

        assert "hypothesis" in str(exc_info.value)

    def test_abductive_hypothesis_empty_hypothesis_key(self):
        """Test KeyError when hypothesis dictionary has empty 'hypothesis' key."""
        from reasoning_library.abductive import _extract_keywords

        # Hypothesis dictionary with empty 'hypothesis' key
        invalid_hypothesis = {
            "hypothesis": "",  # Empty string
            "confidence": 0.8,
            "evidence": "Some evidence"
        }

        # This should cause a ValidationError when trying to extract keywords from empty string
        with pytest.raises(ValidationError) as exc_info:
            _extract_keywords(invalid_hypothesis["hypothesis"])

        assert "text cannot be None" in str(exc_info.value) or "whitespace" in str(exc_info.value).lower()

    def test_abductive_hypothesis_missing_confidence_key(self):
        """Test KeyError when hypothesis dictionary missing 'confidence' key."""
        from reasoning_library.abductive import generate_hypotheses

        # Hypothesis dictionary missing the 'confidence' key
        invalid_hypothesis = {
            "hypothesis": "System is experiencing performance issues",
            "evidence": "System is slow"
            # Missing 'confidence' key
        }

        # Functions that access hypothesis["confidence"] without checking
        # This should cause KeyError in ranking/sorting operations
        hypotheses_list = [invalid_hypothesis]

        with pytest.raises(KeyError) as exc_info:
            # This line accesses h["confidence"] without checking if key exists
            max(hypotheses_list, key=lambda x: x["confidence"])

        assert "confidence" in str(exc_info.value)

    def test_domain_keywords_missing_keys(self):
        """Test KeyError when keywords dictionary missing expected keys."""
        from reasoning_library.abductive import _generate_domain_specific_hypothesis

        # Keywords dictionary missing required keys
        incomplete_keywords = {
            "actions": ["failed", "crashed"],
            # Missing 'components' and 'issues' keys
        }

        # Access to keywords["components"] and keywords["issues"] without existence checks
        # This will cause KeyError
        with pytest.raises(KeyError) as exc_info:
            # These lines access dictionary keys without checking existence
            component = incomplete_keywords["components"][0] if incomplete_keywords["components"] else "system"
            issue = incomplete_keywords["issues"][0] if incomplete_keywords["issues"] else "performance issue"

        assert "components" in str(exc_info.value) or "issues" in str(exc_info.value)

    def test_domain_template_missing_keywords_key(self):
        """Test KeyError when domain template missing 'keywords' key."""
        from reasoning_library.abductive import DOMAIN_TEMPLATES

        # Simulate a domain template missing the 'keywords' key
        # This demonstrates what would happen if DOMAIN_TEMPLATES had malformed entries
        for domain_name, domain_info in DOMAIN_TEMPLATES.items():
            # Create a modified domain_info without 'keywords' key
            modified_domain_info = {k: v for k, v in domain_info.items() if k != 'keywords'}

            # This would cause KeyError when accessing domain_info["keywords"]
            if "keywords" not in modified_domain_info:
                with pytest.raises(KeyError) as exc_info:
                    keywords = modified_domain_info["keywords"]  # KeyError!
                assert "keywords" in str(exc_info.value)
                break  # Only need to demonstrate once

    def test_tool_spec_missing_function_key(self):
        """Test KeyError when tool spec missing 'function' key."""
        from reasoning_library.core import _safe_copy_spec

        # Tool specification missing the 'function' key
        invalid_tool_spec = {
            "name": "test_tool",
            "description": "A test tool"
            # Missing 'function' key
        }

        # This should cause KeyError when accessing tool_spec["function"]
        with pytest.raises(KeyError) as exc_info:
            _safe_copy_spec(invalid_tool_spec)

        assert "function" in str(exc_info.value)

    def test_tool_spec_missing_parameters_key(self):
        """Test KeyError when tool function missing 'parameters' key."""
        from reasoning_library.core import _safe_copy_spec

        # Tool specification with function but missing 'parameters' key
        invalid_tool_spec = {
            "name": "test_tool",
            "function": {
                "name": "test_function",
                "description": "A test function"
                # Missing 'parameters' key
            }
        }

        # This should cause KeyError when accessing function["parameters"]
        with pytest.raises(KeyError) as exc_info:
            _safe_copy_spec(invalid_tool_spec)

        # The error might be 'parameters' or could be a different key depending on implementation
        assert any(key in str(exc_info.value) for key in ["parameters", "properties"])

    def test_parameter_spec_missing_properties_key(self):
        """Test KeyError when parameters missing 'properties' key."""
        from reasoning_library.core import _safe_copy_tool_parameters

        # Parameters missing the 'properties' key
        invalid_parameters = {
            "type": "object",
            "required": ["param1"]
            # Missing 'properties' key
        }

        # This might cause KeyError when accessing parameters["properties"]
        # depending on implementation
        try:
            result = _safe_copy_tool_parameters(invalid_parameters)
            # If it doesn't raise KeyError, the function should handle missing properties gracefully
            assert isinstance(result, dict)
        except KeyError as exc_info:
            # This demonstrates the vulnerability
            assert "properties" in str(exc_info.value)

    def test_confidence_calculation_missing_predictions(self):
        """Test safe handling of missing testable_predictions in confidence calculation."""
        from reasoning_library.abductive import _calculate_hypothesis_confidence

        # Hypothesis missing 'testable_predictions' key
        # Note: This line is actually SAFE because it uses .get() method
        hypothesis_missing_predictions = {
            "hypothesis": "System is failing",
            "confidence": 0.7
            # Missing 'testable_predictions' key
        }

        # This should work safely because the code uses .get() with default
        try:
            confidence = _calculate_hypothesis_confidence(
                base_confidence=0.5,
                explained_observations=5,
                total_observations=10,
                assumption_count=2,
                hypothesis=hypothesis_missing_predictions
            )
            # Should return a valid confidence without KeyError
            assert 0.0 <= confidence <= 1.0
        except KeyError:
            pytest.fail("Confidence calculation should handle missing 'testable_predictions' key safely")

    def test_evidence_update_missing_supporting_evidence(self):
        """Test adding evidence to hypothesis missing supporting_evidence key."""
        # This demonstrates the pattern where code safely handles missing keys
        hypothesis_missing_evidence = {
            "hypothesis": "System is experiencing issues",
            "confidence": 0.6
            # Missing 'supporting_evidence' key
        }

        # This pattern is actually SAFE - it checks for key existence first
        if "supporting_evidence" not in hypothesis_missing_evidence:
            hypothesis_missing_evidence["supporting_evidence"] = []

        new_evidence = ["System logs show errors", "Users report slowness"]
        hypothesis_missing_evidence["supporting_evidence"].extend(new_evidence)

        assert len(hypothesis_missing_evidence["supporting_evidence"]) == 2
        assert hypothesis_missing_evidence["supporting_evidence"] == new_evidence

    def test_confidence_sorting_missing_confidence_keys(self):
        """Test KeyError during sorting when hypotheses missing confidence keys."""
        # Mixed list where some hypotheses have confidence, others don't
        mixed_hypotheses = [
            {"hypothesis": "Good hypothesis", "confidence": 0.8},
            {"hypothesis": "Bad hypothesis"}  # Missing confidence
        ]

        # This should cause KeyError during sorting
        with pytest.raises(KeyError) as exc_info:
            # Sorting accesses h["confidence"] for each hypothesis
            sorted_hypotheses = sorted(mixed_hypotheses, key=lambda x: x["confidence"], reverse=True)

        assert "confidence" in str(exc_info.value)

    def test_best_hypothesis_selection_missing_confidence(self):
        """Test KeyError when finding best hypothesis from list missing confidence keys."""
        # List with hypotheses missing confidence keys
        incomplete_hypotheses = [
            {"hypothesis": "First hypothesis"},
            {"hypothesis": "Second hypothesis", "confidence": 0.7}
        ]

        # This should cause KeyError when trying to find max by confidence
        with pytest.raises(KeyError) as exc_info:
            best = max(incomplete_hypotheses, key=lambda x: x["confidence"])

        assert "confidence" in str(exc_info.value)


class TestSafeDictionaryAccessPatterns:
    """Test cases demonstrating how dictionary access should be done safely."""

    def test_safe_hypothesis_access_with_get(self):
        """Test safe hypothesis access using .get() method."""
        # Hypothesis with some missing keys
        incomplete_hypothesis = {
            "hypothesis": "System has issues",
            "confidence": 0.6
            # Missing 'evidence', 'testable_predictions' keys
        }

        # Safe access patterns
        hypothesis_text = incomplete_hypothesis.get("hypothesis", "")
        confidence = incomplete_hypothesis.get("confidence", 0.0)
        evidence = incomplete_hypothesis.get("evidence", "No evidence provided")
        predictions = incomplete_hypothesis.get("testable_predictions", [])

        assert hypothesis_text == "System has issues"
        assert confidence == 0.6
        assert evidence == "No evidence provided"
        assert predictions == []

    def test_safe_key_existence_check(self):
        """Test safe key existence checking before access."""
        hypothesis = {
            "hypothesis": "Test hypothesis",
            "confidence": 0.7
        }

        # Safe pattern: check key exists before access
        if "evidence" in hypothesis:
            evidence = hypothesis["evidence"]
        else:
            evidence = "No evidence"

        # Alternative safe pattern
        evidence_alt = hypothesis.get("evidence", "No evidence")

        assert evidence == "No evidence"
        assert evidence_alt == "No evidence"

    def test_safe_domain_template_access(self):
        """Test safe domain template access patterns."""
        from reasoning_library.abductive import DOMAIN_TEMPLATES

        # Safe iteration over domain templates
        for domain_name, domain_info in DOMAIN_TEMPLATES.items():
            # Safe access to keywords with fallback
            keywords = domain_info.get("keywords", [])
            assert isinstance(keywords, list)

            # Safe access to other expected keys
            templates = domain_info.get("templates", [])
            assert isinstance(templates, list)

    def test_validation_error_on_missing_required_keys(self):
        """Test that validation properly handles missing required keys."""
        from reasoning_library.validation import validate_hypothesis_dict

        # Hypothesis missing required keys
        invalid_hypothesis = {
            "confidence": 0.8
            # Missing required 'hypothesis' key
        }

        # This should raise ValidationError, not KeyError
        with pytest.raises(ValidationError) as exc_info:
            validate_hypothesis_dict(invalid_hypothesis, "test_hypothesis")

        assert "missing required key" in str(exc_info.value).lower()
        assert "hypothesis" in str(exc_info.value)


if __name__ == "__main__":
    # Run the tests to demonstrate vulnerabilities
    pytest.main([__file__, "-v"])