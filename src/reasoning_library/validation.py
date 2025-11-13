"""
Input validation utilities for complex parameter types.

This module provides reusable validation functions for complex data structures
used in public APIs, ensuring robust input validation and preventing
type-related security vulnerabilities.
"""

from typing import Any, Dict, List, Optional, Union
import re
from .exceptions import ValidationError


def validate_string_list(
    value: Optional[List[Any]],
    field_name: str,
    allow_empty: bool = True,
    max_length: Optional[int] = None,
    pattern: Optional[str] = None
) -> Optional[List[str]]:
    """
    Validate that a value is a list of strings with optional constraints.

    Args:
        value: The value to validate
        field_name: Name of the field for error messages
        allow_empty: Whether empty lists are allowed
        max_length: Maximum number of items allowed
        pattern: Regex pattern each string must match

    Returns:
        List[str] if validation passes

    Raises:
        ValidationError: If validation fails
    """
    if value is None:
        return None

    if not isinstance(value, list):
        raise ValidationError(f"{field_name} must be a list, got {type(value).__name__}")

    if not allow_empty and len(value) == 0:
        raise ValidationError(f"{field_name} cannot be empty")

    if max_length is not None and len(value) > max_length:
        raise ValidationError(f"{field_name} exceeds maximum length of {max_length}")

    validated_strings = []
    for i, item in enumerate(value):
        if not isinstance(item, str):
            raise ValidationError(f"{field_name}[{i}] must be a string, got {type(item).__name__}")

        if len(item.strip()) == 0:
            raise ValidationError(f"{field_name}[{i}] cannot be empty or whitespace")

        if pattern is not None:
            if not re.match(pattern, item):
                raise ValidationError(f"{field_name}[{i}] does not match required pattern")

        validated_strings.append(item.strip())

    return validated_strings


def validate_dict_schema(
    value: Optional[Dict[str, Any]],
    field_name: str,
    required_keys: Optional[List[str]] = None,
    optional_keys: Optional[List[str]] = None,
    key_types: Optional[Dict[str, type]] = None,
    value_validators: Optional[Dict[str, callable]] = None,
    allow_extra_keys: bool = True,
    max_size: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """
    Validate that a value matches a specific dictionary schema.

    Args:
        value: The value to validate
        field_name: Name of the field for error messages
        required_keys: List of required keys
        optional_keys: List of optional keys
        key_types: Dictionary mapping keys to expected types
        value_validators: Dictionary mapping keys to validation functions
        allow_extra_keys: Whether keys not in required/optional are allowed
        max_size: Maximum number of key-value pairs allowed

    Returns:
        Dict[str, Any] if validation passes

    Raises:
        ValidationError: If validation fails
    """
    if value is None:
        return None

    if not isinstance(value, dict):
        raise ValidationError(f"{field_name} must be a dictionary, got {type(value).__name__}")

    if max_size is not None and len(value) > max_size:
        raise ValidationError(f"{field_name} exceeds maximum size of {max_size} items")

    required_keys = required_keys or []
    optional_keys = optional_keys or []
    key_types = key_types or {}
    value_validators = value_validators or {}

    for key in required_keys:
        if key not in value:
            raise ValidationError(f"{field_name} missing required key: {key}")
    all_allowed_keys = set(required_keys + optional_keys)
    if not allow_extra_keys:
        for key in value:
            if key not in all_allowed_keys:
                raise ValidationError(f"{field_name} contains unexpected key: {key}")

  validated_dict = {}
    for key, val in value.items():
        if key in key_types:
            expected_type = key_types[key]
            if not isinstance(val, expected_type):
                type_name = (
                    expected_type.__name__ if hasattr(expected_type, '__name__')
                    else str(expected_type)
                )
                raise ValidationError(
                    f"{field_name}[{key}] must be of type {type_name}, "
                    f"got {type(val).__name__}"
                )

        # Apply custom validators
        if key in value_validators:
            validator = value_validators[key]
            try:
                validated_val = validator(val)
                validated_dict[key] = validated_val
            except Exception as e:
                raise ValidationError(f"{field_name}[{key}] validation failed: {str(e)}")
        else:
            validated_dict[key] = val

    return validated_dict


def validate_hypothesis_dict(
    hypothesis: Dict[str, Any],
    field_name: str,
    index: Optional[int] = None
) -> Dict[str, Any]:
    """
    Validate a single hypothesis dictionary structure.

    Args:
        hypothesis: The hypothesis dictionary to validate
        field_name: Name of the field for error messages
        index: Index of the hypothesis in a list (for error messages)

    Returns:
        Dict[str, Any] if validation passes

    Raises:
        ValidationError: If validation fails
    """
    prefix = f"{field_name}[{index}]" if index is not None else field_name

        def validate_confidence_with_index(confidence: Union[int, float, str, None]) -> float:
        from .abductive import _validate_confidence_value  # Import from abductive for consistent error messages
        return _validate_confidence_value(confidence, index)

    return validate_dict_schema(
        hypothesis,
        prefix,
        required_keys=["hypothesis", "confidence"],
        optional_keys=["evidence", "coverage", "simplicity", "specificity"],
        key_types={
            "hypothesis": str,
            "confidence": (int, float, str, type(None)),  # Allow str, None so value validator can handle it
            "evidence": str,
            "coverage": (int, float),
            "simplicity": (int, float),
            "specificity": (int, float)
        },
        value_validators={
            "hypothesis": lambda x: x.strip() if isinstance(x, str) else x,
            "confidence": validate_confidence_with_index
        }
    )


def validate_confidence_value(confidence: Union[int, float, str, None]) -> float:
    """
    Validate and clamp a confidence value to [0.0, 1.0] range.

    Args:
        confidence: The confidence value to validate

    Returns:
        float: Clamped confidence value

    Raises:
        ValidationError: If confidence is not numeric
    """
    if not isinstance(confidence, (int, float)):
        raise ValidationError(f"Confidence value '{confidence}' must be numeric (int or float), got {type(confidence).__name__}")

    if isinstance(confidence, float):
        if confidence != confidence:  # NaN check
            raise ValidationError(f"Confidence cannot be NaN")
        if confidence in (float('inf'), float('-inf')):
            raise ValidationError(f"Confidence cannot be infinite")

    return max(0.0, min(1.0, float(confidence)))


def validate_hypotheses_list(
    hypotheses: Optional[List[Dict[str, Any]]],
    field_name: str,
    max_hypotheses: Optional[int] = None
) -> Optional[List[Dict[str, Any]]]:
    """
    Validate a list of hypothesis dictionaries.

    Args:
        hypotheses: The list of hypotheses to validate
        field_name: Name of the field for error messages
        max_hypotheses: Maximum number of hypotheses allowed

    Returns:
        List[Dict[str, Any]] if validation passes

    Raises:
        ValidationError: If validation fails
    """
    if hypotheses is None:
        return None

    if not isinstance(hypotheses, list):
        raise ValidationError(f"{field_name} must be a list, got {type(hypotheses).__name__}")

    if len(hypotheses) == 0:
        raise ValidationError(f"{field_name} cannot be empty")

    if max_hypotheses is not None and len(hypotheses) > max_hypotheses:
        raise ValidationError(f"{field_name} exceeds maximum of {max_hypotheses} hypotheses")

    validated_hypotheses = []
    for i, hypothesis in enumerate(hypotheses):
        validated_hypothesis = validate_hypothesis_dict(hypothesis, field_name, i)
        validated_hypotheses.append(validated_hypothesis)

    return validated_hypotheses


def validate_metadata_dict(
    metadata: Optional[Dict[str, Any]],
    field_name: str,
    allowed_key_pattern: Optional[str] = None,
    max_size: int = 50,
    max_string_length: int = 1000
) -> Optional[Dict[str, Any]]:
    """
    Validate metadata dictionary with flexible structure but reasonable constraints.

    Args:
        metadata: The metadata dictionary to validate
        field_name: Name of the field for error messages
        allowed_key_pattern: Regex pattern for allowed keys (None = any key)
        max_size: Maximum number of key-value pairs
        max_string_length: Maximum length for string values

    Returns:
        Dict[str, Any] if validation passes

    Raises:
        ValidationError: If validation fails
    """
    if metadata is None:
        return None

    if not isinstance(metadata, dict):
        raise ValidationError(f"{field_name} must be a dictionary, got {type(metadata).__name__}")

    if len(metadata) > max_size:
        raise ValidationError(f"{field_name} exceeds maximum size of {max_size} items")

    validated_metadata = {}
    for key, value in metadata.items():
        # Validate key
        if not isinstance(key, str):
            raise ValidationError(f"{field_name} keys must be strings, got {type(key).__name__}")

        if allowed_key_pattern is not None:
            if not re.match(allowed_key_pattern, key):
                raise ValidationError(f"{field_name} key '{key}' does not match allowed pattern")

                if isinstance(value, str):
            if len(value) > max_string_length:
                raise ValidationError(f"{field_name}[{key}] string exceeds maximum length of {max_string_length}")
            validated_metadata[key] = value
        elif isinstance(value, (int, float, bool)):
            validated_metadata[key] = value
        elif isinstance(value, list):
            if len(value) > 100:  # Reasonable limit for list size
                raise ValidationError(f"{field_name}[{key}] list exceeds maximum size of 100 items")
            validated_metadata[key] = value
        elif isinstance(value, dict):
            if len(value) > 20:  # Reasonable limit for nested dict size
                raise ValidationError(f"{field_name}[{key}] dictionary exceeds maximum size of 20 items")
            validated_metadata[key] = value
        else:
            raise ValidationError(
                f"{field_name}[{key}] has unsupported type {type(value).__name__}. "
                f"Allowed types: str, int, float, bool, list, dict"
            )

    return validated_metadata


def validate_parameters(**validators):
    """
    Decorator to validate function parameters using provided validators.

    Args:
        **validators: Mapping of parameter names to validation functions

    Returns:
        Decorated function with parameter validation
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Get function signature to map positional args to parameter names
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Validate each parameter that has a validator
            for param_name, validator in validators.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    try:
                        validated_value = validator(value)
                        bound_args.arguments[param_name] = validated_value
                    except Exception as e:
                        raise ValidationError(f"Parameter '{param_name}' validation failed: {str(e)}")

            # Call function with validated arguments
            return func(*bound_args.args, **bound_args.kwargs)

        return wrapper
    return decorator