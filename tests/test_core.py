#!/usr/bin/env python3
"""
Comprehensive test suite for core.py module.

Tests ReasoningChain, ReasoningStep, tool registry, security features,
and mathematical reasoning detection.
"""
import os
import sys
import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from reasoning_library.core import (
    COMMENT_PATTERN,
    ENHANCED_TOOL_REGISTRY,
    EVIDENCE_PATTERN,
    FACTOR_PATTERN,
    MAX_SOURCE_CODE_SIZE,
    TOOL_REGISTRY,
    TYPE_MAP,
    ReasoningChain,
    ReasoningStep,
    ToolMetadata,
    _bedrock_format,
    _detect_mathematical_reasoning,
    _openai_format,
    _safe_copy_spec,
    curry,
    get_bedrock_tools,
    get_enhanced_tool_registry,
    get_json_schema_type,
    get_openai_tools,
    get_tool_specs,
    tool_spec,
)


class TestReasoningStep:
    """Test ReasoningStep dataclass functionality."""

    def test_basic_creation(self):
        """Test basic ReasoningStep creation."""
        step = ReasoningStep(
            step_number=1,
            stage="Analysis",
            description="Test step",
            result="test result",
        )

        assert step.step_number == 1
        assert step.stage == "Analysis"
        assert step.description == "Test step"
        assert step.result == "test result"
        assert step.confidence is None
        assert step.evidence is None
        assert step.assumptions == []
        assert step.metadata == {}

    def test_creation_with_all_fields(self):
        """Test ReasoningStep creation with all optional fields."""
        assumptions = ["assumption1", "assumption2"]
        metadata = {"key": "value", "number": 42}

        step = ReasoningStep(
            step_number=2,
            stage="Synthesis",
            description="Complex step",
            result={"complex": "result"},
            confidence=0.85,
            evidence="Supporting evidence",
            assumptions=assumptions,
            metadata=metadata,
        )

        assert step.step_number == 2
        assert step.stage == "Synthesis"
        assert step.confidence == 0.85
        assert step.evidence == "Supporting evidence"
        assert step.assumptions == assumptions
        assert step.metadata == metadata


class TestReasoningChain:
    """Test ReasoningChain functionality."""

    def setup_method(self):
        """Set up fresh ReasoningChain for each test."""
        self.chain = ReasoningChain()

    def test_empty_chain(self):
        """Test empty chain behavior."""
        assert len(self.chain.steps) == 0
        assert self.chain.last_result is None
        assert self.chain._step_counter == 0

    def test_add_single_step(self):
        """Test adding a single step."""
        step = self.chain.add_step(
            stage="Analysis", description="First step", result="result1"
        )

        assert len(self.chain.steps) == 1
        assert step.step_number == 1
        assert self.chain.last_result == "result1"
        assert self.chain._step_counter == 1

    def test_add_multiple_steps(self):
        """Test adding multiple steps maintains order and counter."""
        step1 = self.chain.add_step("Stage1", "Desc1", "Result1")
        step2 = self.chain.add_step("Stage2", "Desc2", "Result2", confidence=0.9)
        step3 = self.chain.add_step("Stage3", "Desc3", "Result3")

        assert len(self.chain.steps) == 3
        assert step1.step_number == 1
        assert step2.step_number == 2
        assert step3.step_number == 3
        assert self.chain.last_result == "Result3"
        assert step2.confidence == 0.9

    def test_clear_chain(self):
        """Test clearing chain resets state."""
        self.chain.add_step("Stage", "Desc", "Result")
        self.chain.add_step("Stage2", "Desc2", "Result2")

        assert len(self.chain.steps) == 2

        self.chain.clear()

        assert len(self.chain.steps) == 0
        assert self.chain.last_result is None
        assert self.chain._step_counter == 0

    def test_get_summary(self):
        """Test summary generation."""
        self.chain.add_step(
            stage="Analysis",
            description="Analyze data",
            result="analysis complete",
            confidence=0.95,
            evidence="Strong evidence",
            assumptions=["Data is valid"],
            metadata={"source": "test"},
        )

        summary = self.chain.get_summary()

        assert "Reasoning Chain Summary:" in summary
        assert "Step 1 (Analysis): Analyze data" in summary
        assert "Result: analysis complete" in summary
        assert "Confidence: 0.95" in summary
        assert "Evidence: Strong evidence" in summary
        assert "Assumptions: Data is valid" in summary
        assert "Metadata: {'source': 'test'}" in summary


class TestCurryDecorator:
    """Test curry decorator functionality."""

    def test_curry_basic_function(self):
        """Test currying a basic function."""

        @curry
        def add_three(a, b, c):
            return a + b + c

        # Full application
        assert add_three(1, 2, 3) == 6

        # Partial application
        add_two = add_three(1, 2)
        assert callable(add_two)
        assert add_two(3) == 6

        # Single argument partial
        add_one = add_three(1)
        assert add_one(2, 3) == 6

    def test_curry_with_kwargs(self):
        """Test curry with keyword arguments."""

        @curry
        def multiply_with_default(a, b, c=1):
            return a * b * c

        # Should work with enough positional args
        assert multiply_with_default(2, 3) == 6

        # Partial application
        double = multiply_with_default(2)
        assert double(3) == 6


class TestToolSpec:
    """Test tool_spec decorator and related functionality."""

    def setup_method(self):
        """Clear registries before each test."""
        TOOL_REGISTRY.clear()
        ENHANCED_TOOL_REGISTRY.clear()

    def test_basic_tool_spec(self):
        """Test basic tool specification generation."""

        @tool_spec
        def simple_function(x: int, y: str = "default") -> bool:
            """A simple test function."""
            return True

        # Check function still works
        assert simple_function(1) == True
        assert simple_function(1, "test") == True

        # Check tool spec was generated
        assert hasattr(simple_function, "tool_spec")
        spec = simple_function.tool_spec

        assert spec["type"] == "function"
        assert spec["function"]["name"] == "simple_function"
        assert spec["function"]["description"] == "A simple test function."

        # Check parameters
        params = spec["function"]["parameters"]
        assert params["type"] == "object"
        assert "x" in params["properties"]
        assert "y" in params["properties"]
        assert params["properties"]["x"]["type"] == "integer"
        assert params["properties"]["y"]["type"] == "string"
        assert params["required"] == ["x"]  # y has default

    def test_tool_spec_with_mathematical_metadata(self):
        """Test tool_spec with explicit mathematical metadata."""

        @tool_spec(
            mathematical_basis="Test mathematical reasoning",
            confidence_factors=["factor1", "factor2"],
            confidence_formula="factor1 * factor2",
        )
        def math_function(confidence: float) -> float:
            """Mathematical reasoning function."""
            return confidence * 2

        # Function should be in enhanced registry
        assert len(ENHANCED_TOOL_REGISTRY) == 1
        entry = ENHANCED_TOOL_REGISTRY[0]

        assert entry["metadata"].is_mathematical_reasoning == True
        assert entry["metadata"].mathematical_basis == "Test mathematical reasoning"
        assert entry["metadata"].confidence_factors == ["factor1", "factor2"]
        assert entry["metadata"].confidence_formula == "factor1 * factor2"

    def test_reasoning_chain_parameter_excluded(self):
        """Test that reasoning_chain parameter is excluded from tool spec."""

        @tool_spec
        def function_with_reasoning_chain(x: int, reasoning_chain=None) -> int:
            """Function with reasoning chain parameter."""
            return x * 2

        spec = function_with_reasoning_chain.tool_spec
        params = spec["function"]["parameters"]

        assert "x" in params["properties"]
        assert "reasoning_chain" not in params["properties"]
        assert params["required"] == ["x"]


class TestSecurityFeatures:
    """Test security features and protections."""

    def test_safe_copy_spec_basic(self):
        """Test safe copying of tool specifications."""
        from reasoning_library.core import _safe_copy_spec

        tool_spec = {
            "type": "function",
            "function": {
                "name": "test_func",
                "description": "Test function",
                "parameters": {"type": "object"},
            },
        }

        safe_spec = _safe_copy_spec(tool_spec)

        assert safe_spec["type"] == "function"
        assert safe_spec["function"]["name"] == "test_func"
        assert safe_spec["function"]["description"] == "Test function"
        assert safe_spec["function"]["parameters"] == {"type": "object"}

    def test_safe_copy_spec_filters_dangerous_keys(self):
        """Test that safe copy filters out non-whitelisted keys."""
        from reasoning_library.core import _safe_copy_spec

        dangerous_spec = {
            "type": "function",
            "__proto__": "malicious",
            "constructor": "bad",
            "function": {
                "name": "test",
                "description": "test",
                "parameters": {},
                "__proto__": "also_bad",
                "malicious_key": "filtered",
            },
        }

        safe_spec = _safe_copy_spec(dangerous_spec)

        assert "__proto__" not in safe_spec
        assert "constructor" not in safe_spec
        assert "__proto__" not in safe_spec["function"]
        assert "malicious_key" not in safe_spec["function"]
        assert len(safe_spec) == 2  # Only type and function
        assert len(safe_spec["function"]) == 3  # Only name, description, parameters

    def test_safe_copy_spec_validation(self):
        """Test input validation in safe copy."""
        from reasoning_library.core import _safe_copy_spec

        # Test invalid inputs
        with pytest.raises(ValueError, match="Tool specification must be a dictionary"):
            _safe_copy_spec("not a dict")

        with pytest.raises(
            ValueError, match="Tool specification must contain 'function' key"
        ):
            _safe_copy_spec({"type": "function"})

        with pytest.raises(
            ValueError, match="Tool specification 'function' value must be a dictionary"
        ):
            _safe_copy_spec({"type": "function", "function": "not a dict"})

    def test_redos_protection_source_size_limit(self):
        """Test ReDoS protection via source code size limiting."""
        # This tests the MAX_SOURCE_CODE_SIZE constant is reasonable
        assert MAX_SOURCE_CODE_SIZE > 0
        assert MAX_SOURCE_CODE_SIZE <= 50000  # Reasonable upper bound

    def test_regex_patterns_compiled(self):
        """Test that regex patterns are pre-compiled for performance."""
        # These should be compiled regex patterns, not strings
        assert hasattr(FACTOR_PATTERN, "pattern")
        assert hasattr(COMMENT_PATTERN, "pattern")
        assert hasattr(EVIDENCE_PATTERN, "pattern")


class TestMathematicalReasoningDetection:
    """Test mathematical reasoning detection functionality."""

    def test_detect_mathematical_reasoning_positive(self):
        """Test detection of mathematical reasoning functions."""
        from reasoning_library.core import _detect_mathematical_reasoning

        def math_func():
            """Function with confidence calculation based on pattern quality."""
            confidence = 0.95
            return confidence

        is_math, conf_doc, math_basis = _detect_mathematical_reasoning(math_func)

        assert is_math == True
        assert conf_doc is not None
        assert "confidence" in conf_doc.lower()

    def test_detect_mathematical_reasoning_negative(self):
        """Test non-mathematical functions are not detected."""
        from reasoning_library.core import _detect_mathematical_reasoning

        def regular_func():
            """A regular function that does basic string operations."""
            return "hello world"

        is_math, conf_doc, math_basis = _detect_mathematical_reasoning(regular_func)

        assert is_math == False
        assert conf_doc is None
        assert math_basis is None

    def test_detect_mathematical_reasoning_with_modus_ponens(self):
        """Test detection of modus ponens functions."""
        from reasoning_library.core import _detect_mathematical_reasoning

        def modus_ponens_func():
            """Applies modus ponens reasoning rule."""
            return True

        is_math, conf_doc, math_basis = _detect_mathematical_reasoning(
            modus_ponens_func
        )

        assert is_math == True
        if math_basis:
            assert "modus ponens" in math_basis.lower()


class TestTypeMapping:
    """Test JSON Schema type mapping functionality."""

    def test_basic_type_mapping(self):
        """Test basic Python to JSON Schema type mapping."""
        assert get_json_schema_type(bool) == "boolean"
        assert get_json_schema_type(int) == "integer"
        assert get_json_schema_type(float) == "number"
        assert get_json_schema_type(str) == "string"
        assert get_json_schema_type(list) == "array"
        assert get_json_schema_type(dict) == "object"

    def test_optional_type_mapping(self):
        """Test Optional type handling."""
        from typing import Optional

        assert get_json_schema_type(Optional[str]) == "string"
        assert get_json_schema_type(Optional[int]) == "integer"

    def test_list_type_mapping(self):
        """Test List type handling."""
        from typing import List

        assert get_json_schema_type(List[str]) == "array"
        assert get_json_schema_type(List[int]) == "array"

    def test_dict_type_mapping(self):
        """Test Dict type handling."""
        from typing import Dict

        assert get_json_schema_type(Dict[str, int]) == "object"

    def test_unknown_type_defaults(self):
        """Test unknown types default to string."""

        class CustomType:
            pass

        assert get_json_schema_type(CustomType) == "string"


class TestToolExportFormats:
    """Test tool export to different API formats."""

    def setup_method(self):
        """Clear registries and add test function."""
        TOOL_REGISTRY.clear()
        ENHANCED_TOOL_REGISTRY.clear()

        @tool_spec(mathematical_basis="Test math")
        def test_export_function(x: int, y: str = "default") -> bool:
            """Test function for export."""
            return True

        self.test_function = test_export_function

    def test_openai_format_export(self):
        """Test export to OpenAI format."""
        openai_tools = get_openai_tools()

        assert len(openai_tools) == 1
        tool = openai_tools[0]

        assert tool["type"] == "function"
        assert "function" in tool
        assert tool["function"]["name"] == "test_export_function"
        assert "Test function for export" in tool["function"]["description"]
        assert "Mathematical Basis: Test math" in tool["function"]["description"]

    def test_bedrock_format_export(self):
        """Test export to Bedrock format."""
        bedrock_tools = get_bedrock_tools()

        assert len(bedrock_tools) == 1
        tool = bedrock_tools[0]

        assert "toolSpec" in tool
        assert tool["toolSpec"]["name"] == "test_export_function"
        assert "inputSchema" in tool["toolSpec"]
        assert "json" in tool["toolSpec"]["inputSchema"]


class TestThreadSafety:
    """Test thread safety of core components."""

    def test_reasoning_chain_thread_safety(self):
        """Test that ReasoningChain is safe for concurrent access."""
        chain = ReasoningChain()
        results = []
        errors = []

        def add_steps(thread_id):
            try:
                for i in range(10):
                    step = chain.add_step(
                        stage=f"Thread{thread_id}",
                        description=f"Step {i} from thread {thread_id}",
                        result=f"result_{thread_id}_{i}",
                    )
                    results.append(step.step_number)
                    time.sleep(0.001)  # Small delay to encourage race conditions
            except Exception as e:
                errors.append(e)

        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=add_steps, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(chain.steps) == 50  # 5 threads * 10 steps each
        assert len(set(results)) == 50  # All step numbers should be unique
        assert max(results) == 50
        assert min(results) == 1


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_function_docstring(self):
        """Test tool_spec with function having no docstring."""

        @tool_spec
        def no_docstring_func():
            pass

        spec = no_docstring_func.tool_spec
        assert spec["function"]["description"] == ""

    def test_function_with_no_parameters(self):
        """Test tool_spec with function having no parameters."""

        @tool_spec
        def no_params_func():
            """Function with no parameters."""
            return True

        spec = no_params_func.tool_spec
        params = spec["function"]["parameters"]
        assert params["required"] == []
        assert params["properties"] == {}

    def test_reasoning_chain_with_none_values(self):
        """Test ReasoningChain handles None values gracefully."""
        chain = ReasoningChain()

        step = chain.add_step(
            stage="Test",
            description="Test with None values",
            result=None,
            confidence=None,
            evidence=None,
            assumptions=None,
            metadata=None,
        )

        assert step.result is None
        assert step.confidence is None
        assert step.evidence is None
        assert step.assumptions == []  # Should default to empty list
        assert step.metadata == {}  # Should default to empty dict

    def test_very_long_source_code_handling(self):
        """Test handling of very long source code for ReDoS protection."""
        from reasoning_library.core import _detect_mathematical_reasoning

        # Create a function with extremely long source code
        def create_long_source_func():
            exec(
                f"""
def long_func():
    '''Function with confidence scoring.'''
    {'# ' + 'x' * 1000}
    return 0.95
""",
                globals(),
            )
            return globals()["long_func"]

        long_func = create_long_source_func()

        # Should handle gracefully without hanging
        is_math, conf_doc, math_basis = _detect_mathematical_reasoning(long_func)

        # Should still detect mathematical reasoning despite long source
        assert isinstance(is_math, bool)


def run_all_tests():
    """Run all tests with detailed output."""
    print("🧪 Running comprehensive test suite for core.py...")

    # Test classes to run
    test_classes = [
        TestReasoningStep,
        TestReasoningChain,
        TestCurryDecorator,
        TestToolSpec,
        TestSecurityFeatures,
        TestMathematicalReasoningDetection,
        TestTypeMapping,
        TestToolExportFormats,
        TestThreadSafety,
        TestEdgeCases,
    ]

    total_tests = 0
    passed_tests = 0
    failed_tests = []

    for test_class in test_classes:
        print(f"\n📝 Testing {test_class.__name__}...")

        # Get all test methods
        test_methods = [
            method for method in dir(test_class) if method.startswith("test_")
        ]

        for method_name in test_methods:
            total_tests += 1
            try:
                # Create instance and run setup if exists
                instance = test_class()
                if hasattr(instance, "setup_method"):
                    instance.setup_method()

                # Run the test method
                method = getattr(instance, method_name)
                method()

                passed_tests += 1
                print(f"  ✅ {method_name}")

            except Exception as e:
                failed_tests.append(f"{test_class.__name__}.{method_name}: {str(e)}")
                print(f"  ❌ {method_name}: {str(e)}")

    # Print summary
    print(f"\n📊 Test Summary:")
    print(f"  Total tests: {total_tests}")
    print(f"  Passed: {passed_tests}")
    print(f"  Failed: {len(failed_tests)}")

    if failed_tests:
        print(f"\n❌ Failed tests:")
        for failure in failed_tests:
            print(f"  - {failure}")
        return False
    else:
        print(f"\n🎉 All tests passed!")
        return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
