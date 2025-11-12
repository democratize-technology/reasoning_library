"""
Core utilities for the reasoning library.
"""

import inspect
import re
import threading
import weakref
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from .exceptions import ValidationError
from .constants import (
    # Security constants
    MAX_SOURCE_CODE_SIZE,

    # Performance optimization constants
    MAX_CACHE_SIZE,
    MAX_REGISTRY_SIZE,

    # Cache management parameters
    CACHE_EVICTION_FRACTION,
    REGISTRY_EVICTION_FRACTION,

    # Regex pattern constants
    REGEX_WORD_CHAR_MAX,
    REGEX_SPACING_MAX,

    # Text processing limits
    KEYWORD_LENGTH_LIMIT,
    COMPONENT_LENGTH_LIMIT,
    MAX_TEMPLATE_KEYWORDS,
)

# Pre - compiled regex patterns with ReDoS vulnerability fixes
# Using more specific patterns to avoid catastrophic backtracking
FACTOR_PATTERN = re.compile(
    rf"(\w{{0,{REGEX_WORD_CHAR_MAX}}}(?:data_sufficiency | pattern_quality | complexity)_factor)[\s]{{0,5}}(?:\*|,|\+|\-|=)",
    re.IGNORECASE | re.MULTILINE,
)
COMMENT_PATTERN = re.compile(
    r"#\s*(?:Data | Pattern | Complexity)\s+([^#\n]+factor)", re.IGNORECASE | re.MULTILINE
)
EVIDENCE_PATTERN = re.compile(
    r'f?"[^"]*(?:confidence\s + based\s + on | factors?[\s:]*in)[^"]*([^"\.]+pattern[^"\.]*)',
    re.IGNORECASE | re.MULTILINE,
)
COMBINATION_PATTERN = re.compile(
    rf"(\w{{1,{REGEX_WORD_CHAR_MAX}}}_factor)[\s]{{0,{REGEX_SPACING_MAX}}}\*[\s]{{0,{REGEX_SPACING_MAX}}}(\w{{1,{REGEX_WORD_CHAR_MAX}}}_factor)",
    re.IGNORECASE | re.MULTILINE,
)
CLEAN_FACTOR_PATTERN = re.compile(r"[()=\*]+", re.IGNORECASE)

# --- Performance Optimization Caches ---

# Function source code cache using weak references to prevent memory leaks
_function_source_cache: weakref.WeakKeyDictionary[Callable, str] = weakref.WeakKeyDictionary()

# Mathematical reasoning detection cache using function id for key stability
_math_detection_cache: Dict[int, Tuple[bool, Optional[str], Optional[str]]] = {}

# Cache size limit and registry limits are now imported from constants module
# _MAX_CACHE_SIZE and _MAX_REGISTRY_SIZE are replaced by MAX_CACHE_SIZE and MAX_REGISTRY_SIZE

# Backwards compatibility aliases for tests
_MAX_CACHE_SIZE = MAX_CACHE_SIZE
_MAX_REGISTRY_SIZE = MAX_REGISTRY_SIZE

# Thread - safe locks for registry operations
_registry_lock = threading.RLock()

# Thread - safe locks for cache operations
_cache_lock = threading.RLock()

def _get_function_source_cached(func: Callable[..., Any]) -> str:
    """
    SECURE: Get function source code with safety restrictions to prevent information disclosure.

    DISABLED for security: Source code inspection is disabled to prevent:
    - Information disclosure of sensitive implementation details
    - Access to source code from external files through inspect.getsource()
    - Exposure of secrets, API keys, or sensitive data in source comments
    - File system access and path traversal through code inspection
    - Proprietary algorithm exposure

    Thread - safe: Uses _cache_lock to prevent race conditions in cache access.

    Args:
        func: Function to analyze (source code will NOT be extracted for security)

    Returns:
        str: Always empty string for security reasons
    """
    # SECURITY: Source code inspection disabled to prevent information disclosure
    # The inspect.getsource() function can access files on disk and expose sensitive
    # information including API keys, passwords, and proprietary algorithms.
    # This function now returns empty string for all inputs to eliminate the attack vector.

    # Thread - safe cache access with proper locking
    with _cache_lock:
        # Check cache first (WeakKeyDictionary automatically handles cleanup)
        if func in _function_source_cache:
            return _function_source_cache[func]

        # Always return empty string for security - prevents any source code disclosure
        empty_result = ""

        # Cache the empty result to maintain expected behavior and performance
        _function_source_cache[func] = empty_result
        return empty_result

def _get_math_detection_cached(func: Callable[...,
                               Any]) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Get mathematical reasoning detection result with caching.

    Uses function id as cache key for stability across calls.
    Implements LRU - style eviction to prevent unbounded cache growth.

    Thread - safe: Uses _cache_lock to prevent race conditions in cache access
    and eviction logic that could cause data corruption.

    Args:
        func: Function to analyze for mathematical reasoning

    Returns:
        tuple: (is_mathematical, confidence_documentation, mathematical_basis)
    """
    # Create a stable cache key that includes function identity and content
    # This prevents false cache hits when Python reuses object IDs
    try:
        import hashlib
        func_module = getattr(func, '__module__', 'unknown')
        func_qualname = getattr(func, '__qualname__', 'unknown')

        # Get source code for content - based hashing
        try:
            import inspect
            source_code = inspect.getsource(func) or ''
        except (OSError, TypeError):
            source_code = ''

        docstring = func.__doc__ or ''

        # Create a hash based on multiple stable identifiers
        content = f"{func_module}:{func_qualname}:{docstring}:{source_code}"
        func_id = hashlib.md5(content.encode()).hexdigest()

    except (OSError, TypeError, ValueError, AttributeError, ImportError):
        # Fallback to object ID if hashing fails (less safe but functional)
        # Specific exceptions: import errors, type errors, value errors, attribute access errors
        func_id = str(id(func))

    # Thread - safe cache access with proper locking
    with _cache_lock:
        # Check cache first (ensure cached value is not None)
        if (func_id in _math_detection_cache and
                _math_detection_cache[func_id] is not None):
            return _math_detection_cache[func_id]

    # Perform expensive detection outside of lock to minimize contention
    result = _detect_mathematical_reasoning_uncached(func)

    # Thread - safe cache update and eviction with proper locking
    with _cache_lock:
        # Double - check pattern: another thread might have added this while we were detecting
        if (func_id in _math_detection_cache and
                _math_detection_cache[func_id] is not None):
            return _math_detection_cache[func_id]

        # Implement atomic cache size management and eviction
        if len(_math_detection_cache) >= MAX_CACHE_SIZE:
            # Remove oldest entries (simple FIFO approach)
            # In production, consider using functools.lru_cache or more sophisticated eviction
            oldest_keys = list(_math_detection_cache.keys())[:int(MAX_CACHE_SIZE * CACHE_EVICTION_FRACTION)]
            for key in oldest_keys:
                _math_detection_cache.pop(key, None)

        # Ensure result is always a valid tuple (defensive programming)
        if result is None or not isinstance(result, tuple) or len(result) != 3:
            result = (False, None, None)

        # Cache the result
        _math_detection_cache[func_id] = result
        return result

def _manage_registry_size():
    """
    Manage registry size to prevent unbounded growth and memory exhaustion attacks.

    Implements FIFO - style eviction for both ENHANCED_TOOL_REGISTRY and TOOL_REGISTRY
    to maintain bounded memory usage. Only performs expensive operations when
    actually exceeding limits to maintain O(1) performance for normal use.

    Thread - safe: Uses _registry_lock to prevent race conditions.
    """
    with _registry_lock:
        # Early exit if both registries are under limit (O(1) performance)
        if (len(ENHANCED_TOOL_REGISTRY) < MAX_REGISTRY_SIZE and
            len(TOOL_REGISTRY) < MAX_REGISTRY_SIZE):
            return

        # Only if exceeding limit, then do expensive eviction operations
        if len(ENHANCED_TOOL_REGISTRY) >= MAX_REGISTRY_SIZE:
            # Remove oldest percentage of entries (FIFO eviction)
            remove_count = int(MAX_REGISTRY_SIZE * REGISTRY_EVICTION_FRACTION)
            ENHANCED_TOOL_REGISTRY[:] = ENHANCED_TOOL_REGISTRY[remove_count:]

        if len(TOOL_REGISTRY) >= MAX_REGISTRY_SIZE:
            # Remove oldest percentage of entries (FIFO eviction)
            remove_count = int(MAX_REGISTRY_SIZE * REGISTRY_EVICTION_FRACTION)
            TOOL_REGISTRY[:] = TOOL_REGISTRY[remove_count:]


def clear_performance_caches() -> Dict[str, int]:
    """
    Clear all performance optimization caches and registries.

    Useful for testing, memory management, or when function definitions change.

    Thread - safe: Uses both _registry_lock and _cache_lock to prevent race conditions.

    Returns:
        dict: Statistics about cleared cache entries
    """
    # Lock both caches and registries to prevent race conditions during clearing
    with _cache_lock, _registry_lock:
        source_cache_size = len(_function_source_cache)
        math_cache_size = len(_math_detection_cache)
        enhanced_registry_size = len(ENHANCED_TOOL_REGISTRY)
        tool_registry_size = len(TOOL_REGISTRY)

        _function_source_cache.clear()
        _math_detection_cache.clear()
        ENHANCED_TOOL_REGISTRY.clear()
        TOOL_REGISTRY.clear()

        return {
            "source_cache_cleared": source_cache_size,
            "math_detection_cache_cleared": math_cache_size,
            "enhanced_registry_cleared": enhanced_registry_size,
            "tool_registry_cleared": tool_registry_size
        }

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
    platform_notes: Optional[Dict[str, str]] = field(default_factory = dict)
    is_mathematical_reasoning: bool = False
    confidence_formula: Optional[str] = None
    confidence_factors: Optional[List[str]] = field(default_factory = list)


def _detect_mathematical_reasoning_uncached(
    func: Callable[..., Any],
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Detect if a function performs mathematical reasoning and
        extract confidence documentation.

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
        "modus ponens",
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

    # If no mathematical indicators in docs / name, likely not mathematical
    if not has_math_indicators_in_docs:
        return False, None, None

    # Only extract source code if initial check suggests mathematical reasoning
    # Use cached source code retrieval for performance optimization
    source_code = _get_function_source_cached(func)

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

        # Pattern 1: Extract confidence factor variable names using pre - compiled pattern
        factor_matches = FACTOR_PATTERN.findall(source_code)
        if factor_matches:
            confidence_factors.extend(
                [factor.replace("_", " ") for factor in factor_matches[:3]]
            )

        # Pattern 2: Extract meaningful descriptive comments using pre - compiled pattern
        comment_matches = COMMENT_PATTERN.findall(source_code)
        if comment_matches:
            confidence_factors.extend(
                [match.strip().lower() for match in comment_matches[:2]]
            )

        # Pattern 3: Extract from evidence strings with confidence calculations using pre - compiled pattern
        evidence_matches = EVIDENCE_PATTERN.findall(source_code)
        if evidence_matches:
            confidence_factors.extend([match.strip() for match in evidence_matches[:1]])

        # Pattern 4: Look for factor multiplication combinations using pre - compiled pattern
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
                # Remove common code artifacts using pre - compiled pattern
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
            mathematical_basis = (
                "Arithmetic progression analysis with data sufficiency and "
                "pattern quality factors"
            )
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


def _detect_mathematical_reasoning(
    func: Callable[..., Any],
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Detect if a function performs mathematical reasoning with performance optimization.

    This is the optimized version that uses caching to avoid repeated expensive operations.
    Provides significant performance improvement for repeated function analysis.

    Args:
        func: Function to analyze for mathematical reasoning patterns

    Returns:
        tuple: (is_mathematical, confidence_documentation, mathematical_basis)
    """
    return _get_math_detection_cached(func)


def _safe_copy_spec(tool_spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    SECURE: Safely copy tool specification with input validation to prevent injection attacks.

    Prevents multiple injection vectors:
    - Prototype pollution through dangerous keys like __proto__
    - Code injection through malicious function names and descriptions
    - Template injection through parameter descriptions

    Args:
        tool_spec: Tool specification to copy

    Returns:
        Validated and safely copied tool specification

    Raises:
        ValidationError: If tool specification is invalid or missing required fields
    """
    if not isinstance(tool_spec, dict):
        raise ValidationError("Tool specification must be a dictionary")

    if "function" not in tool_spec:
        raise ValidationError("Tool specification must contain 'function' key")

    if not isinstance(tool_spec["function"], dict):
        raise ValidationError("Tool specification 'function' value must be a dictionary")

    def sanitize_text_input(text: Any, max_length: int = KEYWORD_LENGTH_LIMIT * 20) -> str:
        """SECURE: Sanitize text inputs to prevent injection attacks."""
        if not isinstance(text, str):
            return ""

        # Truncate to reasonable length
        text = text[:max_length]

        # Remove dangerous characters that could be used for injection
        sanitized = re.sub(r'[<>"\'`]', '', text)
            # Remove HTML / JS injection characters
        sanitized = re.sub(r'[{}]',
                           '', sanitized)  # Remove template injection characters
        sanitized = re.sub(r'\${[^}]*}', '', sanitized)  # Remove ${...} patterns
        sanitized = re.sub(r'%[sd]', '', sanitized)      # Remove %s, %d patterns
        sanitized = re.sub(r'__import__\s*\(',
                           'BLOCKED', sanitized)  # Block import attempts
        sanitized = re.sub(r'eval\s*\(',
                           'BLOCKED', sanitized)      # Block eval attempts
        sanitized = re.sub(r'exec\s*\(',
                           'BLOCKED', sanitized)      # Block exec attempts

        # Remove newlines and other control characters that could poison logs
        # CRITICAL FIX: Prevent log injection by normalizing newlines and control chars
        sanitized = re.sub(r'[\r\n\t]',
                           ' ', sanitized)  # Convert newlines / tabs to spaces
        sanitized = re.sub(r'\s+', ' ', sanitized)       # Normalize multiple spaces

        # Remove potential ANSI escape sequences that could poison terminal logs
        sanitized = re.sub(r'\x1b\[[0 - 9;]*m', '', sanitized)
            # Remove ANSI color codes

        return sanitized.strip()

    # Whitelist of allowed top - level keys to prevent prototype pollution
    allowed_top_level_keys = {"type", "function"}

    # Whitelist of allowed function keys
    allowed_function_keys = {"name", "description", "parameters"}

    # Blacklist of dangerous keys that could indicate prototype pollution
    dangerous_keys = {"__proto__", "constructor", "prototype", "prototypeof"}

    # Create safe copy with only whitelisted keys
    safe_spec = {}
    for key, value in tool_spec.items():
        # Skip dangerous keys that could cause prototype pollution
        if key in dangerous_keys:
            continue

        if key in allowed_top_level_keys:
            if key == "function":
                # Safely copy function object with whitelisted keys and sanitization
                safe_function = {}
                for func_key, func_value in value.items():
                    if func_key in allowed_function_keys:
                        # Sanitize all string values to prevent injection
                        if func_key == "name":
                            safe_function[func_key] = sanitize_text_input(func_value,
                                                                          max_length = KEYWORD_LENGTH_LIMIT)
                        elif func_key == "description":
                            safe_function[func_key] = sanitize_text_input(func_value,
                                                                          max_length = KEYWORD_LENGTH_LIMIT * 10)
                        elif func_key == "parameters" and isinstance(func_value, dict):
                            # Recursively sanitize parameter object
                            safe_function[func_key] = _sanitize_parameters(func_value)
                        else:
                            safe_function[func_key] = func_value
                safe_spec[key] = safe_function
            else:
                safe_spec[key] = sanitize_text_input(value, max_length = KEYWORD_LENGTH_LIMIT * 2)

    return safe_spec


def _sanitize_parameters(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """SECURE: Recursively sanitize parameter objects to prevent injection."""
    if not isinstance(parameters, dict):
        return {}

    safe_params = {}

    # Process properties
    if "properties" in parameters and isinstance(parameters["properties"], dict):
        safe_params["properties"] = {}
        for param_name, param_spec in parameters["properties"].items():
            # Sanitize parameter name
            safe_name = re.sub(r'[^a - zA - Z0 - 9_]', '', str(param_name))[:KEYWORD_LENGTH_LIMIT]
            if not safe_name:
                safe_name = "param"

            # Sanitize parameter specification
            if isinstance(param_spec, dict):
                safe_spec = {}
                for spec_key, spec_value in param_spec.items():
                    if isinstance(spec_value, str):
                        safe_spec[spec_key] = re.sub(r'[<>"\'`{}]',
                                                     '', spec_value)[:COMPONENT_LENGTH_LIMIT * 4]
                    else:
                        safe_spec[spec_key] = spec_value
                safe_params["properties"][safe_name] = safe_spec

    # Copy other parameter fields safely
    for key, value in parameters.items():
        if key != "properties":
            if isinstance(value, str):
                safe_params[key] = re.sub(r'[<>"\'`{}]', '', value)[:COMPONENT_LENGTH_LIMIT * 2]
            elif isinstance(value, (list, tuple)):
                safe_params[key] = [str(item)[:KEYWORD_LENGTH_LIMIT] for item in value]
            else:
                safe_params[key] = value

    return safe_params


def _openai_format(tool_spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert tool specification to OpenAI ChatCompletions API format.

    Args:
        tool_spec: Standard tool specification

    Returns:
        OpenAI - compatible tool specification
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
        Bedrock - compatible tool specification
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
    SECURE: Enhance tool description with confidence documentation for mathematical reasoning functions.

    Sanitizes all metadata to prevent injection attacks before inclusion in descriptions.

    Args:
        description: Original function description
        metadata: Tool metadata containing confidence information

    Returns:
        Enhanced description with sanitized confidence documentation
    """
    if not metadata.is_mathematical_reasoning:
        return description

    # Avoid duplicate enhancement by checking if already enhanced
    if "Mathematical Basis:" in description:
        return description

    def sanitize_confidence_text(text: Any) -> str:
        """SECURE: Sanitize confidence - related text to prevent injection."""
        if not isinstance(text, str):
            return ""

        # Remove dangerous characters that could be used for injection
        sanitized = re.sub(r'[<>"\'`]', '', text)
            # Remove HTML / JS injection characters
        sanitized = re.sub(r'[{}]',
                           '', sanitized)  # Remove template injection characters
        sanitized = re.sub(r'\${[^}]*}', '', sanitized)  # Remove ${...} patterns
        sanitized = re.sub(r'%[sd]', '', sanitized)      # Remove %s, %d patterns
        sanitized = re.sub(r'__import__\s*\(',
                           'BLOCKED', sanitized)  # Block import attempts
        sanitized = re.sub(r'eval\s*\(',
                           'BLOCKED', sanitized)      # Block eval attempts
        sanitized = re.sub(r'exec\s*\(',
                           'BLOCKED', sanitized)      # Block exec attempts

        # Remove control characters that could poison logs
        sanitized = re.sub(r'[\r\n\t]', ' ', sanitized)

        return sanitized.strip()

    # Sanitize original description
    enhanced_desc = sanitize_confidence_text(description)

    # Sanitize mathematical basis
    if metadata.mathematical_basis:
        safe_basis = sanitize_confidence_text(metadata.mathematical_basis)
        enhanced_desc += f"\n\nMathematical Basis: {safe_basis}"

    # Generate confidence documentation from explicit factors if available
    if metadata.confidence_factors:
        # Sanitize each confidence factor
        safe_factors = [sanitize_confidence_text(factor) for factor in metadata.confidence_factors if factor]
        safe_factors = [factor for factor in safe_factors if factor]
            # Remove empty strings
        if safe_factors:
            enhanced_desc += f"\n\nConfidence Scoring: Confidence calculation based on: {', '.join(safe_factors[:MAX_TEMPLATE_KEYWORDS])}"
    elif metadata.confidence_documentation:
        # Fallback to existing documentation if factors are not provided
        safe_doc = sanitize_confidence_text(metadata.confidence_documentation)
        enhanced_desc += f"\n\nConfidence Scoring: {safe_doc}"

    # Sanitize confidence formula
    if metadata.confidence_formula:
        safe_formula = sanitize_confidence_text(metadata.confidence_formula)
        enhanced_desc += f"\n\nConfidence Formula: {safe_formula}"

    return enhanced_desc


def get_tool_specs() -> List[Dict[str, Any]]:
    """
    Returns a list of all registered tool specifications (legacy format).

    Thread - safe: Uses _registry_lock to prevent race conditions during iteration.
    """
    with _registry_lock:
        return [getattr(func, "tool_spec") for func in TOOL_REGISTRY.copy()]


def get_openai_tools() -> List[Dict[str, Any]]:
    """
    Export tool specifications in OpenAI ChatCompletions API format.

    Thread - safe: Uses _registry_lock to prevent race conditions during iteration.

    Returns:
        List of OpenAI - compatible tool specifications
    """
    with _registry_lock:
        openai_tools = []
        for entry in ENHANCED_TOOL_REGISTRY.copy():
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

    Thread - safe: Uses _registry_lock to prevent race conditions during iteration.

    Returns:
        List of Bedrock - compatible tool specifications
    """
    with _registry_lock:
        bedrock_tools = []
        for entry in ENHANCED_TOOL_REGISTRY.copy():
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

    Thread - safe: Uses _registry_lock to prevent race conditions during access.

    Returns:
        List of enhanced tool registry entries
    """
    with _registry_lock:
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
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
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
    assumptions: Optional[List[str]] = field(default_factory = list)
    metadata: Optional[Dict[str, Any]] = field(default_factory = dict)


@dataclass

class ReasoningChain:
    """
    Manages a sequence of ReasoningStep objects, providing chain - of - thought capabilities.
    """

    steps: List[ReasoningStep] = field(default_factory = list)
    _step_counter: int = field(init = False, default = 0)

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
            step_number = self._step_counter,
            stage = stage,
            description = description,
            result = result,
            confidence = confidence,
            evidence = evidence,
            assumptions = assumptions if assumptions is not None else [],
            metadata = metadata if metadata is not None else {},
        )
        self.steps.append(step)
        return step

    def _sanitize_reasoning_input(self, text: Any) -> str:
        """
        SECURE: Sanitize reasoning input to prevent log injection attacks.

        Args:
            text: Input text to sanitize

        Returns:
            Sanitized text safe for logging
        """
        if not isinstance(text, str):
            return str(text)

        # Use the existing sanitize_text_input function (defined in _safe_copy_spec context)

        def sanitize_text_input_for_reasoning(text: Any, max_length: int = 1000) -> str:
            """SECURE: Sanitize text inputs to prevent injection attacks."""
            if not isinstance(text, str):
                return ""

            # Truncate to reasonable length
            text = text[:max_length]

            # Remove dangerous characters that could be used for injection
            sanitized = re.sub(r'[<>"\'`]',
                               '', text)  # Remove HTML / JS injection characters
            sanitized = re.sub(r'[{}]',
                               '', sanitized)  # Remove template injection characters
            sanitized = re.sub(r'\${[^}]*}', '', sanitized)  # Remove ${...} patterns
            sanitized = re.sub(r'%[sd]', '', sanitized)      # Remove %s, %d patterns
            sanitized = re.sub(r'__import__\s*\(',
                               'BLOCKED', sanitized)  # Block import attempts
            sanitized = re.sub(r'eval\s*\(',
                               'BLOCKED', sanitized)      # Block eval attempts
            sanitized = re.sub(r'exec\s*\(',
                               'BLOCKED', sanitized)      # Block exec attempts

            # CRITICAL FIX: Remove log injection patterns that could poison logs
            # Block common log level patterns that could be used for log injection
            sanitized = re.sub(r'\[(ERROR|CRITICAL|WARN|WARNING|INFO|DEBUG|TRACE|FATAL)\]', '[LOG_LEVEL_BLOCKED]', sanitized)

            # Remove newlines and other control characters that could poison logs
            # CRITICAL FIX: Prevent log injection by normalizing newlines and control chars
            sanitized = re.sub(r'[\r\n\t]',
                               ' ', sanitized)  # Convert newlines / tabs to spaces
            sanitized = re.sub(r'\s+', ' ', sanitized)       # Normalize multiple spaces

            # Remove potential ANSI escape sequences that could poison terminal logs
            sanitized = re.sub(r'\x1b\[[0-9;]*m',
                               '', sanitized)  # Remove ANSI color codes

            return sanitized.strip()

        return sanitize_text_input_for_reasoning(text, max_length = 200)

    def get_summary(self) -> str:
        """
        SECURE: Generates a summary of the reasoning chain with log injection prevention.

        All user input is sanitized to prevent log poisoning attacks.
        """
        summary_parts = ["Reasoning Chain Summary:"]
        for step in self.steps:
            # Sanitize all user - provided input to prevent log injection
            safe_stage = self._sanitize_reasoning_input(step.stage)
            safe_description = self._sanitize_reasoning_input(step.description)
            safe_result = self._sanitize_reasoning_input(step.result)
            safe_evidence = self._sanitize_reasoning_input(step.evidence) if step.evidence else ""
            safe_assumptions = [self._sanitize_reasoning_input(assumption) for assumption in step.assumptions] if step.assumptions else []
            safe_metadata = str(step.metadata) if step.metadata else ""

            summary_parts.append(
                f"  Step {step.step_number} ({safe_stage}): {safe_description}"
            )
            summary_parts.append(f"    Result: {safe_result}")
            if step.confidence is not None:
                summary_parts.append(f"    Confidence: {step.confidence:.2f}")
            if safe_evidence:
                summary_parts.append(f"    Evidence: {safe_evidence}")
            if safe_assumptions:
                summary_parts.append(f"    Assumptions: {', '.join(safe_assumptions)}")
            if safe_metadata:
                summary_parts.append(f"    Metadata: {safe_metadata}")
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
                # This is Optional[X] - get the non - None type
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
            confidence_documentation = confidence_doc,
            mathematical_basis = final_mathematical_basis,
            is_mathematical_reasoning = is_mathematical,
            confidence_formula = confidence_formula,
            confidence_factors = confidence_factors,
            platform_notes={},
        )

        # Thread - safe atomic registry updates with size management
        with _registry_lock:
            ENHANCED_TOOL_REGISTRY.append(
                {"function": wrapper, "tool_spec": tool_specification, "metadata": metadata}
            )

            setattr(wrapper, "tool_spec", tool_specification)
            TOOL_REGISTRY.append(wrapper)

            # Manage registry size AFTER adding entries to prevent race conditions
            _manage_registry_size()

        return wrapper

    if func:
        return decorator(func)
    return decorator
