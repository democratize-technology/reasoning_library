"""
Comprehensive tests for input validation utilities.

This module tests the validation functions for complex parameter types
to ensure robust input validation and prevent type-related security vulnerabilities.
"""

import pytest
from typing import Any, Dict, List, Optional
from reasoning_library.validation import (
    validate_string_list,
    validate_dict_schema,
    validate_hypothesis_dict,
    validate_confidence_value,
    validate_hypotheses_list,
    validate_metadata_dict,
)
from reasoning_library.exceptions import ValidationError


class TestValidateStringList:
    """Test the validate_string_list function."""

    def test_valid_string_list(self):
        """Test validation of a valid string list."""
        result = validate_string_list(["item1", "item2", "item3"], "test_field")
        assert result == ["item1", "item2", "item3"]

    def test_none_value(self):
        """Test that None values are handled correctly."""
        result = validate_string_list(None, "test_field")
        assert result is None

    def test_empty_list_allowed(self):
        """Test that empty lists are allowed when permitted."""
        result = validate_string_list([], "test_field", allow_empty=True)
        assert result == []

    def test_empty_list_not_allowed(self):
        """Test that empty lists raise error when not permitted."""
        with pytest.raises(ValidationError, match="test_field cannot be empty"):
            validate_string_list([], "test_field", allow_empty=False)

    def test_non_list_input(self):
        """Test that non-list inputs raise ValidationError."""
        with pytest.raises(ValidationError, match="test_field must be a list"):
            validate_string_list("not_a_list", "test_field")

    def test_non_string_elements(self):
        """Test that non-string elements raise ValidationError."""
        with pytest.raises(ValidationError, match="test_field\\[1\\] must be a string"):
            validate_string_list(["valid", 123, "another"], "test_field")

    def test_whitespace_strings(self):
        """Test that whitespace-only strings raise ValidationError."""
        with pytest.raises(ValidationError, match="test_field\\[1\\] cannot be empty or whitespace"):
            validate_string_list(["valid", "   ", "another"], "test_field")

    def test_max_length_enforcement(self):
        """Test that max length constraint is enforced."""
        with pytest.raises(ValidationError, match="test_field exceeds maximum length of 2"):
            validate_string_list(["item1", "item2", "item3"], "test_field", max_length=2)

    def test_pattern_matching(self):
        """Test that pattern matching works correctly."""
        # Valid pattern match
        result = validate_string_list(["test_123", "item_456"], "test_field", pattern=r"^[a-z0-9_]+$")
        assert result == ["test_123", "item_456"]

        # Invalid pattern match
        with pytest.raises(ValidationError, match="test_field\\[1\\] does not match required pattern"):
            validate_string_list(["valid", "Invalid-123"], "test_field", pattern=r"^[a-z0-9_]+$")

    def test_string_trimming(self):
        """Test that strings are properly trimmed."""
        result = validate_string_list(["  item1  ", " item2 "], "test_field")
        assert result == ["item1", "item2"]


class TestValidateDictSchema:
    """Test the validate_dict_schema function."""

    def test_valid_dict(self):
        """Test validation of a valid dictionary."""
        result = validate_dict_schema(
            {"key1": "value1", "key2": "value2"},
            "test_field",
            required_keys=["key1"],
            optional_keys=["key2"]
        )
        assert result == {"key1": "value1", "key2": "value2"}

    def test_none_value(self):
        """Test that None values are handled correctly."""
        result = validate_dict_schema(None, "test_field")
        assert result is None

    def test_non_dict_input(self):
        """Test that non-dict inputs raise ValidationError."""
        with pytest.raises(ValidationError, match="test_field must be a dictionary"):
            validate_dict_schema("not_a_dict", "test_field")

    def test_missing_required_key(self):
        """Test that missing required keys raise ValidationError."""
        with pytest.raises(ValidationError, match="test_field missing required key: required_key"):
            validate_dict_schema(
                {"optional_key": "value"},
                "test_field",
                required_keys=["required_key"]
            )

    def test_unexpected_key_not_allowed(self):
        """Test that unexpected keys raise ValidationError when not allowed."""
        with pytest.raises(ValidationError, match="test_field contains unexpected key: unexpected_key"):
            validate_dict_schema(
                {"expected_key": "value", "unexpected_key": "value"},
                "test_field",
                required_keys=["expected_key"],
                allow_extra_keys=False
            )

    def test_key_type_validation(self):
        """Test that key types are validated correctly."""
        with pytest.raises(ValidationError, match="test_field\\[key1\\] must be of type int"):
            validate_dict_schema(
                {"key1": "not_an_int"},
                "test_field",
                key_types={"key1": int}
            )

    def test_custom_value_validators(self):
        """Test that custom value validators work correctly."""
        def validate_positive(value):
            if value <= 0:
                raise ValueError("Must be positive")
            return value

        with pytest.raises(ValidationError, match="test_field\\[key1\\] validation failed"):
            validate_dict_schema(
                {"key1": -5},
                "test_field",
                value_validators={"key1": validate_positive}
            )

        # Valid case
        result = validate_dict_schema(
            {"key1": 5},
            "test_field",
            value_validators={"key1": validate_positive}
        )
        assert result == {"key1": 5}

    def test_max_size_enforcement(self):
        """Test that max size constraint is enforced."""
        large_dict = {f"key{i}": f"value{i}" for i in range(10)}
        with pytest.raises(ValidationError, match="test_field exceeds maximum size of 5"):
            validate_dict_schema(large_dict, "test_field", max_size=5)


class TestValidateHypothesisDict:
    """Test the validate_hypothesis_dict function."""

    def test_valid_hypothesis(self):
        """Test validation of a valid hypothesis dictionary."""
        hypothesis = {
            "hypothesis": "Test hypothesis",
            "confidence": 0.7,
            "evidence": "Supporting evidence"
        }
        result = validate_hypothesis_dict(hypothesis, "test_field")
        assert result["hypothesis"] == "Test hypothesis"
        assert result["confidence"] == 0.7
        assert result["evidence"] == "Supporting evidence"

    def test_missing_required_keys(self):
        """Test that missing required keys raise ValidationError."""
        with pytest.raises(ValidationError, match="missing required key: hypothesis"):
            validate_hypothesis_dict({"confidence": 0.7}, "test_field")

    def test_invalid_confidence_type(self):
        """Test that invalid confidence types raise ValidationError."""
        with pytest.raises(ValidationError, match="must be numeric"):
            validate_hypothesis_dict(
                {"hypothesis": "Test", "confidence": "not_numeric"},
                "test_field"
            )

    def test_hypothesis_string_trimming(self):
        """Test that hypothesis strings are trimmed."""
        hypothesis = {
            "hypothesis": "  Test hypothesis  ",
            "confidence": 0.7
        }
        result = validate_hypothesis_dict(hypothesis, "test_field")
        assert result["hypothesis"] == "Test hypothesis"

    def test_index_in_error_messages(self):
        """Test that index is included in error messages."""
        hypothesis = {"confidence": 0.7}  # Missing hypothesis
        with pytest.raises(ValidationError, match="test_field\\[5\\] missing required key"):
            validate_hypothesis_dict(hypothesis, "test_field", index=5)


class TestValidateConfidenceValue:
    """Test the validate_confidence_value function."""

    def test_valid_float_confidence(self):
        """Test validation of valid float confidence values."""
        result = validate_confidence_value(0.75)
        assert result == 0.75

    def test_valid_int_confidence(self):
        """Test validation of valid integer confidence values."""
        result = validate_confidence_value(1)
        assert result == 1.0

    def test_confidence_clamping_high(self):
        """Test that confidence values are clamped to maximum."""
        result = validate_confidence_value(1.5)
        assert result == 1.0

    def test_confidence_clamping_low(self):
        """Test that confidence values are clamped to minimum."""
        result = validate_confidence_value(-0.5)
        assert result == 0.0

    def test_invalid_confidence_type(self):
        """Test that invalid confidence types raise ValidationError."""
        with pytest.raises(ValidationError, match="Confidence value.*contains invalid characters"):
            validate_confidence_value("not_numeric")


class TestValidateHypothesesList:
    """Test the validate_hypotheses_list function."""

    def test_valid_hypotheses_list(self):
        """Test validation of a valid hypotheses list."""
        hypotheses = [
            {"hypothesis": "Test 1", "confidence": 0.7},
            {"hypothesis": "Test 2", "confidence": 0.5}
        ]
        result = validate_hypotheses_list(hypotheses, "test_field")
        assert len(result) == 2
        assert result[0]["hypothesis"] == "Test 1"
        assert result[1]["confidence"] == 0.5

    def test_none_value(self):
        """Test that None values are handled correctly."""
        result = validate_hypotheses_list(None, "test_field")
        assert result is None

    def test_empty_list_error(self):
        """Test that empty lists raise ValidationError."""
        with pytest.raises(ValidationError, match="test_field cannot be empty"):
            validate_hypotheses_list([], "test_field")

    def test_non_list_input(self):
        """Test that non-list inputs raise ValidationError."""
        with pytest.raises(ValidationError, match="test_field must be a list"):
            validate_hypotheses_list("not_a_list", "test_field")

    def test_invalid_hypothesis_in_list(self):
        """Test that invalid hypotheses in the list raise ValidationError."""
        hypotheses = [
            {"hypothesis": "Valid", "confidence": 0.7},
            {"invalid": "structure"}  # Missing required fields
        ]
        with pytest.raises(ValidationError, match="test_field\\[1\\]"):
            validate_hypotheses_list(hypotheses, "test_field")

    def test_max_hypotheses_enforcement(self):
        """Test that max hypotheses constraint is enforced."""
        hypotheses = [
            {"hypothesis": f"Test {i}", "confidence": 0.5}
            for i in range(5)
        ]
        with pytest.raises(ValidationError, match="test_field exceeds maximum of 3"):
            validate_hypotheses_list(hypotheses, "test_field", max_hypotheses=3)


class TestValidateMetadataDict:
    """Test the validate_metadata_dict function."""

    def test_valid_metadata(self):
        """Test validation of valid metadata dictionary."""
        metadata = {
            "string_key": "string_value",
            "int_key": 42,
            "float_key": 3.14,
            "bool_key": True,
            "list_key": ["item1", "item2"],
            "dict_key": {"nested": "value"}
        }
        result = validate_metadata_dict(metadata, "test_field")
        assert result == metadata

    def test_none_value(self):
        """Test that None values are handled correctly."""
        result = validate_metadata_dict(None, "test_field")
        assert result is None

    def test_non_dict_input(self):
        """Test that non-dict inputs raise ValidationError."""
        with pytest.raises(ValidationError, match="test_field must be a dictionary"):
            validate_metadata_dict("not_a_dict", "test_field")

    def test_string_key_validation(self):
        """Test that keys must be strings."""
        with pytest.raises(ValidationError, match="test_field keys must be strings"):
            validate_metadata_dict({123: "value"}, "test_field")

    def test_key_pattern_validation(self):
        """Test that key patterns are validated correctly."""
        metadata = {"valid_key": "value", "invalid-key": "value"}
        with pytest.raises(ValidationError, match="key 'invalid-key' does not match allowed pattern"):
            validate_metadata_dict(metadata, "test_field", allowed_key_pattern=r"^[a-z_]+$")

    def test_string_length_validation(self):
        """Test that string values have length limits."""
        long_string = "x" * 2000
        with pytest.raises(ValidationError, match="string exceeds maximum length of 1000"):
            validate_metadata_dict({"key": long_string}, "test_field", max_string_length=1000)

    def test_list_size_validation(self):
        """Test that list values have size limits."""
        large_list = list(range(200))
        with pytest.raises(ValidationError, match="list exceeds maximum size of 100"):
            validate_metadata_dict({"key": large_list}, "test_field")

    def test_dict_size_validation(self):
        """Test that nested dict values have size limits."""
        large_dict = {f"key{i}": f"value{i}" for i in range(30)}
        with pytest.raises(ValidationError, match="dictionary exceeds maximum size of 20"):
            validate_metadata_dict({"key": large_dict}, "test_field")

    def test_unsupported_value_types(self):
        """Test that unsupported value types raise ValidationError."""
        metadata = {"key": set([1, 2, 3])}  # Sets are not supported
        with pytest.raises(ValidationError, match="has unsupported type set"):
            validate_metadata_dict(metadata, "test_field")

    def test_max_size_enforcement(self):
        """Test that max size constraint is enforced."""
        large_metadata = {f"key{i}": f"value{i}" for i in range(100)}
        with pytest.raises(ValidationError, match="test_field exceeds maximum size of 50"):
            validate_metadata_dict(large_metadata, "test_field", max_size=50)


class TestValidationIntegration:
    """Integration tests for validation functions."""

    def test_chain_of_thought_validation_scenarios(self):
        """Test validation scenarios relevant to chain_of_thought_step function."""
        # Valid assumptions and metadata
        assumptions = ["assumption1", "assumption2"]
        metadata = {"source": "test", "confidence": 0.8}

        validated_assumptions = validate_string_list(assumptions, "assumptions", max_length=50)
        validated_metadata = validate_metadata_dict(metadata, "metadata", max_size=20)

        assert validated_assumptions == assumptions
        assert validated_metadata == metadata

    def test_abductive_validation_scenarios(self):
        """Test validation scenarios relevant to abductive reasoning functions."""
        # Valid observations
        observations = ["observation1", "observation2", "observation3"]
        validated_observations = validate_string_list(observations, "observations", max_length=100)
        assert validated_observations == observations

        # Valid hypotheses
        hypotheses = [
            {"hypothesis": "Test hypothesis 1", "confidence": 0.7},
            {"hypothesis": "Test hypothesis 2", "confidence": 0.5, "evidence": "some evidence"}
        ]
        validated_hypotheses = validate_hypotheses_list(hypotheses, "hypotheses", max_hypotheses=50)
        assert len(validated_hypotheses) == 2
        assert all("hypothesis" in h and "confidence" in h for h in validated_hypotheses)

    def test_error_propagation(self):
        """Test that validation errors propagate correctly with descriptive messages."""
        with pytest.raises(ValidationError) as exc_info:
            validate_string_list([123, "valid"], "test_field")

        assert "test_field[0] must be a string" in str(exc_info.value)
        assert "got int" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__])