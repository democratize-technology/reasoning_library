"""
Targeted tests to cover specific missing lines for 100% coverage.
"""

import pytest
from reasoning_library import get_all_tool_specs, get_all_openai_tools, get_all_bedrock_tools
from reasoning_library.null_handling import safe_list_coalesce, with_null_safety, EMPTY_LIST, EMPTY_DICT, EMPTY_STRING
from reasoning_library.validation import validate_parameters, ValidationError
from reasoning_library.chain_of_thought import chain_of_thought_step


class TestInitModuleCoverage:
    """Test coverage for __init__.py module."""

    def test_get_all_tool_specs_coverage(self):
        """Test get_all_tool_specs function."""
        # Import modules to populate tool registries
        import reasoning_library.deductive
        import reasoning_library.inductive

        result = get_all_tool_specs()
        assert isinstance(result, list)
        # Should contain tools from the imported modules
        assert len(result) > 0

    def test_get_all_openai_tools_coverage(self):
        """Test get_all_openai_tools function."""
        # Import modules to populate tool registries
        import reasoning_library.deductive
        import reasoning_library.inductive

        result = get_all_openai_tools()
        assert isinstance(result, list)

    def test_get_all_bedrock_tools_coverage(self):
        """Test get_all_bedrock_tools function."""
        # Import modules to populate tool registries
        import reasoning_library.deductive
        import reasoning_library.inductive

        result = get_all_bedrock_tools()
        assert isinstance(result, list)


class TestNullHandlingMissingCoverage:
    """Test specific missing lines in null_handling.py."""

    def test_safe_list_coerce_type_error(self):
        """Test safe_list_coerce with object that can't be converted to list."""
        # This should trigger the except block on lines 62-63
        result = safe_list_coalesce(object())  # object() can't be converted to list
        assert result == []

    def test_with_null_safety_decorator_return_types(self):
        """Test with_null_safety decorator different return types."""
        # Test with list type
        @with_null_safety(expected_return_type=list)
        def test_func_none_list():
            return None

        result = test_func_none_list()
        assert result == EMPTY_LIST  # Should trigger line 197

        # Test with dict type
        @with_null_safety(expected_return_type=dict)
        def test_func_none_dict():
            return None

        result = test_func_none_dict()
        assert result == EMPTY_DICT  # Should trigger line 199

        # Test with str type
        @with_null_safety(expected_return_type=str)
        def test_func_none_str():
            return None

        result = test_func_none_str()
        assert result == EMPTY_STRING  # Should trigger line 201

        # Test with unsupported type (int)
        @with_null_safety(expected_return_type=int)
        def test_func_none_int():
            return None

        result = test_func_none_int()
        assert result is None  # Should trigger line 203


class TestValidationMissingCoverage:
    """Test specific missing lines in validation.py."""

    def test_validate_parameters_decorator(self):
        """Test validate_parameters decorator error path."""
        # Define a validator
        def positive_int(value):
            if not isinstance(value, int) or value <= 0:
                raise ValueError("Must be positive integer")
            return value

        @validate_parameters(param1=positive_int)
        def test_function(param1):
            return f"param1={param1}"

        # Test successful validation
        result = test_function(5)
        assert result == "param1=5"

        # Test validation failure - should trigger line 355
        with pytest.raises(ValidationError) as exc_info:
            test_function(-5)

        assert "param1" in str(exc_info.value)
        assert "validation failed" in str(exc_info.value)


class TestChainOfThoughtMissingCoverage:
    """Test specific missing lines in chain_of_thought.py."""

    def test_chain_of_thought_step_validation_error(self):
        """Test chain_of_thought_step with ValidationError to cover exception handling."""
        # Test with extremely large description to trigger ValidationError
        large_description = "x" * 10000  # Much larger than the max string length
        large_metadata = {"key" + str(i): "value" * 100 for i in range(100)}

        result = chain_of_thought_step(
            conversation_id="test_conv",
            stage="Analysis",
            description=large_description,
            result="test_result",
            metadata=large_metadata
        )

        # Should return error response due to validation failure
        assert result["success"] is False
        assert "error" in result
        assert result["step_number"] == -1