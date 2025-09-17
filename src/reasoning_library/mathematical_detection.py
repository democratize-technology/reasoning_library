"""
Mathematical reasoning detection utilities.

This module contains regex patterns and logic for detecting mathematical reasoning
indicators in function code and docstrings.
"""

import inspect
import re
from typing import Any, Callable, List, Optional, Tuple

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


def _has_mathematical_indicators(func: Callable[..., Any]) -> bool:
    """
    Check if a function has mathematical reasoning indicators in its docstring or name.

    This performs a fast initial check without source code extraction.

    Args:
        func: The function to check

    Returns:
        bool: True if mathematical indicators are found, False otherwise
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
    return any(
        indicator in docstring.lower() or indicator in func_name.lower()
        for indicator in math_indicators
    )


def _extract_safe_source_code(func: Callable[..., Any]) -> str:
    """
    Safely extract source code from a function with size limits for ReDoS protection.

    Args:
        func: The function to extract source code from

    Returns:
        str: The source code, truncated if necessary, or empty string if unavailable
    """
    try:
        source_code = inspect.getsource(func) if hasattr(func, "__code__") else ""
    except (OSError, TypeError):
        # Handle dynamic functions, lambdas, and other edge cases gracefully
        source_code = ""

    # Prevent ReDoS attacks by limiting source code size
    if len(source_code) > MAX_SOURCE_CODE_SIZE:
        source_code = source_code[:MAX_SOURCE_CODE_SIZE]  # Truncate to safe size

    return source_code


def _extract_confidence_factors(source_code: str, docstring: str) -> List[str]:
    """
    Extract confidence factors from source code and docstring using regex patterns.

    Args:
        source_code: The source code to analyze
        docstring: The function's docstring

    Returns:
        List[str]: List of confidence factors found in the source code and docstring
    """
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

    return confidence_factors


def _clean_confidence_factors(factors: List[str]) -> List[str]:
    """
    Clean and deduplicate confidence factors.

    Args:
        factors: List of raw confidence factors

    Returns:
        List[str]: List of cleaned and deduplicated factors
    """
    clean_factors = []
    seen = set()
    for factor in factors:
        clean_factor = factor.strip().lower()
        # Remove common code artifacts using pre-compiled pattern
        clean_factor = CLEAN_FACTOR_PATTERN.sub("", clean_factor).strip()
        if clean_factor and clean_factor not in seen and len(clean_factor) > 2:
            clean_factors.append(clean_factor)
            seen.add(clean_factor)
    return clean_factors


def _extract_mathematical_basis(docstring: str) -> Optional[str]:
    """
    Extract mathematical basis from docstring based on specific patterns.

    Args:
        docstring: The function's docstring

    Returns:
        Optional[str]: Mathematical basis description if found, None otherwise
    """
    docstring_lower = docstring.lower()

    if "arithmetic progression" in docstring_lower:
        return "Arithmetic progression analysis with data sufficiency and pattern quality factors"
    elif "geometric progression" in docstring_lower:
        return "Geometric progression analysis with ratio consistency validation"
    elif "modus ponens" in docstring_lower:
        return "Formal deductive logic using Modus Ponens inference rule"
    elif "chain of thought" in docstring_lower:
        return "Sequential reasoning with conservative confidence aggregation (minimum of step confidences)"

    return None


def _detect_mathematical_reasoning(
    func: Callable[..., Any],
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Detect if a function performs mathematical reasoning and extract confidence documentation.

    Optimized to perform fast initial checks before expensive source code extraction.
    This function orchestrates several focused helper functions for better maintainability.

    Returns:
        tuple: (is_mathematical, confidence_documentation, mathematical_basis)
    """
    # Fast initial check using only docstring and function name
    if not _has_mathematical_indicators(func):
        return False, None, None

    # Only extract source code if initial check suggests mathematical reasoning
    source_code = _extract_safe_source_code(func)
    docstring = func.__doc__ or ""

    # Final check including source code - need to recheck with source code
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

    is_mathematical = any(
        indicator in source_code.lower() or indicator in docstring.lower()
        for indicator in math_indicators
    )

    confidence_doc = None
    mathematical_basis = None

    if is_mathematical:
        # Extract confidence factors using dedicated function
        confidence_factors = _extract_confidence_factors(source_code, docstring)

        # Create meaningful confidence documentation
        if confidence_factors:
            clean_factors = _clean_confidence_factors(confidence_factors)
            if clean_factors:
                confidence_doc = (
                    f"Confidence calculation based on: {', '.join(clean_factors[:3])}"
                )

        # Extract mathematical basis using dedicated function
        mathematical_basis = _extract_mathematical_basis(docstring)

    return is_mathematical, confidence_doc, mathematical_basis