"""
Null/None handling utilities for consistent patterns across the reasoning library.

This module provides standardized patterns for representing "no value" scenarios
and ensures consistent handling of None, empty strings, and empty collections.
"""

from typing import Any, List, Dict, Optional, Callable, TypeVar, Union, cast
from functools import wraps
import logging
import re

# ARCH-ID003-001: Import SecureLogger for mandatory logging sanitization
try:
    from .sanitization import SecureLogger
except ImportError:
    # Fallback for when sanitization module is not available
    SecureLogger = None

# Type variables for generic functions
T = TypeVar('T')
U = TypeVar('U')

# Module logger for exception handling
logger = logging.getLogger(__name__)

NO_VALUE = None
EMPTY_STRING = ""
EMPTY_LIST: List[Any] = []
EMPTY_DICT: Dict[str, Any] = {}


def _sanitize_exception_message(func_name: str, exception_type: str, exception_msg: str) -> str:
    """
    Create a secure exception log message without sensitive system information.

    SECURITY NOTE: This function removes potentially sensitive information from
    exception messages while preserving useful debugging information for developers.

    Args:
        func_name: Name of the function where the exception occurred
        exception_type: Type of exception (e.g., 'KeyError', 'ValueError')
        exception_msg: Original exception message

    Returns:
        Sanitized exception message safe for logging in production
    """
    # Remove file paths that might leak system architecture
    sanitized_msg = exception_msg

    # Remove user directory paths first (before file path replacement)
    sanitized_msg = re.sub(r'/Users/[^/\s]+', '[USER_DIR]', sanitized_msg)
    sanitized_msg = re.sub(r'/home/[^/\s]+', '[USER_DIR]', sanitized_msg)

    # Remove absolute paths (Unix and Windows)
    sanitized_msg = re.sub(r'/[a-zA-Z0-9_/-]+\.(py|js|txt|json)', '[FILE]', sanitized_msg)
    sanitized_msg = re.sub(r'[A-Za-z]:\\[a-zA-Z0-9_/-\\]+\.[a-zA-Z]+', '[FILE]', sanitized_msg)

    # Remove IP addresses and network information
    sanitized_msg = re.sub(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '[IP]', sanitized_msg)

    # Remove potential passwords, tokens, or API keys
    sanitized_msg = re.sub(r'[\'\"]?(?:password|token|key|secret)[\'\"]?\s*[:=]\s*[\'\"]?[^\s\'\"]{8,}[\'\"]?', '[REDACTED]', sanitized_msg, flags=re.IGNORECASE)

    # Remove overly long messages that might contain sensitive data
    if len(sanitized_msg) > 200:
        sanitized_msg = sanitized_msg[:200] + '... [TRUNCATED]'

    # Remove newlines and control characters
    sanitized_msg = re.sub(r'[\r\n\t]', ' ', sanitized_msg)

    # Construct the secure message
    if sanitized_msg.strip():
        return f"{func_name}: {exception_type}: {sanitized_msg}"
    else:
        return f"{func_name}: {exception_type}"


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
            except (ValueError, TypeError, AttributeError, KeyError) as e:
                # SECURE LOGGING: Only log sanitized exception information
                # SECURITY FIX: Removed exc_info=True to prevent information disclosure
                # of stack traces, file paths, and system architecture details
                safe_message = _sanitize_exception_message(func.__name__, type(e).__name__, str(e))
                # ARCH-ID003-001: Use SecureLogger for mandatory sanitization
                if SecureLogger:
                    secure_logger = SecureLogger('null_handling')
                    secure_logger.debug(f"Business exception handled: {safe_message}")
                else:
                    # Fallback to standard logging
                    logger.debug(f"Business exception handled: {safe_message}")
                # Return appropriate empty value based on expected type
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
            # System exceptions like MemoryError, SystemError, KeyboardInterrupt, ImportError,
            # RuntimeError, etc. will propagate correctly (not caught)
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