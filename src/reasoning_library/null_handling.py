"""
Null/None handling utilities for consistent patterns across the reasoning library.

This module provides standardized patterns for representing "no value" scenarios
and ensures consistent handling of None, empty strings, and empty collections.
"""

from typing import Any, List, Dict, Optional, Callable, TypeVar, Union, cast
from functools import wraps

# Type variables for generic functions
T = TypeVar('T')
U = TypeVar('U')

NO_VALUE = None
EMPTY_STRING = ""
EMPTY_LIST: List[Any] = []
EMPTY_DICT: Dict[str, Any] = {}


def safe_none_coalesce(
    value: Optional[T],
    default: T,
    converter: Optional[Callable[[T], U]] = None
) -> Union[T, U]:
    """
    Safely coalesce None values to defaults with optional conversion.

    This function provides type-safe null handling by preserving type information
    through generic type parameters.

    Type Parameters:
        T: The type of the input value and default
        U: The type of the converted output (if converter is provided)

    Args:
        value: The optional value to check (None or type T)
        default: Default value of type T to use if value is None
        converter: Optional converter function from T to U

    Returns:
        Either the original value (T), converted value (U), or default (T)
        - If value is None: returns default (T)
        - If converter provided and value is not None: returns converter(value) (U)
        - Otherwise: returns value (T)
    """
    if value is None:
        return default

    if converter is not None:
        try:
            return converter(value)
        except (ValueError, TypeError):
            return default

    return value


def safe_list_coalesce(value: Optional[List[Any]]) -> List[Any]:
    """
    Coalesce None to empty list, ensuring list type safety.

    Args:
        value: Optional list value

    Returns:
        List value (empty list if None)
    """
    if value is None:
        return []

    if isinstance(value, list):
        return value

    if hasattr(value, '__iter__') and not isinstance(value, (str, bytes)):
        try:
            return list(value)
        except (TypeError, ValueError):
            return []

    # Invalid type - return empty list as fallback
    return []


def safe_dict_coalesce(value: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Coalesce None to empty dict, ensuring dict type safety.

    Args:
        value: Optional dict value

    Returns:
        Dict value (empty dict if None)
    """
    if value is None:
        return {}

    if not isinstance(value, dict):
        try:
            return dict(value)
        except (TypeError, ValueError):
            return {}

    return value


def safe_string_coalesce(value: Optional[str]) -> str:
    """
    Coalesce None to empty string, ensuring string type safety.

    Args:
        value: Optional string value

    Returns:
        String value (empty string if None)
    """
    if value is None:
        return ""

    if not isinstance(value, str):
        try:
            return str(value)
        except (ValueError, TypeError):
            return ""

    return value


def normalize_none_return(value: Any, expected_type: type[T]) -> T:
    """
    Normalize return values to maintain consistent None patterns.

    Type Parameters:
        T: The expected return type

    Args:
        value: The value to normalize
        expected_type: The expected return type (type[T])

    Returns:
        Normalized value of type T with consistent null patterns
    """
    # Handle None values based on expected type
    if value is None:
        if expected_type == list:
            return EMPTY_LIST  # type: ignore[return-value]
        elif expected_type == dict:
            return EMPTY_DICT  # type: ignore[return-value]
        elif expected_type == str:
            return EMPTY_STRING  # type: ignore[return-value]
        else:
            return cast(T, NO_VALUE)

    # Handle boolean values
    if expected_type == bool and isinstance(value, bool):
        return value  # type: ignore[return-value]

    # Handle collection types with appropriate coalescing
    if expected_type == list:
        return safe_list_coalesce(value)  # type: ignore[return-value]
    elif expected_type == dict:
        return safe_dict_coalesce(value)  # type: ignore[return-value]
    elif expected_type == str:
        return safe_string_coalesce(value)  # type: ignore[return-value]

    # For other types, ensure type compatibility
    if isinstance(value, expected_type):
        return value  # type: ignore[return-value]

    # Type conversion fallback - may raise TypeError if conversion fails
    return expected_type(value)  # type: ignore[call-arg]


def handle_optional_params(**kwargs: Any) -> Dict[str, Any]:
    """
    Standardize optional parameter handling across the codebase.

    Args:
        **kwargs: Keyword arguments to normalize

    Returns:
        Dictionary with normalized optional parameters
    """
    normalized = {}

    for key, value in kwargs.items():
        if key.endswith('_list') or 'list' in key.lower() or key == 'assumptions':
            normalized[key] = safe_list_coalesce(value)
        elif key.endswith('_dict') or 'dict' in key.lower() or 'metadata' in key.lower():
            normalized[key] = safe_dict_coalesce(value)
        elif key.endswith('_string') or 'string' in key.lower() or 'text' in key.lower() or 'evidence' in key.lower():
            normalized[key] = safe_string_coalesce(value)
        else:
            # For generic optional parameters, preserve None unless specifically empty
            normalized[key] = value

    return normalized


def with_null_safety(expected_return_type: type = Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator for standardizing null handling in function returns.

    Args:
        expected_return_type: Expected return type for normalization

    Returns:
        Decorated function with standardized null handling
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                result = func(*args, **kwargs)
                return normalize_none_return(result, expected_return_type)
            except Exception:
                if expected_return_type == bool:
                    return NO_VALUE
                elif expected_return_type == list:
                    return EMPTY_LIST
                elif expected_return_type == dict:
                    return EMPTY_DICT
                elif expected_return_type == str:
                    return EMPTY_STRING
                else:
                    return NO_VALUE
        return wrapper
    return decorator


def init_optional_bool(default_value: Optional[bool] = None) -> Optional[bool]:
    """Initialize optional boolean with consistent pattern."""
    return default_value


def init_optional_string(default_value: Optional[str] = None) -> str:
    """Initialize optional string with consistent pattern."""
    return safe_string_coalesce(default_value)


def init_optional_list(default_value: Optional[List[Any]] = None) -> List[Any]:
    """Initialize optional list with consistent pattern."""
    return safe_list_coalesce(default_value)


def init_optional_dict(default_value: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Initialize optional dict with consistent pattern."""
    return safe_dict_coalesce(default_value)