"""
Null/None handling utilities for consistent patterns across the reasoning library.

This module provides standardized patterns for representing "no value" scenarios
and ensures consistent handling of None, empty strings, and empty collections.
"""

from typing import Any, List, Dict, Optional, Callable
from functools import wraps

NO_VALUE = None
EMPTY_STRING = ""
EMPTY_LIST = []
EMPTY_DICT = {}


def safe_none_coalesce(value: Any, default: Any, converter: Optional[Callable[[Any], Any]] = None) -> Any:
    """
    Safely coalesce None values to defaults with optional conversion.

    Args:
        value: The value to check
        default: Default value if value is None
        converter: Optional converter function to apply to non-None values

    Returns:
        value converted and applied, or default if value is None
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


def normalize_none_return(value: Any, expected_type: type) -> Any:
    """
    Normalize return values to maintain consistent None patterns.

    Args:
        value: The value to normalize
        expected_type: The expected return type

    Returns:
        Normalized value (None for no result, properly typed for success)
    """
    if value is None:
        if expected_type == list:
            return EMPTY_LIST
        elif expected_type == dict:
            return EMPTY_DICT
        elif expected_type == str:
            return EMPTY_STRING
        else:
            return NO_VALUE

    if expected_type == bool and isinstance(value, bool):
        return value

    if expected_type == list:
        return safe_list_coalesce(value)
    elif expected_type == dict:
        return safe_dict_coalesce(value)
    elif expected_type == str:
        return safe_string_coalesce(value)

        return value


def handle_optional_params(**kwargs) -> Dict[str, Any]:
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


def with_null_safety(expected_return_type: type = Any):
    """
    Decorator for standardizing null handling in function returns.

    Args:
        expected_return_type: Expected return type for normalization

    Returns:
        Decorated function with standardized null handling
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
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