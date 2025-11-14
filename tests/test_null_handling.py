"""
Tests for standardized null/None handling patterns.

This test suite verifies the consistent handling of None, empty strings,
and empty collections across the reasoning library.
"""

import pytest
import logging
from typing import List, Dict, Optional, Any

from reasoning_library.null_handling import (
    safe_none_coalesce,
    safe_list_coalesce,
    safe_dict_coalesce,
    safe_string_coalesce,
    normalize_none_return,
    handle_optional_params,
    with_null_safety,
    init_optional_bool,
    init_optional_string,
    init_optional_list,
    init_optional_dict,
    NO_VALUE,
    EMPTY_STRING,
    EMPTY_LIST,
    EMPTY_DICT
)


class TestSafeNoneCoalesce:
    """Test the safe_none_coalesce utility function."""

    def test_none_value_with_default(self):
        """Test None values are replaced with defaults."""
        result = safe_none_coalesce(None, "default")
        assert result == "default"

    def test_non_none_value_without_converter(self):
        """Test non-None values are returned as-is."""
        result = safe_none_coalesce("value", "default")
        assert result == "value"

    def test_non_none_value_with_converter(self):
        """Test non-None values are converted when converter provided."""
        result = safe_none_coalesce("123", 0, int)
        assert result == 123

    def test_converter_exception_returns_default(self):
        """Test converter exceptions return the default value."""
        result = safe_none_coalesce("not_a_number", 0, int)
        assert result == 0


class TestSafeListCoalesce:
    """Test the safe_list_coalesce utility function."""

    def test_none_returns_empty_list(self):
        """Test None returns empty list."""
        result = safe_list_coalesce(None)
        assert result == []

    def test_list_returns_as_is(self):
        """Test valid lists are returned unchanged."""
        test_list = [1, 2, 3]
        result = safe_list_coalesce(test_list)
        assert result == test_list
        assert result is test_list  # Same object reference

    def test_tuple_converts_to_list(self):
        """Test tuples are converted to lists."""
        test_tuple = (1, 2, 3)
        result = safe_list_coalesce(test_tuple)
        assert result == [1, 2, 3]
        assert isinstance(result, list)

    def test_invalid_type_returns_empty_list(self):
        """Test invalid types return empty list."""
        result = safe_list_coalesce("not_a_list")
        assert result == []

    def test_object_that_cant_convert_returns_empty_list(self):
        """Test objects that can't be converted to list return empty list."""
        # object() has __iter__ but converting to list should work
        # Use a custom object that has __iter__ but fails when converted
        class BadIterable:
            def __iter__(self):
                raise TypeError("Cannot iterate")

        result = safe_list_coalesce(BadIterable())
        assert result == []


class TestSafeDictCoalesce:
    """Test the safe_dict_coalesce utility function."""

    def test_none_returns_empty_dict(self):
        """Test None returns empty dict."""
        result = safe_dict_coalesce(None)
        assert result == {}

    def test_dict_returns_as_is(self):
        """Test valid dicts are returned unchanged."""
        test_dict = {"key": "value"}
        result = safe_dict_coalesce(test_dict)
        assert result == test_dict
        assert result is test_dict  # Same object reference

    def test_list_of_tuples_converts_to_dict(self):
        """Test list of tuples converts to dict."""
        test_list = [("key1", "value1"), ("key2", "value2")]
        result = safe_dict_coalesce(test_list)
        assert result == {"key1": "value1", "key2": "value2"}
        assert isinstance(result, dict)

    def test_invalid_type_returns_empty_dict(self):
        """Test invalid types return empty dict."""
        result = safe_dict_coalesce("not_a_dict")
        assert result == {}


class TestSafeStringCoalesce:
    """Test the safe_string_coalesce utility function."""

    def test_none_returns_empty_string(self):
        """Test None returns empty string."""
        result = safe_string_coalesce(None)
        assert result == ""

    def test_string_returns_as_is(self):
        """Test valid strings are returned unchanged."""
        test_string = "hello"
        result = safe_string_coalesce(test_string)
        assert result == test_string
        assert result is test_string  # Same object reference

    def test_number_converts_to_string(self):
        """Test numbers convert to strings."""
        result = safe_string_coalesce(123)
        assert result == "123"

    def test_invalid_type_returns_empty_string(self):
        """Test types that can't convert return empty string."""
        class Unconvertible:
            def __str__(self):
                raise ValueError("Cannot convert")

        result = safe_string_coalesce(Unconvertible())
        assert result == ""


class TestNormalizeNoneReturn:
    """Test the normalize_none_return utility function."""

    def test_none_stays_none(self):
        """Test None values are normalized to empty types."""
        # Test generic None stays None
        result = normalize_none_return(None, object)
        assert result is NO_VALUE

        # Test specific types are normalized to empty equivalents
        result = normalize_none_return(None, str)
        assert result == ""

        result = normalize_none_return(None, list)
        assert result == []

        result = normalize_none_return(None, dict)
        assert result == {}

    def test_boolean_return_normalized(self):
        """Test boolean returns are normalized."""
        result = normalize_none_return(True, bool)
        assert result is True

        result = normalize_none_return(False, bool)
        assert result is False

    def test_list_return_normalized(self):
        """Test list returns are normalized."""
        result = normalize_none_return([1, 2, 3], list)
        assert result == [1, 2, 3]

        result = normalize_none_return(None, list)
        assert result == []

    def test_dict_return_normalized(self):
        """Test dict returns are normalized."""
        result = normalize_none_return({"key": "value"}, dict)
        assert result == {"key": "value"}

        result = normalize_none_return(None, dict)
        assert result == {}

    def test_string_return_normalized(self):
        """Test string returns are normalized."""
        result = normalize_none_return("hello", str)
        assert result == "hello"

        result = normalize_none_return(None, str)
        assert result == ""


class TestHandleOptionalParams:
    """Test the handle_optional_params utility function."""

    def test_list_parameters(self):
        """Test list parameters are normalized."""
        result = handle_optional_params(my_list=None, other_list=[1, 2, 3])
        assert result["my_list"] == []
        assert result["other_list"] == [1, 2, 3]

    def test_dict_parameters(self):
        """Test dict parameters are normalized."""
        result = handle_optional_params(my_dict=None, metadata={"key": "value"})
        assert result["my_dict"] == {}
        assert result["metadata"] == {"key": "value"}

    def test_string_parameters(self):
        """Test string parameters are normalized."""
        result = handle_optional_params(evidence=None, description="test")
        assert result["evidence"] == ""
        assert result["description"] == "test"

    def test_generic_parameters_preserved(self):
        """Test generic parameters are preserved."""
        result = handle_optional_params(confidence=0.5, count=None)
        assert result["confidence"] == 0.5
        assert result["count"] is None


class TestWithNullSafety:
    """Test the with_null_safety decorator."""

    def test_successful_return_preserved(self):
        """Test successful returns are preserved."""
        @with_null_safety(expected_return_type=str)
        def test_func():
            return "success"

        result = test_func()
        assert result == "success"

    def test_none_return_normalized(self):
        """Test None returns are normalized."""
        @with_null_safety(expected_return_type=str)
        def test_func():
            return None

        result = test_func()
        assert result == ""

    def test_exception_returns_no_value(self):
        """Test exceptions return appropriate no value."""
        @with_null_safety(expected_return_type=str)
        def test_func():
            raise ValueError("Test error")

        result = test_func()
        assert result == ""

    def test_boolean_exception_handling(self):
        """Test boolean exception handling."""
        @with_null_safety(expected_return_type=bool)
        def test_func():
            raise ValueError("Test error")

        result = test_func()
        assert result is NO_VALUE

    def test_list_exception_handling(self):
        """Test list exception handling."""
        @with_null_safety(expected_return_type=list)
        def test_func():
            raise ValueError("Test error")

        result = test_func()
        assert result == EMPTY_LIST

    def test_dict_exception_handling(self):
        """Test dict exception handling."""
        @with_null_safety(expected_return_type=dict)
        def test_func():
            raise ValueError("Test error")

        result = test_func()
        assert result == EMPTY_DICT

    def test_unsupported_type_exception_handling(self):
        """Test unsupported type exception handling."""
        @with_null_safety(expected_return_type=int)
        def test_func():
            raise ValueError("Test error")

        result = test_func()
        assert result is NO_VALUE


class TestInitOptionalFunctions:
    """Test the initialization utility functions."""

    def test_init_optional_bool(self):
        """Test optional bool initialization."""
        result = init_optional_bool()
        assert result is None

        result = init_optional_bool(True)
        assert result is True

        result = init_optional_bool(False)
        assert result is False

    def test_init_optional_string(self):
        """Test optional string initialization."""
        result = init_optional_string()
        assert result == ""

        result = init_optional_string("hello")
        assert result == "hello"

    def test_init_optional_list(self):
        """Test optional list initialization."""
        result = init_optional_list()
        assert result == []

        result = init_optional_list([1, 2, 3])
        assert result == [1, 2, 3]

    def test_init_optional_dict(self):
        """Test optional dict initialization."""
        result = init_optional_dict()
        assert result == {}

        result = init_optional_dict({"key": "value"})
        assert result == {"key": "value"}


class TestConstants:
    """Test the constants for consistent null handling."""

    def test_no_value_constant(self):
        """Test NO_VALUE constant."""
        assert NO_VALUE is None

    def test_empty_constants(self):
        """Test empty constants."""
        assert EMPTY_STRING == ""
        assert EMPTY_LIST == []
        assert EMPTY_DICT == {}
        assert isinstance(EMPTY_LIST, list)
        assert isinstance(EMPTY_DICT, dict)


class TestIntegrationWithReasoningStep:
    """Test integration with ReasoningStep patterns."""

    def test_reasoning_step_optional_params(self):
        """Test that ReasoningStep optional parameters work correctly."""
        # This would test the actual ReasoningStep class if we import it
        # For now, test the pattern
        normalized = handle_optional_params(
            assumptions=None,
            metadata=None,
            evidence=None
        )

        assert normalized["assumptions"] == []
        assert normalized["metadata"] == {}
        assert normalized["evidence"] == ""


class TestDangerousExceptionHandling:
    """Test dangerous exception swallowing vulnerability and its fix."""

    def test_current_dangerous_exception_swallowing_memoryerror(self):
        """Test that MemoryError is currently dangerously swallowed."""
        @with_null_safety(expected_return_type=str)
        def memory_error_func():
            # Simulate memory exhaustion
            try:
                # This approach might not actually trigger MemoryError reliably
                # due to Python's memory management, but illustrates the point
                raise MemoryError("Out of memory!")
            except MemoryError:
                raise  # Re-raise to test the decorator

        # This should raise MemoryError but currently doesn't (vulnerability)
        # This test documents the dangerous behavior
        with pytest.raises(MemoryError):
            memory_error_func()

    def test_current_dangerous_exception_swallowing_systemerror(self):
        """Test that SystemError is currently dangerously swallowed."""
        @with_null_safety(expected_return_type=str)
        def system_error_func():
            raise SystemError("Critical system error")

        # This should raise SystemError but currently doesn't (vulnerability)
        with pytest.raises(SystemError):
            system_error_func()

    def test_current_dangerous_exception_swallowing_keyboardinterrupt(self):
        """Test that KeyboardInterrupt is currently dangerously swallowed."""
        @with_null_safety(expected_return_type=str)
        def interrupt_func():
            raise KeyboardInterrupt("User interrupted")

        # This should raise KeyboardInterrupt but currently doesn't (vulnerability)
        with pytest.raises(KeyboardInterrupt):
            interrupt_func()

    def test_business_exceptions_should_be_handled_gracefully(self):
        """Test that business exceptions should still be handled gracefully."""
        @with_null_safety(expected_return_type=str)
        def value_error_func():
            raise ValueError("Invalid input value")

        # ValueError should be caught and return empty string (desired behavior)
        result = value_error_func()
        assert result == ""

    def test_type_error_should_be_handled_gracefully(self):
        """Test that TypeError should be handled gracefully."""
        @with_null_safety(expected_return_type=dict)
        def type_error_func():
            raise TypeError("Invalid type operation")

        # TypeError should be caught and return empty dict (desired behavior)
        result = type_error_func()
        assert result == {}

    def test_attribute_error_should_be_handled_gracefully(self):
        """Test that AttributeError should be handled gracefully."""
        @with_null_safety(expected_return_type=list)
        def attribute_error_func():
            raise AttributeError("Missing attribute")

        # AttributeError should be caught and return empty list (desired behavior)
        result = attribute_error_func()
        assert result == []

    def test_key_error_should_be_handled_gracefully(self):
        """Test that KeyError should be handled gracefully."""
        @with_null_safety(expected_return_type=bool)
        def key_error_func():
            raise KeyError("Missing key")

        # KeyError should be caught and return NO_VALUE (desired behavior)
        result = key_error_func()
        assert result is None

    def test_import_error_should_propagate(self):
        """Test that ImportError should propagate (system-level error)."""
        @with_null_safety(expected_return_type=str)
        def import_error_func():
            raise ImportError("Cannot import required module")

        # ImportError should propagate (system error)
        with pytest.raises(ImportError):
            import_error_func()

    def test_runtime_error_should_propagate(self):
        """Test that RuntimeError should propagate (system-level error)."""
        @with_null_safety(expected_return_type=str)
        def runtime_error_func():
            raise RuntimeError("Critical runtime failure")

        # RuntimeError should propagate (system error)
        with pytest.raises(RuntimeError):
            runtime_error_func()

    def test_logging_for_caught_business_exceptions(self):
        """Test that business exceptions are securely handled without information disclosure."""
        from reasoning_library.null_handling import _sanitize_exception_message

        # Test the sanitization function directly
        safe_msg = _sanitize_exception_message("test_func", "KeyError", "'missing_key'")

        # Verify useful information is preserved
        assert "test_func" in safe_msg
        assert "KeyError" in safe_msg
        assert "missing_key" in safe_msg

        # Test that sensitive paths are removed
        path_msg = _sanitize_exception_message("load_config", "FileNotFoundError", "/Users/john/secrets.txt")
        assert "/Users/john" not in path_msg
        assert "[USER_DIR]" in path_msg or "[FILE]" in path_msg

        # Test exception handling behavior
        @with_null_safety(expected_return_type=str)
        def test_function():
            raise KeyError("test_key_error")

        result = test_function()

        # Verify function returns appropriate empty value
        assert result == ""  # EMPTY_STRING for str return type

    def test_debug_logging_format(self):
        """Test that debug logging contains appropriate information."""
        # This test would verify that logging includes:
        # - Function name
        # - Exception type
        # - Exception message
        # - Stack trace (exc_info=True)
        pass  # Implementation would require log capture setup


if __name__ == "__main__":
    pytest.main([__file__])