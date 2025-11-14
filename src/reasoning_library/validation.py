"""
Input validation utilities for complex parameter types.

This module provides reusable validation functions for complex data structures
used in public APIs, ensuring robust input validation and preventing
type-related security vulnerabilities.
"""

import inspect
from typing import Any, Callable, Dict, List, Optional, Union, TypedDict

import numpy as np

# For Python < 3.11 compatibility, we'll use total=False to make fields optional
# instead of using NotRequired

import re
from .exceptions import ValidationError


# TypedDict definitions for type-safe data structures
class Hypothesis(TypedDict, total=False):
    """Type-safe representation of a hypothesis with confidence scoring."""
    hypothesis: str
    confidence: Union[int, float, str, None]
    evidence: str
    coverage: Union[int, float]
    simplicity: Union[int, float]
    specificity: Union[int, float]


class ToolParameter(TypedDict, total=True):
    """Type-safe representation of a tool parameter specification."""
    name: str
    type: str
    description: str
    required: bool


class ToolSpecification(TypedDict, total=True):
    """Type-safe representation of a tool specification."""
    name: str
    description: str
    parameters: Dict[str, ToolParameter]


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
) -> Hypothesis:
    """
    Validate a single hypothesis dictionary structure.

    Args:
        hypothesis: The hypothesis dictionary to validate
        field_name: Name of the field for error messages
        index: Index of the hypothesis in a list (for error messages)

    Returns:
        Validated hypothesis as type-safe Hypothesis TypedDict

    Raises:
        ValidationError: If validation fails
    """
    if hypothesis is None:
        prefix = f"{field_name}[{index}]" if index is not None else field_name
        raise ValidationError(f"{prefix} cannot be None")

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
        confidence: The confidence value to validate (int, float, or str)

    Returns:
        float: Clamped confidence value

    Raises:
        ValidationError: If confidence is not numeric or contains dangerous values
    """
    # Handle None
    if confidence is None:
        raise ValidationError("Confidence value cannot be None")

    # Handle string inputs with secure validation
    if isinstance(confidence, str):
        return _validate_string_confidence(confidence)

    # Handle numeric inputs
    if not isinstance(confidence, (int, float)):
        raise ValidationError(f"Confidence value '{confidence}' must be numeric (int, float, or str), got {type(confidence).__name__}")

    if isinstance(confidence, float):
        if confidence != confidence:  # NaN check
            raise ValidationError("Confidence cannot be NaN")
        if confidence in (float('inf'), float('-inf')):
            raise ValidationError("Confidence cannot be infinite")

    return max(0.0, min(1.0, float(confidence)))


def _validate_string_confidence(confidence_str: str) -> float:
    """
    Securely validate a string confidence value and convert to float.

    Args:
        confidence_str: The string confidence value to validate

    Returns:
        float: Validated and clamped confidence value

    Raises:
        ValidationError: If string contains invalid or dangerous content
    """
    import re

    # Remove whitespace but check for empty/whitespace-only strings
    trimmed = confidence_str.strip()
    if not trimmed:
        raise ValidationError("Confidence value cannot be empty or whitespace-only")

    # Check for dangerous patterns that could cause type coercion issues
    dangerous_patterns = [
        r'^[nN][aA][nN]$',                    # nan, NaN, NAN
        r'^[iI][nN][fF]$',                    # inf, Inf, INF
        r'^-[iI][nN][fF]$',                   # -inf, -Inf
        r'^[+-]?\d*[eE][+-]?\d+$',            # scientific notation like 1e10, 1e-10
        r'^0[xX][0-9a-fA-F]+$',               # hexadecimal notation
        r'^0[bB][01]+$',                      # binary notation
        r'^0[oO][0-7]+$',                     # octal notation
    ]

    # Check for dangerous content in the string
    for pattern in dangerous_patterns:
        if re.match(pattern, trimmed):
            raise ValidationError(f"Confidence value '{confidence_str}' contains invalid format or dangerous content")

    # Check for invalid characters (anything except digits, decimal point, and leading sign)
    if re.search(r'[^\d.\-+]', trimmed):
        raise ValidationError(f"Confidence value '{confidence_str}' contains invalid characters")

    # Strict decimal format validation: optional sign, digits, optional decimal point and more digits
    decimal_pattern = r'^[+-]?(\d+(\.\d*)?|\.\d+)$'
    if not re.match(decimal_pattern, trimmed):
        raise ValidationError(f"Confidence value '{confidence_str}' must be a valid decimal number")

    try:
        # Convert to float safely
        confidence_float = float(trimmed)

        # Check for NaN and infinity that might slip through
        if confidence_float != confidence_float:  # NaN check
            raise ValidationError(f"Confidence value '{confidence_str}' resulted in NaN")

        if confidence_float in (float('inf'), float('-inf')):
            raise ValidationError(f"Confidence value '{confidence_str}' resulted in infinite value")

        # Clamp to valid range [0.0, 1.0]
        return max(0.0, min(1.0, confidence_float))

    except (ValueError, OverflowError) as e:
        raise ValidationError(f"Confidence value '{confidence_str}' cannot be converted to a valid number: {e}")


def validate_hypotheses_list(
    hypotheses: Optional[List[Dict[str, Any]]],
    field_name: str,
    max_hypotheses: Optional[int] = None
) -> Optional[List[Hypothesis]]:
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


def validate_parameters(**validators) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
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


# ===== TYPE VALIDATION FOR ARITHMETIC OPERATIONS =====

def validate_numeric_sequence(sequence: Any, param_name: str = "sequence") -> np.ndarray:
    """
    Validate that input is a numeric sequence suitable for arithmetic operations.

    Args:
        sequence: Input sequence to validate
        param_name: Name of the parameter for error messages

    Returns:
        np.ndarray: Validated numeric array

    Raises:
        ValidationError: If sequence is invalid
    """
    if sequence is None:
        raise ValidationError(f"{param_name} cannot be None")

    # Convert to numpy array for type checking
    try:
        if isinstance(sequence, (list, tuple)):
            array = np.array(sequence, dtype=float)
        elif isinstance(sequence, np.ndarray):
            array = sequence.astype(float, copy=False)
        else:
            raise ValidationError(f"{param_name} must be a list, tuple, or numpy array, got {type(sequence).__name__}")

    except (ValueError, TypeError) as e:
        raise ValidationError(f"{param_name} contains non-numeric values: {str(e)}")

    # Check for NaN or infinite values
    if np.any(np.isnan(array)):
        raise ValidationError(f"{param_name} cannot contain NaN values")

    if np.any(np.isinf(array)):
        raise ValidationError(f"{param_name} cannot contain infinite values")

    if len(array) == 0:
        raise ValidationError(f"{param_name} cannot be empty")

    return array


def validate_numeric_value(value: Any, param_name: str = "value", allow_float: bool = True, allow_int: bool = True) -> float:
    """
    Validate that input is a numeric value suitable for arithmetic operations.

    Args:
        value: Input value to validate
        param_name: Name of the parameter for error messages
        allow_float: Whether to allow float values
        allow_int: Whether to allow int values

    Returns:
        float: Validated numeric value

    Raises:
        ValidationError: If value is invalid
    """
    if value is None:
        raise ValidationError(f"{param_name} cannot be None")

    # ID-006: Explicitly exclude boolean values to prevent type coercion
    # In Python, bool is a subclass of int, so isinstance(True, int) returns True
    if isinstance(value, bool):
        raise ValidationError(f"{param_name} cannot be boolean, got {type(value).__name__}")

    if not isinstance(value, (int, float, np.integer, np.floating)):
        raise ValidationError(f"{param_name} must be numeric, got {type(value).__name__}")

    # Check type constraints
    if isinstance(value, float) and not allow_float:
        raise ValidationError(f"{param_name} cannot be a float")

    if isinstance(value, int) and not allow_int:
        raise ValidationError(f"{param_name} cannot be an integer")

    # Convert to float and check for special values
    float_value = float(value)

    if np.isnan(float_value):
        raise ValidationError(f"{param_name} cannot be NaN")

    if np.isinf(float_value):
        raise ValidationError(f"{param_name} cannot be infinite")

    return float_value


def validate_positive_numeric(value: Any, param_name: str = "value") -> float:
    """
    Validate that input is a positive numeric value.

    Args:
        value: Input value to validate
        param_name: Name of the parameter for error messages

    Returns:
        float: Validated positive numeric value

    Raises:
        ValidationError: If value is invalid or not positive
    """
    validated_value = validate_numeric_value(value, param_name)

    if validated_value <= 0:
        raise ValidationError(f"{param_name} must be positive, got {validated_value}")

    return validated_value


def validate_confidence_range(confidence: Any, param_name: str = "confidence") -> float:
    """
    Validate that input is a confidence value in range [0.0, 1.0].

    Args:
        confidence: Input confidence to validate
        param_name: Name of the parameter for error messages

    Returns:
        float: Validated confidence value

    Raises:
        ValidationError: If confidence is invalid or out of range
    """
    validated_value = validate_numeric_value(confidence, param_name)

    if not (0.0 <= validated_value <= 1.0):
        raise ValidationError(f"{param_name} must be between 0.0 and 1.0, got {validated_value}")

    return validated_value


def validate_sequence_length(length: Any, param_name: str = "length") -> int:
    """
    Validate that input is a valid sequence length (positive integer).

    Args:
        length: Input length to validate
        param_name: Name of the parameter for error messages

    Returns:
        int: Validated length

    Raises:
        ValidationError: If length is invalid
    """
    if length is None:
        raise ValidationError(f"{param_name} cannot be None")

    if not isinstance(length, (int, np.integer)):
        raise ValidationError(f"{param_name} must be an integer, got {type(length).__name__}")

    int_length = int(length)

    if int_length <= 0:
        raise ValidationError(f"{param_name} must be positive, got {int_length}")

    if int_length > 1000000:  # Reasonable upper limit to prevent DoS
        raise ValidationError(f"{param_name} is too large: {int_length}. Maximum allowed: 1000000")

    return int_length


def safe_divide(numerator: Any, denominator: Any, param_name: str = "result", default_value: float = 0.0) -> float:
    """
    Safely perform division with type validation and zero-division protection.

    Args:
        numerator: Numerator value
        denominator: Denominator value
        param_name: Name of the parameter for error messages
        default_value: Value to return if denominator is zero

    Returns:
        float: Result of division or default_value

    Raises:
        ValidationError: If inputs are invalid numeric types
    """
    # ID-006: Perform strict type validation and don't silently accept invalid types
    num = validate_numeric_value(numerator, f"{param_name}_numerator")
    den = validate_numeric_value(denominator, f"{param_name}_denominator")

    # Check for zero or near-zero denominator and return default value only in this case
    if abs(den) < 1e-10:  # Check for near-zero denominator
        return default_value

    return num / den


def safe_array_operation(operation_func: callable, array: Any, *args, **kwargs) -> np.ndarray:
    """
    Safely perform numpy array operations with type validation.

    Args:
        operation_func: Function to apply to the array
        array: Input array
        *args: Additional arguments for operation_func
        **kwargs: Additional keyword arguments for operation_func

    Returns:
        np.ndarray: Result of operation

    Raises:
        ValidationError: If array is invalid or operation fails
    """
    # Validate input array
    validated_array = validate_numeric_sequence(array)

    try:
        result = operation_func(validated_array, *args, **kwargs)

        # Validate result is also numeric
        if isinstance(result, np.ndarray):
            if np.any(np.isnan(result)) or np.any(np.isinf(result)):
                raise ValidationError("Array operation produced NaN or infinite values")

        return result

    except Exception as e:
        raise ValidationError(f"Array operation failed: {str(e)}")


def validate_arithmetic_inputs(*arrays, **scalars) -> None:
    """
    Validate multiple arrays and scalars for arithmetic operations.

    Args:
        *arrays: Variable number of arrays to validate
        **scalars: Variable number of scalars to validate (name=value)

    Raises:
        ValidationError: If any input is invalid
    """
    # Validate all arrays
    for i, array in enumerate(arrays):
        validate_numeric_sequence(array, f"array_{i+1}")

    # Validate all scalars
    for name, value in scalars.items():
        validate_numeric_value(value, name)


# Decorator for automatic type validation of arithmetic functions
def validate_arithmetic_operation(*array_params: str, **scalar_params: str):
    """
    Decorator to automatically validate arithmetic function parameters.

    Args:
        *array_params: Names of parameters that should be numeric arrays
        **scalar_params: Names of parameters that should be numeric scalars

    Usage:
        @validate_arithmetic_operation('sequence1', 'sequence2', base_confidence='scalar')
        def my_function(sequence1, sequence2, base_confidence=0.5):
            return sequence1 + sequence2 * base_confidence
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Get function signature
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Validate array parameters
            for param_name in array_params:
                if param_name in bound_args.arguments:
                    validate_numeric_sequence(
                        bound_args.arguments[param_name],
                        param_name
                    )

            # Validate scalar parameters
            for param_name, param_type in scalar_params.items():
                if param_name in bound_args.arguments:
                    if param_type == 'confidence':
                        validate_confidence_range(
                            bound_args.arguments[param_name],
                            param_name
                        )
                    elif param_type == 'positive':
                        validate_positive_numeric(
                            bound_args.arguments[param_name],
                            param_name
                        )
                    else:
                        validate_numeric_value(
                            bound_args.arguments[param_name],
                            param_name
                        )

            # Call the original function
            return func(*args, **kwargs)

        return wrapper
    return decorator