"""
Decorators for the reasoning library.

This module contains the curry and tool_spec decorators for enhancing functions
with currying capabilities and tool specification generation.
"""

import inspect
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

from .mathematical_detection import _detect_mathematical_reasoning
from .tool_registry import ENHANCED_TOOL_REGISTRY, TOOL_REGISTRY, ToolMetadata
from .type_utils import get_json_schema_type


def curry(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    A currying decorator for functions that properly handles required vs optional parameters.
    Allows functions to be called with fewer arguments than they expect,
    returning a new function that takes the remaining arguments.
    """
    sig = inspect.signature(func)

    @wraps(func)
    def curried(*args: Any, **kwargs: Any) -> Any:
        try:
            # Try to bind the arguments - this will fail if we don't have enough required args
            bound = sig.bind(*args, **kwargs)
        except TypeError:
            # If binding fails (insufficient args), return a curried function
            return lambda *args2, **kwargs2: curried(
                *(args + args2), **(kwargs | kwargs2)
            )

        # If we get here, we have all required arguments - execute the function
        # Any TypeError from the function execution should be propagated, not caught
        return func(*args, **kwargs)

    return curried


def tool_spec(
    func: Optional[Callable[..., Any]] = None,
    *,
    mathematical_basis: Optional[str] = None,
    confidence_factors: Optional[List[str]] = None,
    confidence_formula: Optional[str] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Enhanced decorator to attach a JSON Schema tool specification to a function.
    The spec is derived from the function's signature and docstring.

    This decorator supports a hybrid model for metadata:
    1.  **Explicit Declaration (Preferred):** Pass metadata directly as arguments
        (e.g., `mathematical_basis`, `confidence_factors`).
    2.  **Heuristic Fallback:** If no explicit arguments are provided, it falls back
        to `_detect_mathematical_reasoning` to infer metadata for backward compatibility.
    """

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return fn(*args, **kwargs)

        signature = inspect.signature(fn)
        parameters = {}
        required_params = []

        for name, param in signature.parameters.items():
            if name == "reasoning_chain":  # Exclude from tool spec
                continue

            param_type = (
                param.annotation
                if param.annotation is not inspect.Parameter.empty
                else Any
            )
            json_type = get_json_schema_type(param_type)

            param_info: Dict[str, Any] = {"type": json_type}
            if hasattr(param_type, "__origin__") and param_type.__origin__ is list:
                if hasattr(param_type, "__args__") and param_type.__args__:
                    param_info["items"] = {
                        "type": get_json_schema_type(param_type.__args__[0])
                    }

            parameters[name] = param_info

            if param.default is inspect.Parameter.empty:
                required_params.append(name)

        tool_specification = {
            "type": "function",
            "function": {
                "name": fn.__name__,
                "description": fn.__doc__.strip() if fn.__doc__ else "",
                "parameters": {
                    "type": "object",
                    "properties": parameters,
                    "required": required_params,
                },
            },
        }

        # Hybrid model: Prioritize explicit declaration, then fall back to heuristic detection
        is_mathematical = False
        confidence_doc = None
        # Initialize with explicit parameter or None
        final_mathematical_basis = mathematical_basis

        if confidence_factors:
            confidence_doc = (
                f"Confidence calculation based on: {', '.join(confidence_factors)}"
            )
            is_mathematical = True

        # If mathematical_basis is explicitly provided, this is mathematical reasoning
        if mathematical_basis:
            is_mathematical = True

        # Fallback to heuristic detection if explicit metadata is not provided
        if not is_mathematical and not final_mathematical_basis:
            (
                is_mathematical_heuristic,
                confidence_doc_heuristic,
                mathematical_basis_heuristic,
            ) = _detect_mathematical_reasoning(fn)
            if is_mathematical_heuristic:
                is_mathematical = True
                if not confidence_doc:
                    confidence_doc = confidence_doc_heuristic
                if not final_mathematical_basis:
                    final_mathematical_basis = mathematical_basis_heuristic

        metadata = ToolMetadata(
            confidence_documentation=confidence_doc,
            mathematical_basis=final_mathematical_basis,
            is_mathematical_reasoning=is_mathematical,
            confidence_formula=confidence_formula,
            confidence_factors=confidence_factors,
            platform_notes={},
        )

        ENHANCED_TOOL_REGISTRY.append(
            {"function": wrapper, "tool_spec": tool_specification, "metadata": metadata}
        )

        setattr(wrapper, "tool_spec", tool_specification)
        TOOL_REGISTRY.append(wrapper)

        return wrapper

    if func:
        return decorator(func)
    return decorator