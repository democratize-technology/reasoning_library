"""
Type utilities for JSON Schema mapping.

This module provides utilities for converting Python type hints to JSON Schema types,
handling Optional, List, Dict, and other complex types.
"""

from typing import Any, Union

# Type mapping for basic Python types to JSON Schema types
TYPE_MAP = {
    bool: "boolean",
    int: "integer",
    float: "number",
    str: "string",
    list: "array",
    dict: "object",
    Any: "object",  # Default for Any
}


def get_json_schema_type(py_type: Any) -> str:
    """
    Converts a Python type hint to a JSON Schema type string.
    Handles Optional and List types.
    """
    if hasattr(py_type, "__origin__"):
        if py_type.__origin__ is Union:  # Union types (including Optional)
            # Check if this is Optional[X] (Union[X, None])
            args = py_type.__args__
            if len(args) == 2 and type(None) in args:
                # This is Optional[X] - get the non-None type
                actual_type = args[0] if args[1] is type(None) else args[1]
                return get_json_schema_type(actual_type)
            # For other Union types, default to string
            return "string"
        elif py_type.__origin__ is list:  # List[X]
            return "array"
        elif py_type.__origin__ is dict:  # Dict[K, V]
            return "object"

    return TYPE_MAP.get(py_type, "string")  # Default to string if not found
