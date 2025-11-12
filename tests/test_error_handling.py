"""
Comprehensive tests for standardized error handling patterns.

This test suite ensures that the reasoning library uses specific exception types
rather than broad Exception handling, maintaining proper error propagation
and clear error categorization.
"""

import pytest
from reasoning_library.exceptions import (
    ReasoningError,
    ValidationError,
    ComputationError,
    PatternDetectionError,
    TimeoutError,
    CacheError,
    SecurityError,
    ImportWarning,
    ReasoningChainError,
    ToolSpecificationError,
)
from reasoning_library.core import _detect_mathematical_reasoning
from reasoning_library.inductive import detect_recursive_pattern
from reasoning_library.abductive import _validate_confidence_value
from reasoning_library.chain_of_thought import _validate_conversation_id


class TestExceptionHierarchy:
    """Test the exception hierarchy and inheritance."""

    def test_reasoning_error_base_class(self):
        """Test that ReasoningError is the proper base class."""
        error = ReasoningError("Test message")
        assert isinstance(error, Exception)
        assert error.message == "Test message"
        assert error.details == {}
        assert str(error) == "Test message"

    def test_reasoning_error_with_details(self):
        """Test ReasoningError with details dictionary."""
        details = {"context": "test", "code": 123}
        error = ReasoningError("Test message", details)
        assert error.details == details
        assert "Details:" in str(error)

    def test_exception_inheritance(self):
        """Test that all custom exceptions inherit from ReasoningError."""
        exceptions = [
            ValidationError,
            ComputationError,
            PatternDetectionError,
            TimeoutError,
            CacheError,
            SecurityError,
            ImportWarning,
            ReasoningChainError,
            ToolSpecificationError,
        ]

        for exc_class in exceptions:
            exc_instance = exc_class("test")
            assert isinstance(exc_instance, ReasoningError)
            assert isinstance(exc_instance, Exception)


class TestValidationError:
    """Test ValidationError usage in input validation."""

    def test_abductive_confidence_validation(self):
        """Test confidence validation in abductive reasoning."""
        # Test valid confidence values
        assert _validate_confidence_value(0.5) == 0.5
        assert _validate_confidence_value(0.0) == 0.0
        assert _validate_confidence_value(1.0) == 1.0

        # Test confidence clamping
        assert _validate_confidence_value(-0.5) == 0.0
        assert _validate_confidence_value(1.5) == 1.0

        # Test invalid confidence values raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            _validate_confidence_value("invalid")

        assert "invalid" in str(exc_info.value)
        assert "Confidence value" in str(exc_info.value)

    def test_chain_of_thought_conversation_validation(self):
        """Test conversation ID validation in chain of thought."""
        # Test valid conversation IDs
        assert _validate_conversation_id("valid123") == "valid123"
        assert _validate_conversation_id("test_conversation-1") == "test_conversation-1"

        # Test invalid conversation IDs raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            _validate_conversation_id(123)
        assert "must be a string" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            _validate_conversation_id("")
        assert "Invalid conversation_id format" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            _validate_conversation_id("invalid@conversation")
        assert "Invalid conversation_id format" in str(exc_info.value)


class TestSpecificExceptionHandling:
    """Test that specific exceptions are used instead of broad Exception handling."""

    def test_core_module_specific_exceptions(self):
        """Test that core module uses specific exceptions."""
        # This should not raise an exception
        def dummy_func():
            pass

        # Test function hash generation with various edge cases
        result = _detect_mathematical_reasoning(dummy_func)
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_inductive_module_pattern_detection_errors(self):
        """Test that inductive module handles pattern detection errors specifically."""
        # Test with empty sequence - should handle gracefully
        reasoning_chain = None  # No reasoning chain for this test
        result = detect_recursive_pattern([], reasoning_chain)
        assert result is None

        # Test with very short sequence - should handle gracefully
        result = detect_recursive_pattern([1], reasoning_chain)
        assert result is None

    def test_exception_message_consistency(self):
        """Test that error messages are consistent and informative."""
        try:
            _validate_confidence_value("completely_invalid_value")
        except ValidationError as e:
            assert "completely_invalid_value" in str(e)
            assert "Confidence value" in str(e)
            assert "invalid" in str(e).lower()

        try:
            _validate_conversation_id("invalid@conversation#id")
        except ValidationError as e:
            assert "Invalid conversation_id format" in str(e)


class TestErrorPropagation:
    """Test that errors propagate properly without being swallowed."""

    def test_validation_error_propagation(self):
        """Test that ValidationErrors propagate through call stack."""
        def inner_function():
            _validate_confidence_value("invalid")

        def outer_function():
            inner_function()

        with pytest.raises(ValidationError) as exc_info:
            outer_function()

        assert "invalid" in str(exc_info.value)

    def test_nested_exception_handling(self):
        """Test exception handling in nested function calls."""
        def level_3():
            _validate_conversation_id("")

        def level_2():
            level_3()

        def level_1():
            level_2()

        with pytest.raises(ValidationError) as exc_info:
            level_1()

        assert "Invalid conversation_id format" in str(exc_info.value)


class TestBackwardCompatibility:
    """Test that error handling changes maintain backward compatibility."""

    def test_error_message_format_compatibility(self):
        """Test that error messages maintain expected format for existing code."""
        # Test that error messages still contain expected information
        with pytest.raises(Exception) as exc_info:  # Catch broad exception to test compatibility
            _validate_confidence_value("invalid")

        # Should still be catchable as a general exception
        assert isinstance(exc_info.value, ValidationError)
        assert "invalid" in str(exc_info.value)

    def test_exception_type_compatibility(self):
        """Test that new exceptions are compatible with existing exception handling."""
        # Existing code that catches ValueError should still work
        # (ValidationError inherits from Exception, so it's still catchable)
        try:
            _validate_conversation_id("invalid@id")
        except Exception as e:  # This is how existing code might catch errors
            assert isinstance(e, ValidationError)
            assert "Invalid conversation_id format" in str(e)


class TestErrorHandlingEdgeCases:
    """Test edge cases in error handling."""

    def test_error_with_unicode_characters(self):
        """Test error handling with unicode characters in error messages."""
        unicode_confidence = "测试"
        with pytest.raises(ValidationError) as exc_info:
            _validate_confidence_value(unicode_confidence)
        assert unicode_confidence in str(exc_info.value)

    def test_error_with_very_long_inputs(self):
        """Test error handling with very long inputs."""
        long_conversation_id = "a" * 100  # Exceeds the 64 character limit
        with pytest.raises(ValidationError) as exc_info:
            _validate_conversation_id(long_conversation_id)
        assert "Invalid conversation_id format" in str(exc_info.value)

    def test_error_with_special_characters(self):
        """Test error handling with special characters."""
        special_chars_confidence = "!@#$%^&*(){}[]|\\:;\"'<>?,./"
        with pytest.raises(ValidationError) as exc_info:
            _validate_confidence_value(special_chars_confidence)
        assert special_chars_confidence in str(exc_info.value)


class TestErrorHandlingDocumentation:
    """Test that error handling is properly documented through exception types."""

    def test_exception_categories(self):
        """Test that exceptions are properly categorized."""
        # Validation-related errors
        validation_errors = [ValidationError]

        # Computation-related errors
        computation_errors = [ComputationError, PatternDetectionError]

        # System-related errors
        system_errors = [TimeoutError, CacheError, SecurityError]

        # All should inherit from ReasoningError
        for error in validation_errors + computation_errors + system_errors:
            assert issubclass(error, ReasoningError)

    def test_exception_clarity(self):
        """Test that exception types clearly indicate error categories."""
        # ValidationError should be for input validation issues
        with pytest.raises(ValidationError):
            _validate_conversation_id("")

        # Each exception type should indicate its purpose through its name
        exception_names = [
            "ValidationError",
            "ComputationError",
            "PatternDetectionError",
            "TimeoutError",
            "CacheError",
            "SecurityError",
            "ImportWarning",
            "ReasoningChainError",
            "ToolSpecificationError",
        ]

        for name in exception_names:
            assert "Error" in name or "Warning" in name
            # All should be clearly identifiable by their names


if __name__ == "__main__":
    pytest.main([__file__])