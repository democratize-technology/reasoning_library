"""
Core utilities for the reasoning library.
"""

import inspect
import re
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

# Security constants and compiled patterns
MAX_SOURCE_CODE_SIZE = 10000  # Prevent ReDoS attacks by limiting input size

# Pre-compiled regex patterns with ReDoS vulnerability fixes
# Using more specific patterns to avoid catastrophic backtracking
FACTOR_PATTERN = re.compile(
    r"(\w{0,30}(?:data_sufficiency|pattern_quality|complexity)_factor)[\s]{0,5}(?:\*|,|\+|\-|=)",
    re.IGNORECASE | re.MULTILINE,
)
COMMENT_PATTERN = re.compile(
    r"#\s*(?:Data|Pattern|Complexity)\s+([^#\n]+factor)", re.IGNORECASE | re.MULTILINE
)
EVIDENCE_PATTERN = re.compile(
    r'f?"[^"]*(?:confidence\s+based\s+on|factors?[\s:]*in)[^"]*([^"\.]+pattern[^"\.]*)',
    re.IGNORECASE | re.MULTILINE,
)
COMBINATION_PATTERN = re.compile(
    r"(\w{1,30}_factor)[\s]{0,10}\*[\s]{0,10}(\w{1,30}_factor)",
    re.IGNORECASE | re.MULTILINE,
)
CLEAN_FACTOR_PATTERN = re.compile(r"[()=\*]+", re.IGNORECASE)

# --- Enhanced Tool Registry ---

# Enhanced registry storing functions with rich metadata
ENHANCED_TOOL_REGISTRY: List[Dict[str, Any]] = []

# Legacy registry for backward compatibility
TOOL_REGISTRY: List[Callable[..., Any]] = []


@dataclass
class ToolMetadata:
    """Enhanced metadata for tool specifications."""

    confidence_documentation: Optional[str] = None
    mathematical_basis: Optional[str] = None
    platform_notes: Optional[Dict[str, str]] = field(default_factory=dict)
    is_mathematical_reasoning: bool = False
    confidence_formula: Optional[str] = None
    confidence_factors: Optional[List[str]] = field(default_factory=list)


def _detect_mathematical_reasoning(
    func: Callable[..., Any],
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Detect if a function performs mathematical reasoning and extract confidence documentation.

    Optimized to perform fast initial checks before expensive source code extraction.

    Returns:
        tuple: (is_mathematical, confidence_documentation, mathematical_basis)
    """
    # Check for mathematical reasoning indicators
    math_indicators = [
        "confidence",
        "probability",
        "statistical",
        "variance",
        "coefficient_of_variation",
        "geometric",
        "arithmetic",
        "progression",
        "pattern",
        "deductive",
        "inductive",
        "modus_ponens",
        "logical",
        "reasoning_chain",
    ]

    # Fast initial check using only docstring and function name
    docstring = func.__doc__ or ""
    func_name = getattr(func, "__name__", "")

    # Quick check without source code extraction
    has_math_indicators_in_docs = any(
        indicator in docstring.lower() or indicator in func_name.lower()
        for indicator in math_indicators
    )

    # If no mathematical indicators in docs/name, likely not mathematical
    if not has_math_indicators_in_docs:
        return False, None, None

    # Only extract source code if initial check suggests mathematical reasoning
    try:
        source_code = inspect.getsource(func) if hasattr(func, "__code__") else ""
    except (OSError, TypeError):
        # Handle dynamic functions, lambdas, and other edge cases gracefully
        source_code = ""

    # Prevent ReDoS attacks by limiting source code size
    if len(source_code) > MAX_SOURCE_CODE_SIZE:
        source_code = source_code[:MAX_SOURCE_CODE_SIZE]  # Truncate to safe size

    # Final check including source code
    is_mathematical = any(
        indicator in source_code.lower() or indicator in docstring.lower()
        for indicator in math_indicators
    )

    confidence_doc = None
    mathematical_basis = None

    if is_mathematical:
        # Extract confidence calculation patterns with improved semantic focus
        confidence_factors = []

        # Pattern 1: Extract confidence factor variable names using pre-compiled pattern
        factor_matches = FACTOR_PATTERN.findall(source_code)
        if factor_matches:
            confidence_factors.extend(
                [factor.replace("_", " ") for factor in factor_matches[:3]]
            )

        # Pattern 2: Extract meaningful descriptive comments using pre-compiled pattern
        comment_matches = COMMENT_PATTERN.findall(source_code)
        if comment_matches:
            confidence_factors.extend(
                [match.strip().lower() for match in comment_matches[:2]]
            )

        # Pattern 3: Extract from evidence strings with confidence calculations using pre-compiled pattern
        evidence_matches = EVIDENCE_PATTERN.findall(source_code)
        if evidence_matches:
            confidence_factors.extend([match.strip() for match in evidence_matches[:1]])

        # Pattern 4: Look for factor multiplication combinations using pre-compiled pattern
        combination_matches = COMBINATION_PATTERN.findall(source_code)
        if combination_matches and not confidence_factors:
            # If we haven't found factors yet, use the combination pattern
            factor_names = []
            for match in combination_matches[:2]:
                factor_names.extend(
                    [
                        factor.replace("_factor", "").replace("_", " ")
                        for factor in match
                    ]
                )
            confidence_factors.extend(list(set(factor_names)))  # Remove duplicates

        # Pattern 5: Extract from docstring confidence patterns
        if "confidence" in docstring.lower() and "based on" in docstring.lower():
            # Look for specific patterns in docstring
            if "pattern quality" in docstring.lower():
                confidence_factors.extend(["pattern quality"])
            if "pattern" in docstring.lower() and not confidence_factors:
                confidence_factors.extend(["pattern analysis"])

        # Create meaningful confidence documentation
        if confidence_factors:
            # Clean and deduplicate factors
            clean_factors = []
            seen = set()
            for factor in confidence_factors:
                clean_factor = factor.strip().lower()
                # Remove common code artifacts using pre-compiled pattern
                clean_factor = CLEAN_FACTOR_PATTERN.sub("", clean_factor).strip()
                if clean_factor and clean_factor not in seen and len(clean_factor) > 2:
                    clean_factors.append(clean_factor)
                    seen.add(clean_factor)

            if clean_factors:
                confidence_doc = (
                    f"Confidence calculation based on: {', '.join(clean_factors[:3])}"
                )

        # Extract mathematical basis from docstring or code
        if "arithmetic progression" in docstring.lower():
            mathematical_basis = "Arithmetic progression analysis with data sufficiency and pattern quality factors"
        elif "geometric progression" in docstring.lower():
            mathematical_basis = (
                "Geometric progression analysis with ratio consistency validation"
            )
        elif "modus ponens" in docstring.lower():
            mathematical_basis = (
                "Formal deductive logic using Modus Ponens inference rule"
            )
        elif "chain of thought" in docstring.lower():
            mathematical_basis = "Sequential reasoning with conservative confidence aggregation (minimum of step confidences)"

    return is_mathematical, confidence_doc, mathematical_basis


def _safe_copy_spec(tool_spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Safely copy tool specification with input validation to prevent prototype pollution.

    Args:
        tool_spec: Tool specification to copy

    Returns:
        Validated and safely copied tool specification

    Raises:
        ValueError: If tool specification is invalid or missing required fields
    """
    if not isinstance(tool_spec, dict):
        raise ValueError("Tool specification must be a dictionary")

    if "function" not in tool_spec:
        raise ValueError("Tool specification must contain 'function' key")

    if not isinstance(tool_spec["function"], dict):
        raise ValueError("Tool specification 'function' value must be a dictionary")

    # Whitelist of allowed top-level keys to prevent prototype pollution
    allowed_top_level_keys = {"type", "function"}

    # Whitelist of allowed function keys
    allowed_function_keys = {"name", "description", "parameters"}

    # Create safe copy with only whitelisted keys
    safe_spec = {}
    for key, value in tool_spec.items():
        if key in allowed_top_level_keys:
            if key == "function":
                # Safely copy function object with whitelisted keys only
                safe_function = {}
                for func_key, func_value in value.items():
                    if func_key in allowed_function_keys:
                        safe_function[func_key] = func_value
                safe_spec[key] = safe_function
            else:
                safe_spec[key] = value

    return safe_spec


def _openai_format(tool_spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert tool specification to OpenAI ChatCompletions API format.

    Args:
        tool_spec: Standard tool specification

    Returns:
        OpenAI-compatible tool specification
    """
    # Use safe copy to prevent prototype pollution
    safe_spec = _safe_copy_spec(tool_spec)
    return {
        "type": "function",
        "function": {
            "name": safe_spec["function"]["name"],
            "description": safe_spec["function"]["description"],
            "parameters": safe_spec["function"]["parameters"],
        },
    }


def _bedrock_format(tool_spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert tool specification to AWS Bedrock Converse API format.

    Args:
        tool_spec: Standard tool specification

    Returns:
        Bedrock-compatible tool specification
    """
    # Use safe copy to prevent prototype pollution
    safe_spec = _safe_copy_spec(tool_spec)
    return {
        "toolSpec": {
            "name": safe_spec["function"]["name"],
            "description": safe_spec["function"]["description"],
            "inputSchema": {"json": safe_spec["function"]["parameters"]},
        }
    }


def _enhance_description_with_confidence_docs(
    description: str, metadata: ToolMetadata
) -> str:
    """
    Enhance tool description with confidence documentation for mathematical reasoning functions.

    Args:
        description: Original function description
        metadata: Tool metadata containing confidence information

    Returns:
        Enhanced description with confidence documentation
    """
    if not metadata.is_mathematical_reasoning:
        return description

    # Avoid duplicate enhancement by checking if already enhanced
    if "Mathematical Basis:" in description:
        return description

    enhanced_desc = description

    if metadata.mathematical_basis:
        enhanced_desc += f"\n\nMathematical Basis: {metadata.mathematical_basis}"

    # Generate confidence documentation from explicit factors if available
    if metadata.confidence_factors:
        enhanced_desc += f"\n\nConfidence Scoring: Confidence calculation based on: {', '.join(metadata.confidence_factors)}"
    elif metadata.confidence_documentation:
        # Fallback to existing documentation if factors are not provided
        enhanced_desc += f"\n\nConfidence Scoring: {metadata.confidence_documentation}"

    if metadata.confidence_formula:
        enhanced_desc += f"\n\nConfidence Formula: {metadata.confidence_formula}"

    return enhanced_desc


def get_tool_specs() -> List[Dict[str, Any]]:
    """Returns a list of all registered tool specifications (legacy format)."""
    return [getattr(func, "tool_spec") for func in TOOL_REGISTRY]


def get_openai_tools() -> List[Dict[str, Any]]:
    """
    Export tool specifications in OpenAI ChatCompletions API format.

    Returns:
        List of OpenAI-compatible tool specifications
    """
    openai_tools = []
    for entry in ENHANCED_TOOL_REGISTRY:
        # Create enhanced description using safe copy
        enhanced_spec = _safe_copy_spec(entry["tool_spec"])
        enhanced_spec["function"]["description"] = (
            _enhance_description_with_confidence_docs(
                enhanced_spec["function"]["description"], entry["metadata"]
            )
        )
        openai_tools.append(_openai_format(enhanced_spec))
    return openai_tools


def get_bedrock_tools() -> List[Dict[str, Any]]:
    """
    Export tool specifications in AWS Bedrock Converse API format.

    Returns:
        List of Bedrock-compatible tool specifications
    """
    bedrock_tools = []
    for entry in ENHANCED_TOOL_REGISTRY:
        # Create enhanced description using safe copy
        enhanced_spec = _safe_copy_spec(entry["tool_spec"])
        enhanced_spec["function"]["description"] = (
            _enhance_description_with_confidence_docs(
                enhanced_spec["function"]["description"], entry["metadata"]
            )
        )
        bedrock_tools.append(_bedrock_format(enhanced_spec))
    return bedrock_tools


def get_enhanced_tool_registry() -> List[Dict[str, Any]]:
    """
    Get the complete enhanced tool registry with metadata.

    Returns:
        List of enhanced tool registry entries
    """
    return ENHANCED_TOOL_REGISTRY.copy()


# --- End Enhanced Tool Registry ---


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


@dataclass
class ReasoningStep:
    """
    Represents a single step in a reasoning chain, including its result and metadata.
    """

    step_number: int
    stage: str
    description: str
    result: Any
    confidence: Optional[float] = None
    evidence: Optional[str] = None
    assumptions: Optional[List[str]] = field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)


@dataclass
class ReasoningChain:
    """
    Manages a sequence of ReasoningStep objects, providing chain-of-thought capabilities.
    """

    steps: List[ReasoningStep] = field(default_factory=list)
    _step_counter: int = field(init=False, default=0)

    def add_step(
        self,
        stage: str,
        description: str,
        result: Any,
        confidence: Optional[float] = None,
        evidence: Optional[str] = None,
        assumptions: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ReasoningStep:
        """
        Adds a new reasoning step to the chain.
        """
        self._step_counter += 1
        step = ReasoningStep(
            step_number=self._step_counter,
            stage=stage,
            description=description,
            result=result,
            confidence=confidence,
            evidence=evidence,
            assumptions=assumptions if assumptions is not None else [],
            metadata=metadata if metadata is not None else {},
        )
        self.steps.append(step)
        return step

    def get_summary(self) -> str:
        """
        Generates a summary of the reasoning chain.
        """
        summary_parts = ["Reasoning Chain Summary:"]
        for step in self.steps:
            summary_parts.append(
                f"  Step {step.step_number} ({step.stage}): {step.description}"
            )
            summary_parts.append(f"    Result: {step.result}")
            if step.confidence is not None:
                summary_parts.append(f"    Confidence: {step.confidence:.2f}")
            if step.evidence:
                summary_parts.append(f"    Evidence: {step.evidence}")
            if step.assumptions:
                summary_parts.append(f"    Assumptions: {', '.join(step.assumptions)}")
            if step.metadata:
                summary_parts.append(f"    Metadata: {step.metadata}")
        return "\n".join(summary_parts)

    def clear(self) -> None:
        """
        Clears all steps from the reasoning chain.
        """
        self.steps = []
        self._step_counter = 0

    @property
    def last_result(self) -> Any:
        """
        Returns the result of the last step in the chain, or None if the chain is empty.
        """
        return self.steps[-1].result if self.steps else None


# --- Tool Specification Utility ---

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
