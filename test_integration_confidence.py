"""
Comprehensive Integration Test Suite for Confidence Thresholds Across All Reasoning Types.

This module tests end-to-end confidence scoring integration across deductive, inductive,
and chain-of-thought reasoning, ensuring that:
1. Confidence thresholds work correctly across all reasoning types
2. Tool specifications include accurate confidence documentation
3. End-to-end reasoning workflows maintain confidence tracking
4. Cross-reasoning-type confidence comparisons are mathematically sound
5. Real-world reasoning scenarios produce expected confidence patterns
"""

import pytest
import numpy as np
from typing import List, Dict, Any, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # Import all reasoning modules
    from reasoning_library.deductive import apply_modus_ponens, logical_and_with_confidence
    from reasoning_library.inductive import predict_next_in_sequence, find_pattern_description
    from reasoning_library.chain_of_thought import chain_of_thought_step, get_chain_summary, clear_chain
    from reasoning_library.core import ReasoningChain, get_openai_tools, get_bedrock_tools, get_enhanced_tool_registry
except ImportError:
    # Fallback for direct execution
    from deductive import apply_modus_ponens, logical_and_with_confidence
    from inductive import predict_next_in_sequence, find_pattern_description
    from chain_of_thought import chain_of_thought_step, get_chain_summary, clear_chain
    from core import ReasoningChain, get_openai_tools, get_bedrock_tools, get_enhanced_tool_registry


class TestCrossReasoningConfidenceThresholds:
    """Test confidence thresholds across different reasoning types."""

    def test_deductive_vs_inductive_confidence_ranges(self):
        """Test that deductive and inductive reasoning have appropriate confidence ranges."""
        # Deductive reasoning should have binary confidence (0.0 or 1.0)
        deductive_chain = ReasoningChain()

        # Valid deductive reasoning
        deductive_result = apply_modus_ponens(
            p_is_true=True,
            p_implies_q_is_true=True,
            reasoning_chain=deductive_chain
        )
        deductive_confidence = deductive_chain.steps[0].confidence

        assert deductive_result is True
        assert deductive_confidence == 1.0, "Valid deductive reasoning should have confidence 1.0"

        # Invalid deductive reasoning
        deductive_chain_invalid = ReasoningChain()
        invalid_deductive_result = apply_modus_ponens(
            p_is_true=False,
            p_implies_q_is_true=True,
            reasoning_chain=deductive_chain_invalid
        )
        invalid_deductive_confidence = deductive_chain_invalid.steps[0].confidence

        assert invalid_deductive_result is None
        assert invalid_deductive_confidence == 0.0, "Invalid deductive reasoning should have confidence 0.0"

        # Inductive reasoning should have variable confidence (0.0-1.0)
        inductive_sequences = [
            ([1, 2, 3, 4, 5], "perfect_arithmetic"),           # Should have high confidence
            ([1.1, 2.0, 2.9, 4.1], "noisy_arithmetic"),       # Should have moderate confidence
            ([1, 3, 7, 15, 31], "no_pattern"),                # Should have low/zero confidence
        ]

        for sequence, description in inductive_sequences:
            inductive_chain = ReasoningChain()
            inductive_result = predict_next_in_sequence(sequence, reasoning_chain=inductive_chain)

            if len(inductive_chain.steps) > 0:
                inductive_confidence = inductive_chain.steps[0].confidence

                # Inductive confidence should be in valid range
                assert 0.0 <= inductive_confidence <= 1.0, f"Inductive confidence for {description} should be in [0.0, 1.0]"

                # Perfect patterns should have higher confidence than noisy ones
                if description == "perfect_arithmetic":
                    assert inductive_confidence > 0.8, "Perfect arithmetic pattern should have high confidence"
                elif description == "no_pattern" and inductive_result is None:
                    assert inductive_confidence == 0.0, "No pattern should have zero confidence"

    def test_confidence_threshold_consistency(self):
        """Test that confidence thresholds are consistent across reasoning types."""
        # High confidence threshold (>0.9): Should indicate very reliable reasoning
        high_confidence_cases = [
            # Deductive: Valid logical operations
            ("deductive", lambda: self._test_deductive_high_confidence()),
            # Inductive: Perfect patterns with sufficient data
            ("inductive", lambda: self._test_inductive_high_confidence()),
        ]

        for reasoning_type, test_func in high_confidence_cases:
            confidence = test_func()
            assert confidence > 0.9, f"{reasoning_type} reasoning with perfect conditions should have confidence > 0.9"

        # Low confidence threshold (<0.3): Should indicate unreliable reasoning
        low_confidence_cases = [
            # Deductive: Invalid logical operations
            ("deductive", lambda: self._test_deductive_low_confidence()),
            # Inductive: No detectable patterns
            ("inductive", lambda: self._test_inductive_low_confidence()),
        ]

        for reasoning_type, test_func in low_confidence_cases:
            confidence = test_func()
            assert confidence < 0.3, f"{reasoning_type} reasoning with poor conditions should have confidence < 0.3"

    def _test_deductive_high_confidence(self) -> float:
        """Helper: Test deductive reasoning with high confidence scenario."""
        chain = ReasoningChain()
        apply_modus_ponens(True, True, reasoning_chain=chain)
        return chain.steps[0].confidence

    def _test_deductive_low_confidence(self) -> float:
        """Helper: Test deductive reasoning with low confidence scenario."""
        chain = ReasoningChain()
        apply_modus_ponens(False, True, reasoning_chain=chain)
        return chain.steps[0].confidence

    def _test_inductive_high_confidence(self) -> float:
        """Helper: Test inductive reasoning with high confidence scenario."""
        perfect_sequence = [2, 4, 6, 8, 10, 12]  # Perfect arithmetic progression
        chain = ReasoningChain()
        predict_next_in_sequence(perfect_sequence, reasoning_chain=chain)
        return chain.steps[0].confidence if len(chain.steps) > 0 else 0.0

    def _test_inductive_low_confidence(self) -> float:
        """Helper: Test inductive reasoning with low confidence scenario."""
        random_sequence = [1, 7, 3, 15, 2, 11]  # No clear pattern
        chain = ReasoningChain()
        predict_next_in_sequence(random_sequence, reasoning_chain=chain)
        return chain.steps[0].confidence if len(chain.steps) > 0 else 0.0


class TestEndToEndReasoningWorkflows:
    """Test end-to-end reasoning workflows with confidence tracking."""

    def setup_method(self):
        """Clean up before each test."""
        clear_chain("integration_test")

    def teardown_method(self):
        """Clean up after each test."""
        clear_chain("integration_test")

    def test_mixed_reasoning_chain_confidence_propagation(self):
        """Test confidence propagation in chains mixing different reasoning types."""
        conversation_id = "integration_test"

        # Step 1: Deductive reasoning (should have confidence 1.0)
        deductive_chain = ReasoningChain()
        deductive_result = apply_modus_ponens(
            p_is_true=True,
            p_implies_q_is_true=True,
            reasoning_chain=deductive_chain
        )
        deductive_confidence = deductive_chain.steps[0].confidence

        # Add deductive step to conversation chain
        chain_of_thought_step(
            conversation_id=conversation_id,
            stage="Deductive_Reasoning",
            description="Applied Modus Ponens rule",
            result=deductive_result,
            confidence=deductive_confidence
        )

        # Step 2: Inductive reasoning (should have variable confidence)
        perfect_sequence = [1, 3, 5, 7, 9]
        inductive_chain = ReasoningChain()
        inductive_result = predict_next_in_sequence(perfect_sequence, reasoning_chain=inductive_chain)
        inductive_confidence = inductive_chain.steps[0].confidence

        # Add inductive step to conversation chain
        chain_of_thought_step(
            conversation_id=conversation_id,
            stage="Inductive_Reasoning",
            description="Pattern detection in sequence",
            result=inductive_result,
            confidence=inductive_confidence
        )

        # Step 3: Manual reasoning step with moderate confidence
        manual_confidence = 0.7
        chain_of_thought_step(
            conversation_id=conversation_id,
            stage="Manual_Analysis",
            description="Human reasoning step",
            result="Manual conclusion",
            confidence=manual_confidence
        )

        # Verify overall confidence follows minimum rule
        summary = get_chain_summary(conversation_id)
        expected_min_confidence = min(deductive_confidence, inductive_confidence, manual_confidence)

        assert summary["success"] is True
        assert summary["step_count"] == 3
        assert summary["overall_confidence"] == expected_min_confidence

        # The chain should be as weak as its weakest link
        assert summary["overall_confidence"] <= min(deductive_confidence, inductive_confidence, manual_confidence)

    def test_real_world_scientific_reasoning_scenario(self):
        """Test a real-world scientific reasoning scenario with confidence tracking."""
        conversation_id = "scientific_reasoning"

        # Scenario: Analyzing experimental data and drawing conclusions

        # Step 1: Data pattern analysis (inductive)
        experimental_data = [10.1, 20.0, 30.2, 39.9, 50.1]  # Approximately linear
        pattern_chain = ReasoningChain()
        pattern_result = find_pattern_description(experimental_data, reasoning_chain=pattern_chain)
        pattern_confidence = pattern_chain.steps[0].confidence

        chain_of_thought_step(
            conversation_id=conversation_id,
            stage="Data_Analysis",
            description="Analyzing experimental data pattern",
            result=pattern_result,
            confidence=pattern_confidence
        )

        # Step 2: Hypothesis testing (deductive logic applied to statistical reasoning)
        # If pattern is linear AND slope is significant, THEN relationship exists
        hypothesis_confidence = 0.85  # Based on statistical significance

        chain_of_thought_step(
            conversation_id=conversation_id,
            stage="Hypothesis_Testing",
            description="Testing linear relationship hypothesis",
            result="Linear relationship confirmed",
            confidence=hypothesis_confidence
        )

        # Step 3: Prediction based on pattern (inductive)
        prediction_chain = ReasoningChain()
        next_value = predict_next_in_sequence(experimental_data, reasoning_chain=prediction_chain)
        prediction_confidence = prediction_chain.steps[0].confidence

        chain_of_thought_step(
            conversation_id=conversation_id,
            stage="Prediction",
            description="Predicting next experimental value",
            result=next_value,
            confidence=prediction_confidence
        )

        # Step 4: Conclusion synthesis (conservative confidence)
        conclusion_confidence = 0.75  # Conservative for scientific claims

        chain_of_thought_step(
            conversation_id=conversation_id,
            stage="Conclusion",
            description="Synthesizing experimental findings",
            result="Linear relationship established with predictive capability",
            confidence=conclusion_confidence
        )

        # Verify scientific reasoning chain
        summary = get_chain_summary(conversation_id)
        assert summary["success"] is True
        assert summary["step_count"] == 4

        # Overall confidence should reflect the most uncertain step
        all_confidences = [pattern_confidence, hypothesis_confidence, prediction_confidence, conclusion_confidence]
        expected_min = min(all_confidences)
        assert summary["overall_confidence"] == expected_min

        # Scientific reasoning should maintain reasonable confidence levels
        assert 0.5 <= summary["overall_confidence"] <= 1.0, "Scientific reasoning should maintain reasonable confidence"

        # Clean up
        clear_chain(conversation_id)

    def test_decision_making_workflow_with_uncertainty(self):
        """Test a decision-making workflow that incorporates uncertainty."""
        conversation_id = "decision_making"

        # Scenario: Medical diagnosis decision support

        # Step 1: Symptom pattern recognition (inductive with uncertainty)
        symptom_severity = [2, 3, 3, 4, 4]  # Increasing trend
        symptom_chain = ReasoningChain()
        symptom_pattern = find_pattern_description(symptom_severity, reasoning_chain=symptom_chain)
        symptom_confidence = symptom_chain.steps[0].confidence

        chain_of_thought_step(
            conversation_id=conversation_id,
            stage="Symptom_Analysis",
            description="Analyzing symptom progression pattern",
            result=symptom_pattern,
            confidence=symptom_confidence
        )

        # Step 2: Diagnostic reasoning (deductive with medical knowledge)
        # IF symptoms increase linearly AND duration > 3 days, THEN further testing needed
        diagnostic_confidence = 0.8  # Medical knowledge confidence

        chain_of_thought_step(
            conversation_id=conversation_id,
            stage="Diagnostic_Reasoning",
            description="Applying diagnostic criteria",
            result="Further testing recommended",
            confidence=diagnostic_confidence
        )

        # Step 3: Risk assessment (conservative medical approach)
        risk_confidence = 0.6  # Conservative in medical decisions

        chain_of_thought_step(
            conversation_id=conversation_id,
            stage="Risk_Assessment",
            description="Assessing patient risk factors",
            result="Moderate risk level",
            confidence=risk_confidence
        )

        # Step 4: Treatment recommendation (most conservative)
        treatment_confidence = 0.5  # Very conservative for treatment decisions

        chain_of_thought_step(
            conversation_id=conversation_id,
            stage="Treatment_Recommendation",
            description="Formulating treatment plan",
            result="Conservative monitoring with follow-up",
            confidence=treatment_confidence
        )

        # Verify medical decision-making chain
        summary = get_chain_summary(conversation_id)
        assert summary["success"] is True

        # Medical decisions should reflect the most conservative confidence
        assert summary["overall_confidence"] == 0.5, "Medical decisions should use most conservative confidence"

        # Overall confidence should be appropriately conservative for medical decisions
        assert summary["overall_confidence"] <= 0.6, "Medical reasoning should maintain conservative confidence"

        # Clean up
        clear_chain(conversation_id)


class TestToolSpecificationConfidenceDocumentation:
    """Test that tool specifications include accurate confidence documentation."""

    def test_openai_tool_specifications_include_confidence_docs(self):
        """Test that OpenAI tool specifications include confidence documentation."""
        openai_tools = get_openai_tools()

        # Should have tools from all reasoning modules
        assert len(openai_tools) > 0, "Should have registered tools"

        # Find mathematical reasoning tools
        math_tools = []
        for tool in openai_tools:
            description = tool["function"]["description"]
            if any(keyword in description.lower() for keyword in ["confidence", "mathematical", "arithmetic", "geometric", "modus ponens"]):
                math_tools.append(tool)

        assert len(math_tools) > 0, "Should have mathematical reasoning tools"

        # Verify confidence documentation is present
        for tool in math_tools:
            description = tool["function"]["description"]

            # Check for confidence-related documentation
            confidence_indicators = [
                "confidence", "Mathematical Basis", "Confidence Scoring",
                "reliability", "certainty", "probability"
            ]

            has_confidence_doc = any(indicator in description for indicator in confidence_indicators)
            assert has_confidence_doc, f"Tool {tool['function']['name']} should include confidence documentation"

    def test_bedrock_tool_specifications_include_confidence_docs(self):
        """Test that AWS Bedrock tool specifications include confidence documentation."""
        bedrock_tools = get_bedrock_tools()

        # Should have tools from all reasoning modules
        assert len(bedrock_tools) > 0, "Should have registered tools"

        # Find mathematical reasoning tools
        math_tools = []
        for tool in bedrock_tools:
            description = tool["toolSpec"]["description"]
            if any(keyword in description.lower() for keyword in ["confidence", "mathematical", "arithmetic", "geometric", "modus ponens"]):
                math_tools.append(tool)

        assert len(math_tools) > 0, "Should have mathematical reasoning tools"

        # Verify confidence documentation is present
        for tool in math_tools:
            description = tool["toolSpec"]["description"]

            # Check for confidence-related documentation
            confidence_indicators = [
                "confidence", "Mathematical Basis", "Confidence Scoring",
                "reliability", "certainty", "probability"
            ]

            has_confidence_doc = any(indicator in description for indicator in confidence_indicators)
            assert has_confidence_doc, f"Tool {tool['toolSpec']['name']} should include confidence documentation"

    def test_enhanced_tool_registry_confidence_metadata(self):
        """Test that enhanced tool registry includes proper confidence metadata."""
        enhanced_registry = get_enhanced_tool_registry()

        assert len(enhanced_registry) > 0, "Should have enhanced tool registry entries"

        # Find mathematical reasoning tools
        math_tools = []
        for entry in enhanced_registry:
            if entry["metadata"].is_mathematical_reasoning:
                math_tools.append(entry)

        assert len(math_tools) > 0, "Should have mathematical reasoning tools in enhanced registry"

        # Verify metadata completeness
        for entry in math_tools:
            metadata = entry["metadata"]

            # Check required metadata fields
            assert metadata.is_mathematical_reasoning is True
            assert metadata.confidence_documentation is not None, "Should have confidence documentation"
            assert metadata.mathematical_basis is not None, "Should have mathematical basis"

            # Verify confidence documentation quality
            conf_doc = metadata.confidence_documentation
            assert len(conf_doc) > 10, "Confidence documentation should be substantial"
            assert "confidence" in conf_doc.lower(), "Should mention confidence"

    def test_confidence_documentation_accuracy(self):
        """Test that confidence documentation accurately reflects implementation."""
        enhanced_registry = get_enhanced_tool_registry()

        # Test specific tools for documentation accuracy
        tool_accuracy_tests = {
            "apply_modus_ponens": {
                "expected_keywords": ["modus ponens", "deductive", "1.0", "0.0"],
                "expected_basis": "formal deductive logic"
            },
            "predict_next_in_sequence": {
                "expected_keywords": ["pattern", "arithmetic", "geometric", "sufficiency"],
                "expected_basis": "progression analysis"
            }
        }

        for entry in enhanced_registry:
            tool_name = entry["tool_spec"]["function"]["name"]

            if tool_name in tool_accuracy_tests:
                test_spec = tool_accuracy_tests[tool_name]
                metadata = entry["metadata"]

                # Check documentation contains expected keywords
                full_doc = (metadata.confidence_documentation or "") + " " + (metadata.mathematical_basis or "")
                full_doc = full_doc.lower()

                for keyword in test_spec["expected_keywords"]:
                    assert keyword.lower() in full_doc, f"Tool {tool_name} documentation should contain '{keyword}'"

                # Check mathematical basis
                if metadata.mathematical_basis:
                    basis = metadata.mathematical_basis.lower()
                    assert test_spec["expected_basis"] in basis, f"Tool {tool_name} should have correct mathematical basis"


class TestConfidenceMathematicalConsistency:
    """Test mathematical consistency of confidence scoring across all reasoning types."""

    def test_confidence_ordering_consistency(self):
        """Test that confidence ordering is mathematically consistent."""
        # Perfect conditions should always yield higher confidence than imperfect conditions

        # Deductive reasoning: Valid vs Invalid
        valid_deductive_chain = ReasoningChain()
        apply_modus_ponens(True, True, reasoning_chain=valid_deductive_chain)
        valid_deductive_conf = valid_deductive_chain.steps[0].confidence

        invalid_deductive_chain = ReasoningChain()
        apply_modus_ponens(False, True, reasoning_chain=invalid_deductive_chain)
        invalid_deductive_conf = invalid_deductive_chain.steps[0].confidence

        assert valid_deductive_conf > invalid_deductive_conf, "Valid deductive reasoning should have higher confidence than invalid"

        # Inductive reasoning: Perfect vs Noisy patterns
        perfect_sequence = [1, 2, 3, 4, 5]
        noisy_sequence = [1.1, 1.9, 3.2, 3.8, 5.1]

        perfect_chain = ReasoningChain()
        predict_next_in_sequence(perfect_sequence, reasoning_chain=perfect_chain)
        perfect_conf = perfect_chain.steps[0].confidence if len(perfect_chain.steps) > 0 else 0.0

        noisy_chain = ReasoningChain()
        predict_next_in_sequence(noisy_sequence, reasoning_chain=noisy_chain, rtol=0.3)
        noisy_conf = noisy_chain.steps[0].confidence if len(noisy_chain.steps) > 0 else 0.0

        if perfect_conf > 0 and noisy_conf > 0:
            assert perfect_conf >= noisy_conf, "Perfect patterns should have equal or higher confidence than noisy patterns"

    def test_confidence_bounds_universal(self):
        """Test that confidence bounds [0.0, 1.0] are universally respected."""
        test_scenarios = [
            # Deductive scenarios
            ("deductive_valid", lambda: self._get_deductive_confidence(True, True)),
            ("deductive_invalid", lambda: self._get_deductive_confidence(False, True)),

            # Inductive scenarios
            ("inductive_perfect", lambda: self._get_inductive_confidence([1, 2, 3, 4, 5])),
            ("inductive_noisy", lambda: self._get_inductive_confidence([1.1, 2.0, 2.9, 4.1])),
            ("inductive_random", lambda: self._get_inductive_confidence([1, 5, 2, 9, 3])),

            # Chain-of-thought scenarios
            ("chain_mixed", lambda: self._get_chain_confidence([0.8, 0.6, 0.9])),
            ("chain_extreme", lambda: self._get_chain_confidence([0.0, 1.0, 0.5])),
        ]

        for scenario_name, get_confidence_func in test_scenarios:
            confidence = get_confidence_func()
            assert 0.0 <= confidence <= 1.0, f"Confidence for {scenario_name} should be in [0.0, 1.0], got {confidence}"

    def _get_deductive_confidence(self, p: bool, p_implies_q: bool) -> float:
        """Helper: Get confidence from deductive reasoning."""
        chain = ReasoningChain()
        apply_modus_ponens(p, p_implies_q, reasoning_chain=chain)
        return chain.steps[0].confidence

    def _get_inductive_confidence(self, sequence: List[float]) -> float:
        """Helper: Get confidence from inductive reasoning."""
        chain = ReasoningChain()
        predict_next_in_sequence(sequence, reasoning_chain=chain, rtol=0.3)
        return chain.steps[0].confidence if len(chain.steps) > 0 else 0.0

    def _get_chain_confidence(self, confidences: List[float]) -> float:
        """Helper: Get overall confidence from chain-of-thought reasoning."""
        conversation_id = "test_chain_confidence"
        clear_chain(conversation_id)

        for i, conf in enumerate(confidences):
            chain_of_thought_step(
                conversation_id=conversation_id,
                stage=f"Step_{i+1}",
                description=f"Test step {i+1}",
                result=f"Result {i+1}",
                confidence=conf
            )

        summary = get_chain_summary(conversation_id)
        clear_chain(conversation_id)
        return summary["overall_confidence"]

    def test_confidence_determinism(self):
        """Test that confidence calculations are deterministic."""
        # Same inputs should always produce same confidence scores

        # Test deductive determinism
        for _ in range(10):
            chain1 = ReasoningChain()
            chain2 = ReasoningChain()

            apply_modus_ponens(True, True, reasoning_chain=chain1)
            apply_modus_ponens(True, True, reasoning_chain=chain2)

            assert chain1.steps[0].confidence == chain2.steps[0].confidence, "Deductive confidence should be deterministic"

        # Test inductive determinism
        test_sequence = [1, 2, 3, 4, 5]
        for _ in range(10):
            chain1 = ReasoningChain()
            chain2 = ReasoningChain()

            predict_next_in_sequence(test_sequence, reasoning_chain=chain1)
            predict_next_in_sequence(test_sequence, reasoning_chain=chain2)

            if len(chain1.steps) > 0 and len(chain2.steps) > 0:
                assert chain1.steps[0].confidence == chain2.steps[0].confidence, "Inductive confidence should be deterministic"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])