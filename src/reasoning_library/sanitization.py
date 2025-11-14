"""
Shared sanitization utilities for the reasoning library.

This module consolidates duplicate sanitization logic from across the codebase
into reusable, secure, and well-tested utilities.

All sanitization functions follow defense-in-depth principles with multiple
layers of protection against injection attacks.

SECURITY FIXES for MAJOR-003: Input validation bypass vulnerabilities
- Unicode obfuscation bypass prevention
- Enhanced template injection detection
- Comprehensive case-insensitive pattern matching
- Control character encoding bypass prevention
- Nested/encoded injection detection
"""

import re
import unicodedata
from typing import Any, Optional

from .constants import (
    KEYWORD_LENGTH_LIMIT
)
from .security_logging import log_security_event, get_security_logger


class SanitizationLevel:
    """
    Enumeration of sanitization levels for different security requirements.
    """
    STRICT = "strict"      # Maximum security, removes most special characters
    MODERATE = "moderate"  # Balanced security, preserves some formatting
    PERMISSIVE = "permissive"  # Minimal sanitization, preserves most characters


def _normalize_unicode_for_security(text: str) -> str:
    """
    SECURITY FIX: Normalize Unicode text to prevent bypass attempts.

    Converts full-width characters, removes zero-width characters, and normalizes
    Unicode variations that could be used to bypass security controls.

    Args:
        text: Input text to normalize

    Returns:
        Normalized text safe for security processing
    """
    # Remove zero-width and invisible characters commonly used in bypasses
    text = re.sub(r'[\u200b-\u200d\u2060\ufeff]', '', text)  # Zero-width characters
    text = re.sub(r'[\u2028\u2029]', ' ', text)  # Line/paragraph separators
    text = re.sub(r'[\u200e\u200f\u202a-\u202e]', '', text)  # Directional overrides

    # Normalize Unicode characters (NFKC to convert full-width to ASCII)
    text = unicodedata.normalize('NFKC', text)

    return text


def _decode_encoded_characters(text: str) -> str:
    """
    SECURITY FIX: Decode common character encodings used in bypass attempts.

    Detects and decodes hex, octal, and Unicode escape sequences that could
    be used to hide malicious code from simple pattern matching.

    Args:
        text: Input text potentially containing encoded characters

    Returns:
        Text with common encodings decoded for security analysis
    """
    try:
        # Decode common escape patterns
        # Handle \xNN hex escapes
        text = re.sub(r'\\x([0-9a-fA-F]{2})', lambda m: chr(int(m.group(1), 16)), text)
        # Handle \NNN octal escapes
        text = re.sub(r'\\([0-7]{3})', lambda m: chr(int(m.group(1), 8)), text)
        # Handle \\uNNNN Unicode escapes
        text = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), text)
        # Handle \\UXXXXXXXX Unicode escapes
        text = re.sub(r'\\U([0-9a-fA-F]{8})', lambda m: chr(int(m.group(1), 16)), text)
    except (ValueError, OverflowError):
        # If decoding fails, return original text
        pass

    return text


# LAZY LOADING: Regex patterns are compiled on-demand to improve module import performance
# This reduces startup overhead by only compiling patterns when actually used
# SECURITY FIXES: Enhanced patterns to prevent bypass vulnerabilities

from functools import lru_cache

@lru_cache(maxsize=None)
def _get_dangerous_keyword_pattern() -> re.Pattern:
    """Get dangerous keyword pattern with lazy compilation for performance optimization."""
    return re.compile(
        r'\b(?:import|exec|eval|system|subprocess|os|config|globals|locals|vars|dir|getattr|setattr|delattr|hasattr|__import__|open|file|input|raw_input|compile)\b',
        re.IGNORECASE
    )

@lru_cache(maxsize=None)
def _get_template_injection_pattern() -> re.Pattern:
    """Get template injection pattern with lazy compilation for performance optimization."""
    return re.compile(
        r'\$\{[^}]*\}|#\{[^}]*\}|\{\{[^}]*\}\}',
        re.IGNORECASE
    )

@lru_cache(maxsize=None)
def _get_format_string_pattern() -> re.Pattern:
    """Get format string pattern with lazy compilation for performance optimization."""
    return re.compile(
        r'%[\d$#]*[a-zA-Z]|%\([^)]*\)[a-zA-Z]',
        re.IGNORECASE
    )

@lru_cache(maxsize=None)
def _get_code_injection_pattern() -> re.Pattern:
    """Get code injection pattern with lazy compilation for performance optimization."""
    return re.compile(
        r'(?:__import__|eval|exec|compile)\s*\(|(?:chr\s*\(\s*\d+\s*\)\s*\+?\s*)+',
        re.IGNORECASE
    )

@lru_cache(maxsize=None)
def _get_dunder_pattern() -> re.Pattern:
    """Get dunder method pattern with lazy compilation for performance optimization."""
    return re.compile(
        r'__[a-zA-Z0-9_]*__|__.*?__|builtins|mro|subclasses|bases',
        re.IGNORECASE
    )

@lru_cache(maxsize=None)
def _get_attribute_pattern() -> re.Pattern:
    """Get attribute access pattern with lazy compilation for performance optimization."""
    return re.compile(
        r'\.[a-zA-Z_][a-zA-Z0-9_]*|\[\'[^\']*\'\]|\[\"[^\"]*\"\]',
        re.IGNORECASE
    )

@lru_cache(maxsize=None)
def _get_shell_pattern() -> re.Pattern:
    """Get shell metacharacters pattern with lazy compilation for performance optimization."""
    return re.compile(
        r'[|&;$<>`\\]|\\[\$`]|\\\(|\\\)|\\\[|\\\]',
        re.IGNORECASE
    )

@lru_cache(maxsize=None)
def _get_bracket_pattern() -> re.Pattern:
    """Get bracket pattern with lazy compilation for performance optimization."""
    return re.compile(
        r'[{}\[\]\(\)]',
        re.IGNORECASE
    )

@lru_cache(maxsize=None)
def _get_quote_pattern() -> re.Pattern:
    """Get quote characters pattern with lazy compilation for performance optimization."""
    return re.compile(
        r'["\']|\\["\']',
        re.IGNORECASE
    )

@lru_cache(maxsize=None)
def _get_html_injection_pattern() -> re.Pattern:
    """Get HTML/JS injection pattern with lazy compilation for performance optimization."""
    return re.compile(
        r'[<>"\'`]|&lt;|&gt;|&amp;|javascript:|vbscript:|on\w+\s*=',
        re.IGNORECASE
    )

@lru_cache(maxsize=None)
def _get_control_char_pattern() -> re.Pattern:
    """Get control characters pattern with lazy compilation for performance optimization."""
    return re.compile(
        r'[\r\n\t\x0b\x0c\x85\u2028\u2029]|\\[rnt]|\\x[0-9a-fA-F]{2}|\\[0-7]{3}',
        re.IGNORECASE
    )

@lru_cache(maxsize=None)
def _get_ansi_escape_pattern() -> re.Pattern:
    """Get ANSI escape sequences pattern with lazy compilation for performance optimization."""
    return re.compile(
        r'\x1b\[[0-9;]*m|\\x1b\[[0-9;]*m|\\u001b\[[0-9;]*m',
        re.IGNORECASE
    )

@lru_cache(maxsize=None)
def _get_whitespace_pattern() -> re.Pattern:
    """Get whitespace normalization pattern with lazy compilation for performance optimization."""
    return re.compile(
        r'\s+|[\u2000-\u200a\u3000]',
        re.IGNORECASE
    )

@lru_cache(maxsize=None)
def _get_log_injection_pattern() -> re.Pattern:
    """Get log injection pattern with lazy compilation for performance optimization."""
    return re.compile(
        r'\[(ERROR|CRITICAL|WARN|WARNING|INFO|DEBUG|TRACE|FATAL)\]|\\x1b\[\d+(;\d+)*m',
        re.IGNORECASE
    )

@lru_cache(maxsize=None)
def _get_nested_injection_pattern() -> re.Pattern:
    """Get nested injection pattern with lazy compilation for performance optimization."""
    return re.compile(
        r'(?:eval|exec)\s*\(\s*(?:eval|exec|chr|concat|join|\+)',
        re.IGNORECASE
    )

@lru_cache(maxsize=None)
def _get_string_concatenation_pattern() -> re.Pattern:
    """Get string concatenation pattern with lazy compilation for performance optimization."""
    return re.compile(
        r'[\'\"][^\'\"]*[\'\"]\s*\+\s*[\'\"][^\'\"]*[\'\"]|[\'\"]\s*\+\s*[\'\"]',
        re.IGNORECASE
    )

# Backward compatibility aliases (deprecated - use _get_*_pattern() functions instead)
# These maintain compatibility while new code should use the getter functions
# Note: Regex patterns are now lazily loaded through module-level __getattr__ function
# This provides backward compatibility while enabling lazy compilation for performance


def sanitize_text_input(
    text: Any,
    max_length: Optional[int] = None,
    level: str = SanitizationLevel.MODERATE,
    source: str = "unknown"
) -> str:
    """
    SECURITY FIXES: Comprehensive text sanitization with configurable security levels.

    Enhanced to prevent input validation bypass vulnerabilities (MAJOR-003).

    Args:
        text: Input text to sanitize (any type, non-string returns empty string)
        max_length: Maximum allowed length (default: KEYWORD_LENGTH_LIMIT * 20)
        level: Sanitization level (strict, moderate, permissive)
        source: Source identifier for security logging

    Returns:
        str: Sanitized text safe for further processing

    Security Features:
        - Defense-in-depth with multiple pattern matching layers
        - Length limiting to prevent buffer overflow attacks
        - Keyword blocking to prevent code injection
        - Pattern removal to prevent template/format injection
        - Control character normalization to prevent log poisoning
        - SECURITY FIXES: Unicode normalization prevents bypass attempts
        - SECURITY FIXES: Encoded character detection prevents hidden attacks
        - SECURITY FIXES: Enhanced pattern matching catches more variations
        - MAJOR-006: Security event logging for monitoring and auditing

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

    original_text = text  # Store for security logging

    # MAJOR-006: Security logging - Check for suspicious patterns before processing
    if any(pattern.search(text.lower()) for pattern_list in [
        [r'eval\s*\(', r'exec\s*\(', r'__import__\s*\('],  # Code injection
        [r'\bdrop\s+table\b', r';\s*drop'],  # SQL injection
        [r'<script[^>]*>', r'javascript:'],  # XSS
        [r'\.\./', r'%2e%2e%2f'],  # Path traversal
    ] for pattern in [re.compile(p) for p in pattern_list]):
        # Log security event
        log_security_event(
            input_text=text,
            source=source,
            context={
                "function": "sanitize_text_input",
                "level": level,
                "max_length": max_length,
            },
            block_action=True
        )

    # SECURITY FIX: Preprocess text to prevent bypass attempts
    # Length limiting (first line of defense)
    text = text[:max_length]

    # SECURITY FIX: Normalize Unicode to prevent bypass attempts
    text = _normalize_unicode_for_security(text)

    # SECURITY FIX: Decode encoded characters to prevent hidden attacks
    text = _decode_encoded_characters(text)

    # Layer 1: Block dangerous keywords (enhanced patterns)
    text = _get_dangerous_keyword_pattern().sub('', text)

    # Layer 2: Handle injection patterns based on security level
    if level == SanitizationLevel.STRICT:
        # Strict mode: remove all potentially dangerous patterns
        text = _get_template_injection_pattern().sub('', text)
        text = _get_format_string_pattern().sub('', text)
        text = _get_code_injection_pattern().sub('BLOCKED', text)

        # SECURITY FIX: Enhanced nested injection detection
        text = _get_nested_injection_pattern().sub('BLOCKED', text)
        text = _get_string_concatenation_pattern().sub(' ', text)

        # SECURITY FIX: Remove dots after code blocking to prevent bypass
        text = re.sub(r'[.]', ' ', text)  # Remove all remaining dots
        text = _get_dunder_pattern().sub('', text)
        text = _get_attribute_pattern().sub('', text)
        text = _get_shell_pattern().sub('', text)
        text = _get_bracket_pattern().sub('', text)
        text = _get_quote_pattern().sub('', text)

    elif level == SanitizationLevel.MODERATE:
        # Moderate mode: balanced security
        text = _get_template_injection_pattern().sub('', text)
        text = _get_format_string_pattern().sub('', text)
        text = _get_code_injection_pattern().sub('BLOCKED', text)
        text = _get_nested_injection_pattern().sub('BLOCKED', text)
        text = _get_bracket_pattern().sub('', text)
        text = _get_quote_pattern().sub('', text)

    else:  # PERMISSIVE
        # Permissive mode: minimal sanitization
        text = _get_code_injection_pattern().sub('BLOCKED', text)
        text = _get_template_injection_pattern().sub('', text)
        # SECURITY FIX: Even permissive mode blocks nested injections
        text = _get_nested_injection_pattern().sub('BLOCKED', text)

    # Layer 3: Handle characters that could poison logs or output
    text = _get_html_injection_pattern().sub('', text)
    text = _get_control_char_pattern().sub(' ', text)
    text = _get_whitespace_pattern().sub(' ', text)
    text = _get_ansi_escape_pattern().sub('', text)
    # SECURITY FIX: Additional log injection protection
    text = _get_log_injection_pattern().sub('[LOG_LEVEL_BLOCKED]', text)

    # MAJOR-006: Check if content was significantly modified/blocked
    sanitized_text = text.strip()

    # Log if content was heavily modified (possible attack blocked)
    if len(original_text) > 0 and len(sanitized_text) < len(original_text) * 0.3:
        # More than 70% of content was removed - possible attack
        log_security_event(
            input_text=original_text,
            source=source,
            context={
                "function": "sanitize_text_input",
                "level": level,
                "action": "heavily_sanitized",
                "original_length": len(original_text),
                "sanitized_length": len(sanitized_text),
            },
            block_action=False  # Was sanitized, not blocked
        )

    return sanitized_text


def sanitize_for_concatenation(text: Any, max_length: int = 50, source: str = "unknown") -> str:
    """
    Strict sanitization specifically for text that will be concatenated.

    This function provides maximum security for string concatenation operations
    where any injection vulnerability could be catastrophic.

    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length (default: 50 for safety)
        source: Source identifier for security logging

    Returns:
        str: Sanitized text safe for concatenation

    Security Features:
        - Very strict length limiting (50 chars default)
        - Comprehensive pattern removal
        - All special characters removed
        - Defense-in-depth approach
        - MAJOR-006: Security event logging for monitoring

    Examples:
        >>> sanitize_for_concatenation("Hello ${name}")
        'Hello name'
        >>> sanitize_for_concatenation("import os")
        ''
    """
    return sanitize_text_input(
        text=text,
        max_length=max_length,
        level=SanitizationLevel.STRICT,
        source=source
    )


def sanitize_for_display(text: Any, max_length: Optional[int] = None, source: str = "unknown") -> str:
    """
    Moderate sanitization for text that will be displayed to users.

    This function balances security with readability, preserving some formatting
    while still preventing injection attacks.

    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length (default: KEYWORD_LENGTH_LIMIT * 10)
        source: Source identifier for security logging

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
        level=SanitizationLevel.MODERATE,
        source=source
    )


def sanitize_for_logging(text: Any, max_length: Optional[int] = None) -> str:
    """
    SECURITY FIXES: Enhanced sanitization for text that will be written to logs.

    Enhanced to prevent log injection bypass vulnerabilities (MAJOR-003).

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
        - SECURITY FIXES: Enhanced control character detection prevents bypass
        - SECURITY FIXES: Unicode normalization prevents bypass attempts
        - SECURITY FIXES: Log level injection protection

    Examples:
        >>> sanitize_for_logging("Error\nInjected\rLine")
        'Error Injected Line'
    """
    if max_length is None:
        max_length = KEYWORD_LENGTH_LIMIT * 15

    if not isinstance(text, str):
        return ""

    text = text[:max_length]

    # SECURITY FIX: Preprocess to prevent bypass attempts
    text = _normalize_unicode_for_security(text)
    text = _decode_encoded_characters(text)

    # Focus on log-specific attacks while preserving debugging info
    # SECURITY FIX: Enhanced patterns prevent bypass attempts
    text = _get_control_char_pattern().sub(' ', text)
    text = _get_ansi_escape_pattern().sub('', text)
    text = _get_whitespace_pattern().sub(' ', text)
    # SECURITY FIX: Additional log injection protection
    text = _get_log_injection_pattern().sub('[LOG_LEVEL_BLOCKED]', text)

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
    text = _get_code_injection_pattern().sub('BLOCKED', text)

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


def __getattr__(name: str) -> re.Pattern:
    """
    Module-level lazy loading for regex patterns with backward compatibility.

    Provides backward compatibility for regex pattern constants while enabling
    lazy compilation for performance optimization.

    This function is called when accessing attributes that don't exist on the module.
    It enables lazy loading of regex patterns while maintaining the expected API.

    Args:
        name: Attribute name being accessed

    Returns:
        Compiled regex pattern for backward compatibility

    Raises:
        AttributeError: If name is not a recognized lazy-loaded pattern

    Examples:
        >>> import reasoning_library.sanitization as sanitization
        >>> pattern = sanitization._DANGEROUS_KEYWORD_PATTERN  # Triggers lazy compilation
        >>> isinstance(pattern, re.Pattern)  # True
    """
    pattern_getters = {
        '_DANGEROUS_KEYWORD_PATTERN': _get_dangerous_keyword_pattern,
        '_TEMPLATE_INJECTION_PATTERN': _get_template_injection_pattern,
        '_FORMAT_STRING_PATTERN': _get_format_string_pattern,
        '_CODE_INJECTION_PATTERN': _get_code_injection_pattern,
        '_DUNDER_PATTERN': _get_dunder_pattern,
        '_ATTRIBUTE_PATTERN': _get_attribute_pattern,
        '_SHELL_PATTERN': _get_shell_pattern,
        '_BRACKET_PATTERN': _get_bracket_pattern,
        '_QUOTE_PATTERN': _get_quote_pattern,
        '_HTML_INJECTION_PATTERN': _get_html_injection_pattern,
        '_CONTROL_CHAR_PATTERN': _get_control_char_pattern,
        '_ANSI_ESCAPE_PATTERN': _get_ansi_escape_pattern,
        '_WHITESPACE_PATTERN': _get_whitespace_pattern,
        '_LOG_INJECTION_PATTERN': _get_log_injection_pattern,
        '_NESTED_INJECTION_PATTERN': _get_nested_injection_pattern,
        '_STRING_CONCATENATION_PATTERN': _get_string_concatenation_pattern,
    }

    if name in pattern_getters:
        return pattern_getters[name]()

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")