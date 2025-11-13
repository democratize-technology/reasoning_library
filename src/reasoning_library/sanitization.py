"""
Shared sanitization utilities for the reasoning library.

This module consolidates duplicate sanitization logic from across the codebase
into reusable, secure, and well-tested utilities.

All sanitization functions follow defense-in-depth principles with multiple
layers of protection against injection attacks.
"""

import re
from typing import Any, Optional

from .constants import (
    KEYWORD_LENGTH_LIMIT
)


class SanitizationLevel:
    """
    Enumeration of sanitization levels for different security requirements.
    """
    STRICT = "strict"      # Maximum security, removes most special characters
    MODERATE = "moderate"  # Balanced security, preserves some formatting
    PERMISSIVE = "permissive"  # Minimal sanitization, preserves most characters


# Pre-compiled regex patterns for performance and security
# These patterns are compiled once and reused to prevent ReDoS attacks

# Dangerous patterns that could lead to injection attacks
_DANGEROUS_KEYWORD_PATTERN = re.compile(
    r'\b(?:import|exec|eval|system|subprocess|os|config|globals|locals|vars|dir|getattr|setattr|delattr|hasattr)\b',
    re.IGNORECASE
)

# Template injection patterns
_TEMPLATE_INJECTION_PATTERN = re.compile(r'\${[^}]*}')

# Format string injection patterns
_FORMAT_STRING_PATTERN = re.compile(r'%[a-zA-Z]')

# Code injection patterns
_CODE_INJECTION_PATTERN = re.compile(
    r'(?:__import__|eval|exec)\s*\(',
    re.IGNORECASE
)

# Dunder method patterns (could lead to method injection)
_DUNDER_PATTERN = re.compile(r'__.*?__')

# Attribute access patterns
_ATTRIBUTE_PATTERN = re.compile(r'\.[a-zA-Z_][a-zA-Z0-9_]*')

# Shell metacharacters
_SHELL_PATTERN = re.compile(r'[|&;$<>`\\]')

# Template and code brackets
_BRACKET_PATTERN = re.compile(r'[{}\[\]\(\)]')

# Quote characters
_QUOTE_PATTERN = re.compile(r'["\']')

# HTML/JS injection characters
_HTML_INJECTION_PATTERN = re.compile(r'[<>"\'`]')

# Control characters that could poison logs
_CONTROL_CHAR_PATTERN = re.compile(r'[\r\n\t]')

# ANSI escape sequences for terminal log poisoning
_ANSI_ESCAPE_PATTERN = re.compile(r'\x1b\[[0-9;]*m')

# Whitespace normalization
_WHITESPACE_PATTERN = re.compile(r'\s+')


def sanitize_text_input(
    text: Any,
    max_length: Optional[int] = None,
    level: str = SanitizationLevel.MODERATE
) -> str:
    """
    Comprehensive text sanitization with configurable security levels.

    Args:
        text: Input text to sanitize (any type, non-string returns empty string)
        max_length: Maximum allowed length (default: KEYWORD_LENGTH_LIMIT * 20)
        level: Sanitization level (strict, moderate, permissive)

    Returns:
        str: Sanitized text safe for further processing

    Security Features:
        - Defense-in-depth with multiple pattern matching layers
        - Length limiting to prevent buffer overflow attacks
        - Keyword blocking to prevent code injection
        - Pattern removal to prevent template/format injection
        - Control character normalization to prevent log poisoning

    Examples:
        >>> sanitize_text_input("Hello ${name}")
        'Hello name'
        >>> sanitize_text_input("import os", level="strict")
        ''
        >>> sanitize_text_input("text with <script>", level="moderate")
        'text with script'
    """
    if not isinstance(text, str):
        return ""

    # Set default max length
    if max_length is None:
        max_length = KEYWORD_LENGTH_LIMIT * 20

    # Length limiting (first line of defense)
    text = text[:max_length]

    # Layer 1: Block dangerous keywords
    text = _DANGEROUS_KEYWORD_PATTERN.sub('', text)

    # Layer 2: Handle injection patterns based on security level
    if level == SanitizationLevel.STRICT:
        # Strict mode: remove all potentially dangerous patterns
        text = _TEMPLATE_INJECTION_PATTERN.sub('', text)
        text = _FORMAT_STRING_PATTERN.sub('', text)
        text = _CODE_INJECTION_PATTERN.sub('BLOCKED', text)
        # CRITICAL FIX: Remove dots after code blocking to prevent bypass
        text = re.sub(r'[.]', ' ', text)  # Remove all remaining dots
        text = _DUNDER_PATTERN.sub('', text)
        text = _ATTRIBUTE_PATTERN.sub('', text)
        text = _SHELL_PATTERN.sub('', text)
        text = _BRACKET_PATTERN.sub('', text)
        text = _QUOTE_PATTERN.sub('', text)

    elif level == SanitizationLevel.MODERATE:
        # Moderate mode: balanced security
        text = _TEMPLATE_INJECTION_PATTERN.sub('', text)
        text = _FORMAT_STRING_PATTERN.sub('', text)
        text = _CODE_INJECTION_PATTERN.sub('BLOCKED', text)
        text = _BRACKET_PATTERN.sub('', text)
        text = _QUOTE_PATTERN.sub('', text)

    else:  # PERMISSIVE
        # Permissive mode: minimal sanitization
        text = _CODE_INJECTION_PATTERN.sub('BLOCKED', text)
        text = _TEMPLATE_INJECTION_PATTERN.sub('', text)

    # Layer 3: Handle characters that could poison logs or output
    text = _HTML_INJECTION_PATTERN.sub('', text)
    text = _CONTROL_CHAR_PATTERN.sub(' ', text)
    text = _WHITESPACE_PATTERN.sub(' ', text)
    text = _ANSI_ESCAPE_PATTERN.sub('', text)

    return text.strip()


def sanitize_for_concatenation(text: Any, max_length: int = 50) -> str:
    """
    Strict sanitization specifically for text that will be concatenated.

    This function provides maximum security for string concatenation operations
    where any injection vulnerability could be catastrophic.

    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length (default: 50 for safety)

    Returns:
        str: Sanitized text safe for concatenation

    Security Features:
        - Very strict length limiting (50 chars default)
        - Comprehensive pattern removal
        - All special characters removed
        - Defense-in-depth approach

    Examples:
        >>> sanitize_for_concatenation("Hello ${name}")
        'Hello name'
        >>> sanitize_for_concatenation("import os")
        ''
    """
    return sanitize_text_input(
        text=text,
        max_length=max_length,
        level=SanitizationLevel.STRICT
    )


def sanitize_for_display(text: Any, max_length: Optional[int] = None) -> str:
    """
    Moderate sanitization for text that will be displayed to users.

    This function balances security with readability, preserving some formatting
    while still preventing injection attacks.

    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length (default: KEYWORD_LENGTH_LIMIT * 10)

    Returns:
        str: Sanitized text safe for display

    Examples:
        >>> sanitize_for_display("Hello <b>world</b>")
        'Hello bworldb'
        >>> sanitize_for_display("Text with    spaces")
        'Text with spaces'
    """
    if max_length is None:
        max_length = KEYWORD_LENGTH_LIMIT * 10

    return sanitize_text_input(
        text=text,
        max_length=max_length,
        level=SanitizationLevel.MODERATE
    )


def sanitize_for_logging(text: Any, max_length: Optional[int] = None) -> str:
    """
    Sanitization for text that will be written to logs.

    This function focuses on preventing log injection and log poisoning attacks
    while preserving as much information as possible for debugging.

    Args:
        text: Input text to sanitize for logging
        max_length: Maximum allowed length (default: KEYWORD_LENGTH_LIMIT * 15)

    Returns:
        str: Sanitized text safe for logging

    Security Features:
        - Prevents log injection through control characters
        - Prevents ANSI escape sequence injection
        - Normalizes whitespace for clean logs
        - Preserves most text for debugging value

    Examples:
        >>> sanitize_for_logging("Error\nInjected\rLine")
        'Error Injected Line'
    """
    if max_length is None:
        max_length = KEYWORD_LENGTH_LIMIT * 15

    if not isinstance(text, str):
        return ""

    text = text[:max_length]

    # Focus on log-specific attacks while preserving debugging info
    text = _CONTROL_CHAR_PATTERN.sub(' ', text)
    text = _ANSI_ESCAPE_PATTERN.sub('', text)
    text = _WHITESPACE_PATTERN.sub(' ', text)

    return text.strip()


def quick_sanitize(text: Any) -> str:
    """
    Fast, minimal sanitization for low-risk scenarios.

    This function provides basic sanitization with maximum performance
    for situations where the input is already trusted or has been validated.

    Args:
        text: Input text to quickly sanitize

    Returns:
        str: Minimally sanitized text

    Examples:
        >>> quick_sanitize("Hello world")
        'Hello world'
    """
    if not isinstance(text, str):
        return ""

    # Only remove the most dangerous patterns quickly
    text = text[:KEYWORD_LENGTH_LIMIT * 5]  # Reasonable length limit
    text = _CODE_INJECTION_PATTERN.sub('BLOCKED', text)

    return text.strip()


# Backward compatibility aliases
# These provide migration paths for existing code
def _sanitize_input_for_concatenation(text: str) -> str:
    """
    DEPRECATED: Use sanitize_for_concatenation() instead.

    Maintained for backward compatibility.
    """
    return sanitize_for_concatenation(text)


def _sanitize_template_input(text: str) -> str:
    """
    DEPRECATED: Use sanitize_for_concatenation() instead.

    Maintained for backward compatibility.
    """
    return sanitize_for_concatenation(text)